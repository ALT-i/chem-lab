from rest_framework import permissions

class IsActiveUser(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    def has_permission(self, request, view):
        return not request.user.is_active