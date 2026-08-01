# Request & Response Compression

## Overview

As APIs grow in popularity, the amount of data transferred between clients and backend services increases significantly. Large request and response payloads consume more bandwidth, increase latency, and lead to higher network costs.

Amazon API Gateway supports **payload compression**, allowing responses (and incoming requests from clients) to be compressed using **Gzip** before transmission.

Compression helps:

- Reduce network bandwidth
- Improve response times
- Lower data transfer costs
- Improve mobile application performance
- Improve user experience on slower networks

Compression is especially beneficial for APIs that return large JSON responses.

---

# Why Compression?

Suppose an API returns:

```text
Response Size

↓

1 MB JSON
```

Without compression:

```text
Client

↓

1 MB Download
```

With Gzip compression:

```text
Client

↓

250 KB Download
```

Approximately 75% less data is transferred.

---

# Architecture

```text
                Client

                   │

           Accept-Encoding

              gzip

                   │

                   ▼

         Amazon API Gateway

                   │

        Compress Response

                   │

                   ▼

      Lambda / ECS / EC2
```

API Gateway compresses the response before sending it to the client.

---

# Compression Flow

```text
Client

↓

Accept-Encoding: gzip

↓

API Gateway

↓

Compress Response

↓

Client

↓

Decompress Automatically
```

Modern browsers and HTTP clients automatically decompress responses.

---

# HTTP Compression

Compression is based on standard HTTP headers.

Client request:

```http
GET /products

Accept-Encoding: gzip
```

Response:

```http
Content-Encoding: gzip
```

The browser or client library handles decompression automatically.

---

# Response Compression

Example:

Backend returns:

```json
{
    "products":[ ... thousands of records ... ]
}
```

API Gateway:

```text
Compress

↓

Gzip

↓

Send Response
```

Clients receive the compressed payload.

---

# Minimum Compression Size

API Gateway compresses responses only if they exceed a configured size.

Example:

```text
Minimum Compression Size

1024 Bytes
```

Responses smaller than 1 KB are returned uncompressed.

This avoids wasting CPU on very small payloads.

---

# Small Response Example

Response:

```text
500 Bytes
```

Result:

```text
No Compression
```

Compression overhead would outweigh any benefit.

---

# Large Response Example

Response:

```text
500 KB
```

Result:

```text
Compress

↓

120 KB
```

Network transfer time decreases significantly.

---

# Compression Algorithm

API Gateway supports:

```text
Gzip
```

Gzip is:

- Widely supported
- Fast
- Highly efficient for JSON and text data

---

# Content Types

Compression is most effective for:

- JSON
- XML
- HTML
- CSS
- JavaScript
- CSV
- Plain Text

Compression provides limited benefit for already compressed formats such as:

- JPEG
- PNG
- MP4
- ZIP
- PDF

---

# Client Support

Clients indicate supported compression algorithms.

Example:

```http
Accept-Encoding:

gzip
```

If supported:

```http
Content-Encoding:

gzip
```

If not:

```text
Plain Response
```

---

# Request Compression

Some HTTP clients also compress request bodies.

Example:

```http
Content-Encoding:

gzip
```

The client compresses the payload before sending it.

The backend or integration must be able to process compressed request bodies if this behavior is used.

---

# Compression and Latency

Without compression:

```text
Large Response

↓

Long Network Transfer
```

With compression:

```text
Compression Time

+

Smaller Payload

↓

Lower Overall Latency
```

Although CPU time is used for compression, overall response time is often reduced due to less data being transferred.

---

# Compression vs Caching

| Compression | API Caching |
|-------------|-------------|
| Reduces payload size | Eliminates backend calls |
| Saves bandwidth | Saves compute resources |
| Applied to every response | Applied only on cache hits |
| Improves transfer speed | Improves response time |

Both features can be enabled simultaneously.

---

# Compression vs CloudFront

| API Gateway Compression | CloudFront Compression |
|-------------------------|-------------------------|
| Compresses API responses | Compresses CDN responses |
| Before leaving API Gateway | At Edge Locations |
| REST APIs | Static & Dynamic Content |

Many production systems use both.

---

# Benefits

## Reduced Bandwidth

Smaller payloads reduce network usage.

---

## Lower Latency

Less data travels across the network.

---

## Lower Data Transfer Costs

Especially beneficial for high-volume public APIs.

---

## Better Mobile Experience

Mobile users benefit from smaller downloads and faster page loads.

---

## Faster APIs

Large JSON responses reach clients more quickly.

---

# Limitations

Compression:

- Uses additional CPU resources.
- Provides little benefit for already compressed files.
- May not improve very small responses.
- Should be configured with an appropriate minimum response size.

---

# Real-World Example

An e-commerce platform returns a product catalog.

Without compression:

```text
2 MB JSON

↓

Customer
```

With compression:

```text
2 MB JSON

↓

450 KB Gzip

↓

Customer
```

Customers experience significantly faster downloads, especially on mobile networks.

---

# Best Practices

- Enable compression for production REST APIs.
- Configure an appropriate minimum compression size.
- Compress large JSON and XML responses.
- Do not rely on compression for already compressed file formats.
- Test API performance before and after enabling compression.
- Combine compression with API Gateway Caching and CloudFront for maximum performance.
- Monitor latency and bandwidth usage using CloudWatch.

---

# Common Interview Questions

### What is API Gateway Compression?

API Gateway Compression reduces the size of HTTP payloads using Gzip before sending them to clients, improving performance and reducing bandwidth usage.

---

### Which compression algorithm does API Gateway support?

API Gateway supports **Gzip** compression.

---

### Does API Gateway compress every response?

No.

Only responses larger than the configured **Minimum Compression Size** are compressed.

---

### Which HTTP headers are used for compression?

Clients send:

```http
Accept-Encoding: gzip
```

API Gateway responds with:

```http
Content-Encoding: gzip
```

---

### Which types of responses benefit the most from compression?

Large text-based payloads such as JSON, XML, HTML, CSS, JavaScript, and CSV benefit the most.

---

# Key Takeaways

- API Gateway uses **Gzip compression** to reduce the size of HTTP payloads.
- Compression lowers bandwidth usage, improves response times, and reduces data transfer costs.
- Responses are compressed only when they exceed the configured minimum compression size.
- Compression is most effective for large text-based payloads such as JSON and XML.
- Combining compression with API Gateway Caching and CloudFront provides an efficient, high-performance API architecture.