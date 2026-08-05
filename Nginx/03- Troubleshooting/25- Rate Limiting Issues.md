# Overview

**Rate limiting** is a mechanism that controls how many requests a client can send to the server within a specific period of time.

When rate limiting is configured incorrectly, legitimate users may be blocked, APIs may become inaccessible, or applications may return unexpected **429 Too Many Requests** responses.

Although rate limiting is primarily used to protect servers against abuse, bots, brute-force attacks, and DDoS attacks, an overly restrictive configuration can negatively impact normal users.

---

# Impact

| Impact | Level |
|---------|-------|
| Service Availability | 🟠 High |
| Performance | 🟢 Positive |
| Security | 🔴 Critical |
| Production Risk | 🟠 High |

---

# When You'll See This

This issue commonly occurs when:

- Configuring API rate limiting
- Deploying authentication services
- Protecting login pages
- Handling burst traffic
- Misconfiguring `limit_req`
- Deploying load-balanced applications
- Receiving unexpected traffic spikes

---

# Affected Components

- Rate Limiting
- Reverse Proxy
- APIs
- Authentication
- Load Balancer
- Client Requests

---

# Symptoms

## Browser

```text
429 Too Many Requests
```

---

## API Response

```http
HTTP/1.1 429 Too Many Requests
```

---

## Nginx Error Log

```text
limiting requests, excess: 5.320 by zone "api"
```

---

## Access Log

```text
429
```

---

## Website

- Login requests blocked
- API requests rejected
- Random request failures
- Intermittent client errors

---

# Quick Diagnosis

## Validate Configuration

```bash
sudo nginx -t
```

---

## View Error Log

```bash
sudo tail -100 /var/log/nginx/error.log
```

---

## Monitor Access Log

```bash
tail -f /var/log/nginx/access.log
```

---

## Search Configuration

```bash
grep -rn "limit_req" /etc/nginx/
```

---

## Check Active Connections

```bash
ss -ant
```

---

# Decision Tree

```text
            429 Too Many Requests
                     │
                     ▼
          Is Rate Limiting Enabled?
                │             │
               No            Yes
                │             │
                ▼             ▼
        Check Application   Check limit_req
                                   │
                      ┌────────────┴────────────┐
                      │                         │
                 Too Strict               Configuration OK
                      │                         │
                      ▼                         ▼
              Increase Limits         Check Traffic Pattern
                      │
                      ▼
                Reload Nginx
```

---

# Why This Happens

Typical request flow:

```text
Client

↓

Nginx

↓

Rate Limit Check

↓

Allowed?

│

├── Yes

│      ↓

│   Backend

│

└── No

       ↓

429 Too Many Requests
```

Nginx checks each request against the configured rate limit before forwarding it to the backend.

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Low request rate | Limit too restrictive |
| Burst too small | Temporary traffic spikes blocked |
| Shared IPs | Multiple users share the same IP address |
| Incorrect key | Wrong rate limiting variable |
| Missing burst | Legitimate requests rejected |
| API traffic | High-frequency API calls |

---

# Error Message Decoder

## Too Many Requests

```text
429 Too Many Requests
```

### Meaning

The client exceeded the configured request limit.

### Solution

Review the configured request rate and burst values.

---

## Limiting Requests

```text
limiting requests, excess
```

### Meaning

Nginx rejected requests because they exceeded the configured threshold.

### Solution

Adjust the rate limiting policy if legitimate users are affected.

---

# Step-by-Step Troubleshooting

## Step 1 — Review Rate Limit Configuration

Example

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
```

Verify that the configured rate is appropriate.

---

## Step 2 — Review Location Block

Example

```nginx
location /api/ {

    limit_req zone=api burst=20;

}
```

Ensure the correct zone is applied.

---

## Step 3 — Review Burst Configuration

Without burst:

```nginx
limit_req zone=api;
```

With burst:

```nginx
limit_req zone=api burst=20;
```

Burst allows temporary traffic spikes without rejecting requests immediately.

---

## Step 4 — Monitor Logs

```bash
tail -f /var/log/nginx/error.log
```

Look for repeated:

```text
limiting requests
```

messages.

---

## Step 5 — Test Rate Limiting

Example

```bash
for i in {1..20}
do
    curl http://localhost/api
done
```

Observe when responses change from **200** to **429**.

---

## Step 6 — Validate Configuration

```bash
sudo nginx -t
```

---

## Step 7 — Reload Nginx

```bash
sudo systemctl reload nginx
```

---

# Best Practices

- Apply rate limits only where necessary.
- Use higher limits for authenticated users.
- Configure reasonable burst values.
- Monitor rejected requests.
- Protect login and API endpoints separately.
- Test rate limits before deploying to production.

---

# Real Production Scenario

## Problem

A public REST API began returning:

```text
429 Too Many Requests
```

for legitimate mobile users.

---

## Investigation

The rate limit was configured as:

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=2r/s;
```

Many mobile users shared the same public IP address through their carrier's NAT gateway.

As a result, unrelated users exceeded the shared limit.

---

## Resolution

The configuration was updated:

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=20r/s;

limit_req zone=api burst=40;
```

Legitimate traffic was restored while abusive traffic continued to be limited.

---

# Verification Checklist

After fixing the issue:

- ✅ Legitimate users can access the application
- ✅ Rate limiting protects against abuse
- ✅ Burst values are appropriate
- ✅ Error logs contain minimal rate-limit violations
- ✅ APIs return expected responses
- ✅ No excessive 429 responses

---

# Common Mistakes

❌ Applying the same limit to every endpoint

❌ Configuring request rates that are too low

❌ Forgetting the `burst` parameter

❌ Using the wrong limiting key

❌ Ignoring users behind NAT or proxies

❌ Not testing with realistic traffic

---

# Prevention Tips

- Configure different rate limits for different endpoints.
- Monitor rate-limit metrics continuously.
- Use authentication-aware rate limiting where possible.
- Review access logs after deployments.
- Load test before enabling production rate limits.

---

# Production Notes

Rate limiting should protect infrastructure **without disrupting legitimate users**.

When troubleshooting, investigate in this order:

1. Review `limit_req_zone`
2. Review `limit_req`
3. Check burst configuration
4. Monitor access and error logs
5. Identify shared IP addresses
6. Test with realistic request patterns

A well-configured rate limiting policy reduces abuse while maintaining a smooth experience for legitimate clients.

---
