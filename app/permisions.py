
from rest_framework.permissions import BasePermission, SAFE_METHODS

from app.models import User


class IsAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        if request.method in SAFE_METHODS:
            return True
        return user.is_authenticated and user.role == User.Roles.ADMIN



class IsSellerOrAdmin(BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role == User.Roles.ADMIN:
            return True
        if user.role == User.Roles.SELLER and obj.seller == user:
            return True
        return False



class IsOwnerOrAdminOrReadOnly(BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.method in SAFE_METHODS:
            return True

        if user.role == User.Roles.ADMIN:
            return True


        if user.role == User.Roles.SELLER:
            return obj.product.seller == request.user

        return False


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if obj.user == user:
            return True
        if user.role == User.Roles.ADMIN:
            return True

        return False
