import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import os
import logging
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class RndJobCrawler:
    def __init__(self):
        self.base_url = "https://www.rndjob.or.kr/info/sp_rsch.asp"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.basic_data = []  # 게시판 기본 정보
        self.detail_data = []  # 상세 페이지 정보
        self.driver = None
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def init_driver(self):
        """Selenium WebDriver 초기화"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 브라우저 창 숨기기
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
            chrome_options.page_load_strategy = 'eager'
            
            # Chrome 바이너리 위치 지정 (macOS)
            import os
            if os.path.exists('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'):
                chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            elif os.path.exists('/usr/bin/chromium'):
                chrome_options.binary_location = '/usr/bin/chromium'
            
            # 성능 최적화를 위한 설정
            prefs = {
                'profile.default_content_setting_values': {
                    'images': 2,  # 이미지 로딩 비활성화
                    'plugins': 2,  # 플러그인 비활성화
                    'javascript': 1  # JavaScript는 필요하므로 활성화
                }
            }
            chrome_options.add_experimental_option('prefs', prefs)
            
            # ChromeDriver 경로 설정
            service = None
            chromedriver_paths = [
                '/opt/homebrew/bin/chromedriver',  # macOS Homebrew
                '/usr/local/bin/chromedriver',     # 일반적인 설치 위치
                '/usr/bin/chromedriver'            # Linux 기본 위치
            ]
            
            for path in chromedriver_paths:
                if os.path.exists(path):
                    service = Service(path)
                    logging.info(f"ChromeDriver 발견: {path}")
                    break
            
            if service:
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # PATH에서 자동으로 찾기 시도
                logging.info("ChromeDriver 경로를 자동으로 찾는 중...")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.implicitly_wait(10)
            logging.info("WebDriver 초기화 완료")
            return True
        except Exception as e:
            logging.error(f"WebDriver 초기화 실패: {e}")
            logging.info("WebDriver 없이 크롤링을 계속합니다. (회사 상세정보 제외)")
            return False

    def close_driver(self):
        """WebDriver 종료"""
        if self.driver:
            self.driver.quit()
            logging.info("WebDriver 종료 완료")

    def get_company_detail_info_with_selenium(self, detail_url):
        """selenium을 사용하여 회사 상세정보 크롤링"""
        company_detail_info = {}
        
        try:
            self.driver.get(detail_url)
            
            # info_btn 클래스 찾기
            info_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "info_btn"))
            )
            
            # 버튼 클릭
            info_btn.click()
            
            # 팝업 창이 열릴 때까지 기다리기
            WebDriverWait(self.driver, 10).until(
                lambda driver: len(driver.window_handles) > 1
            )
            
            # 새로운 창으로 전환
            original_window = self.driver.current_window_handle
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    break
            
            # 페이지 로딩 대기
            time.sleep(2)
            
            # 회사 상세정보 크롤링 (research_company_crawler.py와 동일한 방식)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            info_dls = soup.find_all('dl', class_='info_dl')
            
            for dl in info_dls:
                dts = dl.find_all('dt')
                dds = dl.find_all('dd')
                for dt, dd in zip(dts, dds):
                    key = f"회사_상세_{dt.text.strip()}"
                    value = dd.text.strip()
                    company_detail_info[key] = value
            
            # 원래 창으로 돌아가기
            self.driver.close()  # 팝업 창 닫기
            self.driver.switch_to.window(original_window)
            
            logging.info(f"회사 상세정보 크롤링 완료: {len(company_detail_info)}개 필드")
            
        except TimeoutException:
            logging.warning(f"회사 상세정보 버튼을 찾을 수 없습니다: {detail_url}")
        except NoSuchElementException:
            logging.warning(f"회사 상세정보 요소를 찾을 수 없습니다: {detail_url}")
        except Exception as e:
            logging.error(f"회사 상세정보 크롤링 중 오류 발생: {e}")
            # 오류 발생 시 원래 창으로 돌아가기 시도
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
        
        return company_detail_info

    def get_page_content(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logging.error(f"페이지 접근 중 오류 발생: {e}")
            return None

    def get_pagination_info(self, soup):
        pagination = soup.find('div', class_='pagination')
        if not pagination:
            return []
        
        pages = []
        for a_tag in pagination.find_all('a'):
            if a_tag.get('class') and 'active' in a_tag.get('class'):
                pages.append(a_tag.text.strip())
            elif not a_tag.get('class'):
                pages.append(a_tag.text.strip())
        return [p for p in pages if p.isdigit()]

    def get_board_headers(self, soup):
        """게시판의 컬럼명을 가져옵니다."""
        headers = []
        board_table = soup.find('table', class_='board_list')
        if board_table:
            header_row = board_table.find('thead').find('tr')
            headers = [th.text.strip() for th in header_row.find_all('th')]
            headers.append('상세정보_URL')  # URL 컬럼 추가
        return headers

    def get_board_rows(self, soup):
        """게시판의 각 행 데이터를 가져옵니다."""
        rows = []
        board_table = soup.find('table', class_='board_list')
        if board_table:
            # 헤더에서 기업명 컬럼의 인덱스 찾기
            headers = self.get_board_headers(soup)
            company_col_index = -1
            for i, header in enumerate(headers):
                if '기업명' in header or '회사명' in header or '업체명' in header:
                    company_col_index = i
                    break
            
            for tr in board_table.find('tbody').find_all('tr'):
                row_data = []
                # 일반 td 셀들의 텍스트 수집
                tds = tr.find_all('td')
                for idx, td in enumerate(tds):
                    # 기업명 컬럼인 경우 class="comp_name"인 p 태그의 텍스트 우선 추출
                    if idx == company_col_index:
                        comp_name_p = td.find('p', class_='comp_name')
                        if comp_name_p:
                            row_data.append(comp_name_p.text.strip())
                        else:
                            # comp_name 클래스가 없으면 기존 로직 사용
                            row_data.append(td.text.strip())
                    # class="num"인 td의 경우 div 태그 내부의 텍스트도 수집
                    elif td.get('class') and 'num' in td.get('class'):
                        div_tag = td.find('div')
                        if div_tag:
                            # div 내부의 모든 텍스트를 수집
                            text_content = ' '.join([text.strip() for text in div_tag.stripped_strings])
                            # 날짜 형식 변환 (YYYY.MM.DDYYYY.MM.DD -> YYYY-MM-DD/YYYY-MM-DD)
                            if len(text_content) == 20 and text_content.count('.') == 4:
                                date1 = text_content[:10].replace('.', '-')
                                date2 = text_content[10:].replace('.', '-')
                                text_content = f"{date1}/{date2}"
                            row_data.append(text_content)
                        else:
                            row_data.append(td.text.strip())
                    else:
                        # p 태그가 있으면 p 태그의 텍스트를, 없으면 td의 텍스트를 사용
                        p_tag = td.find('p')
                        # span 태그들이 있으면 span 태그들의 텍스트를, 없으면 td의 텍스트를 사용
                        span_tags = td.find_all('span')
                        if span_tags:
                            row_data.append(' '.join([span.text.strip() for span in span_tags]))
                        elif p_tag:
                            row_data.append(p_tag.text.strip())
                        else:
                            row_data.append(td.text.strip())
                
                # URL 추가
                tit_td = tr.find('td', class_='tit')
                if tit_td:
                    dotdot_span = tit_td.find('span', class_='dotdot')
                    if dotdot_span and dotdot_span.find('a'):
                        url = dotdot_span.find('a').get('href', '')
                        full_url = f"https://www.rndjob.or.kr{url}"
                        row_data.append(full_url)
                    else:
                        row_data.append('')
                else:
                    row_data.append('')
                
                rows.append(row_data)
        return rows

    def parse_job_detail(self, soup, detail_url=None):
        """상세 페이지의 정보를 파싱합니다."""
        job_info = {}
        
        # 회사 로고 및 기본 정보
        r_box = soup.find('div', class_='r_box')
        if r_box:
            # 회사 로고
            logo_box = r_box.find('div', class_='logo_box')
            if logo_box and logo_box.find('img'):
                job_info['회사_로고_URL'] = logo_box.find('img').get('src', '')
            
            # 회사 정보 박스
            company_box = r_box.find('div', class_='company_box')
            if company_box:
                # 회사 이름
                name_p = company_box.find('p', class_='name')
                if name_p:
                    job_info['회사명'] = name_p.text.strip()
                
                # 회사 종류
                category_ul = company_box.find('ul', class_='category')
                if category_ul:
                    job_info['회사_종류'] = [li.text.strip() for li in category_ul.find_all('li')]
                
                # 회사 상세 정보
                company_info_list = company_box.find('dl', class_='info_list')
                if company_info_list:
                    for dt in company_info_list.find_all('dt'):
                        key = f"회사_{dt.text.strip()}"
                        dd = dt.find_next_sibling('dd')
                        value = dd.text.strip() if dd else ""
                        job_info[key] = value
        
        # Selenium을 사용하여 회사 상세정보 크롤링 (info_btn 클릭)
        if detail_url and self.driver:
            company_detail_info = self.get_company_detail_info_with_selenium(detail_url)
            job_info.update(company_detail_info)
        
        # 채용공고 기본 정보
        info_lists = soup.find_all('dl', class_='info_list')
        for info_list in info_lists:
            titles = info_list.find_all('dt')
            values = info_list.find_all('dd')
            for title, value in zip(titles, values):
                key = title.text.strip()
                val = value.find('span').text.strip() if value.find('span') else value.text.strip()
                job_info[key] = val

        # 모집 분야 및 인원 정보
        info_list2 = soup.find('ul', class_='info_list2')
        if info_list2:
            recruitment_info = []
            for li in info_list2.find_all('li'):
                recruitment_info.append(li.text.strip())
            job_info['모집_분야_및_인원'] = recruitment_info

        # 채용공고 상세 내용
        sub_each_divs = soup.find_all('div', class_='sub_each')
        for div in sub_each_divs:
            title = div.find('p', class_='sub_tit')
            if not title:
                continue
                
            title_text = title.text.strip()
            content = div.find('div', class_='vin_dtl')
            
            if content:
                # 일반 리스트 항목
                ul_content = content.find('ul')
                if ul_content:
                    items = [li.text.strip() for li in ul_content.find_all('li')]
                    job_info[title_text] = items
                
                # 복리후생 정보
                dl_content = content.find('dl', class_='img_dl')
                if dl_content:
                    welfare_items = {}
                    for dt, dd in zip(dl_content.find_all('dt'), dl_content.find_all('dd')):
                        welfare_title = dt.text.strip()
                        welfare_values = [p.text.strip() for p in dd.find_all('p')]
                        welfare_items[welfare_title] = welfare_values
                    job_info[title_text] = welfare_items

        return job_info

    def crawl(self, basic_filename=None, detail_filename=None, research_companies_path=None):
        """크롤링을 실행합니다."""
        logging.info("크롤링 시작...")
        
        # WebDriver 초기화
        if not self.init_driver():
            logging.error("WebDriver 초기화에 실패했습니다. 회사 상세정보 크롤링을 건너뜁니다.")
        
        try:
            soup = self.get_page_content(self.base_url)
            if not soup:
                return

            # 컬럼명 가져오기
            headers = self.get_board_headers(soup)
            if not headers:
                logging.error("게시판 헤더를 찾을 수 없습니다.")
                return

            pages = self.get_pagination_info(soup)
            total_pages = len(pages)
            logging.info(f"총 {total_pages}개의 페이지를 크롤링합니다.")

            for page_num in pages:
                logging.info(f"페이지 {page_num} 크롤링 중...")
                page_url = f"{self.base_url}?page={page_num}"
                page_soup = self.get_page_content(page_url)
                
                if not page_soup:
                    continue

                # 기본 정보 수집
                rows = self.get_board_rows(page_soup)
                self.basic_data.extend(rows)
                
                # 상세 정보 수집
                for row in rows:
                    detail_url = row[-1]  # URL은 마지막 컬럼
                    if detail_url:
                        detail_soup = self.get_page_content(detail_url)
                        if detail_soup:
                            detail_info = self.parse_job_detail(detail_soup, detail_url)
                            detail_info['상세정보_URL'] = detail_url  # URL을 키로 사용하여 나중에 매칭
                            self.detail_data.append(detail_info)
                            time.sleep(1)  # 서버 부하 방지

                time.sleep(2)  # 페이지 간 딜레이

            if basic_filename and detail_filename:
                self.save_to_csv(headers, basic_filename, detail_filename, research_companies_path)
        
        finally:
            # WebDriver 종료
            self.close_driver()

    def save_to_csv(self, headers, basic_filename, detail_filename, research_companies_path=None):
        """수집된 데이터를 CSV 파일로 저장합니다."""
        if not self.basic_data or not self.detail_data:
            logging.warning("저장할 데이터가 없습니다.")
            return

        try:
            # 결과 저장할 디렉토리 생성
            output_dir = os.path.dirname(basic_filename)
            os.makedirs(output_dir, exist_ok=True)

            # 기본 정보 저장
            df_basic = pd.DataFrame(self.basic_data, columns=headers)

            # '등록일/마감일' 컬럼이 있으면 분리하여 추가
            if '등록일/마감일' in df_basic.columns:
                # '등록일/마감일' 값을 분리하여 새로운 컬럼 생성
                df_basic[['등록일', '마감일']] = df_basic['등록일/마감일'].str.split(' ', n=1, expand=True)
                # 컬럼 순서 조정: 등록일, 마감일을 기존 위치에 삽입
                insert_idx = headers.index('등록일/마감일')
                new_columns = list(df_basic.columns)
                # 등록일, 마감일을 기존 위치에 삽입
                for col in ['마감일', '등록일']:
                    new_columns.remove(col)
                new_columns[insert_idx:insert_idx] = ['등록일', '마감일']
                df_basic = df_basic[new_columns]

            df_basic.to_csv(basic_filename, index=False, encoding='utf-8-sig')
            logging.info(f"기본 정보가 {basic_filename}에 저장되었습니다.")

            # 상세 정보 저장
            df_detail = pd.DataFrame(self.detail_data)

            # research_companies.csv와 회사명 기준으로 주소 매칭
            if research_companies_path is not None and os.path.exists(research_companies_path):
                df_companies = pd.read_csv(research_companies_path)
                if '회사명' in df_companies.columns and '상세_주소' in df_companies.columns:
                    df_detail = pd.merge(
                        df_detail,
                        df_companies[['회사명', '상세_주소']],
                        on='회사명',
                        how='left',
                        suffixes=('', '_research')
                    )
                    # '상세_주소'를 '주소' 컬럼으로 이름 변경
                    df_detail.rename(columns={'상세_주소': '주소'}, inplace=True)

            df_detail.to_csv(detail_filename, index=False, encoding='utf-8-sig')
            logging.info(f"상세 정보가 {detail_filename}에 저장되었습니다.")

        except Exception as e:
            logging.error(f"데이터 저장 중 오류 발생: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='R&D Job Crawler')
    parser.add_argument('--basic-output', required=True, help='Output filename for basic job information')
    parser.add_argument('--detail-output', required=True, help='Output filename for detailed job information')
    parser.add_argument('--research-companies', required=False, help='Path to research_companies.csv')
    
    args = parser.parse_args()
    
    crawler = RndJobCrawler()
    crawler.crawl(
        basic_filename=args.basic_output,
        detail_filename=args.detail_output,
        research_companies_path=args.research_companies
    ) 