from django.shortcuts import render

def home_view(request):
    """
    Esta vista se encarga de renderizar la página de inicio.
    """
    # Simplemente le decimos a Django que renderice el archivo 'home.html'
    # que se encuentra en nuestro directorio 'templates'.
    return render(request, 'home.html')