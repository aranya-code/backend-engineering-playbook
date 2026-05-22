# Caching Strategies

## Cache Aside (Lazy Loading)

Application loads data into cache only when needed.

### Steps
1. Check cache
2. Cache miss
3. Read from DB
4. Store in cache

---

## Write Through

Writes data to:
- Database
- Cache

at the same time.

---

## TTL (Time To Live)

Controls how long cache remains valid.

---

## Best Practice

Cache only frequently accessed and expensive-to-fetch data.
