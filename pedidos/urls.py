from django.urls import path
from . import views

urlpatterns = [
    path('mis-pedidos', views.lista_pedidos_view, name="mis_pedidos")
]
