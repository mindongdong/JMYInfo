import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from concurrent.futures import ThreadPoolExecutor
import logging

class MilitaryJobCrawler:
    def __init__(self):
        self.base_url = "https://work.mma.go.kr/caisBYIS/search/cygonggogeomsaek.do"
        self.driver = None
        self.job_data = []
        self.total_count = 0
        self.detail_info = []
        self.wait = None
        self.detail_driver_pool = []  # WebDriver 풀
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def create_driver(self):
        """WebDriver 인스턴스 생성"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.page_load_strategy = 'eager'
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,
                'plugins': 2,
                'javascript': 1
            }
        }
        options.add_experimental_option('prefs', prefs)
        
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def initialize_detail_drivers(self, count=2):
        """상세 정보 수집용 WebDriver 풀 초기화"""
        for _ in range(count):
            try:
                driver = self.create_driver()
                self.detail_driver_pool.append(driver)
                time.sleep(1)  # 드라이버 생성 간 간격
            except Exception as e:
                logging.error(f"WebDriver 초기화 실패: {e}")

    def get_available_driver(self):
        """사용 가능한 WebDriver 반환"""
        if not self.detail_driver_pool:
            self.initialize_detail_drivers()
        return self.detail_driver_pool[0] if self.detail_driver_pool else None

    def setup_driver(self):
        """Selenium WebDriver 설정"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # 성능 최적화를 위한 설정
        options.page_load_strategy = 'eager'
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,  # 이미지 로딩 비활성화
                'plugins': 2,  # 플러그인 비활성화
                'javascript': 1  # JavaScript는 필요하므로 활성화
            }
        }
        options.add_experimental_option('prefs', prefs)
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def wait_and_find_element(self, by, value, timeout=10):
        """요소를 찾을 때까지 대기하고 찾기"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            logging.warning(f"요소를 찾을 수 없습니다: {value}")
            return None

    def find_service_type_select(self):
        """복무형태 선택 요소 찾기"""
        try:
            table = self.wait_and_find_element(By.CLASS_NAME, 'table_row')
            if not table:
                return None

            rows = table.find_elements(By.TAG_NAME, 'tr')
            for row in rows:
                try:
                    th = row.find_element(By.TAG_NAME, 'th')
                    label = th.find_element(By.TAG_NAME, 'label')
                    if '복무형태' in label.text:
                        td = row.find_element(By.TAG_NAME, 'td')
                        return td.find_element(By.TAG_NAME, 'select')
                except NoSuchElementException:
                    continue
            return None
        except Exception as e:
            logging.error(f"복무형태 선택 요소 찾는 중 오류: {e}")
            return None

    def search_research_positions(self):
        """전문연구요원 공고 검색 설정"""
        try:
            self.driver.get(self.base_url)
            time.sleep(2)

            service_type_select = self.find_service_type_select()
            if service_type_select:
                Select(service_type_select).select_by_value('2')
                logging.info("복무형태 선택 완료")
            else:
                logging.error("복무형태 선택 요소를 찾을 수 없습니다.")
                return False

            search_button = self.wait_and_find_element(By.CSS_SELECTOR, 'span.icon_search a')
            if search_button:
                search_button.click()
                time.sleep(2)
                return True
            return False

        except Exception as e:
            logging.error(f"검색 설정 중 오류 발생: {e}")
            return False

    def get_total_count(self):
        """총 공고 수 가져오기"""
        try:
            topics_text = self.wait_and_find_element(By.CLASS_NAME, 'topics').text
            count_match = re.search(r'총\s+게시물\s*:\s*(\d+)건', topics_text)
            if count_match:
                self.total_count = int(count_match.group(1))
                logging.info(f"총 공고 수: {self.total_count}")
                return True
        except Exception as e:
            logging.error(f"총 공고 수 가져오기 실패: {e}")
        return False

    def get_job_list(self):
        """채용공고 목록 가져오기"""
        try:
            table = self.wait_and_find_element(By.CLASS_NAME, 'brd_list_n')
            headers = [th.text.strip() for th in table.find_elements(By.CSS_SELECTOR, 'thead th')]
            headers.append('상세정보_URL')
            
            rows = []
            for tr in table.find_elements(By.CSS_SELECTOR, 'tbody tr'):
                row_data = [cell.text.strip() for cell in tr.find_elements(By.CSS_SELECTOR, 'th, td')]
                url_cell = tr.find_element(By.CSS_SELECTOR, 'td.title a')
                row_data.append(url_cell.get_attribute('href'))
                rows.append(row_data)
            
            return headers, rows
        except Exception as e:
            logging.error(f"채용공고 목록 가져오기 실패: {e}")
            return None, None

    def get_job_detail(self, url):
        """채용공고 상세 정보 가져오기"""
        max_retries = 5  # 재시도 횟수 증가
        retry_delay = 5  # 대기 시간 증가
        
        for attempt in range(max_retries):
            try:
                logging.info(f"상세 정보 수집 시작 - URL: {url} (시도: {attempt + 1}/{max_retries})")
                self.driver.get(url)
                
                # 페이지 로딩 대기 시간 증가
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.step1'))
                )
                time.sleep(2)  # 추가 대기 시간
                
                detail_data = {
                    '상세정보_URL': url
                }
                
                sections = ['병역지정업체정보', '근무조건', '우대사항 및 복리후생']
                for section in sections:
                    logging.debug(f"'{section}' 섹션 정보 수집 중...")
                    h3_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.step1 h3')
                    for h3 in h3_elements:
                        if h3.text.strip() == section:
                            table = h3.find_element(By.XPATH, './following-sibling::table[1]')
                            rows = table.find_elements(By.CSS_SELECTOR, 'tbody tr')
                            for row in rows:
                                try:
                                    th = row.find_element(By.TAG_NAME, 'th').text.strip()
                                    td = row.find_element(By.TAG_NAME, 'td').text.strip()
                                    detail_data[th] = td
                                except NoSuchElementException:
                                    continue

                # 비고 정보 수집
                tables = self.driver.find_elements(By.CLASS_NAME, 'table_row')
                for table in tables:
                    try:
                        caption = table.find_element(By.TAG_NAME, 'caption')
                        if '비고' in caption.get_attribute('textContent').strip():
                            td_elements = table.find_elements(By.CSS_SELECTOR, 'tbody tr td')
                            bigo_text = ' '.join([td.text.strip() for td in td_elements if td.text.strip()])
                            if bigo_text:
                                detail_data['비고'] = bigo_text
                            break
                    except NoSuchElementException:
                        continue
                
                # 데이터 검증
                if len(detail_data) <= 1:  # URL만 있는 경우
                    raise Exception("상세 정보가 충분히 수집되지 않았습니다.")
                
                logging.info(f"상세 정보 수집 완료 - URL: {url}")
                return detail_data
                
            except Exception as e:
                logging.error(f"상세 정보 가져오기 실패 (URL: {url}, 시도: {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return {'상세정보_URL': url}

    def process_job_details(self, urls):
        """순차적으로 상세 정보 처리"""
        # 중복 URL 제거하되 순서 유지
        seen = set()
        unique_urls = [url for url in urls if not (url in seen or seen.add(url))]
        total_urls = len(unique_urls)
        
        logging.info(f"총 {total_urls}개의 상세 정보 수집 시작")
        results = []
        
        for idx, url in enumerate(unique_urls, 1):
            result = self.get_job_detail(url)
            results.append(result)
            logging.info(f"진행률: {idx}/{total_urls} ({(idx/total_urls*100):.1f}%)")
            time.sleep(3)  # 요청 간 간격
        
        # URL을 키로 사용하여 결과를 매핑
        url_to_detail = {result['상세정보_URL']: result for result in results}
        
        # 원래 URL 순서대로 결과 반환
        final_results = [url_to_detail[url] for url in urls]
        
        # 결과 검증
        successful_count = sum(1 for result in final_results if len(result) > 1)
        logging.info(f"상세 정보 수집 완료 (성공: {successful_count}/{len(final_results)})")
        
        return final_results

    def cleanup_drivers(self):
        """WebDriver 정리"""
        for driver in self.detail_driver_pool:
            try:
                driver.quit()
            except:
                pass
        self.detail_driver_pool.clear()

    def __del__(self):
        """소멸자에서 모든 WebDriver 정리"""
        self.cleanup_drivers()

    def get_pagination_info(self):
        """페이지네이션 정보 가져오기"""
        try:
            pagination = self.wait_and_find_element(By.CLASS_NAME, 'page_move_n')
            if not pagination:
                logging.warning("페이지네이션 요소를 찾을 수 없습니다.")
                return None, []

            # 현재 페이지 찾기
            current_page = None
            current_page_element = pagination.find_element(By.CSS_SELECTOR, 'a[href="#"] span')
            if current_page_element:
                current_page = current_page_element.text.strip()
                logging.info(f"현재 페이지: {current_page}")

            # 다른 페이지 링크들 찾기
            other_pages = []
            page_links = pagination.find_elements(By.TAG_NAME, 'a')
            for link in page_links:
                href = link.get_attribute('href')
                if href != '#':
                    span = link.find_element(By.TAG_NAME, 'span')
                    page_num = span.text.strip()
                    other_pages.append((page_num, link))
                    logging.debug(f"다른 페이지 발견: {page_num}")

            return current_page, other_pages

        except Exception as e:
            logging.error(f"페이지네이션 정보 가져오기 실패: {e}")
            return None, []

    def crawl(self):
        """크롤링 실행"""
        logging.info("크롤링 시작...")
        
        try:
            self.setup_driver()
            
            if not self.search_research_positions():
                return
            
            if not self.get_total_count():
                return
            
            processed_pages = set()
            processed_count = 0
            
            while len(self.job_data) < self.total_count:
                headers, rows = self.get_job_list()
                if not headers or not rows:
                    break
                
                self.job_data.extend(rows)
                processed_count += len(rows)
                logging.info(f"기본 정보 수집 진행률: {processed_count}/{self.total_count} ({(processed_count/self.total_count*100):.1f}%)")
                
                current_page, other_pages = self.get_pagination_info()
                if not current_page or not other_pages:
                    break
                
                processed_pages.add(current_page)
                
                next_page_found = False
                for page_num, link in other_pages:
                    if page_num not in processed_pages:
                        link.click()
                        time.sleep(2)
                        next_page_found = True
                        break
                
                if not next_page_found:
                    break
            
            # 상세 정보 수집 (순차적 처리)
            urls = [row[-1] for row in self.job_data]
            logging.info(f"총 {len(urls)}개의 상세 정보 수집 시작")
            self.detail_info = self.process_job_details(urls)
            
            # 데이터 저장
            self.save_to_csv(headers)
            
        except Exception as e:
            logging.error(f"크롤링 중 오류 발생: {e}")
        finally:
            if self.driver:
                self.driver.quit()

    def save_to_csv(self, headers):
        """수집된 데이터 CSV 파일로 저장"""
        if not self.job_data:
            logging.warning("저장할 데이터가 없습니다.")
            return

        try:
            output_dir = 'crawling_results'
            os.makedirs(output_dir, exist_ok=True)
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # URL 중복 체크
            urls = [row[-1] for row in self.job_data]
            duplicate_urls = [url for url in urls if urls.count(url) > 1]
            if duplicate_urls:
                logging.warning(f"기본 정보에서 중복된 URL이 {len(set(duplicate_urls))}개 발견되었습니다.")
            
            # 기본 정보 저장
            basic_filename = f"{output_dir}/military_jobs_basic_{current_time}.csv"
            df_basic = pd.DataFrame(self.job_data, columns=headers)
            df_basic.to_csv(basic_filename, index=False, encoding='utf-8-sig')
            logging.info(f"기본 정보 {len(df_basic)}개가 {basic_filename}에 저장되었습니다.")

            # 상세 정보 저장
            if self.detail_info:
                detail_filename = f"{output_dir}/military_jobs_detail_{current_time}.csv"
                df_detail = pd.DataFrame(self.detail_info)
                
                # URL을 기준으로 데이터 정렬
                df_basic_urls = df_basic['상세정보_URL'].tolist()
                df_detail['_sort_index'] = df_detail['상세정보_URL'].map(lambda x: df_basic_urls.index(x))
                df_detail = df_detail.sort_values('_sort_index').drop('_sort_index', axis=1)
                
                # 데이터 검증
                if len(df_basic) != len(df_detail):
                    logging.warning(f"기본 정보({len(df_basic)}개)와 상세 정보({len(df_detail)}개)의 데이터 수가 일치하지 않습니다.")
                
                mismatched_urls = set(df_basic['상세정보_URL']) - set(df_detail['상세정보_URL'])
                if mismatched_urls:
                    logging.warning(f"일치하지 않는 URL이 {len(mismatched_urls)}개 있습니다.")
                
                df_detail.to_csv(detail_filename, index=False, encoding='utf-8-sig')
                logging.info(f"상세 정보 {len(df_detail)}개가 {detail_filename}에 저장되었습니다.")

        except Exception as e:
            logging.error(f"데이터 저장 중 오류 발생: {e}")

if __name__ == "__main__":
    crawler = MilitaryJobCrawler()
    crawler.crawl() 