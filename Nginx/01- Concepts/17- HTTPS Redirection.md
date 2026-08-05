# Overview

After configuring SSL/TLS, the next step is ensuring that every visitor uses a secure connection.

Many users still type:

```
http://example.com
```

Instead of:

```
https://example.com
```

Without redirection, users may continue communicating over an insecure HTTP connection.

Nginx solves this problem by automatically redirecting all HTTP requests to HTTPS.

This process is called **HTTPS Redirection**.

---

# Why Redirect HTTP to HTTPS?

Suppose a website supports both HTTP and HTTPS.

```text
User

↓

http://example.com
```

Without redirection:

```text
Browser

↓

HTTP

↓

Nginx

↓

Website
```

The communication is **not encrypted**.

---

With redirection:

```text
Browser

↓

HTTP

↓

Nginx

↓

301 Redirect

↓

HTTPS

↓

Encrypted Connection
```

All traffic becomes secure.

---

# How HTTPS Redirection Works

```text
Browser

        │

http://example.com

        │

        ▼

      Nginx

        │

Return 301

        │

        ▼

https://example.com

        │

        ▼

 Secure Website
```

The browser automatically requests the HTTPS version.

---

# Basic HTTP to HTTPS Redirect

The simplest configuration is:

```nginx
server {

    listen 80;

    server_name example.com;

    return 301 https://$host$request_uri;

}
```

Meaning:

- Listen on HTTP (Port 80)
- Return a permanent redirect
- Preserve the original hostname
- Preserve the requested path

---

# Understanding the Configuration

## listen 80

```nginx
listen 80;
```

Accepts incoming HTTP requests.

---

## server_name

```nginx
server_name example.com;
```

Matches requests for:

```
example.com
```

---

## return 301

```nginx
return 301;
```

Returns an HTTP status code:

```
301 Moved Permanently
```

The browser immediately requests the new URL.

---

## https://$host

```nginx
https://$host
```

Uses the same hostname requested by the client.

Example:

```
blog.example.com

↓

https://blog.example.com
```

---

## $request_uri

Preserves the complete request path.

Example request:

```
http://example.com/products?id=20
```

Redirect becomes:

```
https://example.com/products?id=20
```

The URL path and query string are preserved.

---

# Complete Example

```nginx
server {

    listen 80;

    server_name example.com www.example.com;

    return 301 https://$host$request_uri;

}
```

Requests:

```
http://example.com

↓

https://example.com
```

```
http://www.example.com/shop

↓

https://www.example.com/shop
```

---

# Understanding HTTP Status Codes

Several redirect status codes exist.

| Code | Meaning | Permanent |
|-------|----------|------------|
| 301 | Moved Permanently | ✅ Yes |
| 302 | Found (Temporary Redirect) | ❌ No |
| 307 | Temporary Redirect | ❌ No |
| 308 | Permanent Redirect | ✅ Yes |

---

# 301 Redirect

A **301** redirect tells browsers and search engines that the resource has permanently moved.

Example:

```nginx
return 301 https://$host$request_uri;
```

Advantages:

- Browser caches the redirect.
- Search engines update their indexes.
- Better SEO.

Used for:

- HTTP → HTTPS migration
- Domain migration
- Permanent URL changes

---

# 302 Redirect

A **302** redirect indicates that the move is temporary.

Example:

```nginx
return 302 https://maintenance.example.com;
```

Search engines continue treating the original URL as the primary location.

Common use cases:

- Temporary maintenance pages
- Feature testing
- Temporary routing

---

# 301 vs 302

| Feature | 301 | 302 |
|----------|-----|-----|
| Permanent | Yes | No |
| Browser Caching | Yes | Usually No |
| SEO | Transfers ranking | Original URL retained |
| Typical Use | HTTP → HTTPS | Temporary maintenance |

---

# HTTPS Redirection Flow

```text
Client

    │

HTTP Request

    │

    ▼

Nginx (Port 80)

    │

301 Redirect

    │

    ▼

HTTPS Request

    │

    ▼

Nginx (Port 443)

    │

    ▼

Application
```

---

# Redirecting an Entire Website

Production configuration often uses two server blocks.

HTTP Server:

```nginx
server {

    listen 80;

    server_name example.com;

    return 301 https://$host$request_uri;

}
```

HTTPS Server:

```nginx
server {

    listen 443 ssl http2;

    server_name example.com;

    ssl_certificate /etc/ssl/certs/example.crt;

    ssl_certificate_key /etc/ssl/private/example.key;

}
```

The first server redirects.

The second serves the secure website.

---

# Redirecting Multiple Domains

Example:

```nginx
server {

    listen 80;

    server_name example.com www.example.com;

    return 301 https://example.com$request_uri;

}
```

Now both:

```
http://example.com
```

and

```
http://www.example.com
```

redirect to:

```
https://example.com
```

This helps enforce a single canonical domain.

---

# HSTS (HTTP Strict Transport Security)

After HTTPS is fully configured, browsers can be instructed to always use HTTPS.

Example:

```nginx
add_header Strict-Transport-Security "max-age=31536000" always;
```

Meaning:

- Browser remembers HTTPS for one year.
- Future HTTP requests are automatically converted to HTTPS.

Benefits:

- Prevents protocol downgrade attacks.
- Improves security.

> **Important:** Enable HSTS only after verifying that HTTPS works correctly for your entire site. Once browsers cache HSTS, users cannot bypass HTTPS until the policy expires.

---

# Real-World Example

A production deployment:

```text
Internet

      │

Port 80

      │

Nginx

      │

301 Redirect

      │

Port 443

      │

TLS Handshake

      │

Application
```

Users always end up on the encrypted version of the website.

---

# Best Practices

- Redirect all HTTP traffic to HTTPS using a **301 Permanent Redirect**.
- Preserve the original path using `$request_uri`.
- Preserve the original hostname using `$host`.
- Enable HSTS only after confirming HTTPS is working correctly.
- Redirect all versions of the domain to a single canonical HTTPS URL.
- Test redirects using browsers and command-line tools such as `curl`.

---

# Common Mistakes

## Forgetting `$request_uri`

Incorrect:

```nginx
return 301 https://example.com;
```

Every request redirects only to the homepage.

Correct:

```nginx
return 301 https://example.com$request_uri;
```

This preserves the original path.

---

## Using 302 Instead of 301

Using:

```nginx
return 302;
```

for permanent HTTPS migration can negatively affect SEO and cause inconsistent browser behavior.

---

## Redirect Loops

Incorrect server configuration can cause:

```
HTTP

↓

HTTPS

↓

HTTP

↓

HTTPS
```

Always verify that the HTTPS server does **not** redirect back to HTTP.

---

# Interview Notes

### Beginner Questions

- Why should HTTP be redirected to HTTPS?
- What does `return 301` do?
- What is the purpose of `$host`?
- What is `$request_uri`?

---

### Intermediate Questions

- Explain the difference between 301 and 302 redirects.
- Why is a 301 redirect preferred for HTTPS migration?
- What is HSTS?
- How does HTTPS redirection improve security?
- How do you avoid redirect loops?

---

# Key Takeaways

- HTTPS redirection ensures all client traffic uses encrypted connections.
- Nginx commonly performs this using `return 301 https://$host$request_uri;`.
- A **301** redirect is the preferred choice for permanent HTTP-to-HTTPS migration.
- `$host` preserves the requested hostname, while `$request_uri` preserves the full path and query string.
- HSTS further strengthens security by instructing browsers to always use HTTPS after the first successful secure connection.