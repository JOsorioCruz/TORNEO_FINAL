# 📊 DESARROLLO FRONTEND

## 🎯 RESUMEN

La API está organizada en **4 módulos principales** con **44 endpoints totales**:

```
┌─────────────────────────────────────────────────┐
│   API TORNEO MICROFÚTBOL - ESTRUCTURA          │
├─────────────────────────────────────────────────┤
│                                                 │
│  📁 M1: Usuarios (10 endpoints)                │
│     ├─ Autenticación (Login/Register)          │
│     ├─ Perfil de usuario                       │
│     └─ Gestión admin de usuarios               │
│                                                 │
│  📁 M2: Equipos y Jugadores (10 endpoints)     │
│     ├─ CRUD de equipos                         │
│     ├─ Gestión de jugadores                    │
│     └─ Validación de jugadores                 │
│                                                 │
│  📁 M5: Torneos (15 endpoints)                 │
│     ├─ CRUD de torneos                         │
│     ├─ Gestión de fases                        │
│     ├─ Asignación de equipos                   │
│     └─ Generación de calendario                │
│                                                 │
│  📁 M8: Vista Pública (7 endpoints)            │
│     ├─ Plantillas de equipos                   │
│     ├─ Calendario público                      │
│     └─ Estructura del torneo                   │
│                                                 │
│  📁 Health Check (2 endpoints)                 │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🔐 SISTEMA DE AUTENTICACIÓN

### Flujo de Autenticación
```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Usuario   │─────>│ POST /login  │─────>│  JWT Token  │
└─────────────┘      └──────────────┘      └─────────────┘
                                                   │
                                                   ▼
                          ┌─────────────────────────────────┐
                          │ Authorization: Bearer {token}   │
                          └─────────────────────────────────┘
                                       │
                          ┌────────────┴────────────┐
                          ▼                         ▼
                    ┌──────────┐            ┌──────────┐
                    │  Admin   │            │ Delegado │
                    │ Endpoints│            │ Endpoints│
                    └──────────┘            └──────────┘
```

### Roles del Sistema
```javascript
{
  "roles": [
    {
      "id_rol": 1,
      "nombre": "Administrador",
      "permisos": [
        "Crear torneos",
        "Gestionar fases",
        "Validar jugadores",
        "Ver todos los equipos",
        "Gestionar usuarios",
        "Eliminar equipos"
      ]
    },
    {
      "id_rol": 2,
      "nombre": "Delegado",
      "permisos": [
        "Crear equipos",
        "Agregar jugadores a sus equipos",
        "Ver calendario",
        "Actualizar su perfil"
      ]
    }
  ]
}
```

---

## 🗂️ ESTRUCTURA DE DATOS PRINCIPALES

### 1️⃣ Usuario
```javascript
{
  "id_usuario": 1,
  "nombre_usuario": "Juan Pérez",
  "email": "juan@example.com",
  "id_rol": 2,
  "rol": {
    "id_rol": 2,
    "nombre": "Delegado"
  }
  // password_hash nunca se retorna
}
```

### 2️⃣ Equipo
```javascript
{
  "id_equipo": 1,
  "nombre": "Los Tigres",
  "id_delegado": 2,
  "fecha_creacion": "2024-01-15T10:30:00"
}
```

### 3️⃣ Jugador
```javascript
{
  "id_jugador": 1,
  "cedula": "1234567890",
  "nombre_completo": "Carlos Rodríguez",
  "fecha_nacimiento": "1995-05-15",
  "numero_camiseta": 10,
  "foto_url": "uploads/1_1234567890_FOTO_20240115103000.jpg",
  "documento_probatorio_url": "uploads/1_1234567890_DOC_20240115103000.pdf",
  "estado_validacion": "Validado", // o "Pendiente" o "Rechazado"
  "fecha_validacion": "2024-01-15T14:00:00",
  "id_equipo": 1,
  "id_tipo_jugador": 1,
  "tipo_jugador": {
    "id_tipo_jugador": 1,
    "nombre": "vecino del barrio san luis"
  }
}
```

### 4️⃣ Torneo
```javascript
{
  "id_torneo": 1,
  "nombre": "Torneo Barrio San Luis 2024",
  "esta_activo": true,
  "fecha_inicio": "2024-01-15",
  "fecha_fin": "2024-03-30"
}
```

### 5️⃣ Fase
```javascript
{
  "id_fase": 1,
  "nombre": "Fase de Grupos",
  "orden": 1,
  "id_torneo": 1,
  "id_formato": 2,
  "bonificacion_aplicada": false,
  "reglas_clasificacion": "Mejores 2 equipos por grupo",
  "formato": {
    "id_formato": 2,
    "nombre": "Grupos"
  }
}
```

### 6️⃣ Partido
```javascript
{
  "id_partido": 1,
  "fecha_hora": "2024-01-20T15:00:00",
  "lugar": "Cancha Principal - Grupo A",
  "fase_nombre": "Fase de Grupos",
  "equipo_local_nombre": "Los Tigres",
  "equipo_visitante_nombre": "Las Águilas"
}
```

---

## 🔄 FLUJOS DE TRABAJO PRINCIPALES

### Flujo 1: Registro e Inicio de Sesión
```
1. GET /users/roles/              → Obtener roles disponibles
2. POST /users/register           → Registrar usuario (delegado)
3. POST /users/login              → Obtener token JWT
4. GET /users/me                  → Verificar datos del usuario
```

### Flujo 2: Crear Equipo y Agregar Jugadores
```
1. POST /teams/                   → Crear equipo (con token delegado)
2. GET /teams/tipos-jugador/      → Obtener tipos de jugador
3. POST /teams/{id}/players/      → Agregar jugador (multipart/form-data)
   - Subir foto
   - Subir documento probatorio
   - Llenar datos del jugador
4. GET /teams/{id}/players/       → Ver jugadores del equipo
```

### Flujo 3: Validación de Jugadores (Admin)
```
1. GET /teams/players/pending/    → Ver jugadores pendientes
2. PATCH /teams/players/{id}/validate/ → Validar o rechazar
   {"estado_validacion": "Validado"}
```

### Flujo 4: Crear Torneo y Estructura (Admin)
```
1. POST /tournaments/             → Crear torneo
2. PATCH /tournaments/{id}/activate → Activar torneo
3. GET /tournaments/formats/      → Ver formatos disponibles
4. POST /tournaments/{id}/phases/ → Crear fase
5. POST /tournaments/phases/{id}/assign-teams/ → Asignar equipos
6. POST /tournaments/phases/{id}/generate-schedule/ → Generar partidos
```

### Flujo 5: Consulta Pública
```
1. GET /public/active-tournament/ → Ver torneo activo
2. GET /public/teams-rosters/     → Ver equipos y plantillas
3. GET /public/schedule/          → Ver calendario completo
4. GET /public/tournament-structure/ → Ver estructura (fases)
```

---

## 📋 VALIDACIONES IMPORTANTES DEL BACKEND

### Validaciones de Jugadores
```javascript
const VALIDACIONES = {
  maxJugadoresPorEquipo: 15,
  maxExtranjerosPorEquipo: 3,  // tipos 2, 3, 4
  maxDocentesIE: 2,             // tipo 3
  maxDocentesFundacion: 2,      // tipo 4
  edadMinimaExtranjeros: 26,    // años
  
  tiposJugador: {
    1: "vecino del barrio san luis",
    2: "agente de policía (estación vallejo)",
    3: "docente/trabajador (institución educativa el dorado)",
    4: "docente/trabajador/padre (fundación vallejo)"
  },
  
  archivos: {
    foto: {
      tipos: ["image/jpeg", "image/png", "image/jpg"],
      maxSize: "5MB"
    },
    documento: {
      tipos: ["application/pdf", "image/jpeg", "image/png"],
      maxSize: "10MB"
    }
  }
};
```

### Estados de Validación
```javascript
const ESTADOS_VALIDACION = {
  PENDIENTE: "Pendiente",   // Estado inicial
  VALIDADO: "Validado",     // Aprobado por admin
  RECHAZADO: "Rechazado"    // Rechazado por admin
};
```

---

## 🎨 MANEJO DE ERRORES PARA EL FRONTEND

### 1. Manejo de Autenticación
```javascript
// Guardar token en localStorage
localStorage.setItem('token', response.access_token);

// Incluir en todas las peticiones autenticadas
const headers = {
  'Authorization': `Bearer ${localStorage.getItem('token')}`,
  'Content-Type': 'application/json'
};
```

### 2. Manejo de Errores Comunes
```javascript
const ERROR_HANDLERS = {
  401: "Token inválido o expirado - Redirigir a login",
  403: "Permisos insuficientes - Mostrar mensaje",
  404: "Recurso no encontrado",
  400: "Datos inválidos - Mostrar errores de validación",
  500: "Error del servidor - Reintentar"
};
```

### 3. Estructura de Carpetas Frontend
```
frontend/
├── pages/
│   ├── login.html              → POST /users/login
│   ├── register.html           → POST /users/register
│   ├── dashboard.html          → GET /users/me
│   ├── equipos.html            → GET /teams/
│   ├── crear-equipo.html       → POST /teams/
│   ├── jugadores.html          → GET /teams/{id}/players/
│   ├── agregar-jugador.html    → POST /teams/{id}/players/
│   ├── validar-jugadores.html  → GET /teams/players/pending/
│   ├── torneos.html            → GET /tournaments/
│   ├── crear-torneo.html       → POST /tournaments/
│   ├── fases.html              → GET /tournaments/{id}/phases/
│   ├── calendario.html         → GET /public/schedule/
│   └── plantillas.html         → GET /public/teams-rosters/
├── js/
│   ├── auth.js                 → Manejo de autenticación
│   ├── api.js                  → Funciones para llamar API
│   └── utils.js                → Utilidades comunes
└── css/
    └── styles.css
```

### 4. Funciones JavaScript Básicas
```javascript
// api.js - Ejemplo de funciones helper

const API_BASE = 'http://localhost:8000';

// Obtener token
async function login(email, password) {
  const response = await fetch(`${API_BASE}/users/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await response.json();
  if (response.ok) {
    localStorage.setItem('token', data.access_token);
  }
  return data;
}

// Crear equipo
async function crearEquipo(nombre) {
  const response = await fetch(`${API_BASE}/teams/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: JSON.stringify({ nombre })
  });
  return await response.json();
}

// Agregar jugador (con archivos)
async function agregarJugador(teamId, formData) {
  const response = await fetch(`${API_BASE}/teams/${teamId}/players/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: formData // FormData con archivos
  });
  return await response.json();
}

// Obtener equipos
async function obtenerEquipos() {
  const response = await fetch(`${API_BASE}/teams/`);
  return await response.json();
}

// Obtener calendario público
async function obtenerCalendario() {
  const response = await fetch(`${API_BASE}/public/schedule/`);
  return await response.json();
}
```

---

## 📌 CASOS DE USO ESPECÍFICOS

### Caso 1: Subir Foto de Jugador
```javascript
// HTML
<input type="file" id="foto" accept="image/jpeg,image/png">
<input type="file" id="documento" accept="application/pdf,image/*">

// JavaScript
const formData = new FormData();
formData.append('cedula', '1234567890');
formData.append('nombre_completo', 'Carlos Rodríguez');
formData.append('fecha_nacimiento', '1995-05-15');
formData.append('numero_camiseta', '10');
formData.append('id_tipo_jugador', '1');
formData.append('foto', document.getElementById('foto').files[0]);
formData.append('documento_probatorio', document.getElementById('documento').files[0]);

await agregarJugador(teamId, formData);
```

### Caso 2: Mostrar Imagen desde el Servidor
```javascript
// La URL completa de la imagen es:
const imagenURL = `http://localhost:8000/static/uploads/${jugador.foto_url.split('/').pop()}`;

// En HTML:
<img src="${imagenURL}" alt="${jugador.nombre_completo}">
```

### Caso 3: Verificar Rol del Usuario
```javascript
async function verificarRol() {
  const response = await fetch(`${API_BASE}/users/me`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  });
  const usuario = await response.json();
  
  if (usuario.rol.nombre === 'Administrador') {
    // Mostrar opciones de admin
    mostrarMenuAdmin();
  } else {
    // Mostrar opciones de delegado
    mostrarMenuDelegado();
  }
}
```

---
