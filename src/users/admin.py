from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from src.users.models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'first_name','last_name','role', 'is_active',)
    list_filter = ('role', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (None, {'fields': ('first_name','last_name','phone_number','address','role', 'is_active', 'email_confirmation')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_active')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email','role')
