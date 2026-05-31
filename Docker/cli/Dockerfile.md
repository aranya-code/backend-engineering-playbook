# Dockerfile

---

### Builds an image from a Dockerfile.

```bash
docker build -t <app>:<tag> .
```

### Prevents Python from creating .pyc files.

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1
```

### Flushes Python logs immediately.

```dockerfile
ENV PYTHONUNBUFFERED=1
```

### Installs dependencies without caching.

```bash
pip install --no-cache-dir -r requirements-docker.txt
```

### Starts the Django development server.

```bash
python manage.py runserver 0.0.0.0:8000 --insecure
```

### Collects static files for deployment.

```bash
python manage.py collectstatic --noinput
```
