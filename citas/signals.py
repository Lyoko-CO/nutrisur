from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Cita

@receiver(post_save, sender=Cita)
def avisar_nueva_cita(sender, instance, created, **kwargs):
    # Verificamos si la cita está en un estado que requiera aviso (Pendiente o Confirmada)
    # y evitamos enviar correo si está en borrador o cancelada.
    if instance.estado in ['PENDIENTE', 'CONFIRMADA']:
        
        # Formateamos la fecha para que sea legible (Día/Mes/Año Hora:Minuto)
        fecha_legible = "Fecha por confirmar"
        if instance.fecha:
            fecha_legible = instance.fecha.strftime("%d/%m/%Y a las %H:%M")

        asunto = f"📅 Nueva Cita de Masaje: {instance.cliente_nombre}"
        
        mensaje = f"""
        ¡Tienes una nueva cita reservada!
        
        ------------------------------------------
        DETALLES DEL CLIENTE:
        Cliente: {instance.cliente_nombre}
        Email: {instance.cliente_email}
        Teléfono: {instance.cliente_telefono}
        ------------------------------------------
        
        DATOS DE LA CITA:
        Fecha y Hora: {fecha_legible}
        Estado: {instance.get_estado_display()}
        Observaciones: {instance.observaciones or "Sin observaciones"}
        
        ------------------------------------------
        
        Gestionar cita aquí:
        https://nutrisur.onrender.com/admin/citas/cita/{instance.id}/change/
        """
        
        try:
            # Enviamos el correo al administrador
            send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [settings.EMAIL_HOST_USER])
        except Exception as e:
            print(f"Error enviando correo cita: {e}")