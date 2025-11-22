from django.urls import path
from .views import CitaListView
from . import views

urlpatterns = [
    path('mis-citas', CitaListView.as_view(), name='mis_citas'),
    path('nueva-cita', views.chatbot_view, name='nueva_cita'),
    path('procesar-mensaje', views.procesar_mensaje_view, name='procesar_mensaje_cita'),
]