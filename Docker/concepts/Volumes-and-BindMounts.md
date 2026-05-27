# Volumes and Bind Mounts

# Docker Volumes

## Definition

Docker Volumes are managed persistent storage locations maintained by Docker.

---

## Create Volume

```bash
docker volume create myvolume
```

---

# Bind Mounts

## Definition

Bind mounts map host directories directly into containers.

---

## Example

```bash
docker run -v <host_path>:<container_path> <image>
```
