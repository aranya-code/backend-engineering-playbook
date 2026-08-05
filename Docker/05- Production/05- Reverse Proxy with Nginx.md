# Reverse Proxy with Nginx

## Overview

A reverse proxy is a server that sits between clients and backend applications. Instead of exposing application containers directly to the internet, all incoming requests are first handled by the reverse proxy.

In Docker-based production environments, **Nginx** is one of the most commonly used reverse proxies because it is lightweight, fast, and highly configurable.

Using a reverse proxy improves security, simplifies traffic management, and provides features such as SSL termination, compression, request routing, and load balancing.

---

# What is a Reverse Proxy?

Without a reverse proxy:

```text
Internet

↓

Application
```

With a reverse proxy:

```text
Internet

↓

Nginx

↓

Application
```

Clients communicate only with Nginx. The application remains private inside the Docker network.

---

# Why Use Nginx?

Nginx provides:

- Reverse proxying
- SSL/TLS termination
- Request routing
- Load balancing
- Gzip compression
- Static file serving
- Security headers
- Rate limiting
- Request logging

---

# Typical Production Architecture

```text
                  Internet

                      │

                      ▼

              Nginx Container

                      │

          Docker Compose Network

                      │

                      ▼

             FastAPI / Django

                      │

                      ▼

                 PostgreSQL
```

Only Nginx exposes a public port.

---

# Request Lifecycle

```text
Browser

↓

Nginx

↓

Application

↓

Response

↓

Nginx

↓

Browser
```

---

# Example Docker Compose

```yaml
services:

  app:

    image: myapp:1.0.0

    expose:
      - "8000"

  nginx:

    image: nginx:1.28-alpine

    ports:
      - "80:80"

    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro

    depends_on:
      - app
```

Notice that:

- FastAPI uses `expose`
- Nginx uses `ports`

---

# Example Nginx Configuration

```nginx
server {

    listen 80;

    server_name localhost;

    location / {

        proxy_pass http://app:8000;

        proxy_http_version 1.1;

        proxy_set_header Host $host;

        proxy_set_header X-Real-IP $remote_addr;

        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        proxy_set_header X-Forwarded-Proto $scheme;

    }

}
```

---

# Understanding `proxy_pass`

```nginx
proxy_pass http://app:8000;
```

Docker resolves:

```text
app

↓

Docker DNS

↓

Application Container
```

No IP address is required.

---

# Docker Networking

```text
Docker Network

│

├── nginx

├── app

└── database
```

Containers communicate using service names.

---

# Expose vs Ports

Application

```yaml
expose:

  - "8000"
```

Nginx

```yaml
ports:

  - "80:80"
```

Only Nginx should publish ports.

---

# SSL Termination

Without SSL termination:

```text
HTTPS

↓

Application
```

With Nginx:

```text
HTTPS

↓

Nginx

↓

HTTP

↓

Application
```

The application only handles HTTP traffic while Nginx manages HTTPS.

---

# Security Headers

Example

```nginx
add_header X-Content-Type-Options "nosniff";

add_header X-Frame-Options "SAMEORIGIN";

add_header Referrer-Policy "strict-origin-when-cross-origin";
```

Benefits:

- Better browser security
- Protection against common attacks
- Improved security posture

---

# Gzip Compression

Enable compression

```nginx
gzip on;

gzip_types
    text/plain
    application/json
    text/css
    application/javascript;
```

Benefits:

- Smaller responses
- Faster downloads
- Reduced bandwidth usage

---

# Static File Serving

Instead of forwarding every request:

```text
/static/

↓

Nginx

↓

File
```

Only dynamic requests reach the application.

---

# Health Checks

Nginx can forward health requests.

```text
GET /health

↓

Application

↓

Healthy
```

Health checks are commonly used by Docker and load balancers.

---

# Load Balancing

One Nginx instance can distribute traffic across multiple application containers.

```text
Internet

↓

Nginx

│

├── App 1

├── App 2

└── App 3
```

This improves scalability and availability.

---

# Logging

Nginx generates:

```text
access.log

error.log
```

Typical uses:

- Request auditing
- Troubleshooting
- Performance analysis

---

# Reverse Proxy Workflow

```text
Browser

↓

Nginx

↓

Application

↓

Database

↓

Application

↓

Nginx

↓

Browser
```

---

# Common Mistakes

## Exposing the Application

Incorrect

```yaml
ports:

  - "8000:8000"
```

Correct

```yaml
expose:

  - "8000"
```

Only Nginx should publish ports.

---

## Using IP Addresses

Incorrect

```text
proxy_pass http://172.18.0.2:8000;
```

Correct

```text
proxy_pass http://app:8000;
```

Use Docker service names.

---

## Missing Security Headers

Without security headers, browsers receive less protection against several common attacks.

---

## No Compression

Large responses consume more bandwidth and increase response times.

---

## Serving Static Files Through the Application

Dynamic frameworks should not serve every static asset.

Allow Nginx to serve:

- CSS
- JavaScript
- Images
- Fonts

---

# Production Checklist

Before deployment:

- Reverse proxy configured
- Application kept internal
- HTTPS termination planned
- Security headers enabled
- Gzip enabled
- Static files served by Nginx
- Logs enabled
- Health checks configured
- Service names used
- Application ports not exposed

---

# Best Practices

- Expose only the reverse proxy.
- Keep backend containers on private Docker networks.
- Use Docker service names instead of IP addresses.
- Enable compression and security headers.
- Serve static assets directly from Nginx.
- Keep reverse proxy configuration under version control.
- Validate Nginx configuration before deployment using `nginx -t`.
- Monitor Nginx access and error logs.

---

# Key Takeaways

- A reverse proxy acts as the public entry point for backend applications.
- Nginx improves security by keeping application containers private.
- SSL termination, compression, request routing, and static file serving are common reverse proxy responsibilities.
- Docker service names make container communication simple and reliable.
- Nginx is a fundamental component of many production Docker deployments because it enhances performance, scalability, and security.