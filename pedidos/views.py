from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Pedido
from productos.models import Producto
from django.http import JsonResponse
from django.views.decorators.http import require_POST
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

    productos_escaparate = Producto.objects.all()[:10]
    
    context = {
        'pedido': pedido,
        'productos_escaparate': productos_escaparate
    }
    
    return render(request, 'pedidos/chatbot.html', context)

@login_required
@require_POST
def procesar_mensaje_view(request):
    """
    API interna: Recibe un mensaje del usuario, lo procesa
    y añade productos al pedido pendiente.
    """
    try:
        data = json.loads(request.body)
        mensaje_usuario = data.get('mensaje', '').lower()
        pedido = Pedido.objects.get(usuario=request.user, estado='B')

        # --- AQUÍ EMPIEZA LA LÓGICA MEJORADA ---
        
        # 1. Manejar finalización primero
        if 'finalizar' in mensaje_usuario or 'confirmar' in mensaje_usuario or 'nada más' in mensaje_usuario:
            '''if not pedido.productos.exists():
                return JsonResponse({
                    'status': 'error',
                    'respuesta_bot': 'Tu pedido está vacío. ¿Quieres añadir algún producto?'
                })'''
            if not pedido.productos_chat:
                return JsonResponse({   
                    'status': 'error',
                    'respuesta_bot': 'Tu pedido está vacío. ¿Quieres añadir algún producto?'
                })
                
            pedido.estado = 'P' # Pendiente
            pedido.save()
            return JsonResponse({
                'status': 'finalizado',
                'respuesta_bot': f'¡Pedido confirmado! Muchas gracias.'
            })

        # 2. Búsqueda dinámica de productos
        productos_disponibles = Producto.objects.all()
        productos_anadidos = []
        respuesta_bot = ""

        '''for producto in productos_disponibles:
            # Comprueba si el nombre del producto está en el mensaje
            if producto.nombre.lower() in mensaje_usuario:
                
                # Lógica de cantidad (sigue siendo simple, pero funciona)
                cantidad = 1
                if 'dos' in mensaje_usuario or '2' in mensaje_usuario:
                    cantidad = 2
                if 'tres' in mensaje_usuario or '3' in mensaje_usuario:
                    cantidad = 3
                
                # Usamos el método que YA tenías en tu models.py
                pedido.agregar_producto(producto, cantidad)
                productos_anadidos.append(f"{cantidad} x {producto.nombre}")'''
        
        pedido.agregar_producto_chat(mensaje_usuario)
        pedido.save()
        nuevo_producto = pedido.productos_chat[-1]
        
        if nuevo_producto: 
            respuesta_bot = "¿Algo mas?"
            return JsonResponse({
                'status': 'ok',
                'respuesta_bot': respuesta_bot,
            })
        else:
            return JsonResponse({
                'status': 'error',
                'respuesta_bot': 'No he reconocido ningún producto en esa frase. ¿Puedes ser más específico? (Ej: "Batido de Fresa")'
            })
        

        # 3. Generar la respuesta
        '''if productos_anadidos:
            # Si encontramos productos, lo decimos
            respuesta_bot = f"He añadido: {', '.join(productos_anadidos)}. ¿Algo más?"
            total = pedido.calcular_total()
            return JsonResponse({
                'status': 'ok',
                'respuesta_bot': respuesta_bot,
                'total_pedido': total
            })
        else:
            # Si no encontramos nada, pedimos ayuda
            return JsonResponse({
                'status': 'error',
                'respuesta_bot': 'No he reconocido ningún producto en esa frase. ¿Puedes ser más específico? (Ej: "Batido de Fresa")'
            })
            '''
    # --- FIN DE LA LÓGICA MEJORADA ---

    except Pedido.DoesNotExist:
        return JsonResponse({'status': 'error', 'respuesta_bot': 'Error: No se encontró un pedido activo.'}, status=404)
    except Exception as e:
        # No deberíamos mostrar 'e' al usuario, pero es útil para depurar
        print(f"Error en procesar_mensaje_view: {str(e)}")
        return JsonResponse({'status': 'error', 'respuesta_bot': f'Ha ocurrido un error inesperado.'}, status=500)