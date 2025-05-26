import pandas as pd
import ast
import re
from datetime import datetime
import os
import argparse

# 컬럼 존재 여부 체크 함수
def check_required_columns(df, required_columns, df_name="DataFrame"):
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise KeyError(f"{df_name}에 다음 컬럼이 없습니다: {missing}")

# 안전한 literal_eval
def safe_literal_eval(val):
    if isinstance(val, list):
        return val
    if not isinstance(val, str) or not val.strip():
        return []
    try:
        result = ast.literal_eval(val)
        if isinstance(result, list):
            return result
        elif isinstance(result, str):
            return [result]
        else:
            return []
    except Exception:
        return []

def process_military_jobs(basic_file, detail_file):
    try:
        basic_df = pd.read_csv(basic_file)
        detail_df = pd.read_csv(detail_file)
        # 필수 컬럼 체크
        basic_required = ['상세정보_URL', '업체명', '채용제목', '작성일', '마감일', '요원형태', '최종학력', '자격요원', '주소', '담당업무', '비고']
        detail_required = ['상세정보_URL']
        check_required_columns(basic_df, basic_required, 'military basic_df')
        check_required_columns(detail_df, detail_required, 'military detail_df')
        merged_df = pd.merge(basic_df, detail_df, on='상세정보_URL', how='inner')
        if merged_df.empty:
            print("[경고] 군무원 병합 결과가 비어 있습니다. 입력 파일을 확인하세요.")
            raise ValueError("군무원 병합 결과가 비어 있음")
        print(f"[INFO] 군무원 병합 결과: {len(merged_df)} rows")
        final_df = pd.DataFrame()
        final_df['company_name'] = merged_df['업체명']
        final_df['post_name'] = merged_df['채용제목']
        final_df['registration_date'] = merged_df['작성일']
        final_df['deadline'] = merged_df['마감일']
        final_df['qualification_agent'] = merged_df['요원형태']
        final_df['qualification_education'] = merged_df['최종학력']
        final_df['qualification_career'] = merged_df['자격요원']
        final_df['region'] = merged_df['주소']
        final_df['Field'] = merged_df['담당업무']
        final_df['keywords_list'] = merged_df['비고']
        final_df['source_info'] = merged_df['상세정보_URL']
        final_df['source_type'] = 'military'
        return final_df
    except Exception as e:
        print(f"[ERROR] process_military_jobs 예외: {e}")
        raise

def process_rnd_jobs(basic_file, detail_file):
    try:
        basic_df = pd.read_csv(basic_file)
        detail_df = pd.read_csv(detail_file)
        # 필수 컬럼 체크
        basic_required = ['상세정보_URL', '기업명', '공고명', '등록일', '마감일', '학력', '경력', '지역', '근무환경', '모집_분야_및_인원']
        detail_required = ['상세정보_URL', '담당업무', '자격사항', '우대사항']
        check_required_columns(basic_df, basic_required, 'rnd basic_df')
        check_required_columns(detail_df, detail_required, 'rnd detail_df')
        merged_df = pd.merge(basic_df, detail_df, on='상세정보_URL', how='inner')
        if merged_df.empty:
            print("[경고] RND 병합 결과가 비어 있습니다. 입력 파일을 확인하세요.")
            raise ValueError("RND 병합 결과가 비어 있음")
        print(f"[INFO] RND 병합 결과: {len(merged_df)} rows")
        final_df = pd.DataFrame()
        final_df['company_name'] = merged_df['기업명']
        final_df['post_name'] = merged_df['공고명']
        final_df['registration_date'] = merged_df['등록일']
        final_df['deadline'] = merged_df['마감일']
        final_df['qualification_education'] = merged_df['학력']
        final_df['qualification_career'] = merged_df['경력']
        final_df['region'] = merged_df['지역']
        def extract_employment_type(x):
            if not isinstance(x, str) or not x.strip():
                return ''
            try:
                env_dict = ast.literal_eval(x)
                if isinstance(env_dict, dict):
                    return env_dict.get('고용형태', '')
                else:
                    return ''
            except Exception:
                return ''
        final_df['qualification_agent'] = merged_df['근무환경'].apply(extract_employment_type)
        final_df['Field'] = merged_df['모집_분야_및_인원']
        def combine_keywords(row):
            keywords = []
            for col in ['담당업무', '자격사항', '우대사항']:
                items = safe_literal_eval(row[col]) if col in row and pd.notnull(row[col]) else []
                if items:
                    keywords.extend(items)
            return keywords
        final_df['keywords_list'] = merged_df.apply(combine_keywords, axis=1)
        final_df['source_info'] = merged_df['상세정보_URL']
        final_df['source_type'] = 'rndjob'
        return final_df
    except Exception as e:
        print(f"[ERROR] process_rnd_jobs 예외: {e}")
        raise

def update_job_data(new_df):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_df['update_date'] = current_time
    new_df['status'] = 'new'
    for col in ['company_name', 'post_name', 'source_info']:
        if col not in new_df.columns:
            raise KeyError(f"'{col}' 컬럼이 new_df에 없습니다.")
    if os.path.exists('processed_job_data.csv'):
        existing_df = pd.read_csv('processed_job_data.csv')
        for col in ['company_name', 'post_name', 'source_info']:
            if col not in existing_df.columns:
                raise KeyError(f"'{col}' 컬럼이 기존 데이터에 없습니다.")
        new_df['job_id'] = new_df['company_name'].astype(str) + '_' + new_df['post_name'].astype(str) + '_' + new_df['source_info'].astype(str)
        existing_df['job_id'] = existing_df['company_name'].astype(str) + '_' + existing_df['post_name'].astype(str) + '_' + existing_df['source_info'].astype(str)
        new_entries = new_df[~new_df['job_id'].isin(existing_df['job_id'])]
        updated_entries = new_df[new_df['job_id'].isin(existing_df['job_id'])]
        updated_entries['status'] = 'updated'
        unchanged_entries = existing_df[~existing_df['job_id'].isin(new_df['job_id'])]
        unchanged_entries['status'] = 'unchanged'
        final_df = pd.concat([new_entries, updated_entries, unchanged_entries], ignore_index=True)
        final_df = final_df.drop('job_id', axis=1)
        print(f"[INFO] 신규: {len(new_entries)}, 갱신: {len(updated_entries)}, 유지: {len(unchanged_entries)}")
        return final_df
    else:
        print(f"[INFO] 기존 데이터 없음. 모두 신규로 처리: {len(new_df)} rows")
        return new_df

def main():
    parser = argparse.ArgumentParser(description='Process job data from crawled files')
    parser.add_argument('--military-basic', required=True, help='Path to military jobs basic CSV file')
    parser.add_argument('--military-detail', required=True, help='Path to military jobs detail CSV file')
    parser.add_argument('--rnd-basic', required=True, help='Path to RND jobs basic CSV file')
    parser.add_argument('--rnd-detail', required=True, help='Path to RND jobs detail CSV file')
    parser.add_argument('--output', required=True, help='Path to output processed CSV file')
    args = parser.parse_args()
    try:
        military_df = process_military_jobs(args.military_basic, args.military_detail)
    except Exception as e:
        print(f"[ERROR] 군무원 데이터 처리 실패: {e}")
        military_df = pd.DataFrame()
    try:
        rnd_df = process_rnd_jobs(args.rnd_basic, args.rnd_detail)
    except Exception as e:
        print(f"[ERROR] RND 데이터 처리 실패: {e}")
        rnd_df = pd.DataFrame()
    combined_df = pd.concat([military_df, rnd_df], ignore_index=True)
    print(f"[INFO] 전체 데이터 합계: {len(combined_df)} rows")
    for date_col in ['registration_date', 'deadline']:
        if date_col in combined_df.columns:
            combined_df[date_col] = pd.to_datetime(combined_df[date_col], errors='coerce')
    try:
        final_df = update_job_data(combined_df)
    except Exception as e:
        print(f"[ERROR] update_job_data 처리 실패: {e}")
        final_df = combined_df
    try:
        final_df.to_csv(args.output, index=False, encoding='utf-8-sig')
        print(f"[INFO] 데이터 저장 완료: '{args.output}'")
    except Exception as e:
        print(f"[ERROR] 파일 저장 실패: {e}")
    if 'status' in final_df.columns:
        status_counts = final_df['status'].value_counts()
        print("\n[INFO] Update Statistics:")
        for status, count in status_counts.items():
            print(f"{status}: {count} entries")
    else:
        print("[INFO] status 컬럼 없음. 통계 출력 생략.")

if __name__ == "__main__":
    main() 