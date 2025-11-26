import google.generativeai as genai
from django.conf import settings
from pedidos.models import Pedido, ConfiguracionChatbot
from productos.models import Producto
import json

conversaciones = {}

def obtener_respuesta_gemini(mensaje_usuario, request):
    """
    Procesa el mensaje del usuario usando Gemini y devuelve una respuesta estructurada.
    """
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # 1. Obtener el catálogo actual de la base de datos
        productos = Producto.objects.all()
        catalogo_texto = "\n".join([f"- ID: {p.id}, Nombre: {p.nombre}, Precio: {p.precio}€" for p in productos])

        config_db = ConfiguracionChatbot.objects.first()
        instrucciones_extra = ""
        if config_db and config_db.activado:
            instrucciones_extra = f"""
            NOTAS DEL ADMINISTRADOR (Prioridad Alta):
            {config_db.instrucciones_sistema}
            """

        # 2. Obtener o crear el historial del usuario
        usuario_id = request.user.id
        if usuario_id not in conversaciones:
            conversaciones[usuario_id] = []
        
        historial = conversaciones[usuario_id]

        # 3. Configurar el modelo y el prompt del sistema
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
        
        {instrucciones_extra}
        
        REGLAS:
        1. Si el usuario quiere comprar algo, busca el nombre más parecido en el catálogo.
        2. Si encuentras el producto, añade la acción "agregar" al JSON.
        3. Si el usuario quiere eliminar un producto, añade la acción "eliminar" al JSON.
        4. Si el usuario quiere cancelar su pedido, elimina todos los productos del pedido.
        5. Si el usuario no desea añadir mas productos al pedido, pon "finalizar_pedido": true.
        6. Si el usuario quiere añadir o eliminar un producto pero no lo nombra, se refiere al último producto mencionado.
        7. Si el usuario quiere añadir o eliminar un prodcuto pero el nombre no coincide con ningún producto del catálogo, se refiere al último producto mencionado en el historial con el nombre parecido.
        8. Sé amable y breve.
        9. Pide confirmación antes de finalizar el pedido.
        10. Al finalizar el pedido, resume los productos añadidos y el total a pagar.
        """

        # 4. Construir el historial para el contexto (simplificado)
        chat_completo = prompt_sistema + "\n\n--- HISTORIAL DE CONVERSACIÓN ---\n"
        
        for msg in historial:
            if msg['remitente'] == 'usuario':
                chat_completo += f"Cliente: {msg['contenido']}\n"
            else:
                chat_completo += f"NutriBot: {msg['contenido']}\n"
        
        # 5. Obtener estado actual del pedido
        pedido = Pedido.objects.get(usuario=request.user, estado='B')
        estado_pedido = get_data_pedido(pedido)
        
        chat_completo += f"\nEstado actual del pedido: {json.dumps(estado_pedido, ensure_ascii=False)}\n"
        chat_completo += f"Cliente: {mensaje_usuario}\nNutriBot (JSON):"

        # 6. Generar respuesta
        response = model.generate_content(chat_completo)
        texto_limpio = response.text.replace('```json', '').replace('```', '').strip()
        
        respuesta_json = json.loads(texto_limpio)
        
        # 7. Guardar en la variable historial
        historial.append({
            'remitente': 'usuario',
            'contenido': mensaje_usuario
        })
        
        historial.append({
            'remitente': 'bot',
            'contenido': respuesta_json.get('texto_respuesta', '')
        })
        
        respuesta_json['historial'] = historial

        return respuesta_json

    except Exception as e:
        print(f"Error Gemini: {e}")
        # Respuesta de emergencia si falla la IA
        return {
            "texto_respuesta": "Lo siento, tuve un problema procesando tu solicitud. ¿Podrías repetirlo?",
            "acciones": [],
            "finalizar_pedido": False
        }
    
def get_data_pedido(pedido):
    """Devuelve el estado actual del pedido en formato diccionario para JSON"""
    items = []
    for pp in pedido.pedidoproducto_set.all().select_related('producto'):
        items.append({
            'id_producto': pp.producto.id,
            'nombre': pp.producto.nombre,
            'precio_unitario': float(pp.producto.precio),
            'cantidad': pp.cantidad,
            'subtotal': float(pp.producto.precio * pp.cantidad)
        })
    
    return {
        'total_pedido': float(pedido.calcular_total()),
        'items': items
    }