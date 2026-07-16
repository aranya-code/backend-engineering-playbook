# Overview

Configuration syntax errors are one of the most common reasons why Nginx fails to start or reload.

Even a single missing semicolon, unmatched brace, or misspelled directive can prevent Nginx from loading the configuration.

The good news is that Nginx includes a built-in configuration validator that pinpoints most syntax errors before the service is restarted.

---

# Symptoms

## While Testing Configuration

```bash
sudo nginx -t
```

Output:

```text
nginx: [emerg] unexpected "}"
nginx: configuration file /etc/nginx/nginx.conf test failed
```

---

## During Reload

```bash
sudo systemctl reload nginx
```

Output:

```text
Job for nginx.service failed.
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

# Quick Diagnosis

Always begin with these commands.

## Validate Configuration

```bash
sudo nginx -t
```

---

## Show Complete Configuration

```bash
sudo nginx -T
```

This prints the complete configuration after processing all `include` statements.

---

## View Error Logs

```bash
sudo tail -50 /var/log/nginx/error.log
```

---

## Open the Reported File

```bash
vim /etc/nginx/nginx.conf
```

or

```bash
nano /etc/nginx/nginx.conf
```

---

# Decision Tree

```text
               nginx -t
                    │
                    ▼
        Configuration Test Failed
                    │
        ┌───────────┴────────────┐
        │                        │
  Line Number Reported      No Line Number
        │                        │
 Open Configuration         Check Included Files
        │                        │
        ▼                        ▼
 Fix Syntax Error         Run nginx -T
        │
        ▼
 Run nginx -t Again
        │
        ▼
 Configuration OK
```

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Missing semicolon | Directive not terminated with `;` |
| Unmatched braces | Missing `{` or `}` |
| Misspelled directive | Invalid directive name |
| Directive in wrong context | Directive placed inside an incorrect block |
| Missing include file | Referenced configuration file does not exist |
| Invalid parameter | Wrong number or type of parameters |

---

# Error Message Decoder

## Missing Semicolon

```text
unexpected "}"
```

### Incorrect

```nginx
worker_processes auto
```

### Correct

```nginx
worker_processes auto;
```

---

## Missing Closing Brace

```text
unexpected end of file
```

### Incorrect

```nginx
server {

    listen 80;

    location / {

        root /var/www/html;
```

### Correct

```nginx
server {

    listen 80;

    location / {

        root /var/www/html;

    }

}
```

---

## Unknown Directive

```text
unknown directive
```

Example

```text
unknown directive "proxy_pas"
```

### Incorrect

```nginx
proxy_pas http://backend;
```

### Correct

```nginx
proxy_pass http://backend;
```

---

## Directive Not Allowed Here

```text
"location" directive is not allowed here
```

### Incorrect

```nginx
http {

}

location / {

}
```

### Correct

```nginx
http {

    server {

        location / {

        }

    }

}
```

---

# Step-by-Step Troubleshooting

## Step 1 — Test Configuration

```bash
sudo nginx -t
```

Always read:

- filename
- line number
- exact error message

---

## Step 2 — Open the Reported File

Example:

```text
/etc/nginx/sites-enabled/default:42
```

Open the file.

```bash
nano /etc/nginx/sites-enabled/default
```

Go directly to the reported line.

---

## Step 3 — Check for Common Mistakes

Look for:

- Missing `;`
- Missing `{`
- Missing `}`
- Incorrect indentation
- Misspelled directive
- Invalid parameters

---

## Step 4 — Validate Again

```bash
sudo nginx -t
```

Do not restart Nginx until the configuration test succeeds.

---

## Step 5 — Reload Configuration

```bash
sudo systemctl reload nginx
```

or

```bash
sudo nginx -s reload
```

---

# Best Practices

Use indentation consistently.

Example

```nginx
server {

    listen 80;

    location / {

        proxy_pass http://backend;

    }

}
```

Consistent formatting makes syntax errors easier to spot.

---

# Real Production Scenario

## Problem

A deployment pipeline updated the Nginx configuration automatically.

After deployment:

```text
Website unavailable
```

---

## Investigation

Configuration validation:

```bash
sudo nginx -t
```

Output:

```text
unexpected "}"
```

The generated configuration contained an extra closing brace after a `location` block.

---

## Resolution

The extra brace was removed.

Configuration tested successfully.

```bash
sudo nginx -t
```

Nginx reloaded without downtime.

---

# Verification Checklist

After fixing the configuration:

- ✅ `nginx -t` returns **syntax is ok**
- ✅ Configuration test is successful
- ✅ Service reloads successfully
- ✅ Website responds correctly
- ✅ Error log contains no syntax errors

---

# Common Mistakes

❌ Forgetting semicolons

❌ Incorrect nesting of blocks

❌ Copy-pasting configuration from different Nginx versions

❌ Editing production configuration without testing

❌ Ignoring the reported line number

❌ Restarting Nginx before validating the configuration

---

# Prevention Tips

- Always run `nginx -t` before reloading.
- Use proper indentation.
- Keep configuration files under version control.
- Make small changes and test incrementally.
- Use `nginx -T` to inspect the final merged configuration.

---

