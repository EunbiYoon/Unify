# backend/middleware/thread_local.py
import threading
from django.utils.deprecation import MiddlewareMixin

_thread_locals = threading.local()

def get_current_user():
    return getattr(_thread_locals, "user", None)

class ThreadLocalMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _thread_locals.user = getattr(request, "user", None)