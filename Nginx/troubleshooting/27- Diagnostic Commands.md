# Overview

When troubleshooting Nginx, the first step is gathering accurate diagnostic information.

Nginx itself provides configuration validation commands, while Linux offers numerous utilities to inspect:

- Configuration
- Running processes
- Network connections
- Logs
- SSL certificates
- File permissions
- System resources
- DNS resolution

This document serves as a quick-reference guide containing the most commonly used diagnostic commands for Nginx administrators.

---

# Configuration Commands

## Validate Configuration

```bash
sudo nginx -t
```

Purpose

- Validates configuration syntax
- Detects configuration errors
- Displays the file containing the error

Example

```text
syntax is ok

test is successful
```

---

## Display Complete Configuration

```bash
sudo nginx -T
```

Purpose

- Shows the complete configuration
- Includes all imported configuration files
- Useful for debugging `include` directives

---

## Display Version

```bash
nginx -v
```

Example

```text
nginx version: nginx/1.26.0
```

---

## Display Detailed Build Information

```bash
nginx -V
```

Shows

- OpenSSL version
- Compile options
- Enabled modules
- Configuration arguments

---

# Service Management

## Check Service Status

```bash
sudo systemctl status nginx
```

---

## Start Nginx

```bash
sudo systemctl start nginx
```

---

## Stop Nginx

```bash
sudo systemctl stop nginx
```

---

## Restart Nginx

```bash
sudo systemctl restart nginx
```

---

## Reload Configuration

```bash
sudo systemctl reload nginx
```

Preferred over restart because existing connections remain active.

---

## Enable Automatic Startup

```bash
sudo systemctl enable nginx
```

---

# Log Analysis

## Monitor Error Log

```bash
tail -f /var/log/nginx/error.log
```

---

## Monitor Access Log

```bash
tail -f /var/log/nginx/access.log
```

---

## View Recent Errors

```bash
sudo tail -100 /var/log/nginx/error.log
```

---

## Search Error Logs

```bash
grep "error" /var/log/nginx/error.log
```

---

## Search Specific Status Code

```bash
grep "404" /var/log/nginx/access.log
```

---

# Process Management

## View Running Processes

```bash
ps -ef | grep nginx
```

---

## Display CPU Usage

```bash
top
```

---

## Interactive Process Monitor

```bash
htop
```

---

## Sort Processes by Memory

```bash
ps aux --sort=-%mem | head
```

---

## Sort Processes by CPU

```bash
ps aux --sort=-%cpu | head
```

---

# Network Diagnostics

## View Listening Ports

```bash
ss -tulpn
```

---

## View Active Connections

```bash
ss -ant
```

---

## Using netstat

```bash
netstat -tulpn
```

---

## Test HTTP Response

```bash
curl http://localhost
```

---

## View HTTP Headers

```bash
curl -I http://localhost
```

---

## Test HTTPS

```bash
curl -Iv https://example.com
```

---

# DNS Diagnostics

## nslookup

```bash
nslookup example.com
```

---

## dig

```bash
dig example.com
```

---

## Ping

```bash
ping example.com
```

---

## View Resolver

```bash
cat /etc/resolv.conf
```

---

# SSL Diagnostics

## Test Certificate

```bash
openssl s_client -connect example.com:443
```

---

## View Certificate Details

```bash
openssl x509 -text -noout -in certificate.crt
```

---

## Check Expiration

```bash
openssl x509 -enddate -noout -in certificate.crt
```

---

## Verify Certificate

```bash
openssl verify certificate.crt
```

---

# File Diagnostics

## View Permissions

```bash
ls -l
```

---

## View Directory Permissions

```bash
ls -ld
```

---

## Display File Information

```bash
stat filename
```

---

## Search Configuration Files

```bash
find /etc/nginx -name "*.conf"
```

---

## Search Directive

```bash
grep -rn "proxy_pass" /etc/nginx/
```

---

# Docker Diagnostics

## Running Containers

```bash
docker ps
```

---

## Container Logs

```bash
docker logs nginx
```

---

## Enter Container

```bash
docker exec -it nginx sh
```

---

## View Resource Usage

```bash
docker stats
```

---

## Inspect Container

```bash
docker inspect nginx
```

---

# Kubernetes Diagnostics

## View Pods

```bash
kubectl get pods
```

---

## View Services

```bash
kubectl get svc
```

---

## View Ingress

```bash
kubectl get ingress
```

---

## View Endpoints

```bash
kubectl get endpoints
```

---

## Describe Pod

```bash
kubectl describe pod <pod-name>
```

---

## View Logs

```bash
kubectl logs <pod-name>
```

---

# System Resource Monitoring

## Memory Usage

```bash
free -h
```

---

## Disk Usage

```bash
df -h
```

---

## Disk I/O

```bash
iostat
```

---

## CPU Information

```bash
lscpu
```

---

## Memory Information

```bash
cat /proc/meminfo
```

---

# File Descriptor Diagnostics

## Current Limit

```bash
ulimit -n
```

---

## Count Open Files

```bash
lsof -p $(pidof nginx | awk '{print $1}') | wc -l
```

---

## View Open Files

```bash
lsof -p $(pidof nginx | awk '{print $1}')
```

---

# Performance Testing

## ApacheBench

```bash
ab -n 1000 -c 100 http://localhost/
```

---

## wrk

```bash
wrk -t4 -c100 -d30s http://localhost
```

---

## hey

```bash
hey -n 1000 -c 100 http://localhost
```

---

# Troubleshooting Workflow

Follow this sequence when diagnosing an issue:

```text
Problem Report

↓

Check Service Status

↓

Validate Configuration

↓

Review Error Log

↓

Review Access Log

↓

Test Backend

↓

Check Network

↓

Verify DNS

↓

Verify SSL

↓

Check Resources

↓

Apply Fix

↓

Validate Configuration

↓

Reload Nginx

↓

Verify Resolution
```

---

# Command Cheat Sheet

| Task | Command |
|--------|---------|
| Validate configuration | `nginx -t` |
| Show full configuration | `nginx -T` |
| Restart Nginx | `systemctl restart nginx` |
| Reload configuration | `systemctl reload nginx` |
| View service status | `systemctl status nginx` |
| Monitor error log | `tail -f /var/log/nginx/error.log` |
| Monitor access log | `tail -f /var/log/nginx/access.log` |
| Test HTTP | `curl http://localhost` |
| Test HTTPS | `curl -Iv https://example.com` |
| Check DNS | `dig example.com` |
| View listening ports | `ss -tulpn` |
| View active connections | `ss -ant` |
| Monitor CPU | `top` |
| Monitor Memory | `free -h` |
| View Docker containers | `docker ps` |
| View Kubernetes Pods | `kubectl get pods` |

---

# Best Practices

- Always run `nginx -t` before reloading Nginx.
- Monitor the error log before making configuration changes.
- Use `nginx -T` to troubleshoot included configuration files.
- Reload instead of restarting whenever possible.
- Monitor CPU, memory, and network resources during troubleshooting.
- Document frequently used diagnostic commands for your team.

---

# Real Production Scenario

## Problem

A production API began returning intermittent **502 Bad Gateway** errors.

---

## Investigation

The following commands were executed:

```bash
sudo systemctl status nginx

sudo nginx -t

tail -100 /var/log/nginx/error.log

curl http://backend:8000

ss -ant
```

The error log showed:

```text
connect() failed (111: Connection refused)
```

The backend service had stopped unexpectedly.

---

## Resolution

The backend service was restarted, connectivity was verified using `curl`, and Nginx was reloaded.

The API returned to normal operation without requiring changes to the Nginx configuration.

---

# Verification Checklist

Before closing an incident:

- ✅ Configuration validated
- ✅ Service status verified
- ✅ Error logs reviewed
- ✅ Access logs reviewed
- ✅ Backend connectivity tested
- ✅ DNS verified
- ✅ SSL tested
- ✅ Resource usage checked
- ✅ Website responds correctly
- ✅ Monitoring confirms normal operation

---

# Common Mistakes

❌ Restarting Nginx without checking logs

❌ Ignoring `nginx -t`

❌ Forgetting to verify backend services

❌ Looking only at browser errors

❌ Not checking system resources

❌ Making multiple configuration changes before identifying the root cause

---

# Production Notes

Most production incidents can be diagnosed using fewer than ten commands.

A recommended troubleshooting order is:

1. `systemctl status nginx`
2. `nginx -t`
3. `tail -f error.log`
4. `tail -f access.log`
5. `curl`
6. `ss`
7. `dig`
8. `openssl`
9. `top`
10. `reload nginx`

Following a consistent diagnostic workflow minimizes downtime and helps identify the root cause efficiently.

---
