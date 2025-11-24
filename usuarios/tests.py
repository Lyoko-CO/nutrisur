from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from productos.models import Producto

User = get_user_model()

class UsuariosTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_data = {
            'email': 'test@ejemplo.com',
            'nombre': 'Usuario Test',
            'password': 'password123',
            'telefono': '123456789'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_crear_usuario_modelo(self):
        """Verifica que el CustomUser se crea correctamente"""
        self.assertEqual(self.user.email, 'test@ejemplo.com')
        self.assertTrue(self.user.check_password('password123'))
        self.assertEqual(str(self.user), 'Usuario Test, (test@ejemplo.com)')

    def test_registrar_compra_logica(self):
        """Prueba que el historial de productos rota correctamente (max 6)"""
        # Creamos 7 productos ficticios
        prod_ids = [i for i in range(1, 8)]
        
        # El usuario compra los 7 productos
        self.user.registrar_compra(prod_ids)
        self.user.refresh_from_db()
        
        # Debe tener solo 6
        self.assertEqual(len(self.user.historial_productos), 6)
        # El 1 (el más antiguo en la lista enviada) debería haber salido si la lógica es FIFO
        # pero tu lógica pone los nuevos al principio.
        # Si pasas [1,2,3,4,5,6,7], el historial guarda los primeros 6 de esa lista + lo que había.
        self.assertIn(1, self.user.historial_productos) 
        
    def test_login_view(self):
        """Verifica que se puede iniciar sesión"""
        login_url = reverse('login')
        response = self.client.post(login_url, {
            'username': 'test@ejemplo.com', # Django Auth usa 'username' en el form aunque sea email
            'password': 'password123'
        })
        # Redirección significa login exitoso (código 302)
        self.assertEqual(response.status_code, 302) 
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_perfil_view_access(self):
        """Verifica que solo usuarios logueados ven el perfil"""
        self.client.logout()
        response = self.client.get(reverse('perfil'))
        self.assertNotEqual(response.status_code, 200) # Debe redirigir
        
        self.client.login(email='test@ejemplo.com', password='password123')
        response = self.client.get(reverse('perfil'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usuario Test')
