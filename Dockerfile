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
    echo "=== SVELTE BUILD OUTPUT STRUCTURE ===" && \
    find frontend_dashboard/.svelte-kit/output/client/ -name "index.html" -o -name "*.js" -o -name "*.css" | head -10 && \
    echo "=== COPYING ALL FILES ===" && \
    cp -r frontend_dashboard/.svelte-kit/output/client/* backend_gastos/static/ 2>/dev/null || true && \
    echo "=== SPECIFICALLY COPYING INDEX.HTML ===" && \
    cp frontend_dashboard/.svelte-kit/output/client/index.html backend_gastos/static/index.html 2>/dev/null || echo "Failed to copy index.html" && \
    echo "=== FINAL STATIC DIRECTORY CONTENTS ===" && \
    ls -la backend_gastos/static/ && \
    echo "=== VERIFYING INDEX.HTML EXISTS ===" && \
    test -f backend_gastos/static/index.html && echo "✅ index.html found!" || echo "❌ index.html missing!"

# Exponer puerto (Railway lo asigna automáticamente)
EXPOSE 8000

# No CMD - Railway usará el startCommand del railway.json