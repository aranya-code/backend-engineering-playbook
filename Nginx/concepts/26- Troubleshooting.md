# Overview

No matter how well an Nginx server is configured, issues will eventually occur.

Some common problems include:

- Website not loading
- 404 Not Found
- 403 Forbidden
- 500 Internal Server Error
- 502 Bad Gateway
- 503 Service Unavailable
- SSL certificate errors
- Reverse proxy failures
- Permission issues
- High CPU usage

A systematic troubleshooting approach helps identify and resolve problems quickly.

---

# Troubleshooting Workflow

```text
Problem Report

       │

       ▼

Identify Symptoms

       │

       ▼

Check Configuration

       │

       ▼

Check Logs

       │

       ▼

Check Backend

       │

       ▼

Verify Network

       │

       ▼

Apply Fix

       │

       ▼

Validate Solution
```

---

# Step 1 - Verify Nginx Status

First, confirm that Nginx is running.

Linux (Systemd):

```bash
sudo systemctl status nginx
```

If Nginx is stopped:

```bash
sudo systemctl start nginx
```

Restart Nginx:

```bash
sudo systemctl restart nginx
```

Reload configuration:

```bash
sudo systemctl reload nginx
```

---

# Step 2 - Validate Configuration

Always test configuration changes before reloading.

```bash
nginx -t
```

Successful output:

```text
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

If errors exist:

```text
unexpected "}"

unknown directive

duplicate location
```

Fix the configuration before reloading.

---

# Step 3 - Check Access Log

Access Log:

```text
/var/log/nginx/access.log
```

Example:

```text
192.168.1.15 "GET /products HTTP/1.1" 200
```

Useful for:

- Request history
- Client IP
- Status codes
- User agents

---

# Step 4 - Check Error Log

Error Log:

```text
/var/log/nginx/error.log
```

Example:

```text
connect() failed (111: Connection refused)
while connecting to upstream
```

The Error Log is usually the first place to investigate production issues.

---

# Common HTTP Errors

| Status Code | Meaning |
|-------------|----------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |
| 502 | Bad Gateway |
| 503 | Service Unavailable |
| 504 | Gateway Timeout |

---

# 404 Not Found

Example:

```text
GET /images/logo.png

↓

404
```

Possible causes:

- Incorrect root path
- Missing file
- Wrong location block
- Typographical errors

Check:

```nginx
root

location
```

Verify that the requested file exists.

---

# 403 Forbidden

Example:

```text
403 Forbidden
```

Possible causes:

- File permissions
- Directory permissions
- `deny all`
- Missing index file
- Disabled directory listing

Example:

```nginx
autoindex off;
```

If requesting a directory without an index file:

```
403
```

may be returned.

---

# 500 Internal Server Error

Usually indicates an application issue.

Possible causes:

- Backend exception
- PHP/Django/FastAPI errors
- Incorrect permissions
- Invalid scripts

Check:

- Application logs
- Error Log
- Backend service

---

# 502 Bad Gateway

One of the most common production errors.

Example:

```text
Browser

↓

Nginx

↓

Backend

×

Unavailable
```

Possible causes:

- Backend not running
- Wrong proxy_pass
- Firewall
- Docker networking
- Incorrect socket path

Example:

```nginx
proxy_pass http://127.0.0.1:8000;
```

Verify that the backend is actually listening on the configured address.

---

# 503 Service Unavailable

Usually indicates:

- Backend overloaded
- Maintenance mode
- No available upstream servers

Check:

- Backend status
- Upstream configuration
- Health checks

---

# 504 Gateway Timeout

Example:

```text
Browser

↓

Nginx

↓

Backend

↓

Too Slow
```

Possible causes:

- Long-running database queries
- Slow APIs
- Backend timeout
- Network latency

Relevant directives:

```nginx
proxy_read_timeout

proxy_connect_timeout
```

---

# Permission Issues

Example:

```text
Permission denied
```

Possible causes:

- Nginx user lacks file access
- Incorrect ownership
- Wrong directory permissions

Typical directories:

```text
/var/www

/var/log/nginx

/etc/nginx
```

Ensure the Nginx worker process has the required read permissions.

---

# SSL Certificate Errors

Common problems:

```text
Certificate Expired

Certificate Not Trusted

Private Key Mismatch
```

Check:

```bash
openssl x509 -in server.crt -text
```

Verify:

- Expiration date
- Domain name
- Certificate chain

---

# Reverse Proxy Problems

Example:

```nginx
proxy_pass http://backend;
```

Verify:

- Backend server is running
- Correct hostname
- Correct port
- Docker/Kubernetes networking
- Firewall rules

---

# DNS Problems

Example:

```text
example.com

↓

Cannot Resolve
```

Check:

```bash
nslookup example.com
```

or

```bash
dig example.com
```

---

# Port Already in Use

Error:

```text
bind() to 0.0.0.0:80 failed
```

Find the process:

```bash
sudo lsof -i :80
```

or

```bash
sudo ss -tulpn
```

Stop the conflicting service or change the listening port.

---

# Docker Troubleshooting

Check running containers:

```bash
docker ps
```

View logs:

```bash
docker logs nginx
```

Open a shell:

```bash
docker exec -it nginx bash
```

Inspect Docker networks:

```bash
docker network ls
```

---

# Kubernetes Troubleshooting

View Pods:

```bash
kubectl get pods
```

View Services:

```bash
kubectl get svc
```

View Ingress:

```bash
kubectl get ingress
```

View logs:

```bash
kubectl logs pod-name
```

Describe resources:

```bash
kubectl describe pod pod-name
```

---

# Debugging HTTPS

Verify certificate:

```bash
openssl s_client -connect example.com:443
```

Useful for checking:

- Certificate chain
- TLS version
- Handshake issues

---

# Testing HTTP Responses

Retrieve response headers:

```bash
curl -I https://example.com
```

Verbose request:

```bash
curl -v https://example.com
```

Useful for checking:

- Redirects
- Security headers
- Cache headers
- Response codes

---

# Performance Troubleshooting

Monitor:

- CPU usage
- Memory usage
- Disk usage
- Network traffic
- Active connections

Useful commands:

```bash
top
```

```bash
htop
```

```bash
df -h
```

```bash
free -h
```

---

# Configuration Reload vs Restart

Reload:

```bash
sudo systemctl reload nginx
```

- No downtime
- Existing connections remain active

Restart:

```bash
sudo systemctl restart nginx
```

- Stops and starts Nginx
- Existing connections are interrupted

Prefer **reload** after configuration changes whenever possible.

---

# Troubleshooting Checklist

```text
Problem

↓

Is Nginx Running?

↓

Configuration Valid?

↓

Logs Checked?

↓

Backend Running?

↓

Network Reachable?

↓

Permissions Correct?

↓

SSL Valid?

↓

Problem Resolved
```

---

# Real-World Example

Problem:

```
502 Bad Gateway
```

Investigation:

```text
Check nginx -t

↓

Configuration OK

↓

Check error.log

↓

Connection Refused

↓

Backend Service Stopped

↓

Restart Backend

↓

Issue Resolved
```

---

# Best Practices

- Always validate the configuration using `nginx -t`.
- Check the Error Log before making configuration changes.
- Use `reload` instead of `restart` whenever possible.
- Monitor server resources continuously.
- Test changes in a staging environment before production.
- Keep backups of working configuration files.

---

# Common Mistakes

## Restarting Without Testing

Restarting Nginx without validating the configuration can cause the service to fail to start.

Always execute:

```bash
nginx -t
```

first.

---

## Ignoring Error Logs

Most production issues can be diagnosed from:

```
error.log
```

Ignoring it often increases troubleshooting time.

---

## Assuming the Problem is Nginx

Many issues actually originate from:

- Application servers
- Databases
- DNS
- Firewalls
- Docker networking
- Kubernetes networking

Investigate the complete request path.

---

# Interview Notes

### Beginner Questions

- Where are Nginx logs stored?
- What does `nginx -t` do?
- What is the difference between reload and restart?
- What causes a 404 error?

---

### Intermediate Questions

- How would you troubleshoot a 502 Bad Gateway?
- Explain the difference between 502 and 504.
- How would you diagnose SSL certificate problems?
- How do you troubleshoot Nginx inside Docker?
- Which tools would you use to investigate production issues?

---

# Key Takeaways

- Troubleshooting should follow a structured process: validate configuration, inspect logs, verify backend services, and test networking.
- `nginx -t` is the safest way to verify configuration changes before reloading.
- Access Logs record requests, while Error Logs provide detailed diagnostic information.
- Many HTTP errors point to specific classes of problems, such as missing files (404), permission issues (403), backend failures (502), or slow upstream services (504).
- Effective troubleshooting combines Nginx logs, operating system tools, Docker or Kubernetes diagnostics, and application logs to identify the root cause efficiently.