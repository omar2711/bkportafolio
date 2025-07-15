from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image, ImageDraw, ImageFont
import io
import logging
import os
import uvicorn
import time
import hashlib
from typing import Optional
from collections import defaultdict, deque
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fire Detection API", version="1.0.0")

allowed_hosts = os.getenv("ALLOWED_HOSTS", "*").split(",")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

request_times = defaultdict(deque)
failed_attempts = defaultdict(int)
blocked_ips = defaultdict(float)

MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "10"))
RATE_LIMIT_WINDOW = 60
MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
BLOCK_DURATION = int(os.getenv("BLOCK_DURATION", "300")) 

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))
MAX_IMAGE_WIDTH = int(os.getenv("MAX_IMAGE_WIDTH", "4000"))
MAX_IMAGE_HEIGHT = int(os.getenv("MAX_IMAGE_HEIGHT", "4000"))

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    logger.warning("⚠️  API_KEY no configurada en .env - usando valor por defecto")
    API_KEY = "tu_api_key_secreta_123"
else:
    logger.info("✅ API_KEY cargada desde variables de entorno")

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verificar API key (opcional para demostración)"""
    if not x_api_key:
        return None
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="API key inválida")
    return x_api_key

def get_client_ip(request: Request) -> str:
    """Obtener IP real del cliente (considerando proxies)"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host

def is_ip_blocked(client_ip: str) -> bool:
    """Verificar si la IP está bloqueada"""
    if client_ip in blocked_ips:
        if time.time() - blocked_ips[client_ip] < BLOCK_DURATION:
            return True
        else:
            del blocked_ips[client_ip]
            failed_attempts[client_ip] = 0
    return False

def block_ip(client_ip: str):
    """Bloquear IP por intentos fallidos"""
    blocked_ips[client_ip] = time.time()
    logger.warning(f"IP bloqueada por 5 minutos: {client_ip}")

def check_rate_limit(client_ip: str):
    """Rate limiting mejorado con bloqueo por intentos fallidos"""
    if is_ip_blocked(client_ip):
        raise HTTPException(
            status_code=429, 
            detail="IP bloqueada temporalmente por actividad sospechosa"
        )
    
    now = time.time()
    minute_ago = now - RATE_LIMIT_WINDOW
    
    request_times[client_ip] = deque([
        req_time for req_time in request_times[client_ip] 
        if req_time > minute_ago
    ])
    
    if len(request_times[client_ip]) >= MAX_REQUESTS_PER_MINUTE:
        failed_attempts[client_ip] += 1
        
        if failed_attempts[client_ip] >= MAX_FAILED_ATTEMPTS:
            block_ip(client_ip)
        
        raise HTTPException(
            status_code=429, 
            detail=f"Rate limit excedido. Máximo {MAX_REQUESTS_PER_MINUTE} requests por minuto"
        )
    
    request_times[client_ip].append(now)

model = None
device = None
class_names = ["fuego", "humo"]

def load_model():
    global model, device
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_path = os.getenv("MODEL_PATH", "models/fireDetection.pt")
    
    if os.path.exists(model_path):
        try:
            from ultralytics import YOLO
            model = YOLO(model_path)
            model.eval()
            model.is_ultralytics = True
            logger.info(f"✅ Modelo YOLO cargado exitosamente desde: {model_path}")
        except Exception as e:
            logger.error(f"❌ Error cargando YOLO: {e}")
            model = create_fallback_model()
    else:
        logger.warning(f"⚠️  Modelo no encontrado en: {model_path} - usando fallback")
        model = create_fallback_model()
    
    model.to(device)
    logger.info(f"🔧 Dispositivo: {device}")

def create_fallback_model():
    from torchvision.models import resnet50
    model = resnet50(weights='IMAGENET1K_V1')
    model.fc = nn.Linear(model.fc.in_features, 2)
    model.eval()
    model.is_ultralytics = False
    logger.info("Usando modelo fallback")
    return model

def preprocess_image(image: Image.Image) -> torch.Tensor:
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    if hasattr(model, 'is_ultralytics') and model.is_ultralytics:
        return image
    else:
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        return transform(image).unsqueeze(0).to(device)

def predict_and_draw(image: Image.Image) -> Image.Image:
    if hasattr(model, 'is_ultralytics') and model.is_ultralytics:
        results = model(image, conf=0.25, iou=0.45)
        return draw_yolo_detections(image, results)
    else:
        return draw_classification(image)

def draw_yolo_detections(image: Image.Image, results) -> Image.Image:
    draw_image = image.copy()
    draw = ImageDraw.Draw(draw_image)
    
    colors = {"fuego": "#FF0000", "humo": "#888888"}
    
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    for result in results:
        if result.boxes is not None:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                conf = float(box.conf[0].cpu().numpy())
                cls = int(box.cls[0].cpu().numpy())
                
                original_class = class_names[cls] if cls < len(class_names) else "unknown"
                class_name = "humo" if original_class == "fuego" else "fuego" if original_class == "humo" else original_class
                
                color = colors.get(class_name, "#FFFF00")
                draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                
                text = f"{class_name}: {conf:.2f}"
                try:
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                except:
                    text_width, text_height = len(text) * 8, 16
                
                draw.rectangle([x1, y1-text_height-4, x1+text_width+4, y1], fill=color)
                draw.text((x1+2, y1-text_height-2), text, fill="white", font=font)
    
    return draw_image

def draw_classification(image: Image.Image) -> Image.Image:
    tensor = preprocess_image(image)
    
    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.nn.functional.softmax(outputs[0], dim=0)
        conf, cls = torch.max(probs, 0)
    
    if conf > 0.5:
        original_class = class_names[cls] if cls < len(class_names) else "unknown"
        class_name = "humo" if original_class == "fuego" else "fuego" if original_class == "humo" else original_class
        
        draw_image = image.copy()
        draw = ImageDraw.Draw(draw_image)
        
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        text = f"Clasificación: {class_name} ({conf:.1%})"
        colors = {"fuego": "#FF0000", "humo": "#888888"}
        color = colors.get(class_name, "#FFFF00")
        
        try:
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
        except:
            text_width, text_height = len(text) * 10, 20
        
        margin = 10
        draw.rectangle([margin, margin, margin+text_width+20, margin+text_height+10], fill=color, outline="white", width=2)
        draw.text((margin+10, margin+5), text, fill="white", font=font)
        
        return draw_image
    
    return image

def validate_image_security(image_bytes: bytes, filename: str = "") -> bool:
    """Validar seguridad de la imagen"""
    image_signatures = {
        b'\xFF\xD8\xFF': 'JPEG',
        b'\x89PNG\r\n\x1a\n': 'PNG',
        b'GIF87a': 'GIF',
        b'GIF89a': 'GIF',
        b'RIFF': 'WEBP'
    }
    
    is_valid_image = False
    for signature in image_signatures:
        if image_bytes.startswith(signature):
            is_valid_image = True
            break
    
    if not is_valid_image:
        return False
    
    suspicious_patterns = [b'<script', b'javascript:', b'<?php', b'<%']
    for pattern in suspicious_patterns:
        if pattern in image_bytes.lower():
            return False
    
    return True

@app.on_event("startup")
async def startup():
    load_model()

@app.post("/predict-image")
async def predict_image_endpoint(
    file: UploadFile = File(...), 
    x_api_key: Optional[str] = Header(None),
    request: Request = None
):
    client_ip = get_client_ip(request) if request else "127.0.0.1"
    
    check_rate_limit(client_ip)
    verify_api_key(x_api_key)
    
    if not file.content_type or not file.content_type.startswith("image/"):
        failed_attempts[client_ip] += 1
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")
    
    try:
        image_bytes = await file.read()
        
        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"Archivo muy grande. Máximo {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if not validate_image_security(image_bytes, file.filename):
            failed_attempts[client_ip] += 1
            logger.warning(f"🚨 Archivo sospechoso desde IP: {client_ip}")
            raise HTTPException(status_code=400, detail="Archivo de imagen inválido o sospechoso")
        
        image = Image.open(io.BytesIO(image_bytes))
        
        if image.width > MAX_IMAGE_WIDTH or image.height > MAX_IMAGE_HEIGHT:
            raise HTTPException(
                status_code=413, 
                detail=f"Imagen muy grande. Máximo {MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT} pixels"
            )
        
        annotated_image = predict_and_draw(image)
        
        img_buffer = io.BytesIO()
        annotated_image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        if client_ip in failed_attempts:
            failed_attempts[client_ip] = 0
        
        logger.info(f"Predicción exitosa para IP: {client_ip}")
        
        return StreamingResponse(
            io.BytesIO(img_buffer.getvalue()), 
            media_type="image/png",
            headers={
                "Content-Disposition": "inline; filename=detections.png",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando imagen desde IP {client_ip}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando imagen: {str(e)}")

@app.get("/")
async def root():
    """Endpoint de información"""
    return {
        "message": "Fire Detection API - Segura y Optimizada",
        "version": "2.0.0",
        "endpoints": {
            "/predict-image": "Detectar fuego y humo en imágenes",
            "/health": "Estado del servidor",
            "/security-stats": "Estadísticas de seguridad (requiere API key)"
        },
        "security_features": {
            "rate_limiting": f"{MAX_REQUESTS_PER_MINUTE} requests por minuto",
            "ip_blocking": f"Bloqueo automático tras {MAX_FAILED_ATTEMPTS} intentos fallidos",
            "file_validation": "Validación de magic numbers y contenido",
            "size_limits": f"{MAX_FILE_SIZE // (1024*1024)}MB máximo, {MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT} pixels",
            "security_headers": "X-Content-Type-Options, X-Frame-Options"
        },
        "api_key_required": False,
        "note": "API protegida para uso profesional en portafolio"
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "device": str(device) if device else "not_initialized"
    }

@app.get("/security-stats")
async def security_stats(x_api_key: Optional[str] = Header(None)):
    """Estadísticas de seguridad (requiere API key)"""
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="API key requerida para estadísticas")
    
    return {
        "active_rate_limits": len([ip for ip, times in request_times.items() if times]),
        "blocked_ips": len(blocked_ips),
        "failed_attempts_count": len([ip for ip, count in failed_attempts.items() if count > 0]),
        "total_monitored_ips": len(set(list(request_times.keys()) + list(failed_attempts.keys()))),
        "security_features": [
            "Rate limiting (10 req/min)",
            "IP blocking (5 failed attempts)",
            "File validation",
            "Magic number verification",
            "Malware detection",
            "Size limits",
            "Security headers"
        ]
    }

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"🚀 Iniciando servidor en {host}:{port}")
    logger.info(f"🔒 API Key configurada: {'✅' if API_KEY != 'tu_api_key_secreta_123' else '⚠️  usando valor por defecto'}")
    logger.info(f"⚡ Rate limiting: {MAX_REQUESTS_PER_MINUTE} req/min")
    logger.info(f"📁 Límites: {MAX_FILE_SIZE // (1024*1024)}MB, {MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT}px")
    
    uvicorn.run("app:app", host=host, port=port)

