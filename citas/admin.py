from django.contrib import admin
from .models import Cita

# Register your models here.

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display= ('usuario', 'tipo', 'fecha', 'estado')
    list_filter = ('estado', 'tipo', 'fecha')
    search_fields = ('usuario__email', 'usuario__nombre', 'tipo')
    
    fieldsets = (
        (None, {'fields': ('usuario', 'tipo')}),
        ('Horario y Estado', {'fields': ('fecha', 'estado')}),
    )