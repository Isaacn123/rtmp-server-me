#!/bin/bash
# Script to initialize SSL certificates with certbot
# Run this once to get your first certificate

DOMAIN="live.kayanja1.org"
EMAIL="your-email@example.com"  # Change this to your email address

# Create directories if they don't exist
mkdir -p certbot/conf
mkdir -p certbot/www

echo "Requesting SSL certificate for $DOMAIN..."
echo "Make sure your domain $DOMAIN points to this server's IP address!"
echo ""
echo "NOTE: Since port 80 is used by another nginx, you have two options:"
echo "  1. Configure your main nginx to proxy /.well-known/acme-challenge/ to port 8080"
echo "  2. Use DNS-01 challenge instead (run certbot-init-dns.sh)"
echo ""

# Check if main nginx is configured to proxy certbot challenges
echo "Attempting webroot method (requires main nginx to proxy challenges)..."
echo ""

docker run --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  certbot/certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email $EMAIL \
  --agree-tos \
  --no-eff-email \
  -d $DOMAIN

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Certificate obtained successfully!"
    echo "Now restart nginx:"
    echo "  docker compose restart nginx-rtmp"
    echo ""
    echo "Your site will be available at: https://$DOMAIN:8443"
else
    echo ""
    echo "❌ Webroot method failed. Try DNS-01 challenge instead:"
    echo "  ./certbot-init-dns.sh"
    echo ""
    echo "Or configure your main nginx to proxy certbot challenges:"
    echo "  See nginx-proxy-config.conf for configuration"
fi
