import os
import json
import logging
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from services.ai_service import process_message_for_events, generate_availability_response, generate_auto_summary
from services.calendar_service import add_event_to_calendar, get_upcoming_availability
from services.excel_service import log_to_excel, get_recent_history
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()
app = Flask(__name__)

ALLOWED_GROUPS = os.getenv("ALLOWED_GROUPS", "").split(",")
BOSS_NUMBER = os.getenv("BOSS_NUMBER", "505XXXXXXXX@c.us")
SUMMARY_THRESHOLD = int(os.getenv("SUMMARY_THRESHOLD", "150"))
COUNTERS_FILE = "group_counters.json"

def get_counter(group_id):
    if not os.path.exists(COUNTERS_FILE): return 0
    with open(COUNTERS_FILE, "r") as f: 
        try:
            return json.load(f).get(group_id, 0)
        except:
            return 0

def set_counter(group_id, count):
    data = {}
    if os.path.exists(COUNTERS_FILE):
        with open(COUNTERS_FILE, "r") as f:
            try:
                data = json.load(f)
            except:
                pass
    data[group_id] = count
    with open(COUNTERS_FILE, "w") as f: json.dump(data, f)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400
        
    sender = data.get('from', '')
    author = data.get('author', '')
    body = data.get('body', '')
    is_group = data.get('isGroupMsg', False)
    
    # El verdadero remitente del mensaje
    real_sender = author if author else sender
    
    logging.info(f"Mensaje recibido: de [{real_sender}] en [{sender}] - '{body}'")
    
    # Filtrar por grupo: Solo permitidos
    if is_group:
        if sender not in ALLOWED_GROUPS:
            logging.info("Mensaje de grupo ignorado (no en ALLOWED_GROUPS).")
            return jsonify({"status": "ignored"}), 200
            
        # Lógica de resumen automático de mensajes no leídos
        if real_sender == BOSS_NUMBER:
            # Si el jefe habla en el grupo, se reinicia el contador a 0
            set_counter(sender, 0)
        else:
            # Alguien más habló, aumentar contador
            count = get_counter(sender) + 1
            set_counter(sender, count)
            logging.info(f"Mensajes acumulados en {sender}: {count}/{SUMMARY_THRESHOLD}")
            
            if count >= SUMMARY_THRESHOLD:
                logging.info("Umbral alcanzado. Generando resumen automático para el jefe...")
                history = get_recent_history(limit=SUMMARY_THRESHOLD)
                summary_text = generate_auto_summary(history)
                
                # Enviar resumen por mensaje privado al jefe conectando con Node.js
                try:
                    node_url = os.getenv("NODE_URL", "http://localhost:3000")
                    requests.post(f"{node_url}/send-message", json={
                        "chatId": BOSS_NUMBER,
                        "text": f"🤖 *Resumen Automático del Grupo*\nMientras no estabas, se acumularon {SUMMARY_THRESHOLD} mensajes. Aquí tienes el resumen de lo que hablaron:\n\n{summary_text}"
                    })
                    logging.info("Resumen automático enviado al jefe exitosamente.")
                except Exception as e:
                    logging.error(f"No se pudo enviar el mensaje a Node.js: {e}")
                
                # Reiniciar contador
                set_counter(sender, 0)
        
        # Solo responder o interactuar con el grupo si mencionan a Zair
        if "zair" not in body.lower():
            # Igualmente lo guardamos en Excel en silencio para alimentar el resumen automático
            log_to_excel(real_sender, is_group, body, "Silencio (Guardado para historial)", "")
            return jsonify({"status": "ignored"}), 200

    try:
        # 1. Procesar mensaje con IA para extraer evento
        event_data = process_message_for_events(body)
        
        if event_data:
            logging.info(f"Evento detectado: {event_data}")
            add_event_to_calendar(event_data)
            reply_text = f"📅 ¡Hecho! He agendado: '{event_data.get('title')}' para el {event_data.get('date')} a las {event_data.get('time')}."
            log_to_excel(real_sender, is_group, body, "Evento Agendado", str(event_data))
            return jsonify({"status": "event_scheduled", "reply": reply_text}), 200
        else:
            if not os.path.exists('credentials.json'):
                upcoming_events = "NOT_CONFIGURED"
            else:
                upcoming_events = get_upcoming_availability()
            
            recent_history = get_recent_history(limit=15)
            
            response_text = generate_availability_response(body, upcoming_events, recent_history)
            
            import re
            file_to_send = None
            match = re.search(r'\[ENVIAR_ARCHIVO:(.+?)\]', response_text)
            if match:
                file_to_send = match.group(1).strip()
                response_text = response_text.replace(match.group(0), "").strip()
            
            log_to_excel(real_sender, is_group, body, "Respuesta", response_text)
            
            return jsonify({"status": "replied", "reply": response_text, "file_to_send": file_to_send}), 200

    except Exception as e:
        logging.error(f"Error procesando webhook: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logging.info("Iniciando servidor Flask...")
    start_scheduler()
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
