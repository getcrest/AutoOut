from django.db import models
from django.utils import timezone


class Dataset(models.Model):
    path = models.TextField(default="")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'datasets'
