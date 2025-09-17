# Sistema de Gestión de Gastos 💰

Sistema completo de gestión de gastos con automatización vía MacroDroid y notificaciones Telegram.

## 🏗️ Arquitectura del Proyecto

```
gasta2/
├── backend_gastos/          # 🚀 API Backend (FastAPI)
│   ├── app.py              # Aplicación principal
│   ├── core/               # Lógica del negocio
│   ├── integrations/       # Telegram bot
│   └── ...                 # Configuración y deployment
├── frontend_web/           # 🔮 [FUTURO] Dashboard Web
└── mobile_app/            # 📱 [FUTURO] App Android
```

## ✨ Características Actuales

- 🤖 **Bot de Telegram** - Notificaciones automáticas y confirmación de gastos
- 📱 **Integración MacroDroid** - Automatización de entrada de gastos desde notificaciones
- 🏷️ **Categorización Automática** - ML para clasificar gastos por comercio
- 📊 **Almacenamiento Excel** - Compatible con sistemas existentes
- ☁️ **Deploy en Railway** - Listo para producción
- 🔒 **Webhook Seguro** - Validación de requests

## 🚀 Deployment

### Backend (MVP Personal)
- **Plataforma:** Railway (Deploy automático)
- **Framework:** FastAPI + Python 3.11
- **Base de datos:** Parquet + Excel (eficiente para uso personal)
- **Notificaciones:** Telegram Bot API (opcional)
- **Costo:** $0/mes (plan gratuito)

### 🚀 Deploy Automático en 5 Minutos

#### Opción 1: Script Automático (Recomendado)
```bash
# Ejecutar script de deploy
./deploy.sh

# El script te guiará por todo el proceso
```

#### Opción 2: Deploy Manual

1. **Preparar el código:**
```bash
git add .
git commit -m "Ready for Railway deploy"
git push origin main
```

2. **Deploy en Railway:**
   - Ve a [railway.app](https://railway.app)
   - "Start a New Project" → "Deploy from GitHub"
   - Selecciona tu repositorio `gasta2`
   - Railway detectará automáticamente la configuración
   - ¡Deploy automático en 2-3 minutos!

3. **Configurar variables (opcional):**
```bash
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui
```

4. **Verificar funcionamiento:**
```bash
# Health check
curl https://tu-app.railway.app/api/health

# API Documentation
# https://tu-app.railway.app/api/docs
```

### 📋 URLs Importantes
- **API Base:** `https://tu-app.railway.app`
- **Health Check:** `/api/health`
- **API Docs:** `/api/docs`
- **Dashboard:** `/` (próximamente)

Ver [DEPLOY.md](DEPLOY.md) para guía completa y troubleshooting.

## 📱 Integración MacroDroid

El sistema funciona con MacroDroid para automatizar la entrada de gastos:

1. **Regex de notificaciones** - Extrae monto, comercio y método de pago
2. **API automática** - Envía gasto directamente al backend
3. **Confirmación Telegram** - Notifica éxito/error

Ver [backend_gastos/MACRODROID_CONFIG.md](backend_gastos/MACRODROID_CONFIG.md) para configuración completa.

## 🎯 Roadmap Futuro

### Frontend Web Dashboard 🖥️
- 📊 Visualización de gastos y tendencias
- 🎛️ Configuración de categorías
- 📈 Reportes y análisis
- 💾 Migración a base de datos real

### App Mobile 📱
- 📷 Escaneo de recibos con OCR
- 📍 Gastos con geolocalización
- 📊 Dashboard móvil
- 🔔 Notificaciones push

### Mejoras Backend 🔧
- 🗄️ Migración a PostgreSQL
- 🔐 Autenticación y usuarios múltiples
- 🤖 IA mejorada para categorización
- 📊 APIs de reportes avanzados

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Especialmente para:
- 🎨 Frontend development
- 📱 Mobile app development  
- 🤖 ML/AI improvements
- 📚 Documentation

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles.

---

⭐ **¿Te gusta el proyecto?** ¡Dale una estrella en GitHub!
