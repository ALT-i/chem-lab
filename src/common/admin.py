from django.contrib import admin

from src.common.models import MoodleConfiguration


@admin.register(MoodleConfiguration)
class MoodleConfigurationAdmin(admin.ModelAdmin):
    """Single-row admin for the institution's Moodle connection."""

    list_display = ('__str__', 'is_active', 'course_id', 'last_verified_at')
    readonly_fields = ('last_verified_at', 'last_verification_error', 'updated_at', 'updated_by')
    fieldsets = (
        ('Moodle site', {
            'fields': ('base_url', 'token', 'is_active'),
            'description': (
                'Point the lab at your own Moodle site. The token is created in Moodle under '
                'Site administration &rarr; Server &rarr; Web services &rarr; Manage tokens, for a user '
                'with permission to view enrolled users and save assignment grades.'
            ),
        }),
        ('Course', {'fields': ('course_id', 'default_assignment_id')}),
        ('Last verification', {'fields': ('last_verified_at', 'last_verification_error', 'updated_at', 'updated_by')}),
    )

    def _is_allowed(self, request):
        # Institution-wide credentials: superusers only, regardless of what
        # other model permissions a staff account may have been granted.
        return bool(getattr(request.user, 'is_superuser', False))

    def has_module_permission(self, request):
        return self._is_allowed(request)

    def has_view_permission(self, request, obj=None):
        return self._is_allowed(request)

    def has_change_permission(self, request, obj=None):
        return self._is_allowed(request)

    def has_add_permission(self, request):
        # The singleton row is created on demand by MoodleConfiguration.load().
        return (
            super().has_add_permission(request)
            and self._is_allowed(request)
            and not MoodleConfiguration.objects.exists()
        )

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        MoodleConfiguration.load()
        return super().changelist_view(request, extra_context)

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
