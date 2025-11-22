import json
from django.shortcuts import render
from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from django.template.defaultfilters import date as date_format
from datetime import datetime
from .models import Cita
from .utils.dates import parse_user_date

class CitaListView(LoginRequiredMixin, ListView):
    model = Cita
    template_name="citas/mis_citas.html"
    context_object_name = 'citas'
    
    def get_queryset(self):
        return Cita.objects.filter(usuario=self.request.user).order_by('fecha')
    
@login_required
def chatbot_view(request):
    if 'cita_temporal' in request.session:
        del request.session['cita_temporal']
    

    mensaje_inicial = f"¡Hola {request.user.nombre}! ... ¿Qué <strong>día</strong> te viene bien?"

    context = {
        'mensaje_inicial': mensaje_inicial 
    }
    
    return render(request, 'citas/chatbot.html', context)

@login_required
@require_POST
def procesar_mensaje_view(request):
    try:
        data = json.loads(request.body)
        mensaje_usuario = (data.get('mensaje', '') or '').strip()
        mensaje_lower = mensaje_usuario.lower()

        # 1. RECUPERAR DATOS DE LA SESIÓN (Memoria temporal)
        # Usamos un diccionario simple, no el modelo de base de datos
        datos_temp = request.session.get('cita_temporal', {
            'fecha_iso': None,  # Guardaremos fecha como string ISO
            'hora_fijada': False, # Flag para saber si ya tenemos la hora
            'observaciones': None
        })

        respuesta_texto = ""
        status_respuesta = 'ok'
        cita_guardada_db = None # Para devolver al final si se guarda

        # COMANDO GLOBAL DE CANCELACIÓN
        if any(x in mensaje_lower for x in ['cancelar', 'borrar', 'inicio', 'empezar de nuevo']):
            # Borramos la sesión
            if 'cita_temporal' in request.session:
                del request.session['cita_temporal']
            
            return JsonResponse({
                'status': 'reset',
                'respuesta_bot': "He reiniciado la reserva. Empecemos de nuevo: ¿Qué <strong>día</strong> te gustaría venir?",
                'datos_cita': None
            })

        # --- MÁQUINA DE ESTADOS (Usando diccionario en sesión) ---

        # PASO 1: AGENDAR DÍA (Si no tenemos fecha guardada)
        if not datos_temp['fecha_iso']:
            # Parseamos fecha
            nueva_fecha = parse_user_date(mensaje_usuario, default_hour=0, default_minute=0)
            
            if nueva_fecha:
                # Guardamos en sesión como STRING (las sesiones no guardan objetos datetime)
                datos_temp['fecha_iso'] = nueva_fecha.replace(hour=0, minute=0, second=0).isoformat()
                datos_temp['hora_fijada'] = False
                
                # Actualizamos sesión
                request.session['cita_temporal'] = datos_temp
                
                fecha_bonita = date_format(nueva_fecha, "l j \d\e F")
                respuesta_texto = f"Vale, apuntado el {fecha_bonita}. ¿A qué <strong>hora</strong> te viene bien?"
            else:
                respuesta_texto = "No he entendido el día. Prueba diciendo algo simple como 'Lunes', 'Mañana' o '15 de Mayo'."

        # PASO 2: AGENDAR HORA (Si tenemos fecha, pero el flag de hora es False)
        elif not datos_temp['hora_fijada']:
            # Recuperamos la fecha que teníamos guardada (string -> datetime)
            fecha_guardada = datetime.fromisoformat(datos_temp['fecha_iso'])
            
            # Detectamos solo la hora
            hora_detectada = parse_user_date(mensaje_usuario)
            
            if hora_detectada:
                # Combinamos día guardado + hora nueva
                fecha_completa = fecha_guardada.replace(
                    hour=hora_detectada.hour,
                    minute=hora_detectada.minute,
                    tzinfo=hora_detectada.tzinfo # Importante mantener la zona horaria
                )
                
                if fecha_completa < timezone.now():
                     respuesta_texto = "Esa hora ya ha pasado. Por favor dime una hora futura."
                else:
                    # Guardamos la fecha completa y marcamos hora como OK
                    datos_temp['fecha_iso'] = fecha_completa.isoformat()
                    datos_temp['hora_fijada'] = True
                    
                    request.session['cita_temporal'] = datos_temp
                    
                    fecha_str = fecha_completa.strftime('%d/%m a las %H:%M')
                    respuesta_texto = (
                        f"Perfecto: {fecha_str}. "
                        "Por último, ¿tienes alguna <strong>observación</strong>, dolor o comentario? (Escribe 'no' si todo está bien)."
                    )
            else:
                respuesta_texto = "No he entendido la hora. Por favor, usa un formato como '17:00', '5 de la tarde' o '10:30'."

        # PASO 3: OBSERVACIONES Y GUARDADO FINAL EN DB
        else:
            # 1. Procesar observaciones
            obs = mensaje_usuario
            if any(x in mensaje_lower for x in ['no', 'nada', 'ninguna', 'todo bien']):
                obs = "Sin observaciones"
            
            # 2. RECUPERAR FECHA FINAL
            fecha_final = datetime.fromisoformat(datos_temp['fecha_iso'])
            
            # 3. ¡¡AQUÍ ES DONDE GUARDAMOS EN LA BASE DE DATOS!!
            # Solo llegamos aquí si todo lo anterior ha ido bien.
            nueva_cita = Cita.objects.create(
                usuario=request.user,
                fecha=fecha_final,
                observaciones=obs,
                estado='PENDIENTE' # Directamente pendiente, nos saltamos BORRADOR
            )
            
            # 4. Limpiamos la sesión (ya no necesitamos los datos temporales)
            del request.session['cita_temporal']
            
            respuesta_texto = f"¡Reserva confirmada! Te esperamos el {fecha_final.strftime('%A %d a las %H:%M')}. Gracias."
            status_respuesta = 'finalizado'
            cita_guardada_db = nueva_cita

        # PREPARAR RESPUESTA JSON PARA EL FRONTEND
        datos_frontend = None
        
        # Si acabamos de guardar en DB, mandamos esos datos
        if cita_guardada_db:
             datos_frontend = {
                'fecha': cita_guardada_db.fecha.strftime('%d/%m/%Y'),
                'hora': cita_guardada_db.fecha.strftime('%H:%M'),
                'observaciones': cita_guardada_db.observaciones,
                'estado': cita_guardada_db.estado
            }
        # Si estamos a medias (en sesión), construimos los datos desde el diccionario temporal
        elif datos_temp['fecha_iso']:
            dt_obj = datetime.fromisoformat(datos_temp['fecha_iso'])
            datos_frontend = {
                'fecha': dt_obj.strftime('%d/%m/%Y'),
                # Si hora_fijada es False, mostramos "Pendiente"
                'hora': dt_obj.strftime('%H:%M') if datos_temp['hora_fijada'] else 'Pendiente',
                'observaciones': '-',
                'estado': 'BORRADOR' # Solo para visualización visual en el front
            }

        return JsonResponse({
            'status': status_respuesta,
            'respuesta_bot': respuesta_texto,
            'datos_cita': datos_frontend
        })

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'status': 'error', 'respuesta_bot': 'Error técnico.'}, status=500)