from django.test import TestCase
from .models import CustomUser

# Create your tests here.
class CustomUserModelTest(TestCase):
    def test_crear_usuario(self):
        user = CustomUser.objects.create_user(
            email='test@correo.com',
            nombre='Juan',
            telefono='123456789',
            password='segura123'
        )
        self.assertEqual(user.email, 'test@correo.com')
        self.assertTrue(user.check_password('segura123'))
        self.assertFalse(user.is_staff)
        
    def test_crear_superusuario(self):
        superuser = CustomUser.objects.create_superuser(
            email='admin@correo.com',
            nombre='Admin',
            password='admin123'
        )
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
