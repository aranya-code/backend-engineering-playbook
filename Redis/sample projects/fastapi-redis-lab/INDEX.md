# FastAPI Redis Lab - Quick Navigation Index

> 🚀 **Jump to exactly what you need**

---

## 📖 I Want To...

### Get Started
- [ ] **First time here?** → Read [`README.md`](README.md)
- [ ] **Quick setup (5 min)?** → Read [`QUICKSTART.md`](QUICKSTART.md)
- [ ] **One-click install?** → Run `setup.bat`
- [ ] **Start the server?** → Run `start_server.bat` or `uvicorn app.main:app --reload`

### Learn Redis
- [ ] **Understand patterns?** → Read [`REDIS_PATTERNS.md`](REDIS_PATTERNS.md)
- [ ] **See implementations?** → Read `app/services.py` and `app/redis_client.py`
- [ ] **Try examples?** → Visit http://localhost:8000/docs → Redis Examples

### Understand the Code
- [ ] **See all files?** → Read [`FILE_MANIFEST.md`](FILE_MANIFEST.md)
- [ ] **Project overview?** → Read [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md)
- [ ] **Architecture?** → Read `app/main.py` and `README.md#Architecture`

### Test & Verify
- [ ] **Add sample data?** → Run `python seed_data.py seed`
- [ ] **Test all APIs?** → Run `python test_api.py`
- [ ] **Check Redis?** → Run `redis-cli` then `KEYS *`

---

## 📁 Quick File Access

### 🎯 Start Here
1. [`README.md`](README.md) - Main documentation (650 lines)
2. [`QUICKSTART.md`](QUICKSTART.md) - 5-minute setup
3. [`app/main.py`](app/main.py) - Application entry point

### 📚 Documentation
- [`README.md`](README.md) - Complete guide
- [`QUICKSTART.md`](QUICKSTART.md) - Quick start
- [`REDIS_PATTERNS.md`](REDIS_PATTERNS.md) - Pattern explanations (850 lines)
- [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md) - Project overview
- [`FILE_MANIFEST.md`](FILE_MANIFEST.md) - All files documented
- [`INDEX.md`](INDEX.md) - This file

### ⚙️ Configuration
- [`.env.example`](.env.example) - Environment template
- [`requirements.txt`](requirements.txt) - Python packages
- [`celeryconfig.py`](celeryconfig.py) - Celery settings
- [`.gitignore`](.gitignore) - Git ignore rules

### 🎯 Core Application
- [`app/main.py`](app/main.py) - FastAPI app
- [`app/config.py`](app/config.py) - Settings
- [`app/database.py`](app/database.py) - Database setup
- [`app/redis_client.py`](app/redis_client.py) - Redis client (240 lines)
- [`app/models.py`](app/models.py) - SQLAlchemy models
- [`app/schemas.py`](app/schemas.py) - Pydantic schemas
- [`app/services.py`](app/services.py) - Business logic (430 lines)
- [`app/dependencies.py`](app/dependencies.py) - FastAPI deps
- [`app/utils.py`](app/utils.py) - Utilities

### 🔄 Redis Features
- [`app/redis_client.py`](app/redis_client.py) - Helper functions
- [`app/locks.py`](app/locks.py) - Distributed locking
- [`app/pubsub.py`](app/pubsub.py) - Pub/Sub implementation
- [`app/stream.py`](app/stream.py) - Streams implementation
- [`app/tasks.py`](app/tasks.py) - Celery tasks

### 🛣️ API Routes
- [`app/routers/products.py`](app/routers/products.py) - Products CRUD
- [`app/routers/cart.py`](app/routers/cart.py) - Shopping cart
- [`app/routers/auth.py`](app/routers/auth.py) - Authentication
- [`app/routers/analytics.py`](app/routers/analytics.py) - Analytics
- [`app/routers/redis_examples.py`](app/routers/redis_examples.py) - Redis demos

### 🧪 Utilities
- [`seed_data.py`](seed_data.py) - Database seeder
- [`test_api.py`](test_api.py) - API test suite
- [`setup.bat`](setup.bat) - Setup script
- [`start_server.bat`](start_server.bat) - Start server
- [`start_celery.bat`](start_celery.bat) - Start Celery

---

## 🎓 Learning Paths

### Path 1: Quick Start (30 minutes)
```
1. QUICKSTART.md          (read: 10 min)
2. setup.bat              (run: 2 min)
3. start_server.bat       (run: 1 min)
4. http://localhost:8000/docs (explore: 15 min)
5. test_api.py            (run: 2 min)
```

### Path 2: Understand Redis (2 hours)
```
1. README.md              (read: 30 min)
2. REDIS_PATTERNS.md      (read: 45 min)
3. app/redis_client.py    (study: 20 min)
4. app/services.py        (study: 25 min)
```

### Path 3: Full Mastery (1 day)
```
1. All documentation      (read: 2 hours)
2. All source code        (study: 4 hours)
3. Modify and experiment  (code: 2 hours)
```

---

## 🔍 Find By Feature

### Caching
- Pattern: `REDIS_PATTERNS.md#1-caching-pattern`
- Code: `app/services.py` → `ProductService.get_product()`
- Helper: `app/redis_client.py` → `set_cache()`, `get_cache()`
- Endpoint: `GET /products` and `GET /products/{id}`

### Shopping Cart
- Pattern: `REDIS_PATTERNS.md#2-shopping-cart-with-hash`
- Code: `app/services.py` → `CartService`
- Helper: `app/redis_client.py` → `hash_set()`, `hash_get_all()`
- Endpoint: `POST /cart`, `GET /cart`

### OTP Authentication
- Pattern: `REDIS_PATTERNS.md#3-otp-with-ttl`
- Code: `app/services.py` → `AuthService`
- Helper: `app/redis_client.py` → `set_with_expiry()`
- Endpoint: `POST /auth/otp`, `POST /auth/login`

### Rate Limiting
- Pattern: `REDIS_PATTERNS.md#4-rate-limiting`
- Code: `app/utils.py` → `check_rate_limit()`
- Applied: All endpoints with `rate_limit` decorator

### Leaderboard
- Pattern: `REDIS_PATTERNS.md#6-leaderboard-with-sorted-set`
- Code: `app/services.py` → `AnalyticsService.get_leaderboard()`
- Helper: `app/redis_client.py` → `add_to_sorted_set()`
- Endpoint: `GET /analytics/leaderboard`

### Pub/Sub
- Pattern: `REDIS_PATTERNS.md#7-pubsub-messaging`
- Code: `app/pubsub.py` → `PubSubManager`
- Endpoint: `POST /redis/publish`

### Streams
- Pattern: `REDIS_PATTERNS.md#8-event-sourcing-with-streams`
- Code: `app/stream.py` → `StreamManager`
- Endpoint: `POST /redis/stream`, `GET /redis/stream/read`

### Distributed Lock
- Pattern: `REDIS_PATTERNS.md#9-distributed-locking`
- Code: `app/locks.py` → `DistributedLock`
- Endpoint: `POST /redis/lock/demo`

### Background Tasks
- Pattern: `REDIS_PATTERNS.md#10-celery-task-queue`
- Code: `app/tasks.py` → All task functions
- Endpoint: `POST /redis/celery/*`

### HyperLogLog
- Pattern: `REDIS_PATTERNS.md#11-unique-visitors-with-hyperloglog`
- Code: `app/services.py` → `AnalyticsService.track_visitor()`
- Endpoint: `GET /analytics`

### Bitmap
- Pattern: `REDIS_PATTERNS.md#12-daily-active-users-with-bitmap`
- Code: `app/services.py` → `AnalyticsService.track_daily_login()`
- Endpoint: `GET /analytics`

---

## 🎯 Find By Task

### Setup & Installation
```
📄 QUICKSTART.md          - Step-by-step guide
🔧 setup.bat              - Automated setup
📄 README.md#installation - Manual installation
🔧 requirements.txt       - Dependencies
📄 .env.example           - Configuration template
```

### Running the Application
```
🔧 start_server.bat       - Start FastAPI
🔧 start_celery.bat       - Start Celery
📄 README.md#running      - Manual commands
📄 QUICKSTART.md#step-7   - Verification steps
```

### Testing
```
🧪 test_api.py            - API test suite
🧪 seed_data.py           - Database seeder
📄 QUICKSTART.md#verify   - Verification tests
📄 README.md#api-examples - cURL examples
```

### Understanding Code
```
📄 PROJECT_SUMMARY.md     - High-level overview
📄 FILE_MANIFEST.md       - All files explained
📄 README.md#architecture - Architecture diagram
💻 app/main.py            - Application structure
```

### Learning Redis
```
📄 REDIS_PATTERNS.md      - All 12 patterns
💻 app/redis_client.py    - Helper functions
💻 app/services.py        - Real implementations
💻 app/routers/redis_examples.py - Demonstrations
```

### Debugging
```
📄 QUICKSTART.md#troubleshooting - Common issues
💻 app/main.py            - Exception handlers
🔧 .env.example           - Configuration
📄 README.md              - Full documentation
```

---

## 🌐 API Endpoints Quick Reference

### Health & Info
- `GET /` - API information
- `GET /health` - App health
- `GET /redis/health` - Redis health
- `GET /redis/stats` - Redis statistics

### Products (Caching)
- `POST /products` - Create
- `GET /products` - List (cached)
- `GET /products/{id}` - Get (cached + tracked)
- `PUT /products/{id}` - Update
- `DELETE /products/{id}` - Delete

### Cart (Hash)
- `POST /cart` - Add item
- `GET /cart` - Get cart
- `DELETE /cart/{product_id}` - Remove item
- `DELETE /cart` - Clear cart

### Auth (OTP + TTL)
- `POST /auth/otp` - Request OTP
- `POST /auth/login` - Login with OTP

### Analytics
- `GET /analytics/leaderboard` - Top products
- `GET /analytics` - Full analytics

### Redis Examples
- `POST /redis/publish` - Pub/Sub
- `POST /redis/stream` - Add event
- `GET /redis/stream/read` - Read events
- `POST /redis/lock/demo` - Lock demo
- `POST /redis/cache/clear` - Clear cache
- `POST /redis/celery/*` - Background tasks

---

## 📊 Project Stats

| Metric | Value |
|--------|-------|
| Total Files | 25+ |
| Lines of Code | 3,500+ |
| Lines of Docs | 2,500+ |
| Python Files | 18 |
| Documentation | 6 files |
| Redis Patterns | 12 |
| API Endpoints | 20+ |
| Celery Tasks | 8 |
| Sample Products | 20 |
| Setup Time | 5 minutes |

---

## 🔗 External Resources

### Official Docs
- [FastAPI](https://fastapi.tiangolo.com/) - Framework
- [Redis](https://redis.io/docs/) - Data store
- [Celery](https://docs.celeryq.dev/) - Task queue
- [SQLAlchemy](https://docs.sqlalchemy.org/) - ORM
- [Pydantic](https://docs.pydantic.dev/) - Validation

### Tools
- [Redis CLI](https://redis.io/docs/ui/cli/) - Command line
- [Swagger UI](http://localhost:8000/docs) - API docs (when running)
- [ReDoc](http://localhost:8000/redoc) - API docs (when running)

---

## 💡 Quick Commands

### Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python seed_data.py seed
```

### Run
```bash
uvicorn app.main:app --reload
celery -A app.tasks worker --loglevel=info --pool=solo
```

### Test
```bash
python test_api.py
python seed_data.py stats
redis-cli KEYS *
```

### Development
```bash
# Check Python
python --version

# Check Redis
redis-cli ping

# List packages
pip list

# Format code
black app/

# Type check
mypy app/
```

---

## 🎯 Choose Your Adventure

### I'm a beginner
→ Start: `QUICKSTART.md`  
→ Then: `README.md`  
→ Finally: Try API at `/docs`

### I know FastAPI
→ Start: `REDIS_PATTERNS.md`  
→ Then: `app/redis_client.py`  
→ Finally: `app/services.py`

### I know Redis
→ Start: `app/main.py`  
→ Then: `app/routers/`  
→ Finally: Add new features

### I want to extend this
→ Start: `PROJECT_SUMMARY.md`  
→ Then: Read all code  
→ Finally: Fork and modify

### I'm interviewing
→ Start: `REDIS_PATTERNS.md`  
→ Then: `app/services.py`  
→ Finally: Explain patterns

---

## ✅ Completion Checklist

### Setup Phase
- [ ] Read README.md
- [ ] Run setup.bat
- [ ] Verify Redis connection
- [ ] Access http://localhost:8000/docs

### Learning Phase
- [ ] Read REDIS_PATTERNS.md
- [ ] Try all 12 patterns
- [ ] Read services.py
- [ ] Run test_api.py

### Mastery Phase
- [ ] Understand all files
- [ ] Modify a feature
- [ ] Add a new pattern
- [ ] Deploy to production

---

## 🚀 Next Steps

After completing this project:

1. ✅ **Understand**: All 12 Redis patterns
2. ✅ **Apply**: In your own projects
3. ✅ **Extend**: Add new features
4. ✅ **Share**: Help others learn
5. ✅ **Build**: Production applications

---

## 📞 Need Help?

1. **Setup issues?** → Read `QUICKSTART.md#troubleshooting`
2. **Redis errors?** → Check `redis-cli ping`
3. **Code questions?** → Read `FILE_MANIFEST.md`
4. **Pattern questions?** → Read `REDIS_PATTERNS.md`

---

**Navigate to what you need, learn at your pace, build with confidence!** 🎯

Last Updated: 2024
Version: 1.0.0
