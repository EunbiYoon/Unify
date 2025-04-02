import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "QualityAnalysis"))
sys.path.append(os.path.join(BASE_DIR, "VideoTutorial"))

from django.core.wsgi import get_wsgi_application
from QualityAnalysis.flasktodo import create_app as create_quality_analysis_app
from VideoTutorial.flaskapp import create_app as create_video_tutorial_app

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'system.settings')

django_application = get_wsgi_application()
quality_analysis_app = create_quality_analysis_app()
video_tutorial_app = create_video_tutorial_app()

def application(environ, start_response):
    path = environ.get('PATH_INFO', '')
    if path.startswith('/qualityanalysisdashboard'):
        return quality_analysis_app(environ, start_response)
    elif path.startswith('/lgsupportvideotutorial'):
        return video_tutorial_app(environ, start_response)
    return django_application(environ, start_response)
