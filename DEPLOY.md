# 🚀 Deploy del Sistema de Gastos - Railway

## 📋 Descripción
Guía completa para desplegar el MVP del sistema de gestión de gastos en Railway para uso personal.

## 🎯 Requisitos Previos

### 1. Cuenta en Railway
- Ve a [railway.app](https://railway.app) y crea una cuenta gratuita
- Railway ofrece $5 de crédito inicial (suficiente para este proyecto)

### 2. Repositorio Git
- Tu código debe estar en un repositorio Git (GitHub, GitLab, etc.)
- Railway se conecta automáticamente a tu repo

### 3. Variables de Entorno (Opcional)
- Token de Telegram Bot (para notificaciones)
- ID de Chat de Telegram

---

## 🚀 Proceso de Deploy

### Paso 1: Conectar Repositorio

1. **Inicia sesión en Railway**
   - Ve a [railway.app](https://railway.app)
   - Haz clic en "Start a New Project"

2. **Conecta tu repositorio**
   - Selecciona "Deploy from GitHub" (o tu plataforma Git)
   - Autoriza el acceso a tu repositorio
   - Selecciona el repositorio `gasta2`

3. **Configura el proyecto**
   - Railway detectará automáticamente la configuración
   - El `railway.json` ya está configurado correctamente

### Paso 2: Configurar Variables de Entorno

1. **Ve a Variables de Entorno**
   - En el dashboard de Railway, ve a la pestaña "Variables"

2. **Agrega las variables necesarias**:
   ```
   TELEGRAM_BOT_TOKEN=tu_token_aqui          # Opcional
   TELEGRAM_CHAT_ID=tu_chat_id_aqui           # Opcional
   ```

3. **Nota**: Si no configuras Telegram, el sistema funcionará igual pero sin notificaciones

### Paso 3: Deploy Automático

1. **Railway detectará automáticamente**:
   - `railway.json` - Configuración de build y deploy
   - `Procfile` - Comando de inicio
   - `requirements.txt` - Dependencias Python

2. **El deploy comenzará automáticamente**
   - Railway construirá la imagen
   - Instalará las dependencias
   - Iniciará el servidor

### Paso 4: Verificar Deploy

1. **Revisa los logs**
    - Ve a la pestaña "Deployments" en Railway
    - Haz clic en el deploy activo para ver logs

2. **Obtén la URL del servicio**
    - En "Settings" > "Domains"
    - Railway te dará una URL como: `https://gasta2-production.up.railway.app`

3. **Prueba el health check**
    - Ve a: `https://tu-url.railway.app/api/health`
    - Deberías ver un JSON con status "healthy"

4. **Accede al Dashboard Web**
    - Ve directamente a: `https://tu-url.railway.app/`
    - El dashboard web ya está disponible y funcionando

5. **Verifica la API**
    - Documentación Swagger: `https://tu-url.railway.app/api/docs`
    - Documentación ReDoc: `https://tu-url.railway.app/api/redoc`

---

## 🔧 Configuración del Sistema

### Health Check Endpoint
```
GET /api/health
```
- Verifica que todos los componentes estén funcionando
- Retorna estado del sistema, versión, y componentes

### API Endpoints Principales
```
POST /api/gasto          # Crear nuevo gasto
GET  /api/gastos         # Listar todos los gastos
GET  /api/dashboard/summary  # Resumen del dashboard
GET  /api/dashboard/categories  # Breakdown por categorías
```

### Documentación API
- Swagger UI: `https://tu-url.railway.app/api/docs`
- ReDoc: `https://tu-url.railway.app/api/redoc`

---

## 📊 Monitoreo y Logs

### Ver Logs en Railway
1. Ve al dashboard del proyecto
2. Pestaña "Deployments"
3. Haz clic en el deploy activo
4. Sección "Logs" para ver logs en tiempo real

### Health Monitoring
- El sistema incluye health checks automáticos
- Railway reiniciará el servicio si falla
- Monitorea uso de CPU y memoria

---

## 💾 Almacenamiento de Datos

### Sistema de Archivos
- **Parquet**: Almacenamiento principal eficiente con pyarrow
- **Excel**: Sincronización automática para compatibilidad
- **JSON**: Configuraciones y presupuestos

### Directorio de Datos
```
/app/backend_gastos/data/
├── movimientos_normalizados.parquet  # Datos principales
├── presupuestos.json                 # Presupuestos
└── backups/                         # Respaldos automáticos
```

### Configuración Técnica Actual
- **Python**: 3.11 con FastAPI
- **Node.js**: 20.x para frontend
- **Base de datos**: Parquet + Excel (eficiente para uso personal)
- **Frontend**: SvelteKit compilado y servido por FastAPI
- **Container**: Docker multi-stage build
- **Deploy**: Railway con configuración automática

### Backup Automático
- El sistema crea backups automáticamente
- Los backups se almacenan en el directorio `data/backups/`
- Se recomienda descargar backups regularmente

---

## 🔧 Configuración de Telegram (Opcional)

### 1. Crear Bot de Telegram
1. Ve a [@BotFather](https://t.me/botfather) en Telegram
2. Envía `/newbot`
3. Sigue las instrucciones para crear tu bot
4. Copia el **BOT TOKEN**

### 2. Obtener Chat ID
1. Envía un mensaje a tu bot
2. Ve a: `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
3. Busca el `"chat":{"id":XXXXX}`
4. Copia el **CHAT ID**

### 3. Configurar en Railway
1. Ve a Variables de Entorno
2. Agrega:
   ```
   TELEGRAM_BOT_TOKEN=tu_bot_token
   TELEGRAM_CHAT_ID=tu_chat_id
   ```

---

## 🚨 Solución de Problemas

### Deploy Falla
**Síntomas**: Build falla o servicio no inicia
**Solución**:
1. Revisa los logs en Railway
2. Verifica que `requirements.txt` tenga versiones compatibles
3. Asegúrate de que `railway.json` esté correcto
4. Verifica que el Dockerfile use Node.js 20.x
5. Confirma que pyarrow esté incluido en requirements.txt

### Problemas con el Dashboard Web
**Síntomas**: Dashboard no carga o muestra error 404
**Solución**:
1. Verifica que el Dockerfile copie archivos desde `frontend_dashboard/build/`
2. Confirma que `index.html` existe en `/app/backend_gastos/static/`
3. Revisa logs del build para errores de compilación de SvelteKit

### API No Responde
**Síntomas**: 500 errors o timeouts
**Solución**:
1. Verifica health check: `/api/health`
2. Revisa logs del servicio
3. Verifica variables de entorno

### Problemas de Memoria
**Síntomas**: Servicio se reinicia por OOM
**Solución**:
1. Railway Starter Plan tiene 512MB RAM
2. Si necesitas más, actualiza el plan
3. Optimiza el uso de memoria en el código

---

## 💰 Costos de Railway

### Plan Gratuito (Recomendado para MVP)
- **512 MB RAM**
- **1 GB Storage**
- **$0/mes** (primeros $5 gratis)
- Suficiente para uso personal

### Plan Hobby
- **1 GB RAM**
- **5 GB Storage**
- **$5/mes**
- Para múltiples usuarios

### Plan Pro
- **4 GB RAM**
- **50 GB Storage**
- **$25/mes**
- Para producción completa

---

## 🔄 Actualizaciones

### Deploy Automático
1. **Push a tu repositorio**
2. **Railway detecta cambios automáticamente**
3. **Se construye nueva versión**
4. **Se despliega sin downtime**

### Rollback
1. Ve a "Deployments" en Railway
2. Selecciona versión anterior
3. Haz clic en "Rollback"

---

## 📞 Soporte

### Recursos Útiles
- [Documentación Railway](https://docs.railway.app/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Railway Discord](https://discord.gg/railway)

### Logs de Debug
Para debugging avanzado, habilita logs detallados:
```bash
# En railway.json
{
  "deploy": {
    "startCommand": "cd backend_gastos && uvicorn app:app --host 0.0.0.0 --port $PORT --log-level debug"
  }
}
```

---

## ✅ Checklist de Deploy

- [ ] Repositorio conectado a Railway
- [ ] Variables de entorno configuradas
- [ ] Deploy completado exitosamente
- [ ] Health check funcionando: `/api/health`
- [ ] API docs accesibles: `/api/docs`
- [ ] Telegram configurado (opcional)
- [ ] Backup inicial descargado

---

## 🎉 ¡Listo para usar!

Una vez completado el deploy, tendrás:
- ✅ API REST funcionando
- ✅ Dashboard web accesible
- ✅ Sistema de gastos operativo
- ✅ Notificaciones Telegram (opcional)
- ✅ Backup automático
- ✅ Health monitoring

**URL de tu aplicación**: `https://tu-proyecto.railway.app`

¡Empieza a registrar tus gastos y disfruta de tu sistema personal de gestión financiera! 🚀