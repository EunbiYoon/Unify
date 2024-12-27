from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

# Create your models here.
class Team(models.Model):
    team_name=models.CharField(max_length=50)
    team_manager=models.CharField(max_length=50)
    manager_email=models.EmailField(
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9._%+-]+@lge\.com$',
                message='Email address must end with lge.com'
            )
    ])
    def __str__(self):
        return self.team_name

class CustomUser(AbstractUser):
    first_name=models.CharField(max_length=30)
    last_name=models.CharField(max_length=30)
    team_at=models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)
    email=models.EmailField(
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9._%+-]+@lge\.com$',
                message='Email address must end with lge.com'
            )
        ]
    )
    myday_credit=models.IntegerField(null=True, blank=True, default=1)
    def __str__(self):
        return self.username


