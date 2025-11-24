import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch
from .models import Pedido, PedidoProducto
from productos.models import Producto

User = get_user_model()

class PedidosFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        # CORRECCIÓN: Añadido el campo 'telefono'
        self.user = User.objects.create_user(
            email='cliente@test.com', 
            nombre='Cliente', 
            telefono='600123456',
            password='pass'
        )
        self.client.force_login(self.user)
        
        # Productos de prueba
        self.prod1 = Producto.objects.create(nombre='Aloe Vera', precio=10.00)
        self.prod2 = Producto.objects.create(nombre='Té Verde', precio=20.00)

    def test_vista_lista_pedidos(self):
        """Verifica que se ven los pedidos propios"""
        Pedido.objects.create(usuario=self.user, estado='P')
        response = self.client.get(reverse('mis_pedidos'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['pedidos']), 1)

    def test_actualizar_cantidad_api(self):
        """Prueba la API interna de incrementar/decrementar"""
        # Crear pedido borrador
        pedido = Pedido.objects.create(usuario=self.user, estado='B')
        pedido.agregar_producto(self.prod1, 1)
        
        url = reverse('actualizar_cantidad')
        
        # 1. Incrementar
        data_inc = {'id_producto': self.prod1.id, 'accion': 'incrementar'}
        resp = self.client.post(url, data_inc, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['total_pedido'], 20.0) # 2 * 10
        
        # 2. Decrementar (borrar)
        # Bajamos a 1
        self.client.post(url, {'id_producto': self.prod1.id, 'accion': 'decrementar'}, content_type='application/json')
        # Bajamos a 0 (se borra)
        resp = self.client.post(url, {'id_producto': self.prod1.id, 'accion': 'decrementar'}, content_type='application/json')
        self.assertEqual(resp.json()['total_pedido'], 0.0)
        self.assertFalse(PedidoProducto.objects.filter(pedido=pedido).exists())

    @patch('pedidos.views.obtener_respuesta_gemini')
    def test_chatbot_procesar_mensaje_agregar(self, mock_gemini):
        """
        Simula que el usuario pide 'Aloe' y Gemini devuelve la instrucción JSON correcta.
        """
        # Configuramos el Mock para que devuelva lo que devolvería Gemini
        mock_gemini.return_value = {
            "texto_respuesta": "He añadido Aloe Vera.",
            "acciones": [
                { "tipo": "agregar", "producto_nombre": "Aloe", "cantidad": 2 }
            ],
            "finalizar_pedido": False
        }

        url = reverse('procesar_mensaje_pedido')
        data = {'mensaje': 'Quiero 2 áloes'}
        
        response = self.client.post(url, data, content_type='application/json')
        
        # Verificaciones
        self.assertEqual(response.status_code, 200)
        json_resp = response.json()
        
        self.assertEqual(json_resp['status'], 'ok')
        self.assertEqual(json_resp['total_pedido'], 20.0) # 2 * 10.00
        
        # Verificar DB
        pedido = Pedido.objects.get(usuario=self.user, estado='B')
        self.assertEqual(pedido.pedidoproducto_set.first().cantidad, 2)

    @patch('pedidos.views.obtener_respuesta_gemini')
    def test_chatbot_finalizar_pedido(self, mock_gemini):
        """Simula confirmar el pedido"""
        # Preparamos un pedido con algo
        pedido = Pedido.objects.create(usuario=self.user, estado='B')
        pedido.agregar_producto(self.prod1)

        mock_gemini.return_value = {
            "texto_respuesta": "Pedido confirmado.",
            "acciones": [],
            "finalizar_pedido": True
        }

        response = self.client.post(
            reverse('procesar_mensaje_pedido'), 
            {'mensaje': 'Confirmar'}, 
            content_type='application/json'
        )
        
        self.assertEqual(response.json()['status'], 'finalizado')
        
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'P') # Debe haber pasado a Pendiente
