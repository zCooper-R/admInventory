#!/bin/sh
set -e

echo "Waiting for PostgreSQL to be ready..."

until pg_isready -h "${DATABASE_HOST:-db}" -p "${DATABASE_PORT:-5432}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "Ensuring required directories exist and are writable..."
mkdir -p /app/logs /app/media /app/staticfiles

chmod -R 775 /app/logs /app/media /app/staticfiles 2>/dev/null || true

for dir in /app/logs /app/media /app/staticfiles; do
    if [ ! -w "$dir" ]; then
        echo "WARNING: Directory $dir is not writable. Check permissions."
    else
        echo "OK: Directory $dir is writable."
    fi
done

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting application..."
exec "$@"