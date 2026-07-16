# Overview

One of the most common problems encountered when deploying websites behind Nginx is that **CSS, JavaScript, images, fonts, or other static assets fail to load**.

Although the main application may load successfully, missing static resources can cause:

- Broken layouts
- Missing images
- Unstyled pages
- JavaScript errors
- Missing fonts
- Slow page rendering

This issue is usually caused by incorrect file paths, improper Nginx configuration, deployment mistakes, or permission problems.

---

# Impact

| Impact | Level |
|---------|-------|
| Service Availability | 🟡 Medium |
| Performance | 🟠 High |
| Security | 🟢 None |
| Production Risk | 🟠 High |

---

# When You'll See This

This issue commonly occurs when:

- Deploying a new application
- Moving static assets
- Configuring Docker volumes
- Deploying Django applications
- Deploying React/Vue/Angular applications
- Changing the `root` or `alias` directive
- Migrating servers

---

# Affected Components

- Static Files
- Root Directive
- Alias Directive
- Docker Volumes
- Reverse Proxy
- Browser Cache
- CDN

---

# Symptoms

## Browser

```text
404 Not Found
```

---

## Browser Console

```text
Failed to load resource

404 (Not Found)
```

---

## Developer Tools

```
GET /static/css/style.css

404
```

---

## Nginx Error Log

```text
open() "/var/www/html/static/css/style.css"

failed (2: No such file or directory)
```

---

## Website

- Images missing
- CSS not loading
- JavaScript not loading
- Fonts missing

---

# Quick Diagnosis

## Validate Configuration

```bash
sudo nginx -t
```

---

## Verify Static Directory

```bash
ls -l /var/www/html/static
```

---

## Check Error Log

```bash
sudo tail -100 /var/log/nginx/error.log
```

---

## Verify Browser Requests

Open

```
Developer Tools

→ Network
```

---

## Test Static File

```bash
curl http://localhost/static/logo.png
```

---

# Decision Tree

```text
         Static Files Missing
                  │
                  ▼
        Does File Exist?
            │          │
           No         Yes
            │          │
            ▼          ▼
     Deploy Static   Check Nginx Path
                          │
                ┌─────────┴─────────┐
                │                   │
             Wrong Path        Correct Path
                │                   │
                ▼                   ▼
          Fix root/alias     Check Permissions
                                      │
                                      ▼
                               Test Again
```

---

# Why This Happens

Typical request flow:

```text
Browser

↓

Nginx

↓

Location Block

↓

root / alias

↓

Filesystem

↓

Static File

↓

Response
```

If any step fails, the browser cannot load the resource.

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Missing files | Static assets not deployed |
| Wrong root | Incorrect document root |
| Incorrect alias | Alias points to wrong directory |
| Wrong location block | Request routed incorrectly |
| Docker volume issue | Static directory not mounted |
| File permissions | Nginx cannot read files |
| Browser cache | Old asset references |

---

# Error Message Decoder

## File Not Found

```text
No such file or directory
```

### Meaning

The requested file does not exist.

### Solution

Verify the deployment and file path.

---

## Permission Denied

```text
Permission denied
```

### Meaning

Nginx cannot read the static file.

### Solution

Verify ownership and permissions.

---

## 404 Not Found

```text
GET /static/style.css

404
```

### Meaning

The browser requested a file that Nginx could not locate.

### Solution

Verify the `root`, `alias`, and deployment directory.

---

# Step-by-Step Troubleshooting

## Step 1 — Verify File Exists

```bash
ls -l /var/www/html/static
```

Ensure the requested file exists.

---

## Step 2 — Verify Nginx Configuration

Example

```nginx
location /static/ {

    root /var/www/html;

}
```

or

```nginx
location /static/ {

    alias /var/www/static/;

}
```

Verify the configured path.

---

## Step 3 — Check File Permissions

```bash
ls -l /var/www/html/static
```

Typical permissions:

```text
-rw-r--r--
```

Directories:

```text
drwxr-xr-x
```

---

## Step 4 — Verify Browser Request

Open:

```
Developer Tools

→ Network
```

Verify:

- Requested URL
- HTTP Status
- Response Headers

---

## Step 5 — Docker Deployment

Verify mounted volumes.

```bash
docker inspect nginx
```

Confirm the static directory is available inside the container.

---

## Step 6 — Django Applications

Verify static files have been collected.

```bash
python manage.py collectstatic
```

Ensure Nginx serves the configured `STATIC_ROOT`.

---

## Step 7 — Validate Configuration

```bash
sudo nginx -t
```

---

## Step 8 — Reload Nginx

```bash
sudo systemctl reload nginx
```

---

# Best Practices

- Store static files separately from application code.
- Use `alias` carefully.
- Deploy static assets before updating Nginx.
- Use browser Developer Tools during testing.
- Use a CDN for production environments.
- Version static assets to avoid cache conflicts.

---

# Real Production Scenario

## Problem

A Django application deployed successfully, but users reported that the website appeared without styling.

The browser displayed multiple:

```text
404 Not Found
```

errors for CSS and JavaScript files.

---

## Investigation

Running:

```bash
python manage.py collectstatic
```

showed that static assets had never been collected into the production directory.

Nginx was correctly configured to serve:

```text
/var/www/static
```

but the directory was empty.

---

## Resolution

Static files were collected.

```bash
python manage.py collectstatic
```

Nginx was reloaded.

All CSS, JavaScript, and images loaded successfully.

---

# Verification Checklist

After fixing the issue:

- ✅ Static files exist
- ✅ Nginx location is correct
- ✅ Root/Alias configuration is correct
- ✅ File permissions are correct
- ✅ Docker volume is mounted (if applicable)
- ✅ Browser loads all static assets
- ✅ Website renders correctly

---

# Common Mistakes

❌ Forgetting `collectstatic` in Django

❌ Mixing `root` and `alias`

❌ Incorrect Docker volume mappings

❌ Wrong file permissions

❌ Hardcoded development paths

❌ Ignoring browser Developer Tools

---

# Prevention Tips

- Automate static asset deployment.
- Validate static URLs before release.
- Test using browser Developer Tools.
- Version static assets.
- Store static assets in a dedicated directory.
- Monitor 404 errors for static resources.

---

# Production Notes

Static file issues are among the **most common deployment problems**.

When troubleshooting, investigate in this order:

1. Does the file exist?
2. Is the browser requesting the correct URL?
3. Is `root` or `alias` configured correctly?
4. Are file permissions correct?
5. Are Docker volumes mounted?
6. Has the application generated or collected static files?
7. Is browser caching serving old asset references?

In production environments, deployment mistakes—rather than Nginx configuration—are the most common cause of missing static assets.

---
