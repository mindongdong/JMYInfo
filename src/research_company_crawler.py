import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import os
import re
import logging

class ResearchCompanyCrawler:
    def __init__(self):
        self.base_url = "https://www.rndjob.or.kr/info/sp_rsch_comp.asp"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.company_data = []
        self.total_count = 0
        self.current_page_list = 1
        self.columns = []
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def get_page_content(self, url):
        """페이지 내용 가져오기"""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"페이지 접근 중 오류 발생: {e}")
            return None

    def get_total_count(self, soup):
        """전체 기업 수 가져오기"""
        mark_box = soup.find('div', class_='mark_box')
        if mark_box:
            sel_box = mark_box.find('div', class_='sel_box')
            if sel_box:
                count_text = sel_box.find('span').text.strip()
                return int(re.sub(r'[^0-9]', '', count_text))
        return 0

    def get_table_columns(self, soup):
        """테이블 컬럼명 가져오기"""
        board_list = soup.find('table', class_='board_list')
        if board_list:
            thead = board_list.find('thead')
            if thead:
                columns = [th.text.strip() for th in thead.find_all('th')]
                # 상세정보 URL 컬럼 추가
                columns.append('상세정보_URL')
                return columns
        return []

    def get_company_detail_info(self, company_id):
        """회사 상세 정보를 수집합니다."""
        detail_info = {}
        
        # 상세 정보 URL 생성
        detail_url = f"https://www.rndjob.or.kr/info/company_info.asp?jsno={company_id}"
        detail_info['상세정보_URL'] = detail_url
        
        # 상세 페이지 접근
        detail_soup = self.get_page_content(detail_url)
        if detail_soup:
            # 상세 정보 수집
            info_dls = detail_soup.find_all('dl', class_='info_dl')
            for dl in info_dls:
                for dt, dd in zip(dl.find_all('dt'), dl.find_all('dd')):
                    key = f"상세_{dt.text.strip()}"
                    value = dd.text.strip()
                    detail_info[key] = value
            
            logging.info(f"회사 ID {company_id}의 상세 정보 수집 완료")
        else:
            logging.error(f"회사 ID {company_id}의 상세 정보 수집 실패")
        
        return detail_info

    def get_company_rows(self, soup):
        """기업 정보 행 가져오기"""
        rows = []
        board_list = soup.find('table', class_='board_list')
        if board_list:
            tbody = board_list.find('tbody')
            if tbody:
                for tr in tbody.find_all('tr'):
                    row_data = {}
                    
                    # 기본 정보 수집
                    for idx, td in enumerate(tr.find_all('td')):
                        column_name = self.columns[idx] if idx < len(self.columns) else f'Column_{idx}'
                        
                        # span 안에 또 다른 span이 있는 경우
                        nested_spans = td.find_all('span', recursive=False)
                        if nested_spans:
                            cell_data = []
                            for span in nested_spans:
                                inner_spans = span.find_all('span')
                                if inner_spans:
                                    cell_data.extend([s.text.strip() for s in inner_spans])
                                else:
                                    cell_data.append(span.text.strip())
                            row_data[column_name] = ' '.join(cell_data)
                        else:
                            # 일반적인 span 처리
                            span = td.find('span')
                            row_data[column_name] = span.text.strip() if span else td.text.strip()
                    
                    # 상세 정보 링크 찾기 및 회사 ID 추출
                    apply_td = tr.find('td', class_='apply')
                    if apply_td:
                        a_tag = apply_td.find('a')
                        if a_tag and 'href' in a_tag.attrs:
                            href = a_tag['href']
                            # JavaScript 함수에서 회사 ID 추출
                            match = re.search(r"info_pop_open\('([^']+)'\)", href)
                            if match:
                                company_id = match.group(1)
                                # 상세 정보 수집
                                detail_info = self.get_company_detail_info(company_id)
                                # 기본 정보와 상세 정보 병합
                                row_data.update(detail_info)
                                
                                logging.info(f"회사 ID {company_id}의 정보 수집 완료")
                    
                    rows.append(row_data)
                    time.sleep(1)  # 서버 부하 방지
        
        return rows

    def get_pagination_info(self, soup):
        """페이지네이션 정보 가져오기"""
        pagination = soup.find('div', class_='pagination')
        if not pagination:
            return [], False

        pages = []
        has_next = False

        # 현재 페이지와 일반 페이지 번호 수집
        for a_tag in pagination.find_all('a'):
            if 'page-arrow r1' in a_tag.get('class', []):
                has_next = True  # 다음 페이지 목록 버튼이 있는지 확인
            elif 'active' in a_tag.get('class', []):
                current_page = int(a_tag.text.strip())
                pages.append(current_page)
            elif not a_tag.get('class'):
                pages.append(int(a_tag.text.strip()))

        return sorted(pages), has_next

    def get_all_pages(self):
        """전체 페이지 번호 생성"""
        total_pages = (self.total_count + 49) // 50  # 한 페이지당 50개 항목
        return range(1, total_pages + 1)

    def crawl(self):
        """크롤링 실행"""
        logging.info("크롤링 시작...")
        
        # 첫 페이지에서 전체 기업 수와 컬럼명 가져오기
        first_url = f"{self.base_url}?page=1&page_size=50&ODBY=C&BIZC=&BIZF="
        soup = self.get_page_content(first_url)
        if not soup:
            return

        self.total_count = self.get_total_count(soup)
        self.columns = self.get_table_columns(soup)
        
        logging.info(f"전체 기업 수: {self.total_count}")
        logging.info(f"기본 컬럼: {self.columns}")

        # 전체 페이지 번호 계산
        all_pages = self.get_all_pages()
        
        for page_num in all_pages:
            if len(self.company_data) >= self.total_count:
                break
                
            logging.info(f"페이지 {page_num} 크롤링 중... (현재 {len(self.company_data)}/{self.total_count})")
            page_url = f"{self.base_url}?page={page_num}&page_size=50&ODBY=C&BIZC=&BIZF="
            page_soup = self.get_page_content(page_url)
            
            if page_soup:
                rows = self.get_company_rows(page_soup)
                self.company_data.extend(rows)

            # 10페이지마다 추가 딜레이
            if page_num % 10 == 0:
                logging.info(f"=== 페이지 {page_num}까지 완료. 잠시 대기... ===")
                time.sleep(3)

        # 전체 기업 수에 맞게 데이터 자르기
        self.company_data = self.company_data[:self.total_count]
        
        logging.info(f"크롤링 완료! 총 {len(self.company_data)}개의 기업 정보를 수집했습니다.")

    def save_to_csv(self):
        """수집된 데이터 CSV 파일로 저장"""
        if not self.company_data:
            logging.warning("저장할 데이터가 없습니다.")
            return

        # 결과 저장할 디렉토리 생성
        output_dir = 'crawled_data'
        os.makedirs(output_dir, exist_ok=True)

        # 현재 시간을 파일명에 포함
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{output_dir}/research_companies_{current_time}.csv"

        # DataFrame 생성 및 저장
        df = pd.DataFrame(self.company_data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logging.info(f"크롤링 결과가 {filename}에 저장되었습니다.")
        logging.info(f"총 {len(self.company_data)}개 기업 정보 저장 완료")

if __name__ == "__main__":
    crawler = ResearchCompanyCrawler()
    crawler.crawl()
    crawler.save_to_csv() 