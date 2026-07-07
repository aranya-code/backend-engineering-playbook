# TTL and DNS Caching

TTL (Time To Live) controls how long a DNS response may be cached by resolvers and clients before they're required to re-query.

## Low TTL (e.g., 60 seconds)

**Benefits:** faster propagation of changes, faster effective failover time.
**Costs:** more DNS queries hitting Route 53 (billing impact), more load on authoritative infrastructure.

## High TTL (e.g., 86400 seconds / 24 hours)

**Benefits:** fewer queries, faster responses for end users (served from cache), lower query cost.
**Costs:** slower propagation — a change made now may not be visible to some users for up to the full TTL duration.

## The Propagation Reality

"DNS propagation" is often misunderstood as something that happens on Route 53's side. In reality, once a record change is made, it is authoritative and correct **immediately** at Route 53's nameservers. What actually takes time is every downstream cache (resolvers, OS caches, browsers) honoring the *old* TTL until it naturally expires — Route 53 has no way to force a remote cache to drop a value early.

## TTL Strategy for Migrations

A common, deliberate practice before a planned cutover (e.g., migrating a domain to new infrastructure):

1. Lower the TTL well in advance (e.g., a day before) — this doesn't help the current change, it ensures the *next* change propagates fast
2. Make the actual cutover change
3. Raise the TTL back to normal once the change is confirmed stable

## Negative Caching TTL

Separate from record TTL, the SOA record's minimum/negative-caching value controls how long resolvers cache an NXDOMAIN (nonexistent) response. This matters when you're adding a *new* record — if it was queried and failed recently, some resolvers may hold onto that failure for longer than you'd expect.

## Senior-Level Considerations

- TTL is a client-side/resolver-side contract, not a Route 53 guarantee — some resolvers ignore or cap TTLs (a small minority over-cache well past the stated TTL, which is an occasional real-world nuisance during migrations)
- Alias records to AWS resources don't expose a configurable TTL in the same way — Route 53 manages effective caching behavior for those internally
