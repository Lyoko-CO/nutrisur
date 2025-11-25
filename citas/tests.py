import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Cita
from .utils.dates import parse_user_date

User = get_user_model()

class DateUtilsTests(TestCase):
    def test_parse_fechas_validas(self):
        """Prueba que el parser entienda fechas relativas y absolutas"""
        # Mañana
        manana = timezone.now() + timedelta(days=1)
        res = parse_user_date("mañana")
        self.assertIsNotNone(res)
        self.assertEqual(res.day, manana.day)

        # Fecha específica futura (formato español)
        futuro = "25/12/2028"
        res = parse_user_date(futuro)
        self.assertEqual(res.year, 2028)
        self.assertEqual(res.month, 12)
        self.assertEqual(res.day, 25)

    def test_parse_fechas_pasadas(self):
        """Las fechas pasadas deben devolver None"""
        ayer = (timezone.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        res = parse_user_date(ayer)
        self.assertIsNone(res)

    def test_parse_horas(self):
        """Prueba detección de horas"""
        res = parse_user_date("mañana a las 17:30") # Usamos mañana para asegurar futuro
        self.assertEqual(res.hour, 17)
        self.assertEqual(res.minute, 30)
        
        # Usamos "mañana" para evitar que falle si ejecutas el test tarde
        res2 = parse_user_date("mañana 5 pm")
        self.assertIsNotNone(res2)
        self.assertEqual(res2.hour, 17)


class CitaFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        # CORRECCIÓN: Añadido el campo 'telefono'
        self.user = User.objects.create_user(
            email='cita@test.com', 
            nombre='Paciente', 
            telefono='666777888', 
            password='pass'
        )
        self.client.force_login(self.user)
        self.url = reverse('procesar_mensaje_cita')

    def test_flujo_completo_creacion_cita(self):
        # 1. Usuario dice el día ("Mañana")
        resp1 = self.client.post(self.url, json.dumps({'mensaje': 'mañana'}), content_type='application/json')
        self.assertIn('A qué <strong>hora</strong>', resp1.json()['respuesta_bot'])
        
        # Verificar sesión
        session = self.client.session
        self.assertTrue(session['cita_temporal']['fecha_iso'])
        self.assertFalse(session['cita_temporal']['hora_fijada'])

        # 2. Usuario dice la hora ("10:00")
        resp2 = self.client.post(self.url, json.dumps({'mensaje': '10:00'}), content_type='application/json')
        self.assertIn('observación', resp2.json()['respuesta_bot'])
        
        # 3. Usuario confirma observaciones ("Me duele la espalda")
        resp3 = self.client.post(self.url, json.dumps({'mensaje': 'Dolor de espalda'}), content_type='application/json')
        
        # Verificar finalización
        data = resp3.json()
        self.assertEqual(data['status'], 'finalizado')
        self.assertEqual(data['datos_cita']['observaciones'], 'Dolor de espalda')
        
        # Verificar Base de Datos
        cita = Cita.objects.get(usuario=self.user)
        self.assertEqual(cita.estado, 'PENDIENTE')
        self.assertEqual(cita.observaciones, 'Dolor de espalda')

    def test_cancelar_resetea_sesion(self):
        """Si el usuario dice cancelar, se borra la sesión"""
        # Iniciamos una cita
        self.client.post(self.url, json.dumps({'mensaje': 'mañana'}), content_type='application/json')
        
        # Cancelamos
        resp = self.client.post(self.url, json.dumps({'mensaje': 'cancelar'}), content_type='application/json')
        
        self.assertEqual(resp.json()['status'], 'reset')
        self.assertNotIn('cita_temporal', self.client.session)
