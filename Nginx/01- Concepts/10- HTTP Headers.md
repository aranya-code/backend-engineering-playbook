# Overview

HTTP headers are additional pieces of information exchanged between the client and the server as part of an HTTP request or response.

Headers contain metadata about:

- The client
- The server
- The request
- The response
- Security policies
- Caching behavior
- Authentication
- Content type

Nginx allows you to read incoming headers and add or modify outgoing response headers.

This is extremely useful for improving:

- Security
- Browser compatibility
- Performance
- Caching
- API communication

---

# What are HTTP Headers?

Every HTTP message consists of three parts:

```text
HTTP Request

Request Line

↓

Headers

↓

Body (Optional)
```

Example:

```http
GET /products HTTP/1.1
Host: api.example.com
User-Agent: Mozilla/5.0
Accept: application/json
Authorization: Bearer xxxxx
```

The lines after the request line are HTTP headers.

---

# HTTP Response Headers

The server also sends headers back to the client.

Example:

```http
HTTP/1.1 200 OK

Content-Type: application/json

Content-Length: 1250

Cache-Control: no-cache

Server: nginx
```

These headers tell the browser how to process the response.

---

# Request vs Response Headers

| Request Headers | Response Headers |
|-----------------|------------------|
| Sent by Client | Sent by Server |
| Describe the request | Describe the response |
| User-Agent | Content-Type |
| Authorization | Cache-Control |
| Accept | Content-Length |
| Cookie | Set-Cookie |

---

# Adding Headers in Nginx

Nginx uses the **add_header** directive to send custom response headers.

Syntax:

```nginx
add_header Header-Name "Value";
```

Example:

```nginx
add_header X-Application "Backend API";
```

Response:

```http
X-Application: Backend API
```

---

# Basic Example

```nginx
server {

    location / {

        add_header X-Server "Nginx";

    }

}
```

Every response includes:

```http
X-Server: Nginx
```

---

# Adding Multiple Headers

```nginx
location / {

    add_header X-App "Backend";

    add_header X-Version "1.0";

    add_header X-Environment "Production";

}
```

Result:

```http
X-App: Backend

X-Version: 1.0

X-Environment: Production
```

---

# Security Headers

One of the most common uses of HTTP headers is improving application security.

## X-Frame-Options

Prevents clickjacking attacks.

```nginx
add_header X-Frame-Options "DENY";
```

Possible values:

- DENY
- SAMEORIGIN

---

## X-Content-Type-Options

Prevents browsers from MIME type sniffing.

```nginx
add_header X-Content-Type-Options "nosniff";
```

---

## Referrer-Policy

Controls how much referrer information is shared.

```nginx
add_header Referrer-Policy "strict-origin-when-cross-origin";
```

---

## Content-Security-Policy (CSP)

Restricts where browsers can load resources from.

Example:

```nginx
add_header Content-Security-Policy "default-src 'self';";
```

CSP helps reduce:

- Cross-Site Scripting (XSS)
- Content injection attacks

---

## Strict-Transport-Security (HSTS)

Forces browsers to use HTTPS.

```nginx
add_header Strict-Transport-Security "max-age=31536000";
```

Normally enabled only after HTTPS is fully configured.

---

# Cache-Control Header

Controls browser caching.

Disable caching:

```nginx
add_header Cache-Control "no-cache";
```

Enable browser caching:

```nginx
add_header Cache-Control "public, max-age=3600";
```

Meaning:

- Public cache
- Valid for one hour

---

# CORS Headers

When frontend and backend are hosted on different domains, browsers enforce the Same-Origin Policy.

CORS headers allow controlled cross-origin access.

Example:

```nginx
add_header Access-Control-Allow-Origin "*";
```

Specific domain:

```nginx
add_header Access-Control-Allow-Origin "https://example.com";
```

Common CORS headers:

```nginx
add_header Access-Control-Allow-Origin "*";

add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE";

add_header Access-Control-Allow-Headers "Authorization, Content-Type";
```

---

# Custom Headers

Applications often use custom headers for debugging.

Example:

```nginx
add_header X-Build "2026.07";

add_header X-Service "Payments";
```

These headers help identify:

- Application version
- Deployment
- Service name
- Environment

---

# Using Variables

Headers can contain variables.

Example:

```nginx
add_header X-Client-IP $remote_addr;

add_header X-Host $host;
```

If the client IP is:

```
192.168.1.20
```

The response becomes:

```http
X-Client-IP: 192.168.1.20
```

---

# Header Inheritance

Headers defined in a parent context are inherited by child contexts unless overridden.

Example:

```nginx
http {

    add_header X-Powered-By "Nginx";

    server {

        location / {

        }

    }

}
```

Every server and location inside the `http` context receives the header.

---

# Real-World Example

Production configuration:

```nginx
server {

    add_header X-Frame-Options "DENY";

    add_header X-Content-Type-Options "nosniff";

    add_header Referrer-Policy "strict-origin-when-cross-origin";

    add_header Cache-Control "no-cache";

}
```

Benefits:

- Better browser security
- Reduced attack surface
- Improved cache behavior
- Consistent responses

---

# Commonly Used Headers

| Header | Purpose |
|----------|---------|
| Content-Type | Response MIME type |
| Content-Length | Response size |
| Cache-Control | Browser caching |
| Authorization | Authentication |
| Cookie | Client session |
| Set-Cookie | Create cookies |
| User-Agent | Browser information |
| Host | Requested domain |
| X-Frame-Options | Clickjacking protection |
| X-Content-Type-Options | MIME protection |
| Strict-Transport-Security | Force HTTPS |
| Content-Security-Policy | Resource restrictions |
| Referrer-Policy | Referrer control |

---

# Best Practices

- Add essential security headers to every production application.
- Avoid exposing unnecessary server information.
- Configure CORS carefully instead of allowing every origin.
- Use HTTPS together with HSTS.
- Keep custom headers meaningful and consistent.
- Validate header behavior using browser developer tools or `curl`.

---

# Common Mistakes

## Using Wildcard CORS in Production

```nginx
Access-Control-Allow-Origin *
```

This is convenient during development but may not be appropriate for production APIs.

---

## Exposing Sensitive Information

Avoid adding headers that reveal:

- Internal server names
- Software versions
- Infrastructure details

---

## Forgetting Security Headers

Missing security headers can leave applications vulnerable to common browser-based attacks.

---

# Interview Notes

### Beginner Questions

- What are HTTP headers?
- What is the difference between request and response headers?
- What does the `add_header` directive do?
- What is the purpose of `Cache-Control`?

---

### Intermediate Questions

- Explain how security headers improve application security.
- What is CORS, and how is it configured in Nginx?
- What is HSTS?
- Why is Content Security Policy important?
- How can Nginx add custom response headers?

---

# Key Takeaways

- HTTP headers carry metadata about requests and responses.
- Nginx uses the `add_header` directive to send response headers.
- Security headers help protect applications against common browser-based attacks.
- CORS headers control cross-origin access.
- Variables can be used to generate dynamic header values.
- Proper header configuration improves security, performance, and maintainability in production deployments.