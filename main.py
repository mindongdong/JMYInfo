import os
import sys
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# 기본 디렉토리 설정
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'crawled_data'
DATA_DIR.mkdir(exist_ok=True)

# 현재 시간을 한 번만 생성하여 모든 파일에서 사용
CURRENT_TIME = datetime.now().strftime("%Y%m%d_%H%M%S")

# 스크립트 실행 순서 및 설정
SCRIPTS = [
    {
        'name': 'R&D Job 공고 크롤러',
        'script': 'src/rndjob_job_crawler.py',
        'output_files': [
            DATA_DIR / f'rndjob_basic_{CURRENT_TIME}.csv',
            DATA_DIR / f'rndjob_detail_{CURRENT_TIME}.csv'
        ]
    },
    {
        'name': '병무청 전문연구요원 공고 크롤러',
        'script': 'src/military_job_crawler.py',
        'output_files': [
            DATA_DIR / f'military_jobs_basic_{CURRENT_TIME}.csv',
            DATA_DIR / f'military_jobs_detail_{CURRENT_TIME}.csv'
        ]
    }
]

def run_script(script_info):
    """스크립트를 실행하고 결과를 확인합니다."""
    script_name = script_info['name']
    script_path = script_info['script']
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    logger.info(f"=== {script_name} 실행 시작 ===")
    
    try:
        # 명령어 구성
        cmd = [sys.executable, script_path]
        
        # 출력 파일 파라미터 추가
        if 'output_files' in script_info:
            cmd.extend([
                '--basic-output', str(script_info['output_files'][0]),
                '--detail-output', str(script_info['output_files'][1])
            ])
        
        # 추가 인자 파라미터 추가
        if 'args' in script_info:
            cmd.extend(script_info['args'])
        
        # 스크립트 실행
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        # 로그 파일에 기록
        run_log_path = DATA_DIR / 'run.log'
        error_log_path = DATA_DIR / 'error.log'
        sep = '\n' + ('='*40) + f"\n[{now_str}] {script_name} 실행 결과\n" + ('-'*40) + '\n'
        # 표준 출력 기록
        if result.stdout:
            with open(run_log_path, 'a', encoding='utf-8') as f:
                f.write(sep)
                f.write(result.stdout)
                f.write('\n')
        # 표준 에러 기록
        if result.stderr:
            with open(error_log_path, 'a', encoding='utf-8') as f:
                f.write(sep)
                f.write(result.stderr)
                f.write('\n')
        
        # 출력 로깅
        if result.stdout:
            logger.info(f"{script_name} 출력:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"{script_name} 경고/에러:\n{result.stderr}")
            
        # 출력 파일 확인
        if 'output_files' in script_info:
            for output_file in script_info['output_files']:
                if output_file.exists():
                    logger.info(f"출력 파일 생성됨: {output_file}")
                else:
                    logger.error(f"출력 파일이 생성되지 않음: {output_file}")
                    return False
                
        logger.info(f"=== {script_name} 실행 완료 ===")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"{script_name} 실행 실패 (종료 코드: {e.returncode})")
        run_log_path = DATA_DIR / 'run.log'
        error_log_path = DATA_DIR / 'error.log'
        sep = '\n' + ('='*40) + f"\n[{now_str}] {script_name} 실행 실패\n" + ('-'*40) + '\n'
        if e.stdout:
            with open(run_log_path, 'a', encoding='utf-8') as f:
                f.write(sep)
                f.write(e.stdout)
                f.write('\n')
            logger.error(f"표준 출력:\n{e.stdout}")
        if e.stderr:
            with open(error_log_path, 'a', encoding='utf-8') as f:
                f.write(sep)
                f.write(e.stderr)
                f.write('\n')
            logger.error(f"표준 에러:\n{e.stderr}")
        return False
    except Exception as e:
        logger.error(f"{script_name} 실행 중 예외 발생: {str(e)}")
        error_log_path = DATA_DIR / 'error.log'
        sep = '\n' + ('='*40) + f"\n[{now_str}] {script_name} 예외 발생\n" + ('-'*40) + '\n'
        with open(error_log_path, 'a', encoding='utf-8') as f:
            f.write(sep)
            f.write(str(e))
            f.write('\n')
        return False

def main():
    """메인 실행 함수"""
    logger.info("크롤링 프로세스 시작")
    
    # 각 스크립트 순차 실행
    for script_info in SCRIPTS:
        if not run_script(script_info):
            logger.error(f"{script_info['name']} 실패로 인해 프로세스 중단")
            sys.exit(1)
    
    # 데이터 처리 스크립트 실행
    process_script = {
        'name': '데이터 처리',
        'script': 'src/process_job_data.py',
        'output_files': [DATA_DIR / 'processed_job_data.csv'],
        'args': [
            '--military-basic', str(SCRIPTS[1]['output_files'][0]),
            '--military-detail', str(SCRIPTS[1]['output_files'][1]),
            '--rnd-basic', str(SCRIPTS[0]['output_files'][0]),
            '--rnd-detail', str(SCRIPTS[0]['output_files'][1]),
            '--output', str(DATA_DIR / 'processed_job_data.csv')
        ]
    }
    
    # 입력 파일 존재 여부 확인
    required_files = [
        ('Military Basic', SCRIPTS[1]['output_files'][0]),
        ('Military Detail', SCRIPTS[1]['output_files'][1]),
        ('RND Basic', SCRIPTS[0]['output_files'][0]),
        ('RND Detail', SCRIPTS[0]['output_files'][1])
    ]
    
    missing_files = []
    for file_type, file_path in required_files:
        if not file_path.exists():
            missing_files.append(f"{file_type}: {file_path}")
    
    if missing_files:
        logger.error("데이터 처리에 필요한 파일이 누락되었습니다:")
        for missing_file in missing_files:
            logger.error(f"- {missing_file}")
        logger.error("데이터 처리 실패")
        sys.exit(1)
    
    if not run_script(process_script):
        logger.error("데이터 처리 실패")
        sys.exit(1)
    
    logger.info("모든 프로세스가 성공적으로 완료되었습니다.")

if __name__ == "__main__":
    main() 