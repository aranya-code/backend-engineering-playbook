# Overview

One of the primary reasons Nginx is widely adopted is its ability to act as a **reverse proxy** and **load balancer**. Instead of clients communicating directly with backend applications, Nginx sits in front of them, handling incoming requests and intelligently routing traffic.

This architecture improves security, scalability, reliability, and performance, making it the standard deployment model for modern web applications and microservices.

---

# What is a Reverse Proxy?

A reverse proxy is a server that receives client requests and forwards them to one or more backend servers.

Unlike a forward proxy, which represents clients, a reverse proxy represents servers.

```text
            Client
               │
               ▼
        Reverse Proxy (Nginx)
               │
       ┌───────┴────────┐
       ▼                ▼
   Backend 1       Backend 2
```

Clients communicate only with Nginx and are unaware of the backend infrastructure.

---

# Why Use a Reverse Proxy?

Using Nginx as a reverse proxy provides several advantages:

- Hides backend servers from clients
- Centralizes SSL/TLS termination
- Improves security
- Enables load balancing
- Supports caching
- Compresses responses
- Simplifies routing
- Improves scalability
- Reduces backend workload

---

# Reverse Proxy Example

```nginx
server {

    listen 80;

    server_name api.example.com;

    location / {

        proxy_pass http://127.0.0.1:8000;

    }

}
```

Flow:

```text
Browser
    │
    ▼
Nginx
    │
    ▼
FastAPI
```

Nginx forwards every request to the backend application running on port **8000**.

---

# Understanding proxy_pass

The `proxy_pass` directive forwards requests to another server.

Example:

```nginx
location / {

    proxy_pass http://backend;

}
```

It is one of the most commonly used directives in production deployments.

Typical backend targets include:

- FastAPI
- Django
- Flask
- Node.js
- Spring Boot
- ASP.NET
- Go applications

---

# Passing Client Information

By default, backend applications do not automatically receive all client information.

Common proxy headers are:

```nginx
location / {

    proxy_pass http://backend;

    proxy_set_header Host $host;

    proxy_set_header X-Real-IP $remote_addr;

    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

    proxy_set_header X-Forwarded-Proto $scheme;

}
```

These headers allow backend applications to identify:

- Original client IP
- Requested host
- Protocol (HTTP/HTTPS)
- Proxy chain

---

# What is Load Balancing?

Load balancing distributes incoming requests across multiple backend servers.

Instead of sending all traffic to one server, requests are shared among multiple instances.

```text
              Nginx
                 │
      ┌──────────┼──────────┐
      ▼          ▼          ▼
 Backend 1   Backend 2   Backend 3
```

This improves:

- Availability
- Scalability
- Fault tolerance
- Performance

---

# Upstream Block

Backend servers are grouped using an `upstream` block.

Example:

```nginx
upstream backend {

    server app1:8000;

    server app2:8000;

    server app3:8000;

}
```

Requests can then be forwarded to the upstream group.

```nginx
location / {

    proxy_pass http://backend;

}
```

Nginx automatically selects one of the available servers.

---

# Load Balancing Algorithms

Nginx supports several traffic distribution strategies.

## Round Robin (Default)

Requests are distributed sequentially.

```text
Request 1 → Server 1

Request 2 → Server 2

Request 3 → Server 3

Request 4 → Server 1
```

Best for servers with similar capacity.

---

## Least Connections

Requests are sent to the server with the fewest active connections.

```nginx
upstream backend {

    least_conn;

    server app1:8000;

    server app2:8000;

}
```

Useful for long-running requests.

---

## IP Hash

Requests from the same client IP are consistently routed to the same backend.

```nginx
upstream backend {

    ip_hash;

    server app1:8000;

    server app2:8000;

}
```

Useful for applications requiring session persistence.

---

# Backend Failure Handling

If one backend becomes unavailable, Nginx automatically routes traffic to healthy servers.

Example:

```text
            Nginx
              │
      ┌───────┴────────┐
      ▼                ▼
 App 1 (Healthy)   App 2 (Down)
```

Traffic continues to be served by healthy instances, improving application availability.

---

# SSL Termination with Reverse Proxy

A common production setup is:

```text
Client (HTTPS)
        │
        ▼
      Nginx
        │
     HTTP
        │
        ▼
 Backend Services
```

Nginx handles encryption while backend applications communicate over an internal network.

---

# Reverse Proxy in a Microservices Architecture

```text
                 Client
                    │
                    ▼
                 Nginx
      ┌──────────┼──────────┐
      ▼          ▼          ▼
 User API   Order API   Payment API
```

Nginx routes requests to different services based on the request path.

Example:

```text
/api/users     → User Service

/api/orders    → Order Service

/api/payment   → Payment Service
```

---

# Real-World Example

Suppose an e-commerce application has three backend services.

```nginx
upstream backend {

    server app1:8000;

    server app2:8000;

    server app3:8000;

}

server {

    listen 80;

    server_name api.shop.com;

    location / {

        proxy_pass http://backend;

    }

}
```

Client requests are distributed across all three application servers, allowing the system to handle higher traffic and remain available even if one instance fails.

---

# Common Interview Questions

- What is a reverse proxy?
- How is a reverse proxy different from a forward proxy?
- What is `proxy_pass`?
- Why are proxy headers important?
- What is an upstream block?
- How does Round Robin load balancing work?
- When would you use `least_conn`?
- What is `ip_hash`?
- Why is Nginx commonly used in front of backend applications?
- How does Nginx improve application scalability?

---

# Best Practices

- Always place Nginx in front of backend applications.
- Define backend servers using `upstream` blocks.
- Forward client information using proxy headers.
- Use HTTPS between clients and Nginx.
- Keep backend applications isolated from direct internet access.
- Choose a load-balancing algorithm based on application requirements.
- Monitor backend health and remove unhealthy servers from rotation.

---

# Key Takeaways

- Nginx acts as a reverse proxy by forwarding client requests to backend applications.
- The `proxy_pass` directive is the foundation of reverse proxy configurations.
- `upstream` blocks group backend servers for load balancing.
- Round Robin, Least Connections, and IP Hash are common load-balancing algorithms.
- Reverse proxying improves security, scalability, availability, and performance.
- Nginx is commonly used as the entry point for modern web applications and microservices.