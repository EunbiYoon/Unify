####################### RUN Flask ###############################
from flasktodo import create_app
app = create_app()

####################### RUN Django ###############################
# import flasktodo
# import os
# from django.core.wsgi import get_wsgi_application
# from flasktodo import create_app  # Flask 애플리케이션 임포트

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'system.settings')

# django_application = get_wsgi_application()

# # WSGI에서 Flask를 통합 (경로 기반으로 나누기)
# def application(environ, start_response):
#     if environ.get('PATH_INFO').startswith('/qualityanalysisdashboard'):
#         return flasktodo(environ, start_response)
#     return django_application(environ, start_response)