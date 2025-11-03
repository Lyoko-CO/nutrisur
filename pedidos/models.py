from django.db import models
from django.conf import settings
from django.utils import timezone
from productos.models import Producto


# Create your models here.
class Pedido(models.Model):
    ESTADOS =[
        ('P', 'Pendiente'),
        ('R', 'Realizado')
    ]
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    
    fecha_pedido = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='P')
    productos = models.ManyToManyField(
            Producto,
            through='PedidoProducto',  # referencia al modelo intermedio
            related_name='pedidos'
        )    
    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.nombre}"

class PedidoProducto(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ('pedido', 'producto')
        
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} (Pedido #{self.pedido.id})"

    
