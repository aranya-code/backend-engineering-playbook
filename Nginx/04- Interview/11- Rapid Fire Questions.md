# Overview

Rapid-fire interview rounds are commonly used to evaluate how quickly candidates can recall core concepts. These questions are typically short, direct, and expect concise answers rather than lengthy explanations.

This chapter provides a collection of frequently asked Nginx interview questions with brief answers, making it ideal for quick revision before interviews.

---

# Nginx Basics

### What is Nginx?

A high-performance web server, reverse proxy, load balancer, API gateway, and HTTP cache.

---

### What does Nginx stand for?

Nginx is pronounced **"Engine-X."**

---

### What is Nginx primarily used for?

- Reverse Proxy
- Web Server
- Load Balancer
- SSL Termination
- API Gateway
- Static File Server

---

### Why is Nginx faster than traditional web servers?

Because it uses an **event-driven, asynchronous architecture** instead of creating one thread or process per connection.

---

### What process manages worker processes?

The **Master Process**.

---

### Which process handles client requests?

The **Worker Process**.

---

### What is a worker process?

A process responsible for handling client connections and processing requests.

---

### What is `worker_processes auto;`?

Automatically creates one worker process per available CPU core.

---

### What does `worker_connections` control?

The maximum number of simultaneous connections handled by each worker process.

---

# Configuration

### What is the main Nginx configuration file?

```text
nginx.conf
```

---

### What directive includes additional configuration files?

```nginx
include
```

---

### What command validates the configuration?

```bash
nginx -t
```

---

### What command displays the complete configuration?

```bash
nginx -T
```

---

### Which block defines a virtual host?

```nginx
server
```

---

### Which block handles URL routing?

```nginx
location
```

---

### Which directive specifies the listening port?

```nginx
listen
```

---

### Which directive specifies the domain name?

```nginx
server_name
```

---

# Reverse Proxy

### What is a reverse proxy?

A server that receives client requests and forwards them to backend servers.

---

### Which directive forwards requests?

```nginx
proxy_pass
```

---

### Why use a reverse proxy?

- Security
- Load balancing
- SSL termination
- Centralized routing
- Backend isolation

---

### Which header forwards the client's IP address?

```nginx
X-Real-IP
```

---

### Which header preserves the proxy chain?

```nginx
X-Forwarded-For
```

---

# Load Balancing

### What directive defines backend servers?

```nginx
upstream
```

---

### What is the default load-balancing algorithm?

Round Robin.

---

### Which algorithm routes requests to the least busy server?

```text
least_conn
```

---

### Which algorithm provides session persistence?

```text
ip_hash
```

---

# Static Files

### Why should Nginx serve static files?

Because it is significantly faster than application servers for serving static content.

---

### Which directive specifies the document root?

```nginx
root
```

---

### What is the difference between `root` and `alias`?

- `root` appends the request URI to the configured path.
- `alias` replaces the matched location path with the specified path.

---

### Which directive specifies the default file?

```nginx
index
```

---

# SSL & Security

### Which port is commonly used for HTTPS?

```text
443
```

---

### Which directive enables SSL?

```nginx
listen 443 ssl;
```

---

### Which directive redirects HTTP to HTTPS?

```nginx
return 301 https://$host$request_uri;
```

---

### What is HSTS?

A security mechanism that forces browsers to use HTTPS.

---

### Which directive hides the Nginx version?

```nginx
server_tokens off;
```

---

# Performance

### Which directive enables Gzip compression?

```nginx
gzip on;
```

---

### What does `sendfile` do?

Transfers files efficiently from disk to the network without unnecessary memory copies.

---

### What is keepalive?

Allows multiple requests to reuse the same TCP connection.

---

### Why use caching?

To reduce backend load and improve response times.

---

# Logging & Monitoring

### What are the two primary log files?

- Access Log
- Error Log

---

### Which log records every request?

Access Log.

---

### Which log records server errors?

Error Log.

---

### Which module provides runtime statistics?

```text
stub_status
```

---

# Docker & Kubernetes

### Why use Nginx with Docker?

To act as a reverse proxy and serve as the public entry point.

---

### What is the role of Nginx in Kubernetes?

It commonly functions as an **Ingress Controller**.

---

### What is an Ingress?

A Kubernetes resource that defines how external traffic reaches cluster services.

---

# Troubleshooting

### What usually causes a 502 Bad Gateway?

The backend server is unavailable or unreachable.

---

### What usually causes a 504 Gateway Timeout?

The backend server takes too long to respond.

---

### What command should you run before reloading Nginx?

```bash
nginx -t
```

---

### Why would Nginx fail to start?

Common reasons include:

- Configuration syntax errors
- Port conflicts
- Missing files
- Permission issues

---

# Production

### Why terminate SSL at Nginx?

To centralize certificate management and reduce backend complexity.

---

### Why deploy multiple Nginx instances?

To eliminate a single point of failure and improve availability.

---

### Why use Nginx as an API Gateway?

Because it provides:

- Routing
- Authentication
- Rate limiting
- SSL termination
- Load balancing
- Logging

---

### Why keep backend servers private?

To improve security and ensure all traffic passes through Nginx.

---

### What is the first thing to check when production fails?

Validate the configuration and review the Nginx error log.

---

# Key Takeaways

- Rapid-fire questions test your understanding of core Nginx concepts rather than deep implementation details.
- Focus on concise, accurate answers that demonstrate conceptual clarity.
- Mastering common directives, architecture, reverse proxying, load balancing, security, and troubleshooting prepares you for most Nginx interview rounds.
- Regularly reviewing these questions helps reinforce key concepts and improves confidence during technical interviews.