# 01- Testing Fundamentals

## Overview

Testing is the systematic verification of software behavior against explicit expectations.

For production Python systems, testing is not primarily about maximizing the number of test cases. It is about creating fast, reliable feedback that detects incorrect behavior, protects important contracts, and makes refactoring safer.

A backend system typically needs multiple testing levels:

```text
                    ┌──────────────────────┐
                    │   Production System  │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │ End-to-End / System  │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │ API / Integration    │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │ Service / Component  │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │ Unit Tests           │
                    └──────────────────────┘
```

The important distinction is not simply *what tool is used*, but **what boundary is being verified**.

Python's testing ecosystem commonly includes:

- `unittest` from the standard library;
- `pytest`;
- fixtures;
- parametrization;
- mocks and fakes;
- API test clients;
- database integration tests;
- contract tests;
- property-based testing;
- coverage tooling;
- static type checking;
- linters and formatters.

This section begins with the fundamental testing model before moving into more specialized techniques.

---

## Why Testing Matters

Without tests, correctness is primarily established through:

```text
code review
+
manual verification
+
production observation
```

This becomes increasingly expensive as a system grows.

Tests provide executable expectations:

```text
Requirement
    ↓
Expected behavior
    ↓
Test
    ↓
Implementation
    ↓
Automated verification
```

A useful test suite provides confidence when engineers:

- refactor code;
- upgrade dependencies;
- change database schemas;
- modify API contracts;
- optimize performance;
- add concurrency;
- change deployment configuration.

Testing is therefore a maintainability mechanism as much as a correctness mechanism.

---

## What Should Be Tested?

Test **observable behavior and important contracts**, not implementation details by default.

For a backend service:

```text
Input
  ↓
Validation
  ↓
Business rules
  ↓
Persistence
  ↓
External side effects
  ↓
Output
```

Tests should establish important guarantees at the appropriate boundary.

For example:

```text
"An inactive customer cannot create an order."
```

is a business behavior.

A test should verify that behavior without unnecessarily asserting:

```text
the service called private_method_17()
```

unless that implementation detail itself is part of the contract.

---

## Test Pyramid

A common model is the test pyramid:

```text
              /\
             /  \
            / E2E\
           /------\
          /  API   \
         /----------\
        / Integration \
       /--------------\
      /   Unit Tests   \
     /------------------\
```

The lower layers generally provide:

- faster execution;
- greater isolation;
- easier diagnosis;
- lower infrastructure cost.

The upper layers provide stronger system-level confidence but are typically:

- slower;
- more environment-dependent;
- more expensive to maintain.

A mature system uses a **balanced distribution**, not an arbitrary numerical ratio.

---

## Test Types

| Test type | Primary purpose | Typical speed | Infrastructure |
|---|---|---:|---|
| Unit | Isolated behavior | Very fast | None/minimal |
| Component | One component with controlled dependencies | Fast | Limited |
| Integration | Real dependency interaction | Medium | Database/cache/etc. |
| API | HTTP/API contract and behavior | Medium | Application |
| Contract | Compatibility between systems | Medium | Consumer/provider |
| End-to-end | Complete user workflow | Slow | Full stack |
| Performance | Latency/throughput/capacity | Variable | Production-like |
| Security | Security properties and abuse cases | Variable | Depends |
| Property-based | General invariants over generated inputs | Fast/medium | Usually minimal |

The correct test type depends on the behavior being verified.

---

## Unit Tests

A unit test verifies a small unit of behavior with controlled dependencies.

Example:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Order:
    total: int


def calculate_discount(order: Order, percentage: int) -> int:
    if not 0 <= percentage <= 100:
        raise ValueError("percentage must be between 0 and 100")

    return order.total * percentage // 100
```

A unit test can verify the business rule without involving PostgreSQL, Redis, or HTTP.

```python
import pytest

from app.orders import Order, calculate_discount


@pytest.mark.parametrize(
    ("total", "percentage", "expected"),
    [
        (1000, 10, 100),
        (2500, 20, 500),
        (999, 0, 0),
    ],
)
def test_calculate_discount(total: int, percentage: int, expected: int) -> None:
    assert calculate_discount(Order(total=total), percentage) == expected


def test_calculate_discount_rejects_invalid_percentage() -> None:
    with pytest.raises(ValueError, match="percentage"):
        calculate_discount(Order(total=1000), 101)
```

The test is:

- deterministic;
- fast;
- isolated;
- easy to diagnose.

---

## Test Anatomy

A useful mental model is:

```text
Arrange
   ↓
Act
   ↓
Assert
```

Example:

```python
def test_create_order() -> None:
    # Arrange
    customer = Customer(id="customer-1")
    service = OrderService(...)

    # Act
    order = service.create_order(customer, amount=1000)

    # Assert
    assert order.amount == 1000
```

The three phases make the test's intent explicit.

Avoid putting substantial unrelated logic into the test itself.

---

## What Makes a Good Test?

A good test should usually be:

- deterministic;
- isolated at the appropriate boundary;
- readable;
- fast enough for frequent execution;
- focused on one behavior;
- independent of execution order;
- reproducible;
- meaningful when it fails.

A useful test failure should answer:

> What behavior broke?

rather than:

> Some internal implementation changed.

---

## Test Independence

Tests should generally not depend on previous tests.

Bad:

```text
test_create_user
      ↓
test_update_user assumes created user
      ↓
test_delete_user assumes updated user
```

If one test fails, the rest become unreliable.

Prefer:

```text
test_create_user
test_update_user
test_delete_user
```

where each test establishes its own required state.

---

## Determinism

Tests should not depend unpredictably on:

- current wall-clock time;
- random values;
- external network services;
- unordered external state;
- shared databases;
- test execution order;
- machine-specific filesystem state.

Inject unstable dependencies when necessary.

For example:

```python
from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        ...
```

The production implementation can use the real clock while tests can provide a fixed clock.

---

## Test Isolation

Isolation can exist at different levels.

```text
Unit
→ isolated dependencies

Integration
→ isolated test data/resources

E2E
→ isolated environment or controlled dataset
```

Isolation does not mean every test must mock every dependency.

A PostgreSQL integration test may intentionally use a real PostgreSQL instance because database semantics are what the test needs to verify.

---

## Test Fixtures

Fixtures provide reusable test setup.

With `pytest`:

```python
import pytest


@pytest.fixture
def customer() -> Customer:
    return Customer(
        id="customer-1",
        active=True,
    )
```

A test can consume the fixture:

```python
def test_active_customer_can_create_order(customer: Customer) -> None:
    assert customer.active is True
```

Fixtures are useful for:

- shared setup;
- resource lifecycle;
- test data;
- database sessions;
- API clients;
- configuration.

However, excessive fixture nesting can make tests difficult to understand.

---

## Fixture Scope

Pytest fixtures can have different lifetimes.

Common scopes include:

| Scope | Lifetime |
|---|---|
| `function` | One test |
| `class` | One test class |
| `module` | One module |
| `package` | One package |
| `session` | Entire test session |

Use the narrowest scope that provides the required efficiency.

A session-scoped mutable database state can create test coupling if not carefully managed.

---

## Test Data

Test data should be:

- minimal;
- explicit;
- relevant;
- deterministic.

Prefer:

```python
customer = Customer(
    id="customer-1",
    active=True,
)
```

over a large fixture containing dozens of unrelated fields.

Excessive test data creates hidden dependencies.

---

## Factories

Factories are useful when domain objects require substantial setup.

Example:

```python
def build_customer(
    *,
    customer_id: str = "customer-1",
    active: bool = True,
) -> Customer:
    return Customer(
        id=customer_id,
        active=active,
    )
```

Tests can override only the relevant behavior:

```python
def test_inactive_customer_is_rejected() -> None:
    customer = build_customer(active=False)

    ...
```

Factories should remain understandable.

A factory with dozens of implicit defaults can hide the actual test scenario.

---

## Assertions

Assertions should express the behavior being verified.

Prefer:

```python
assert response.status_code == 201
assert response.json()["status"] == "created"
```

over vague assertions:

```python
assert response
```

For exceptions:

```python
with pytest.raises(NotFoundError):
    service.get_order("missing")
```

Assertions should be specific enough to catch meaningful regressions without unnecessarily coupling tests to irrelevant representation details.

---

## Testing Exceptions

Exceptions are part of a function or service contract when callers depend on them.

Example:

```python
def test_missing_order_raises_not_found() -> None:
    with pytest.raises(OrderNotFound):
        service.get_order("missing-order")
```

When the error message is itself part of the contract, test it.

Otherwise, prefer asserting the exception type and relevant structured attributes.

---

## Testing Return Values

Do not test only that a function executes.

This:

```python
service.create_order(...)
```

does not prove much.

Prefer:

```python
order = service.create_order(...)

assert order.status == OrderStatus.CREATED
assert order.total == 2500
```

Test the observable result that matters to callers.

---

## Testing Side Effects

Side effects include:

- database writes;
- messages;
- emails;
- HTTP calls;
- cache updates;
- filesystem writes.

A service test may verify that the correct boundary was invoked.

```python
publisher.publish.assert_called_once_with(
    OrderCreated(order_id="order-1")
)
```

But do not make every unit test assert every internal call.

Use integration tests when the actual integration behavior matters.

---

## Mocking

Mocking replaces a dependency with a controlled test double.

Example:

```python
from unittest.mock import Mock


payment_client = Mock()
payment_client.charge.return_value = PaymentResult(
    transaction_id="txn-1",
)

service = PaymentService(payment_client=payment_client)

result = service.pay(order_id="order-1", amount=1000)

assert result.transaction_id == "txn-1"
payment_client.charge.assert_called_once()
```

Mocking is useful when:

- the dependency is slow;
- the dependency is external;
- the behavior is difficult to reproduce;
- the test needs precise failure simulation.

---

## Mocking Pitfalls

Mocks can create false confidence.

If the real dependency behaves differently from the mock, the test may pass while production fails.

Bad:

```text
Mock says:
"Database accepts this query"

Production:
PostgreSQL rejects query
```

Use integration tests to verify important real dependency behavior.

A good rule is:

> Mock boundaries when isolation provides value; integrate where the real behavior is part of what you need to verify.

---

## Mocks vs Fakes vs Stubs

| Test double | Purpose |
|---|---|
| Stub | Provides predetermined responses |
| Mock | Verifies interactions |
| Fake | Lightweight working implementation |
| Spy | Records calls to an otherwise real implementation |

For many application services, a fake can be easier to maintain than extensive mock configuration.

Example:

```python
class InMemoryOrderRepository:
    def __init__(self) -> None:
        self.orders: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self.orders[order.id] = order

    def get(self, order_id: str) -> Order | None:
        return self.orders.get(order_id)
```

The fake can test service behavior without requiring PostgreSQL.

---

## Integration Tests

Integration tests verify interactions with real infrastructure or substantial components.

Examples:

```text
Application
    ↓
SQLAlchemy
    ↓
PostgreSQL
```

or:

```text
Application
    ↓
Redis
```

Integration tests are particularly important for:

- SQL queries;
- transactions;
- constraints;
- indexes;
- serialization;
- connection behavior;
- Redis semantics;
- Kafka integration.

---

## Database Integration Tests

Application-level mocks cannot verify actual PostgreSQL behavior.

A real database test can detect:

- invalid SQL;
- constraint violations;
- transaction behavior;
- isolation issues;
- incorrect joins;
- ORM mapping errors;
- index-dependent query behavior.

A typical flow is:

```text
Test
 ↓
Application service
 ↓
Repository
 ↓
Connection pool
 ↓
PostgreSQL
```

For important database behavior, prefer testing against the same database engine used in production.

---

## Test Database Isolation

Database tests need isolation.

Common approaches include:

- transaction rollback;
- per-test schemas;
- disposable databases;
- containers;
- database snapshots;
- carefully controlled fixtures.

The appropriate approach depends on the application and test suite size.

The key requirement is that one test should not silently depend on another test's committed state.

---

## API Testing

API tests verify behavior at the HTTP boundary.

Example with FastAPI:

```python
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_order() -> None:
    response = client.post(
        "/orders",
        json={
            "customer_id": "customer-1",
            "amount": 2500,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["amount"] == 2500
    assert body["status"] == "created"
```

API tests can verify:

- routing;
- authentication;
- authorization;
- validation;
- status codes;
- response schemas;
- error contracts.

They should not necessarily replace lower-level service tests.

---

## REST API Contract Testing

API contracts include:

- request schemas;
- response schemas;
- status codes;
- headers;
- error formats;
- authentication requirements.

For example:

```text
POST /orders
        ↓
201 Created
        ↓
{
  "id": "...",
  "status": "created"
}
```

Contract tests help prevent accidental breaking changes.

---

## gRPC Testing

gRPC tests should verify:

- request/response schemas;
- status codes;
- metadata;
- deadlines;
- authentication;
- error behavior.

The same architectural principle applies:

```text
gRPC transport
      ↓
Application service
      ↓
Infrastructure
```

Do not duplicate business logic specifically for gRPC tests.

---

## Django Testing

Django provides testing support for:

- views;
- URL routing;
- ORM behavior;
- forms;
- middleware;
- authentication;
- transactions.

Django tests can use the framework's test database facilities to isolate database state.

The important distinction remains:

```text
unit behavior
vs
Django integration behavior
```

Use the appropriate level rather than making every test exercise the entire framework.

---

## Testing Authentication and Authorization

Security behavior deserves explicit tests.

Examples:

```text
Unauthenticated → 401
Authenticated but unauthorized → 403
Authorized → success
```

Test:

- missing credentials;
- invalid credentials;
- expired tokens;
- insufficient roles;
- resource ownership;
- tenant boundaries;
- privileged operations.

Authorization bugs can be more serious than ordinary functional bugs, so critical access-control paths should have direct regression tests.

---

## Testing Validation

Test both valid and invalid input.

For example:

```text
valid amount
zero amount
negative amount
missing field
wrong type
oversized value
unknown field
malformed identifier
```

For API validation, assert the stable contract rather than depending unnecessarily on framework-internal error formatting.

---

## Parametrization

Parametrization avoids repetitive tests.

```python
import pytest


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, True),
        (1, True),
        (-1, False),
        (100, True),
        (101, False),
    ],
)
def test_valid_percentage(value: int, expected: bool) -> None:
    assert is_valid_percentage(value) is expected
```

Use parametrization when multiple inputs exercise the same behavior.

Avoid turning every edge case into a large opaque parameter table.

---

## Boundary Testing

Many defects occur at boundaries.

For numeric values:

```text
minimum - 1
minimum
minimum + 1
maximum - 1
maximum
maximum + 1
```

For strings:

```text
empty
minimum length
maximum length
maximum + 1
```

For pagination:

```text
first page
middle page
last page
empty page
invalid cursor
```

Boundary tests are particularly useful for request validation and business constraints.

---

## Testing Time

Time-dependent logic should not rely directly on the system clock when deterministic behavior matters.

Bad:

```python
if datetime.now() > expires_at:
    ...
```

Prefer injecting a clock or isolating time access.

Then tests can use:

```text
now = 2026-09-06T10:00:00Z
expires = 2026-09-06T10:01:00Z
```

and verify deterministic behavior.

---

## Testing Randomness

Randomness can make tests flaky.

Inject a random source or deterministic seed where appropriate.

For security-sensitive randomness, do not replace cryptographically secure randomness with predictable test behavior in production.

Tests should verify the contract without weakening production security.

---

## Testing External APIs

Do not make normal unit tests depend on live third-party APIs.

External API tests can fail because of:

- network outages;
- provider changes;
- rate limits;
- credentials;
- regional differences;
- provider latency.

Use:

```text
Unit tests
→ fake/mock provider

Integration/contract tests
→ controlled provider or sandbox

Production monitoring
→ real provider behavior
```

---

## Contract Tests for External Services

When an application depends on another service, contract testing can verify assumptions such as:

```text
request schema
response schema
status behavior
required fields
error semantics
```

This is particularly useful for microservices where independently deployed systems must remain compatible.

---

## Testing Retries

Retry behavior should be tested explicitly.

Example scenarios:

```text
attempt 1 → timeout
attempt 2 → success
```

and:

```text
attempt 1 → permanent 4xx
→ no retry
```

Also test:

- maximum attempts;
- backoff;
- jitter behavior where observable;
- idempotency;
- exhausted retries;
- dead-letter behavior.

Retry tests are important because incorrect retry logic can amplify production outages.

---

## Testing Idempotency

For operations such as:

```text
POST /payments
```

test repeated execution.

```text
same idempotency key
       ↓
first request  → creates payment
second request → returns existing result
```

The test should verify the durable behavior rather than only whether an application-level dictionary was consulted.

---

## Testing Transactions

Transaction behavior should be tested with a real database when correctness depends on database semantics.

Important scenarios include:

- commit;
- rollback;
- constraint failure;
- concurrent updates;
- deadlocks;
- serialization failures;
- transaction boundaries.

A mock cannot reliably reproduce PostgreSQL's transaction semantics.

---

## Testing Concurrency

Concurrency defects are often nondeterministic.

Tests can still target important properties:

```text
two requests update same resource
        ↓
only one succeeds
```

or:

```text
two workers process same message
        ↓
final state remains correct
```

Use:

- synchronization primitives;
- barriers;
- controlled scheduling;
- real databases;
- repeated stress tests.

Avoid assuming that a single passing concurrency test proves race-freedom.

---

## Testing Asyncio

Async tests should exercise actual async behavior.

With pytest and an appropriate async plugin:

```python
import pytest


@pytest.mark.asyncio
async def test_fetch_order() -> None:
    order = await service.fetch_order("order-1")

    assert order.id == "order-1"
```

Test:

- cancellation;
- timeouts;
- concurrent tasks;
- task failures;
- resource cleanup.

Blocking synchronous code inside async paths should also be detected through performance and integration testing.

---

## Testing Background Jobs

Background jobs should be tested independently from HTTP request handling.

Example:

```text
API test
→ verifies job creation/enqueue contract

Worker test
→ verifies task behavior

Integration test
→ verifies queue + worker + database interaction
```

Test:

- successful execution;
- retry;
- duplicate delivery;
- timeout;
- permanent failure;
- idempotency;
- job state transitions.

---

## Testing Kafka Consumers

Kafka consumers should be tested around processing semantics.

Important cases include:

```text
message received
 ↓
processing succeeds
 ↓
offset committed
```

and:

```text
message received
 ↓
processing fails
 ↓
offset not treated as successfully processed
 ↓
retry/recovery
```

Use integration environments when testing actual Kafka behavior.

---

## Testing Redis

Redis integration tests should verify actual semantics for operations that matter.

Examples:

- TTL behavior;
- atomic commands;
- transactions;
- distributed locks where applicable;
- serialization;
- cache invalidation.

Do not assume an in-memory Python dictionary accurately represents Redis behavior.

---

## Test Naming

Names should communicate behavior.

Prefer:

```python
def test_inactive_customer_cannot_create_order():
    ...
```

over:

```python
def test_order_service_3():
    ...
```

For complex behavior:

```python
def test_payment_is_not_retried_after_permanent_provider_error():
    ...
```

Good names reduce the need to inspect implementation details when a test fails.

---

## Arrange Tests Around Behavior

A test suite should make important domain rules discoverable.

For example:

```text
orders/
├── test_creation.py
├── test_cancellation.py
├── test_payment.py
└── test_authorization.py
```

or another structure consistent with the codebase.

The organization should help engineers locate tests associated with a behavior quickly.

---

## Testing Error Responses

Backend APIs need stable error behavior.

Test:

```text
400 → invalid request
401 → unauthenticated
403 → unauthorized
404 → resource missing
409 → conflict
422 → validation failure where applicable
429 → rate limited
5xx → server failure
```

The exact status code depends on the API contract.

Tests should verify that errors do not accidentally expose:

- stack traces;
- database credentials;
- internal infrastructure details;
- secrets;
- unnecessary sensitive information.

---

## Flaky Tests

A flaky test sometimes passes and sometimes fails without a relevant code change.

Common causes include:

- timing assumptions;
- shared mutable state;
- test-order dependence;
- real external services;
- race conditions;
- uncontrolled randomness;
- current-time dependence;
- filesystem/network assumptions;
- insufficient cleanup.

Flaky tests are dangerous because engineers eventually stop trusting the test suite.

Treat recurring flakes as defects.

---

## Test Cleanup

Resources must be cleaned up after tests.

Examples:

```text
database connections
temporary files
Redis keys
Kafka consumers
threads
async tasks
environment variables
mocks
```

Use fixtures and context managers where appropriate.

A test that passes while leaking resources can eventually destabilize the entire test process.

---

## Test Order

Tests should ideally pass regardless of execution order.

If order matters accidentally:

```text
test A modifies global state
 ↓
test B expects clean state
```

the suite contains hidden coupling.

Run tests in randomized order or isolated workers when useful to detect order dependence.

---

## Test Parallelism

Large suites may run tests concurrently.

Benefits:

- shorter CI time;
- better CPU utilization.

Risks:

- shared database state;
- port conflicts;
- filesystem collisions;
- global mutable state;
- race conditions in test infrastructure.

Parallel execution should be enabled only after tests are sufficiently isolated.

---

## Coverage

Coverage measures which code was executed by tests.

Common forms include:

- statement coverage;
- branch coverage;
- condition coverage.

Coverage is useful as a diagnostic signal.

It is not proof of correctness.

This test can provide coverage without meaningful verification:

```python
def test_order() -> None:
    service.create_order(...)
```

without asserting the result.

Prefer:

```text
coverage
+
meaningful assertions
+
risk-based test selection
```

---

## Coverage Strategy

Do not optimize solely for a global percentage.

High-value targets include:

- authentication;
- authorization;
- financial operations;
- transaction logic;
- state transitions;
- retry behavior;
- idempotency;
- data transformation;
- security-sensitive code.

Low-value targets may include trivial wrappers with no meaningful behavior.

Coverage should guide investigation, not become the sole engineering objective.

---

## Testing in CI/CD

A typical pipeline is:

```text
Commit
  ↓
Formatting
  ↓
Linting
  ↓
Type checking
  ↓
Unit tests
  ↓
Integration tests
  ↓
API/contract tests
  ↓
Security checks
  ↓
Build artifact
  ↓
Deploy
```

Fast tests should run early.

Slower tests can run in later stages or parallel jobs.

The goal is rapid feedback without sacrificing important integration confidence.

---

## Local vs CI vs Production-Like Tests

| Environment | Primary goal |
|---|---|
| Local | Fast developer feedback |
| CI | Repeatable automated verification |
| Staging | System integration and deployment validation |
| Production | Runtime monitoring and controlled verification |

Do not move all testing into staging simply because it resembles production.

Developers need fast local feedback.

---

## Test Environment Configuration

Test configuration should be explicit.

For example:

```text
APP_ENV=test
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

Avoid accidentally connecting tests to production resources.

Safety controls should make this difficult or impossible.

A test process should never be able to silently delete production data because an environment variable was misconfigured.

---

## Testing Security

Security tests should verify both normal and adversarial behavior.

Examples:

```text
missing authentication
invalid authentication
privilege escalation
cross-tenant access
SQL injection attempts
malicious file uploads
oversized requests
SSRF payloads
replay attacks
invalid webhook signatures
```

Security testing should complement normal functional testing.

---

## Testing Data Isolation

Multi-tenant systems require explicit isolation tests.

Example:

```text
Tenant A
 └── order A

Tenant B
 └── order B
```

Test that:

```text
Tenant A request
→ cannot access order B
```

This should be a regression test for every critical tenant-scoped access path.

---

## Testing State Machines

Systems with explicit states should test valid and invalid transitions.

Example:

```text
PENDING
  ├── PAID
  └── CANCELLED

PAID
  └── REFUNDED
```

Tests should verify:

```text
PENDING → PAID       valid
PENDING → CANCELLED  valid
PAID → REFUNDED      valid
PAID → CANCELLED     invalid
```

State transition tests are particularly useful for orders, payments, jobs, workflows, and deployments.

---

## Testing Serialization

Serialization boundaries should be tested explicitly.

Examples:

```text
Python object
 ↓
JSON
 ↓
HTTP
```

and:

```text
Database record
 ↓
ORM model
 ↓
API schema
```

Verify:

- required fields;
- types;
- optional fields;
- backward compatibility;
- timezone handling;
- precision;
- enum representation.

---

## Testing Timezones and Money

These are common sources of production defects.

For time:

```text
UTC
timezone-aware datetimes
DST transitions
boundary dates
```

For money:

```text
decimal precision
rounding
currency
zero
negative values
large amounts
```

Do not rely only on ordinary happy-path values.

---

## Testing File Processing

File-processing tests should cover:

- empty files;
- large files;
- malformed input;
- unexpected encoding;
- invalid structure;
- duplicate records;
- partial processing;
- temporary-file cleanup.

For large-file systems, include tests that verify the implementation does not unnecessarily materialize the entire file into memory.

---

## Testing Performance

Functional tests answer:

> Is the behavior correct?

Performance tests answer:

> Does it meet the required latency, throughput, and resource constraints?

Do not turn every unit test into a benchmark.

Use specialized performance testing for:

- API throughput;
- database query performance;
- queue processing;
- serialization;
- memory usage;
- concurrency.

---

## Testing Memory Behavior

Memory-sensitive applications should test workloads that resemble production.

Useful measurements include:

- RSS;
- allocation growth;
- peak memory;
- queue depth;
- batch size;
- worker memory.

Tools such as `tracemalloc` can help diagnose Python-level allocations, while process-level metrics are needed to understand total memory consumption.

---

## Testing Observability

Observability behavior can also be tested.

Examples:

```text
request
 ↓
trace ID
 ↓
structured log
 ↓
downstream call
```

Verify important requirements such as:

- required log fields;
- correlation IDs;
- expected metrics;
- error recording.

Do not make tests unnecessarily dependent on exact log wording.

Prefer stable event names and structured fields.

---

## Testing Graceful Shutdown

Shutdown behavior should be tested explicitly.

Scenarios include:

```text
shutdown while idle
shutdown during HTTP request
shutdown during database transaction
shutdown during background job
shutdown during message processing
shutdown during external API call
shutdown deadline exceeded
```

Verify that:

- new work stops;
- safe in-flight work drains;
- resources close;
- unfinished durable work remains recoverable;
- shutdown completes within the configured deadline.

---

## Test Reliability Model

A useful reliability model is:

```text
Test Reliability
    =
Determinism
+
Isolation
+
Meaningful Assertions
+
Controlled Dependencies
+
Repeatability
```

If one of these is weak, the suite becomes less trustworthy.

---

## Test Design and Architecture

Good architecture makes testing easier.

For example:

```text
HTTP Handler
     ↓
OrderService
     ↓
OrderRepository
     ↓
PostgreSQL
```

The service can be unit-tested with a fake repository:

```text
OrderService
     ↓
FakeOrderRepository
```

Then the repository can be integration-tested independently:

```text
OrderRepository
     ↓
Real PostgreSQL
```

Finally, API tests can verify the transport boundary.

This creates focused tests without sacrificing real integration coverage.

---

## Testing Anti-Patterns

### Testing Implementation Details

Tests tightly coupled to private methods often break during harmless refactoring.

Test behavior unless implementation itself is contractual.

### Mocking Everything

A fully mocked system can pass tests while failing in production.

Real integrations are necessary where integration behavior matters.

### Testing Nothing but End-to-End

E2E tests are valuable but expensive and difficult to diagnose.

Use lower-level tests for most local behavior.

### Excessive Test Duplication

Repeated setup makes suites harder to maintain.

Use fixtures and factories where they improve clarity.

### Giant Fixtures

Large shared fixtures hide scenario-specific requirements.

Keep test data focused.

### Ignoring Flaky Tests

A flaky test is not harmless noise.

It reduces trust in the entire suite.

### Overusing Coverage Targets

A high percentage does not guarantee meaningful tests.

Measure risk coverage and behavioral confidence.

### Tests Depending on Production

Tests must be isolated from production data and credentials.

Use explicit test resources.

---

## Production Testing Strategy

A mature backend may use:

```text
                ┌─────────────────────┐
                │ Unit Tests          │
                │ Fast feedback       │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │ Integration Tests   │
                │ Real dependencies   │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │ Contract/API Tests  │
                │ Service boundaries  │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │ E2E / Staging       │
                │ Full workflows      │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │ Production          │
                │ Monitoring + checks │
                └─────────────────────┘
```

Each layer answers different questions.

No single testing technique provides complete confidence.

---

## Test Selection Framework

When deciding how to test a behavior, ask:

| Question | Preferred approach |
|---|---|
| Pure business rule? | Unit test |
| Service orchestration? | Unit/component test |
| PostgreSQL semantics? | Integration test |
| Redis semantics? | Integration test |
| HTTP contract? | API/contract test |
| External service compatibility? | Contract/integration test |
| Complete user workflow? | E2E test |
| Throughput/latency? | Performance test |
| Security boundary? | Security + functional test |
| Concurrency behavior? | Integration/stress test |
| Memory behavior? | Workload/performance test |

The goal is to put each assertion at the lowest level that can reliably verify it.

---

## Practical Backend Example

Consider:

```text
POST /orders
```

with this workflow:

```text
HTTP request
   ↓
Authentication
   ↓
Validation
   ↓
OrderService
   ↓
PostgreSQL transaction
   ├── create order
   └── insert outbox event
   ↓
COMMIT
   ↓
Response
```

A balanced test strategy could be:

### Unit

Verify:

```text
inactive customer → rejected
invalid amount → rejected
valid order → created
```

### Service

Verify:

```text
authorized customer
→ repository called
→ domain rules applied
→ expected result returned
```

### Integration

Verify:

```text
PostgreSQL
→ constraints
→ transaction rollback
→ unique idempotency key
```

### API

Verify:

```text
POST /orders
→ authentication
→ validation
→ status code
→ response schema
```

### Contract

Verify:

```text
API response
→ expected schema consumed by clients
```

### End-to-End

Verify:

```text
client
→ API
→ PostgreSQL
→ outbox
→ event processing
```

This gives substantially better confidence than attempting to verify everything through one large E2E test.

---

## Testing Checklist

### Test Design

- [ ] Test observable behavior.
- [ ] Keep tests deterministic.
- [ ] Keep tests independent.
- [ ] Use meaningful assertions.
- [ ] Cover important boundaries and failure paths.

### Unit Tests

- [ ] Business rules are covered.
- [ ] Dependencies are controlled where appropriate.
- [ ] Tests execute quickly.
- [ ] Exceptions are verified explicitly.
- [ ] Parameterized cases cover meaningful variations.

### Integration

- [ ] Critical database behavior uses a real database.
- [ ] Redis behavior is tested against Redis where required.
- [ ] Messaging behavior is integration-tested.
- [ ] Database state is isolated.
- [ ] External dependencies are controlled.

### API

- [ ] Authentication is tested.
- [ ] Authorization is tested.
- [ ] Validation is tested.
- [ ] Status codes are tested.
- [ ] Response contracts are tested.
- [ ] Error behavior is tested.

### Reliability

- [ ] Retry behavior is tested.
- [ ] Idempotency is tested.
- [ ] Transaction rollback is tested.
- [ ] Duplicate messages are tested.
- [ ] Timeouts are tested.
- [ ] Graceful shutdown is tested where relevant.

### CI/CD

- [ ] Tests run automatically.
- [ ] Fast tests provide early feedback.
- [ ] Integration tests run in controlled environments.
- [ ] Test failures block unsafe releases.
- [ ] Test artifacts and reports are retained appropriately.

### Security

- [ ] Tests cannot accidentally target production.
- [ ] Secrets are not committed.
- [ ] Authorization boundaries are tested.
- [ ] Sensitive error disclosure is tested.
- [ ] Multi-tenant isolation is tested where applicable.

---

## Interview Traps

### "More Tests Means Better Quality"

Not necessarily.

A large suite of redundant or implementation-coupled tests can increase maintenance cost without increasing confidence.

### "100% Coverage Means the Code Is Correct"

Coverage indicates execution, not correctness.

A test can execute every line without meaningful assertions.

### "Unit Tests Should Mock Everything"

No.

Some behavior is only trustworthy when tested against the real dependency.

Database semantics are a common example.

### "Integration Tests Are Always Better"

No.

They are valuable but slower, more complex, and harder to diagnose.

Use the lowest appropriate test level.

### "Tests Should Never Use Databases"

Incorrect.

Database behavior is often exactly what needs to be tested.

### "Flaky Tests Can Be Retried"

Retries may hide the underlying defect.

Fix the source of nondeterminism.

### "End-to-End Tests Replace Unit Tests"

They do not.

E2E tests verify system workflows but are usually poor at diagnosing small behavioral regressions.

### "Mocks Prove the Integration Works"

They do not.

Mocks verify application behavior against the mocked contract, not the real dependency.

## Key Takeaways

- **Test behavior at the appropriate boundary:** use unit tests for isolated logic, integration tests for real dependency semantics, API/contract tests for interfaces, and E2E tests for complete workflows.
- **Determinism and isolation are foundational:** flaky, order-dependent, time-dependent, or externally coupled tests destroy confidence in the test suite.
- **Do not mock away important system behavior:** PostgreSQL, Redis, Kafka, HTTP contracts, transactions, and concurrency semantics often require real integration testing.
- **Coverage is a signal, not a correctness guarantee:** meaningful assertions, failure-path coverage, security tests, idempotency tests, and critical business-rule coverage matter more than an arbitrary percentage.
- **Testing is part of system design:** clear service, repository, API, transaction, dependency, and lifecycle boundaries make systems easier to test and safer to change.