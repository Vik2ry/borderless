from django.core.management.base import BaseCommand
from payments.models import User, Wallet, WalletBalance
from payments.services import CURRENCY_MAP

class Command(BaseCommand):
    help = "Seed two demo users and their wallets"

    def handle(self, *args, **kwargs):
        u1, _ = User.objects.get_or_create(handle='ada@example.com')
        u2, _ = User.objects.get_or_create(handle='jean@example.com')
        w1, _ = Wallet.objects.get_or_create(user=u1)
        w2, _ = Wallet.objects.get_or_create(user=u2)
        for w in (w1, w2):
            for c in CURRENCY_MAP.keys():
                WalletBalance.objects.get_or_create(wallet=w, currency=c, defaults={'amount':0})
        self.stdout.write(self.style.SUCCESS(f"Seeded: {u1.handle} ({w1.id}), {u2.handle} ({w2.id})"))
