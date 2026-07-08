# Cache-Aside vs Write-Through vs Write-Back

Three caching strategies that fundamentally change how your application handles data freshness, write latency, and durability. Pick the wrong one and you either serve stale data, tank write performance, or lose data entirely.

---

## Cache-Aside (Lazy Loading)

The application owns all cache logic. Nothing happens automatically.

```
READ PATH:
┌─────────┐    1. GET key    ┌─────────┐
│   App   │ ───────────────► │  Cache  │
│ Server  │ ◄─────────────── │(Redis)  │
└────┬────┘    2. MISS       └─────────┘
     │
     │  3. SELECT * FROM ...
     ▼
┌─────────┐
│   DB    │
│ (RDS)   │
└────┬────┘
     │  4. Result
     ▼
┌─────────┐    5. SET key    ┌─────────┐
│   App   │ ───────────────► │  Cache  │
│ Server  │                  │(Redis)  │
└─────────┘                  └─────────┘

WRITE PATH:
┌─────────┐    1. UPDATE     ┌─────────┐
│   App   │ ───────────────► │   DB    │
│ Server  │                  │ (RDS)   │
└────┬────┘                  └─────────┘
     │
     │  2. DELETE key (invalidate)
     ▼
┌─────────┐
│  Cache  │
│(Redis)  │
└─────────┘
```

**How it works:** App checks cache first. On miss, reads from DB, then populates cache. Writes go directly to DB and invalidate the cache entry. The next read triggers a fresh load.

**Why invalidate, not update on write?** Updating the cache on write creates race conditions when two concurrent writes hit different orders in cache vs DB. Delete-then-reload is simpler and safer.

---

## Write-Through

Every write goes to both cache and DB before returning success to the caller.

```
WRITE PATH:
┌─────────┐    1. Write     ┌─────────┐    2. Write     ┌─────────┐
│   App   │ ──────────────► │  Cache  │ ──────────────► │   DB    │
│ Server  │ ◄────────────── │(Redis)  │ ◄────────────── │ (RDS)   │
└─────────┘    4. ACK       └─────────┘    3. ACK       └─────────┘

READ PATH:
┌─────────┐    1. GET key    ┌─────────┐
│   App   │ ───────────────► │  Cache  │
│ Server  │ ◄─────────────── │(Redis)  │
└─────────┘    2. HIT        └─────────┘
               (always fresh)
```

**How it works:** The caching layer intercepts every write, persists to both cache and DB synchronously. Reads always hit cache with guaranteed-fresh data. No stale reads — ever.

**The cost:** Every write pays double latency (cache + DB round trip). If you write 10,000 records/sec but only read 500/sec, you're caching 9,500 records nobody ever reads.

---

## Write-Back (Write-Behind)

Writes land in cache only. A background process asynchronously flushes dirty entries to DB.

```
WRITE PATH:
┌─────────┐    1. Write     ┌─────────┐
│   App   │ ──────────────► │  Cache  │    (return immediately)
│ Server  │ ◄────────────── │(Redis)  │
└─────────┘    2. ACK       └────┬────┘
                                  │
                    3. Async flush (batched)
                                  ▼
                            ┌─────────┐
                            │   DB    │
                            │ (RDS)   │
                            └─────────┘
```

**How it works:** App writes to cache and gets immediate acknowledgment. A background worker flushes dirty cache entries to DB on a timer or batch threshold. Writes are coalesced — if the same key is updated 50 times in 1 second, only the final value hits the DB.

**The risk:** If the cache node dies before flushing, those writes are gone. Redis with AOF persistence mitigates this partially, but you're still trading durability for speed.

---

## Comparison Table

| Dimension              | Cache-Aside            | Write-Through           | Write-Back              |
|------------------------|------------------------|-------------------------|-------------------------|
| **Read latency (hit)** | Low                    | Low                     | Low                     |
| **Read latency (miss)**| High (DB + cache set)  | N/A (always populated)  | N/A (always populated)  |
| **Write latency**      | Low (DB only)          | High (cache + DB sync)  | Very low (cache only)   |
| **Data freshness**     | Eventual (stale until invalidated) | Always fresh | Always fresh in cache   |
| **Cache miss penalty** | Full DB read + cache write | Minimal (cold start only) | Minimal (cold start only) |
| **Data loss risk**     | None                   | None                    | **Yes — unflushed writes** |
| **Write amplification**| None                   | High (cache every write)| Low (coalesced writes)  |
| **Implementation**     | Simple (app-level)     | Moderate (middleware)   | Complex (flush logic)   |
| **Cache pollution**    | Low (only read data cached) | High (all written data) | High (all written data) |
| **Consistency model**  | Eventual               | Strong                  | Eventual                |
| **Best for**           | Read-heavy, tolerates staleness | Read-heavy, needs freshness | Write-heavy, tolerates risk |

---

## Decision Matrix

**Use Cache-Aside when:**
- Read-heavy workload (>80% reads)
- You can tolerate brief staleness (TTL-based expiry is acceptable)
- You want simple implementation with no caching infrastructure dependency on writes
- Example: Product catalog, user profiles, configuration lookups

**Use Write-Through when:**
- Data freshness is non-negotiable (financial dashboards, inventory counts)
- Read-to-write ratio is high enough to justify caching every write
- You need strong consistency between cache and DB
- Example: Session stores, real-time leaderboards, pricing engines

**Use Write-Back when:**
- Write-heavy workload where latency matters more than durability
- You can tolerate the risk of losing recent writes on cache failure
- Writes to the same key are frequent (coalescing saves DB load)
- Example: Analytics counters, IoT sensor aggregation, logging pipelines

---

## Combining Patterns

Production systems rarely use a single pattern in isolation.

**Cache-Aside + Write-Through:** Use write-through for critical paths (inventory, payments) and cache-aside for everything else (product details, recommendations). This gives you freshness where it matters without over-caching low-value data.

**Cache-Aside + Write-Back:** Use write-back for high-frequency counters (page views, likes) and cache-aside for the read path of less volatile data. Accept that counter accuracy lags by the flush interval.

**Write-Through + TTL:** Even with write-through, set a TTL as a safety net. If a bug bypasses the cache update path, the TTL ensures eventual correction rather than permanently stale data.

---

## Interview-Ready Explanation

> "Cache-aside puts the application in full control — it checks cache, falls back to DB on miss, and populates cache for next time. Writes bypass cache and go straight to DB; you invalidate the cache entry so the next read fetches fresh data. It's simple and avoids caching data that's never read.
>
> Write-through guarantees cache and DB are always in sync by writing to both on every operation. You pay higher write latency but never serve stale data. It's ideal when freshness is critical and the read-to-write ratio justifies the overhead.
>
> Write-back is the opposite trade — writes land in cache only and flush to DB asynchronously. You get the lowest write latency and natural write coalescing, but if the cache node crashes before flushing, those writes are lost. It's appropriate for workloads like analytics counters where speed matters more than perfect durability."

---

## Key Takeaways

1. **Cache-aside is your default.** Start here unless you have a specific reason not to. It's simple, well-understood, and avoids cache pollution.
2. **Write-through eliminates staleness** but doubles write latency. Only worth it when read freshness is a hard requirement.
3. **Write-back is a durability gamble.** Lowest latency, but you must accept the data loss window. Size that window carefully.
4. **Invalidate, don't update** in cache-aside. Cache updates on write create subtle race conditions.
5. **Combine patterns** based on data criticality. Not every table deserves the same caching strategy.
6. **TTL is your safety net** regardless of pattern. Always set one.
7. **Monitor cache hit ratio.** Below 80%? Your caching strategy isn't working — re-evaluate key design and TTL values.
