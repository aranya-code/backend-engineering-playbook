# Overview

As the number of users increases, a single application server eventually becomes unable to handle all incoming requests.

Instead of upgrading to a larger server (Vertical Scaling), modern systems distribute requests across multiple servers (Horizontal Scaling).

This technique is known as **Load Balancing**.

Nginx includes a powerful software load balancer capable of distributing requests across multiple backend servers while improving:

- Availability
- Scalability
- Performance
- Reliability
- Fault Tolerance

Load balancing is one of the most common reasons organizations deploy Nginx in production.

---

# What is Load Balancing?

Load balancing is the process of distributing incoming client requests among multiple backend servers.

Instead of one server processing every request:

```text
             Client
                │
                ▼
          Single Server
```

The workload is shared.

```text
                 Client
                    │
                    ▼
              +-----------+
              |   Nginx   |
              +-----------+
             /      │      \
            ▼       ▼       ▼
       Server1  Server2  Server3
```

Each backend processes only a portion of the traffic.

---

# Why Load Balancing?

Imagine your application receives:

```
100,000 requests/minute
```

A single server eventually reaches its limits.

Problems include:

- High CPU utilization
- Memory exhaustion
- Increased response times
- Timeouts
- Server crashes

Adding more backend servers allows requests to be distributed efficiently.

---

# Load Balancing Workflow

```text
Client

    │

HTTP Request

    │

    ▼

Nginx

    │

Choose Backend

    │

    ▼

Application Server

    │

Generate Response

    │

    ▼

Client
```

The client is unaware of which backend handled the request.

---

# The `upstream` Directive

Backend servers are grouped using the `upstream` directive.

Example:

```nginx
upstream backend {

    server 192.168.1.10:8000;

    server 192.168.1.11:8000;

    server 192.168.1.12:8000;

}
```

The group is named:

```
backend
```

---

# Connecting to an Upstream

Once an upstream is defined:

```nginx
location / {

    proxy_pass http://backend;

}
```

Every request is forwarded to one of the backend servers.

---

# Load Balancing Algorithms

Nginx supports multiple scheduling algorithms.

- Round Robin
- Least Connections
- IP Hash
- Weighted Round Robin

Each algorithm is designed for different workloads.

---

# Round Robin

Round Robin is the **default algorithm**.

Requests are distributed sequentially.

Example:

```text
Request 1 → Server 1

Request 2 → Server 2

Request 3 → Server 3

Request 4 → Server 1

Request 5 → Server 2
```

Advantages:

- Very simple
- Even distribution
- No additional configuration

Best suited for:

- Similar backend servers
- Similar request processing times

---

# Least Connections

Instead of alternating requests, Nginx selects the server with the fewest active connections.

Configuration:

```nginx
upstream backend {

    least_conn;

    server app1;

    server app2;

}
```

Example:

| Server | Active Connections |
|---------|-------------------:|
| App1 | 120 |
| App2 | 25 |

Next request:

```
↓

App2
```

Best suited for:

- Long-running requests
- File downloads
- Streaming services

---

# IP Hash (Sticky Sessions)

Some applications store user sessions in server memory.

To ensure a user always reaches the same backend server, Nginx provides **IP Hash**.

Configuration:

```nginx
upstream backend {

    ip_hash;

    server app1;

    server app2;

}
```

Example:

```text
Client IP

192.168.1.20

↓

Server 1

↓

Future Requests

↓

Server 1
```

The same client IP is consistently routed to the same backend.

---

# Weighted Round Robin

Sometimes servers have different hardware capacities.

Example:

```nginx
upstream backend {

    server app1 weight=4;

    server app2 weight=2;

    server app3 weight=1;

}
```

Approximate distribution:

```text
App1

57%

App2

29%

App3

14%
```

Powerful servers receive more traffic.

---

# Load Balancing Comparison

| Algorithm | Best For |
|------------|----------|
| Round Robin | General-purpose applications |
| Least Connections | Long-running requests |
| IP Hash | Sticky Sessions |
| Weighted | Mixed hardware environments |

---

# Sticky Sessions

Sticky Sessions ensure that a user's requests continue reaching the same backend server.

Example:

```text
User Login

↓

Server 2

↓

Shopping Cart

↓

Server 2

↓

Checkout

↓

Server 2
```

Without sticky sessions:

```text
Login

↓

Server 1

↓

Checkout

↓

Server 3
```

The application may lose session information if sessions are stored locally.

> **Modern Recommendation:** Instead of relying on sticky sessions, many production systems store sessions in **Redis**, **Memcached**, or use **JWT-based authentication**, allowing any backend server to process the request.

---

# Health Checks

Suppose one backend server crashes.

Without health checks:

```text
Client

↓

Nginx

↓

Offline Server

↓

Error
```

Nginx supports passive health checks.

Example:

```nginx
upstream backend {

    server app1 max_fails=3 fail_timeout=30s;

    server app2;

}
```

Meaning:

- After three consecutive failures
- Mark the server unavailable
- Retry after thirty seconds

---

# Backup Server

A backup server handles requests only if all primary servers fail.

Example:

```nginx
upstream backend {

    server app1;

    server app2;

    server backup-server backup;

}
```

Normal traffic:

```text
App1

App2
```

If both fail:

```text
Backup Server
```

---

# Architecture Example

```text
                 Internet

                     │

                     ▼

                 Load Balancer

                     │

                     ▼

                    Nginx

          ┌──────────┼──────────┐

          ▼          ▼          ▼

     Django 1    Django 2    Django 3

          │          │          │

          └──────────┼──────────┘

                     ▼

               PostgreSQL
```

Each application server runs the same codebase.

---

# Microservices Example

```text
                 Client

                    │

                    ▼

                  Nginx

        ┌───────────┼───────────┐

        ▼           ▼           ▼

   User API    Order API   Payment API

        │

        ▼

 Multiple Instances
```

Each service can have its own upstream group.

---

# Scaling Strategies

## Vertical Scaling

Increase server resources.

```text
2 CPU

↓

8 CPU

↓

16 CPU
```

Advantages:

- Simple

Disadvantages:

- Hardware limits
- Downtime during upgrades
- Higher cost

---

## Horizontal Scaling

Add additional servers.

```text
Server 1

↓

Server 1

Server 2

↓

Server 1

Server 2

Server 3
```

Advantages:

- Better availability
- Better scalability
- Easier maintenance

Modern cloud-native applications generally favor horizontal scaling.

---

# Real-World Example

A streaming platform receives:

```
500,000 users
```

Architecture:

```text
Users

↓

Nginx

↓

Round Robin

↓

Streaming Server 1

Streaming Server 2

Streaming Server 3
```

If one server becomes unavailable:

```text
Server 2

↓

Offline

↓

Traffic automatically redistributed
```

The service remains available.

---

# Best Practices

- Use **Round Robin** for most applications.
- Use **Least Connections** when request durations vary significantly.
- Prefer centralized session storage over sticky sessions.
- Configure health checks for backend servers.
- Monitor backend CPU, memory, and response times.
- Scale horizontally as traffic increases.

---

# Common Mistakes

## Assuming Load Balancing Solves Performance Problems

Load balancing distributes traffic.

It does **not** optimize:

- Slow SQL queries
- Inefficient algorithms
- Memory leaks

Application performance must still be optimized.

---

## Storing Sessions on Individual Servers

If sessions are stored locally:

```text
Login

↓

Server 1

↓

Next Request

↓

Server 2
```

The user may appear logged out.

Use Redis, Memcached, or database-backed sessions.

---

## Ignoring Server Health

Without proper failure detection, requests may continue being sent to unavailable servers.

---

# Interview Notes

### Beginner Questions

- What is load balancing?
- Why is load balancing needed?
- What is an upstream block?
- What is the default load balancing algorithm?

---

### Intermediate Questions

- Explain Round Robin.
- Explain Least Connections.
- What are Sticky Sessions?
- What is IP Hash?
- Why are centralized session stores preferred over Sticky Sessions?
- How does Nginx handle backend server failures?

---

# Key Takeaways

- Load balancing distributes incoming traffic across multiple backend servers.
- The `upstream` directive defines backend server groups.
- Round Robin is the default load balancing algorithm.
- Nginx also supports Least Connections, IP Hash, and Weighted Round Robin.
- Passive health checks help prevent traffic from reaching failed servers.
- Modern architectures combine Nginx load balancing with centralized session storage, horizontal scaling, and continuous monitoring.