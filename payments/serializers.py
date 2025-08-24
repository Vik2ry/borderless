from decimal import Decimal
from rest_framework import serializers
# from .models import User, Wallet, WalletBalance, Transaction
from .services import CURRENCY_MAP, SUPPORTED
from django.contrib.auth import get_user_model

User = get_user_model()  # ✅ now uses accounts.User

class UserCreateSer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','handle']

class BalanceSer(serializers.Serializer):
    currency = serializers.CharField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=2)

class WalletDetailSer(serializers.Serializer):
    id = serializers.UUIDField()
    balances = BalanceSer(many=True)
    total_usd = serializers.DecimalField(max_digits=20, decimal_places=2)

class DepositSer(serializers.Serializer):
    currency = serializers.ChoiceField(choices=SUPPORTED)
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal('0.01'))

class SwapSer(serializers.Serializer):
    from_currency = serializers.ChoiceField(choices=SUPPORTED)
    to_currency = serializers.ChoiceField(choices=SUPPORTED)
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal('0.01'))
    preview = serializers.BooleanField(required=False, default=False)

class TransferSer(serializers.Serializer):
    from_wallet_id = serializers.UUIDField()
    to_wallet_id = serializers.UUIDField()
    currency = serializers.ChoiceField(choices=SUPPORTED)  # sender currency
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal('0.01'))
    target_currency = serializers.ChoiceField(choices=SUPPORTED, required=False)
    preview = serializers.BooleanField(required=False, default=False)
