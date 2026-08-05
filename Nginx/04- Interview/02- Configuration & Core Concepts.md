# Overview

Nginx is configured through a collection of directives organized into configuration blocks. Understanding how these directives and blocks work together is essential for building secure, scalable, and maintainable Nginx deployments.

This chapter covers the core configuration concepts that every backend engineer should know before working with reverse proxies, load balancing, SSL, caching, or production deployments.

---

# Understanding the Configuration File

The primary configuration file is:

```text
/etc/nginx/nginx.conf
```

On Windows:

```text
C:\nginx\conf\nginx.conf
```

This file acts as the entry point for all Nginx configuration.

Additional configuration files can be included using the `include` directive.

---

# Configuration Hierarchy

Nginx configurations are organized into a hierarchy of contexts.

```text
nginx.conf
│
├── Main Context
│
├── Events Context
│
├── HTTP Context
│   │
│   ├── Server Context
│   │     │
│   │     ├── Location Context
│   │     └── Location Context
│   │
│   └── Server Context
│
└── Stream Context (Optional)
```

Each context has a specific responsibility and supports a defined set of directives.

---

# Main Context

The **Main Context** is the top-level configuration.

It controls global settings that affect the entire Nginx instance.

Example:

```nginx
worker_processes auto;

pid /run/nginx.pid;

error_log /var/log/nginx/error.log;
```

Typical directives include:

- worker_processes
- error_log
- pid
- user
- include

---

# Events Context

The `events` block controls how Nginx handles client connections.

Example:

```nginx
events {

    worker_connections 1024;

}
```

Common directives include:

- worker_connections
- use
- multi_accept

This context focuses on connection handling rather than HTTP processing.

---

# HTTP Context

The `http` block contains configuration related to HTTP and HTTPS traffic.

Example:

```nginx
http {

    include mime.types;

    default_type application/octet-stream;

}
```

Inside this context you can configure:

- Logging
- Compression
- Caching
- Upstreams
- Server blocks
- Proxy settings
- MIME types

Most Nginx configurations are written inside the HTTP context.

---

# Server Context

A `server` block represents a virtual server.

Each server block usually corresponds to a domain, subdomain, or application.

Example:

```nginx
server {

    listen 80;

    server_name example.com;

}
```

A single Nginx instance can contain multiple server blocks.

Example:

```text
Nginx

├── example.com

├── api.example.com

└── admin.example.com
```

---

# Location Context

The `location` block defines how requests for specific URLs are handled.

Example:

```nginx
server {

    location / {

        root /var/www/html;

    }

}
```

A location block may:

- Serve static files
- Proxy requests
- Redirect users
- Rewrite URLs
- Return custom responses

Location matching is one of the most important concepts in Nginx.

---

# Directives

A directive is an instruction that tells Nginx how to behave.

Example:

```nginx
worker_processes auto;

listen 80;

server_name example.com;
```

Every directive has a specific purpose.

Examples include:

- listen
- root
- alias
- proxy_pass
- return
- rewrite
- index

---

# Configuration Blocks

A block groups related directives.

Example:

```nginx
server {

    listen 80;

    server_name example.com;

}
```

Blocks improve readability and organize configuration logically.

---

# Semicolons Matter

Every directive must end with a semicolon.

Correct:

```nginx
listen 80;

server_name example.com;
```

Incorrect:

```nginx
listen 80

server_name example.com
```

Missing semicolons will cause configuration validation to fail.

---

# Comments

Comments help document configuration files.

Single-line comments begin with `#`.

Example:

```nginx
# Redirect HTTP to HTTPS

return 301 https://$host$request_uri;
```

Using comments is considered a best practice for production configurations.

---

# Including Configuration Files

Large deployments usually split configurations into multiple files.

Example:

```nginx
http {

    include /etc/nginx/conf.d/*.conf;

}
```

Benefits include:

- Better organization
- Easier maintenance
- Simpler deployments
- Modular configuration

---

# Configuration Validation

Always validate configuration changes before reloading Nginx.

```bash
nginx -t
```

Example output:

```text
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

Testing configurations helps prevent production outages caused by syntax errors.

---

# Common Configuration Structure

A typical production configuration follows this layout.

```text
Main Context
      │
      ▼
Events Context
      │
      ▼
HTTP Context
      │
      ├──────────────┐
      ▼              ▼
 Server Block   Server Block
      │              │
      ▼              ▼
Location Block  Location Block
```

This hierarchy allows Nginx to apply settings at different levels.

---

# Real-World Example

Consider a company hosting multiple applications.

```text
Internet
     │
     ▼
   Nginx
     │
 ┌───┼──────────────┐
 ▼   ▼              ▼
Web API         Admin
```

Configuration:

```nginx
server {

    listen 80;

    server_name www.example.com;

}

server {

    listen 80;

    server_name api.example.com;

}

server {

    listen 80;

    server_name admin.example.com;

}
```

Each application is handled by its own server block while sharing the same Nginx instance.

---

# Best Practices

- Keep configurations modular using the `include` directive.
- Use meaningful comments for complex configurations.
- Organize related directives into appropriate contexts.
- Validate configuration changes using `nginx -t`.
- Keep server blocks focused on a single application or domain.
- Avoid duplicating configuration across multiple files.

---

# Key Takeaways

- Nginx configuration is organized into hierarchical contexts.
- The main configuration file is typically `nginx.conf`.
- Directives define individual configuration settings, while blocks group related directives.
- The `http`, `server`, and `location` contexts form the foundation of most Nginx deployments.
- Modular configurations improve maintainability and scalability.
- Always validate configuration changes before reloading Nginx.