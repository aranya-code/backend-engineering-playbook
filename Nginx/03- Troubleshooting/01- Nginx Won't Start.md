# Overview

One of the most common issues encountered while working with Nginx is that the service fails to start or immediately exits after startup.

This problem can occur due to:

- Configuration syntax errors
- Port conflicts
- Permission issues
- Missing SSL certificates
- Invalid directives
- Incorrect file paths
- System resource limitations

Fortunately, Nginx usually provides detailed error messages that make troubleshooting straightforward.

This guide walks through a systematic approach to diagnosing and resolving startup failures.

---

# Symptoms

You may observe one or more of the following symptoms.

## Browser

```text
This site can't be reached
```

or

```text
ERR_CONNECTION_REFUSED
```

---

## Systemd

```text
Failed to start nginx.service
```

---

## Service Status

```bash
sudo systemctl status nginx
```

Output:

```text
Active: failed (Result: exit-code)
```

---

## Docker

```bash
docker ps
```

Container repeatedly exits.

```text
Exited (1)
```

---

## Kubernetes

```bash
kubectl get pods
```

```text
CrashLoopBackOff
```

---

# Quick Diagnosis

Always start with these commands.

## Validate Configuration

```bash
sudo nginx -t
```

---

## Check Service Status

```bash
sudo systemctl status nginx
```

---

## View Error Logs

```bash
sudo tail -50 /var/log/nginx/error.log
```

---

## View System Logs

```bash
sudo journalctl -u nginx
```

---

## Check Listening Ports

```bash
sudo ss -tulpn
```

or

```bash
sudo netstat -tulpn
```

---

## Docker

```bash
docker logs nginx
```

---

## Kubernetes

```bash
kubectl logs <pod-name>
```

---

# Decision Tree

```text
                    Nginx Won't Start
                            │
                            ▼
                 Run: nginx -t
                            │
          ┌─────────────────┴─────────────────┐
          │                                   │
      Syntax Error                        Configuration OK
          │                                   │
      Fix Configuration                Check Service Status
                                              │
                          ┌───────────────────┴───────────────────┐
                          │                                       │
                    Port Already Used                     Service Still Fails
                          │                                       │
                 Find Conflicting Process                 Check Error Logs
                          │                                       │
                          ▼                                       ▼
                  Stop Conflicting App                SSL / Permissions /
                                                     Missing Files /
                                                     Resource Issues
```

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Invalid configuration | Syntax or directive errors in configuration files |
| Port conflict | Another service is already using port 80 or 443 |
| Missing SSL certificate | Configured certificate or key file does not exist |
| Permission issue | Nginx cannot access required files or directories |
| Invalid file path | Incorrect `root`, `alias`, or include paths |
| Unsupported directive | Directive not supported by installed Nginx version |
| Resource limitation | Insufficient memory or system resources |

---

# Error Message Decoder

## Invalid Configuration

```text
nginx: [emerg] unexpected "}"
```

### Meaning

There is a syntax error in the configuration.

### Fix

Run:

```bash
sudo nginx -t
```

Correct the reported line.

---

## Port Already in Use

```text
bind() to 0.0.0.0:80 failed
```

### Meaning

Another application is already listening on port 80.

### Find the Process

```bash
sudo lsof -i :80
```

or

```bash
sudo ss -tulpn
```

---

## Missing SSL Certificate

```text
cannot load certificate
```

### Meaning

The configured certificate file cannot be found.

### Verify

```bash
ls -l /etc/ssl/
```

Confirm that the paths specified in:

```nginx
ssl_certificate

ssl_certificate_key
```

are correct.

---

## Permission Denied

```text
Permission denied
```

### Meaning

Nginx does not have permission to access a required file.

### Verify

```bash
ls -l
```

Check ownership and permissions.

---

# Step-by-Step Troubleshooting

## Step 1 — Validate the Configuration

Always begin with:

```bash
sudo nginx -t
```

Expected output:

```text
syntax is ok

test is successful
```

---

## Step 2 — Check Service Status

```bash
sudo systemctl status nginx
```

Look for:

- Exit code
- Failure reason
- Recent log entries

---

## Step 3 — Read the Error Log

```bash
sudo tail -100 /var/log/nginx/error.log
```

Most startup problems are clearly described here.

---

## Step 4 — Check Port Usage

```bash
sudo ss -tulpn
```

or

```bash
sudo lsof -i :80

sudo lsof -i :443
```

If another service is using the port, stop it or configure Nginx to use a different port.

---

## Step 5 — Verify File Paths

Ensure that all configured paths exist:

- SSL certificates
- Root directory
- Included configuration files
- Static file directories

Example:

```bash
ls -l /var/www/html
```

---

# Real Production Scenario

## Problem

After deploying a new configuration, Nginx failed to start.

Users reported:

```text
502 Bad Gateway
```

---

## Investigation

Configuration test:

```bash
sudo nginx -t
```

Output:

```text
cannot load certificate
```

The deployment pipeline copied the configuration but failed to copy the new certificate files.

---

## Resolution

The missing certificate files were restored.

Configuration validated successfully:

```bash
sudo nginx -t
```

Nginx was reloaded:

```bash
sudo systemctl restart nginx
```

The website became available again.

---

# Verification Checklist

After fixing the issue, verify the following:

- ✅ Configuration test passes (`nginx -t`)
- ✅ Service is active (`systemctl status nginx`)
- ✅ Ports 80 and 443 are listening
- ✅ Error log contains no startup errors
- ✅ Website loads successfully
- ✅ HTTPS certificate is valid (if applicable)

---

# Common Mistakes

❌ Editing configuration without validating it

❌ Forgetting to reload or restart Nginx

❌ Incorrect SSL certificate paths

❌ Running another web server (Apache, Caddy, etc.) on the same port

❌ Incorrect file permissions

❌ Using directives unsupported by the installed Nginx version

---

# Prevention Tips

- Always run `nginx -t` before reloading the service.
- Keep configuration files under version control.
- Validate SSL certificate paths during deployments.
- Monitor the Nginx error log for startup issues.
- Use automated configuration validation in CI/CD pipelines.

---

