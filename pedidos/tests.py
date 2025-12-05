import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch
from .models import Pedido, PedidoProducto
from productos.models import Producto

User = get_user_model()

class PedidosBaseTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.user = User.objects.create_user(
            email='cliente@test.com',
            nombre='Cliente Normal',
            telefono='600123456',
            password='pass'
        )
        
        self.vip_user = User.objects.create_user(
            email='vip@test.com',
            nombre='Cliente VIP',
            telefono='700123456',
            password='pass',
            is_vip=True
        )
        
        self.prod1 = Producto.objects.create(nombre='Aloe Vera', precio=10.00)
        self.prod2 = Producto.objects.create(nombre='Té Verde', precio=20.00)
        self.prod3 = Producto.objects.create(nombre='Batido Fresa', precio=35.00)

# --- 1. TESTS DE ACCESO Y SEGURIDAD (Casos Negativos y Positivos) ---
class PedidosAccessTests(PedidosBaseTest):
    
    def test_acceso_chatbot_usuario_normal_denegado(self):
        """Caso Negativo: Un usuario NO VIP intenta entrar al chatbot y es redirigido."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('chatbot_pedidos'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('opciones_compra'), response.url)
        
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn("reservado para clientes VIP", str(messages[0]))

    def test_acceso_chatbot_usuario_vip_permitido(self):
        """Caso Positivo: Un usuario VIP entra y obtiene código 200."""
        self.client.force_login(self.vip_user)
        response = self.client.get(reverse('chatbot_pedidos'))
        self.assertEqual(response.status_code, 200)

    def test_seguridad_cancelar_pedido_ajeno(self):
        """Caso Negativo: Usuario intenta cancelar el pedido de OTRO usuario."""
        pedido_ajeno = Pedido.objects.create(usuario=self.user, estado='P')
        
        self.client.force_login(self.vip_user)
        
        url = reverse('cancelar_pedido', args=[pedido_ajeno.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        
        pedido_ajeno.refresh_from_db()
        self.assertEqual(pedido_ajeno.estado, 'P')


# --- 2. TESTS DE GESTIÓN DE PEDIDOS (Lógica de Negocio) ---
class PedidosManagementTests(PedidosBaseTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_cancelar_pedido_pendiente_exito(self):
        """Caso Positivo: Cancelar un pedido pendiente."""
        pedido = Pedido.objects.create(usuario=self.user, estado='P')
        
        url = reverse('cancelar_pedido', args=[pedido.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'C')

    def test_cancelar_pedido_realizado_fallo(self):
        """Caso Negativo: No se puede cancelar un pedido ya enviado (Realizado)."""
        pedido = Pedido.objects.create(usuario=self.user, estado='R')
        
        url = reverse('cancelar_pedido', args=[pedido.id])
        self.client.get(url)
        
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'R')

    def test_modificar_pedido_intercambio_borradores(self):
        """
        Caso Complejo: El usuario tiene un carrito activo (Borrador) y quiere editar
        un pedido antiguo (Pendiente). El sistema debe intercambiarlos.
        """
        carrito_actual = Pedido.objects.create(usuario=self.user, estado='B')
        carrito_actual.agregar_producto(self.prod1)
        
        pedido_antiguo = Pedido.objects.create(usuario=self.user, estado='P')
        pedido_antiguo.agregar_producto(self.prod2)
        
        url = reverse('modificar_pedido', args=[pedido_antiguo.id])
        self.client.get(url)
        
        carrito_actual.refresh_from_db()
        pedido_antiguo.refresh_from_db()
        
        self.assertEqual(carrito_actual.estado, 'P')
        
        self.assertEqual(pedido_antiguo.estado, 'B')


# --- 3. TESTS DE API Y CHATBOT (Integración Mockeada) ---
class PedidosAPITests(PedidosBaseTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.vip_user)

    def test_api_decrementar_hasta_eliminar(self):
        """Caso Positivo: Si bajo la cantidad a 0, el ítem desaparece."""
        pedido = Pedido.objects.create(usuario=self.vip_user, estado='B')
        pp = pedido.agregar_producto(self.prod1, 1)
        
        url = reverse('actualizar_cantidad')
        data = {'id_producto': self.prod1.id, 'accion': 'decrementar'}
        
        self.client.post(url, data, content_type='application/json')
        
        exists = PedidoProducto.objects.filter(id=pp.id).exists()
        self.assertFalse(exists)

    @patch('pedidos.views.obtener_respuesta_gemini')
    def test_chatbot_producto_inexistente(self, mock_gemini):
        """
        Caso Negativo: La IA sugiere un producto que no existe en nuestra BD.
        El sistema no debe fallar.
        """

        mock_gemini.return_value = {
            "texto_respuesta": "Añadiendo Coca Cola.",
            "acciones": [
                { "tipo": "agregar", "producto_nombre": "Coca Cola", "cantidad": 1 }
            ],
            "finalizar_pedido": False
        }

        url = reverse('procesar_mensaje_pedido')
        response = self.client.post(url, {'mensaje': 'Quiero coca cola'}, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        pedido = Pedido.objects.get(usuario=self.vip_user, estado='B')
        self.assertEqual(pedido.pedidoproducto_set.count(), 0)

    @patch('pedidos.views.obtener_respuesta_gemini')
    def test_chatbot_busqueda_aproximada(self, mock_gemini):
        """Caso Positivo: La IA devuelve 'Batido' y el sistema encuentra 'Batido Fresa'."""
        mock_gemini.return_value = {
            "texto_respuesta": "Añadido.",
            "acciones": [
                { "tipo": "agregar", "producto_nombre": "Batido", "cantidad": 1 }
            ],
            "finalizar_pedido": False
        }

        url = reverse('procesar_mensaje_pedido')
        self.client.post(url, {'mensaje': 'dame un batido'}, content_type='application/json')
        
        pedido = Pedido.objects.get(usuario=self.vip_user, estado='B')
        self.assertTrue(pedido.pedidoproducto_set.filter(producto=self.prod3).exists())