from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'nombre', 'telefono', 'is_staff', 'is_active', 'is_superuser', 'is_vip')
    list_filter = ('is_staff', 'is_active', 'is_superuser')
    search_fields = ('email', 'nombre', 'telefono')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Información personal'), {'fields': ('nombre', 'telefono')}),
        (_('Permisos'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_vip','groups', 'user_permissions')}),
        (_('Fechas importantes'), {'fields': ('last_login', 'fecha_ingreso')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'telefono', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser', 'is_vip'),
        }),
    )

    readonly_fields = ('fecha_ingreso', 'last_login')
