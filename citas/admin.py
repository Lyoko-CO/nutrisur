from django.contrib import admin
from .models import Cita, ConfiguracionChatbotCitas

# Register your models here.

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display= ('usuario', 'fecha', 'estado', 'observaciones')
    list_editable = ('estado',)
    list_filter = ('estado', 'fecha')
    search_fields = ('usuario__email', 'usuario__nombre')
    
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        
        if db_field.name == "estado":
            kwargs['choices'] = (
                ('PENDIENTE', 'Pendiente'),
                ('CONFIRMADA', 'Confirmada'),
                ('FINALIZADA', 'Finalizada'),
                ('CANCELADA', 'Cancelada'),
            )
            
        return super().formfield_for_choice_field(db_field, request, **kwargs)
    
    fieldsets = (
        (None, {'fields': ('usuario', 'observaciones')}),
        ('Horario y Estado', {'fields': ('fecha', 'estado')}),
    )

@admin.register(ConfiguracionChatbotCitas)
class ConfiguracionCitasAdmin(admin.ModelAdmin):
    list_display = ('titulo',)
    def has_add_permission(self, request):
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)