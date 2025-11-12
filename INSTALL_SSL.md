# SSL Certificate Installation Guide

## Prerequisites

1. ✅ Domain `live.kayanja1.org` DNS is pointing to your server IP
2. ✅ Main nginx is configured to proxy to port 8080 (see `nginx-proxy-config.conf`)
3. ✅ Docker containers are running

## Step-by-Step Installation

### Step 1: Update Email Address

Edit `certbot-init.sh` and change the email:

```bash
nano certbot-init.sh
```

Change this line:
```bash
EMAIL="your-email@example.com"  # Change to your actual email
```

### Step 2: Make Script Executable

```bash
chmod +x certbot-init.sh
```

### Step 3: Ensure Main Nginx is Configured

Make sure your main nginx (on port 80) has the proxy configuration from `nginx-proxy-config.conf`:

```bash
# Check if configuration exists
sudo nginx -t

# If not configured, add the configuration from nginx-proxy-config.conf
# Then reload:
sudo systemctl reload nginx
```

### Step 4: Start Docker Containers

```bash
docker compose up -d
```

### Step 5: Run Certbot to Get Certificate

```bash
./certbot-init.sh
```

This will:
- Request a certificate from Let's Encrypt
- Use the webroot method (requires port 80 to proxy to 8080)
- Save certificates to `./certbot/conf/`

### Step 6: Restart RTMP Nginx

After certificate is obtained:

```bash
docker compose restart nginx-rtmp
```

### Step 7: Verify SSL Works

Visit: `https://live.kayanja1.org:8443/`

## Alternative: DNS-01 Challenge (If Webroot Fails)

If the webroot method fails (port 80 issues), use DNS challenge:

```bash
chmod +x certbot-init-dns.sh
./certbot-init-dns.sh
```

When prompted, add a TXT record to your DNS:
- Go to your DNS provider
- Add TXT record: `_acme-challenge.live.kayanja1.org`
- Value: (will be shown in the script output)
- Wait a few minutes for DNS propagation
- Press Enter to continue

## Troubleshooting

### Error: "Connection refused" or "Port 80 not accessible"

**Solution**: Make sure your main nginx is configured to proxy `/.well-known/acme-challenge/` to port 8080

### Error: "Domain not pointing to this server"

**Solution**: 
1. Check DNS: `dig live.kayanja1.org` or `nslookup live.kayanja1.org`
2. Wait for DNS propagation (can take up to 48 hours, usually 5-60 minutes)

### Error: "Certificate already exists"

**Solution**: Certificates are already installed. Just restart nginx:
```bash
docker compose restart nginx-rtmp
```

### Check Certificate Status

```bash
# View certificate details
docker run --rm -v "$(pwd)/certbot/conf:/etc/letsencrypt" certbot/certbot certificates
```

## Auto-Renewal

Certificates automatically renew every 12 hours via the certbot container in docker-compose.yml.

To manually renew:
```bash
docker compose exec certbot certbot renew
docker compose restart nginx-rtmp
```

## Verify Installation

After installation, test your SSL:

```bash
# Check certificate
openssl s_client -connect live.kayanja1.org:8443 -servername live.kayanja1.org

# Or visit in browser
https://live.kayanja1.org:8443/
```

You should see a valid SSL certificate from Let's Encrypt! 🔒

