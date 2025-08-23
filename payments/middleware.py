from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .models import AuditLog, IdempotencyRecord

class AuditLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            AuditLog.objects.create(
                user=None,  # attach if you add auth later
                ip=(request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR', '')),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                method=request.method,
                path=request.path,
                created_at=timezone.now()
            )
        except Exception:
            pass  # never block

class IdempotencyMiddleware(MiddlewareMixin):
    """
    If 'Idempotency-Key' header is present, ensures the same (path, key) isn't processed twice.
    Returns 409 on duplicates.
    """
    def process_request(self, request):
        if request.method in ('POST', 'PUT', 'PATCH'):
            key = request.headers.get('Idempotency-Key')
            if key:
                exists = IdempotencyRecord.objects.filter(key=key, path=request.path).exists()
                if exists:
                    from django.http import JsonResponse
                    return JsonResponse({'detail':'Duplicate request'}, status=409)
                # reserve the key up-front
                try:
                    IdempotencyRecord.objects.create(key=key, path=request.path)
                except Exception:
                    pass
        return None
