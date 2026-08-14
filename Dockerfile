FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

COPY pyproject.toml README.md ./
COPY app ./app

RUN python -m pip install --no-cache-dir .

COPY alembic.ini ./
COPY alembic ./alembic

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
