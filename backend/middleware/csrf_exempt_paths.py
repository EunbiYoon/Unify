from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import CsrfViewMiddleware

class CsrfExemptFinanceApiMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.csrf = CsrfViewMiddleware(get_response)

    def __call__(self, request):
        if request.path.startswith("/finance/api/"):
            request._dont_enforce_csrf_checks = True
        return self.csrf(request)
