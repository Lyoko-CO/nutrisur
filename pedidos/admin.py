from django.contrib import admin
from .models import Pedido, PedidoProducto

class PedidoProductoInline(admin.TabularInline):
    model = PedidoProducto
    extra = 0  # No mostrar filas vacías extra (pon 1 si quieres permitir añadir directamente)
    autocomplete_fields = ['producto']  # muestra un campo vacío adicional para agregar nuevos productos

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'fecha_pedido', 'estado', 'calcular_total_display')
    list_display_links = ('id', 'usuario')  # 👈 Esto hace que puedas pinchar en el pedido
    list_filter = ('estado', 'fecha_pedido')
    search_fields = ('usuario__nombre', 'usuario__email')
    inlines = [PedidoProductoInline]
    actions = ['marcar_como_pendiente', 'marcar_como_realizado']  
    

    def calcular_total_display(self, obj):
        return f"{obj.calcular_total():.2f} €"
    calcular_total_display.short_description = "Total"
    
    @admin.action(description='Marcar como Pendiente')
    def marcar_como_pendiente(self, request, queryset):
        queryset.update(estado='P')

    @admin.action(description='Marcar como Realizado')
    def marcar_como_realizado(self, request, queryset):
        queryset.update(estado='R')

@admin.register(PedidoProducto)
class PedidoProductoAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'producto', 'cantidad')
    list_filter = ('pedido', 'producto')
