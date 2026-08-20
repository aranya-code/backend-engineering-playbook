# 06- Edge Computing Questions

## Overview

CloudFront edge computing is the execution of request-processing logic at or near CloudFront's edge locations rather than exclusively at the centralized origin.

The primary AWS mechanisms are:

- **CloudFront Functions** — lightweight JavaScript execution for high-volume, low-latency viewer request and viewer response processing.
- **Lambda@Edge** — AWS Lambda functions associated with CloudFront events and executed in AWS edge infrastructure for more advanced request and response processing.

The architectural goal is to move suitable computation closer to users:

```text
                         Global Users
                    ┌──────┬──────┬──────┐
                    ▼      ▼      ▼      ▼
                 Edge A  Edge B  Edge C  Edge D
                    │      │      │      │
                    └──────┴──────┬───────┘
                                   │
                              Origin Region
                                   │
                          ┌────────┴────────┐
                          │ Django/FastAPI  │
                          │ S3 / ALB / APIs │
                          └─────────────────┘
```

For backend engineers, edge computing matters because it changes where decisions are made in the request lifecycle. Authentication-related routing, redirects, URL normalization, header manipulation, cache-oriented request transformation, and lightweight personalization can sometimes be performed before traffic reaches the origin.

The important engineering question is not simply **"Can this run at the edge?"** but:

> **"Is this computation suitable for distributed execution under CloudFront's execution constraints?"**

---

## CloudFront Edge Computing Models

| Capability | CloudFront Functions | Lambda@Edge |
|---|---|---|
| Runtime | JavaScript | Node.js / Python |
| Execution model | Lightweight edge function | Lambda execution at CloudFront edge |
| Startup characteristics | Very low overhead | Higher overhead |
| Resource model | Highly constrained | More capable |
| Viewer request | Yes | Yes |
| Viewer response | Yes | Yes |
| Origin request | No | Yes |
| Origin response | No | Yes |
| Request transformation | Excellent | Excellent |
| Complex application logic | Limited | Better suited |
| External network access | Not intended for arbitrary external calls | More capable, subject to Lambda@Edge constraints |
| Typical use | Headers, redirects, normalization, lightweight routing | Advanced routing, origin manipulation, response processing |
| Deployment model | CloudFront Function association | Lambda version associated with CloudFront |
| Best for | Very lightweight edge logic | More advanced edge workloads |

The exact supported runtime features, limits, event triggers, and deployment restrictions should be checked against current AWS documentation before designing a production workload.

---

## What Is Edge Computing?

Traditional backend execution often looks like:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Origin
  │
  ▼
Django/FastAPI
  │
  ▼
Database / Redis / Other services
```

With edge computing:

```text
Client
  │
  ▼
CloudFront Edge
  │
  ├── Edge logic
  │
  ├── Redirect
  │
  ├── Header transformation
  │
  ├── Request normalization
  │
  └── Routing decision
  │
  ▼
Origin
```

The purpose is to process suitable requests before they travel across the network to the centralized backend.

---

## Why Execute Logic at the Edge?

The biggest reason is **latency reduction**.

Suppose users are distributed globally while the application runs in one AWS Region:

```text
User in India ───────────────► US Origin
User in Europe ──────────────► US Origin
User in Australia ───────────► US Origin
```

Some request processing can instead happen at a nearby CloudFront edge location:

```text
User in India
      │
      ▼
Nearby CloudFront Edge
      │
      ├── Normalize request
      ├── Redirect
      ├── Add headers
      └── Route/cache
      │
      ▼
Origin only when necessary
```

This can reduce:

- Round trips to the origin.
- Origin request volume.
- Application-server work.
- Latency for edge-resolvable operations.

---

## CloudFront Functions

### What Is CloudFront Functions?

CloudFront Functions is a lightweight serverless execution environment designed for high-scale CloudFront request and response manipulation.

It is particularly suitable for operations such as:

- URL normalization.
- Redirects.
- Header manipulation.
- Cookie inspection.
- Simple request routing.
- Cache-related request transformations.
- Lightweight access decisions.

The function executes as part of the CloudFront request lifecycle.

---

## CloudFront Functions Request Lifecycle

A simplified viewer-request flow is:

```mermaid
sequenceDiagram
    participant C as Client
    participant CF as CloudFront Edge
    participant F as CloudFront Function
    participant O as Origin

    C->>CF: HTTP request
    CF->>F: Viewer request
    F->>F: Transform / inspect request
    F-->>CF: Modified request
    CF->>CF: Cache lookup

    alt Cache hit
        CF-->>C: Cached response
    else Cache miss
        CF->>O: Origin request
        O-->>CF: Response
        CF-->>C: Response
    end
```

The key architectural point is that edge logic can influence what CloudFront does with the request before the origin is contacted.

---

## CloudFront Function Example

A common use case is redirecting HTTP requests or normalizing URLs.

For example:

```javascript
function handler(event) {
    var request = event.request;

    if (request.uri.endsWith("/")) {
        request.uri = request.uri.slice(0, -1);
    }

    return request;
}
```

The function is intentionally small.

Edge functions should generally avoid becoming miniature backend applications.

---

## URL Normalization

Different URLs may represent the same logical resource:

```text
/products/123
/products/123/
/products/123?source=homepage
```

Poor normalization can increase cache fragmentation.

An edge function can normalize requests before cache processing when the transformation is safe.

For example:

```text
Incoming:
GET /products/123/

             │
             ▼

CloudFront Function

             │
             ▼

Normalized:
GET /products/123
```

This can improve cache consistency.

However, normalization must preserve application semantics. Removing or rewriting path components without understanding origin routing can create incorrect responses.

---

## Header Manipulation

CloudFront edge functions can inspect or modify request and response headers.

Common use cases include:

- Adding security-related headers.
- Normalizing request headers.
- Routing based on headers.
- Removing unnecessary headers.
- Adding diagnostic metadata.
- Supporting cache-oriented transformations.

Example:

```javascript
function handler(event) {
    var response = event.response;

    response.headers["x-content-type-options"] = {
        value: "nosniff"
    };

    return response;
}
```

Security headers should still be designed consistently across the entire application architecture rather than being added randomly at the CDN layer.

---

## Redirects at the Edge

Redirects are an excellent edge-computing use case because the origin does not need to participate.

For example:

```text
GET /old-product
        │
        ▼
CloudFront
        │
        ▼
Edge Function
        │
        ▼
301 /products/new-product
```

This avoids:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Origin
  │
  ▼
Application
  │
  ▼
301 response
```

The edge can generate the redirect directly.

---

## When Should Redirects Run at the Edge?

Use edge redirects when:

- The mapping is deterministic.
- The decision does not require database state.
- The redirect is globally applicable.
- Low latency is valuable.
- The origin does not need to participate.

Do not move redirects to the edge when the destination depends on complex user state that only the backend can determine.

---

## Lambda@Edge

### What Is Lambda@Edge?

Lambda@Edge allows Lambda functions to execute in response to CloudFront events in AWS edge infrastructure.

It is intended for more advanced request and response processing than CloudFront Functions.

A simplified lifecycle is:

```text
Viewer Request
      │
      ▼
CloudFront
      │
      ├── Viewer Request
      │
      ├── Cache Lookup
      │
      ├── Origin Request
      │
      ├── Origin Response
      │
      └── Viewer Response
```

Lambda@Edge can participate in several of these stages.

---

## Lambda@Edge Event Types

The major CloudFront event points are:

| Event | Approximate location in lifecycle | Typical use |
|---|---|---|
| Viewer Request | Before cache lookup | Authentication/routing/transformation |
| Viewer Response | Before response reaches viewer | Response manipulation |
| Origin Request | Before request reaches origin | Dynamic origin selection |
| Origin Response | After origin response | Response transformation |

The exact capabilities and restrictions differ by event type.

---

## Viewer Request vs Origin Request

This distinction is frequently tested in interviews.

### Viewer Request

Runs for requests coming from viewers.

Conceptually:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Viewer Request Function
  │
  ▼
Cache processing
```

It is useful when the logic should run before CloudFront evaluates the request against its cache.

### Origin Request

Runs when CloudFront is preparing to contact the origin.

Conceptually:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Cache lookup
  │
  └── Cache miss
          │
          ▼
   Origin Request
          │
          ▼
       Origin
```

This distinction matters because origin-request logic is associated with the path to the origin rather than every viewer request.

---

## Viewer Response vs Origin Response

These events also occur at different points.

### Viewer Response

The function can modify the response before it is returned to the viewer.

```text
Origin / Cache
      │
      ▼
CloudFront
      │
      ▼
Viewer Response
      │
      ▼
Client
```

### Origin Response

The function processes the response after CloudFront receives it from the origin.

```text
Origin
  │
  ▼
Origin Response
  │
  ▼
CloudFront
  │
  ▼
Client
```

Understanding the lifecycle is more important than memorizing event names.

---

## Choosing Between CloudFront Functions and Lambda@Edge

A practical decision process is:

```text
Does the logic need edge execution?
          │
          ├── No ──► Keep it in application/origin
          │
          ▼
Is it simple and lightweight?
          │
          ├── Yes ──► CloudFront Functions
          │
          ▼
Does it require advanced processing?
          │
          └─────────► Lambda@Edge
```

The exact decision should also consider runtime support, execution limits, operational complexity, and event requirements.

---

## CloudFront Functions vs Lambda@Edge

| Requirement | CloudFront Functions | Lambda@Edge |
|---|---:|---:|
| Simple URL rewrite | Excellent | Possible |
| Redirect | Excellent | Possible |
| Header manipulation | Excellent | Possible |
| Cookie inspection | Excellent | Possible |
| Lightweight routing | Excellent | Excellent |
| Origin selection | No | Yes |
| Origin request processing | No | Yes |
| Complex Python logic | No | Yes |
| More advanced processing | Limited | Better |
| Minimal execution overhead | Excellent | Lower than origin but more capable |
| High-volume lightweight processing | Excellent | Possible |
| Complex backend integration | Poor fit | Better, but still constrained |

---

## Edge Computing and Django/FastAPI

Edge computing should complement the backend rather than replace it.

A strong architecture is:

```text
                    Internet
                       │
                       ▼
                  CloudFront
                       │
              ┌────────┴─────────┐
              │ Edge Logic       │
              │                  │
              │ Redirects        │
              │ Normalization    │
              │ Headers          │
              │ Lightweight      │
              │ Routing          │
              └────────┬─────────┘
                       │
                       ▼
                 Nginx / ALB
                       │
                       ▼
                Django/FastAPI
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      PostgreSQL     Redis        Kafka
```

The edge handles globally distributed, lightweight concerns.

The backend handles business logic.

---

## What Should Stay in Django or FastAPI?

Keep logic at the origin when it requires:

- Database queries.
- Complex authorization.
- Transaction management.
- Long-running processing.
- PostgreSQL access.
- Redis state.
- Kafka interaction.
- Celery workflows.
- Complex domain logic.
- External service orchestration.
- Large application dependencies.

For example:

```text
GET /orders/123
        │
        ▼
CloudFront
        │
        ▼
Django/FastAPI
        │
        ├── PostgreSQL
        ├── Redis
        └── Payment service
```

Moving this business logic to the edge usually increases architectural complexity without providing a meaningful benefit.

---

## Edge Authentication

Authentication at the edge is possible for certain architectures, but it should be approached carefully.

For example, an edge function might inspect a token or cookie and make a lightweight decision.

However, complex authentication workflows often belong in the application or a dedicated identity layer.

A useful separation is:

```text
Edge
│
├── Lightweight request validation
├── Routing
└── Early rejection
       │
       ▼
Application
│
├── Authentication
├── Authorization
├── Business rules
└── Database state
```

Do not turn a CloudFront Function into a complete identity provider.

---

## JWT Processing at the Edge

A lightweight edge function may inspect JWT-related information in architectures where the runtime and security model support the required cryptographic operations.

However, several questions must be answered before doing this:

- Where is the signing key stored?
- Can the edge runtime securely access it?
- Which algorithms are supported?
- How are keys rotated?
- How are revoked tokens handled?
- What happens when identity state changes?
- How are clock differences handled?

For many applications, token verification at the API gateway or application layer is simpler and easier to operate.

Edge JWT validation is an optimization and architectural choice, not a default requirement.

---

## Dynamic Origin Selection

One of Lambda@Edge's more advanced use cases is selecting an origin dynamically.

For example:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Edge logic
  │
  ├── Region = US ──► US origin
  ├── Region = EU ──► EU origin
  └── Region = AP ──► AP origin
```

This can be useful for:

- Multi-region architectures.
- Tenant-specific origins.
- Migration strategies.
- Region-aware content delivery.

However, dynamic origin selection increases operational complexity and should not be introduced merely because it is technically possible.

---

## Multi-Region Backend Example

Consider an API platform deployed in three regions:

```text
                    CloudFront
                        │
                 Edge routing logic
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
      US API          EU API          AP API
        │               │               │
     Database        Database        Database
```

The edge layer can make routing decisions based on supported request attributes or deployment architecture.

A senior engineer must also consider:

- Data consistency.
- Session state.
- Database replication.
- Failover.
- Regional outages.
- Authentication state.
- Cache consistency.

Routing users closer to an origin is not automatically equivalent to a reliable multi-region architecture.

---

## Edge Personalization

Personalization can be performed at the edge when the required decision is lightweight.

For example:

```text
Cookie: language=en
        │
        ▼
CloudFront edge
        │
        ├── /en/*
        └── /fr/*
```

This can reduce origin requests for simple routing decisions.

However, personalization based on rapidly changing or highly private application state should generally remain in the application.

---

## Edge Computing and Cache Keys

Edge logic often interacts with cache behavior.

Suppose the application supports:

```text
Accept-Language: en
Accept-Language: fr
```

If the response differs by language, the cache architecture must account for that variation.

Conceptually:

```text
Request
   │
   ▼
Edge normalization
   │
   ▼
Cache key
   │
   ├── English representation
   └── French representation
```

Incorrect cache-key design can cause:

- Cache fragmentation.
- Low cache hit ratios.
- Incorrect content delivery.
- Cross-user data exposure.

The cache key must represent every request attribute that materially changes the cached representation.

---

## Edge Computing and Security

Edge logic expands the security boundary.

Important considerations include:

### Minimize Trust

Do not put high-value secrets into edge code unnecessarily.

### Avoid Hard-Coded Credentials

Edge code should not contain:

```javascript
var apiKey = "super-secret-key";
```

Secrets in distributed execution environments create unnecessary exposure risk.

### Validate Inputs

Headers, cookies, paths, and query strings are attacker-controlled inputs.

### Keep Logic Small

Smaller functions are easier to audit and reason about.

### Avoid Sensitive Data in Logs

Do not log:

- Authorization tokens.
- Session cookies.
- Signed URLs.
- Personal information.

---

## Edge Computing and Performance

Edge execution can improve latency when it prevents unnecessary origin requests.

For example:

```text
Without edge redirect:

Client
  │
  ▼
CloudFront
  │
  ▼
Origin
  │
  ▼
Redirect
  │
  ▼
Client
```

With edge redirect:

```text
Client
  │
  ▼
CloudFront Edge
  │
  ▼
Redirect
  │
  ▼
Client
```

The second architecture eliminates an origin round trip.

However, edge execution is not automatically faster for every workload. Complex processing can increase execution time and operational complexity.

---

## Edge Computing and Scalability

The edge is useful for distributing small computations across a global request path.

For example:

```text
Millions of requests
       │
       ▼
CloudFront
       │
 ┌─────┼─────┬─────┐
 ▼     ▼     ▼     ▼
Edge  Edge  Edge  Edge
 Fn    Fn    Fn    Fn
```

This can prevent simple transformations from becoming centralized origin workloads.

The strongest scaling benefit often comes from **avoiding origin traffic altogether**, rather than merely moving CPU work from one server to another.

---

## Edge Computing Cost Considerations

Edge execution introduces additional operational and billing considerations.

Before moving logic to the edge, evaluate:

- Request volume.
- Function invocation frequency.
- Execution characteristics.
- Origin traffic saved.
- Cache-hit improvements.
- Operational complexity.

A function that executes for every viewer request can become expensive or operationally significant if it performs work that could have been avoided.

A useful question is:

> Does the edge computation reduce enough origin work or latency to justify its execution cost and complexity?

---

## Common Edge Computing Use Cases

| Use case | Edge suitability |
|---|---|
| HTTP redirects | Excellent |
| URL normalization | Excellent |
| Header manipulation | Excellent |
| Simple routing | Excellent |
| Cache-oriented transformations | Excellent |
| Lightweight device classification | Good |
| Dynamic origin selection | Good with Lambda@Edge |
| Complex authorization | Usually origin/application |
| Database queries | Poor fit |
| PostgreSQL access | Poor fit |
| Redis workflows | Poor fit |
| Kafka publishing | Poor fit |
| Celery task orchestration | Poor fit |
| Long-running processing | Poor fit |
| Complex business workflows | Poor fit |

---

## Real-World Example: Legacy URL Migration

Suppose an organization migrates:

```text
/legacy/products/123
```

to:

```text
/products/123
```

A CloudFront Function can perform the redirect at the edge.

```javascript
function handler(event) {
    var request = event.request;

    if (request.uri.startsWith("/legacy/")) {
        return {
            statusCode: 301,
            statusDescription: "Moved Permanently",
            headers: {
                location: {
                    value: request.uri.replace("/legacy", "")
                }
            }
        };
    }

    return request;
}
```

This is a good edge use case because:

- No database is required.
- The mapping is deterministic.
- The origin does not need to execute.
- The logic is lightweight.
- The redirect can happen close to the viewer.

---

## Real-World Example: Multi-Tenant Routing

Consider:

```text
tenant-a.example.com
tenant-b.example.com
tenant-c.example.com
```

The edge can inspect the host header:

```text
Host
 │
 ├── tenant-a.example.com
 │       │
 │       ▼
 │    Origin A
 │
 ├── tenant-b.example.com
 │       │
 │       ▼
 │    Origin B
 │
 └── tenant-c.example.com
         │
         ▼
      Origin C
```

This can be useful when each tenant maps to a distinct origin.

However, tenant isolation must also exist at the application and data layers. Edge routing alone is not sufficient isolation.

---

## Real-World Example: Static Asset Versioning

Suppose the application uses:

```text
/static/app.js?v=2026-08-20
```

An edge function can normalize or transform requests when the caching model requires it.

However, a stronger application-level pattern is often immutable asset versioning:

```text
/static/app.8f31c2.js
```

This allows long-lived caching while deployment creates a new filename for changed content.

The best optimization is often to fix the cache architecture rather than continuously adding edge logic.

---

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Moving all backend logic to the edge | Edge appears globally available | Keep domain logic in application |
| Using edge code for database access | Treating edge like a normal server | Use origin/backend services |
| Hard-coding secrets | Distributed execution misunderstood | Use appropriate secure architecture |
| Ignoring cache-key behavior | Function and cache viewed separately | Design request transformation with caching |
| Performing expensive computation | Edge assumed to be unlimited | Keep computation lightweight |
| Using edge for complex authorization | Desire for lower latency | Use application/identity layer where appropriate |
| Assuming edge routing creates multi-region HA | Routing mistaken for resilience | Design replication and failover separately |
| Logging tokens/cookies | Debugging convenience | Redact sensitive values |
| Overusing Lambda@Edge | More capability seems better | Prefer CloudFront Functions when sufficient |
| Ignoring event lifecycle | Viewer and origin events confused | Understand cache/request sequence |
| Creating tenant isolation only at edge | Routing mistaken for security | Enforce authorization at the backend |
| Excessive personalization | Every user variation becomes unique | Design cache strategy explicitly |

---

## Interview Questions and Answers

### What is CloudFront edge computing?

It is the execution of request or response processing logic in CloudFront's edge infrastructure so that suitable operations can occur closer to users instead of always executing at the origin.

---

### What are the main AWS technologies for CloudFront edge computing?

The primary technologies are:

- CloudFront Functions.
- Lambda@Edge.

CloudFront Functions are designed for lightweight, high-scale edge processing, while Lambda@Edge provides a more capable Lambda execution model for advanced CloudFront events.

---

### What is the difference between CloudFront Functions and Lambda@Edge?

CloudFront Functions are designed for lightweight JavaScript execution with very low overhead.

Lambda@Edge provides more runtime capabilities and can participate in origin request and origin response events, making it suitable for more advanced processing.

---

### Which should you use for a simple redirect?

CloudFront Functions are generally the better fit because a redirect is lightweight and deterministic.

---

### Which should you use for dynamic origin selection?

Lambda@Edge is the appropriate mechanism when the architecture requires origin request processing and dynamic origin selection.

---

### What is the difference between viewer request and origin request?

Viewer request processing occurs when the viewer's request reaches CloudFront.

Origin request processing occurs when CloudFront is preparing to contact the origin, typically after the cache lookup determines that the origin needs to be contacted.

Therefore, origin-request logic does not have the same execution frequency as viewer-request logic.

---

### Why does that execution frequency matter?

Suppose CloudFront has a high cache hit ratio.

With viewer-request processing:

```text
1,000,000 viewer requests
        │
        ▼
Potentially 1,000,000 edge executions
```

With origin-request processing:

```text
1,000,000 viewer requests
        │
        ▼
High cache hit ratio
        │
        ▼
Far fewer origin requests
        │
        ▼
Far fewer origin-request executions
```

The distinction affects both architecture and cost.

---

### Can CloudFront Functions access PostgreSQL?

They should not be used as a mechanism for database access.

Database-backed business logic belongs in the backend architecture, such as Django/FastAPI and its supporting services.

---

### Can edge computing replace Django or FastAPI?

No.

Edge computing complements application servers by handling suitable request-processing workloads before traffic reaches the origin.

Complex business logic, transactions, database access, and domain workflows should remain in the backend.

---

### Can edge computing reduce API latency?

It can reduce latency for operations that can be resolved at the edge, such as redirects, request normalization, lightweight routing, and certain response transformations.

It does not make a database-backed operation local to the user.

---

### Can edge computing improve scalability?

Yes, especially when it reduces origin traffic.

For example:

```text
Without edge optimization:

1M requests
    │
    ▼
Origin
    │
    ├── 1M application requests
    └── Backend scaling required

With edge optimization:

1M requests
    │
    ▼
CloudFront
    │
    ├── Edge-resolvable requests
    └── Only required traffic → Origin
```

The largest benefit is often origin offloading.

---

### What should not be moved to the edge?

Avoid moving logic that requires:

- PostgreSQL.
- Redis state.
- Kafka.
- Celery.
- Long-running computation.
- Complex transactions.
- Large application dependencies.
- Complex business workflows.

---

### Can you perform authentication at the edge?

Lightweight authentication or token validation can be part of some architectures, but edge authentication should be designed carefully around key management, token revocation, identity state, and runtime constraints.

Complex authentication workflows generally belong in a dedicated identity or application layer.

---

### Why can edge personalization reduce cache efficiency?

Suppose every user receives a different response:

```text
User A → Personalized response A
User B → Personalized response B
User C → Personalized response C
```

If the cache varies unnecessarily by user-specific information, the cache can become fragmented.

This reduces cache-hit efficiency and may increase origin traffic.

---

### Can edge logic dynamically choose an origin?

Yes, Lambda@Edge can be used for origin-request processing and dynamic origin selection.

Typical use cases include multi-region routing and tenant-specific origin selection.

---

### Does dynamic origin selection automatically provide high availability?

No.

Routing users to multiple origins does not automatically solve:

- Data replication.
- Database consistency.
- Failover.
- Session management.
- Disaster recovery.
- Regional failure handling.

Those concerns must be designed separately.

---

### Why should edge functions be kept small?

Edge code runs on the critical request path.

Large or complex functions can increase:

- Execution latency.
- Operational complexity.
- Debugging difficulty.
- Deployment risk.
- Cost.

A good edge function usually performs one narrow responsibility.

---

### What is the biggest cache-related edge-computing mistake?

Changing requests at the edge without understanding the resulting cache key.

If the response varies by a request attribute, that variation must be represented correctly in the caching model.

Otherwise the system can experience cache fragmentation or, more seriously, incorrect content being served to users.

---

### When would you choose CloudFront Functions over Lambda@Edge?

Choose CloudFront Functions when the operation is lightweight and supported by its runtime and event model, such as:

- Redirects.
- URL normalization.
- Simple header manipulation.
- Lightweight request transformation.

Choose Lambda@Edge when the workload requires capabilities unavailable to CloudFront Functions, particularly origin request or origin response processing.

---

### Is edge computing always faster?

No.

Edge execution is beneficial when it eliminates network round trips or reduces origin work.

If edge code performs expensive processing that could have been handled efficiently elsewhere, the total request may not improve.

---

### What is the most important edge-computing design principle?

> **Run simple, globally applicable request processing at the edge; keep stateful, transactional, and domain-specific business logic at the origin.**

---

## Edge Computing Decision Matrix

| Requirement | Recommended location |
|---|---|
| HTTP redirect | CloudFront Function |
| URL normalization | CloudFront Function |
| Simple header transformation | CloudFront Function |
| Lightweight cookie inspection | CloudFront Function |
| Simple request routing | CloudFront Function |
| Dynamic origin selection | Lambda@Edge |
| Origin request transformation | Lambda@Edge |
| Origin response processing | Lambda@Edge |
| PostgreSQL query | Django/FastAPI |
| Redis operation | Backend |
| Kafka publishing | Backend |
| Celery workflow | Backend |
| Payment transaction | Backend |
| Complex authorization | Backend/identity layer |
| Database-backed personalization | Backend |
| Long-running processing | Backend/async workers |

## Production Checklist

Before deploying edge logic, verify:

- [ ] The computation genuinely benefits from edge execution.
- [ ] CloudFront Functions are used when their capabilities are sufficient.
- [ ] Lambda@Edge is used only when its additional capabilities are required.
- [ ] The request lifecycle and event type are understood.
- [ ] Cache-key implications have been evaluated.
- [ ] Edge functions remain small and deterministic where possible.
- [ ] Secrets are not unnecessarily embedded in edge code.
- [ ] Sensitive headers, cookies, and tokens are not logged.
- [ ] Complex business logic remains in Django/FastAPI or another appropriate backend service.
- [ ] Database and stateful service dependencies remain outside lightweight edge functions.
- [ ] Origin failover is designed independently from edge routing.
- [ ] Multi-region routing does not substitute for database replication and disaster recovery.
- [ ] Edge-specific monitoring and deployment procedures exist.
- [ ] Security implications of request manipulation have been reviewed.
- [ ] Performance and cost are measured before and after introducing edge execution.

## Key Takeaways

- **CloudFront edge computing moves suitable request and response processing closer to users, reducing origin traffic and potentially improving latency.**
- **CloudFront Functions are the preferred fit for lightweight, high-scale transformations such as redirects, URL normalization, and header manipulation; Lambda@Edge provides broader event and runtime capabilities.**
- **Keep stateful, transactional, database-backed, and complex domain logic in Django, FastAPI, or other backend services rather than turning edge functions into distributed application servers.**
- **Edge logic and caching must be designed together because request transformations can directly affect cache keys, cache hit ratios, and even response correctness.**
- **Edge routing can improve global traffic handling, but it does not by itself provide multi-region high availability, data consistency, or disaster recovery.**