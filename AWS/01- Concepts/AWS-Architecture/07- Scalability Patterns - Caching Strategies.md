# Scalability Patterns — Caching Strategies

Caching is one of the highest-leverage architectural decisions available — it can cut latency and backend load simultaneously — but each caching layer has its own invalidation problem, and "cache invalidation is hard" is a cliché precisely because it's true.

## Caching Layers on AWS

| Layer | AWS Service | Caches |
|---|---|---|
| CDN / edge | CloudFront | Static assets, cacheable API responses, close to the end user |
| Application / in-memory | ElastiCache (Redis/Memcached) | Frequently accessed data, session state, computed results |
| Database | RDS/Aurora query cache, DAX (for DynamoDB) | Query results, reducing direct database load |
| Client-side | Browser cache, mobile app cache | Reduces requests from reaching AWS at all |

## Cache-Aside (Lazy Loading)

The application checks the cache first; on a miss, it reads from the database, then populates the cache for next time.

```text
Read request → Check cache → Miss → Read DB → Write to cache → Return
```

**Trade-off:** simple and only caches what's actually requested, but the first request for any given key always pays the full database latency (a "cold" cache miss).

## Write-Through Cache

Every write goes to the cache and the database together, so the cache is never stale relative to the database.

**Trade-off:** every write has added latency (writing to two places), and data that's written but never read still consumes cache space unnecessarily.

## Write-Behind (Write-Back) Cache

Writes go to the cache immediately and are asynchronously flushed to the database later.

**Trade-off:** fastest write path, but introduces a real risk of data loss if the cache fails before the flush completes — appropriate only when that risk is acceptable for the specific data.

## Cache Invalidation Strategies

- **TTL-based expiration** — simplest, but means stale data can be served for up to the TTL duration
- **Explicit invalidation on write** — more accurate, but requires every write path to remember to invalidate, and missed invalidation paths are a common source of stale-data bugs
- **Versioned/keyed cache entries** — encoding a version or timestamp into the cache key so old versions simply stop being requested rather than needing explicit deletion

## Senior-Level Considerations

- A cache is an availability risk if the application can't function at all when it's unavailable — design for cache failures to degrade gracefully (fall back to the database, perhaps with added latency) rather than fail the request entirely
- "Thundering herd" applies to caches too — if a hot key expires and many concurrent requests all miss simultaneously, they can all hit the database at once; request coalescing (only one request actually queries the DB, others wait for that result) mitigates this
- Caching data that changes very frequently, or is rarely read more than once, often isn't worth the invalidation complexity — cache what's read often relative to how often it changes
