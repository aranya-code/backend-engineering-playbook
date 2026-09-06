# 03- pytest

## Overview

`pytest` is a third-party Python testing framework designed around simple test functions, powerful fixtures, parametrization, extensibility, and readable failure reporting.

For modern Python backend systems, `pytest` is often the default testing framework because it scales from small unit tests to large integration and API test suites without requiring test classes for ordinary cases.

Its core model is:

```text
Test Function
     ↓
Fixtures
     ↓
Application / Component
     ↓
Assertions
     ↓
pytest Runner
     ↓
Test Result
```

`pytest` can also execute existing `unittest.TestCase` tests, making it useful in projects that gradually evolve from standard-library testing to a richer test ecosystem.

The important engineering principle remains the same:

> Use `pytest` to make meaningful behavioral verification easy; do not let the framework determine the architecture of the tests.

---

## Why pytest Exists

Python's built-in `unittest` provides a solid foundation, but large application test suites often benefit from:

- reusable dependency fixtures;
- concise test functions;
- native parametrization;
- rich failure output;
- plugin support;
- flexible test selection;
- straightforward integration with async applications;
- extensive ecosystem support.

A typical `pytest` test is deliberately small:

```python
def test_calculate_total() -> None:
    result = calculate_total(price=100, quantity=3)

    assert result == 300
```

There is no required `TestCase` subclass and no need to call an assertion method.

---

## Installation

Install `pytest` as a development dependency:

```bash
python -m pip install pytest
```

For a project using `pyproject.toml`, keep testing dependencies separate from runtime dependencies.

For example:

```toml
[dependency-groups]
test = [
    "pytest",
]
```

The exact dependency-group syntax depends on the package manager used by the project.

---

## Basic Project Structure

A common structure is:

```text
project/
├── pyproject.toml
├── src/
│   └── app/
│       ├── orders.py
│       └── users.py
└── tests/
    ├── unit/
    │   ├── test_orders.py
    │   └── test_users.py
    ├── integration/
    │   └── test_order_repository.py
    └── api/
        └── test_orders.py
```

Another valid approach is feature-oriented organization:

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

Choose the structure that makes important behavior easy to locate.

---

## Running pytest

Run the entire suite:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run a specific file:

```bash
pytest tests/unit/test_orders.py
```

Run a specific test:

```bash
pytest tests/unit/test_orders.py::test_create_order
```

Run tests matching an expression:

```bash
pytest -k "order and not slow"
```

Stop after the first failure:

```bash
pytest -x
```

Run only the last failed tests:

```bash
pytest --lf
```

Run tests from a directory:

```bash
pytest tests/unit
```

---

## Test Discovery

By default, `pytest` discovers conventional test files such as:

```text
test_*.py
*_test.py
```

and test functions/methods beginning with:

```text
test_
```

For example:

```python
def test_create_order() -> None:
    ...


def test_cancel_order() -> None:
    ...
```

Discovery can be customized through configuration.

---

## Basic Assertions

`pytest` uses ordinary Python `assert` statements.

```python
def test_order_total() -> None:
    total = calculate_total(1000, 2)

    assert total == 2000
```

This produces detailed failure output when the assertion fails.

For example, instead of:

```text
Assertion failed
```

pytest can show the relevant expression and values.

This is one of its major usability advantages.

---

## Assertion Introspection

Consider:

```python
assert response.status_code == 201
```

If it fails, pytest can report the actual and expected values without requiring specialized assertion methods.

This allows tests to remain close to normal Python expressions:

```python
assert order.status == OrderStatus.CREATED
assert order.total == 2500
assert "order_id" in response.json()
```

Use explicit assertions that communicate the contract.

---

## Exception Testing

Use `pytest.raises()`.

```python
import pytest


def test_invalid_amount_is_rejected() -> None:
    with pytest.raises(ValueError, match="amount"):
        calculate_total(price=-100, quantity=2)
```

You can inspect the exception when necessary:

```python
def test_missing_order() -> None:
    with pytest.raises(OrderNotFoundError) as exc_info:
        service.get_order("missing")

    assert exc_info.value.order_id == "missing"
```

Avoid asserting exact error strings unless the message is part of the public contract.

---

## Fixtures

Fixtures are one of the defining features of pytest.

```python
import pytest


@pytest.fixture
def customer() -> Customer:
    return Customer(
        id="customer-1",
        active=True,
    )
```

Tests request fixtures by parameter name:

```python
def test_active_customer(customer: Customer) -> None:
    assert customer.active is True
```

pytest resolves the fixture dependency automatically.

This is substantially more flexible than large `setUp()` methods.

---

## Fixture Dependency Graph

Fixtures can depend on other fixtures.

```python
@pytest.fixture
def repository() -> InMemoryOrderRepository:
    return InMemoryOrderRepository()


@pytest.fixture
def service(
    repository: InMemoryOrderRepository,
) -> OrderService:
    return OrderService(repository=repository)
```

The dependency graph becomes:

```text
repository
    ↓
service
    ↓
test
```

This makes resource construction explicit and composable.

---

## Fixture Scope

Fixtures can have different lifetimes.

| Scope | Lifetime | Typical use |
|---|---|---|
| `function` | Each test | Default test data |
| `class` | Test class | Shared class resource |
| `module` | Test module | Expensive module setup |
| `package` | Package | Package-level resource |
| `session` | Entire test run | Very expensive shared resource |

Example:

```python
@pytest.fixture(scope="session")
def database() -> Database:
    db = create_test_database()
    yield db
    db.close()
```

Broader scopes can improve performance but increase state-sharing risk.

Use the narrowest scope that satisfies the test architecture.

---

## Yield Fixtures

`yield` fixtures provide a natural setup/cleanup boundary.

```python
@pytest.fixture
def database() -> Iterator[Database]:
    db = create_database()

    yield db

    db.close()
```

Execution is:

```text
setup
  ↓
yield
  ↓
test executes
  ↓
cleanup
```

This is particularly useful for:

- database connections;
- temporary files;
- API clients;
- Redis clients;
- background workers.

---

## Fixture Cleanup

Use `yield` for resource lifecycle management.

```python
@pytest.fixture
def client() -> Iterator[ApiClient]:
    client = ApiClient()
    yield client
    client.close()
```

For multiple resources, structure fixture ownership carefully so cleanup remains deterministic.

Poor fixture design can make resource ownership difficult to understand.

---

## Autouse Fixtures

An `autouse` fixture executes automatically.

```python
@pytest.fixture(autouse=True)
def reset_environment() -> Iterator[None]:
    reset_state()
    yield
    restore_state()
```

Autouse fixtures can be useful for genuinely universal setup.

Avoid overusing them.

A test that depends on invisible setup is harder to understand and debug.

---

## Fixture Factories

A fixture can return a factory function.

```python
@pytest.fixture
def customer_factory() -> Callable[..., Customer]:
    def build(
        *,
        customer_id: str = "customer-1",
        active: bool = True,
    ) -> Customer:
        return Customer(
            id=customer_id,
            active=active,
        )

    return build
```

A test can then create focused scenarios:

```python
def test_inactive_customer(
    customer_factory: Callable[..., Customer],
) -> None:
    customer = customer_factory(active=False)

    assert customer.active is False
```

This is useful for domain-heavy test data.

---

## Parametrization

Parametrization allows one test definition to run against multiple cases.

```python
import pytest


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (0, False),
        (1, True),
        (100, True),
        (-1, False),
    ],
)
def test_amount_validation(
    amount: int,
    expected: bool,
) -> None:
    assert is_valid_amount(amount) is expected
```

This is usually cleaner than manually duplicating tests.

---

## Multiple Parameters

Parameters can represent realistic scenarios:

```python
@pytest.mark.parametrize(
    ("status", "can_cancel"),
    [
        (OrderStatus.PENDING, True),
        (OrderStatus.PAID, True),
        (OrderStatus.SHIPPED, False),
        (OrderStatus.CANCELLED, False),
    ],
)
def test_cancellation_rules(
    status: OrderStatus,
    can_cancel: bool,
) -> None:
    assert can_cancel_order(status) is can_cancel
```

Keep parameter tables readable.

If the table becomes large or difficult to understand, split the scenarios into focused tests.

---

## Parameter IDs

pytest can display meaningful IDs for cases.

```python
@pytest.mark.parametrize(
    "amount",
    [
        pytest.param(0, id="zero"),
        pytest.param(100, id="positive"),
        pytest.param(-1, id="negative"),
    ],
)
def test_amount(amount: int) -> None:
    ...
```

This improves CI output and targeted test selection.

---

## Markers

Markers classify tests.

Built-in examples include:

```python
@pytest.mark.skip(reason="requires unavailable dependency")
def test_external_provider() -> None:
    ...
```

and:

```python
@pytest.mark.xfail(reason="known upstream defect")
def test_known_provider_bug() -> None:
    ...
```

Custom markers can classify tests such as:

```text
unit
integration
slow
e2e
```

Register custom markers in project configuration to avoid unknown-marker warnings.

---

## Marker Configuration

Example:

```toml
[tool.pytest.ini_options]
markers = [
    "integration: tests requiring external infrastructure",
    "slow: tests that take significant time",
]
```

Then:

```python
@pytest.mark.integration
def test_repository_persists_order() -> None:
    ...
```

Run only integration tests:

```bash
pytest -m integration
```

Run everything except integration tests:

```bash
pytest -m "not integration"
```

---

## Test Selection Strategy

Markers allow CI to create separate test stages:

```text
Commit
  ↓
unit
  ↓
integration
  ↓
e2e
```

For example:

```bash
pytest -m "not integration and not e2e"
```

followed by:

```bash
pytest -m integration
```

This allows fast feedback without abandoning deeper tests.

---

## `conftest.py`

`conftest.py` provides shared pytest configuration and fixtures.

Example:

```text
tests/
├── conftest.py
├── unit/
│   └── test_orders.py
└── integration/
    ├── conftest.py
    └── test_repository.py
```

Fixtures defined in a parent `conftest.py` are available to tests beneath that directory.

This is useful for shared infrastructure.

Avoid turning `conftest.py` into a global dependency container containing unrelated fixtures.

---

## Fixture Layering

Fixtures can be scoped by directory.

```text
tests/
├── conftest.py
│   └── common fixtures
│
├── unit/
│   └── lightweight fixtures
│
└── integration/
    └── database fixtures
```

This keeps infrastructure-specific setup near the tests that need it.

---

## Dependency Injection Through Fixtures

pytest fixtures work particularly well with dependency injection.

```python
@pytest.fixture
def repository() -> OrderRepository:
    return InMemoryOrderRepository()


@pytest.fixture
def service(
    repository: OrderRepository,
) -> OrderService:
    return OrderService(repository=repository)
```

The test remains focused:

```python
def test_create_order(service: OrderService) -> None:
    order = service.create_order(
        customer_id="customer-1",
        amount=2500,
    )

    assert order.status == OrderStatus.CREATED
```

This aligns naturally with a layered backend architecture.

---

## Fixtures and Database Sessions

A database fixture might establish a transaction boundary:

```python
@pytest.fixture
def db_session() -> Iterator[Session]:
    session = create_test_session()

    try:
        yield session
    finally:
        session.rollback()
        session.close()
```

The exact isolation strategy depends on the database framework.

For PostgreSQL-heavy applications, test infrastructure should reproduce production-relevant transaction semantics rather than relying exclusively on mocks.

---

## Database Integration Testing

A real integration test can exercise:

```text
pytest
   ↓
Service
   ↓
Repository
   ↓
Connection Pool
   ↓
PostgreSQL
```

This catches problems such as:

- invalid SQL;
- incorrect ORM mappings;
- constraint failures;
- transaction bugs;
- incorrect joins;
- PostgreSQL-specific behavior.

A mock cannot provide equivalent confidence.

---

## FastAPI Testing

FastAPI applications can be tested at the HTTP boundary.

For example:

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

    assert body["status"] == "created"
    assert body["amount"] == 2500
```

The API test verifies transport-level behavior without needing to inspect private implementation details.

---

## Async FastAPI Testing

For asynchronous tests, use the project's async testing stack.

A common approach uses `pytest` with `pytest-asyncio`:

```python
import pytest


@pytest.mark.asyncio
async def test_fetch_order() -> None:
    order = await service.fetch_order("order-1")

    assert order.id == "order-1"
```

The exact async plugin and configuration should be standardized across the repository.

Test async-specific behavior such as:

- cancellation;
- timeouts;
- concurrent tasks;
- resource cleanup;
- exception propagation.

---

## Django Testing

pytest can test Django applications through the Django pytest ecosystem.

A typical test may look like:

```python
import pytest


@pytest.mark.django_db
def test_create_order() -> None:
    order = Order.objects.create(
        customer_id="customer-1",
        amount=2500,
    )

    assert order.amount == 2500
```

Database access should be explicitly marked/configured so that tests requiring Django's database are distinguishable from pure unit tests.

---

## HTTP Client Testing

External HTTP dependencies should normally be controlled.

For example:

```text
OrderService
     ↓
PaymentClient
     ↓
HTTP provider
```

Unit test:

```text
OrderService
     ↓
Fake PaymentClient
```

Integration/contract test:

```text
PaymentClient
     ↓
Controlled provider
```

Avoid making ordinary CI unit tests depend on live third-party APIs.

---

## Mocking with unittest.mock

pytest does not replace `unittest.mock`.

They work together naturally:

```python
from unittest.mock import Mock


def test_payment() -> None:
    payment_client = Mock()
    payment_client.charge.return_value = PaymentResult(
        transaction_id="txn-1",
    )

    service = PaymentService(payment_client)

    result = service.pay(
        order_id="order-1",
        amount=1000,
    )

    assert result.transaction_id == "txn-1"
    payment_client.charge.assert_called_once_with(
        "order-1",
        1000,
    )
```

Use mocks to control boundaries where isolation is valuable.

---

## pytest-mock

`pytest-mock` provides a pytest fixture commonly named `mocker` around `unittest.mock`.

Example:

```python
def test_send_email(mocker) -> None:
    send_email = mocker.patch(
        "app.orders.send_email",
    )

    create_order(...)

    send_email.assert_called_once()
```

It can simplify patch lifecycle management.

The underlying testing principle remains the same: patch where the dependency is looked up.

---

## Mocking Async Dependencies

Use `AsyncMock` for async functions.

```python
from unittest.mock import AsyncMock


def test_async_payment() -> None:
    client = AsyncMock()

    client.charge.return_value = PaymentResult(
        transaction_id="txn-1",
    )

    ...
```

The test should await the dependency through the production code and verify the resulting behavior.

---

## Fakes vs Mocks

A fake can be preferable when the service depends on a simple interface.

```python
class FakeOrderRepository:
    def __init__(self) -> None:
        self.orders: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self.orders[order.id] = order

    def get(self, order_id: str) -> Order | None:
        return self.orders.get(order_id)
```

Then:

```python
def test_create_order() -> None:
    repository = FakeOrderRepository()
    service = OrderService(repository)

    order = service.create_order(
        customer_id="customer-1",
        amount=2500,
    )

    assert repository.orders[order.id] == order
```

Fakes can be more maintainable than a large collection of interaction assertions.

---

## Testing Exceptions and Side Effects

A robust service test may verify both failure behavior and important side effects.

```python
def test_payment_failure_does_not_mark_order_paid(
    payment_client: PaymentClient,
) -> None:
    payment_client.charge.side_effect = PaymentProviderError()

    with pytest.raises(PaymentError):
        service.pay("order-1", amount=1000)

    order = repository.get("order-1")

    assert order.status == OrderStatus.PENDING
```

The important assertion is the resulting business state, not merely that a dependency raised an exception.

---

## Testing Retries

Retries should be tested as behavior.

```python
def test_transient_payment_error_is_retried(
    payment_client: Mock,
) -> None:
    payment_client.charge.side_effect = [
        PaymentProviderTimeout(),
        PaymentResult(transaction_id="txn-1"),
    ]

    result = service.pay(
        order_id="order-1",
        amount=1000,
    )

    assert result.transaction_id == "txn-1"
    assert payment_client.charge.call_count == 2
```

Also test permanent failures and retry exhaustion.

---

## Testing Idempotency

Critical operations should test duplicate requests.

```python
def test_duplicate_idempotency_key_returns_existing_payment() -> None:
    first = service.create_payment(
        order_id="order-1",
        idempotency_key="request-123",
    )

    second = service.create_payment(
        order_id="order-1",
        idempotency_key="request-123",
    )

    assert second.id == first.id
```

For real database-backed idempotency, integration tests should verify the database constraint and transaction behavior.

---

## Testing Authorization

Authorization should be tested explicitly.

```python
def test_user_cannot_access_another_tenant_order(
    client: TestClient,
) -> None:
    response = client.get(
        "/orders/order-from-tenant-b",
        headers=tenant_a_headers(),
    )

    assert response.status_code in {403, 404}
```

The exact expected status depends on the API's resource-existence disclosure policy.

Test critical tenant boundaries independently.

---

## Testing Validation

Use parametrization for systematic input validation.

```python
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"amount": -1},
        {"amount": 0},
        {"amount": "invalid"},
    ],
)
def test_invalid_order_payload(payload: dict) -> None:
    response = client.post("/orders", json=payload)

    assert response.status_code in {400, 422}
```

Prefer exact status and error assertions when they are part of the API contract.

---

## Testing State Transitions

Parametrization is effective for state-machine behavior.

```python
@pytest.mark.parametrize(
    ("current", "target", "allowed"),
    [
        ("pending", "paid", True),
        ("pending", "cancelled", True),
        ("paid", "refunded", True),
        ("paid", "cancelled", False),
    ],
)
def test_order_transition(
    current: str,
    target: str,
    allowed: bool,
) -> None:
    assert can_transition(current, target) is allowed
```

State transitions should also be tested against the persistence layer when concurrency or database constraints matter.

---

## Testing Time

Inject a clock when possible.

```python
class FixedClock:
    def __init__(self, current: datetime) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current
```

Fixture:

```python
@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(
        datetime(2026, 9, 6, 10, 0, tzinfo=timezone.utc),
    )
```

This avoids fragile tests based on the wall clock.

---

## Testing Temporary Files

Use pytest fixtures or Python's `tempfile`.

```python
def test_process_upload(tmp_path) -> None:
    path = tmp_path / "orders.json"

    path.write_text(
        '{"id": "order-1"}',
        encoding="utf-8",
    )

    result = process_upload(path)

    assert result.order_id == "order-1"
```

`tmp_path` provides an isolated temporary directory for the test.

---

## Testing Environment Variables

Use `monkeypatch` for temporary environment changes.

```python
def test_load_configuration(monkeypatch) -> None:
    monkeypatch.setenv(
        "APP_ENV",
        "test",
    )

    config = load_config()

    assert config.environment == "test"
```

pytest restores the modified state after the test.

---

## `monkeypatch`

`monkeypatch` can temporarily modify:

- attributes;
- environment variables;
- dictionaries;
- `sys.path`;
- current working directory.

Example:

```python
def test_feature_flag(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.features.NEW_CHECKOUT",
        True,
    )

    assert checkout_mode() == "new"
```

This is often simpler than manually restoring global state.

---

## Testing Warnings

Use `pytest.warns()`:

```python
def test_deprecated_api_warns() -> None:
    with pytest.warns(DeprecationWarning):
        legacy_function()
```

Warnings can be part of compatibility contracts for libraries and long-lived applications.

---

## Testing Logs

Use `caplog` when log behavior matters.

```python
def test_failed_payment_is_logged(caplog) -> None:
    with caplog.at_level("WARNING"):
        service.process_payment("order-1")

    assert "payment failed" in caplog.text
```

For structured logging, prefer stable fields or event names rather than exact rendered messages.

---

## Capturing Output

pytest provides `capsys` for stdout/stderr.

```python
def test_cli_output(capsys) -> None:
    run_command()

    captured = capsys.readouterr()

    assert "completed" in captured.out
```

For CLI applications, distinguish:

```text
stdout → command result/output
stderr → diagnostics/errors
exit code → machine-readable success/failure
```

---

## Testing CLI Applications

pytest works well with CLI tests.

Example:

```python
def test_export_command(capsys) -> None:
    exit_code = run_cli(
        ["export", "--format", "json"],
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"status": "completed"' in captured.out
```

For packaged CLIs, integration tests can execute the actual entry point rather than bypassing it.

---

## Async Fixtures

Async fixtures depend on the async pytest plugin used by the project.

A typical pattern is:

```python
import pytest


@pytest.fixture
async def async_client():
    client = create_async_client()

    yield client

    await client.close()
```

The project should standardize the async testing plugin and configuration rather than mixing multiple approaches without reason.

---

## Testing Background Jobs

Separate transport from application behavior.

```text
Celery task
    ↓
Application service
    ↓
Repository / external clients
```

Unit test the application service independently.

Integration-test the actual queue/worker interaction when required.

Test:

- successful execution;
- duplicate delivery;
- retries;
- timeout;
- permanent failure;
- idempotency;
- job state transitions.

---

## Testing Kafka Consumers

Kafka integration tests should verify behavior such as:

```text
consume
  ↓
process
  ↓
commit offset
```

and failure behavior:

```text
consume
  ↓
processing failure
  ↓
retry/recovery
```

Unit tests can mock the consumer interface, but important offset, partition, ordering, and delivery semantics require integration testing.

---

## Testing Redis

Redis-specific behavior should be tested against Redis where semantics matter.

Examples include:

- TTL;
- atomic operations;
- cache invalidation;
- distributed coordination;
- serialization;
- key expiration.

A Python dictionary is not an equivalent substitute for Redis behavior.

---

## Contract Testing

pytest can execute contract tests between services.

For example:

```text
Consumer
   ↓
Expected API contract
   ↓
Provider
```

Tests can verify:

- request schema;
- response schema;
- required fields;
- status codes;
- compatibility.

This is particularly important in independently deployed microservices.

---

## Property-Based Testing

pytest integrates naturally with Hypothesis.

Example conceptually:

```python
@given(st.integers(min_value=0, max_value=100))
def test_percentage_is_bounded(value: int) -> None:
    assert 0 <= normalize_percentage(value) <= 100
```

Property-based testing is useful when correctness should hold across many generated inputs.

Use it for invariants and input-space exploration rather than replacing all example-based tests.

---

## Integration with Static Analysis

A mature Python CI pipeline often combines:

```text
pytest
+
Ruff
+
Mypy/Pyright
+
Coverage
+
Security scanning
```

Each tool verifies a different property.

```text
pytest
→ runtime behavior

type checker
→ static type contracts

linter
→ code quality rules

coverage
→ executed code paths

security tools
→ known security risks
```

No single tool replaces the others.

---

## Coverage with pytest

A common command using `coverage.py` is:

```bash
coverage run -m pytest
coverage report
```

For an HTML report:

```bash
coverage html
```

Coverage can identify untested paths but does not establish correctness.

Prioritize high-risk behavior:

- authentication;
- authorization;
- financial operations;
- transactions;
- retries;
- idempotency;
- state transitions;
- security boundaries.

---

## Test Configuration

pytest configuration can live in `pyproject.toml`.

Example:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
markers = [
    "integration: tests requiring external infrastructure",
    "slow: tests that take significant time",
]
```

Centralized configuration makes local and CI execution more consistent.

Avoid hiding important test behavior in undocumented shell aliases or developer-specific configuration.

---

## Test Collection Control

Use `testpaths` to define where tests live:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

This prevents accidental collection of unrelated scripts.

For large repositories, explicit configuration becomes increasingly important.

---

## Import and Packaging Considerations

Tests should import the application the same way production code does.

With a `src` layout:

```text
src/
└── app/
```

the package should be installed into the test environment rather than relying on accidental current-directory import behavior.

This catches packaging and import mistakes earlier.

---

## Test Isolation and Databases

Database tests should not depend on execution order.

Avoid:

```text
test_create_customer
       ↓
test_update_customer assumes customer exists
```

Each test should establish the state it needs.

For PostgreSQL-backed applications, use an isolation strategy appropriate to the ORM and transaction model.

---

## Test Parallelism

pytest can be extended with parallel execution tooling such as `pytest-xdist`.

Conceptually:

```bash
pytest -n auto
```

Parallel tests require strong isolation.

Potential conflicts include:

- shared PostgreSQL state;
- Redis keys;
- filesystem paths;
- ports;
- environment variables;
- global process state.

Do not introduce parallel execution until the suite is safe for it.

---

## Performance and Test Suite Design

A test suite is part of the developer feedback loop.

Common performance problems include:

- recreating expensive databases per test;
- excessive application startup;
- unnecessary E2E tests;
- large fixtures;
- external network calls;
- serialized CI jobs;
- redundant integration tests.

The solution is not simply "make tests faster."

Instead:

```text
fast unit tests
        ↓
focused integration tests
        ↓
API/contract tests
        ↓
targeted E2E tests
```

Optimize the architecture of the test suite.

---

## Flaky Tests

A flaky test produces inconsistent results without a relevant code change.

Typical causes include:

- uncontrolled time;
- randomness;
- race conditions;
- shared state;
- external services;
- test ordering;
- asynchronous timing;
- filesystem assumptions.

Do not normalize flakes by rerunning tests indefinitely.

A flaky test reduces confidence in the entire CI pipeline.

---

## Retrying Tests

Automatic test retries can be useful for diagnosing environmental instability, but they can also hide genuine defects.

Avoid treating:

```text
first run fails
second run passes
```

as success without investigation.

If retries are enabled, monitor and track retry frequency separately from ordinary pass/fail results.

---

## Test Data Management

Prefer small, explicit test data.

Good:

```python
order = Order(
    id="order-1",
    amount=2500,
    status=OrderStatus.PENDING,
)
```

Avoid fixtures containing dozens of irrelevant records.

Large implicit datasets make failures difficult to understand and can significantly increase suite runtime.

---

## Test Boundaries

A useful backend testing architecture is:

```text
                    ┌──────────────────┐
                    │      E2E         │
                    │ Full workflows   │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ API / Contract   │
                    │ External boundary│
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ Integration      │
                    │ Real dependencies│
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ Unit / Component │
                    │ Fast + isolated  │
                    └──────────────────┘
```

pytest can orchestrate all of these layers while each test type retains a distinct purpose.

---

## pytest and unittest

pytest can run many existing `unittest` tests.

This enables incremental adoption:

```text
Existing unittest suite
        ↓
Run under pytest
        ↓
Add pytest fixtures
        ↓
Add parametrization
        ↓
Gradually simplify tests
```

A migration does not require rewriting the entire suite immediately.

---

## unittest vs pytest

| Concern | unittest | pytest |
|---|---|---|
| Standard library | Yes | No |
| Test functions | Limited/native model differs | Yes |
| Fixtures | Lifecycle methods | Rich fixture system |
| Parametrization | `subTest` | Native |
| Mocking | `unittest.mock` | Compatible |
| Plugins | Smaller ecosystem | Extensive |
| Failure output | Good | Excellent introspection |
| Async ecosystem | Standard-library support | Strong plugin ecosystem |
| Existing class-based suites | Native | Supported |
| Application test ergonomics | Good | Usually stronger |

Framework choice should follow project requirements and team conventions.

---

## Production CI/CD Workflow

A backend repository may use:

```text
Pull Request
     ↓
Formatting / Lint
     ↓
Type Checking
     ↓
Fast pytest suite
     ↓
Integration tests
     ↓
Contract tests
     ↓
Security checks
     ↓
Build artifact
     ↓
Staging
     ↓
E2E / smoke tests
     ↓
Production
```

Tests should fail the pipeline when critical verification fails.

Do not make important tests optional simply because they increase CI duration.

Instead, optimize execution and parallelize safe workloads.

---

## Docker-Based Integration Tests

For infrastructure-heavy tests:

```text
pytest
  │
  ├── Application
  ├── PostgreSQL
  ├── Redis
  └── Kafka
```

Use disposable test environments where practical.

The test environment should approximate production semantics without requiring production infrastructure.

---

## Kubernetes Testing

Kubernetes-specific testing may validate:

- readiness behavior;
- startup behavior;
- graceful shutdown;
- service discovery;
- configuration;
- resource limits;
- worker behavior.

These belong primarily in integration, system, or deployment validation tests rather than ordinary unit tests.

---

## AWS Integration Testing

AWS-dependent tests should use isolated resources or controlled environments.

Potential services include:

- RDS;
- S3;
- SQS;
- SNS;
- ElastiCache;
- Secrets Manager.

Never allow ordinary automated tests to accidentally use production credentials or production data.

---

## Security Considerations

Test infrastructure must be treated as production-adjacent.

Protect against:

- production credential usage;
- accidental production database access;
- sensitive fixture data;
- secrets in CI logs;
- real customer information;
- destructive integration tests.

Use synthetic data and explicit test configuration.

Security tests should cover:

- authentication;
- authorization;
- tenant isolation;
- input validation;
- SSRF defenses;
- SQL injection resistance;
- webhook signatures;
- sensitive error disclosure.

---

## Reliability Considerations

A reliable pytest suite should be:

- deterministic;
- isolated;
- repeatable;
- observable;
- appropriately fast.

Track:

- test duration;
- flaky test rate;
- failure frequency;
- integration environment failures;
- retry frequency;
- CI queue time.

Test infrastructure itself can become an operational bottleneck in large organizations.

---

## Observability for Tests

CI should expose enough information to diagnose failures.

Useful artifacts include:

```text
test output
failure traceback
coverage report
logs
integration-service logs
screenshots for UI/E2E tests
performance metrics where relevant
```

For distributed integration tests, correlate application logs and traces with the test or CI job identifier where practical.

---

## Common Mistakes

### Giant `conftest.py`

Putting every fixture into one global file creates hidden dependencies.

Keep fixtures near the tests that need them.

### Overusing Autouse Fixtures

Implicit setup makes individual tests harder to understand.

Prefer explicit fixture parameters.

### Fixture Overengineering

A deeply nested fixture graph can become harder to understand than ordinary setup.

Keep dependency graphs intentional.

### Mocking Everything

Mocks can hide real integration defects.

Use real dependencies where their behavior matters.

### Large Parameter Tables

Parametrization is useful until cases become difficult to read.

Split complex scenarios into focused tests.

### Excessive Markers

Too many categories make test selection confusing.

Keep a small, meaningful marker taxonomy.

### Ignoring Flaky Tests

A flaky suite trains engineers to ignore CI.

Treat nondeterminism as a defect.

---

## Production Pitfalls

### Shared Database State

Tests pass individually but fail as a suite because previous tests modify persistent state.

Use reliable isolation.

### Live Third-Party APIs

Tests become dependent on provider availability, latency, credentials, and rate limits.

Use mocks, fakes, sandboxes, or contract tests.

### Overly Broad Fixtures

A single fixture may silently create users, orders, Redis keys, and database state for every test.

This increases runtime and hidden coupling.

### CI-Only Failures

Differences in Python versions, dependencies, environment variables, filesystem behavior, or concurrency can expose bugs.

Keep local and CI environments reproducible.

### Test Retries Hiding Defects

Retries can mask races and timing bugs.

Track retry occurrences and investigate the underlying failure.

---

## Best Practices

- Prefer plain test functions for ordinary pytest tests.
- Use fixtures for explicit dependency and resource management.
- Keep fixture scopes as narrow as practical.
- Use parametrization for systematic variations.
- Use markers to separate meaningful test categories.
- Keep shared fixtures small and discoverable.
- Use real dependencies for integration semantics.
- Use mocks and fakes at appropriate boundaries.
- Use `monkeypatch` for temporary process-state changes.
- Use `tmp_path` for filesystem isolation.
- Use `pytest.raises()` and `pytest.warns()` for explicit failure contracts.
- Keep API tests focused on public behavior.
- Test transactions, idempotency, retries, and authorization explicitly.
- Treat flaky tests as defects.
- Keep production resources inaccessible from test environments.
- Use coverage as a diagnostic signal rather than the primary quality metric.
- Standardize pytest configuration in `pyproject.toml`.
- Keep fast tests fast enough for frequent local execution.

---

## Practical pytest Checklist

### Test Design

- [ ] Tests verify observable behavior.
- [ ] Test names describe the scenario.
- [ ] Assertions are specific.
- [ ] Boundary conditions are covered.
- [ ] Failure paths are tested.

### Fixtures

- [ ] Fixtures have intentional scope.
- [ ] Resource cleanup is deterministic.
- [ ] Autouse fixtures are limited.
- [ ] Fixture dependencies are understandable.
- [ ] Test data is minimal.

### Integration

- [ ] PostgreSQL behavior is tested against PostgreSQL.
- [ ] Redis behavior is tested where required.
- [ ] Kafka behavior is tested where required.
- [ ] External APIs are controlled.
- [ ] Database state is isolated.

### Backend Reliability

- [ ] Transactions are tested.
- [ ] Retries are tested.
- [ ] Idempotency is tested.
- [ ] Duplicate messages are tested.
- [ ] Timeouts are tested.
- [ ] Graceful shutdown is tested where relevant.

### Security

- [ ] Tests cannot target production accidentally.
- [ ] Secrets are not committed.
- [ ] Authentication is tested.
- [ ] Authorization is tested.
- [ ] Tenant isolation is tested.
- [ ] Sensitive errors are not exposed.

### CI/CD

- [ ] pytest runs automatically.
- [ ] Fast tests run early.
- [ ] Integration tests run in controlled infrastructure.
- [ ] Important failures block deployment.
- [ ] Flaky tests are tracked.
- [ ] Test duration is monitored.

---

## Interview Traps

### Why Is pytest Often Preferred Over unittest?

Because it provides concise test syntax, powerful fixtures, native parametrization, strong failure introspection, and an extensive plugin ecosystem.

### Is pytest Only for Unit Tests?

No.

pytest can run:

- unit tests;
- integration tests;
- API tests;
- contract tests;
- E2E tests;
- performance-oriented test harnesses.

The framework does not determine the test level.

### Does pytest Replace unittest.mock?

No.

pytest works naturally with `unittest.mock`.

### What Is pytest's Most Important Feature?

For backend engineering, fixtures are arguably its most important architectural feature because they allow reusable, composable dependency and resource setup.

### Why Can Fixtures Become Dangerous?

Because broad-scoped or deeply nested fixtures can hide state, increase coupling, and make tests difficult to understand.

### Should Everything Be a Fixture?

No.

Use fixtures for reusable dependencies and lifecycle-managed resources. Simple local values often belong directly in the test.

### Does Parametrization Replace Separate Tests?

Not always.

Use parametrization when cases exercise the same behavior. Separate tests are preferable when scenarios have materially different intent.

### Does High Coverage Mean a Good pytest Suite?

No.

Coverage measures execution, not correctness, isolation, meaningful assertions, integration confidence, or security.

### Can pytest Test Async Code?

Yes.

Python's async support and pytest plugins allow asynchronous tests, but the project should standardize the chosen async testing approach.

### Should Integration Tests Be Mocked?

No.

If the purpose of the test is to verify integration semantics, use the real dependency in a controlled environment.

## Key Takeaways

- **pytest is a testing framework, not a testing strategy:** use it across unit, integration, API, contract, and E2E boundaries according to what each test needs to verify.
- **Fixtures are the core pytest capability:** use them to compose dependencies and manage resources while keeping scope narrow and setup explicit.
- **Parametrization and markers improve test scalability:** use parametrization for systematic cases and a small marker taxonomy for controlled CI execution.
- **Real infrastructure still matters:** mocks and fakes provide isolation, but PostgreSQL, Redis, Kafka, HTTP, transaction, and concurrency semantics require appropriate integration testing.
- **A strong pytest suite is deterministic and operationally trustworthy:** isolate state, control external dependencies, eliminate flaky tests, protect production resources, and optimize the test pipeline for fast feedback.