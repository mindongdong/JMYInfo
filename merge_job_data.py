import pandas as pd
import os
from datetime import datetime

def load_and_preprocess_data():
    """
    세 개의 CSV 파일을 로드하고 전처리합니다.
    """
    # 파일 경로 설정
    rndjob_file = 'crawling_results/rndjob_crawling_20250418_220648.csv'
    military_basic_file = 'crawling_results/military_jobs_basic_20250420_183014.csv'
    
    # 데이터 로드
    rndjob_df = pd.read_csv(rndjob_file, encoding='utf-8-sig')
    military_basic_df = pd.read_csv(military_basic_file, encoding='utf-8-sig')
    
    # 컬럼명 통일
    rndjob_df = rndjob_df.rename(columns={
        '회사명': '기업명',
        '회사_종류': '기업구분',
        '회사_산업(업종)': '산업분야',
        '담당업무': '주요업무',
        '자격사항': '자격요건',
        '우대사항': '우대조건',
        '근무환경': '근무조건',
        '채용공고_URL': '상세정보_URL'
    })
    
    military_basic_df = military_basic_df.rename(columns={
        '업체명': '기업명',
        '채용제목': '공고제목'
    })

    # URL 정리 (병합 전에 미리 처리)
    rndjob_df['상세정보_URL'] = rndjob_df['상세정보_URL'].apply(lambda x: x.split('>')[0] if pd.notna(x) and '>' in x else x)
    military_basic_df['상세정보_URL'] = military_basic_df['상세정보_URL'].apply(lambda x: x.split('>')[0] if pd.notna(x) and '>' in x else x)

    # 필요한 컬럼 선택
    rndjob_columns = [
        '기업명', '기업구분', '산업분야', '경력', '주요업무', '자격요건', 
        '우대조건', '근무조건', '전형절차', '제출서류', '기타사항', 
        '복리후생', '상세정보_URL'
    ]
    
    military_columns = [
        '기업명', '공고제목', '마감일', '작성일', '조회수', '상세정보_URL'
    ]

    rndjob_df = rndjob_df[rndjob_columns]
    military_basic_df = military_basic_df[military_columns]

    # 중복 확인을 위한 정보 출력
    print("\n[데이터 병합 전 중복 검사]")
    print(f"RndJob 데이터 수: {len(rndjob_df):,}개")
    print(f"Military 데이터 수: {len(military_basic_df):,}개")
    
    # URL 기준 중복 검사
    url_duplicates = set(rndjob_df['상세정보_URL']).intersection(set(military_basic_df['상세정보_URL']))
    print(f"URL 기준 중복 건수: {len(url_duplicates):,}개")
    
    # 기업명 기준 중복 검사
    company_duplicates = set(rndjob_df['기업명']).intersection(set(military_basic_df['기업명']))
    print(f"기업명 기준 중복 건수: {len(company_duplicates):,}개")

    # 데이터 병합 (outer join 대신 left join으로 변경)
    merged_df = pd.merge(
        military_basic_df,
        rndjob_df,
        on=['기업명', '상세정보_URL'],
        how='outer',
        indicator=True
    )

    # 병합 결과 분석
    print("\n[데이터 병합 결과]")
    merge_stats = merged_df['_merge'].value_counts()
    print(f"Military 데이터만 있는 경우: {merge_stats.get('left_only', 0):,}개")
    print(f"RndJob 데이터만 있는 경우: {merge_stats.get('right_only', 0):,}개")
    print(f"양쪽 모두 있는 경우: {merge_stats.get('both', 0):,}개")

    # _merge 컬럼 제거
    merged_df = merged_df.drop('_merge', axis=1)

    # 데이터 정리
    merged_df = clean_data(merged_df)
    
    return merged_df

def clean_data(df):
    """
    병합된 데이터를 정리합니다.
    """
    # 리스트 형태의 문자열을 실제 리스트로 변환
    list_columns = ['기업구분', '주요업무', '자격요건', '우대조건', '전형절차', '제출서류']
    for col in list_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: eval(str(x)) if pd.notna(x) and str(x).strip().startswith('[') else x)
            df[col] = df[col].apply(lambda x: [item.strip() for item in x] if isinstance(x, list) else x)

    # 날짜 형식 통일
    date_columns = ['마감일', '작성일']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format='%Y-%m-%d', errors='coerce')
            df[col] = df[col].dt.strftime('%Y-%m-%d')

    # 복리후생 정리
    if '복리후생' in df.columns:
        df['복리후생'] = df['복리후생'].apply(lambda x: 
            eval(str(x))['연금.보험'] if pd.notna(x) and isinstance(eval(str(x)), dict) and '연금.보험' in eval(str(x))
            else None
        )

    return df

def save_merged_data(df):
    """
    병합된 데이터를 저장합니다.
    """
    # 저장 디렉토리 생성
    output_dir = 'merged_results'
    os.makedirs(output_dir, exist_ok=True)
    
    # 현재 시간을 파일명에 포함
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"{output_dir}/merged_jobs_{current_time}.csv"
    
    # CSV 파일로 저장
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n데이터가 성공적으로 저장되었습니다: {output_file}")
    
    # 데이터 요약 정보 출력
    print(f"\n{'='*50}")
    print("데이터 통합 결과")
    print(f"{'='*50}")
    print(f"총 채용공고 수: {len(df):,}개")
    print(f"\n포함된 컬럼 목록:")
    for idx, column in enumerate(df.columns, 1):
        non_null_count = df[column].notna().sum()
        percentage = (non_null_count / len(df)) * 100
        print(f"{idx}. {column:.<30} {percentage:.1f}% ({non_null_count:,}/{len(df):,})")

def main():
    """
    메인 실행 함수
    """
    try:
        print("데이터 통합을 시작합니다...")
        merged_df = load_and_preprocess_data()
        save_merged_data(merged_df)
        print("\n데이터 통합이 완료되었습니다.")
    except Exception as e:
        print(f"\n오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main() 