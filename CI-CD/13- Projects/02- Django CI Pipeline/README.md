# 02 - Django CI Pipeline

Runnable Django health endpoint with automated Django checks and pytest.

## Run

```bash
pip install -r requirements.txt
python manage.py runserver
```

Open `http://127.0.0.1:8000/health/`.

## CI focus

- Django system checks
- pytest-django
- Python dependency caching
- Pull-request validation
