# Overview

Nginx is one of the most frequently asked topics in Backend Developer, DevOps Engineer, Site Reliability Engineer (SRE), Platform Engineer, and Cloud Engineer interviews.

Interviewers generally expect candidates to understand:

- Core Nginx architecture
- Request processing
- Reverse Proxy
- Load Balancing
- SSL/TLS
- Performance optimization
- Caching
- Docker deployments
- Kubernetes Ingress
- Production troubleshooting

This chapter summarizes the most commonly asked interview questions and provides concise answers.

---

# Beginner Level Questions

## 1. What is Nginx?

**Answer**

Nginx is an open-source web server that can also function as:

- Reverse Proxy
- Load Balancer
- HTTP Cache
- SSL/TLS Terminator
- API Gateway
- Static File Server

It is event-driven and designed to handle a large number of concurrent connections efficiently.

---

## 2. Why is Nginx faster than Apache?

**Answer**

Nginx uses an asynchronous, event-driven architecture.

Instead of creating one thread or process per connection, a small number of worker processes can manage thousands of simultaneous connections.

Apache traditionally uses process-based or thread-based models, which generally consume more memory under high concurrency.

---

## 3. What is the difference between Nginx and Apache?

| Nginx | Apache |
|--------|---------|
| Event-driven | Process/Thread-driven (traditional models) |
| Lower memory usage | Higher memory usage under heavy concurrency |
| Excellent Reverse Proxy | Excellent Web Server |
| High concurrency | Strong module ecosystem |

---

## 4. What is a Reverse Proxy?

A Reverse Proxy receives requests from clients and forwards them to backend servers.

```text
Client

↓

Nginx

↓

Backend Application
```

The client never communicates directly with the backend.

---

## 5. What is Load Balancing?

Load balancing distributes requests among multiple backend servers.

```text
Client

↓

Nginx

↓

App1

App2

App3
```

This improves scalability and availability.

---

## 6. What is an Upstream Block?

An upstream block defines a group of backend servers.

Example:

```nginx
upstream backend {

    server app1:8000;

    server app2:8000;

}
```

---

## 7. What is the purpose of `proxy_pass`?

`proxy_pass` forwards requests to another server.

Example:

```nginx
location / {

    proxy_pass http://backend;

}
```

---

## 8. What is the difference between HTTP and HTTPS?

| HTTP | HTTPS |
|------|--------|
| Unencrypted | Encrypted |
| Port 80 | Port 443 |
| No TLS | TLS Enabled |

HTTPS protects data transmitted between clients and servers.

---

## 9. Why should static files be served by Nginx?

Nginx serves static files directly from disk without involving the application server.

Benefits:

- Lower CPU usage
- Faster responses
- Reduced backend load

---

## 10. What is Gzip Compression?

Gzip compresses HTTP responses before sending them to the client.

Benefits:

- Smaller response size
- Faster downloads
- Reduced bandwidth usage

---

# Intermediate Level Questions

## 11. Explain the Nginx request lifecycle.

```text
Client

↓

DNS Resolution

↓

Nginx

↓

Server Block

↓

Location Block

↓

Static File

OR

Reverse Proxy

↓

Backend

↓

Response
```

---

## 12. Explain the difference between Browser Cache and Proxy Cache.

| Browser Cache | Proxy Cache |
|---------------|-------------|
| Stored in Browser | Stored by Nginx |
| Client-side | Server-side |
| Reduces downloads | Reduces backend requests |

---

## 13. What is FastCGI Cache?

FastCGI Cache stores responses from FastCGI applications such as PHP-FPM.

It reduces repeated application execution by serving cached responses directly from Nginx.

---

## 14. What is Proxy Cache?

Proxy Cache stores HTTP responses received from backend applications such as Django, FastAPI, or Node.js.

---

## 15. Explain Round Robin.

Round Robin distributes requests sequentially.

```text
Request 1

↓

Server 1

Request 2

↓

Server 2

Request 3

↓

Server 3
```

---

## 16. What is Least Connections?

Requests are sent to the backend with the fewest active connections.

Useful for long-running requests.

---

## 17. What is IP Hash?

IP Hash routes requests from the same client IP to the same backend server.

Useful for session persistence.

---

## 18. What is `worker_processes auto`?

It automatically creates one worker process for each available CPU core.

---

## 19. What is `worker_connections`?

It defines the maximum number of simultaneous connections each worker process can handle.

---

## 20. What is `sendfile`?

`sendfile` enables efficient transfer of static files from disk to the network, reducing CPU usage.

---

# Advanced Level Questions

## 21. Explain the event-driven architecture of Nginx.

Unlike process-per-request servers, Nginx uses a small number of worker processes that rely on an event loop to manage many concurrent connections.

This allows Nginx to handle high traffic with low memory consumption.

---

## 22. How does Nginx handle 100,000 concurrent users?

By combining:

- Event-driven architecture
- Worker processes
- Worker connections
- epoll (Linux)
- Keepalive connections
- Load balancing
- Caching

---

## 23. Explain the difference between `reload` and `restart`.

| Reload | Restart |
|----------|----------|
| Reload configuration | Stop and start Nginx |
| Existing connections continue | Existing connections are interrupted |
| Preferred after configuration changes | Used when a full restart is required |

---

## 24. What causes a 502 Bad Gateway?

Common causes:

- Backend service stopped
- Incorrect `proxy_pass`
- Wrong socket path
- Firewall restrictions
- Docker networking issues

---

## 25. Difference between 502 and 504?

| 502 | 504 |
|------|------|
| Backend unavailable | Backend too slow |
| Connection failure | Timeout |

---

## 26. How would you secure an Nginx server?

Typical production measures include:

- HTTPS
- TLS 1.2 / TLS 1.3
- HSTS
- Security headers
- Rate limiting
- Connection limiting
- Disable directory listing
- Protect hidden files
- Hide Nginx version
- Regular updates

---

## 27. How do you troubleshoot Nginx?

General approach:

1. Validate configuration

```bash
nginx -t
```

2. Check Access Log

3. Check Error Log

4. Verify backend availability

5. Test networking

6. Reload configuration

---

## 28. Explain Nginx in a Docker environment.

```text
Internet

↓

Nginx Container

↓

Application Container

↓

Database
```

Nginx acts as:

- Reverse Proxy
- SSL Terminator
- Static File Server
- Load Balancer

---

## 29. Explain Nginx Ingress.

Nginx Ingress Controller is a Kubernetes component that routes external traffic to Services inside the cluster.

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

## 30. How would you deploy a Django application using Nginx?

Typical architecture:

```text
Internet

↓

Nginx

↓

Gunicorn

↓

Django

↓

PostgreSQL
```

Nginx responsibilities:

- HTTPS
- Static files
- Reverse proxy
- Compression
- Caching

Gunicorn:

- Python application server

---

# Scenario-Based Questions

## Scenario 1

Your website returns **502 Bad Gateway**.

How would you investigate?

**Answer**

- Check `nginx -t`
- Review `error.log`
- Verify backend process
- Test backend port
- Verify `proxy_pass`
- Check firewall and networking
- Reload configuration

---

## Scenario 2

Users report that CSS changes are not visible.

Possible causes:

- Browser cache
- CDN cache
- Proxy Cache
- Missing cache busting

Solution:

- Version static assets
- Clear caches
- Verify `Cache-Control` headers

---

## Scenario 3

CPU usage suddenly reaches 100%.

Possible causes:

- Traffic spike
- Slow backend
- Cache disabled
- Infinite redirect loop
- DDoS attack

Investigation:

- Review logs
- Check backend performance
- Monitor active connections
- Verify rate limiting

---

## Scenario 4

Users experience slow page loading.

Potential improvements:

- Enable Gzip or Brotli
- Configure Browser Cache
- Enable Proxy Cache
- Optimize database queries
- Enable HTTP/2
- Serve static assets directly through Nginx

---

# Frequently Used Commands

Validate configuration:

```bash
nginx -t
```

Reload:

```bash
nginx -s reload
```

Restart:

```bash
systemctl restart nginx
```

View Access Log:

```bash
tail -f /var/log/nginx/access.log
```

View Error Log:

```bash
tail -f /var/log/nginx/error.log
```

Check listening ports:

```bash
ss -tulpn
```

Docker logs:

```bash
docker logs nginx
```

Kubernetes logs:

```bash
kubectl logs pod-name
```

---

# Production Deployment Checklist

| Item | Status |
|--------|--------|
| HTTPS Enabled | ✅ |
| HTTP → HTTPS Redirect | ✅ |
| TLS 1.2 / TLS 1.3 | ✅ |
| Reverse Proxy | ✅ |
| Static File Serving | ✅ |
| Gzip Compression | ✅ |
| Browser Cache | ✅ |
| Proxy Cache | ✅ |
| Security Headers | ✅ |
| Rate Limiting | ✅ |
| Logging | ✅ |
| Monitoring | ✅ |
| Configuration Tested (`nginx -t`) | ✅ |

---

# Interview Preparation Tips

- Understand the complete request lifecycle from browser to backend.
- Be able to explain **why** a directive is used, not just its syntax.
- Practice reading and writing Nginx configuration files.
- Learn to troubleshoot common production issues such as 404, 502, and SSL errors.
- Understand how Nginx integrates with Docker and Kubernetes.
- Be comfortable explaining caching, compression, reverse proxying, and load balancing using diagrams.
- Practice scenario-based questions that require reasoning instead of memorization.

---

# Key Takeaways

- Nginx interview questions range from basic web server concepts to advanced production architecture.
- Strong understanding of reverse proxying, caching, SSL/TLS, load balancing, and troubleshooting is expected for backend and DevOps roles.
- Practical experience with Docker, Kubernetes, and production deployments significantly strengthens interview performance.
- Understanding the reasoning behind Nginx configurations is more valuable than memorizing directives.
- Combining conceptual knowledge with hands-on troubleshooting prepares you for real-world engineering interviews.