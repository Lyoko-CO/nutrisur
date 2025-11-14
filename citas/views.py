from django.shortcuts import render
from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
# Create your views here.
from .models import Cita


class CitaListView(LoginRequiredMixin, ListView):
    model = Cita
    template_name="citas/mis_citas.html"
    context_object_name = 'citas'
    
    
    def get_queryset(self):
        return Cita.objects.filter(usuario=self.request.user).order_by('fecha')
    