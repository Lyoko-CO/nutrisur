import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from unittest.mock import patch
from productos.models import Producto
from pedidos.models import Pedido
from citas.models import Cita

User = get_user_model()

class FlujoUsuarioNutrisurTest(TestCase):

    def setUp(self):
        self.patcher = patch('threading.Thread')
        self.mock_thread = self.patcher.start()
        
        def run_synchronously(target, *args, **kwargs):
            class SyncThread:
                def start(self):
                    target(*args, **kwargs)
            return SyncThread()
            
        self.mock_thread.side_effect = run_synchronously

        self.client = Client()
        
        self.usuario = User.objects.create_user(
            email='cliente@test.com',
            nombre='Cliente Tester',
            telefono='123456789',
            password='password123',
            is_vip=True
        )
        
        self.prod1 = Producto.objects.create(nombre="Batido Fresa", precio=35.50)
        self.prod2 = Producto.objects.create(nombre="Té Verde", precio=20.00)

        mail.outbox = []

    def tearDown(self):
        self.patcher.stop()

    @patch('pedidos.views.obtener_respuesta_gemini') 
    def test_historia_compra_completa(self, mock_gemini):
        self.client.force_login(self.usuario)

        mock_gemini.return_value = {
            "texto_respuesta": "He añadido el Batido de Fresa a tu carrito.",
            "acciones": [
                { "tipo": "agregar", "producto_nombre": "Batido Fresa", "cantidad": 2 }
            ],
            "finalizar_pedido": False
        }

        url_chat = reverse('procesar_mensaje_pedido')
        response = self.client.post(
            url_chat, 
            json.dumps({'mensaje': 'Quiero dos batidos de fresa'}), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        pedido = Pedido.objects.get(usuario=self.usuario, estado='B')
        self.assertEqual(pedido.pedidoproducto_set.count(), 1)
        self.assertEqual(pedido.calcular_total(), 71.00)

        mock_gemini.return_value = {
            "texto_respuesta": "Pedido confirmado.",
            "acciones": [],
            "finalizar_pedido": True
        }

        response = self.client.post(
            url_chat, 
            json.dumps({'mensaje': 'Eso es todo, gracias'}), 
            content_type='application/json'
        )

        self.assertEqual(response.json()['status'], 'finalizado')

        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'P')

        self.assertEqual(len(mail.outbox), 2)
        
        asuntos = [m.subject for m in mail.outbox]
        self.assertTrue(any("Nuevo Pedido Recibido" in s for s in asuntos))


    @patch('citas.views.consultar_gemini_citas')
    def test_historia_reserva_cita(self, mock_gemini_citas):

        self.client.force_login(self.usuario)
        url_cita = reverse('procesar_mensaje_cita')

        mock_gemini_citas.return_value = {
            "texto_respuesta": "¿Te va bien a las 10:00?",
            "datos_extraidos": {
                "fecha": "2025-12-25",
                "hora": "10:00",
                "observaciones": "Dolor de espalda"
            },
            "intencion": "continuar",
            "resetear": False
        }

        self.client.post(
            url_cita, 
            json.dumps({'mensaje': 'Quiero cita para navidad por la mañana'}), 
            content_type='application/json'
        )

        session = self.client.session
        self.assertEqual(session['cita_temporal']['fecha'], '2025-12-25')

        mock_gemini_citas.return_value = {
            "texto_respuesta": "Perfecto, reservada.",
            "datos_extraidos": {},
            "intencion": "confirmar",
            "resetear": False
        }

        response = self.client.post(
            url_cita, 
            json.dumps({'mensaje': 'Sí, perfecto'}), 
            content_type='application/json'
        )

        self.assertEqual(response.json()['status'], 'finalizado')

        cita_db = Cita.objects.filter(usuario=self.usuario).last()
        self.assertIsNotNone(cita_db)
        self.assertEqual(cita_db.estado, 'PENDIENTE')
        self.assertEqual(cita_db.observaciones, "Dolor de espalda")

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Nueva Cita de Masaje", mail.outbox[0].subject)