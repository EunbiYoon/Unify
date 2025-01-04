# system/wsgi.py
import os
from django.core.wsgi import get_wsgi_application

# ✅ Flask 경로 수정 (절대경로 문제 해결)
from QualityAnalysis.flasktodo import create_app

# Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'system.settings')

# Django 및 Flask 애플리케이션 로드
django_application = get_wsgi_application()
flask_app = create_app()

# ✅ WSGI: 경로 분기
def application(environ, start_response):
    if environ.get('PATH_INFO').startswith('/qualityanalysisdashboard'):
        return flask_app(environ, start_response)
    return django_application(environ, start_response)
