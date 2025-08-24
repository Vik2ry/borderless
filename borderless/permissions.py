from rest_framework import permissions
from .models import Wallet

class IsWalletOwner(permissions.BasePermission):
    """Allows access only to owners of the wallet."""

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Wallet):
            return obj.user == request.user
        return False
