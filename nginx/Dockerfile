FROM nginx:1.27-alpine

# Bake static files into the image so we don't need a bind mount.
# Build context must be the project root (context: . in compose).
COPY static /app/static

# Create all volume mountpoints and declare them as VOLUME.
# This mirrors the postgres image pattern and avoids mkdirat
# on VPS hosts with read-only overlayfs.
RUN mkdir -p /app/static/uploads \
             /var/www/certbot \
             /etc/letsencrypt

# The official nginx image symlinks access/error logs to stdout/stderr.
# Replace them with real files so the host-mounted ./logs/nginx/ volume
# contains actual log files that can be age-rotated by db_backup.sh clean.
RUN rm -f /var/log/nginx/access.log /var/log/nginx/error.log \
 && touch /var/log/nginx/access.log /var/log/nginx/error.log \
 && chown nginx:nginx /var/log/nginx/access.log /var/log/nginx/error.log

VOLUME ["/app/static/uploads", "/var/www/certbot", "/etc/letsencrypt", "/var/log/nginx"]
