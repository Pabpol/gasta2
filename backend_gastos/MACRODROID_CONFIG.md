# 📱 Configuración MacroDroid para Gastos Automáticos

## 🎯 Ejemplo de Notificación del Banco:
```
Banco Estado
Compra aprobada por $15.000 en RESTAURANT XYZ con tu tarjeta terminada en 1234.
Saldo disponible: $450.000
```

## 🔧 Configuración de Variables en MacroDroid:

### Variable 1: notification_text
```
Valor: {notification_text}
Descripción: Texto completo de la notificación
```

### Variable 2: monto
```
Para notificaciones Scotiabank:
Regex: por \$([0-9.,]+)
Resultado: 18329 (sin $ ni puntos, solo números)

Para otros bancos:
Regex estándar: \$([0-9.,]+)
```

### Variable 3: descripcion  
```
Para notificaciones Scotiabank/similares:
Regex principal: en\s+([^.]+)\.
Regex alternativo: en (.+?)\s*\.

Ejemplo con texto real:
"Se realizó compra... por $18.329 en MERCADOPAGO*MER. Si desconoces..."
Resultado: MERCADOPAGO*MER

Para otros bancos:
Regex estándar: en (.+?) con tu tarjeta
```

## 🧪 Pruebas de Regex:

### Texto de ejemplo Scotiabank:
```
Se realizó compra con tu tarjeta de crédito xxxx7698 por $18.329 en MERCADOPAGO*MER. Si desconoces esta operación...
```

### Regex: `en\s+([^.]+)\.`
- ✅ Resultado: `MERCADOPAGO*MER`

### Regex alternativo: `en (.+?)\s*\.` 
- ✅ Resultado: `MERCADOPAGO*MER`

## 🔄 Configuración Multi-Regex en MacroDroid:

Para manejar diferentes formatos de notificación, usa estas opciones en orden:

### Opción 1: Notificación bancaria estándar
```
Regex: en (.+?) con tu tarjeta
Si coincide → usar resultado
```

### Opción 2: MercadoPago específico  
```
Regex: MERCADOPAGO\*(.+)
Si coincide → usar resultado
Si no → continuar a opción 3
```

### Opción 3: Texto completo como fallback
```
Regex: (.+)
Limpiar resultado manualmente
```

### Variable 4: medio
```
Valor fijo: TC (Tarjeta de Crédito)
Si es débito: TD
```

## 📤 HTTP Request Configuration:

### URL:
```
http://192.168.1.100:8000/api/gasto
(Reemplaza con tu IP local)
```

### Headers:
```
Content-Type: application/json
```

### Body:
```json
{
  "descripcion": "{descripcion}",
  "monto_clp": {monto},
  "medio": "TC",
  "fuente": "macrodroid",
  "fecha": "{ldate} {ltime}"
}
```

## 🎨 Ejemplo de Regex por Banco:

### Banco Estado:
```
Monto: \$([0-9.,]+)
Comercio: en (.+?) con tu tarjeta
```

### Santander:
```
Monto: \$([0-9.,]+)
Comercio: Comercio: (.+?)
```

### BCI:
```
Monto: por \$([0-9.,]+)
Comercio: en (.+?) el
```

## 🔍 Testing:
1. Configura la macro
2. Haz una compra pequeña de prueba
3. Verifica que llegue la notificación al bot de Telegram
4. Ajusta las regex según el formato de tu banco
