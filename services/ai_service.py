import os
import json
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
# Inicializar el cliente oficial y actualizado de Gemini
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

def process_message_for_events(message: str) -> dict:
    """Extrae eventos usando LLM y devuelve dict o None."""
    import datetime
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=f"Eres un asistente de extracción. Hoy es {today}. Analiza el mensaje. Si hay una tarea, evento o reunión, devuelve ÚNICAMENTE un objeto JSON válido con las claves: title, date (YYYY-MM-DD), time (HH:MM), description. Si no hay eventos, devuelve la palabra null.",
                temperature=0.0
            )
        )
        
        content = response.text.strip()
        
        # Limpiar posibles bloques de código Markdown
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        if content.lower() == "null" or not content:
            return None
            
        event_json = json.loads(content)
        return event_json
        
    except json.JSONDecodeError:
        logging.error(f"Gemini no devolvió un JSON válido. Respuesta en crudo: {content}")
        return None
    except Exception as e:
        logging.error(f"Error en AI Service (extracción con Gemini): {e}")
        return None

def generate_availability_response(message: str, availability, history: str = "") -> str:
    """Genera una respuesta natural basada en disponibilidad y memoria reciente."""
    try:
        if availability == "NOT_CONFIGURED":
            events_str = "[SISTEMA]: El usuario NO ha conectado su Google Calendar (falta el archivo credentials.json). Si te pide leer o agendar eventos, avísale amablemente que debe añadir ese archivo a la carpeta flask_backend para que funcione la magia."
        else:
            events_str = "\n".join([f"- {e['title']} ({e['time']})" for e in availability]) if availability else "No hay eventos programados para los próximos 7 días."
        
        system_prompt = (
            "Eres el asistente personal avanzado del usuario (Zair). Tu trabajo es gestionar su agenda, recordar su estado personal y enviar archivos cuando te lo pidan.\n"
            f"Esta es la información de su agenda:\n{events_str}\n\n"
        )
        
        BOSS_NUMBER = os.getenv("BOSS_NUMBER", "")
        if history:
            system_prompt += (
                f"Aquí tienes el historial reciente del chat (Memoria a corto plazo):\n{history}\n\n"
                "REGLAS DEL ASISTENTE AVANZADO:\n"
                f"1. ESTADO PERSONAL: El número o usuario '{BOSS_NUMBER}' pertenece a Zair (el jefe). Si en el historial ves que ese usuario indica su estado (ej. 'estoy ocupado', 'salí a almorzar', 'estoy en clase'), apréndetelo como la verdad absoluta. Si alguien más en un grupo menciona a Zair o pregunta por él, infórmales su estado actual amigablemente excusándolo.\n"
                "2. GESTIÓN DE ARCHIVOS: Si en el historial alguien envía un archivo (verás que dice literalmente [ARCHIVO ADJUNTO RECIBIDO]: nombre.ext), recuerda que ese archivo existe. Si alguien pide que reenvíes o pases ese archivo, puedes hacerlo.\n"
                "3. CÓMO ENVIAR ARCHIVOS: Para enviar un archivo, DEBES incluir AL FINAL EXACTO de tu respuesta esta etiqueta: [ENVIAR_ARCHIVO:nombre.ext] (reemplazando nombre.ext por el nombre del archivo).\n"
                "Ejemplo de respuesta tuya: 'Claro, aquí tienes el documento que pidió Zair. [ENVIAR_ARCHIVO:reporte.pdf]'\n"
            )
            
        system_prompt += "Responde de forma natural, corta y profesional. Actúa como el mejor y más inteligente asistente."

        response = client.models.generate_content(
            model=model_name,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7
            )
        )
        return response.text.strip()
    except Exception as e:
        logging.error(f"Error en AI Service (respuesta con Gemini): {e}")
        return "Hubo un problema al procesar la respuesta."

def generate_auto_summary(history: str) -> str:
    """Genera un resumen automático de los últimos N mensajes para enviarlo al jefe."""
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Haz un resumen detallado y muy claro de la siguiente conversación. Destaca si hay algo importante para el jefe (Zair).",
            config=types.GenerateContentConfig(
                system_instruction=f"Eres el asistente de IA de Zair. Se han acumulado muchos mensajes en el grupo mientras él no estaba. Aquí tienes el historial:\n{history}\n\nTu tarea es resumirlo en un solo mensaje fácil de leer, separando temas o puntos clave si es necesario.",
                temperature=0.4
            )
        )
        return response.text.strip()
    except Exception as e:
        logging.error(f"Error generando resumen automático: {e}")
        return "No se pudo generar el resumen debido a un error."
