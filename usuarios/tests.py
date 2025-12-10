from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.messages import get_messages

User = get_user_model()

class UsuariosModelTests(TestCase):
    """
    Tests para la lógica interna del modelo CustomUser y su Manager.
    """

    def test_crear_usuario_exitoso(self):
        """Caso Positivo: Crear usuario con todos los campos requeridos."""
        user = User.objects.create_user(
            email='juan@test.com',
            nombre='Juan Pérez',
            telefono='123456789',
            password='password123'
        )
        self.assertEqual(user.email, 'juan@test.com')
        self.assertEqual(user.nombre, 'Juan Pérez')
        self.assertTrue(user.check_password('password123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_vip)

    def test_crear_superuser_exitoso(self):
        """Caso Positivo: Crear superusuario debe tener permisos especiales."""
        admin = User.objects.create_superuser(
            email='admin@test.com',
            nombre='Admin',
            password='adminpass'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)

    def test_crear_usuario_sin_email(self):
        """Caso Negativo: No se puede crear usuario sin email."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email=None, nombre='Juan', telefono='000000000', password='123')

    def test_crear_usuario_sin_nombre(self):
        """Caso Negativo: No se puede crear usuario sin nombre."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='test@test.com', nombre='', telefono='000000000', password='123')

    def test_metodo_str(self):
        """Caso Positivo: La representación en string es 'Nombre, (Email)'."""
        user = User.objects.create_user(
            email='a@b.com', 
            nombre='Pepe', 
            telefono='123456789',
            password='123'
        )
        self.assertEqual(str(user), "Pepe, (a@b.com)")

    def test_registrar_compra_logica_historial(self):
        """
        Caso Lógica: El historial debe guardar los últimos productos comprados,
        evitar duplicados consecutivos y limitarse a 6 elementos.
        """
        user = User.objects.create_user(
            email='hist@test.com', 
            nombre='Hist', 
            telefono='111222333',
            password='123'
        )
        
        user.registrar_compra([10, 20])
        user.refresh_from_db()
        self.assertEqual(user.historial_productos, [10, 20])
        
        user.registrar_compra([30])
        user.refresh_from_db()
        self.assertEqual(user.historial_productos, [30, 10, 20])
        
        user.registrar_compra([20]) 
        user.refresh_from_db()
        self.assertEqual(user.historial_productos, [20, 30, 10]) 
        
        user.registrar_compra([40, 50, 60, 70])
        user.refresh_from_db()
        self.assertEqual(len(user.historial_productos), 6)
        self.assertEqual(user.historial_productos, [40, 50, 60, 70, 20, 30])


class UsuariosViewTests(TestCase):
    """
    Tests para las vistas: Registro, Login, Logout y Perfil.
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='login@test.com',
            nombre='Login User',
            telefono='999888777',
            password='password123'
        )
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.registro_url = reverse('registro')
        self.perfil_url = reverse('perfil')

    # --- REGISTRO ---
    def test_registro_view_get(self):
        """Caso Positivo: La página de registro carga correctamente."""
        response = self.client.get(self.registro_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/registro.html')

    def test_registro_view_post_exitoso(self):
        """Caso Positivo: Un registro válido redirige al login."""
        data = {
            'email': 'nuevo@test.com',
            'nombre': 'Nuevo Usuario',
            'telefono': '666000111',
            'password1': 'segura123',
            'password2': 'segura123',
            'terminos': True
        }
        response = self.client.post(self.registro_url, data)
        
        self.assertRedirects(response, self.login_url)
        
        self.assertTrue(User.objects.filter(email='nuevo@test.com').exists())
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('éxito', str(messages[0]))

    def test_registro_view_post_email_duplicado(self):
        """Caso Negativo: No se puede registrar un email que ya existe."""
        data = {
            'email': 'login@test.com',
            'nombre': 'Impostor',
            'telefono': '123456789',
            'password1': 'pass',
            'password2': 'pass',
            'terminos': True
        }
        response = self.client.post(self.registro_url, data)
        
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('Ya existe Usuario con este Email', form.errors['email'][0])

    def test_registro_view_post_passwords_no_coinciden(self):
        """Caso Negativo: Las contraseñas deben ser iguales."""
        data = {
            'email': 'badpass@test.com',
            'nombre': 'Bad Pass',
            'telefono': '123456789',
            'password1': 'clave1',
            'password2': 'clave2',
            'terminos': True
        }
        response = self.client.post(self.registro_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no coinciden")

    # --- LOGIN ---
    def test_login_exitoso(self):
        """Caso Positivo: Login con credenciales correctas."""
        response = self.client.post(self.login_url, {
            'username': 'login@test.com',
            'password': 'password123'
        })
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.id)

    def test_login_fallido(self):
        """Caso Negativo: Login con contraseña incorrecta."""
        response = self.client.post(self.login_url, {
            'username': 'login@test.com',
            'password': 'WRONGPASSWORD'
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertTrue(form.errors.get('__all__')) 

    # --- PERFIL Y ACCESO ---
    def test_perfil_acceso_denegado_anonimo(self):
        """Caso Negativo: Un usuario anónimo intenta ver perfil y es redirigido."""
        response = self.client.get(self.perfil_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.perfil_url}")

    def test_perfil_acceso_permitido_logueado(self):
        """Caso Positivo: Usuario logueado ve su perfil."""
        self.client.force_login(self.user)
        response = self.client.get(self.perfil_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.nombre)
        self.assertContains(response, self.user.email)

    # --- LOGOUT ---
    def test_logout_view(self):
        """Caso Positivo: Cerrar sesión funciona."""
        self.client.force_login(self.user)
        response = self.client.post(self.logout_url)
        
        self.assertRedirects(response, reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)