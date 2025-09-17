# 🚀 **Configuración Rápida para Usuarios Alpha**

> **Tiempo estimado:** 15-30 minutos | **Dificultad:** Fácil

---

## 📦 **Opción 1: Setup Automático (Recomendado)**

### Paso 1: Descargar y ejecutar
```bash
# Clona el repositorio de configuración alpha
git clone https://github.com/tu-usuario/gasta2-alpha-setup.git
cd gasta2-alpha-setup

# Ejecuta el setup automático
./setup-alpha.sh
```

### Paso 2: Configurar credenciales
El script te pedirá:
- ✅ Tu nombre de usuario alpha
- ✅ Token de Telegram (opcional)
- ✅ URL de tu servidor alpha

### Paso 3: Probar
```bash
# Verificar que todo funciona
./test-setup.sh
```

---

## 🔧 **Opción 2: Setup Manual**

### Paso 1: Instalar dependencias
```bash
# Para Ubuntu/Debian
sudo apt update
sudo apt install curl wget git

# Para macOS
brew install curl wget git
```

### Paso 2: Configurar MacroDroid
1. **Sigue la guía completa**: [ALPHA_MACRODROID_GUIDE.md](ALPHA_MACRODROID_GUIDE.md)
2. **Usa la configuración rápida** para tu banco (ver tabla abajo)

### Paso 3: Configurar Telegram (Opcional pero recomendado)
```bash
# El bot te contactará automáticamente cuando configures MacroDroid
# Solo necesitas tener Telegram instalado en tu teléfono
```

---

## 🏦 **Configuración Rápida por Banco**

### ⚡ **Copia y pega estas configuraciones en MacroDroid:**

#### **Banco Estado** (Más común)
```
Trigger: Notificación de "Banco Estado" contiene "compra"
Monto Regex: \$([0-9.,]+)
Descripción Regex: en (.+?) con tu tarjeta
```

#### **Scotiabank**
```
Trigger: Notificación de "Scotiabank" contiene "compra"
Monto Regex: por \$([0-9.,]+)
Descripción Regex: en\s+([^.]+)\.
```

#### **Santander**
```
Trigger: Notificación de "Santander" contiene "cargo"
Monto Regex: \$([0-9.,]+)
Descripción Regex: Comercio: (.+?)
```

---

## 🧪 **Verificar Instalación**

### Paso 1: Probar backend
```bash
# Verificar que el servidor responde
curl http://tu-servidor-alpha:8000/api/health
```

### Paso 2: Probar MacroDroid
1. Configura la macro (pero NO la actives aún)
2. Ve a MacroDroid → Macros → Tu macro
3. Toca "Probar" (ícono de play)
4. Deberías ver una confirmación

### Paso 3: Probar gasto real
1. Haz una compra pequeña ($1.000 CLP)
2. Espera la notificación bancaria
3. Verifica en Telegram y dashboard

---

## 🔍 **Solución Rápida de Problemas**

### ❌ **"No se conecta al servidor"**
```bash
# Verificar conectividad
ping tu-servidor-alpha

# Verificar puerto
telnet tu-servidor-alpha 8000
```

### ❌ **"Regex no funciona"**
```
1. Copia el texto EXACTO de la notificación
2. Prueba en https://regex101.com
3. Usa la configuración de "Otro banco" como fallback
```

### ❌ **"No recibe notificaciones de Telegram"**
```
1. Verifica que tienes Telegram instalado
2. Configura el bot token en el servidor
3. El bot te contactará automáticamente
```

---

## 📞 **¿Necesitas Ayuda?**

### 🚨 **Contactos de soporte alpha:**
- **WhatsApp**: [Tu número]
- **Telegram**: @gasta2_support
- **Email**: alpha@gasta2.com

### 📋 **Información útil para soporte:**
```
- Tu nombre de usuario alpha
- Marca y modelo de teléfono
- Versión de Android
- Banco que usas
- Error específico que ves
```

---

## 🎯 **Próximos Pasos**

### ✅ **Cuando todo funciona:**
1. **Activa la macro** en MacroDroid
2. **Configura categorías** personalizadas (opcional)
3. **Invita a amigos** alpha
4. **Explora el dashboard** web

### 🚀 **Características para probar:**
- ✅ **Registro automático** de gastos
- ✅ **Categorización inteligente**
- ✅ **Gastos compartidos**
- ✅ **Backup automático**
- ✅ **Dashboard responsive**

---

**¡Listo para automatizar tus finanzas!** 💰🤖

¿Tuviste algún problema con la configuración?