FROM nginx:1.27-alpine

# Pre-create all mount-point directories so Docker never needs to
# mkdir inside the (potentially read-only) overlay filesystem.
RUN mkdir -p /app/static/uploads \
             /var/www/certbot \
             /etc/letsencrypt
