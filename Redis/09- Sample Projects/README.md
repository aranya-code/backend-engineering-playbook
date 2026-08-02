# Sample Projects

Two complete, runnable projects that demonstrate **12 Redis features** each through real backend implementations — not tutorials or pseudo-code.

Both projects implement the same Redis features side by side, so you can compare how Django and FastAPI handle identical problems.

---

## Projects

| Project | Framework | Redis Client | Key Difference |
|---------|-----------|-------------|----------------|
| [django-redis-lab](./django-redis-lab/) | Django 5 + DRF + Celery | Sync `redis-py` + `django-redis` | Django cache framework, DRF serializers, sync architecture |
| [fastapi-redis-lab](./fastapi-redis-lab/) | FastAPI + SQLAlchemy 2 + Celery | Async `redis.asyncio` | Native async, Pydantic v2, dependency injection, auto-generated Swagger docs |

---

## Redis Features Implemented

Both projects implement all 12 features:

| # | Feature | Redis Data Structure | Implementation |
|---|---------|---------------------|----------------|
| 01 | Product Response Cache | String + JSON | Cache list/detail endpoints with invalidation |
| 02 | Shopping Cart | Hash | `cart:user:{id}` — per-user cart with atomic quantity updates |
| 03 | OTP Verification | String + TTL | `SET key value EX 300` — auto-expires in 5 minutes |
| 04 | Rate Limiter | INCR + EXPIRE | Per-IP request throttling with sliding window |
| 05 | Product View Counter | INCR | Atomic page view counting |
| 06 | Leaderboard | Sorted Set | `ZADD` / `ZREVRANGE` — top viewed products |
| 07 | Pub/Sub | Pub/Sub | Publish messages to named channels |
| 08 | Streams | Stream | `XADD` / `XREVRANGE` — ordered event log for orders |
| 09 | Distributed Lock | SET NX EX | Lua-script-based atomic acquire/release |
| 10 | Celery Background Tasks | Redis Broker | Simulated email sending via Celery workers |
| 11 | HyperLogLog | HyperLogLog | Approximate unique visitor counting (~12 KB) |
| 12 | Bitmap | Bitmap | Daily login tracking with `SETBIT` / `BITCOUNT` |

---

## Architecture (Both Projects)

```text
Client (HTTP Request)
       │
       ▼
┌─────────────────┐
│  Views / Router  │  ← Thin controllers (validation + response)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Service Layer   │  ← Business logic
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
    ▼          ▼
┌────────┐ ┌────────────┐
│ SQLite │ │   Redis    │  ← All Redis ops in one module
└────────┘ └──────┬─────┘
                  │
                  ▼
           ┌────────────┐
           │   Celery    │  ← Background tasks
           └────────────┘
```

---

## API Endpoints (Both Projects)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products` | List all products (cached) |
| GET | `/products/{id}` | Product detail (cached, tracks views) |
| POST | `/cart` | Add item to cart |
| GET | `/cart` | Get cart contents |
| DELETE | `/cart` | Clear cart |
| POST | `/otp` | Generate OTP |
| POST | `/login` | Verify OTP |
| GET | `/leaderboard` | Top 10 most-viewed products |
| POST | `/publish` | Publish Pub/Sub message |
| POST | `/stream` | Add order event to stream |
| POST | `/cache/clear` | Clear all cache |
| GET | `/analytics` | HyperLogLog + Bitmap + view counts |

---

## Quick Start

### Prerequisites

- Python 3.12+
- Redis running on `localhost:6379`

### django-redis-lab

```bash
cd django-redis-lab
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
# Celery (separate terminal): celery -A config worker --loglevel=info
```

### fastapi-redis-lab

```bash
cd fastapi-redis-lab
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
# Celery (separate terminal): celery -A app.tasks worker --loglevel=info
```

Visit `http://localhost:8000/docs` (FastAPI) for interactive Swagger UI.

---

## Django vs FastAPI Comparison

| Aspect | django-redis-lab | fastapi-redis-lab |
|--------|-----------------|-------------------|
| Redis Client | Sync `redis-py` | Async `redis.asyncio` |
| Cache Backend | `django-redis` (cache framework) | Manual JSON cache in Redis |
| Validation | DRF Serializers | Pydantic v2 models |
| Dependency Injection | Manual | FastAPI `Depends()` |
| Rate Limiting | Custom decorator | FastAPI dependency |
| API Docs | Manual README | Auto-generated Swagger + ReDoc |
| ORM | Django ORM | SQLAlchemy 2.x |
| Database | SQLite | SQLite |

---
