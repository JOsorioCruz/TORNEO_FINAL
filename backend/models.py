from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Date, Boolean, DateTime, Text, func, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.database import Base

# -----------------------------------------------------
# MÓDULO 1: GESTIÓN DE USUARIOS Y ROLES
# -----------------------------------------------------

class Rol(Base):
    __tablename__ = 'Rol'

    id_rol = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)

    # Relaciones
    usuarios = relationship("Usuario", back_populates="rol")


class Usuario(Base):
    __tablename__ = 'Usuario'

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    id_rol = Column(Integer, ForeignKey('Rol.id_rol'), nullable=False)

    # Relaciones
    rol = relationship("Rol", back_populates="usuarios")
    equipos = relationship("Equipo", back_populates="delegado")


# -----------------------------------------------------
# MÓDULO 2: GESTIÓN DE EQUIPOS Y JUGADORES
# -----------------------------------------------------

class TipoJugador(Base):
    __tablename__ = 'Tipo_Jugador'

    id_tipo_jugador = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)

    # Relaciones
    jugadores = relationship("Jugador", back_populates="tipo_jugador")


class Equipo(Base):
    __tablename__ = 'Equipo'

    id_equipo = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    fecha_creacion = Column(DateTime, default=func.now(), nullable=False)
    id_delegado = Column(Integer, ForeignKey('Usuario.id_usuario'), nullable=False)

    # Relaciones
    delegado = relationship("Usuario", back_populates="equipos")
    jugadores = relationship("Jugador", back_populates="equipo", cascade="all, delete-orphan")
    fases_equipo = relationship("FaseEquipo", back_populates="equipo", cascade="all, delete-orphan")
    partidos_local = relationship("Partido", foreign_keys="[Partido.id_equipo_local]", back_populates="equipo_local")
    partidos_visitante = relationship("Partido", foreign_keys="[Partido.id_equipo_visitante]",
                                      back_populates="equipo_visitante")


class Jugador(Base):
    __tablename__ = 'Jugador'

    id_jugador = Column(Integer, primary_key=True, index=True)
    cedula = Column(String(20), unique=True, nullable=False, index=True)
    nombre_completo = Column(String(150), nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    numero_camiseta = Column(Integer)
    foto_url = Column(String(255))
    documento_probatorio_url = Column(String(255))
    estado_validacion = Column(
        Enum('Pendiente', 'Validado', 'Rechazado', name='estado_validacion_enum'),
        default='Pendiente',
        nullable=False
    )
    fecha_validacion = Column(DateTime)
    id_equipo = Column(Integer, ForeignKey('Equipo.id_equipo'), nullable=False)
    id_tipo_jugador = Column(Integer, ForeignKey('Tipo_Jugador.id_tipo_jugador'), nullable=False)

    # Relaciones
    equipo = relationship("Equipo", back_populates="jugadores")
    tipo_jugador = relationship("TipoJugador", back_populates="jugadores")

    # Constraint: Número de camiseta único por equipo
    __table_args__ = (
        UniqueConstraint('id_equipo', 'numero_camiseta', name='uq_equipo_camiseta'),
    )


# -----------------------------------------------------
# MÓDULO 5: GESTIÓN DEL TORNEO (ESTRUCTURA)
# -----------------------------------------------------

class Torneo(Base):
    __tablename__ = 'Torneo'

    id_torneo = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    esta_activo = Column(Boolean, default=True)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)

    # Relaciones
    fases = relationship("Fase", back_populates="torneo", cascade="all, delete-orphan")


class FormatoFase(Base):
    __tablename__ = 'Formato_Fase'

    id_formato = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)  # Liga, Grupos, Eliminacion Directa

    # Relaciones
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
    partidos = relationship("Partido", back_populates="fase", cascade="all, delete-orphan")
    fases_equipo = relationship("FaseEquipo", back_populates="fase", cascade="all, delete-orphan")

    # Constraint: Orden único por torneo
    __table_args__ = (
        UniqueConstraint('id_torneo', 'orden', name='uq_torneo_orden'),
    )


class FaseEquipo(Base):
    __tablename__ = 'Fase_Equipo'

    id_fase_equipo = Column(Integer, primary_key=True, index=True)
    id_fase = Column(Integer, ForeignKey('Fase.id_fase'), nullable=False)
    id_equipo = Column(Integer, ForeignKey('Equipo.id_equipo'), nullable=False)
    nombre_grupo = Column(String(50))
    es_cabeza_serie = Column(Boolean, default=False)

    # Relaciones
    fase = relationship("Fase", back_populates="fases_equipo")
    equipo = relationship("Equipo", back_populates="fases_equipo")

    # Constraint: Un equipo no puede estar dos veces en la misma fase
    __table_args__ = (
        UniqueConstraint('id_fase', 'id_equipo', name='uq_fase_equipo'),
    )


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
    equipo_local = relationship(
        "Equipo",
        foreign_keys=[id_equipo_local],
        back_populates="partidos_local"
    )
    equipo_visitante = relationship(
        "Equipo",
        foreign_keys=[id_equipo_visitante],
        back_populates="partidos_visitante"
    )