from django.contrib import admin
from .models import Cita

# Register your models here.

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display= ('usuario', 'fecha', 'estado', 'observaciones')
    list_filter = ('estado', 'fecha')
    search_fields = ('usuario__email', 'usuario__nombre')
    
    fieldsets = (
        (None, {'fields': ('usuario', 'observaciones')}),
        ('Horario y Estado', {'fields': ('fecha', 'estado')}),
    )