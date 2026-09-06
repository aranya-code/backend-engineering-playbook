# 05- Assertions

## Overview

Assertions are executable statements that verify assumptions about application behavior.

In Python testing, assertions answer questions such as:

- Did the function return the expected value?
- Did the API return the correct status code?
- Did a database operation produce the expected state?
- Was the correct exception raised?
- Did an external dependency receive the expected request?

A good assertion expresses a meaningful contract:

```python
assert order.status == OrderStatus.PAID
```

rather than an implementation detail:

```python
assert service._internal_state["last_transition"] == "paid"
```

In `pytest`, ordinary Python `assert` statements are the primary assertion mechanism. pytest enhances failed assertions with expression introspection, making failures substantially easier to diagnose.

---

## Why Assertions Matter

A test without meaningful assertions may execute code without actually verifying correctness.

For example:

```python
def test_create_order(service: OrderService) -> None:
    service.create_order(
        customer_id="customer-1",
        amount=2500,
    )
```

The test could pass even if the implementation returns the wrong object or produces the wrong state.

A useful test verifies observable behavior:

```python
def test_create_order(service: OrderService) -> None:
    order = service.create_order(
        customer_id="customer-1",
        amount=2500,
    )

    assert order.status == OrderStatus.CREATED
    assert order.amount == 2500
```

The assertions define what the test considers correct.

---

## Python `assert` Statement

Python's `assert` statement has the form:

```python
assert condition
```

or:

```python
assert condition, "message"
```

Example:

```python
assert amount > 0
```

With a message:

```python
assert amount > 0, "amount must be positive"
```

Conceptually, Python evaluates:

```python
if not condition:
    raise AssertionError(...)
```

The important production distinction is that Python assertions can be disabled with optimization.

Running Python with:

```bash
python -O application.py
```

can remove assertion checks.

Therefore, assertions used for application invariants must **not** be relied upon for security, validation, authorization, or other production-critical behavior.

---

## Assertions in pytest

pytest builds on ordinary Python assertions:

```python
def test_total() -> None:
    assert calculate_total(100, 3) == 300
```

If the assertion fails, pytest analyzes the expression and reports useful information.

For example:

```text
assert 250 == 300
```

rather than providing only a generic assertion failure.

This is one of pytest's major advantages over assertion APIs that require specialized methods for every comparison.

---

## Python Assertions vs pytest Assertions

| Mechanism | Typical purpose | Can be disabled with `-O`? |
|---|---|---:|
| Python `assert` | Internal application invariants | Yes |
| pytest `assert` | Test verification | Tests are normally run by pytest | 
| `pytest.raises()` | Exception verification | No |
| `pytest.warns()` | Warning verification | No |
| `unittest.TestCase.assertEqual()` | unittest assertions | No |

Inside tests, Python `assert` is normally the preferred pytest style.

Inside production application code, use explicit validation or exceptions when behavior must always execute.

---

## Equality Assertions

Use `==` when verifying value equality.

```python
def test_order_amount() -> None:
    order = create_order(amount=2500)

    assert order.amount == 2500
```

For collections:

```python
assert response.json() == {
    "status": "created",
    "amount": 2500,
}
```

Equality is appropriate when the contract concerns values.

---

## Identity Assertions

Use `is` when object identity matters.

```python
def test_cached_object_is_reused(cache: Cache) -> None:
    first = cache.get("order-1")
    second = cache.get("order-1")

    assert first is second
```

Do not use `is` for ordinary value comparison.

Incorrect:

```python
assert response.status_code is 200
```

Correct:

```python
assert response.status_code == 200
```

A common exception is singleton checks such as:

```python
assert result is None
```

---

## Boolean Assertions

Boolean assertions should generally assert the value directly.

Prefer:

```python
assert customer.is_active
```

over:

```python
assert customer.is_active is True
```

The first expresses the semantic requirement more directly.

However, when explicitly verifying that a value is the boolean singleton `True`, `is True` can be appropriate.

---

## `None` Assertions

Use identity for `None`:

```python
assert repository.get("missing") is None
```

Avoid:

```python
assert repository.get("missing") == None
```

`None` is a singleton, and `is None` communicates the intended semantic check clearly.

---

## Collection Assertions

pytest supports normal Python collection comparisons.

```python
assert active_users == [
    "alice",
    "bob",
]
```

For membership:

```python
assert "order-123" in order_ids
```

For absence:

```python
assert "order-999" not in order_ids
```

For length:

```python
assert len(orders) == 3
```

Choose assertions that directly express the contract.

---

## Dictionary Assertions

When the complete dictionary is the API contract:

```python
assert response.json() == {
    "id": "order-123",
    "status": "created",
}
```

When only selected fields matter:

```python
body = response.json()

assert body["status"] == "created"
assert body["id"]
```

Do not assert every incidental field if the test only depends on a subset of the response contract.

---

## Partial Assertions

For APIs, partial assertions are often more resilient.

```python
body = response.json()

assert body["status"] == "created"
assert body["amount"] == 2500
```

This can be preferable to:

```python
assert body == {
    "id": "order-123",
    "status": "created",
    "amount": 2500,
    "created_at": "...",
    "metadata": {},
}
```

The full comparison is appropriate when the complete response schema is intentionally part of the test contract.

---

## Nested Assertions

Keep related assertions readable:

```python
body = response.json()

assert body["order"]["status"] == "created"
assert body["order"]["amount"] == 2500
assert body["customer"]["id"] == "customer-1"
```

Avoid deeply nested one-line expressions that produce difficult failures.

Extract intermediate values when doing so improves diagnostics:

```python
order = response.json()["order"]

assert order["status"] == "created"
assert order["amount"] == 2500
```

---

## Multiple Assertions in One Test

Multiple assertions are acceptable when they verify one coherent behavior.

```python
def test_create_order(client: TestClient) -> None:
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

These assertions collectively verify the `create order` contract.

Avoid combining unrelated behaviors into one test merely because they happen to share setup.

---

## Assertion Granularity

The right granularity depends on the behavior being tested.

Too weak:

```python
assert response.status_code < 500
```

Too broad:

```python
assert response.json() == entire_database_snapshot
```

Better:

```python
assert response.status_code == 201
assert response.json()["status"] == "created"
```

Assertions should be precise enough to detect meaningful regressions without coupling tests to irrelevant implementation details.

---

## Exception Assertions

Use `pytest.raises()` instead of manually catching exceptions.

```python
import pytest


def test_invalid_amount() -> None:
    with pytest.raises(ValueError):
        calculate_total(price=-100, quantity=2)
```

This verifies that the operation raises the expected exception.

---

## Exception Type

Prefer asserting the most specific meaningful exception type.

```python
with pytest.raises(PaymentProviderError):
    payment_service.charge(order)
```

Avoid:

```python
with pytest.raises(Exception):
    payment_service.charge(order)
```

The latter can allow unrelated defects to pass the test.

---

## Exception Message

Use `match` when the message itself is part of the useful contract.

```python
with pytest.raises(
    ValueError,
    match="amount must be positive",
):
    calculate_total(price=-100, quantity=2)
```

Avoid asserting complete error strings unnecessarily because wording changes can break otherwise valid tests.

Prefer stable fragments or structured exception attributes when available.

---

## Inspecting Exceptions

Use the context manager result when the exception contains structured information.

```python
with pytest.raises(OrderNotFoundError) as exc_info:
    service.get_order("order-999")

assert exc_info.value.order_id == "order-999"
```

This is preferable to parsing an error string.

---

## API Error Assertions

For REST APIs, test the externally visible contract:

```python
def test_missing_order(client: TestClient) -> None:
    response = client.get("/orders/order-999")

    assert response.status_code == 404

    body = response.json()

    assert body["code"] == "ORDER_NOT_FOUND"
```

If the API guarantees a structured error schema, assert the stable fields rather than incidental formatting.

---

## HTTP Assertions

A useful API test may verify:

```python
assert response.status_code == 201
assert response.headers["content-type"].startswith(
    "application/json"
)
```

and:

```python
body = response.json()

assert body["status"] == "created"
```

Do not over-assert headers or framework-generated values unless they are part of the API contract.

---

## Database Assertions

Database tests should verify persisted state when persistence is part of the behavior.

```python
def test_create_order(db_session: Session) -> None:
    service.create_order(
        customer_id="customer-1",
        amount=2500,
    )

    order = (
        db_session.query(Order)
        .filter_by(customer_id="customer-1")
        .one()
    )

    assert order.amount == 2500
    assert order.status == OrderStatus.CREATED
```

A mocked repository cannot verify actual database behavior.

---

## Transaction Assertions

Transactions require assertions about durable state and failure behavior.

```python
def test_failed_payment_does_not_commit_order(
    db_session: Session,
) -> None:
    with pytest.raises(PaymentError):
        service.process_payment(
            order_id="order-1",
            amount=2500,
        )

    order = get_order(db_session, "order-1")

    assert order.status == OrderStatus.PENDING
```

The important assertion is the externally observable transaction outcome.

---

## Side-Effect Assertions

Sometimes the important behavior is a side effect:

```python
def test_order_event_is_published(
    publisher: Mock,
) -> None:
    service.create_order(
        customer_id="customer-1",
        amount=2500,
    )

    publisher.publish.assert_called_once()
```

Interaction assertions should be used when the interaction itself is part of the contract.

Otherwise, prefer asserting resulting state.

---

## Mock Call Assertions

`unittest.mock` provides specialized assertions:

```python
publisher.publish.assert_called_once_with(
    "order.created",
    {"order_id": "order-1"},
)
```

Common methods include:

| Assertion | Purpose |
|---|---|
| `assert_called()` | Called at least once |
| `assert_called_once()` | Called exactly once |
| `assert_called_with()` | Most recent call matches |
| `assert_called_once_with()` | Exactly one call with arguments |
| `assert_any_call()` | At least one matching call |
| `assert_not_called()` | Never called |

Use interaction assertions selectively.

---

## State Assertions vs Interaction Assertions

Consider an order service:

```text
OrderService
    ↓
Repository
    ↓
Database
```

A fragile unit test may assert every repository method:

```python
repository.save.assert_called_once_with(order)
repository.commit.assert_called_once()
```

A stronger behavioral test may assert:

```python
assert order.status == OrderStatus.CREATED
```

and use integration testing to verify actual persistence.

The right assertion depends on the test boundary.

---

## Assertion Messages

pytest rarely requires explicit assertion messages because it provides assertion introspection.

Prefer:

```python
assert response.status_code == 201
```

over:

```python
assert response.status_code == 201, "The response should be successful"
```

The second message adds little information.

Use custom messages when they provide meaningful context that pytest cannot infer.

---

## Comparing Floating-Point Values

Avoid exact equality for floating-point calculations when numerical precision matters.

Instead:

```python
import pytest


def test_exchange_rate() -> None:
    result = calculate_rate(100, 83.27)

    assert result == pytest.approx(8327)
```

`pytest.approx()` supports approximate numeric comparisons.

For financial systems, prefer integer minor units or `Decimal` where appropriate rather than relying on binary floating-point arithmetic.

---

## Decimal Assertions

For monetary values:

```python
from decimal import Decimal


def test_order_total() -> None:
    total = calculate_total(
        Decimal("19.99"),
        Decimal("2"),
    )

    assert total == Decimal("39.98")
```

The assertion verifies exact decimal semantics.

---

## Datetime Assertions

Avoid fragile assertions based on exact wall-clock timestamps.

Instead of:

```python
assert order.created_at == datetime.now(timezone.utc)
```

prefer a controlled clock or an appropriate tolerance:

```python
assert order.created_at <= datetime.now(timezone.utc)
```

Better still, inject a clock:

```python
assert order.created_at == expected_time
```

Controlled time produces deterministic tests.

---

## Ordering Assertions

When ordering is part of the contract:

```python
assert orders == [
    first_order,
    second_order,
    third_order,
]
```

When ordering is irrelevant:

```python
assert set(actual_ids) == {
    "order-1",
    "order-2",
    "order-3",
}
```

Do not accidentally make tests depend on ordering that the application does not guarantee.

---

## Approximate Collections

For larger structures, compare only the semantics the application promises.

For example:

```python
assert set(actual_customer_ids) == expected_customer_ids
```

rather than requiring an arbitrary database result ordering.

For API collections, explicitly test ordering if the endpoint promises a sort order.

---

## Dataclass and Object Assertions

Dataclasses support value-oriented equality by default in common configurations.

```python
expected = Order(
    id="order-1",
    amount=2500,
    status=OrderStatus.CREATED,
)

assert actual == expected
```

This is useful when the complete object value is part of the contract.

For complex domain objects, targeted assertions may provide better failure diagnostics.

---

## Custom Equality

Objects can define `__eq__()`.

Therefore:

```python
assert actual == expected
```

may invoke application-defined equality semantics.

Understand what equality means for domain objects before using it as the primary assertion.

If identity matters:

```python
assert actual is expected
```

---

## Collection Comparison Diagnostics

pytest provides useful failure output for collection comparisons.

For example:

```python
assert actual_users == expected_users
```

can expose the differing elements.

This makes ordinary Python assertions practical even for relatively complex data structures.

---

## Snapshot-Like Assertions

Large response snapshots can be tempting:

```python
assert response.json() == huge_expected_payload
```

They can detect broad regressions but may become difficult to review.

Prefer explicit assertions for important business semantics.

Snapshot-style testing is most useful when:

- output is structurally large;
- output changes infrequently;
- reviewing the full diff is practical;
- the snapshot itself represents a meaningful contract.

---

## Assertion Helpers

Repeated complex assertions can be extracted into helpers.

```python
def assert_order_created(
    order: Order,
    *,
    amount: int,
) -> None:
    assert order.status == OrderStatus.CREATED
    assert order.amount == amount
```

Then:

```python
def test_create_order() -> None:
    order = service.create_order(
        customer_id="customer-1",
        amount=2500,
    )

    assert_order_created(order, amount=2500)
```

Keep helpers small and domain-oriented.

Overly generic assertion helpers can hide what the test actually verifies.

---

## Custom Assertion Functions

A domain-specific assertion can improve readability:

```python
def assert_successful_order(order: Order) -> None:
    assert order.status == OrderStatus.CREATED
    assert order.id
    assert order.amount > 0
```

This is useful when the same domain contract appears across many tests.

The helper should still produce useful failure information.

---

## Assertions and Fixtures

Fixtures establish state; assertions verify behavior.

```python
@pytest.fixture
def pending_order() -> Order:
    return Order(
        id="order-1",
        status=OrderStatus.PENDING,
        amount=2500,
    )


def test_payment_marks_order_paid(
    pending_order: Order,
) -> None:
    service.pay(pending_order)

    assert pending_order.status == OrderStatus.PAID
```

Keep these responsibilities conceptually separate.

---

## Assertions and Parametrization

Parametrization works well with precise assertions:

```python
@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (OrderStatus.PENDING, True),
        (OrderStatus.PAID, True),
        (OrderStatus.SHIPPED, False),
    ],
)
def test_can_cancel(
    status: OrderStatus,
    expected: bool,
) -> None:
    assert can_cancel(status) is expected
```

The assertion represents the invariant shared across all parameter cases.

---

## Negative Assertions

Test important invalid behavior explicitly.

```python
def test_duplicate_order_is_rejected() -> None:
    with pytest.raises(DuplicateOrderError):
        service.create_order(
            idempotency_key="request-123",
        )
```

Negative assertions are especially important for:

- authorization;
- validation;
- duplicate requests;
- invalid state transitions;
- resource limits;
- security boundaries.

---

## Security Assertions

Security tests should verify denial, not merely successful access.

```python
def test_customer_cannot_access_other_tenant_order(
    client: TestClient,
) -> None:
    response = client.get(
        "/orders/tenant-b-order",
        headers=tenant_a_headers(),
    )

    assert response.status_code in {403, 404}
```

Also test that sensitive information is not exposed:

```python
body = response.json()

assert "internal_database_error" not in str(body)
```

Use stable security contracts rather than implementation-specific internals.

---

## Assertions for Authentication

A typical API test may verify:

```python
def test_missing_authentication_is_rejected(
    client: TestClient,
) -> None:
    response = client.get("/orders")

    assert response.status_code == 401
```

Authentication and authorization should be tested separately where their semantics differ.

---

## Assertions for Idempotency

Idempotency tests should verify externally observable equivalence:

```python
def test_duplicate_request_is_idempotent() -> None:
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

Where appropriate, also verify that only one durable side effect occurred.

---

## Assertions for Message Processing

For Kafka or Celery consumers, assertions should cover outcomes such as:

```python
assert event.status == "processed"
```

and duplicate behavior:

```python
assert processed_event_count == 1
```

For infrastructure semantics, integration tests should verify actual acknowledgment, commit, retry, or redelivery behavior.

---

## Assertions and Concurrency

Concurrency tests should assert deterministic invariants rather than exact scheduling.

Good:

```python
assert successful_updates == 1
assert final_balance == expected_balance
```

Fragile:

```python
assert task_a_completed_before_task_b
```

unless ordering is explicitly part of the contract.

Concurrency scheduling is nondeterministic by nature.

---

## Assertions and Async Code

Async tests use the same assertion model:

```python
@pytest.mark.asyncio
async def test_fetch_order() -> None:
    order = await service.fetch_order("order-1")

    assert order.id == "order-1"
    assert order.status == OrderStatus.CREATED
```

Assertions should verify asynchronous behavior and outcomes, not implementation details of the event loop.

---

## Assertions and Timeouts

Timeout behavior should be explicitly tested.

```python
def test_external_service_timeout() -> None:
    client = Mock()
    client.fetch.side_effect = TimeoutError()

    with pytest.raises(ServiceUnavailableError):
        service.fetch_order("order-1")
```

For actual asynchronous timeout behavior, test the real timeout mechanism in integration tests where it matters.

---

## Assertion Ordering

Place assertions in a logical order.

For API tests:

```python
assert response.status_code == 201

body = response.json()

assert body["id"]
assert body["status"] == "created"
assert body["amount"] == 2500
```

This makes failures easier to interpret.

Avoid dozens of unrelated assertions with no grouping.

---

## Fail-Fast and Assertions

pytest can stop after the first failure:

```bash
pytest -x
```

This is useful during local debugging.

In CI, allowing the suite to report multiple independent failures may provide better diagnostic value.

Assertion design should therefore make each failure independently understandable.

---

## Performance of Assertions

Assertions are usually inexpensive compared with database, network, and application operations.

The bigger performance issue is often doing unnecessary work solely to assert a result.

Avoid:

```python
assert expensive_full_database_scan() == expected
```

when a targeted query can verify the same invariant.

Test verification should be proportional to the behavior being tested.

---

## Common Assertion Mistakes

### Testing Implementation Details

Fragile:

```python
repository.save.assert_called_once()
```

when the actual contract is:

```python
assert order.status == OrderStatus.CREATED
```

Use interaction assertions only when the interaction is meaningful.

### Overly Broad Exceptions

Avoid:

```python
with pytest.raises(Exception):
    ...
```

Use the expected domain-specific exception.

### Exact Floating-Point Equality

Avoid:

```python
assert result == 0.3
```

when binary floating-point rounding is involved.

Use `pytest.approx()` or appropriate exact numeric types.

### Comparing Unordered Data as Lists

If ordering is not guaranteed:

```python
assert set(actual) == set(expected)
```

### Over-Asserting API Payloads

Do not assert generated timestamps, internal metadata, or unrelated fields unless they are part of the contract.

### Using Production `assert`

Do not use:

```python
assert user.is_admin
```

as an authorization mechanism in production code.

Use explicit control flow:

```python
if not user.is_admin:
    raise PermissionError("admin access required")
```

---

## Assertion Quality Checklist

Before finalizing a test, ask:

- Does each assertion verify meaningful behavior?
- Is the expected value explicit?
- Is the assertion tied to the public contract?
- Is the exception type specific enough?
- Am I accidentally depending on ordering?
- Am I comparing floats safely?
- Am I asserting implementation details unnecessarily?
- Would the failure message identify the problem quickly?
- Does the test verify security or authorization boundaries where relevant?
- Does the assertion remain valid if internal implementation changes?

---

## Interview Traps

### Why Does pytest Use Plain `assert`?

pytest can introspect Python assertion expressions and provide detailed failure information while keeping test code concise.

### Why Should `assert` Not Be Used for Production Validation?

Python can remove assertions when optimization is enabled. Assertions therefore are not appropriate for security checks, input validation, authorization, or mandatory business rules.

### When Should You Use `is` Instead of `==`?

Use `is` for object identity, especially singleton checks such as:

```python
assert value is None
```

Use `==` for value equality.

### Why Is `pytest.raises()` Better Than `assert isinstance(...)` for Exceptions?

`pytest.raises()` verifies that executing a specific operation actually raises the expected exception.

### Should Every Test Have Only One Assertion?

No.

Multiple assertions are appropriate when they verify one coherent behavior. Splitting every assertion into a separate test can create unnecessary setup and reduce readability.

### Why Avoid `assert response.json() == huge_payload`?

It can couple the test to irrelevant response details and make legitimate API evolution unnecessarily expensive. Assert the stable contract unless the entire payload is intentionally contractual.

### Why Can Mock Assertions Be Fragile?

They couple tests to interaction details. Refactoring internal implementation can break tests even when externally observable behavior remains correct.

### What Is the Difference Between a State Assertion and an Interaction Assertion?

A state assertion verifies the resulting system state. An interaction assertion verifies that a dependency was called in a particular way. Prefer state assertions for behavior and interaction assertions when the interaction itself is part of the contract.

## Key Takeaways

- **Assertions define the behavior a test actually verifies:** make them precise, meaningful, and aligned with the public or domain contract.
- **Use pytest's normal `assert` for value and state checks:** use `is` for identity, `pytest.raises()` for exceptions, and specialized helpers such as `pytest.approx()` where appropriate.
- **Avoid implementation-coupled assertions:** prefer observable outcomes over asserting every internal method call or private state transition.
- **Do not use Python `assert` for production enforcement:** optimized Python execution can remove assertions, so security, validation, authorization, and business rules require explicit runtime logic.
- **Strong assertions improve reliability and maintainability:** verify transactions, authorization, idempotency, retries, and other critical backend behavior while avoiding irrelevant or unstable details.