import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text  # Importación de 'text' es clave
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql

# 1. Cargar variables de entorno
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# URL base para conexión sin base de datos específica (solo al servidor)
SQLALCHEMY_SERVER_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
# URL de conexión al esquema de la base de datos
SQLALCHEMY_DATABASE_URL = f"{SQLALCHEMY_SERVER_URL}/{DB_NAME}"

# 2. Configuración del ORM
Engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)
Base = declarative_base()


# 3. Función de Autogestión y Creación
def create_database_and_tables():
    """
    Intenta crear la base de datos si no existe y luego crea todas las tablas.
    Esto permite la autogestión de la base de datos.
    """
    try:
        # Intenta conectar al servidor (sin especificar la BD)
        server_engine = create_engine(SQLALCHEMY_SERVER_URL)
        with server_engine.connect() as connection:

            # 🚨 CORRECCIÓN 1: Envolver la consulta SELECT en text() 🚨
            # Verifica si la base de datos existe
            result = connection.execute(
                text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{DB_NAME}'")
            ).fetchone()

            # Si no existe, la crea
            if not result:
                print(f"La base de datos '{DB_NAME}' no existe. Creándola...")

                # 🚨 CORRECCIÓN 2: Envolver el comando CREATE DATABASE en text() 🚨
                connection.execute(text(f"CREATE DATABASE {DB_NAME}"))
                # Se requiere commit para aplicar el DDL (CREATE DATABASE)
                connection.commit()
                connection.close()  # Cierra la conexión al servidor

        # Conecta al motor de la BD recién creada/existente
        final_engine = create_engine(SQLALCHEMY_DATABASE_URL)
        # Crea todas las tablas definidas en los modelos
        Base.metadata.create_all(bind=final_engine)
        print("Tablas verificadas/creadas exitosamente.")

    except Exception as e:
        print(f"Error al conectar o crear la base de datos/tablas: {e}")
        print("Asegúrese de que el servidor MySQL esté corriendo y las credenciales en .env sean correctas.")
        # Se relanza la excepción para que uvicorn falle si la conexión es imposible
        raise e


# 4. Inyección de dependencia para obtener la sesión
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
