from django.contrib import admin
from .models import Pedido, PedidoProducto, ConfiguracionChatbot

class PedidoProductoInline(admin.TabularInline):
    model = PedidoProducto
    extra = 0  # No mostrar filas vacías extra (pon 1 si quieres permitir añadir directamente)
    autocomplete_fields = ['producto']  # muestra un campo vacío adicional para agregar nuevos productos

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'fecha_pedido', 'estado', 'calcular_total_display', 'is_vip_display')
    list_display_links = ('id', 'usuario')  # 👈 Esto hace que puedas pinchar en el pedido
    list_filter = ('estado', 'fecha_pedido', 'usuario__is_vip')
    search_fields = ('usuario__nombre', 'usuario__email')
    inlines = [PedidoProductoInline]
    actions = ['marcar_como_pendiente', 'marcar_como_realizado']  
    

    def calcular_total_display(self, obj):
        return f"{obj.calcular_total():.2f} €"
    calcular_total_display.short_description = "Total"
    
    def is_vip_display(self, obj):
        return obj.usuario.is_vip
    
    is_vip_display.boolean = True  # Esto hace que salga el icono de ✅/❌ en vez de True/False
    is_vip_display.short_description = "Cliente VIP" # Título de la columna
    is_vip_display.admin_order_field = 'usuario__es_vip'
    
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

@admin.register(ConfiguracionChatbot)
class ConfiguracionChatbotAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'activado')
    # Limitamos para que no se creen infinitos, lo ideal es tener solo 1
    def has_add_permission(self, request):
        # Si ya existe 1, no dejar añadir más
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)
