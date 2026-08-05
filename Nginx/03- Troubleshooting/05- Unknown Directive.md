# Overview

The **Unknown Directive** error occurs when Nginx encounters a directive that it does not recognize.

This usually happens because:

- The directive name is misspelled.
- The required Nginx module is not installed.
- The configuration was copied from another Nginx version.
- A third-party module is missing.
- The directive is being used in an unsupported version of Nginx.

Since Nginx parses the entire configuration before starting, a single unknown directive prevents the service from starting or reloading.

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

- Upgrading Nginx
- Copying configuration from online tutorials
- Installing third-party modules
- Migrating between Linux distributions
- Using Docker images with different Nginx builds
- Typing directive names manually

---

# Affected Components

- Configuration Parser
- Main Context
- HTTP Context
- Server Block
- Location Block
- Nginx Modules

---

# Symptoms

## Configuration Test

```bash
sudo nginx -t
```

Output

```text
nginx: [emerg] unknown directive "proxy_pas"
```

---

## Another Example

```text
nginx: [emerg] unknown directive "brotli"
```

---

## Service Status

```bash
sudo systemctl status nginx
```

Output

```text
Active: failed (Result: exit-code)
```

---

## Docker

```bash
docker logs nginx
```

Output

```text
unknown directive
```

---

# Quick Diagnosis

## Validate Configuration

```bash
sudo nginx -t
```

---

## Display Complete Configuration

```bash
sudo nginx -T
```

---

## Check Installed Version

```bash
nginx -V
```

---

## Locate the Directive

```bash
grep -rn "proxy_pas" /etc/nginx/
```

Replace **proxy_pas** with the directive reported in the error.

---

## Check Available Modules

```bash
nginx -V 2>&1
```

Review the compiled modules.

---

# Decision Tree

```text
             Unknown Directive
                    │
                    ▼
              Run nginx -t
                    │
         ┌──────────┴──────────┐
         │                     │
     Misspelled?          Correct Spelling
         │                     │
         ▼                     ▼
 Correct Typo          Check Installed Module
                               │
                  ┌────────────┴────────────┐
                  │                         │
            Module Missing          Version Issue
                  │                         │
                  ▼                         ▼
          Install Module         Upgrade / Replace
                  │
                  ▼
           Validate Again
```

---

# Why This Happens

Nginx only understands directives that are:

- Built into the core
- Included through compiled modules
- Available in installed dynamic modules

If a directive belongs to a module that isn't installed, Nginx reports:

```text
unknown directive
```

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Typographical error | Misspelled directive |
| Missing module | Required module not installed |
| Wrong Nginx version | Directive unsupported |
| Third-party configuration | Module unavailable |
| Copy-paste mistake | Invalid directive from another server |

---

# Error Message Decoder

## Misspelled Directive

```text
unknown directive "proxy_pas"
```

### Meaning

The directive name is incorrect.

### Incorrect

```nginx
proxy_pas http://backend;
```

### Correct

```nginx
proxy_pass http://backend;
```

---

## Missing Module

```text
unknown directive "brotli"
```

### Meaning

The Brotli module is not installed.

### Verify

```bash
nginx -V
```

Check whether the Brotli module is available.

---

## Unsupported Directive

```text
unknown directive "http3"
```

### Meaning

Your installed version of Nginx does not support HTTP/3.

### Solution

Upgrade to a compatible version.

---

# Step-by-Step Troubleshooting

## Step 1 — Read the Error Carefully

```bash
sudo nginx -t
```

Example

```text
unknown directive "proxy_pas"
```

Read the exact directive name.

---

## Step 2 — Check for Typographical Errors

Example

Incorrect

```nginx
proxy_pas
```

Correct

```nginx
proxy_pass
```

---

## Step 3 — Verify Installed Modules

```bash
nginx -V
```

Example output

```text
--with-http_ssl_module

--with-http_v2_module
```

Confirm that the required module exists.

---

## Step 4 — Check Documentation

Verify that the directive exists in the official Nginx documentation and is supported by your installed version.

---

## Step 5 — Test Configuration Again

```bash
sudo nginx -t
```

Expected

```text
syntax is ok

test is successful
```

---

## Step 6 — Reload Nginx

```bash
sudo systemctl reload nginx
```

---

# Best Practices

- Always verify directive names before deployment.
- Use the official Nginx documentation when adding new features.
- Check installed modules using `nginx -V`.
- Keep production servers updated.
- Avoid copying configuration blindly from the internet.

---

# Real Production Scenario

## Problem

A developer copied a configuration enabling Brotli compression.

After deployment:

```text
unknown directive "brotli"
```

The production server used the standard Nginx package without the Brotli module.

---

## Investigation

Running

```bash
nginx -V
```

confirmed that the Brotli module was not compiled into the installed binary.

---

## Resolution

The unsupported directives were removed until the required module was installed.

Configuration validation succeeded.

```bash
sudo nginx -t
```

The service reloaded successfully.

---

# Verification Checklist

After fixing the issue:

- ✅ Configuration validates successfully
- ✅ No unknown directives remain
- ✅ Required modules are installed
- ✅ Nginx starts successfully
- ✅ Website responds normally

---

# Common Mistakes

❌ Misspelling directive names

❌ Assuming every Nginx installation includes every module

❌ Copying configuration from newer Nginx versions

❌ Ignoring module dependencies

❌ Forgetting to run `nginx -t`

---

# Prevention Tips

- Use syntax highlighting in your editor.
- Check the official documentation before using new directives.
- Standardize Nginx versions across environments.
- Validate configuration in CI/CD pipelines.
- Review configuration changes before deployment.

---

# Production Notes

Different Linux distributions often ship different Nginx builds.

For example:

- Ubuntu package
- Debian package
- Alpine package
- Official Docker image
- Nginx Plus

Each build may include a different set of modules.

Always verify module availability before deploying new configuration features.

---

