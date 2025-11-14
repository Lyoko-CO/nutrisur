from django.urls import path
from .views import CitaListView

urlpatterns = [
    # Citas se accede vía /citas/
    path('', CitaListView.as_view(), name='mis_citas'),
]