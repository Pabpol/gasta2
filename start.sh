#!/bin/bash
# Script de inicio para Railway
# Maneja el puerto dinámicamente asignado por Railway

# Usar puerto asignado por Railway o 8000 por defecto
PORT=${PORT:-8000}

echo "Starting application on port $PORT"

# Ejecutar uvicorn con el puerto correcto
exec uvicorn backend_gastos.app:app --host 0.0.0.0 --port $PORT