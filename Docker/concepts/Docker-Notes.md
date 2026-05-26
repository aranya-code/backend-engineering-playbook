# Docker Notes

Created by: aranya majumdar

---

# Background

**Docker** is an open-source platform that allows developers to automate the deployment, scaling, and management of applications. It does this by packaging software into standardized, isolated units called **containers**.

### Sample Docker File

```docker
# Import the python image with version
FROM python:3.12-slim

# Prevent python from creating pyc file and buffering logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Mention work directory
WORKDIR /app

# Import requirements file
COPY requirements-docker.txt .

#Install dependencies
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copy project files
COPY . .

# Expose port 
EXPOSE 8000

# Default command to run
CMD python manage.py collectstatic --noinput && \
    python manage.py runserver 0.0.0.0:8000

```

### Sample Docker Compose File

```docker
# ==============================================================================
# MULTI-CONTAINER DJANGO DOCKER COMPOSE ARCHITECTURE
# ==============================================================================
# This setup runs two identical Django applications side-by-side. 
# They share the exact same codebase and static files but are accessible 
# on different ports. This is the foundational setup for load balancing.

services:

  # ----------------------------------------------------------------------------
  # SERVICE 1: The Primary Worker (web-1)
  # ----------------------------------------------------------------------------
  web-1:
    # Looks in the current directory (.) for the Dockerfile and builds the image.
    build: . 
    
    # The '>' tells Docker to treat the following multiple lines as a single command.
    # 'sh -c' opens a shell to run these two commands sequentially using '&&':
    # 1. 'collectstatic' gathers all CSS/JS into the static root automatically.
    # 2. 'runserver' starts the app and forces static file serving (--insecure).
    command: >
      sh -c "
      python manage.py collectstatic --noinput &&
      python manage.py runserver 0.0.0.0:8000 --insecure
      "
      
    volumes:
      # Bind Mount: Syncs your local Windows folder into the container's /app folder.
      # When you hit save in VS Code, the container instantly sees the update.
      - .:/app
      # Named Volume: Attaches an isolated, shared storage bucket (static_volume) 
      # to the directory where Django collects static files.
      - static_volume:/app/staticfiles
      
    ports:
      # HOST:CONTAINER map. Maps port 8000 on your Windows machine to 8000 inside Docker.
      - "8000:8000"
      
    env_file:
      # Loads variables from your Docker-specific environment file.
      - .env.docker
      
    environment:
      # Hardcoded variable that overrides the .env file for this specific container.
      - DEBUG=1

  # ----------------------------------------------------------------------------
  # SERVICE 2: The Secondary Worker (web-2)
  # ----------------------------------------------------------------------------
  web-2:
    build: .
    
    # Notice this DOES NOT run collectstatic. It doesn't need to.
    # Because web-1 runs it, web-2 just starts up and reads from the shared volume.
    command: "python manage.py runserver 0.0.0.0:8000 --insecure"
    
    volumes:
      # Uses the exact same volumes as web-1. This guarantees both containers 
      # are running the exact same code and serving the exact same CSS files.
      - .:/app
      - static_volume:/app/staticfiles
      
    ports:
      # You cannot have two apps listening on host port 8000 simultaneously.
      # This maps host port 8001 to container port 8000 to avoid conflicts.
      # localhost:8000 -> web-1 | localhost:8001 -> web-2
      - "8001:8000"
      
    env_file:
      - .env.docker
      
    environment:
      - DEBUG=1
 
# ------------------------------------------------------------------------------
# GLOBAL DECLARATIONS
# ------------------------------------------------------------------------------
volumes:
  # This sits outside the services block. It tells Docker to create an empty, 
  # persistent storage drive named 'static_volume' before starting any containers 
  # so that web-1 and web-2 can share files seamlessly.
  static_volume:
```

---

# Docker Volumes

## Definition

Docker Volumes are managed storage locations created and maintained by Docker to persist container data.

Volumes remain even if the container is removed.

---

## Why Use Volumes?

- Persistent data storage
- Share data between containers
- Backup and restore support
- Better performance
- Docker-managed storage

---

## Volume Lifecycle

Container deleted ❌

Volume deleted ❌

Volume survives independently.

---

### Create a Volume

```bash
docker volume create <volume name>
```

## Best Practices

- Use volumes for databases
- Use named volumes in production
- Avoid storing important data inside containers
- Backup volumes regularly

# Docker Bind Mounts

### Definition

Bind Mounts map a file or directory from the host machine directly into the container.

Host controls the data.

### Why Use Bind Mounts?

- Real-time file sharing
- Local development
- Code synchronization
- Easy debugging

### Difference Between Volume and Bind Mount


```docker
| Feature | Volume | Bind Mount |
|---|---|---|
| Managed by Docker | Yes | No |
| Stored by Docker | Yes | No |
| Host Path Required | No | Yes |
| Best for Production | Yes | Usually No |
| Best for Development | Good | Excellent |
```

### Bind Mount Syntax

```docker
docker run -v <host_path>:<container_path> <image>
```

```docker
docker run --mount type=bind,source=<host_path>,target=<container_path> <image>
```

## Common Bind Mount Use Cases

- Local code development
- Live reload applications
- Sharing configuration files
- Sharing logs
- Testing applications

## Important Notes

- Host path must exist
- Changes reflect instantly
- Bind mounts depend on host filesystem
- Not ideal for portability

## Best Practices

- Use bind mounts during development
- Use volumes in production
- Use read-only mounts when possible
- Avoid mounting sensitive host directories

---

## ENTRYPOINT & CMD

This is the command the container ALWAYS runs when it starts.

This is the process that should keep the container alive.

### Real world analogy

Imagine Docker container = a machine.

- `ENTRYPOINT` = machine engine
- `CMD` = default settings/options for the engine
- `ENTRYPOINT` = Fixed executable
- `CMD` = Default arguments

```docker
ENTRYPOINT ["python"]
CMD ["app.py"]
```

### Example 1 — Simple Python App

```docker
FROM python:3.12

WORKDIR /app

COPY . .

ENTRYPOINT ["python", "main.py"]
```

### Example 2 — Using CMD + ENTRYPOINT Together

```docker
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
```

### ENTRYPOINT vs CMD

| Feature | ENTRYPOINT | CMD |
| --- | --- | --- |
| Purpose | Main command | Default arguments |
| Mandatory? | No | No |
| Easily overridden? | Harder | Easy |
| Best use | Fixed application | Configurable defaults |
| Runs as PID 1 | Usually Yes | Sometimes |

---

# Shell Form vs Exec Form in Docker

## Definition

Docker instructions like `RUN`, `CMD`, and `ENTRYPOINT` can be written in two formats:

1. Shell Form
2. Exec Form


# 1. Shell Form

## Syntax

```docker
CMD python app.py
```

or

```docker
ENTRYPOINT python app.py
```


## Internal Working

Docker automatically runs:

```bash
/bin/sh -c "python app.py"
```

Meaning:

- A shell process starts first
- Then the shell starts the application


## Process Structure

```
PID 1 -> sh -> python
```


## Advantages

- Supports shell features
- Supports variable expansion
- Supports pipes and chaining

Example:

```docker
RUN apt update && apt install -y nginx
```


## Disadvantages

- Poor signal handling
- Shell becomes PID 1
- Not ideal for production
- Can cause zombie processes
- Kubernetes shutdown issues


# 2. Exec Form

## Syntax

```docker
CMD ["python", "app.py"]
```

or

```docker
ENTRYPOINT ["python", "app.py"]
```


## Internal Working

Docker directly executes:

```bash
python app.py
```

No shell is involved.


## Process Structure

```
PID 1 -> python
```


## Advantages

- Proper signal handling
- Application becomes PID 1
- Better for production
- Better Kubernetes compatibility
- Cleaner process management
- More secure


## Disadvantages

- No shell variable expansion
- No shell operators like:
    - `&&`
    - pipes (`|`)
    - redirects (`>`)


# Signal Handling Difference

## Shell Form

```docker
ENTRYPOINT python app.py
```

Docker sends signals to:

```
/bin/sh
```

Sometimes the shell does not properly forward signals to the app.

Can cause:

- hanging containers
- improper shutdown
- data corruption


## Exec Form

```docker
ENTRYPOINT ["python", "app.py"]
```

Signals go directly to:

```
python
```

Result:

- graceful shutdown
- clean container stopping
- better reliability


# Environment Variable Difference

## Shell Form

Supports variable expansion:

```docker
CMD echo $HOME
```


## Exec Form

Does NOT expand variables automatically:

```docker
CMD ["echo", "$HOME"]
```

Outputs:

```
$HOME
```

literally.


# Using Variables in Exec Form

Use explicit shell:

```docker
ENTRYPOINT ["sh", "-c", "echo $HOME"]
```


# Best Practices

## Use Shell Form For

### RUN instructions

Example:

```docker
RUN apt update && apt install -y curl
```

Reason:

- shell operators are useful


## Use Exec Form For

### CMD

### ENTRYPOINT

Example:

```docker
ENTRYPOINT ["gunicorn", "app.wsgi:application"]
```

Reason:

- proper signal handling
- production-grade containers


# Comparison Table

| Feature | Shell Form | Exec Form |
| --- | --- | --- |
| Uses shell | Yes | No |
| PID 1 is application | No | Yes |
| Signal handling | Poor | Excellent |
| Variable expansion | Yes | No |
| Supports shell operators | Yes | No |
| Production recommended | No | Yes |
| Kubernetes friendly | Weak | Strong |
| Security | Less secure | More secure |


# Professional Recommendation

## Preferred Industry Standard

```docker
ENTRYPOINT ["python", "app.py"]
```

Use:

- Exec form for CMD and ENTRYPOINT
- Shell form mainly for RUN


# Common Beginner Mistake

## Bad

```docker
ENTRYPOINT python app.py
```


## Good

```docker
ENTRYPOINT ["python", "app.py"]
```


# Interview One-Liner

> Shell form runs commands through `/bin/sh -c`, while exec form directly executes the process. Exec form is preferred in production because it provides proper signal handling and cleaner process management.
> 

---