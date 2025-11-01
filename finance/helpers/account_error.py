from ninja.errors import HttpError

def _login_error(request):
    if not request.user.is_authenticated:
        raise HttpError(401, "로그인이 필요합니다.")

def _superuser_error(request):
    if not request.user.is_superuser:
        raise HttpError(403, "관리자만 초기화할 수 있습니다.")