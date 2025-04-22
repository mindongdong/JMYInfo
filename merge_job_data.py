import pandas as pd
from datetime import datetime
import os
import re
from fuzzywuzzy import fuzz
from tqdm import tqdm  # 진행률 표시용

# 필수 의존성 설치 명령어
# pip install pandas python-dateutil fuzzywuzzy python-Levenshtein tqdm

def check_files(filenames):
    """필요한 파일 존재 여부 확인"""
    missing = [f for f in filenames if not os.path.exists(f)]
    if missing:
        raise FileNotFoundError(f"누락된 파일: {', '.join(missing)}")

def normalize_date(date_str):
    """날짜 형식 표준화 (YYYY.MM.DD 추출)"""
    if isinstance(date_str, str):
        # YYYY-MM-DD/YYYY-MM-DD 형식 처리
        if '/' in date_str and '-' in date_str:
            try:
                # 마지막 날짜(마감일)만 추출
                deadline = date_str.split('/')[-1]
                return datetime.strptime(deadline, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # YYYY.MM.DDYYYY.MM.DD 형식 처리
        dates = re.findall(r'\d{4}\.\d{2}\.\d{2}', date_str)
        if dates:
            return datetime.strptime(dates[-1], '%Y.%m.%d').date()  # 마지막 날짜(마감일) 사용
    return None

def standardize_columns(df, source):
    """컬럼명 표준화"""
    column_mapping = {
        'military': {
            '채용제목': 'title',
            '업체명': 'company',
            '마감일': 'deadline'
        },
        'rndjob': {
            '공고명': 'title',
            '기업명': 'company',
            '등록일/마감일': 'deadline'
        }
    }
    return df.rename(columns=column_mapping[source])

def create_description(row, source):
    """상세 정보 생성"""
    if source == 'military':
        description = []
        if pd.notna(row.get('담당업무')):
            description.append(f"[담당업무]\n{row['담당업무']}")
        if pd.notna(row.get('자격요원')):
            description.append(f"[자격요건]\n{row['자격요원']}")
        if pd.notna(row.get('우대사항')):
            description.append(f"[우대사항]\n{row['우대사항']}")
        if pd.notna(row.get('비고')):
            description.append(f"[기타사항]\n{row['비고']}")
        return '\n\n'.join(description)
    else:  # rndjob
        description = []
        if pd.notna(row.get('담당업무')):
            description.append(f"[담당업무]\n{row['담당업무']}")
        if pd.notna(row.get('자격사항')):
            description.append(f"[자격요건]\n{row['자격사항']}")
        if pd.notna(row.get('우대사항')):
            description.append(f"[우대사항]\n{row['우대사항']}")
        if pd.notna(row.get('기타사항')):
            description.append(f"[기타사항]\n{row['기타사항']}")
        return '\n\n'.join(description)

def clean_company_name(name):
    """회사명 정제"""
    if not isinstance(name, str):
        return ""
    # 괄호와 특수문자 제거
    name = re.sub(r'[\(\)\[\]\{\}]', '', name)
    # (주) -> 주식회사 변환
    name = name.replace('(주)', '주식회사')
    # 공백 정규화
    name = re.sub(r'\s+', ' ', name).strip()
    # 기업부설연구소 관련 텍스트 제거
    name = re.sub(r'기업부설연구소|벤처기업부설연구소', '', name).strip()
    return name

def clean_job_title(title):
    """채용공고 제목 정제"""
    if not isinstance(title, str):
        return ""
    # 공백 정규화
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def extract_deadline(date_str):
    """마감일 추출"""
    if pd.isna(date_str):
        return None
    
    # YYYY-MM-DD/YYYY-MM-DD 형식 처리
    if isinstance(date_str, str) and '/' in date_str and '-' in date_str:
        try:
            # 마지막 날짜(마감일)만 추출
            deadline = date_str.split('/')[-1]
            return datetime.strptime(deadline, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # YYYY.MM.DDYYYY.MM.DD 형식 처리
    if isinstance(date_str, str):
        dates = re.findall(r'\d{4}\.\d{2}\.\d{2}', date_str)
        if dates:
            try:
                return datetime.strptime(dates[-1], '%Y.%m.%d').date()  # 마지막 날짜(마감일) 사용
            except ValueError:
                pass
    return None

def find_similar_jobs(df1, df2, threshold=60):
    """유사 채용공고 탐지"""
    similar_pairs = []
    total = len(df1) * len(df2)
    
    with tqdm(total=total, desc="유사 공고 검사 진행") as pbar:
        for i, row1 in df1.iterrows():
            for j, row2 in df2.iterrows():
                # 회사명 정제
                company1 = clean_company_name(str(row1['company']))
                company2 = clean_company_name(str(row2['company']))
                
                # 제목 정제
                title1 = clean_job_title(str(row1['title']))
                title2 = clean_job_title(str(row2['title']))
                
                # 마감일 비교
                deadline1 = extract_deadline(row1['deadline'])
                deadline2 = extract_deadline(row2['deadline'])
                
                # 전체 텍스트 유사도 계산
                full_text1 = f"{company1} {title1}"
                full_text2 = f"{company2} {title2}"
                full_score = fuzz.token_sort_ratio(full_text1, full_text2)
                
                # 회사명 유사도 계산
                company_score = fuzz.ratio(company1, company2)
                
                # 날짜 일치 여부 확인
                date_match = deadline1 == deadline2 if deadline1 and deadline2 else False
                
                # 마감일이 같고 유사도가 0보다 크면 같은 공고로 판단
                if date_match and (full_score > 0 or company_score > 0):
                    similar_pairs.append({
                        'df1_index': i,
                        'df2_index': j,
                        'full_similarity': full_score,
                        'company_similarity': company_score,
                        'date_match': date_match,
                        'deadline1': deadline1,
                        'deadline2': deadline2,
                        'title1': title1,
                        'title2': title2,
                        'company1': company1,
                        'company2': company2
                    })
                # 마감일이 다르지만 유사도가 임계값보다 높은 경우
                elif not date_match and (full_score > threshold and company_score > 40):
                    similar_pairs.append({
                        'df1_index': i,
                        'df2_index': j,
                        'full_similarity': full_score,
                        'company_similarity': company_score,
                        'date_match': date_match,
                        'deadline1': deadline1,
                        'deadline2': deadline2,
                        'title1': title1,
                        'title2': title2,
                        'company1': company1,
                        'company2': company2
                    })
                pbar.update(1)
    
    return pd.DataFrame(similar_pairs)

def merge_similar_jobs(df1, df2, similar_pairs, df1_detail, df2_detail):
    """유사한 채용공고 병합"""
    # 중복 제거를 위한 인덱스 집합
    df1_used = set()
    df2_used = set()
    
    merged_rows = []
    
    # 유사한 공고 먼저 처리
    for _, pair in similar_pairs.iterrows():
        if pair['df1_index'] not in df1_used and pair['df2_index'] not in df2_used:
            # df1의 데이터를 우선 사용
            merged_row = df1.iloc[pair['df1_index']].copy()
            # 상세 정보 병합
            df1_desc = create_description(df1_detail.iloc[pair['df1_index']], 'military')
            df2_desc = create_description(df2_detail.iloc[pair['df2_index']], 'rndjob')
            merged_row['description'] = f"{df1_desc}\n\n[다른 사이트의 상세 정보]\n{df2_desc}"
            merged_rows.append(merged_row)
            
            df1_used.add(pair['df1_index'])
            df2_used.add(pair['df2_index'])
    
    # 나머지 공고 추가
    for i, row in df1.iterrows():
        if i not in df1_used:
            merged_row = row.copy()
            merged_row['description'] = create_description(df1_detail.iloc[i], 'military')
            merged_rows.append(merged_row)
    
    for i, row in df2.iterrows():
        if i not in df2_used:
            merged_row = row.copy()
            merged_row['description'] = create_description(df2_detail.iloc[i], 'rndjob')
            merged_rows.append(merged_row)
    
    return pd.DataFrame(merged_rows)

# 메인 실행 블록
if __name__ == "__main__":
    # 1. 파일 검사
    required_files = [
        'crawling_results/military_jobs_basic_20250422_222821.csv',
        'crawling_results/military_jobs_detail_20250422_222821.csv',
        'crawling_results/rndjob_basic_20250422_221113.csv',
        'crawling_results/rndjob_detail_20250422_221113.csv'
    ]
    check_files(required_files)

    # 2. 데이터 로드 및 전처리
    military_basic = pd.read_csv('crawling_results/military_jobs_basic_20250422_222821.csv')
    military_detail = pd.read_csv('crawling_results/military_jobs_detail_20250422_222821.csv')
    rndjob_basic = pd.read_csv('crawling_results/rndjob_basic_20250422_221113.csv')
    rndjob_detail = pd.read_csv('crawling_results/rndjob_detail_20250422_221113.csv')

    # 컬럼명 확인
    print("\n=== 컬럼명 확인 ===")
    print("military_basic 컬럼:", military_basic.columns.tolist())
    print("rndjob_basic 컬럼:", rndjob_basic.columns.tolist())

    # 3. 컬럼명 표준화
    military_basic = standardize_columns(military_basic, 'military')
    rndjob_basic = standardize_columns(rndjob_basic, 'rndjob')

    # 4. 날짜 형식 표준화
    military_basic['deadline'] = military_basic['deadline'].apply(normalize_date)
    rndjob_basic['deadline'] = rndjob_basic['deadline'].apply(normalize_date)

    # 5. 유사 공고 검사
    print("\n유사 공고 검사 시작...")
    similar_pairs = find_similar_jobs(military_basic, rndjob_basic)
    
    if not similar_pairs.empty:
        similar_pairs.to_csv('similar_jobs.csv', index=False, encoding='utf-8-sig')
        print(f"유사 공고 {len(similar_pairs)}개 발견 → similar_jobs.csv 저장")

    # 6. 데이터 병합
    print("\n데이터 병합 시작...")
    merged_df = merge_similar_jobs(military_basic, rndjob_basic, similar_pairs, military_detail, rndjob_detail)

    # 7. 최종 저장
    merged_df.to_csv('merged_jobs_final.csv', index=False, encoding='utf-8-sig')
    print("\n병합 완료: merged_jobs_final.csv")

    # 8. 최종 요약
    print("\n최종 결과 요약")
    print(f"총 공고 수: {len(merged_df)}")
    print(f"유사 공고 수: {len(similar_pairs)}")
    # print(merged_df.head(3).to_markdown(index=False))

