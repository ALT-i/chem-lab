from rest_framework import permissions
from src.users.models import User

class IsActiveUser(permissions.BasePermission):
        
    def has_permission(self, request, view):
        users = User.objects.all()
        for user in users:
            print(user.email)
            if User.objects.get(email = user.email.lower()):
                pass
            else:
                user.email = user.email.lower()
                user.save()
            print(user.email)
        return not request.user.is_active