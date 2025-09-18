# Sistema de Gestión de Gastos 💰

Sistema completo de gestión de gastos con automatización vía MacroDroid y notificaciones Telegram.

## 🏗️ Arquitectura del Proyecto

```
gasta2/
├── backend_gastos/          # 🚀 API Backend (FastAPI)
│   ├── app.py              # Aplicación principal
│   ├── core/               # Lógica del negocio
│   ├── integrations/       # Telegram bot
│   ├── static/             # Archivos frontend compilados
│   └── ...                 # Configuración y deployment
├── frontend_dashboard/      # 🎨 Dashboard Web (SvelteKit)
│   ├── src/                # Código fuente
│   ├── build/              # Archivos compilados (generado)
│   └── package.json        # Dependencias Node.js
└── mobile_app/            # 📱 [FUTURO] App Android
```

## ✨ Características Actuales

- 🎨 **Dashboard Web Completo** - Interfaz moderna con SvelteKit para gestión de gastos
- 🤖 **Bot de Telegram** - Notificaciones automáticas y confirmación de gastos con botones interactivos
- 📱 **Integración MacroDroid** - Automatización de entrada de gastos desde notificaciones
- 🏷️ **Categorización Automática** - ML para clasificar gastos por comercio
- 📊 **Almacenamiento Dual** - Parquet eficiente + Excel para compatibilidad
- ☁️ **Deploy en Railway** - Listo para producción con Docker
- 🔒 **Webhook Seguro** - Validación de requests con debugging avanzado
- 📈 **Visualización de Datos** - Gráficos y análisis de gastos
- 🔄 **Sincronización Automática** - Entre Parquet y Excel
- 🗑️ **Gestión Completa de Gastos** - Crear, leer, actualizar y eliminar gastos

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
- **Dashboard Web:** `/` (¡Ya disponible!)
- **API Redoc:** `/api/redoc`

Ver [DEPLOY.md](DEPLOY.md) para guía completa y troubleshooting.

## 🔌 API Endpoints

### Gastos (Expenses)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/gastos` | Obtener todos los gastos |
| `POST` | `/api/gasto` | Crear nuevo gasto |
| `DELETE` | `/api/gasto/{id}` | **🆕** Eliminar gasto por ID |
| `PUT` | `/api/gasto/{id}/categoria` | Actualizar categoría de gasto |

### Dashboard

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/dashboard/summary` | Resumen general del dashboard |
| `GET` | `/api/dashboard/categories` | Desglose por categorías |
| `GET` | `/api/dashboard/trends` | Tendencias mensuales |

### Sistema

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check del sistema |
| `GET` | `/api/docs` | Documentación interactiva de la API |

### Ejemplos de Uso

```bash
# Crear un gasto
curl -X POST https://tu-app.railway.app/api/gasto \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Almuerzo en restaurante",
    "monto_clp": 15000,
    "medio": "TC",
    "fuente": "manual"
  }'

# Eliminar un gasto
curl -X DELETE https://tu-app.railway.app/api/gasto/123e4567-e89b-12d3-a456-426614174000

# Obtener todos los gastos
curl https://tu-app.railway.app/api/gastos
```

## 📱 Integración MacroDroid

El sistema funciona con MacroDroid para automatizar la entrada de gastos:

1. **Regex de notificaciones** - Extrae monto, comercio y método de pago
2. **API automática** - Envía gasto directamente al backend
3. **Confirmación Telegram** - Notifica éxito/error

Ver [backend_gastos/MACRODROID_CONFIG.md](backend_gastos/MACRODROID_CONFIG.md) para configuración completa.

## 🎯 Roadmap Futuro

### Frontend Web Dashboard 🖥️ ✅ IMPLEMENTADO
- 📊 Visualización de gastos y tendencias
- 🎛️ Configuración de categorías
- 📈 Reportes y análisis
- 💾 Migración a base de datos real (próximamente)

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
