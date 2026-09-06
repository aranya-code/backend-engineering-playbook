# 21- Testing Strategies

## Overview

A testing strategy defines **what to test, at which layer, with which level of isolation, and with what confidence**.

A production Python backend should not rely on one type of test. Different test levels detect different classes of defects:

```text
                         Testing Strategy
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
       Unit Tests          Integration Tests       API Tests
          │                     │                     │
          ▼                     ▼                     ▼
    Business logic       Real infrastructure    External behavior
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                ▼
                       Contract / E2E Tests
                                │
                                ▼
                       Production Confidence
```

A strong strategy balances:

- correctness;
- execution speed;
- isolation;
- realism;
- maintainability;
- failure diagnosis;
- CI cost;
- production risk.

The objective is not to maximize the number of tests. It is to obtain **appropriate confidence at acceptable cost**.

---

## Testing Pyramid

The traditional testing pyramid emphasizes many fast, isolated tests and fewer expensive end-to-end tests.

```text
                 /\
                /  \
               / E2E\
              /------\
             /  API   \
            /----------\
           / Integration\
          /--------------\
         /     Unit       \
        /------------------\
```

The exact shape varies by system.

A backend service might instead use:

```text
Many:
  Unit + component tests

Moderate:
  Integration + API tests

Few:
  Contract + end-to-end tests
```

The pyramid is a heuristic, not a mandatory architecture.

---

## Test Types

| Test type | Primary purpose | Typical speed | Infrastructure |
|---|---|---:|---|
| Unit | Isolated logic | Very fast | None |
| Component | Component behavior with controlled boundaries | Fast | Limited |
| Integration | Real component integration | Moderate | Real dependencies |
| API | External HTTP/RPC behavior | Moderate | Application |
| Contract | Interface compatibility | Moderate | Consumer/provider |
| End-to-end | Complete business workflow | Slow | Full environment |
| Performance | Capacity and latency | Variable | Production-like |
| Security | Security properties | Variable | Environment-dependent |
| Property-based | Broad input behavior | Variable | Usually limited |

A mature test suite uses multiple layers rather than forcing every behavior into one category.

---

## Unit Testing Strategy

Unit tests should verify small units of behavior in isolation.

Typical candidates:

- business rules;
- parsers;
- validators;
- transformations;
- state transitions;
- retry decisions;
- authorization policies.

Example:

```python
def calculate_discount(total: float) -> float:
    if total >= 100:
        return total * 0.10

    return 0.0
```

Test the behavior:

```python
import pytest


@pytest.mark.parametrize(
    ("total", "expected"),
    [
        (100, 10),
        (150, 15),
        (99.99, 0),
    ],
)
def test_calculate_discount(total, expected):
    assert calculate_discount(total) == expected
```

Unit tests should generally be:

- deterministic;
- isolated;
- fast;
- easy to diagnose.

---

## What Should Be Unit Tested?

Good unit-test candidates include:

```text
Domain Logic
    ├── validation
    ├── calculations
    ├── state transitions
    ├── authorization decisions
    └── transformations
```

Avoid requiring PostgreSQL, Redis, Kafka, or HTTP for every business-rule test.

The purpose of unit isolation is to make failures local and inexpensive to diagnose.

---

## Component Testing

Component tests sit between unit and integration tests.

A component might include:

```text
API Handler
    │
    ▼
Service Layer
    │
    ▼
Repository Interface
```

while replacing external systems with controlled fakes.

This is useful when testing several application layers together without requiring the entire infrastructure stack.

Component tests can be particularly valuable in large services where pure unit tests become too isolated from actual application wiring.

---

## Integration Testing Strategy

Integration tests verify that multiple components work together using real or production-representative boundaries.

Examples:

- application + PostgreSQL;
- application + Redis;
- consumer + Kafka;
- service + external HTTP service;
- ORM + PostgreSQL;
- gRPC client + server.

Example:

```text
Application
     │
     ▼
Repository
     │
     ▼
PostgreSQL
```

A database integration test can verify:

- SQL correctness;
- schema constraints;
- transactions;
- indexes;
- type mappings;
- connection behavior.

Mocks cannot provide the same confidence.

---

## Real Database Testing

If production uses PostgreSQL, important database semantics should be tested against PostgreSQL.

Do not rely exclusively on SQLite for PostgreSQL applications.

PostgreSQL-specific behavior can include:

- JSONB;
- UUID;
- timezone handling;
- transaction isolation;
- constraints;
- locking;
- indexes;
- query planning.

A test passing against SQLite does not prove equivalent PostgreSQL behavior.

---

## API Testing Strategy

API tests validate externally visible HTTP or RPC behavior.

For a FastAPI service:

```text
HTTP Request
     │
     ▼
Authentication
     │
     ▼
Authorization
     │
     ▼
Validation
     │
     ▼
Service
     │
     ▼
Repository
     │
     ▼
Response
```

API tests should cover:

- status codes;
- response schemas;
- validation;
- authentication;
- authorization;
- persistence;
- error contracts;
- pagination;
- idempotency;
- important side effects.

Example:

```python
def test_create_order(authenticated_client):
    response = authenticated_client.post(
        "/orders",
        json={
            "product_id": "product-123",
            "quantity": 2,
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["quantity"] == 2
```

---

## Contract Testing

Contract tests verify that independently deployed services agree on an interface.

For example:

```text
Order Service
     │
     │ HTTP / gRPC
     ▼
Payment Service
```

The contract defines expectations around:

- request schema;
- response schema;
- status/error behavior;
- required fields;
- compatibility.

Contract testing is valuable in microservice architectures because unit tests cannot detect an incompatible deployed dependency.

---

## Consumer-Driven Contracts

A consumer-driven contract describes what a consumer expects from a provider.

```text
Consumer
   │
   │ expected contract
   ▼
Provider
```

This can detect breaking changes before deployment.

For example, if a consumer expects:

```json
{
  "payment_id": "123",
  "status": "authorized"
}
```

and the provider changes or removes `status`, contract verification should fail.

---

## End-to-End Testing

End-to-end tests validate complete workflows across multiple components.

Example:

```text
Client
  │
  ▼
Nginx / Load Balancer
  │
  ▼
Order API
  │
  ├── PostgreSQL
  ├── Redis
  └── Kafka
        │
        ▼
   Payment Worker
        │
        ▼
   Payment Service
```

An E2E test might verify:

```text
Create order
   ↓
Persist order
   ↓
Publish event
   ↓
Process payment
   ↓
Update order status
```

E2E tests provide strong confidence but are expensive and often slower to diagnose.

Use them for a small number of critical business workflows.

---

## Smoke Testing

Smoke tests provide fast verification that a deployment is fundamentally functional.

Typical checks:

- application starts;
- health endpoint works;
- authentication works;
- critical API responds;
- database connectivity works;
- essential dependency connectivity works.

Example:

```bash
curl --fail https://api.example.com/health
```

Smoke tests are useful immediately after deployment.

---

## Regression Testing

Regression tests protect behavior that previously failed or changed.

When fixing a production defect:

```text
Production Bug
      │
      ▼
Reproduce
      │
      ▼
Write failing test
      │
      ▼
Fix implementation
      │
      ▼
Test passes
```

The test becomes a permanent regression guard.

Avoid fixing production bugs without adding an appropriate regression test when feasible.

---

## Testing the Happy Path

Every important workflow should have a successful-path test.

Example:

```text
POST /orders
   │
   ▼
201 Created
   │
   ▼
Order persisted
   │
   ▼
Event published
```

Happy-path tests establish baseline behavior.

They are necessary but insufficient.

---

## Testing Failure Paths

Production systems fail primarily at boundaries.

Test scenarios such as:

- database timeout;
- Redis unavailable;
- Kafka publish failure;
- external API timeout;
- malformed input;
- invalid authentication;
- insufficient permissions;
- transaction rollback;
- duplicate requests.

Example:

```python
def test_payment_timeout_is_retryable(payment_client):
    payment_client.charge.side_effect = TimeoutError

    result = process_payment(payment_client)

    assert result.retryable is True
```

Failure behavior should be tested as deliberately as success behavior.

---

## Boundary Testing

Boundary values frequently reveal defects.

For:

```python
quantity >= 1
```

test:

```text
0
1
2
-1
very large value
```

For pagination:

```text
page = 0
page = 1
page = last page
page > last page
limit = minimum
limit = maximum
limit > maximum
```

Boundary tests are often more valuable than adding large numbers of random examples.

---

## Equivalence Classes

Instead of testing every possible input, group equivalent behaviors.

For an order quantity:

| Class | Example |
|---|---:|
| Invalid negative | `-1` |
| Invalid zero | `0` |
| Valid minimum | `1` |
| Valid normal | `10` |
| Valid maximum | `100` |
| Invalid above maximum | `101` |

This gives good behavioral coverage without combinatorial explosion.

---

## State Transition Testing

Many backend domains are state machines.

For example:

```text
PENDING
   │
   ├── payment success ──► CONFIRMED
   │
   ├── cancellation ────► CANCELLED
   │
   └── payment failure ──► FAILED
```

Tests should verify:

- valid transitions;
- invalid transitions;
- terminal states;
- repeated transitions;
- concurrent transitions where relevant.

Example:

```python
def test_cancelled_order_cannot_be_confirmed():
    order = Order(status="cancelled")

    with pytest.raises(InvalidStateTransition):
        order.confirm()
```

---

## Authorization Testing

Authentication and authorization should be tested separately.

```text
No credentials
      │
      ▼
     401

Valid identity
      │
      ▼
Insufficient permission
      │
      ▼
     403

Authorized identity
      │
      ▼
    200/201
```

Test:

- unauthenticated access;
- authenticated but unauthorized access;
- correct role;
- tenant boundaries;
- resource ownership;
- administrative access.

Authorization bugs can have much higher impact than ordinary application defects.

---

## Multi-Tenant Testing

For multi-tenant systems, isolation must be explicitly tested.

```text
Tenant A
   │
   └── Customer A

Tenant B
   │
   └── Customer B
```

A test should prove that:

```text
Tenant A request
      │
      ▼
Cannot access Tenant B data
```

Do not rely solely on application-level assumptions.

Test repository filters, authorization, database queries, and API behavior where appropriate.

---

## Idempotency Testing

Retryable operations must be tested for idempotency.

Example:

```text
POST /payments
Idempotency-Key: abc123
```

Repeated requests should not create multiple charges.

Test:

```python
first = create_payment(
    idempotency_key="abc123",
)

second = create_payment(
    idempotency_key="abc123",
)

assert second.payment_id == first.payment_id
```

Idempotency is especially important for:

- payments;
- order creation;
- message processing;
- webhooks;
- retries.

---

## Retry Testing

Retry logic should test:

- retryable errors;
- non-retryable errors;
- maximum attempts;
- backoff;
- final failure;
- idempotency.

Example:

```python
def test_retries_transient_failure(client):
    client.request.side_effect = [
        TimeoutError,
        TimeoutError,
        {"status": "ok"},
    ]

    result = call_with_retry(client)

    assert result["status"] == "ok"
    assert client.request.call_count == 3
```

Do not use real long sleeps in unit tests.

Inject or control the timing mechanism where appropriate.

---

## Testing Transactions

Transactions should be tested at the database integration level when transaction semantics matter.

Important scenarios:

```text
Operation
   │
   ├── Success → COMMIT
   │
   └── Failure → ROLLBACK
```

Test that partial state is not persisted after failures.

For concurrency-sensitive systems, also test:

- isolation levels;
- row locks;
- deadlocks;
- optimistic locking;
- concurrent updates.

---

## Testing External Services

External services should be tested at multiple layers.

### Unit Level

Mock the client:

```python
payment_client.charge = AsyncMock(
    return_value=PaymentResult(
        status="authorized",
    )
)
```

### Integration Level

Use a sandbox, emulator, or disposable test service where appropriate.

### Contract Level

Verify interface compatibility.

### E2E Level

Validate a small number of critical workflows.

No single layer provides complete confidence.

---

## Testing Redis

Tests should verify application behavior involving Redis where relevant:

- cache hits;
- cache misses;
- expiration;
- invalidation;
- distributed locks;
- rate limiting.

A mock can verify that application code calls Redis.

A real Redis integration test is needed to verify Redis semantics.

---

## Testing Kafka

Kafka consumers should test:

- message processing;
- acknowledgment/offset behavior;
- malformed messages;
- retries;
- redelivery;
- idempotency;
- ordering assumptions;
- consumer failure.

Example architecture:

```text
Producer
   │
   ▼
Kafka
   │
   ▼
Consumer
   │
   ├── Success → Commit offset
   │
   └── Failure → Retry / DLQ
```

Testing only the consumer function does not validate the entire messaging lifecycle.

---

## Testing Celery

For Celery applications, distinguish task logic from worker infrastructure.

Unit tests can execute task logic directly.

Integration tests can verify:

- task submission;
- broker interaction;
- worker execution;
- retry behavior;
- acknowledgment;
- result handling where applicable.

Avoid turning every unit test into a real distributed worker test.

---

## Async Testing Strategy

Async applications require explicit testing of:

- successful awaits;
- exceptions;
- cancellation;
- timeout;
- concurrent tasks;
- async context managers;
- async iterators.

Example:

```python
@pytest.mark.asyncio
async def test_fetch_customer(repository):
    repository.get = AsyncMock(
        return_value=Customer(id="customer-123"),
    )

    customer = await fetch_customer(
        repository,
        "customer-123",
    )

    assert customer.id == "customer-123"
    repository.get.assert_awaited_once_with("customer-123")
```

Avoid synchronizing tests with arbitrary `asyncio.sleep()` calls.

Prefer events, queues, task completion, or other explicit synchronization primitives.

---

## Concurrency Testing

Concurrency bugs are often nondeterministic.

Important scenarios include:

- race conditions;
- duplicate processing;
- lock contention;
- deadlocks;
- concurrent updates;
- task cancellation.

Use deterministic coordination where possible.

For example:

```text
Task A ───────┐
              ├── synchronization point
Task B ───────┘
```

A concurrency test should control ordering rather than hoping a race occurs naturally.

---

## Property-Based Testing

Property-based testing generates many inputs to validate general invariants.

For example:

```text
Any valid quantity
        │
        ▼
calculate_total(quantity, price)
        │
        ▼
result >= 0
```

It is useful for:

- parsers;
- serializers;
- validation;
- mathematical transformations;
- state invariants;
- data processing.

Property-based testing complements example-based testing rather than replacing it.

---

## Mutation Testing

Mutation testing evaluates whether tests actually detect defects.

A mutation might change:

```python
if total >= 100:
```

to:

```python
if total > 100:
```

A strong test suite should fail.

Conceptually:

```text
Production Code
      │
      ▼
Create mutation
      │
      ▼
Run tests
      │
      ├── Tests fail → mutation killed
      └── Tests pass → surviving mutation
```

Surviving mutations can reveal weak assertions or missing behavioral coverage.

Mutation testing is usually more expensive than normal coverage and should be applied selectively.

---

## Test Doubles Strategy

Use the simplest appropriate test double.

| Double | Purpose |
|---|---|
| Dummy | Fulfills an unused parameter |
| Stub | Provides controlled responses |
| Fake | Lightweight working implementation |
| Spy | Records interactions |
| Mock | Verifies interactions/behavior |

Prefer fakes or real infrastructure when behavior is important.

Use mocks primarily to isolate boundaries or verify interaction contracts.

---

## Mocks vs Fakes

A mock:

```python
repository.get = AsyncMock(
    return_value=customer,
)
```

tests application behavior against a defined interaction.

A fake:

```python
class InMemoryCustomerRepository:
    def __init__(self):
        self.customers = {}

    async def get(self, customer_id):
        return self.customers.get(customer_id)
```

provides a lightweight implementation.

Fakes can sometimes produce more realistic tests with fewer brittle interaction assertions.

---

## Testing Observability

Important operational behavior can be tested too.

Examples:

- required log events;
- metric increments;
- trace attributes;
- error classification.

Avoid asserting every log line.

Prefer testing important observable contracts:

```text
Payment failure
      │
      ├── structured error log
      ├── failure metric
      └── trace status
```

Observability tests should remain focused because excessive logging assertions become brittle.

---

## Testing Time

Time-dependent code should avoid directly depending on wall-clock time where possible.

Prefer injectable clocks or controlled time.

Example:

```python
class Clock(Protocol):
    def now(self) -> datetime:
        ...
```

Tests can provide a deterministic implementation.

This is useful for:

- token expiration;
- TTL;
- scheduled jobs;
- retry backoff;
- subscription periods;
- rate limits.

---

## Testing Randomness and UUIDs

Randomness should be controlled when it affects assertions.

For unique identifiers, it is often better to verify properties:

```python
assert order.id is not None
```

rather than asserting a specific UUID.

If deterministic identifiers are required for a test, inject the identifier generator or patch the dependency at the lookup location.

---

## Testing File and Serialization Boundaries

File-processing systems should test:

- valid files;
- empty files;
- malformed files;
- encoding issues;
- large files;
- duplicate records;
- invalid schemas.

For JSON APIs, test:

- required fields;
- unexpected fields where relevant;
- type mismatches;
- nullability;
- serialization compatibility.

Coverage of parsing code does not guarantee that real-world input formats are handled correctly.

---

## Testing Performance

Performance tests answer different questions from functional tests.

Useful measurements include:

- latency;
- throughput;
- memory;
- CPU;
- database query count;
- connection-pool utilization.

Example targets:

```text
API
 ├── p50 latency
 ├── p95 latency
 ├── p99 latency
 ├── throughput
 └── error rate
```

Avoid placing heavy load tests in every pull request.

Use targeted performance tests in CI and dedicated environments for larger load tests.

---

## Testing Database Query Performance

Functional tests can verify correctness:

```python
orders = repository.list_orders(customer_id)
assert len(orders) == 10
```

Performance regressions may require additional assertions:

```text
Expected:
1 query

Regression:
101 queries
```

Exact query-count assertions are useful for targeted N+1 regressions but should not become universal implementation-detail assertions.

---

## Test Isolation Strategy

Tests should be independent whenever practical.

Common isolation techniques include:

- function-scoped fixtures;
- transaction rollback;
- database truncation;
- schema-per-worker;
- database-per-worker;
- unique Redis keys;
- unique Kafka topics;
- temporary directories;
- environment restoration.

The correct strategy depends on the system.

---

## Parallel Testing

Parallel execution can significantly reduce CI time.

Example:

```text
CI
 ├── Worker 1 → Tests A–D
 ├── Worker 2 → Tests E–H
 ├── Worker 3 → Tests I–L
 └── Worker 4 → Tests M–P
```

Parallel-safe tests must isolate:

- database state;
- files;
- ports;
- environment variables;
- Redis keys;
- Kafka topics;
- temporary resources.

Process isolation alone does not isolate shared external infrastructure.

---

## Test Data Strategy

Use factories for reusable valid data.

```python
customer = customer_factory(
    status="active",
)

order = order_factory(
    customer_id=customer.id,
)
```

Avoid:

- massive global fixtures;
- shared mutable test data;
- random data without reproducibility;
- hidden database writes;
- unrealistic domain state.

Test data should reflect production invariants without depending on production data.

---

## Test Organization

A scalable test suite can use:

```text
tests/
├── unit/
├── integration/
├── api/
├── contract/
├── e2e/
├── performance/
├── factories/
├── fixtures/
└── conftest.py
```

The exact structure should reflect repository size and deployment architecture.

Small projects may combine directories.

Large repositories benefit from clear ownership boundaries.

---

## Test Selection Strategy

Not every change requires every test.

A pull request pipeline can use layers:

```text
Developer Feedback
      │
      ▼
Fast unit tests
      │
      ▼
Component/API tests
      │
      ▼
Integration tests
      │
      ▼
Contract tests
      │
      ▼
Deployment
      │
      ▼
Smoke / E2E
```

The faster feedback loops should contain the tests most likely to identify local defects.

---

## CI Pipeline Strategy

A practical CI pipeline:

```text
                 Pull Request
                      │
                      ▼
             Lint + Type Check
                      │
                      ▼
                Unit Tests
                      │
                      ▼
            Component / API Tests
                      │
                      ▼
             Integration Tests
                      │
                      ▼
          Coverage + Quality Gates
                      │
                      ▼
              Contract Tests
                      │
                      ▼
                Build Image
                      │
                      ▼
             Deployment Tests
```

Expensive suites should run only where their confidence justifies the cost.

---

## Test Categorization

pytest markers can separate expensive test categories.

```python
@pytest.mark.integration
def test_postgres_transaction():
    ...


@pytest.mark.e2e
def test_checkout_workflow():
    ...
```

Example commands:

```bash
pytest -m "not integration"
```

```bash
pytest -m integration
```

```bash
pytest -m e2e
```

Markers should represent meaningful execution characteristics, not arbitrary team labels.

---

## Test Selection by Risk

A senior testing strategy considers risk.

| Change | High-value tests |
|---|---|
| Pure calculation | Unit |
| Service business rule | Unit + component |
| SQL query | Integration |
| API schema | API |
| Auth policy | Unit + API |
| Kafka consumer | Unit + integration |
| Database transaction | Integration |
| Payment workflow | API + integration + limited E2E |
| Cross-service contract | Contract |
| Deployment configuration | Smoke / deployment test |

This prevents over-testing simple changes while under-testing high-risk ones.

---

## Testing Distributed Systems

Distributed systems require testing beyond individual functions.

Important behaviors include:

- retries;
- duplicate messages;
- delayed messages;
- partial failures;
- timeouts;
- network failures;
- eventual consistency;
- idempotency;
- ordering;
- service version compatibility.

For example:

```text
Order Service
      │
      ▼
Kafka
      │
      ▼
Payment Service
      │
      ▼
Payment Provider
```

Test failures at each boundary rather than only testing the final success case.

---

## Eventual Consistency Testing

Distributed systems may not update all components synchronously.

Example:

```text
Create Order
     │
     ▼
Order = PENDING
     │
     ▼
Kafka Event
     │
     ▼
Payment Worker
     │
     ▼
Order = CONFIRMED
```

Tests should distinguish:

- immediate consistency requirements;
- eventual consistency requirements.

Avoid brittle tests that require distributed state to change instantly.

Use bounded polling or explicit synchronization mechanisms where appropriate.

---

## Testing Deployment Behavior

Production confidence includes deployment behavior.

Useful tests include:

- application startup;
- configuration validation;
- health checks;
- readiness checks;
- migration compatibility;
- graceful shutdown;
- environment configuration.

For Kubernetes:

```text
Pod Start
   │
   ▼
Startup
   │
   ▼
Readiness
   │
   ▼
Receive Traffic
   │
   ▼
SIGTERM
   │
   ▼
Graceful Shutdown
```

These concerns cannot be validated solely through unit tests.

---

## Security Testing Strategy

Security testing should be layered.

```text
Static Analysis
      +
Unit Security Tests
      +
API Authorization Tests
      +
Dependency Scanning
      +
Integration Tests
      +
Penetration Testing
```

Important test areas:

- authentication;
- authorization;
- tenant isolation;
- input validation;
- secrets handling;
- token expiration;
- privilege boundaries;
- rate limiting;
- sensitive-data exposure.

Never use real credentials or production personal data in automated tests.

---

## Reliability Testing

Reliability tests deliberately exercise failure behavior.

Examples:

- dependency timeout;
- database connection failure;
- Redis outage;
- Kafka failure;
- worker restart;
- duplicate message;
- transaction conflict.

A mature system should verify not only:

```text
Failure occurs
```

but:

```text
Failure
   │
   ▼
Detected
   │
   ▼
Classified
   │
   ▼
Recovered / Retried / Rejected
   │
   ▼
Consistent final state
```

---

## Disaster Recovery Testing

For systems with significant operational requirements, test recovery procedures rather than merely documenting them.

Examples:

- restore PostgreSQL backup;
- recreate infrastructure;
- restore configuration;
- recover Kafka-dependent workflows;
- validate application startup against restored data.

Disaster recovery confidence comes from exercising the recovery process.

---

## Test Environment Strategy

Environment fidelity matters.

| Environment | Purpose |
|---|---|
| Local | Fast development feedback |
| CI | Repeatable automated validation |
| Integration | Real infrastructure semantics |
| Staging | Production-like system validation |
| Production | Smoke/health/observability validation |

Do not make local environments unnecessarily complex.

Do make CI and staging representative enough to expose important production defects.

---

## Cost Considerations

Testing has infrastructure and execution costs.

Expensive resources include:

- PostgreSQL containers;
- Kafka clusters;
- Redis;
- cloud environments;
- large datasets;
- browser-based E2E tests;
- load testing.

Optimize with:

- fixture reuse for safe infrastructure;
- parallel workers;
- targeted integration suites;
- disposable environments;
- smaller realistic datasets;
- selective E2E execution.

Do not reduce critical integration coverage solely to minimize CI cost.

---

## Monitoring Test Health

Track the test suite itself.

Useful metrics include:

- total runtime;
- flaky-test rate;
- failure rate;
- retry rate;
- coverage;
- test count;
- slowest tests;
- CI queue time.

A test suite is an engineering system.

If developers stop trusting it, its practical value approaches zero.

---

## Flaky Tests

A flaky test produces different results without a relevant code change.

Common causes:

- race conditions;
- shared state;
- timing assumptions;
- external services;
- random data;
- unordered results;
- leaked background tasks.

Do not simply retry indefinitely.

Retries can hide real defects.

A better approach is:

```text
Flaky failure
     │
     ▼
Reproduce
     │
     ▼
Identify nondeterminism
     │
     ▼
Fix isolation / synchronization
     │
     ▼
Restore confidence
```

---

## Test Maintenance

Tests are production code for the development process.

Maintain:

- clear naming;
- small focused tests;
- reusable fixtures;
- stable factories;
- meaningful assertions;
- deterministic behavior.

Remove tests when the behavior they protect no longer exists.

Do not preserve obsolete tests simply because they increase coverage.

---

## Common Mistakes

### Testing Implementation Details

Bad:

```python
assert service._internal_cache["x"] == ...
```

when the contract is the returned behavior.

**Better:** assert observable behavior unless the internal structure is itself a meaningful contract.

### Too Many Mocks

Heavy mocking can produce tests that pass while production integrations fail.

**Better:** mock narrow boundaries and use integration tests for important infrastructure semantics.

### Too Many E2E Tests

Large E2E suites are slow and difficult to diagnose.

**Better:** keep E2E coverage focused on critical workflows.

### Ignoring Failure Paths

Happy-path-only suites provide weak reliability confidence.

**Better:** test dependency failures, retries, authorization failures, and invalid inputs.

### Shared Mutable Fixtures

Shared state causes order-dependent failures.

**Better:** isolate mutable state at function or appropriate worker scope.

### Arbitrary Sleeps

Using:

```python
await asyncio.sleep(1)
```

to wait for another task creates slow and flaky tests.

**Better:** use events, queues, task completion, or bounded polling with explicit conditions.

### Overusing Coverage

Adding tests solely to increase coverage can create low-value tests.

**Better:** use coverage to identify blind spots and then evaluate whether those paths matter.

---

## Production Pitfalls

### Testing Only the Application Layer

A service can have excellent unit coverage while PostgreSQL queries or Kafka behavior remain broken.

### Using Unrealistic Test Data

Factories that violate production invariants create false confidence.

### Testing Distributed Systems as Synchronous Systems

Immediate assertions against eventually consistent state create flaky tests.

### Ignoring Version Compatibility

Microservices can pass their own tests while incompatible versions fail in production.

Use contract testing and compatibility testing.

### Running Tests Against Shared Infrastructure

Shared databases, Redis instances, or Kafka topics can cause cross-test contamination.

Prefer disposable or isolated resources.

### Making CI Too Slow

If feedback takes too long, developers stop running tests locally.

Maintain fast test layers and move expensive suites to appropriate pipeline stages.

### Making CI Too Weak

A fast pipeline that skips critical integration behavior creates false confidence.

Optimize the pipeline rather than simply removing tests.

---

## Recommended Strategy for a Python Backend

A balanced backend test strategy is:

```text
                    Production Code
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
       Unit Tests     Component Tests   Static Checks
          │               │
          └───────────────┼────────────────┘
                          ▼
                    API Tests
                          │
                          ▼
                 Integration Tests
                 ├── PostgreSQL
                 ├── Redis
                 ├── Kafka
                 └── External services
                          │
                          ▼
                   Contract Tests
                          │
                          ▼
                 Limited E2E Tests
                          │
                          ▼
               Deployment / Smoke Tests
```

A typical distribution might be:

| Layer | Volume | Speed | Confidence |
|---|---:|---:|---:|
| Unit | High | Very fast | Local behavior |
| Component | Medium | Fast | Application composition |
| API | Medium | Moderate | External interface |
| Integration | Medium | Moderate/slow | Real dependencies |
| Contract | Low/medium | Moderate | Service compatibility |
| E2E | Low | Slow | Critical workflows |
| Performance | Low | Expensive | Capacity/latency |
| Security | Targeted | Variable | Security properties |

The exact ratio should follow system risk and architecture.

---

## Senior-Level Testing Principles

### Test Behavior, Not Lines

Coverage tells you where execution occurred.

Assertions tell you what behavior is protected.

### Test at the Lowest Useful Layer

If a business rule can be completely verified with a unit test, do not require an E2E test for every variation.

### Test Real Boundaries

Use real PostgreSQL, Redis, Kafka, HTTP, or gRPC integration tests when their semantics matter.

### Make Failures Cheap to Diagnose

A failure in a unit test should ideally identify a small area of responsibility.

### Design for Determinism

Control time, randomness, concurrency, external dependencies, and test data.

### Treat Tests as Architecture Feedback

If code is extremely difficult to test, investigate whether the production design has excessive coupling.

---

## Testing Decision Guide

| Question | Preferred approach |
|---|---|
| Is this pure business logic? | Unit test |
| Does it require multiple internal components? | Component test |
| Does correctness depend on PostgreSQL? | Integration test |
| Does correctness depend on Redis/Kafka? | Integration test |
| Is it an HTTP/RPC contract? | API/contract test |
| Is it cross-service compatibility? | Contract test |
| Is it a critical user workflow? | Limited E2E test |
| Is it a performance requirement? | Performance test |
| Is it a security boundary? | Security-focused tests |
| Is the input space broad? | Property-based testing |
| Did a production defect occur? | Regression test |

---

## Test Review Checklist

### Correctness

- [ ] Happy path is covered.
- [ ] Important failure paths are covered.
- [ ] Boundary conditions are tested.
- [ ] Business invariants are asserted.
- [ ] State transitions are tested.

### Integration

- [ ] Real database semantics are tested where required.
- [ ] External dependency behavior is tested at the appropriate layer.
- [ ] Transactions are tested.
- [ ] Messaging behavior is tested.
- [ ] Contract compatibility is verified.

### Reliability

- [ ] Retries are tested.
- [ ] Idempotency is tested.
- [ ] Timeouts are tested.
- [ ] Cancellation is tested for async workflows.
- [ ] Duplicate processing is considered.

### Isolation

- [ ] Tests are order-independent.
- [ ] Mutable state is isolated.
- [ ] Temporary resources are cleaned up.
- [ ] Parallel execution is safe.
- [ ] Test configuration cannot target production.

### CI/CD

- [ ] Fast tests run early.
- [ ] Expensive tests run at appropriate stages.
- [ ] Coverage is measured consistently.
- [ ] Flaky tests are investigated.
- [ ] Test failures fail the pipeline.
- [ ] Critical deployment behavior has smoke coverage.

---

## Interview Traps

### What Is the Testing Pyramid?

It is a heuristic that favors many fast, isolated tests and fewer expensive, broad tests. It is not a rigid requirement.

### Should Everything Be an Integration Test?

No. Integration tests provide realism but are slower and harder to diagnose. Unit tests remain valuable for isolated business behavior.

### Why Not Mock the Database Everywhere?

Mocks can verify application interaction but cannot validate SQL, constraints, transactions, locking, query planning, or database-specific semantics.

### Why Are E2E Tests Limited?

They provide broad confidence but are slower, more expensive, more environment-dependent, and harder to diagnose than lower-level tests.

### What Should Be Tested at the API Layer?

Externally visible behavior: status codes, schemas, authentication, authorization, validation, persistence effects, error contracts, and important workflow behavior.

### What Is Contract Testing?

It verifies that independently deployed services agree on an interface and remain compatible as they evolve.

### How Do You Test Retry Logic?

Test retryable failures, non-retryable failures, maximum attempts, final failure, backoff behavior where important, and idempotency.

### How Do You Test Eventual Consistency?

Test the expected intermediate state and then wait for a clearly defined condition using bounded polling or explicit synchronization rather than arbitrary sleeps.

### How Do You Test Concurrency Reliably?

Control execution order with synchronization primitives and deterministic coordination rather than relying on timing races.

### Does High Code Coverage Mean High Test Quality?

No. Coverage measures execution. It does not prove that assertions are meaningful or that integrations, distributed behavior, security, or failure recovery are correct.

### What Is the Senior-Level Testing Principle?

Choose the **lowest-cost test layer that provides sufficient confidence**, then add broader tests where integration, compatibility, deployment, or business risk requires them.

## Key Takeaways

- **Use multiple test layers:** unit, component, integration, API, contract, and targeted E2E tests provide different forms of confidence.
- **Test behavior and risk, not percentages:** coverage is useful for finding blind spots, but meaningful assertions and critical-path testing matter more.
- **Use real infrastructure where semantics matter:** PostgreSQL, Redis, Kafka, transactions, concurrency, and external contracts cannot be fully validated with mocks.
- **Design for deterministic isolation:** control shared state, time, randomness, concurrency, external dependencies, and test data so failures remain reproducible.
- **Optimize the testing system itself:** keep fast feedback early, expensive tests targeted, CI reliable, and flaky tests treated as defects rather than normalized noise.