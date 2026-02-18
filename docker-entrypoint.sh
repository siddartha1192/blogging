#!/bin/sh
# docker-entrypoint.sh  — runs as root, drops to 'app' before gunicorn
set -e

# ── 1. Fix uploads volume ownership ───────────────────────────────────────
# The named volume is often created as root-owned; the 'app' user needs
# write access so image uploads via the admin panel work.
mkdir -p /app/static/uploads
chown -R app:app /app/static/uploads
echo "[entrypoint] Uploads directory ownership fixed."

# ── 2. Sync Git-tracked seed images into the uploads volume ───────────────
# Place any images / files you commit to the repo under static/seed/.
# On every container start they are copied into the uploads volume
# (non-destructively — existing runtime uploads are never overwritten).
if [ -d /app/static/seed ] && [ "$(ls -A /app/static/seed 2>/dev/null)" ]; then
    cp -rn /app/static/seed/. /app/static/uploads/
    chown -R app:app /app/static/uploads
    echo "[entrypoint] Seed images synced to uploads volume."
fi

# ── 3. Wait for PostgreSQL ─────────────────────────────────────────────────
echo "[entrypoint] Waiting for PostgreSQL..."
until gosu app python3 -c \
    "import psycopg2, os; psycopg2.connect(os.environ['DATABASE_URL']).close()" \
    2>/dev/null; do
    sleep 2
done
echo "[entrypoint] PostgreSQL is ready."

# ── 4. Initialise DB (idempotent) — runs ONCE before workers start ─────────
# This avoids the gunicorn multi-worker race condition where every worker
# imported app.py simultaneously and all tried to seed the database.
gosu app python3 - <<'PYEOF'
from app import app, db, init_db, create_placeholder_images
with app.app_context():
    init_db()
    create_placeholder_images()
PYEOF
echo "[entrypoint] Database initialised."

# ── 5. Hand off to gunicorn as unprivileged 'app' user ────────────────────
echo "[entrypoint] Starting gunicorn..."
exec gosu app gunicorn wsgi:app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
