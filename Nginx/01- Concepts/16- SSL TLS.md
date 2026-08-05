# Overview

Modern websites use **HTTPS** instead of HTTP to protect communication between clients and servers.

HTTPS is achieved by combining:

- HTTP
- SSL/TLS

Today, SSL has been deprecated and replaced by **TLS (Transport Layer Security)**.

However, the term **SSL Certificate** is still commonly used even though the underlying protocol is TLS.

This chapter explains:

- SSL vs TLS
- Certificates
- Public Key Cryptography
- Certificate Authorities (CA)
- Certificate Chains
- Diffie-Hellman Parameters
- Self-Signed Certificates
- Let's Encrypt
- TLS Configuration in Nginx

---

# Why HTTPS?

Suppose a user logs into a website.

Without HTTPS:

```text
Browser

↓

username

password

↓

Internet

↓

Server
```

The data travels in plain text.

Anyone intercepting the traffic can read it.

---

With HTTPS:

```text
Browser

↓

Encrypted Data

↓

Internet

↓

Encrypted Data

↓

Server
```

Even if someone captures the packets, they cannot read the contents.

---

# What is SSL?

**Secure Sockets Layer (SSL)** was the original protocol for securing Internet communication.

Versions:

```
SSL 2.0

↓

SSL 3.0
```

These versions are now considered insecure.

SSL should **never** be enabled on modern servers.

---

# What is TLS?

**Transport Layer Security (TLS)** replaced SSL.

Versions:

```
TLS 1.0

↓

TLS 1.1

↓

TLS 1.2

↓

TLS 1.3
```

Modern production servers should use:

- TLS 1.2
- TLS 1.3

Older versions should generally be disabled.

---

# SSL vs TLS

| SSL | TLS |
|------|------|
| Older protocol | Modern protocol |
| Deprecated | Current standard |
| Less secure | More secure |
| SSL 2.0 / 3.0 | TLS 1.2 / 1.3 |
| Should not be used | Recommended |

Although everyone says "SSL Certificate", today's certificates are actually used with TLS.

---

# How HTTPS Works

```text
Browser

      │

HTTPS Request

      │

      ▼

Nginx

      │

TLS Handshake

      │

Encrypted Connection

      │

      ▼

Application
```

Before any HTTP data is exchanged, the browser and server perform a **TLS Handshake**.

---

# What is a Digital Certificate?

A digital certificate proves the identity of a server.

It contains:

- Domain name
- Public key
- Certificate Authority
- Expiration date
- Digital signature

Example:

```
example.com

Issued By

Let's Encrypt

Valid Until

Jan 2027
```

---

# Public Key Cryptography

HTTPS uses **Asymmetric Encryption**.

Two keys are created:

```
Public Key

Private Key
```

---

## Public Key

The public key:

- Can be shared with everyone.
- Is included inside the certificate.

Example:

```text
Certificate

↓

Public Key
```

---

## Private Key

The private key:

- Must remain secret.
- Stays on the server.
- Must never be shared.

Example:

```text
Server

↓

Private Key
```

If someone obtains the private key, they can impersonate the server.

---

# How Encryption Works

```text
Browser

↓

Uses Public Key

↓

Encrypted Data

↓

Server

↓

Private Key

↓

Original Data
```

Only the server possessing the private key can decrypt the data.

---

# Certificate Authority (CA)

A **Certificate Authority** verifies the identity of a website before issuing a certificate.

Examples:

- Let's Encrypt
- DigiCert
- GlobalSign
- Sectigo

Browsers trust certificates issued by trusted Certificate Authorities.

---

# Certificate Chain

A certificate is usually part of a trust chain.

```text
Root CA

      │

Intermediate CA

      │

Website Certificate
```

The browser validates the entire chain before trusting the website.

---

# Self-Signed Certificate

A self-signed certificate is signed by the server itself.

```text
Server

↓

Creates Certificate

↓

Signs Certificate
```

Advantages:

- Free
- Easy to create
- Useful for development

Disadvantages:

- Browsers display security warnings.
- Not trusted by default.

---

# Certificate Signing Request (CSR)

Before obtaining a certificate from a CA, the server generates a **Certificate Signing Request (CSR)**.

The CSR contains:

- Domain Name
- Organization
- Public Key

The CA uses this information to issue the certificate.

---

# Let's Encrypt

Let's Encrypt is a free Certificate Authority.

Benefits:

- Free SSL/TLS certificates
- Automated renewal
- Trusted by modern browsers

Many production Nginx deployments use Let's Encrypt together with **Certbot**.

---

# Certificate Files

A typical Nginx HTTPS configuration uses:

```
Certificate (.crt or .pem)

Private Key (.key)
```

Example:

```text
/etc/ssl/certs/example.crt

/etc/ssl/private/example.key
```

---

# Basic HTTPS Configuration

```nginx
server {

    listen 443 ssl http2;

    server_name example.com;

    ssl_certificate /etc/ssl/certs/example.crt;

    ssl_certificate_key /etc/ssl/private/example.key;

}
```

Meaning:

- Listen on HTTPS
- Load certificate
- Load private key
- Enable TLS

---

# Choosing TLS Versions

Recommended:

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
```

Avoid enabling:

- SSLv2
- SSLv3
- TLSv1.0
- TLSv1.1

These versions are outdated and have known security weaknesses.

---

# Diffie-Hellman Parameters

Diffie-Hellman (DH) parameters improve key exchange security.

Example:

```nginx
ssl_dhparam /etc/nginx/dhparam.pem;
```

Benefits:

- Stronger key exchange
- Forward secrecy
- Better protection against interception

Generating DH parameters may take time, but they only need to be created occasionally.

---

# HTTPS Request Flow

```text
Browser

      │

TLS Handshake

      │

Certificate Verification

      │

Secure Session Created

      │

Encrypted HTTP Requests

      │

Nginx

      │

Backend Application
```

---

# Real-World Example

A production Django deployment:

```text
Internet

      │

HTTPS

      │

Nginx

      │

Gunicorn

      │

Django

      │

PostgreSQL
```

Responsibilities:

Nginx:

- TLS Handshake
- Certificate Management
- HTTPS Communication

Gunicorn:

- Python Application

Django:

- Business Logic

---

# Best Practices

- Use TLS 1.2 and TLS 1.3 only.
- Obtain certificates from trusted Certificate Authorities.
- Protect private keys with appropriate file permissions.
- Renew certificates before they expire.
- Enable HTTP/2 together with HTTPS.
- Test SSL/TLS configuration regularly.

---

# Common Mistakes

## Using Expired Certificates

Expired certificates cause browser security warnings and may block access to your website.

---

## Exposing Private Keys

Private keys should never be:

- Uploaded to public repositories
- Shared via email
- Stored in insecure locations

Compromised private keys require immediate certificate replacement.

---

## Enabling Old Protocols

Protocols such as SSLv3 and TLS 1.0 have known vulnerabilities.

Disable them in production.

---

# Interview Notes

### Beginner Questions

- What is HTTPS?
- What is the difference between SSL and TLS?
- What is a digital certificate?
- What is the purpose of a private key?

---

### Intermediate Questions

- Explain how HTTPS works.
- What is a Certificate Authority?
- What is a Certificate Chain?
- What is a self-signed certificate?
- Why should TLS 1.2 and TLS 1.3 be preferred?
- What are Diffie-Hellman parameters used for?

---

# Key Takeaways

- HTTPS secures HTTP communication using TLS.
- SSL is deprecated; TLS is the modern security protocol.
- Digital certificates verify server identity and contain the server's public key.
- The private key remains on the server and must be protected.
- Certificate Authorities establish trust between browsers and websites.
- Modern Nginx deployments should use TLS 1.2/1.3, trusted certificates, HTTP/2, and secure key management.