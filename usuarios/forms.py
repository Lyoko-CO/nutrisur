from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
# ¡Importa esto para manejar los errores correctamente!
from django.core.exceptions import ValidationError 

User = get_user_model() 

class CustomUserCreationForm(UserCreationForm):
    """
    Un formulario de creación de usuario que funciona con 
    nuestro CustomUser (que usa 'email' como username).
    """
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'nombre', 'telefono')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asumiendo que el teléfono es opcional, como en tu modelo
        self.fields['telefono'].required = False 
        
    
    # --- ¡ESTA ES LA CORRECCIÓN MÁS IMPORTANTE! ---
    # Sobrescribimos el método 'save' para que SÍ use 
    # nuestro manager 'create_user'
    
    def save(self, commit=True):
        # Limpiamos los datos (comprueba que las contraseñas coinciden, etc.)
        # 'self.cleaned_data' ya está disponible aquí
        
        # Ya no llamamos a super().save()
        # En su lugar, llamamos a nuestro 'create_user'
        try:
            user = User.objects.create_user(
                email=self.cleaned_data['email'],
                nombre=self.cleaned_data['nombre'],
                password=self.cleaned_data['password1'],
                
                # Usamos .get() para manejar el campo opcional 'telefono'
                # Esto funciona con el 'create_user' que corregimos antes
                telefono=self.cleaned_data.get('telefono'),
            )
            return user
        
        except ValueError as e:
            # Si 'create_user' lanza un ValueError (ej. "Email obligatorio"),
            # lo capturamos y lo convertimos en un error de formulario
            # que se mostrará en el bloque 'non_field_errors'.
            raise ValidationError(e)