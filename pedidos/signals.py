import threading
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from usuarios.models import CustomUser
from pedidos.models import Pedido

@receiver(post_save, sender=CustomUser)
def avisar_nuevo_usuario(sender, instance, created, **kwargs):
    if created: # Solo si es un usuario NUEVO (no si edita su perfil)
        asunto = f"👤 Nuevo Usuario Registrado: {instance.nombre}"
        mensaje = f"""
        Se ha registrado un nuevo cliente en NutriSur.
        
        Nombre: {instance.nombre}
        Email: {instance.email}
        Teléfono: {instance.telefono}
        
        Entra para revisar si es un cliente habitual:
        https://nutrisur.onrender.com/admin/usuarios/
        """
        try:
            send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [settings.EMAIL_HOST_USER])
        except Exception as e:
            print(f"Error enviando correo usuario: {e}")


@receiver(post_save, sender=Pedido)
def avisar_nuevo_pedido(sender, instance, created, **kwargs):
    # Solo enviamos el correo cuando el estado pasa a 'P' (Pendiente/Confirmado)
    if instance.estado == 'P': 
        
        # 1. GENERAMOS LA LISTA DE PRODUCTOS
        # Recorremos los productos asociados a este pedido
        items_texto = ""
        for item in instance.pedidoproducto_set.all():
            # Formato: "- 2 x Batido Fresa (35.50 €)"
            # Usamos item.subtotal que ya definiste en models.py
            items_texto += f"- {item.cantidad} x {item.producto.nombre} ({item.subtotal} €)\n"

        # 2. CONSTRUIMOS EL MENSAJE
        asunto = f"💰 Nuevo Pedido Recibido #{instance.id}"
        mensaje = f"""
        ¡Enhorabuena! Tienes una nueva venta confirmada.
        
        ------------------------------------------
        DETALLES DEL CLIENTE:
        Cliente: {instance.usuario.nombre}
        Email: {instance.usuario.email}
        ------------------------------------------
        
        CARRITO DE COMPRA:
        {items_texto}
        
        ------------------------------------------
        TOTAL DEL PEDIDO: {instance.calcular_total()} €
        ------------------------------------------
        
        Gestionar pedido aquí:
        https://nutrisur.onrender.com/admin/pedidos/pedido/{instance.id}/change/
        """
        
        try:
            send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [settings.EMAIL_HOST_USER])
        except Exception as e:
            print(f"Error enviando correo pedido: {e}")
            
@receiver(pre_save, sender=Pedido)
def detectar_cambio_a_realizado(sender, instance, **kwargs):
    if instance.pk: # Solo si el pedido ya existía (es una edición)
        try:
            pedido_antiguo = Pedido.objects.get(pk=instance.pk)
            # Verificamos: Antes NO era 'R' y Ahora SÍ es 'R'
            if pedido_antiguo.estado != 'R' and instance.estado == 'R':
                instance._enviar_correo_cliente = True # Ponemos una marca temporal
        except Pedido.DoesNotExist:
            pass
        
@receiver(post_save, sender=Pedido)
def enviar_aviso_cliente(sender, instance, **kwargs):
    # Buscamos si existe la marca que pusimos antes
    if getattr(instance, '_enviar_correo_cliente', False):
        items_texto = ""
        for item in instance.pedidoproducto_set.all():
            # Formato: "- 2 x Batido Fresa (35.50 €)"
            # Usamos item.subtotal que ya definiste en models.py
            items_texto += f"- {item.cantidad} x {item.producto.nombre} ({item.subtotal} €)\n"
        
        asunto = f"🚚 ¡Tu pedido ha sido enviado!"
        mensaje = f"""
        Hola {instance.usuario.nombre},
        
        ¡Buenas noticias! Tu pedido ha sido procesado y marcado como REALIZADO.
        Pronto lo recibirás en la dirección habitual.
        
        Resumen del pedido #{instance.id}:
        
        CARRITO DE COMPRA:
        {items_texto}
        
        ------------------------------------------
        TOTAL DEL PEDIDO: {instance.calcular_total()} €
        ------------------------------------------
        
        Gracias por confiar en NutriSur.
        """
        def tarea_enviar_email():
            try:
                print(f"Hilo: Intentando enviar correo a {instance.usuario.email}...")
                send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [instance.usuario.email])
                print(f"Correo de confirmación enviado a {instance.usuario.email}")
            except Exception as e:
                print(f"Error enviando correo al cliente: {e}")        
        email_thread = threading.Thread(target=tarea_enviar_email)
        email_thread.start()

            