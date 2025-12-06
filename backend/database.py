import os
import logging
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import pymysql

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ========================================
# 1. VALIDACIÓN DE VARIABLES DE ENTORNO
# ========================================

class DatabaseSettings(BaseSettings):
    """Configuración de base de datos con validación"""
    DB_USER: str = Field(..., description="Usuario de la base de datos")
    DB_PASSWORD: str = Field(..., description="Contraseña de la base de datos")
    DB_HOST: str = Field(default="localhost", description="Host de la base de datos")
    DB_PORT: int = Field(default=3306, ge=1, le=65535, description="Puerto de MySQL")
    DB_NAME: str = Field(..., description="Nombre de la base de datos")

    @field_validator('DB_NAME')
    @classmethod
    def validate_db_name(cls, v):
        """Valida que el nombre de BD no contenga caracteres peligrosos"""
        if not v.replace('_', '').isalnum():
            raise ValueError("El nombre de la base de datos solo puede contener letras, números y guiones bajos")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


# Cargar y validar configuración
try:
    load_dotenv()
    settings = DatabaseSettings()
except Exception as e:
    logger.error(f"Error al cargar configuración de base de datos: {e}")
    raise RuntimeError(
        "No se pudo cargar la configuración de la base de datos. "
        "Verifique que el archivo .env existe y contiene todas las variables requeridas: "
        "DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME"
    ) from e

# ========================================
# 2. CONSTRUCCIÓN DE URLs DE CONEXIÓN
# ========================================

# URL base para conexión sin base de datos específica (solo al servidor)
SQLALCHEMY_SERVER_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}"
)

# URL de conexión al esquema de la base de datos
SQLALCHEMY_DATABASE_URL = f"{SQLALCHEMY_SERVER_URL}/{settings.DB_NAME}"

logger.info(f"Configurando conexión a base de datos: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

# ========================================
# 3. CONFIGURACIÓN DEL ORM
# ========================================

try:
    # Engine con configuración de pool para producción
    Engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,  # Verifica conexiones antes de usarlas
        pool_recycle=3600,  # Recicla conexiones cada hora
        pool_size=5,  # Tamaño del pool de conexiones
        max_overflow=10,  # Máximo de conexiones adicionales
        echo=False  # Cambiar a True para debug de queries
    )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)
    Base = declarative_base()

    logger.info("Motor de base de datos configurado correctamente")

except Exception as e:
    logger.error(f"Error al configurar el motor de base de datos: {e}")
    raise RuntimeError("No se pudo configurar el motor de base de datos") from e


# ========================================
# 4. FUNCIÓN DE AUTOGESTIÓN Y CREACIÓN
# ========================================

def create_database_and_tables() -> None:
    """
    Intenta crear la base de datos si no existe y luego crea todas las tablas.
    Esto permite la autogestión de la base de datos.

    Raises:
        RuntimeError: Si no se puede conectar al servidor o crear la BD
    """
    server_engine = None
    final_engine = None

    try:
        logger.info("Intentando conectar al servidor MySQL...")

        # Crear engine temporal para conectar al servidor (sin BD específica)
        server_engine = create_engine(
            SQLALCHEMY_SERVER_URL,
            pool_pre_ping=True,
            isolation_level="AUTOCOMMIT"  # Necesario para DDL
        )

        with server_engine.connect() as connection:
            # Verificar si la base de datos existe
            logger.info(f"Verificando existencia de base de datos '{settings.DB_NAME}'...")

            result = connection.execute(
                text(
                    "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
                    "WHERE SCHEMA_NAME = :db_name"
                ),
                {"db_name": settings.DB_NAME}
            ).fetchone()

            # Si no existe, crearla
            if not result:
                logger.warning(f"La base de datos '{settings.DB_NAME}' no existe. Creándola...")

                connection.execute(
                    text(f"CREATE DATABASE `{settings.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                )

                logger.info(f"✅ Base de datos '{settings.DB_NAME}' creada exitosamente")
            else:
                logger.info(f"✅ La base de datos '{settings.DB_NAME}' ya existe")

        # Cerrar conexión temporal al servidor
        server_engine.dispose()

        # Conectar al motor de la BD específica para crear tablas
        logger.info("Creando/verificando tablas en la base de datos...")

        final_engine = create_engine(SQLALCHEMY_DATABASE_URL)

        # Crear todas las tablas definidas en los modelos
        Base.metadata.create_all(bind=final_engine)

        logger.info("✅ Tablas verificadas/creadas exitosamente")

        # Cerrar conexión
        final_engine.dispose()

    except pymysql.err.OperationalError as e:
        error_msg = (
            f"Error de conexión a MySQL: {e}\n"
            f"Verifique que:\n"
            f"  1. El servidor MySQL esté corriendo\n"
            f"  2. Las credenciales en .env sean correctas\n"
            f"  3. El host '{settings.DB_HOST}' y puerto '{settings.DB_PORT}' sean accesibles"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    except pymysql.err.ProgrammingError as e:
        error_msg = f"Error de sintaxis SQL o permisos insuficientes: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    except Exception as e:
        error_msg = f"Error inesperado al crear base de datos/tablas: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    finally:
        # Asegurar que se cierren las conexiones
        if server_engine:
            server_engine.dispose()
        if final_engine:
            final_engine.dispose()


# ========================================
# 5. INYECCIÓN DE DEPENDENCIA
# ========================================

def get_db() -> Generator[Session, None, None]:
    """
    Generador de sesiones de base de datos para inyección de dependencias.

    Uso en FastAPI:
        @router.get("/endpoint")
        def my_endpoint(db: Session = Depends(get_db)):
            # usar db aquí
            pass

    Yields:
        Session: Sesión de SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Error en transacción de base de datos: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# ========================================
# 6. UTILIDADES ADICIONALES
# ========================================

def test_database_connection() -> bool:
    """
    Prueba la conexión a la base de datos.

    Returns:
        bool: True si la conexión es exitosa, False en caso contrario
    """
    try:
        with Engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("✅ Prueba de conexión exitosa")
        return True
    except Exception as e:
        logger.error(f"❌ Fallo en prueba de conexión: {e}")
        return False


def get_database_info() -> dict:
    """
    Obtiene información sobre la base de datos.

    Returns:
        dict: Información de la base de datos
    """
    try:
        with Engine.connect() as connection:
            version = connection.execute(text("SELECT VERSION()")).scalar()
            charset = connection.execute(
                text("SELECT DEFAULT_CHARACTER_SET_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = :db_name"),
                {"db_name": settings.DB_NAME}
            ).scalar()

            return {
                "host": settings.DB_HOST,
                "port": settings.DB_PORT,
                "database": settings.DB_NAME,
                "version": version,
                "charset": charset,
                "status": "connected"
            }
    except Exception as e:
        logger.error(f"Error al obtener información de la base de datos: {e}")
        return {
            "status": "error",
            "error": str(e)
        }