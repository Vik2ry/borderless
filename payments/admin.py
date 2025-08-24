from django.contrib import admin
from .models import Wallet, WalletBalance, Transaction, RateCache, AuditLog, IdempotencyRecord
from django.contrib.auth import get_user_model

User = get_user_model()  # ✅ now uses accounts.User

admin.site.register(User)
admin.site.register(Wallet)
admin.site.register(WalletBalance)
admin.site.register(Transaction)
admin.site.register(RateCache)
admin.site.register(AuditLog)
admin.site.register(IdempotencyRecord)
