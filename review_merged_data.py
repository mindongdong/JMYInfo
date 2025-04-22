import pandas as pd
import os
from datetime import datetime

def check_merged_data():
    """병합된 데이터 검토"""
    if not os.path.exists('merged_jobs_final.csv'):
        print("병합된 데이터 파일이 없습니다.")
        return

    # 데이터 로드
    df = pd.read_csv('merged_jobs_final.csv')
    
    # 1. 기본 정보 출력
    print("\n=== 기본 정보 ===")
    print(f"총 공고 수: {len(df)}")
    print(f"컬럼 목록: {', '.join(df.columns)}")
    
    # 2. 날짜 형식 검사
    print("\n=== 날짜 형식 검사 ===")
    invalid_dates = df[df['deadline'].isna()]
    if len(invalid_dates) > 0:
        print(f"날짜 형식이 잘못된 공고 수: {len(invalid_dates)}")
        print("예시:")
        print(invalid_dates[['company', 'title', 'deadline']].head())
    else:
        print("모든 날짜 형식이 정상입니다.")
    
    # 3. 상세 정보 검사
    print("\n=== 상세 정보 검사 ===")
    missing_desc = df[df['description'].isna()]
    if len(missing_desc) > 0:
        print(f"상세 정보가 없는 공고 수: {len(missing_desc)}")
        print("예시:")
        print(missing_desc[['company', 'title']].head())
    else:
        print("모든 공고에 상세 정보가 포함되어 있습니다.")
    
    # 4. 유사 공고 검사
    print("\n=== 유사 공고 검사 ===")
    similar_jobs = df[df['description'].str.contains('다른 사이트의 상세 정보', na=False)]
    print(f"유사 공고 수: {len(similar_jobs)}")
    if len(similar_jobs) > 0:
        print("\n유사 공고 예시:")
        for _, row in similar_jobs.head(3).iterrows():
            print(f"\n회사: {row['company']}")
            print(f"제목: {row['title']}")
            print(f"마감일: {row['deadline']}")
            print("상세 정보 길이:", len(str(row['description'])))
    
    # 5. 샘플 데이터 출력
    print("\n=== 샘플 데이터 (3개) ===")
    for _, row in df.head(3).iterrows():
        print(f"\n회사: {row['company']}")
        print(f"제목: {row['title']}")
        print(f"마감일: {row['deadline']}")
        print("상세 정보 길이:", len(str(row['description'])))
        print("-" * 50)

if __name__ == "__main__":
    check_merged_data() 