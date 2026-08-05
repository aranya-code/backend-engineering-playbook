# Overview

Docker volumes allow containers to access persistent files stored outside the container.

For Nginx, volumes are commonly used to mount:

- Nginx configuration files
- SSL certificates
- Static files
- Media files
- Log files
- HTML content

Incorrect volume configuration can prevent Nginx from starting, cause configuration files to disappear, or result in **404**, **403**, and **502** errors.

---

# Impact

| Impact | Level |
|---------|-------|
| Service Availability | 🔴 High |
| Performance | 🟢 None |
| Security | 🟡 Medium |
| Production Risk | 🔴 High |

---

# When You'll See This

This issue commonly occurs when:

- Deploying Docker Compose applications
- Mounting configuration files
- Mounting SSL certificates
- Migrating applications
- Deploying static files
- Sharing files between host and container

---

# Affected Components

- Docker Volumes
- Bind Mounts
- Nginx Configuration
- SSL Certificates
- Static Files
- Docker Compose

---

# Symptoms

## Nginx Fails to Start

```text
nginx: [emerg] open() "/etc/nginx/nginx.conf" failed
```

---

## Browser

```text
404 Not Found
```

---

Another Example

```text
403 Forbidden
```

---

Docker Logs

```text
No such file or directory
```

---

Configuration Test

```bash
nginx -t
```

Output

```text
failed (2: No such file or directory)
```

---

# Quick Diagnosis

## View Running Containers

```bash
docker ps
```

---

## Inspect Container

```bash
docker inspect nginx
```

---

## Verify Mounted Volumes

```bash
docker inspect nginx --format '{{json .Mounts}}'
```

---

## Enter Container

```bash
docker exec -it nginx sh
```

---

## Verify Mounted Files

```bash
ls -l /etc/nginx/
```

---

# Decision Tree

```text
          Files Missing?
                │
                ▼
        Check Docker Mount
                │
      ┌─────────┴──────────┐
      │                    │
     Missing          Mount Exists
      │                    │
      ▼                    ▼
 Check Compose       Check Permissions
      │                    │
      ▼                    ▼
 Restart Container    Verify File Paths
              │
              ▼
        Test Configuration
```

---

# Why This Happens

Docker volumes replace files inside the container with files from the host.

Typical architecture

```text
Host Machine

↓

Docker Volume

↓

Nginx Container

↓

Configuration

↓

Website
```

If the mounted directory is empty or incorrect, Nginx cannot find its configuration or website files.

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Wrong host path | Mounted directory does not exist |
| Incorrect container path | Mounted to wrong location |
| Empty directory | Host directory contains no files |
| File permissions | Nginx cannot read mounted files |
| Incorrect Compose file | Wrong volume mapping |
| Read-only mount | Files cannot be updated |

---

# Error Message Decoder

## File Not Found

```text
No such file or directory
```

### Meaning

The mounted file or directory does not exist.

### Solution

Verify the host path.

---

## Cannot Load Configuration

```text
open() "/etc/nginx/nginx.conf" failed
```

### Meaning

The configuration file was not mounted correctly.

### Solution

Verify the volume mapping.

---

## Permission Denied

```text
Permission denied
```

### Meaning

Nginx cannot access the mounted files.

### Solution

Verify ownership and permissions on the host.

---

# Step-by-Step Troubleshooting

## Step 1 — Inspect Docker Compose

Example

```yaml
services:

  nginx:

    volumes:

      - ./nginx/nginx.conf:/etc/nginx/nginx.conf

      - ./static:/var/www/static
```

Verify every host path exists.

---

## Step 2 — Verify Mounts

```bash
docker inspect nginx
```

Look for

```text
Mounts
```

---

## Step 3 — Enter Container

```bash
docker exec -it nginx sh
```

Verify mounted files

```bash
ls -l /etc/nginx

ls -l /var/www/static
```

---

## Step 4 — Verify Host Files

Example

```bash
ls -l ./nginx

ls -l ./static
```

---

## Step 5 — Check Permissions

Example

```bash
chmod -R 755 ./static
```

Verify Nginx can read every file.

---

## Step 6 — Restart Containers

```bash
docker compose down

docker compose up -d
```

---

# Best Practices

- Mount directories instead of individual files when possible.
- Keep configuration under version control.
- Use named volumes for persistent data.
- Use read-only mounts for certificates.
- Verify volume mappings before deployment.

---

# Real Production Scenario

## Problem

A deployment introduced a new Docker Compose file.

Users immediately received:

```text
404 Not Found
```

for every static file.

---

## Investigation

Running

```bash
docker exec -it nginx sh
```

showed:

```text
/var/www/static

(empty)
```

The Compose file mounted:

```yaml
./assets:/var/www/static
```

However, the application stored files inside:

```text
./static
```

---

## Resolution

The volume mapping was corrected.

```yaml
./static:/var/www/static
```

Containers were restarted.

Static files loaded successfully.

---

# Verification Checklist

After fixing the issue:

- ✅ Host directory exists
- ✅ Volume mapping is correct
- ✅ Mounted files are visible inside the container
- ✅ Nginx configuration validates
- ✅ Static files load successfully
- ✅ HTTPS certificates are accessible

---

# Common Mistakes

❌ Mounting an empty directory

❌ Mounting over `/etc/nginx`

❌ Wrong relative paths

❌ Incorrect file permissions

❌ Forgetting to restart containers

❌ Editing files inside the container instead of the host

---

# Prevention Tips

- Keep all volume paths documented.
- Use absolute paths where appropriate.
- Validate Docker Compose before deployment.
- Store SSL certificates separately.
- Test mounted files inside the container before releasing.

---

# Production Notes

Volume-related problems are one of the most common causes of failed Docker deployments.

When troubleshooting, always verify:

1. Host directory exists
2. Volume mapping is correct
3. Files exist inside the container
4. File permissions are correct
5. Nginx configuration validates
6. Containers have been restarted after changes

Remember that **a mounted directory completely replaces the corresponding directory inside the container**. If the host directory is empty, the container's original files become inaccessible.

---
