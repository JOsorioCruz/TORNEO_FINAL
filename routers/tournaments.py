from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
# Importaciones de modelos (asegúrate de que los nombres coincidan con models.py)
from models import Equipo, Jugador, TipoJugador, Fase, Partido, Torneo, FormatoFase
from schemas import (
    TorneoCreate, Torneo, FaseCreate, Fase,
    FormatoFaseSchema, # CORRECCIÓN: Se importa directamente el nombre del esquema
    FaseEquipoCreate
)
from typing import List
from datetime import datetime

router = APIRouter(prefix="/tournaments", tags=["Gestión del Torneo (M5)"])


# --- Lógica de Seguridad (Placeholders Corregidos y Limpios) ---
# Usamos una dependencia limpia para el ID del administrador (ID 1)
def get_current_admin_id() -> int:
    """Retorna un ID de Administrador de ejemplo (ID 1)."""
    return 1  # ID del Admin hardcodeado para pruebas

def is_admin(admin_id: int = Depends(get_current_admin_id)):
    """Dependencia que verifica que el usuario es Admin."""
    if admin_id != 1:
        raise HTTPException(status_code=403, detail="Permiso denegado. Solo Administradores.")
    return admin_id


# -----------------------------------------------------------

# Endpoint 1: Crear un Torneo (RF-5.1)
@router.post("/", response_model=Torneo, status_code=status.HTTP_201_CREATED)
def create_tournament(
        torneo: TorneoCreate,
        db: Session = Depends(get_db),
        admin_id: int = Depends(is_admin) # Usa la dependencia corregida
):
    """Permite al Administrador crear un nuevo Torneo (ej. 'Torneo 2024-II')."""
    db_torneo = Torneo(**torneo.dict())
    db.add(db_torneo)
    db.commit()
    db.refresh(db_torneo)
    return db_torneo


# Endpoint 2: Obtener Formatos de Fase disponibles (RF-5.3)
@router.get("/formats/", response_model=List[FormatoFaseSchema])
def get_phase_formats(db: Session = Depends(get_db)):
    """Obtiene los formatos de fase: Liga, Grupos, Eliminación Directa (RF-5.3)."""
    formats = db.query(FormatoFase).all()
    if not formats:
        # Lógica de precarga inicial si la tabla está vacía
        formatos_data = [
            {"nombre": "Liga"},
            {"nombre": "Grupos"},
            {"nombre": "Eliminacion Directa"}
        ]
        for data in formatos_data:
            db_format = FormatoFase(**data)
            db.add(db_format)
        db.commit()
        formats = db.query(FormatoFase).all()

    return formats


# Endpoint 3: Crear una Fase dentro de un Torneo (RF-5.2)
@router.post("/{torneo_id}/phases/", response_model=Fase, status_code=status.HTTP_201_CREATED)
def create_phase(
        torneo_id: int,
        fase: FaseCreate,
        db: Session = Depends(get_db),
        admin_id: int = Depends(is_admin) # Usa la dependencia corregida
):
    """Permite al Administrador crear una Fase dentro de un Torneo."""
    torneo = db.query(Torneo).filter(Torneo.id_torneo == torneo_id).first()
    formato = db.query(FormatoFase).filter(FormatoFase.id_formato == fase.id_formato).first()

    if not torneo or not formato:
        raise HTTPException(status_code=404, detail="Torneo o Formato no encontrado.")

    db_fase = Fase(
        nombre=fase.nombre,
        orden=fase.orden,
        id_torneo=torneo_id,
        id_formato=fase.id_formato
    )
    db.add(db_fase)
    db.commit()
    db.refresh(db_fase)
    return db_fase


# Endpoint 4: Asignar Equipos a una Fase (RF-5.4, RF-5.5)
@router.post("/phases/{fase_id}/teams/", status_code=status.HTTP_204_NO_CONTENT)
def assign_teams_to_phase(
        fase_id: int,
        equipos_data: List[FaseEquipoCreate],
        db: Session = Depends(get_db),
        admin_id: int = Depends(is_admin) # Usa la dependencia corregida
):
    """Asigna equipos a una Fase, definiendo grupos o cabezas de serie si es necesario."""
    fase = db.query(Fase).filter(Fase.id_fase == fase_id).first()
    if not fase:
        raise HTTPException(status_code=404, detail="Fase no encontrada.")

    for equipo_data in equipos_data:
        equipo = db.query(Equipo).filter(Equipo.id_equipo == equipo_data.id_equipo).first()
        if not equipo:
            raise HTTPException(status_code=404, detail=f"Equipo con ID {equipo_data.id_equipo} no encontrado.")

        # 1. Validación de formato de fase y datos recibidos
        # Se asume que 'fase.formato' está disponible gracias a las relaciones de SQLAlchemy.
        formato_nombre = fase.formato.nombre
        if formato_nombre == "Grupos" and not equipo_data.nombre_grupo:
            raise HTTPException(status_code=400, detail="Para formato 'Grupos', el nombre del grupo es obligatorio.")

        # 2. Creación del registro de asignación
        db_fase_equipo = FaseEquipo(
            id_fase=fase_id,
            id_equipo=equipo_data.id_equipo,
            nombre_grupo=equipo_data.nombre_grupo,
            es_cabeza_serie=equipo_data.es_cabeza_serie
        )
        db.add(db_fase_equipo)

    db.commit()
    return {"message": "Equipos asignados a la fase correctamente."}


# Endpoint 5: Generar Calendario de Partidos (RF-5.7)
@router.post("/phases/{fase_id}/generate-schedule/", status_code=status.HTTP_201_CREATED)
def generate_schedule(
        fase_id: int,
        db: Session = Depends(get_db),
        admin_id: int = Depends(is_admin) # Usa la dependencia corregida
):
    """Genera automáticamente el calendario para fases de formato 'Liga' o 'Grupos' (RF-5.7)."""
    fase = db.query(Fase).filter(Fase.id_fase == fase_id).first()
    if not fase:
        raise HTTPException(status_code=404, detail="Fase no encontrada.")

    formato_nombre = fase.formato.nombre

    if formato_nombre not in ["Liga", "Grupos"]:
        raise HTTPException(status_code=400, detail="Solo se genera calendario para formatos 'Liga' o 'Grupos'.")

    equipos_en_fase = db.query(FaseEquipo.id_equipo).filter(FaseEquipo.id_fase == fase_id).all()
    equipo_ids = [e[0] for e in equipos_en_fase]

    # LÓGICA DE GENERACIÓN DE CALENDARIO (ALGORITMO)
    partidos_generados = []
    if len(equipo_ids) >= 2:
        for i in range(len(equipo_ids)):
            for j in range(i + 1, len(equipo_ids)):
                # Simulación de un partido (Algoritmo Round-Robin simplificado)
                partidos_generados.append(Partido(
                    id_fase=fase_id,
                    id_equipo_local=equipo_ids[i],
                    id_equipo_visitante=equipo_ids[j],
                    fecha_hora=datetime.now()
                ))

        for p in partidos_generados:
            db.add(p)
        db.commit()

    return {"message": f"Calendario de {len(partidos_generados)} partidos generado para la fase '{fase.nombre}'."}


# Endpoint 6: Aplicar Bonificación (RF-5.8)
@router.patch("/phases/{fase_id}/apply-bonus/", response_model=Fase)
def apply_bonus(
        fase_id: int,
        db: Session = Depends(get_db),
        admin_id: int = Depends(is_admin) # Usa la dependencia corregida
):
    """Permite al Administrador aplicar la bonificación de puntos (+0.75, +0.50) a la Fase (RF-5.8)."""
    fase = db.query(Fase).filter(Fase.id_fase == fase_id).first()
    if not fase:
        raise HTTPException(status_code=404, detail="Fase no encontrada.")

    fase.bonificacion_aplicada = True
    db.commit()
    db.refresh(fase)
    return fase