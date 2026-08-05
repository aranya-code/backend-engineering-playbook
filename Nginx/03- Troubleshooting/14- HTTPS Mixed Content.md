# Overview

A **Mixed Content** issue occurs when a web page is loaded over **HTTPS**, but some of its resources are still requested using **HTTP**.

Modern browsers consider HTTP resources insecure because they are transmitted without encryption.

As a result, browsers either:

- Block the insecure resource
- Display a security warning
- Mark the website as "Not Secure"

Mixed content commonly affects:

- Images
- CSS files
- JavaScript files
- Fonts
- Videos
- API requests
- AJAX calls
- WebSocket connections

---

# Impact

| Impact | Level |
|---------|-------|
| Service Availability | 🟢 Low |
| Performance | 🟢 None |
| Security | 🔴 High |
| Production Risk | 🟡 Medium |

---

# When You'll See This

This issue commonly occurs when:

- Migrating from HTTP to HTTPS
- Deploying SSL certificates
- Moving legacy websites
- Using hardcoded HTTP URLs
- Loading third-party resources
- Using CDNs incorrectly

---

# Affected Components

- HTTPS
- SSL/TLS
- Browser Security
- HTML
- CSS
- JavaScript
- Reverse Proxy

---

# Symptoms

## Browser Warning

```text
This page is trying to load scripts from unauthenticated sources.
```

---

Chrome Developer Tools

```text
Mixed Content:

The page at

https://example.com

was loaded over HTTPS,

but requested an insecure resource

http://example.com/app.js
```

---

Browser Address Bar

```text
⚠ Not Secure
```

or

```text
Connection is not fully secure
```

---

# Quick Diagnosis

## Open Browser Developer Tools

```
F12
```

Navigate to:

```text
Console
```

or

```text
Network
```

---

## Search for HTTP Resources

```bash
grep -rn "http://" .
```

---

## Test Website

```bash
curl -I https://example.com
```

---

## Check HTML Source

```text
View Source
```

Look for:

```html
http://
```

---

# Decision Tree

```text
            Browser Shows Warning
                     │
                     ▼
           Open Developer Tools
                     │
                     ▼
        Mixed Content Warning?
              │            │
             No           Yes
              │            │
              ▼            ▼
      Check Certificate  Locate HTTP URL
                              │
                     ┌────────┴─────────┐
                     │                  │
                Internal          Third-party
                  URL               Resource
                     │                  │
                     ▼                  ▼
            Change to HTTPS      Replace Provider
                     │
                     ▼
              Refresh Browser
```

---

# Why This Happens

A secure HTTPS page should load **every resource** over HTTPS.

Example:

```text
Browser

↓

HTTPS Page

↓

HTML

↓

CSS

↓

JavaScript

↓

Images

↓

Fonts

↓

API

↓

HTTPS Only
```

If even one resource is loaded using HTTP:

```text
↓

HTTP Resource

↓

Mixed Content
```

the browser may block it.

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Hardcoded HTTP URLs | HTML contains `http://` links |
| CSS references | Images loaded over HTTP |
| JavaScript requests | AJAX uses HTTP |
| API endpoints | Backend still configured for HTTP |
| CDN | External resources only support HTTP |
| WebSocket | Using `ws://` instead of `wss://` |

---

# Error Message Decoder

## Mixed Content Warning

```text
Mixed Content:
```

### Meaning

The page loaded securely, but one or more resources were requested over HTTP.

### Solution

Convert every resource to HTTPS.

---

## Blocked Script

```text
Blocked loading mixed active content
```

### Meaning

Browser blocked an insecure JavaScript file.

### Solution

Serve the script using HTTPS.

---

## Blocked Image

```text
Mixed Content:
The image was loaded over HTTP
```

### Meaning

Image is being served insecurely.

### Solution

Replace:

```text
http://
```

with

```text
https://
```

---

# Step-by-Step Troubleshooting

## Step 1 — Open Browser Developer Tools

```
F12
```

Go to:

```
Console
```

Review every Mixed Content warning.

---

## Step 2 — Identify HTTP Resources

Search project files.

```bash
grep -rn "http://" .
```

---

## Step 3 — Update URLs

Incorrect

```html
<script src="http://example.com/app.js"></script>
```

Correct

```html
<script src="https://example.com/app.js"></script>
```

---

## Step 4 — Check API Calls

Incorrect

```javascript
fetch("http://api.example.com")
```

Correct

```javascript
fetch("https://api.example.com")
```

---

## Step 5 — Verify WebSocket Connections

Incorrect

```text
ws://example.com/socket
```

Correct

```text
wss://example.com/socket
```

---

## Step 6 — Configure HTTPS Redirect

Example

```nginx
server {

    listen 80;

    server_name example.com;

    return 301 https://$host$request_uri;

}
```

---

## Step 7 — Reload Nginx

```bash
sudo nginx -t

sudo systemctl reload nginx
```

---

# Best Practices

- Always use HTTPS URLs.
- Use protocol-relative or relative URLs where appropriate.
- Enable HSTS after migration.
- Avoid loading third-party HTTP resources.
- Test websites using browser developer tools.
- Redirect all HTTP traffic to HTTPS.

---

# Real Production Scenario

## Problem

After enabling HTTPS, users reported that the website displayed:

```text
Connection is not fully secure
```

Although the page loaded correctly, several icons and JavaScript files failed to load.

---

## Investigation

Chrome Developer Tools showed:

```text
Mixed Content:

http://cdn.example.com/app.js
```

The CDN URL was hardcoded to HTTP.

---

## Resolution

The application configuration was updated to use:

```text
https://cdn.example.com
```

After clearing the browser cache and reloading the page, the browser displayed:

```text
Connection is secure
```

---

# Verification Checklist

After fixing the issue:

- ✅ All resources load over HTTPS
- ✅ Browser shows a secure connection
- ✅ No Mixed Content warnings
- ✅ API requests use HTTPS
- ✅ WebSocket uses `wss://`
- ✅ HTTP automatically redirects to HTTPS

---

# Common Mistakes

❌ Hardcoding HTTP URLs

❌ Forgetting CSS image URLs

❌ Using `ws://` instead of `wss://`

❌ Loading third-party scripts over HTTP

❌ Ignoring browser console warnings

❌ Assuming HTTPS is enabled just because the homepage loads

---

# Prevention Tips

- Enforce HTTPS throughout the application.
- Use Content Security Policy (CSP) to block insecure resources.
- Enable HSTS after validating HTTPS.
- Scan applications regularly for HTTP links.
- Review browser console warnings during testing.

---

# Production Notes

Mixed Content issues are **application-level problems**, not Nginx configuration problems.

During production migrations:

1. Enable HTTPS.
2. Redirect all HTTP traffic.
3. Update application URLs.
4. Update CDN URLs.
5. Update API endpoints.
6. Test using browser developer tools.
7. Enable HSTS only after confirming that every resource loads securely.

---
