from rest_framework.permissions import BasePermission

class is_authenticated(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        else:
            return False