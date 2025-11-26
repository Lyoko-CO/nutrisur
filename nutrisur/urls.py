"""
URL configuration for nutrisur project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from . import views
from pedidos import views as pedidos_views


urlpatterns = [
    path('', views.home_view, name='home'),
    path('comprar/', views.opciones_compra_view, name='opciones_compra'),
    path('admin/', admin.site.urls),
    path('pedidos/', include('pedidos.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('citas/', include('citas.urls')),
    path('sobre-mi/', views.sobre_mi_view, name='sobre_mi'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)