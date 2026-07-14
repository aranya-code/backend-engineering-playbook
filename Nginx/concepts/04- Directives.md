# Overview

A **directive** is an individual instruction inside the Nginx configuration file.

Directives tell Nginx **what to do**.

Almost every line in an Nginx configuration file is a directive.

For example:

```nginx
listen 80;

server_name localhost;

root /usr/share/nginx/html;
```

Each of the above lines is a directive.

Think of contexts as **containers**, while directives are the **instructions** placed inside those containers.

---

# Directive Syntax

The basic syntax is:

```nginx
directive_name value;
```

Example:

```nginx
worker_processes auto;
```

Here,

- **Directive Name:** `worker_processes`
- **Value:** `auto`

Every directive ends with a **semicolon (`;`)**.

---

# Directives Inside Contexts

Directives must be placed inside the correct context.

Example:

```nginx
http {

    sendfile on;

    server {

        listen 80;

        server_name localhost;

    }

}
```

In this example:

- `sendfile` belongs to the `http` context.
- `listen` belongs to the `server` context.
- `server_name` belongs to the `server` context.

If a directive is placed in the wrong context, Nginx will fail to start.

---

# Types of Directives

Nginx directives can be divided into two categories.

## 1. Simple Directives

Simple directives contain a name followed by one or more values.

Example:

```nginx
worker_processes auto;

sendfile on;

keepalive_timeout 65;

client_max_body_size 50M;
```

These are the most commonly used directives.

---

## 2. Block Directives

Block directives contain other directives inside curly braces.

Example:

```nginx
http {

}
```

Another example:

```nginx
server {

}
```

Another example:

```nginx
location / {

}
```

Block directives create new configuration contexts.

---

# Common Directives

## worker_processes

Specifies the number of Worker Processes.

```nginx
worker_processes auto;
```

Production recommendation:

```nginx
worker_processes auto;
```

---

## worker_connections

Specifies the maximum number of simultaneous connections handled by each worker.

```nginx
events {

    worker_connections 1024;

}
```

---

## listen

Defines the port on which Nginx listens.

Example:

```nginx
listen 80;
```

HTTPS:

```nginx
listen 443 ssl;
```

Multiple ports:

```nginx
listen 8080;
```

---

## server_name

Defines the domain name handled by the server.

```nginx
server_name example.com;
```

Multiple domains:

```nginx
server_name example.com www.example.com;
```

Wildcard:

```nginx
server_name *.example.com;
```

---

## root

Specifies the root directory for serving files.

```nginx
root /var/www/html;
```

Example:

```text
Request

http://example.com/index.html

↓

Nginx

↓

/var/www/html/index.html
```

---

## index

Defines the default file returned when a directory is requested.

```nginx
index index.html;
```

Multiple files:

```nginx
index index.html index.htm default.html;
```

---

## error_page

Defines custom error pages.

Example:

```nginx
error_page 404 /404.html;
```

Example:

```text
Client

↓

404

↓

/404.html
```

---

## access_log

Stores information about successful requests.

```nginx
access_log logs/access.log;
```

Typical information:

- Client IP
- URL
- Status Code
- Request Time
- User Agent

---

## error_log

Stores server errors.

```nginx
error_log logs/error.log;
```

Common log levels:

- debug
- info
- notice
- warn
- error
- crit
- alert
- emerg

---

## include

Imports another configuration file.

```nginx
include mime.types;
```

Another example:

```nginx
include conf.d/*.conf;
```

This keeps configurations modular.

---

## gzip

Enables HTTP response compression.

```nginx
gzip on;
```

Benefits:

- Smaller response size
- Faster page loading
- Reduced bandwidth usage

---

## sendfile

Enables efficient file transfers.

```nginx
sendfile on;
```

When enabled, Nginx transfers files directly from disk to the network socket without unnecessary copying between kernel and user space, improving performance.

---

## client_max_body_size

Limits the maximum request body size.

Example:

```nginx
client_max_body_size 20M;
```

Useful for:

- File uploads
- Preventing oversized requests
- Improving security

---

# How Directives Work Together

Consider the following configuration:

```nginx
server {

    listen 80;

    server_name localhost;

    root html;

    index index.html;

}
```

When a client requests:

```
http://localhost/
```

Nginx processes the directives in combination:

1. `listen` accepts the connection on port **80**.
2. `server_name` selects the appropriate virtual server.
3. `root` identifies the document root.
4. `index` serves the default file.

Final file served:

```
html/index.html
```

---

# Directive Scope

Some directives affect the entire server.

Others affect only a single website.

Example:

```nginx
http {

    gzip on;

    server {

        server_name api.example.com;

    }

}
```

Here:

- `gzip` applies to every server inside the `http` context.
- `server_name` applies only to its own server block.

This behavior is known as **inheritance**, which will be covered in a dedicated chapter.

---

# Real-World Example

A typical server block:

```nginx
server {

    listen 80;

    server_name api.company.com;

    root /var/www/api;

    index index.html;

    access_log logs/api_access.log;

    error_log logs/api_error.log;

}
```

This configuration tells Nginx:

- Listen on port **80**
- Respond to **api.company.com**
- Serve files from **/var/www/api**
- Use **index.html** as the default document
- Record successful requests in **api_access.log**
- Record errors in **api_error.log**

---

# Best Practices

- Keep directives inside their correct contexts.
- Use meaningful file paths.
- Separate reusable configuration using `include`.
- Prefer `worker_processes auto` for production.
- Enable `sendfile` for static file serving.
- Limit upload sizes using `client_max_body_size`.
- Always validate configuration changes before reloading:

```bash
nginx -t
```

---

# Common Mistakes

## Forgetting the Semicolon

Incorrect:

```nginx
listen 80
```

Correct:

```nginx
listen 80;
```

---

## Placing Directives in the Wrong Context

Incorrect:

```nginx
events {

    server_name localhost;

}
```

`server_name` is valid only inside a `server` block.

---

## Assuming Every Directive Is Global

Not every directive affects the entire configuration.

Many directives apply only within the context where they are defined.

Understanding directive scope is essential for troubleshooting configuration issues.

---

# Interview Notes

### Beginner Questions

- What is a directive in Nginx?
- What is the difference between a directive and a context?
- Name some commonly used directives.
- What does the `listen` directive do?
- What is the purpose of `server_name`?

---

### Intermediate Questions

- Explain the difference between simple and block directives.
- What happens if a directive is placed in the wrong context?
- How do directives inherit values from parent contexts?
- Why is `include` useful in production environments?
- Explain how `root` and `index` work together.

---

# Key Takeaways

- A **directive** is an instruction that tells Nginx how to behave.
- Directives must be placed inside the appropriate context.
- Simple directives end with a semicolon.
- Block directives create new contexts.
- Common directives include:
  - `listen`
  - `server_name`
  - `root`
  - `index`
  - `access_log`
  - `error_log`
  - `gzip`
  - `sendfile`
  - `include`
- Understanding directives is essential before learning request processing, reverse proxying, SSL configuration, and load balancing.