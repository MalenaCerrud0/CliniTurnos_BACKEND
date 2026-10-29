# Cómo correr CliniTurnos con Docker

## Requisitos previos

En la PC donde lo vayas a levantar:

1. Docker Desktop instalado y en ejecución
2. Git
3. (Opcional) Un editor de texto para editar el archivo `.env`

Comprobar:

```bash
docker --version
docker compose version
```

## 1. Clonar el repositorio

```bash
git clone https://github.com/USUARIO/CliniTurnos.git
cd CliniTurnos/cliniturnos
```

(Cambiá la URL y la carpeta por las de tu repo)

## 2. Crear el archivo de entorno

Copiá el ejemplo y editá los valores:

```bash
# Windows (PowerShell / CMD)
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Abrí `.env` y completá al menos:

```env
SECRET_KEY=genera-una-clave-larga-y-aleatoria
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=cliniturnos
DB_USER=clini
DB_PASSWORD=clini_pass
DB_ROOT_PASSWORD=root_pass
DB_HOST=db
DB_PORT=3306

# Email (Resend u otro SMTP)
EMAIL_HOST=smtp.resend.com
EMAIL_PORT=587
EMAIL_HOST_USER=resend
EMAIL_HOST_PASSWORD=tu_api_key
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=CliniTurnos
```

> **Importante:** no subas el `.env` a GitHub (debe estar en `.gitignore`). Solo versioná `.env.example` sin secretos.

## 3. Construir e iniciar los contenedores

Desde la carpeta del proyecto (donde está `docker-compose.yml`):

```bash
docker compose build
docker compose up -d
```

La primera vez puede tardar varios minutos (imagen de Python, MySQL, dependencias).

Servicios típicos:

| Servicio | Rol |
|----------|-----|
| `db` | MySQL 8 |
| `web` | API Django (Gunicorn) |
| `cron` | Limpieza de turnos vencidos + recordatorios (cada hora) |

## 4. Verificar que está arriba

```bash
docker compose ps
```

Los contenedores deberían figurar como `running` / `healthy`.

Probar la API en el navegador o con `curl`:

```
http://127.0.0.1:8000/api/
```

o el admin:

```
http://127.0.0.1:8000/admin/
```

## 5. Crear un superusuario (admin)

```bash
docker compose exec web python manage.py createsuperuser
```

Seguí las preguntas (login/usuario, email si pide, contraseña).

Login JWT de ejemplo:

```http
POST http://127.0.0.1:8000/api/auth/login/
Content-Type: application/json

{
  "login": "tu_usuario",
  "password": "tu_password"
}
```


## 6. Comandos útiles

```bash
# Ver logs de la API
docker compose logs -f web

# Ver logs del cron (recordatorios / limpieza)
docker compose logs -f cron

# Parar todo
docker compose down

# Parar y borrar también la base de datos del volumen
docker compose down -v

# Entrar a una shell dentro del contenedor web
docker compose exec web bash

# Migraciones manuales (si hiciera falta)
docker compose exec web python manage.py migrate
```

## 7. Puertos

| Puerto en la PC | Servicio |
|------------------|----------|
| 8000 | API Django |
| 3307 | MySQL (mapeado desde el contenedor; solo si está expuesto en `docker-compose.yml`) |

Si el puerto 8000 está ocupado, cambiá en `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"
```

y usá `http://127.0.0.1:8001`.

## 8. Problemas frecuentes

| Problema | Qué hacer |
|----------|-----------|
| `docker compose` no se reconoce | Actualizar Docker Desktop; en versiones viejas probar `docker-compose` |
| Error de conexión a MySQL al arrancar | Esperar a que el healthcheck de `db` pase; volver a `docker compose up -d` |
| Puerto en uso | Cambiar el mapeo de puertos en `docker-compose.yml` |
| No llegan mails | Revisar variables de email en `.env` y reiniciar: `docker compose up -d --force-recreate web` |
| Cambios en el código no se ven | Rebuild: `docker compose build --no-cache web && docker compose up -d` |

## Estructura mínima esperada en el repo

```
cliniturnos/
├── docker-compose.yml
├── Dockerfile
├── docker/
│   └── entrypoint.sh
├── .env.example
├── requirements.txt
├── manage.py
├── config/
└── ...
```