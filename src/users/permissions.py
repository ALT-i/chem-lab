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


STAFF_ROLES = {User.Roles.INSTRUCTOR, User.Roles.ADMIN, User.Roles.SUPER}


def is_staff_user(user):
    """True for authenticated INSTRUCTOR / ADMIN / SUPER accounts."""
    if not user or not user.is_authenticated:
        return False
    if not isinstance(user, User):
        return False
    return user.role in STAFF_ROLES


class IsInstructorOrAdmin(permissions.BasePermission):
    """Allow only INSTRUCTOR, ADMIN, or SUPER roles."""

    def has_permission(self, request, view):
        return is_staff_user(request.user)


class IsInstructorOrAdminOrReadOnly(permissions.BasePermission):
    """Catalogue permission: anyone may read, only staff may write.

    Reads stay open because released desktop clients fetch lessons,
    substances and apparatus without an Authorization header; requiring
    auth here would break every installed copy. Writes are staff-only.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return is_staff_user(request.user)


class IsSessionOwnerOrStaff(permissions.BasePermission):
    """A lesson session belongs to its student; staff may see/act on any."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if is_staff_user(request.user):
            return True
        return obj.student_id == request.user.id
