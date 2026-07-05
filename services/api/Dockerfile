FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PORT=8000

WORKDIR /app

# git is required by pip to install the agent-finops dependency below
# (a git+https source, not a PyPI package).
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY services/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/api/src /app/src
COPY platform/database/postgres-migration.sql /app/migrations/postgres-migration.sql

EXPOSE 8000

CMD ["sh", "-c", "uvicorn aegisai.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
