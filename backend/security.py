"""
security.py - Sistema de Seguridad CORREGIDO v2
================================================

CORRECCIONES APLICADAS:
- JWT real con python-jose
- Bcrypt con validación de longitud
- Compatibilidad con hashes antiguos
- Manejo de errores robusto

VERSIÓN: 2.0
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Usuario as UsuarioModel
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

# Importaciones para seguridad REAL
from passlib.context import CryptContext
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

# ========================================
# CONFIGURACIÓN
# ========================================

# Configuración de hashing bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración JWT
SECRET_KEY = os.getenv("SECRET_KEY", "CAMBIAR_EN_PRODUCCION_usar_openssl_rand_hex_32")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Advertencia si se usa clave por defecto
if SECRET_KEY == "CAMBIAR_EN_PRODUCCION_usar_openssl_rand_hex_32":
    logger.warning("⚠️ ADVERTENCIA: Usando SECRET_KEY por defecto. ¡CAMBIAR EN PRODUCCIÓN!")

# Configuración de seguridad HTTP Bearer
security = HTTPBearer()


# ========================================
# FUNCIONES DE HASHING DE CONTRASEÑAS
# ========================================

def get_password_hash(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt.

    LÍMITE: bcrypt solo acepta contraseñas de máximo 72 bytes.

    Args:
        password: Contraseña en texto plano

    Returns:
        Hash bcrypt de la contraseña

    Raises:
        ValueError: Si la contraseña es muy larga (>72 bytes)

    Ejemplo:
        >>> hashed = get_password_hash("mi_contraseña_segura")
        >>> print(hashed)
        $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWUIqW9LQQS
    """
    # ✅ VALIDACIÓN CRÍTICA: bcrypt tiene límite de 72 bytes
    password_bytes = password.encode('utf-8')

    if len(password_bytes) > 72:
        raise ValueError(
            f"La contraseña es muy larga ({len(password_bytes)} bytes). "
            f"Máximo permitido: 72 bytes. "
            f"Por favor, use una contraseña más corta."
        )

    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Error al hashear contraseña: {e}")
        raise ValueError(f"Error al procesar contraseña: {str(e)}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña coincide con su hash.
    Incluye compatibilidad con hashes antiguos del sistema placeholder.

    Args:
        plain_password: Contraseña en texto plano a verificar
        hashed_password: Hash bcrypt almacenado

    Returns:
        True si coinciden, False si no

    Ejemplo:
        >>> is_valid = verify_password("mi_contraseña", hashed)
        >>> print(is_valid)
        True
    """
    # ✅ COMPATIBILIDAD: Detectar y manejar hashes antiguos (placeholder)
    if hashed_password.startswith("hashed_"):
        logger.warning(
            "⚠️ Usuario usando hash antiguo (placeholder). "
            "IMPORTANTE: Cambiar contraseña inmediatamente."
        )
        # Sistema antiguo: "hashed_" + password
        expected_old_hash = "hashed_" + plain_password
        return hashed_password == expected_old_hash

    # ✅ Sistema nuevo: bcrypt
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError as e:
        # Error de formato de hash
        logger.error(f"Error de formato de hash: {e}")
        return False
    except Exception as e:
        logger.error(f"Error al verificar contraseña: {e}")
        return False


# ========================================
# FUNCIONES DE JWT
# ========================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT firmado.

    Args:
        data: Datos a incluir en el payload del token
        expires_delta: Tiempo de expiración (opcional)

    Returns:
        Token JWT firmado

    Ejemplo:
        >>> token = create_access_token({"sub": "user@example.com", "user_id": 1})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error al crear token: {e}")
        raise ValueError("Error al generar token de autenticación")


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodifica y verifica un token JWT.

    Args:
        token: Token JWT a decodificar

    Returns:
        Payload del token si es válido, None si no es válido

    Ejemplo:
        >>> payload = decode_access_token(token)
        >>> print(payload)
        {'sub': 'user@example.com', 'user_id': 1, 'exp': 1234567890}
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"Error al decodificar token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado al decodificar token: {e}")
        return None


# ========================================
# AUTENTICACIÓN DE USUARIOS
# ========================================

def authenticate_user(db: Session, email: str, password: str) -> Optional[UsuarioModel]:
    """
    Autentica un usuario verificando email y contraseña.

    Args:
        db: Sesión de base de datos
        email: Email del usuario
        password: Contraseña en texto plano

    Returns:
        Usuario autenticado o None si las credenciales son inválidas

    Ejemplo:
        >>> user = authenticate_user(db, "admin@torneo.com", "admin123")
        >>> print(user.nombre_usuario if user else "Credenciales inválidas")
        Administrador
    """
    try:
        user = db.query(UsuarioModel).filter(UsuarioModel.email == email).first()

        if not user:
            logger.info(f"Intento de login - usuario no encontrado: {email}")
            return None

        if not verify_password(password, user.password_hash):
            logger.info(f"Intento de login - contraseña incorrecta: {email}")
            return None

        return user

    except Exception as e:
        logger.error(f"Error en autenticación: {e}")
        return None


# ========================================
# DEPENDENCIAS DE AUTENTICACIÓN
# ========================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UsuarioModel:
    """
    Dependencia que extrae y valida el usuario actual desde el token Bearer.

    Uso:
        @router.get("/perfil")
        def get_profile(current_user: UsuarioModel = Depends(get_current_user)):
            return {"usuario": current_user.nombre_usuario}

    Args:
        credentials: Credenciales HTTP Bearer
        db: Sesión de base de datos

    Returns:
        Usuario autenticado

    Raises:
        HTTPException 401: Si el token es inválido o el usuario no existe
    """
    token = credentials.credentials

    # Decodificar el token
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[int] = payload.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: falta user_id",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Buscar el usuario en la base de datos
    user = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_user_id(current_user: UsuarioModel = Depends(get_current_user)) -> int:
    """
    Obtiene solo el ID del usuario actual.

    Uso:
        @router.get("/mis-equipos")
        def get_my_teams(user_id: int = Depends(get_current_user_id)):
            return db.query(Equipo).filter(Equipo.id_delegado == user_id).all()

    Args:
        current_user: Usuario actual

    Returns:
        ID del usuario autenticado
    """
    return current_user.id_usuario


def get_current_admin(current_user: UsuarioModel = Depends(get_current_user)) -> UsuarioModel:
    """
    Verifica que el usuario actual sea un Administrador.

    Uso:
        @router.post("/admin/torneos")
        def create_tournament(
            torneo: TorneoCreate,
            admin: UsuarioModel = Depends(get_current_admin)
        ):
            # Solo admins pueden ejecutar esto
            return create_tournament_logic(torneo)

    Args:
        current_user: Usuario autenticado

    Returns:
        Usuario si es administrador

    Raises:
        HTTPException 403: Si el usuario no es administrador
    """
    if current_user.rol.nombre != "Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado. Se requiere rol de Administrador."
        )
    return current_user


def get_current_admin_id(admin: UsuarioModel = Depends(get_current_admin)) -> int:
    """
    Obtiene el ID del administrador actual.

    Uso:
        @router.patch("/torneos/{id}/activar")
        def activate_tournament(id: int, admin_id: int = Depends(get_current_admin_id)):
            # Solo admins, retorna su ID
            return activate_tournament_logic(id, admin_id)

    Args:
        admin: Usuario administrador

    Returns:
        ID del administrador
    """
    return admin.id_usuario


def is_admin(admin_id: int = Depends(get_current_admin_id)) -> int:
    """
    Dependencia simplificada para verificar que el usuario es Admin.

    Uso:
        @router.delete("/equipos/{id}")
        def delete_team(id: int, admin_id: int = Depends(is_admin)):
            # Automáticamente verifica que es admin
            return delete_team_logic(id)

    Args:
        admin_id: ID del administrador (obtenido de get_current_admin_id)

    Returns:
        ID del administrador
    """
    return admin_id


# ========================================
# DEPENDENCIAS DE ROL DELEGADO
# ========================================

def get_current_delegado(current_user: UsuarioModel = Depends(get_current_user)) -> UsuarioModel:
    """
    Verifica que el usuario actual sea un Delegado.

    Uso:
        @router.post("/equipos")
        def create_team(
            team: EquipoCreate,
            delegado: UsuarioModel = Depends(get_current_delegado)
        ):
            # Solo delegados pueden crear equipos
            return create_team_logic(team, delegado.id_usuario)

    Args:
        current_user: Usuario autenticado

    Returns:
        Usuario si es delegado

    Raises:
        HTTPException 403: Si el usuario no es delegado
    """
    if current_user.rol.nombre not in ["Delegado", "Administrador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado. Se requiere rol de Delegado o Administrador."
        )
    return current_user


def get_current_delegado_id(delegado: UsuarioModel = Depends(get_current_delegado)) -> int:
    """
    Obtiene el ID del delegado actual.

    Args:
        delegado: Usuario delegado

    Returns:
        ID del delegado
    """
    return delegado.id_usuario


# ========================================
# UTILIDADES
# ========================================

def verify_team_ownership(team_id: int, user_id: int, db: Session) -> bool:
    """
    Verifica si un usuario es el delegado de un equipo.

    Args:
        team_id: ID del equipo
        user_id: ID del usuario
        db: Sesión de base de datos

    Returns:
        True si el usuario es delegado del equipo, False si no
    """
    from models import Equipo

    team = db.query(Equipo).filter(Equipo.id_equipo == team_id).first()

    if not team:
        return False

    return team.id_delegado == user_id


def require_team_ownership(team_id: int, current_user: UsuarioModel, db: Session):
    """
    Verifica que el usuario sea delegado del equipo o lanza excepción.

    Args:
        team_id: ID del equipo
        current_user: Usuario actual
        db: Sesión de base de datos

    Raises:
        HTTPException 403: Si el usuario no es delegado del equipo
        HTTPException 404: Si el equipo no existe
    """
    from models import Equipo

    team = db.query(Equipo).filter(Equipo.id_equipo == team_id).first()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipo no encontrado"
        )

    # Admins pueden modificar cualquier equipo
    if current_user.rol.nombre == "Administrador":
        return

    if team.id_delegado != current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar este equipo"
        )


# ========================================
# FUNCIONES AUXILIARES PARA GENERACIÓN
# ========================================

def generate_secret_key() -> str:
    """
    Genera una clave secreta segura para JWT.

    Returns:
        Clave secreta hexadecimal de 32 bytes

    Ejemplo:
        >>> key = generate_secret_key()
        >>> print(key)
        09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
    """
    import secrets
    return secrets.token_hex(32)


if __name__ == "__main__":
    # Ejemplo de uso para generar SECRET_KEY
    print("=== GENERADOR DE SECRET_KEY ===")
    print(f"SECRET_KEY={generate_secret_key()}")
    print("\n⚠️ Copiar esta clave al archivo .env")

    # Ejemplo de hashing
    print("\n=== EJEMPLO DE HASHING ===")
    password = "mi_contraseña_segura"
    try:
        hashed = get_password_hash(password)
        print(f"Password: {password}")
        print(f"Hash: {hashed}")
        print(f"Verificación: {verify_password(password, hashed)}")
    except ValueError as e:
        print(f"Error: {e}")

    # Ejemplo de JWT
    print("\n=== EJEMPLO DE JWT ===")
    token_data = {"sub": "admin@torneo.com", "user_id": 1}
    token = create_access_token(token_data)
    print(f"Token: {token[:50]}...")
    decoded = decode_access_token(token)
    print(f"Decodificado: {decoded}")