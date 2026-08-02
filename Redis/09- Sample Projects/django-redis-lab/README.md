# Django Redis Lab

A production-quality Django project demonstrating every major Redis feature through real backend implementations. Built for backend engineers who want to understand how Redis integrates with Django in practical, real-world scenarios.

---

## Features

| # | Feature | Redis Data Structure | Description |
|---|---------|---------------------|-------------|
| 01 | Product Response Cache | Django Cache Framework | Cache list/detail endpoints with invalidation |
| 02 | Shopping Cart | Hash | Per-user cart with add/get/delete operations |
| 03 | OTP Verification | String + TTL | One-time password with 300-second expiration |
| 04 | Rate Limiter | INCR + EXPIRE | Request throttling per IP |
| 05 | Product View Counter | INCR | Track product page views |
| 06 | Leaderboard | Sorted Set | Top viewed products ranked by view count |
| 07 | Pub/Sub | Pub/Sub | Publish and subscribe to notification channels |
| 08 | Streams | Stream | Ordered event log for order events |
| 09 | Distributed Lock | SET NX EX | Prevent race conditions in concurrent operations |
| 10 | Celery Tasks | Redis Broker | Background email simulation |
| 11 | HyperLogLog | HyperLogLog | Approximate unique visitor counting |
| 12 | Bitmap | Bitmap | Daily login tracking |

---

## Architecture

```text
Client (API Request)
       │
       ▼
┌─────────────────┐
│  Django Views    │  ← Thin controllers (validation, serialization, response)
│  (views.py)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Service Layer   │  ← Business logic (services.py)
│  (services.py)   │
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
    ▼          ▼
┌────────┐ ┌────────────┐
│ SQLite │ │   Redis    │  ← redis_service.py (all Redis operations)
│ (ORM)  │ │ (Cache,    │
│        │ │  Counters, │
└────────┘ │  Queues)   │
           └──────┬─────┘
                  │
                  ▼
           ┌────────────┐
           │   Celery    │  ← Background tasks via Redis broker
           │  (tasks.py) │
           └────────────┘
```

---

## Installation

### Prerequisites

- Python 3.12+
- Redis Server running on `localhost:6379`

### Redis Setup

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**Windows:**
```bash
# Install from https://github.com/tporadowski/redis/releases
# Or use WSL and follow the Ubuntu instructions
```

**Verify Redis is running:**
```bash
redis-cli ping
# Expected: PONG
```

### Project Setup

```bash
# Clone the repository
cd D:\backend-engineering-playbook\Redis\sample projects
cd django-redis-lab

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Run migrations
python manage.py migrate

# Seed sample data (optional)
python manage.py shell -c "
from playground.models import Product
products = [
    Product(name='Laptop', description='High-performance laptop', price=999.99, stock=50, category='Electronics'),
    Product(name='Headphones', description='Noise-cancelling headphones', price=199.99, stock=200, category='Electronics'),
    Product(name='Python Book', description='Advanced Python programming', price=49.99, stock=100, category='Books'),
    Product(name='Mechanical Keyboard', description='RGB mechanical keyboard', price=149.99, stock=75, category='Peripherals'),
    Product(name='Monitor', description='4K Ultra HD monitor', price=449.99, stock=30, category='Electronics'),
]
Product.objects.bulk_create(products)
print(f'Created {len(products)} products')
"

# Start the development server
python manage.py runserver
```

### Running Celery

Open a separate terminal:

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Start Celery worker
celery -A config worker --loglevel=info
```

---

## API Documentation

### Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products/` | List all products (cached) |
| GET | `/api/products/{id}/` | Get product detail (cached, increments view counter) |

### Shopping Cart

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| POST | `/api/cart/` | `{"user_id": 1, "product_id": 1, "quantity": 2}` | Add item to cart |
| GET | `/api/cart/?user_id=1` | — | Get cart contents |
| DELETE | `/api/cart/` | `{"user_id": 1}` | Clear entire cart |

### OTP & Login

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| POST | `/api/otp/` | `{"email": "user@example.com"}` | Generate and store OTP (TTL 300s) |
| POST | `/api/login/` | `{"email": "user@example.com", "otp": "123456"}` | Verify OTP and log in |

### Leaderboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/leaderboard/` | Top 10 most-viewed products |

### Pub/Sub

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| POST | `/api/publish/` | `{"channel": "notifications", "message": "Hello"}` | Publish message to a channel |

### Streams

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| POST | `/api/stream/` | `{"order_id": 1, "event": "created", "data": {"total": 99.99}}` | Add order event to stream |

### Cache Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/cache/clear/` | Clear all cached data |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/` | Unique visitors (HyperLogLog), daily logins (Bitmap), view counts |

---

## Project Structure

```text
django-redis-lab/
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── .gitignore                 # Git ignore rules
├── manage.py                  # Django management script
│
├── config/                    # Django project configuration
│   ├── __init__.py
│   ├── settings.py            # Django settings (Redis, Cache, Celery config)
│   ├── urls.py                # Root URL configuration
│   ├── asgi.py                # ASGI entry point
│   ├── wsgi.py                # WSGI entry point
│   └── celery.py              # Celery application setup
│
├── playground/                # Main application
│   ├── __init__.py
│   ├── apps.py                # App configuration
│   ├── admin.py               # Admin registration
│   ├── models.py              # Product model
│   ├── serializers.py         # DRF serializers
│   ├── urls.py                # App URL routes
│   ├── views.py               # API views (thin controllers)
│   ├── services.py            # Business logic layer
│   ├── redis_service.py       # All Redis operations
│   ├── tasks.py               # Celery background tasks
│   ├── pubsub.py              # Redis Pub/Sub helpers
│   ├── stream.py              # Redis Streams helpers
│   ├── locks.py               # Distributed lock implementation
│   ├── utils.py               # Utility functions
│   └── migrations/            # Database migrations
│
└── db.sqlite3                 # SQLite database (auto-created)
```

---

## Redis Features Explained

### 1. Product Response Cache
Uses Django's cache framework backed by `django-redis`. Product list and detail responses are cached with configurable TTL. Cache is automatically invalidated when products are modified.

### 2. Shopping Cart (Hash)
Each user's cart is stored as a Redis Hash at key `cart:user:{id}`. Product IDs are fields, quantities are values. Enables atomic operations on individual items without loading the entire cart.

### 3. OTP (String + TTL)
One-time passwords are stored with `SET key value EX 300`. Redis automatically expires the OTP after 5 minutes. No database writes, no cleanup cron jobs.

### 4. Rate Limiter (INCR + EXPIRE)
Tracks request count per IP using `INCR`. On the first request, sets an `EXPIRE` of 60 seconds. If the count exceeds the limit, the request is rejected with 429 Too Many Requests.

### 5. View Counter (INCR)
Atomic `INCR` on `product:views:{id}` counts product page views. Atomic means no race conditions even with concurrent requests.

### 6. Leaderboard (Sorted Set)
`ZADD` adds view counts as scores. `ZREVRANGE` retrieves the top-N products. Redis handles sorting internally — O(log N) insertion, O(log N + M) range queries.

### 7. Pub/Sub
Publish messages to named channels. Subscribers receive messages in real time. Useful for real-time notifications, event broadcasting, and inter-service communication.

### 8. Streams
Ordered, append-only event log. Each entry has an auto-generated ID (timestamp-based). Supports consumer groups for distributed processing. Used here for order event tracking.

### 9. Distributed Lock (SET NX EX)
`SET lock_key value NX EX 10` acquires a lock only if it doesn't exist (NX), with automatic expiration (EX). Prevents race conditions in distributed environments.

### 10. Celery (Redis Broker)
Redis serves as the message broker for Celery. Background tasks (e.g., sending emails) are queued in Redis and processed by Celery workers asynchronously.

### 11. HyperLogLog
Probabilistic data structure that estimates unique counts using ~12 KB of memory regardless of the number of elements. Used for counting unique visitors with 0.81% standard error.

### 12. Bitmap
Bit-level operations on strings. Each bit represents a user ID. `SETBIT` marks a user as logged in. `BITCOUNT` counts total logins. Extremely memory-efficient for binary state tracking.

---

## Learning Objectives

After studying this project, you will understand:

1. How to configure Redis as a Django cache backend
2. When to use Redis Hashes, Sorted Sets, Streams, HyperLogLog, and Bitmaps
3. How to implement a service layer that separates Redis logic from views
4. How to build rate limiters, view counters, and leaderboards with Redis
5. How Redis Pub/Sub and Streams differ and when to use each
6. How to implement distributed locks for concurrent operations
7. How to configure Celery with Redis as a message broker
8. How cache invalidation works in practice

---

> **Part of the [Backend Engineering Playbook](../../) — a structured learning resource for backend engineers.**

*Created by Aranya Majumdar*
