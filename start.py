#!/usr/bin/env pthon3
"""
Script de inicio para la API de detección de fuego en Render
"""
import os
import logging
import uvicorn
from app import app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Función principal para iniciar el servidor"""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "10000"))
    
    workers = int(os.getenv("WORKERS", "1"))
    
    logger.info("🚀 Iniciando Fire Detection API en Render")
    logger.info(f"📡 Host: {host}")
    logger.info(f"🔌 Puerto: {port}")
    logger.info(f"👥 Workers: {workers}")
    
    # Iniciar servidor
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
