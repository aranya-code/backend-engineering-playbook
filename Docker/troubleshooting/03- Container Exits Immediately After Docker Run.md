# Ubuntu Container Exits Immediately After `docker run -d`

```bash
docker run -d --name ubuntu ubuntu:14.04
```

## Why It Happens

Starts the container, but Ubuntu has no foreground process to keep it alive, so it exits immediately.

We need to keep it alive by running a process inside the container.

Docker containers stay alive only while a foreground process is running.

In this case:

- Ubuntu image starts
- No active foreground process exists
- Container exits immediately

## Solution 1 — Run Interactively

```bash
docker run -it --name ubuntu ubuntu:14.04 /bin/bash
```

### What Happens

- `i` → interactive mode
- `t` → terminal access
- `/bin/bash` → keeps container alive

Now you are inside the container.

## Solution 2 — Run in Detached Mode

```bash
docker run -dit --name ubuntu ubuntu:14.04 bash
```

### What Happens

- `d` → detached/background mode
- `i` → interactive
- `t` → terminal
- `bash` → foreground process

Container keeps running.
