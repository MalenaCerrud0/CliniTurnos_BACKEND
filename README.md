# CliniTurnos – Backend

API REST (Django + DRF + MySQL) para gestión de turnos médicos.

## Requisitos
- Docker Desktop  
- o Python 3.12 + MySQL 8

## Docker
1. Copiar `.env.example` a `.env` y completar valores  
2. `docker compose up -d --build`  
3. `docker compose exec web python manage.py createsuperuser`  
4. API en http://127.0.0.1:8000

## Desarrollo local
Ver documentación del equipo / variables en `.env.example`