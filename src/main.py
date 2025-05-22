import logging
from datetime import datetime
import os
from military_job_crawler import MilitaryJobCrawler
from rndjob_job_crawler import RndJobCrawler

def main():
    # 로깅 설정
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("크롤링 프로세스 시작")
    
    # 출력 디렉토리 설정
    output_dir = '/app/crawled_data'
    os.makedirs(output_dir, exist_ok=True)
    
    # 현재 시간을 기준으로 파일명 생성
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # R&D Job 공고 크롤러 실행
    logger.info("=== R&D Job 공고 크롤러 실행 시작 ===")
    try:
        rndjob_crawler = RndJobCrawler()
        rndjob_basic_filename = f"{output_dir}/rndjob_basic_{current_time}.csv"
        rndjob_detail_filename = f"{output_dir}/rndjob_detail_{current_time}.csv"
        rndjob_crawler.crawl(rndjob_basic_filename, rndjob_detail_filename)
    except Exception as e:
        logger.warning(f"R&D Job 공고 크롤러 경고/에러: {e}")
        logger.error(f"R&D Job 공고 크롤러 실패로 인해 프로세스 중단")
        return
    
    # Military Job 공고 크롤러 실행
    logger.info("=== Military Job 공고 크롤러 실행 시작 ===")
    try:
        military_crawler = MilitaryJobCrawler()
        military_basic_filename = f"{output_dir}/military_jobs_basic_{current_time}.csv"
        military_detail_filename = f"{output_dir}/military_jobs_detail_{current_time}.csv"
        military_crawler.crawl(military_basic_filename, military_detail_filename)
    except Exception as e:
        logger.warning(f"Military Job 공고 크롤러 경고/에러: {e}")
        logger.error(f"Military Job 공고 크롤러 실패로 인해 프로세스 중단")
        return
    
    logger.info("크롤링 프로세스 완료")

if __name__ == "__main__":
    main() 