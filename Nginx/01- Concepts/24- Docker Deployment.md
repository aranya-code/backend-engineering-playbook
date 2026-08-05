# Overview

Modern applications are commonly deployed using **Docker** containers.

Instead of installing Nginx directly on the operating system, Nginx itself runs inside a container and communicates with other application containers.

A typical production deployment may contain:

- Nginx
- Django / FastAPI
- PostgreSQL
- Redis
- Celery

Each service runs inside its own container.

This approach provides:

- Isolation
- Portability
- Scalability
- Easier deployments
- Consistent environments

---

# Why Run Nginx in Docker?

Without Docker:

```text
Operating System

↓

Install Nginx

↓

Configure Nginx

↓

Deploy Application
```

Every server must be configured manually.

With Docker:

```text
Docker Image

↓

Docker Container

↓

Run Anywhere
```

The same image can be deployed on:

- Local machine
- Development server
- Test environment
- Production server
- Cloud platforms

---

# Typical Docker Architecture

```text
               Internet

                   │

                   ▼

            Nginx Container

                   │

         Reverse Proxy

                   │

          ┌────────┴────────┐

          ▼                 ▼

   Django Container   FastAPI Container

          │

          ▼

 PostgreSQL Container
```

Only the Nginx container is exposed to the Internet.

---

# Why Put Nginx in Front?

Instead of exposing:

```
8000

8001

5000
```

Expose only:

```
80

443
```

Architecture:

```text
Internet

↓

Nginx

↓

Application Containers
```

Benefits:

- Better security
- SSL termination
- Centralized routing
- Load balancing
- Compression
- Caching

---

# Docker Networking

Containers communicate using Docker networks.

```text
Docker Network

│

├── nginx

├── django

├── postgres

└── redis
```

Containers communicate using service names instead of IP addresses.

Example:

```text
http://django:8000
```

instead of

```text
http://192.168.x.x
```

---

# Docker Compose Example

```yaml
version: "3.9"

services:

  nginx:
    image: nginx:latest

  django:
    build: .

  postgres:
    image: postgres:16
```

Docker Compose starts every service together.

---

# Exposing Ports

Example:

```yaml
ports:

  - "80:80"

  - "443:443"
```

Meaning:

```
Host Port 80

↓

Container Port 80
```

---

# Mounting Configuration Files

Instead of rebuilding the image after every configuration change:

```yaml
volumes:

  - ./nginx.conf:/etc/nginx/nginx.conf
```

The configuration file is mounted directly.

Changes can be applied by reloading Nginx.

---

# Mounting Static Files

Example:

```yaml
volumes:

  - ./static:/app/static
```

Nginx can directly serve:

- CSS
- JavaScript
- Images
- Fonts

without involving Django or FastAPI.

---

# Reverse Proxy Configuration

Example:

```nginx
server {

    listen 80;

    location / {

        proxy_pass http://django:8000;

    }

}
```

Notice:

```
django
```

is the Docker service name.

Docker DNS automatically resolves it.

---

# Multiple Applications

Example:

```nginx
server {

    location /api {

        proxy_pass http://fastapi:8000;

    }

    location / {

        proxy_pass http://frontend:3000;

    }

}
```

Nginx routes requests to different containers.

---

# HTTPS in Docker

Certificates are mounted into the container.

Example:

```yaml
volumes:

  - ./certs:/etc/nginx/certs
```

Configuration:

```nginx
ssl_certificate
/etc/nginx/certs/server.crt;

ssl_certificate_key
/etc/nginx/certs/server.key;
```

---

# Static File Serving

Instead of:

```text
Browser

↓

Django

↓

Static File
```

Use:

```text
Browser

↓

Nginx

↓

Static File
```

This reduces backend workload.

---

# Docker Request Flow

```text
Browser

      │

      ▼

Nginx Container

      │

Reverse Proxy

      │

      ▼

Application Container

      │

      ▼

Database
```

---

# Scaling Containers

Docker allows multiple application containers.

```text
            Nginx

       ┌─────┼─────┐

       ▼     ▼     ▼

 Django1 Django2 Django3
```

Nginx distributes requests among them.

---

# Environment Variables

Avoid hardcoding configuration.

Example:

```yaml
environment:

  DEBUG=False

  DATABASE_HOST=postgres
```

Use environment variables for:

- Database credentials
- API keys
- Secret keys
- Hostnames

---

# Health Checks

Docker can monitor container health.

Example:

```yaml
healthcheck:

  test: ["CMD", "curl", "-f", "http://localhost"]
```

If a container becomes unhealthy, orchestration platforms can restart it.

---

# Logs

View logs:

```bash
docker logs nginx
```

Follow logs continuously:

```bash
docker logs -f nginx
```

Useful for:

- Configuration errors
- SSL problems
- Reverse proxy issues

---

# Reloading Configuration

After modifying the configuration:

```bash
docker exec nginx nginx -t
```

Test configuration.

Then:

```bash
docker exec nginx nginx -s reload
```

Reload without stopping the container.

---

# Production Architecture

```text
                 Internet

                     │

                     ▼

            Nginx Container

                     │

     Reverse Proxy + HTTPS

                     │

      ┌──────────────┼──────────────┐

      ▼              ▼              ▼

 Django         FastAPI         Node.js

      │

      ▼

 PostgreSQL

      │

      ▼

 Redis
```

---

# Best Practices

- Expose only Nginx to the public Internet.
- Use Docker networks instead of container IP addresses.
- Store certificates outside the container and mount them as volumes.
- Serve static assets directly through Nginx.
- Validate configuration before reloading.
- Keep application containers isolated.
- Use environment variables instead of hardcoded values.

---

# Common Mistakes

## Exposing Backend Containers

Avoid exposing:

```
8000

5000

3000
```

directly to the Internet.

Clients should communicate only with Nginx.

---

## Hardcoding IP Addresses

Incorrect:

```nginx
proxy_pass http://172.18.0.5:8000;
```

Correct:

```nginx
proxy_pass http://django:8000;
```

Docker service names remain stable even if container IP addresses change.

---

## Storing Certificates Inside the Image

Certificates should be mounted as volumes.

This allows certificate renewal without rebuilding the Docker image.

---

## Forgetting to Test Configuration

Always run:

```bash
docker exec nginx nginx -t
```

before reloading Nginx.

---

# Interview Notes

### Beginner Questions

- Why run Nginx inside Docker?
- Why is Nginx placed in front of application containers?
- How do containers communicate with each other?
- What is Docker Compose?

---

### Intermediate Questions

- Explain how Nginx reverse proxies requests inside Docker.
- Why should service names be used instead of IP addresses?
- How are SSL certificates managed inside Docker?
- Why should static files be served directly by Nginx?
- How would you scale a Dockerized Django application?

---

# Key Takeaways

- Nginx is commonly deployed as a Docker container in modern applications.
- Docker networks allow containers to communicate using service names instead of IP addresses.
- Nginx acts as the public entry point, handling HTTPS, reverse proxying, static file serving, caching, and load balancing.
- Docker Compose simplifies multi-container deployments by managing networking, volumes, and environment variables.
- A well-designed Docker deployment keeps backend services private while exposing only the Nginx container to external clients.