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

# 파일 유효성 검사 함수 추가
def validate_csv_file(file_path, file_type=""):
    """CSV 파일이 유효한지 검사"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_type} 파일을 찾을 수 없습니다: {file_path}")
    
    try:
        # 파일이 비어있는지 확인
        if os.path.getsize(file_path) == 0:
            raise ValueError(f"{file_type} 파일이 비어있습니다: {file_path}")
        
        # CSV 읽기 시도
        test_df = pd.read_csv(file_path, nrows=1)
        if test_df.empty or len(test_df.columns) == 0:
            raise ValueError(f"{file_type} 파일에 유효한 데이터가 없습니다: {file_path}")
            
        return True
    except pd.errors.EmptyDataError:
        raise ValueError(f"{file_type} 파일을 읽을 수 없습니다: {file_path}")

# 안전한 literal_eval
def safe_literal_eval(val):
    if isinstance(val, list):
        return val
    if pd.isna(val) or not isinstance(val, str) or not val.strip():
        return []
    try:
        # 문자열 정리
        val = val.strip()
        if not val:
            return []
            
        result = ast.literal_eval(val)
        if isinstance(result, list):
            return result
        elif isinstance(result, str):
            return [result]
        else:
            return []
    except (ValueError, SyntaxError, TypeError) as e:
        print(f"[WARNING] literal_eval 실패: {val[:50]}... - {e}")
        return []

# 날짜 형식 통일 함수 추가
def normalize_date_format(date_str):
    """날짜 문자열을 표준 형식으로 변환"""
    if pd.isna(date_str) or not isinstance(date_str, str) or not date_str.strip():
        return None
    
    date_str = str(date_str).strip()
    
    try:
        # YYYY.MM.DD 형식을 YYYY-MM-DD로 변환
        if '.' in date_str and len(date_str) == 10:
            # 2025.06.09 -> 2025-06-09
            return date_str.replace('.', '-')
        
        # 이미 YYYY-MM-DD 형식인 경우
        if '-' in date_str and len(date_str) == 10:
            return date_str
            
        # 기타 형식 시도
        # pandas to_datetime으로 파싱 시도
        parsed_date = pd.to_datetime(date_str, errors='coerce')
        if pd.notna(parsed_date):
            return parsed_date.strftime('%Y-%m-%d')
            
        return None
        
    except Exception as e:
        print(f"[WARNING] 날짜 형식 변환 실패: {date_str} - {e}")
        return None

def process_military_jobs(basic_file, detail_file):
    try:
        # 파일 유효성 검사
        validate_csv_file(basic_file, "군무원 기본")
        validate_csv_file(detail_file, "군무원 상세")
        
        print(f"[INFO] 군무원 파일 읽기 시작...")
        basic_df = pd.read_csv(basic_file)
        detail_df = pd.read_csv(detail_file)
        
        print(f"[INFO] 군무원 기본 데이터: {len(basic_df)} rows, 상세 데이터: {len(detail_df)} rows")
        
        # 데이터가 비어있는지 확인
        if basic_df.empty:
            print("[WARNING] 군무원 기본 데이터가 비어있습니다.")
            return pd.DataFrame()
        if detail_df.empty:
            print("[WARNING] 군무원 상세 데이터가 비어있습니다.")
            return pd.DataFrame()
        
        # 필수 컬럼 체크
        basic_required = ['상세정보_URL', '업체명', '채용제목', '작성일', '마감일']
        detail_required = ['상세정보_URL', '요원형태', '최종학력', '자격요원', '주소', '담당업무', '비고']
        
        check_required_columns(basic_df, basic_required, 'military basic_df')
        check_required_columns(detail_df, detail_required, 'military detail_df')
        
        # 병합 전 키 컬럼 확인
        if '상세정보_URL' not in basic_df.columns or '상세정보_URL' not in detail_df.columns:
            raise KeyError("병합 키 '상세정보_URL'이 없습니다.")
        
        # 중복 컬럼 제거 (상세정보_URL 제외)
        overlap_cols = [col for col in detail_df.columns if col in basic_df.columns and col != '상세정보_URL']
        if overlap_cols:
            detail_df = detail_df.drop(columns=overlap_cols)
        
        merged_df = pd.merge(basic_df, detail_df, on='상세정보_URL', how='inner')
        
        if merged_df.empty:
            print("[WARNING] 군무원 병합 결과가 비어 있습니다.")
            return pd.DataFrame()
            
        print(f"[INFO] 군무원 병합 성공: {len(merged_df)} rows")
        
        # 병합 후 컬럼명 확인
        print("[DEBUG] 병합 후 merged_df 컬럼:", merged_df.columns.tolist())
        
        final_df = pd.DataFrame()
        # 매핑 규칙에 따라 컬럼 할당
        final_df['company_name'] = merged_df.get('업체명', '')
        final_df['post_name'] = merged_df.get('채용제목', '')
        # 날짜 형식 통일 적용
        final_df['registration_date'] = merged_df['작성일'].apply(normalize_date_format) if '작성일' in merged_df.columns else ''
        final_df['deadline'] = merged_df['마감일'].apply(normalize_date_format) if '마감일' in merged_df.columns else ''
        final_df['qualification_agent'] = merged_df.get('요원형태', '')
        final_df['qualification_education'] = merged_df.get('최종학력', '')
        final_df['qualification_career'] = merged_df.get('자격요원', '')
        final_df['region'] = merged_df.get('주소', '')
        final_df['Field'] = merged_df.get('담당업무', '')
        final_df['keywords_list'] = merged_df.get('비고', '')
        final_df['source_info'] = merged_df.get('상세정보_URL', '')
        final_df['source_type'] = 'military'
        
        print("[DEBUG] Military registration_date 변환 전:", final_df['registration_date'].head(5).tolist())
        print("[DEBUG] Military deadline 변환 전:", final_df['deadline'].head(5).tolist())
                
        return final_df
        
    except Exception as e:
        print(f"[ERROR] process_military_jobs 예외: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def process_rnd_jobs(basic_file, detail_file):
    try:
        # 파일 유효성 검사
        validate_csv_file(basic_file, "RND 기본")
        validate_csv_file(detail_file, "RND 상세")
        
        print(f"[INFO] RND 파일 읽기 시작...")
        basic_df = pd.read_csv(basic_file)
        detail_df = pd.read_csv(detail_file)
        
        print(f"[INFO] RND 기본 데이터: {len(basic_df)} rows, 상세 데이터: {len(detail_df)} rows")
        
        # 데이터가 비어있는지 확인
        if basic_df.empty:
            print("[WARNING] RND 기본 데이터가 비어있습니다.")
            return pd.DataFrame()
        if detail_df.empty:
            print("[WARNING] RND 상세 데이터가 비어있습니다.")
            return pd.DataFrame()
        
        # 필수 컬럼 체크
        basic_required = ['상세정보_URL', '기업명', '공고명', '등록일', '마감일']
        detail_required = ['상세정보_URL', '고용형태', '학력', '경력', '회사_상세_주소', '모집_분야_및_인원', '담당업무', '자격사항', '우대사항']
        
        check_required_columns(basic_df, basic_required, 'rnd basic_df')
        check_required_columns(detail_df, detail_required, 'rnd detail_df')
        
        # 병합 전 키 컬럼 확인
        if '상세정보_URL' not in basic_df.columns or '상세정보_URL' not in detail_df.columns:
            raise KeyError("병합 키 '상세정보_URL'이 없습니다.")
        
        # 중복 컬럼 제거 (상세정보_URL 제외)
        overlap_cols = [col for col in detail_df.columns if col in basic_df.columns and col != '상세정보_URL']
        if overlap_cols:
            detail_df = detail_df.drop(columns=overlap_cols)
        
        merged_df = pd.merge(basic_df, detail_df, on='상세정보_URL', how='inner')
        
        if merged_df.empty:
            print("[WARNING] RND 병합 결과가 비어 있습니다.")
            return pd.DataFrame()
            
        print(f"[INFO] RND 병합 성공: {len(merged_df)} rows")
        
        # 병합 후 컬럼명 확인
        print("[DEBUG] 병합 후 merged_df 컬럼:", merged_df.columns.tolist())
        
        # 병합 후 값 확인
        print("[DEBUG] merged_df['등록일'] 샘플:", merged_df['등록일'].head(10).tolist())
        print("[DEBUG] merged_df['마감일'] 샘플:", merged_df['마감일'].head(10).tolist())
        
        final_df = pd.DataFrame()
        final_df['company_name'] = merged_df.get('기업명', '')
        final_df['post_name'] = merged_df.get('공고명', '')
        # 날짜 형식 통일 적용
        final_df['registration_date'] = merged_df['등록일'].apply(normalize_date_format) if '등록일' in merged_df.columns else ''
        final_df['deadline'] = merged_df['마감일'].apply(normalize_date_format) if '마감일' in merged_df.columns else ''
        final_df['qualification_agent'] = merged_df.get('고용형태', '')
        final_df['qualification_education'] = merged_df.get('학력', '')
        final_df['qualification_career'] = merged_df.get('경력', '')
        final_df['region'] = merged_df.get('회사_상세_주소', '')
        final_df['Field'] = merged_df.get('모집_분야_및_인원', '')
        # keywords_list: detail의 3개 컬럼 합치기
        def combine_keywords(row):
            keywords = []
            for col in ['담당업무', '자격사항', '우대사항']:
                if col in row and pd.notna(row[col]):
                    items = safe_literal_eval(row[col])
                    if items:
                        keywords.extend(items)
            return keywords
        final_df['keywords_list'] = merged_df.apply(combine_keywords, axis=1)
        final_df['source_info'] = merged_df.get('상세정보_URL', '')
        final_df['source_type'] = 'rndjob'
        
        print("[DEBUG] RND registration_date 변환 전:", final_df['registration_date'].head(5).tolist())
        print("[DEBUG] RND deadline 변환 전:", final_df['deadline'].head(5).tolist())
        
        return final_df
        
    except Exception as e:
        print(f"[ERROR] process_rnd_jobs 예외: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def update_job_data(new_df):
    try:
        if new_df.empty:
            print("[WARNING] 업데이트할 새 데이터가 없습니다.")
            return pd.DataFrame()
        
        # 필수 컬럼 확인
        for col in ['company_name', 'post_name', 'source_info']:
            if col not in new_df.columns:
                print(f"[WARNING] '{col}' 컬럼이 new_df에 없습니다. 빈 컬럼 추가.")
                new_df[col] = ''
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 모든 데이터를 신규로 처리
        new_df['update_date'] = current_time
        new_df['status'] = 'new'
        
        return new_df
            
    except Exception as e:
        print(f"[ERROR] update_job_data 예외: {e}")
        import traceback
        traceback.print_exc()
        return new_df

def main():
    parser = argparse.ArgumentParser(description='Process job data from crawled files')
    parser.add_argument('--military-basic', required=True, help='Path to military jobs basic CSV file')
    parser.add_argument('--military-detail', required=True, help='Path to military jobs detail CSV file')
    parser.add_argument('--rnd-basic', required=True, help='Path to RND jobs basic CSV file')
    parser.add_argument('--rnd-detail', required=True, help='Path to RND jobs detail CSV file')
    parser.add_argument('--output', required=True, help='Path to output processed CSV file')
    
    args = parser.parse_args()
    
    all_dataframes = []
    
    # 군무원 데이터 처리
    try:
        military_df = process_military_jobs(args.military_basic, args.military_detail)
        if not military_df.empty:
            all_dataframes.append(military_df)
            print(f"[INFO] 군무원 데이터 처리 완료: {len(military_df)} rows")
    except Exception as e:
        print(f"[ERROR] 군무원 데이터 처리 실패: {e}")
    
    # RND 데이터 처리
    try:
        rnd_df = process_rnd_jobs(args.rnd_basic, args.rnd_detail)
        if not rnd_df.empty:
            all_dataframes.append(rnd_df)
            print(f"[INFO] RND 데이터 처리 완료: {len(rnd_df)} rows")
    except Exception as e:
        print(f"[ERROR] RND 데이터 처리 실패: {e}")
    
    # 데이터가 하나도 없는 경우
    if not all_dataframes:
        print("[ERROR] 처리할 데이터가 없습니다.")
        return
    
    # 데이터 결합
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    print(f"[INFO] 전체 데이터 합계: {len(combined_df)} rows")
    
    # 날짜 형식 변환 - 이미 normalize_date_format으로 처리되어 표준 형식이므로 직접 변환
    for date_col in ['registration_date', 'deadline']:
        if date_col in combined_df.columns:
            print(f"[DEBUG] {date_col} 변환 전 샘플:", combined_df[date_col].head().tolist())
            print(f"[DEBUG] {date_col} 변환 전 데이터 타입:", combined_df[date_col].dtype)
            
            # None 값을 NaT로 변환하고, 유효한 날짜 문자열만 datetime으로 변환
            combined_df[date_col] = pd.to_datetime(combined_df[date_col], errors='coerce')
            print(f"[DEBUG] {date_col} 변환 후 샘플 (처음 5개):", combined_df[date_col].head().tolist())
            print(f"[DEBUG] {date_col} null 개수:", combined_df[date_col].isnull().sum())
    
    # 업데이트 처리
    try:
        final_df = update_job_data(combined_df)
    except Exception as e:
        print(f"[ERROR] update_job_data 처리 실패: {e}")
        final_df = combined_df
    
    # 파일 저장
    try:
        if not final_df.empty:
            final_df.to_csv(args.output, index=False, encoding='utf-8-sig')
            print(f"[INFO] 데이터 저장 완료: '{args.output}'")
            
            # 상태 통계 출력
            if 'status' in final_df.columns:
                status_counts = final_df['status'].value_counts()
                print("\n[INFO] Update Statistics:")
                for status, count in status_counts.items():
                    print(f"  {status}: {count} entries")
        else:
            print("[ERROR] 저장할 데이터가 없습니다.")
    except Exception as e:
        print(f"[ERROR] 파일 저장 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()