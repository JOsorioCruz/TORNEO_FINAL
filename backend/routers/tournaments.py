from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.database import get_db
from backend.models import Equipo, Fase, Partido, Torneo, FormatoFase, FaseEquipo
from backend.schemas import (
    TorneoCreate, Torneo as TorneoSchema,
    FaseCreate, Fase as FaseSchema,
    FormatoFaseSchema,
    FaseEquipoCreate
)
from typing import List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tournaments", tags=["Gestión del Torneo (M5)"])


# --- Lógica de Seguridad (Placeholders) ---

def get_current_admin_id() -> int:
    """Retorna un ID de Administrador de ejemplo (ID 1)."""
    return 1


def is_admin(admin_id: int = Depends(get_current_admin_id)):
    """Dependencia que verifica que el usuario es Admin."""
    if admin_id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado. Solo Administradores."
        )
    return admin_id


# -----------------------------------------------------------
# ENDPOINTS
# -----------------------------------------------------------

@router.post("/", response_model=TorneoSchema, status_code=status.HTTP_201_CREATED)
def create_tournament(
        torneo: TorneoCreate,
        db: Session = Depends(get_db),
        admin_id: int = Depends(is_admin)
):
    """
    Permite al Administrador crear un nuevo Torneo.

    RF-5.1: Creación de Torneos
    """
    db_torneo = Torneo(
        nombre=torneo.nombre,
        fecha_inicio=torneo.fecha_inicio,
        fecha_fin=torneo.fecha_fin,
        esta_activo=True
    )

    try:
        db.add(db_torneo)
        db.commit()
        db.refresh(db_torneo)
        logger.info(f"✅ Torneo '{torneo.nombre}' creado correctamente")
        return db_torneo
    except IntegrityError:
        db.rollback()
        logger.warning(f"⚠️ Intento de crear torneo duplicado: {torneo.nombre}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El torneo '{torneo.nombre}' ya existe."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al crear torneo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el torneo."
        )


@router.get("/", response_model=List[TorneoSchema])
def get_tournaments(db: Session = Depends(get_db)):
    """Obtiene la lista de todos los torneos"""
    torneos = db.query(Torneo).all()
    return torneos


@router.get("/{torneo_id}", response_model=TorneoSchema)
def get_tournament(torneo_id: int, db: Session = Depends(get_db)):
    """Obtiene un torneo por ID"""
    torneo = db.query(Torneo).filter(Torneo.id_torneo == torneo_id).first()
    if not torneo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Torneo no encontrado."
        )
    return torneo


@router.patch("/{torneo_id}/activate", response_model=TorneoSchema)
def activate_tournament(
        torneo_id: int,
        db: Session = Depends(get_db),
        admin_id: int = Depends(is_admin)
):
    """Activa un torneo y desactiva los demás"""
    # Desactivar todos los torneos
    db.query(Torneo).update({"esta_activo": False})

    # Activar el torneo seleccionado
    torneo = db.query(Torneo).filter(Torneo.id_torneo == torneo_id).first()
    if not torneo:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Torneo no encontrado."
        )

    torneo.esta_activo = True

    try:
        db.commit()
        db.refresh(torneo)
        logger.info(f"✅ Torneo ID {torneo_id} activado")
        return torneo
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al activar torneo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al activar el torneo."
        )


@router.get("/formats/", response_model=List[FormatoFaseSchema])
def get_phase_formats(db: Session = Depends(get_db)):
    """
    Obtiene los formatos de fase disponibles.

    RF-5.3: Formatos de Fase (Liga, Grupos, Eliminación Directa)
    """
    formats = db.query(FormatoFase).all()

    # Precarga inicial si la tabla está vacía
    if not formats:
        formatos_data = [
            {"nombre": "Liga"},
            {"nombre": "Grupos"},
            {"nombre": "Eliminacion Directa"}
        ]

        for data in formatos_data:
            db_format = FormatoFase(**data)
            db.add(db_format)

        try:
            db.commit()
            formats = db.query(FormatoFase).all()
            logger.info("✅ Formatos de fase precargados")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error al precargar formatos: {e}")

    return formats


@router.post("/{torneo_id}/phases/", response_model=FaseSchema, status_code=status.HTTP_201_CREATED)
def create_phase(
        torneo_id: int,
        fase: FaseCreate,
        db: Session = Depends(get_db),
        admin_id: int = Depends(is_admin)
):
    """
    Permite al Administrador crear una Fase dentro de un Torneo.

    RF-5.2: Creación de Fases
    """
    # Verificar que el torneo existe
    torneo = db.query(Torneo).filter(Torneo.id_torneo == torneo_id).first()
    if not torneo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Torneo no encontrado."
        )

    # Verificar que el formato existe
    formato = db.query(FormatoFase).filter(FormatoFase.id_formato == fase.id_formato).first()
    if not formato:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formato de fase no encontrado."
        )

    # Verificar que no exista otra fase con el mismo orden en este torneo
    existing_fase = db.query(Fase).filter(
        Fase.id_torneo == torneo_id,
        Fase.orden == fase.orden
    ).first()

    if existing_fase:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una fase con orden {fase.orden} en este torneo."
        )

    db_fase = Fase(
        nombre=fase.nombre,
        orden=fase.orden,
        id_torneo=torneo_id,
        id_formato=fase.id_formato
    )

    try:
        db.add(db_fase)
        db.commit()
        db.refresh(db_fase)
        logger.info(f"✅ Fase '{fase.nombre}' creada en torneo ID {torneo_id}")
        return db_fase
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al crear fase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear la fase."
        )


@router.get("/{torneo_id}/phases/", response_model=List[FaseSchema])
def get_tournament_phases(torneo_id: int, db: Session = Depends(get_db)):
    """Obtiene todas las fases de un torneo"""
    torneo = db.query(Torneo).filter(Torneo.id_torneo == torneo_id).first()
    if not torneo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Torneo no encontrado."
        )

    fases = db.query(Fase).filter(Fase.id_torneo == torneo_id).order_by(Fase.orden).all()
    return fases


@router.post("/phases/{fase_id}/teams/", status_code=status.HTTP_201_CREATED)
def assign_teams_to_phase(
        fase_id: int,
        equipos_data: List[FaseEquipoCreate],
        db: Session = Depends(get_db),
        admin_id: int = Depends(is_admin)
):
    """
    Asigna equipos a una Fase, definiendo grupos o cabezas de serie si es necesario.

    RF-5.4: Asignación de Equipos a Fases
    RF-5.5: Configuración de Grupos y Cabezas de Serie
    """
    fase = db.query(Fase).filter(Fase.id_fase == fase_id).first()
    if not fase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fase no encontrada."
        )

    formato_nombre = fase.formato.nombre
    equipos_asignados = []

    for equipo_data in equipos_data:
        # Verificar que el equipo existe
        equipo = db.query(Equipo).filter(Equipo.id_equipo == equipo_data.id_equipo).first()
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipo con ID {equipo_data.id_equipo} no encontrado."
            )

        # Validación: Para formato 'Grupos', el nombre del grupo es obligatorio
        if formato_nombre == "Grupos" and not equipo_data.nombre_grupo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para formato 'Grupos', el nombre del grupo es obligatorio."
            )

        # Verificar que el equipo no esté ya asignado a esta fase
        existing_assignment = db.query(FaseEquipo).filter(
            FaseEquipo.id_fase == fase_id,
            FaseEquipo.id_equipo == equipo_data.id_equipo
        ).first()

        if existing_assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El equipo '{equipo.nombre}' ya está asignado a esta fase."
            )

        # Crear el registro de asignación
        db_fase_equipo = FaseEquipo(
            id_fase=fase_id,
            id_equipo=equipo_data.id_equipo,
            nombre_grupo=equipo_data.nombre_grupo,
            es_cabeza_serie=equipo_data.es_cabeza_serie
        )

        equipos_asignados.append(db_fase_equipo)

    try:
        for equipo_asignado in equipos_asignados:
            db.add(equipo_asignado)
        db.commit()
        logger.info(f"✅ {len(equipos_asignados)} equipos asignados a fase ID {fase_id}")
        return {
            "message": "Equipos asignados a la fase correctamente.",
            "equipos_asignados": len(equipos_asignados)
        }
    except IntegrityError as e:
        db.rollback()
        logger.error(f"❌ Error de integridad al asignar equipos: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al asignar equipos. Verifique que no haya duplicados."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al asignar equipos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al asignar equipos a la fase."
        )


@router.get("/phases/{fase_id}/teams/")
def get_phase_teams(fase_id: int, db: Session = Depends(get_db)):
    """Obtiene todos los equipos asignados a una fase"""
    fase = db.query(Fase).filter(Fase.id_fase == fase_id).first()
    if not fase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fase no encontrada."
        )

    asignaciones = db.query(FaseEquipo).filter(FaseEquipo.id_fase == fase_id).all()

    equipos_info = []
    for asignacion in asignaciones:
        equipo = db.query(Equipo).filter(Equipo.id_equipo == asignacion.id_equipo).first()
        if equipo:
            equipos_info.append({
                "id_equipo": equipo.id_equipo,
                "nombre": equipo.nombre,
                "nombre_grupo": asignacion.nombre_grupo,
                "es_cabeza_serie": asignacion.es_cabeza_serie
            })

    return {
        "fase_id": fase_id,
        "fase_nombre": fase.nombre,
        "formato": fase.formato.nombre,
        "equipos": equipos_info
    }


@router.post("/phases/{fase_id}/generate-schedule/", status_code=status.HTTP_201_CREATED)
def generate_schedule(
        fase_id: int,
        db: Session = Depends(get_db),
        admin_id: int = Depends(is_admin)
):
    """
    Genera automáticamente el calendario para fases de formato 'Liga' o 'Grupos'.

    RF-5.7: Generación Automática de Calendario
    """
    fase = db.query(Fase).filter(Fase.id_fase == fase_id).first()
    if not fase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fase no encontrada."
        )

    formato_nombre = fase.formato.nombre

    if formato_nombre not in ["Liga", "Grupos"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se genera calendario para formatos 'Liga' o 'Grupos'."
        )

    # Verificar si ya existen partidos para esta fase
    existing_matches = db.query(Partido).filter(Partido.id_fase == fase_id).count()
    if existing_matches > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La fase ya tiene {existing_matches} partidos generados. Elimínelos primero si desea regenerar."
        )

    # Obtener equipos de la fase
    equipos_en_fase = db.query(FaseEquipo).filter(FaseEquipo.id_fase == fase_id).all()

    if len(equipos_en_fase) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se necesitan al menos 2 equipos para generar el calendario."
        )

    # Organizar equipos por grupo si es formato Grupos
    if formato_nombre == "Grupos":
        grupos = {}
        for asignacion in equipos_en_fase:
            grupo = asignacion.nombre_grupo or "Sin Grupo"
            if grupo not in grupos:
                grupos[grupo] = []
            grupos[grupo].append(asignacion.id_equipo)

        # Generar partidos por grupo
        partidos_generados = []
        fecha_base = datetime.now() + timedelta(days=7)  # Empezar en una semana
        contador_dias = 0

        for grupo, equipo_ids in grupos.items():
            if len(equipo_ids) < 2:
                continue

            # Algoritmo Round-Robin simple
            for i in range(len(equipo_ids)):
                for j in range(i + 1, len(equipo_ids)):
                    partido = Partido(
                        id_fase=fase_id,
                        id_equipo_local=equipo_ids[i],
                        id_equipo_visitante=equipo_ids[j],
                        fecha_hora=fecha_base + timedelta(days=contador_dias),
                        lugar=f"Cancha Principal - Grupo {grupo}"
                    )
                    partidos_generados.append(partido)
                    contador_dias += 1
    else:
        # Formato Liga: todos contra todos
        equipo_ids = [asignacion.id_equipo for asignacion in equipos_en_fase]
        partidos_generados = []
        fecha_base = datetime.now() + timedelta(days=7)
        contador_dias = 0

        for i in range(len(equipo_ids)):
            for j in range(i + 1, len(equipo_ids)):
                partido = Partido(
                    id_fase=fase_id,
                    id_equipo_local=equipo_ids[i],
                    id_equipo_visitante=equipo_ids[j],
                    fecha_hora=fecha_base + timedelta(days=contador_dias),
                    lugar="Cancha Principal"
                )
                partidos_generados.append(partido)
                contador_dias += 1

    try:
        for partido in partidos_generados:
            db.add(partido)
        db.commit()
        logger.info(f"✅ {len(partidos_generados)} partidos generados para fase ID {fase_id}")
        return {
            "message": f"Calendario de {len(partidos_generados)} partidos generado para la fase '{fase.nombre}'.",
            "partidos_generados": len(partidos_generados)
        }
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al generar calendario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al generar el calendario."
        )


@router.get("/phases/{fase_id}/matches/")
def get_phase_matches(fase_id: int, db: Session = Depends(get_db)):
    """Obtiene todos los partidos de una fase"""
    fase = db.query(Fase).filter(Fase.id_fase == fase_id).first()
    if not fase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fase no encontrada."
        )

    partidos = db.query(Partido).filter(Partido.id_fase == fase_id).all()

    partidos_info = []
    for partido in partidos:
        equipo_local = db.query(Equipo).filter(Equipo.id_equipo == partido.id_equipo_local).first()
        equipo_visitante = db.query(Equipo).filter(Equipo.id_equipo == partido.id_equipo_visitante).first()

        partidos_info.append({
            "id_partido": partido.id_partido,
            "fecha_hora": partido.fecha_hora,
            "lugar": partido.lugar,
            "equipo_local": equipo_local.nombre if equipo_local else "TBD",
            "equipo_visitante": equipo_visitante.nombre if equipo_visitante else "TBD"
        })

    return {
        "fase_id": fase_id,
        "fase_nombre": fase.nombre,
        "total_partidos": len(partidos_info),
        "partidos": partidos_info
    }


@router.patch("/phases/{fase_id}/apply-bonus/", response_model=FaseSchema)
def apply_bonus(
        fase_id: int,
        db: Session = Depends(get_db),
        admin_id: int = Depends(is_admin)
):
    """
    Permite al Administrador aplicar la bonificación de puntos a la Fase.

    RF-5.8: Bonificación de Puntos (+0.75, +0.50)
    """
    fase = db.query(Fase).filter(Fase.id_fase == fase_id).first()
    if not fase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fase no encontrada."
        )

    if fase.bonificacion_aplicada:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La bonificación ya ha sido aplicada a esta fase."
        )

    fase.bonificacion_aplicada = True

    try:
        db.commit()
        db.refresh(fase)
        logger.info(f"✅ Bonificación aplicada a fase ID {fase_id}")
        return fase
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al aplicar bonificación: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al aplicar bonificación."
        )