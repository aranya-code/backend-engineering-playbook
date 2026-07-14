# Overview

Nginx configuration is organized into **contexts**.

A **context** is simply a block enclosed within curly braces `{}` that groups related directives together.

Every directive in Nginx belongs to a specific context, and where you place a directive determines **its scope** and **which components it affects**.

For example:

```nginx
http {

    server {

        location / {

        }

    }

}
```

Here:

- `http` is a context.
- `server` is a context.
- `location` is a context.

Each context has a different responsibility.

Understanding contexts is one of the most important skills when working with Nginx.

---

# Why Contexts Exist

Imagine configuring an entire web server using a single file without any organization.

Questions such as:

- Which settings apply to the entire server?
- Which settings apply to only one website?
- Which settings apply to a specific URL?

would become difficult to answer.

Contexts solve this problem by organizing configuration into logical sections.

---

# Nginx Configuration Hierarchy

The configuration file follows a hierarchical structure.

```text
Main Context
│
├── events
│
└── http
     │
     ├── server
     │      │
     │      ├── location
     │      ├── location
     │      └── location
     │
     └── server
            │
            ├── location
            └── location
```

Each level has its own purpose.

---

# Main Context

The **Main Context** is the top-most configuration level.

Everything outside curly braces belongs to the Main Context.

Example:

```nginx
worker_processes auto;

error_log logs/error.log;

events {

}

http {

}
```

The Main Context usually contains global server configuration.

Common directives include:

- `worker_processes`
- `pid`
- `error_log`
- `include`
- `daemon`
- `user`

These settings affect the entire Nginx server.

---

# Events Context

The `events` context controls how Nginx handles client connections.

Example:

```nginx
events {

    worker_connections 1024;

}
```

Typical directives:

- `worker_connections`
- `multi_accept`
- `use`

Example:

```nginx
events {

    worker_connections 4096;

    multi_accept on;

}
```

This context is focused on connection handling and performance.

---

# HTTP Context

The `http` context contains all HTTP-related configuration.

Every website hosted by Nginx is usually defined inside this context.

Example:

```nginx
http {

    include mime.types;

    default_type application/octet-stream;

}
```

Typical directives:

- `include`
- `sendfile`
- `gzip`
- `access_log`
- `log_format`
- `upstream`
- `server`

This is one of the largest contexts in Nginx.

---

# Server Context

A `server` block represents a **virtual server**.

Each server block can represent:

- A website
- A REST API
- A microservice
- A reverse proxy

Example:

```nginx
server {

    listen 80;

    server_name example.com;

}
```

A single Nginx installation can contain multiple server blocks.

Example:

```nginx
http {

    server {

        server_name api.example.com;

    }

    server {

        server_name blog.example.com;

    }

}
```

Each server can have completely different behavior.

---

# Location Context

The `location` context defines how Nginx should process requests for a particular URL.

Example:

```nginx
location / {

    root html;

}
```

Another example:

```nginx
location /api {

    proxy_pass http://backend;

}
```

Another example:

```nginx
location /images {

    root /var/www;

}
```

Different URLs can perform completely different actions.

---

# Relationship Between Contexts

Each context is nested inside another.

```text
Main
│
└── http
      │
      └── server
              │
              └── location
```

This hierarchy is important because child contexts inherit many settings from their parent.

This concept is called **inheritance**, which will be discussed in detail in a later chapter.

---

# Configuration Flow

When Nginx starts:

1. It reads the Main Context.
2. It initializes the Events Context.
3. It loads the HTTP Context.
4. It loads every Server Context.
5. It prepares every Location Context.

Only after completing these steps does Nginx begin accepting client requests.

---

# Example Configuration

```nginx
worker_processes auto;

events {

    worker_connections 1024;

}

http {

    sendfile on;

    server {

        listen 80;

        server_name localhost;

        location / {

            root html;

            index index.html;

        }

    }

}
```

Let's identify each context.

```text
Main Context
│
├── worker_processes
│
├── events
│      └── worker_connections
│
└── http
       │
       ├── sendfile
       │
       └── server
               │
               ├── listen
               ├── server_name
               │
               └── location
                       ├── root
                       └── index
```

Understanding this hierarchy makes reading large configuration files much easier.

---

# Context Responsibilities

| Context | Responsibility |
|----------|----------------|
| Main | Global Nginx configuration |
| events | Connection handling |
| http | HTTP server configuration |
| server | Individual website or virtual host |
| location | URL-specific request handling |

---

# Real-World Example

Suppose you host two applications:

- Company Website
- REST API

Configuration:

```text
Main
│
└── http
      │
      ├── server (company.com)
      │      ├── /
      │      └── /images
      │
      └── server (api.company.com)
             ├── /
             └── /v1
```

Both applications run on the same Nginx instance but have completely different routing rules.

---

# Best Practices

- Keep global settings in the Main Context.
- Configure connection-related directives only inside the `events` context.
- Place HTTP-specific directives inside the `http` context.
- Use separate `server` blocks for different domains or applications.
- Keep `location` blocks focused on specific URL patterns.
- Maintain proper indentation to improve readability.

---

# Common Mistakes

### Placing Directives in the Wrong Context

Example:

```nginx
events {

    listen 80;

}
```

This is invalid because `listen` belongs inside a `server` block.

---

### Mixing Global and Server Configuration

Avoid placing server-specific settings in the Main Context.

Incorrect:

```nginx
server_name example.com;
```

Correct:

```nginx
server {

    server_name example.com;

}
```

---

### Overusing Location Blocks

Creating too many overlapping location blocks makes configurations difficult to maintain.

Group similar routes whenever possible.

---

# Interview Notes

### Beginner Questions

- What is a context in Nginx?
- Name the five major contexts.
- Which context defines virtual hosts?
- Which context handles client connections?

---

### Intermediate Questions

- Explain the hierarchy of Nginx contexts.
- What is the difference between the `http` and `server` contexts?
- Why does Nginx use nested configuration blocks?
- What happens if a directive is placed in the wrong context?

---

# Key Takeaways

- A **context** is a configuration block enclosed by `{}`.
- Nginx configuration follows a hierarchical structure.
- The five primary contexts are:
  - Main
  - events
  - http
  - server
  - location
- Each context has a specific responsibility.
- Understanding contexts is essential before learning directives, inheritance, reverse proxying, and request processing.