FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN pip install poetry && poetry install --no-root --no-interaction

COPY src/ src/

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "eorzea_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
