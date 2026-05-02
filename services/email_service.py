import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_daily_summary(events_list: list):
    """Envía un resumen de los eventos por email usando smtplib."""
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    
    if not all([sender_email, sender_password, recipient_email]):
        logging.error("Credenciales SMTP incompletas. No se enviará el resumen por correo.")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "📅 Tu Asistente AI: Resumen de Agenda para Mañana"
        
        # Formato del correo en HTML
        body = "<h3>Tus eventos programados para mañana:</h3><ul>"
        if not events_list:
            body += "<li>No tienes eventos programados. ¡Tienes el día libre!</li>"
        else:
            for event in events_list:
                body += f"<li><b>{event['time']}</b>: {event['title']}</li>"
        body += "</ul>"
        
        msg.attach(MIMEText(body, 'html'))
        
        # Conexión segura al servidor SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        logging.info("📧 Resumen diario enviado exitosamente por correo.")
    except Exception as e:
        logging.error(f"Error enviando correo SMTP: {e}")
