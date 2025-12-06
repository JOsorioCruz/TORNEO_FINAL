-- Tabla para los roles de usuario: Administrador, Delegado, Público
CREATE TABLE Rol (
    id_rol INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

-- Tabla de usuarios (Administrador, Delegado)
-- Solo los usuarios autenticados (Admin y Delegado) necesitan registro.
CREATE TABLE Usuario (
    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
    nombre_usuario VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- Para el RF-1.1: Autenticación
    id_rol INT NOT NULL,
    FOREIGN KEY (id_rol) REFERENCES Rol(id_rol)
);

-- Tabla de equipos (RF-2.1)
CREATE TABLE Equipo (
    id_equipo INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_delegado INT, -- El Delegado es el usuario que creó y gestiona el equipo (RF-1.2, RF-2.1)
    FOREIGN KEY (id_delegado) REFERENCES Usuario(id_usuario)
);

-- Tabla para almacenar los tipos de jugador (Habitante, Extranjero, etc.) (RF-2.4)
CREATE TABLE Tipo_Jugador (
    id_tipo_jugador INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Tabla de jugadores (RF-2.2)
CREATE TABLE Jugador (
    id_jugador INT PRIMARY KEY AUTO_INCREMENT,
    cedula VARCHAR(20) UNIQUE NOT NULL, -- Campo obligatorio (RF-2.3)
    nombre_completo VARCHAR(150) NOT NULL,
    fecha_nacimiento DATE NOT NULL, -- Campo obligatorio (RF-2.3)
    numero_camiseta INT, -- (RF-2.9)
    foto_url VARCHAR(255), -- Foto reciente (RF-2.3)
    documento_probatorio_url VARCHAR(255), -- Carga de documentos (RF-2.5)
    estado_validacion ENUM('Pendiente', 'Validado', 'Rechazado') NOT NULL DEFAULT 'Pendiente', -- (RF-2.6)
    fecha_validacion DATETIME,
    id_equipo INT NOT NULL,
    id_tipo_jugador INT NOT NULL, -- Campo obligatorio (RF-2.3)
    FOREIGN KEY (id_equipo) REFERENCES Equipo(id_equipo),
    FOREIGN KEY (id_tipo_jugador) REFERENCES Tipo_Jugador(id_tipo_jugador)
    -- Se añade un índice único para (id_equipo, numero_camiseta) para (RF-2.9)
    -- y se aplicarán restricciones de máx. 16 jugadores por equipo (RF-2.2) en el código.
);

-- Módulo 5: Gestión del Torneo (RF-5.1)
CREATE TABLE Torneo (
    id_torneo INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    fecha_inicio DATE,
    fecha_fin DATE,
    esta_activo BOOLEAN DEFAULT TRUE
);

-- Tabla para los posibles formatos de fase (RF-5.3)
CREATE TABLE Formato_Fase (
    id_formato INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL UNIQUE -- Liga, Grupos, Eliminacion Directa
);

-- Tabla de fases del torneo (RF-5.2)
CREATE TABLE Fase (
    id_fase INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    orden INT NOT NULL,
    bonificacion_aplicada BOOLEAN DEFAULT FALSE, -- (RF-5.8)
    reglas_clasificacion TEXT, -- (RF-5.5)
    id_torneo INT NOT NULL,
    id_formato INT NOT NULL,
    FOREIGN KEY (id_torneo) REFERENCES Torneo(id_torneo),
    FOREIGN KEY (id_formato) REFERENCES Formato_Fase(id_formato)
);

-- Tabla para manejar la asignación de equipos a una fase (RF-5.4)
CREATE TABLE Fase_Equipo (
    id_fase_equipo INT PRIMARY KEY AUTO_INCREMENT,
    id_fase INT NOT NULL,
    id_equipo INT NOT NULL,
    nombre_grupo VARCHAR(50), -- Para formato 'Grupos' (RF-5.5)
    es_cabeza_serie BOOLEAN DEFAULT FALSE, -- (RF-5.5)
    FOREIGN KEY (id_fase) REFERENCES Fase(id_fase),
    FOREIGN KEY (id_equipo) REFERENCES Equipo(id_equipo),
    UNIQUE (id_fase, id_equipo)
);

-- Tabla para el calendario de partidos (Generado en Módulo 5, visible en Módulo 8) (RF-5.7, RF-8.2)
-- El registro de marcadores (Módulo 4) está fuera de alcance, pero la tabla es necesaria para el calendario.
CREATE TABLE Partido (
    id_partido INT PRIMARY KEY AUTO_INCREMENT,
    fecha_hora DATETIME NOT NULL,
    lugar VARCHAR(100),
    id_fase INT NOT NULL,
    id_equipo_local INT,
    id_equipo_visitante INT,
    FOREIGN KEY (id_fase) REFERENCES Fase(id_fase),
    FOREIGN KEY (id_equipo_local) REFERENCES Equipo(id_equipo),
    FOREIGN KEY (id_equipo_visitante) REFERENCES Equipo(id_equipo)
);