from django.urls import path
from . import views

urlpatterns = [
    path('mis-pedidos', views.lista_pedidos_view, name="mis_pedidos"),
    
    path('nuevo-pedido', views.chatbot_view, name="chatbot_pedidos"),
    path('procesar-mensaje-pedido', views.procesar_mensaje_view, name="procesar_mensaje_pedido"),
    
]
