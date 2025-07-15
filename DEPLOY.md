# 🚀 Checklist de Despliegue en Render

## ✅ Archivos Requeridos (Completado)
- [x] `app.py` - Aplicación principal
- [x] `start.py` - Script de inicio para Render
- [x] `requirements.txt` - Dependencias Python
- [x] `runtime.txt` - Versión de Python (3.12.1)
- [x] `render.yaml` - Configuración de Render
- [x] `README.md` - Documentación
- [x] `.gitignore` - Archivos a ignorar en Git
- [x] `.env.example` - Plantilla de variables de entorno
- [x] `models/fireDetection.pt` - Modelo YOLO

## 🔧 Pasos para Desplegar

### 1. Preparar el repositorio Git
```bash
git add .
git commit -m "Preparado para despliegue en Render"
git push origin main
```

### 2. Crear servicio en Render
1. Ve a [render.com](https://render.com)
2. Conecta tu cuenta de GitHub
3. Selecciona "New Web Service"
4. Conecta tu repositorio `bkportafolio`
5. Render detectará automáticamente `render.yaml`

### 3. Configurar variables de entorno (Opcional)
Si prefieres configurar manualmente en lugar de usar `render.yaml`:

```
API_KEY=cae84f79b6dc4f34bb935fb2f3d1a8f76491eaf2a9b74d59bca4d389d4a1cb97
MAX_REQUESTS_PER_MINUTE=10
MAX_FAILED_ATTEMPTS=5
BLOCK_DURATION=300
MAX_FILE_SIZE=10485760
MAX_IMAGE_WIDTH=4000
MAX_IMAGE_HEIGHT=4000
```

### 4. Configuración del servicio
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python start.py`
- **Python Version**: 3.12.1

## 🌐 URLs de tu API una vez desplegada
- API Base: `https://tu-app-name.onrender.com`
- Documentación: `https://tu-app-name.onrender.com/docs` (FastAPI auto-docs)
- Health Check: `https://tu-app-name.onrender.com/health`
- Predicción: `POST https://tu-app-name.onrender.com/predict-image`

## 🔑 Testing de la API
```bash
# Health check
curl https://tu-app-name.onrender.com/health

# Estadísticas de seguridad (con API key)
curl -H "X-API-Key: cae84f79b6dc4f34bb935fb2f3d1a8f76491eaf2a9b74d59bca4d389d4a1cb97" \
     https://tu-app-name.onrender.com/security-stats

# Upload de imagen
curl -X POST \
     -H "X-API-Key: cae84f79b6dc4f34bb935fb2f3d1a8f76491eaf2a9b74d59bca4d389d4a1cb97" \
     -F "file=@imagen.jpg" \
     https://tu-app-name.onrender.com/predict-image
```

## ⚠️ Consideraciones importantes
- **Plan gratuito**: El servicio se "duerme" después de 15 minutos de inactividad
- **Arranque en frío**: Puede tardar 30-60 segundos en responder tras despertar
- **Límites**: 750 horas gratis por mes
- **Logs**: Disponibles en el dashboard de Render

## 🔒 Configuración de seguridad adicional
Una vez desplegado, considera:
1. Configurar dominio personalizado
2. Actualizar `ALLOWED_HOSTS` con tu dominio real
3. Configurar `CORS_ORIGINS` con tu frontend
4. Monitorear logs de seguridad

## 📊 Monitoreo
- Dashboard de Render: métricas de CPU, memoria, requests
- Logs en tiempo real desde el dashboard
- Endpoint `/health` para uptime monitoring
- Endpoint `/security-stats` para seguridad
