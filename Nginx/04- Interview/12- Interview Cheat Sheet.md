# Overview

This cheat sheet summarizes the most important Nginx concepts, directives, commands, architectures, and interview tips. It is designed as a last-minute revision guide before technical interviews.

---

# Nginx in One Minute

- High-performance web server
- Reverse proxy
- Load balancer
- API gateway
- HTTP cache
- Static file server
- SSL/TLS termination
- TCP/UDP proxy

Architecture:

```text
Client
   │
   ▼
Nginx
   │
Backend
```

---

# Core Architecture

```text
           Master Process
                  │
      ┌───────────┴───────────┐
      ▼                       ▼
 Worker Process         Worker Process
      │                       │
      └───────────┬───────────┘
                  ▼
          Client Connections
```

Remember:

- Master manages workers.
- Workers handle requests.
- Event-driven architecture.
- High concurrency.

---

# Request Processing

```text
Client
   │
   ▼
Server Block
   │
   ▼
Location Block
   │
   ▼
Execute Directives
   │
   ├───────────────┐
   ▼               ▼
Static File    Reverse Proxy
   │               │
   └───────┬───────┘
           ▼
     Send Response
```

Order:

1. Accept request
2. Select server
3. Select location
4. Execute directives
5. Return response

---

# Configuration Hierarchy

```text
Main

│

├── Events

│

└── HTTP

     │

     ├── Server

     │      │

     │      └── Location

     │

     └── Server
```

---

# Important Directives

| Directive | Purpose |
|------------|---------|
| `listen` | Listening port |
| `server_name` | Domain name |
| `location` | URL routing |
| `root` | Document root |
| `alias` | Alternative file path |
| `index` | Default file |
| `proxy_pass` | Reverse proxy |
| `rewrite` | Rewrite URLs |
| `return` | Return redirect or response |
| `try_files` | File existence check |
| `upstream` | Backend servers |
| `gzip` | Compression |
| `sendfile` | Efficient file transfer |
| `access_log` | Request logging |
| `error_log` | Error logging |

---

# Reverse Proxy

```text
Browser

   │

   ▼

Nginx

   │

   ▼

Backend
```

Main directive:

```nginx
proxy_pass
```

Common headers:

```nginx
proxy_set_header Host $host;

proxy_set_header X-Real-IP $remote_addr;

proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

proxy_set_header X-Forwarded-Proto $scheme;
```

---

# Load Balancing

Algorithms:

- Round Robin (default)
- Least Connections
- IP Hash

Example:

```nginx
upstream backend {

    server app1:8000;

    server app2:8000;

}
```

---

# Performance Optimization

Remember these directives:

```nginx
worker_processes auto;

sendfile on;

gzip on;

keepalive_timeout 65;

proxy_buffering on;
```

Goals:

- Lower latency
- Lower CPU usage
- Higher throughput
- Better scalability

---

# Security Checklist

✔ HTTPS enabled

✔ TLS 1.2 / TLS 1.3

✔ HSTS

✔ Security headers

✔ Rate limiting

✔ Connection limiting

✔ Hide Nginx version

```nginx
server_tokens off;
```

---

# Logging

Access Log

```text
/var/log/nginx/access.log
```

Error Log

```text
/var/log/nginx/error.log
```

Useful variables:

- `$remote_addr`
- `$host`
- `$status`
- `$request`
- `$request_time`
- `$http_user_agent`

---

# Docker Architecture

```text
Internet

   │

   ▼

Nginx

   │

   ▼

Application Container
```

Remember:

- Reverse proxy
- Static files
- SSL termination

---

# Kubernetes Architecture

```text
Internet

   │

   ▼

Load Balancer

   │

   ▼

Ingress Controller

   │

   ▼

Service

   │

   ▼

Pods
```

Nginx commonly acts as the **Ingress Controller**.

---

# Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 301 | Permanent Redirect |
| 302 | Temporary Redirect |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |
| 502 | Bad Gateway |
| 503 | Service Unavailable |
| 504 | Gateway Timeout |

---

# Frequently Asked Commands

Validate configuration

```bash
nginx -t
```

Show configuration

```bash
nginx -T
```

Show version

```bash
nginx -V
```

Reload configuration

```bash
nginx -s reload
```

Restart service

```bash
systemctl restart nginx
```

Check status

```bash
systemctl status nginx
```

---

# Common Interview Questions

- What is Nginx?
- Explain the event-driven architecture.
- Difference between Nginx and Apache?
- What is a reverse proxy?
- What is `proxy_pass`?
- Explain `upstream`.
- Difference between `root` and `alias`.
- Explain `try_files`.
- How does Nginx process a request?
- What is SSL termination?
- How does load balancing work?
- How would you troubleshoot a 502 error?
- How would you deploy Nginx in Kubernetes?
- How would you scale Nginx?
- Why use Nginx as an API Gateway?

---

# Senior-Level Interview Tips

When answering system design or production questions:

- Start with the architecture.
- Explain the request flow.
- Discuss scalability.
- Mention high availability.
- Explain security considerations.
- Discuss monitoring and logging.
- Consider rollback and disaster recovery.
- Mention performance optimization.

Interviewers evaluate your reasoning and trade-offs as much as your technical knowledge.

---

# 30-Second Revision

Remember these keywords:

- Event-driven
- Master Process
- Worker Process
- Reverse Proxy
- Load Balancer
- API Gateway
- Server Block
- Location Block
- Upstream
- proxy_pass
- try_files
- SSL Termination
- Gzip
- sendfile
- Caching
- Rate Limiting
- HSTS
- Access Log
- Error Log
- Ingress Controller

---

# Key Takeaways

- Nginx is a high-performance web server and reverse proxy widely used in modern production environments.
- Master the core architecture, configuration hierarchy, reverse proxying, load balancing, SSL/TLS, logging, and performance optimization.
- Understand how Nginx integrates with Docker, Kubernetes, and microservices.
- Follow structured troubleshooting and deployment practices when discussing production scenarios.
- A strong interview answer demonstrates conceptual understanding, practical experience, and the ability to explain architectural decisions clearly.