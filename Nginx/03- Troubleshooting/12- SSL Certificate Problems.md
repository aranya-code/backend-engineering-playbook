# Overview

SSL certificate problems are among the most common production issues when deploying HTTPS-enabled websites.

These problems can prevent Nginx from starting, cause browsers to display security warnings, or block secure connections entirely.

Common SSL certificate issues include:

- Missing certificate files
- Invalid certificate paths
- Expired certificates
- Incorrect certificate-key pair
- Incorrect file permissions
- Incomplete certificate chain
- Unsupported TLS versions

Since HTTPS is the standard for modern web applications, resolving SSL issues quickly is essential for maintaining application availability and user trust.

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
- Renewing SSL certificates
- Migrating servers
- Deploying new domains
- Using Let's Encrypt
- Copying certificates manually
- Restoring backups

---

# Affected Components

- SSL Certificates
- TLS Configuration
- HTTPS
- Certificate Chain
- Private Key
- Browser Security

---

# Symptoms

## Browser

```text
Your connection is not private
```

---

Chrome

```text
NET::ERR_CERT_COMMON_NAME_INVALID
```

---

Firefox

```text
SEC_ERROR_UNKNOWN_ISSUER
```

---

Nginx Error Log

```text
cannot load certificate
```

---

Another Example

```text
SSL_CTX_use_PrivateKey_file failed
```

---

Configuration Test

```bash
sudo nginx -t
```

Output

```text
cannot load certificate
```

---

# Quick Diagnosis

## Validate Configuration

```bash
sudo nginx -t
```

---

## Check Certificate

```bash
openssl x509 -in certificate.crt -text -noout
```

---

## Verify Private Key

```bash
openssl rsa -in private.key -check
```

---

## Verify Certificate Expiration

```bash
openssl x509 -enddate -noout -in certificate.crt
```

---

## Verify Certificate Matches Private Key

Certificate

```bash
openssl x509 -noout -modulus -in certificate.crt | openssl md5
```

Private Key

```bash
openssl rsa -noout -modulus -in private.key | openssl md5
```

The hashes must match.

---

# Decision Tree

```text
             HTTPS Not Working
                    │
                    ▼
              Run nginx -t
                    │
        ┌───────────┴────────────┐
        │                        │
   Configuration Error      Configuration OK
        │                        │
        ▼                        ▼
 Check Certificate Path    Browser Warning?
                                   │
                     ┌─────────────┴─────────────┐
                     │                           │
                    Yes                         No
                     │                           │
                     ▼                           ▼
         Verify Certificate             Check TLS Version
         Verify Private Key             Check Cipher Suites
                     │
                     ▼
             Restart Nginx
```

---

# Why This Happens

An HTTPS connection requires:

- A valid SSL certificate
- A matching private key
- A complete certificate chain
- Supported TLS protocols

If any of these components are missing or invalid, HTTPS connections fail.

Typical flow:

```text
Browser

↓

TLS Handshake

↓

Certificate Validation

↓

Success

OR

SSL Error
```

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Missing certificate | Certificate file not found |
| Wrong certificate path | Invalid file path in configuration |
| Incorrect private key | Key does not match certificate |
| Expired certificate | Certificate validity has expired |
| Missing intermediate certificate | Incomplete certificate chain |
| Incorrect permissions | Nginx cannot read certificate files |
| Invalid hostname | Certificate does not match requested domain |

---

# Error Message Decoder

## Cannot Load Certificate

```text
cannot load certificate
```

### Meaning

Nginx cannot locate or read the certificate file.

### Solution

Verify:

```bash
ls -l /etc/ssl/
```

---

## Private Key Mismatch

```text
SSL_CTX_use_PrivateKey_file failed
```

### Meaning

The configured private key does not match the certificate.

### Solution

Verify both files belong to the same certificate.

---

## Certificate Expired

Browser

```text
NET::ERR_CERT_DATE_INVALID
```

### Meaning

The certificate has expired.

### Solution

Renew the certificate.

---

## Common Name Invalid

Browser

```text
NET::ERR_CERT_COMMON_NAME_INVALID
```

### Meaning

The certificate was issued for a different domain.

### Solution

Install a certificate that matches the requested hostname.

---

# Step-by-Step Troubleshooting

## Step 1 — Validate Configuration

```bash
sudo nginx -t
```

Fix any reported SSL configuration errors.

---

## Step 2 — Verify Certificate Exists

```bash
ls -l /etc/nginx/ssl/
```

Ensure the configured certificate file exists.

---

## Step 3 — Verify Private Key

```bash
openssl rsa -check -in private.key
```

---

## Step 4 — Verify Certificate Expiration

```bash
openssl x509 -enddate -noout -in certificate.crt
```

Example

```text
notAfter=Aug 30 18:20:35 2026 GMT
```

---

## Step 5 — Verify Certificate Chain

```bash
openssl verify -CAfile chain.pem certificate.crt
```

Expected

```text
certificate.crt: OK
```

---

## Step 6 — Verify Certificate Configuration

Example

```nginx
ssl_certificate     /etc/nginx/ssl/fullchain.pem;

ssl_certificate_key /etc/nginx/ssl/private.key;
```

Ensure both paths are correct.

---

## Step 7 — Restart Nginx

```bash
sudo systemctl restart nginx
```

---

# Best Practices

- Always use **fullchain.pem** instead of only the server certificate.
- Store certificates outside the web root.
- Restrict private key permissions.
- Enable automatic certificate renewal.
- Monitor certificate expiration.
- Use TLS 1.2 and TLS 1.3 only.

---

# Real Production Scenario

## Problem

Users suddenly reported:

```text
Your connection is not private
```

after a weekend deployment.

---

## Investigation

Running:

```bash
openssl x509 -enddate -noout -in fullchain.pem
```

returned:

```text
notAfter=Jul 14 2026
```

The certificate had expired because the automated renewal job failed.

---

## Resolution

The certificate was renewed using Certbot.

```bash
sudo certbot renew
```

Nginx was reloaded.

```bash
sudo systemctl reload nginx
```

HTTPS immediately began working again.

---

# Verification Checklist

After fixing the issue:

- ✅ Certificate file exists
- ✅ Private key exists
- ✅ Certificate matches the key
- ✅ Certificate chain is complete
- ✅ Certificate is not expired
- ✅ HTTPS loads successfully
- ✅ Browser shows a secure connection

---

# Common Mistakes

❌ Using the wrong private key

❌ Forgetting intermediate certificates

❌ Incorrect certificate paths

❌ Expired certificates

❌ Weak TLS protocol configuration

❌ Incorrect file permissions on certificate files

---

# Prevention Tips

- Enable automatic certificate renewal.
- Monitor certificate expiration with alerts.
- Store certificates securely.
- Test HTTPS after every deployment.
- Keep backups of certificates and private keys.
- Regularly validate SSL configuration using online SSL testing tools.

---

# Production Notes

In production environments, SSL issues are usually caused by:

1. Expired certificates
2. Failed certificate renewals
3. Incorrect certificate deployment
4. Missing intermediate certificates
5. Wrong private key

Monitor certificate expiration proactively to prevent unexpected outages.

---

