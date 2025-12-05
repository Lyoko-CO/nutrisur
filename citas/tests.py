import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Cita
from .utils.dates import parse_user_date
from unittest.mock import patch

User = get_user_model()

class DateUtilsTests(TestCase):
    '''
    Pruebas de la detección y parseo de fechas y horas del bot de citas.
    '''
    def test_parse_fechas_validas(self):
        manana = timezone.now() + timedelta(days=1)
        res = parse_user_date("mañana")
        self.assertIsNotNone(res)
        self.assertEqual(res.day, manana.day)

        futuro = "25/12/2028"
        res = parse_user_date(futuro)
        self.assertEqual(res.year, 2028)
        self.assertEqual(res.month, 12)
        self.assertEqual(res.day, 25)

    def test_parse_fechas_pasadas(self):
        ayer = (timezone.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        res = parse_user_date(ayer)
        self.assertIsNone(res)

    def test_parse_horas(self):
        res = parse_user_date("mañana a las 17:30")
        self.assertEqual(res.hour, 17)
        self.assertEqual(res.minute, 30)


class ChatbotFlowTest(TestCase):
    '''
    Pruebas del flujo de conversación con el chatbot de citas.
    '''
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='chat@test.com', nombre='Chat User', telefono='123456789', password='pass')
        self.client.force_login(self.user)
        self.url = reverse('procesar_mensaje_cita')

    @patch('citas.views.consultar_gemini_citas')
    def test_flujo_continuar_conversacion(self, mock_gemini):
        mock_gemini.return_value = {
            "texto_respuesta": "¿A qué hora te viene bien?",
            "datos_extraidos": {
                "fecha": "2025-12-25",
                "hora": None,
                "observaciones": None
            },
            "intencion": "continuar",
            "resetear": False
        }

        data = {'mensaje': 'Quiero cita para navidad'}
        response = self.client.post(self.url, json.dumps(data), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        resp_json = response.json()
        
        self.assertEqual(resp_json['status'], 'ok')
        self.assertIn('hora', resp_json['datos_cita'])
        
        session = self.client.session
        self.assertEqual(session['cita_temporal']['fecha'], "2025-12-25")
        self.assertIsNone(session['cita_temporal']['hora'])

    @patch('citas.views.consultar_gemini_citas')
    def test_flujo_confirmar_reserva(self, mock_gemini):
        session = self.client.session
        session['cita_temporal'] = {
            'fecha': '2025-12-25',
            'hora': None,
            'observaciones': None
        }
        session.save()

        mock_gemini.return_value = {
            "texto_respuesta": "Perfecto, reservado.",
            "datos_extraidos": {
                "fecha": "2025-12-25",
                "hora": "10:00",
                "observaciones": "Sin dolor"
            },
            "intencion": "confirmar",
            "resetear": False
        }

        data = {'mensaje': 'A las 10 de la mañana'}
        response = self.client.post(self.url, json.dumps(data), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'finalizado')
        
        cita = Cita.objects.filter(usuario=self.user).last()
        self.assertIsNotNone(cita)
        self.assertEqual(cita.estado, 'PENDIENTE')
        hora_local = timezone.localtime(cita.fecha).hour
        self.assertEqual(hora_local, 10)
        self.assertEqual(cita.observaciones, "Sin dolor")
        
        session = self.client.session
        self.assertNotIn('cita_temporal', session)

    @patch('citas.views.consultar_gemini_citas')
    def test_flujo_resetear(self, mock_gemini):
        """Simula que el usuario pide cancelar/reiniciar"""
        mock_gemini.return_value = {
            "texto_respuesta": "Entendido, empezamos de nuevo.",
            "datos_extraidos": {},
            "intencion": "cancelar",
            "resetear": True
        }

        response = self.client.post(self.url, json.dumps({'mensaje': 'Cancelar'}), content_type='application/json')
        
        self.assertEqual(response.json()['status'], 'reset')
        self.assertIsNone(response.json()['datos_cita'])


class CitaViewsTest(TestCase):
    '''
    Pruebas del manejo de citas desde las vistas (listar, cancelar, modificar).
    '''
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@test.com', 
            nombre='Test User',
            telefono='123456789',
            password='password'
        )
        self.client.force_login(self.user)
        
        self.fecha_futura = timezone.now() + timedelta(days=5)

    def test_lista_mis_citas(self):
        Cita.objects.create(usuario=self.user, fecha=self.fecha_futura, estado='PENDIENTE')
        
        response = self.client.get(reverse('mis_citas'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mis Citas')
        self.assertEqual(len(response.context['citas']), 1)

    def test_cancelar_cita_exito(self):
        cita = Cita.objects.create(usuario=self.user, fecha=self.fecha_futura, estado='PENDIENTE')
        
        url = reverse('cancelar_cita', args=[cita.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        
        cita.refresh_from_db()
        self.assertEqual(cita.estado, 'CANCELADA')

    def test_cancelar_cita_ajena_error(self):
        otro_user = User.objects.create_user(email='otro@test.com', nombre='Otro', telefono='123456789', password='pass')
        cita_ajena = Cita.objects.create(usuario=otro_user, fecha=self.fecha_futura, estado='PENDIENTE')
        
        url = reverse('cancelar_cita', args=[cita_ajena.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)

    def test_modificar_cita_logica(self):
        cita = Cita.objects.create(
            usuario=self.user, 
            fecha=self.fecha_futura, 
            estado='PENDIENTE',
            observaciones="Nota original"
        )
        
        url = reverse('modificar_cita', args=[cita.id])
        response = self.client.get(url)
        
        self.assertRedirects(response, reverse('nueva_cita'))
        
        cita.refresh_from_db()
        self.assertEqual(cita.estado, 'CANCELADA')
        
        session = self.client.session
        self.assertIn('cita_temporal', session)
        self.assertEqual(session['cita_temporal']['observaciones'], "Nota original")


class CitaAdminTest(TestCase):
    '''
    Pruebas del panel de administración para las citas.
    '''
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com', 
            nombre='Admin',
            telefono='987654321',
            password='password123'
        )
        self.client.force_login(self.admin_user)
        
        self.cita = Cita.objects.create(
            usuario=self.admin_user,
            fecha=timezone.now(),
            estado='PENDIENTE',
            observaciones="Test admin"
        )

    def test_admin_citas_list_view(self):
        url = reverse('admin:citas_cita_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test admin")

    def test_admin_filtro_estados_personalizado(self):
        url = reverse('admin:citas_cita_change', args=[self.cita.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        self.assertNotContains(response, '<option value="BORRADOR">')
        self.assertContains(response, '<option value="CONFIRMADA">')

    def test_admin_cambio_estado_cita(self):
        url = reverse('admin:citas_cita_change', args=[self.cita.id])
        datos_formulario = {
            'usuario': self.admin_user.id,
            'fecha_0': '2025-12-25',
            'fecha_1': '10:00:00',
            'estado': 'CONFIRMADA',
            'observaciones': 'Validado por admin'
        }

        response = self.client.post(url, datos_formulario)

        self.assertEqual(response.status_code, 302)

        self.cita.refresh_from_db()
        
        self.assertEqual(self.cita.estado, 'CONFIRMADA')
        self.assertEqual(self.cita.observaciones, 'Validado por admin')