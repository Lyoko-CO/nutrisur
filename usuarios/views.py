from django.shortcuts import render, redirect
# Quita la importación 'login' que ya no usaremos aquí
# from django.contrib.auth import login 

# ¡Añade la importación de 'messages'!
from django.contrib import messages 
from .forms import CustomUserCreationForm

def register_view(request):
    """
    Gestiona el registro de nuevos usuarios.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        
        if form.is_valid():
            # Solo guardamos al usuario
            user = form.save()
            print("Usuario registrado:", user)
            
            # --- MODIFICACIONES ---
            
            # 1. Quita esta línea (ya no logueamos al usuario)
            # login(request, user) 
            
            # 2. Añade un mensaje de éxito
            messages.success(request, '¡Te has registrado con éxito! Ahora puedes iniciar sesión.')
            
            # 3. Redirige a 'login' en lugar de 'home'
            return redirect('login') 
            
            # --- FIN DE MODIFICACIONES ---
            
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'registro.html', {'form': form})
