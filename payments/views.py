from decimal import Decimal
from django.conf import settings
from django.db import transaction as dbtx
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Wallet, WalletBalance, Transaction, AuditLog
from .serializers import (
    UserCreateSer, WalletDetailSer, DepositSer, SwapSer, TransferSer
)
from .services import cross_rate, CURRENCY_MAP, to_usd, get_rate
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model

User = get_user_model()  # ✅ now uses accounts.User

@extend_schema(
    summary="Create a new user",
    description="Registers a user (email or phone handle) and creates their primary wallet.",
    responses={201: UserCreateSer},
)
@api_view(['POST'])
def create_user(request):
    ...

def _get_balance(wallet, currency):
    bal, _ = WalletBalance.objects.get_or_create(wallet=wallet, currency=currency, defaults={'amount':0})
    return bal

@api_view(['POST'])
def create_user(request):
    ser = UserCreateSer(data=request.data)
    ser.is_valid(raise_exception=True)
    user, _ = User.objects.get_or_create(handle=ser.validated_data['handle'])
    wallet, _ = Wallet.objects.get_or_create(user=user)
    for c in CURRENCY_MAP.keys():
        WalletBalance.objects.get_or_create(wallet=wallet, currency=c, defaults={'amount':0})
    return Response({'id': str(user.id), 'handle': user.handle, 'wallet_id': str(wallet.id)}, status=201)

@api_view(['POST'])
def create_wallet(request):
    user_id = request.data.get('user_id')
    user = get_object_or_404(User, id=user_id)
    wallet = Wallet.objects.create(user=user)
    for c in CURRENCY_MAP.keys():
        WalletBalance.objects.create(wallet=wallet, currency=c, amount=0)
    return Response({'id': str(wallet.id), 'user_id': str(user.id)}, status=201)

@api_view(['GET'])
def wallet_transactions(request, wallet_id):
    limit = int(request.GET.get('limit', 100))
    qs = Transaction.objects.filter(wallet_id=wallet_id).order_by('-created_at')[:limit]
    data = [{
        'id': str(t.id),
        'type': t.type,
        'from_currency': t.from_currency,
        'to_currency': t.to_currency,
        'from_amount': str(t.from_amount) if t.from_amount is not None else None,
        'to_amount': str(t.to_amount) if t.to_amount is not None else None,
        'rate': str(t.rate) if t.rate is not None else None,
        'counterparty_wallet_id': str(t.counterparty_wallet) if t.counterparty_wallet else None,
        'created_at': t.created_at.isoformat()
    } for t in qs]
    return Response(data)

@api_view(['POST'])
def transfer(request):
    ser = TransferSer(data=request.data); ser.is_valid(raise_exception=True)
    from_wallet = get_object_or_404(Wallet, id=ser.validated_data['from_wallet_id'])
    to_wallet   = get_object_or_404(Wallet, id=ser.validated_data['to_wallet_id'])
    currency    = ser.validated_data['currency']  # sender's currency
    amount      = ser.validated_data['amount']
    target_currency = ser.validated_data.get('target_currency', currency)  # receiver currency
    preview = ser.validated_data['preview']

    if target_currency != currency:
        to_amount, rate = cross_rate(amount, currency, target_currency)
        if preview:
            return Response({'preview': True, 'credited': str(to_amount.quantize(Decimal('0.01'))), 'rate': str(rate)})

        with dbtx.atomic():
            sender_bal = _get_balance(from_wallet, currency)
            if sender_bal.amount < amount:
                return Response({'detail':'Insufficient balance.'}, status=400)
            sender_bal.amount -= amount; sender_bal.save(update_fields=['amount'])
            recv_bal = _get_balance(to_wallet, target_currency)
            recv_bal.amount += to_amount; recv_bal.save(update_fields=['amount'])

            key = request.headers.get('Idempotency-Key')
            Transaction.objects.create(wallet=from_wallet, type='TRANSFER_OUT',
                from_currency=currency, from_amount=amount, to_currency=target_currency, to_amount=to_amount,
                rate=rate, counterparty_wallet=to_wallet.id, idempotency_key=key)
            Transaction.objects.create(wallet=to_wallet, type='TRANSFER_IN',
                from_currency=currency, from_amount=amount, to_currency=target_currency, to_amount=to_amount,
                rate=rate, counterparty_wallet=from_wallet.id, idempotency_key=key)
            Transaction.objects.create(wallet=from_wallet, type='AUTO_SWAP',
                from_currency=currency, to_currency=target_currency, from_amount=amount, to_amount=to_amount,
                rate=rate, counterparty_wallet=to_wallet.id, idempotency_key=key)

        return Response({'success': True, 'credited': str(to_amount.quantize(Decimal('0.01'))), 'rate': str(rate)}, status=201)

    # Same-currency transfer
    if preview:
        return Response({'preview': True, 'credited': str(amount), 'rate': '1'})

    with dbtx.atomic():
        sender_bal = _get_balance(from_wallet, currency)
        if sender_bal.amount < amount:
            return Response({'detail':'Insufficient balance.'}, status=400)
        sender_bal.amount -= amount; sender_bal.save(update_fields=['amount'])
        recv_bal = _get_balance(to_wallet, currency)
        recv_bal.amount += amount; recv_bal.save(update_fields=['amount'])

        key = request.headers.get('Idempotency-Key')
        Transaction.objects.create(wallet=from_wallet, type='TRANSFER_OUT',
            from_currency=currency, from_amount=amount, counterparty_wallet=to_wallet.id, idempotency_key=key)
        Transaction.objects.create(wallet=to_wallet, type='TRANSFER_IN',
            to_currency=currency, to_amount=amount, counterparty_wallet=from_wallet.id, idempotency_key=key)

    return Response({'success': True}, status=201)

@api_view(['GET'])
def get_rate_view(request):
    frm = request.query_params.get('from')
    to  = request.query_params.get('to')
    if not frm or not to:
        return Response({"detail": "Both 'from' and 'to' are required."}, status=400)
    rate = get_rate(frm, to)
    return Response({"from": frm, "to": to, "rate": str(rate)})

@api_view(['GET'])
def explorer_recent(request):
    """
    Block-style public feed (last N transactions).
    """
    limit = int(request.GET.get('limit', 50))
    qs = Transaction.objects.order_by('-created_at')[:limit]
    data = [{
        'id': str(t.id),
        'type': t.type,
        'from': {'wallet_id': str(t.wallet_id), 'currency': t.from_currency, 'amount': str(t.from_amount) if t.from_amount is not None else None},
        'to':   {'currency': t.to_currency, 'amount': str(t.to_amount) if t.to_amount is not None else None},
        'rate': str(t.rate) if t.rate is not None else None,
        'counterparty_wallet_id': str(t.counterparty_wallet) if t.counterparty_wallet else None,
        'ts': t.created_at.isoformat()
    } for t in qs]
    return Response(data)

@api_view(['GET'])
def admin_audit_logs(request):
    """
    Protected by ADMIN_API_TOKEN setting. Returns latest audit logs.
    """
    token = request.headers.get('X-Admin-Token')
    if token != getattr(settings, 'ADMIN_API_TOKEN', ''):
        return Response({'detail':'Forbidden'}, status=403)
    limit = int(request.GET.get('limit', 200))
    qs = AuditLog.objects.order_by('-created_at')[:limit]
    data = [{'ip': a.ip, 'ua': a.user_agent, 'method': a.method, 'path': a.path, 'ts': a.created_at.isoformat()} for a in qs]
    return Response(data)

@api_view(['GET'])
def fx_assistant_explain(request):
    """
    Lightweight 'assistant' that explains a conversion (rule-based narrative).
    Query: ?from=USDx&to=cNGN&amount=100
    """
    frm = request.query_params.get('from')
    to  = request.query_params.get('to')
    amt = request.query_params.get('amount', '1')
    if not frm or not to:
        return Response({"detail":"from & to required"}, status=400)
    to_amount, rate = cross_rate(Decimal(amt), frm, to)
    note = f"We convert {amt} {frm} to {to} using live FX. The rate is {rate} ({to} per 1 {frm}). "\
           f"So you would receive approximately {to_amount.quantize(Decimal('0.01'))} {to}. "\
           f"Rates are cached for 10 minutes to ensure responsiveness."
    return Response({"from": frm, "to": to, "amount": amt, "rate": str(rate), "estimated_to_amount": str(to_amount.quantize(Decimal('0.01'))), "explanation": note})
@extend_schema(
    summary="Create a new user",
    description="Registers a user (email or phone handle) and creates their primary wallet.",
    request=UserCreateSer,
    responses={201: UserCreateSer},
)
@api_view(['POST'])
def create_user(request):
    ser = UserCreateSer(data=request.data)
    ser.is_valid(raise_exception=True)
    user, _ = User.objects.get_or_create(handle=ser.validated_data['handle'])
    wallet, _ = Wallet.objects.get_or_create(user=user)
    for c in CURRENCY_MAP.keys():
        WalletBalance.objects.get_or_create(wallet=wallet, currency=c, defaults={'amount':0})
    return Response({'id': str(user.id), 'handle': user.handle, 'wallet_id': str(wallet.id)}, status=201)

@extend_schema(
    summary="Create a new wallet for an existing user",
    description="Creates a new wallet for a specified user.",
    request=None, # Define a serializer if you expect a specific request body for user_id
    responses={201: {'description': 'Wallet created successfully', 'schema': WalletDetailSer}},
)
@api_view(['POST'])
def create_wallet(request):
    user_id = request.data.get('user_id')
    user = get_object_or_404(User, id=user_id)
    wallet = Wallet.objects.create(user=user)
    for c in CURRENCY_MAP.keys():
        WalletBalance.objects.create(wallet=wallet, currency=c, amount=0)
    return Response({'id': str(wallet.id), 'user_id': str(user.id)}, status=201)

@extend_schema(
    summary="Get wallet details",
    description="Retrieves the details and balances of a specific wallet.",
    responses={200: WalletDetailSer},
)
@api_view(['GET'])
def get_wallet(request, wallet_id):
    wallet = get_object_or_404(Wallet, id=wallet_id)
    balances = WalletBalance.objects.filter(wallet=wallet)
    out = []
    total_usd = Decimal('0')
    for b in balances:
        out.append({'currency': b.currency, 'amount': b.amount})
        total_usd += to_usd(b.amount, b.currency)
    data = {'id': str(wallet.id), 'balances': out, 'total_usd': total_usd.quantize(Decimal('0.01'))}
    return Response(WalletDetailSer(data).data)
@extend_schema(
    summary="Deposit funds into a wallet",
    description="Deposits a specified amount of currency into the wallet.",
    request=DepositSer,
    responses={201: {'description': 'Deposit successful'}},
)

@api_view(['POST'])
def deposit(request, wallet_id):
    ser = DepositSer(data=request.data); ser.is_valid(raise_exception=True)
    currency = ser.validated_data['currency']
    amount = ser.validated_data['amount']
    wallet = get_object_or_404(Wallet, id=wallet_id)
    with dbtx.atomic():
        bal = _get_balance(wallet, currency)
        bal.amount = bal.amount + amount
        bal.save(update_fields=['amount'])
        Transaction.objects.create(wallet=wallet, type='DEPOSIT',
                                   to_currency=currency, to_amount=amount,
                                   idempotency_key=request.headers.get('Idempotency-Key'))
    return Response({'success': True}, status=201)
@extend_schema(
    summary="Swap currencies within a wallet",
    description="Swaps a specified amount from one currency to another within the same wallet.",
    request=SwapSer,
    responses={201: {'description': 'Swap successful', 'schema': SwapSer}},
)
@api_view(['POST'])
def swap(request, wallet_id):
    ser = SwapSer(data=request.data); ser.is_valid(raise_exception=True)
    fcur = ser.validated_data['from_currency']
    tcur = ser.validated_data['to_currency']
    amt = ser.validated_data['amount']
    preview = ser.validated_data['preview']
    if fcur == tcur: return Response({'detail':'Currencies must differ.'}, status=400)
    wallet = get_object_or_404(Wallet, id=wallet_id)

    to_amt, rate = cross_rate(amt, fcur, tcur)
    if preview:
        return Response({'preview': True, 'to_amount': str(to_amt.quantize(Decimal('0.01'))), 'rate': str(rate)})

    with dbtx.atomic():
        from_bal = _get_balance(wallet, fcur)
        if from_bal.amount < amt:
            return Response({'detail':'Insufficient balance.'}, status=400)
        to_bal = _get_balance(wallet, tcur)
        from_bal.amount -= amt
        to_bal.amount += to_amt
        from_bal.save(update_fields=['amount'])
        to_bal.save(update_fields=['amount'])
        Transaction.objects.create(wallet=wallet, type='SWAP',
            from_currency=fcur, to_currency=tcur, from_amount=amt, to_amount=to_amt, rate=rate,
            idempotency_key=request.headers.get('Idempotency-Key'))
    return Response({'success': True, 'to_amount': str(to_amt.quantize(Decimal('0.01'))), 'rate': str(rate)}, status=201)
