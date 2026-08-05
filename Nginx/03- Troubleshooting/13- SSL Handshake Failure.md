# Overview

An **SSL Handshake Failure** occurs when the client and the server are unable to establish a secure TLS connection.

Before any encrypted HTTP communication begins, the browser and Nginx perform a **TLS Handshake**, where they negotiate:

- TLS version
- Cipher suite
- SSL certificate
- Certificate chain
- Encryption keys

If any step of this process fails, the connection is terminated and the user receives an SSL error instead of the requested webpage.

Unlike **SSL Certificate Problems**, where the certificate itself is invalid, an SSL Handshake Failure is usually caused by compatibility, protocol, configuration, or networking issues.

---

# Impact

| Impact | Level |
|---------|-------|
| Service Availability | 🔴 Critical |
| Performance | 🟢 None |
| Security | 🔴 Critical |
| Production Risk | 🔴 Critical |

---

# When You'll See This

This issue commonly occurs when:

- Configuring HTTPS for the first time
- Disabling old TLS versions
- Upgrading OpenSSL
- Configuring custom cipher suites
- Installing a new certificate
- Using load balancers
- Connecting with legacy browsers

---

# Affected Components

- TLS Handshake
- SSL Certificate
- Cipher Suites
- OpenSSL
- Browser
- Load Balancer
- Reverse Proxy

---

# Symptoms

## Browser

```text
ERR_SSL_PROTOCOL_ERROR
```

---

Chrome

```text
ERR_SSL_VERSION_OR_CIPHER_MISMATCH
```

---

Firefox

```text
SSL_ERROR_HANDSHAKE_FAILURE_ALERT
```

---

OpenSSL

```text
SSL routines:ssl3_read_bytes:sslv3 alert handshake failure
```

---

Nginx Error Log

```text
SSL_do_handshake() failed
```

---

# Quick Diagnosis

## Test HTTPS

```bash
curl -Iv https://example.com
```

---

## Check SSL Configuration

```bash
sudo nginx -t
```

---

## Test Using OpenSSL

```bash
openssl s_client -connect example.com:443
```

---

## Verify TLS Versions

```bash
openssl s_client -tls1_2 -connect example.com:443
```

---

## Check Nginx Logs

```bash
sudo tail -100 /var/log/nginx/error.log
```

---

# Decision Tree

```text
              HTTPS Connection Failed
                        │
                        ▼
              Run openssl s_client
                        │
            ┌───────────┴───────────┐
            │                       │
     Certificate Error       Handshake Failed
            │                       │
            ▼                       ▼
  Verify Certificate        Check TLS Version
                             Check Cipher Suites
                             Check OpenSSL
                                     │
                                     ▼
                             Test Again
                                     │
                                     ▼
                              Reload Nginx
```

---

# Why This Happens

A successful TLS handshake follows this sequence:

```text
Client

↓

Client Hello

↓

Server Hello

↓

Certificate Exchange

↓

Cipher Negotiation

↓

Key Exchange

↓

Encrypted Connection
```

If any step fails, the handshake terminates immediately.

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Unsupported TLS version | Client and server cannot agree on a protocol |
| Invalid cipher suite | No common cipher available |
| Incorrect certificate | Invalid or incompatible certificate |
| Incomplete certificate chain | Missing intermediate certificate |
| OpenSSL mismatch | Client and server support different features |
| Expired certificate | Certificate validation fails |
| Load balancer configuration | TLS termination configured incorrectly |

---

# Error Message Decoder

## SSL Handshake Failed

```text
SSL_do_handshake() failed
```

### Meaning

The TLS handshake could not be completed.

### Solution

Review the SSL configuration, supported TLS versions, and cipher suites.

---

## Protocol Error

```text
ERR_SSL_PROTOCOL_ERROR
```

### Meaning

The browser and server could not negotiate a common TLS protocol.

### Solution

Verify:

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
```

---

## Cipher Mismatch

```text
ERR_SSL_VERSION_OR_CIPHER_MISMATCH
```

### Meaning

No compatible cipher suite was found.

### Solution

Review the configured cipher suites and OpenSSL version.

---

# Step-by-Step Troubleshooting

## Step 1 — Test SSL Handshake

```bash
openssl s_client -connect example.com:443
```

Review:

- Certificate
- TLS Version
- Cipher
- Handshake status

---

## Step 2 — Verify TLS Configuration

Example

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
```

Avoid enabling deprecated protocols such as SSLv3 or TLS 1.0.

---

## Step 3 — Verify Cipher Suites

Example

```nginx
ssl_ciphers HIGH:!aNULL:!MD5;
```

Ensure the configured ciphers are supported by your OpenSSL version.

---

## Step 4 — Verify Certificate Chain

```bash
openssl verify -CAfile chain.pem fullchain.pem
```

Expected

```text
fullchain.pem: OK
```

---

## Step 5 — Validate Configuration

```bash
sudo nginx -t
```

---

## Step 6 — Restart Nginx

```bash
sudo systemctl restart nginx
```

---

# Best Practices

- Enable only TLS 1.2 and TLS 1.3.
- Keep OpenSSL updated.
- Use modern cipher suites.
- Disable deprecated SSL/TLS versions.
- Test HTTPS using multiple browsers.
- Validate the certificate chain after every deployment.

---

# Real Production Scenario

## Problem

Users with older browsers could not access the website after a security update.

Modern browsers worked correctly.

---

## Investigation

Running:

```bash
openssl s_client -connect example.com:443
```

showed that only TLS 1.3 was enabled.

Older browsers supported only TLS 1.2.

---

## Resolution

The configuration was updated:

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
```

After reloading Nginx, both modern and older supported browsers connected successfully.

---

# Verification Checklist

After fixing the issue:

- ✅ TLS handshake completes successfully
- ✅ Certificate chain is valid
- ✅ Browser connects securely
- ✅ OpenSSL reports no errors
- ✅ Nginx configuration validates successfully
- ✅ HTTPS returns HTTP 200

---

# Common Mistakes

❌ Disabling TLS 1.2 too early

❌ Using unsupported cipher suites

❌ Forgetting intermediate certificates

❌ Ignoring OpenSSL compatibility

❌ Assuming every client supports TLS 1.3

❌ Not testing with multiple browsers

---

# Prevention Tips

- Keep OpenSSL and Nginx updated.
- Test SSL configuration before deployment.
- Monitor TLS handshake failures.
- Use SSL testing tools during CI/CD.
- Review browser compatibility before disabling protocols.

---

# Production Notes

SSL handshake failures are often caused by **protocol or cipher mismatches**, not by expired certificates.

When troubleshooting, investigate in this order:

1. Certificate validity
2. Certificate chain
3. TLS protocol versions
4. Cipher suites
5. OpenSSL version
6. Browser compatibility
7. Load balancer or CDN configuration

Using tools like `openssl s_client` provides far more diagnostic information than relying solely on browser error messages.

---
