
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN groupadd --system appgroup \
    && useradd --system --gid appgroup appuser

COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip install --no-cache-dir pytest

COPY . .

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

CMD ["python", "app.py"]
