import os
import sys

# 프로젝트 루트 기준 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "quality"))
sys.path.append(os.path.join(BASE_DIR, "lgsupport"))

from django.core.wsgi import get_wsgi_application

# Flask 앱 import
from quality.flasktodo import create_app as create_quality_analysis_app
from lgsupport.flaskapp import create_app as create_video_tutorial_app

# Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Django 앱 생성
django_application = get_wsgi_application()

# Flask 앱 생성
quality_analysis_app = create_quality_analysis_app()
video_tutorial_app = create_video_tutorial_app()

# 경로 기반 WSGI 라우팅
def application(environ, start_response):
    path = environ.get('PATH_INFO', '')
    if path.startswith('/quality/dashboard'):
        return quality_analysis_app(environ, start_response)
    elif path.startswith('/lgsupport/video'):
        return video_tutorial_app(environ, start_response)
    return django_application(environ, start_response)
