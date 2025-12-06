from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db
from backend.models import Equipo, Jugador, TipoJugador, Fase, Partido, Torneo
from backend.schemas import EquipoPlantilla, PartidoPublico, FaseVistaPublica, JugadorPublico
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["Vista Pública (M8)"])


@router.get("/teams-rosters/", response_model=List[EquipoPlantilla])
def get_validated_rosters(db: Session = Depends(get_db)):
    """
    Muestra públicamente la lista de equipos y sus plantillas de jugadores Validados.

    RF-8.1: Plantillas de Equipos Validados
    """
    try:
        # OPTIMIZACIÓN: Cargar relaciones delegado en una sola consulta
        equipos = db.query(Equipo).options(
            joinedload(Equipo.delegado)
        ).all()

        public_data = []

        for equipo in equipos:
            # Filtrar solo jugadores 'Validado' (RF-8.1)
            # OPTIMIZACIÓN: Usar joinedload para cargar tipo_jugador
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

        logger.info(f"✅ Consultadas plantillas de {len(public_data)} equipos")
        return public_data

    except Exception as e:
        logger.error(f"❌ Error al obtener plantillas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener las plantillas de equipos."
        )


@router.get("/schedule/", response_model=List[PartidoPublico])
def get_public_schedule(db: Session = Depends(get_db)):
    """
    Muestra públicamente el Calendario completo de las fases creadas.

    RF-8.2: Calendario Completo
    """
    try:
        # OPTIMIZACIÓN: Cargar Fase, Equipo Local y Equipo Visitante en una sola consulta
        partidos_query = db.query(Partido).options(
            joinedload(Partido.fase),
            joinedload(Partido.equipo_local),
            joinedload(Partido.equipo_visitante)
        ).order_by(Partido.fecha_hora).all()

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

        logger.info(f"✅ Calendario público con {len(calendario)} partidos")
        return calendario

    except Exception as e:
        logger.error(f"❌ Error al obtener calendario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el calendario."
        )


@router.get("/tournament-structure/", response_model=List[FaseVistaPublica])
def get_tournament_structure(db: Session = Depends(get_db)):
    """
    Muestra la estructura del torneo (fases), incluyendo Tablas y Llaves.

    RF-8.3: Tablas de Posiciones (Inicialmente vacías)
    RF-8.4: Llaves de Eliminación (Inicialmente vacías)
    """
    try:
        # Buscar el torneo activo
        torneo_activo = db.query(Torneo).filter(Torneo.esta_activo == True).first()

        if not torneo_activo:
            logger.info("⚠️ No hay torneo activo")
            return []

        # OPTIMIZACIÓN: Cargar FormatoFase junto con la Fase
        fases_query = db.query(Fase).filter(
            Fase.id_torneo == torneo_activo.id_torneo
        ).options(
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
                tablas_posiciones=[],  # Alimentadas en Fase 2
                llaves=[]  # Alimentadas en Fase 2
            ))

        logger.info(f"✅ Estructura del torneo con {len(public_structure)} fases")
        return public_structure

    except Exception as e:
        logger.error(f"❌ Error al obtener estructura del torneo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener la estructura del torneo."
        )


@router.get("/statistics-placeholders/")
def get_statistics_placeholders():
    """
    Muestra las páginas (inicialmente vacías) para las Estadísticas del torneo.

    RF-8.5: Páginas de Estadísticas
    """
    logger.info("✅ Páginas de estadísticas consultadas (placeholders)")
    return {
        "message": "Páginas de estadísticas habilitadas.",
        "estadisticas_disponibles": {
            "goleador": {
                "estado": "Pendiente de implementación en Fase 2",
                "descripcion": "Tabla de goleadores del torneo"
            },
            "valla_menos_vencida": {
                "estado": "Pendiente de implementación en Fase 2",
                "descripcion": "Porteros con menos goles recibidos"
            },
            "tarjetas": {
                "estado": "Pendiente de implementación en Fase 2",
                "descripcion": "Jugadores con más tarjetas"
            },
            "fair_play": {
                "estado": "Pendiente de implementación en Fase 2",
                "descripcion": "Equipos con mejor comportamiento"
            }
        },
        "nota": "Estas estadísticas se calcularán automáticamente una vez se registren los resultados de los partidos."
    }


@router.get("/active-tournament/")
def get_active_tournament(db: Session = Depends(get_db)):
    """Obtiene información del torneo activo"""
    try:
        torneo_activo = db.query(Torneo).filter(Torneo.esta_activo == True).first()

        if not torneo_activo:
            return {
                "message": "No hay torneo activo actualmente",
                "torneo": None
            }

        # Contar fases y partidos del torneo
        total_fases = db.query(Fase).filter(Fase.id_torneo == torneo_activo.id_torneo).count()

        total_partidos = db.query(Partido).join(Fase).filter(
            Fase.id_torneo == torneo_activo.id_torneo
        ).count()

        # Contar equipos inscritos (equipos con jugadores validados)
        equipos_con_validados = db.query(Equipo).join(Jugador).filter(
            Jugador.estado_validacion == 'Validado'
        ).distinct().count()

        logger.info(f"✅ Información del torneo activo '{torneo_activo.nombre}'")
        return {
            "torneo": {
                "id_torneo": torneo_activo.id_torneo,
                "nombre": torneo_activo.nombre,
                "fecha_inicio": torneo_activo.fecha_inicio,
                "fecha_fin": torneo_activo.fecha_fin,
                "esta_activo": torneo_activo.esta_activo
            },
            "estadisticas": {
                "total_fases": total_fases,
                "total_partidos": total_partidos,
                "equipos_inscritos": equipos_con_validados
            }
        }

    except Exception as e:
        logger.error(f"❌ Error al obtener torneo activo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener información del torneo activo."
        )


@router.get("/teams/{team_id}/roster/", response_model=EquipoPlantilla)
def get_team_roster(team_id: int, db: Session = Depends(get_db)):
    """Obtiene la plantilla de un equipo específico (solo jugadores validados)"""
    try:
        equipo = db.query(Equipo).options(
            joinedload(Equipo.delegado)
        ).filter(Equipo.id_equipo == team_id).first()

        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipo no encontrado."
            )

        jugadores_validados = db.query(Jugador).filter(
            Jugador.id_equipo == team_id,
            Jugador.estado_validacion == 'Validado'
        ).options(joinedload(Jugador.tipo_jugador)).all()

        jugadores_publicos = [
            JugadorPublico(
                nombre_completo=j.nombre_completo,
                numero_camiseta=j.numero_camiseta,
                cedula=j.cedula,
                estado_validacion=j.estado_validacion
            ) for j in jugadores_validados
        ]

        delegado_email = equipo.delegado.email if equipo.delegado else "N/A"

        logger.info(f"✅ Plantilla del equipo '{equipo.nombre}' consultada")
        return EquipoPlantilla(
            id_equipo=equipo.id_equipo,
            nombre=equipo.nombre,
            delegado_email=delegado_email,
            jugadores_validados=jugadores_publicos
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error al obtener plantilla del equipo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener la plantilla del equipo."
        )


@router.get("/phases/{fase_id}/schedule/", response_model=List[PartidoPublico])
def get_phase_schedule(fase_id: int, db: Session = Depends(get_db)):
    """Obtiene el calendario de una fase específica"""
    try:
        fase = db.query(Fase).filter(Fase.id_fase == fase_id).first()

        if not fase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fase no encontrada."
            )

        partidos = db.query(Partido).options(
            joinedload(Partido.fase),
            joinedload(Partido.equipo_local),
            joinedload(Partido.equipo_visitante)
        ).filter(
            Partido.id_fase == fase_id
        ).order_by(Partido.fecha_hora).all()

        calendario = []
        for p in partidos:
            calendario.append(PartidoPublico(
                id_partido=p.id_partido,
                fecha_hora=p.fecha_hora,
                lugar=p.lugar,
                fase_nombre=fase.nombre,
                equipo_local_nombre=p.equipo_local.nombre if p.equipo_local else "TBD",
                equipo_visitante_nombre=p.equipo_visitante.nombre if p.equipo_visitante else "TBD"
            ))

        logger.info(f"✅ Calendario de fase '{fase.nombre}' con {len(calendario)} partidos")
        return calendario

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error al obtener calendario de fase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el calendario de la fase."
        )