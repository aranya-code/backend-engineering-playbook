# Overview

One of the primary reasons organizations use Nginx is as a **Reverse Proxy**.

Instead of exposing backend applications directly to the Internet, Nginx sits in front of them and forwards client requests to the appropriate backend server.

This architecture provides:

- Better security
- Improved performance
- SSL termination
- Load balancing
- Caching
- Compression
- Centralized request routing

Almost every production deployment of **Django**, **FastAPI**, **Flask**, **Node.js**, **Spring Boot**, or **ASP.NET Core** uses a reverse proxy.

---

# What is a Reverse Proxy?

A Reverse Proxy is a server that receives requests from clients and forwards them to one or more backend servers.

The client never communicates directly with the backend application.

```text
                Client
                   │
                   ▼
          +----------------+
          |     Nginx      |
          | Reverse Proxy  |
          +----------------+
                   │
                   ▼
            Backend Server
```

To the client, Nginx appears to be the actual web server.

---

# Reverse Proxy vs Forward Proxy

These two terms are often confused.

| Forward Proxy | Reverse Proxy |
|--------------|---------------|
| Represents the client | Represents the server |
| Used by clients | Used by servers |
| Hides client identity | Hides backend servers |
| Controls outgoing traffic | Controls incoming traffic |

---

# Without Reverse Proxy

Suppose a Django application runs directly on port **8000**.

```text
Browser
    │
    ▼
Django (Port 8000)
```

Problems:

- Application server is publicly exposed.
- No SSL termination.
- Poor static file handling.
- Difficult to scale.
- Limited request filtering.

---

# With Reverse Proxy

```text
Browser
    │
 HTTPS
    │
    ▼
+----------------+
|     Nginx      |
+----------------+
    │
HTTP
    │
    ▼
Django (8000)
```

The client communicates only with Nginx.

Nginx communicates with Django internally.

---

# How Reverse Proxy Works

Request Flow:

```text
Browser

    │

GET /products

    │

    ▼

Nginx

    │

proxy_pass

    │

    ▼

Backend Server

    │

Generate Response

    │

    ▼

Nginx

    │

    ▼

Browser
```

The browser never knows that another server handled the request.

---

# The `proxy_pass` Directive

The most important directive for reverse proxying is:

```nginx
proxy_pass http://backend;
```

or

```nginx
proxy_pass http://127.0.0.1:8000;
```

This tells Nginx where to forward incoming requests.

---

# Basic Reverse Proxy Configuration

```nginx
server {

    listen 80;

    server_name example.com;

    location / {

        proxy_pass http://127.0.0.1:8000;

    }

}
```

Flow:

```text
Browser

↓

Nginx

↓

127.0.0.1:8000

↓

Application
```

---

# Reverse Proxy with FastAPI

Suppose FastAPI is running on:

```
http://127.0.0.1:8000
```

Configuration:

```nginx
server {

    listen 80;

    location / {

        proxy_pass http://127.0.0.1:8000;

    }

}
```

Users access:

```
http://example.com
```

They never see:

```
http://127.0.0.1:8000
```

---

# Reverse Proxy with Django

Production architecture:

```text
Browser

     │

 HTTPS

     │

     ▼

Nginx

     │

 Gunicorn

     │

     ▼

 Django
```

Example:

```nginx
location / {

    proxy_pass http://127.0.0.1:8000;

}
```

Gunicorn serves Django internally while Nginx handles client communication.

---

# Passing Client Information

By default, the backend does not know the original client's IP address.

Nginx forwards this information using headers.

Example:

```nginx
location / {

    proxy_set_header Host $host;

    proxy_set_header X-Real-IP $remote_addr;

    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

    proxy_set_header X-Forwarded-Proto $scheme;

    proxy_pass http://127.0.0.1:8000;

}
```

These headers allow the backend to identify:

- Original Host
- Client IP
- Request Protocol
- Proxy chain

---

# Understanding Common Proxy Headers

## Host

```nginx
proxy_set_header Host $host;
```

Passes the original domain name.

---

## X-Real-IP

```nginx
proxy_set_header X-Real-IP $remote_addr;
```

Passes the client's IP address.

---

## X-Forwarded-For

```nginx
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

Maintains the complete chain of client and proxy IP addresses.

Useful when multiple reverse proxies are involved.

---

## X-Forwarded-Proto

```nginx
proxy_set_header X-Forwarded-Proto $scheme;
```

Indicates whether the original request used:

```
http
```

or

```
https
```

Many frameworks use this header to generate secure URLs.

---

# Reverse Proxy Architecture

```text
                    Internet

                        │

                        ▼

                Load Balancer

                        │

                        ▼

                     Nginx

          ┌─────────────┼──────────────┐

          ▼             ▼              ▼

      FastAPI       Django        Node.js
```

One Nginx server can route requests to multiple backend applications.

---

# Routing Different Applications

Example:

```nginx
server {

    location /api {

        proxy_pass http://fastapi;

    }

    location /admin {

        proxy_pass http://django;

    }

}
```

Result:

| URL | Destination |
|------|-------------|
| `/api` | FastAPI |
| `/admin` | Django |

This pattern is common in microservice architectures.

---

# Reverse Proxy for Microservices

```text
                    Client

                       │

                       ▼

                    Nginx

      ┌──────────────┼──────────────┐

      ▼              ▼              ▼

 User API      Order API      Payment API
```

Each service runs independently while Nginx acts as the single entry point.

---

# Benefits of Reverse Proxy

- Hides backend servers
- Improves security
- Enables HTTPS termination
- Supports load balancing
- Simplifies routing
- Supports caching
- Enables response compression
- Improves scalability
- Simplifies maintenance

---

# Real-World Example

A production e-commerce application:

```text
Customer

      │

      ▼

Nginx

      │

 ┌────┴─────────────┐

 ▼                  ▼

Frontend         Backend API

                     │

                     ▼

                 PostgreSQL
```

Responsibilities:

Nginx:

- Accept HTTPS requests
- Serve static assets
- Forward API requests
- Compress responses
- Add security headers
- Write access logs

Backend:

- Business logic
- Authentication
- Database operations

---

# Best Practices

- Never expose application servers directly to the Internet.
- Always use HTTPS between clients and Nginx.
- Forward the appropriate proxy headers.
- Keep backend services on private networks whenever possible.
- Separate static file serving from application request handling.
- Validate configurations with:

```bash
nginx -t
```

before reloading Nginx.

---

# Common Mistakes

## Forgetting Proxy Headers

Without forwarding headers such as:

```nginx
X-Forwarded-For
```

the backend may log the reverse proxy's IP address instead of the client's.

---

## Exposing Backend Ports

Allowing public access to ports such as:

```
8000
```

or

```
5000
```

bypasses the reverse proxy and reduces security.

---

## Mixing Static Files with Backend Requests

Static assets should be served directly by Nginx whenever possible instead of forwarding every request to the application server.

---

# Interview Notes

### Beginner Questions

- What is a reverse proxy?
- Why is Nginx commonly used as a reverse proxy?
- What does the `proxy_pass` directive do?
- What are the benefits of using a reverse proxy?

---

### Intermediate Questions

- Explain the request flow in a reverse proxy architecture.
- What is the purpose of `proxy_set_header`?
- What is the difference between `X-Real-IP` and `X-Forwarded-For`?
- Why should backend applications not be exposed directly to the Internet?
- How does a reverse proxy improve scalability and security?

---

# Key Takeaways

- A reverse proxy sits between clients and backend applications.
- The `proxy_pass` directive forwards requests to upstream servers.
- `proxy_set_header` preserves important request information for backend services.
- Reverse proxies improve security, scalability, and maintainability.
- Nginx is widely used as a reverse proxy for Django, FastAPI, Flask, Node.js, Spring Boot, and other backend frameworks.
- Reverse proxying is a foundational concept in modern backend architecture and cloud-native deployments.