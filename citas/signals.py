from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone 
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
            
            
@receiver(pre_save, sender=Cita)
def detectar_confirmacion_cita(sender, instance, **kwargs):
    if instance.pk: # Solo si es una edición (la cita ya existía)
        try:
            cita_antigua = Cita.objects.get(pk=instance.pk)
            # Si ANTES no estaba confirmada Y AHORA sí lo está
            if cita_antigua.estado != 'CONFIRMADA' and instance.estado == 'CONFIRMADA':
                instance._enviar_confirmacion = True # Ponemos la bandera
        except Cita.DoesNotExist:
            pass

@receiver(post_save, sender=Cita)
def enviar_email_confirmacion(sender, instance, **kwargs):
    # Verificamos la bandera
    if getattr(instance, '_enviar_confirmacion', False):
        
        fecha_str = "Fecha por definir"
        if instance.fecha:
            fecha_local = timezone.localtime(instance.fecha)
            fecha_str = fecha_local.strftime("%d/%m/%Y a las %H:%M")

        asunto = f"✅ Cita Confirmada: {fecha_str}"
        mensaje = f"""
        Hola {instance.cliente_nombre},
        
        Te confirmamos que tu cita ha sido aceptada por el administrador.
        
        DETALLES DE LA CITA:
        📅 Fecha: {fecha_str}
        📍 Lugar: Av. Santa Lucia 62, Alcalá de Guadaíra, Sevilla
        
        Por favor, intenta llegar 5 minutos antes.
        Si necesitas cancelar, puedes hacerlo desde tu panel de usuario.
        
        ¡Te esperamos!
        """
        
        try:
            send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [instance.cliente_email])
            print(f"Correo de cita confirmada enviado a {instance.cliente_email}")
        except Exception as e:
            print(f"Error enviando correo confirmación cita: {e}")