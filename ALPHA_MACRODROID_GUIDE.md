# 🚀 **Guía MacroDroid para Usuarios Alpha - Gastos Automáticos**

> **Versión:** Alpha 1.0.0 | **Última actualización:** Septiembre 2025
>
> Esta guía te ayudará a configurar MacroDroid para automatizar el registro de tus gastos bancarios. ¡Es más fácil de lo que parece!

---

## 📋 **Antes de Empezar**

### ✅ **Prerrequisitos**
- **Android con MacroDroid** instalado ([Descargar de Google Play](https://play.google.com/store/apps/details?id=com.arlosoft.macrodroid))
- **Cuenta bancaria** con notificaciones push activadas
- **URL de tu servidor** (te la daremos cuando actives tu cuenta alpha)

### 🎯 **Lo que lograrás**
- ✅ Gastos registrados automáticamente al recibir notificaciones bancarias
- ✅ Categorización inteligente de tus compras
- ✅ Notificaciones en Telegram para confirmar gastos
- ✅ Dashboard web con análisis de tus finanzas

---

## 📱 **Paso 1: Instalar y Configurar MacroDroid**

### 1.1 Instalar MacroDroid
1. Ve a Google Play Store
2. Busca "MacroDroid"
3. Instala la aplicación (es gratuita)

### 1.2 Permisos necesarios
Abre MacroDroid y concede estos permisos:
- ✅ **Notificaciones**: Para leer notificaciones bancarias
- ✅ **Acceso total**: Para ejecutar acciones automáticamente
- ✅ **No molestar**: Para enviar notificaciones (opcional)

### 1.3 Configuración inicial
1. Abre MacroDroid
2. Toca "Continuar" en la configuración inicial
3. Activa "Ayudante de accesibilidad" cuando se solicite
4. Otorga permisos de notificaciones

---

## 🏦 **Paso 2: Configurar Notificaciones Bancarias**

### 2.1 Activar notificaciones en tu app bancaria
Ve a la configuración de tu app bancaria y asegúrate de que:
- ✅ **Notificaciones push** estén activadas
- ✅ **Notificaciones de compras** estén activadas
- ✅ **Texto completo** en notificaciones (no solo títulos)

### 2.2 Tipos de notificaciones que necesitamos
```
✅ Compra con tarjeta de crédito
✅ Compra con tarjeta de débito
✅ Transferencias y pagos
❌ Solo alertas de seguridad (no sirven)
```

---

## ⚙️ **Paso 3: Crear la Macro Automática**

### 3.1 Crear nueva macro
1. Abre MacroDroid
2. Toca el botón **+** (Agregar macro)
3. Selecciona **"Macro vacía"**
4. Nombra tu macro: **"Gastos Automáticos"**

### 3.2 Configurar el Disparador (Trigger)

#### Opción A: Para la mayoría de los bancos
```
Tipo de disparador: UI → Notificación Recibida
Propietario de la app: [Tu app bancaria]
Texto contiene: compra OR débito OR cargo OR transferencia
```

#### Opción B: Para bancos específicos
Busca tu banco en la tabla más abajo y usa esa configuración específica.

### 3.3 Configurar las Acciones (Actions)

#### Acción 1: Extraer información del gasto
```
Tipo: Variables → Establecer Variable
Nombre: notification_text
Valor: {notification_text}
```

#### Acción 2: Extraer el monto
```
Tipo: Variables → Establecer Variable
Nombre: monto
Valor: [Usa el regex de tu banco - ver tabla abajo]
```

#### Acción 3: Extraer la descripción
```
Tipo: Variables → Establecer Variable
Nombre: descripcion
Valor: [Usa el regex de tu banco - ver tabla abajo]
```

#### Acción 4: Enviar al servidor
```
Tipo: Red → HTTP Request
URL: [Tu URL de servidor alpha]
Método: POST
Headers:
  Content-Type: application/json

Body:
{
  "descripcion": "{descripcion}",
  "monto_clp": {monto},
  "medio": "TC",
  "fuente": "macrodroid"
}
```

---

## 🏛️ **Paso 4: Configuración por Banco**

### 📊 **Tabla de Configuración por Banco**

| Banco | Regex Monto | Regex Descripción | Notas |
|-------|-------------|-------------------|--------|
| **Banco Estado** | `\$([0-9.,]+)` | `en (.+?) con tu tarjeta` | Más común |
| **Santander** | `\$([0-9.,]+)` | `Comercio: (.+?)` | Incluye débito |
| **BCI** | `por \$([0-9.,]+)` | `en (.+?) el` | Fecha incluida |
| **Scotiabank** | `por \$([0-9.,]+)` | `en\s+([^.]+)\.` | MercadoPago compatible |
| **Itaú** | `\$([0-9.,]+)` | `en (.+?)\s` | Débito automático |
| **MercadoPago** | `\$([0-9.,]+)` | `MERCADOPAGO\*(.+)` | Solo MP |
| **Otro banco** | `\$([0-9.,]+)` | `en (.+?) con` | Configuración genérica |

### 🔧 **Ejemplos de Notificaciones**

#### Banco Estado:
```
Banco Estado
Compra aprobada por $15.000 en RESTAURANT XYZ con tu tarjeta terminada en 1234.
Saldo disponible: $450.000
```
- **Monto:** `$15.000` → `15000`
- **Descripción:** `RESTAURANT XYZ`

#### Scotiabank:
```
Scotiabank
Se realizó compra con tu tarjeta xxxx7698 por $18.329 en MERCADOPAGO*MER.
```
- **Monto:** `$18.329` → `18329`
- **Descripción:** `MERCADOPAGO*MER`

---

## 🧪 **Paso 5: Probar la Configuración**

### 5.1 Prueba básica
1. Configura la macro con tu banco
2. **NO actives aún** la macro
3. Ve a MacroDroid → Macros → Tu macro
4. Toca **"Probar"** (ícono de play)
5. Envía una notificación de prueba desde tu app bancaria

### 5.2 Prueba real
1. Haz una **compra pequeña** de prueba ($1.000-2.000 CLP)
2. Espera la notificación bancaria
3. Verifica que llegue al bot de Telegram
4. Revisa el dashboard web para confirmar el registro

### 5.3 Activar la macro
```
Solo activa la macro cuando:
✅ Las pruebas funcionan correctamente
✅ Recibes confirmaciones en Telegram
✅ Los datos aparecen en el dashboard
```

---

## 🔧 **Solución de Problemas**

### ❌ **No recibe notificaciones**
```
🔍 Verificar:
- Notificaciones push activadas en app bancaria
- Permisos de notificación en Android
- MacroDroid tiene permisos de accesibilidad
```

### ❌ **Regex no funciona**
```
🔍 Verificar:
- Copiar exactamente el texto de la notificación
- Probar regex en https://regex101.com
- Usar la configuración específica de tu banco
```

### ❌ **No llega al servidor**
```
🔍 Verificar:
- URL correcta (incluyendo http:// o https://)
- Conexión a internet funcionando
- Firewall no bloquea la conexión
```

### ❌ **Categorización incorrecta**
```
🔍 Verificar:
- Descripción extraída correctamente
- Telegram bot configurado
- Esperar respuesta del bot para corregir
```

---

## 📞 **Soporte para Alpha Users**

### 🚨 **Si algo no funciona**
1. **Captura pantalla** del error
2. **Copia el texto** de la notificación bancaria
3. **Envía por WhatsApp** con tu nombre de usuario alpha

### 📋 **Información útil para soporte**
```
- Marca y modelo de tu teléfono
- Versión de Android
- Nombre de tu banco
- Texto exacto de la notificación problemática
- Qué esperabas vs qué pasó
```

---

## 🎯 **Próximos Pasos Después de la Configuración**

### ✅ **Cuando todo funciona**
1. **Activa la macro** definitivamente
2. **Configura Telegram** para confirmaciones
3. **Explora el dashboard** web
4. **Invita a tus amigos** alpha

### 🚀 **Características Alpha Disponibles**
- ✅ **Registro automático** de gastos
- ✅ **Categorización inteligente** con IA
- ✅ **Telegram confirmaciones** interactivas
- ✅ **Dashboard web** con gráficos
- ✅ **Backup automático** de datos
- ✅ **Soporte compartido** de gastos

---

## 📚 **Recursos Adicionales**

- 📖 **Documentación completa**: [Enlace al repo]
- 🎥 **Video tutorial**: [Próximamente]
- 💬 **Comunidad alpha**: [Grupo de WhatsApp]
- 🐛 **Reportar bugs**: [Issues en GitHub]

---

**¡Felicitaciones!** 🎉 Ya tienes gastos automáticos configurados. Cada compra que hagas se registrará automáticamente en tu sistema de finanzas personales.

¿Necesitas ayuda con algún paso específico?