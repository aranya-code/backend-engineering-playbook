# Volumes and Bind Mounts

---

### Lists all Docker volumes.

```bash
docker volume ls
```

### Creates a named volume.

```bash
docker volume create <volume>
```

### Removes a volume.

```bash
docker volume rm <volume>
```

### Deletes unused volumes.

```bash
docker volume prune
```

### Mounts a named volume.

```bash
docker run -v <volume>:<container-path>
```

### Creates a bind mount from the host.

```bash
docker run -v <host-path>:<container-path>
```
