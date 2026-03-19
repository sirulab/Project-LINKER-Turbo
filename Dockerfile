FROM python:3.12-slim

# Install system dependencies required by psycopg2-binary
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (cached layer — only rebuilds when requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Normalise line endings (in case the repo was cloned on Windows with CRLF)
# and make the entrypoint executable
RUN sed -i 's/\r$//' scripts/entrypoint.sh && \
    chmod +x scripts/entrypoint.sh

EXPOSE 8000

# entrypoint.sh runs `alembic upgrade head` then starts Uvicorn
ENTRYPOINT ["scripts/entrypoint.sh"]
