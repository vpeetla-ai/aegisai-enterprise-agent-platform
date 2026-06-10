FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PORT=8000

WORKDIR /app

COPY services/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/api/src /app/src

EXPOSE 8000

CMD ["sh", "-c", "uvicorn aegisai.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
