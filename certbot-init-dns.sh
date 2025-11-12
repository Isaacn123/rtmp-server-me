#!/bin/bash
# Alternative: Use DNS-01 challenge (doesn't require port 80)
# This is useful when port 80 is already in use

DOMAIN="live.kayanja1.org"
EMAIL="your-email@example.com"  # Change this to your email address

# Create directories if they don't exist
mkdir -p certbot/conf
mkdir -p certbot/www

echo "Requesting SSL certificate for $DOMAIN using DNS-01 challenge..."
echo "This method doesn't require port 80 to be available."
echo ""
echo "You'll need to add a TXT record to your DNS when prompted."
echo ""
echo "Press Enter to continue..."
read

docker run -it --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  certbot/certbot certonly \
  --manual \
  --preferred-challenges dns \
  --email $EMAIL \
  --agree-tos \
  --no-eff-email \
  --manual-public-ip-logging-ok \
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
    echo "❌ Certificate request failed."
    echo ""
    echo "Make sure you:"
    echo "  1. Added the TXT record to your DNS"
    echo "  2. Waited for DNS propagation (check with: dig TXT _acme-challenge.live.kayanja1.org)"
    echo "  3. Pressed Enter when prompted"
fi

