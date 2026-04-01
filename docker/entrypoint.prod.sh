#!/bin/sh
set -e

run_as_django() {
  su -s /bin/sh django -c "$*"
}

LOG_DIR=${LOG_DIR:-/app/logs}
echo "Preparing log directory: ${LOG_DIR}"
mkdir -p "${LOG_DIR}"
chown -R django:django "${LOG_DIR}" || true
chmod -R u+rwX,g+rwX "${LOG_DIR}" || true
run_as_django "touch '${LOG_DIR}/.write_test'"
rm -f "${LOG_DIR}/.write_test"

echo "Waiting for database..."
until run_as_django "python -c \"
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
\""; do
  sleep 1
done

echo "Running migrations..."
run_as_django "python manage.py migrate --noinput"

echo "Collecting static files..."
run_as_django "python manage.py collectstatic --noinput --clear"

WORKERS=${GUNICORN_WORKERS:-4}
echo "Starting Gunicorn (workers=${WORKERS})..."
exec su -s /bin/sh django -c "gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers '${WORKERS}' \
    --worker-class sync \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info"
