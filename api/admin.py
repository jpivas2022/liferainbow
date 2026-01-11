"""
=============================================================================
LIFE RAINBOW 2.0 - Admin para Perfis de Usuário
=============================================================================
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline para editar perfil junto com usuário."""
    model = UserProfile
    can_delete = False
    verbose_name = 'Perfil'
    verbose_name_plural = 'Perfil'
    fields = ['role']


class UserAdmin(BaseUserAdmin):
    """Admin customizado para User com perfil inline."""
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active', 'profile__role']

    @admin.display(description='Perfil')
    def get_role(self, obj):
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.get_role_display()
        return '-'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin para UserProfile."""
    list_display = ['user', 'role', 'created_at', 'updated_at']
    list_filter = ['role']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = [
        ('Usuário', {
            'fields': ['user']
        }),
        ('Perfil', {
            'fields': ['role']
        }),
        ('Datas', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


# Re-registrar User com o novo admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
