# 크롤링/데이터 처리 스크립트 정리

## 1. rndjob_job_crawler.py

- **크롤링 대상 사이트**  
  - [R&D Job (연구개발특구진흥재단)](https://www.rndjob.or.kr/info/sp_rsch.asp)
- **수집 데이터**  
  - 연구개발 관련 채용공고의 기본 정보(기업명, 공고명, 등록일/마감일 등) 및 상세 정보(회사 정보, 모집 분야, 근무환경, 자격요건, 우대사항 등)
- **주요 기능**
  - 게시판의 모든 페이지를 순회하며 채용공고 목록을 수집
  - 각 공고의 상세 페이지에 접근하여 추가 정보 파싱
  - 기본 정보와 상세 정보를 각각 CSV로 저장
  - 컬럼명 자동 추출 및 날짜 등 데이터 전처리
  - 서버 부하 방지를 위한 딜레이 적용 및 로깅

---

## 2. research_company_crawler.py

- **크롤링 대상 사이트**  
  - [R&D Job 연구개발특구 기업정보](https://www.rndjob.or.kr/info/sp_rsch_comp.asp)
- **수집 데이터**  
  - 연구개발특구 내 기업의 기본 정보(기업명, 업종, 주소 등) 및 상세 정보(기업 개요, 주요 사업, 인력 현황 등)
- **주요 기능**
  - 전체 기업 목록 페이지를 순회하며 기업 리스트 수집
  - 각 기업의 상세 정보 페이지에 접근하여 추가 정보 파싱
  - 기본 정보와 상세 정보를 병합하여 CSV로 저장
  - 전체 기업 수, 컬럼명 자동 추출, 서버 부하 방지 딜레이, 로깅

---

## 3. military_job_crawler.py

- **크롤링 대상 사이트**  
  - [병무청 전문연구요원 채용공고](https://work.mma.go.kr/caisBYIS/search/cygonggogeomsaek.do)
- **수집 데이터**  
  - 전문연구요원 채용공고의 기본 정보(업체명, 채용제목, 작성일, 마감일 등) 및 상세 정보(병역지정업체 정보, 근무조건, 우대사항, 비고 등)
- **주요 기능**
  - Selenium을 활용한 동적 페이지 크롤링 및 페이지네이션 처리
  - 각 공고의 상세 페이지 접근 및 정보 파싱
  - 기본 정보와 상세 정보를 각각 CSV로 저장
  - WebDriver 풀 관리, 중복 URL 처리, 데이터 정렬 및 검증, 로깅

---

## 4. process_job_data.py

- **기능 목적**  
  - 위 세 개의 크롤러가 수집한 CSV 데이터를 통합 및 전처리하여 최종 분석/활용 가능한 형태로 가공
- **주요 기능**
  - 각 크롤러의 기본/상세 CSV 파일을 읽어 병합
  - 주요 컬럼(회사명, 공고명, 등록일, 마감일, 자격요건, 지역, 담당업무, 키워드 등)만 추출 및 가공
  - 군/민간 구분(source_type) 추가
  - 최종 통합 데이터 CSV(`processed_job_data.csv`)로 저장

---

# requirements.txt

아래는 위 스크립트들이 정상 동작하기 위해 필요한 주요 파이썬 패키지 목록입니다.

```txt
requests
beautifulsoup4
pandas
selenium
webdriver-manager
```

> **참고:**  
> - `selenium` 및 `webdriver-manager`는 military_job_crawler.py에서만 필요합니다.  
> - `logging`, `os`, `time`, `datetime`, `re` 등은 파이썬 표준 라이브러리이므로 별도 설치가 필요 없습니다.

---

# 예시 디렉토리 구조

```
.
├── rndjob_job_crawler.py
├── research_company_crawler.py
├── military_job_crawler.py
├── process_job_data.py
├── requirements.txt
└── crawling_results/
    ├── rndjob_basic_*.csv
    ├── rndjob_detail_*.csv
    ├── research_companies_*.csv
    ├── military_jobs_basic_*.csv
    └── military_jobs_detail_*.csv
```