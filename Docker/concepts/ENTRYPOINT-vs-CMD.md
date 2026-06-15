# ENTRYPOINT vs CMD

## Overview

Both `ENTRYPOINT` and `CMD` define what command runs when a container starts, but they serve different purposes.

- **ENTRYPOINT** defines the main executable of the container.
- **CMD** provides default arguments for the executable or a default command if no ENTRYPOINT is specified.

Understanding the difference is important for building flexible and reusable Docker images.

---

# ENTRYPOINT

## Definition

`ENTRYPOINT` specifies the command that will always be executed when the container starts.

It turns the container into a dedicated executable.

### Characteristics

- Cannot be easily overridden by additional arguments passed to `docker run`.
- Additional arguments are appended to the ENTRYPOINT command.
- Best used when the container should always run a specific program.

---

## Syntax

### Exec Form (Recommended)

```dockerfile
ENTRYPOINT ["executable", "arg1"]
```

Example:

```dockerfile
ENTRYPOINT ["python"]
```

---

### Shell Form

```dockerfile
ENTRYPOINT python
```

Example:

```dockerfile
ENTRYPOINT python app.py
```

⚠️ Shell form runs through:

```bash
/bin/sh -c
```

and does not handle signals as effectively as exec form.

---

# CMD

## Definition

`CMD` provides default arguments for the container.

If used together with ENTRYPOINT, CMD acts as the default parameters supplied to ENTRYPOINT.

### Characteristics

- Can be overridden at runtime.
- Only the last CMD instruction is used.
- Useful for defining default behavior.

---

## Syntax

### Exec Form (Recommended)

```dockerfile
CMD ["arg1", "arg2"]
```

Example:

```dockerfile
CMD ["app.py"]
```

---

### Default Command Example

Without ENTRYPOINT:

```dockerfile
CMD ["nginx", "-g", "daemon off;"]
```

Docker executes:

```bash
nginx -g "daemon off;"
```

---

# ENTRYPOINT + CMD Together

This is the most common and recommended approach.

## Dockerfile

```dockerfile
ENTRYPOINT ["python"]
CMD ["app.py"]
```

When the container starts, Docker combines them:

```bash
python app.py
```

---

## Runtime Example

Build image:

```bash
docker build -t my-python-app .
```

Run container:

```bash
docker run my-python-app
```

Docker executes:

```bash
python app.py
```

---

## Overriding CMD

Run:

```bash
docker run my-python-app test.py
```

Docker executes:

```bash
python test.py
```

Only CMD is replaced.

ENTRYPOINT remains unchanged.

---

## Overriding ENTRYPOINT

Run:

```bash
docker run --entrypoint bash my-python-app
```

Docker executes:

```bash
bash
```

ENTRYPOINT is completely replaced.

---

# Execution Flow

### Only CMD

Dockerfile:

```dockerfile
CMD ["nginx"]
```

Run:

```bash
docker run myimage
```

Execution:

```bash
nginx
```

---

### Only ENTRYPOINT

Dockerfile:

```dockerfile
ENTRYPOINT ["python"]
```

Run:

```bash
docker run myimage app.py
```

Execution:

```bash
python app.py
```

Arguments supplied at runtime are appended.

---

### ENTRYPOINT + CMD

Dockerfile:

```dockerfile
ENTRYPOINT ["python"]
CMD ["app.py"]
```

Run:

```bash
docker run myimage
```

Execution:

```bash
python app.py
```

---

# Visual Representation

```text
ENTRYPOINT = Main Program
CMD        = Default Arguments

ENTRYPOINT ["python"]
CMD ["app.py"]

Docker combines them as:

python app.py
```

---

# Real-World Examples

## Example 1: Python Application

```dockerfile
ENTRYPOINT ["python"]
CMD ["app.py"]
```

Possible executions:

```bash
docker run myimage
```

Result:

```bash
python app.py
```

```bash
docker run myimage test.py
```

Result:

```bash
python test.py
```

---

## Example 2: Ping Utility

```dockerfile
ENTRYPOINT ["ping"]
CMD ["google.com"]
```

Run:

```bash
docker run ping-image
```

Result:

```bash
ping google.com
```

Run:

```bash
docker run ping-image github.com
```

Result:

```bash
ping github.com
```

---

# Best Practices

### Use ENTRYPOINT when:

- The container should behave like a specific executable.
- You want users to pass only arguments.
- The main process should always run.

Examples:
- Python scripts
- Java applications
- Utility containers

---

### Use CMD when:

- Providing default arguments.
- Defining a default command that users may replace.
- Creating flexible images.

---

### Recommended Pattern

```dockerfile
ENTRYPOINT ["python"]
CMD ["app.py"]
```

This provides:
- A fixed executable (`python`)
- A configurable default argument (`app.py`)

---

# Interview Question

### What is the difference between ENTRYPOINT and CMD?

**Answer:**

`ENTRYPOINT` defines the main executable that always runs when a container starts, while `CMD` provides default arguments or a default command. When both are used together, Docker executes the ENTRYPOINT command with CMD values as its default arguments. CMD can be overridden at runtime, whereas ENTRYPOINT remains fixed unless explicitly replaced using `--entrypoint`.