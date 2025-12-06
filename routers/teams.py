import os
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db

# 🚨 AJUSTE DE IMPORTACIÓN: Renombrar el modelo 'Rol' del ORM a 'RolModel'
from models import Equipo, Usuario, Jugador, TipoJugador, Rol as RolModel

from schemas import (
    EquipoCreate,
    Equipo,
    JugadorCreate,
    Jugador,
    TipoJugadorSchema,
    JugadorValidation
)
from typing import List, Optional
from datetime import date, datetime

router = APIRouter(prefix="/teams", tags=["Equipos y Jugadores"])


# --- Lógica de Seguridad (Placeholders Corregidos) ---
# Estos placeholders DEBEN coincidir con los IDs creados en la base de datos (Admin=1, Delegado=2)

def get_current_user_id() -> int:
    """Placeholder: Retorna el ID del Delegado (ID 2)."""
    return 2


def get_current_admin_id() -> int:
    """Placeholder: Retorna el ID del Administrador (ID 1)."""
    return 1


def is_admin(admin_id: int = Depends(get_current_admin_id)):
    """Dependencia que verifica que el ID obtenido es el del Admin (simulado)."""
    if admin_id != 1:
        raise HTTPException(status_code=403, detail="Permiso denegado. Solo Administradores.")
    return admin_id


# ----------------------------------------

# Directorio donde se guardarán los archivos
UPLOAD_DIR = "uploads"


# Endpoint 1: Obtener Tipos de Jugador (Ayuda al formulario de inscripción)
@router.get("/tipos-jugador/", response_model=List[TipoJugadorSchema])
def get_tipos_jugador(db: Session = Depends(get_db)):
    """Muestra las opciones de Tipo de Jugador del reglamento (RF-2.4)."""
    tipos = db.query(TipoJugador).all()
    return tipos


# Endpoint 2: Crear un Equipo (RF-2.1)
@router.post("/", response_model=Equipo, status_code=status.HTTP_201_CREATED)
def create_team(
        team_data: EquipoCreate,
        db: Session = Depends(get_db),
        delegado_id: int = Depends(get_current_user_id)  # ID del Delegado autenticado
):
    """Permite al Delegado crear un equipo y se asigna automáticamente como delegado (RF-2.1)."""

    # 2.1. Validación de Rol del Creador
    # 🚨 AJUSTE DE LÓGICA: Usar RolModel (el modelo de SQLAlchemy)
    delegado_role = db.query(RolModel).join(Usuario).filter(Usuario.id_usuario == delegado_id).first()

    # Manejo de casos si el ID no existe (solución al error "Usuario Delegado no encontrado.")
    if not delegado_role:
        raise HTTPException(status_code=404, detail="Usuario Delegado no encontrado. Asegúrese que el ID 2 exista y sea un Delegado.")

    role_name = delegado_role.nombre
    if role_name != "Delegado" and role_name != "Administrador":
        raise HTTPException(status_code=403, detail="Solo Delegados o Administradores pueden crear equipos.")

    # 2.2. Creación
    db_team = Equipo(nombre=team_data.nombre, id_delegado=delegado_id)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


# Endpoint 3: Agregar un Jugador a un Equipo (RF-2.2, RF-2.3, RF-2.5, RF-2.7, RF-2.8, RF-2.9)
@router.post("/{team_id}/players/", response_model=Jugador, status_code=status.HTTP_201_CREATED)
async def add_player_to_team(
        team_id: int,
        db: Session = Depends(get_db),
        # Datos del formulario
        cedula: str = Form(...),
        nombre_completo: str = Form(...),
        fecha_nacimiento: date = Form(...),
        id_tipo_jugador: int = Form(...),
        numero_camiseta: Optional[int] = Form(None),
        # Archivos
        foto: UploadFile = File(..., description="Foto reciente (RF-2.3)"),
        documento_probatorio: UploadFile = File(..., description="Documentos probatorios (PDF/Imagen) (RF-2.5)"),
        delegado_id: int = Depends(get_current_user_id)
):
    """Permite al Delegado agregar un jugador a su equipo con validaciones de reglamento."""

    # 3.1. Validación de Propiedad y Límites (RF-2.2)
    team = db.query(Equipo).filter(Equipo.id_equipo == team_id).first()
    if not team or team.id_delegado != delegado_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para agregar jugadores a este equipo.")

    current_players_count = db.query(Jugador).filter(Jugador.id_equipo == team_id).count()
    if current_players_count >= 16:
        raise HTTPException(status_code=400, detail="Máximo 16 jugadores por equipo alcanzado (RF-2.2).")

    # 3.2. Validación de Cédula y Camiseta (RF-2.9)
    if db.query(Jugador).filter(Jugador.cedula == cedula).first():
        raise HTTPException(status_code=400, detail="La cédula ya está registrada.")

    if numero_camiseta is not None:
        if not (1 <= numero_camiseta <= 20):
            raise HTTPException(status_code=400, detail="El número de camiseta debe estar entre 1 y 20.")
        if db.query(Jugador).filter(Jugador.id_equipo == team_id, Jugador.numero_camiseta == numero_camiseta).first():
            raise HTTPException(status_code=400,
                                detail="El número de camiseta ya está ocupado en este equipo (RF-2.9).")

    # 3.3. Validación de Tipo de Jugador y Reglas de Cuota (RF-2.7, RF-2.8)
    tipo_jugador = db.query(TipoJugador).filter(TipoJugador.id_tipo_jugador == id_tipo_jugador).first()
    if not tipo_jugador:
        raise HTTPException(status_code=400, detail="Tipo de jugador no válido.")

    tipo_nombre = tipo_jugador.nombre.lower()

    # Tipos de "extranjeros" definidos por el reglamento (RF-2.4)
    TIPO_POLICIA = "agente de policía (estación vallejo)"
    TIPO_IE = "docente/trabajador (institución educativa el dorado)"
    TIPO_FUNDACION = "docente/trabajador/padre (fundación vallejo)"

    tipos_extranjeros = [TIPO_POLICIA, TIPO_IE, TIPO_FUNDACION]

    is_foreign_player = tipo_nombre in tipos_extranjeros

    # --- Validación de Cuotas (RF-2.7) ---

    # 3.3.1. Validación Global: Máximo 3 "Extranjeros"
    if is_foreign_player:
        current_extranjeros_count = db.query(func.count(Jugador.id_jugador)).join(TipoJugador).filter(
            Jugador.id_equipo == team_id,
            TipoJugador.nombre.in_(tipos_extranjeros)
        ).scalar()

        # Si ya se tienen 3 extranjeros y el nuevo jugador también lo es, se rechaza.
        if current_extranjeros_count >= 3:
            raise HTTPException(status_code=400, detail="Máximo 3 'Extranjeros' por equipo alcanzado (RF-2.7).")

    # 3.3.2. Validación Granular: Máximo 2 Docentes I.E. El Dorado
    if tipo_nombre == TIPO_IE:
        count_ie = db.query(func.count(Jugador.id_jugador)).join(TipoJugador).filter(
            Jugador.id_equipo == team_id,
            TipoJugador.nombre == TIPO_IE
        ).scalar()
        if count_ie >= 2:
            raise HTTPException(status_code=400,
                                detail=f"Máximo 2 Docentes/Trabajadores I.E. El Dorado por equipo (RF-2.7).")

    # 3.3.3. Validación Granular: Máximo 2 Docentes/Padres Fundación
    if tipo_nombre == TIPO_FUNDACION:
        count_fundacion = db.query(func.count(Jugador.id_jugador)).join(TipoJugador).filter(
            Jugador.id_equipo == team_id,
            TipoJugador.nombre == TIPO_FUNDACION
        ).scalar()
        if count_fundacion >= 2:
            raise HTTPException(status_code=400,
                                detail=f"Máximo 2 Docentes/Trabajadores/Padres Fundación por equipo (RF-2.7).")

    # 3.3.4. Validación de Edad para Extranjeros (RF-2.8)
    if is_foreign_player:
        today = date.today()
        # Cálculo de edad
        age = today.year - fecha_nacimiento.year - (
                (today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
        if age < 26:
            raise HTTPException(status_code=400,
                                detail="Los jugadores 'Extranjeros' deben tener 26 años o más (RF-2.8).")

    # 3.4. Guardado de Archivos (RF-2.5)
    # Generar nombres de archivo únicos
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    foto_filename = f"{team_id}_{cedula}_FOTO_{timestamp}.{foto.filename.split('.')[-1]}"
    doc_filename = f"{team_id}_{cedula}_DOC_{timestamp}.{documento_probatorio.filename.split('.')[-1]}"

    # Almacenamiento en el disco
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Guardar Foto
        with open(os.path.join(UPLOAD_DIR, foto_filename), "wb") as f:
            f.write(await foto.read())

        # Guardar Documento
        with open(os.path.join(UPLOAD_DIR, doc_filename), "wb") as f:
            f.write(await documento_probatorio.read())

    except Exception as e:
        # En caso de error de disco, se lanza un 500
        raise HTTPException(status_code=500, detail=f"Error al guardar archivos: {e}")

    # 3.5. Creación del registro en BD
    db_jugador = Jugador(
        cedula=cedula,
        nombre_completo=nombre_completo,
        fecha_nacimiento=fecha_nacimiento,
        numero_camiseta=numero_camiseta,
        id_tipo_jugador=id_tipo_jugador,
        id_equipo=team_id,
        foto_url=os.path.join(UPLOAD_DIR, foto_filename),
        documento_probatorio_url=os.path.join(UPLOAD_DIR, doc_filename),
        estado_validacion='Pendiente'  # Estado inicial por defecto
    )
    db.add(db_jugador)
    db.commit()
    db.refresh(db_jugador)

    return db_jugador


# Endpoint 4: Panel de Validación de Jugadores (Administrador) (RF-2.6)
@router.patch("/players/{player_id}/validate/", response_model=Jugador)
def validate_player(
        player_id: int,
        validation_data: JugadorValidation,
        db: Session = Depends(get_db),
        admin_id: int = Depends(is_admin)  # Solo Admin puede acceder usando la dependencia corregida
):
    """Permite al Administrador Validar o Rechazar a un jugador (RF-2.6)."""
    db_jugador = db.query(Jugador).filter(Jugador.id_jugador == player_id).first()
    if not db_jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado.")

    # Validar que el estado sea uno permitido
    new_state = validation_data.estado_validacion
    if new_state not in ['Validado', 'Rechazado']:
        raise HTTPException(status_code=400, detail="El estado debe ser 'Validado' o 'Rechazado'.")

    db_jugador.estado_validacion = new_state

    # Solo establece fecha de validación si el estado es 'Validado'
    db_jugador.fecha_validacion = datetime.now() if new_state == 'Validado' else None

    db.commit()
    db.refresh(db_jugador)
    return db_jugador


# Endpoint 5: Obtener Jugadores Pendientes (Para el panel de Admin)
@router.get("/players/pending/", response_model=List[Jugador])
def get_pending_players(
        db: Session = Depends(get_db),
        admin_id: int = Depends(is_admin)  # Solo Admin puede acceder
):
    """Lista todos los jugadores en estado 'Pendiente' para revisión del Admin."""
    pending_players = db.query(Jugador).filter(Jugador.estado_validacion == 'Pendiente').all()
    return pending_players