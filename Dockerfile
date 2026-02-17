FROM python:3.11-slim

WORKDIR /app

# Install system deps for potential C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/static/uploads

# Railway injects PORT; default to 8080
ENV PORT=8080

EXPOSE ${PORT}

# Run with gunicorn — workers & threads tuned for Railway starter plan
CMD gunicorn wsgi:app \
    --bind 0.0.0.0:${PORT} \
    --workers 2 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
