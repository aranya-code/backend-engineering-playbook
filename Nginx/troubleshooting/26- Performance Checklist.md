# Overview

Before deploying Nginx into production, every configuration should go through a **Performance Checklist**.

Many production incidents are not caused by software bugs but by configuration oversights such as:

- Incorrect worker configuration
- Missing compression
- Poor caching strategy
- Missing Keepalive
- Excessive logging
- Inefficient SSL configuration
- Missing monitoring

This checklist serves as a final verification guide before deploying or updating an Nginx server.

---

# Why Use a Performance Checklist?

A properly tuned Nginx server provides:

- Faster response times
- Lower CPU usage
- Reduced memory consumption
- Better scalability
- Improved reliability
- Better user experience

Skipping these checks can lead to avoidable production issues.

---

# Performance Checklist

## 1. Worker Processes

Recommended

```nginx
worker_processes auto;
```

Verify

- ✅ Uses all available CPU cores
- ✅ Not hardcoded unnecessarily

---

## 2. Worker Connections

Example

```nginx
events {

    worker_connections 4096;

}
```

Verify

- ✅ Suitable for expected traffic
- ✅ Matches OS file descriptor limits

---

## 3. Enable Keepalive

Example

```nginx
keepalive_timeout 65;
```

Benefits

- Reduced TCP connection overhead
- Faster repeat requests

---

## 4. Enable Gzip Compression

Example

```nginx
gzip on;

gzip_types
    text/plain
    text/css
    application/javascript
    application/json;
```

Verify

- ✅ Enabled for text-based content
- ❌ Avoid compressing already compressed files

---

## 5. Configure Static File Caching

Example

```nginx
location /static/ {

    expires 30d;

    add_header Cache-Control "public";

}
```

Benefits

- Faster page loads
- Reduced bandwidth usage

---

## 6. Configure Proxy Cache (If Applicable)

Example

```nginx
proxy_cache my_cache;
```

Benefits

- Reduces backend load
- Improves response time

---

## 7. Optimize SSL

Recommended

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
```

Verify

- ✅ TLS 1.2 enabled
- ✅ TLS 1.3 enabled
- ❌ SSLv3 disabled
- ❌ TLS 1.0 disabled

---

## 8. Enable HTTP/2

Example

```nginx
listen 443 ssl http2;
```

Benefits

- Multiplexing
- Reduced latency
- Improved browser performance

---

## 9. Configure Timeouts

Example

```nginx
client_body_timeout 60s;

client_header_timeout 60s;

keepalive_timeout 65s;

send_timeout 60s;
```

Avoid unnecessarily large timeout values.

---

## 10. Configure Logging

Example

```nginx
access_log /var/log/nginx/access.log;

error_log /var/log/nginx/error.log warn;
```

Verify

- Logs rotate correctly
- Appropriate log level configured

---

## 11. Configure Security Headers

Example

```nginx
add_header X-Frame-Options "SAMEORIGIN";

add_header X-Content-Type-Options "nosniff";

add_header Referrer-Policy "strict-origin";
```

Verify

- Security headers present
- Browser security tests pass

---

## 12. Configure Rate Limiting

Example

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=20r/s;
```

Protect

- Login pages
- APIs
- Authentication endpoints

---

## 13. Configure Load Balancing

Example

```nginx
upstream backend {

    server app1:8000;

    server app2:8000;

}
```

Verify

- Backend servers are healthy
- Health checks configured

---

## 14. Validate Configuration

Always run

```bash
sudo nginx -t
```

Expected

```text
syntax is ok

test is successful
```

---

## 15. Reload Gracefully

```bash
sudo systemctl reload nginx
```

Avoid restarting unless necessary.

---

## 16. Monitor Resource Usage

Monitor

```bash
top
```

```bash
htop
```

```bash
free -h
```

```bash
df -h
```

Review

- CPU
- Memory
- Disk
- Network

---

## 17. Monitor Logs

```bash
tail -f /var/log/nginx/access.log
```

```bash
tail -f /var/log/nginx/error.log
```

Verify

- No unexpected errors
- Normal traffic patterns

---

## 18. Test Performance

Useful tools

```bash
ab
```

```bash
wrk
```

```bash
hey
```

Example

```bash
wrk -t4 -c100 -d30s http://localhost
```

Measure

- Requests per second
- Latency
- Error rate

---

## 19. Verify Static Assets

Check

- CSS loads
- JavaScript loads
- Images load
- Fonts load

Browser Developer Tools →

```text
Network
```

---

## 20. Verify HTTPS

Test

```bash
openssl s_client -connect example.com:443
```

Verify

- Certificate chain
- TLS version
- Cipher suite

---

# Complete Deployment Checklist

| Item | Status |
|--------|:------:|
| Configuration validated | ☐ |
| Worker processes configured | ☐ |
| Worker connections tuned | ☐ |
| Keepalive enabled | ☐ |
| Gzip enabled | ☐ |
| Static caching configured | ☐ |
| Proxy cache configured | ☐ |
| SSL configured | ☐ |
| HTTP/2 enabled | ☐ |
| Security headers added | ☐ |
| Rate limiting configured | ☐ |
| Logging configured | ☐ |
| Load balancing verified | ☐ |
| Static files verified | ☐ |
| HTTPS tested | ☐ |
| Performance tested | ☐ |
| Resource usage monitored | ☐ |
| Logs reviewed | ☐ |
| Configuration backed up | ☐ |
| Monitoring enabled | ☐ |

---

# Best Practices

- Validate configuration before every deployment.
- Reload instead of restarting whenever possible.
- Monitor system resources continuously.
- Keep Nginx updated.
- Automate deployment validation.
- Test under production-like load.

---

# Real Production Scenario

## Problem

A company deployed a new Nginx configuration without validation.

Although the application started successfully, performance degraded significantly under normal traffic.

---

## Investigation

Several optimization steps had been skipped:

- Gzip disabled
- Static assets not cached
- Keepalive disabled
- Worker connections too low

CPU usage increased while response times nearly doubled.

---

## Resolution

The deployment checklist was followed before the next release.

Performance improved immediately:

- Response time reduced by 45%
- CPU usage reduced by 30%
- Static asset requests reduced significantly
- No configuration-related incidents occurred

---

# Verification Checklist

Before every production deployment:

- ✅ Configuration validated
- ✅ Performance settings reviewed
- ✅ HTTPS verified
- ✅ Monitoring enabled
- ✅ Logs checked
- ✅ Resource utilization acceptable
- ✅ Load testing completed

---

# Common Mistakes

❌ Deploying without running `nginx -t`

❌ Forgetting to enable compression

❌ No caching strategy

❌ Using outdated TLS protocols

❌ Ignoring performance testing

❌ Not monitoring logs after deployment

---

# Prevention Tips

- Standardize deployment procedures.
- Automate validation in CI/CD pipelines.
- Use infrastructure-as-code for consistency.
- Review performance after every release.
- Maintain a documented deployment checklist.

---

# Production Notes

A performance checklist helps eliminate common configuration mistakes before they affect production.

Run this checklist:

- Before deploying a new server
- Before major configuration changes
- Before enabling HTTPS
- Before migrating infrastructure
- After performance tuning
- During production readiness reviews

Treat this checklist as a mandatory pre-deployment review rather than an optional optimization guide.

---

