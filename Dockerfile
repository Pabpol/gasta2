# 🐳 Dockerfile para Railway - Sistema de Gestión de Gastos
# Usa Python 3.11 slim para optimizar el tamaño de la imagen

FROM python:3.11-slim

# Instalar dependencias del sistema necesarias (incluyendo Node.js 20)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Configurar PYTHONPATH para que Python encuentre los módulos
ENV PYTHONPATH=/app/backend_gastos:${PYTHONPATH}

# Copiar archivos de dependencias primero (para aprovechar cache de Docker)
COPY backend_gastos/requirements.txt backend_gastos/requirements.txt

# Instalar dependencias de Pythons
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend_gastos/requirements.txt

# Copiar todo el proyecto
COPY . .

# Crear directorios necesarios para datos
RUN mkdir -p backend_gastos/data backend_gastos/models

# Construir frontend para producción
RUN cd frontend_dashboard && \
    npm ci && \
    npm run build

# Copiar archivos del frontend construido al directorio estático del backend
RUN rm -rf backend_gastos/static/* && \
    cp -r frontend_dashboard/.svelte-kit/output/client/* backend_gastos/static/ && \
    mkdir -p backend_gastos/static/_app && \
    cp -r frontend_dashboard/.svelte-kit/output/client/_app/* backend_gastos/static/_app/ && \
    cp frontend_dashboard/.svelte-kit/output/client/index.html backend_gastos/static/ 2>/dev/null || true

# Exponer puerto (Railway lo asigna automáticamente)
EXPOSE 8000

# No CMD - Railway usará el startCommand del railway.json