#!/bin/bash
# =============================================================================
# db_backup.sh — TechBobbles PostgreSQL backup & restore tool
#
# Usage:
#   ./db_backup.sh            → create a backup (default)
#   ./db_backup.sh backup     → create a backup
#   ./db_backup.sh restore    → restore from a chosen backup file
#   ./db_backup.sh list       → list all available backups
#   ./db_backup.sh clean      → delete backups older than KEEP_DAYS
#
# Requirements:
#   - Docker + docker-compose running
#   - .env file present in the same directory as this script
# =============================================================================

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/backups"
KEEP_DAYS=30          # delete backups older than this many days during clean
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# ── Load .env ─────────────────────────────────────────────────────────────────
ENV_FILE="${SCRIPT_DIR}/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: .env file not found at ${ENV_FILE}"
    exit 1
fi

# Export only the Postgres vars we need (avoids polluting the environment)
export $(grep -E '^POSTGRES_(USER|PASSWORD|DB)=' "$ENV_FILE" | xargs)

: "${POSTGRES_USER:?POSTGRES_USER not set in .env}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD not set in .env}"
: "${POSTGRES_DB:?POSTGRES_DB not set in .env}"

# ── Helpers ───────────────────────────────────────────────────────────────────
red()    { printf '\033[0;31m%s\033[0m\n' "$*"; }
green()  { printf '\033[0;32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[0;33m%s\033[0m\n' "$*"; }
bold()   { printf '\033[1m%s\033[0m\n'   "$*"; }
hr()     { printf '%0.s─' {1..60}; echo; }

check_db_running() {
    if ! docker-compose -f "${SCRIPT_DIR}/docker-compose.yml" ps db \
            --format '{{.State}}' 2>/dev/null | grep -q "running"; then
        red "ERROR: The 'db' container is not running."
        echo "Start it with:  docker-compose up -d db"
        exit 1
    fi
}

# ── Backup ────────────────────────────────────────────────────────────────────
do_backup() {
    mkdir -p "$BACKUP_DIR"
    check_db_running

    local file="${BACKUP_DIR}/techblog_${TIMESTAMP}.sql.gz"

    bold; echo "Creating backup…"; hr

    docker-compose -f "${SCRIPT_DIR}/docker-compose.yml" exec -T db \
        pg_dump \
            --username="$POSTGRES_USER" \
            --no-password \
            --clean \
            --if-exists \
            --no-owner \
            --no-acl \
            "$POSTGRES_DB" \
        | gzip > "$file"

    local size
    size="$(du -sh "$file" | cut -f1)"

    green "Backup saved:"
    echo "  File : ${file}"
    echo "  Size : ${size}"
    echo "  Time : $(date)"
    hr
}

# ── List ──────────────────────────────────────────────────────────────────────
do_list() {
    mkdir -p "$BACKUP_DIR"
    bold; echo "Available backups in ${BACKUP_DIR}:"; hr

    local files=("${BACKUP_DIR}"/techblog_*.sql.gz)
    if [[ ! -e "${files[0]}" ]]; then
        yellow "No backups found."
        return
    fi

    local i=1
    for f in "${files[@]}"; do
        printf "  %2d.  %s  (%s)\n" "$i" "$(basename "$f")" "$(du -sh "$f" | cut -f1)"
        (( i++ ))
    done
    hr
    echo "Total: $((i-1)) backup(s)"
}

# ── Restore ───────────────────────────────────────────────────────────────────
do_restore() {
    mkdir -p "$BACKUP_DIR"
    check_db_running

    # Build array of available backups
    local files=("${BACKUP_DIR}"/techblog_*.sql.gz)
    if [[ ! -e "${files[0]}" ]]; then
        red "No backup files found in ${BACKUP_DIR}"
        exit 1
    fi

    bold; echo "Available backups:"; hr
    local i=1
    for f in "${files[@]}"; do
        printf "  %2d.  %s  (%s)\n" "$i" "$(basename "$f")" "$(du -sh "$f" | cut -f1)"
        (( i++ ))
    done
    hr

    local choice
    read -rp "Enter number to restore (or 'q' to quit): " choice
    [[ "$choice" == "q" ]] && exit 0

    if ! [[ "$choice" =~ ^[0-9]+$ ]] || (( choice < 1 || choice >= i )); then
        red "Invalid selection."
        exit 1
    fi

    local target="${files[$((choice-1))]}"
    echo
    yellow "WARNING: This will OVERWRITE the current '${POSTGRES_DB}' database."
    read -rp "Type 'yes' to confirm: " confirm
    [[ "$confirm" != "yes" ]] && { echo "Aborted."; exit 0; }

    bold; echo "Restoring from $(basename "$target")…"; hr

    gunzip -c "$target" | \
        docker-compose -f "${SCRIPT_DIR}/docker-compose.yml" exec -T db \
            psql \
                --username="$POSTGRES_USER" \
                --no-password \
                --dbname="$POSTGRES_DB" \
                --quiet

    green "Restore complete."
    echo "Restart the app to pick up changes:  docker-compose restart app"
    hr
}

# ── Clean ─────────────────────────────────────────────────────────────────────
do_clean() {
    mkdir -p "$BACKUP_DIR"
    bold; echo "Removing backups older than ${KEEP_DAYS} days…"; hr

    local count=0
    while IFS= read -r -d '' f; do
        echo "  Deleting: $(basename "$f")"
        rm -f "$f"
        (( count++ ))
    done < <(find "$BACKUP_DIR" -name 'techblog_*.sql.gz' \
                -mtime +"$KEEP_DAYS" -print0)

    if (( count == 0 )); then
        green "Nothing to clean — all backups are within ${KEEP_DAYS} days."
    else
        green "Deleted ${count} old backup(s)."
    fi
    hr
}

# ── Entry point ───────────────────────────────────────────────────────────────
CMD="${1:-backup}"

case "$CMD" in
    backup)  do_backup  ;;
    restore) do_restore ;;
    list)    do_list    ;;
    clean)   do_clean   ;;
    *)
        echo "Usage: $0 [backup|restore|list|clean]"
        exit 1
        ;;
esac
