# Docker Compose

## Multi-Container Django Architecture

```yaml
services:

  web-1:
    build: .
    command: >
      sh -c "
      python manage.py collectstatic --noinput &&
      python manage.py runserver 0.0.0.0:8000 --insecure
      "

    volumes:
      - .:/app
      - static_volume:/app/staticfiles

    ports:
      - "8000:8000"

  web-2:
    build: .

    command: "python manage.py runserver 0.0.0.0:8000 --insecure"

    volumes:
      - .:/app
      - static_volume:/app/staticfiles

    ports:
      - "8001:8000"

volumes:
  static_volume:
```
