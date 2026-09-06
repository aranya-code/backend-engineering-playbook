# 02- unittest

## Overview

`unittest` is Python's standard-library testing framework. It provides the core primitives required to structure, execute, isolate, and report automated tests without introducing an external testing dependency.

It is based primarily on:

- `TestCase`;
- test methods;
- assertions;
- fixtures;
- test suites;
- test runners;
- `unittest.mock`.

A typical `unittest` test follows:

```text
TestCase
   ↓
setUp
   ↓
test method
   ↓
assertions
   ↓
tearDown
```

For backend engineering, `unittest` is useful when:

- a project wants standard-library-only testing;
- a library should minimize dependencies;
- existing systems already use `unittest`;
- compatibility with Python's standard tooling matters;
- engineers need a foundation for understanding higher-level frameworks such as `pytest`.

`pytest` is often preferred for modern Python application development because of its fixture system, parametrization, plugin ecosystem, and concise syntax. However, understanding `unittest` remains important because it is part of Python itself and is widely present in production codebases and third-party libraries.

---

## Why `unittest` Exists

Python needs a standardized mechanism for expressing expectations about code behavior.

Without a testing framework, developers would need to build:

```text
test discovery
test execution
assertion reporting
fixture lifecycle
failure reporting
test suites
```

`unittest` provides these capabilities in the standard library.

A test can be executed directly:

```bash
python -m unittest
```

or with more specific discovery options:

```bash
python -m unittest discover
```

---

## Core Architecture

The primary components are:

```text
                    unittest
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   TestCase         TestSuite       Mock
        │              │
        ▼              ▼
   Test methods    Collection
        │
        ▼
   Assertions
        │
        ▼
   TestResult
        │
        ▼
   TestRunner
```

| Component | Responsibility |
|---|---|
| `TestCase` | Defines related test behavior |
| Test method | Individual test scenario |
| Assertion | Verifies expected behavior |
| Fixture | Sets up and cleans up resources |
| `TestSuite` | Groups tests |
| `TestLoader` | Discovers/loads tests |
| `TestRunner` | Executes tests |
| `TestResult` | Records outcomes |
| `unittest.mock` | Provides test doubles |

---

## Basic Test Case

A minimal test looks like:

```python
import unittest


def calculate_total(price: int, quantity: int) -> int:
    return price * quantity


class TestCalculateTotal(unittest.TestCase):
    def test_calculate_total(self) -> None:
        result = calculate_total(100, 3)

        self.assertEqual(result, 300)


if __name__ == "__main__":
    unittest.main()
```

The test class inherits from `unittest.TestCase`.

Methods beginning with `test` are discovered as test methods.

---

## Running Tests

Run a specific module:

```bash
python -m unittest tests.test_orders
```

Run a specific class:

```bash
python -m unittest tests.test_orders.TestOrderService
```

Run a specific test:

```bash
python -m unittest tests.test_orders.TestOrderService.test_create_order
```

Discover tests:

```bash
python -m unittest discover
```

Specify a directory:

```bash
python -m unittest discover -s tests
```

Specify a pattern:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Using `python -m unittest` ensures that the test runner is associated with the selected Python interpreter.

---

## Test Discovery

By convention, `unittest` discovery searches for test modules matching:

```text
test*.py
```

A common project structure is:

```text
project/
├── src/
│   └── app/
│       ├── orders.py
│       └── users.py
└── tests/
    ├── test_orders.py
    └── test_users.py
```

Run:

```bash
python -m unittest discover -s tests
```

Discovery loads matching modules and identifies `TestCase` classes and test methods.

---

## Naming Tests

Use names that describe behavior.

Prefer:

```python
def test_inactive_customer_cannot_create_order(self) -> None:
    ...
```

over:

```python
def test_order_3(self) -> None:
    ...
```

A useful test name should communicate:

```text
condition
+
behavior
+
expected result
```

This makes CI failures easier to understand.

---

## Arrange, Act, Assert

Although `unittest` does not enforce a specific test structure, the Arrange-Act-Assert model is useful.

```python
def test_create_order(self) -> None:
    # Arrange
    service = OrderService(repository=FakeOrderRepository())
    customer = Customer(id="customer-1", active=True)

    # Act
    order = service.create_order(customer, amount=2500)

    # Assert
    self.assertEqual(order.amount, 2500)
    self.assertEqual(order.status, OrderStatus.CREATED)
```

Keep the test focused on the behavior being verified.

---

## Assertions

`TestCase` provides many assertion methods.

| Assertion | Purpose |
|---|---|
| `assertEqual(a, b)` | Values are equal |
| `assertNotEqual(a, b)` | Values differ |
| `assertTrue(x)` | Value is truthy |
| `assertFalse(x)` | Value is falsy |
| `assertIs(a, b)` | Same object |
| `assertIsNone(x)` | Value is `None` |
| `assertIsNotNone(x)` | Value is not `None` |
| `assertIn(a, b)` | `a` is contained in `b` |
| `assertNotIn(a, b)` | `a` is not contained in `b` |
| `assertIsInstance(x, T)` | Instance has expected type |
| `assertRaises(E)` | Code raises exception |
| `assertAlmostEqual(a, b)` | Values approximately equal |

Prefer the most specific assertion that communicates intent.

---

## Equality vs Identity Assertions

Use:

```python
self.assertEqual(actual, expected)
```

for value equality.

Use:

```python
self.assertIs(actual, expected)
```

for object identity.

For example:

```python
self.assertIsNone(result)
```

is preferable to:

```python
self.assertEqual(result, None)
```

when the contract specifically requires `None`.

---

## Exception Testing

Use `assertRaises` for expected exceptions.

```python
def test_invalid_amount_is_rejected(self) -> None:
    with self.assertRaises(ValueError):
        calculate_total(-100, 2)
```

You can also verify the exception message:

```python
def test_invalid_amount_message(self) -> None:
    with self.assertRaisesRegex(ValueError, "price must be positive"):
        calculate_total(-100, 2)
```

Do not catch exceptions manually unless the test specifically needs to inspect behavior that `assertRaises` cannot express cleanly.

---

## Testing Return Values

A test should verify meaningful behavior.

Weak:

```python
def test_create_order(self) -> None:
    service.create_order(...)
```

Stronger:

```python
def test_create_order(self) -> None:
    order = service.create_order(
        customer_id="customer-1",
        amount=2500,
    )

    self.assertEqual(order.amount, 2500)
    self.assertEqual(order.status, OrderStatus.CREATED)
```

A test that merely executes code can provide misleading confidence.

---

## `setUp`

`setUp()` runs before each test method.

```python
import unittest


class TestOrderService(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryOrderRepository()
        self.service = OrderService(repository=self.repository)

    def test_create_order(self) -> None:
        order = self.service.create_order(
            customer_id="customer-1",
            amount=2500,
        )

        self.assertEqual(order.amount, 2500)
```

This is useful for common per-test setup.

Because it runs for every test, keep it inexpensive and focused.

---

## `tearDown`

`tearDown()` runs after each test method that reaches the normal fixture lifecycle.

```python
class TestFileProcessor(unittest.TestCase):
    def setUp(self) -> None:
        self.file = TemporaryFile()

    def tearDown(self) -> None:
        self.file.close()
```

For resources where cleanup must happen even if setup or test execution fails, `addCleanup()` is often safer.

---

## `addCleanup`

`addCleanup()` registers cleanup functions.

```python
class TestClient(unittest.TestCase):
    def setUp(self) -> None:
        self.client = create_client()
        self.addCleanup(self.client.close)
```

This is particularly useful when setup has multiple resources:

```python
self.db = create_database()
self.addCleanup(self.db.close)

self.redis = create_redis()
self.addCleanup(self.redis.close)
```

Cleanup is executed in reverse order of registration.

This makes resource ownership explicit.

---

## `setUpClass` and `tearDownClass`

Use `setUpClass()` for expensive setup shared by all tests in a class.

```python
class TestPostgresRepository(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = create_test_database()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.database.close()
```

This can improve performance, but shared state increases coupling risk.

Use class-level resources only when they are safe to share.

---

## `setUpModule` and `tearDownModule`

Module-level fixtures are also available:

```python
def setUpModule() -> None:
    ...


def tearDownModule() -> None:
    ...
```

They are useful for expensive module-wide setup.

However, broader fixture scope means greater risk of state leakage.

Prefer the narrowest practical lifecycle.

---

## Fixture Lifecycle

The overall lifecycle can be represented as:

```text
Test module
    ↓
setUpModule
    ↓
Test class
    ↓
setUpClass
    ↓
For each test
    ↓
setUp
    ↓
test_method
    ↓
tearDown
    ↓
Next test
    ↓
tearDownClass
    ↓
tearDownModule
```

`addCleanup()` provides an additional cleanup mechanism associated with individual test cases.

---

## Cleanup on Failure

A common mistake is assuming `tearDown()` handles every possible setup failure.

For resource-specific cleanup, use:

```python
def setUp(self) -> None:
    self.client = create_client()
    self.addCleanup(self.client.close)
```

This is particularly useful when setup itself can fail after some resources have already been created.

---

## `skip`

Tests can be skipped explicitly.

```python
@unittest.skip("requires external service")
def test_external_payment_flow(self) -> None:
    ...
```

Conditional skipping is also possible:

```python
@unittest.skipUnless(
    os.getenv("RUN_INTEGRATION_TESTS"),
    "integration tests disabled",
)
def test_payment_provider(self) -> None:
    ...
```

Skipping should not become a way to hide failing tests.

A skipped test should have a legitimate reason and preferably an explicit execution condition.

---

## Expected Failures

`expectedFailure` indicates that a test is expected to fail.

```python
@unittest.expectedFailure
def test_known_bug(self) -> None:
    self.assertEqual(current_behavior(), expected_behavior())
```

This can document a known defect temporarily.

Do not use expected failures as permanent substitutes for fixing broken behavior.

---

## Subtests

`subTest()` allows multiple related cases within one test method.

```python
class TestValidation(unittest.TestCase):
    def test_valid_amounts(self) -> None:
        cases = [
            (1, True),
            (100, True),
            (0, False),
            (-1, False),
        ]

        for amount, expected in cases:
            with self.subTest(amount=amount):
                self.assertEqual(
                    is_valid_amount(amount),
                    expected,
                )
```

If one subtest fails, the remaining cases can still execute.

This can be useful for small data-driven cases.

For larger parameterized test suites, `pytest.mark.parametrize` is often more expressive.

---

## Table-Driven Testing

`subTest()` provides a standard-library approach to table-driven tests.

```python
class TestStatusMapping(unittest.TestCase):
    def test_status_mapping(self) -> None:
        cases = [
            (200, "success"),
            (400, "client_error"),
            (500, "server_error"),
        ]

        for status_code, expected in cases:
            with self.subTest(status_code=status_code):
                self.assertEqual(
                    map_status(status_code),
                    expected,
                )
```

The test data becomes explicit and easy to extend.

---

## `unittest.mock`

`unittest.mock` is one of the most important parts of the standard testing ecosystem.

It provides tools for replacing dependencies during tests.

```text
Service
  ↓
PaymentClient
```

can become:

```text
Service
  ↓
Mock PaymentClient
```

This isolates the service from the external provider.

---

## `Mock`

Basic example:

```python
from unittest.mock import Mock


payment_client = Mock()
payment_client.charge.return_value = PaymentResult(
    transaction_id="txn-1",
)

service = PaymentService(payment_client=payment_client)

result = service.pay(
    order_id="order-1",
    amount=1000,
)

self.assertEqual(result.transaction_id, "txn-1")
```

Mocks can:

- return controlled values;
- raise exceptions;
- record calls;
- verify arguments.

---

## `MagicMock`

`MagicMock` extends `Mock` with support for many Python magic methods.

For example:

```python
from unittest.mock import MagicMock


response = MagicMock()
response.status_code = 200
response.json.return_value = {"status": "ok"}
```

Use `MagicMock` when magic-method behavior is required.

Otherwise, ordinary `Mock` is often clearer.

---

## `spec`

A mock can be constrained to an existing interface.

```python
payment_client = Mock(spec=PaymentClient)
```

This reduces the risk of inventing attributes that do not exist on the real dependency.

Without a specification:

```python
payment_client.chagre(...)
```

could accidentally create a mock attribute because of a typo.

---

## `spec_set`

`spec_set` is stricter:

```python
payment_client = Mock(spec_set=PaymentClient)
```

It prevents setting attributes that are not present on the specified object.

This is useful when tests should closely follow the actual dependency interface.

---

## `autospec`

`autospec` can create mocks based on the actual callable signatures.

```python
from unittest.mock import create_autospec


payment_client = create_autospec(PaymentClient)
```

This helps detect incorrect calls.

For example, if the real method requires:

```python
charge(order_id, amount)
```

a test incorrectly calling:

```python
payment_client.charge(amount)
```

can fail earlier.

Mocks that reflect real interfaces are generally safer than unrestricted mocks.

---

## Verifying Calls

Mocks can verify interactions:

```python
payment_client.charge.assert_called_once_with(
    "order-1",
    1000,
)
```

Other common assertions include:

```python
mock.assert_called()
mock.assert_not_called()
mock.assert_called_once()
mock.assert_called_with(...)
mock.assert_called_once_with(...)
```

Interaction assertions are useful when the interaction itself is part of the behavior.

Avoid asserting every internal call merely because the mock makes it possible.

---

## Mock Side Effects

`side_effect` can simulate failures:

```python
payment_client.charge.side_effect = PaymentProviderTimeout()
```

The service can then be tested:

```python
with self.assertRaises(PaymentTimeout):
    service.pay(
        order_id="order-1",
        amount=1000,
    )
```

It can also provide sequential results:

```python
client.fetch.side_effect = [
    TimeoutError(),
    {"status": "ok"},
]
```

This is useful for testing retry behavior.

---

## Patching

`patch()` temporarily replaces an object during a test.

```python
from unittest.mock import patch


with patch("app.orders.send_email") as mock_send:
    create_order(...)

    mock_send.assert_called_once()
```

The most important rule is:

> Patch where the dependency is looked up, not necessarily where it was originally defined.

---

## Patch Where Used

Suppose:

```python
# app/orders.py
from app.email import send_email
```

and:

```python
# app/email.py
def send_email(...):
    ...
```

If `orders.py` calls:

```python
send_email(...)
```

patch:

```python
patch("app.orders.send_email")
```

not:

```python
patch("app.email.send_email")
```

The `orders` module already has its own reference.

This is one of the most common `unittest.mock` mistakes.

---

## Patching Classes

A class can be patched:

```python
with patch("app.orders.PaymentClient") as payment_client:
    instance = payment_client.return_value
    instance.charge.return_value = PaymentResult(
        transaction_id="txn-1",
    )

    ...
```

However, patching construction can create tightly coupled tests.

Dependency injection is often cleaner:

```python
service = PaymentService(payment_client=fake_client)
```

Use patching when replacing an existing lookup is simpler than restructuring the code.

---

## Patching Environment Variables

`patch.dict()` can temporarily modify dictionaries.

```python
import os
from unittest.mock import patch


with patch.dict(
    os.environ,
    {"APP_ENV": "test"},
):
    config = load_config()

    self.assertEqual(config.environment, "test")
```

This prevents permanent mutation of the process environment during tests.

---

## Patching Time

Time-dependent code is often easier to test when time is injected.

Instead of patching:

```python
datetime.now
```

prefer:

```python
class Clock(Protocol):
    def now(self) -> datetime:
        ...
```

and inject a test clock.

This creates a clearer dependency boundary.

Patching is still useful when modifying legacy code that directly accesses global time functions.

---

## `patch.object`

`patch.object()` patches an attribute on an object.

```python
with patch.object(
    service,
    "send_notification",
) as mock_send:
    service.create_order(...)

    mock_send.assert_called_once()
```

Use it when the object reference is already available.

---

## `patch.dict`

`patch.dict()` temporarily modifies dictionaries.

Common uses include:

- environment variables;
- configuration dictionaries;
- registry state.

```python
with patch.dict(
    settings,
    {"FEATURE_NEW_CHECKOUT": True},
):
    ...
```

The original dictionary state is restored after the context exits.

---

## `patch.multiple`

Multiple attributes can be patched together.

```python
with patch.multiple(
    "app.config",
    DATABASE_URL="test-db",
    REDIS_URL="test-redis",
):
    ...
```

Use sparingly.

Large patch blocks can make test setup difficult to understand.

---

## AsyncMock

For asynchronous dependencies, use `AsyncMock`.

```python
from unittest.mock import AsyncMock


client = AsyncMock()

client.fetch_order.return_value = Order(
    id="order-1",
)

order = await client.fetch_order("order-1")

client.fetch_order.assert_awaited_once_with("order-1")
```

Useful assertions include:

```python
assert_awaited()
assert_awaited_once()
assert_awaited_with(...)
assert_awaited_once_with(...)
assert_not_awaited()
```

Do not use ordinary `Mock` when the dependency must be awaited.

---

## Testing FastAPI Services

For application-level tests, separate service behavior from HTTP behavior where practical.

```text
FastAPI route
      ↓
OrderService
      ↓
Repository
```

Unit test:

```text
OrderService
      ↓
Fake repository
```

API test:

```text
HTTP client
      ↓
FastAPI
      ↓
Service
```

Integration test:

```text
HTTP client
      ↓
FastAPI
      ↓
Service
      ↓
PostgreSQL
```

`unittest` can be used for all these layers, although frameworks such as `pytest` often provide more convenient fixtures for complex application testing.

---

## Testing Django Applications

Django integrates heavily with `unittest.TestCase` and its own test classes.

A test may look like:

```python
from django.test import TestCase


class OrderTests(TestCase):
    def test_create_order(self) -> None:
        response = self.client.post(
            "/orders/",
            data={
                "amount": 2500,
            },
        )

        self.assertEqual(response.status_code, 201)
```

Django's test framework provides database-aware behavior and test client functionality on top of Python's testing model.

Use Django's specialized classes when framework integration is part of what you need to verify.

---

## Testing Database Transactions

For transaction-sensitive behavior, use an integration test against the real database engine.

Example scenarios:

```text
create record
→ commit

create record
→ constraint failure
→ rollback
```

A mock repository cannot verify:

- PostgreSQL constraints;
- transaction isolation;
- locking;
- SQL semantics.

`unittest` can structure these tests, but the infrastructure should still be real when the behavior under test depends on it.

---

## Testing REST APIs

An API test should verify the public contract.

```python
class TestOrdersAPI(unittest.TestCase):
    def test_create_order_returns_created(self) -> None:
        response = client.post(
            "/orders",
            json={
                "customer_id": "customer-1",
                "amount": 2500,
            },
        )

        self.assertEqual(response.status_code, 201)

        body = response.json()

        self.assertEqual(body["status"], "created")
        self.assertEqual(body["amount"], 2500)
```

Avoid coupling API tests to private service implementation.

---

## Testing Authentication and Authorization

Security behavior should be explicit.

```python
def test_unauthenticated_request_is_rejected(self) -> None:
    response = client.get("/admin/orders")

    self.assertEqual(response.status_code, 401)
```

Also test:

```text
authenticated + unauthorized
authenticated + authorized
wrong tenant
expired credential
invalid credential
```

Authorization regressions should have dedicated tests because they can expose security vulnerabilities even when normal functional behavior remains correct.

---

## Testing Message Consumers

A message-processing unit test can control the broker-facing dependency:

```python
consumer = Mock()
consumer.receive.return_value = OrderCreated(
    order_id="order-1",
)

processor = OrderProcessor(repository=fake_repository)

processor.handle(consumer.receive())

repository.assert_called_once()
```

Integration tests should verify actual broker semantics when required.

For Kafka and similar systems, test important guarantees around:

- acknowledgment;
- offset handling;
- duplicate delivery;
- retries;
- schema compatibility.

---

## Testing Celery Tasks

A task should expose application behavior that can be tested independently.

```python
class TestProcessOrder(unittest.TestCase):
    def test_process_order(self) -> None:
        result = process_order(
            order_id="order-1",
        )

        self.assertEqual(result.status, "completed")
```

Task infrastructure can then be tested separately.

Avoid putting the entire business workflow directly inside the Celery task wrapper.

Prefer:

```text
Celery task
 ↓
Application service
 ↓
Business logic
```

This improves reuse and testability.

---

## Test Suites

`TestSuite` groups test cases.

```python
suite = unittest.TestSuite()

suite.addTest(
    TestOrderService("test_create_order")
)

runner = unittest.TextTestRunner()
runner.run(suite)
```

Manual suites are less common in modern projects because discovery is usually preferable.

They remain useful when:

- custom test selection is required;
- tests need explicit ordering/selection;
- integrating unusual test runners.

Do not use manual suites when normal discovery is sufficient.

---

## Test Loaders

`TestLoader` discovers tests.

```python
loader = unittest.TestLoader()

suite = loader.loadTestsFromTestCase(
    TestOrderService
)
```

It can also discover tests from modules and packages.

Most application developers should prefer:

```bash
python -m unittest discover
```

rather than manually constructing suites.

---

## Test Runners

The default runner can be invoked with:

```python
unittest.main()
```

It executes discovered tests and reports results.

CI systems generally depend on the process exit status:

```text
tests pass
→ exit code 0

test failure
→ non-zero exit code
```

This allows CI/CD systems to prevent unsafe releases.

---

## Failure Output

A useful test failure should expose:

```text
test name
expected value
actual value
location
exception/traceback
```

Specific assertions improve diagnostics.

Prefer:

```python
self.assertEqual(
    response.status_code,
    201,
)
```

over:

```python
self.assertTrue(response.status_code)
```

The first failure directly communicates the contract violation.

---

## Test Organization

A production project might use:

```text
tests/
├── unit/
│   ├── test_orders.py
│   └── test_pricing.py
├── integration/
│   ├── test_order_repository.py
│   └── test_redis_cache.py
└── api/
    └── test_orders_api.py
```

Another valid strategy is to organize by feature:

```text
tests/
├── orders/
│   ├── test_service.py
│   ├── test_repository.py
│   └── test_api.py
└── users/
    ├── test_service.py
    └── test_api.py
```

Choose the structure that makes the system easy to navigate.

---

## Test Isolation

Tests should not depend on execution order.

Avoid:

```text
test_create_user
      ↓
test_update_user relies on previous test
```

Prefer each test creating the state it needs.

For database tests, use:

- isolated test data;
- transactions;
- rollback;
- disposable databases;
- controlled fixtures.

The correct mechanism depends on the application and infrastructure.

---

## Deterministic Tests

Avoid uncontrolled dependencies on:

- current time;
- randomness;
- external networks;
- environment state;
- process-global mutable data;
- filesystem layout;
- test order.

For example:

```python
def test_expiration() -> None:
    now = datetime.now()
    ...
```

can become fragile around timing boundaries.

Injecting a clock makes the test deterministic.

---

## Temporary Files

Use `tempfile` for filesystem tests.

```python
import tempfile
import unittest
from pathlib import Path


class TestFileProcessor(unittest.TestCase):
    def test_process_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "orders.json"
            path.write_text(
                '{"id": "order-1"}',
                encoding="utf-8",
            )

            result = process_file(path)

            self.assertEqual(result.order_id, "order-1")
```

Temporary resources should not depend on developer-specific paths.

---

## Testing Environment Configuration

Avoid permanently modifying process state.

Use:

```python
with patch.dict(
    os.environ,
    {"APP_ENV": "test"},
):
    ...
```

rather than:

```python
os.environ["APP_ENV"] = "test"
```

without cleanup.

State leakage can cause failures in unrelated tests.

---

## Testing Logging

Logging usually should not be asserted line-by-line.

If logging behavior itself is important, use `assertLogs`.

```python
with self.assertLogs("app.orders", level="WARNING") as logs:
    service.cancel_order("order-1")

self.assertTrue(
    any("already cancelled" in message for message in logs.output)
)
```

For structured logging, prefer testing stable event names and fields rather than exact rendered log strings.

---

## Testing Warnings

Warnings can be captured with:

```python
with self.assertWarns(DeprecationWarning):
    legacy_function()
```

This is useful for verifying deprecation behavior and compatibility contracts.

---

## Testing Async Code

`unittest` supports asynchronous test cases through `IsolatedAsyncioTestCase`.

```python
import unittest


class TestOrderClient(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_order(self) -> None:
        order = await self.client.fetch_order("order-1")

        self.assertEqual(order.id, "order-1")
```

This provides an isolated event loop for each test case.

For async backend systems, also test:

- cancellation;
- timeouts;
- concurrent tasks;
- resource cleanup;
- exception propagation.

---

## Async Fixtures

`IsolatedAsyncioTestCase` supports async lifecycle methods.

```python
class TestOrderClient(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.client = AsyncOrderClient()

    async def asyncTearDown(self) -> None:
        await self.client.close()

    async def test_fetch_order(self) -> None:
        order = await self.client.fetch_order("order-1")

        self.assertEqual(order.id, "order-1")
```

This is useful for clients, connection pools, and async resources.

---

## Threading and Concurrency Tests

Concurrency tests should be designed around observable guarantees.

For example:

```text
two workers
   ↓
same order
   ↓
attempt concurrent update
   ↓
only one valid transition
```

`unittest` can organize the test, but concurrency behavior often requires:

- synchronization primitives;
- barriers;
- real databases;
- repeated execution;
- stress testing.

A single successful run does not prove the absence of a race condition.

---

## Property-Based Testing

`unittest` itself does not provide property-based test generation.

Libraries such as Hypothesis can complement it.

The distinction is:

```text
Example-based
→ explicit examples

Property-based
→ generated inputs + invariant
```

For example:

```text
serialize(deserialize(x))
```

should preserve a specified property for a broad class of valid inputs.

Use property-based testing where input-space exploration provides meaningful value.

---

## Coverage

Coverage tools can be used with `unittest`.

A typical command with `coverage.py` is:

```bash
coverage run -m unittest discover
coverage report
```

Coverage can identify untested code paths.

It cannot prove correctness.

The objective should be:

```text
meaningful behavior coverage
```

rather than maximizing a percentage mechanically.

---

## Performance of the Test Suite

A slow test suite reduces developer feedback speed.

Common causes include:

- excessive database setup;
- unnecessary integration tests;
- external network calls;
- large fixtures;
- repeated application startup;
- excessive mocking configuration;
- shared infrastructure contention.

Optimize test architecture without removing important coverage.

A useful approach is:

```text
fast unit tests
      ↓
integration tests
      ↓
API/contract tests
      ↓
E2E tests
```

---

## Parallel Test Execution

The standard `unittest` runner is not primarily a sophisticated parallel test orchestrator.

Projects needing parallel execution commonly use external tooling or CI-level parallelization.

Before parallelizing, ensure tests do not share:

- database state;
- filesystem paths;
- ports;
- environment variables;
- mutable global state.

Parallelism can expose hidden test coupling.

---

## `unittest` vs `pytest`

| Capability | `unittest` | `pytest` |
|---|---|---|
| Standard library | Yes | No |
| `TestCase` classes | Yes | Supported |
| Plain test functions | No native model | Yes |
| Fixtures | `setUp`/`tearDown` lifecycle | Rich fixture system |
| Parametrization | `subTest` | Native parametrization |
| Mocking | `unittest.mock` | Uses/extends standard mocking |
| Plugins | Limited ecosystem | Extensive ecosystem |
| Discovery | Built in | Built in |
| Async testing | `IsolatedAsyncioTestCase` | Plugin-based ecosystem |
| Learning curve | Moderate | Often simpler for application tests |
| Framework integration | Strong baseline | Extensive ecosystem |

`pytest` can execute many `unittest.TestCase` tests, which makes gradual migration possible.

---

## When to Prefer `unittest`

Use `unittest` when:

- standard-library-only dependencies are desirable;
- maintaining an existing `unittest` codebase;
- building a library with conservative dependencies;
- compatibility with established tooling matters;
- class-based test organization fits the project.

---

## When to Prefer `pytest`

`pytest` is often a better default for new backend application test suites when the project benefits from:

- reusable fixtures;
- parametrization;
- plugins;
- concise tests;
- flexible discovery;
- extensive framework integration.

The important skill is understanding testing principles rather than treating the test framework as the architecture.

---

## Migrating from `unittest` to `pytest`

A `unittest` test:

```python
class TestPricing(unittest.TestCase):
    def test_discount(self) -> None:
        result = calculate_discount(1000, 10)

        self.assertEqual(result, 100)
```

can become:

```python
def test_discount() -> None:
    result = calculate_discount(1000, 10)

    assert result == 100
```

The underlying behavioral contract remains the same.

Migration should focus on improving test maintainability rather than rewriting tests merely for syntax.

---

## Production Backend Testing Architecture

A realistic backend may use:

```text
                       CI/CD
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        Unit Tests             Static Checks
              │
              ▼
       Integration Tests
              │
      ┌───────┼────────┐
      ▼       ▼        ▼
 PostgreSQL  Redis    Kafka
              │
              ▼
        API / Contract
              │
              ▼
             E2E
```

`unittest` can provide the foundation for the unit and integration layers while framework-specific tooling can handle infrastructure-heavy tests.

---

## Security Considerations

Tests themselves can introduce security risks.

Avoid:

- production credentials;
- production databases;
- real payment credentials;
- real customer data;
- secrets committed to fixtures;
- logging sensitive test payloads.

Use synthetic test data.

For security-sensitive systems, test:

- authentication;
- authorization;
- tenant isolation;
- secret handling;
- input validation;
- SSRF protections;
- SQL injection resistance;
- webhook signature verification.

---

## Reliability Considerations

A reliable test suite should be:

```text
deterministic
+
isolated
+
repeatable
+
fast enough
+
meaningful
```

If tests frequently fail because of infrastructure noise, engineers may begin ignoring CI failures.

That is a serious reliability problem.

Treat flaky tests as engineering defects.

---

## CI/CD Integration

A simple CI command is:

```bash
python -m unittest discover -s tests -v
```

The `-v` option provides more detailed test output.

A typical pipeline might be:

```text
Checkout
  ↓
Install dependencies
  ↓
Lint
  ↓
Type check
  ↓
unittest
  ↓
Integration tests
  ↓
Coverage
  ↓
Build artifact
  ↓
Deploy
```

Tests should run against a clean, controlled environment.

---

## Docker and Kubernetes

Containerized tests should not accidentally depend on developer machine state.

Integration environments can provide:

```text
Test container
   ├── Python application
   ├── PostgreSQL
   ├── Redis
   └── Kafka
```

For Kubernetes-based CI, ephemeral environments can provide stronger system-level validation.

However, infrastructure-heavy tests should remain separate from fast unit tests so that ordinary development does not require starting the entire production stack.

---

## AWS Integration Testing

AWS-dependent systems may require testing against:

- S3;
- SQS;
- SNS;
- RDS;
- ElastiCache;
- Secrets Manager.

Avoid calling real production resources from automated tests.

Use:

- isolated AWS accounts;
- dedicated test resources;
- local emulators where their behavior is sufficiently compatible;
- controlled integration environments.

For AWS semantics that matter critically, validate against the real service in a safe environment.

---

## Common Mistakes

### Testing Implementation Instead of Behavior

Tests that assert every private method call become brittle.

Test externally meaningful behavior.

### Overusing `setUp`

A huge `setUp()` method can hide what each test actually needs.

Keep shared setup minimal.

### Shared Mutable State

Class/module-level mutable state can leak between tests.

Prefer fresh per-test state unless sharing is deliberate and safe.

### Mocking the Wrong Namespace

Patching where an object was defined instead of where it is used often leaves the real dependency active.

Patch the lookup location.

### Using `Mock` for Async Functions

An async function needs an awaitable test double.

Use `AsyncMock`.

### Mocking Database Semantics

Mocks cannot verify real PostgreSQL behavior.

Use integration tests for database-specific correctness.

### Catching Exceptions Manually

Prefer:

```python
with self.assertRaises(ValueError):
    ...
```

over manually catching and asserting exceptions unless special handling is needed.

### Excessive Interaction Assertions

A test that asserts every call sequence is tightly coupled to implementation.

Verify interactions that matter to the contract.

### Ignoring Cleanup

Open connections, files, threads, and tasks can leak across tests.

Use `addCleanup`, context managers, and explicit lifecycle management.

### Relying on Test Order

Tests should establish their own state.

Order-dependent tests are difficult to parallelize and diagnose.

---

## Production Pitfalls

### Slow Integration Suite

If every test starts a complete application and database, developers may avoid running tests locally.

Separate fast and infrastructure-heavy tests.

### External API Dependency

Live third-party APIs create flaky and slow tests.

Use controlled integration or contract testing.

### False Confidence from Mocks

A mock can confirm that your code called the mock correctly while the real integration remains broken.

Maintain integration coverage for important boundaries.

### Inadequate Failure Testing

Happy-path tests alone do not validate production resilience.

Test:

- timeouts;
- retries;
- dependency failures;
- transaction rollback;
- duplicate messages;
- authorization failures.

### Test Environment Contamination

Shared databases and caches can cause hidden dependencies.

Isolate test resources.

---

## Best Practices

- Prefer behavior-focused tests.
- Keep unit tests deterministic and fast.
- Use integration tests for real infrastructure semantics.
- Keep fixtures small and explicit.
- Use `addCleanup()` for reliable resource cleanup.
- Use `spec` or `autospec` for mocks where appropriate.
- Patch dependencies where they are looked up.
- Use `AsyncMock` for asynchronous interfaces.
- Keep test data synthetic.
- Test failure paths as deliberately as success paths.
- Treat flaky tests as defects.
- Keep CI environments isolated from production.
- Use coverage as a diagnostic signal rather than a target by itself.
- Keep test boundaries aligned with application architecture.

---

## Practical Test Design Checklist

### Unit Tests

- [ ] Business rules are tested.
- [ ] Inputs and expected outputs are explicit.
- [ ] Exceptions are tested.
- [ ] Boundary values are covered.
- [ ] Dependencies are controlled appropriately.

### Integration Tests

- [ ] PostgreSQL behavior is tested against PostgreSQL.
- [ ] Redis behavior is tested where semantics matter.
- [ ] Kafka/message behavior is integration-tested.
- [ ] Transactions and constraints are verified.
- [ ] Test resources are isolated.

### API Tests

- [ ] Authentication is tested.
- [ ] Authorization is tested.
- [ ] Validation is tested.
- [ ] Status codes are verified.
- [ ] Response contracts are verified.
- [ ] Error responses are verified.

### Reliability

- [ ] Timeouts are tested.
- [ ] Retry behavior is tested.
- [ ] Idempotency is tested.
- [ ] Duplicate messages are tested.
- [ ] Resource cleanup is tested.
- [ ] Graceful shutdown is tested where relevant.

### CI/CD

- [ ] Tests run automatically.
- [ ] Failures produce non-zero exit status.
- [ ] Production resources cannot be targeted accidentally.
- [ ] Dependencies are reproducible.
- [ ] Test execution time is monitored.

---

## Interview Traps

### Is `unittest` the Same as Unit Testing?

No.

`unittest` is a testing framework.

Unit testing is a testing strategy.

You can write integration tests using `unittest`.

### Is `TestCase` Required for Every Test?

For native `unittest` discovery, tests are conventionally organized around `TestCase` subclasses and test methods, although the framework also provides lower-level suite and loader APIs.

### Does `unittest` Mock Everything Automatically?

No.

Mocking is provided separately through `unittest.mock`.

### Should Every Dependency Be Mocked?

No.

Mock dependencies when isolation is useful. Use real integrations when the integration behavior matters.

### Why Does a Patch Not Work?

Usually because the wrong namespace was patched.

Patch where the code under test looks up the dependency.

### Can `Mock` Replace an Async Function?

Not correctly when the function must be awaited.

Use `AsyncMock`.

### Does High Coverage Mean High Quality?

No.

Coverage measures execution, not whether assertions verify meaningful behavior.

### Is `pytest` a Replacement for Understanding `unittest`?

No.

`pytest` is a separate testing framework, but `unittest` remains part of Python's standard library and its concepts are fundamental to Python testing.

## Key Takeaways

- **`unittest` provides a complete standard-library testing foundation:** `TestCase`, assertions, fixtures, discovery, suites, runners, and `unittest.mock`.
- **Test behavior at the appropriate boundary:** use isolated tests for business logic and real integration tests when PostgreSQL, Redis, Kafka, HTTP, or framework semantics matter.
- **Use mocks deliberately:** patch where dependencies are looked up, prefer `spec`/`autospec` where useful, and use `AsyncMock` for asynchronous interfaces.
- **Reliable tests require isolation and deterministic cleanup:** avoid shared mutable state, uncontrolled time or randomness, external services, test-order dependencies, and leaked resources.
- **`unittest` is a foundation, not a testing strategy:** framework choice matters less than meaningful assertions, appropriate test boundaries, failure-path coverage, and confidence in production behavior.