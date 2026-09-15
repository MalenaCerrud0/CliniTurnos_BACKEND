# API CliniTurnos – Lista de endpoints

Base: `http://127.0.0.1:8000`
Auth: header `Authorization: Bearer <access_token>` (salvo donde diga público)

---

## Auth

| Método | URL | Auth | Descripción |
|--------|-----|------|-------------|
| POST | `/api/auth/login/` | No | Login JWT (`login` + `password`) → access + refresh |
| POST | `/api/auth/refresh/` | No | Renovar access con refresh token |

*(Si usás otra ruta tipo `/api/token/`, es la misma idea.)*

---

## Users

| Método | URL | Auth | Descripción |
|--------|-----|------|-------------|
| POST | `/api/users/registro/` | No | Alta paciente (Usuario + rol PACIENTE + Paciente + historia) |
| GET/PATCH | `/api/users/me/` | Sí | Perfil del usuario logueado (+ datos paciente si aplica) |
| GET/POST | `/api/users/usuarios/` | Sí | Listar / crear usuarios |
| GET/PUT/PATCH/DELETE | `/api/users/usuarios/{id}/` | Sí | Detalle / editar / borrar usuario |
| GET/POST | `/api/users/roles/` | Sí | Roles |
| GET/PUT/PATCH/DELETE | `/api/users/roles/{id}/` | Sí | Detalle rol |
| GET/POST | `/api/users/usuario-roles/` | Sí | Asignar rol a usuario |
| GET/PUT/PATCH/DELETE | `/api/users/usuario-roles/{id}/` | Sí | Detalle asignación |

---

## Profesionales

| Método | URL | Auth | Descripción |
|--------|-----|------|-------------|
| GET | `/api/profesionales/especialidades/` | Sí | Catálogo (lectura todos) |
| POST/PUT/PATCH/DELETE | `/api/profesionales/especialidades/` … | Admin | CRUD especialidades (R21) |
| GET/POST | `/api/profesionales/profesionales/` | Sí | Listar / crear profesionales |
| GET/PUT/PATCH/DELETE | `/api/profesionales/profesionales/{id}/` | Sí | Detalle profesional |
| POST | `/api/profesionales/profesionales/alta/` | Admin | Alta completa (usuario + MEDICO + profesional + matrícula/especialidades) |
| POST | `/api/profesionales/profesionales/{id}/baja/` | Admin | Baja (usuario INACTIVO) |
| POST | `/api/profesionales/profesionales/{id}/reactivar/` | Admin | Reactivar |
| GET/POST | `/api/profesionales/matriculas/` | Sí | Matrículas |
| GET/PUT/PATCH/DELETE | `/api/profesionales/matriculas/{id}/` | Sí | Detalle matrícula |
| GET/POST | `/api/profesionales/horarios/` | Sí | Horarios (médico: solo los suyos) |
| GET/PUT/PATCH/DELETE | `/api/profesionales/horarios/{id}/` | Sí | Detalle horario |

*(Si el router usa otros path names — `profesional-especialidades`, etc. — el patrón es el mismo.)*

---

## Pacientes

| Método | URL | Auth | Descripción |
|--------|-----|------|-------------|
| GET/POST | `/api/pacientes/pacientes/` (o la ruta que tengan) | Sí | Listar / crear |
| GET/PUT/PATCH/DELETE | `/api/pacientes/pacientes/{id}/` | Sí | Detalle |
| GET/POST | obras sociales (si expusieron ViewSet) | Sí | Catálogo OS |

---

## Turnos

| Método | URL | Auth | Descripción |
|--------|-----|------|-------------|
| GET | `/api/turnos/turnos/` | Sí | Listado (filtrado por rol) |
| GET | `/api/turnos/turnos/?proximos=1` | Sí | Próximos |
| GET | `/api/turnos/turnos/?pasados=1` | Sí | Pasados |
| GET | `/api/turnos/turnos/?estado=RESERVADO` | Sí | Por estado |
| GET | `/api/turnos/turnos/?profesional=1` | Sí | Por profesional |
| GET | `/api/turnos/turnos/{id}/` | Sí | Detalle |
| GET | `/api/turnos/turnos/disponibilidad/?fecha=YYYY-MM-DD` | Sí | Slots libres (opcional: `tipo_turno`, `especialidad_id`, `profesional_id`) |
| GET | `/api/turnos/turnos/profesionales-disponibles/?fecha=YYYY-MM-DD` | Sí | Profesionales con hueco ese día |
| POST | `/api/turnos/turnos/generar_slots/` | Admin/Médico | Generar slots consulta (profesional + horarios) |
| POST | `/api/turnos/turnos/generar-slots-estudio/` | Admin/Médico | Generar slots estudio (especialidad, sin médico) |
| POST | `/api/turnos/turnos/{id}/reservar/` | Sí | Reservar (`paciente_id` opcional si es el paciente logueado; `comentario`) |
| POST | `/api/turnos/turnos/{id}/cancelar/` | Dueño/Admin | Cancelar (regla 24 hs) |
| POST | `/api/turnos/turnos/{id}/reprogramar/` | Dueño/Admin | Body: `{ "nuevo_turno_id": N }` |
| POST | `/api/turnos/turnos/{id}/iniciar/` | Admin/Médico | EN_CURSO + Consulta o Estudio (`tipo_estudio_id` si ESTUDIO) |
| GET/POST | `/api/turnos/fechas-bloqueadas/` (si está registrado) | Sí | Bloqueos de fechas |

**Commands (no HTTP):**
`python manage.py limpiar_turnos_vencidos`
`python manage.py enviar_recordatorios`

---

## Clínicos

| Método | URL | Auth | Descripción |
|--------|-----|------|-------------|
| GET/POST | `/api/clinicos/consultas/` | Admin/Médico | Consultas |
| GET/PUT/PATCH | `/api/clinicos/consultas/{id}/` | Admin/Médico | Completar informe |
| POST | `/api/clinicos/consultas/{id}/finalizar/` | Admin/Médico | Consulta + turno FINALIZADO |
| GET | `/api/clinicos/historias-clinicas/` | Sí | Historias (paciente: la suya; médico/admin: según filtro) |
| GET | `/api/clinicos/historias-clinicas/{id}/` | Sí | Detalle + `informes` (consultas finalizadas) |
| GET/POST | `/api/clinicos/alergias/` | Admin/Médico | Alergias |
| GET/PUT/PATCH/DELETE | `/api/clinicos/alergias/{id}/` | Admin/Médico | |
| GET/POST | `/api/clinicos/medicaciones/` | Admin/Médico | Medicaciones habituales |
| GET/PUT/PATCH/DELETE | `/api/clinicos/medicaciones/{id}/` | Admin/Médico | |
| GET/POST | `/api/clinicos/tipos-estudio/` | Sí | Tipos de estudio |
| GET/PUT/PATCH/DELETE | `/api/clinicos/tipos-estudio/{id}/` | Sí | |
| GET/POST | `/api/clinicos/estudios/` | Sí (escritura Admin/Médico) | Estudios |
| GET/PUT/PATCH | `/api/clinicos/estudios/{id}/` | Sí | Completar; `REALIZADO` → cierra turno |
| GET/POST | `/api/clinicos/documentos/` | Lectura autenticada; escritura Admin/Médico | Adjuntos (form-data) |
| GET/PUT/PATCH/DELETE | `/api/clinicos/documentos/{id}/` | Según permisos | |
| GET | `/api/clinicos/documentos/?consulta=1` | Sí | Filtrar por consulta |
| GET | `/api/clinicos/documentos/?estudio=1` | Sí | Filtrar por estudio |
| GET | `/api/clinicos/documentos/?turno=1` | Sí | Filtrar por turno |

---

## Notificaciones

| Método | URL | Auth | Descripción |
|--------|-----|------|-------------|
| GET | `/api/notificaciones/notificaciones/` | Sí | Listado (admin: todas; resto: las suyas) |
| GET | `/api/notificaciones/notificaciones/{id}/` | Sí | Detalle |
| POST/PATCH… | según ViewSet | Sí | Alta/edición manual si está habilitada |

Se crean solas al **reservar / cancelar / reprogramar** y con el command de **recordatorios**.

---

## Flujos típicos (recordatorio)

**Paciente – consulta**
`disponibilidad` → `reservar` → (opcional cancelar/reprogramar) → médico `iniciar` → PATCH consulta → `finalizar`

**Paciente – estudio**
`generar-slots-estudio` (admin) → `disponibilidad?tipo_turno=ESTUDIO` → `reservar` → `iniciar` + `tipo_estudio_id` → PATCH estudio `REALIZADO`

**Admin – profesional**
`POST .../profesionales/alta/` → `baja` / `reactivar`

---

## Notas para el front

1. Guardar `access` y renovar con `refresh` cuando expire.
2. Uploads de documentos: **multipart/form-data**, no JSON.
3. Media en dev: `/media/...` si configuraron `MEDIA_URL`.
4. Errores de negocio suelen ser **400** con `{ "error": "..." }`; login inactivo **401**.

Si algún path en tu router difiere (por ejemplo `generar_slots` vs `generar-slots`), priorizá lo que salga en:

`GET http://127.0.0.1:8000/api/`
o el browsable API de DRF.
