from datetime import date, datetime # Importar date y datetime correctamente
from typing import Optional, List
from pydantic import BaseModel, EmailStr
# No necesitas importar FormatoFase del modelo aquí a menos que lo uses para Type Hinting del objeto SQLAlchemy.
# from models import FormatoFase 

# --- Módulo 1: Gestión de Usuarios y Roles ---

class RolBase(BaseModel):
    nombre: str

class RolCreate(RolBase):
    pass

class Rol(RolBase):
    id_rol: int
    class Config:
        from_attributes = True

class UsuarioBase(BaseModel):
    nombre_usuario: str
    email: EmailStr
    id_rol: int # El Admin creará al Delegado asignándole el rol.

class UsuarioCreate(UsuarioBase):
    password: str # Se usa para el input, pero se hashea en el modelo.

class Usuario(UsuarioBase):
    id_usuario: int
    rol: Rol # Incluir el rol en la respuesta

    class Config:
        from_attributes = True

# --- Esquemas de Tokens (para la autenticación, RF-1.1) ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


# --- Módulo 2: Gestión de Equipos y Jugadores ---

class TipoJugadorSchema(BaseModel): # Renombrado para consistencia
    id_tipo_jugador: int
    nombre: str

    class Config:
        from_attributes = True

# Esquema para la creación/respuesta del Equipo
class EquipoBase(BaseModel):
    nombre: str

class EquipoCreate(EquipoBase):
    pass

class Equipo(EquipoBase):
    id_equipo: int
    id_delegado: int
    fecha_creacion: date 

    class Config:
        from_attributes = True

# Esquema para el registro de un Jugador (Input/Creación)
class JugadorCreate(BaseModel):
    cedula: str
    nombre_completo: str
    fecha_nacimiento: date
    id_tipo_jugador: int 
    numero_camiseta: Optional[int] = None 

# Esquema para la validación (Input del Administrador)
class JugadorValidation(BaseModel):
    estado_validacion: str  # 'Validado' o 'Rechazado'

# Esquema de respuesta completo del Jugador
class Jugador(BaseModel):
    id_jugador: int
    cedula: str
    nombre_completo: str
    fecha_nacimiento: date
    numero_camiseta: Optional[int]
    foto_url: Optional[str]
    documento_probatorio_url: Optional[str]
    estado_validacion: str
    id_equipo: int
    tipo_jugador: TipoJugadorSchema # Usar el esquema de Pydantic

    class Config:
        from_attributes = True


# --- Módulo 5: Gestión del Torneo (Flexible) ---

# Esquemas de Torneo (RF-5.1)
class TorneoBase(BaseModel):
    nombre: str
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None

class TorneoCreate(TorneoBase):
    pass

class Torneo(TorneoBase):
    id_torneo: int
    esta_activo: bool

    class Config:
        from_attributes = True

# Esquemas de Formato de Fase (Liga, Grupos, Eliminación)
class FormatoFaseSchema(BaseModel): # Nombre claro para el esquema de Pydantic
    id_formato: int
    nombre: str

    class Config:
        from_attributes = True

# Esquemas de Fase (RF-5.2)
class FaseBase(BaseModel):
    nombre: str
    orden: int
    id_formato: int  # Liga(1), Grupos(2), Eliminación Directa(3)

class FaseCreate(FaseBase):
    pass

class Fase(FaseBase): # CORRECCIÓN: Usa FormatoFaseSchema
    id_fase: int
    id_torneo: int
    bonificacion_aplicada: bool  # RF-5.8
    reglas_clasificacion: Optional[str] = None  # RF-5.5
    formato: FormatoFaseSchema # Usa el esquema de Pydantic para la serialización

    class Config:
        from_attributes = True

# Esquema para asignar equipos a una Fase (RF-5.4, RF-5.5)
class FaseEquipoCreate(BaseModel):
    id_equipo: int
    nombre_grupo: Optional[str] = None  # Si el formato es 'Grupos'
    es_cabeza_serie: Optional[bool] = False  # RF-5.5


# --- Módulo 8: Vista Pública ---

# Esquema simplificado del Jugador para Vista Pública (solo Validados)
class JugadorPublico(BaseModel):
    nombre_completo: str
    numero_camiseta: Optional[int]
    cedula: str
    estado_validacion: str

    class Config:
        from_attributes = True


# Esquema del Equipo con su Plantilla Validada para Vista Pública (RF-8.1)
class EquipoPlantilla(BaseModel):
    id_equipo: int
    nombre: str
    delegado_email: str
    jugadores_validados: List[JugadorPublico]

    class Config:
        from_attributes = True


# Esquema del Partido para el Calendario Público (RF-8.2)
class PartidoPublico(BaseModel):
    id_partido: int
    fecha_hora: datetime
    lugar: Optional[str]
    fase_nombre: str
    equipo_local_nombre: Optional[str]
    equipo_visitante_nombre: Optional[str]

    class Config:
        from_attributes = True


# Esquemas de Fases/Llaves (RF-8.3, RF-8.4)
class FaseVistaPublica(BaseModel):
    id_fase: int
    nombre: str
    formato: str  # Ej. Liga, Grupos, Eliminacion Directa

    # Para Tablas de Posiciones (RF-8.3)
    tablas_posiciones: List[dict]

    # Para Llaves de Eliminación (RF-8.4)
    llaves: List[dict]

    class Config:
        from_attributes = True