#!/bin/sh
set -e

LOG_DIR=${LOG_DIR:-/app/logs}
echo "Preparing log directory: ${LOG_DIR}"
mkdir -p "${LOG_DIR}"
chmod -R 0777 "${LOG_DIR}" || true
touch "${LOG_DIR}/.write_test" && rm -f "${LOG_DIR}/.write_test" || true

echo "Waiting for database..."
until python -c "
import os, psycopg2
try:
    conn = psycopg2.connect(
        dbname=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        host=os.environ.get('POSTGRES_HOST', 'db'),
        port=os.environ.get('POSTGRES_PORT', '5432'),
    )
    conn.close()
    print('DB is ready')
except Exception as e:
    print(f'DB not ready: {e}')
    exit(1)
"; do
  sleep 1
done


echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Loading demo data (skips if already present)..."
python manage.py create_demo_data || echo "Demo data step skipped."

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000
