from django.db import models

from django_multidatabase_queryset.models import MultiDataBaseModel
from django.contrib.auth import get_user_model


class UserAction(MultiDataBaseModel):
    DATABASES = ["default", "db_cold"]

    type = models.TextField(default="")
    detail = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.pk}: {self.type}"
