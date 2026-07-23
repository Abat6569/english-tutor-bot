FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recurse-suggests \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src
COPY alembic.ini ./
COPY alembic ./alembic

RUN pip install --no-cache-dir .

CMD ["python", "-m", "src.bot.main"]
