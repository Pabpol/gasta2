#!/bin/bash

# 🚀 Gasta2 Alpha Setup Script
# Automated setup for alpha users

set -e

echo "🚀 Gasta2 Alpha Setup"
echo "===================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if running on supported OS
check_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_success "Linux detected - compatible"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_success "macOS detected - compatible"
    else
        print_error "Unsupported OS: $OSTYPE"
        print_error "This script supports Linux and macOS only"
        exit 1
    fi
}

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."

    local missing_deps=()

    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi

    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    fi

    if [[ ${#missing_deps[@]} -ne 0 ]]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_status "Please install them and run the script again"
        exit 1
    fi

    print_success "All dependencies found"
}

# Get user configuration
get_user_config() {
    print_status "Configuración de usuario alpha"
    echo

    read -p "Tu nombre de usuario alpha: " ALPHA_USER
    read -p "URL del servidor alpha (ej: https://tu-servidor-alpha.com): " SERVER_URL
    read -p "Token de Telegram (opcional, presiona Enter para omitir): " TELEGRAM_TOKEN

    # Validate inputs
    if [[ -z "$ALPHA_USER" ]]; then
        print_error "Nombre de usuario alpha es requerido"
        exit 1
    fi

    if [[ -z "$SERVER_URL" ]]; then
        print_error "URL del servidor alpha es requerida"
        exit 1
    fi

    print_success "Configuración guardada"
}

# Test server connectivity
test_server() {
    print_status "Probando conectividad con el servidor..."

    if curl -s --max-time 10 "$SERVER_URL/api/health" > /dev/null; then
        print_success "Servidor responde correctamente"
    else
        print_error "No se puede conectar al servidor: $SERVER_URL"
        print_error "Verifica la URL e intenta nuevamente"
        exit 1
    fi
}

# Create MacroDroid configuration
create_macrodroid_config() {
    print_status "Creando configuración de MacroDroid..."

    cat > "macrodroid-config-$ALPHA_USER.json" << EOF
{
  "user": "$ALPHA_USER",
  "server_url": "$SERVER_URL",
  "telegram_token": "$TELEGRAM_TOKEN",
  "created_at": "$(date)",
  "version": "alpha-1.0.0",
  "macros": {
    "gastos_automaticos": {
      "trigger": "notification_received",
      "actions": [
        {
          "type": "extract_amount",
          "regex": "\\\$([0-9.,]+)"
        },
        {
          "type": "extract_description",
          "regex": "en (.+?) con tu tarjeta"
        },
        {
          "type": "send_to_server",
          "url": "$SERVER_URL/api/gasto",
          "method": "POST"
        }
      ]
    }
  }
}
EOF

    print_success "Configuración creada: macrodroid-config-$ALPHA_USER.json"
}

# Create test script
create_test_script() {
    print_status "Creando script de pruebas..."

    cat > "test-alpha-setup.sh" << 'EOF'
#!/bin/bash

# 🧪 Test script for alpha setup

SERVER_URL="REPLACE_WITH_YOUR_SERVER_URL"

echo "🧪 Probando configuración alpha..."

# Test 1: Server health
echo "1. Probando salud del servidor..."
if curl -s "$SERVER_URL/api/health" | grep -q "healthy"; then
    echo "✅ Servidor saludable"
else
    echo "❌ Servidor no responde"
    exit 1
fi

# Test 2: Create test expense
echo "2. Creando gasto de prueba..."
RESPONSE=$(curl -s -X POST "$SERVER_URL/api/gasto" \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Test expense from alpha setup",
    "monto_clp": 1000,
    "medio": "TC",
    "fuente": "alpha_test"
  }')

if echo "$RESPONSE" | grep -q "success.*true"; then
    echo "✅ Gasto de prueba creado exitosamente"
else
    echo "❌ Error creando gasto de prueba"
    echo "Respuesta: $RESPONSE"
    exit 1
fi

# Test 3: Check dashboard
echo "3. Verificando dashboard..."
SUMMARY=$(curl -s "$SERVER_URL/api/dashboard/summary")
if echo "$SUMMARY" | grep -q "total_expenses"; then
    echo "✅ Dashboard funcionando"
else
    echo "❌ Dashboard no responde"
    exit 1
fi

echo ""
echo "🎉 ¡Todas las pruebas pasaron!"
echo "Tu configuración alpha está lista."
echo ""
echo "Próximos pasos:"
echo "1. Configura MacroDroid usando la guía ALPHA_MACRODROID_GUIDE.md"
echo "2. Activa la macro después de probar"
echo "3. Invita a otros usuarios alpha"
EOF

    # Replace placeholder in test script
    sed -i "s|REPLACE_WITH_YOUR_SERVER_URL|$SERVER_URL|g" "test-alpha-setup.sh"

    chmod +x "test-alpha-setup.sh"
    print_success "Script de pruebas creado: test-alpha-setup.sh"
}

# Create summary
create_summary() {
    print_status "Creando resumen de configuración..."

    cat > "alpha-setup-summary-$ALPHA_USER.txt" << EOF
🚀 Gasta2 Alpha Setup - Completado
=====================================

Usuario Alpha: $ALPHA_USER
Servidor: $SERVER_URL
Fecha: $(date)

📋 Archivos creados:
- macrodroid-config-$ALPHA_USER.json (configuración para MacroDroid)
- test-alpha-setup.sh (script de pruebas)

📖 Próximos pasos:
1. Lee ALPHA_MACRODROID_GUIDE.md para configurar MacroDroid
2. Ejecuta ./test-alpha-setup.sh para verificar todo funciona
3. Configura Telegram (opcional pero recomendado)
4. ¡Disfruta tus gastos automáticos!

📞 Soporte:
- WhatsApp: [Tu número de contacto]
- Email: alpha@gasta2.com

¡Gracias por ser usuario alpha! 🎉
EOF

    print_success "Resumen creado: alpha-setup-summary-$ALPHA_USER.txt"
}

# Main execution
main() {
    echo
    print_status "Iniciando setup de Gasta2 Alpha..."
    echo

    check_os
    check_dependencies
    get_user_config
    test_server
    create_macrodroid_config
    create_test_script
    create_summary

    echo
    print_success "¡Setup completado exitosamente!"
    echo
    print_status "Archivos creados:"
    echo "  📄 macrodroid-config-$ALPHA_USER.json"
    echo "  🧪 test-alpha-setup.sh"
    echo "  📋 alpha-setup-summary-$ALPHA_USER.txt"
    echo
    print_status "Próximos pasos:"
    echo "  1. Lee ALPHA_MACRODROID_GUIDE.md"
    echo "  2. Ejecuta ./test-alpha-setup.sh"
    echo "  3. Configura MacroDroid"
    echo "  4. ¡Comienza a automatizar tus gastos!"
    echo
    print_success "¡Bienvenido al futuro de las finanzas personales! 💰🤖"
}

# Run main function
main