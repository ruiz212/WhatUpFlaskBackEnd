import os
import datetime
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')

def get_calendar_service():
    """Autentica y devuelve el servicio de Google Calendar."""
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        logging.warning(f"Archivo de credenciales de Calendar ({SERVICE_ACCOUNT_FILE}) no encontrado.")
        return None
        
    try:
        creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        logging.error(f"Error al autenticar con Google Calendar: {e}")
        return None

def add_event_to_calendar(event_data: dict):
    """Inserta un evento extraído por la IA en Google Calendar."""
    service = get_calendar_service()
    if not service: return None
    
    try:
        # Formato esperado en event_data: date: YYYY-MM-DD, time: HH:MM
        start_datetime_str = f"{event_data['date']}T{event_data['time']}:00"
        
        # Asumiendo 1 hora de duración predeterminada
        start_dt = datetime.datetime.strptime(start_datetime_str, "%Y-%m-%dT%H:%M:%S")
        end_dt = start_dt + datetime.timedelta(hours=1)
        
        event = {
          'summary': event_data.get('title', 'Reunión / Tarea Programada'),
          'description': event_data.get('description', 'Agendado automáticamente por el Asistente AI.'),
          'start': {
            'dateTime': start_dt.isoformat(),
            'timeZone': 'America/Mexico_City', # Ajusta a tu zona horaria
          },
          'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': 'America/Mexico_City',
          },
        }

        event_result = service.events().insert(calendarId='primary', body=event).execute()
        return event_result
    except Exception as e:
        logging.error(f"Error insertando evento: {e}")
        return None

def get_upcoming_availability() -> list:
    """Obtiene los eventos programados para los próximos 7 días."""
    service = get_calendar_service()
    if not service: return []
    
    try:
        # Definir rango de fechas (próximos 7 días)
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        end_of_period = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).replace(hour=23, minute=59, second=59).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary', timeMin=now, timeMax=end_of_period, 
            maxResults=30, singleEvents=True, orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        availability = []
        for event in events:
            # Manejar eventos de todo el día vs eventos con hora específica
            start = event['start'].get('dateTime', event['start'].get('date'))
            availability.append({
                "title": event.get('summary', 'Ocupado'),
                "time": start
            })
            
        return availability
    except Exception as e:
        logging.error(f"Error obteniendo disponibilidad: {e}")
        return []
