import os
import sys
# Agregar el directorio actual al path para que encuentre 'services'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.calendar_service import get_upcoming_availability

try:
    print("Validando archivo credentials.json...")
    if not os.path.exists('credentials.json'):
        print("ERROR: No se encuentra el archivo 'credentials.json' en la carpeta flask_backend.")
        sys.exit(1)
        
    print("Archivo encontrado. Intentando conectar con Google Calendar API...")
    events = get_upcoming_availability()
    
    if events is None:
        print("ERROR: La conexión devolvió None. Revisa los permisos de la API de Google Calendar.")
    else:
        print("\n✅ SUCCESS: ¡Conexión al calendario exitosa!")
        print(f"📅 Próximos eventos encontrados en tu agenda: {len(events)}")
        for e in events:
            print(f"   - {e['title']} ({e['time']})")
except Exception as e:
    print(f"\n❌ ERROR de validación: {e}")
