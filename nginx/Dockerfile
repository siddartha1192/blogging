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

VOLUME ["/app/static/uploads", "/var/www/certbot", "/etc/letsencrypt"]
