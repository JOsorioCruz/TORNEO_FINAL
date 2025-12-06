"""
users.py - Router de Gestión de Usuarios CORREGIDO
==================================================

Este archivo implementa CORRECTAMENTE el módulo de usuarios con:
- Registro de usuarios
- Login con JWT
- Gestión de perfil
- Listado de usuarios (admin)

REEMPLAZA el archivo users.py que estaba duplicado de tournaments.py
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from backend.database import get_db
from backend.models import Usuario as UsuarioModel, Rol as RolModel
from backend.schemas import (
    UsuarioCreate,
    Usuario as UsuarioSchema,
    Token,
    Rol as RolSchema
)
from backend.security import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_admin
)
from typing import List
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Gestión de Usuarios (M1)"])


# ========================================
# ENDPOINTS DE AUTENTICACIÓN
# ========================================

@router.post("/register", response_model=UsuarioSchema, status_code=status.HTTP_201_CREATED)
def register_user(
        user_data: UsuarioCreate,
        db: Session = Depends(get_db)
):
    """
    Registra un nuevo usuario en el sistema.

    RF-1.2: Registro de Usuarios

    Validaciones:
    - Email único
    - Rol válido
    - Contraseña se hashea automáticamente

    Args:
        user_data: Datos del usuario (nombre, email, password, id_rol)
        db: Sesión de base de datos

    Returns:
        Usuario creado (sin password)

    Raises:
        HTTPException 400: Si el email ya existe o el rol no es válido
        HTTPException 500: Error al crear usuario

    Ejemplo:
        POST /users/register
        {
            "nombre_usuario": "Juan Pérez",
            "email": "juan@example.com",
            "password": "contraseña_segura",
            "id_rol": 2
        }
    """
    # Verificar que el rol existe
    rol = db.query(RolModel).filter(RolModel.id_rol == user_data.id_rol).first()

    if not rol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol con ID {user_data.id_rol} no existe. Use 1 para Admin o 2 para Delegado."
        )

    # Verificar que el email no exista
    existing_user = db.query(UsuarioModel).filter(
        UsuarioModel.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El email '{user_data.email}' ya está registrado."
        )

    # Hashear la contraseña
    hashed_password = get_password_hash(user_data.password)

    # Crear el usuario
    db_user = UsuarioModel(
        nombre_usuario=user_data.nombre_usuario,
        email=user_data.email,
        password_hash=hashed_password,
        id_rol=user_data.id_rol
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"✅ Usuario registrado: {user_data.email} (Rol: {rol.nombre})")
        return db_user
    except IntegrityError as e:
        db.rollback()
        logger.error(f"❌ Error de integridad al registrar usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al registrar usuario. Verifique los datos."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al registrar usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al registrar el usuario."
        )


@router.post("/login", response_model=Token)
def login(
        email: str = Body(..., embed=True),
        password: str = Body(..., embed=True),
        db: Session = Depends(get_db)
):
    """
    Autentica un usuario y genera un token JWT.

    RF-1.1: Autenticación de Usuarios

    Args:
        email: Email del usuario
        password: Contraseña en texto plano
        db: Sesión de base de datos

    Returns:
        Token JWT y tipo de token

    Raises:
        HTTPException 401: Si las credenciales son incorrectas

    Ejemplo:
        POST /users/login
        {
            "email": "admin@torneo.com",
            "password": "admin123"
        }

        Respuesta:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "token_type": "bearer"
        }
    """
    user = authenticate_user(db, email, password)

    if not user:
        logger.warning(f"⚠️ Intento de login fallido para: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Crear token JWT
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id_usuario},
        expires_delta=access_token_expires
    )

    logger.info(f"✅ Login exitoso: {email} (Rol: {user.rol.nombre})")

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ========================================
# ENDPOINTS DE PERFIL
# ========================================

@router.get("/me", response_model=UsuarioSchema)
def get_current_user_profile(
        current_user: UsuarioModel = Depends(get_current_user)
):
    """
    Obtiene el perfil del usuario autenticado.

    RF-1.3: Consulta de Perfil

    Headers requeridos:
        Authorization: Bearer {token}

    Args:
        current_user: Usuario autenticado (inyectado por dependencia)

    Returns:
        Datos del usuario autenticado

    Ejemplo:
        GET /users/me
        Headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

        Respuesta:
        {
            "id_usuario": 1,
            "nombre_usuario": "Administrador",
            "email": "admin@torneo.com",
            "id_rol": 1,
            "rol": {
                "id_rol": 1,
                "nombre": "Administrador"
            }
        }
    """
    logger.info(f"📋 Consulta de perfil: {current_user.email}")
    return current_user


@router.patch("/me", response_model=UsuarioSchema)
def update_current_user_profile(
        nombre_usuario: str = Body(None),
        password: str = Body(None),
        current_user: UsuarioModel = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Actualiza el perfil del usuario autenticado.

    RF-1.4: Actualización de Perfil

    Campos actualizables:
    - nombre_usuario: Nuevo nombre de usuario
    - password: Nueva contraseña (se hasheará automáticamente)

    Args:
        nombre_usuario: Nuevo nombre (opcional)
        password: Nueva contraseña (opcional)
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Usuario actualizado

    Ejemplo:
        PATCH /users/me
        Headers: Authorization: Bearer {token}
        {
            "nombre_usuario": "Nuevo Nombre",
            "password": "nueva_contraseña"
        }
    """
    updated = False

    if nombre_usuario:
        current_user.nombre_usuario = nombre_usuario
        updated = True
        logger.info(f"📝 Actualización de nombre: {current_user.email}")

    if password:
        current_user.password_hash = get_password_hash(password)
        updated = True
        logger.info(f"🔒 Actualización de contraseña: {current_user.email}")

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron campos para actualizar"
        )

    try:
        db.commit()
        db.refresh(current_user)
        logger.info(f"✅ Perfil actualizado: {current_user.email}")
        return current_user
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al actualizar perfil: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el perfil"
        )


# ========================================
# ENDPOINTS DE ADMINISTRACIÓN
# ========================================

@router.get("/", response_model=List[UsuarioSchema])
def get_all_users(
        skip: int = 0,
        limit: int = 100,
        admin: UsuarioModel = Depends(get_current_admin),
        db: Session = Depends(get_db)
):
    """
    Lista todos los usuarios del sistema (solo admins).

    RF-1.5: Listado de Usuarios (Admin)

    Parámetros de paginación:
    - skip: Número de usuarios a saltar (default: 0)
    - limit: Máximo de usuarios a retornar (default: 100)

    Args:
        skip: Paginación - registros a saltar
        limit: Paginación - máximo de registros
        admin: Usuario administrador
        db: Sesión de base de datos

    Returns:
        Lista de usuarios

    Ejemplo:
        GET /users/?skip=0&limit=10
        Headers: Authorization: Bearer {admin_token}
    """
    users = db.query(UsuarioModel).options(
        joinedload(UsuarioModel.rol)
    ).offset(skip).limit(limit).all()

    logger.info(f"📋 Admin {admin.email} consultó lista de usuarios")
    return users


@router.get("/{user_id}", response_model=UsuarioSchema)
def get_user_by_id(
        user_id: int,
        admin: UsuarioModel = Depends(get_current_admin),
        db: Session = Depends(get_db)
):
    """
    Obtiene un usuario por ID (solo admins).

    RF-1.6: Consulta de Usuario por ID (Admin)

    Args:
        user_id: ID del usuario a buscar
        admin: Usuario administrador
        db: Sesión de base de datos

    Returns:
        Usuario encontrado

    Raises:
        HTTPException 404: Si el usuario no existe

    Ejemplo:
        GET /users/5
        Headers: Authorization: Bearer {admin_token}
    """
    user = db.query(UsuarioModel).options(
        joinedload(UsuarioModel.rol)
    ).filter(UsuarioModel.id_usuario == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado"
        )

    logger.info(f"📋 Admin {admin.email} consultó usuario ID {user_id}")
    return user


@router.patch("/{user_id}", response_model=UsuarioSchema)
def update_user_by_admin(
        user_id: int,
        nombre_usuario: str = Body(None),
        id_rol: int = Body(None),
        admin: UsuarioModel = Depends(get_current_admin),
        db: Session = Depends(get_db)
):
    """
    Actualiza un usuario (solo admins).

    RF-1.7: Actualización de Usuario (Admin)

    Los admins pueden modificar:
    - nombre_usuario: Cambiar nombre
    - id_rol: Cambiar rol

    Args:
        user_id: ID del usuario a actualizar
        nombre_usuario: Nuevo nombre (opcional)
        id_rol: Nuevo rol (opcional)
        admin: Usuario administrador
        db: Sesión de base de datos

    Returns:
        Usuario actualizado

    Raises:
        HTTPException 404: Si el usuario no existe
        HTTPException 400: Si el rol no es válido

    Ejemplo:
        PATCH /users/5
        Headers: Authorization: Bearer {admin_token}
        {
            "nombre_usuario": "Nuevo Nombre",
            "id_rol": 2
        }
    """
    user = db.query(UsuarioModel).filter(
        UsuarioModel.id_usuario == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado"
        )

    updated = False

    if nombre_usuario:
        user.nombre_usuario = nombre_usuario
        updated = True

    if id_rol:
        # Verificar que el rol existe
        rol = db.query(RolModel).filter(RolModel.id_rol == id_rol).first()
        if not rol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol con ID {id_rol} no existe"
            )
        user.id_rol = id_rol
        updated = True

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron campos para actualizar"
        )

    try:
        db.commit()
        db.refresh(user)
        logger.info(f"✅ Admin {admin.email} actualizó usuario ID {user_id}")
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al actualizar usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el usuario"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
        user_id: int,
        admin: UsuarioModel = Depends(get_current_admin),
        db: Session = Depends(get_db)
):
    """
    Elimina un usuario del sistema (solo admins).

    RF-1.8: Eliminación de Usuario (Admin)

    ADVERTENCIA: Esta acción es irreversible.

    Args:
        user_id: ID del usuario a eliminar
        admin: Usuario administrador
        db: Sesión de base de datos

    Returns:
        204 No Content si se elimina exitosamente

    Raises:
        HTTPException 404: Si el usuario no existe
        HTTPException 403: Si intenta eliminarse a sí mismo

    Ejemplo:
        DELETE /users/5
        Headers: Authorization: Bearer {admin_token}
    """
    # No permitir que el admin se elimine a sí mismo
    if user_id == admin.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes eliminarte a ti mismo"
        )

    user = db.query(UsuarioModel).filter(
        UsuarioModel.id_usuario == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado"
        )

    try:
        db.delete(user)
        db.commit()
        logger.info(f"✅ Admin {admin.email} eliminó usuario ID {user_id}")
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al eliminar usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el usuario"
        )


# ========================================
# ENDPOINTS DE ROLES
# ========================================

@router.get("/roles/", response_model=List[RolSchema])
def get_all_roles(db: Session = Depends(get_db)):
    """
    Obtiene todos los roles disponibles en el sistema.

    RF-1.9: Listado de Roles

    No requiere autenticación (endpoint público).

    Args:
        db: Sesión de base de datos

    Returns:
        Lista de roles disponibles

    Ejemplo:
        GET /users/roles/

        Respuesta:
        [
            {"id_rol": 1, "nombre": "Administrador"},
            {"id_rol": 2, "nombre": "Delegado"}
        ]
    """
    roles = db.query(RolModel).all()

    # Si no hay roles, crear los roles por defecto
    if not roles:
        default_roles = [
            RolModel(nombre="Administrador"),
            RolModel(nombre="Delegado")
        ]

        try:
            for rol in default_roles:
                db.add(rol)
            db.commit()
            roles = db.query(RolModel).all()
            logger.info("✅ Roles por defecto creados")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error al crear roles por defecto: {e}")

    return roles


# ========================================
# ENDPOINT DE INICIALIZACIÓN
# ========================================

@router.post("/init-admin", response_model=UsuarioSchema)
def initialize_admin(db: Session = Depends(get_db)):
    """
    Crea un usuario administrador inicial si no existe ninguno.

    Útil para la primera configuración del sistema.

    Credenciales por defecto:
    - Email: admin@torneo.com
    - Password: admin123

    ⚠️ CAMBIAR LA CONTRASEÑA INMEDIATAMENTE EN PRODUCCIÓN

    Args:
        db: Sesión de base de datos

    Returns:
        Usuario administrador creado

    Raises:
        HTTPException 400: Si ya existe un administrador

    Ejemplo:
        POST /users/init-admin
    """
    # Verificar si existe algún administrador
    admin_rol = db.query(RolModel).filter(RolModel.nombre == "Administrador").first()

    if not admin_rol:
        # Crear roles si no existen
        get_all_roles(db)
        admin_rol = db.query(RolModel).filter(RolModel.nombre == "Administrador").first()

    existing_admin = db.query(UsuarioModel).filter(
        UsuarioModel.id_rol == admin_rol.id_rol
    ).first()

    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un administrador en el sistema"
        )

    # Crear admin por defecto
    admin_user = UsuarioModel(
        nombre_usuario="Administrador",
        email="admin@torneo.com",
        password_hash=get_password_hash("admin123"),
        id_rol=admin_rol.id_rol
    )

    try:
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        logger.info("✅ Administrador inicial creado: admin@torneo.com")
        logger.warning("⚠️ CAMBIAR CONTRASEÑA POR DEFECTO")
        return admin_user
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al crear administrador inicial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear administrador inicial"
        )