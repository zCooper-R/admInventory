FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 django && \
    mkdir -p /app /app/staticfiles /app/media /app/logs && \
    chown -R django:django /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY --chown=django:django backend/ .

RUN mkdir -p /app/docker
COPY --chown=django:django docker/entrypoint.sh /app/docker/entrypoint.sh
COPY --chown=django:django docker/wait-for-postgres.sh /app/docker/wait-for-postgres.sh
RUN sed -i 's/\r$//' /app/docker/entrypoint.sh /app/docker/wait-for-postgres.sh && \
    chmod +x /app/docker/entrypoint.sh /app/docker/wait-for-postgres.sh

USER django

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
