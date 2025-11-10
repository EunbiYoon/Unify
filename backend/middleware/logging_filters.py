# backend/logging_filters.py
import logging
from backend.middleware.thread_local import get_current_user

class UserFilter(logging.Filter):
    def filter(self, record):
        user = get_current_user()
        record.user = getattr(user, "username", "anonymous")
        return True