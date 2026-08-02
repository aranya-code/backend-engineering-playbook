# FastAPI Redis Lab 🚀

A **production-quality** FastAPI project demonstrating comprehensive Redis integration patterns for backend development.

This is **NOT** a tutorial. This is a **real, runnable project** that showcases Redis features through practical backend implementations.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Project](#running-the-project)
- [API Documentation](#api-documentation)
- [Redis Features](#redis-features)
- [Architecture](#architecture)
- [Learning Objectives](#learning-objectives)
- [API Examples](#api-examples)

## 🎯 Overview

FastAPI Redis Lab is a complete backend application that demonstrates how to integrate Redis with FastAPI for building high-performance, scalable web services. Every Redis feature is implemented in a real-world context with proper error handling, type safety, and best practices.

## ✨ Features

### Core Features

- ✅ **Product Catalog** - Full CRUD with intelligent caching
- ✅ **Shopping Cart** - Redis Hash-based cart management
- ✅ **OTP Authentication** - Time-limited one-time passwords
- ✅ **Rate Limiting** - Request throttling per client
- ✅ **Analytics Dashboard** - Real-time metrics and insights
- ✅ **Background Tasks** - Celery integration for async jobs
- ✅ **Distributed Locking** - Prevent race conditions
- ✅ **Real-time Messaging** - Pub/Sub implementation
- ✅ **Event Sourcing** - Redis Streams for event logs

### Redis Data Structures

| Structure | Use Case | Implementation |
|-----------|----------|----------------|
| **String** | Caching, Counters, OTP | Product cache, view counters |
| **Hash** | Structured data | Shopping cart storage |
| **Sorted Set** | Leaderboards, Rankings | Top viewed products |
| **HyperLogLog** | Cardinality estimation | Unique visitors count |
| **Bitmap** | Boolean flags | Daily active users tracking |
| **Streams** | Event logs, Message queues | Order events, notifications |
| **Pub/Sub** | Real-time messaging | Event broadcasting |
| **SET NX EX** | Distributed locks | Critical section protection |

## 🛠️ Tech Stack

- **Python** 3.12+
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server
- **SQLAlchemy 2.x** - Async ORM
- **Pydantic v2** - Data validation
- **Redis** - In-memory data store
- **redis-py** (async) - Redis client
- **Celery** - Distributed task queue
- **SQLite** - Database (for simplicity)
- **python-dotenv** - Environment management

## 📁 Project Structure

```
fastapi-redis-lab/
├── app/
│   ├── __init__.py           # Package initialization
│   ├── main.py               # FastAPI application entry point
│   ├── config.py             # Configuration management
│   ├── database.py           # Database setup and session management
│   ├── redis_client.py       # Redis client and helper functions
│   ├── models.py             # SQLAlchemy models
│   ├── schemas.py            # Pydantic schemas
│   ├── services.py           # Business logic layer
│   ├── dependencies.py       # FastAPI dependencies
│   ├── utils.py              # Utility functions
│   ├── tasks.py              # Celery tasks
│   ├── pubsub.py             # Redis Pub/Sub implementation
│   ├── stream.py             # Redis Streams implementation
│   ├── locks.py              # Distributed locking
│   └── routers/
│       ├── __init__.py
│       ├── products.py       # Product CRUD endpoints
│       ├── cart.py           # Shopping cart endpoints
│       ├── auth.py           # Authentication endpoints
│       ├── analytics.py      # Analytics endpoints
│       └── redis_examples.py # Redis feature demonstrations
│
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## 📦 Installation

### Prerequisites

- Python 3.12 or higher
- Redis Server 6.0 or higher
- pip (Python package manager)

### Step 1: Clone or Navigate to Project

```bash
cd "D:\backend-engineering-playbook\Redis\sample projects\fastapi-redis-lab"
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Setup Environment Variables

```bash
# Copy example environment file
copy .env.example .env

# Edit .env file with your configuration (if needed)
```

## ⚙️ Configuration

Edit `.env` file to configure the application:

```env
# Application
APP_NAME=FastAPI Redis Lab
DEBUG=True

# Database
DATABASE_URL=sqlite:///./db.sqlite3

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Rate Limiting
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60

# Cache
CACHE_TTL=300
```

## 🚀 Running the Project

### Step 1: Start Redis Server

**Windows (if installed as service):**
```bash
redis-server
```

**Linux/Mac:**
```bash
redis-server
# Or if installed via package manager
sudo systemctl start redis
```

**Docker (alternative):**
```bash
docker run -d -p 6379:6379 redis:latest
```

### Step 2: Start FastAPI Application

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Step 3: Start Celery Worker (Optional)

For background task processing:

```bash
# Windows
celery -A app.tasks worker --loglevel=info --pool=solo

# Linux/Mac
celery -A app.tasks worker --loglevel=info
```

## 📚 API Documentation

Once the application is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Available Endpoints

#### Products (`/products`)
- `POST /products` - Create product
- `GET /products` - List products (cached)
- `GET /products/{id}` - Get product (cached + view counter)
- `PUT /products/{id}` - Update product
- `DELETE /products/{id}` - Delete product

#### Cart (`/cart`)
- `POST /cart` - Add item to cart
- `GET /cart` - Get cart contents
- `DELETE /cart/{product_id}` - Remove item
- `DELETE /cart` - Clear cart

#### Authentication (`/auth`)
- `POST /auth/otp` - Request OTP
- `POST /auth/login` - Login with OTP

#### Analytics (`/analytics`)
- `GET /analytics/leaderboard` - Top products
- `GET /analytics` - Comprehensive analytics

#### Redis Examples (`/redis`)
- `POST /redis/publish` - Publish Pub/Sub message
- `POST /redis/stream` - Add event to stream
- `GET /redis/stream/read` - Read stream events
- `POST /redis/lock/demo` - Distributed lock demo
- `POST /redis/cache/clear` - Clear cache
- `POST /redis/celery/welcome-email` - Trigger Celery task
- `GET /redis/stats` - Redis statistics
- `GET /redis/health` - Redis health check

## 🔥 Redis Features

### 1. Response Caching (String)

**Pattern**: Cache-Aside

```python
# Automatic caching in product endpoints
GET /products          # List cached for 5 minutes
GET /products/{id}     # Detail cached for 5 minutes
```

**Implementation**: `app/services.py` - `ProductService.get_product()`

### 2. Shopping Cart (Hash)

**Pattern**: Redis Hash for structured data

```python
# Cart stored as: cart:user:{user_id}
# Fields: product_id -> JSON(product_info)
```

**Implementation**: `app/services.py` - `CartService`

### 3. OTP Storage (String + TTL)

**Pattern**: Time-limited data

```python
# Key: otp:{phone_number}
# TTL: 300 seconds (5 minutes)
```

**Implementation**: `app/services.py` - `AuthService`

### 4. Rate Limiting (String + INCR)

**Pattern**: Token bucket

```python
# Key: rate_limit:{identifier}
# INCR + EXPIRE for sliding window
```

**Implementation**: `app/utils.py` - `check_rate_limit()`

### 5. View Counter (String + INCR)

**Pattern**: Atomic counters

```python
# Key: products:views:{product_id}
# INCR on each product view
```

**Implementation**: `app/services.py` - `ProductService.get_product()`

### 6. Leaderboard (Sorted Set)

**Pattern**: Ranked data

```python
# Key: products:leaderboard
# Score: view count
# Member: product_id
```

**Implementation**: `app/services.py` - `AnalyticsService.get_leaderboard()`

### 7. Redis Pub/Sub

**Pattern**: Real-time messaging

```python
POST /redis/publish
{
  "channel": "notifications",
  "message": "New order received"
}
```

**Implementation**: `app/pubsub.py` - `PubSubManager`

### 8. Redis Streams

**Pattern**: Event sourcing

```python
POST /redis/stream
{
  "event_type": "order.created",
  "data": {"order_id": 123, "total": 99.99}
}
```

**Implementation**: `app/stream.py` - `StreamManager`

### 9. Distributed Lock (SET NX EX)

**Pattern**: Mutual exclusion

```python
POST /redis/lock/demo?resource=inventory_update
# Prevents concurrent access to critical section
```

**Implementation**: `app/locks.py` - `DistributedLock`

### 10. Celery Background Tasks

**Pattern**: Asynchronous job processing

```python
POST /redis/celery/welcome-email
{
  "email": "user@example.com",
  "user_name": "John Doe"
}
```

**Implementation**: `app/tasks.py` - Celery tasks

### 11. HyperLogLog (Unique Visitors)

**Pattern**: Cardinality estimation

```python
# Key: analytics:unique_visitors
# PFADD for tracking, PFCOUNT for counting
```

**Implementation**: `app/services.py` - `AnalyticsService.track_visitor()`

### 12. Bitmap (Daily Active Users)

**Pattern**: Boolean flags

```python
# Key: analytics:logins:{date}
# SETBIT user_id 1 for each login
```

**Implementation**: `app/services.py` - `AnalyticsService.track_daily_login()`

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Client                           │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Application                     │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐               │
│  │   Routers    │  │ Dependencies │               │
│  └──────┬───────┘  └──────────────┘               │
│         │                                           │
│         ▼                                           │
│  ┌──────────────┐                                  │
│  │   Services   │  (Business Logic)                │
│  └──────┬───────┘                                  │
│         │                                           │
│    ┌────┴────┐                                     │
│    ▼         ▼                                     │
│  ┌────┐   ┌─────┐                                 │
│  │ DB │   │Redis│                                 │
│  └────┘   └─────┘                                 │
└─────────────────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns**
   - Routers handle HTTP
   - Services handle business logic
   - Models represent data

2. **Dependency Injection**
   - Database sessions
   - Redis clients
   - User authentication

3. **Type Safety**
   - Pydantic for validation
   - Type hints everywhere
   - SQLAlchemy 2.0 typed models

4. **Async First**
   - Async database operations
   - Async Redis operations
   - Non-blocking I/O

## 🎓 Learning Objectives

After exploring this project, you'll understand:

### Redis Fundamentals
- ✅ When to use each Redis data structure
- ✅ TTL and expiration strategies
- ✅ Cache invalidation patterns
- ✅ Atomic operations

### Caching Strategies
- ✅ Cache-Aside pattern
- ✅ Cache invalidation
- ✅ Cache key naming conventions
- ✅ TTL management

### Distributed Systems
- ✅ Distributed locking
- ✅ Race condition prevention
- ✅ Eventual consistency
- ✅ Event sourcing

### FastAPI Best Practices
- ✅ Router organization
- ✅ Dependency injection
- ✅ Async operations
- ✅ Error handling
- ✅ Request validation

### Production Patterns
- ✅ Background task processing
- ✅ Rate limiting
- ✅ Health checks
- ✅ Monitoring and metrics

## 🧪 API Examples

### Create Products

```bash
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "description": "High-performance laptop",
    "price": 999.99,
    "stock": 50,
    "category": "Electronics"
  }'
```

### Add to Cart

```bash
curl -X POST "http://localhost:8000/cart" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{
    "product_id": 1,
    "quantity": 2
  }'
```

### Request OTP

```bash
curl -X POST "http://localhost:8000/auth/otp" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1234567890"
  }'
```

### Get Analytics

```bash
curl -X GET "http://localhost:8000/analytics" \
  -H "X-User-Id: 1"
```

### Publish Message

```bash
curl -X POST "http://localhost:8000/redis/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "notifications",
    "message": "Test message"
  }'
```

### Check Redis Health

```bash
curl -X GET "http://localhost:8000/redis/health"
```

## 🔍 Code Quality

- ✅ PEP 8 compliant
- ✅ Type hints throughout
- ✅ Comprehensive docstrings
- ✅ Error handling
- ✅ Input validation
- ✅ Async/await best practices

## 🤝 Contributing

This is an educational project. Feel free to:
- Fork and experiment
- Add new Redis patterns
- Improve documentation
- Share your learnings

## 📝 License

This project is for educational purposes. Use freely for learning and reference.

## 🙏 Acknowledgments

Built with:
- FastAPI framework
- Redis (the amazing in-memory store)
- SQLAlchemy ORM
- Pydantic validation
- Celery task queue

---

**Happy Learning! 🚀**

For questions or suggestions, feel free to open an issue or reach out.
