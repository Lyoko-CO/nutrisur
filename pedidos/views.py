from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Pedido

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
