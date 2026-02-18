FROM python:3.11-slim

WORKDIR /app

# Install system deps
# gosu  → clean privilege-drop in entrypoint (root → app user)
# gcc / libpq-dev → compile psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create unprivileged user and hand ownership of /app to it.
# The uploads directory is owned by 'app' here, but the entrypoint
# re-applies chown at runtime so named-volume mounts are always writable.
RUN mkdir -p /app/static/uploads /app/static/seed \
    && addgroup --system app && adduser --system --ingroup app app \
    && chown -R app:app /app

# Entrypoint runs as root so it can fix volume permissions, then drops
# to 'app' via gosu before exec-ing gunicorn.
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
