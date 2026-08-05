# Overview

One of the biggest reasons behind Nginx's popularity is its **architecture**.

Unlike traditional web servers that create a new thread or process for every client, Nginx follows an **asynchronous event-driven architecture**.

This allows it to:

- Handle thousands of simultaneous connections
- Consume very little memory
- Scale efficiently
- Deliver high performance under heavy traffic

This chapter explains the internal architecture that makes all of this possible.

---

# High-Level Architecture

A simplified Nginx architecture looks like this:

```text
                   Clients
                      │
                      │
         ┌────────────┴────────────┐
         │                         │
         ▼                         ▼
      Client 1                 Client N
                │
                ▼
        +----------------+
        | Master Process |
        +----------------+
                 │
      ┌──────────┼──────────┐
      │          │          │
      ▼          ▼          ▼
 Worker 1    Worker 2    Worker 3
      │          │          │
      └──────────┼──────────┘
                 ▼
         Handles Client Requests
```

The **Master Process** manages the server.

The **Worker Processes** perform the actual work.

---

# Master Process

The Master Process is the **controller** of Nginx.

It does **not** process client requests.

Instead, it is responsible for managing worker processes.

## Responsibilities

- Reads the configuration file
- Validates configuration
- Starts worker processes
- Stops worker processes
- Reloads configuration
- Gracefully restarts workers
- Monitors worker health

Think of the Master Process as a **manager** supervising multiple employees.

---

# Worker Processes

Worker Processes perform the real work.

Every incoming client request is handled by a worker process.

Responsibilities include:

- Accepting client connections
- Reading HTTP requests
- Serving static files
- Forwarding requests to upstream servers
- Compressing responses
- Writing logs
- Closing client connections

Unlike the Master Process, Worker Processes are responsible for actual traffic.

---

# How Requests Flow

```text
Browser

   │

   ▼

Master Process
   │
   │ (Assigns Workers)
   ▼

Worker Process

   │

   ▼

Process Request

   │

   ▼

Return Response
```

Notice that the Master Process **does not process the request itself**.

It only creates and manages Worker Processes.

---

# Worker Processes vs Worker Connections

Many beginners confuse these two concepts.

## Worker Process

A Worker Process is an operating system process.

Example:

```text
worker_processes 4;
```

This means Nginx creates **4 Worker Processes**.

---

## Worker Connections

Each Worker Process can handle many client connections simultaneously.

Example:

```nginx
events {
    worker_connections 1024;
}
```

This means:

- 1 Worker Process
- can handle 1024 simultaneous connections

If there are four workers:

```
4 × 1024 = 4096 concurrent connections
```

This is only a simplified calculation. The actual number also depends on file descriptors, keep-alive connections, and operating system limits.

---

# Event-Driven Architecture

Traditional servers block while waiting for clients.

Nginx does not.

Instead, it waits for events.

Examples of events:

- Client connected
- Request received
- File ready
- Database response arrived
- Socket became writable
- Response completed

Instead of creating a new thread for every request, one worker keeps listening for these events.

---

# Traditional Server Model

```text
Client 1 → Thread 1

Client 2 → Thread 2

Client 3 → Thread 3

Client 4 → Thread 4

...
```

Problems:

- High memory usage
- More CPU context switching
- Poor scalability

---

# Nginx Event Loop

```text
Worker Process

       │

       ▼

 Wait for Event

       │

       ▼

 Event Arrives

       │

       ▼

 Process Event

       │

       ▼

 Back to Waiting
```

The worker never creates thousands of threads.

Instead, it continuously processes events.

This is one of the main reasons behind Nginx's excellent performance.

---

# Why Nginx is So Fast

Reasons include:

- Event-driven architecture
- Non-blocking I/O
- Few worker processes
- Low memory usage
- Efficient socket handling
- Optimized file serving
- Kernel event notification mechanisms (such as epoll on Linux)

---

# Worker Processes Configuration

Example:

```nginx
worker_processes auto;
```

This tells Nginx to automatically create one Worker Process per CPU core.

Example:

| CPU Cores | Worker Processes |
|-----------|-----------------:|
| 2 | 2 |
| 4 | 4 |
| 8 | 8 |
| 16 | 16 |

This is the recommended configuration for most production deployments.

---

# Worker Connections Configuration

```nginx
events {

    worker_connections 2048;

}
```

Meaning:

Each Worker Process can maintain up to **2048 simultaneous connections**.

---

# How Concurrency Works

Suppose your configuration is:

```nginx
worker_processes auto;

events {

    worker_connections 1024;

}
```

Server:

- 8 CPU cores
- 8 Worker Processes

Maximum theoretical connections:

```
8 × 1024 = 8192
```

Actual capacity depends on:

- Open file descriptor limits
- Operating system configuration
- Keep-alive settings
- Upstream connections
- Available system resources

---

# Buffers

While processing requests, Nginx stores data in memory buffers.

Examples:

- Request headers
- Request body
- Response headers
- Response body

Using buffers reduces disk access and improves performance.

Later chapters will cover:

- proxy_buffer_size
- proxy_buffers
- client_body_buffer_size
- fastcgi_buffers

---

# Threads vs Processes

| Feature | Process | Thread |
|----------|----------|---------|
| Memory | Separate | Shared |
| Isolation | High | Low |
| Creation Cost | Higher | Lower |
| Used by Nginx | ✅ Worker Processes | Optional Thread Pools |

Nginx primarily relies on **processes**, not threads.

Thread pools are available for specific workloads but are not used for handling every HTTP request.

---

# Real-World Example

Suppose an e-commerce website receives **50,000 users** during a flash sale.

Without an efficient architecture:

- Thousands of threads would consume significant memory.
- The server could become CPU-bound due to context switching.

With Nginx:

- A small number of Worker Processes handle thousands of connections using an event loop.
- Memory usage remains relatively low.
- The server remains responsive even under high concurrency.

This is one reason why Nginx is commonly used in front of high-traffic applications.

---

# Best Practices

- Use `worker_processes auto` unless you have a specific reason not to.
- Tune `worker_connections` based on expected traffic and operating system limits.
- Monitor CPU and memory usage before changing worker settings.
- Avoid setting extremely high connection limits without increasing file descriptor limits.
- Validate configuration changes with:

```bash
nginx -t
```

---

# Common Mistakes

### Setting Too Many Worker Processes

More worker processes than CPU cores can increase context switching without improving performance.

---

### Confusing Workers with Threads

Worker Processes are **operating system processes**, not threads.

---

### Assuming Maximum Connections Are Guaranteed

The calculation:

```
worker_processes × worker_connections
```

is only a theoretical upper limit.

Real-world capacity depends on operating system and application constraints.

---

# Interview Notes

### Beginner Questions

- What is the role of the Master Process?
- What is the role of a Worker Process?
- What is `worker_processes`?
- What is `worker_connections`?

---

### Intermediate Questions

- Explain Nginx's event-driven architecture.
- Why is Nginx more scalable than traditional thread-based servers?
- How does Nginx achieve high concurrency?
- Why is `worker_processes auto` recommended?
- How do Worker Processes differ from Worker Connections?

---

# Key Takeaways

- Nginx separates management (Master Process) from request handling (Worker Processes).
- Worker Processes handle all client traffic.
- One Worker Process can manage thousands of concurrent connections using an event-driven model.
- `worker_processes` controls the number of worker processes.
- `worker_connections` controls how many simultaneous connections each worker can manage.
- Nginx's architecture is one of the main reasons for its speed and scalability.

---

# Quick Revision

- **Master Process** → Manages Nginx
- **Worker Process** → Handles client requests
- **worker_processes** → Number of worker processes
- **worker_connections** → Maximum connections per worker
- **Event-Driven** → Waits for events instead of creating one thread per client
- **Non-Blocking I/O** → Enables efficient handling of many concurrent connections