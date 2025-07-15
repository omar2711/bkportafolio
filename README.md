# 🔥 Fire Detection API

API segura para detección de fuego y humo en imágenes usando YOLO y PyTorch.

## 🚀 Características

- **Detección YOLO**: Modelo entrenado para detectar fuego y humo
- **API Segura**: Rate limiting, bloqueo de IPs, validación de archivos
- **Variables de Entorno**: Configuración flexible y segura
- **Logging Avanzado**: Monitoreo completo de actividad
- **Headers de Seguridad**: Protección contra ataques web

## 📋 Configuración

### 1. Clonar y configurar entorno

```bash
git clone <tu-repo>
cd bkportafolio
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copia el archivo de ejemplo y configura tus valores:

```bash
cp .env.example .env
```

Edita `.env` con tus configuraciones:

```env
# API Configuration
API_KEY=tu_api_key_secreta_aqui

# Security Configuration
MAX_REQUESTS_PER_MINUTE=10
MAX_FAILED_ATTEMPTS=5
BLOCK_DURATION=300

# Server Configuration
PORT=8000
HOST=0.0.0.0

# File Limits
MAX_FILE_SIZE=10485760
MAX_IMAGE_WIDTH=4000
MAX_IMAGE_HEIGHT=4000
```

### 3. Ejecutar la aplicación

```bash
python app.py
```

## 🔑 API Key Configurada

Tu API key actual: `cae84f79b6dc4f34bb935fb2f3d1a8f76491eaf2a9b74d59bca4d389d4a1cb97`

## 📡 Endpoints

### POST `/predict-image`
Detecta fuego y humo en imágenes

**Headers:**
- `X-API-Key` (opcional): API key para acceso
- `Content-Type`: multipart/form-data

**Body:**
- `file`: Archivo de imagen (JPG, PNG, GIF, WEBP)

**Límites:**
- Tamaño máximo: 10MB
- Dimensiones máximas: 4000x4000 pixels
- Rate limit: 10 requests/minuto por IP

### GET `/`
Información de la API y características de seguridad

### GET `/health`
Estado del servidor y modelo

### GET `/security-stats`
Estadísticas de seguridad (requiere API key)

## 🛡️ Características de Seguridad

### Rate Limiting
- **10 requests por minuto** por IP
- Ventana deslizante de 60 segundos

### Bloqueo Automático
- **5 intentos fallidos** = IP bloqueada por 5 minutos
- Detección de actividad sospechosa

### Validación de Archivos
- Verificación de magic numbers
- Detección de contenido malicioso
- Límites de tamaño y dimensiones

### Headers de Seguridad
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- CORS configurado

## 🚀 Despliegue en Render

### Archivos preparados para despliegue:
- ✅ `render.yaml` - Configuración automática
- ✅ `start.py` - Script de inicio optimizado
- ✅ `runtime.txt` - Python 3.12.1
- ✅ Variables de entorno configuradas

### Pasos rápidos:
1. **Push a GitHub**:
   ```bash
   git add .
   git commit -m "Ready for Render deployment"
   git push origin main
   ```

2. **Crear servicio en Render**:
   - Ve a [render.com](https://render.com)
   - "New Web Service" → Conecta este repositorio
   - Render usará automáticamente `render.yaml`

3. **¡Listo!** Tu API estará disponible en: `https://tu-app.onrender.com`

### API Key configurada:
```
cae84f79b6dc4f34bb935fb2f3d1a8f76491eaf2a9b74d59bca4d389d4a1cb97
```

Ver `DEPLOY.md` para instrucciones detalladas.

## 📊 Monitoreo

### Logs de seguridad:
- Requests exitosos y fallidos
- IPs bloqueadas
- Archivos sospechosos
- Rate limiting

### Estadísticas en tiempo real:
```bash
curl -H "X-API-Key: tu_api_key" http://localhost:8000/security-stats
```

## 🔧 Desarrollo

### Estructura del proyecto:
```
bkportafolio/
├── app.py              # API principal
├── requirements.txt    # Dependencias
├── .env               # Variables de entorno (NO subir a git)
├── .env.example       # Ejemplo de configuración
├── .gitignore         # Archivos a ignorar
├── models/
│   └── fireDetection.pt  # Modelo YOLO
└── README.md          # Este archivo
```

### Testing local:
```bash
# Cambiar puerto si es necesario
PORT=8001 python app.py
```

## 📄 Licencia

Proyecto para portafolio profesional.
