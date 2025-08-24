import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # ✅ Reference accounts.User instead of redefining User
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallets"
    )
    created_at = models.DateTimeField(default=timezone.now)


class WalletBalance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="balances")
    currency = models.CharField(max_length=10)  # 'USDx','EURx','cNGN','cXAF'
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        unique_together = ("wallet", "currency")


class Transaction(models.Model):
    TYPE_CHOICES = [
        ("DEPOSIT", "DEPOSIT"),
        ("SWAP", "SWAP"),
        ("TRANSFER_OUT", "TRANSFER_OUT"),
        ("TRANSFER_IN", "TRANSFER_IN"),
        ("AUTO_SWAP", "AUTO_SWAP"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="transactions"
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    from_currency = models.CharField(max_length=10, null=True, blank=True)
    to_currency = models.CharField(max_length=10, null=True, blank=True)
    from_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    to_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    rate = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)  
    counterparty_wallet = models.UUIDField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)


class RateCache(models.Model):
    id = models.AutoField(primary_key=True)
    base = models.CharField(max_length=10)   # fiat (USD, NGN, XAF, EUR)
    quote = models.CharField(max_length=10)
    rate = models.DecimalField(max_digits=20, decimal_places=8)
    fetched_at = models.DateTimeField(default=timezone.now)


class AuditLog(models.Model):  # bonus compliance log
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    ip = models.CharField(max_length=64, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    method = models.CharField(max_length=8, null=True, blank=True)
    path = models.CharField(max_length=256, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)


class IdempotencyRecord(models.Model):
    """
    Records an idempotency key per (path, key) to prevent duplicate processing.
    """
    id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=64, db_index=True)
    path = models.CharField(max_length=256, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
