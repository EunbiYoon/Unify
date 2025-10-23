# Python 이미지를 사용 (최신 안정 버전)
FROM python:3.10-slim

# 작업 디렉터리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 라이브러리 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 의존성 복사 및 설치 (가상 환경 사용)
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=system.settings
ENV PATH="/opt/venv/bin:$PATH"

# 데이터베이스 마이그레이션 및 static 파일 수집 (필요시)
RUN . /opt/venv/bin/activate && python manage.py collectstatic --noinput
# ⛔️ 빌드 타임 migrate 제거
# RUN . /opt/venv/bin/activate && python manage.py migrate

EXPOSE 8000

# 컨테이너 시작 시 migrate 실행 후 gunicorn 시작
CMD ["/bin/sh", "-c", ". /opt/venv/bin/activate && python manage.py migrate --noinput && exec gunicorn system.wsgi:application --bind 0.0.0.0:8000"]