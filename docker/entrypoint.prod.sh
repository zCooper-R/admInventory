#!/bin/sh
set -e

echo "Waiting for PostgreSQL to be ready..."
/app/docker/wait-for-postgres.sh

echo "Ensuring required directories exist and are writable..."
mkdir -p /app/logs /app/staticfiles /app/media
chmod -R 775 /app/logs /app/staticfiles /app/media 2>/dev/null || true

for dir in /app/logs /app/staticfiles /app/media; do
    if [ ! -w "$dir" ]; then
        echo "WARNING: Directory $dir is not writable. Check permissions."
    fi
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
