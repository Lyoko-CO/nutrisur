from django.db import models
from django.conf import settings

# Create your models here.

class Cita(models.Model):
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='citas')
    
    fecha = models.DateTimeField(null=True, blank=True)
    
    ESTADOS = [
        ('BORRADOR', 'Borrador'),
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
        ('FINALIZADA', 'Finalizada'),
    ]
    estado = models.CharField(
        max_length=10, 
        choices = ESTADOS,
        default = 'BORRADOR'
    )

    observaciones = models.TextField(blank=True, null=True)
    
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
        return super().__str__()