# DRF/Admin CSS Missing in Docker

## The Problem

When containerizing a Django Rest Framework (DRF) application, the browsable API and Django Admin interfaces often lose their CSS styling, rendering as plain, unformatted HTML.

This happens because of the "Static Files Disconnect." Django does not inherently serve static files (like CSS, JavaScript, and images) in a production or containerized environment. While the `runserver` command magically handles static files during standard local development, it drops this functionality when containerized or when `DEBUG` is set to `False` for security and performance reasons.

## The Quick Fix (Development Only)

To fix this temporarily in a Dockerized development environment, you must force Django to gather all the DRF and Admin CSS files into a single directory, and then start the server.

This is done by chaining commands in the `Dockerfile` or `docker-compose.yml`:

```dockerfile
# Gathers all static files into the STATIC_ROOT directory, then starts the server
CMD python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000
```
