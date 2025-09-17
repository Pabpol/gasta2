# 🐳 Dockerfile para Railway - Sistema de Gestión de Gastos
# Usa Python 3.11 slim para optimizar el tamaño de la imagen

FROM python:3.11-slim

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias primero (para aprovechar cache de Docker)
COPY backend_gastos/requirements.txt backend_gastos/requirements.txt

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend_gastos/requirements.txt

# Copiar todo el proyecto
COPY . .

# Crear directorios necesarios para datos
RUN mkdir -p backend_gastos/data backend_gastos/models

# Exponer puerto (Railway lo asigna automáticamente)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Comando de inicio
CMD ["uvicorn", "backend_gastos.app:app", "--host", "0.0.0.0", "--port", "8000"]