# Amazon ElastiCache

## Definition

Fully managed in-memory caching service.

Supports:
- Redis
- Memcached

---

## Benefits

- Ultra-low latency
- Reduces DB load
- Faster applications
- Improves scalability

---

## Cache Flow

1. App checks cache
2. Cache hit -> return data
3. Cache miss -> fetch from DB
4. Store in cache

---

## Important Note

ElastiCache usually requires application code changes.
