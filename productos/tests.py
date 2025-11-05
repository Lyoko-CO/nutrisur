from django.test import TestCase
from productos.models import Producto

class ProductoModelTest(TestCase):
    def test_creacion_producto(self):
        prod = Producto.objects.create(nombre='Manzana', descripcion='Roja', precio=2.5)
        self.assertEqual(prod.nombre, 'Manzana')
        self.assertEqual(str(prod), 'Manzana')  # si tu __str__ devuelve el nombre
