from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model

# 로거
import logging
logger = logging.getLogger(__name__)


@receiver(post_migrate)
def create_default_admin(sender, **kwargs):
    if sender.name != "account":  # ✅ account 앱에서만 실행
        return

    User = get_user_model()
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@example.com", "Ella135!")
        logger.info("✅ Default superuser 'admin' created")
    else:
        logger.info("ℹ️  Default superuser already exists.")