# Overview

The **Permission Denied** error occurs when Nginx does not have sufficient permissions to access files, directories, sockets, certificates, or log files required to process a request.

Since Nginx typically runs as a non-root user (such as `www-data` or `nginx`), it can only access resources that the operating system explicitly permits.

Permission-related issues commonly affect:

- Website files
- Static assets
- SSL certificates
- Log files
- Unix sockets
- Configuration files
- Cache directories

---

# Impact

| Impact | Level |
|---------|-------|
| Service Availability | 🔴 Critical |
| Performance | 🟢 None |
| Security | 🟢 None |
| Production Risk | 🔴 High |

---

# When You'll See This

This issue commonly occurs when:

- Deploying new applications
- Migrating websites
- Changing file ownership
- Configuring SSL
- Using Docker bind mounts
- Deploying with CI/CD
- Running Gunicorn or PHP-FPM

---

# Affected Components

- Linux File Permissions
- Ownership
- Nginx User
- SSL Certificates
- Static Files
- Unix Sockets
- Log Files

---

# Symptoms

## Browser

```text
403 Forbidden
```

---

## Nginx Error Log

```text
Permission denied
```

---

Another Example

```text
open() "/var/www/html/index.html" failed (13: Permission denied)
```

---

SSL

```text
cannot load certificate

Permission denied
```

---

Unix Socket

```text
connect() to unix:/run/gunicorn.sock failed (13: Permission denied)
```

---

# Quick Diagnosis

## View Error Log

```bash
sudo tail -100 /var/log/nginx/error.log
```

---

## Check File Permissions

```bash
ls -l /var/www/html
```

---

## Check Directory Permissions

```bash
ls -ld /var/www/html
```

---

## Check Running User

```bash
ps aux | grep nginx
```

Typical output

```text
www-data
```

or

```text
nginx
```

---

## Check Ownership

```bash
stat /var/www/html/index.html
```

---

# Decision Tree

```text
           Permission Denied
                   │
                   ▼
          What Resource Failed?
                   │
      ┌────────────┼─────────────┐
      │            │             │
   Website      SSL File      Socket
      │            │             │
      ▼            ▼             ▼
 Check Owner   Check Owner   Check Socket
 Check chmod   Check chmod   Check User
      │            │             │
      ▼            ▼             ▼
     Retry      Restart      Test Again
```

---

# Why This Happens

Every file has:

- Owner
- Group
- Permission bits

Example:

```text
-rw-r--r--
```

Meaning:

```text
Owner

Read Write

Group

Read

Others

Read
```

If the Nginx worker process lacks permission to access the file, Linux denies access before Nginx can serve the request.

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Wrong ownership | Files owned by another user |
| Incorrect permissions | Read permission missing |
| Directory traversal denied | Missing execute (`x`) permission |
| Unix socket permissions | Backend socket inaccessible |
| SSL permissions | Certificate not readable |
| Docker bind mount | Host permissions incorrect |
| SELinux/AppArmor | Security policy blocks access |

---

# Error Message Decoder

## Permission Denied

```text
Permission denied
```

### Meaning

The operating system blocked access.

### Solution

Check:

- Owner
- Group
- Permissions

---

## Socket Permission Denied

```text
connect() failed (13: Permission denied)
```

### Meaning

Nginx cannot access the backend Unix socket.

### Solution

Verify socket ownership.

---

## SSL Permission Denied

```text
cannot load certificate
```

### Meaning

Nginx cannot read the certificate file.

### Solution

Verify certificate permissions.

---

# Step-by-Step Troubleshooting

## Step 1 — Identify the Resource

Read the error log.

```bash
sudo tail -100 /var/log/nginx/error.log
```

Locate the exact file or socket causing the failure.

---

## Step 2 — Verify Ownership

```bash
ls -l /var/www/html
```

Example

```text
-rw------- root root index.html
```

Nginx cannot read this file.

---

## Step 3 — Correct Ownership

Example

```bash
sudo chown -R www-data:www-data /var/www/html
```

Adjust the user based on your distribution.

---

## Step 4 — Verify Permissions

Example

```bash
chmod 644 index.html
```

Directories

```bash
chmod 755 /var/www/html
```

---

## Step 5 — Verify Unix Socket

Example

```bash
ls -l /run/gunicorn.sock
```

The socket owner should match the Nginx user or belong to a shared group.

---

## Step 6 — Verify SSL Permissions

Example

```bash
ls -l /etc/nginx/ssl
```

Ensure Nginx can read:

- fullchain.pem
- privkey.pem

---

## Step 7 — Restart Services

```bash
sudo systemctl restart gunicorn

sudo systemctl restart nginx
```

---

# Best Practices

- Follow the principle of least privilege.
- Avoid using `chmod 777`.
- Use dedicated users for applications.
- Store certificates outside the web root.
- Keep consistent ownership across deployments.
- Document required file permissions.

---

# Real Production Scenario

## Problem

A Django application suddenly returned:

```text
502 Bad Gateway
```

---

## Investigation

Nginx logs contained:

```text
connect() to unix:/run/gunicorn.sock failed (13: Permission denied)
```

The Gunicorn service recreated the socket with ownership:

```text
root root
```

while Nginx was running as:

```text
www-data
```

---

## Resolution

The Gunicorn service configuration was updated to create the socket with the correct ownership and permissions.

After restarting both services, Nginx successfully connected to the backend.

---

# Verification Checklist

After fixing the issue:

- ✅ File ownership is correct
- ✅ File permissions are correct
- ✅ Directory permissions allow traversal
- ✅ SSL certificates are readable
- ✅ Unix sockets are accessible
- ✅ Website returns HTTP 200

---

# Common Mistakes

❌ Using `chmod 777` to solve permission problems

❌ Forgetting directory execute (`x`) permission

❌ Running Nginx as a different user than expected

❌ Ignoring Unix socket permissions

❌ Mounting Docker volumes with incorrect ownership

❌ Forgetting SELinux or AppArmor policies

---

# Prevention Tips

- Standardize ownership during deployments.
- Automate permission checks in CI/CD pipelines.
- Use dedicated service accounts.
- Monitor permission-related errors.
- Test deployments with the same user as production.

---

# Production Notes

Permission errors can affect **any file that Nginx interacts with**, not just website content.

When troubleshooting, investigate in this order:

1. Error log
2. File ownership
3. File permissions
4. Directory permissions
5. Unix socket permissions
6. SSL certificate permissions
7. SELinux/AppArmor policies

Avoid using overly permissive permissions. Correct ownership is usually a safer and more maintainable solution than granting unrestricted access.

---
