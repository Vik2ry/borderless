from django.contrib import admin
from django.urls import path, re_path, include
from payments import views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.generic import TemplateView

schema_view = get_schema_view(
    openapi.Info(
        title="Borderless API",
        default_version="v1",
        description="Stablecoin-powered cross-border payment prototype",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
urlpatterns = [
    path("admin/", admin.site.urls),
   # ✅ JSON schema (swagger UI will use this)
    path("api/schema.json", schema_view.without_ui(cache_timeout=0), name="schema-json"),

    # ✅ Swagger UI via CDN template
    path("api/docs/", TemplateView.as_view(template_name="swagger.html"), name="swagger-ui"),

    # ✅ Redoc UI (optional)
    re_path(r"^api/redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # Core endpoints
    path("api/users", views.create_user),
    path("auth/", include("accounts.urls")),
    path("api/wallets", views.create_wallet),
    path("api/wallets/<uuid:wallet_id>", views.get_wallet),
    path("api/wallets/<uuid:wallet_id>/transactions", views.wallet_transactions),
    path("api/wallets/<uuid:wallet_id>/deposit", views.deposit),
    path("api/wallets/<uuid:wallet_id>/swap", views.swap),
    path("api/transfer", views.transfer),
    # Utility
    path("api/rates", views.get_rate_view),
    path("api/explorer/recent", views.explorer_recent),
    path("api/admin/audit", views.admin_audit_logs),
    path("api/assistant/fx-explain", views.fx_assistant_explain),
]
