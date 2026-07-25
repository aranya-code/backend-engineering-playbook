# Quick Start Guide 🚀

Get FastAPI Redis Lab up and running in 5 minutes!

## Prerequisites Check

```bash
# Check Python version (need 3.12+)
python --version

# Check if Redis is installed
redis-cli --version

# Check if pip is available
pip --version
```

## Step-by-Step Setup

### 1. Navigate to Project

```bash
cd "D:\backend-engineering-playbook\Redis\sample projects\fastapi-redis-lab"
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Create Environment File

```bash
copy .env.example .env
```

### 6. Start Redis Server

**Option A: Windows Service**
```bash
redis-server
```

**Option B: Docker**
```bash
docker run -d -p 6379:6379 --name redis-lab redis:latest
```

**Option C: WSL (Windows Subsystem for Linux)**
```bash
wsl
sudo service redis-server start
```

### 7. Start FastAPI Application

```bash
uvicorn app.main:app --reload
```

You should see:
```
==================================================
Starting FastAPI Redis Lab v1.0.0
==================================================
Initializing database...
✓ Database initialized
Testing Redis connection...
✓ Redis connected
==================================================
Application started successfully!
API Documentation: http://localhost:8000/docs
==================================================
```

## Verify Installation

### Test 1: Check API Health

Open browser: http://localhost:8000

You should see:
```json
{
  "name": "FastAPI Redis Lab",
  "version": "1.0.0",
  "description": "FastAPI Redis Lab - Redis integration examples"
}
```

### Test 2: Check Redis Connection

Open browser: http://localhost:8000/redis/health

You should see:
```json
{
  "status": "healthy",
  "redis": "connected",
  "message": "Redis is responding to PING"
}
```

### Test 3: Open API Documentation

Open browser: http://localhost:8000/docs

You should see interactive Swagger UI documentation.

## First API Calls

### 1. Create a Product

```bash
curl -X POST "http://localhost:8000/products" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Laptop\",\"description\":\"Gaming Laptop\",\"price\":1299.99,\"stock\":10,\"category\":\"Electronics\"}"
```

### 2. Get Products (Cached)

```bash
curl http://localhost:8000/products
```

### 3. Add to Cart

```bash
curl -X POST "http://localhost:8000/cart" ^
  -H "Content-Type: application/json" ^
  -H "X-User-Id: 1" ^
  -d "{\"product_id\":1,\"quantity\":2}"
```

### 4. Get Cart

```bash
curl -X GET "http://localhost:8000/cart" ^
  -H "X-User-Id: 1"
```

### 5. Request OTP

```bash
curl -X POST "http://localhost:8000/auth/otp" ^
  -H "Content-Type: application/json" ^
  -d "{\"phone\":\"+1234567890\"}"
```

### 6. Check Analytics

```bash
curl -X GET "http://localhost:8000/analytics" ^
  -H "X-User-Id: 1"
```

## Optional: Start Celery Worker

Open a **new terminal** window:

```bash
cd "D:\backend-engineering-playbook\Redis\sample projects\fastapi-redis-lab"
venv\Scripts\activate
celery -A app.tasks worker --loglevel=info --pool=solo
```

Then test Celery:

```bash
curl -X POST "http://localhost:8000/redis/celery/welcome-email?email=test@example.com&user_name=John"
```

## Troubleshooting

### Issue: Redis Connection Failed

**Solution 1:** Make sure Redis is running
```bash
redis-cli ping
# Should return: PONG
```

**Solution 2:** Check Redis port
```bash
redis-cli -p 6379 ping
```

**Solution 3:** Restart Redis
```bash
# Stop
redis-cli shutdown

# Start
redis-server
```

### Issue: Module Not Found

**Solution:** Reinstall dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Issue: Port Already in Use

**Solution:** Use different port
```bash
uvicorn app.main:app --reload --port 8001
```

### Issue: Database Error

**Solution:** Delete and recreate database
```bash
del db.sqlite3
# Restart the application - it will recreate automatically
```

## Next Steps

1. ✅ Explore API documentation at http://localhost:8000/docs
2. ✅ Try all the endpoints
3. ✅ Check Redis data using Redis CLI:
   ```bash
   redis-cli
   KEYS *
   GET products:detail:1
   HGETALL cart:user:1
   ```
4. ✅ Read the main README.md for detailed explanations
5. ✅ Explore the code in `app/` directory

## Useful Commands

### Redis CLI

```bash
# Connect to Redis
redis-cli

# List all keys
KEYS *

# Get string value
GET key_name

# Get hash
HGETALL hash_key

# Get sorted set
ZRANGE leaderboard 0 -1 WITHSCORES

# Monitor all commands
MONITOR

# Get server info
INFO
```

### Development

```bash
# Run with auto-reload
uvicorn app.main:app --reload

# Run on different port
uvicorn app.main:app --reload --port 8001

# Run with specific host
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Project URLs

- **API Root**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Redis Health**: http://localhost:8000/redis/health

---

**You're all set! Start exploring! 🎉**
