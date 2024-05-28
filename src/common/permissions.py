from rest_framework import permissions
from src.users.models import User

class IsActiveUser(permissions.BasePermission):
        
    def has_permission(self, request, view):
        users = User.objects.all()
        for user in users:
            print(user.email)
            user.email = user.email.lower()
            print(user.email)
            user.save()
        return not request.user.is_active