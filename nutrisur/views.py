from django.shortcuts import render

def home_view(request):
    """
    Esta vista se encarga de renderizar la página de inicio.
    """
    # Simplemente le decimos a Django que renderice el archivo 'home.html'
    # que se encuentra en nuestro directorio 'templates'.
    return render(request, 'home.html')

def opciones_compra_view(request):
    """
    Vista intermedia para que el usuario elija entre el Chatbot
    o la web oficial de Herbalife.
    """
    return render(request, 'opciones_compra.html')

def sobre_mi_view(request):
    return render(request, 'sobre_mi.html')