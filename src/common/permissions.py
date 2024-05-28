from rest_framework import permissions
from src.users.models import User

class IsActiveUser(permissions.BasePermission):
        
    def has_permission(self, request, view):
        return not request.user.is_active