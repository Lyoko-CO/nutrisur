from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Pedido, PedidoProducto
from productos.models import Producto
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .gemini_utils import obtener_respuesta_gemini, get_data_pedido
import json

# Create your views here.

@login_required
def lista_pedidos_view(request):
    """
    Muestra una lista de todos los pedidos
    pertenecientes al usuario logueado.
    """
    
    # 1. Filtramos los pedidos para obtener SOLO los del usuario actual
    # 2. Ordenamos del más reciente al más antiguo
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha_pedido')
    
    # 3. Pasamos los pedidos a la plantilla
    context = {
        'pedidos': pedidos
    }
    return render(request, 'pedidos/pedidos.html', context)

@login_required
def chatbot_view(request):
    
    pedido = Pedido.objects.get_or_create(
        usuario = request.user,
        estado = 'B'
    )

    productos_recientes_ids = request.user.historial_productos
    productos_recientes = []
    if productos_recientes_ids:
        recientes_db = Producto.objects.filter(id__in=productos_recientes_ids)
        # Mantener el orden según historial
        productos_recientes = sorted(recientes_db, key=lambda p: productos_recientes_ids.index(p.id))

    productos_escaparate = Producto.objects.exclude(id__in=productos_recientes_ids)[:25]
    
    context = {
        'pedido': pedido,
        'historial': productos_recientes,
        'productos_escaparate': productos_escaparate
    }
    
    return render(request, 'pedidos/chatbot.html', context)

@login_required
@require_POST
def actualizar_cantidad_view(request):
    try:
        data = json.loads(request.body)
        id_producto = data.get('id_producto')
        accion = data.get('accion') # 'incrementar' o 'decrementar'
        
        pedido = Pedido.objects.get(usuario=request.user, estado='B')
        producto = get_object_or_404(Producto, id=id_producto)
        
        # Buscamos la relación (item del pedido)
        pp, created = PedidoProducto.objects.get_or_create(pedido=pedido, producto=producto)
        
        if accion == 'incrementar':
            pp.cantidad += 1
            pp.save()
        elif accion == 'decrementar':
            if pp.cantidad > 1:
                pp.cantidad -= 1
                pp.save()
            else:
                pp.delete() # Si baja de 1, lo borramos
        
        # Devolvemos los datos actualizados usando nuestra función auxiliar
        response_data = get_data_pedido(pedido)
        response_data['status'] = 'ok'
        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@login_required
def cancelar_pedido_view(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    
    # Solo permitimos cancelar si NO está Realizado
    if pedido.estado != 'R':
        pedido.estado = 'C' # Cancelado
        pedido.save()
        messages.success(request, f"El pedido #{pedido.id} ha sido cancelado.")
    else:
        messages.error(request, "No se puede cancelar un pedido que ya ha sido realizado.")
        
    return redirect('mis_pedidos')

@login_required
def modificar_pedido_view(request, pedido_id):
    pedido_a_modificar = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    
    if pedido_a_modificar.estado == 'R':
        messages.error(request, "No se puede modificar un pedido ya realizado.")
        return redirect('mis_pedidos')
        
    # 1. Buscamos si YA existe un borrador activo (el carrito actual)
    borrador_actual = Pedido.objects.filter(usuario=request.user, estado='B').first()
    
    if borrador_actual:
        # Si es el mismo pedido, no hacemos nada, solo redirigimos
        if borrador_actual.id == pedido_a_modificar.id:
            return redirect('chatbot_pedidos')
            
        # Si es OTRO pedido, lo "aparcamos" (lo pasamos a Pendiente) para no perderlo
        borrador_actual.estado = 'P'
        borrador_actual.save()
    
    # 2. Convertimos el pedido seleccionado en el nuevo Borrador Activo
    pedido_a_modificar.estado = 'B'
    pedido_a_modificar.save()
    
    messages.info(request, f"Estás editando el pedido #{pedido_a_modificar.id}.")
    return redirect('chatbot_pedidos')

@login_required
@require_POST
def procesar_mensaje_view(request):
    """
    Procesa el mensaje usando Gemini y actualiza el pedido.
    """
    try:
        data = json.loads(request.body)
        mensaje_usuario = data.get('mensaje', '')
        
        # Obtener o crear el pedido borrador
        pedido, _ = Pedido.objects.get_or_create(usuario=request.user, estado='B')

        # --- LLAMADA A GEMINI ---
        respuesta_ai = obtener_respuesta_gemini(mensaje_usuario, request)
        
        texto_bot = respuesta_ai.get("texto_respuesta", "No te he entendido bien.")
        acciones = respuesta_ai.get("acciones", [])
        finalizar = respuesta_ai.get("finalizar_pedido", False)
        
        # --- EJECUTAR ACCIONES ---
        for accion in acciones:
            tipo = accion.get("tipo")
            nombre_prod = accion.get("producto_nombre") # Recibimos NOMBRE
            cantidad = int(accion.get("cantidad", 1))
            
            if nombre_prod:
                # --- CAMBIO: Búsqueda por nombre aproximado ---
                # 'icontains' busca si el texto está contenido en el nombre (mayúsculas/minúsculas ignoradas)
                producto = Producto.objects.filter(nombre__icontains=nombre_prod).first()
                
                if producto:
                    if tipo == "agregar":
                        pedido.agregar_producto(producto, cantidad)
                    
                    elif tipo == "eliminar":
                        pp = PedidoProducto.objects.filter(pedido=pedido, producto=producto).first()
                        if pp:
                            # Si cantidad es 0 (orden de "borrar todo") o si la resta deja < 0
                            if cantidad == 0 or (pp.cantidad - cantidad) <= 0:
                                pp.delete()
                            else:
                                pp.cantidad -= cantidad
                                pp.save()

        # --- MANEJAR FINALIZACIÓN ---
        status_respuesta = 'ok'
        if finalizar:
            if pedido.pedidoproducto_set.exists():
                pedido.estado = 'P' # Pasamos a Pendiente
                pedido.save()

                #Actualizar historial del usuario
                ids_pedidos = [p.producto.id for p in pedido.pedidoproducto_set.all()]
                request.user.registrar_compra(ids_pedidos)

                status_respuesta = 'finalizado'
                texto_bot = "¡Pedido confirmado! Gracias por tu compra en NutriSur. Para recibir su pedido, haga bizum al 123456789 con su nombre completo en el concepto."
            else:
                texto_bot = "No tienes productos en el carrito para confirmar."

        response_data = get_data_pedido(pedido) # Obtenemos items y total actualizado
        response_data['status'] = status_respuesta
        response_data['respuesta_bot'] = texto_bot

        return JsonResponse(response_data)

    except Exception as e:
        print(f"Error en vista: {e}")
        return JsonResponse({'status': 'error', 'respuesta_bot': 'Error interno del servidor.'}, status=500)
