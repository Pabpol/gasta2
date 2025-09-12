# 🚂 Deploy en Railway - Guía Paso a Paso

## 1. Preparar el repositorio GitHub

### Subir código a GitHub:
```bash
cd /home/pabpol/projects/gasta2
git init
git add .
git commit -m "Initial commit - Expense management backend"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/gasta2.git
git push -u origin main
```

## 2. Configurar en Railway.app

### Crear proyecto:
1. Ir a https://railway.app
2. Login con GitHub
3. Click "New Project"
4. Seleccionar "Deploy from GitHub repo"
5. Elegir tu repositorio `gasta2`

## Guía de Deployment: Backend de Gastos en Railway

## Arquitectura del Proyecto

```
gasta2/
├── backend_gastos/          # API Backend (FastAPI)
│   ├── app.py              # Aplicación principal
│   ├── core/               # Lógica del negocio
│   ├── integrations/       # Telegram bot
│   ├── Procfile           # Railway config
│   ├── requirements.txt   # Dependencias Python
│   └── railway.json       # Configuración Railway
├── frontend_web/           # [FUTURO] Dashboard Web
└── mobile_app/            # [FUTURO] App Android
```

## Preparación para GitHub

### 1. Inicializar Git en el directorio raíz

```bash
cd /home/pabpol/projects/gasta2
git init
git add .
git commit -m "Initial commit: Backend expense management system"
```

### 2. Crear repositorio en GitHub

1. Ir a [GitHub](https://github.com) → New Repository
2. Nombre: `gasta2` o `expense-manager`
3. Descripción: "Sistema de gestión de gastos con notificaciones Telegram"
4. **No** inicializar con README (ya tienes uno)

### 3. Conectar repositorio local con GitHub

```bash
git remote add origin https://github.com/TU_USUARIO/gasta2.git
git branch -M main
git push -u origin main
```

## Deployment en Railway

### Opción 1: Monorepo (Recomendado para futuro con frontend)

**Ventajas:**
- Un solo repositorio para todo el proyecto
- Fácil compartir código/modelos entre backend y frontend
- Versionado unificado

**Configuración Railway:**
1. Conectar el repositorio `gasta2`
2. En Railway, configurar **Root Directory**: `backend_gastos`
3. Railway solo desplegará el backend por ahora

### Opción 2: Repositorios separados

**Solo si prefieres separar completamente:**
- `gasta2-backend`
- `gasta2-frontend` (futuro)

## Configuración Railway

### 1. Variables de Entorno Requeridas

```env
TELEGRAM_BOT_TOKEN=tu_token_del_bot
TELEGRAM_CHAT_ID=tu_chat_id  
WEBHOOK_SECRET=una_clave_secreta_aleatoria
EXCEL_PATH=data/Presupuesto_Auto.xlsx
```

### 2. Configuración Automática

Railway detectará automáticamente:
- `Procfile` → Comando de inicio
- `requirements.txt` → Dependencias Python
- `runtime.txt` → Python 3.11
- `railway.json` → Configuración específica

### 3. Pasos de Deployment

1. **Conectar a Railway:**
   - Ir a [Railway](https://railway.app)
   - New Project → Deploy from GitHub repo
   - Seleccionar `gasta2`
   - Set Root Directory: `backend_gastos`

2. **Configurar Variables:**
   - Variables tab → Add variables
   - Copiar las variables de entorno

3. **Deploy:**
   - Railway iniciará el deployment automáticamente
   - Obtener la URL del servicio

## Post-Deployment

### 1. Configurar Webhook Telegram

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" 
     -H "Content-Type: application/json" 
     -d '{"url": "https://TU-DOMINIO-RAILWAY.up.railway.app/webhook/telegram"}'
```

### 2. Actualizar MacroDroid

Cambiar la URL de:
```
https://ngrok-url.ngrok-free.app/api/gasto
```

A:
```
https://TU-DOMINIO-RAILWAY.up.railway.app/api/gasto
```

### 3. Testing

```bash
# Test endpoint
curl -X POST https://TU-DOMINIO-RAILWAY.up.railway.app/api/gasto 
  -H "Content-Type: application/json" 
  -d '{"descripcion": "Test Railway", "monto_clp": 5000, "medio": "TC", "fuente": "test"}'
```

## Estructura Futura Recomendada

Cuando agregues frontend:

```
gasta2/
├── backend_gastos/          # API actual
├── frontend_web/           # Dashboard React/Vue/Angular
│   ├── package.json
│   ├── src/
│   └── railway.json       # Configuración separada
├── mobile_app/            # App Flutter/React Native  
├── shared/                # Modelos/tipos compartidos
└── docs/                  # Documentación
```

### Deployments Separados en Railway

- **Backend:** `gasta2` repo, root: `backend_gastos`
- **Frontend:** `gasta2` repo, root: `frontend_web`
- **API Gateway:** Opcional para routing

## Beneficios de esta Arquitectura

1. **Escalabilidad:** Cada servicio se puede escalar independientemente
2. **Desarrollo:** Equipos pueden trabajar en paralelo
3. **Deployment:** Deployments independientes
4. **Costos:** Pagar solo por lo que usas
5. **Flexibilidad:** Diferentes tecnologías por servicio

### Configurar directorio de build:
En Settings → Build:
- Root Directory: `backend_gastos`

## 3. Configurar Webhook de Telegram

Una vez que Railway esté deployado, obtendrás una URL como:
`https://tu-proyecto.railway.app`

### Configurar webhook real:
```bash
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://tu-proyecto.railway.app/telegram/webhook"}'
```

### Verificar webhook:
```bash
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo"
```

## 4. Actualizar MacroDroid

Cambiar la URL en MacroDroid de:
```
https://xxx.ngrok-free.app/api/gasto
```

A:
```
https://tu-proyecto.railway.app/api/gasto
```

## 5. Verificar funcionamiento

### Test endpoints:
- Health check: `https://tu-proyecto.railway.app/`
- Crear gasto: `https://tu-proyecto.railway.app/api/gasto`
- Webhook Telegram: `https://tu-proyecto.railway.app/telegram/webhook`

### Test con curl:
```bash
curl -X POST https://tu-proyecto.railway.app/api/gasto \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Test Railway", "monto_clp": 1000, "medio": "TC", "fuente": "test"}'
```

## 6. Dominio personalizado (Opcional)

En Railway Settings → Domains:
- Agregar dominio personalizado
- Configurar DNS según instrucciones

## 7. Monitoreo

Railway proporciona:
- ✅ Logs en tiempo real
- ✅ Métricas de CPU/RAM
- ✅ Alertas automáticas
- ✅ Restart automático

## 8. Costo

- **Starter Plan**: $5/mes (512MB RAM, 1GB storage)
- **Pro Plan**: $20/mes (8GB RAM, 100GB storage)

---

## ⚡ Ventajas de Railway vs ngrok:

✅ **Disponibilidad 24/7** - No se desconecta
✅ **URL fija** - No cambia nunca  
✅ **SSL automático** - HTTPS nativo
✅ **Webhook real** - No polling, más eficiente
✅ **Escalabilidad** - Se adapta al tráfico
✅ **Monitoreo** - Logs y métricas incluidos
