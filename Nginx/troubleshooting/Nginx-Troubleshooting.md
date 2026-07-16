# Nginx Advanced Troubleshooting Guide

Created by: aranya majumdar

---

# Overview

This troubleshooting guide provides comprehensive solutions to common and advanced Nginx issues encountered in production environments.

Topics covered:

- Configuration context errors
- HTTP error codes
- Docker and Kubernetes issues
- SSL/TLS problems
- Performance bottlenecks
- Reverse proxy failures
- Permission issues
- Network troubleshooting
- Real-world debugging scenarios

---

# Troubleshooting Methodology

```text
Problem Identified

        │

        ▼

Reproduce Issue

        │

        ▼

Gather Information

        │

        ▼

Check Logs

        │

        ▼

Isolate Root Cause

        │

        ▼

Apply Fix

        │

        ▼

Verify Solution

        │

        ▼

Document Resolution
```

---

# Section 1: Configuration Errors

## Issue 1.1: Worker_processes Directive Not Allowed Here

![Worker Process Issue](../images/Worker_Process.png)

### Problem:

```text
nginx: [emerg] "worker_processes" directive is not allowed here
in /etc/nginx/conf.d/default.conf:1
```

### Root Cause:

When containerizing Nginx with Docker, the `worker_processes` directive cannot be placed inside configuration files located in `/etc/nginx/conf.d/`.

**Why This Happens:**

Nginx configuration follows a strict hierarchy:

```text
Main Context
    │
    ├── worker_processes
    ├── events { }
    │
    └── http {
            │
            └── server { }
    }
```

The official Nginx Docker image automatically includes files from `/etc/nginx/conf.d/*.conf` **inside** the `http { }` block.

If your `default.conf` contains:

```nginx
worker_processes auto;

server {
    listen 80;
}
```

Nginx reads it as:

```nginx
http {
    worker_processes auto;  # ❌ Wrong context!
}
```

This violates the configuration hierarchy.

### Solution:

**Option 1: Remove the Directive (Recommended)**

Delete `worker_processes` from your `default.conf` file.

The official Nginx Docker image already configures:

```nginx
worker_processes auto;
```

in the main `/etc/nginx/nginx.conf` file, which automatically scales workers to match CPU cores.

**Option 2: Override Main Configuration**

If you need full control, replace the entire `nginx.conf`:

```dockerfile
FROM nginx:alpine
COPY custom-nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/default.conf
```

Your `custom-nginx.conf`:

```nginx
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/conf.d/*.conf;
}
```

---

## Issue 1.2: Duplicate Location Block

### Problem:

```text
nginx: [emerg] duplicate location "/"
in /etc/nginx/conf.d/default.conf:15
```

### Root Cause:

You cannot define the same location block twice in the same `server` context.

Example of invalid configuration:

```nginx
server {
    location / {
        root /var/www/html;
    }

    location / {  # ❌ Duplicate!
        proxy_pass http://backend;
    }
}
```

### Solution:

Combine the logic into one location block or use more specific patterns:

```nginx
server {
    # Serve static files
    location /static {
        root /var/www;
    }

    # Proxy everything else
    location / {
        proxy_pass http://backend;
    }
}
```

---

## Issue 1.3: Unknown Directive

### Problem:

```text
nginx: [emerg] unknown directive "proxy_cache_bypass"
in /etc/nginx/nginx.conf:45
```

### Root Cause:

The directive does not exist in your Nginx version, or Nginx was compiled without the required module.

### Solution:

**Check Nginx Version:**

```bash
nginx -V
```

Look for:

```text
--with-http_proxy_module
--with-http_cache_module
```

**Upgrade Nginx:**

If the module is missing, you may need to:

- Upgrade Nginx
- Recompile with the required module
- Use the official packages that include all standard modules

---

## Issue 1.4: Unexpected End of File

### Problem:

```text
nginx: [emerg] unexpected end of file,
expecting "}" in /etc/nginx/nginx.conf:89
```

### Root Cause:

Missing closing brace `}` in your configuration.

### Solution:

Validate your configuration:

```bash
nginx -t
```

Check for matching braces:

```nginx
http {
    server {
        location / {
            proxy_pass http://backend;
        }
    }  # ✅ Each block properly closed
}
```

**Tip:** Use a code editor with syntax highlighting to identify mismatched braces.

---

# Section 2: HTTP Error Codes

## Issue 2.1: 404 Not Found

### Problem:

```text
GET /images/logo.png

↓

404 Not Found
```

### Common Causes:

1. File does not exist
2. Incorrect `root` directive
3. Wrong location block
4. Typo in file path

### Debugging Steps:

**Step 1: Check the file exists**

```bash
ls -la /var/www/html/images/logo.png
```

**Step 2: Verify root directive**

```nginx
server {
    root /var/www/html;

    location /images {
        # Nginx looks for: /var/www/html/images/logo.png
    }
}
```

**Step 3: Check access log**

```bash
tail -f /var/log/nginx/access.log
```

Look for the requested path.

**Step 4: Check error log**

```bash
tail -f /var/log/nginx/error.log
```

Look for:

```text
open() "/var/www/html/images/logo.png" failed (2: No such file or directory)
```

### Solution:

Fix the root path or create the missing file.

---

## Issue 2.2: 403 Forbidden

### Problem:

```text
GET /admin

↓

403 Forbidden
```

### Common Causes:

| Cause | Description |
|-------|-------------|
| File permissions | Nginx user cannot read file |
| Directory permissions | Nginx user cannot access directory |
| Directory listing disabled | No index file and autoindex off |
| Explicit deny | `deny all` directive present |

### Debugging Steps:

**Step 1: Check file permissions**

```bash
ls -la /var/www/html/admin
```

Expected:

```text
drwxr-xr-x  nginx nginx  admin/
-rw-r--r--  nginx nginx  index.html
```

**Step 2: Check Nginx user**

```bash
ps aux | grep nginx
```

Look for:

```text
nginx: worker process
```

running as user `nginx` or `www-data`.

**Step 3: Fix permissions**

```bash
sudo chown -R nginx:nginx /var/www/html
sudo chmod -R 755 /var/www/html
```

**Step 4: Enable directory listing (if needed)**

```nginx
location /admin {
    autoindex on;
}
```

**Step 5: Check for deny directives**

```nginx
location /admin {
    deny all;  # ❌ This causes 403
}
```

---

## Issue 2.3: 502 Bad Gateway

### Problem:

```text
Browser → Nginx → Backend

                     ×

                 Unavailable
```

One of the **most common production errors**.

### Common Causes:

1. Backend service not running
2. Wrong `proxy_pass` address
3. Firewall blocking connections
4. Docker networking issue
5. Socket permission problem
6. Backend crashed

### Debugging Steps:

**Step 1: Check error log**

```bash
tail -f /var/log/nginx/error.log
```

Look for:

```text
connect() failed (111: Connection refused) while connecting to upstream
```

or

```text
upstream prematurely closed connection
```

**Step 2: Verify backend is running**

```bash
curl http://127.0.0.1:8000
```

If this fails, the backend is not running.

**Step 3: Check backend logs**

```bash
# For systemd services
sudo journalctl -u your-app -f

# For Docker
docker logs your-container -f
```

**Step 4: Verify proxy_pass configuration**

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;  # Verify address and port
}
```

**Step 5: Check if port is listening**

```bash
sudo netstat -tlnp | grep 8000
```

or

```bash
sudo ss -tlnp | grep 8000
```

Expected output:

```text
tcp   0   0   127.0.0.1:8000   0.0.0.0:*   LISTEN   1234/python
```

**Step 6: Docker-specific checks**

If using Docker networks:

```bash
docker network ls
docker network inspect bridge
```

Verify Nginx and backend are on the same network.

**Step 7: Test backend directly**

```bash
curl -I http://backend:8000
```

### Solution Examples:

**Backend not running:**

```bash
# Systemd
sudo systemctl start your-app

# Docker
docker start your-container
```

**Wrong address in proxy_pass:**

```nginx
# Before
proxy_pass http://localhost:8000;

# After (Docker)
proxy_pass http://app:8000;
```

---

## Issue 2.4: 504 Gateway Timeout

### Problem:

```text
Browser → Nginx → Backend

                  ⏱️

              Too Slow
```

### Root Cause:

Backend takes too long to respond.

### Common Causes:

- Slow database queries
- Long-running API calls
- Backend timeout
- Network latency
- Insufficient backend resources

### Solution:

**Increase Nginx timeouts:**

```nginx
location / {
    proxy_pass http://backend;
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
}
```

**Check backend performance:**

```bash
# Monitor backend response times
tail -f /var/log/nginx/access.log | grep "request_time"
```

**Add custom log format to track timing:**

```nginx
log_format timing '$request_time $upstream_response_time $request';
access_log /var/log/nginx/timing.log timing;
```

---

## Issue 2.5: 500 Internal Server Error

### Problem:

Application-level error passed through Nginx.

### Debugging Steps:

**Check application logs first:**

```bash
# Django
tail -f /var/log/django/error.log

# FastAPI (if using uvicorn)
tail -f /var/log/uvicorn/error.log

# Docker
docker logs app-container -f
```

**Check Nginx error log:**

```bash
tail -f /var/log/nginx/error.log
```

Look for upstream errors.

### Common Causes:

- Application exceptions
- Missing dependencies
- Database connection failures
- Incorrect environment variables
- File permission issues in application

---

# Section 3: SSL/TLS Issues

## Issue 3.1: SSL Certificate Errors

### Problem:

```text
ERR_CERT_AUTHORITY_INVALID
```

or

```text
Certificate not trusted
```

### Common Causes:

| Issue | Description |
|-------|-------------|
| Self-signed certificate | Not trusted by browsers |
| Expired certificate | Certificate validity period ended |
| Wrong domain | Certificate issued for different domain |
| Missing intermediate certificates | Incomplete certificate chain |

### Debugging Steps:

**Step 1: Verify certificate details**

```bash
openssl x509 -in /etc/ssl/certs/server.crt -text -noout
```

Check:

```text
Subject: CN=example.com
Validity
    Not Before: Jan 1 2026
    Not After : Dec 31 2026
```

**Step 2: Test SSL connection**

```bash
openssl s_client -connect example.com:443 -servername example.com
```

Look for:

```text
Verify return code: 0 (ok)
```

or errors like:

```text
Verify return code: 21 (unable to verify the first certificate)
```

**Step 3: Check certificate chain**

```bash
openssl s_client -connect example.com:443 -showcerts
```

You should see:

- Server certificate
- Intermediate certificate(s)
- Root certificate

**Step 4: Verify certificate matches private key**

```bash
openssl x509 -noout -modulus -in server.crt | openssl md5
openssl rsa -noout -modulus -in server.key | openssl md5
```

The MD5 hashes must match.

### Solutions:

**Use Let's Encrypt (Recommended):**

```bash
sudo certbot --nginx -d example.com
```

**Include intermediate certificates:**

```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/ssl/certs/fullchain.pem;  # Includes chain
    ssl_certificate_key /etc/ssl/private/privkey.pem;
}
```

---

## Issue 3.2: Mixed Content Warnings

### Problem:

HTTPS page loading HTTP resources:

```text
https://example.com

↓

<img src="http://example.com/logo.png">  ❌

Mixed Content Warning
```

### Solution:

**Use protocol-relative URLs:**

```html
<img src="//example.com/logo.png">
```

**Or configure HTTPS redirect:**

```nginx
server {
    listen 80;
    return 301 https://$host$request_uri;
}
```

**Add HSTS header:**

```nginx
add_header Strict-Transport-Security "max-age=31536000" always;
```

---

## Issue 3.3: SSL Handshake Failure

### Problem:

```text
SSL_do_handshake() failed
```

### Common Causes:

- Protocol version mismatch
- Cipher suite incompatibility
- Client using outdated browser

### Solution:

**Configure modern SSL protocols:**

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
```

**Test SSL configuration:**

```bash
nmap --script ssl-enum-ciphers -p 443 example.com
```

---

# Section 4: Docker and Container Issues

## Issue 4.1: Container Immediately Exits

### Problem:

```bash
docker ps
```

Shows no running Nginx container.

### Debugging Steps:

**Step 1: Check container logs**

```bash
docker logs nginx-container
```

Look for:

```text
nginx: [emerg] host not found in upstream "backend"
```

or

```text
nginx: configuration file test failed
```

**Step 2: View all containers including stopped**

```bash
docker ps -a
```

**Step 3: Inspect container**

```bash
docker inspect nginx-container
```

### Common Solutions:

**Configuration error:**

```bash
# Test configuration locally first
docker run --rm -v $(pwd)/nginx.conf:/etc/nginx/nginx.conf nginx nginx -t
```

**Missing upstream:**

```yaml
# docker-compose.yml
services:
  nginx:
    depends_on:
      - backend  # ✅ Ensures backend starts first
```

---

## Issue 4.2: Cannot Connect to Backend Service

### Problem:

```text
502 Bad Gateway
```

when Nginx is in Docker.

### Root Cause:

Using `localhost` or `127.0.0.1` in `proxy_pass` within Docker containers refers to the **container itself**, not the host machine.

### Solution:

**Use Docker service names:**

```nginx
# ❌ Wrong in Docker
proxy_pass http://127.0.0.1:8000;

# ✅ Correct in Docker
proxy_pass http://backend:8000;
```

**Docker Compose example:**

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    networks:
      - app-network

  backend:
    image: python:3.11
    networks:
      - app-network

networks:
  app-network:
```

Nginx configuration:

```nginx
server {
    location / {
        proxy_pass http://backend:8000;  # Uses service name
    }
}
```

---

## Issue 4.3: Volume Mount Issues

### Problem:

Configuration changes not reflected in container.

### Debugging Steps:

**Step 1: Verify mount**

```bash
docker inspect nginx-container | grep Mounts -A 20
```

**Step 2: Check file inside container**

```bash
docker exec nginx-container cat /etc/nginx/conf.d/default.conf
```

**Step 3: Reload Nginx**

```bash
docker exec nginx-container nginx -s reload
```

### Solution:

**Correct volume mount:**

```bash
docker run -d \
  -v $(pwd)/nginx.conf:/etc/nginx/nginx.conf:ro \
  -v $(pwd)/conf.d:/etc/nginx/conf.d:ro \
  nginx:alpine
```

**Docker Compose:**

```yaml
services:
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./conf.d:/etc/nginx/conf.d:ro
```

---

## Issue 4.4: Port Already in Use

### Problem:

```text
Error starting userland proxy: listen tcp 0.0.0.0:80:
bind: address already in use
```

### Solution:

**Find process using port:**

```bash
# Linux
sudo lsof -i :80

# Windows
netstat -ano | findstr :80
```

**Stop conflicting service:**

```bash
sudo systemctl stop apache2
# or
docker stop other-container
```

**Use different port:**

```bash
docker run -p 8080:80 nginx:alpine
```

---

# Section 5: Kubernetes and Ingress Issues

## Issue 5.1: Ingress Not Working

### Problem:

Cannot access application through Ingress.

### Debugging Steps:

**Step 1: Check Ingress status**

```bash
kubectl get ingress
```

Expected:

```text
NAME      CLASS    HOSTS           ADDRESS        PORTS
my-app    nginx    example.com     10.0.1.100     80
```

**Step 2: Describe Ingress**

```bash
kubectl describe ingress my-app
```

Look for events and errors.

**Step 3: Check Ingress Controller logs**

```bash
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller -f
```

**Step 4: Verify Service exists**

```bash
kubectl get svc
```

**Step 5: Test Service directly**

```bash
kubectl port-forward svc/my-app 8080:80
curl localhost:8080
```

### Common Issues:

**Missing Ingress Class:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
spec:
  ingressClassName: nginx  # ✅ Required
  rules:
    - host: example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-app
                port:
                  number: 80
```

**Wrong Service Name:**

Verify the service name matches:

```bash
kubectl get svc
```

---

## Issue 5.2: 503 Service Unavailable in Kubernetes

### Problem:

Ingress returns 503 error.

### Root Cause:

Backend Pods are not ready or not running.

### Debugging Steps:

**Check Pod status:**

```bash
kubectl get pods
```

Look for:

```text
NAME        READY   STATUS    RESTARTS
my-app-0    0/1     Running   0
```

**Check Pod logs:**

```bash
kubectl logs my-app-0
```

**Check endpoints:**

```bash
kubectl get endpoints my-app
```

Expected:

```text
NAME     ENDPOINTS
my-app   10.244.0.5:80
```

If endpoints are empty, Pods are not ready.

**Check readiness probe:**

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
        - name: app
          readinessProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10
```

---

## Issue 5.3: Ingress Certificate Issues

### Problem:

SSL certificate not working with Ingress.

### Solution:

**Use cert-manager with Let's Encrypt:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
    - hosts:
        - example.com
      secretName: example-tls
  rules:
    - host: example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-app
                port:
                  number: 80
```

**Check certificate status:**

```bash
kubectl get certificate
```

**Check cert-manager logs:**

```bash
kubectl logs -n cert-manager deployment/cert-manager -f
```

---

# Section 6: Performance Issues

## Issue 6.1: High CPU Usage

### Problem:

Nginx consuming excessive CPU resources.

### Debugging Steps:

**Monitor CPU:**

```bash
top -p $(pgrep nginx)
```

**Check active connections:**

```bash
# View Nginx stub_status
curl http://localhost/nginx_status
```

Expected output:

```text
Active connections: 291
server accepts handled requests
 16630 16630 31070
Reading: 6 Writing: 179 Waiting: 106
```

**Check for slow requests:**

```nginx
# Add to nginx.conf
log_format timing '$request_time $upstream_response_time $request';
access_log /var/log/nginx/timing.log timing;
```

**Analyze slow requests:**

```bash
awk '{if ($1 > 1.0) print $0}' /var/log/nginx/timing.log
```

### Solutions:

**Enable caching:**

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m;

server {
    location / {
        proxy_cache my_cache;
        proxy_cache_valid 200 1h;
        proxy_pass http://backend;
    }
}
```

**Rate limiting:**

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

server {
    location /api {
        limit_req zone=api burst=20;
    }
}
```

**Optimize worker configuration:**

```nginx
worker_processes auto;
worker_connections 4096;
```

---

## Issue 6.2: Memory Leaks

### Problem:

Nginx memory usage continuously grows.

### Debugging Steps:

**Monitor memory:**

```bash
watch -n 1 'ps aux | grep nginx'
```

**Check for file descriptor leaks:**

```bash
lsof -p $(pgrep nginx) | wc -l
```

### Solutions:

**Configure buffer limits:**

```nginx
client_body_buffer_size 128k;
client_max_body_size 10m;
client_header_buffer_size 1k;
large_client_header_buffers 4 8k;
```

**Limit connection lifetime:**

```nginx
keepalive_timeout 30;
keepalive_requests 100;
```

**Graceful reload instead of restart:**

```bash
nginx -s reload  # Doesn't interrupt connections
```

---

## Issue 6.3: Slow Response Times

### Problem:

High latency in responses.

### Debugging Steps:

**Add detailed logging:**

```nginx
log_format detailed '$remote_addr - $request_time - $upstream_response_time - $request';
access_log /var/log/nginx/detailed.log detailed;
```

**Analyze logs:**

```bash
# Find slowest requests
sort -n -k2 /var/log/nginx/detailed.log | tail -20
```

**Check backend performance:**

```bash
curl -w "\nTime: %{time_total}s\n" http://localhost:8000/api/test
```

### Solutions:

**Enable compression:**

```nginx
gzip on;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript;
```

**Enable caching:**

```nginx
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

**Use upstream keepalive:**

```nginx
upstream backend {
    server app1:8000;
    server app2:8000;
    keepalive 32;
}
```

---

# Section 7: Network and Connectivity

## Issue 7.1: DNS Resolution Failures

### Problem:

```text
nginx: [emerg] host not found in upstream "api.example.com"
```

### Debugging Steps:

**Test DNS resolution:**

```bash
nslookup api.example.com
```

**Check resolver configuration:**

```bash
cat /etc/resolv.conf
```

**Test from container:**

```bash
docker exec nginx-container nslookup api.example.com
```

### Solutions:

**Configure explicit resolver:**

```nginx
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

server {
    location / {
        set $backend "http://api.example.com";
        proxy_pass $backend;
    }
}
```

**Use IP addresses for critical services:**

```nginx
upstream backend {
    server 10.0.1.100:8000;
    server 10.0.1.101:8000;
}
```

---

## Issue 7.2: Connection Timeouts

### Problem:

```text
upstream timed out (110: Connection timed out)
```

### Debugging Steps:

**Test connectivity:**

```bash
telnet backend-server 8000
```

**Check firewall:**

```bash
# Linux
sudo iptables -L -n

# Check if port is accessible
nc -zv backend-server 8000
```

**Check network latency:**

```bash
ping backend-server
traceroute backend-server
```

### Solutions:

**Increase timeouts:**

```nginx
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
```

**Configure keepalive:**

```nginx
upstream backend {
    server app:8000;
    keepalive 16;
    keepalive_timeout 60s;
}
```

---

## Issue 7.3: Connection Refused

### Problem:

```text
connect() failed (111: Connection refused)
```

### Root Cause:

Backend service not listening on the specified port.

### Debugging Steps:

**Check if service is running:**

```bash
sudo systemctl status your-app
```

**Verify listening ports:**

```bash
sudo netstat -tlnp | grep 8000
```

Expected:

```text
tcp  0  0  0.0.0.0:8000  0.0.0.0:*  LISTEN  1234/python
```

**Docker-specific:**

```bash
docker ps
docker logs backend-container
```

### Solution:

Start the backend service and ensure it's listening on the correct interface:

```python
# Python (FastAPI/Flask)
# ❌ Wrong - only localhost
app.run(host="127.0.0.1", port=8000)

# ✅ Correct - all interfaces
app.run(host="0.0.0.0", port=8000)
```

---

# Section 8: Real-World Debugging Scenarios

## Scenario 8.1: Intermittent 502 Errors

### Problem:

502 errors occur randomly, not consistently.

### Investigation Process:

**Step 1: Monitor patterns**

```bash
grep "502" /var/log/nginx/access.log | wc -l
```

**Step 2: Check upstream health**

```nginx
upstream backend {
    server app1:8000 max_fails=3 fail_timeout=30s;
    server app2:8000 max_fails=3 fail_timeout=30s;
}
```

**Step 3: Enable upstream logging**

```nginx
log_format upstreamlog '$remote_addr - $upstream_addr - $upstream_status - $request_time';
access_log /var/log/nginx/upstream.log upstreamlog;
```

**Step 4: Analyze logs**

```bash
grep "502" /var/log/nginx/access.log | \
awk '{print $4}' | \
sort | uniq -c
```

### Common Causes:

- Backend server overload
- Connection pool exhaustion
- Memory issues in application
- Database connection limits

### Solution:

**Implement health checks:**

```nginx
upstream backend {
    server app1:8000;
    server app2:8000;
    
    check interval=3000 rise=2 fall=5 timeout=1000 type=http;
    check_http_send "GET /health HTTP/1.0\r\n\r\n";
    check_http_expect_alive http_2xx http_3xx;
}
```

**Scale backend services:**

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3  # Multiple instances
```

---

## Scenario 8.2: Static Files Not Loading After Deployment

### Problem:

After deployment, CSS and JavaScript files return 404.

### Investigation Process:

**Step 1: Check browser console**

```text
Failed to load resource: /static/css/main.css 404
```

**Step 2: Verify file exists**

```bash
ls -la /var/www/static/css/main.css
```

**Step 3: Check Nginx configuration**

```nginx
location /static {
    alias /var/www/static;
    expires 1y;
}
```

**Step 4: Test direct access**

```bash
curl -I http://localhost/static/css/main.css
```

### Common Mistakes:

**Using `root` instead of `alias`:**

```nginx
# ❌ Wrong - looks for /var/www/static/static/
location /static {
    root /var/www/static;
}

# ✅ Correct - looks for /var/www/static/
location /static {
    alias /var/www/static/;  # Note trailing slash
}
```

### Solution:

```nginx
location /static/ {
    alias /var/www/static/;
    access_log off;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

---

## Scenario 8.3: WebSocket Connection Failing

### Problem:

WebSocket connections immediately close or fail to upgrade.

### Investigation Process:

**Check browser console:**

```text
WebSocket connection failed: Error during WebSocket handshake
```

**Check Nginx error log:**

```bash
tail -f /var/log/nginx/error.log
```

### Solution:

**Configure WebSocket support:**

```nginx
location /ws {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    
    proxy_connect_timeout 7d;
    proxy_send_timeout 7d;
    proxy_read_timeout 7d;
}
```

**Key points:**

- `proxy_http_version 1.1` - Required for WebSocket
- `Upgrade` and `Connection` headers - Enable protocol upgrade
- Long timeouts - WebSocket connections are persistent

---

## Scenario 8.4: Rate Limiting Blocking Legitimate Users

### Problem:

Users report being blocked after normal usage.

### Investigation Process:

**Check error log:**

```bash
grep "limiting requests" /var/log/nginx/error.log
```

Output:

```text
limiting requests, excess: 5.000 by zone "api"
```

**Review rate limit configuration:**

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

server {
    location /api {
        limit_req zone=api burst=5;  # Too strict
    }
}
```

### Solution:

**Adjust burst and nodelay:**

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

server {
    location /api {
        limit_req zone=api burst=20 nodelay;
        limit_req_status 429;
    }
}
```

**Use better key for rate limiting:**

```nginx
# Rate limit by user session instead of IP
limit_req_zone $cookie_sessionid zone=api:10m rate=10r/s;
```

**Whitelist trusted IPs:**

```nginx
geo $limit {
    default 1;
    10.0.0.0/8 0;  # Internal network
    192.168.1.0/24 0;  # Office network
}

map $limit $limit_key {
    0 "";
    1 $binary_remote_addr;
}

limit_req_zone $limit_key zone=api:10m rate=10r/s;
```

---

# Section 9: Diagnostic Commands Reference

## Essential Commands

### Validate Configuration

```bash
nginx -t
```

### Reload Without Downtime

```bash
nginx -s reload
# or
sudo systemctl reload nginx
```

### View Running Processes

```bash
ps aux | grep nginx
```

### Check Listening Ports

```bash
# Linux
sudo netstat -tlnp | grep nginx
sudo ss -tlnp | grep nginx

# Test specific port
nc -zv localhost 80
```

### Monitor Logs in Real-Time

```bash
# Access log
tail -f /var/log/nginx/access.log

# Error log
tail -f /var/log/nginx/error.log

# Filter errors
tail -f /var/log/nginx/error.log | grep -i error

# Show only 502 errors
grep "502" /var/log/nginx/access.log | tail -20
```

### Test HTTP Requests

```bash
# Basic request
curl -I http://localhost

# Verbose output
curl -v https://example.com

# Follow redirects
curl -L https://example.com

# Show timing
curl -w "\nTime: %{time_total}s\n" http://localhost/api

# Test specific host header
curl -H "Host: example.com" http://localhost
```

### SSL/TLS Testing

```bash
# Test SSL connection
openssl s_client -connect example.com:443 -servername example.com

# Check certificate expiration
echo | openssl s_client -connect example.com:443 2>/dev/null | \
openssl x509 -noout -dates

# View certificate details
openssl x509 -in cert.pem -text -noout

# Test specific SSL protocol
openssl s_client -connect example.com:443 -tls1_2
```

### Docker Commands

```bash
# View logs
docker logs nginx-container -f

# Execute command in container
docker exec nginx-container nginx -t

# Shell access
docker exec -it nginx-container sh

# Inspect container
docker inspect nginx-container

# View networks
docker network ls
docker network inspect bridge

# Check resource usage
docker stats nginx-container
```

### Kubernetes Commands

```bash
# Get resources
kubectl get pods
kubectl get svc
kubectl get ingress

# Describe resources
kubectl describe ingress my-app
kubectl describe pod my-app-0

# View logs
kubectl logs pod-name -f
kubectl logs -l app=nginx -f  # All pods with label

# Port forward
kubectl port-forward pod/my-app-0 8080:80

# Execute command in pod
kubectl exec -it pod-name -- nginx -t

# Check endpoints
kubectl get endpoints
```

---

# Section 10: Monitoring and Metrics

## Enable Stub Status Module

```nginx
server {
    listen 80;
    server_name localhost;

    location /nginx_status {
        stub_status;
        access_log off;
        allow 127.0.0.1;
        deny all;
    }
}
```

**Access metrics:**

```bash
curl http://localhost/nginx_status
```

**Output:**

```text
Active connections: 291
server accepts handled requests
 16630 16630 31070
Reading: 6 Writing: 179 Waiting: 106
```

**Metrics explanation:**

- **Active connections:** Currently open connections
- **Accepts:** Total accepted connections
- **Handled:** Total handled connections
- **Requests:** Total client requests
- **Reading:** Reading request headers
- **Writing:** Sending response
- **Waiting:** Keepalive connections

---

## Custom Log Format for Monitoring

```nginx
log_format monitoring '$remote_addr - $request_time - $upstream_response_time '
                      '- $status - "$request" - $body_bytes_sent';

access_log /var/log/nginx/monitoring.log monitoring;
```

**Analyze performance:**

```bash
# Average request time
awk '{sum+=$3; count++} END {print "Avg:", sum/count}' /var/log/nginx/monitoring.log

# Requests by status code
awk '{print $7}' /var/log/nginx/monitoring.log | sort | uniq -c

# Slowest requests
sort -n -k3 /var/log/nginx/monitoring.log | tail -20
```

---

## Prometheus Integration

```nginx
# Install nginx-prometheus-exporter
# https://github.com/nginxinc/nginx-prometheus-exporter

# Run exporter
nginx-prometheus-exporter -nginx.scrape-uri http://localhost/nginx_status
```

**Docker deployment:**

```yaml
version: '3.8'
services:
  nginx-exporter:
    image: nginx/nginx-prometheus-exporter:latest
    ports:
      - "9113:9113"
    command:
      - -nginx.scrape-uri=http://nginx/nginx_status
```

---

# Section 11: Troubleshooting Checklist

## Initial Assessment

- [ ] Is Nginx running?
- [ ] Is configuration valid? (`nginx -t`)
- [ ] Are logs accessible?
- [ ] Can you reproduce the issue?

## Configuration Issues

- [ ] Check for syntax errors
- [ ] Verify directive contexts
- [ ] Validate file paths
- [ ] Check for duplicate blocks
- [ ] Verify module availability

## HTTP Error Troubleshooting

### For 404 Errors:
- [ ] File exists at expected path
- [ ] Root/alias directive correct
- [ ] File permissions allow read access
- [ ] No typos in location block

### For 403 Errors:
- [ ] File permissions (644 for files, 755 for directories)
- [ ] Nginx user has access
- [ ] No `deny` directives blocking access
- [ ] Directory index exists or autoindex enabled

### For 502 Errors:
- [ ] Backend service running
- [ ] Correct proxy_pass address
- [ ] Network connectivity to backend
- [ ] Backend listening on correct port
- [ ] Firewall not blocking connections
- [ ] Check Docker/K8s networking

### For 504 Errors:
- [ ] Backend responds within timeout
- [ ] Timeout values appropriately configured
- [ ] Backend not overloaded
- [ ] No slow database queries
- [ ] Check upstream_response_time in logs

## SSL/TLS Issues

- [ ] Certificate files exist and readable
- [ ] Certificate matches domain
- [ ] Certificate not expired
- [ ] Certificate chain complete
- [ ] Private key matches certificate
- [ ] SSL protocols properly configured

## Docker/Container Issues

- [ ] Container running (`docker ps`)
- [ ] Configuration mounted correctly
- [ ] Using service names not localhost
- [ ] Containers on same network
- [ ] Ports properly exposed
- [ ] Check container logs

## Performance Issues

- [ ] Monitor CPU usage
- [ ] Monitor memory usage
- [ ] Check active connections
- [ ] Review request times
- [ ] Analyze slow queries
- [ ] Verify caching working
- [ ] Check for rate limiting

---

# Section 12: Best Practices for Production

## Before Deployment

```bash
# Always test configuration
nginx -t

# Test in staging first
# Deploy during low-traffic periods
# Have rollback plan ready
```

## Configuration Management

```nginx
# Use includes for organization
http {
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}

# Version control configurations
git add nginx.conf
git commit -m "Update proxy timeouts"
```

## Backup Strategy

```bash
# Backup before changes
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d)

# Automated backups
0 2 * * * tar -czf /backups/nginx-$(date +\%Y\%m\%d).tar.gz /etc/nginx/
```

## Monitoring Setup

```bash
# Set up log rotation
cat > /etc/logrotate.d/nginx << EOF
/var/log/nginx/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        nginx -s reload > /dev/null 2>&1
    endscript
}
EOF
```

## Security Hardening

```nginx
# Hide version
server_tokens off;

# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;

# Rate limiting
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;

# SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
```

---

# Section 13: Emergency Response Procedures

## Nginx Won't Start

```bash
# Step 1: Check configuration
nginx -t

# Step 2: Check if port is in use
sudo lsof -i :80

# Step 3: Check error log
sudo tail -50 /var/log/nginx/error.log

# Step 4: Start with verbose output
sudo nginx -g 'daemon off;'
```

## Site Down - Quick Recovery

```bash
# Step 1: Restart Nginx
sudo systemctl restart nginx

# Step 2: Check status
sudo systemctl status nginx

# Step 3: If failed, restore backup
sudo cp /etc/nginx/nginx.conf.backup /etc/nginx/nginx.conf
sudo systemctl start nginx

# Step 4: Verify site accessible
curl -I http://localhost
```

## High Load Emergency

```bash
# Step 1: Check connections
curl http://localhost/nginx_status

# Step 2: Identify top IPs
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10

# Step 3: Block abusive IP
# Add to nginx.conf
deny 1.2.3.4;

# Step 4: Reload
nginx -s reload

# Step 5: Enable rate limiting if not already
# See rate limiting section above
```

## SSL Certificate Expired

```bash
# Step 1: Verify expiration
openssl x509 -in /etc/ssl/certs/server.crt -noout -dates

# Step 2: Renew with Let's Encrypt
sudo certbot renew

# Step 3: Reload Nginx
sudo systemctl reload nginx

# Step 4: Verify
curl -I https://example.com
```

---

# Section 14: Advanced Debugging Techniques

## Enable Debug Logging

```nginx
error_log /var/log/nginx/debug.log debug;
```

**Warning:** Debug logs are extremely verbose. Use only temporarily.

```bash
# View debug log
tail -f /var/log/nginx/debug.log

# Disable after debugging
# Change back to: error_log /var/log/nginx/error.log warn;
```

## Trace Requests

```nginx
log_format trace '$time_local - $request_id - $remote_addr - $request - '
                 '$status - $request_time - $upstream_response_time';

access_log /var/log/nginx/trace.log trace;
```

## Network Packet Capture

```bash
# Capture traffic on port 80
sudo tcpdump -i any port 80 -w nginx.pcap

# View captured traffic
tcpdump -r nginx.pcap -A

# Use wireshark for detailed analysis
wireshark nginx.pcap
```

## Strace Nginx Process

```bash
# Attach to worker process
sudo strace -p $(pgrep -f "nginx: worker process") -f

# Save to file
sudo strace -p $(pgrep -f "nginx: worker process") -f -o nginx-strace.log
```

**Use cases:**

- Identify which files Nginx is trying to access
- Debug permission issues
- Find configuration file load order

---

# Section 15: Common Configuration Mistakes

## Mistake 1: Mixing root and alias

```nginx
# ❌ Wrong
location /static {
    root /var/www/static;  # Looks for /var/www/static/static/
}

# ✅ Correct
location /static {
    alias /var/www/static/;  # Looks for /var/www/static/
}
```

## Mistake 2: Missing trailing slash in proxy_pass

```nginx
# ❌ Wrong - passes /api/users to backend
location /api/ {
    proxy_pass http://backend;
}

# ✅ Correct - passes /users to backend
location /api/ {
    proxy_pass http://backend/;
}
```

## Mistake 3: Not using $host in proxy headers

```nginx
# ❌ Wrong
proxy_set_header Host example.com;  # Hardcoded

# ✅ Correct
proxy_set_header Host $host;  # Dynamic
```

## Mistake 4: Forgetting to reload after changes

```bash
# ❌ Wrong
vim /etc/nginx/nginx.conf
# Changes not applied!

# ✅ Correct
vim /etc/nginx/nginx.conf
nginx -t
nginx -s reload
```

## Mistake 5: Using same location twice

```nginx
# ❌ Wrong - nginx: [emerg] duplicate location
location / {
    root /var/www/html;
}

location / {
    proxy_pass http://backend;
}

# ✅ Correct - use specific paths
location /static {
    root /var/www;
}

location / {
    proxy_pass http://backend;
}
```

---

# Section 16: Troubleshooting Tools

## Essential Tools

| Tool | Purpose | Example |
|------|---------|---------|
| `curl` | Test HTTP requests | `curl -I http://localhost` |
| `openssl` | Test SSL/TLS | `openssl s_client -connect example.com:443` |
| `tcpdump` | Packet capture | `tcpdump -i any port 80` |
| `strace` | System call tracing | `strace -p <pid>` |
| `lsof` | List open files | `lsof -i :80` |
| `netstat` | Network statistics | `netstat -tlnp` |
| `ss` | Socket statistics | `ss -tlnp` |
| `htop` | Process monitoring | `htop` |
| `ab` | Apache benchmark | `ab -n 1000 -c 10 http://localhost/` |
| `wrk` | HTTP benchmarking | `wrk -t4 -c100 http://localhost/` |

## Log Analysis Tools

```bash
# goaccess - Real-time web log analyzer
goaccess /var/log/nginx/access.log -o report.html

# ngxtop - Real-time metrics
pip install ngxtop
ngxtop -l /var/log/nginx/access.log

# AWK for custom analysis
# Top 10 IPs by request count
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10

# Top 10 requested URLs
awk '{print $7}' access.log | sort | uniq -c | sort -rn | head -10

# Requests by status code
awk '{print $9}' access.log | sort | uniq -c

# Average response time
awk '{sum+=$NF; count++} END {print sum/count}' access.log
```

---

# Section 17: Interview Preparation

## Beginner Questions

**Q: How do you check if Nginx is running?**
```bash
sudo systemctl status nginx
# or
ps aux | grep nginx
```

**Q: How do you validate Nginx configuration?**
```bash
nginx -t
```

**Q: What's the difference between reload and restart?**
- **Reload:** Graceful, no downtime, keeps existing connections
- **Restart:** Stops and starts, drops connections

**Q: Where are Nginx logs located?**
```text
/var/log/nginx/access.log
/var/log/nginx/error.log
```

## Intermediate Questions

**Q: How would you troubleshoot a 502 Bad Gateway error?**

1. Check error log: `tail -f /var/log/nginx/error.log`
2. Verify backend running: `curl http://127.0.0.1:8000`
3. Check proxy_pass configuration
4. Verify network connectivity
5. Check backend logs
6. Review firewall rules

**Q: How do you debug SSL certificate issues?**
```bash
# Check certificate
openssl x509 -in cert.pem -text -noout

# Test SSL connection
openssl s_client -connect example.com:443

# Verify certificate dates
openssl x509 -in cert.pem -noout -dates
```

**Q: How would you handle high CPU usage in Nginx?**

1. Monitor with `top` or `htop`
2. Check active connections via stub_status
3. Review access logs for traffic patterns
4. Enable caching if not present
5. Implement rate limiting
6. Optimize worker configuration

## Advanced Questions

**Q: Explain how you would troubleshoot intermittent 502 errors.**

1. Enable upstream logging
2. Monitor patterns in access logs
3. Check backend health and capacity
4. Review backend application logs
5. Implement health checks
6. Consider connection pool exhaustion
7. Check for memory/resource limits
8. Scale backend if needed

**Q: How do you debug Docker networking issues with Nginx?**

1. Verify containers on same network
2. Use service names instead of localhost
3. Check Docker network configuration
4. Test connectivity between containers
5. Review Docker logs
6. Verify port mappings
7. Check firewall rules

**Q: Describe your approach to diagnosing performance issues.**

1. Establish baseline metrics
2. Enable detailed logging with timing
3. Analyze request/response times
4. Identify bottlenecks (Nginx vs backend)
5. Check resource utilization
6. Review cache hit rates
7. Implement monitoring
8. Load test before/after changes

---

# Summary

This troubleshooting guide covers:

✅ **Configuration errors** - Context issues, syntax errors, module problems
✅ **HTTP errors** - 404, 403, 502, 504, 500 with debugging steps
✅ **SSL/TLS issues** - Certificate validation, handshake failures
✅ **Docker/Kubernetes** - Container networking, volume mounts, Ingress
✅ **Performance** - High CPU, memory leaks, slow responses
✅ **Network issues** - DNS, timeouts, connection failures
✅ **Real-world scenarios** - Intermittent errors, WebSocket issues
✅ **Diagnostic commands** - Complete reference of troubleshooting tools
✅ **Monitoring** - Metrics, logging, alerting
✅ **Best practices** - Production deployment, security, backups
✅ **Emergency procedures** - Quick recovery steps

---

# Key Takeaways

- **Always validate configuration** with `nginx -t` before reloading
- **Check logs first** - error.log is your best friend
- **Follow a systematic approach** - gather information before making changes
- **Test in staging** before production deployment
- **Monitor continuously** - don't wait for issues to occur
- **Document solutions** - build your own troubleshooting playbook
- **Keep backups** - configuration and certificates
- **Use proper tools** - leverage curl, openssl, tcpdump, logs
- **Understand the stack** - Nginx is often just one piece of the puzzle
- **Practice proactive maintenance** - monitoring, log rotation, security updates

---

**Remember:** Most production issues can be quickly diagnosed by systematically checking configuration, logs, backend services, and network connectivity. Stay calm, follow the process, and document your findings.

---

*Last Updated: 2026*
*Created by: aranya majumdar*
