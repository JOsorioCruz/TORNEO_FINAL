from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

# Importaciones de routers (incluye M1, M2, M5 y M8)
from routers import users, teams, tournaments, public_view

# Importaciones de configuración de BD
from database import create_database_and_tables

# Importación de modelos:
# NOTA: Importar todos los modelos (usando *) es crucial
# para que SQLAlchemy (Base.metadata.create_all)
# sepa qué tablas crear durante la autogestión.
from models import * # Directorio donde se guardan los archivos
UPLOAD_DIR = "uploads"

# Asegurarse de que el directorio de uploads exista al iniciar
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Inicialización de la Base de Datos y Tablas ---
# Esta función intentará crear la BD y todas las tablas si no existen.
create_database_and_tables()

# --- Inicialización de la Aplicación FastAPI ---
app = FastAPI(
    title="Plataforma de Torneo - Fase 1",
    version="1.0.0",
    description="Backend para la inscripción y configuración del Torneo (MVP)."
)

# --- Configuración de Archivos Estáticos (Fotos y Documentos) ---
# Se monta el directorio 'uploads' para que sea accesible públicamente en la URL /static/uploads
app.mount("/static/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads_static")

# --- Incluir Routers (Consolidación de M1, M2, M5 y M8) ---
app.include_router(users.router)
app.include_router(teams.router)
app.include_router(tournaments.router)
app.include_router(public_view.router)

# --- Endpoint de prueba ---
@app.get("/")
def read_root():
    return {"message": "API del Torneo de Microfútbol, Fase 1. Lista para usar."}

# Para ejecutar (ya no es necesario importar uvicorn aquí si usas la terminal):
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)