from django.contrib import admin
from .models import User, Wallet, WalletBalance, Transaction, RateCache, AuditLog, IdempotencyRecord

admin.site.register(User)
admin.site.register(Wallet)
admin.site.register(WalletBalance)
admin.site.register(Transaction)
admin.site.register(RateCache)
admin.site.register(AuditLog)
admin.site.register(IdempotencyRecord)
