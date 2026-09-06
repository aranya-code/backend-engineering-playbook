# 08- Mocking

## Overview

Mocking replaces a real dependency with a controlled test double so that a test can isolate the behavior of the component under test.

In Python, mocking is primarily provided by `unittest.mock`, with pytest adding convenient integration through fixtures and plugins such as `pytest-mock`.

A typical backend service has dependencies such as:

```text
HTTP handler
    │
    ├── domain service
    │      ├── PostgreSQL
    │      ├── Redis
    │      ├── external HTTP API
    │      └── Kafka
    │
    └── authentication provider
```

Testing the handler does not always require starting every dependency. A mock can replace a specific dependency:

```text
HTTP handler
    │
    ├── domain service
    │      ├── PostgreSQL       → mock
    │      ├── Redis            → mock
    │      └── external API     → mock
    │
    └── authentication provider → mock
```

The purpose is **controlled isolation**, not simply avoiding real infrastructure.

Mocking is most effective when:

- the dependency is slow;
- the dependency is nondeterministic;
- the dependency is expensive;
- the dependency is unavailable in a unit-test environment;
- a failure or response is difficult to reproduce;
- the test needs to verify an interaction with a dependency.

Mocking should not replace integration tests when the real dependency's behavior is part of the contract.

---

## Test Doubles

"Test double" is the broader concept. A mock is one type of test double.

| Test double | Primary purpose |
|---|---|
| Dummy | Satisfies an argument requirement but is not used |
| Stub | Provides controlled responses |
| Fake | Provides a working simplified implementation |
| Spy | Records interactions for later inspection |
| Mock | Configures behavior and verifies interactions |

In Python, `unittest.mock` can implement several of these roles depending on how it is configured.

For example:

```python
from unittest.mock import Mock

payment_gateway = Mock()
payment_gateway.charge.return_value = True
```

Here the mock is effectively acting as a stub.

If the test verifies:

```python
payment_gateway.charge.assert_called_once_with(
    amount=100,
)
```

it is also being used as an interaction-verification mock.

The distinction is conceptual rather than a strict API classification.

---

## Why Mocking Exists

A unit test should normally control the boundaries around the unit under test.

Consider:

```python
class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
        payment_gateway: PaymentGateway,
    ) -> None:
        self.repository = repository
        self.payment_gateway = payment_gateway

    def create_order(self, amount: int) -> Order:
        payment = self.payment_gateway.charge(amount)

        if not payment.success:
            raise PaymentFailedError

        return self.repository.create(amount)
```

A unit test does not need a real payment provider or PostgreSQL database to verify the service's decision-making.

```text
OrderService
    │
    ├── PaymentGateway → mock
    └── Repository     → mock
```

This makes the test:

- fast;
- deterministic;
- isolated;
- easy to execute in CI;
- capable of testing failure paths that may be difficult to trigger externally.

---

## `Mock`

`Mock` is the fundamental object provided by `unittest.mock`.

```python
from unittest.mock import Mock

gateway = Mock()

gateway.charge.return_value = True

assert gateway.charge(100) is True
```

Unconfigured method calls automatically produce further mock objects:

```python
value = gateway.some_method()
```

This flexibility is useful but can also hide mistakes.

For example, a typo:

```python
gateway.chagre(100)
```

may silently create a new mock attribute instead of failing.

For production-quality tests, constrain mocks where practical with `spec`, `spec_set`, or `autospec`.

---

## `MagicMock`

`MagicMock` extends `Mock` with support for Python's magic methods.

```python
from unittest.mock import MagicMock

response = MagicMock()
response.status_code = 200

assert response.status_code == 200
```

It is useful when the object under test interacts with protocols such as:

- context managers;
- iteration;
- length;
- containment;
- numeric operations.

Example:

```python
response = MagicMock()
response.__enter__.return_value = response
response.status_code = 200
```

Use ordinary `Mock` when magic-method support is unnecessary.

---

## `AsyncMock`

Async dependencies should use `AsyncMock`.

```python
from unittest.mock import AsyncMock

client = AsyncMock()

client.get.return_value = {"id": "order-1"}

result = await client.get("/orders/order-1")

assert result["id"] == "order-1"
```

This matters because an asynchronous dependency is awaited:

```python
result = await client.get(...)
```

`AsyncMock` behaves as an awaitable mock and supports assertions such as:

```python
client.get.assert_awaited_once_with(
    "/orders/order-1",
)
```

Do not use a regular `Mock` for an async callable that the code under test awaits.

---

## `spec`

A mock can be constrained to the attributes of an existing object or class.

```python
from unittest.mock import Mock

gateway = Mock(spec=PaymentGateway)
```

Now accessing an attribute that does not exist on `PaymentGateway` raises an `AttributeError`.

This catches many interface mistakes.

However, `spec` primarily constrains attribute access. It does not provide the strongest signature enforcement.

---

## `spec_set`

`spec_set` is stricter.

```python
gateway = Mock(spec_set=PaymentGateway)
```

It prevents setting attributes that are not part of the specification.

This is useful when tests should detect accidental API drift.

---

## `autospec`

`autospec` creates mocks that more closely follow the callable signatures of the target.

```python
from unittest.mock import create_autospec

gateway = create_autospec(PaymentGateway)
```

If the real method is:

```python
def charge(self, amount: int, currency: str) -> PaymentResult:
    ...
```

then incorrect calls are more likely to be detected:

```python
gateway.charge(100)
```

This is one reason `autospec` is generally preferable to completely unconstrained mocks when practical.

---

## Mock Configuration

Mocks can control return values:

```python
repository = Mock()
repository.get_by_id.return_value = Order(
    id="order-1",
    amount=100,
)
```

They can also represent exceptions:

```python
repository.get_by_id.side_effect = DatabaseError(
    "connection failed",
)
```

This allows tests to exercise failure paths deterministically.

---

## `return_value`

`return_value` defines what a call returns.

```python
client = Mock()
client.get.return_value = {"status": "ok"}

result = client.get("/health")

assert result == {"status": "ok"}
```

For chained calls, configure the relevant return object explicitly rather than relying on automatically generated nested mocks.

---

## `side_effect`

`side_effect` is useful for exceptions, dynamic results, and sequences.

### Exception

```python
client = Mock()
client.get.side_effect = TimeoutError
```

Every call raises the exception.

### Sequence

```python
client = Mock()
client.get.side_effect = [
    TimeoutError,
    {"status": "ok"},
]
```

This can model a first-attempt failure followed by success.

### Callable

```python
def calculate_response(order_id: str) -> dict:
    return {"id": order_id}


client = Mock()
client.get.side_effect = calculate_response
```

The callable receives the same arguments passed to the mock.

---

## Verifying Calls

Mocks record interactions.

```python
gateway = Mock()

gateway.charge(100)

gateway.charge.assert_called_once_with(100)
```

Common assertions include:

```python
mock.assert_called()
mock.assert_not_called()
mock.assert_called_once()
mock.assert_called_with(...)
mock.assert_called_once_with(...)
```

For async mocks:

```python
mock.assert_awaited()
mock.assert_awaited_once()
mock.assert_awaited_with(...)
mock.assert_awaited_once_with(...)
```

Use interaction assertions when the interaction itself is part of the behavior being tested.

---

## Call Arguments

Arguments can be inspected directly:

```python
gateway.charge(
    amount=100,
    currency="USD",
)

gateway.charge.assert_called_once_with(
    amount=100,
    currency="USD",
)
```

For more complex inspection:

```python
args, kwargs = gateway.charge.call_args

assert args == ()
assert kwargs["amount"] == 100
```

Prefer direct assertions such as `assert_called_once_with()` when they communicate the expected contract clearly.

---

## `call` and Multiple Calls

For ordered calls:

```python
from unittest.mock import Mock, call

repository = Mock()

repository.begin()
repository.save()
repository.commit()

assert repository.method_calls == [
    call.begin(),
    call.save(),
    call.commit(),
]
```

This is useful when call ordering is behaviorally important.

Do not assert every incidental call merely because the mock records it.

---

## `call_args_list`

For repeated calls:

```python
repository.save(1)
repository.save(2)
repository.save(3)

assert repository.save.call_args_list == [
    call(1),
    call(2),
    call(3),
]
```

This is useful for batch processing and retry scenarios.

---

## `patch`

`patch` temporarily replaces an object during a test.

```python
from unittest.mock import patch

with patch("orders.service.PaymentGateway") as gateway:
    gateway.return_value.charge.return_value = True
```

The replacement exists only within the patch context.

A decorator form is also available:

```python
@patch("orders.service.PaymentGateway")
def test_create_order(gateway) -> None:
    ...
```

Patchers should be automatically cleaned up by the decorator or context manager.

---

## Patch Where the Dependency Is Used

This is one of the most important mocking rules in Python:

> Patch the name where the code under test looks it up, not necessarily where the object was originally defined.

Suppose:

```python
# payments.py

class PaymentGateway:
    ...
```

and:

```python
# orders.py

from payments import PaymentGateway


def create_order() -> None:
    gateway = PaymentGateway()
    ...
```

The test should patch:

```python
patch("orders.PaymentGateway")
```

not:

```python
patch("payments.PaymentGateway")
```

because `orders.py` already holds its own reference to `PaymentGateway`.

The lookup flow is:

```text
orders.create_order()
        │
        ▼
orders.PaymentGateway
        │
        ▼
patched object
```

This rule explains many confusing `patch()` failures.

---

## `patch.object`

`patch.object()` patches an attribute directly on an object or class.

```python
with patch.object(
    PaymentGateway,
    "charge",
    return_value=True,
):
    ...
```

Use it when the target object is already directly available.

---

## `patch.dict`

`patch.dict()` temporarily modifies dictionaries.

```python
from unittest.mock import patch

with patch.dict(
    "os.environ",
    {"PAYMENT_MODE": "test"},
):
    assert os.environ["PAYMENT_MODE"] == "test"
```

The original mapping is restored after the patch.

This is useful for controlled configuration tests.

---

## `patch.multiple`

Multiple attributes can be patched together:

```python
with patch.multiple(
    "orders.service",
    PAYMENT_TIMEOUT=1,
    MAX_RETRIES=2,
):
    ...
```

Use this sparingly. Many patched values can make a test difficult to understand.

---

## `new` and `new_callable`

`patch()` can replace an object with a specific value:

```python
with patch(
    "orders.service.DEFAULT_TIMEOUT",
    new=5,
):
    ...
```

`new_callable` creates a replacement dynamically:

```python
with patch(
    "orders.service.PaymentGateway",
    new_callable=Mock,
):
    ...
```

For most application tests, ordinary `patch()` with an automatically created mock is sufficient.

---

## `create=True`

`patch()` can be instructed to create a missing attribute:

```python
patch(
    "module.MISSING_ATTRIBUTE",
    create=True,
)
```

This is usually dangerous.

It can allow tests to pass against an attribute that does not actually exist in production.

Prefer failing fast unless dynamic attributes are an intentional part of the design.

---

## Mocking Classes

When patching a class:

```python
with patch(
    "orders.service.PaymentGateway",
) as gateway_class:
    gateway_class.return_value.charge.return_value = True
```

There are two layers:

```text
gateway_class
      │
      └── return_value
              │
              └── instance mock
                      │
                      └── charge()
```

The class mock represents the constructor.

The `return_value` represents the constructed instance.

---

## Mocking HTTP Clients

A service might depend on an HTTP client:

```python
class CustomerClient:
    async def get_customer(self, customer_id: str) -> dict:
        ...
```

The unit test can use:

```python
client = AsyncMock(spec=CustomerClient)

client.get_customer.return_value = {
    "id": "customer-1",
    "status": "active",
}
```

Then:

```python
service = OrderService(customer_client=client)

result = await service.create_order("customer-1")

client.get_customer.assert_awaited_once_with(
    "customer-1",
)
```

This verifies the service's interaction without making a network request.

---

## Mocking REST APIs

For a FastAPI handler, dependency injection often provides a cleaner boundary than patching globals.

Conceptually:

```text
HTTP request
     │
     ▼
FastAPI route
     │
     ▼
OrderService
     │
     └── PaymentClient → mock
```

A test can override the dependency and verify the route's behavior without contacting the real provider.

The exact mechanism depends on the application's dependency-injection design.

---

## Mocking FastAPI Dependencies

FastAPI's dependency override mechanism can be used for test isolation:

```python
def override_current_user() -> User:
    return User(
        id="user-1",
        role="admin",
    )


app.dependency_overrides[
    get_current_user
] = override_current_user
```

Tests should clean up overrides after execution:

```python
try:
    response = client.get("/orders")
finally:
    app.dependency_overrides.clear()
```

A fixture is generally preferable for reusable setup and deterministic cleanup.

---

## Mocking Django Dependencies

Django applications can use `unittest.mock` for external boundaries:

```python
@patch("orders.services.PaymentClient")
def test_create_order(payment_client) -> None:
    payment_client.return_value.charge.return_value = True

    ...
```

Be careful when mocking Django ORM operations.

Mocking the ORM can make a test fast, but it cannot validate:

- SQL correctness;
- constraints;
- transaction semantics;
- query behavior;
- database isolation;
- indexes.

Those require integration tests against an appropriate database.

---

## Mocking PostgreSQL

Mock PostgreSQL when testing application logic that does not depend on actual database semantics.

For example:

```python
repository = Mock(spec=OrderRepository)

repository.get_by_id.return_value = Order(
    id="order-1",
    amount=100,
)
```

Do not mock database behavior that is itself the thing being tested.

Use integration tests for:

- SQL queries;
- unique constraints;
- foreign keys;
- transactions;
- isolation levels;
- locking;
- PostgreSQL-specific operators;
- indexes;
- query performance.

A mock can tell you that `repository.save()` was called. It cannot tell you whether PostgreSQL successfully persisted the data.

---

## Mocking Redis

Mock Redis when testing application-level cache decisions:

```python
cache = Mock(spec=Cache)
cache.get.return_value = {"id": "order-1"}
```

Use real Redis integration tests when behavior depends on:

- TTL;
- atomic operations;
- distributed locks;
- eviction;
- Lua scripts;
- serialization;
- connection behavior.

---

## Mocking Kafka

A Kafka producer can be mocked to verify that a domain event is emitted:

```python
producer = Mock(spec=EventProducer)

service = OrderService(
    repository=repository,
    producer=producer,
)

service.create_order(...)

producer.publish.assert_called_once()
```

This validates application intent.

It does not validate:

- Kafka broker availability;
- serialization compatibility;
- partitioning;
- consumer offsets;
- delivery guarantees;
- schema compatibility.

Those require integration or contract testing.

---

## Mocking Celery

Celery task dispatch can be mocked when testing whether a task is scheduled:

```python
with patch(
    "orders.services.send_confirmation.delay",
) as send_confirmation:
    service.create_order(...)

send_confirmation.assert_called_once_with(
    "order-1",
)
```

This verifies dispatch.

It does not prove that the task:

- reaches the broker;
- executes successfully;
- retries correctly;
- acknowledges messages correctly;
- handles worker crashes.

Those concerns belong in appropriate integration tests.

---

## Mocking Time

Time-dependent code should ideally receive a clock dependency rather than repeatedly calling global time functions.

Instead of tightly coupling business logic to:

```python
datetime.now()
```

design an injectable clock:

```python
from datetime import datetime, timezone


class Clock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
```

Production:

```python
clock = Clock()
```

Test:

```python
clock = Mock(spec=Clock)
clock.now.return_value = datetime(
    2026,
    9,
    6,
    tzinfo=timezone.utc,
)
```

This is usually cleaner than globally patching time throughout a large test suite.

---

## Mocking Randomness

Randomness should similarly be controlled at a boundary.

```python
random_source = Mock()
random_source.token.return_value = "fixed-token"
```

The test becomes deterministic without changing global random state.

This is preferable to relying on actual random values in assertions.

---

## Mocking Environment Variables

Use `patch.dict()` or pytest's `monkeypatch`:

```python
from unittest.mock import patch

with patch.dict(
    "os.environ",
    {"APP_ENV": "test"},
):
    config = load_config()
```

Do not let tests silently inherit arbitrary developer-machine environment variables.

---

## Mocking File Systems

For application logic around file paths, use temporary directories when filesystem behavior matters.

For pure orchestration logic, a file abstraction can be mocked:

```python
storage = Mock(spec=ObjectStorage)

storage.upload.return_value = "s3://bucket/object"
```

Use integration tests for actual S3, filesystem permissions, path handling, or object-storage semantics.

---

## Mocking AWS Services

For AWS-dependent code, mocking the client can isolate business logic:

```python
s3 = Mock(spec=S3Client)

s3.put_object.return_value = {
    "ETag": '"abc123"',
}
```

This is appropriate for verifying application decisions.

For real AWS semantics, consider integration testing with:

- isolated AWS test resources;
- local emulators where they provide sufficient fidelity;
- dedicated cloud test accounts.

Do not assume a mock validates IAM permissions, network policies, retries, throttling, or AWS service behavior.

---

## Mocking Exceptions

Failure-path testing is one of mocking's strongest use cases.

```python
gateway = Mock(spec=PaymentGateway)
gateway.charge.side_effect = PaymentProviderError()

with pytest.raises(PaymentFailedError):
    service.create_order(amount=100)
```

This allows deterministic testing of conditions that may be rare in production.

Important failure classes include:

- timeouts;
- connection failures;
- authorization failures;
- rate limits;
- malformed responses;
- dependency outages;
- transient errors;
- permanent errors.

---

## Testing Retry Logic

Mocks can model transient failures:

```python
gateway = Mock(spec=PaymentGateway)

gateway.charge.side_effect = [
    TimeoutError,
    TimeoutError,
    PaymentResult(success=True),
]
```

Then:

```python
result = service.charge_with_retry(amount=100)

assert result.success is True
assert gateway.charge.call_count == 3
```

This verifies retry behavior deterministically.

Do not test only successful retries. Also test:

- maximum attempts;
- non-retryable errors;
- backoff behavior;
- timeout interaction;
- idempotency;
- final failure.

---

## Interaction Testing vs State Testing

There are two fundamentally different assertions.

### State-Based

```python
assert order.status == OrderStatus.PAID
```

### Interaction-Based

```python
gateway.charge.assert_called_once_with(
    amount=100,
)
```

Prefer state or externally observable behavior when possible.

Interaction assertions are appropriate when the interaction itself is important:

- a payment must be charged;
- an event must be published;
- a task must be scheduled;
- a cache must be invalidated;
- an audit record must be emitted.

Do not assert every internal method call.

---

## Over-Mocking

Over-mocking creates tests that verify implementation structure rather than application behavior.

For example:

```python
repository.get_by_id.assert_called_once()
repository.validate.assert_called_once()
repository.transform.assert_called_once()
repository.save.assert_called_once()
```

If all these methods are implementation details, a harmless refactor can break the tests without changing behavior.

A better test verifies the resulting behavior:

```python
assert result.status == "completed"
```

and only verifies critical interactions.

---

## Mocking Internal Methods

Avoid mocking methods of the same object merely to make a unit test easier.

This:

```python
with patch.object(
    service,
    "_calculate_total",
    return_value=100,
):
    ...
```

can bypass the very logic the test should validate.

Prefer mocking external collaborators:

```text
Service under test
    │
    ├── Repository → mock
    ├── Gateway    → mock
    └── Publisher  → mock
```

rather than:

```text
Service under test
    │
    └── internal methods → mock
```

---

## Dependency Injection and Mockability

Dependency injection makes mocking significantly easier.

Prefer:

```python
class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
        gateway: PaymentGateway,
    ) -> None:
        self.repository = repository
        self.gateway = gateway
```

over constructing dependencies internally:

```python
class OrderService:
    def create_order(self, amount: int) -> Order:
        gateway = PaymentGateway()
        ...
```

The first design allows:

```python
service = OrderService(
    repository=Mock(spec=OrderRepository),
    gateway=Mock(spec=PaymentGateway),
)
```

This is not merely a testing technique. Explicit dependency boundaries generally improve architecture, substitutability, and operational control.

---

## Mocking and Interfaces

Mocks become safer when dependencies expose stable interfaces.

Using a protocol:

```python
from typing import Protocol


class PaymentGateway(Protocol):
    def charge(self, amount: int) -> PaymentResult:
        ...
```

A mock can be created against that contract:

```python
gateway = create_autospec(
    PaymentGateway,
)
```

This reduces accidental coupling to a concrete implementation.

---

## Mocking and Type Checking

Mocks are dynamically flexible, so static typing can become weaker around them.

Prefer:

```python
gateway = create_autospec(PaymentGateway)
```

over an unconstrained:

```python
gateway = Mock()
```

When necessary, annotate test doubles explicitly or use typed test-fake classes.

A handwritten fake can sometimes provide stronger type safety than a heavily configured mock.

---

## Mocks vs Fakes

Consider a repository:

```python
class InMemoryOrderRepository:
    def __init__(self) -> None:
        self.orders: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self.orders[order.id] = order

    def get(self, order_id: str) -> Order | None:
        return self.orders.get(order_id)
```

This is a fake rather than a mock.

A fake is often better when the dependency has meaningful behavior that multiple tests need.

| Use | Mock | Fake |
|---|---|---|
| Verify call | Excellent | Poor |
| Control return values | Excellent | Good |
| Model complex behavior | Poorer | Better |
| Reuse across tests | Good | Excellent |
| Detect interaction contracts | Excellent | Limited |
| Preserve realistic semantics | Limited | Often better |

---

## Mocks vs Integration Tests

A healthy test architecture uses both.

```text
                    Test Suite
                       │
          ┌────────────┴────────────┐
          │                         │
       Unit Tests             Integration Tests
          │                         │
       mocks/fakes             real dependencies
          │                         │
     fast + isolated          realistic semantics
```

Mocks answer:

> Did this component behave correctly given controlled dependency behavior?

Integration tests answer:

> Do these components actually work together correctly?

Neither replaces the other.

---

## Contract Testing

Mocks can accidentally encode an incorrect understanding of an external API.

For example:

```python
client.get_customer.return_value = {
    "id": "customer-1",
}
```

The mock may pass forever even if the real API changes.

Contract tests can validate:

- request structure;
- response schema;
- status codes;
- serialization;
- compatibility.

For important microservice or gRPC boundaries, contract testing can complement mocks.

---

## Mocking External APIs: Recommended Layering

A practical strategy:

```text
Unit tests
    │
    └── mocked HTTP client

Integration tests
    │
    └── controlled service/test environment

Contract tests
    │
    └── request/response compatibility

Production
    │
    └── real external service
```

Do not make every unit test depend on a live external API.

---

## Resetting Mocks

Mocks can retain call history.

```python
mock.reset_mock()
```

However, relying heavily on reset operations can indicate poor test isolation.

Prefer creating a fresh mock per test:

```python
@pytest.fixture
def gateway() -> Mock:
    return Mock(spec=PaymentGateway)
```

This makes test state explicit and avoids cross-test contamination.

---

## Mock Lifecycle

Patching should have a clear lifetime.

Prefer:

```python
with patch("orders.service.PaymentGateway") as gateway:
    ...
```

over manually starting and stopping patches:

```python
patcher = patch("orders.service.PaymentGateway")
gateway = patcher.start()

# test

patcher.stop()
```

If manual patchers are necessary, register cleanup reliably:

```python
self.addCleanup(patcher.stop)
```

Uncleaned patches can leak state into subsequent tests.

---

## `unittest.mock` with pytest

pytest works directly with `unittest.mock`:

```python
from unittest.mock import Mock, patch
```

A pytest test can therefore use:

```python
def test_payment_failure() -> None:
    gateway = Mock(spec=PaymentGateway)
    gateway.charge.side_effect = PaymentProviderError()

    ...
```

pytest does not require a separate mocking framework.

---

## `pytest-mock`

The `pytest-mock` plugin provides the `mocker` fixture:

```python
def test_payment(
    mocker,
) -> None:
    gateway = mocker.Mock(spec=PaymentGateway)

    gateway.charge.return_value = True

    ...
```

It also provides convenient patching:

```python
def test_payment(mocker) -> None:
    charge = mocker.patch(
        "orders.service.PaymentGateway.charge",
        return_value=True,
    )

    ...

    charge.assert_called_once()
```

The plugin manages cleanup automatically.

Use it when it improves consistency in a pytest-heavy codebase. `unittest.mock` remains the underlying standard-library foundation.

---

## Mocking Async Code

For async services:

```python
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_create_order() -> None:
    gateway = AsyncMock(spec=PaymentGateway)
    gateway.charge.return_value = PaymentResult(
        success=True,
    )

    service = OrderService(gateway=gateway)

    result = await service.create_order(100)

    assert result.success is True

    gateway.charge.assert_awaited_once_with(100)
```

Also test async failure paths:

```python
gateway.charge.side_effect = TimeoutError
```

Important async behaviors include:

- awaiting the dependency;
- cancellation;
- timeout handling;
- retry behavior;
- concurrency;
- task failure propagation.

Mocks should not hide incorrect coroutine usage.

---

## Mocking Concurrency

Concurrency tests require special care.

A mock can verify that a function was invoked:

```python
worker = Mock()
```

but this does not prove:

- thread safety;
- race-free state transitions;
- lock correctness;
- task scheduling;
- cancellation safety.

For concurrency behavior, combine mocks with real concurrency tests.

For example:

```text
Unit test
 → mock external service
 → verify business decision

Concurrency test
 → real threads/tasks
 → shared state
 → synchronization behavior
```

---

## Mocking Transactions

A mock can verify that transaction boundaries are invoked:

```python
transaction = Mock()

service = OrderService(transaction=transaction)

...
```

But it cannot validate actual transaction semantics.

Use real database integration tests for:

- rollback;
- commit;
- isolation;
- deadlocks;
- locking;
- concurrent writes.

Transaction behavior is part of PostgreSQL or database semantics, not merely application control flow.

---

## Mocking Logging

Logging can be mocked when a specific audit or security event is part of the behavior.

```python
with patch("orders.service.logger") as logger:
    service.cancel_order("order-1")

    logger.info.assert_called_once()
```

Do not assert every log statement.

Logging implementation is usually less important than externally observable behavior.

For operationally important logs, structured logging and integration/observability tests may provide more value than extensive mock assertions.

---

## Mocking Metrics

Similarly, avoid tightly coupling tests to every metrics call.

If emitting a metric is a contractual requirement:

```python
metrics.increment.assert_called_once_with(
    "orders.created",
)
```

Otherwise, prefer testing the behavior that causes the metric rather than implementation-level telemetry calls.

---

## Mocking Security Boundaries

Mock authentication providers when testing application authorization logic:

```python
identity = Mock(spec=IdentityProvider)
identity.get_user.return_value = User(
    id="user-1",
    role="admin",
)
```

But authorization should still be tested against meaningful role and permission matrices.

Mocks must not cause security tests to bypass the authorization layer accidentally.

A dangerous test is one where the mock always returns an administrator and therefore makes every endpoint appear authorized.

---

## Security Considerations

Mocking introduces several security risks in test design.

### Never Use Real Credentials

Do not place production:

- API keys;
- OAuth tokens;
- database passwords;
- AWS credentials;
- private keys

inside mocks or fixtures.

### Avoid Production Endpoints

Tests should never accidentally call production services because a mock was not applied.

Use environment isolation and explicit test configuration.

### Test Negative Paths

Do not only mock successful authentication or authorization.

Test:

```text
anonymous
authenticated
insufficient permissions
expired credentials
revoked credentials
```

### Avoid Overly Permissive Mocks

A mock that accepts every call can hide incorrect authorization or dependency usage.

Use `spec`, explicit return values, and meaningful assertions.

---

## Scalability Considerations

Mocks improve test execution speed, but excessive mocking can produce a large suite of low-fidelity tests.

A scalable testing strategy balances:

| Layer | Typical dependency strategy |
|---|---|
| Unit | Mocks/fakes |
| Component | Selected real dependencies |
| Integration | Real infrastructure |
| Contract | Controlled external interfaces |
| E2E | Production-like stack |

The objective is fast feedback without losing confidence in real system behavior.

---

## Reliability and CI/CD

Mocks are particularly useful in CI because they remove unnecessary environmental dependencies.

A unit test should ideally not fail because:

- PostgreSQL is temporarily unavailable;
- Redis is down;
- Kafka is unreachable;
- an external API is rate-limiting requests;
- DNS is unavailable.

Those failure modes should be tested separately.

A reliable CI pipeline typically has:

```text
Commit
  │
  ├── lint/type checks
  │
  ├── fast unit tests
  │      └── mocks/fakes
  │
  ├── integration tests
  │      └── real dependencies
  │
  └── contract/E2E tests
         └── controlled environments
```

---

## Performance Considerations

Mock-heavy unit tests are generally much faster than infrastructure-heavy tests.

For example:

```text
10,000 unit tests
    → milliseconds to low minutes

100 integration tests
    → potentially minutes

10 end-to-end tests
    → potentially minutes or longer
```

Actual performance depends on the system and environment.

Do not optimize purely for test speed by replacing every real dependency with a mock. The value of a test depends on the confidence it provides.

---

## Maintainability

Mock-heavy tests have a maintenance cost.

When a dependency interface changes:

```text
PaymentGateway
      │
      ├── production implementation
      ├── unit-test mocks
      ├── integration tests
      └── contract tests
```

Mocks may need updates.

`autospec` and explicit interfaces help detect drift.

Fakes can sometimes reduce repeated mock configuration when many tests need the same realistic behavior.

---

## Common Mistakes

### Patching the Wrong Location

Incorrect:

```python
patch("payments.PaymentGateway")
```

when the code uses:

```python
from payments import PaymentGateway
```

and looks up:

```python
orders.PaymentGateway
```

Patch the lookup location.

### Using `Mock` for Async Code

Use `AsyncMock` when the callable is awaited.

### Mocking Everything

Excessive mocks produce tests that can pass while real integrations are broken.

### Testing Implementation Details

Do not assert every private method call.

### Unconstrained Mocks

Typos can silently create mock attributes.

Prefer `spec` or `autospec`.

### Forgetting Cleanup

Patches that leak beyond a test can create order-dependent failures.

### Mocking the Database Too Aggressively

A mock cannot validate SQL or transaction semantics.

### Giant Chained Mocks

This:

```python
client.return_value.session.return_value.response.json.return_value
```

usually indicates a design or testability problem.

Prefer explicit abstractions.

---

## Production Pitfalls

### Mocking the Wrong Boundary

A test may mock an internal implementation rather than an external dependency, making refactoring difficult.

### Mocking Protocols Incorrectly

A mock may return a value that looks valid but does not reflect real HTTP, database, Kafka, or Redis semantics.

### Unrealistic Responses

If production returns:

```json
{
  "data": {
    "id": "order-1"
  },
  "meta": {
    "request_id": "abc"
  }
}
```

but the mock returns:

```python
{"id": "order-1"}
```

the test may validate an API contract that does not actually exist.

### Missing Failure Cases

Happy-path mocks are easy to write. Production reliability requires testing timeouts, retries, malformed responses, and dependency failures.

### Hidden Coupling

Large numbers of patch statements can indicate that application components are too tightly coupled to concrete implementations.

---

## A Practical Mocking Pattern

A clean service boundary might look like:

```python
from typing import Protocol


class PaymentGateway(Protocol):
    async def charge(
        self,
        amount: int,
    ) -> PaymentResult:
        ...


class OrderRepository(Protocol):
    async def save(self, order: Order) -> None:
        ...


class EventPublisher(Protocol):
    async def publish(self, event: OrderCreated) -> None:
        ...


class OrderService:
    def __init__(
        self,
        gateway: PaymentGateway,
        repository: OrderRepository,
        publisher: EventPublisher,
    ) -> None:
        self.gateway = gateway
        self.repository = repository
        self.publisher = publisher

    async def create_order(self, amount: int) -> Order:
        payment = await self.gateway.charge(amount)

        if not payment.success:
            raise PaymentFailedError

        order = Order.create(amount)

        await self.repository.save(order)
        await self.publisher.publish(
            OrderCreated(order_id=order.id),
        )

        return order
```

The test can isolate all external boundaries:

```python
from unittest.mock import AsyncMock, create_autospec


@pytest.mark.asyncio
async def test_create_order() -> None:
    gateway = create_autospec(PaymentGateway)
    repository = create_autospec(OrderRepository)
    publisher = create_autospec(EventPublisher)

    gateway.charge = AsyncMock(
        return_value=PaymentResult(success=True),
    )
    repository.save = AsyncMock()
    publisher.publish = AsyncMock()

    service = OrderService(
        gateway=gateway,
        repository=repository,
        publisher=publisher,
    )

    order = await service.create_order(100)

    assert order.amount == 100

    gateway.charge.assert_awaited_once_with(100)
    repository.save.assert_awaited_once()
    publisher.publish.assert_awaited_once()
```

The test verifies the service's behavior and important dependency interactions without requiring PostgreSQL, Kafka, or a payment provider.

---

## Recommended Mocking Decision Framework

When deciding whether to mock a dependency, ask:

```text
Is this dependency external to the unit?
        │
        ├── No → Prefer testing real internal behavior
        │
        └── Yes
             │
             ├── Is its behavior part of this test?
             │       │
             │       ├── Yes → Consider integration testing
             │       │
             │       └── No → Mock/fake it
             │
             └── Is interaction itself contractual?
                     │
                     ├── Yes → Verify the interaction
                     └── No → Prefer state/behavior assertions
```

This prevents mocking from becoming an automatic default.

---

## Mocking Checklist

### Before Mocking

- [ ] Is the dependency genuinely outside the unit under test?
- [ ] Is the test trying to isolate behavior?
- [ ] Would a fake or integration test provide more value?
- [ ] Is dependency injection available?

### When Creating the Mock

- [ ] Use `spec` or `autospec` where practical.
- [ ] Use `AsyncMock` for awaited dependencies.
- [ ] Configure explicit return values.
- [ ] Configure realistic failure responses.
- [ ] Avoid `create=True` unless intentional.
- [ ] Give complex cases meaningful names.

### When Patching

- [ ] Patch where the code looks up the dependency.
- [ ] Keep patch scope as small as practical.
- [ ] Ensure cleanup occurs automatically.
- [ ] Avoid patching internal implementation details.

### Assertions

- [ ] Prefer behavior/state assertions.
- [ ] Verify interactions only when they matter.
- [ ] Verify important call arguments.
- [ ] Test failure and retry paths.
- [ ] Avoid asserting incidental calls.

### Integration

- [ ] Test real PostgreSQL behavior where relevant.
- [ ] Test real Redis semantics where relevant.
- [ ] Test Kafka delivery/serialization behavior where relevant.
- [ ] Test Celery/broker behavior where relevant.
- [ ] Test external API contracts where relevant.

---

## Interview Traps

### What Is Mocking?

Mocking replaces a dependency with a controlled test double so that a test can isolate and verify the behavior of the component under test.

### Mock vs Stub?

A stub primarily supplies controlled responses. A mock additionally records interactions and is commonly used to verify how the dependency was called.

### What Is the Most Important `patch()` Rule?

Patch the name where the code under test looks up the dependency, not necessarily the module where that dependency was originally defined.

### Why Use `AsyncMock`?

An async dependency returns an awaitable and is normally used with `await`. `AsyncMock` models this behavior and provides await-specific assertions.

### Why Use `autospec`?

It constrains mocks to the target's interface and callable signatures, helping detect incorrect method names and argument usage.

### Should You Mock PostgreSQL?

Mock the repository or database boundary when testing application logic that does not depend on database semantics. Use integration tests for SQL, transactions, constraints, locking, isolation, and other real PostgreSQL behavior.

### Why Is Over-Mocking Dangerous?

It can make tests tightly coupled to implementation details and allow tests to pass even when real integrations or contracts are broken.

### Does a Mock Validate an External API?

No. A mock validates the behavior programmed into the test. Contract or integration tests are required to validate the real external API's schema and semantics.

### Mock vs Fake?

A mock is particularly useful for controlled behavior and interaction verification. A fake is a simplified working implementation and is often better when realistic dependency behavior is reused across many tests.

### What Should Be Mocked in a Backend Service?

Usually external boundaries such as repositories, payment gateways, HTTP clients, message publishers, and other infrastructure dependencies when their real behavior is outside the unit being tested.

### Should Every Dependency Be Mocked?

No. Mocking is a design decision. Excessive mocking reduces realism and can create brittle tests. Combine unit tests with integration, contract, and end-to-end tests.

## Key Takeaways

- **Mock external boundaries, not internal behavior:** use mocks to isolate units from databases, APIs, queues, caches, and other infrastructure when their real semantics are outside the test's scope.
- **Patch where the dependency is looked up:** Python imports bind names locally, so patching the module where an object was originally defined is often incorrect.
- **Constrain mocks:** prefer `spec`/`autospec`, use `AsyncMock` for asynchronous dependencies, and configure realistic return values and failure modes.
- **Avoid over-mocking:** prioritize observable behavior and use interaction assertions only when the interaction is itself part of the contract.
- **Mocks do not replace integration tests:** PostgreSQL, Redis, Kafka, Celery, HTTP, transaction, concurrency, and external API semantics require tests against appropriately realistic infrastructure.