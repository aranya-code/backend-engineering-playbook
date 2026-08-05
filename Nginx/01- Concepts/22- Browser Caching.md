# Overview

Every time a user visits a website, the browser downloads resources such as:

- HTML
- CSS
- JavaScript
- Images
- Fonts
- Videos

If these resources are downloaded on every page visit, unnecessary network traffic is generated and page loading becomes slower.

**Browser Caching** allows the browser to store resources locally and reuse them for future requests.

This reduces:

- Network traffic
- Server load
- Page load time
- Bandwidth consumption

Browser caching is one of the simplest and most effective ways to improve website performance.

---

# What is Browser Caching?

Browser caching stores previously downloaded resources on the user's device.

Instead of downloading the same file again:

```text
Browser

↓

Internet

↓

Nginx

↓

Download CSS
```

The browser can reuse the cached copy.

```text
Browser

↓

Local Cache

↓

Load CSS
```

No request reaches the server.

---

# Browser Cache Workflow

```text
           Browser

               │

        Resource Cached?

          │          │

         Yes         No

          │          │

          ▼          ▼

 Use Cached      Request File

   Resource           │

                      ▼

                    Nginx

                      │

                Return Response

                      │

                      ▼

              Store in Browser
```

---

# Why Browser Caching?

Suppose a website contains:

- 1 HTML page
- 3 CSS files
- 8 JavaScript files
- 25 Images

Without caching:

```text
Every Page Visit

↓

Download Everything Again
```

With browser caching:

```text
First Visit

↓

Download Files

↓

Store in Cache

↓

Next Visit

↓

Reuse Cached Files
```

The page loads significantly faster.

---

# Cache-Control Header

The primary mechanism for browser caching is the **Cache-Control** header.

Example:

```nginx
add_header Cache-Control "public, max-age=3600";
```

Meaning:

- Public resource
- Cache for 3600 seconds

---

# Understanding Cache-Control

Example:

```http
Cache-Control: public, max-age=86400
```

Meaning:

```
public

↓

Anyone may cache

+

86400 seconds

↓

24 Hours
```

The browser can reuse the file for one day.

---

# Common Cache-Control Directives

| Directive | Description |
|------------|-------------|
| public | Resource may be cached by browsers and proxies |
| private | Cache only in the browser |
| no-cache | Validate before using cached copy |
| no-store | Never cache |
| max-age | Cache lifetime in seconds |
| immutable | Resource will not change during cache lifetime |

---

# Expires Header

Before `Cache-Control` became standard, browsers used the **Expires** header.

Example:

```nginx
expires 7d;
```

Equivalent response:

```http
Expires: Wed, 23 Jul 2026 12:00:00 GMT
```

Modern applications typically rely on `Cache-Control`, but `expires` remains widely used because Nginx automatically generates the appropriate headers.

---

# The `expires` Directive

Example:

```nginx
location /static {

    expires 30d;

}
```

Meaning:

```
Cache Static Files

↓

30 Days
```

---

# Static Asset Caching

A common production configuration:

```nginx
location /static {

    expires 30d;

    add_header Cache-Control "public";

}
```

Resources:

- CSS
- JavaScript
- Images
- Fonts

are stored locally by the browser.

---

# Long-Term Caching

Versioned assets can be cached for much longer.

Example:

```nginx
location ~* \.(css|js|png|jpg|svg|woff2)$ {

    expires 365d;

    add_header Cache-Control "public, immutable";

}
```

Benefits:

- Extremely fast repeat visits
- Lower bandwidth usage
- Reduced server requests

---

# What is `immutable`?

Example:

```http
Cache-Control: public, max-age=31536000, immutable
```

Meaning:

The browser assumes the file will **never change** during its cache lifetime.

Suitable for:

- Versioned CSS
- Versioned JavaScript
- Fonts
- Logos

---

# Cache Busting

If browsers cache a file for one year, how do users receive updates?

The solution is **Cache Busting**.

Old file:

```
style.css
```

New file:

```
style.v2.css
```

or

```
style.css?v=2
```

Since the URL changes, browsers download the updated file.

---

# ETag

An **ETag (Entity Tag)** uniquely identifies a specific version of a resource.

Example:

```http
ETag: "abc123"
```

Later:

```text
Browser

↓

If-None-Match: "abc123"

↓

Server
```

If the file has not changed:

```http
304 Not Modified
```

The browser continues using the cached copy.

---

# Last-Modified

Nginx can also indicate when a file was last updated.

Example:

```http
Last-Modified: Tue, 15 Jul 2026 09:30:00 GMT
```

Next request:

```http
If-Modified-Since: Tue, 15 Jul 2026 09:30:00 GMT
```

If unchanged:

```http
304 Not Modified
```

The browser reuses the cached resource.

---

# Conditional Requests

Instead of downloading the file again:

```text
Browser

↓

Has File

↓

Ask Server

↓

Changed?
```

Server replies:

```
304 Not Modified
```

No file is transferred.

Benefits:

- Lower bandwidth
- Faster loading
- Reduced server workload

---

# Browser Caching vs Proxy Cache

| Browser Cache | Proxy Cache |
|---------------|-------------|
| Stored in browser | Stored by Nginx |
| Client-side | Server-side |
| Reduces browser downloads | Reduces backend requests |
| Per user | Shared across users |

Many production systems use both together.

---

# Browser Caching vs FastCGI Cache

| Browser Cache | FastCGI Cache |
|---------------|---------------|
| Browser stores resources | Nginx stores FastCGI responses |
| Improves page reload speed | Reduces PHP processing |
| Client-side optimization | Server-side optimization |

---

# Django Example

Typical project:

```text
project/

└── static/

    ├── css

    ├── js

    └── images
```

Configuration:

```nginx
location /static {

    expires 30d;

    add_header Cache-Control "public";

}
```

The browser caches Django static files.

---

# FastAPI Example

Suppose uploaded images are public.

```nginx
location /uploads {

    expires 30d;

    add_header Cache-Control "public";

}
```

Frequently viewed images load much faster on subsequent visits.

---

# Real-World Example

An online shopping website contains:

```
Homepage

↓

CSS

↓

JavaScript

↓

Images

↓

Fonts
```

First visit:

```
12 MB Downloaded
```

Second visit:

```
450 KB Downloaded
```

Only new or changed resources are downloaded.

---

# Best Practices

- Cache static assets aggressively.
- Use versioned filenames for CSS and JavaScript.
- Use `immutable` only for files whose URLs change when content changes.
- Avoid caching dynamic HTML pages unless appropriate.
- Combine browser caching with Gzip or Brotli compression.
- Test cache behavior using browser developer tools.

---

# Common Mistakes

## Caching Dynamic Pages

Avoid caching pages containing:

- User profiles
- Shopping carts
- Payment information
- Personalized dashboards

These pages often require fresh content.

---

## Forgetting Cache Busting

If a file changes but the URL stays the same:

```
style.css
```

Users may continue using the old cached version.

Always use versioned filenames or query strings for long-lived assets.

---

## Using Very Short Cache Times

Caching static assets for only a few minutes reduces the benefits of browser caching.

Choose cache durations based on how frequently assets change.

---

# Interview Notes

### Beginner Questions

- What is browser caching?
- Why is browser caching important?
- What does the `expires` directive do?
- What is the purpose of the `Cache-Control` header?

---

### Intermediate Questions

- Explain `ETag` and `Last-Modified`.
- What is cache busting?
- What does `immutable` mean?
- Compare Browser Cache, Proxy Cache, and FastCGI Cache.
- When should browser caching be avoided?

---

# Key Takeaways

- Browser caching stores resources on the client to reduce repeated downloads.
- The `Cache-Control` header and `expires` directive control browser cache behavior.
- `ETag` and `Last-Modified` enable efficient cache validation using conditional requests.
- Versioned filenames and cache busting ensure users receive updated assets while benefiting from long cache lifetimes.
- Browser caching, combined with server-side caching and compression, significantly improves website performance and reduces bandwidth consumption.