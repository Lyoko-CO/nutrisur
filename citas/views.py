import json
from django.shortcuts import render
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect # <--- AÑADIDO
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Cita

# Importamos el nuevo cerebro IA
from .utils.gemini_utils import consultar_gemini_citas


def obtener_horarios_ocupados():
    """
    Devuelve un string con las fechas y horas de citas futuras que ya están ocupadas.
    """
    ahora = timezone.now()
    # Buscamos citas desde ahora hasta dentro de 30 días (para no saturar el prompt)
    limite = ahora + timedelta(days=30)
    
    citas_ocupadas = Cita.objects.filter(
        fecha__range=(ahora, limite),
        estado__in=['PENDIENTE', 'CONFIRMADA']
    ).order_by('fecha')
    
    if not citas_ocupadas.exists():
        return "No hay citas ocupadas. Todo el horario está libre."
    
    lista_txt = []
    for c in citas_ocupadas:
        # Formato legible para la IA: "YYYY-MM-DD HH:MM"
        fecha_str = c.fecha.astimezone(timezone.get_current_timezone()).strftime("%Y-%m-%d %H:%M")
        lista_txt.append(f"- {fecha_str}")
        
    return "\n".join(lista_txt)

class CitaListView(LoginRequiredMixin, ListView):
    model = Cita
    template_name="citas/mis_citas.html"
    context_object_name = 'citas'
    
    def get_queryset(self):
        return Cita.objects.filter(usuario=self.request.user).order_by('fecha')

@login_required
def chatbot_view(request):
    # Reiniciamos sesión al entrar para empezar limpio
    if 'cita_temporal' in request.session and not request.session.pop('keep_session', False):
        del request.session['cita_temporal']
    
    # Obtenemos la última cita real para mostrar algo en el panel (opcional)
    cita_actual = None

    mensaje_inicial = f"¡Hola {request.user.nombre}! Soy tu asistente de bienestar. ¿Cuándo te gustaría reservar tu próxima sesión?"

    context = {
        'cita_actual': cita_actual, 
        'mensaje_inicial': mensaje_inicial 
    }
    return render(request, 'citas/chatbot.html', context)

@login_required
@require_POST
def procesar_mensaje_view(request):
    try:
        data = json.loads(request.body)
        mensaje_usuario = data.get('mensaje', '')

        # 1. Recuperar estado de la sesión (Memoria a corto plazo)
        datos_temp = request.session.get('cita_temporal', {
            'fecha': None,        # Guardaremos string 'YYYY-MM-DD'
            'hora': None,         # Guardaremos string 'HH:MM'
            'observaciones': None
        })
        
        string_ocupados = obtener_horarios_ocupados()

        # 2. SE LA PASAMOS A LA FUNCIÓN DE GEMINI
        # (Tendremos que modificar consultar_gemini_citas para que acepte este argumento)
        respuesta_ai = consultar_gemini_citas(mensaje_usuario, datos_temp, string_ocupados)
        
        # Validación básica por si falla la API
        if not respuesta_ai or respuesta_ai.get('intencion') == 'error':
            return JsonResponse({'status': 'error', 'respuesta_bot': 'Error de conexión con la IA.'}, status=500)

        # 3. Procesar la respuesta de la IA
        datos_nuevos = respuesta_ai.get('datos_extraidos', {})
        intencion = respuesta_ai.get('intencion')
        resetear = respuesta_ai.get('resetear', False)
        texto_bot = respuesta_ai.get('texto_respuesta')

        # CASO A: Usuario quiere cancelar/reiniciar
        if resetear or intencion == 'cancelar':
            if 'cita_temporal' in request.session:
                del request.session['cita_temporal']
            return JsonResponse({
                'status': 'reset',
                'respuesta_bot': texto_bot or "Reserva cancelada. ¿En qué más puedo ayudarte?",
                'datos_cita': None
            })

        # CASO B: Actualizar datos en sesión (IA detectó fecha/hora nuevas)
        if datos_nuevos.get('fecha'): datos_temp['fecha'] = datos_nuevos['fecha']
        if datos_nuevos.get('hora'): datos_temp['hora'] = datos_nuevos['hora']
        if datos_nuevos.get('observaciones'): datos_temp['observaciones'] = datos_nuevos['observaciones']
        
        request.session['cita_temporal'] = datos_temp

        # CASO C: Confirmación y Guardado en BD
        status_respuesta = 'ok'
        
        # Si la IA dice que está confirmado y tenemos los datos mínimos
        if intencion == 'confirmar' and datos_temp['fecha'] and datos_temp['hora']:
            try:
                # Combinar fecha y hora para crear el objeto datetime
                fecha_str = f"{datos_temp['fecha']} {datos_temp['hora']}"
                fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M")
                # Hacerla consciente de la zona horaria (settings.TIME_ZONE)
                fecha_aware = timezone.make_aware(fecha_dt, timezone.get_current_timezone())

                # Crear la cita real en base de datos
                Cita.objects.create(
                    usuario=request.user,
                    fecha=fecha_aware,
                    observaciones=datos_temp.get('observaciones', ''),
                    estado='PENDIENTE'
                )
                
                # Limpiar sesión tras éxito
                del request.session['cita_temporal']
                status_respuesta = 'finalizado'
                
            except ValueError as e:
                print(f"Error formato fecha: {e}")
                texto_bot = "Hubo un error técnico al guardar la fecha. Por favor, inténtalo de nuevo."

        # 4. Preparar datos para actualizar la tabla visual (Frontend)
        # Formateamos la fecha para que se vea bonita (DD/MM/YYYY)
        fecha_visual = datos_temp['fecha']
        if fecha_visual:
            try:
                f_obj = datetime.strptime(fecha_visual, "%Y-%m-%d")
                fecha_visual = f_obj.strftime("%d/%m/%Y")
            except: pass

        datos_frontend = {
            'fecha': fecha_visual,
            'hora': datos_temp['hora'] or 'Pendiente', # Si es None, mostramos texto
            'observaciones': datos_temp['observaciones'] or '-',
            'estado': 'BORRADOR'
        }

        return JsonResponse({
            'status': status_respuesta,
            'respuesta_bot': texto_bot,
            'datos_cita': datos_frontend
        })

    except Exception as e:
        print(f"Error Vista Citas: {e}")
        return JsonResponse({'status': 'error', 'respuesta_bot': 'Ocurrió un error interno.'}, status=500)

@login_required
def cancelar_cita_view(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, usuario=request.user)
    
    if cita.estado in ['PENDIENTE', 'CONFIRMADA']:
        cita.estado = 'CANCELADA'
        cita.save()
        messages.success(request, "Tu cita ha sido cancelada.")
    else:
        messages.error(request, "No se puede cancelar esta cita.")
        
    return redirect('mis_citas')

@login_required
def modificar_cita_view(request, cita_id):
    """
    Para modificar, cancelamos la cita actual y cargamos sus datos
    en el chatbot para que el usuario elija una nueva fecha cómodamente.
    """
    cita = get_object_or_404(Cita, id=cita_id, usuario=request.user)
    
    if cita.estado not in ['PENDIENTE', 'CONFIRMADA']:
        messages.error(request, "Solo puedes modificar citas futuras.")
        return redirect('mis_citas')
    
    # 1. Extraemos datos para pre-rellenar el chat
    # Convertimos a string para el JSON de sesión
    fecha_str = cita.fecha.strftime("%Y-%m-%d")
    hora_str = cita.fecha.strftime("%H:%M")
    
    datos_temp = {
        'fecha': fecha_str,
        'hora': hora_str,
        'observaciones': cita.observaciones
    }
    
    # 2. Guardamos en sesión y activamos la bandera para no borrarlos al entrar
    request.session['cita_temporal'] = datos_temp
    request.session['keep_session'] = True 
    
    # 3. "Cancelamos" la vieja para que no se duplique al confirmar la nueva
    cita.estado = 'CANCELADA'
    cita.save()
    
    messages.info(request, "Vamos a reprogramar tu cita. He guardado tus datos, solo dime la nueva fecha.")
    return redirect('nueva_cita')