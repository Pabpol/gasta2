#!/bin/bash

# 🚀 Script de Deploy Rápido para Railway
# Uso: ./deploy.sh

echo "🚀 SISTEMA DE GASTOS - DEPLOY A RAILWAY"
echo "========================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes coloreados
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar si estamos en el directorio correcto
if [ ! -f "railway.json" ]; then
    print_error "No se encuentra railway.json. Ejecuta este script desde el directorio raíz del proyecto."
    exit 1
fi

print_status "Verificando configuración del proyecto..."

# Verificar archivos necesarios
files_to_check=("railway.json" "Procfile" "backend_gastos/requirements.txt" "backend_gastos/app.py")
for file in "${files_to_check[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Archivo faltante: $file"
        exit 1
    fi
done

print_success "Todos los archivos de configuración están presentes"

# Verificar dependencias
print_status "Verificando dependencias de Python..."
cd backend_gastos

if command -v python3 &> /dev/null; then
    python3 -c "
import sys
try:
    import fastapi, uvicorn, pandas
    print('✅ Dependencias principales OK')
except ImportError as e:
    print(f'❌ Dependencia faltante: {e}')
    sys.exit(1)
"
else
    print_warning "Python3 no encontrado. Las dependencias se verificarán durante el deploy."
fi

cd ..
print_success "Verificación de dependencias completada"

# Crear resumen de deploy
echo ""
echo "📋 RESUMEN DE DEPLOY"
echo "===================="
echo "Proyecto: Sistema de Gestión de Gastos"
echo "Plataforma: Railway"
echo "Tipo: MVP Personal"
echo ""
echo "Archivos de configuración:"
echo "  ✅ railway.json - Configuración de build/deploy"
echo "  ✅ Procfile - Comando de inicio"
echo "  ✅ requirements.txt - Dependencias Python"
echo "  ✅ .env.example - Variables de entorno"
echo ""
echo "🚀 PASOS PARA COMPLETAR EL DEPLOY:"
echo ""
echo "1. 📤 Sube tu código a GitHub/GitLab:"
echo "   git add ."
echo "   git commit -m 'Ready for Railway deploy'"
echo "   git push origin main"
echo ""
echo "2. 🌐 Ve a https://railway.app y crea un nuevo proyecto"
echo ""
echo "3. 🔗 Conecta tu repositorio:"
echo "   - Selecciona 'Deploy from GitHub'"
echo "   - Elige tu repositorio 'gasta2'"
echo "   - Railway detectará automáticamente la configuración"
echo ""
echo "4. ⚙️  Configura variables de entorno (opcional):"
echo "   - TELEGRAM_BOT_TOKEN"
echo "   - TELEGRAM_CHAT_ID"
echo ""
echo "5. 🚀 Railway comenzará el deploy automáticamente"
echo ""
echo "6. ✅ Verifica que funcione:"
echo "   - Health check: https://tu-app.railway.app/api/health"
echo "   - API Docs: https://tu-app.railway.app/api/docs"
echo ""

print_success "¡Configuración lista para deploy!"
print_status "Sigue los pasos arriba para completar el deploy en Railway"
print_warning "Recuerda: Railway ofrece \$5 gratis para comenzar"

echo ""
echo "💡 TIPS PARA EL DEPLOY:"
echo "• El primer deploy puede tomar 5-10 minutos"
echo "• Revisa los logs en Railway si algo falla"
echo "• El health check te dirá si todo está funcionando"
echo "• Puedes hacer rollback fácilmente si algo sale mal"
echo ""

# Verificar si hay un repositorio git configurado
if [ -d ".git" ]; then
    print_status "Repositorio Git detectado"
    REMOTE_URL=$(git remote get-url origin 2>/dev/null)
    if [ $? -eq 0 ]; then
        print_success "Remote configurado: $REMOTE_URL"
    else
        print_warning "No hay remote configurado. Recuerda hacer 'git remote add origin <url>'"
    fi
else
    print_warning "No se detectó repositorio Git. Inicializa con 'git init'"
fi

echo ""
print_success "🎉 ¡Todo listo para el deploy!"