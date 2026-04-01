#!/bin/sh
set -e

host="${POSTGRES_HOST:-db}"
port="${POSTGRES_PORT:-5432}"
user="${POSTGRES_USER:-postgres}"
password="${POSTGRES_PASSWORD:-postgres}"
dbname="${POSTGRES_DB:-postgres}"

echo "Waiting for PostgreSQL at $host:$port..."
until PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "postgres" -c '\q' 2>/dev/null; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "PostgreSQL is up and database $dbname is ready"
