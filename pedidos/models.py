from django.db import models
from django.conf import settings
from django.utils import timezone
from productos.models import Producto


# Create your models here.
class Pedido(models.Model):
    ESTADOS =[
        ('B', 'Borrador'),
        ('P', 'Pendiente'),
        ('R', 'Realizado')
    ]
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    productos_chat = models.JSONField(default=list)
    
    fecha_pedido = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='P')
    productos = models.ManyToManyField(
            Producto,
            through='PedidoProducto',  # referencia al modelo intermedio
            related_name='pedidos'
        )    
    
    def agregar_producto(self, producto, cantidad=1):
        pedido_producto, creado = PedidoProducto.objects.get_or_create(
            pedido = self, 
            producto = producto,
            defaults={'cantidad': cantidad}
        )
        if not creado:
            pedido_producto.cantidad += cantidad
            pedido_producto.save()
        return pedido_producto
    
    def calcular_total(self):
        total = sum([
            pp.producto.precio * pp.cantidad for pp in self.pedidoproducto_set.all()
        ])
        return total
    
    def agregar_producto_chat(self, producto):
        self.productos_chat.append(producto)
    
    @property
    def cliente_nombre(self):
        return self.usuario.nombre
    
    @property
    def cliente_email(self):
        return self.usuario.email
    
    @property
    def cliente_telefono(self):
        return self.usuario.telefono
        
        
    
    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.nombre}"
    
    

class PedidoProducto(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ('pedido', 'producto')
        
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} (Pedido #{self.pedido.id})"

    
