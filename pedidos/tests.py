from django.test import TestCase
from django.contrib.auth import get_user_model
from productos.models import Producto
from .models import Pedido, PedidoProducto



# Create your tests here.
User = get_user_model()

class PedidoModelTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            email='cliente@test.com',
            nombre='Cliente Test',
            telefono='123456789',
            password='test1234'
        )
        self.prod1 = Producto.objects.create(
                nombre='Manzanas', descripcion='Fruta roja', precio=2.50
            )
        self.prod2 = Producto.objects.create(
                nombre='Peras', descripcion='Fruta verde', precio=3.00
            )
        
        self.pedido = Pedido.objects.create(usuario=self.usuario)
        
    def test_str(self):
        texto = str(self.pedido)
        self.assertIn(f"Pedido #{self.pedido.id}", texto)
        self.assertIn(self.usuario.nombre, texto)

    def test_agregar_producto(self):
        self.pedido.agregar_producto(self.prod1, cantidad=2)
        relacion = PedidoProducto.objects.get(pedido=self.pedido, producto=self.prod1)
        self.assertEqual(relacion.cantidad, 2)
        self.assertEqual(self.pedido.productos.count(), 1)
        
    def test_agregar_productos_suma_cantidad(self):
        self.pedido.agregar_producto(self.prod1, cantidad=2)
        self.pedido.agregar_producto(self.prod1, cantidad=3)
        relacion = PedidoProducto.objects.get(pedido=self.pedido, producto=self.prod1)
        self.assertEqual(relacion.cantidad, 5)
        
    def test_calcular_total(self):
        self.pedido.agregar_producto(self.prod1, cantidad=2)  
        self.pedido.agregar_producto(self.prod2, cantidad=1) 
        total = self.pedido.calcular_total()
        self.assertEqual(total, 8.0)

    def test_cliente_datos(self):
        self.assertEqual(self.pedido.cliente_nombre, 'Cliente Test')
        self.assertEqual(self.pedido.cliente_email, 'cliente@test.com')
        self.assertEqual(self.pedido.cliente_telefono, '123456789')


