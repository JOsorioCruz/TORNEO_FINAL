# 📚 Documentación Backend - Torneo de Microfútbol

**Proyecto:** Sistema de Gestión de Torneo de Microfútbol  
**Versión:** 1.0.0  
**Framework:** FastAPI  
**Base de Datos:** MySQL  
**Fecha:** Diciembre 2025

---

## 📋 Tabla de Contenidos

1. [Tecnologías Utilizadas](#tecnologías-utilizadas)
2. [Requisitos Previos](#requisitos-previos)
3. [Instalación en Windows](#instalación-en-windows)
4. [Instalación en macOS](#instalación-en-macos)
5. [Configuración](#configuración)
6. [Ejecución](#ejecución)
7. [Documentación API (Swagger)](#documentación-api-swagger)
8. [Estructura del Proyecto](#estructura-del-proyecto)
9. [Endpoints Principales](#endpoints-principales)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)

---

## 🛠️ Tecnologías Utilizadas

### **Backend Framework**
- **FastAPI** `0.104.1` - Framework web moderno y de alto rendimiento
- **Uvicorn** `0.24.0` - Servidor ASGI para Python

### **Base de Datos**
- **MySQL** `8.0+` - Sistema de gestión de base de datos
- **SQLAlchemy** `2.0.23` - ORM (Object-Relational Mapping)
- **PyMySQL** `1.1.0` - Conector MySQL para Python

### **Seguridad**
- **python-jose[cryptography]** `3.3.0` - JWT (JSON Web Tokens)
- **passlib[bcrypt]** `1.7.4` - Hashing de contraseñas con bcrypt
- **bcrypt** `4.0.1` - Algoritmo de hash criptográfico

### **Validación de Datos**
- **Pydantic** `2.5.0` - Validación de datos con type hints
- **pydantic-settings** `2.1.0` - Gestión de configuración

### **Utilidades**
- **python-dotenv** `1.0.0` - Gestión de variables de entorno
- **python-multipart** `0.0.6` - Manejo de archivos multipart

### **Desarrollo y Testing**
- **pytest** `7.4.3` - Framework de testing
- **pytest-cov** `4.1.0` - Cobertura de tests
- **pytest-asyncio** `0.21.1` - Testing asíncrono
- **black** `23.11.0` - Formateador de código
- **flake8** `6.1.0` - Linter de código
- **mypy** `1.7.1` - Type checker estático

---

## ⚙️ Requisitos Previos

### **Software Necesario**

#### Windows:
- **Python** 3.9 o superior ([Descargar](https://www.python.org/downloads/))
- **MySQL** 8.0 o superior ([Descargar](https://dev.mysql.com/downloads/installer/))
- **Git** ([Descargar](https://git-scm.com/download/win))
- **Visual Studio Code** (Recomendado) ([Descargar](https://code.visualstudio.com/))

#### macOS:
- **Python** 3.9 o superior (incluido o via Homebrew)
- **MySQL** 8.0 o superior (via Homebrew o DMG)
- **Git** (incluido en Xcode Command Line Tools)
- **Visual Studio Code** (Recomendado)

### **Verificar Instalaciones**

```bash
# Python
python --version  # o python3 --version

# MySQL
mysql --version

# Git
git --version
```

---

## 💻 Instalación en Windows

### **Paso 1: Clonar el Repositorio**

```powershell
# Abrir PowerShell o CMD
cd C:\Users\TuUsuario\Documents

# Clonar repositorio (o descomprimir ZIP)
git clone <url-del-repositorio>
cd parcial_desarrollo_web
```

### **Paso 2: Crear Entorno Virtual**

```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\activate

# Verificar activación (debería aparecer (venv) en el prompt)
```

### **Paso 3: Instalar Dependencias**

```powershell
# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
pip list
```

### **Paso 4: Configurar MySQL**

```powershell
# Iniciar MySQL (si no está corriendo)
net start MySQL80

# Conectar a MySQL
mysql -u root -p

# Crear base de datos (opcional, la app la crea automáticamente)
CREATE DATABASE examen_final_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### **Paso 5: Configurar Variables de Entorno**

```powershell
# Crear archivo .env en la raíz del proyecto
notepad .env
```

Copiar el siguiente contenido:

```env
# Configuración de Base de Datos
DB_USER=root
DB_PASSWORD=tu_password_mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=examen_final_db

# Configuración de Seguridad
SECRET_KEY=tu_clave_secreta_generada_con_openssl
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configuración de Archivos
UPLOAD_DIR=uploads
MAX_IMAGE_SIZE=5242880
MAX_DOC_SIZE=10485760
```

### **Paso 6: Generar SECRET_KEY**

```powershell
# Opción 1: Con Python
python -c "import secrets; print(f'SECRET_KEY={secrets.token_hex(32)}')"

# Copiar el resultado y pegarlo en .env
```

### **Paso 7: Ejecutar la Aplicación**

```powershell
# Iniciar servidor
uvicorn main:app --reload

# La aplicación estará disponible en:
# http://127.0.0.1:8000
```

---

## 🍎 Instalación en macOS

### **Paso 1: Instalar Homebrew (si no está instalado)**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### **Paso 2: Instalar Dependencias del Sistema**

```bash
# Instalar Python (si no está instalado)
brew install python@3.12

# Instalar MySQL
brew install mysql

# Iniciar MySQL
brew services start mysql

# Configurar MySQL (primera vez)
mysql_secure_installation
```

### **Paso 3: Clonar el Repositorio**

```bash
# Navegar a tu directorio de proyectos
cd ~/Documents

# Clonar repositorio
git clone <url-del-repositorio>
cd parcial_desarrollo_web
```

### **Paso 4: Crear Entorno Virtual**

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Verificar activación (debería aparecer (venv) en el prompt)
```

### **Paso 5: Instalar Dependencias**

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
pip list
```

### **Paso 6: Configurar MySQL**

```bash
# Conectar a MySQL
mysql -u root -p

# Crear base de datos (opcional)
CREATE DATABASE examen_final_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### **Paso 7: Configurar Variables de Entorno**

```bash
# Crear archivo .env
touch .env
nano .env  # o usar: code .env
```

Copiar el siguiente contenido:

```env
# Configuración de Base de Datos
DB_USER=root
DB_PASSWORD=tu_password_mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=examen_final_db

# Configuración de Seguridad
SECRET_KEY=tu_clave_secreta_generada
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configuración de Archivos
UPLOAD_DIR=uploads
MAX_IMAGE_SIZE=5242880
MAX_DOC_SIZE=10485760
```

### **Paso 8: Generar SECRET_KEY**

```bash
# Con OpenSSL (recomendado)
openssl rand -hex 32

# O con Python
python3 -c "import secrets; print(secrets.token_hex(32))"

# Copiar el resultado y agregarlo al .env como SECRET_KEY=...
```

### **Paso 9: Ejecutar la Aplicación**

```bash
# Iniciar servidor
uvicorn main:app --reload

# La aplicación estará disponible en:
# http://127.0.0.1:8000
```

---

## ⚙️ Configuración

### **Variables de Entorno (.env)**

```env
# ==========================================
# CONFIGURACIÓN DE BASE DE DATOS
# ==========================================
DB_USER=root                    # Usuario de MySQL
DB_PASSWORD=password            # Contraseña de MySQL
DB_HOST=127.0.0.1              # Host (localhost)
DB_PORT=3306                   # Puerto de MySQL
DB_NAME=examen_final_db        # Nombre de la base de datos

# ==========================================
# CONFIGURACIÓN DE SEGURIDAD
# ==========================================
SECRET_KEY=clave_muy_larga_y_secreta_generada_con_openssl_rand_hex_32
ALGORITHM=HS256                # Algoritmo JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30 # Expiración de tokens (minutos)

# ==========================================
# CONFIGURACIÓN DE ARCHIVOS
# ==========================================
UPLOAD_DIR=uploads             # Directorio para archivos subidos
MAX_IMAGE_SIZE=5242880        # 5MB en bytes
MAX_DOC_SIZE=10485760         # 10MB en bytes
```

### **Configuración de la Base de Datos**

La aplicación creará automáticamente:
- ✅ La base de datos (si no existe)
- ✅ Todas las tablas necesarias
- ✅ Las relaciones entre tablas

### **Primer Inicio**

```bash
# 1. Crear administrador inicial
curl -X POST http://localhost:8000/users/init-admin

# 2. Login
curl -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@torneo.com","password":"admin123"}'

# 3. Cambiar contraseña del admin (IMPORTANTE)
curl -X PATCH http://localhost:8000/users/me \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"password":"nueva_contraseña_segura"}'
```

---

## 🚀 Ejecución

### **Modo Desarrollo**

```bash
# Activar entorno virtual
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Ejecutar con auto-reload
uvicorn main:app --reload

# Opciones adicionales:
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level info
```

### **Modo Producción**

```bash
# Sin auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### **Con Gunicorn (Producción)**

```bash
# Instalar gunicorn
pip install gunicorn

# Ejecutar
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 📖 Documentación API (Swagger)

### **URLs de Documentación**

Una vez iniciado el servidor, acceder a:

#### **Swagger UI (Interactiva)**
```
http://127.0.0.1:8000/docs
```
- Interfaz interactiva
- Probar endpoints directamente
- Ver schemas de request/response
- Autenticación integrada

#### **ReDoc (Alternativa)**
```
http://127.0.0.1:8000/redoc
```
- Documentación estilo libro
- Mejor para lectura
- Exportable a PDF

#### **OpenAPI JSON**
```
http://127.0.0.1:8000/openapi.json
```
- Especificación OpenAPI 3.0
- Para importar en Postman/Insomnia
- Para generar clientes

### **Cómo Usar Swagger UI**

1. **Abrir** `http://127.0.0.1:8000/docs`

2. **Autenticarse:**
   - Hacer POST a `/users/login`
   - Copiar el `access_token`
   - Click en "Authorize" (candado arriba a la derecha)
   - Pegar: `Bearer {tu_token}`
   - Click "Authorize"

3. **Probar Endpoints:**
   - Expandir cualquier endpoint
   - Click "Try it out"
   - Completar parámetros
   - Click "Execute"
   - Ver respuesta

---

## 📁 Estructura del Proyecto

```
parcial_desarrollo_web/
├── 📄 main.py                  # Punto de entrada de la aplicación
├── 📄 database.py              # Configuración de base de datos
├── 📄 models.py                # Modelos ORM (SQLAlchemy)
├── 📄 schemas.py               # Schemas de validación (Pydantic)
├── 📄 security.py              # Autenticación y seguridad (JWT, bcrypt)
│
├── 📁 routers/                 # Módulos de rutas
│   ├── 📄 users.py            # Gestión de usuarios
│   ├── 📄 teams.py            # Gestión de equipos y jugadores
│   ├── 📄 tournaments.py      # Gestión de torneos y fases
│   └── 📄 public_view.py      # Vistas públicas
│
├── 📁 uploads/                 # Archivos subidos (fotos, documentos)
├── 📁 tests/                   # Tests unitarios e integración
│
├── 📄 .env                     # Variables de entorno (NO versionar)
├── 📄 .env.example             # Ejemplo de variables de entorno
├── 📄 .gitignore               # Archivos ignorados por Git
├── 📄 requirements.txt         # Dependencias Python
└── 📄 README.md                # Documentación básica
```

---

## 🔗 Endpoints Principales

### **🏠 Health Check**

#### `GET /`
Verifica que la API está funcionando.

**Respuesta:**
```json
{
  "message": "API del Torneo de Microfútbol, Fase 1",
  "status": "operational",
  "version": "1.0.0"
}
```

#### `GET /health`
Estado detallado del sistema.

**Respuesta:**
```json
{
  "status": "healthy",
  "database": "connected",
  "uploads_dir": true
}
```

---

### **👥 Gestión de Usuarios** (`/users`)

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/users/register` | Registrar nuevo usuario | ❌ |
| POST | `/users/login` | Iniciar sesión (obtener token) | ❌ |
| GET | `/users/me` | Obtener perfil del usuario autenticado | ✅ |
| PATCH | `/users/me` | Actualizar perfil propio | ✅ |
| GET | `/users/` | Listar todos los usuarios | ✅ Admin |
| GET | `/users/{id}` | Obtener usuario por ID | ✅ Admin |
| PATCH | `/users/{id}` | Actualizar usuario | ✅ Admin |
| DELETE | `/users/{id}` | Eliminar usuario | ✅ Admin |
| GET | `/users/roles/` | Listar roles disponibles | ❌ |
| POST | `/users/init-admin` | Crear administrador inicial | ❌ |

#### **Ejemplos:**

```bash
# Registrar usuario
curl -X POST http://localhost:8000/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "nombre_usuario": "Juan Pérez",
    "email": "juan@example.com",
    "password": "contraseña123",
    "id_rol": 2
  }'

# Login
curl -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@torneo.com",
    "password": "admin123"
  }'

# Obtener perfil
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer {token}"
```

---

### **⚽ Gestión de Equipos** (`/teams`)

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/teams/` | Crear equipo | ✅ Delegado |
| GET | `/teams/` | Listar todos los equipos | ❌ |
| GET | `/teams/{id}` | Obtener equipo por ID | ❌ |
| POST | `/teams/{id}/players/` | Agregar jugador al equipo | ✅ Delegado |
| GET | `/teams/{id}/players/` | Listar jugadores del equipo | ❌ |
| PATCH | `/teams/players/{id}/validate/` | Validar/rechazar jugador | ✅ Admin |
| GET | `/teams/players/pending/` | Listar jugadores pendientes | ✅ Admin |
| GET | `/teams/tipos-jugador/` | Listar tipos de jugador | ❌ |

#### **Ejemplos:**

```bash
# Crear equipo
curl -X POST http://localhost:8000/teams/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Los Tigres"}'

# Agregar jugador (multipart/form-data)
curl -X POST http://localhost:8000/teams/1/players/ \
  -H "Authorization: Bearer {token}" \
  -F "cedula=123456789" \
  -F "nombre_completo=Carlos García" \
  -F "fecha_nacimiento=1995-05-15" \
  -F "id_tipo_jugador=1" \
  -F "numero_camiseta=10" \
  -F "foto=@foto.jpg" \
  -F "documento_probatorio=@documento.pdf"
```

---

### **🏆 Gestión de Torneos** (`/tournaments`)

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/tournaments/` | Crear torneo | ✅ Admin |
| GET | `/tournaments/` | Listar torneos | ❌ |
| GET | `/tournaments/{id}` | Obtener torneo por ID | ❌ |
| PATCH | `/tournaments/{id}/activate` | Activar torneo | ✅ Admin |
| POST | `/tournaments/{id}/phases/` | Crear fase | ✅ Admin |
| GET | `/tournaments/{id}/phases/` | Listar fases del torneo | ❌ |
| POST | `/tournaments/phases/{id}/teams/` | Asignar equipos a fase | ✅ Admin |
| GET | `/tournaments/phases/{id}/teams/` | Listar equipos de fase | ❌ |
| POST | `/tournaments/phases/{id}/generate-schedule/` | Generar calendario | ✅ Admin |
| GET | `/tournaments/phases/{id}/matches/` | Listar partidos de fase | ❌ |
| PATCH | `/tournaments/phases/{id}/apply-bonus/` | Aplicar bonificación | ✅ Admin |
| GET | `/tournaments/formats/` | Listar formatos de fase | ❌ |

---

### **🌐 Vista Pública** (`/public`)

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/public/teams-rosters/` | Plantillas de equipos validados | ❌ |
| GET | `/public/schedule/` | Calendario completo | ❌ |
| GET | `/public/tournament-structure/` | Estructura del torneo | ❌ |
| GET | `/public/statistics-placeholders/` | Estadísticas (placeholder) | ❌ |
| GET | `/public/active-tournament/` | Torneo activo | ❌ |
| GET | `/public/teams/{id}/roster/` | Plantilla de equipo específico | ❌ |
| GET | `/public/phases/{id}/schedule/` | Calendario de fase específica | ❌ |

---

## 🧪 Testing

### **Ejecutar Tests**

```bash
# Activar entorno virtual
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\activate   # Windows

# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=. --cov-report=html

# Ver reporte de cobertura
# Abrir: htmlcov/index.html.html
```

### **Tests Disponibles**

```bash
# Test de seguridad
pytest tests/test_security.py -v

# Test de usuarios
pytest tests/test_users.py -v

# Test específico
pytest tests/test_users.py::test_login -v
```

---

## 🔧 Troubleshooting

### **Error: "ModuleNotFoundError"**

```bash
# Verificar que el entorno virtual está activo
# Debería aparecer (venv) en el prompt

# Reinstalar dependencias
pip install -r requirements.txt
```

### **Error: "Can't connect to MySQL server"**

```bash
# Windows
net start MySQL80

# macOS
brew services start mysql

# Verificar que MySQL está corriendo
mysql -u root -p
```

### **Error: "SECRET_KEY not found"**

```bash
# Crear archivo .env con SECRET_KEY
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env

# O generar manualmente
python -c "import secrets; print(secrets.token_hex(32))"
```

### **Error: "password cannot be longer than 72 bytes"**

La contraseña es muy larga. Bcrypt solo acepta máximo 72 bytes.

```bash
# Usar una contraseña más corta (máx ~70 caracteres)
```

### **Error: "hash could not be identified"**

Usuario con hash antiguo del sistema placeholder.

**Solución:**
```bash
# Opción 1: Limpiar base de datos
mysql -u root -p
USE examen_final_db;
DELETE FROM Usuario;
EXIT;

# Recrear admin
curl -X POST http://localhost:8000/users/init-admin

# Opción 2: Ver SOLUCION_ERROR_HASH.md
```

### **Puerto 8000 en uso**

```bash
# Usar otro puerto
uvicorn main:app --reload --port 8001

# O matar el proceso en el puerto
# Windows:
netstat -ano | findstr :8000
taskkill /PID {PID} /F

# macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

---

## 📞 Soporte y Recursos

### **Documentación Oficial**

- **FastAPI:** https://fastapi.tiangolo.com/
- **SQLAlchemy:** https://docs.sqlalchemy.org/
- **Pydantic:** https://docs.pydantic.dev/
- **JWT:** https://jwt.io/

### **Archivos de Referencia**

- `ANALISIS_PROYECTO.md` - Análisis técnico completo
- `GUIA_IMPLEMENTACION.md` - Guía de implementación paso a paso
- `SOLUCION_ERROR_HASH.md` - Solución a errores de hash
- `RESUMEN_EJECUTIVO.md` - Resumen ejecutivo del proyecto

### **Comandos Útiles**

```bash
# Ver logs del servidor
uvicorn main:app --reload --log-level debug

# Verificar estructura de BD
mysql -u root -p -e "USE examen_final_db; SHOW TABLES;"

# Exportar BD
mysqldump -u root -p examen_final_db > backup.sql

# Importar BD
mysql -u root -p examen_final_db < backup.sql

# Ver dependencias instaladas
pip freeze

# Actualizar dependencia específica
pip install --upgrade fastapi
```

---

## 🎯 Próximos Pasos

Después de la instalación:

1. ✅ Crear administrador inicial (`/users/init-admin`)
2. ✅ Cambiar contraseña del admin
3. ✅ Crear roles y usuarios de prueba
4. ✅ Explorar la documentación en `/docs`
5. ✅ Crear equipos y jugadores de prueba
6. ✅ Configurar torneo

---

## 📝 Notas Importantes

### **Seguridad**

- ⚠️ **Cambiar `SECRET_KEY`** en producción
- ⚠️ **Cambiar contraseña de admin** después del primer inicio
- ⚠️ **NO versionar** el archivo `.env`
- ⚠️ **Usar HTTPS** en producción
- ⚠️ **Configurar CORS** según dominios permitidos

### **Base de Datos**

- La aplicación crea automáticamente la BD y tablas
- Hacer backups regulares en producción
- Configurar índices para mejor rendimiento

### **Archivos**

- Los archivos se guardan en `uploads/`
- Configurar límites de tamaño según necesidad
- Validar tipos de archivo en producción

---

## ✅ Checklist de Instalación

- [ ] Python 3.9+ instalado
- [ ] MySQL 8.0+ instalado y corriendo
- [ ] Repositorio clonado
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Archivo `.env` configurado
- [ ] `SECRET_KEY` generada
- [ ] Base de datos accesible
- [ ] Servidor iniciado (`uvicorn main:app --reload`)
- [ ] Documentación accesible (`http://localhost:8000/docs`)
- [ ] Admin inicial creado (`/users/init-admin`)
- [ ] Login funciona correctamente

---

**¡Sistema listo para usar!** 🚀

Para más información, consulta la documentación interactiva en:
- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

---

_Documentación generada para el proyecto Torneo de Microfútbol_  
_Versión: 1.0.0 - Diciembre 2025_