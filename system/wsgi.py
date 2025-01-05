import os
from django.core.wsgi import get_wsgi_application

# Flask 앱 임포트 (QualityAnalysis & VideoTutorial)
from QualityAnalysis.flasktodo import create_app as create_quality_analysis_app
from VideoTutorial.flaskapp import create_app as create_video_tutorial_app

# Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'system.settings')

# Django 애플리케이션 로드
django_application = get_wsgi_application()

# Flask 애플리케이션 로드
quality_analysis_app = create_quality_analysis_app()
video_tutorial_app = create_video_tutorial_app()

# WSGI: 경로 분기 로직 (Flask + Django 통합)
def application(environ, start_response):
    path = environ.get('PATH_INFO', '')

    # QualityAnalysis Flask 앱 경로
    if path.startswith('/qualityanalysisdashboard'):
        return quality_analysis_app(environ, start_response)
    
    # VideoTutorial Flask 앱 경로
    elif path.startswith('/lgsupportvideotutorial'):
        return video_tutorial_app(environ, start_response)
    
    # Django 기본 애플리케이션 (루트 경로)
    return django_application(environ, start_response)
