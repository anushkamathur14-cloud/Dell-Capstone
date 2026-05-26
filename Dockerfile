# Railway: explicit image avoids Nixpacks/Railpack merge issues on heavy Python stacks.
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Wheels for scipy / sklearn usually suffice; build-essential covers edge compiles.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-railway.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-railway.txt

COPY . .

RUN mkdir -p /app/data \
    && chmod +x scripts/run_api_prod.sh

EXPOSE 8080
CMD ["sh", "scripts/run_api_prod.sh"]
