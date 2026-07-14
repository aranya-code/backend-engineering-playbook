# Overview

One of the most useful features of Nginx is **directive inheritance**.

Inheritance allows child contexts to automatically use directives defined in their parent contexts.

Instead of repeating the same configuration in every `server` or `location` block, you can define it once in a higher-level context.

This makes configurations:

- Cleaner
- Easier to maintain
- Less error-prone
- More consistent

However, not every directive is inherited in the same way.

Understanding inheritance is essential when troubleshooting unexpected Nginx behavior.

---

# What is Directive Inheritance?

Inheritance means that a child context automatically receives configuration from its parent context unless it explicitly overrides it.

Consider the following hierarchy:

```text
Main
│
└── http
      │
      └── server
              │
              └── location
```

Settings defined in the `http` context can often be used by every `server` and `location` inside it.

---

# Example of Inheritance

```nginx
http {

    gzip on;

    server {

        location / {

        }

    }

}
```

Although `gzip` is defined only once, it is available inside the server and location blocks.

```text
http
│
├── gzip on
│
└── server
      │
      └── location
```

The child contexts inherit the `gzip` directive.

---

# Why Inheritance Matters

Imagine hosting 20 different websites.

Without inheritance:

```nginx
server {

    gzip on;

}

server {

    gzip on;

}

server {

    gzip on;

}
```

The same directive must be repeated in every server block.

With inheritance:

```nginx
http {

    gzip on;

    server {

    }

    server {

    }

    server {

    }

}
```

The configuration becomes much simpler.

---

# Inheritance Flow

```text
Main
│
│
▼
http
│
│
▼
server
│
│
▼
location
```

Directives generally flow **from parent to child**.

---

# Overriding Inherited Directives

A child context can replace an inherited value by defining the same directive again.

Example:

```nginx
http {

    client_max_body_size 50M;

    server {

        client_max_body_size 10M;

    }

}
```

Result:

| Context | Maximum Upload Size |
|----------|--------------------:|
| http | 50 MB |
| server | 10 MB |

The server block overrides the inherited value.

---

# Another Example

```nginx
http {

    root /var/www;

    server {

        root /home/project;

    }

}
```

Requests handled by this server will use:

```
/home/project
```

instead of:

```
/var/www
```

---

# Inheritance Across Multiple Levels

Configuration:

```nginx
http {

    client_max_body_size 20M;

    server {

        location / {

        }

    }

}
```

Hierarchy:

```text
http
│
├── client_max_body_size 20M
│
└── server
      │
      └── location
```

The `location` block automatically receives the inherited value because neither the `server` nor the `location` block overrides it.

---

# Multiple Levels of Override

```nginx
http {

    client_max_body_size 50M;

    server {

        client_max_body_size 20M;

        location /upload {

            client_max_body_size 5M;

        }

    }

}
```

Effective values:

| Context | Upload Limit |
|----------|-------------:|
| http | 50 MB |
| server | 20 MB |
| location | 5 MB |

The most specific configuration takes precedence.

---

# Directives That Commonly Inherit

Many directives naturally inherit values.

Examples include:

- `root`
- `index`
- `client_max_body_size`
- `access_log`
- `error_log`
- `gzip`
- `charset`

These directives can usually be defined once and reused by child contexts.

---

# Directives That Do Not Always Inherit

Not every directive follows inheritance.

Some directives replace inherited values instead of extending them.

Others are valid only inside specific contexts.

For example:

```nginx
listen 80;
```

can only appear inside a `server` block.

Similarly,

```nginx
worker_connections
```

can only appear inside the `events` context.

Attempting to inherit these directives is not possible because they are not valid in child contexts.

Always refer to the official documentation when unsure about a directive's inheritance behavior.

---

# Real-World Example

Suppose a company hosts three applications.

```text
Main
│
└── http
      │
      ├── gzip on
      ├── access_log logs/access.log
      │
      ├── server (Website)
      │
      ├── server (API)
      │
      └── server (Admin)
```

Since `gzip` and `access_log` are defined in the `http` context, every application automatically uses the same configuration.

Only application-specific settings need to be defined inside individual server blocks.

---

# Best Practices

- Define common settings in the highest appropriate context.
- Override directives only when necessary.
- Avoid duplicating configuration across multiple server blocks.
- Keep global configuration centralized.
- Understand whether a directive is inherited before relying on default behavior.

---

# Common Mistakes

## Repeating the Same Directive Everywhere

Instead of:

```nginx
server {

    gzip on;

}

server {

    gzip on;

}
```

Prefer:

```nginx
http {

    gzip on;

}
```

---

## Assuming Every Directive is Inherited

Not all directives inherit values.

Some directives are context-specific.

Others completely replace inherited values.

---

## Overriding Values Unintentionally

Example:

```nginx
http {

    root /var/www;

    server {

        root /tmp;

    }

}
```

Developers sometimes expect both paths to be used.

In reality, the server block replaces the inherited value.

---

# Interview Notes

### Beginner Questions

- What is directive inheritance?
- Why is inheritance useful?
- Can child contexts override inherited values?
- What happens if the same directive is defined in both parent and child contexts?

---

### Intermediate Questions

- Explain how inheritance works in Nginx.
- Are all directives inherited?
- How does Nginx resolve conflicting directive values?
- Why should common directives be placed in the `http` context?

---

# Key Takeaways

- Directive inheritance allows child contexts to reuse configuration from parent contexts.
- Child contexts can override inherited values by defining the same directive again.
- Inheritance reduces configuration duplication and improves maintainability.
- Not every directive is inherited, and some directives are valid only within specific contexts.
- Understanding inheritance is essential for writing clean, scalable, and production-ready Nginx configurations.