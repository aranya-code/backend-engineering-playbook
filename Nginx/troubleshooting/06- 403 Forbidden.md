# Overview

The **403 Forbidden** error indicates that Nginx successfully received the client's request but refuses to serve the requested resource.

Unlike a **404 Not Found**, where the requested resource does not exist, a **403 Forbidden** response means the resource exists but the client is not allowed to access it.

This error is commonly caused by:

- Incorrect file permissions
- Incorrect directory permissions
- Missing index file
- Disabled directory listing
- Access restrictions (`allow` / `deny`)
- SELinux or AppArmor restrictions
- Incorrect root or alias configuration

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

- Deploying a new website
- Migrating applications
- Moving static files
- Changing Linux file permissions
- Deploying inside Docker
- Configuring new Virtual Hosts

---

# Affected Components

- Static File Serving
- File Permissions
- Directory Permissions
- Root Directive
- Alias Directive
- Linux File System

---

# Symptoms

## Browser

```text
403 Forbidden

You don't have permission to access this resource.
```

---

## Access Log

```text
GET /index.html HTTP/1.1

403
```

---

## Error Log

```text
Permission denied
```

or

```text
directory index of "/var/www/html/" is forbidden
```

---

# Quick Diagnosis

## Validate Configuration

```bash
sudo nginx -t
```

---

## Check Error Log

```bash
sudo tail -50 /var/log/nginx/error.log
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

## Verify Running User

```bash
ps aux | grep nginx
```

Typical user:

```text
www-data
```

or

```text
nginx
```

---

# Decision Tree

```text
              403 Forbidden
                    │
                    ▼
          Does file exist?
           │            │
          No           Yes
           │            │
           ▼            ▼
         Check      Check File
         Root       Permissions
                        │
              ┌─────────┴─────────┐
              │                   │
         Permission OK      Permission Denied
              │                   │
              ▼                   ▼
      Check Index File     Fix Ownership
              │
              ▼
     Check allow / deny
              │
              ▼
       Verify SELinux
```

---

# Why This Happens

Nginx must have permission to:

- Read the requested file
- Traverse every parent directory
- Access the configured root directory

If any permission is missing, Nginx returns:

```text
403 Forbidden
```

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Incorrect file permissions | Nginx cannot read the file |
| Incorrect directory permissions | Cannot traverse directories |
| Missing index file | No default page available |
| autoindex disabled | Directory listing disabled |
| allow / deny rules | Access explicitly blocked |
| SELinux | Security policy prevents access |
| Wrong root | Incorrect document root |

---

# Error Message Decoder

## Permission Denied

```text
Permission denied
```

### Meaning

Nginx cannot read the requested file.

### Solution

Verify:

```bash
ls -l
```

---

## Directory Index Forbidden

```text
directory index of "/var/www/html/" is forbidden
```

### Meaning

No index file exists and directory listing is disabled.

### Solution

Either:

Create

```text
index.html
```

or enable

```nginx
autoindex on;
```

---

## Access Forbidden by Rule

```text
access forbidden by rule
```

### Meaning

A configuration rule is blocking access.

Example

```nginx
deny all;
```

---

# Step-by-Step Troubleshooting

## Step 1 — Check File Exists

```bash
ls -l /var/www/html
```

Confirm the requested file exists.

---

## Step 2 — Verify Permissions

Example

```bash
ls -l index.html
```

Typical output

```text
-rw-r--r--
```

---

## Step 3 — Verify Directory Permissions

```bash
ls -ld /var/www/html
```

Typical output

```text
drwxr-xr-x
```

---

## Step 4 — Verify Owner

```bash
ls -l
```

Owner should typically be:

```text
www-data
```

or another user readable by the Nginx worker process.

---

## Step 5 — Check Configuration

Example

```nginx
root /var/www/html;
```

Ensure the path is correct.

---

## Step 6 — Check Index Directive

Example

```nginx
index index.html;
```

Verify that the file exists.

---

## Step 7 — Test Configuration

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

- Keep static files readable by the Nginx user.
- Avoid using overly permissive permissions such as `777`.
- Verify directory ownership after deployments.
- Store websites under dedicated directories.
- Test access after every deployment.

---

# Real Production Scenario

## Problem

A deployment copied all website files using the root user.

Permissions became:

```text
-rw-------
```

Only root could read the files.

Every request returned:

```text
403 Forbidden
```

---

## Investigation

Checking permissions:

```bash
ls -l
```

showed that the Nginx worker user lacked read access.

---

## Resolution

Ownership and permissions were corrected.

```bash
sudo chown -R www-data:www-data /var/www/html

sudo chmod -R 755 /var/www/html
```

The website immediately became accessible.

---

# Verification Checklist

After fixing the issue:

- ✅ Requested file exists
- ✅ File permissions are correct
- ✅ Directory permissions are correct
- ✅ Root path is valid
- ✅ Index file exists
- ✅ Configuration validates successfully
- ✅ Website returns HTTP 200

---

# Common Mistakes

❌ Setting permissions to `700`

❌ Forgetting directory execute permission

❌ Incorrect `root` directive

❌ Missing `index.html`

❌ Using `deny all` unintentionally

❌ Forgetting SELinux restrictions

---

# Prevention Tips

- Standardize deployment permissions.
- Verify ownership after CI/CD deployments.
- Use least-privilege permissions.
- Test website accessibility after every release.
- Monitor the Nginx error log regularly.

---

# Production Notes

If this issue occurs:

- On Linux → Check file permissions first.
- Inside Docker → Verify mounted volume permissions.
- In Kubernetes → Verify mounted ConfigMaps, Secrets, and Persistent Volumes.
- On SELinux-enabled systems → Check security contexts before changing permissions.

In production, **incorrect file permissions are the most common cause of HTTP 403 responses**.

---

