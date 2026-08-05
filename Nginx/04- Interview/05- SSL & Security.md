# Overview

Security is one of the most important responsibilities of Nginx in modern web applications. In most production environments, Nginx serves as the public-facing entry point, handling HTTPS connections, enforcing security policies, protecting backend services, and mitigating common web attacks.

Properly configuring SSL/TLS and security-related directives helps ensure data confidentiality, integrity, and availability while improving user trust and meeting industry best practices.

---

# Why SSL/TLS Matters

Without encryption, all communication between a client and a server is transmitted in plain text.

```text
Client
   │
HTTP
   │
   ▼
Server
```

An attacker could intercept:

- Usernames
- Passwords
- API tokens
- Credit card information
- Session cookies

Using HTTPS encrypts all communication.

```text
Client
   │
HTTPS
   │
   ▼
Nginx
```

This prevents eavesdropping and data tampering.

---

# What is SSL/TLS?

SSL (Secure Sockets Layer) is the predecessor to TLS (Transport Layer Security).

Today, the term **SSL** is still commonly used, although modern deployments use **TLS**.

TLS provides:

- Encryption
- Authentication
- Data integrity

Together, these ensure secure communication between clients and servers.

---

# SSL/TLS Handshake

Before encrypted communication begins, the client and server perform a TLS handshake.

```text
Client
   │
   ▼
Client Hello
   │
   ▼
Server Hello
   │
   ▼
Certificate Exchange
   │
   ▼
Key Exchange
   │
   ▼
Encrypted Communication
```

The handshake establishes:

- Supported TLS version
- Encryption algorithms
- Session keys
- Server identity

---

# SSL Termination

A common production architecture terminates HTTPS at Nginx.

```text
Client
   │
HTTPS
   │
   ▼
Nginx
   │
HTTP
   │
   ▼
Backend Application
```

Benefits include:

- Centralized certificate management
- Reduced backend complexity
- Better performance
- Easier scaling

In highly secure environments, HTTPS may also be used between Nginx and backend services.

---

# Certificates

An SSL/TLS certificate proves the identity of a server.

Common certificate providers include:

- Let's Encrypt
- DigiCert
- GlobalSign
- Sectigo

A certificate typically contains:

- Domain name
- Public key
- Expiration date
- Certificate authority
- Digital signature

---

# Basic HTTPS Configuration

Example:

```nginx
server {

    listen 443 ssl;

    server_name example.com;

    ssl_certificate /etc/ssl/certs/example.crt;

    ssl_certificate_key /etc/ssl/private/example.key;

}
```

Nginx uses the certificate and private key to establish secure connections.

---

# Redirect HTTP to HTTPS

A common production practice is to redirect all HTTP traffic to HTTPS.

Example:

```nginx
server {

    listen 80;

    server_name example.com;

    return 301 https://$host$request_uri;

}
```

Benefits:

- Enforces secure communication
- Improves user trust
- Helps with SEO
- Prevents accidental HTTP access

---

# Supported TLS Versions

Older protocol versions contain known security vulnerabilities.

Modern deployments should allow only recent versions.

Example:

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
```

Recommended:

- TLS 1.2
- TLS 1.3

Avoid:

- SSLv2
- SSLv3
- TLS 1.0
- TLS 1.1

---

# Strong Cipher Suites

Cipher suites determine how encrypted communication is performed.

Example:

```nginx
ssl_prefer_server_ciphers on;
```

Use modern cipher suites and remove weak or deprecated algorithms.

---

# HTTP Strict Transport Security (HSTS)

HSTS instructs browsers to always use HTTPS.

Example:

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

Benefits:

- Prevents protocol downgrade attacks
- Forces HTTPS
- Improves security

Enable HSTS only after verifying that HTTPS is fully configured.

---

# Security Headers

Nginx can add HTTP response headers that improve browser security.

Common headers include:

```nginx
add_header X-Frame-Options "SAMEORIGIN";

add_header X-Content-Type-Options "nosniff";

add_header Referrer-Policy "strict-origin-when-cross-origin";
```

These headers help protect against:

- Clickjacking
- MIME type sniffing
- Information leakage

---

# Rate Limiting

Rate limiting helps protect applications against abuse.

Example:

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

limit_req zone=api burst=20;
```

Common use cases:

- Login endpoints
- Public APIs
- Authentication services
- Password reset endpoints

---

# Connection Limiting

Nginx can also limit the number of simultaneous connections.

Example:

```nginx
limit_conn_zone $binary_remote_addr zone=conn:10m;

limit_conn conn 20;
```

This helps protect against excessive resource consumption.

---

# Access Control

Access can be restricted based on IP addresses.

Example:

```nginx
location /admin {

    allow 192.168.1.0/24;

    deny all;

}
```

This is useful for:

- Internal dashboards
- Administrative portals
- Monitoring tools

---

# Hiding Server Information

By default, Nginx may expose version information.

Disable it in production.

```nginx
server_tokens off;
```

This reduces information disclosure to potential attackers.

---

# Secure File Permissions

Protect configuration files and private keys.

Recommendations:

- Restrict access to private keys.
- Use appropriate file ownership.
- Avoid world-readable permissions.
- Regularly rotate certificates.

---

# Common Security Architecture

```text
                 Internet
                     │
                     ▼
              HTTPS (443)
                     │
                     ▼
                  Nginx
          ┌──────────┴──────────┐
          ▼                     ▼
 Authentication API       Application API
          │                     │
          └──────────┬──────────┘
                     ▼
                  Database
```

Nginx acts as the secure entry point for all client traffic.

---

# Real-World Example

Consider an online banking application.

Security measures include:

- HTTPS for all traffic
- Automatic HTTP to HTTPS redirects
- HSTS enabled
- Strong TLS versions
- Security headers
- Rate limiting on login endpoints
- IP restrictions for administration
- Hidden server version information

These layers work together to reduce the attack surface and improve overall security.

---

# Best Practices

- Use HTTPS for all production traffic.
- Prefer TLS 1.2 and TLS 1.3.
- Redirect HTTP requests to HTTPS.
- Enable HSTS only after validating HTTPS.
- Configure modern cipher suites.
- Add security-related HTTP headers.
- Protect sensitive endpoints with rate limiting.
- Restrict administrative access using IP-based rules.
- Disable server version disclosure.
- Regularly renew and rotate SSL/TLS certificates.

---

# Key Takeaways

- Nginx commonly serves as the SSL/TLS termination point for web applications.
- HTTPS protects data confidentiality, integrity, and authentication.
- Strong TLS versions and cipher suites improve communication security.
- Security headers help defend against common browser-based attacks.
- Rate limiting and connection limiting reduce abuse and denial-of-service risks.
- Proper SSL/TLS and security configuration are essential for secure production deployments.