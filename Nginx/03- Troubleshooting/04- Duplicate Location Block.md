# Overview

A **Duplicate Location Block** error occurs when multiple `location` blocks match the same request in an unintended way or when duplicate configurations create ambiguity.

Although Nginx has well-defined location matching rules, duplicate or conflicting location blocks often lead to unexpected routing behavior, configuration errors, or startup failures.

This issue commonly appears after copying configuration snippets, merging configuration files, or managing large applications with multiple developers.

---

# Impact

| Impact | Level |
|---------|-------|
| Service Availability | 🟡 Medium |
| Performance | 🟢 Low |
| Security | 🟡 Medium |
| Production Risk | 🟡 Medium |

---

# When You'll See This

This issue commonly occurs when:

- Copying configuration from tutorials
- Splitting configuration into multiple files
- Multiple developers edit the same server block
- Migrating applications
- Large reverse proxy configurations
- Managing many virtual hosts

---

# Affected Components

- Server Block
- Location Block
- Request Routing
- Reverse Proxy
- Static File Serving

---

# Symptoms

## Configuration Test

```bash
sudo nginx -t
```

Possible Output

```text
duplicate location "/"
```

or

```text
conflicting location "/api"
```

---

## Incorrect Routing

Example:

```
https://example.com/api
```

Instead of reaching the API backend:

```
404 Not Found
```

or

```
Wrong backend server
```

---

## Unexpected Static Files

Users receive static files instead of dynamic application responses.

---

# Quick Diagnosis

## Validate Configuration

```bash
sudo nginx -t
```

---

## Print Complete Configuration

```bash
sudo nginx -T
```

---

## Search Location Blocks

```bash
grep -rn "location" /etc/nginx/
```

---

## View Included Files

```bash
ls /etc/nginx/conf.d/

ls /etc/nginx/sites-enabled/
```

---

# Decision Tree

```text
                 Wrong Routing
                       │
                       ▼
                 Run nginx -t
                       │
          ┌────────────┴────────────┐
          │                         │
   Configuration Error          No Errors
          │                         │
          ▼                         ▼
 Find Duplicate Block       Check Matching Rules
          │                         │
          ▼                         ▼
 Remove Duplicate       Verify Location Priority
          │
          ▼
     Test Configuration
          │
          ▼
      Reload Nginx
```

---

# Why This Happens

Nginx evaluates location blocks using a defined priority.

General order:

```text
Exact Match (=)

↓

Prefix Match

↓

Longest Prefix

↓

Regular Expression

↓

Default Location
```

If multiple location blocks overlap, requests may be routed differently than expected.

---

# Incorrect Configuration

Example:

```nginx
location / {

    root /var/www/html;

}

location / {

    proxy_pass http://backend;

}
```

Result

```text
Duplicate location "/"
```

---

# Another Incorrect Example

```nginx
location /api {

    proxy_pass http://api1;

}

location /api {

    proxy_pass http://api2;

}
```

Only one location should exist for the same path.

---

# Correct Configuration

```nginx
location / {

    root /var/www/html;

}

location /api {

    proxy_pass http://backend;

}
```

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Copy-paste | Duplicate configuration copied accidentally |
| Multiple include files | Same location defined in different files |
| Merge conflicts | Duplicate blocks after Git merge |
| Incorrect refactoring | Old location block not removed |
| Conflicting regex | Multiple regex locations matching the same request |

---

# Error Message Decoder

## Duplicate Location

```text
duplicate location "/"
```

### Meaning

Two identical location blocks exist.

### Solution

Remove one of them.

---

## Conflicting Location

```text
conflicting location "/api"
```

### Meaning

Multiple location blocks can process the same request.

### Solution

Review location matching rules.

---

# Step-by-Step Troubleshooting

## Step 1 — Validate Configuration

```bash
sudo nginx -t
```

Read the reported file and line number.

---

## Step 2 — Search All Location Blocks

```bash
grep -rn "location" /etc/nginx/
```

Example:

```text
/etc/nginx/nginx.conf

/etc/nginx/conf.d/api.conf

/etc/nginx/sites-enabled/default
```

---

## Step 3 — Check Included Files

Sometimes duplicate locations exist because two configuration files are loaded.

Verify:

```nginx
include /etc/nginx/conf.d/*.conf;

include /etc/nginx/sites-enabled/*;
```

---

## Step 4 — Review Matching Priority

Remember:

```text
=

↓

Longest Prefix

↓

Regex

↓

Default
```

Verify that the intended location has the highest priority.

---

## Step 5 — Test Again

```bash
sudo nginx -t
```

Expected

```text
syntax is ok

test is successful
```

---

## Step 6 — Reload Configuration

```bash
sudo systemctl reload nginx
```

---

# Best Practices

- Keep one responsibility per location block.
- Avoid duplicate URL prefixes.
- Group related routes together.
- Document complex regex locations.
- Test configuration after every change.

---

# Real Production Scenario

## Problem

An engineering team introduced a new API configuration.

Both files contained:

```nginx
location /api
```

The application began routing requests inconsistently.

---

## Investigation

Running:

```bash
sudo nginx -T
```

revealed two included configuration files defining the same location.

---

## Resolution

The duplicate block was removed.

Configuration validated successfully.

```bash
sudo nginx -t
```

Nginx was reloaded without downtime.

---

# Verification Checklist

After fixing the issue:

- ✅ Configuration validation succeeds
- ✅ Only one location exists for each route
- ✅ Requests reach the correct backend
- ✅ Static files load correctly
- ✅ Reverse proxy behaves as expected

---

# Common Mistakes

❌ Defining the same location twice

❌ Forgetting included configuration files

❌ Mixing regex and prefix locations unnecessarily

❌ Ignoring location matching priority

❌ Copying configuration without review

---

# Prevention Tips

- Keep configuration modular and organized.
- Review location blocks during code reviews.
- Avoid duplicate URL paths.
- Use `nginx -T` before production deployments.
- Store configuration in version control.

---

# Production Notes

In large environments, duplicate locations usually appear after:

- Git merge conflicts
- Infrastructure automation
- Configuration templating
- Multiple include files

Automated configuration validation in CI/CD pipelines can detect these issues before deployment.

---
