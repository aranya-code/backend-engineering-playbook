# Overview

This chapter serves as a quick reference for the most commonly used Nginx directives, commands, configuration snippets, status codes, and production best practices.

Use this chapter whenever you need a quick reminder instead of reading the full documentation.

---

# Default Locations

| Purpose | Linux Path |
|----------|------------|
| Main Configuration | `/etc/nginx/nginx.conf` |
| Site Configuration | `/etc/nginx/conf.d/` or `/etc/nginx/sites-enabled/` |
| Access Log | `/var/log/nginx/access.log` |
| Error Log | `/var/log/nginx/error.log` |
| SSL Certificates | `/etc/ssl/certs/` |
| Private Keys | `/etc/ssl/private/` |

---

# Most Common Commands

## Check Version

```bash
nginx -v
```

---

## Detailed Build Information

```bash
nginx -V
```

---

## Validate Configuration

```bash
nginx -t
```

---

## Reload Configuration

```bash
sudo systemctl reload nginx
```

or

```bash
nginx -s reload
```

---

## Restart Nginx

```bash
sudo systemctl restart nginx
```

---

## Stop Nginx

```bash
sudo systemctl stop nginx
```

---

## Check Status

```bash
sudo systemctl status nginx
```

---

# Configuration Structure

```text
nginx.conf

│

├── events

├── http

│     ├── upstream

│     ├── server

│     │      └── location

│     └── include
```

---

# Essential Directives

## Server Block

```nginx
server {

}
```

Defines a virtual host.

---

## Location Block

```nginx
location / {

}
```

Matches incoming requests.

---

## Listen

```nginx
listen 80;
```

Specifies the listening port.

---

## Server Name

```nginx
server_name example.com;
```

Defines the hostname.

---

## Root

```nginx
root /var/www/html;
```

Sets the document root.

---

## Index

```nginx
index index.html;
```

Specifies the default file.

---

# Reverse Proxy

```nginx
location / {

    proxy_pass http://backend;

}
```

---

# Load Balancer

```nginx
upstream backend {

    server app1:8000;

    server app2:8000;

}
```

---

# HTTPS

```nginx
listen 443 ssl;

ssl_certificate server.crt;

ssl_certificate_key server.key;
```

---

# HTTP to HTTPS Redirect

```nginx
server {

    listen 80;

    return 301 https://$host$request_uri;

}
```

---

# Static Files

```nginx
location /static {

    root /var/www;
}
```

---

# Gzip Compression

```nginx
gzip on;

gzip_comp_level 6;
```

---

# Browser Cache

```nginx
expires 30d;

add_header Cache-Control "public";
```

---

# Proxy Cache

```nginx
proxy_cache API_CACHE;
```

---

# FastCGI Cache

```nginx
fastcgi_cache FASTCGI_CACHE;
```

---

# Security Headers

```nginx
add_header X-Frame-Options "DENY";

add_header X-Content-Type-Options "nosniff";

add_header Strict-Transport-Security "max-age=31536000" always;
```

---

# Hide Version

```nginx
server_tokens off;
```

---

# Disable Directory Listing

```nginx
autoindex off;
```

---

# Upload Size

```nginx
client_max_body_size 20M;
```

---

# Worker Processes

```nginx
worker_processes auto;
```

---

# Worker Connections

```nginx
worker_connections 4096;
```

---

# Sendfile

```nginx
sendfile on;
```

---

# Keepalive

```nginx
keepalive_timeout 65;
```

---

# Common Variables

| Variable | Description |
|----------|-------------|
| `$host` | Hostname |
| `$request_uri` | Complete URI |
| `$remote_addr` | Client IP |
| `$request_method` | HTTP Method |
| `$status` | Response Status |
| `$request_time` | Processing Time |
| `$body_bytes_sent` | Response Size |
| `$http_user_agent` | Browser |
| `$upstream_addr` | Backend Server |
| `$upstream_response_time` | Backend Response Time |

---

# Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 301 | Permanent Redirect |
| 302 | Temporary Redirect |
| 304 | Not Modified |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |
| 502 | Bad Gateway |
| 503 | Service Unavailable |
| 504 | Gateway Timeout |

---

# Common Log Locations

```text
/var/log/nginx/access.log

/var/log/nginx/error.log
```

---

# Docker Commands

View logs

```bash
docker logs nginx
```

Enter container

```bash
docker exec -it nginx bash
```

Test configuration

```bash
docker exec nginx nginx -t
```

Reload

```bash
docker exec nginx nginx -s reload
```

---

# Kubernetes Commands

View Pods

```bash
kubectl get pods
```

View Services

```bash
kubectl get svc
```

View Ingress

```bash
kubectl get ingress
```

View Logs

```bash
kubectl logs pod-name
```

Describe Resource

```bash
kubectl describe pod pod-name
```

---

# Troubleshooting Commands

Validate configuration

```bash
nginx -t
```

Check listening ports

```bash
ss -tulpn
```

Find process using port

```bash
lsof -i :80
```

Check DNS

```bash
dig example.com
```

Test HTTPS

```bash
openssl s_client -connect example.com:443
```

Test Response

```bash
curl -I https://example.com
```

Verbose Request

```bash
curl -v https://example.com
```

---

# Production Checklist

| Item | Recommended |
|------|-------------|
| HTTPS | ✅ |
| TLS 1.2 / TLS 1.3 | ✅ |
| HTTP → HTTPS Redirect | ✅ |
| Reverse Proxy | ✅ |
| Browser Cache | ✅ |
| Proxy Cache | ✅ |
| Gzip Compression | ✅ |
| Static File Serving | ✅ |
| Security Headers | ✅ |
| Rate Limiting | ✅ |
| Logging | ✅ |
| Monitoring | ✅ |
| Load Balancing | ✅ |
| Docker | ✅ |
| Kubernetes Ingress | ✅ |

---

# Architecture Cheat Sheet

## Reverse Proxy

```text
Client

↓

Nginx

↓

Backend
```

---

## Load Balancer

```text
Client

↓

Nginx

↓

App1

App2

App3
```

---

## Docker Deployment

```text
Internet

↓

Nginx

↓

Application

↓

Database
```

---

## Kubernetes Deployment

```text
Internet

↓

Ingress

↓

Service

↓

Pods
```

---

# Best Practices

- Always validate configuration using `nginx -t`.
- Use `reload` instead of `restart` whenever possible.
- Enable HTTPS using TLS 1.2 or TLS 1.3.
- Serve static assets directly through Nginx.
- Enable Gzip or Brotli compression.
- Configure Browser Cache and Proxy Cache appropriately.
- Monitor Access and Error Logs regularly.
- Keep Nginx updated with the latest stable release.
- Use Docker or Kubernetes for modern deployments.
- Store secrets and certificates securely.

---

# One-Page Interview Revision

Remember these core concepts:

- Nginx uses an **event-driven architecture**.
- A **Reverse Proxy** hides backend servers from clients.
- An **Upstream** defines a group of backend servers.
- **Load Balancing** distributes requests across multiple servers.
- **HTTPS** uses **TLS**, not SSL.
- **Proxy Cache** caches backend HTTP responses.
- **FastCGI Cache** caches FastCGI application responses.
- **Browser Cache** stores resources on the client.
- **Gzip** reduces response size.
- **Security Headers** improve browser security.
- **Logging** is essential for monitoring and troubleshooting.
- **Docker** packages Nginx into portable containers.
- **Kubernetes Ingress** manages external traffic inside Kubernetes clusters.
- Always validate configurations before reloading using:

```bash
nginx -t
```

---
