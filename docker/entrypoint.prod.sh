#!/bin/sh
# Production entrypoint — uses Gunicorn instead of runserver.
set -e

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
python manage.py collectstatic --noinput --clear

WORKERS=${GUNICORN_WORKERS:-4}
echo "Starting Gunicorn (workers=${WORKERS})..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${WORKERS}" \
    --worker-class sync \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
