# 16- Backend Integration

Use S3 behind well-defined application boundaries; do not turn a bucket into an unaudited shared filesystem.

## How to use this section

Read the chapters in order, then apply the checks to one real bucket or backend workflow. The aim is not API memorization; it is a defensible design decision that can be verified in production.

## Chapters

- [Django](./01-%20Django.md)
- [Django REST Framework](./02-%20Django%20REST%20Framework.md)
- [FastAPI](./03-%20FastAPI.md)
- [Flask](./04-%20Flask.md)
- [Celery](./05-%20Celery.md)

## Completion check

You can explain the relevant request path, authorization boundary, data lifecycle, observability signal, and rollback or recovery procedure.
