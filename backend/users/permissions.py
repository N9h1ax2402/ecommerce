from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Only admins can access"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsAdminOrStaff(permissions.BasePermission):
    """Admins and staff can access"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff_user


class IsAdminOrReadOnly(permissions.BasePermission):
    """Admins can modify, others can only read"""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.is_admin

