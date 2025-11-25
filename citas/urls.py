from django.urls import path
from .views import CitaListView
from . import views

urlpatterns = [
    path('mis-citas', CitaListView.as_view(), name='mis_citas'),
    path('nueva-cita', views.chatbot_view, name='nueva_cita'),
    path('procesar-mensaje', views.procesar_mensaje_view, name='procesar_mensaje_cita'),
    path('cancelar/<int:cita_id>/', views.cancelar_cita_view, name='cancelar_cita'),
    path('modificar/<int:cita_id>/', views.modificar_cita_view, name='modificar_cita'),
]