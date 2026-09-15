#!/bin/sh
set -e

echo "Esperando a MySQL en $DB_HOST:$DB_PORT..."
python << 'EOF'
import os, time, sys
import MySQLdb

host = os.environ.get("DB_HOST", "db")
port = int(os.environ.get("DB_PORT", "3306"))
user = os.environ["DB_USER"]
password = os.environ["DB_PASSWORD"]
name = os.environ["DB_NAME"]

for i in range(30):
    try:
        MySQLdb.connect(host=host, user=user, passwd=password, db=name, port=port)
        print("MySQL listo")
        sys.exit(0)
    except Exception as e:
        print(f"Intento {i+1}/30: {e}")
        time.sleep(2)

print("No se pudo conectar a MySQL")
sys.exit(1)
EOF

echo "Migraciones..."
python manage.py migrate --noinput

echo "Collectstatic..."
python manage.py collectstatic --noinput || true

exec "$@"