# Overview

A **Browser Cache Problem** occurs when the browser continues to use previously downloaded files instead of requesting the latest version from the server.

Although caching significantly improves website performance by reducing network requests, it can also cause users to see outdated content after deployments.

Typical symptoms include:

- Old CSS after deployment
- JavaScript changes not reflected
- Images not updating
- HTML displaying outdated content
- Users reporting issues that cannot be reproduced on another device

In most cases, Nginx is serving the correct files, but the browser is using cached copies.

---

# Impact

| Impact | Level |
|---------|-------|
| Service Availability | 🟢 Low |
| Performance | 🟢 Positive |
| Security | 🟡 Medium |
| Production Risk | 🟡 Medium |

---

# When You'll See This

This issue commonly occurs when:

- Deploying new frontend versions
- Updating CSS or JavaScript files
- Changing images or fonts
- Configuring Cache-Control headers
- Using CDN caching
- Deploying Single Page Applications (SPA)

---

# Affected Components

- Browser Cache
- HTTP Headers
- Cache-Control
- ETag
- Expires Header
- CDN
- Static Assets

---

# Symptoms

## Browser

- Old website version appears
- CSS changes are missing
- JavaScript updates do not work

---

## Browser Developer Tools

```text
Status Code: 304 Not Modified
```

---

## Response Header

```text
Cache-Control: max-age=31536000
```

---

## Hard Refresh Fixes the Problem

```text
Ctrl + Shift + R
```

or

```text
Ctrl + F5
```

---

# Quick Diagnosis

## Open Developer Tools

```
F12
```

Go to:

```text
Network
```

---

## Disable Cache

Developer Tools →

```text
Disable Cache
```

Refresh the page.

---

## Inspect Response Headers

Look for:

```text
Cache-Control
```

```text
ETag
```

```text
Expires
```

---

## Test with curl

```bash
curl -I https://example.com
```

---

## Validate Configuration

```bash
sudo nginx -t
```

---

# Decision Tree

```text
          Old Website Version
                  │
                  ▼
         Hard Refresh Works?
            │            │
           No           Yes
            │            │
            ▼            ▼
      Check Deployment  Browser Cache
                             │
                    ┌────────┴─────────┐
                    │                  │
                Wrong Headers      Correct Headers
                    │                  │
                    ▼                  ▼
           Update Cache Rules    Version Assets
                    │
                    ▼
             Reload Nginx
```

---

# Why This Happens

Typical request flow:

```text
Browser

↓

Cache Lookup

↓

Cached Copy Exists?

│

├── Yes → Use Cached File

│

└── No

↓

Nginx

↓

Latest File
```

If the browser determines that the cached file is still valid, it skips downloading a new copy.

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Long cache lifetime | `max-age` too high |
| Missing asset versioning | Browser cannot detect changes |
| Incorrect Cache-Control | Browser caches dynamic content |
| CDN cache | CDN serves old files |
| ETag mismatch | Validation issues |
| Browser cache | Old assets remain locally stored |

---

# Error Message Decoder

## 304 Not Modified

```text
304 Not Modified
```

### Meaning

The browser already has the latest version according to the server.

### Solution

Verify that the file actually changed or use asset versioning.

---

## Cache-Control

```text
Cache-Control: max-age=31536000
```

### Meaning

The browser can cache the file for one year.

### Solution

Use long cache durations only for versioned static assets.

---

## Expires Header

```text
Expires:
```

### Meaning

Specifies when the cached resource becomes stale.

### Solution

Ensure the expiration time matches your deployment strategy.

---

# Step-by-Step Troubleshooting

## Step 1 — Verify Browser Cache

Perform a hard refresh.

```
Ctrl + Shift + R
```

If the issue disappears, it is likely a caching problem.

---

## Step 2 — Disable Cache

Open Developer Tools.

```
F12
```

Navigate to:

```
Network
```

Enable:

```text
Disable Cache
```

Refresh the page.

---

## Step 3 — Inspect Response Headers

```bash
curl -I https://example.com
```

Review:

- Cache-Control
- Expires
- ETag
- Last-Modified

---

## Step 4 — Review Nginx Configuration

Example

```nginx
location /static/ {

    expires 30d;

    add_header Cache-Control "public";

}
```

Avoid applying long cache durations to dynamic content.

---

## Step 5 — Version Static Assets

Instead of:

```text
style.css
```

Use:

```text
style.v2.css
```

or

```text
style.css?v=2
```

This forces browsers to download the updated file.

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

- Version static assets after every deployment.
- Cache CSS, JavaScript, fonts, and images.
- Avoid caching HTML pages aggressively.
- Review Cache-Control headers regularly.
- Use immutable assets where appropriate.
- Test deployments in an incognito browser.

---

# Real Production Scenario

## Problem

A new frontend release was deployed successfully.

Developers verified the changes, but users continued seeing the old interface.

---

## Investigation

Developer Tools showed:

```text
304 Not Modified
```

The CSS file was:

```text
style.css
```

Its filename had not changed for several months.

The browser continued using the cached version.

---

## Resolution

The deployment pipeline was updated to generate versioned assets.

Example:

```text
style.4d2f91.css
```

Users automatically downloaded the latest files without clearing their browser cache.

---

# Verification Checklist

After fixing the issue:

- ✅ Latest files are downloaded
- ✅ Static assets are versioned
- ✅ Cache-Control headers are appropriate
- ✅ Dynamic pages are not cached incorrectly
- ✅ Browser displays the latest content
- ✅ No stale assets remain

---

# Common Mistakes

❌ Caching HTML pages for long periods

❌ Forgetting to version CSS and JavaScript

❌ Using one-year cache durations without asset versioning

❌ Ignoring CDN cache invalidation

❌ Assuming every user has the latest files

---

# Prevention Tips

- Version static assets during every deployment.
- Configure appropriate Cache-Control headers.
- Test deployments using an incognito browser.
- Purge CDN cache after releases.
- Monitor browser caching behavior.

---

# Production Notes

Browser caching problems are **deployment issues more often than Nginx issues**.

Investigate in this order:

1. Hard refresh the browser
2. Inspect response headers
3. Review Cache-Control settings
4. Check ETag and Last-Modified headers
5. Verify asset versioning
6. Purge CDN cache if applicable

Using **hashed filenames** for static assets is considered the industry standard and eliminates most browser cache problems after deployments.

---
