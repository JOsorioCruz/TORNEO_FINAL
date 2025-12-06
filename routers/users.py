from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
# 🚨 CORRECCIÓN: Renombrar ambos modelos de SQLAlchemy para evitar ambigüedad
from models import Usuario as UsuarioModel, Rol as RolModel
from schemas import UsuarioCreate, Usuario, RolCreate, Rol, Token

# Importaciones necesarias para Seguridad (se asume que están configuradas)
# from security import get_password_hash, create_access_token, authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/users", tags=["Usuarios y Roles"])


# --- Helper functions (Implementación real en módulo de seguridad) ---
def get_password_hash(password: str) -> str:
    # Placeholder: En producción, usar passlib.hash.bcrypt
    return "hashed_" + password


def create_access_token(data: dict, expires_delta=None):
    # Placeholder: En producción, usar jose/jwt
    return "fake_jwt_token"


def authenticate_user(db: Session, email: str, password: str):
    # Placeholder: En producción, verificar hash
    # Usar el modelo de SQLAlchemy renombrado
    user = db.query(UsuarioModel).filter(UsuarioModel.email == email).first()
    if not user or user.password_hash != "hashed_" + password:
        return False
    return user


# --------------------------------------------------------------------

@router.post("/roles/", response_model=Rol, status_code=status.HTTP_201_CREATED)
def create_role(rol: RolCreate, db: Session = Depends(get_db)):
    """Permite al Admin crear nuevos roles (e.g., 'Administrador', 'Delegado')."""

    # 🚨 CORRECCIÓN: Usar RolModel (el modelo de SQLAlchemy)
    db_rol = RolModel(nombre=rol.nombre)

    try:
        db.add(db_rol)
        db.commit()
        db.refresh(db_rol)
        return db_rol
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El rol ya existe o hubo un error al crear."
        )


@router.post("/", response_model=Usuario, status_code=status.HTTP_201_CREATED)
def create_user(user: UsuarioCreate, db: Session = Depends(get_db)):
    """Permite al Admin crear un nuevo usuario (e.g., un Delegado). (RF-73)"""

    hashed_password = get_password_hash(user.password)

    # 🚨 CORRECCIÓN: Usar UsuarioModel (el modelo de SQLAlchemy)
    db_user = UsuarioModel(
        nombre_usuario=user.nombre_usuario,
        email=user.email,
        password_hash=hashed_password,
        id_rol=user.id_rol
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado o el rol no existe."
        )


@router.post("/token", response_model=Token)
def login_for_access_token(db: Session = Depends(get_db), email: str = None, password: str = None):
    """Endpoint para autenticación de usuario (Inicio de Sesión - RF-1.1)."""
    user = authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Token expira en 30 minutos por defecto
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}