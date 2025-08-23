from django.contrib import admin
from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from payments import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # API schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Core endpoints
    path('api/users', views.create_user),
    path('api/wallets', views.create_wallet),
    path('api/wallets/<uuid:wallet_id>', views.get_wallet),
    path('api/wallets/<uuid:wallet_id>/transactions', views.wallet_transactions),
    path('api/wallets/<uuid:wallet_id>/deposit', views.deposit),
    path('api/wallets/<uuid:wallet_id>/swap', views.swap),
    path('api/transfer', views.transfer),

    # Utility
    path('api/rates', views.get_rate_view),
    path('api/explorer/recent', views.explorer_recent),
    path('api/admin/audit', views.admin_audit_logs),
    path('api/assistant/fx-explain', views.fx_assistant_explain),
]
