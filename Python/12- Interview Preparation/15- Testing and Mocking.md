# 15- Testing and Mocking

## Overview

Testing is a core engineering mechanism for establishing confidence in Python systems as they evolve. In backend applications, tests should validate not only individual functions but also contracts between application code, databases, APIs, queues, caches, and external services.

A production-oriented testing strategy balances several goals:

- correctness;
- regression prevention;
- fast feedback;
- realistic infrastructure behavior;
- maintainability;
- isolation;
- confidence during refactoring;
- deployment safety.

Mocking is one technique within that strategy. It replaces a real dependency with a controlled test double so that a unit can be tested independently.

The key distinction is:

```text
Testing
  │
  ├── Unit tests
  ├── Integration tests
  ├── API tests
  ├── Database tests
  ├── Contract tests
  ├── End-to-end tests
  └── Performance / resilience tests

Test Doubles
  │
  ├── Mock
  ├── Stub
  ├── Fake
  └── Spy
```

A senior engineer does not ask:

> "How can I mock this?"

The better question is:

> "What behavior or contract do I need confidence in, and which dependencies should be real for this test?"

---

## Testing Pyramid

A practical test strategy usually contains more fast, focused tests and fewer expensive end-to-end tests.

```text
              ┌───────────────┐
              │ End-to-End    │
              └───────────────┘
             ┌─────────────────┐
             │ Integration     │
             └─────────────────┘
          ┌───────────────────────┐
          │ Unit / Component      │
          └───────────────────────┘
```

| Test type | Speed | Isolation | Real infrastructure | Typical purpose |
|---|---|---|---|---|
| Unit | Very high | High | No | Business logic |
| Component | High | Moderate | Selected | Service behavior |
| Integration | Moderate | Low | Yes | DB/cache/queue interactions |
| API | Moderate | Moderate | Often | HTTP contracts |
| End-to-end | Low | Low | Yes | Complete user workflows |

The pyramid is a heuristic, not a rigid law. Systems with substantial distributed behavior may need more integration and contract testing.

---

## What Makes a Good Test

A useful test should have:

- a clear purpose;
- deterministic behavior;
- meaningful assertions;
- controlled dependencies;
- minimal unnecessary setup;
- failure messages that aid diagnosis.

A common structure is:

```text
Arrange
   │
   ▼
Act
   │
   ▼
Assert
```

Example:

```python
def test_total_price_applies_discount():
    cart = Cart(
        items=[
            CartItem(price=100, quantity=2),
        ]
    )

    total = cart.total(discount_percent=10)

    assert total == Decimal("180")
```

The test should communicate the business rule without requiring the reader to understand irrelevant implementation details.

---

## Unit Tests

A unit test verifies a small unit of behavior in isolation.

Good unit-test candidates include:

- domain rules;
- parsers;
- validators;
- pure functions;
- state transitions;
- service logic with explicit dependencies.

Example:

```python
def test_account_rejects_overdraft():
    account = Account(balance=Decimal("100"))

    with pytest.raises(InsufficientFunds):
        account.debit(Decimal("150"))
```

Unit tests should generally be fast enough to run frequently during development.

---

## What Should Not Be a Unit Test

Avoid calling a test a unit test when it depends on:

- a real PostgreSQL instance;
- a real Redis server;
- an external HTTP service;
- Kafka;
- S3;
- the network.

Those are integration or higher-level tests.

The distinction matters because developers need to understand the test's isolation and failure surface.

---

## pytest

`pytest` is a widely used Python testing framework.

Basic execution:

```bash
pytest
```

Useful commands:

```bash
pytest tests/
pytest tests/test_orders.py
pytest tests/test_orders.py::test_create_order
pytest -q
pytest -x
pytest --maxfail=3
```

A typical configuration can be placed in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
```

Keep test configuration explicit and version-controlled.

---

## Test Discovery

pytest commonly discovers:

```text
test_*.py
*_test.py
```

and test functions such as:

```python
def test_create_user():
    ...
```

Classes are typically named with a `Test` prefix:

```python
class TestUserService:
    def test_create_user(self):
        ...
```

Consistent naming makes test execution predictable.

---

## Assertions

Assertions should verify behavior that matters.

Prefer:

```python
assert response.status_code == 201
assert response.json()["id"] == user.id
```

over weak assertions such as:

```python
assert response is not None
```

For exceptions:

```python
with pytest.raises(ValueError, match="invalid email"):
    service.create_user("invalid")
```

Assertions should fail for the right reasons.

---

## Fixtures

Fixtures provide reusable test dependencies.

```python
@pytest.fixture
def user_service(repository):
    return UserService(repository)
```

Fixtures can provide:

- test data;
- database sessions;
- clients;
- configuration;
- temporary directories;
- mocked dependencies.

They should remain understandable. Deep fixture dependency graphs can make tests difficult to reason about.

---

## Fixture Scope

pytest supports scopes such as:

- `function`;
- `class`;
- `module`;
- `package`;
- `session`.

Example:

```python
@pytest.fixture(scope="session")
def application():
    return create_application()
```

Broader scopes reduce setup overhead but increase shared state and isolation risks.

Use the narrowest scope that is practical.

---

## Fixture Isolation

Avoid mutable shared fixtures:

```python
@pytest.fixture(scope="session")
def users():
    return []
```

One test can accidentally modify the list and affect later tests.

Prefer function-scoped mutable state unless there is a deliberate reason to share it.

---

## Parametrization

Parametrization prevents repetitive test code.

```python
@pytest.mark.parametrize(
    ("email", "expected"),
    [
        ("user@example.com", True),
        ("invalid", False),
        ("", False),
    ],
)
def test_email_validation(email, expected):
    assert validate_email(email) is expected
```

It is especially useful for:

- validation rules;
- boundary conditions;
- error cases;
- protocol variations.

Do not create enormous parameter matrices that obscure the behavior being tested.

---

## Testing Boundaries

The highest-value tests often focus on boundaries:

```text
HTTP
 │
 ▼
Application
 │
 ▼
Database
 │
 ▼
External Systems
```

Examples:

- malformed HTTP input;
- unauthorized access;
- database constraint violation;
- downstream timeout;
- duplicate event;
- invalid Kafka message;
- cache failure.

These failures are often more operationally important than simple arithmetic errors.

---

## Test Doubles

A test double substitutes for a real dependency.

| Double | Purpose |
|---|---|
| Stub | Returns predetermined data |
| Mock | Verifies interactions |
| Fake | Lightweight working implementation |
| Spy | Records calls while providing behavior |

The terminology can vary between testing communities, but the distinction is useful when deciding what the test should verify.

---

## Stub

A stub supplies controlled data.

```python
class StubUserRepository:
    def get_by_id(self, user_id: int):
        return User(id=user_id, email="user@example.com")
```

Use a stub when the test needs a predictable dependency result.

The test should then assert the resulting behavior rather than the internal call mechanics.

---

## Mock

A mock can verify interactions with a dependency.

```python
from unittest.mock import Mock


def test_service_saves_user():
    repository = Mock()
    service = UserService(repository)

    user = service.create_user("user@example.com")

    repository.save.assert_called_once_with(user)
```

Mock assertions are useful when an interaction is part of the contract.

They become harmful when tests assert every internal implementation detail.

---

## Fake

A fake is a simplified but functional implementation.

```python
class InMemoryUserRepository:
    def __init__(self):
        self.users = {}

    def save(self, user):
        self.users[user.id] = user

    def get_by_id(self, user_id):
        return self.users.get(user_id)
```

Fakes are often more realistic than mocks for complex behavior.

They are useful when:

- a real dependency is expensive;
- deterministic behavior is needed;
- the dependency has substantial stateful behavior.

The limitation is that the fake may diverge from the real implementation.

---

## Spy

A spy records interactions while executing real or wrapped behavior.

Conceptually:

```text
Application
    │
    ▼
   Spy
   │
   ▼
Real Dependency
```

Spies are useful when the test needs both actual behavior and interaction information.

Use them carefully because interaction-focused tests can become coupled to implementation details.

---

## unittest.mock

Python's standard library provides:

```python
from unittest.mock import Mock, MagicMock, AsyncMock, patch
```

Important capabilities include:

- replacing dependencies;
- recording calls;
- controlling return values;
- raising exceptions;
- asserting interactions;
- mocking async functions.

---

## Mock Return Values

```python
repository = Mock()
repository.get_by_id.return_value = User(
    id=1,
    email="user@example.com",
)

service = UserService(repository)

user = service.get_user(1)

assert user.id == 1
```

A mock should model the dependency behavior relevant to the test, not become a complete simulation of the production system.

---

## Mock Side Effects

`side_effect` can simulate failures or dynamic behavior.

```python
repository = Mock()

repository.get_by_id.side_effect = DatabaseTimeout(
    "database unavailable"
)

with pytest.raises(DatabaseTimeout):
    service.get_user(1)
```

It can also provide a sequence:

```python
client.get.side_effect = [
    TimeoutError(),
    {"status": "ok"},
]
```

This is useful for testing retry logic.

---

## MagicMock

`MagicMock` supports many Python magic methods automatically.

For example:

```python
mock_response = MagicMock()
mock_response.__enter__.return_value = mock_response
```

It can be useful for mocking objects implementing protocols such as:

- context managers;
- iterators;
- containers.

Prefer `Mock` when magic methods are not needed.

---

## AsyncMock

Use `AsyncMock` for async dependencies.

```python
client = AsyncMock()

client.get.return_value = {
    "id": 123,
    "status": "active",
}

result = await client.get("/users/123")

client.get.assert_awaited_once_with("/users/123")
```

Using an ordinary `Mock` for an awaited dependency can produce incorrect tests or runtime failures.

---

## Mocking Async Exceptions

```python
client = AsyncMock()

client.get.side_effect = TimeoutError()

with pytest.raises(TimeoutError):
    await service.fetch_user()
```

This allows testing timeout and recovery paths without making real network calls.

---

## `patch`

`patch` temporarily replaces an object during a test.

```python
from unittest.mock import patch


def test_service_uses_clock():
    with patch("app.service.time.time", return_value=1_700_000_000):
        result = create_timestamped_record()

    assert result.created_at == 1_700_000_000
```

The most important rule is:

> Patch where the dependency is looked up, not necessarily where it was originally defined.

---

## Patch Where It Is Used

Suppose:

```python
# app/service.py
from app.clock import now


def create_record():
    return now()
```

The correct target is generally:

```python
patch("app.service.now")
```

not:

```python
patch("app.clock.now")
```

because `service.py` already holds its own reference to `now`.

This is one of the most common `patch` interview questions.

---

## `patch.object`

Use `patch.object` when the target object is already available.

```python
clock = Clock()

with patch.object(clock, "now", return_value=123):
    assert clock.now() == 123
```

This can be clearer when testing an explicit object.

---

## Autospeccing

Mocks can accidentally allow invalid APIs:

```python
mock = Mock()
mock.nonexistent_method()
```

This may succeed even though the real object has no such method.

Use a spec:

```python
mock = Mock(spec=UserRepository)
```

or:

```python
mock = create_autospec(UserRepository)
```

Autospeccing helps detect incorrect method names and signatures.

---

## Why Autospec Matters

Without a spec:

```python
repository.svae(user)
```

might silently pass as a mock interaction.

With autospec, incorrect interfaces are more likely to fail immediately.

This makes tests more closely aligned with the production contract.

---

## Mocking vs Dependency Injection

Hard-coded dependencies are difficult to test:

```python
class UserService:
    def get_user(self, user_id):
        repository = PostgresUserRepository()
        return repository.get_by_id(user_id)
```

Dependency injection makes the boundary explicit:

```python
class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def get_user(self, user_id):
        return self.repository.get_by_id(user_id)
```

Testing becomes simpler:

```python
repository = Mock(spec=UserRepository)
service = UserService(repository)
```

Explicit dependencies usually produce better testability than excessive patching.

---

## Mocking HTTP Clients

Suppose a service calls an external payment provider.

A good unit test replaces the provider:

```python
payment_client = Mock(spec=PaymentClient)
payment_client.charge.return_value = PaymentResult(
    status="approved",
    transaction_id="txn-123",
)

service = CheckoutService(payment_client)

result = service.checkout(order)

assert result.transaction_id == "txn-123"
```

Then a separate integration or contract test should validate the real client behavior against the provider or a controlled test environment.

---

## Mocking the Network

Do not rely exclusively on mocks for HTTP integrations.

A realistic strategy is:

```text
Unit tests
   │
   └── Mock HTTP client

Integration tests
   │
   └── Controlled HTTP service

Contract tests
   │
   └── Verify request/response contract
```

Mocks validate application behavior around the dependency. They do not prove that the real dependency behaves as expected.

---

## API Testing

For FastAPI, API tests can use a test client.

```python
from fastapi.testclient import TestClient


def test_create_user(app):
    client = TestClient(app)

    response = client.post(
        "/users",
        json={"email": "user@example.com"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "user@example.com"
```

API tests should verify:

- status codes;
- response schemas;
- validation;
- authentication;
- authorization;
- important headers;
- error contracts.

---

## Database Integration Testing

When database behavior matters, use a real database environment.

Test:

- migrations;
- constraints;
- transactions;
- query behavior;
- indexes where relevant;
- isolation;
- PostgreSQL-specific behavior.

A fake repository cannot prove that PostgreSQL correctly enforces a unique constraint.

---

## Transaction Testing

Example:

```python
def test_order_creation_rolls_back_on_payment_failure(db):
    with pytest.raises(PaymentFailed):
        create_order_with_payment(
            db,
            payment_client=FailingPaymentClient(),
        )

    assert count_orders(db) == 0
```

This verifies an important system invariant rather than merely checking that an exception was raised.

---

## Test Database Isolation

Integration tests must avoid leaking state.

Common strategies include:

- transaction rollback;
- database truncation;
- disposable databases;
- per-test schemas;
- containers.

For high-confidence tests, the mechanism should match the application's actual transaction behavior.

---

## External Service Testing

External dependencies should generally be tested at multiple levels.

| Level | Dependency |
|---|---|
| Unit | Mock/stub |
| Integration | Controlled real service |
| Contract | API schema/behavior |
| Production | Real service with monitoring |

Do not make the entire test suite dependent on internet availability.

---

## Contract Testing

Contract tests verify that two independently deployed systems agree on an interface.

```text
Producer
   │
   │ API / Event Contract
   ▼
Consumer
```

This is particularly useful for:

- microservices;
- REST APIs;
- gRPC;
- Kafka events.

Contract tests catch integration mismatches without requiring complete end-to-end environments.

---

## Kafka Testing

For Kafka consumers, test important semantics such as:

- valid message processing;
- malformed messages;
- duplicate messages;
- retry behavior;
- offset handling;
- idempotency;
- dead-letter behavior.

A mock Kafka producer does not validate actual serialization, partitioning, consumer behavior, or broker semantics.

Use integration tests for those concerns.

---

## Redis Testing

Mock Redis when testing application logic that merely depends on a cache interface.

Use a real Redis instance when testing:

- TTL behavior;
- atomic operations;
- distributed locks;
- Lua scripts;
- eviction-related behavior;
- serialization;
- connection failures.

Redis semantics are not always accurately reproduced by an in-memory dictionary.

---

## Celery Testing

Unit-test task business logic separately from Celery infrastructure.

Then integration-test:

- task serialization;
- broker interaction;
- retries;
- acknowledgements;
- result behavior where used.

Avoid relying entirely on eager execution because it does not reproduce all worker/broker semantics.

---

## Test Architecture

A production backend test suite can be organized as:

```text
tests/
├── unit/
│   ├── domain/
│   └── services/
├── integration/
│   ├── database/
│   ├── redis/
│   └── messaging/
├── api/
│   ├── test_auth.py
│   └── test_users.py
├── contract/
└── e2e/
```

The exact organization should match the repository structure and team workflow.

---

## Test Naming

A test name should describe behavior.

Prefer:

```python
def test_create_order_rejects_insufficient_inventory():
    ...
```

over:

```python
def test_order_3():
    ...
```

Behavior-focused names make failures immediately useful in CI.

---

## Testing Exceptions

Test both the exception type and meaningful details.

```python
with pytest.raises(InsufficientInventory, match="SKU-123"):
    service.create_order(order)
```

Avoid testing exact full exception strings when the message is not part of the contract.

---

## Testing Retries

Retry logic should test:

- retryable failure;
- maximum attempts;
- backoff behavior where practical;
- eventual success;
- final failure;
- non-retryable errors.

Example:

```python
client = Mock()
client.send.side_effect = [
    TimeoutError(),
    TimeoutError(),
    {"status": "ok"},
]

result = send_with_retry(client)

assert result["status"] == "ok"
assert client.send.call_count == 3
```

Do not use real sleeps in unit tests.

Inject or control the timing mechanism instead.

---

## Testing Time

Time-dependent code is difficult to test when it directly calls global clocks.

Prefer dependency injection or a clock abstraction:

```python
class Clock(Protocol):
    def now(self) -> datetime:
        ...
```

Then production and test implementations can be supplied explicitly.

This is usually cleaner than repeatedly patching `datetime`.

---

## Testing Randomness

Random behavior should also be controllable.

```python
def generate_token(random_source):
    return random_source.token_hex(16)
```

The test can provide a deterministic source.

This avoids flaky tests caused by uncontrolled randomness.

---

## Testing File Operations

Use temporary directories rather than fixed filesystem paths.

```python
def test_export_report(tmp_path):
    output = tmp_path / "report.json"

    export_report(output)

    assert output.exists()
```

pytest's `tmp_path` fixture provides isolated temporary filesystem state.

---

## Testing Environment Configuration

Tests should not accidentally depend on developer-specific environment variables.

Explicitly provide test configuration:

```text
Production
  DATABASE_URL → production PostgreSQL

Test
  DATABASE_URL → disposable test PostgreSQL
```

Never point automated tests at production infrastructure.

---

## Deterministic Tests

A deterministic test produces the same result under the same conditions.

Common sources of nondeterminism include:

- current time;
- randomness;
- thread scheduling;
- async task ordering;
- external services;
- shared state;
- unordered assumptions;
- database state.

Control these sources rather than adding arbitrary retries to flaky tests.

---

## Testing Concurrency

Concurrency tests should target actual invariants.

Examples:

- no duplicate processing;
- bounded concurrency;
- correct locking;
- safe cancellation;
- queue ordering where required.

Avoid tests that depend on timing such as:

```python
time.sleep(0.1)
assert worker.finished
```

Such tests are inherently fragile.

Prefer synchronization primitives and explicit state observation.

---

## Async Testing

pytest can test async functions with an appropriate async test plugin.

Example:

```python
@pytest.mark.asyncio
async def test_fetch_user(client):
    user = await client.fetch_user(123)

    assert user.id == 123
```

Async tests should verify:

- awaited dependencies;
- cancellation;
- timeouts;
- concurrent operations;
- exception propagation.

Do not mix blocking operations into async tests unnecessarily.

---

## Flaky Tests

A flaky test sometimes passes and sometimes fails without a relevant code change.

Typical causes:

- shared state;
- timing assumptions;
- real network calls;
- race conditions;
- unordered data;
- random values;
- environment dependencies.

Do not simply rerun flaky tests until they pass.

A flaky test reduces trust in the entire test suite.

---

## Test Isolation

Tests should ideally be independent.

Bad:

```text
test_create_user
      │
      ▼
test_update_user
      │
      ▼
test_delete_user
```

Each test should establish its own required state.

Test ordering should not determine correctness.

---

## Mocking Overuse

Excessive mocking creates tests such as:

```python
repository.method_a.assert_called_once()
repository.method_b.assert_called_once()
repository.method_c.assert_called_once()
repository.method_d.assert_called_once()
```

These tests can pass while the actual business behavior is wrong.

Prefer asserting externally meaningful outcomes.

---

## Mocking Internal Implementation

Suppose:

```python
result = service.process()
```

The test should usually care about:

```python
assert result.status == "completed"
```

rather than every private helper called internally.

Tests should survive safe refactoring.

---

## Mocking Classes vs Interfaces

If a service depends on a protocol:

```python
class UserRepository(Protocol):
    def get_by_id(self, user_id: int) -> User | None:
        ...
```

tests can mock the contract rather than an implementation.

This aligns testing with dependency inversion.

---

## Mutation Testing

Mutation testing deliberately changes code to determine whether tests detect the change.

Conceptually:

```text
Original code
     │
     ▼
Introduce mutation
     │
     ▼
Run tests
     │
     ├── Test fails → mutation killed
     └── Test passes → weak coverage
```

It is useful for evaluating test effectiveness, but can be computationally expensive for large projects.

---

## Code Coverage

Coverage measures which code was executed by tests.

Common metrics include:

- line coverage;
- branch coverage;
- function coverage.

High coverage does not automatically mean high confidence.

This:

```python
assert result is not None
```

may execute a line without meaningfully validating behavior.

Coverage is a signal, not a quality guarantee.

---

## Branch Coverage

Branch coverage helps reveal untested conditions.

For:

```python
if user.is_admin:
    allow()
else:
    deny()
```

a useful test suite should exercise both branches when both are meaningful.

Focus on business-critical branches rather than chasing an arbitrary percentage.

---

## Testing Strategy for a Backend Service

A practical strategy might be:

```text
Every commit
  │
  ├── Unit tests
  ├── Static type checks
  └── Fast API/component tests

Pull request
  │
  ├── Integration tests
  ├── Database tests
  └── Contract tests

Pre-deployment
  │
  ├── E2E tests
  ├── Smoke tests
  └── Migration validation

Production
  │
  ├── Health checks
  ├── Metrics
  ├── Logs
  └── Traces
```

Not every repository needs every layer on every commit.

---

## CI/CD Testing

A mature CI pipeline might look like:

```mermaid
flowchart LR
    A[Commit] --> B[Lint]
    B --> C[Type Check]
    C --> D[Unit Tests]
    D --> E[Integration Tests]
    E --> F[Security Checks]
    F --> G[Build Container]
    G --> H[Deploy]
    H --> I[Smoke Tests]
```

Fast failures should happen early.

Slow or expensive tests can run later in the pipeline when appropriate.

---

## Test Parallelization

pytest can run tests in parallel with appropriate tooling.

Parallel execution can reduce CI time but exposes hidden shared-state assumptions.

Before parallelizing, ensure tests do not rely on:

- shared files;
- fixed ports;
- global mutable state;
- shared database rows;
- order-dependent fixtures.

Parallel testing is both a performance optimization and a test-isolation test.

---

## Testing in Docker

Integration environments can use containers to provide realistic dependencies:

```text
Test Runner
    │
    ├── PostgreSQL container
    ├── Redis container
    └── Kafka container
```

This provides more realistic behavior than replacing every infrastructure component with mocks.

For CI, disposable environments help prevent test state from leaking across runs.

---

## Testing Kubernetes Deployments

Deployment tests should verify:

- readiness;
- liveness;
- configuration;
- secret injection;
- database connectivity;
- graceful shutdown;
- rolling deployment compatibility.

A deployment that passes unit tests but cannot start correctly in Kubernetes is not production-ready.

---

## Security Testing

Tests should verify important security boundaries.

Examples:

```text
Unauthenticated request → 401
Authenticated but unauthorized → 403
Malformed input → 400
Valid request → expected result
```

Also test:

- tenant isolation;
- object-level authorization;
- privilege escalation paths;
- secret handling;
- injection protections;
- rate limiting where required.

Do not treat tests as the only security control.

---

## Performance Testing

Functional tests answer:

> Is the behavior correct?

Performance tests answer:

> Does it remain acceptable under realistic load?

Separate performance tests should evaluate:

- latency;
- throughput;
- CPU;
- memory;
- database load;
- queue depth;
- concurrency.

Avoid putting expensive load tests into every unit-test run.

---

## Production Testability

Good architecture makes production behavior observable and testable.

Prefer explicit dependencies:

```text
Service
 ├── Repository
 ├── Cache
 ├── Clock
 ├── HTTP Client
 └── Message Publisher
```

Each boundary can then be:

- tested independently;
- instrumented;
- replaced;
- configured.

Testability is often an architectural property rather than a testing trick.

---

## Common Mistakes

### Mocking Everything

Why it happens:

- unit tests are fast;
- real dependencies are inconvenient.

Why it is dangerous:

- mocks do not reproduce real infrastructure semantics.

Better approach:

- mock at unit boundaries;
- use integration tests for infrastructure behavior.

### Patching the Wrong Location

Why it happens:

- developers patch where a function was originally defined.

Better approach:

- patch where the code under test looks up the dependency.

### Using Unspecced Mocks

Why it happens:

- `Mock()` is convenient.

Risk:

- invalid method names and signatures can silently pass.

Better approach:

- use `spec` or `autospec`.

### Testing Implementation Details

Why it happens:

- internal calls are easy to assert.

Risk:

- harmless refactoring breaks tests.

Better approach:

- assert behavior and externally meaningful interactions.

### Shared Mutable Fixtures

Why it happens:

- broad fixture scope appears faster.

Risk:

- test order and parallelism affect results.

Better approach:

- isolate mutable state.

### Real Network Calls in Unit Tests

Why it happens:

- the integration appears realistic.

Risk:

- slow, flaky, environment-dependent tests.

Better approach:

- isolate network behavior in unit tests and cover real integration separately.

### Sleeping in Tests

Why it happens:

- developers attempt to "wait for" asynchronous behavior.

Risk:

- slow and nondeterministic tests.

Better approach:

- use explicit synchronization and state observation.

---

## Interview Traps

### What Is the Difference Between a Mock and a Stub?

A stub primarily supplies predetermined behavior or data. A mock is commonly used to verify interactions.

The terminology varies, but the practical distinction is whether the test primarily needs controlled output or interaction verification.

### What Is a Fake?

A fake is a lightweight working implementation, such as an in-memory repository.

### Why Should You Patch Where a Dependency Is Used?

Because Python imports bind names in the importing module. Patching the original definition may not replace the already-bound reference used by the code under test.

### Why Use `autospec`?

It constrains mocks to the interface and signature of the real dependency, reducing false-positive tests.

### Should You Mock PostgreSQL?

For unit tests of business logic, usually yes through a repository or gateway boundary.

For testing SQL, constraints, transactions, and PostgreSQL-specific behavior, use a real PostgreSQL integration environment.

### Is 100% Coverage Good?

It can be useful, but coverage measures execution rather than test quality. A poorly asserted test can produce high coverage and low confidence.

### Why Are Flaky Tests Dangerous?

They reduce trust in CI. Once engineers expect tests to fail randomly, legitimate regressions are more likely to be ignored.

---

## Senior-Level Interview Questions

### How Would You Test a Payment Service?

Separate concerns:

```text
Unit
 ├── business rules
 ├── authorization
 └── state transitions

Integration
 ├── database transactions
 └── payment client behavior

Contract
 └── payment provider API

E2E
 └── complete checkout flow
```

Test idempotency, retries, timeouts, duplicate requests, and partial failures.

### How Would You Test a Kafka Consumer?

Verify:

- valid messages;
- malformed messages;
- duplicate delivery;
- idempotency;
- retry behavior;
- dead-letter handling;
- offset behavior.

Use mocks for isolated business logic and real Kafka integration tests for broker-specific semantics.

### How Would You Test a Distributed Lock?

A mock can verify that the application requests a lock, but only a real Redis/database integration test can provide meaningful confidence in:

- atomic acquisition;
- expiration;
- contention;
- lock release;
- failure behavior.

### How Would You Reduce a 30-Minute Test Suite?

First measure where time is spent.

Potential improvements include:

- parallelizing isolated tests;
- reducing unnecessary fixture scope;
- eliminating real network calls from unit tests;
- reusing expensive immutable setup;
- separating slow integration suites;
- optimizing database setup;
- removing redundant tests.

Do not blindly convert integration tests into mocks just to improve runtime.

### How Would You Design Tests for a Microservice?

Test the service at multiple boundaries:

```text
Unit
  ↓
Component
  ↓
Database / Infrastructure Integration
  ↓
API / Contract
  ↓
End-to-End
```

Use mocks to isolate local logic, integration tests to validate infrastructure semantics, contract tests to protect service boundaries, and a smaller number of E2E tests for critical workflows.

---

## Test Quality Heuristics

A strong test suite should be:

| Property | Meaning |
|---|---|
| Fast | Developers can run it frequently |
| Deterministic | Same conditions produce same result |
| Isolated | Tests do not depend on ordering |
| Focused | Failure identifies a specific behavior |
| Realistic | Important infrastructure semantics are covered |
| Maintainable | Refactoring does not cause unnecessary failures |
| Observable | CI failures provide useful diagnostics |

The goal is not maximum test count.

The goal is **maximum confidence per unit of test complexity**.

---

## Production Testing Checklist

### Unit Tests

- [ ] Business rules have focused tests.
- [ ] Boundary conditions are covered.
- [ ] Error paths are tested.
- [ ] Tests avoid unnecessary infrastructure.
- [ ] Dependencies are explicit.

### Mocking

- [ ] Mocks represent meaningful boundaries.
- [ ] `spec` or `autospec` is used where useful.
- [ ] Async dependencies use `AsyncMock`.
- [ ] Patches target lookup locations.
- [ ] Tests do not over-assert implementation details.

### Integration

- [ ] PostgreSQL behavior is tested with real PostgreSQL where required.
- [ ] Redis-specific semantics are tested against Redis where required.
- [ ] Messaging behavior is integration-tested.
- [ ] Database state is isolated.
- [ ] Migrations are exercised.

### API

- [ ] Status codes are verified.
- [ ] Response contracts are verified.
- [ ] Validation is tested.
- [ ] Authentication and authorization are tested.
- [ ] Error contracts are stable.

### CI/CD

- [ ] Fast tests run early.
- [ ] Integration tests run in disposable environments.
- [ ] Tests can run reliably in parallel where appropriate.
- [ ] Coverage is monitored without becoming the only quality metric.
- [ ] Deployment smoke tests exist.

### Reliability

- [ ] Retry behavior is tested.
- [ ] Timeout behavior is tested.
- [ ] Idempotency is tested.
- [ ] Duplicate events are tested.
- [ ] Graceful failure paths are tested.

## Key Takeaways

- **Testing is about confidence, not test count:** use unit, integration, API, contract, and end-to-end tests according to the behavior and boundary being validated.
- **Mock selectively:** mocks are valuable for isolating business logic, but they cannot prove that PostgreSQL, Redis, Kafka, HTTP services, or other infrastructure behave correctly.
- **Patch where the dependency is looked up:** combine explicit dependency injection with `spec`/`autospec`, `AsyncMock`, and correctly targeted patches to avoid false-positive tests.
- **Optimize for deterministic, maintainable tests:** isolate mutable state, avoid real network calls and arbitrary sleeps in unit tests, control time and randomness, and design concurrency tests around explicit synchronization.
- **Treat testability as an architectural property:** clear dependency boundaries, stable contracts, realistic integration environments, and layered CI/CD testing provide stronger production confidence than extensive mocking alone.