# 16- API Testing

## Overview

API testing verifies that an application's HTTP or RPC interface behaves correctly from the perspective of its consumers.

For backend systems, the API is often the primary integration boundary between:

- browsers and mobile applications;
- internal services;
- external customers;
- automation clients;
- background workers;
- API gateways and reverse proxies.

API tests should validate more than status codes. A production-oriented API test verifies the contract across request validation, authentication, authorization, application logic, persistence, serialization, error handling, and important side effects.

A typical request lifecycle is:

```text
Client
  │
  │ HTTP request
  ▼
Nginx / Load Balancer
  │
  ▼
FastAPI / Django
  │
  ├── Routing
  ├── Middleware
  ├── Authentication
  ├── Validation
  ├── Authorization
  │
  ▼
Application Service
  │
  ├── PostgreSQL
  ├── Redis
  └── Kafka
  │
  ▼
Response Serialization
  │
  ▼
HTTP Response
```

API tests should target the behavior exposed by this boundary rather than coupling heavily to internal implementation details.

---

## What API Testing Validates

API testing answers:

> Does the API behave correctly for valid, invalid, unauthorized, concurrent, and failure scenarios?

Important dimensions include:

| Dimension | Examples |
|---|---|
| Routing | Correct endpoint and HTTP method |
| Request validation | Required fields, types, constraints |
| Authentication | Missing, invalid, expired credentials |
| Authorization | Resource and role permissions |
| Business behavior | Correct application outcome |
| Persistence | Correct database state |
| Serialization | Correct response schema |
| Error handling | Correct status and error contract |
| Idempotency | Repeated requests behave correctly |
| Pagination | Correct limits, cursors, metadata |
| Concurrency | Correct behavior under concurrent requests |
| Performance | Acceptable latency and resource usage |
| Security | No unauthorized data exposure |

---

## API Testing vs Other Test Types

| Test type | Primary concern | Typical dependency strategy |
|---|---|---|
| Unit | Individual function/class behavior | Mocked |
| Integration | Component interaction | Real dependencies |
| API | External application interface | Real application boundary |
| Contract | Consumer/provider compatibility | Contract representations |
| End-to-End | Complete user/system workflow | Production-like environment |

API testing can overlap with integration testing.

For example:

```text
API Test
    │
    ├── HTTP application
    ├── Authentication
    ├── Service layer
    └── PostgreSQL
```

This is both an API test and an integration test.

The distinction is primarily about the boundary being validated.

---

## API Testing Levels

A mature test suite commonly uses several levels.

### In-Process API Tests

The HTTP client communicates directly with the application:

```text
Test Client
    │
    ▼
ASGI / WSGI Application
```

These are fast and useful for broad API coverage.

### Network-Level API Tests

The test communicates with an actual server:

```text
Test Client
    │
    ▼
TCP
    │
    ▼
Nginx
    │
    ▼
Application Server
```

These validate additional infrastructure behavior but are slower.

### Environment-Level API Tests

The test targets a deployed environment:

```text
CI / Test Client
       │
       ▼
Load Balancer
       │
       ▼
Kubernetes
       │
       ├── API
       ├── PostgreSQL
       ├── Redis
       └── Kafka
```

These are useful for deployment and smoke validation.

---

## HTTP Methods

API tests should verify that HTTP methods have the expected semantics.

| Method | Typical purpose | Common test |
|---|---|---|
| GET | Read resource | Returns expected representation |
| POST | Create/process | Creates resource or operation |
| PUT | Replace resource | Replacement is correct |
| PATCH | Partial update | Only requested fields change |
| DELETE | Remove resource | Resource becomes unavailable |

Do not test only the happy path.

For example, a `PATCH` test should verify that fields not included in the request remain unchanged.

---

## HTTP Status Codes

API tests should assert status codes as part of the API contract.

Typical categories:

| Status | Meaning | Example |
|---:|---|---|
| 200 | Successful request | GET resource |
| 201 | Resource created | POST resource |
| 202 | Accepted for processing | Async operation |
| 204 | Success without body | DELETE |
| 400 | Invalid request | Malformed input |
| 401 | Unauthenticated | Missing/invalid credentials |
| 403 | Forbidden | Insufficient permission |
| 404 | Resource unavailable | Unknown resource |
| 409 | Conflict | Duplicate/state conflict |
| 422 | Validation failure | Invalid semantic input |
| 429 | Rate limited | Too many requests |
| 500 | Server failure | Unexpected internal error |
| 503 | Service unavailable | Dependency/service unavailable |

The exact mapping should follow the API's documented contract rather than blindly applying generic conventions.

---

## Request Validation

Validation should be tested at the API boundary.

Example:

```python
@pytest.mark.asyncio
async def test_create_order_rejects_invalid_quantity(client):
    response = await client.post(
        "/orders",
        json={
            "customer_id": "customer-123",
            "items": [
                {
                    "product_id": "product-1",
                    "quantity": 0,
                }
            ],
        },
    )

    assert response.status_code == 422
```

Test important validation categories:

- missing fields;
- incorrect types;
- empty strings;
- invalid enum values;
- invalid formats;
- boundary values;
- oversized payloads;
- mutually exclusive fields;
- invalid nested objects.

---

## Boundary Testing

For a field such as:

```text
quantity: 1–100
```

test:

```text
0      → invalid
1      → valid
100    → valid
101    → invalid
```

Boundary tests provide substantially more confidence than testing several arbitrary values in the middle of the range.

---

## Authentication Testing

Authentication determines whether the caller is known.

Test at minimum:

```text
No credentials
      │
      ▼
    401

Malformed token
      │
      ▼
    401

Expired token
      │
      ▼
    401

Valid token
      │
      ▼
 authenticated request
```

Example:

```python
async def test_protected_endpoint_requires_auth(client):
    response = await client.get("/orders")

    assert response.status_code == 401
```

Do not mock authentication in every API test. A smaller set of unit tests can mock authentication internals, while API tests should exercise the real authentication boundary where practical.

---

## Authorization Testing

Authentication answers:

> Who are you?

Authorization answers:

> Are you allowed to perform this operation?

Example:

```python
async def test_user_cannot_delete_another_users_order(
    client,
    user_token,
    other_users_order,
):
    response = await client.delete(
        f"/orders/{other_users_order.id}",
        headers={
            "Authorization": f"Bearer {user_token}",
        },
    )

    assert response.status_code in {403, 404}
```

The expected response depends on the security policy.

Test:

- role permissions;
- ownership;
- tenant boundaries;
- resource-level permissions;
- disabled accounts;
- service-to-service permissions.

---

## Multi-Tenant API Testing

Multi-tenant APIs require explicit isolation tests.

```text
Tenant A
   │
   └── order-A

Tenant B
   │
   └── order-B
```

A request authenticated for Tenant A must not retrieve or modify Tenant B's resources.

Test both direct access:

```http
GET /orders/order-B
```

and indirect access:

```http
GET /orders?customer_id=customer-B
```

The second case is particularly important because authorization vulnerabilities frequently occur through filters and collection endpoints.

---

## Request and Response Schemas

API tests should verify the externally visible schema.

For example:

```python
response = await client.get("/orders/order-123")

body = response.json()

assert body["id"] == "order-123"
assert body["status"] in {
    "pending",
    "confirmed",
    "cancelled",
}
assert "created_at" in body
```

Do not assert every incidental implementation detail.

Focus on fields and semantics that consumers depend on.

---

## Schema Validation

For APIs with formal OpenAPI or JSON Schema contracts, schema validation can detect:

- missing response fields;
- incorrect types;
- unexpected enum values;
- incompatible structure changes;
- invalid serialization.

Schema validation is especially useful when many consumers depend on the API.

---

## Request Serialization

Test serialization at the boundary.

Important cases include:

- JSON encoding;
- dates and datetimes;
- UUIDs;
- decimals;
- enums;
- nested objects;
- nullable values.

For example:

```python
response = await client.get("/orders/order-123")

assert response.json()["created_at"].endswith("Z")
```

The exact timestamp representation should follow the API contract.

---

## Response Serialization

The API should not accidentally expose internal persistence models.

For example:

```text
Database Model
     │
     ▼
Domain Model
     │
     ▼
API Response Model
```

Tests should verify that:

- only intended fields are exposed;
- sensitive fields are excluded;
- computed fields are correct;
- nullable fields follow the contract.

---

## Sensitive Data Exposure

Security-focused API tests should ensure responses do not expose:

- passwords;
- password hashes;
- authentication tokens;
- private keys;
- internal credentials;
- unrelated tenant data;
- internal database identifiers where prohibited.

Example:

```python
body = response.json()

assert "password_hash" not in body
assert "access_token" not in body
```

Sensitive-field assertions are high-value regression tests.

---

## CRUD API Testing

For resource-oriented APIs, test the lifecycle:

```text
POST
 │
 ▼
Create
 │
 ▼
GET
 │
 ▼
PATCH / PUT
 │
 ▼
GET
 │
 ▼
DELETE
 │
 ▼
GET → 404
```

However, do not make every test depend on the previous test.

Each test should establish its own required state.

---

## API Test Isolation

Avoid:

```text
test_create
    ↓
test_get
    ↓
test_update
    ↓
test_delete
```

where each test depends on the previous test.

Prefer:

```text
test_create → creates own data
test_get    → creates own data
test_update → creates own data
test_delete → creates own data
```

This makes failures independent and allows parallel execution.

---

## Database State Assertions

An API test should sometimes verify the database after the request.

```python
response = await client.post(
    "/customers",
    json=payload,
)

assert response.status_code == 201

customer_id = response.json()["id"]

customer = await customer_repository.get(
    customer_id,
)

assert customer.email == payload["email"]
```

This catches cases where the API returns a successful response but persistence failed or produced incorrect state.

---

## Side-Effect Assertions

API operations often produce multiple side effects.

For example:

```text
POST /orders
      │
      ├── PostgreSQL → order
      ├── PostgreSQL → outbox event
      ├── Redis → cache invalidation
      └── Kafka → event publication
```

Test the important contract rather than merely:

```python
assert response.status_code == 201
```

For critical workflows, verify the resulting state and externally observable effects.

---

## Idempotency Testing

Idempotency is important for APIs handling retries, payments, orders, and other state-changing operations.

Example:

```python
headers = {
    "Idempotency-Key": "request-123",
}

first = await client.post(
    "/payments",
    headers=headers,
    json=payload,
)

second = await client.post(
    "/payments",
    headers=headers,
    json=payload,
)

assert first.status_code == 201
assert second.status_code == 201
assert first.json()["payment_id"] == second.json()["payment_id"]
```

The exact status behavior depends on the API contract.

The important property is that the operation is not accidentally performed twice.

---

## Retry Testing

Clients and infrastructure may retry requests after:

- timeouts;
- connection failures;
- 502 responses;
- 503 responses.

API tests should verify that retryable operations are safe where the API contract requires it.

This is particularly important for:

- payment APIs;
- order creation;
- job submission;
- webhook processing.

---

## Pagination Testing

Test:

- default page size;
- explicit page size;
- maximum page size;
- empty result;
- first page;
- middle pages;
- final page;
- invalid cursor;
- duplicate/missing records across pages.

For cursor pagination:

```text
Request
  │
  ▼
GET /orders?cursor=abc
  │
  ▼
Items + next_cursor
```

Do not assume offset pagination remains efficient for very large datasets.

---

## Filtering and Sorting

For collection endpoints, test combinations that materially affect behavior:

```http
GET /orders?status=pending
GET /orders?created_after=...
GET /orders?sort=-created_at
```

Verify both:

- returned records;
- ordering.

If filters affect authorization, test tenant and ownership isolation simultaneously.

---

## API Error Contracts

Errors should be predictable.

For example:

```json
{
  "error": {
    "code": "ORDER_NOT_FOUND",
    "message": "Order was not found",
    "request_id": "req-123"
  }
}
```

API tests can verify:

```python
assert response.status_code == 404

body = response.json()

assert body["error"]["code"] == "ORDER_NOT_FOUND"
assert "request_id" in body["error"]
```

Avoid asserting exact human-readable messages unless they are explicitly part of the public contract.

Prefer stable machine-readable error codes.

---

## Error Mapping

Application exceptions should map to appropriate API responses.

```text
Domain Exception
      │
      ▼
Exception Handler
      │
      ▼
HTTP Status + Error Schema
```

Example:

```python
class OrderNotFoundError(Exception):
    pass
```

The API layer may translate it to:

```text
OrderNotFoundError
       ↓
404 Not Found
       ↓
ORDER_NOT_FOUND
```

Integration/API tests should verify this translation.

---

## Database Failure Testing

When appropriate, simulate or trigger database failures.

Examples:

- connection failure;
- constraint violation;
- transaction rollback;
- timeout;
- deadlock;
- unavailable database.

Verify that the API does not accidentally expose internal database details.

Prefer:

```text
Database failure
      │
      ▼
Application error handling
      │
      ▼
Safe API response
```

rather than:

```text
Database failure
      │
      ▼
Raw SQL error returned to client
```

---

## Dependency Failure Testing

An API may depend on:

```text
API
 ├── PostgreSQL
 ├── Redis
 ├── Kafka
 └── External HTTP service
```

Test important degraded modes.

For example:

```text
Redis unavailable
      │
      ▼
Cache bypass
      │
      ▼
PostgreSQL
      │
      ▼
200 OK
```

if Redis is an optional cache.

If Redis is a required dependency, the expected behavior may instead be `503`.

The test should encode the intended resilience policy.

---

## FastAPI API Testing

FastAPI integrates naturally with HTTPX-based testing.

```python
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_get_order(app):
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/orders/order-123",
        )

    assert response.status_code == 200
```

FastAPI dependency overrides are useful for controlled boundaries:

```python
app.dependency_overrides[get_current_user] = get_test_user
```

Use overrides selectively. If every API test overrides the complete authentication or database layer, the suite stops validating important integration behavior.

---

## Django API Testing

Django applications can use Django's test client or the testing utilities provided by the API framework in use.

A test might look conceptually like:

```python
response = client.post(
    "/api/orders/",
    data=payload,
    content_type="application/json",
)

assert response.status_code == 201
```

For Django REST Framework, API tests should exercise serializers, authentication, permissions, views, and persistence at appropriate test levels.

Avoid testing only view functions while bypassing the actual middleware and authentication behavior when those are part of the API contract.

---

## Authentication Overrides

Dependency overrides are useful for targeted tests:

```python
app.dependency_overrides[
    get_current_user
] = lambda: test_user
```

This is appropriate when testing business behavior independently of authentication.

Maintain separate API tests for the actual authentication mechanism.

A useful split is:

```text
Authentication tests
    → real authentication boundary

Business API tests
    → controlled authenticated identity
```

This provides both confidence and test-suite performance.

---

## Mocking in API Tests

Mocking can be appropriate for expensive or unstable external dependencies:

```python
with patch(
    "app.services.payment.PaymentClient.charge",
) as charge:
    charge.return_value = PaymentResult(
        id="pay-123",
        status="approved",
    )

    response = client.post(...)
```

However, do not mock the component whose behavior the API test is intended to verify.

If the purpose is to validate PostgreSQL integration, mocking the repository defeats the purpose.

---

## Patch Where Used

When mocking dependencies in Python, patch the name looked up by the code under test.

If:

```python
# orders/service.py
from payments import PaymentClient
```

then the test generally patches:

```python
patch("orders.service.PaymentClient")
```

rather than:

```python
patch("payments.PaymentClient")
```

unless the application performs a different lookup.

This follows Python's import and name-binding semantics.

---

## API Contract Testing

Contract testing verifies compatibility between API providers and consumers.

For REST:

```text
Consumer
   │
   │ expected contract
   ▼
API Provider
```

Important contract elements include:

- paths;
- HTTP methods;
- request schemas;
- response schemas;
- status codes;
- required fields;
- enum values;
- error structures.

Contract testing is particularly valuable in microservice architectures where services deploy independently.

---

## Backward Compatibility

API changes should be evaluated for compatibility.

Potential breaking changes include:

- removing fields;
- changing field types;
- changing required fields;
- removing enum values;
- changing authentication requirements;
- changing status codes;
- changing pagination semantics.

An API test suite should protect consumer-visible contracts.

---

## API Versioning

Versioned APIs can be tested independently:

```text
/api/v1/orders
/api/v2/orders
```

Tests should verify that:

- supported versions continue working;
- new versions implement their intended contract;
- deprecated versions behave consistently until removal;
- migrations do not accidentally break existing consumers.

Do not duplicate the entire test suite blindly if versions share behavior.

---

## OpenAPI Contract Validation

OpenAPI can provide a machine-readable API contract.

A CI pipeline may validate:

```text
Application
    │
    ▼
Generate OpenAPI
    │
    ▼
Validate Schema
    │
    ▼
Contract Checks
    │
    ▼
CI Pass/Fail
```

This can detect accidental contract drift before deployment.

---

## Security Testing

API security tests should cover:

- authentication bypass;
- authorization bypass;
- tenant isolation;
- IDOR/BOLA vulnerabilities;
- malformed input;
- oversized payloads;
- mass assignment;
- sensitive-field exposure;
- rate limiting;
- CORS behavior where applicable;
- security headers;
- token expiration;
- replay/idempotency behavior.

### IDOR/BOLA Example

```text
User A
  │
  └── GET /orders/order-owned-by-B
                    │
                    ▼
                 Must deny
```

This is one of the highest-value authorization tests for resource APIs.

---

## Rate-Limit Testing

If an API implements rate limiting:

```text
Requests
  │
  ▼
Rate Limiter
  │
  ├── within limit → 2xx
  │
  └── exceeded     → 429
```

Test:

- limit boundaries;
- response status;
- retry headers where documented;
- identity/IP behavior;
- distributed rate limiting where Redis is involved.

Avoid relying solely on local in-memory rate limiting tests for distributed deployments.

---

## Request Size Limits

APIs should protect against unexpectedly large payloads.

Test:

```text
small valid payload → accepted
maximum valid payload → accepted
oversized payload → rejected
```

This protects memory and CPU resources and reduces denial-of-service risk.

---

## Timeout Testing

API tests should validate bounded behavior when dependencies are slow.

For example:

```text
API
 │
 ▼
External Service
 │
 └── timeout
       │
       ▼
   controlled API error
```

The API should not hold resources indefinitely.

Test timeout behavior at the boundary that owns the timeout policy.

---

## Concurrency Testing

Some API behavior only fails under concurrent requests.

Examples:

- duplicate resource creation;
- inventory reservation;
- idempotency;
- optimistic locking;
- distributed locks;
- race conditions.

A targeted concurrency test might execute multiple requests simultaneously:

```python
results = await asyncio.gather(
    client.post("/orders", json=payload),
    client.post("/orders", json=payload),
)
```

Assertions should focus on the intended invariant rather than assuming a particular scheduling order.

---

## Race Conditions

Suppose inventory contains one unit:

```text
Inventory = 1

Request A ──┐
            ├── reserve → ?
Request B ──┘
```

The invariant may be:

```text
successful reservations ≤ available inventory
```

Integration/API tests using real database transactions are much more useful here than mocks.

---

## Async API Testing

Async tests should:

- await the actual request;
- use async clients;
- close clients deterministically;
- avoid arbitrary sleeps;
- clean up created tasks;
- apply bounded timeouts.

Example:

```python
@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")

    assert response.status_code == 200
```

For concurrent behavior, use explicit synchronization and task completion rather than timing assumptions.

---

## Streaming API Testing

Streaming APIs require different assertions from ordinary JSON endpoints.

Examples:

- Server-Sent Events;
- chunked responses;
- streaming downloads;
- streaming uploads.

Test:

- first response availability;
- chunk format;
- ordering;
- completion;
- disconnect behavior;
- cancellation;
- resource cleanup.

Do not force a streaming endpoint into a single `response.json()` assertion.

---

## WebSocket API Testing

WebSocket tests should verify:

```text
Connect
  │
  ▼
Authenticate
  │
  ▼
Send message
  │
  ▼
Receive message
  │
  ▼
Disconnect
```

Important cases include:

- authentication;
- invalid messages;
- connection limits;
- reconnect behavior;
- server shutdown;
- client disconnect;
- authorization.

---

## API Performance Testing

Functional API tests should not become full load tests.

Use dedicated performance testing for:

- throughput;
- latency distributions;
- concurrency;
- CPU;
- memory;
- connection pools;
- database load.

API integration tests can still catch obvious performance regressions such as an unexpectedly expensive endpoint.

For production systems, measure:

```text
p50
p95
p99
error rate
throughput
```

rather than relying only on average latency.

---

## N+1 Query Detection

API tests can detect accidental N+1 database access when the test environment exposes query counts.

For example:

```text
GET /orders
      │
      ├── query orders
      ├── query customer
      ├── query customer
      ├── query customer
      └── ...
```

A targeted test can assert a reasonable query count for a known endpoint.

Do not make every test dependent on exact query counts because legitimate implementation changes can invalidate brittle assertions.

---

## API Observability

API tests should verify observability where it is part of the operational contract.

Important signals include:

- request ID propagation;
- structured logs;
- metrics;
- trace context;
- error classification.

For example:

```text
Client
  │
  │ X-Request-ID
  ▼
API
  │
  ├── application logs
  ├── database traces
  └── downstream HTTP traces
```

The same request identifier should allow operators to correlate failures across services when the system supports such propagation.

---

## Health and Readiness Endpoints

Test health endpoints according to their purpose.

### Liveness

Answers:

> Is the process capable of running?

### Readiness

Answers:

> Should this instance receive traffic?

Kubernetes commonly uses these independently.

Do not make liveness depend on every external dependency if doing so would cause healthy processes to be restarted during a dependency outage.

---

## API Smoke Tests

Smoke tests are a small set of high-value tests executed against a deployed environment.

Example:

```text
Deploy
  │
  ▼
Health check
  │
  ▼
Authenticate
  │
  ▼
Read critical resource
  │
  ▼
Create controlled test resource
  │
  ▼
Verify
```

Smoke tests should be small, stable, and representative.

They are not a replacement for the complete test suite.

---

## CI/CD Strategy

A practical pipeline is:

```text
Pull Request
    │
    ├── Unit Tests
    ├── API Tests
    │
    ▼
Integration Environment
    │
    ├── PostgreSQL
    ├── Redis
    └── Kafka
    │
    ▼
Contract Tests
    │
    ▼
Build
    │
    ▼
Deploy
    │
    ▼
Smoke Tests
```

Run fast API tests early and environment-dependent tests later.

---

## Test Data Management

API tests should create controlled data.

Prefer:

```python
customer = customer_factory()
order = order_factory(customer_id=customer.id)
```

over relying on hard-coded shared records.

Unique identifiers reduce parallel-test collisions:

```python
external_id = f"test-{uuid4()}"
```

Clean up resources that are not automatically isolated.

---

## Fixtures for API Tests

A good fixture hierarchy might look like:

```text
session
 ├── application
 ├── database
 └── redis

function
 ├── client
 ├── authenticated_user
 └── test_data
```

Keep fixture scopes intentional.

Broad shared mutable fixtures can create hidden coupling between tests.

---

## Production Environment Safety

API tests must never accidentally target production.

Use explicit environment validation:

```python
if settings.environment == "production":
    raise RuntimeError(
        "API tests cannot run against production"
    )
```

Also validate:

- database host;
- API base URL;
- AWS account;
- Kafka cluster;
- Redis endpoint.

Fail closed rather than assuming configuration is safe.

---

## Common Mistakes

### Testing Only Status Codes

```python
assert response.status_code == 200
```

This may pass while the response contains incorrect data.

Test important response fields and resulting state.

### Testing Only Happy Paths

Real APIs encounter:

- invalid requests;
- unauthorized users;
- missing resources;
- dependency failures;
- duplicate requests;
- concurrency.

Negative paths are essential.

### Mocking Everything

If the API test mocks:

```text
database
authentication
repository
service
cache
event publisher
```

it may be little more than a unit test with HTTP syntax.

Keep real boundaries that matter.

### Sharing Mutable Test Data

Shared users, orders, Redis keys, and Kafka messages create order-dependent failures.

Prefer isolated data.

### Asserting Human Messages Too Strictly

Exact messages change more frequently than machine-readable error codes.

Prefer stable codes and schemas.

### Using Production Data

Production data can expose sensitive information and create legal/security risks.

Use synthetic test data.

### Arbitrary Sleeps

Sleeping to wait for asynchronous processing makes tests slow and flaky.

Wait for explicit conditions.

### Ignoring Cleanup

Unclosed clients, database connections, temporary resources, and background tasks can contaminate later tests.

Use fixtures and deterministic cleanup.

---

## Production Pitfalls

### Contract Drift

An API implementation can remain internally correct while breaking consumers.

Protect public schemas with contract tests and compatibility checks.

### Authorization Gaps

Testing `GET /resource/{id}` is insufficient if authorization can be bypassed through:

```text
GET /resources?owner_id=...
```

Test equivalent access paths.

### Hidden Side Effects

Returning `201` does not prove that:

- the database committed;
- the event was recorded;
- the cache was invalidated.

Test critical side effects.

### Shared Infrastructure

A shared test PostgreSQL or Kafka cluster can introduce:

- data collisions;
- stale state;
- test interference;
- unpredictable failures.

Prefer isolated environments.

### Excessive API Test Coverage

A large number of nearly identical API tests increases maintenance cost without proportionate confidence.

Prefer representative boundary and behavior coverage.

---

## API Testing Checklist

### Request

- [ ] Correct HTTP method?
- [ ] Correct path?
- [ ] Required fields validated?
- [ ] Invalid values rejected?
- [ ] Boundary values tested?
- [ ] Payload-size limits tested?

### Authentication

- [ ] Missing credentials?
- [ ] Invalid credentials?
- [ ] Expired credentials?
- [ ] Valid credentials?
- [ ] Authentication middleware exercised?

### Authorization

- [ ] Correct role?
- [ ] Resource ownership?
- [ ] Tenant isolation?
- [ ] Collection filtering?
- [ ] IDOR/BOLA scenarios?

### Response

- [ ] Correct status code?
- [ ] Correct response schema?
- [ ] Correct serialization?
- [ ] Sensitive fields excluded?
- [ ] Error contract stable?

### Persistence and Side Effects

- [ ] Database state verified?
- [ ] Transaction behavior verified?
- [ ] Cache behavior verified?
- [ ] Events/outbox verified?
- [ ] Idempotency verified?

### Reliability

- [ ] Dependency failures?
- [ ] Timeouts?
- [ ] Retries?
- [ ] Concurrent requests?
- [ ] Eventual consistency?

### Operations

- [ ] Tests isolated?
- [ ] Tests parallel-safe?
- [ ] Cleanup deterministic?
- [ ] CI infrastructure reproducible?
- [ ] Production endpoints protected?

---

## Best Practices

- Treat the API as a public contract, not merely a controller implementation.
- Test both successful and failure behavior.
- Validate important response schemas and persistent state.
- Exercise real authentication and authorization boundaries in targeted tests.
- Use mocks only for dependencies whose real behavior is outside the test's purpose.
- Test idempotency for retry-sensitive state-changing operations.
- Include tenant-isolation and authorization regression tests.
- Use deterministic fixtures and isolated test data.
- Avoid arbitrary sleeps and blind retries.
- Keep API tests independent and parallel-safe.
- Separate functional API tests from dedicated load and stress testing.
- Protect API contracts with OpenAPI or contract-testing mechanisms where appropriate.
- Run smoke tests against deployed environments before considering a release healthy.
- Never allow automated API tests to access production infrastructure accidentally.

---

## Interview Traps

### Is API Testing the Same as Integration Testing?

No. API testing focuses on the application's externally visible API boundary. An API test may also be an integration test when it exercises real databases, caches, brokers, or other dependencies.

### Should API Tests Mock the Database?

Not always. If the purpose is to test HTTP behavior independently of persistence, mocking can be appropriate. If the purpose is to verify API-to-database integration, use a real database.

### What Should an API Test Assert?

At minimum, the relevant status code and response contract. For important state-changing operations, also verify persistent state and critical side effects.

### Why Test Authorization Through the API?

Authorization often depends on authentication context, routing, request parameters, database state, and middleware. Testing only an internal authorization function can miss integration defects.

### How Do You Test Idempotency?

Send the same logical operation multiple times with the same idempotency key and verify that the resulting business operation occurs only once according to the API contract.

### How Do You Test Eventual Consistency?

Wait for an explicit condition with a bounded timeout rather than sleeping for a fixed duration. Verify the final invariant rather than assuming a particular processing delay.

### Should API Tests Run Against Production?

No. Use isolated test environments for automated tests. Production validation should use explicitly designed smoke, canary, or verification mechanisms.

### How Do You Prevent API Tests from Becoming Slow?

Keep the suite focused, use in-process clients for broad API coverage, reuse expensive infrastructure safely, isolate test data, parallelize where possible, and reserve full deployed-environment testing for targeted scenarios.

### What Makes an API Test High Value?

It protects a consumer-visible contract or system invariant that could realistically regress, such as authorization isolation, transaction behavior, response schema, idempotency, or correct persistence.

### How Do API Tests Fit Into CI/CD?

Fast API tests should run early, infrastructure-dependent API/integration tests should run in isolated environments, contract tests should protect service compatibility, and a small smoke suite should validate deployed environments.

## Key Takeaways

- **Treat APIs as contracts:** test request validation, authentication, authorization, status codes, response schemas, and error behavior from the consumer's perspective.
- **Test important side effects:** for state-changing operations, verify database state, transactions, events, cache behavior, and idempotency rather than checking only HTTP status codes.
- **Protect security boundaries:** explicitly test tenant isolation, ownership, role permissions, IDOR/BOLA scenarios, sensitive-field exposure, and authentication failures.
- **Keep tests deterministic and isolated:** use controlled fixtures, independent test data, bounded timeouts, explicit synchronization, and parallel-safe resources.
- **Use layered API testing:** combine fast in-process API tests with targeted integration, contract, concurrency, security, and deployed-environment smoke tests.