# Overview

The **worker_processes** directive controls how many worker processes Nginx creates to handle incoming client requests.

One of the most common mistakes beginners make is placing this directive inside the wrong configuration context.

Since **worker_processes** is a **Main Context** directive, placing it inside an `http`, `server`, or `location` block causes Nginx to fail during configuration validation.

---

# Symptoms

## Configuration Test

```bash
sudo nginx -t
```

Output:

```text
nginx: [emerg] "worker_processes" directive is not allowed here
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

## Reload Failure

```bash
sudo systemctl reload nginx
```

Output

```text
Job for nginx.service failed.
```

---

# Quick Diagnosis

Run the following commands.

## Validate Configuration

```bash
sudo nginx -t
```

---

## Show Complete Configuration

```bash
sudo nginx -T
```

---

## Search for worker_processes

```bash
grep -rn "worker_processes" /etc/nginx/
```

---

## Open nginx.conf

```bash
sudo nano /etc/nginx/nginx.conf
```

---

# Decision Tree

```text
                 nginx -t
                      │
                      ▼
      "worker_processes" not allowed here
                      │
                      ▼
        Search Configuration File
                      │
                      ▼
     Inside http/server/location?
             │               │
            Yes              No
             │               │
             ▼               ▼
 Move to Main Context   Check for Duplicate
             │
             ▼
        Validate Again
             │
             ▼
       Configuration OK
```

---

# Why This Happens

Nginx configuration is divided into **contexts**.

Each directive is only valid in specific contexts.

The **worker_processes** directive belongs only to the **Main Context**.

Correct hierarchy:

```text
Main Context

│

├── events

├── http

│     ├── server

│     │      └── location

│     └── upstream
```

Since `worker_processes` configures the entire Nginx instance, it cannot be placed inside child contexts.

---

# Incorrect Configuration

```nginx
http {

    worker_processes auto;

}
```

Result

```text
worker_processes directive is not allowed here
```

---

# Correct Configuration

```nginx
worker_processes auto;

events {

    worker_connections 1024;

}

http {

    include mime.types;

}
```

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Wrong context | Directive placed inside `http` block |
| Copy-paste error | Configuration copied from another file |
| Included file | Directive exists inside a file included under `http` |
| Duplicate configuration | `worker_processes` defined multiple times |

---

# Error Message Decoder

## Directive Not Allowed Here

```text
worker_processes directive is not allowed here
```

### Meaning

The directive exists in an invalid configuration context.

### Solution

Move it to the top of `nginx.conf`.

---

## Duplicate Directive

```text
worker_processes directive is duplicate
```

### Meaning

The directive has been defined more than once.

### Solution

Keep only one definition.

---

# Step-by-Step Troubleshooting

## Step 1 — Validate Configuration

```bash
sudo nginx -t
```

Read the complete error message.

---

## Step 2 — Locate the Directive

```bash
grep -rn "worker_processes" /etc/nginx/
```

Example

```text
/etc/nginx/nginx.conf:2

/etc/nginx/conf.d/custom.conf:8
```

If multiple files contain the directive, remove the duplicate.

---

## Step 3 — Verify Context

Correct

```nginx
worker_processes auto;

events {

}
```

Incorrect

```nginx
http {

    worker_processes auto;

}
```

---

## Step 4 — Test Again

```bash
sudo nginx -t
```

Expected

```text
syntax is ok

test is successful
```

---

## Step 5 — Reload Nginx

```bash
sudo systemctl reload nginx
```

---

# Best Practices

Use only one `worker_processes` directive.

For most production servers:

```nginx
worker_processes auto;
```

This automatically matches the number of available CPU cores.

Avoid hardcoding values unless performance tuning requires it.

---

# Real Production Scenario

## Problem

An engineer moved several directives into a separate configuration file.

The new file was included inside the `http` block.

It contained:

```nginx
worker_processes auto;
```

After deployment:

```text
nginx failed to start
```

---

## Investigation

Configuration validation showed:

```text
worker_processes directive is not allowed here
```

---

## Resolution

The directive was removed from the included file and placed back into the Main Context of `nginx.conf`.

Configuration validation succeeded and the service started normally.

---

# Verification Checklist

After fixing the issue:

- ✅ `worker_processes` exists only once
- ✅ It is placed in the Main Context
- ✅ `nginx -t` succeeds
- ✅ Nginx starts successfully
- ✅ Worker processes are running

Verify running workers:

```bash
ps -ef | grep nginx
```

Expected

```text
root      nginx: master process

www-data  nginx: worker process

www-data  nginx: worker process
```

---

# Common Mistakes

❌ Defining `worker_processes` inside the `http` block

❌ Copying directives from tutorials without checking their valid context

❌ Defining the directive multiple times

❌ Forgetting to validate the configuration after editing

---

# Prevention Tips

- Learn which directives belong to each configuration context.
- Keep global directives at the top of `nginx.conf`.
- Run `nginx -t` after every configuration change.
- Use `grep` to detect duplicate directives before deployment.
- Follow consistent configuration organization across environments.

---

