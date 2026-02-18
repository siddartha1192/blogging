#!/bin/bash
# =============================================================================
# db_backup.sh — TechBobbles full backup & restore (DB + static uploads)
#
# Each backup is a single .tar.gz bundle:
#   techblog_YYYYMMDD_HHMMSS.tar.gz
#   ├── db.sql.gz        ← PostgreSQL dump
#   └── uploads.tar.gz   ← /app/static/uploads/ from the uploads volume
#
# Usage:
#   ./db_backup.sh              → create a full backup (default)
#   ./db_backup.sh backup       → create a full backup
#   ./db_backup.sh restore      → restore DB + uploads from a chosen backup
#   ./db_backup.sh restore db   → restore database only
#   ./db_backup.sh restore files→ restore uploads only
#   ./db_backup.sh list         → list all available backups
#   ./db_backup.sh clean        → delete backups older than KEEP_DAYS
#                                 AND log files older than LOG_KEEP_DAYS (10 days)
#
# Requirements:
#   - Docker + docker-compose running  (db and app containers)
#   - .env file in the same directory as this script
# =============================================================================

set -euo pipefail

# ── Config ─────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/backups"
KEEP_DAYS=30      # delete backup archives older than this many days
LOG_KEEP_DAYS=10  # delete log files older than this many days
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG_DIR="${SCRIPT_DIR}/logs"
COMPOSE="docker-compose -f ${SCRIPT_DIR}/docker-compose.yml"

# ── Load .env ──────────────────────────────────────────────────────────────
ENV_FILE="${SCRIPT_DIR}/.env"
[[ -f "$ENV_FILE" ]] || { echo "ERROR: .env not found at ${ENV_FILE}"; exit 1; }
export $(grep -E '^POSTGRES_(USER|PASSWORD|DB)=' "$ENV_FILE" | xargs)
: "${POSTGRES_USER:?POSTGRES_USER not set in .env}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD not set in .env}"
: "${POSTGRES_DB:?POSTGRES_DB not set in .env}"

# ── Helpers ────────────────────────────────────────────────────────────────
red()    { printf '\033[0;31m%s\033[0m\n' "$*"; }
green()  { printf '\033[0;32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[0;33m%s\033[0m\n' "$*"; }
bold()   { printf '\033[1m%s\033[0m\n'   "$*"; }
step()   { printf '\033[0;36m  %-40s\033[0m' "$*"; }
ok()     { printf '\033[0;32m OK\033[0m\n'; }
hr()     { printf '%0.s─' {1..60}; echo; }

check_running() {
    local svc="$1"
    # docker-compose v1 prints "Up"; v2 prints "running" — match either
    if ! $COMPOSE ps "$svc" 2>/dev/null | grep -qE "\bUp\b|running"; then
        red "ERROR: '${svc}' container is not running."
        echo "Start it with:  docker-compose up -d ${svc}"
        exit 1
    fi
}

# Create a temp dir and guarantee cleanup on exit
TMPDIR_WORK=""
cleanup() {
    [[ -n "$TMPDIR_WORK" && -d "$TMPDIR_WORK" ]] && rm -rf "$TMPDIR_WORK"
}
trap cleanup EXIT

# ── Backup ─────────────────────────────────────────────────────────────────
do_backup() {
    mkdir -p "$BACKUP_DIR"
    check_running db
    check_running app

    local bundle="${BACKUP_DIR}/techblog_${TIMESTAMP}.tar.gz"
    TMPDIR_WORK="$(mktemp -d)"

    bold; echo "Creating full backup…"; hr

    # 1. Database dump
    step "Dumping PostgreSQL database…"
    $COMPOSE exec -T db \
        pg_dump \
            --username="$POSTGRES_USER" \
            --no-password \
            --clean \
            --if-exists \
            --no-owner \
            --no-acl \
            "$POSTGRES_DB" \
        | gzip > "${TMPDIR_WORK}/db.sql.gz"
    ok

    # 2. Static uploads from the app container (reads the Docker volume)
    step "Archiving static uploads…"
    $COMPOSE exec -T app \
        tar czf - -C /app/static/uploads . \
        > "${TMPDIR_WORK}/uploads.tar.gz" 2>/dev/null || {
            # If uploads dir is empty tar exits non-zero; create an empty archive
            tar czf "${TMPDIR_WORK}/uploads.tar.gz" -T /dev/null 2>/dev/null || true
        }
    ok

    # 3. Bundle both into one archive
    step "Bundling into single archive…"
    tar czf "$bundle" -C "$TMPDIR_WORK" db.sql.gz uploads.tar.gz
    ok

    local size
    size="$(du -sh "$bundle" | cut -f1)"

    echo
    green "Backup saved:"
    echo "  File      : ${bundle}"
    echo "  Size      : ${size}"
    echo "  Timestamp : ${TIMESTAMP}"
    echo "  Contains  : PostgreSQL dump + static uploads"
    hr
}

# ── List ───────────────────────────────────────────────────────────────────
do_list() {
    mkdir -p "$BACKUP_DIR"
    bold; echo "Available backups in ${BACKUP_DIR}:"; hr

    local files=("${BACKUP_DIR}"/techblog_*.tar.gz)
    if [[ ! -e "${files[0]}" ]]; then
        yellow "No backups found."
        return
    fi

    local i=1
    for f in "${files[@]}"; do
        local ts
        ts="$(basename "$f" | sed 's/techblog_\(.*\)\.tar\.gz/\1/' \
              | sed 's/\(....\)\(..\)\(..\)_\(..\)\(..\)\(..\)/\1-\2-\3 \4:\5:\6/')"
        printf "  %2d.  %-45s %s  (%s)\n" \
            "$i" "$(basename "$f")" "$ts" "$(du -sh "$f" | cut -f1)"
        (( i++ ))
    done
    hr
    echo "Total: $((i-1)) backup(s)"
}

# ── Pick a backup file interactively ───────────────────────────────────────
pick_backup() {
    local files=("${BACKUP_DIR}"/techblog_*.tar.gz)
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

    # Return selected file via stdout
    echo "${files[$((choice-1))]}"
}

# ── Restore ────────────────────────────────────────────────────────────────
do_restore() {
    mkdir -p "$BACKUP_DIR"
    check_running db
    check_running app

    # Optional mode: "db" | "files" | "" (both)
    local mode="${1:-both}"

    local target
    target="$(pick_backup)"

    echo
    case "$mode" in
        db)    yellow "WARNING: This will OVERWRITE the '${POSTGRES_DB}' database." ;;
        files) yellow "WARNING: This will OVERWRITE all files in the uploads volume." ;;
        both)  yellow "WARNING: This will OVERWRITE the database AND all uploads." ;;
    esac
    read -rp "Type 'yes' to confirm: " confirm
    [[ "$confirm" != "yes" ]] && { echo "Aborted."; exit 0; }

    TMPDIR_WORK="$(mktemp -d)"
    bold; echo; echo "Restoring from $(basename "$target")…"; hr

    # Extract the bundle
    step "Extracting bundle…"
    tar xzf "$target" -C "$TMPDIR_WORK"
    ok

    # ── Restore database ────────────────────────────────────────────────
    if [[ "$mode" == "db" || "$mode" == "both" ]]; then
        step "Restoring PostgreSQL database…"
        gunzip -c "${TMPDIR_WORK}/db.sql.gz" | \
            $COMPOSE exec -T db \
                psql \
                    --username="$POSTGRES_USER" \
                    --no-password \
                    --dbname="$POSTGRES_DB" \
                    --quiet
        ok
    fi

    # ── Restore uploads ─────────────────────────────────────────────────
    if [[ "$mode" == "files" || "$mode" == "both" ]]; then
        step "Restoring static uploads…"
        # Clear existing uploads inside the container, then extract
        $COMPOSE exec -T app sh -c \
            'find /app/static/uploads -mindepth 1 -not -name ".gitkeep" -delete'
        $COMPOSE exec -T app \
            tar xzf - -C /app/static/uploads \
            < "${TMPDIR_WORK}/uploads.tar.gz"
        # Fix ownership in case tar extracted as root
        $COMPOSE exec -T app sh -c \
            'chown -R app:app /app/static/uploads 2>/dev/null || true'
        ok
    fi

    echo
    green "Restore complete."
    echo "Restart the app to pick up changes:"
    echo "  docker-compose restart app"
    hr
}

# ── Clean ──────────────────────────────────────────────────────────────────
do_clean() {
    mkdir -p "$BACKUP_DIR"

    # ── 1. Old backup archives ───────────────────────────────────────────
    bold; echo "Removing backups older than ${KEEP_DAYS} days…"; hr

    local bcount=0
    while IFS= read -r -d '' f; do
        echo "  Deleting: $(basename "$f")"
        rm -f "$f"
        (( bcount++ ))
    done < <(find "$BACKUP_DIR" -name 'techblog_*.tar.gz' \
                -mtime +"$KEEP_DAYS" -print0)

    if (( bcount == 0 )); then
        green "No old backups — all within ${KEEP_DAYS} days."
    else
        green "Deleted ${bcount} old backup(s)."
    fi

    # ── 2. Old log files ─────────────────────────────────────────────────
    echo
    bold; echo "Removing log files older than ${LOG_KEEP_DAYS} days…"; hr

    local lcount=0
    if [[ -d "$LOG_DIR" ]]; then
        while IFS= read -r -d '' f; do
            echo "  Deleting: ${f#${SCRIPT_DIR}/}"
            rm -f "$f"
            (( lcount++ ))
        done < <(find "$LOG_DIR" -type f \( -name '*.log' -o -name '*.log.*' \) \
                    -mtime +"$LOG_KEEP_DAYS" -print0)
    fi

    if (( lcount == 0 )); then
        green "No old log files — all within ${LOG_KEEP_DAYS} days."
    else
        green "Deleted ${lcount} old log file(s) from ${LOG_DIR}."
    fi
    hr
}

# ── Entry point ────────────────────────────────────────────────────────────
CMD="${1:-backup}"
SUBCMD="${2:-both}"

case "$CMD" in
    backup)  do_backup ;;
    restore)
        case "$SUBCMD" in
            db)    do_restore db    ;;
            files) do_restore files ;;
            both|"") do_restore both ;;
            *)
                red "Unknown restore target '${SUBCMD}'. Use: db | files | (blank for both)"
                exit 1
                ;;
        esac
        ;;
    list)    do_list   ;;
    clean)   do_clean  ;;
    *)
        bold "Usage: $0 [backup|restore [db|files]|list|clean]"
        exit 1
        ;;
esac
