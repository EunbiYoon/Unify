from django.contrib.auth import get_user_model
from django.db.utils import OperationalError, ProgrammingError

# 로거
import logging
logger = logging.getLogger(__name__)


def create_default_admin():
    try:
        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "Ella135!")
            logger.info("✅ Default superuser 'admin' created")
        else:
            logger.info("ℹ️ Default superuser already exists.")
    except (OperationalError, ProgrammingError):
        # DB가 아직 초기화되지 않았을 경우 무시
        pass