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
python manage.py collectstatic --noinput

echo "Loading demo data (skips if already present)..."
python manage.py create_demo_data || echo "Demo data step skipped."

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000
