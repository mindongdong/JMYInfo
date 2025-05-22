# Python 3.9 slim 이미지 사용
FROM --platform=linux/arm64/v8 python:3.9-slim-buster

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Seoul
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    ca-certificates \
    xvfb \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxtst6 \
    libgtk-3-0 \
    libasound2 \
    libdbus-glib-1-2 \
    libnspr4 \
    libnss3 \
    fonts-nanum \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Chromium 및 ChromeDriver 설치 (ARM64용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriver 심볼릭 링크 생성 (ARM64용 경로 수정)
RUN if [ -f /usr/bin/chromedriver ]; then \
        ln -sf /usr/bin/chromedriver /usr/local/bin/chromedriver; \
    elif [ -f /usr/lib/chromium-browser/chromedriver ]; then \
        ln -sf /usr/lib/chromium-browser/chromedriver /usr/local/bin/chromedriver; \
    elif [ -f /usr/lib/chromium/chromedriver ]; then \
        ln -sf /usr/lib/chromium/chromedriver /usr/local/bin/chromedriver; \
    else \
        echo "Chromedriver not found in expected locations" && exit 1; \
    fi

# 버전 확인 (빌드 로그용)
RUN chromium --version && chromedriver --version

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY src/ ./src/
COPY main.py .

# 데이터 디렉토리 생성
RUN mkdir -p /app/crawled_data

# 실행 명령
CMD ["python", "main.py"] 