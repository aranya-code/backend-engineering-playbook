# Overview

The **404 Not Found** error indicates that Nginx successfully received and processed the client's request but could not locate the requested resource.

Unlike a **403 Forbidden**, where the resource exists but access is denied, a **404 Not Found** response means that Nginx could not find the requested file, directory, or backend endpoint.

This issue commonly occurs because of:

- Incorrect `root` or `alias` directive
- Missing files
- Incorrect `location` blocks
- Wrong `try_files` configuration
- Incorrect reverse proxy routing
- Deployment issues
- Case-sensitive filename mismatches

---

# Impact

| Impact | Level |
|---------|-------|
| Service Availability | 🟡 Medium |
| Performance | 🟢 None |
| Security | 🟢 None |
| Production Risk | 🟡 Medium |

---

# When You'll See This

This issue commonly occurs when:

- Deploying a new application
- Migrating websites
- Moving static assets
- Renaming files
- Configuring new location blocks
- Deploying Single Page Applications (SPA)

---

# Affected Components

- Static File Serving
- Root Directive
- Alias Directive
- Location Blocks
- Reverse Proxy
- try_files Directive

---

# Symptoms

## Browser

```text
404 Not Found
```

---

## Access Log

```text
GET /images/logo.png HTTP/1.1

404
```

---

## Error Log

```text
open() "/var/www/html/images/logo.png" failed

(2: No such file or directory)
```

---

# Quick Diagnosis

## Validate Configuration

```bash
sudo nginx -t
```

---

## Check Access Log

```bash
sudo tail -50 /var/log/nginx/access.log
```

---

## Check Error Log

```bash
sudo tail -50 /var/log/nginx/error.log
```

---

## Verify Requested File

```bash
ls -l /var/www/html
```

---

## Print Configuration

```bash
sudo nginx -T
```

---

# Decision Tree

```text
               404 Not Found
                     │
                     ▼
         Does requested file exist?
               │              │
              No             Yes
               │              │
               ▼              ▼
       Upload/Create File   Check root/alias
                              │
                    ┌─────────┴─────────┐
                    │                   │
               Correct Path       Wrong Path
                    │                   │
                    ▼                   ▼
          Check Location Block   Fix Configuration
                    │
                    ▼
             Validate & Reload
```

---

# Why This Happens

Nginx determines the file to serve using:

- `server`
- `location`
- `root`
- `alias`
- `try_files`

If the final calculated path does not exist, Nginx returns:

```text
404 Not Found
```

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Missing file | Requested resource does not exist |
| Wrong root | Incorrect document root |
| Incorrect alias | Alias points to the wrong directory |
| Wrong location block | Request matches an unexpected location |
| Incorrect try_files | Invalid fallback configuration |
| Deployment issue | Static assets not copied |
| Case mismatch | Linux filenames are case-sensitive |

---

# Error Message Decoder

## File Not Found

```text
No such file or directory
```

### Meaning

The requested file does not exist.

### Solution

Verify:

```bash
ls -l
```

---

## open() Failed

```text
open() failed (2)
```

### Meaning

Nginx attempted to open a file that could not be found.

### Solution

Verify the `root` or `alias` configuration.

---

## Incorrect Alias

Example

```nginx
location /images {

    alias /data/img;
}
```

If:

```text
/data/img
```

does not exist,

Nginx returns:

```text
404 Not Found
```

---

# Step-by-Step Troubleshooting

## Step 1 — Verify the File Exists

Example

```bash
ls -l /var/www/html/images
```

Confirm that the requested file exists.

---

## Step 2 — Verify Root Directive

Example

```nginx
root /var/www/html;
```

Ensure the path matches the actual website directory.

---

## Step 3 — Verify Alias Directive

Example

```nginx
location /images {

    alias /data/images;
}
```

Confirm the alias directory exists.

---

## Step 4 — Verify Location Block

Ensure the request is matching the expected location.

Example

```nginx
location /api {

    proxy_pass http://backend;
}
```

---

## Step 5 — Check try_files

Example

```nginx
try_files $uri $uri/ =404;
```

Ensure the fallback is appropriate for your application.

For Single Page Applications (SPA), you may need:

```nginx
try_files $uri /index.html;
```

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

- Keep static assets organized.
- Verify all deployment paths.
- Use meaningful location blocks.
- Test every new route after deployment.
- Avoid unnecessary alias directives.

---

# Real Production Scenario

## Problem

A frontend deployment succeeded, but users received:

```text
404 Not Found
```

for every JavaScript file.

---

## Investigation

The deployment pipeline copied files to:

```text
/var/www/frontend
```

However, Nginx was configured with:

```nginx
root /var/www/html;
```

---

## Resolution

The root directive was updated:

```nginx
root /var/www/frontend;
```

Configuration validation succeeded.

```bash
sudo nginx -t
```

The website loaded successfully.

---

# Verification Checklist

After fixing the issue:

- ✅ Requested file exists
- ✅ Root directive is correct
- ✅ Alias directive is correct
- ✅ Location block matches the request
- ✅ try_files is configured correctly
- ✅ Configuration validation succeeds
- ✅ Website returns HTTP 200

---

# Common Mistakes

❌ Typographical errors in filenames

❌ Incorrect `root` directive

❌ Misusing `alias`

❌ Missing static assets after deployment

❌ Forgetting Linux is case-sensitive

❌ Incorrect `try_files` configuration

---

# Prevention Tips

- Keep deployment directories consistent.
- Verify static assets after deployment.
- Use automated deployment validation.
- Test important URLs before releasing changes.
- Monitor Access and Error Logs after deployments.

---

# Production Notes

In production environments, **404 errors are often caused by deployment problems rather than Nginx itself**.

Typical examples include:

- Missing frontend build artifacts
- Incorrect Docker volume mounts
- Wrong Kubernetes Persistent Volume mounts
- Incorrect CDN synchronization
- Incorrect static file collection (`collectstatic` in Django)

Always verify the application deployment before modifying the Nginx configuration.

---
