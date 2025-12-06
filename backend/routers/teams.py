"""
teams_REFACTORIZADO.py - Ejemplo de Refactorización
===================================================

Este archivo muestra cómo REFACTORIZAR teams.py para:
1. Eliminar funciones de seguridad duplicadas
2. Usar las dependencias de security.py
3. Mejorar la validación de archivos

CAMBIOS PRINCIPALES:
- ❌ Eliminar get_current_user_id() y get_current_admin_id() locales
- ✅ Usar dependencias de security.py
- ✅ Añadir validación robusta de archivos
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from backend.database import get_db
from backend.models import Equipo, Usuario, Jugador, TipoJugador
from backend.schemas import (
    EquipoCreate,
    Equipo as EquipoSchema,
    Jugador as JugadorSchema,
    TipoJugadorSchema,
    JugadorValidation
)
from typing import List, Optional
from datetime import date, datetime
import logging

# ✅ CORRECCIÓN: Importar desde security.py en lugar de definir localmente
from backend.security import (
    get_current_user,
    get_current_user_id,
    is_admin,
    require_team_ownership
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["Equipos y Jugadores"])

# ========================================
# ❌ ELIMINAR ESTAS FUNCIONES LOCALES
# ========================================
# def get_current_user_id() -> int:
#     return 2  # ⚠️ HARDCODED - INSEGURO
#
# def get_current_admin_id() -> int:
#     return 1  # ⚠️ HARDCODED - INSEGURO
#
# def is_admin(admin_id: int = Depends(get_current_admin_id)):
#     if admin_id != 1:
#         raise HTTPException(...)
#     return admin_id


# ========================================
# ✅ NUEVA FUNCIÓN: VALIDACIÓN DE ARCHIVOS
# ========================================

# Configuración de archivos permitidos
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg"}
ALLOWED_DOC_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_DOC_SIZE = 10 * 1024 * 1024  # 10MB

UPLOAD_DIR = "uploads"


def validate_uploaded_file(
        file: UploadFile,
        allowed_types: set,
        max_size: int,
        field_name: str
) -> tuple[str, str]:
    """
    Valida un archivo subido.

    Args:
        file: Archivo subido
        allowed_types: Tipos MIME permitidos
        max_size: Tamaño máximo en bytes
        field_name: Nombre del campo (para mensajes de error)

    Returns:
        Tupla (filename_seguro, extension)

    Raises:
        HTTPException 400: Si el archivo no es válido
    """
    # Validar que el archivo tiene un nombre
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name}: Archivo sin nombre"
        )

    # Validar tipo MIME
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name}: Tipo de archivo no permitido. Permitidos: {', '.join(allowed_types)}"
        )

    # Validar tamaño
    file.file.seek(0, 2)  # Ir al final del archivo
    size = file.file.tell()
    file.file.seek(0)  # Volver al inicio

    if size > max_size:
        max_mb = max_size / 1024 / 1024
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name}: Archivo muy grande (máximo {max_mb}MB)"
        )

    if size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name}: Archivo vacío"
        )

    # Sanitizar nombre de archivo
    # Eliminar caracteres peligrosos y mantener solo el nombre base
    filename = os.path.basename(file.filename)
    # Reemplazar caracteres problemáticos
    filename = filename.replace(" ", "_")
    filename = "".join(c for c in filename if c.isalnum() or c in "._-")

    # Obtener extensión
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    if not extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name}: Archivo sin extensión"
        )

    return filename, extension


# ========================================
# ENDPOINTS REFACTORIZADOS
# ========================================

@router.get("/tipos-jugador/", response_model=List[TipoJugadorSchema])
def get_tipos_jugador(db: Session = Depends(get_db)):
    """
    Muestra las opciones de Tipo de Jugador del reglamento.
    RF-2.4: Tipos de Jugador
    """
    tipos = db.query(TipoJugador).all()

    if not tipos:
        tipos_data = [
            {"nombre": "vecino del barrio san luis"},
            {"nombre": "agente de policía (estación vallejo)"},
            {"nombre": "docente/trabajador (institución educativa el dorado)"},
            {"nombre": "docente/trabajador/padre (fundación vallejo)"}
        ]

        for tipo_data in tipos_data:
            db_tipo = TipoJugador(**tipo_data)
            db.add(db_tipo)

        db.commit()
        tipos = db.query(TipoJugador).all()
        logger.info("✅ Tipos de jugador precargados")

    return tipos


@router.post("/", response_model=EquipoSchema, status_code=status.HTTP_201_CREATED)
def create_team(
        team_data: EquipoCreate,
        db: Session = Depends(get_db),
        # ✅ CORRECCIÓN: Usar dependencia de security.py
        delegado_id: int = Depends(get_current_user_id)
):
    """
    Permite al Delegado crear un equipo y se asigna automáticamente como delegado.
    RF-2.1: Creación de Equipos

    ✅ MEJORAS:
    - Usa get_current_user_id de security.py (autenticación real)
    - No más IDs hardcodeados
    """
    # Validación de Rol del Creador
    usuario = db.query(Usuario).filter(Usuario.id_usuario == delegado_id).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )

    # Verificar que el usuario tiene rol de Delegado o Administrador
    role_name = usuario.rol.nombre
    if role_name not in ["Delegado", "Administrador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo Delegados o Administradores pueden crear equipos."
        )

    # Creación del equipo
    db_team = Equipo(nombre=team_data.nombre, id_delegado=delegado_id)

    try:
        db.add(db_team)
        db.commit()
        db.refresh(db_team)
        logger.info(f"✅ Equipo '{team_data.nombre}' creado por {usuario.email}")
        return db_team
    except IntegrityError:
        db.rollback()
        logger.warning(f"⚠️ Intento de crear equipo duplicado: {team_data.nombre}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El equipo '{team_data.nombre}' ya existe."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al crear equipo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el equipo."
        )


@router.get("/", response_model=List[EquipoSchema])
def get_teams(db: Session = Depends(get_db)):
    """Obtiene la lista de todos los equipos"""
    teams = db.query(Equipo).all()
    return teams


@router.get("/{team_id}", response_model=EquipoSchema)
def get_team(team_id: int, db: Session = Depends(get_db)):
    """Obtiene un equipo por ID"""
    team = db.query(Equipo).filter(Equipo.id_equipo == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipo no encontrado."
        )
    return team


@router.post("/{team_id}/players/", response_model=JugadorSchema, status_code=status.HTTP_201_CREATED)
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
        # ✅ CORRECCIÓN: Usar get_current_user en lugar de get_current_user_id
        current_user: Usuario = Depends(get_current_user)
):
    """
    Permite al Delegado agregar un jugador a su equipo con validaciones de reglamento.

    ✅ MEJORAS:
    - Validación robusta de archivos (tipo, tamaño)
    - Usa autenticación real de security.py
    - Usa require_team_ownership para verificar permisos

    RF-2.2: Agregar Jugadores
    RF-2.3: Foto del Jugador
    RF-2.5: Documentos Probatorios
    RF-2.7: Cuotas de Extranjeros
    RF-2.8: Edad Mínima de Extranjeros
    RF-2.9: Unicidad de Cédula y Camiseta
    """
    # ✅ CORRECCIÓN: Usar función de security.py para verificar ownership
    require_team_ownership(team_id, current_user, db)

    # Validación de Propiedad y Límites
    team = db.query(Equipo).filter(Equipo.id_equipo == team_id).first()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipo no encontrado."
        )

    # Validar límite de 16 jugadores
    current_players_count = db.query(Jugador).filter(Jugador.id_equipo == team_id).count()
    if current_players_count >= 16:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Máximo 16 jugadores por equipo alcanzado (RF-2.2)."
        )

    # Validación de Cédula (RF-2.9)
    if db.query(Jugador).filter(Jugador.cedula == cedula).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cédula ya está registrada."
        )

    # Validación de Número de Camiseta (RF-2.9)
    if numero_camiseta is not None:
        if not (1 <= numero_camiseta <= 20):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El número de camiseta debe estar entre 1 y 20."
            )

        existing_jersey = db.query(Jugador).filter(
            Jugador.id_equipo == team_id,
            Jugador.numero_camiseta == numero_camiseta
        ).first()

        if existing_jersey:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El número de camiseta ya está ocupado en este equipo (RF-2.9)."
            )

    # Validación de Tipo de Jugador
    tipo_jugador = db.query(TipoJugador).filter(
        TipoJugador.id_tipo_jugador == id_tipo_jugador
    ).first()

    if not tipo_jugador:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de jugador no válido."
        )

    tipo_nombre = tipo_jugador.nombre.lower()

    # Tipos de "extranjeros" definidos por el reglamento (RF-2.4)
    TIPO_POLICIA = "agente de policía (estación vallejo)"
    TIPO_IE = "docente/trabajador (institución educativa el dorado)"
    TIPO_FUNDACION = "docente/trabajador/padre (fundación vallejo)"

    tipos_extranjeros = [TIPO_POLICIA, TIPO_IE, TIPO_FUNDACION]
    is_foreign_player = tipo_nombre in tipos_extranjeros

    # Validación de Cuotas (RF-2.7)
    if is_foreign_player:
        # Validación Global: Máximo 3 "Extranjeros"
        current_extranjeros_count = db.query(func.count(Jugador.id_jugador)).join(TipoJugador).filter(
            Jugador.id_equipo == team_id,
            TipoJugador.nombre.in_(tipos_extranjeros)
        ).scalar()

        if current_extranjeros_count >= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Máximo 3 'Extranjeros' por equipo alcanzado (RF-2.7)."
            )

        # Validación Granular: Máximo 2 Docentes I.E. El Dorado
        if tipo_nombre == TIPO_IE:
            count_ie = db.query(func.count(Jugador.id_jugador)).join(TipoJugador).filter(
                Jugador.id_equipo == team_id,
                TipoJugador.nombre == TIPO_IE
            ).scalar()

            if count_ie >= 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Máximo 2 Docentes/Trabajadores I.E. El Dorado por equipo (RF-2.7)."
                )

        # Validación Granular: Máximo 2 Docentes/Padres Fundación
        if tipo_nombre == TIPO_FUNDACION:
            count_fundacion = db.query(func.count(Jugador.id_jugador)).join(TipoJugador).filter(
                Jugador.id_equipo == team_id,
                TipoJugador.nombre == TIPO_FUNDACION
            ).scalar()

            if count_fundacion >= 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Máximo 2 Docentes/Trabajadores/Padres Fundación por equipo (RF-2.7)."
                )

    # Validación de Edad para Extranjeros (RF-2.8)
    if is_foreign_player:
        today = date.today()
        age = today.year - fecha_nacimiento.year - (
                (today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
        )

        if age < 26:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los jugadores 'Extranjeros' deben tener 26 años o más (RF-2.8)."
            )

    # ✅ MEJORA: Validación robusta de archivos
    try:
        foto_filename, foto_ext = validate_uploaded_file(
            foto,
            ALLOWED_IMAGE_TYPES,
            MAX_IMAGE_SIZE,
            "Foto"
        )

        doc_filename, doc_ext = validate_uploaded_file(
            documento_probatorio,
            ALLOWED_DOC_TYPES,
            MAX_DOC_SIZE,
            "Documento probatorio"
        )
    except HTTPException:
        raise

    # Guardado de Archivos (RF-2.5)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    foto_filename_final = f"{team_id}_{cedula}_FOTO_{timestamp}.{foto_ext}"
    doc_filename_final = f"{team_id}_{cedula}_DOC_{timestamp}.{doc_ext}"

    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Guardar Foto
        foto_path = os.path.join(UPLOAD_DIR, foto_filename_final)
        with open(foto_path, "wb") as f:
            content = await foto.read()
            f.write(content)

        # Guardar Documento
        doc_path = os.path.join(UPLOAD_DIR, doc_filename_final)
        with open(doc_path, "wb") as f:
            content = await documento_probatorio.read()
            f.write(content)

        logger.info(f"✅ Archivos guardados: {foto_filename_final}, {doc_filename_final}")

    except Exception as e:
        logger.error(f"❌ Error al guardar archivos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar archivos: {str(e)}"
        )

    # Creación del registro en BD
    db_jugador = Jugador(
        cedula=cedula,
        nombre_completo=nombre_completo,
        fecha_nacimiento=fecha_nacimiento,
        numero_camiseta=numero_camiseta,
        id_tipo_jugador=id_tipo_jugador,
        id_equipo=team_id,
        foto_url=foto_path,
        documento_probatorio_url=doc_path,
        estado_validacion='Pendiente'
    )

    try:
        db.add(db_jugador)
        db.commit()
        db.refresh(db_jugador)
        logger.info(f"✅ Jugador '{nombre_completo}' agregado al equipo ID {team_id}")
        return db_jugador
    except Exception as e:
        db.rollback()
        # Intentar eliminar archivos si falla la BD
        try:
            if os.path.exists(foto_path):
                os.remove(foto_path)
            if os.path.exists(doc_path):
                os.remove(doc_path)
        except:
            pass
        logger.error(f"❌ Error al crear jugador: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el jugador."
        )


@router.get("/{team_id}/players/", response_model=List[JugadorSchema])
def get_team_players(team_id: int, db: Session = Depends(get_db)):
    """Obtiene todos los jugadores de un equipo"""
    team = db.query(Equipo).filter(Equipo.id_equipo == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipo no encontrado."
        )

    players = db.query(Jugador).filter(Jugador.id_equipo == team_id).all()
    return players


@router.patch("/players/{player_id}/validate/", response_model=JugadorSchema)
def validate_player(
        player_id: int,
        validation_data: JugadorValidation,
        db: Session = Depends(get_db),
        # ✅ CORRECCIÓN: Usar dependencia de security.py
        admin_id: int = Depends(is_admin)
):
    """
    Permite al Administrador Validar o Rechazar a un jugador.

    ✅ MEJORAS:
    - Usa is_admin de security.py (autenticación real)
    - No más verificaciones hardcodeadas

    RF-2.6: Validación de Jugadores
    """
    db_jugador = db.query(Jugador).filter(Jugador.id_jugador == player_id).first()

    if not db_jugador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jugador no encontrado."
        )

    # Validar que el estado sea uno permitido
    new_state = validation_data.estado_validacion
    if new_state not in ['Validado', 'Rechazado']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El estado debe ser 'Validado' o 'Rechazado'."
        )

    db_jugador.estado_validacion = new_state
    db_jugador.fecha_validacion = datetime.now() if new_state == 'Validado' else None

    try:
        db.commit()
        db.refresh(db_jugador)
        logger.info(f"✅ Jugador ID {player_id} {new_state.lower()} por admin ID {admin_id}")
        return db_jugador
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al validar jugador: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al validar el jugador."
        )


@router.get("/players/pending/", response_model=List[JugadorSchema])
def get_pending_players(
        db: Session = Depends(get_db),
        # ✅ CORRECCIÓN: Usar dependencia de security.py
        admin_id: int = Depends(is_admin)
):
    """
    Lista todos los jugadores en estado 'Pendiente' para revisión del Admin.

    ✅ MEJORAS:
    - Usa is_admin de security.py

    RF-2.6: Panel de Validación
    """
    pending_players = db.query(Jugador).filter(
        Jugador.estado_validacion == 'Pendiente'
    ).all()

    return pending_players


# ========================================
# RESUMEN DE CAMBIOS
# ========================================
"""
CAMBIOS REALIZADOS EN ESTA REFACTORIZACIÓN:

1. ❌ ELIMINADO:
   - Funciones locales get_current_user_id() hardcodeadas
   - Funciones locales get_current_admin_id() hardcodeadas
   - Función local is_admin() hardcodeada

2. ✅ AGREGADO:
   - Importación de dependencias desde security.py
   - Función validate_uploaded_file() para validación robusta
   - Configuración de tipos y tamaños de archivos permitidos
   - Uso de require_team_ownership() de security.py

3. ✅ MEJORADO:
   - Validación de archivos (tipo, tamaño, sanitización)
   - Autenticación real con JWT
   - Mensajes de log más informativos con emails de usuarios

PRÓXIMOS PASOS:
1. Hacer lo mismo con tournaments.py
2. Actualizar main.py para incluir el nuevo users.py
3. Añadir tests unitarios
4. Documentar con Swagger/OpenAPI
"""