# 🐳 Dockerfile para Backend FastAPI
# Este archivo define cómo construir el contenedor del backend

# PASO 1: Imagen base con Python 3.11
FROM python:3.11-slim

# PASO 2: Configurar directorio de trabajo dentro del contenedor
WORKDIR /app

# PASO 3: Instalar dependencias del sistema (si las necesitamos)
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# PASO 4: Copiar y instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# PASO 5: Copiar todo el código del backend
COPY . .

# PASO 6: Crear directorios necesarios
RUN mkdir -p data models config

# PASO 7: Exponer el puerto 8000
EXPOSE 8000

# PASO 8: Comando para iniciar el servidor
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
