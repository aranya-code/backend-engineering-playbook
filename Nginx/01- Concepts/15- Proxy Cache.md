# Overview

One of the biggest advantages of using Nginx as a reverse proxy is its ability to **cache responses from backend servers**.

Instead of forwarding every request to the application, Nginx can store backend responses and serve them directly from cache.

This feature is known as **Proxy Cache**.

Proxy Cache is commonly used with:

- Django
- FastAPI
- Flask
- Node.js
- Express.js
- Spring Boot
- ASP.NET Core
- Go APIs

Unlike **FastCGI Cache**, which caches responses from FastCGI applications (such as PHP-FPM), **Proxy Cache** caches responses received over the HTTP protocol.

---

# Why Proxy Cache?

Imagine a product API.

```
GET /products
```

Thousands of users request the same endpoint.

Without caching:

```text
Browser

↓

Nginx

↓

Application

↓

Database

↓

Response
```

Every request reaches the application.

With Proxy Cache:

```text
Browser

↓

Nginx

↓

Cache

↓

Response
```

The backend is skipped whenever a valid cached response exists.

---

# How Proxy Cache Works

```text
                Client

                   │

                   ▼

                 Nginx

                   │

         Cache Available?

            │          │

          Yes          No

           │            │

           ▼            ▼

 Return Cached      Backend API

    Response            │

                        ▼

                Generate Response

                        │

                        ▼

                Store in Cache

                        │

                        ▼

                  Return Client
```

---

# Proxy Cache vs FastCGI Cache

| Feature | Proxy Cache | FastCGI Cache |
|----------|-------------|---------------|
| Backend Protocol | HTTP | FastCGI |
| Typical Backend | Django, FastAPI, Node.js | PHP-FPM |
| Directive | proxy_cache | fastcgi_cache |
| Communication | HTTP | FastCGI Protocol |

---

# Creating a Cache Zone

Before enabling caching, define a cache storage area.

```nginx
proxy_cache_path /var/cache/nginx
levels=1:2
keys_zone=API_CACHE:100m
inactive=60m
max_size=5g;
```

This creates a cache zone named:

```
API_CACHE
```

---

# Understanding `proxy_cache_path`

Syntax:

```nginx
proxy_cache_path path parameters;
```

Example:

```nginx
proxy_cache_path /var/cache/nginx;
```

Nginx stores cached responses in this directory.

---

# Understanding `keys_zone`

Example:

```nginx
keys_zone=API_CACHE:100m
```

Meaning:

- Cache Zone Name

```
API_CACHE
```

- Shared Memory

```
100 MB
```

The shared memory stores metadata for fast cache lookups.

---

# Understanding `levels`

```nginx
levels=1:2
```

Instead of storing every cache file in one directory, Nginx creates nested folders.

Example:

```text
/var/cache/nginx

├── a
│   └── 1f

├── c
│   └── 72

└── e
    └── 99
```

This improves filesystem performance.

---

# Enabling Proxy Cache

Example:

```nginx
location / {

    proxy_cache API_CACHE;

    proxy_pass http://backend;

}
```

Now responses can be stored in the cache.

---

# Cache Key

Each cached response needs a unique identifier.

```nginx
proxy_cache_key "$scheme$request_method$host$request_uri";
```

Example request:

```
GET https://example.com/products?page=2
```

Possible cache key:

```
httpsGETexample.com/products?page=2
```

---

# Cache Validity

Specify how long responses remain cached.

```nginx
proxy_cache_valid 200 30m;

proxy_cache_valid 404 5m;
```

Meaning:

| Status | Cached For |
|---------|-----------:|
| 200 | 30 Minutes |
| 404 | 5 Minutes |

---

# Cache Bypass

Authenticated users often require fresh responses.

Example:

```nginx
proxy_cache_bypass $http_authorization;

proxy_no_cache $http_authorization;
```

If the request contains an Authorization header:

```text
↓

Skip Cache

↓

Forward Request
```

---

# Complete Configuration Example

```nginx
proxy_cache_path /var/cache/nginx
levels=1:2
keys_zone=API_CACHE:100m
inactive=60m
max_size=5g;

server {

    location / {

        proxy_cache API_CACHE;

        proxy_cache_key "$scheme$request_method$host$request_uri";

        proxy_cache_valid 200 30m;

        proxy_pass http://backend;

    }

}
```

---

# Cache Hit and Cache Miss

## Cache Miss

```text
Client

↓

Nginx

↓

Cache

↓

MISS

↓

Backend

↓

Database

↓

Store Response

↓

Client
```

The first request generates the cache.

---

## Cache Hit

```text
Client

↓

Nginx

↓

Cache

↓

HIT

↓

Client
```

The backend is not contacted.

---

# Viewing Cache Status

It is useful to know whether a response came from the cache.

Example:

```nginx
add_header X-Cache-Status $upstream_cache_status;
```

Possible responses:

| Value | Meaning |
|--------|----------|
| MISS | Cache not found |
| HIT | Served from cache |
| BYPASS | Cache skipped |
| EXPIRED | Cache expired |
| STALE | Served stale content while updating |

Example response header:

```http
X-Cache-Status: HIT
```

This is very useful for debugging.

---

# Cache Lock

Without cache locking:

```text
100 Users

↓

100 Requests

↓

Backend
```

All requests reach the application simultaneously.

Enable cache locking:

```nginx
proxy_cache_lock on;
```

Now:

```text
100 Users

↓

First Request

↓

Backend

↓

Create Cache

↓

Remaining Requests

↓

Serve Cached Response
```

Only one request generates the cache.

---

# Serving Stale Cache

Suppose the backend server is temporarily unavailable.

Instead of returning an error, Nginx can serve an older cached response.

Example:

```nginx
proxy_cache_use_stale
error
timeout
updating
http_500
http_502
http_503
http_504;
```

Benefits:

- Higher availability
- Better user experience
- Reduced downtime

---

# Cache Revalidation

To avoid downloading unchanged resources repeatedly:

```nginx
proxy_cache_revalidate on;
```

Nginx validates the cached object with the backend before downloading it again.

---

# Proxy Cache with Django

Architecture:

```text
Browser

↓

Nginx

↓

Proxy Cache

↓

Gunicorn

↓

Django

↓

PostgreSQL
```

Frequently accessed API endpoints can be served directly by Nginx.

---

# Proxy Cache with FastAPI

```text
Browser

↓

Nginx

↓

Proxy Cache

↓

Uvicorn

↓

FastAPI
```

Public API endpoints such as:

```
GET /products

GET /categories

GET /news
```

are ideal candidates for caching.

---

# What Should Be Cached?

Good candidates:

- Public API responses
- Product catalog
- Blog articles
- News pages
- Documentation
- Static JSON responses

Avoid caching:

- Login pages
- Payment pages
- Shopping carts
- User profiles
- Admin dashboard
- Personalized content

---

# Real-World Example

An online store receives:

```
25,000 requests/minute
```

Most users request:

```
GET /products
```

Without Proxy Cache:

```text
25,000

↓

Application

↓

Database
```

With Proxy Cache:

```text
25,000

↓

Nginx Cache

↓

Database receives only occasional requests
```

Benefits:

- Lower CPU usage
- Lower memory usage
- Reduced database load
- Faster responses

---

# Best Practices

- Cache only responses that are safe to reuse.
- Use meaningful cache keys.
- Avoid caching authenticated content.
- Enable cache locking to prevent request storms.
- Monitor cache hit ratios.
- Configure appropriate cache expiration times.
- Use stale cache when backend availability is critical.

---

# Common Mistakes

## Caching Personalized Responses

Never cache pages that contain user-specific information unless the cache key includes the user identity.

---

## Ignoring Authorization Headers

Authenticated requests should generally bypass the cache.

Otherwise, one user's response may be served to another user.

---

## Very Long Cache Durations

Long cache durations can cause outdated information to be served after data changes.

Balance freshness and performance.

---

# Proxy Cache vs Application Cache

| Proxy Cache | Application Cache |
|--------------|-------------------|
| Managed by Nginx | Managed by Application |
| No application code required | Requires application logic |
| Very Fast | Depends on implementation |
| Reduces backend traffic | Reduces computation |

Many production systems use **both** together.

---

# Interview Notes

### Beginner Questions

- What is Proxy Cache?
- Why is Proxy Cache useful?
- How is Proxy Cache different from FastCGI Cache?
- What is a cache hit?

---

### Intermediate Questions

- Explain `proxy_cache_path`.
- What is the purpose of `proxy_cache_key`?
- What does `proxy_cache_lock` do?
- What is stale cache?
- When should Proxy Cache be bypassed?

---

# Key Takeaways

- Proxy Cache stores HTTP responses from backend applications and serves them directly from Nginx.
- It is commonly used with Django, FastAPI, Flask, Node.js, and other HTTP-based application servers.
- Cache zones are defined using `proxy_cache_path`.
- Proper cache keys, cache durations, and bypass rules are essential for correct behavior.
- Features such as cache locking, stale cache, and cache revalidation improve performance and resilience in production.
- Proxy Cache is one of the most effective ways to reduce backend load and improve response times in high-traffic applications.