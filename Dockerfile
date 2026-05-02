FROM python:3.11-slim

WORKDIR /app

# Copiar el archivo de requerimientos
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Variables de entorno
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5000

# Usar Gunicorn para producción
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
