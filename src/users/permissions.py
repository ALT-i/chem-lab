from rest_framework import permissions
from src.users.models import User


class IsUserOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user


class IsInstructorOrAdmin(permissions.BasePermission):
    """Allow only INSTRUCTOR, ADMIN, or SUPER roles."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if not isinstance(user, User):
            return False
        return user.role in {User.Roles.INSTRUCTOR, User.Roles.ADMIN, User.Roles.SUPER}
