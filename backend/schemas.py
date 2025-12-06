from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


# --- Módulo 1: Gestión de Usuarios y Roles ---

class RolBase(BaseModel):
    nombre: str


class RolCreate(RolBase):
    pass


class Rol(RolBase):
    id_rol: int

    model_config = ConfigDict(from_attributes=True)


class UsuarioBase(BaseModel):
    nombre_usuario: str
    email: EmailStr
    id_rol: int


class UsuarioCreate(UsuarioBase):
    password: str


class Usuario(UsuarioBase):
    id_usuario: int
    rol: Rol

    model_config = ConfigDict(from_attributes=True)


# --- Esquemas de Tokens (para la autenticación, RF-1.1) ---

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# --- Módulo 2: Gestión de Equipos y Jugadores ---

class TipoJugadorSchema(BaseModel):
    id_tipo_jugador: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class EquipoBase(BaseModel):
    nombre: str


class EquipoCreate(EquipoBase):
    pass


class Equipo(EquipoBase):
    id_equipo: int
    id_delegado: int
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)


class JugadorCreate(BaseModel):
    cedula: str
    nombre_completo: str
    fecha_nacimiento: date
    id_tipo_jugador: int
    numero_camiseta: Optional[int] = None


class JugadorValidation(BaseModel):
    estado_validacion: str  # 'Validado' o 'Rechazado'


class Jugador(BaseModel):
    id_jugador: int
    cedula: str
    nombre_completo: str
    fecha_nacimiento: date
    numero_camiseta: Optional[int] = None
    foto_url: Optional[str] = None
    documento_probatorio_url: Optional[str] = None
    estado_validacion: str
    fecha_validacion: Optional[datetime] = None
    id_equipo: int
    id_tipo_jugador: int
    tipo_jugador: TipoJugadorSchema

    model_config = ConfigDict(from_attributes=True)


# --- Módulo 5: Gestión del Torneo (Flexible) ---

class TorneoBase(BaseModel):
    nombre: str
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None


class TorneoCreate(TorneoBase):
    pass


class Torneo(TorneoBase):
    id_torneo: int
    esta_activo: bool

    model_config = ConfigDict(from_attributes=True)


class FormatoFaseSchema(BaseModel):
    id_formato: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class FaseBase(BaseModel):
    nombre: str
    orden: int
    id_formato: int


class FaseCreate(FaseBase):
    pass


class Fase(FaseBase):
    id_fase: int
    id_torneo: int
    bonificacion_aplicada: bool
    reglas_clasificacion: Optional[str] = None
    formato: FormatoFaseSchema

    model_config = ConfigDict(from_attributes=True)


class FaseEquipoCreate(BaseModel):
    id_equipo: int
    nombre_grupo: Optional[str] = None
    es_cabeza_serie: Optional[bool] = False


# --- Módulo 8: Vista Pública ---

class JugadorPublico(BaseModel):
    nombre_completo: str
    numero_camiseta: Optional[int] = None
    cedula: str
    estado_validacion: str

    model_config = ConfigDict(from_attributes=True)


class EquipoPlantilla(BaseModel):
    id_equipo: int
    nombre: str
    delegado_email: str
    jugadores_validados: List[JugadorPublico]

    model_config = ConfigDict(from_attributes=True)


class PartidoPublico(BaseModel):
    id_partido: int
    fecha_hora: datetime
    lugar: Optional[str] = None
    fase_nombre: str
    equipo_local_nombre: Optional[str] = None
    equipo_visitante_nombre: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FaseVistaPublica(BaseModel):
    id_fase: int
    nombre: str
    formato: str
    tablas_posiciones: List[dict] = []
    llaves: List[dict] = []

    model_config = ConfigDict(from_attributes=True)