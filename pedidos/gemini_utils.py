import google.generativeai as genai
from django.conf import settings
from productos.models import Producto
import json

def obtener_respuesta_gemini(mensaje_usuario):
    """
    Procesa el mensaje del usuario usando Gemini y devuelve una respuesta estructurada.
    """
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # 1. Obtener el catálogo actual de la base de datos
        productos = Producto.objects.all()
        catalogo_texto = "\n".join([f"- ID: {p.id}, Nombre: {p.nombre}, Precio: {p.precio}€" for p in productos])

        # 2. Configurar el modelo y el prompt del sistema
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt_sistema = f"""
        Eres 'NutriBot', el asistente virtual de ventas de NutriSur.
        
        CATÁLOGO DISPONIBLE:
        {catalogo_texto}
        
        TU OBJETIVO:
        Ayudar al usuario a elegir productos y añadirlos a su pedido.
        
        INSTRUCCIONES DE RESPUESTA (IMPORTANTE):
        Debes responder SIEMPRE en formato JSON estricto. No añadas texto fuera del JSON.
        
        El JSON debe tener esta estructura:
        {{
            "texto_respuesta": "Tu respuesta amable al cliente aquí...",
            "acciones": [
                {{ "tipo": "agregar", "producto_nombre": "Nombre Exacto del Producto", "cantidad": 1 }},
                {{ "tipo": "eliminar", "producto_nombre": "Nombre exacto del producto", "cantidad": 1 }}
            ],
            "finalizar_pedido": false
        }}
        
        REGLAS:
        1. Si el usuario quiere comprar algo, busca el nombre más parecido en el catálogo.
        2. Si encuentras el producto, añade la acción "agregar_producto" al JSON.
        3. Si el usuario no desea añadir mas productos al pedido, pon "finalizar_pedido": true.
        4. Sé amable y breve.
        """

        # 3. Construir el historial para el contexto (simplificado)
        chat_completo = prompt_sistema + "\n\n"
        # Aquí podrías añadir mensajes anteriores si los guardaras en BD
        
        chat_completo += f"Cliente: {mensaje_usuario}\nNutriBot (JSON):"

        # 4. Generar respuesta
        response = model.generate_content(chat_completo)
        texto_limpio = response.text.replace('```json', '').replace('```', '').strip()
        
        return json.loads(texto_limpio)

    except Exception as e:
        print(f"Error Gemini: {e}")
        # Respuesta de emergencia si falla la IA
        return {
            "texto_respuesta": "Lo siento, tuve un problema procesando tu solicitud. ¿Podrías repetirlo?",
            "acciones": [],
            "finalizar_pedido": False
        }