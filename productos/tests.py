from django.test import TestCase
from .models import Producto
from decimal import Decimal

class ProductoTests(TestCase):
    def setUp(self):
        self.producto = Producto.objects.create(
            nombre='Batido Fresa',
            descripcion='Delicioso batido',
            precio=Decimal('50.50'),
            enlace_img='http://imagen.com/fresa.jpg'
        )

    def test_modelo_producto(self):
        """Prueba la creación y representación del modelo"""
        self.assertEqual(self.producto.nombre, 'Batido Fresa')
        self.assertEqual(self.producto.precio, 50.50)
        self.assertEqual(str(self.producto), 'Batido Fresa')

    def test_precio_decimal(self):
        """Asegura que el precio se guarde como Decimal"""
        self.assertIsInstance(self.producto.precio, Decimal)
