#!/bin/bash
# =============================================================================
# init-ssl.sh — One-time Let's Encrypt SSL setup
#
# Run this ONCE after your DNS A record is live and containers are up.
# It will:
#   1. Issue a certificate via certbot (webroot challenge through nginx)
#   2. Generate nginx/nginx-ssl.conf with your domain substituted in
#   3. Switch docker-compose to use the SSL nginx config
#   4. Reload nginx
#   5. Install a cron job that renews + reloads nginx twice daily
#
# Prerequisites:
#   - DOMAIN and EMAIL set in .env
#   - DNS A record for DOMAIN pointing to this server's IP
#   - Ports 80 and 443 open in your firewall
#   - Containers running: docker-compose up -d
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE="docker compose -f ${SCRIPT_DIR}/docker-compose.yml"

# ── Colours ────────────────────────────────────────────────────────────────
red()    { printf '\033[0;31m%s\033[0m\n' "$*"; }
green()  { printf '\033[0;32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[0;33m%s\033[0m\n' "$*"; }
bold()   { printf '\033[1m%s\033[0m\n'   "$*"; }
step()   { printf '\033[0;36m  %-52s\033[0m' "$*"; }
ok()     { printf '\033[0;32m OK\033[0m\n'; }
hr()     { printf '%0.s─' {1..60}; echo; }

# ── Load .env ──────────────────────────────────────────────────────────────
ENV_FILE="${SCRIPT_DIR}/.env"
[[ -f "$ENV_FILE" ]] || { red "ERROR: .env not found at ${ENV_FILE}"; exit 1; }
# source rather than export+xargs so values with spaces/special chars work
set -a; source "$ENV_FILE"; set +a

: "${DOMAIN:?DOMAIN not set in .env}"
: "${EMAIL:?EMAIL not set in .env}"

[[ "$DOMAIN" == "yourdomain.com" ]] && {
    red "ERROR: Replace 'yourdomain.com' with your actual domain in .env"
    exit 1
}

# ── Guard: already done? ───────────────────────────────────────────────────
SSL_CONF="${SCRIPT_DIR}/nginx/nginx-ssl.conf"
if [[ -f "$SSL_CONF" ]]; then
    yellow "nginx-ssl.conf already exists."
    read -rp "Re-issue certificate and regenerate config? [y/N] " ans
    [[ "${ans,,}" == "y" ]] || { echo "Aborted."; exit 0; }
fi

bold "SSL Initialisation — ${DOMAIN}"
hr

# ── Step 1: Verify containers ──────────────────────────────────────────────
step "Checking nginx and certbot containers…"
for svc in nginx certbot; do
    cid="$($COMPOSE ps -q "$svc" 2>/dev/null)"
    if [[ -z "$cid" ]] || \
       ! docker inspect -f '{{.State.Running}}' "$cid" 2>/dev/null | grep -q "^true$"; then
        echo
        red "ERROR: '${svc}' container is not running."
        echo "  Run: docker-compose up -d"
        exit 1
    fi
done
ok

# ── Step 2: Issue certificate via webroot ─────────────────────────────────
echo
bold "Requesting Let's Encrypt certificate for ${DOMAIN} and www.${DOMAIN}…"
hr
$COMPOSE exec -T certbot certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --domain "$DOMAIN" \
    --domain "www.${DOMAIN}" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    --keep-until-expiring
echo
green "Certificate issued successfully."
hr

# ── Step 3: Generate nginx SSL config (substitute domain) ─────────────────
step "Generating nginx/nginx-ssl.conf…"
# nginx doesn't do env-var substitution; sed the template on the host instead
sed "s|\${DOMAIN}|${DOMAIN}|g" "${SCRIPT_DIR}/nginx/nginx.conf" > "$SSL_CONF"
ok

# ── Step 4: Switch docker-compose to the SSL config ───────────────────────
step "Updating docker-compose.yml nginx volume…"
sed -i \
    "s|nginx-initial\.conf:/etc/nginx/conf\.d/default\.conf|nginx-ssl.conf:/etc/nginx/conf.d/default.conf|g" \
    "${SCRIPT_DIR}/docker-compose.yml"
ok

step "Restarting nginx with SSL config…"
$COMPOSE up -d --no-deps --force-recreate nginx
ok

# ── Step 5: Verify nginx is serving HTTPS ────────────────────────────────
echo
step "Verifying HTTPS response…"
sleep 2   # give nginx a moment to start
if curl -sSf --max-time 10 "https://${DOMAIN}" -o /dev/null 2>/dev/null; then
    ok
else
    yellow "(Could not verify — check firewall / DNS propagation if site is unreachable)"
fi

# ── Step 6: Install renewal cron ──────────────────────────────────────────
mkdir -p "${SCRIPT_DIR}/logs"
RENEW_SCRIPT="${SCRIPT_DIR}/ssl-renew.sh"
CRON_LINE="0 0,12 * * * ${RENEW_SCRIPT} >> ${SCRIPT_DIR}/logs/ssl-renew.log 2>&1"

step "Installing renewal cron job…"
if crontab -l 2>/dev/null | grep -qF "$RENEW_SCRIPT"; then
    yellow "(already installed — skipped)"
else
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
    ok
fi

hr
green "SSL setup complete!"
echo "  Site      : https://${DOMAIN}  (www.${DOMAIN} redirects here)"
echo "  Cert dir  : /etc/letsencrypt/live/${DOMAIN}/"
echo "  Renewal   : ${RENEW_SCRIPT}"
echo "  Cron      : daily at 00:00 and 12:00"
echo "  Log       : ${SCRIPT_DIR}/logs/ssl-renew.log"
hr
