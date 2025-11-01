from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from .models import TeamPrediction, TeamPredictionHistory

User = get_user_model()

def get_default_user():
    return User.objects.order_by("id").first()

def serialize_dict(data: dict):
    """datetime 등 JSON 직렬화 불가능한 값 변환"""
    from datetime import datetime, date
    import json

    def default(o):
        if isinstance(o, (datetime, date)):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        return str(o)

    return json.loads(json.dumps(data, default=default))

def get_changed_fields(old_data, new_data):
    changed = {}
    for field, old_value in old_data.items():
        new_value = new_data.get(field)
        if old_value != new_value:
            changed[field] = {"old": old_value, "new": new_value}
    return changed


# ✅ pre_save: 기존 값 백업
@receiver(pre_save, sender=TeamPrediction)
def backup_old_data(sender, instance, **kwargs):
    try:
        old_instance = sender.objects.get(pk=instance.pk)
        instance._old_data = serialize_dict(model_to_dict(old_instance))
    except sender.DoesNotExist:
        instance._old_data = None


# ✅ post_save: 비교 및 기록
@receiver(post_save, sender=TeamPrediction)
def save_team_prediction_history(sender, instance, created, **kwargs):
    request_user = getattr(instance, "_request_user", None) or get_default_user()

    if created:
        TeamPredictionHistory.objects.create(
            team_prediction=instance,
            action="created",
            changed_at=now(),
            new_snapshot=serialize_dict(model_to_dict(instance)),
            changed_by=request_user
        )
    else:
        old_data = getattr(instance, "_old_data", {})
        new_data = serialize_dict(model_to_dict(instance))

        changed_fields = get_changed_fields(old_data, new_data)

        if changed_fields:
            TeamPredictionHistory.objects.create(
                team_prediction=instance,
                action="updated",
                changed_at=now(),
                previous_snapshot=old_data,
                new_snapshot=new_data,
                changed_fields=changed_fields,
                changed_by=request_user
            )


# ✅ pre_delete: 삭제 기록
@receiver(pre_delete, sender=TeamPrediction)
def delete_team_prediction_history(sender, instance, **kwargs):
    request_user = getattr(instance, "_request_user", None) or get_default_user()

    TeamPredictionHistory.objects.create(
        team_prediction=None,
        action="deleted",
        changed_at=now(),
        previous_snapshot=serialize_dict(model_to_dict(instance)),
        changed_by=request_user
    )
