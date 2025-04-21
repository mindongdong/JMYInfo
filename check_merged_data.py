import pandas as pd
import os
import glob
from datetime import datetime

def load_latest_merged_file():
    """
    merged_results 디렉토리에서 가장 최근에 생성된 파일을 로드합니다.
    """
    merged_dir = 'merged_results'
    files = glob.glob(os.path.join(merged_dir, '*.csv'))
    if not files:
        raise FileNotFoundError("병합된 데이터 파일을 찾을 수 없습니다.")
    
    latest_file = max(files, key=os.path.getctime)
    print(f"분석 대상 파일: {os.path.basename(latest_file)}\n")
    return pd.read_csv(latest_file, encoding='utf-8-sig')

def check_data_completeness(df):
    """
    데이터의 완성도를 검사합니다.
    """
    print(f"{'='*50}")
    print("1. 데이터 완성도 검사")
    print(f"{'='*50}")
    
    # 전체 행 수
    total_rows = len(df)
    print(f"총 채용공고 수: {total_rows:,}개")
    
    # 각 컬럼의 결측치 비율
    print("\n각 컬럼별 데이터 존재 비율:")
    for col in df.columns:
        non_null_count = df[col].notna().sum()
        percentage = (non_null_count / total_rows) * 100
        print(f"{col:.<30} {percentage:.1f}% ({non_null_count:,}/{total_rows:,})")

def check_data_consistency(df):
    """
    데이터의 일관성을 검사합니다.
    """
    print(f"\n{'='*50}")
    print("2. 데이터 일관성 검사")
    print(f"{'='*50}")
    
    # URL 형식 검사
    invalid_urls = df[~df['상세정보_URL'].str.contains('http', na=False)]['상세정보_URL'].unique()
    print("\n[URL 형식 검사]")
    print(f"부적절한 URL 개수: {len(invalid_urls)}개")
    if len(invalid_urls) > 0:
        print("예시:")
        for url in invalid_urls[:3]:
            print(f"- {url}")
    
    # 날짜 형식 검사
    print("\n[날짜 형식 검사]")
    for col in ['마감일', '작성일']:
        if col in df.columns:
            invalid_dates = df[~df[col].str.match(r'^\d{4}-\d{2}-\d{2}$', na=True)][col].unique()
            print(f"\n{col} 형식 오류: {len(invalid_dates)}개")
            if len(invalid_dates) > 0:
                print("예시:")
                for date in invalid_dates[:3]:
                    print(f"- {date}")

def analyze_data_patterns(df):
    """
    데이터의 패턴을 분석합니다.
    """
    print(f"\n{'='*50}")
    print("3. 데이터 패턴 분석")
    print(f"{'='*50}")
    
    # 산업분야 분포
    if '산업분야' in df.columns:
        print("\n[산업분야 분포]")
        industry_counts = df['산업분야'].value_counts()
        for industry, count in industry_counts.head().items():
            print(f"{industry:.<30} {count:,}개")
    
    # 경력 요구사항 분포
    if '경력' in df.columns:
        print("\n[경력 요구사항 분포]")
        experience_counts = df['경력'].value_counts()
        for exp, count in experience_counts.head().items():
            print(f"{exp:.<30} {count:,}개")
    
    # 기업구분 분포
    if '기업구분' in df.columns:
        print("\n[기업구분 분포]")
        company_type_counts = df['기업구분'].value_counts()
        for type_, count in company_type_counts.head().items():
            print(f"{type_:.<30} {count:,}개")

def check_list_columns(df):
    """
    리스트 형태의 컬럼들을 검사합니다.
    """
    print(f"\n{'='*50}")
    print("4. 리스트 컬럼 검사")
    print(f"{'='*50}")
    
    list_columns = ['기업구분', '주요업무', '자격요건', '우대조건', '전형절차', '제출서류']
    
    for col in list_columns:
        if col in df.columns:
            print(f"\n[{col}]")
            # 리스트가 아닌 형태의 데이터 개수
            non_list_count = df[df[col].notna()][~df[col].apply(lambda x: isinstance(x, list))][col].count()
            print(f"리스트 형식이 아닌 데이터: {non_list_count:,}개")
            
            # 가장 흔한 항목들
            if non_list_count == 0:
                all_items = [item for sublist in df[col].dropna() for item in sublist]
                item_counts = pd.Series(all_items).value_counts()
                print("\n가장 흔한 항목 (상위 5개):")
                for item, count in item_counts.head().items():
                    print(f"- {item}: {count:,}회")

def main():
    """
    메인 실행 함수
    """
    try:
        print("데이터 검토를 시작합니다...\n")
        
        # 데이터 로드
        df = load_latest_merged_file()
        
        # 각종 검사 실행
        check_data_completeness(df)
        check_data_consistency(df)
        analyze_data_patterns(df)
        check_list_columns(df)
        
        print("\n데이터 검토가 완료되었습니다.")
        
    except Exception as e:
        print(f"\n오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main() 