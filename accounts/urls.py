from django.urls import path
from borderless.api_demo import DemoAuthPing, DemoFXView
from .views import RegisterView, LoginView, RefreshView, MeView, ChangePasswordView, LogoutView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Demo endpoints
    path("demo/fx/", DemoFXView.as_view(), name="demo-fx"),
    path("demo/auth-ping/", DemoAuthPing.as_view(), name="demo-auth-ping"),

    # Auth endpoints
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
]
