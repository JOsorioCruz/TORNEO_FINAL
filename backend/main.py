from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging

# Importaciones de routers
from backend.routers import teams, users, tournaments, public_view

# Importaciones de configuración de BD
from backend.database import create_database_and_tables, test_database_connection

# Importación de modelos - CRÍTICO para que SQLAlchemy cree las tablas

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directorio donde se guardan los archivos
UPLOAD_DIR = "../frontend/uploads"

# Asegurarse de que el directorio de uploads exista al iniciar
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Inicialización de la Base de Datos y Tablas ---
try:
    logger.info("Iniciando configuración de base de datos...")
    create_database_and_tables()

    # Probar la conexión
    if test_database_connection():
        logger.info("✅ Base de datos lista y operativa")
    else:
        logger.warning("⚠️ Advertencia: Problemas con la conexión a la base de datos")

except Exception as e:
    logger.error(f"❌ Error crítico al inicializar la base de datos: {e}")
    raise

# --- Inicialización de la Aplicación FastAPI ---
app = FastAPI(
    title="API del Torneo de Microfútbol",
    description="Sistema de gestión para torneos deportivos",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # <-- Permite cualquier origen
    allow_credentials=True,
    allow_methods=["*"],   # <-- GET, POST, PUT, DELETE, etc
    allow_headers=["*"],   # <-- Authorization, Content-Type, etc
)
# --- Configuración de Archivos Estáticos ---
# Montar el directorio 'uploads' para acceso público
try:
    app.mount("/static/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads_static")
    logger.info(f"✅ Directorio estático montado: /static/uploads -> {UPLOAD_DIR}")
except Exception as e:
    logger.error(f"❌ Error al montar directorio estático: {e}")

# --- Incluir Routers ---
app.include_router(users.router)
app.include_router(teams.router)
app.include_router(tournaments.router)
app.include_router(public_view.router)

logger.info("✅ Routers incluidos correctamente")


# --- Eventos de inicio y cierre ---
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Aplicación iniciada correctamente")
    logger.info("📚 Documentación disponible en: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Cerrando aplicación...")


# --- Endpoint de prueba ---
@app.get("/", tags=["Health Check"])
def read_root():
    """Endpoint raíz para verificar que la API está funcionando"""
    return {
        "message": "API del Torneo de Microfútbol, Fase 1",
        "status": "operational",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "users": "/users",
            "teams": "/teams",
            "tournaments": "/tournaments",
            "public": "/public"
        }
    }


@app.get("/health", tags=["Health Check"])
def health_check():
    """Endpoint para verificar el estado de salud de la aplicación"""
    try:
        db_status = test_database_connection()
        return {
            "status": "healthy" if db_status else "degraded",
            "database": "connected" if db_status else "disconnected",
            "uploads_dir": os.path.exists(UPLOAD_DIR)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Para ejecutar directamente con python main.py
if __name__ == "__main__":
    import uvicorn

    logger.info("🔧 Iniciando servidor en modo desarrollo...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload en desarrollo
        log_level="info"
    )