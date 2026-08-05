# Overview

A web application is exposed to various browser-based attacks.

Even if your application code is secure, an improperly configured web server can leave users vulnerable.

Nginx allows you to add **Security Headers** to every HTTP response.

These headers instruct browsers how to safely handle your website.

Security headers help protect against:

- Clickjacking
- Cross-Site Scripting (XSS)
- MIME Type Sniffing
- Downgrade Attacks
- Information Leakage

Most production websites include several security headers by default.

---

# What are Security Headers?

Security headers are HTTP response headers that instruct the browser to enforce specific security policies.

Example:

```http
HTTP/1.1 200 OK

Strict-Transport-Security: max-age=31536000

X-Frame-Options: DENY

X-Content-Type-Options: nosniff
```

Whenever the browser receives these headers, it follows the specified security rules.

---

# Adding Security Headers

Nginx uses the `add_header` directive.

Syntax:

```nginx
add_header Header-Name "Value";
```

Example:

```nginx
add_header X-Frame-Options "DENY";
```

---

# Common Security Headers

| Header | Purpose |
|----------|----------|
| Strict-Transport-Security | Force HTTPS |
| X-Frame-Options | Prevent Clickjacking |
| X-Content-Type-Options | Prevent MIME Sniffing |
| X-XSS-Protection | Legacy XSS protection |
| Referrer-Policy | Control referrer information |
| Content-Security-Policy | Restrict resource loading |
| Permissions-Policy | Restrict browser features |

---

# Strict-Transport-Security (HSTS)

HSTS forces browsers to always communicate using HTTPS.

Example:

```nginx
add_header Strict-Transport-Security "max-age=31536000" always;
```

Meaning:

```
31536000 seconds

↓

1 Year
```

Once received, the browser automatically upgrades future HTTP requests to HTTPS.

---

## Why HSTS?

Without HSTS:

```text
Browser

↓

HTTP

↓

Attacker

↓

HTTPS
```

An attacker may attempt a protocol downgrade.

With HSTS:

```text
Browser

↓

HTTPS Only

↓

Server
```

The browser refuses insecure HTTP connections.

---

# X-Frame-Options

This header prevents your website from being embedded inside another webpage.

Example:

```nginx
add_header X-Frame-Options "DENY";
```

Possible values:

| Value | Meaning |
|--------|----------|
| DENY | Never allow framing |
| SAMEORIGIN | Allow framing only from the same domain |

---

## Clickjacking Attack

Without protection:

```text
Attacker Website

↓

Invisible Frame

↓

Your Website
```

Users unknowingly interact with your application through the attacker's page.

With:

```nginx
X-Frame-Options: DENY
```

the browser blocks the embedded page.

---

# X-Content-Type-Options

Browsers sometimes try to guess a file's content type.

This behavior is called **MIME Sniffing**.

Disable it using:

```nginx
add_header X-Content-Type-Options "nosniff";
```

Now browsers use only the Content-Type specified by the server.

---

## Why Disable MIME Sniffing?

Suppose a file is uploaded as:

```
profile.jpg
```

but actually contains JavaScript.

Without protection:

```
Browser

↓

Guess Content

↓

Execute Script
```

With:

```
nosniff
```

the browser refuses to guess the content type.

---

# X-XSS-Protection

Older browsers included an XSS filter.

Example:

```nginx
add_header X-XSS-Protection "1; mode=block";
```

Meaning:

```
Enable XSS Filter

↓

Block Page if Attack Detected
```

> **Note:** Modern browsers have deprecated this header and instead rely on **Content Security Policy (CSP)**. It may still appear in legacy configurations for compatibility.

---

# Referrer-Policy

Controls how much information is sent when users navigate to another website.

Example:

```nginx
add_header Referrer-Policy "strict-origin-when-cross-origin";
```

Benefits:

- Better privacy
- Reduced information leakage

---

# Content-Security-Policy (CSP)

One of the strongest browser security mechanisms.

Example:

```nginx
add_header Content-Security-Policy "default-src 'self';";
```

Meaning:

Only resources from the same origin are allowed.

This helps prevent:

- Cross-Site Scripting (XSS)
- Malicious script injection
- Unauthorized third-party resources

---

# Example CSP

```nginx
add_header Content-Security-Policy "
default-src 'self';
img-src 'self';
script-src 'self';
style-src 'self';
";
```

Only scripts, images, and styles from your own domain are permitted.

---

# Permissions-Policy

Controls browser features.

Example:

```nginx
add_header Permissions-Policy "geolocation=(), camera=(), microphone=()";
```

This disables:

- Camera
- Microphone
- Geolocation

unless explicitly allowed.

---

# Complete Security Header Configuration

```nginx
server {

    add_header Strict-Transport-Security "max-age=31536000" always;

    add_header X-Frame-Options "DENY";

    add_header X-Content-Type-Options "nosniff";

    add_header Referrer-Policy "strict-origin-when-cross-origin";

    add_header Content-Security-Policy "default-src 'self';";

}
```

This provides a solid baseline for many production deployments.

---

# Security Header Flow

```text
Browser

      │

HTTPS Request

      │

      ▼

Nginx

      │

Add Security Headers

      │

      ▼

HTTP Response

      │

      ▼

Browser

↓

Apply Security Policies
```

---

# Checking Security Headers

Use:

```bash
curl -I https://example.com
```

Example output:

```http
Strict-Transport-Security: max-age=31536000

X-Frame-Options: DENY

X-Content-Type-Options: nosniff

Content-Security-Policy: default-src 'self'
```

You can also inspect headers using your browser's Developer Tools.

---

# Real-World Example

Production API:

```text
Internet

↓

Nginx

↓

Security Headers Added

↓

FastAPI

↓

Response
```

Every client automatically receives the same security protections without requiring application code changes.

---

# Best Practices

- Always enable HSTS after HTTPS is fully configured.
- Use `X-Frame-Options: DENY` unless framing is required.
- Enable `X-Content-Type-Options: nosniff`.
- Implement a carefully tested Content Security Policy.
- Use Referrer-Policy to limit unnecessary information sharing.
- Review security headers periodically as browser standards evolve.

---

# Common Mistakes

## Enabling HSTS Too Early

If HTTPS is not fully working, browsers may refuse future HTTP connections after caching the HSTS policy.

Verify your HTTPS configuration before enabling HSTS.

---

## Overly Restrictive CSP

A CSP that blocks required JavaScript or third-party resources may break application functionality.

Test policies thoroughly before deploying them.

---

## Relying Only on X-XSS-Protection

Modern browsers largely ignore this header.

Use Content Security Policy as the primary defense against XSS.

---

# Interview Notes

### Beginner Questions

- What are HTTP security headers?
- Why is HSTS important?
- What does X-Frame-Options protect against?
- What does `nosniff` do?

---

### Intermediate Questions

- Explain Clickjacking.
- What is MIME Sniffing?
- What is Content Security Policy?
- Why has X-XSS-Protection become less important?
- How do security headers improve web application security?

---

# Key Takeaways

- Security headers instruct browsers to enforce security policies.
- HSTS forces browsers to use HTTPS.
- X-Frame-Options protects against Clickjacking attacks.
- X-Content-Type-Options prevents MIME type sniffing.
- Content Security Policy (CSP) is one of the most effective defenses against Cross-Site Scripting (XSS).
- A well-configured set of security headers significantly improves the security posture of Nginx-based applications without requiring changes to application code.