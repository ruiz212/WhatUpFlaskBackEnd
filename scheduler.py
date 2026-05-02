import logging
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from services.calendar_service import get_calendar_service
from services.email_service import send_daily_summary

def job_send_daily_summary():
    """Trabajo programado: Obtiene eventos de mañana y envía un correo."""
    logging.info("Iniciando ejecución de tarea programada: Resumen diario...")
    service = get_calendar_service()
    if not service:
        logging.warning("No se puede generar resumen diario sin acceso a Google Calendar.")
        return
        
    try:
        # Calcular el rango para el día de mañana (UTC)
        tomorrow = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        start_of_tomorrow = tomorrow.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        end_of_tomorrow = tomorrow.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary', timeMin=start_of_tomorrow,
            timeMax=end_of_tomorrow, maxResults=20, singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        parsed_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            parsed_events.append({
                "title": event.get('summary', 'Evento'),
                "time": start
            })
            
        # Llamar al servicio de email
        send_daily_summary(parsed_events)
    except Exception as e:
        logging.error(f"Error en el job de resumen diario: {e}")

def start_scheduler():
    """Inicializa y arranca el cron job con APScheduler."""
    scheduler = BackgroundScheduler()
    # Programado para ejecutarse todos los días a las 20:00 (ajustable a tu servidor)
    scheduler.add_job(job_send_daily_summary, 'cron', hour=20, minute=0)
    scheduler.start()
    logging.info("APScheduler iniciado correctamente (Resumen programado para las 20:00).")
