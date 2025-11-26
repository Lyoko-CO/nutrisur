import google.generativeai as genai
from django.conf import settings
from django.utils import timezone
from citas.models import ConfiguracionChatbotCitas
import json
import os
import locale

# Intentamos establecer locale para que Python sepa los días en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    pass

def consultar_gemini_citas(mensaje_usuario, datos_actuales, slots_ocupados):
    """
    Procesa el mensaje del usuario para gestionar una cita.
    datos_actuales: Diccionario con lo que ya sabemos {'fecha': ..., 'hora': ...}
    """
    try:
        api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY'))
        if not api_key:
            return None
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash') 

        # 1. Contexto Temporal (Fundamental para entender "mañana" o "el lunes")
        ahora = timezone.localtime(timezone.now())
        contexto_tiempo = f"Hoy es {ahora.strftime('%A, %d de %B de %Y')}. Hora actual: {ahora.strftime('%H:%M')}."

        config_db = ConfiguracionChatbotCitas.objects.first()
        instrucciones_extra = ""
        if config_db:
            instrucciones_extra = f"""
            REGLAS ESPECIALES DEL CENTRO:
            {config_db.instrucciones_adicionales}
            """

        # 2. Prompt del Sistema (Las reglas del negocio)
        prompt = f"""
        Eres el recepcionista virtual de 'NutriSur' (Centro de bienestar).
        {contexto_tiempo}

        ESTADO ACTUAL DE LA RESERVA (Lo que ya sabemos):
        - Fecha: {datos_actuales.get('fecha') or 'No definida'}
        - Hora: {datos_actuales.get('hora') or 'No definida'}
        - Observaciones: {datos_actuales.get('observaciones') or 'Ninguna'}

        --------------------------------------------------------
        ⚠️ AGENDA OCUPADA (NO RESERVAR EN ESTAS FECHAS/HORAS) ⚠️
        {slots_ocupados}
        --------------------------------------------------------

        {instrucciones_extra}

        TU MISIÓN:
        1. Analizar el mensaje del usuario.
        2. Extraer información nueva (Día, Hora u Observaciones).
        3. Validar que la cita sea FUTURA y en HORARIO COMERCIAL.
        4. Generar una respuesta amable pidiendo el dato que falte o confirmando.
        5. Validar disponibilidad: Si el usuario pide una fecha/hora que está en la lista de "AGENDA OCUPADA", dile amablemente que está ocupado y sugiere otra hora cercana.
        
        REGLAS DE HORARIO:
        - Lunes a Viernes.
        - Mañanas: 10:00 a 14:00.
        - Tardes: 17:00 a 21:00.
        - Fines de semana CERRADO.
        (Las horas de cierre son EXCLUSIVAS, no se puede reservar a esa hora).

        INSTRUCCIONES DE RESPUESTA (JSON ESTRICTO):
        Responde SOLO con un JSON con esta estructura:
        {{
            "texto_respuesta": "Tu respuesta amable al usuario...",
            "datos_extraidos": {{
                "fecha": "YYYY-MM-DD" (formato ISO, o null si no se menciona),
                "hora": "HH:MM" (formato 24h, o null si no se menciona),
                "observaciones": "Texto extraído" (o null)
            }},
            "intencion": "continuar" | "cancelar" | "confirmar",
            "resetear": false (pon true si el usuario quiere cancelar/reiniciar)
        }}

        Si el usuario quiere cancelar o reiniciar, pon "resetear": true.
        Si el usuario solo da información nueva, pon "intencion": "continuar".
        Si el usuario quiere cancelar la cita, pon "intencion": "cancelar".
        Si el usuario no da observaciones, pregunta amablemente si desea añadir alguna antes de confirmar la cita.
        Si el usuario expresa que es válida la respuesta y TIENES fecha y hora válidas, pon "intencion": "confirmar".
        Si la fecha/hora pedida está cerrada o es pasada, explícalo en "texto_respuesta" y pon los datos como null.
        Si el usuario no proporciona una hora con los minutos en 00 no es válida, pidele que sea exacta.

        Usuario dice: "{mensaje_usuario}"
        """

        response = model.generate_content(prompt)
        # Limpieza por si la IA devuelve bloques de código markdown
        texto_limpio = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(texto_limpio)

    except Exception as e:
        print(f"Error Gemini Citas: {e}")
        return {
            "texto_respuesta": "Disculpa, mi sistema de IA está teniendo problemas. ¿Podrías repetir?",
            "intencion": "error"
        }