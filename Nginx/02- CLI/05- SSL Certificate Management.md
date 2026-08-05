# SSL Certificate Management

CLI commands for managing SSL/TLS certificates with Nginx — from Let's Encrypt automation to certificate inspection, renewal, and OCSP stapling.

---

# Let's Encrypt with Certbot

## Installation

```bash
# Debian/Ubuntu
sudo apt install certbot python3-certbot-nginx

# RHEL/CentOS
sudo dnf install certbot python3-certbot-nginx

# Amazon Linux 2
sudo amazon-linux-extras install epel
sudo yum install certbot python3-certbot-nginx
```

## Obtain a Certificate

```bash
# Automatic mode — certbot modifies Nginx config for you
sudo certbot --nginx -d example.com -d www.example.com

# Certificate-only mode — get cert without modifying Nginx config
sudo certbot certonly --nginx -d example.com -d www.example.com

# Webroot mode — for servers you don't want certbot to touch
sudo certbot certonly --webroot -w /var/www/html -d example.com

# Standalone mode — certbot runs its own temporary web server (port 80 must be free)
sudo certbot certonly --standalone -d example.com
```

## Certificate File Locations

After certbot succeeds:

```text
/etc/letsencrypt/live/example.com/
├── fullchain.pem     ← Certificate + intermediate CA (use in ssl_certificate)
├── privkey.pem       ← Private key (use in ssl_certificate_key)
├── cert.pem          ← Server certificate only
└── chain.pem         ← Intermediate CA certificate only
```

## Nginx SSL Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # Modern TLS settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/example.com/chain.pem;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
}
```

---

# Certificate Renewal

## Automatic Renewal

Certbot installs a systemd timer or cron job that runs twice daily:

```bash
# Check if the renewal timer is active
sudo systemctl status certbot.timer

# View the timer schedule
sudo systemctl list-timers | grep certbot

# Or check the cron job
cat /etc/cron.d/certbot
```

## Manual Renewal

```bash
# Dry-run to test renewal without actually renewing
sudo certbot renew --dry-run

# Force renewal of all certificates
sudo certbot renew

# Renew a specific certificate
sudo certbot renew --cert-name example.com

# Renew and reload Nginx automatically
sudo certbot renew --deploy-hook "systemctl reload nginx"
```

## Deploy Hook

Set up automatic Nginx reload after renewal:

```bash
# Create a deploy hook that runs after every successful renewal
sudo mkdir -p /etc/letsencrypt/renewal-hooks/deploy
cat << 'EOF' | sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
#!/bin/bash
systemctl reload nginx
EOF
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```

**Important**: Let's Encrypt certificates expire after **90 days**. Certbot renews when less than 30 days remain. Always verify the renewal timer is active.

---

# Certificate Inspection

## View Certificate Details

```bash
# View certificate expiration and subject from a file
openssl x509 -in /etc/letsencrypt/live/example.com/fullchain.pem -noout -text | head -30

# Show only expiration date
openssl x509 -in /etc/letsencrypt/live/example.com/fullchain.pem -noout -enddate
# Output: notAfter=Oct 16 10:30:00 2026 GMT

# Show subject and issuer
openssl x509 -in /etc/letsencrypt/live/example.com/fullchain.pem -noout -subject -issuer

# Show all SANs (Subject Alternative Names)
openssl x509 -in /etc/letsencrypt/live/example.com/fullchain.pem -noout -ext subjectAltName
```

## Check Certificate from a Live Server

```bash
# Connect to a server and show its certificate
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | \
    openssl x509 -noout -subject -issuer -dates

# Output:
# subject=CN = example.com
# issuer=C = US, O = Let's Encrypt, CN = R3
# notBefore=Jul 18 10:30:00 2026 GMT
# notAfter=Oct 16 10:30:00 2026 GMT

# Show the full certificate chain
echo | openssl s_client -connect example.com:443 -servername example.com -showcerts 2>/dev/null

# Check TLS version and cipher negotiated
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | \
    grep -E 'Protocol|Cipher'
# Output:
#   Protocol  : TLSv1.3
#   Cipher    : TLS_AES_256_GCM_SHA384
```

## Check Certificate Expiration Across All Domains

```bash
# List all certbot-managed certificates and their expiry
sudo certbot certificates

# Output:
# Certificate Name: example.com
#   Domains: example.com www.example.com
#   Expiry Date: 2026-10-16 10:30:00+00:00 (VALID: 89 days)
#   Certificate Path: /etc/letsencrypt/live/example.com/fullchain.pem
#   Private Key Path: /etc/letsencrypt/live/example.com/privkey.pem
```

## Quick Expiration Check Script

```bash
#!/bin/bash
# Check SSL expiry for multiple domains
DOMAINS="example.com api.example.com admin.example.com"

for DOMAIN in $DOMAINS; do
    EXPIRY=$(echo | openssl s_client -connect ${DOMAIN}:443 -servername ${DOMAIN} 2>/dev/null | \
        openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
    DAYS_LEFT=$(( ($(date -d "${EXPIRY}" +%s) - $(date +%s)) / 86400 ))

    if [ $DAYS_LEFT -lt 14 ]; then
        echo "⚠️  ${DOMAIN}: EXPIRES in ${DAYS_LEFT} days (${EXPIRY})"
    else
        echo "✅ ${DOMAIN}: OK — ${DAYS_LEFT} days remaining"
    fi
done
```

---

# Verify Certificate Chain

```bash
# Verify the certificate chain is complete and valid
openssl verify -CAfile /etc/ssl/certs/ca-certificates.crt \
    /etc/letsencrypt/live/example.com/fullchain.pem

# If you see "error 20: unable to get local issuer certificate"
# → The chain is incomplete. Use fullchain.pem, not cert.pem.

# Verify that the private key matches the certificate
CERT_MD5=$(openssl x509 -noout -modulus -in /etc/letsencrypt/live/example.com/fullchain.pem | md5sum)
KEY_MD5=$(openssl rsa -noout -modulus -in /etc/letsencrypt/live/example.com/privkey.pem | md5sum)

if [ "$CERT_MD5" = "$KEY_MD5" ]; then
    echo "✅ Certificate and private key MATCH"
else
    echo "❌ Certificate and private key DO NOT MATCH"
fi
```

---

# Self-Signed Certificates (Development Only)

```bash
# Generate a self-signed certificate valid for 365 days
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/selfsigned.key \
    -out /etc/nginx/ssl/selfsigned.crt \
    -subj "/C=US/ST=State/L=City/O=Dev/CN=localhost"

# Generate Diffie-Hellman parameters (for PFS)
openssl dhparam -out /etc/nginx/ssl/dhparam.pem 2048
```

**Never use self-signed certificates in production**. Browsers will show security warnings, and clients will reject the connection.

---

# OCSP Stapling Verification

```bash
# Check if OCSP stapling is working
echo | openssl s_client -connect example.com:443 -servername example.com -status 2>/dev/null | \
    grep -A 5 "OCSP Response Status"

# Expected output (stapling working):
# OCSP Response Status: successful (0x0)

# If empty, OCSP stapling is not configured or the resolver is failing
```

---

# Common Mistakes

- Using `cert.pem` instead of `fullchain.pem` in `ssl_certificate`. This breaks the chain — some clients (especially mobile) will reject the certificate.
- Not setting up a certbot deploy hook to reload Nginx after renewal. The renewed certificate won't take effect until Nginx reloads.
- Not testing renewal with `--dry-run` after initial setup. If renewal fails silently, you'll discover it when the site goes down in 90 days.
- Forgetting to check that the private key matches the certificate after manual certificate replacement.
- Not enabling OCSP stapling — clients make an extra roundtrip to the CA's OCSP server, adding latency to the TLS handshake.

---

# Key Takeaways

- Use `certbot --nginx` for the simplest Let's Encrypt setup. It handles everything.
- Always use `fullchain.pem` (not `cert.pem`) in `ssl_certificate` to include the intermediate chain.
- Set up a deploy hook (`systemctl reload nginx`) so Nginx picks up renewed certificates automatically.
- Run `certbot renew --dry-run` after initial setup to verify automatic renewal works.
- Use `openssl s_client` to inspect live certificates and verify TLS configuration.
- Enable OCSP stapling to reduce TLS handshake latency.
- Let's Encrypt certificates expire in 90 days — always verify the certbot timer is active.

---
