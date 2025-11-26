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
    

class ConfiguracionChatbotCitas(models.Model):
    titulo = models.CharField(max_length=100, default="Configuración Citas")
    instrucciones_adicionales = models.TextField(
        help_text="Reglas extra para el recepcionista. Ej: 'Recuerda que los viernes cerramos a las 14:00 excepcionalmente'.",
        default="",
        blank=True
    )

    class Meta:
        verbose_name = "Configuración del Chatbot (Citas)"
        verbose_name_plural = "Configuración del Chatbot (Citas)"

    def __str__(self):
        return self.titulo