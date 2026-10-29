@echo off
cd /d C:\Users\malen\Desktop\CliniTurnos\backend\cliniturnos
call venv\Scripts\activate.bat
python manage.py generar_slots_automatico --dias 30