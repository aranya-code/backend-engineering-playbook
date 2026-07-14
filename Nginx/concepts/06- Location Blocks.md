# Overview

The **location** block is one of the most important components of Nginx configuration.

After selecting the appropriate **server block**, Nginx uses **location blocks** to determine **how a specific request should be handled**.

Depending on the URL, Nginx can:

- Serve static files
- Forward requests to a backend application
- Redirect the client
- Deny access
- Return custom responses
- Apply caching rules
- Configure different headers

Almost every production Nginx configuration relies heavily on location blocks.

---

# Basic Syntax

```nginx
server {

    location / {

    }

}
```

General syntax:

```nginx
location [modifier] URI {

    directives...

}
```

The modifier is optional.

---

# How Location Matching Works

Once Nginx selects the appropriate **server block**, it begins searching for the best matching location.

Example request:

```
GET /images/logo.png
```

Configuration:

```nginx
server {

    location / {

    }

    location /images {

    }

}
```

Nginx compares the request URI against every location block and chooses the best match.

---

# Location Matching Flow

```text
Incoming Request
        │
        ▼
Select Server Block
        │
        ▼
Evaluate Location Blocks
        │
        ▼
Best Match Found
        │
        ▼
Execute Directives
```

---

# Prefix Match

The simplest location block is a **prefix match**.

```nginx
location /images {

}
```

This matches:

```
/images
/images/
/images/logo.png
/images/icons/icon.png
```

It does **not** require an exact match.

---

# Root Location

The root location is:

```nginx
location / {

}
```

It matches **every request**.

Examples:

```
/

```

```
/about
```

```
/products
```

```
/api/users
```

Because every URI starts with `/`, this location acts as the default handler.

---

# Exact Match (`=`)

The `=` modifier tells Nginx to match the URI exactly.

Example:

```nginx
location = /login {

}
```

Matches:

```
/login
```

Does **not** match:

```
/login/
```

```
/login/user
```

Exact matching is useful for:

- Login pages
- Health check endpoints
- Robots.txt
- Favicon

---

# Prefix Match (`^~`)

The `^~` modifier tells Nginx:

> "If this prefix matches, stop searching and use this location."

Example:

```nginx
location ^~ /images {

}
```

Request:

```
/images/logo.png
```

Nginx immediately selects this location without checking regular expressions.

This improves performance when a specific prefix should always win.

---

# Regular Expression Match (`~`)

The `~` modifier performs a **case-sensitive regular expression match**.

Example:

```nginx
location ~ \.php$ {

}
```

Matches:

```
index.php
```

```
login.php
```

Does not match:

```
INDEX.PHP
```

---

# Case-Insensitive Regular Expression (`~*`)

The `~*` modifier performs a **case-insensitive regular expression match**.

Example:

```nginx
location ~* \.(jpg|png|gif)$ {

}
```

Matches:

```
logo.PNG
```

```
banner.jpg
```

```
ICON.GIF
```

Useful for serving static assets.

---

# Common Location Modifiers

| Modifier | Meaning |
|-----------|---------|
| *(none)* | Prefix Match |
| `=` | Exact Match |
| `^~` | Priority Prefix Match |
| `~` | Case-Sensitive Regular Expression |
| `~*` | Case-Insensitive Regular Expression |

---

# Location Matching Priority

Nginx follows a specific order when evaluating locations.

1. Exact Match (`=`)
2. Priority Prefix (`^~`)
3. Regular Expressions (`~` and `~*`)
4. Longest Prefix Match (`/`, `/images`, etc.)

Understanding this priority is essential when multiple location blocks could match the same request.

---

# Example Configuration

```nginx
server {

    location = /login {

    }

    location ^~ /images {

    }

    location ~ \.php$ {

    }

    location / {

    }

}
```

Request:

```
/login
```

Selected Location:

```nginx
location = /login
```

---

Request:

```
/images/logo.png
```

Selected Location:

```nginx
location ^~ /images
```

---

Request:

```
index.php
```

Selected Location:

```nginx
location ~ \.php$
```

---

Request:

```
/contact
```

Selected Location:

```nginx
location /
```

---

# Serving Static Files

One of the most common uses of location blocks is serving static content.

Example:

```nginx
location /images {

    root /var/www;

}
```

Request:

```
/images/logo.png
```

Nginx searches for:

```
/var/www/images/logo.png
```

If the file exists, it is returned immediately.

---

# Reverse Proxy Example

Location blocks are commonly used to forward requests to backend applications.

```nginx
location /api {

    proxy_pass http://backend;

}
```

Flow:

```text
Browser
   │
   ▼
Nginx
   │
   ▼
FastAPI
```

Every request beginning with `/api` is forwarded to the backend server.

---

# Multiple Location Blocks

A single server can contain multiple location blocks.

```nginx
server {

    location / {

    }

    location /images {

    }

    location /css {

    }

    location /js {

    }

    location /api {

    }

}
```

Each location can have completely different behavior.

---

# Real-World Example

A production website might use:

```nginx
server {

    location / {

        root /var/www/frontend;

    }

    location /api {

        proxy_pass http://backend;

    }

    location /images {

        root /var/www;

    }

    location ~* \.(jpg|png|css|js)$ {

        expires 30d;

    }

}
```

Request:

```
/
```

Serves the frontend.

---

Request:

```
/api/products
```

Forwards to the backend.

---

Request:

```
/images/logo.png
```

Serves a static image.

---

Request:

```
style.css
```

Applies browser caching.

---

# Best Practices

- Keep location rules simple.
- Use exact matching for unique endpoints.
- Use prefix matching for directories.
- Use regular expressions only when necessary.
- Group related routes together.
- Place static assets in dedicated location blocks.
- Avoid overlapping or conflicting location rules.

---

# Common Mistakes

## Assuming Order Determines Matching

Unlike many programming languages, Nginx does **not** simply execute the first matching location block.

It follows its own location matching algorithm.

Understanding modifier priority is more important than the order in which location blocks appear.

---

## Using Regular Expressions Unnecessarily

Regular expressions are more expensive than prefix matching.

Prefer prefix matches whenever possible.

---

## Overlapping Location Blocks

Example:

```nginx
location /api {

}
```

```nginx
location /api/v1 {

}
```

Ensure you understand which block will be selected for each request.

---

# Interview Notes

### Beginner Questions

- What is a location block?
- When does Nginx evaluate location blocks?
- What is the purpose of `location /`?
- What is the difference between `root` and `location`?

---

### Intermediate Questions

- Explain the location matching algorithm.
- What is the difference between `=`, `^~`, `~`, and `~*`?
- Why should regular expressions be used carefully?
- How does Nginx decide which location block to execute?

---

# Key Takeaways

- Location blocks determine how requests are processed after a server block is selected.
- Different modifiers provide different matching behaviors.
- The five most common matching types are:
  - Prefix Match
  - Exact Match (`=`)
  - Priority Prefix (`^~`)
  - Case-Sensitive Regex (`~`)
  - Case-Insensitive Regex (`~*`)
- Location blocks are commonly used for:
  - Static files
  - Reverse proxy
  - Caching
  - Security rules
  - URL routing
- Understanding location matching is essential for building production-ready Nginx configurations.