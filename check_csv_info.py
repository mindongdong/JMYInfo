import pandas as pd
import os
import glob

def analyze_csv_files(directory='crawling_results'):
    """
    지정된 디렉토리에서 CSV 파일들을 읽어서 컬럼 목록과 행 개수를 출력합니다.
    """
    # CSV 파일 찾기
    csv_files = glob.glob(os.path.join(directory, '*.csv'))
    
    if not csv_files:
        print(f"'{directory}' 디렉토리에서 CSV 파일을 찾을 수 없습니다.")
        return
    
    # 각 CSV 파일 분석
    for csv_file in csv_files:
        try:
            # CSV 파일 읽기
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            
            # 파일명 출력
            print(f"\n{'='*50}")
            print(f"파일명: {os.path.basename(csv_file)}")
            print(f"{'='*50}")
            
            # 컬럼 목록 출력
            print("\n[컬럼 목록]")
            for idx, column in enumerate(df.columns, 1):
                print(f"{idx}. {column}")
            
            # 행 개수 출력
            print(f"\n총 행 개수: {len(df):,}개")
            
        except Exception as e:
            print(f"\n파일 '{os.path.basename(csv_file)}' 처리 중 오류 발생: {e}")

if __name__ == "__main__":
    analyze_csv_files() 