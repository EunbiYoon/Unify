from django.http import HttpResponse
from django.conf import settings
import os

def frontendView(request):
    # React 빌드된 index.html 파일 경로
    index_path = os.path.join(settings.BASE_DIR, 'static/react/index.html')
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("React build file not found. Run 'npm run build' and move files to 'static/react/'.", status=404)
