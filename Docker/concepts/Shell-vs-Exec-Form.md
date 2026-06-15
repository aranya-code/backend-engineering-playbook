# Shell Form vs Exec Form

## Overview

Docker instructions such as `RUN`, `CMD`, and `ENTRYPOINT` can be written in two formats:

1. **Shell Form**
2. **Exec Form**

Understanding the difference is crucial because it affects:

- Signal handling
- Process management
- Environment variable expansion
- Container shutdown behavior
- Production reliability

---

# Shell Form

## Definition

In Shell Form, Docker executes the command through a shell.

Docker automatically wraps the command with:

```bash
/bin/sh -c
```

on Linux containers.

---

## Syntax

```dockerfile
CMD python app.py
```

Docker internally executes:

```bash
/bin/sh -c "python app.py"
```

---

## Example

### Dockerfile

```dockerfile
FROM python:3.12

COPY app.py .

CMD python app.py
```

### Runtime Execution

```bash
docker run myimage
```

Docker actually runs:

```bash
/bin/sh -c "python app.py"
```

---

## Process Tree

```text
PID 1
 │
 └── /bin/sh
      │
      └── python app.py
```

Notice that:

- Shell becomes PID 1.
- Application runs as a child process.

---

## Advantages

### Easier Command Writing

No JSON syntax required.

```dockerfile
CMD python app.py
```

instead of:

```dockerfile
CMD ["python", "app.py"]
```

---

### Supports Shell Features

You can use:

#### Pipes

```dockerfile
CMD cat file.txt | grep error
```

#### Redirection

```dockerfile
CMD python app.py > output.log
```

#### Command Chaining

```dockerfile
CMD echo "Starting" && python app.py
```

#### Environment Variable Expansion

```dockerfile
CMD echo $HOME
```

---

## Disadvantages

### Extra Shell Process

Docker starts:

```bash
/bin/sh
```

before launching your application.

This adds an extra layer.

---

### Signal Handling Problems

Since the shell is PID 1:

```text
PID 1 → /bin/sh
PID 2 → python
```

Signals may not be forwarded correctly.

Examples:

- SIGTERM
- SIGINT
- SIGKILL

This can cause:

- Slow shutdowns
- Stuck containers
- Zombie processes

---

# Exec Form

## Definition

Exec Form executes the command directly without invoking a shell.

The application becomes PID 1 inside the container.

---

## Syntax

```dockerfile
CMD ["python", "app.py"]
```

---

## Example

### Dockerfile

```dockerfile
FROM python:3.12

COPY app.py .

CMD ["python", "app.py"]
```

### Runtime Execution

```bash
docker run myimage
```

Docker directly starts:

```bash
python app.py
```

---

## Process Tree

```text
PID 1
 │
 └── python app.py
```

No shell exists between Docker and the application.

---

## Advantages

### Better Signal Handling

Application receives signals directly.

Example:

```bash
docker stop container
```

Docker sends:

```bash
SIGTERM
```

directly to:

```bash
python app.py
```

Result:

- Graceful shutdown
- Faster termination
- Better reliability

---

### Recommended for Production

Most production-grade images use:

```dockerfile
CMD ["python", "app.py"]
```

or

```dockerfile
ENTRYPOINT ["python"]
```

because they avoid PID 1 issues.

---

### No Extra Shell Process

Fewer processes:

```text
PID 1
 │
 └── Application
```

Result:

- Lower overhead
- Cleaner process tree
- Better container behavior

---

## Disadvantages

### No Shell Features

The following will NOT work:

```dockerfile
CMD ["cat", "file.txt", "|", "grep", "error"]
```

Docker treats every item as a literal argument.

---

### No Automatic Variable Expansion

This:

```dockerfile
CMD ["echo", "$HOME"]
```

outputs:

```text
$HOME
```

instead of the actual value.

---

# Side-by-Side Comparison

| Feature | Shell Form | Exec Form |
|----------|------------|------------|
| Syntax | `CMD python app.py` | `CMD ["python","app.py"]` |
| Uses Shell | Yes | No |
| Runs Through | `/bin/sh -c` | Direct Execution |
| PID 1 | Shell | Application |
| Signal Handling | Poor | Excellent |
| Supports Pipes | Yes | No |
| Supports Redirection | Yes | No |
| Supports Variable Expansion | Yes | No |
| Production Recommended | No | Yes |

---

# ENTRYPOINT Examples

## Shell Form

```dockerfile
ENTRYPOINT python app.py
```

Docker executes:

```bash
/bin/sh -c "python app.py"
```

Process tree:

```text
PID 1
 │
 └── /bin/sh
      │
      └── python
```

---

## Exec Form

```dockerfile
ENTRYPOINT ["python", "app.py"]
```

Process tree:

```text
PID 1
 │
 └── python
```

This is the preferred approach.

---

# Signal Handling Example

### Shell Form

```dockerfile
CMD python app.py
```

Container receives:

```bash
SIGTERM
```

Signal goes to:

```bash
/bin/sh
```

and may not reach:

```bash
python
```

properly.

---

### Exec Form

```dockerfile
CMD ["python", "app.py"]
```

Signal goes directly to:

```bash
python
```

Result:

```text
Graceful Shutdown
```

---

# Real-World Recommendation

### Use Shell Form When

You need shell features such as:

```dockerfile
CMD echo "Starting" && python app.py
```

or

```dockerfile
CMD cat file.txt | grep error
```

---

### Use Exec Form When

You are running:

- Python applications
- Java applications
- Node.js applications
- Go binaries
- Nginx
- Apache
- Production workloads

Examples:

```dockerfile
CMD ["node", "server.js"]
```

```dockerfile
CMD ["java", "-jar", "app.jar"]
```

```dockerfile
CMD ["nginx", "-g", "daemon off;"]
```

---

# Best Practice

For modern Docker images:

```dockerfile
ENTRYPOINT ["python"]
CMD ["app.py"]
```

or

```dockerfile
CMD ["python", "app.py"]
```

Prefer **Exec Form** unless you specifically require shell functionality.

---

# Common Interview Question

### Which form is recommended for production containers?

**Answer:**

Exec Form is recommended because it runs the application directly as PID 1, provides proper signal handling, avoids an unnecessary shell process, and enables graceful container shutdown.

---

# Interview One-Liner

**Shell Form** runs commands through `/bin/sh -c`, providing shell features but weaker signal handling.

**Exec Form** runs commands directly without a shell, making it the preferred choice for production Docker containers.