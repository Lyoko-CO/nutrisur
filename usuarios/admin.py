from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html  # <--- IMPORTANTE: Importar esto
from .models import CustomUser

@admin.action(description='Marcar como Cliente VIP')
def hacer_vip(modeladmin, request, queryset):
    updated = queryset.update(is_vip=True)
    modeladmin.message_user(request, f"{updated} usuarios marcados como VIP exitosamente.")

@admin.action(description='Quitar estado de Cliente VIP')
def quitar_vip(modeladmin, request, queryset):
    updated = queryset.update(is_vip=False)
    modeladmin.message_user(request, f"{updated} usuarios desmarcados como VIP exitosamente.")

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'nombre', 'status_vip','telefono', 'is_staff', 'is_active', 'is_superuser', 'is_vip')
    list_editable= ('is_vip',)
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'is_vip')
    search_fields = ('email', 'nombre', 'telefono')
    ordering = ('email',)

    actions = [hacer_vip, quitar_vip]

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
    
    def status_vip(self, obj):
        if obj.is_vip:
            # Renderizamos una estrella dorada y texto en negrita
            return format_html(
                '<span style="color: #FFD700; font-weight: bold; font-size: 14px;">★ VIP</span>'
            )
        else:
            # Devolvemos un string vacío o un guion para no ensuciar la vista
            return "-"
    
    # Configuramos los metadatos de la columna
    status_vip.short_description = 'Distinción'  # Título de la columna
    status_vip.admin_order_field = 'is_vip'

    readonly_fields = ('fecha_ingreso', 'last_login')

