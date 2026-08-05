# Overview

One of the biggest reasons organizations choose Nginx is its excellent performance.

Even with default settings, Nginx can handle thousands of concurrent connections.

However, production systems often require additional tuning to handle:

- High traffic
- Large file downloads
- API workloads
- Reverse proxy traffic
- Microservices
- High concurrency

Performance tuning involves optimizing Nginx to make efficient use of:

- CPU
- Memory
- Network
- Disk I/O

---

# Performance Optimization Goals

A well-tuned Nginx server should provide:

- Lower latency
- Higher throughput
- Better resource utilization
- Reduced backend load
- Improved scalability
- Faster response times

---

# Performance Tuning Workflow

```text
Incoming Requests

        │

        ▼

Connection Handling

        │

        ▼

Worker Processes

        │

        ▼

Compression

        │

        ▼

Caching

        │

        ▼

Backend Server

        │

        ▼

Response
```

---

# Worker Processes

Worker processes perform the actual request processing.

Directive:

```nginx
worker_processes auto;
```

Example:

```nginx
worker_processes auto;
```

Using:

```
auto
```

allows Nginx to create one worker process per CPU core.

Example:

| CPU Cores | Worker Processes |
|------------|-----------------:|
| 2 | 2 |
| 4 | 4 |
| 8 | 8 |
| 16 | 16 |

---

# Worker Connections

Each worker process can maintain multiple client connections.

Directive:

```nginx
worker_connections 4096;
```

Example:

```nginx
events {

    worker_connections 4096;

}
```

Maximum theoretical connections:

```
Worker Processes

×

Worker Connections
```

Example:

```
8 Workers

×

4096 Connections

=

32768 Connections
```

Actual capacity depends on available system resources.

---

# Multi Accept

By default, workers accept one connection at a time.

Enable:

```nginx
multi_accept on;
```

Workers can accept multiple new connections simultaneously.

Useful during traffic spikes.

---

# Event Model

Linux systems commonly use:

```nginx
events {

    use epoll;

}
```

Supported event models:

| Operating System | Event Model |
|------------------|-------------|
| Linux | epoll |
| FreeBSD | kqueue |
| macOS | kqueue |
| Solaris | event ports |

`epoll` is highly efficient for handling large numbers of concurrent connections.

---

# Keepalive Connections

Instead of creating a new TCP connection for every request:

```text
Request

↓

Connect

↓

Disconnect
```

Nginx can reuse existing connections.

Configuration:

```nginx
keepalive_timeout 65;
```

Benefits:

- Lower latency
- Reduced TCP overhead
- Better browser performance

---

# Upstream Keepalive

Persistent connections can also be maintained between Nginx and backend servers.

Example:

```nginx
upstream backend {

    server app1;

    server app2;

    keepalive 32;

}
```

Benefits:

- Fewer TCP handshakes
- Lower backend latency
- Better throughput

---

# Sendfile

The `sendfile` directive allows Nginx to transfer files directly from disk to the network without copying them through user space.

Enable:

```nginx
sendfile on;
```

Benefits:

- Lower CPU usage
- Faster static file delivery
- Reduced memory copying

---

# TCP Optimizations

### tcp_nopush

```nginx
tcp_nopush on;
```

Delays packet transmission until enough data is available.

Useful for:

- Large static files
- File downloads

---

### tcp_nodelay

```nginx
tcp_nodelay on;
```

Sends small packets immediately.

Useful for:

- APIs
- Interactive applications
- WebSockets

---

# File Descriptor Limits

Every client connection consumes a file descriptor.

Linux systems have operating system limits.

Increase limits when handling high traffic.

Example:

```nginx
worker_rlimit_nofile 100000;
```

Operating system limits must also be increased.

---

# Client Body Size

Limit upload size.

Example:

```nginx
client_max_body_size 20M;
```

Benefits:

- Prevents excessive uploads
- Protects server resources

---

# Client Timeouts

Prevent idle clients from consuming resources indefinitely.

Example:

```nginx
client_header_timeout 15s;

client_body_timeout 15s;

send_timeout 15s;
```

Connections exceeding these limits are closed.

---

# Gzip Compression

Enable response compression.

```nginx
gzip on;

gzip_comp_level 6;
```

Benefits:

- Smaller responses
- Lower bandwidth usage
- Faster downloads

---

# Proxy Cache

Frequently requested responses should be cached.

Example:

```nginx
proxy_cache API_CACHE;
```

Benefits:

- Lower backend CPU usage
- Reduced database load
- Faster responses

---

# Static File Serving

Serve static resources directly from Nginx.

Avoid forwarding requests such as:

- Images
- CSS
- JavaScript
- Fonts

to backend applications.

This reduces application workload significantly.

---

# Load Balancing

Distribute requests among multiple servers.

```text
Nginx

↓

App1

App2

App3
```

No single server becomes overloaded.

---

# Rate Limiting

Prevent abusive traffic.

Example:

```nginx
limit_req_zone
```

Benefits:

- Prevents brute-force attacks
- Protects APIs
- Reduces traffic spikes

---

# Monitoring Performance

Monitor metrics such as:

- CPU Usage
- Memory Usage
- Active Connections
- Requests Per Second
- Response Time
- Upstream Response Time
- Cache Hit Ratio

Tools:

- Grafana
- Prometheus
- ELK Stack
- Netdata

---

# Benchmarking

Useful benchmarking tools:

```text
ab (Apache Benchmark)

wrk

siege

hey
```

Example:

```bash
wrk http://localhost
```

Benchmark before and after configuration changes.

---

# Example Optimized Configuration

```nginx
worker_processes auto;

worker_rlimit_nofile 100000;

events {

    worker_connections 4096;

    multi_accept on;

    use epoll;

}

http {

    sendfile on;

    tcp_nopush on;

    tcp_nodelay on;

    keepalive_timeout 65;

    gzip on;

    gzip_comp_level 6;

}
```

This serves as a strong baseline for many production deployments.

---

# Performance Optimization Checklist

| Optimization | Benefit |
|---------------|----------|
| worker_processes auto | Uses all CPU cores |
| worker_connections | Handles more clients |
| sendfile | Faster static files |
| keepalive | Fewer TCP handshakes |
| Gzip | Smaller responses |
| Proxy Cache | Lower backend load |
| Load Balancing | Horizontal scaling |
| epoll | Efficient event handling |
| Rate Limiting | Protects server resources |

---

# Real-World Example

Production API architecture:

```text
Internet

      │

      ▼

Nginx

      │

Compression

      │

Proxy Cache

      │

Load Balancer

      │

┌───────────────┐

▼               ▼

FastAPI 1   FastAPI 2

      │

      ▼

Redis

      │

      ▼

PostgreSQL
```

Nginx handles:

- Compression
- Caching
- Connection management
- Request routing

The application servers focus solely on business logic.

---

# Best Practices

- Use `worker_processes auto`.
- Configure `worker_connections` according to expected traffic.
- Enable `sendfile` for static content.
- Enable Gzip or Brotli for text-based responses.
- Use Proxy Cache where appropriate.
- Keep static assets out of the application server.
- Benchmark configuration changes before deploying them.
- Monitor production metrics continuously.

---

# Common Mistakes

## Increasing Worker Connections Without OS Tuning

Increasing:

```nginx
worker_connections 100000;
```

without raising operating system file descriptor limits may prevent Nginx from using the configured value.

---

## Overcompressing Responses

Using:

```nginx
gzip_comp_level 9;
```

can significantly increase CPU usage with minimal additional compression.

Levels **5–6** are generally a better balance.

---

## Ignoring Monitoring

Without monitoring:

- Slow APIs
- High CPU usage
- Cache misses
- Backend bottlenecks

may go unnoticed until users are affected.

---

# Interview Notes

### Beginner Questions

- What does `worker_processes auto` do?
- What is `worker_connections`?
- Why is `sendfile` useful?
- What is `keepalive_timeout`?

---

### Intermediate Questions

- Explain how Nginx handles thousands of concurrent connections.
- Why is `epoll` preferred on Linux?
- What is the relationship between worker processes and worker connections?
- Why should Proxy Cache and Gzip be combined?
- How would you tune Nginx for a high-traffic REST API?

---

# Key Takeaways

- Performance tuning enables Nginx to efficiently handle high traffic and large numbers of concurrent connections.
- Core tuning areas include worker processes, worker connections, connection handling, static file delivery, compression, caching, and load balancing.
- Features such as `sendfile`, `epoll`, `keepalive`, Gzip, and Proxy Cache significantly improve throughput and reduce latency.
- Benchmarking and continuous monitoring are essential to validate performance improvements.
- Effective Nginx tuning combines server configuration, operating system tuning, and application-level optimization for the best results.