import os, requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import RateCache

CURRENCY_MAP = {"USDx":"USD","EURx":"EUR","cNGN":"NGN","cXAF":"XAF"}
SUPPORTED = list(CURRENCY_MAP.keys())

def parse_overrides():
    """
    Env: FIXED_RATE_OVERRIDES = "USD->NGN:1576.5,EUR->USD:1.08"
    """
    overrides = {}
    raw = getattr(settings, 'FIXED_RATE_OVERRIDES', '')
    for pair in raw.split(','):
        if '->' in pair and ':' in pair:
            left, rate = pair.split(':', 1)
            frm, to = left.split('->', 1)
            overrides[(frm.strip(), to.strip())] = Decimal(rate.strip())
    return overrides

OVERRIDES = parse_overrides()

def _cache_get(base_fiat, quote_fiat):
    rec = RateCache.objects.filter(base=base_fiat, quote=quote_fiat).order_by('-fetched_at').first()
    if rec and (timezone.now() - rec.fetched_at) < timedelta(minutes=10):
        return rec.rate
    return None

def _cache_set(base_fiat, quote_fiat, rate):
    RateCache.objects.create(base=base_fiat, quote=quote_fiat, rate=Decimal(str(rate)))

def _fx_exchangerate_host(base, quote):
    url = f"https://api.exchangerate.host/convert?from={base}&to={quote}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    result = data.get('result')
    if result is None:
        raise RuntimeError('exchangerate.host no result')
    return Decimal(str(result))

def _fx_frankfurter(base, quote):
    url = f"https://api.frankfurter.app/latest?from={base}&to={quote}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    rate = data['rates'].get(quote)
    if rate is None:
        raise RuntimeError('frankfurter no rate')
    return Decimal(str(rate))

def get_rate(base_symbol, quote_symbol):
    base = CURRENCY_MAP.get(base_symbol, base_symbol)
    quote = CURRENCY_MAP.get(quote_symbol, quote_symbol)

    if base == quote:
        return Decimal('1')

    # Fixed override first (useful for demos)
    if (base, quote) in OVERRIDES:
        return OVERRIDES[(base, quote)]

    # Cache
    cached = _cache_get(base, quote)
    if cached:
        return cached

    # Provider chain: exchangerate.host -> frankfurter
    try:
        rate = _fx_exchangerate_host(base, quote)
    except Exception:
        rate = _fx_frankfurter(base, quote)

    _cache_set(base, quote, rate)
    return rate

def cross_rate(amount, from_symbol, to_symbol):
    """
    Returns (to_amount, rate_used) with USD pivot fallback.
    """
    from_fiat = CURRENCY_MAP.get(from_symbol, from_symbol)
    to_fiat = CURRENCY_MAP.get(to_symbol, to_symbol)
    amt = Decimal(amount)

    if from_fiat == to_fiat:
        return (amt, Decimal('1'))

    try:
        rate = get_rate(from_symbol, to_symbol)
        return (amt * rate, rate)
    except Exception:
        # Pivot via USD if direct not available
        r1 = get_rate(from_symbol, 'USDx')
        r2 = get_rate('USDx', to_symbol)
        rate = r1 * r2
        return (amt * rate, rate)

def to_usd(amount, symbol):
    """Convert any supported symbol to USDx amount."""
    amt = Decimal(amount)
    if symbol == 'USDx':
        return amt
    usd_amt, _ = cross_rate(amt, symbol, 'USDx')
    return usd_amt
