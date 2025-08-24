import os, requests
from decimal import Decimal
from django.utils import timezone
try:
    from accounts.models import RatesCache
except Exception:
    RatesCache = None

class FXServiceError(Exception):
    pass

class FXService:
    def __init__(self, timeout=None):
        self.timeout = float(os.getenv('FX_HTTP_TIMEOUT', timeout or 2.5))
    def _normalize(self, code: str):
        return code.replace('x','').replace('c','')[:3].upper()
    def _live(self, src, dst):
        base = self._normalize(src)
        symbols = self._normalize(dst)
        url = f'https://api.exchangerate.host/latest?base={base}&symbols={symbols}'
        r = requests.get(url, timeout=self.timeout)
        if r.status_code != 200:
            raise FXServiceError('live provider error')
        data = r.json()
        rate = data.get('rates', {}).get(symbols)
        if not rate:
            raise FXServiceError('rate missing')
        return float(rate)
    def _fixed(self, src, dst):
        ov = os.getenv('FIXED_RATE_OVERRIDES','')
        for chunk in [c.strip() for c in ov.split(',') if c.strip()]:
            if ':' not in chunk or '->' not in chunk:
                continue
            pair, val = chunk.split(':')
            a,b = pair.split('->')
            if a.strip()==src and b.strip()==dst:
                try:
                    return float(val.strip())
                except:
                    pass
        return None
    def _cache_get(self, src, dst):
        if RatesCache is None:
            return None
        try:
            rc = RatesCache.objects.get(from_currency=src, to_currency=dst)
            return float(rc.rate)
        except RatesCache.DoesNotExist:
            return None
    def _cache_set(self, src, dst, rate):
        if RatesCache is None:
            return
        RatesCache.objects.update_or_create(
            from_currency=src, to_currency=dst,
            defaults={'rate': Decimal(str(rate)), 'updated_at': timezone.now()},
        )
    def get_rate(self, src, dst):
        try:
            rate = self._live(src,dst)
            self._cache_set(src,dst,rate)
            return rate
        except Exception:
            pass
        fixed = self._fixed(src,dst)
        if fixed is not None:
            return fixed
        cached = self._cache_get(src,dst)
        if cached is not None:
            return cached
        raise FXServiceError(f'Unable to get rate for {src}->{dst}')
