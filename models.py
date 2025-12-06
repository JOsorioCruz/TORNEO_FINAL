from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Date, Boolean, DateTime, Text, func
from sqlalchemy.orm import relationship
from database import Base


# -----------------------------------------------------
# MÓDULO 1: GESTIÓN DE USUARIOS Y ROLES
# -----------------------------------------------------

class Rol(Base):
    __tablename__ = 'Rol'
    id_rol = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)

    usuarios = relationship("Usuario", back_populates="rol")


class Usuario(Base):
    __tablename__ = 'Usuario'
    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    id_rol = Column(Integer, ForeignKey('Rol.id_rol'), nullable=False)

    rol = relationship("Rol", back_populates="usuarios")
    equipos = relationship("Equipo", back_populates="delegado")


# -----------------------------------------------------
# MÓDULO 2: GESTIÓN DE EQUIPOS Y JUGADORES
# -----------------------------------------------------

class TipoJugador(Base):
    __tablename__ = 'Tipo_Jugador'
    id_tipo_jugador = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)


class Equipo(Base):
    __tablename__ = 'Equipo'
    id_equipo = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    fecha_creacion = Column(DateTime, default=func.now(), nullable=False)
    id_delegado = Column(Integer, ForeignKey('Usuario.id_usuario'))

    delegado = relationship("Usuario", back_populates="equipos")
    jugadores = relationship("Jugador", back_populates="equipo")
    fases_equipo = relationship("FaseEquipo", back_populates="equipo")  # Relación a las fases en que participa


class Jugador(Base):
    __tablename__ = 'Jugador'
    id_jugador = Column(Integer, primary_key=True, index=True)
    cedula = Column(String(20), unique=True, nullable=False)
    nombre_completo = Column(String(150), nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    numero_camiseta = Column(Integer)
    foto_url = Column(String(255))
    documento_probatorio_url = Column(String(255))
    estado_validacion = Column(Enum('Pendiente', 'Validado', 'Rechazado'), default='Pendiente', nullable=False)
    fecha_validacion = Column(DateTime)
    id_equipo = Column(Integer, ForeignKey('Equipo.id_equipo'), nullable=False)
    id_tipo_jugador = Column(Integer, ForeignKey('Tipo_Jugador.id_tipo_jugador'), nullable=False)

    equipo = relationship("Equipo", back_populates="jugadores")
    tipo_jugador = relationship("TipoJugador")


# -----------------------------------------------------
# MÓDULO 5: GESTIÓN DEL TORNEO (ESTRUCTURA)
# -----------------------------------------------------

class Torneo(Base):
    __tablename__ = 'Torneo'
    id_torneo = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    esta_activo = Column(Boolean, default=True)
    fases = relationship("Fase", back_populates="torneo")


class FormatoFase(Base):
    __tablename__ = 'Formato_Fase'
    id_formato = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)  # Liga, Grupos, Eliminacion Directa
    fases = relationship("Fase", back_populates="formato")


class Fase(Base):
    __tablename__ = 'Fase'
    id_fase = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    orden = Column(Integer, nullable=False)
    bonificacion_aplicada = Column(Boolean, default=False)
    reglas_clasificacion = Column(Text)
    id_torneo = Column(Integer, ForeignKey('Torneo.id_torneo'), nullable=False)
    id_formato = Column(Integer, ForeignKey('Formato_Fase.id_formato'), nullable=False)

    # Relaciones
    torneo = relationship("Torneo", back_populates="fases")
    formato = relationship("FormatoFase", back_populates="fases")
    partidos = relationship("Partido", back_populates="fase")
    fases_equipo = relationship("FaseEquipo", back_populates="fase")  # Relación a la tabla de asociación


class FaseEquipo(Base):
    __tablename__ = 'Fase_Equipo'
    id_fase_equipo = Column(Integer, primary_key=True, index=True)
    id_fase = Column(Integer, ForeignKey('Fase.id_fase'), nullable=False)
    id_equipo = Column(Integer, ForeignKey('Equipo.id_equipo'), nullable=False)
    nombre_grupo = Column(String(50))
    es_cabeza_serie = Column(Boolean, default=False)

    # Relaciones (para que la asignación de equipos funcione en M5)
    fase = relationship("Fase", back_populates="fases_equipo")
    equipo = relationship("Equipo", back_populates="fases_equipo")
    # Nota: SQLAlchemy requiere que id_fase y id_equipo sean UNIQUE juntos para evitar duplicados en la misma fase.


class Partido(Base):
    __tablename__ = 'Partido'

    id_partido = Column(Integer, primary_key=True, index=True)
    fecha_hora = Column(DateTime, nullable=False)
    lugar = Column(String(100))
    id_fase = Column(Integer, ForeignKey('Fase.id_fase'), nullable=False)
    id_equipo_local = Column(Integer, ForeignKey('Equipo.id_equipo'))
    id_equipo_visitante = Column(Integer, ForeignKey('Equipo.id_equipo'))

    # Relaciones
    fase = relationship("Fase", back_populates="partidos")
    equipo_local = relationship("Equipo", foreign_keys=[id_equipo_local])
    equipo_visitante = relationship("Equipo", foreign_keys=[id_equipo_visitante])