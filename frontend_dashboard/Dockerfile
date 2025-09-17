# 🐳 Dockerfile para Frontend SvelteKit
# Este archivo define cómo construir el contenedor del frontend

# PASO 1: Imagen base con Node.js 20 (LTS más reciente)
FROM node:20-alpine

# PASO 2: Configurar directorio de trabajo
WORKDIR /app

# PASO 3: Copiar archivos de dependencias primero (para cache)
COPY package*.json ./

# PASO 4: Instalar dependencias de Node.js
RUN npm ci --only=production=false

# PASO 5: Copiar todo el código del frontend
COPY . .

# PASO 6: Exponer el puerto 5173 (puerto por defecto de Vite)
EXPOSE 5173

# PASO 7: Comando para iniciar el servidor de desarrollo
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
