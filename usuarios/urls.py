from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name="login"),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name="logout"),
    path('registro/', views.register_view, name="registro"),
    
    path('perfil/', views.perfil_view, name="perfil"),
]
