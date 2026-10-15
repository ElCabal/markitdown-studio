# Imagen base ligera con Python 3.12
FROM python:3.12-slim

# Evitar prompts interactivos y buffers de Python
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Instalar dependencias del sistema necesarias para audio y PDFs
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar librerías
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto (frontend estático, app.py, etc.)
COPY . .

# Hugging Face Spaces usa el puerto 7860 por defecto; Render/Koyeb usan la variable $PORT
ENV PORT=7860
EXPOSE 7860

# Comando de inicio compatible con Render, Hugging Face y Koyeb
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
