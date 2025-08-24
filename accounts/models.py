import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.username

class RatesCache(models.Model):
    from_currency = models.CharField(max_length=12, db_index=True)
    to_currency = models.CharField(max_length=12, db_index=True)
    rate = models.DecimalField(max_digits=20, decimal_places=8)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ("from_currency","to_currency")
