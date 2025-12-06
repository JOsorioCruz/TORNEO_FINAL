from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from database import get_db
# Importar todos los modelos necesarios
from models import Equipo, Jugador, TipoJugador, Fase, Partido, Torneo, FormatoFase
from schemas import EquipoPlantilla, PartidoPublico, FaseVistaPublica, JugadorPublico
from typing import List, Optional

router = APIRouter(prefix="/public", tags=["Vista Pública (M8)"])


# Endpoint 1: Obtener Plantillas de Equipos Validados (RF-8.1)
@router.get("/teams-rosters/", response_model=List[EquipoPlantilla])
def get_validated_rosters(db: Session = Depends(get_db)):
    """Muestra públicamente la lista de equipos y sus plantillas de jugadores Validados (RF-8.1)."""

    # OPTIMIZACIÓN: Cargar relaciones delegado y tipo_jugador en una sola consulta
    equipos = db.query(Equipo).options(
        joinedload(Equipo.delegado)
    ).all()

    public_data = []

    for equipo in equipos:
        # Filtrar solo jugadores 'Validado' (RF-8.1)
        # Nota: La consulta separada aquí es necesaria para aplicar el filtro de estado_validacion
        jugadores_validados = db.query(Jugador).join(TipoJugador).filter(
            Jugador.id_equipo == equipo.id_equipo,
            Jugador.estado_validacion == 'Validado'
        ).options(joinedload(Jugador.tipo_jugador)).all()

        # Mapeo de jugadores a su esquema público
        jugadores_publicos = [
            JugadorPublico(
                nombre_completo=j.nombre_completo,
                numero_camiseta=j.numero_camiseta,
                cedula=j.cedula,
                estado_validacion=j.estado_validacion
            ) for j in jugadores_validados
        ]

        # Obtener email del delegado usando la relación cargada (joinedload)
        delegado_email = equipo.delegado.email if equipo.delegado else "N/A"

        public_data.append(EquipoPlantilla(
            id_equipo=equipo.id_equipo,
            nombre=equipo.nombre,
            delegado_email=delegado_email,
            jugadores_validados=jugadores_publicos
        ))

    return public_data


# Endpoint 2: Obtener el Calendario Completo (RF-8.2)
@router.get("/schedule/", response_model=List[PartidoPublico])
def get_public_schedule(db: Session = Depends(get_db)):
    """Muestra públicamente el Calendario completo de las fases creadas (RF-8.2)."""

    # OPTIMIZACIÓN: Cargar Fase, Equipo Local y Equipo Visitante en una sola consulta
    partidos_query = db.query(Partido).options(
        joinedload(Partido.fase),
        joinedload(Partido.equipo_local),
        joinedload(Partido.equipo_visitante)
    ).all()

    calendario = []
    for p in partidos_query:
        # Usar la relación 'fase' que fue cargada (evitando la consulta N+1)
        fase_nombre = p.fase.nombre if p.fase else "Desconocida"

        calendario.append(PartidoPublico(
            id_partido=p.id_partido,
            fecha_hora=p.fecha_hora,
            lugar=p.lugar,
            fase_nombre=fase_nombre,
            equipo_local_nombre=p.equipo_local.nombre if p.equipo_local else "TBD",
            equipo_visitante_nombre=p.equipo_visitante.nombre if p.equipo_visitante else "TBD"
        ))

    return calendario


# Endpoint 3: Obtener Estructura de Fases (Tablas y Llaves) (RF-8.3, RF-8.4)
@router.get("/tournament-structure/", response_model=List[FaseVistaPublica])
def get_tournament_structure(db: Session = Depends(get_db)):
    """Muestra la estructura del torneo (fases), incluyendo Tablas y Llaves (Inicialmente vacías)."""

    torneo_activo = db.query(Torneo).filter(Torneo.esta_activo == True).first()
    if not torneo_activo:
        return []

    # OPTIMIZACIÓN: Cargar FormatoFase junto con la Fase
    fases_query = db.query(Fase).filter(Fase.id_torneo == torneo_activo.id_torneo).options(
        joinedload(Fase.formato)
    ).order_by(Fase.orden).all()

    public_structure = []
    for fase in fases_query:
        # Usar la relación 'formato' cargada
        formato_nombre = fase.formato.nombre if fase.formato else "Desconocido"

        public_structure.append(FaseVistaPublica(
            id_fase=fase.id_fase,
            nombre=fase.nombre,
            formato=formato_nombre,
            tablas_posiciones=[],  # Alimentadas en Fase 2 [cite: 69]
            llaves=[]  # Alimentadas en Fase 2 [cite: 70]
        ))

    return public_structure


# Endpoint 4: Páginas de Estadísticas (Inicialmente Vacías) (RF-8.5)
@router.get("/statistics-placeholders/")
def get_statistics_placeholders():
    """Muestra las páginas (inicialmente vacías) para las Estadísticas del torneo (RF-8.5)."""
    return {
        "message": "Páginas de estadísticas habilitadas.",
        "goleador": "Pendiente de implementación en Fase 2.",
        "valla_menos_vencida": "Pendiente de implementación en Fase 2."
    }