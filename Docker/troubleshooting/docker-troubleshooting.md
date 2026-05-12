# Docker Notes

Created by: aranya majumdar

### Docker database issue

![Database Issue](../images/DB_Issue.png)

#### Option 1: Your database is running on your Windows machine

If you already have PostgreSQL installed and running natively on your local computer, you just need to tell Docker how to reach outside the container and talk to your host machine.

Docker has a special DNS name specifically for this: `host.docker.internal`.

![Fix 1](../images/DB_Issue_Fix.png)

#### Option 2: Containerize the Database

![Fix 2](../images/DB_Containerize.png)

```yaml
services:
  web:
    build: .
    command: "python manage.py runserver 0.0.0.0:8000"
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - DEBUG=1
    depends_on:
      - db # This tells Docker to start the DB first

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=my_database_name
      - POSTGRES_USER=my_database_user
      - POSTGRES_PASSWORD=my_secure_password
    ports:
      - "5432:5432"
```

### DRF CSS Styling Missing in Docker

**The Problem Statement**

When containerizing a Django Rest Framework (DRF) application, the browsable API and Django Admin interfaces often lose their CSS styling, rendering as plain, unformatted HTML.

This happens because of the "Static Files Disconnect." Django does not inherently serve static files (like CSS, JavaScript, and images) in a production or containerized environment. While the `runserver` command magically handles static files during standard local development, it drops this functionality when containerized or when `DEBUG` is set to `False` for security and performance reasons.

#### The Quick Fix (Development Only)

To fix this temporarily in a Dockerized development environment, you must force Django to gather all the DRF and Admin CSS files into a single directory, and then start the server.

This is done by chaining commands in the `Dockerfile` or `docker-compose.yml`:

```docker
# Gathers all static files into the STATIC_ROOT directory, then starts the server
CMD python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000
```