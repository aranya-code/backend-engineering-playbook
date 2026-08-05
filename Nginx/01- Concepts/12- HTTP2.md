# Overview

HTTP/2 is the second major version of the Hypertext Transfer Protocol (HTTP).

It was designed to solve many of the performance limitations of HTTP/1.1 while remaining fully compatible with existing web applications.

Unlike HTTP/1.1, HTTP/2 focuses on reducing latency and improving network efficiency by introducing features such as:

- Binary protocol
- Header compression
- Persistent connections
- Multiplexing
- Server Push

Today, HTTP/2 is supported by all major browsers and is widely used in production systems.

---

# Why HTTP/2 Was Introduced

HTTP/1.1 worked well for many years but had several limitations.

For example:

- One request often blocked another.
- Multiple TCP connections were required.
- Headers were repeatedly transmitted.
- High latency for modern websites with many assets.

Modern web applications contain:

- HTML
- CSS
- JavaScript
- Images
- Fonts
- APIs
- Videos

Loading hundreds of resources efficiently became increasingly difficult with HTTP/1.1.

HTTP/2 was introduced to solve these problems.

---

# HTTP/1.1 Request Flow

A browser requests multiple resources.

```text
Browser

 │

 ├──── HTML

 ├──── CSS

 ├──── JavaScript

 ├──── Images

 └──── Fonts
```

With HTTP/1.1, multiple TCP connections are often required to improve performance.

---

# HTTP/2 Request Flow

```text
Browser

      │

      ▼

 Single TCP Connection

      │

      ▼

 Multiple Parallel Streams

      │

 ┌────┼────┬────┬────┐

 ▼    ▼    ▼    ▼    ▼

HTML CSS JS IMG Font
```

A single connection carries multiple requests and responses simultaneously.

---

# Binary Protocol

HTTP/1.1 is a **text-based protocol**.

Example:

```http
GET /products HTTP/1.1
Host: example.com
```

HTTP/2 converts communication into **binary frames**.

Instead of sending plain text, data is encoded into binary before transmission.

Benefits:

- Faster parsing
- Reduced errors
- More efficient communication
- Better performance

Applications still use HTTP normally.

The binary conversion happens internally between the browser and the server.

---

# Header Compression (HPACK)

HTTP requests often contain many repeated headers.

Example:

```http
Host: api.example.com

User-Agent: Chrome

Accept: */*

Cookie: session=abc123
```

When a browser sends hundreds of requests, many of these headers remain identical.

Instead of sending them repeatedly, HTTP/2 compresses headers using **HPACK**.

Benefits:

- Smaller request size
- Lower bandwidth usage
- Faster communication

---

# Persistent Connection

HTTP/2 uses a **single long-lived TCP connection**.

```text
Browser

      │

One TCP Connection

      │

      ▼

Nginx
```

Instead of opening and closing multiple connections, the same connection remains open.

Benefits:

- Reduced latency
- Lower connection overhead
- Better resource utilization

---

# Multiplexing

One of HTTP/2's biggest improvements is **multiplexing**.

Multiple requests can travel simultaneously over the same TCP connection.

Without waiting for one request to complete before sending the next.

Example:

```text
Connection

│

├── Stream 1 → HTML

├── Stream 2 → CSS

├── Stream 3 → JavaScript

├── Stream 4 → Image

└── Stream 5 → API
```

Every stream is independent.

If one stream is delayed, the others continue processing.

---

# Server Push

HTTP/2 introduced **Server Push**.

Normally:

```text
Browser

↓

Requests CSS

↓

Server

↓

Returns CSS
```

With Server Push:

```text
Browser

↓

Requests HTML

↓

Server

↓

Returns HTML

+

Automatically Pushes

CSS

JavaScript

Fonts
```

The server proactively sends resources that it knows the browser will need.

This reduces additional round trips.

> **Note:** Although Server Push is part of the HTTP/2 specification, it is no longer widely recommended. Modern browsers have reduced or removed support, and many production systems now rely on techniques such as `preload` headers instead.

---

# HTTP/1.1 vs HTTP/2

| Feature | HTTP/1.1 | HTTP/2 |
|----------|-----------|---------|
| Protocol | Text | Binary |
| Header Compression | No | Yes (HPACK) |
| Multiplexing | No | Yes |
| Persistent Connection | Limited | Improved |
| Server Push | No | Yes (limited modern use) |
| Performance | Good | Better |

---

# HTTP/2 in Nginx

HTTP/2 is enabled on HTTPS server blocks.

Example:

```nginx
server {

    listen 443 ssl http2;

    server_name example.com;

}
```

The `http2` parameter enables HTTP/2 support.

---

# HTTPS Requirement

Although the HTTP/2 specification does not strictly require encryption, **all major browsers support HTTP/2 only over HTTPS**.

Typical production setup:

```text
Browser

HTTPS

↓

Nginx

↓

HTTP/2

↓

Application
```

For this reason, HTTP/2 is almost always deployed together with SSL/TLS.

---

# Request Processing with HTTP/2

```text
Browser

      │

      ▼

Single HTTPS Connection

      │

      ▼

Nginx

      │

Multiple Streams

      │

 ┌────┬────┬────┐

 ▼    ▼    ▼    ▼

API  CSS JS IMG

      │

      ▼

Responses Returned
Simultaneously
```

---

# Real-World Example

Suppose an online shopping website contains:

- 1 HTML page
- 8 CSS files
- 12 JavaScript files
- 45 Images
- 10 API calls

With HTTP/1.1:

- Multiple TCP connections
- Higher latency
- More waiting

With HTTP/2:

- Single persistent connection
- Multiplexed streams
- Compressed headers
- Faster page rendering

Users experience noticeably faster page loads, especially on high-latency networks.

---

# Benefits of HTTP/2

- Faster page loading
- Reduced latency
- Better bandwidth utilization
- Lower network overhead
- Improved browser performance
- Better support for modern web applications
- Efficient handling of many simultaneous requests

---

# Best Practices

- Always enable HTTP/2 for HTTPS-enabled websites.
- Use modern TLS versions and strong cipher suites.
- Continue to optimize images and static assets; HTTP/2 is not a replacement for good optimization practices.
- Enable Gzip or Brotli together with HTTP/2 for text-based responses.
- Monitor browser compatibility and server performance after enabling HTTP/2.

---

# Common Mistakes

## Assuming HTTP/2 Makes Optimization Unnecessary

HTTP/2 improves transport efficiency but does not eliminate the need for:

- Image optimization
- Compression
- Browser caching
- Efficient application code

---

## Enabling HTTP/2 Without HTTPS

Most browsers require HTTPS before using HTTP/2.

Without HTTPS, browsers typically fall back to HTTP/1.1.

---

## Expecting Server Push to Improve Every Website

Server Push is no longer broadly supported by browsers and is rarely recommended for new deployments.

Focus on modern optimization techniques such as caching, compression, and preload hints.

---

# Interview Notes

### Beginner Questions

- What is HTTP/2?
- Why was HTTP/2 introduced?
- What is a binary protocol?
- What is header compression?
- What is multiplexing?

---

### Intermediate Questions

- Compare HTTP/1.1 and HTTP/2.
- Explain HPACK.
- Why is multiplexing faster than HTTP/1.1?
- Why is HTTP/2 commonly used with HTTPS?
- Is Server Push still recommended today?

---

# Key Takeaways

- HTTP/2 is a major improvement over HTTP/1.1, designed to reduce latency and improve efficiency.
- It introduces a binary protocol, HPACK header compression, multiplexing, and improved persistent connections.
- HTTP/2 is typically enabled in Nginx using the `http2` parameter on HTTPS server blocks.
- Most modern browsers use HTTP/2 only over HTTPS.
- Combined with Gzip/Brotli, caching, and efficient application design, HTTP/2 significantly improves the performance of modern web applications.