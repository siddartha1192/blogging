#!/bin/bash
# =============================================================================
# ssl-renew.sh — Renew Let's Encrypt cert and reload nginx
#
# Called by cron (installed by init-ssl.sh) twice daily.
# certbot only performs a real renewal when the cert has fewer than 30 days
# left, so this is safe to run frequently.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE="docker-compose -f ${SCRIPT_DIR}/docker-compose.yml"

echo "$(date '+%Y-%m-%d %H:%M:%S') --- ssl-renew start ---"

# Attempt renewal (no-op if cert is still valid for >30 days)
$COMPOSE exec -T certbot certbot renew --quiet

# Reload nginx to pick up any newly issued cert
$COMPOSE exec -T nginx nginx -s reload

echo "$(date '+%Y-%m-%d %H:%M:%S') --- ssl-renew done ---"
