# JMYInfo - 전문연구요원 채용정보 수집 시스템

## 프로젝트 개요

JMYInfo는 전문연구요원 채용 정보를 자동으로 수집하고 분석하는 통합 시스템입니다. 병무청과 연구개발특구의 채용 정보를 실시간으로 수집하여, 취업 준비생과 연구원들이 효율적으로 채용 정보를 파악할 수 있도록 도와줍니다.

### 주요 기능

1. **전문연구요원 채용정보 수집**
   - 병무청 전문연구요원 채용공고 실시간 수집
   - 연구개발특구 채용공고 자동 수집
   - 기업 상세 정보 및 채용 조건 수집

2. **통합 데이터 관리**
   - 기본 정보 (업체명, 채용제목, 등록일, 마감일)
   - 상세 정보 (요원형태, 학력, 경력, 근무지역)
   - 채용 조건 (자격요건, 우대사항, 담당업무)

3. **데이터 정제 및 분석**
   - 중복 데이터 자동 제거
   - 날짜 형식 표준화
   - 키워드 기반 채용 정보 분류
   - 데이터 품질 검증

4. **사용자 친화적 데이터 제공**
   - CSV 형식의 구조화된 데이터 제공
   - Docker 기반 쉬운 실행 환경
   - 자동화된 데이터 업데이트

# 프로젝트 실행 가이드 (Docker 기반)

## 1. Docker로 전체 프로젝트 실행하기

### 1) 도커 이미지 빌드

```bash
docker build -t jmyinfo-crawling-bot .
```

- 현재 디렉토리(`Dockerfile`이 위치한 곳)에서 위 명령어를 실행하세요.
- `jmyinfo-crawling-bot`은 원하는 이미지 이름으로 변경할 수 있습니다.

### 2) 도커 컨테이너 실행

```bash
docker run --rm -it -v $(pwd)/crawled_data:/app/crawled_data jmyinfo-crawling-bot
```

- 컨테이너가 실행되며, `/app/crawled_data` 폴더가 호스트의 `crawled_data`와 연결됩니다.
- 크롤링 결과 등 데이터가 컨테이너 종료 후에도 호스트에 남습니다.
- 필요에 따라 `-it` 옵션은 생략할 수 있습니다.

### 3) 주요 참고사항

- ARM64(M1/M2 등) 환경에서 정상 동작하도록 Dockerfile이 작성되어 있습니다.
- 컨테이너 내에서 `main.py`가 자동 실행됩니다.
- 크롤링 결과는 `/app/crawled_data`(호스트의 `crawled_data`)에 저장됩니다.
- 추가 파이썬 스크립트 실행이 필요하다면, 컨테이너 내에서 직접 명령어를 실행하거나 Dockerfile/CMD를 수정하세요.

---

# 크롤링/데이터 처리 스크립트 정리

## 1. military_job_crawler.py

- **크롤링 대상 사이트**
  - [병무청 전문연구요원 채용공고](https://work.mma.go.kr/caisBYIS/search/cygonggogeomsaek.do)
- **주요 기능**
  - Selenium 기반 동적 페이지 크롤링
  - WebDriver 풀을 통한 병렬 처리
  - 자동 재시도 메커니즘 (최대 5회)
  - 상세 정보 수집을 위한 멀티스레딩
- **수집 데이터**
  - 기본 정보: 업체명, 채용제목, 작성일, 마감일
  - 상세 정보: 요원형태, 최종학력, 자격요원, 주소, 담당업무, 비고
- **기술적 특징**
  - 헤드리스 Chrome 브라우저 사용
  - 이미지/플러그인 비활성화로 성능 최적화
  - 자동화된 에러 처리 및 로깅
  - 데이터 품질 검증

## 2. rndjob_job_crawler.py

- **크롤링 대상 사이트**
  - [R&D Job 연구개발특구 채용공고](https://www.rndjob.or.kr/info/sp_rsch.asp)
- **주요 기능**
  - BeautifulSoup4 기반 정적 페이지 크롤링
  - Selenium을 활용한 동적 콘텐츠 처리
  - 회사 상세정보 팝업 처리
  - 페이지네이션 자동 처리
- **수집 데이터**
  - 기본 정보: 기업명, 공고명, 등록일, 마감일
  - 상세 정보: 고용형태, 학력, 경력, 회사 주소, 모집 분야, 담당업무
  - 회사 정보: 기업 개요, 주요 사업, 인력 현황
- **기술적 특징**
  - 크로스 플랫폼 지원 (Windows/macOS/Linux)
  - 자동 ChromeDriver 경로 탐색
  - 멀티 윈도우 처리
  - 데이터 정규화 및 검증

## 3. process_job_data.py

- **기능 목적**
  - 크롤링된 데이터의 통합 및 전처리
  - 데이터 품질 향상 및 표준화
- **주요 기능**
  - CSV 파일 유효성 검사
  - 날짜 형식 표준화 (YYYY-MM-DD)
  - 중복 데이터 제거
  - 키워드 기반 데이터 분류
- **데이터 처리**
  - 기본/상세 정보 병합
  - 컬럼명 표준화
  - 누락 데이터 처리
  - 데이터 검증 및 로깅

## 4. Jupyter Notebooks

- **military.ipynb**
  - 병무청 데이터 분석 및 시각화
  - 채용 트렌드 분석
  - 데이터 품질 검증

- **rndjob.ipynb**
  - R&D Job 데이터 분석
  - 기업 정보 분석
  - 채용 패턴 분석

- **process_job.ipynb**
  - 통합 데이터 분석
  - 데이터 품질 개선
  - 분석 결과 시각화

---

# requirements.txt

아래는 위 스크립트들이 정상 동작하기 위해 필요한 주요 파이썬 패키지 목록입니다.

```txt
requests
beautifulsoup4
pandas
selenium
webdriver-manager
jupyter
matplotlib
seaborn
```

> **참고:**
>
> - `selenium` 및 `webdriver-manager`는 동적 페이지 크롤링에 필요합니다.
> - `jupyter`, `matplotlib`, `seaborn`은 데이터 분석 및 시각화에 사용됩니다.
> - `logging`, `os`, `time`, `datetime`, `re` 등은 파이썬 표준 라이브러리이므로 별도 설치가 필요 없습니다.
