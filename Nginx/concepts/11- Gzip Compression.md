# Overview

One of the easiest ways to improve website performance is by reducing the size of data sent from the server to the client.

Nginx supports **Gzip Compression**, which compresses HTTP responses before sending them to clients.

Smaller responses mean:

- Faster page loads
- Reduced bandwidth usage
- Better user experience
- Lower infrastructure costs

Most modern websites and REST APIs enable Gzip compression by default.

---

# What is Gzip?

**Gzip** is a lossless compression algorithm that reduces the size of HTTP responses.

Instead of sending the original file, Nginx compresses it first.

The browser automatically decompresses the response after receiving it.

The user never notices this process.

---

# Why Compression Matters

Suppose your HTML page is:

```
250 KB
```

After Gzip compression:

```
45 KB
```

Instead of transferring 250 KB across the network, only 45 KB is transferred.

Benefits:

- Faster downloads
- Lower latency
- Reduced network traffic
- Faster API responses

---

# How Gzip Works

```text
               Browser
                   │
         HTTP Request
                   │
                   ▼
               Nginx Server
                   │
        Compress Response
          Using Gzip
                   │
                   ▼
         Compressed Response
                   │
                   ▼
              Browser
        Automatically
        Decompresses
```

The browser handles decompression automatically.

---

# Compression Flow

```text
Original File

      │

      ▼

Nginx Compression

      │

      ▼

Compressed Data

      │

      ▼

Internet

      │

      ▼

Browser

      │

      ▼

Decompressed Page
```

---

# Enabling Gzip

The simplest configuration:

```nginx
gzip on;
```

This enables Gzip compression.

---

# Checking Browser Support

Browsers indicate whether they support Gzip using the request header:

```http
Accept-Encoding: gzip
```

If this header is present:

```
Nginx

↓

Compress Response
```

Otherwise:

```
Nginx

↓

Send Original Response
```

---

# Basic Configuration

```nginx
http {

    gzip on;

}
```

This enables Gzip globally.

---

# Compression Level

Nginx allows different compression levels.

Directive:

```nginx
gzip_comp_level 6;
```

Range:

```
1 → Fastest

↓

9 → Maximum Compression
```

Trade-off:

| Level | CPU Usage | Compression |
|--------|-----------|-------------|
| 1 | Very Low | Lower |
| 3 | Low | Good |
| 5 | Moderate | Better |
| 6 | Recommended | Excellent |
| 9 | High | Maximum |

Most production systems use:

```nginx
gzip_comp_level 5;
```

or

```nginx
gzip_comp_level 6;
```

---

# Minimum Response Size

Very small responses usually should not be compressed.

Directive:

```nginx
gzip_min_length 1024;
```

Meaning:

Only compress responses larger than **1024 bytes**.

---

# HTTP Version

Compression normally works with HTTP/1.1 and above.

Example:

```nginx
gzip_http_version 1.1;
```

---

# MIME Types

Not every file type should be compressed.

Nginx compresses only the specified content types.

Example:

```nginx
gzip_types
    text/plain
    text/css
    text/javascript
    application/javascript
    application/json
    application/xml
    application/rss+xml
    image/svg+xml;
```

Commonly compressed:

- HTML
- CSS
- JavaScript
- JSON
- XML
- SVG

---

# Files That Should Not Be Compressed

Already compressed files gain little or no benefit.

Examples:

- JPEG
- PNG
- GIF
- MP4
- ZIP
- PDF

Compressing these files wastes CPU resources.

---

# Complete Configuration

```nginx
http {

    gzip on;

    gzip_comp_level 6;

    gzip_min_length 1024;

    gzip_http_version 1.1;

    gzip_types
        text/plain
        text/css
        application/json
        application/javascript
        text/xml
        application/xml
        image/svg+xml;

}
```

This is a common production-ready starting point.

---

# How Compression Improves Performance

Without Gzip:

```text
Client

    │

250 KB

    │

Internet

    │

250 KB

    ▼

Browser
```

---

With Gzip:

```text
Client

    │

45 KB

    │

Internet

    │

45 KB

    ▼

Browser
```

The browser automatically restores the original content.

---

# Gzip and APIs

Compression is especially useful for REST APIs.

Example response:

```json
{
    "products": [
        ...
    ]
}
```

Large JSON payloads compress extremely well.

Benefits:

- Faster API responses
- Lower bandwidth consumption
- Better mobile performance

---

# Gzip and Static Files

Static resources commonly compressed:

- CSS
- JavaScript
- HTML
- SVG
- XML

Example:

```text
style.css

↓

Gzip

↓

Browser
```

This reduces page load time significantly.

---

# Gzip vs Brotli

| Feature | Gzip | Brotli |
|----------|-------|---------|
| Compression Ratio | Good | Better |
| CPU Usage | Lower | Higher |
| Browser Support | Excellent | Excellent |
| Speed | Fast | Slightly Slower |
| Production Usage | Very Common | Increasing |

Brotli generally produces smaller files than Gzip but requires more CPU during compression.

Many production environments support both.

---

# Real-World Example

Suppose an e-commerce website serves:

```
home.html
```

Original size:

```
320 KB
```

Compressed:

```
58 KB
```

Every visitor downloads approximately **80% less data**.

For websites with thousands of users, this results in:

- Faster page loads
- Lower CDN costs
- Reduced bandwidth usage
- Better SEO scores

---

# Best Practices

- Enable Gzip globally in the `http` context.
- Use `gzip_comp_level 5` or `6` for production.
- Compress text-based content only.
- Avoid compressing already compressed files.
- Test performance after enabling compression.
- Combine Gzip with browser caching for optimal performance.

---

# Common Mistakes

## Compressing Images

Images such as:

- JPEG
- PNG
- GIF

are already compressed.

Running Gzip on them increases CPU usage without meaningful size reduction.

---

## Using Maximum Compression

Setting:

```nginx
gzip_comp_level 9;
```

does not always provide a noticeable improvement over level 6 but requires significantly more CPU.

---

## Compressing Tiny Responses

Compressing very small responses can increase CPU overhead while providing little benefit.

Use:

```nginx
gzip_min_length
```

to avoid unnecessary compression.

---

# Interview Notes

### Beginner Questions

- What is Gzip?
- Why is Gzip used?
- How does browser decompression work?
- Which directive enables Gzip?

---

### Intermediate Questions

- What is `gzip_comp_level`?
- Which MIME types should be compressed?
- Why shouldn't JPEG images be compressed again?
- Explain the trade-off between CPU usage and compression level.
- Compare Gzip and Brotli.

---

# Key Takeaways

- Gzip compresses HTTP responses before sending them to clients.
- Smaller responses improve performance and reduce bandwidth usage.
- Enable compression using the `gzip on` directive.
- Use `gzip_comp_level 5` or `6` for a good balance between performance and CPU usage.
- Compress text-based resources such as HTML, CSS, JavaScript, JSON, XML, and SVG.
- Avoid compressing files that are already compressed, such as images and videos.
- Gzip is a simple yet highly effective optimization used in almost every production Nginx deployment.