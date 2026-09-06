# 07- Parametrization

## Overview

Parametrization allows one pytest test definition to execute against multiple input combinations.

Instead of duplicating nearly identical tests:

```python
def test_valid_amount_100() -> None:
    assert is_valid_amount(100) is True


def test_valid_amount_500() -> None:
    assert is_valid_amount(500) is True


def test_invalid_amount_zero() -> None:
    assert is_valid_amount(0) is False
```

pytest can express the behavior once:

```python
@pytest.mark.parametrize(
    "amount",
    [100, 500, 0],
)
def test_amount_validation(amount: int) -> None:
    ...
```

Parametrization is most valuable when the **behavior under test is the same but the inputs or expected outcomes vary**.

In backend systems, it is particularly useful for:

- validation rules;
- state transitions;
- authorization matrices;
- HTTP status codes;
- serialization formats;
- boundary conditions;
- retry behavior;
- configuration combinations;
- domain rules.

Good parametrization reduces duplication without hiding the intent of individual scenarios.

---

## Why Parametrization Matters

Without parametrization, repetitive tests tend to drift:

```text
test_case_1 ─┐
test_case_2 ─┼── same behavior
test_case_3 ─┘
```

A future change may update two tests but accidentally omit the third.

Parametrization centralizes the behavior:

```text
                ┌── case A
                ├── case B
test definition ┼── case C
                └── case D
```

This improves:

- consistency;
- coverage of input spaces;
- maintainability;
- failure reporting;
- reviewability.

The goal is not to minimize the number of test functions. The goal is to represent a behavioral rule efficiently.

---

## Basic Parametrization

Use `pytest.mark.parametrize()`:

```python
import pytest


@pytest.mark.parametrize(
    "amount",
    [100, 500, 1000],
)
def test_positive_amount_is_valid(amount: int) -> None:
    assert is_valid_amount(amount) is True
```

pytest executes the test once per parameter:

```text
test_positive_amount_is_valid[100]
test_positive_amount_is_valid[500]
test_positive_amount_is_valid[1000]
```

Each invocation is an independent test case from pytest's perspective.

---

## Parametrization with Expected Results

The most common pattern is input plus expected output:

```python
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

This is effectively a small executable specification:

```text
Input → Expected behavior
```

It works particularly well for deterministic domain rules.

---

## Multiple Parameters

Multiple inputs can be parametrized together:

```python
@pytest.mark.parametrize(
    ("price", "quantity", "expected"),
    [
        (100, 1, 100),
        (100, 2, 200),
        (250, 4, 1000),
    ],
)
def test_calculate_total(
    price: int,
    quantity: int,
    expected: int,
) -> None:
    assert calculate_total(price, quantity) == expected
```

Keep the parameter table readable.

If each row requires significant explanation, separate tests may communicate intent better.

---

## Parameter Order

The values in each parameter row correspond positionally to the parameter names.

```python
@pytest.mark.parametrize(
    ("price", "quantity"),
    [
        (100, 2),
        (250, 4),
    ],
)
def test_total(price: int, quantity: int) -> None:
    ...
```

The first value maps to `price`; the second maps to `quantity`.

For complex cases, prefer explicit structures or named parameter objects when positional tuples become difficult to review.

---

## Parametrization with `pytest.param`

`pytest.param()` allows metadata to be attached to individual cases.

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

This produces meaningful case identifiers:

```text
test_amount[zero]
test_amount[positive]
test_amount[negative]
```

Readable IDs are valuable in CI failure output.

---

## Parameter IDs

For larger scenarios, use explicit IDs:

```python
@pytest.mark.parametrize(
    ("status", "expected"),
    [
        pytest.param(
            OrderStatus.PENDING,
            True,
            id="pending-can-cancel",
        ),
        pytest.param(
            OrderStatus.SHIPPED,
            False,
            id="shipped-cannot-cancel",
        ),
    ],
)
def test_cancellation_rules(
    status: OrderStatus,
    expected: bool,
) -> None:
    assert can_cancel(status) is expected
```

This makes failures self-describing.

---

## Parametrizing Exceptions

Parametrization works well for invalid inputs.

```python
@pytest.mark.parametrize(
    "amount",
    [-100, -1, 0],
)
def test_invalid_amount_raises(
    amount: int,
) -> None:
    with pytest.raises(ValueError):
        validate_amount(amount)
```

If different inputs should produce different exception types or messages, include those as parameters.

```python
@pytest.mark.parametrize(
    ("payload", "exception"),
    [
        ({}, MissingFieldError),
        ({"amount": -1}, InvalidAmountError),
    ],
)
def test_invalid_payload(
    payload: dict,
    exception: type[Exception],
) -> None:
    with pytest.raises(exception):
        validate_payload(payload)
```

---

## Parametrizing API Responses

Parametrization is useful for HTTP contracts.

```python
@pytest.mark.parametrize(
    ("payload", "status_code"),
    [
        ({"amount": 100}, 201),
        ({"amount": 0}, 422),
        ({"amount": -1}, 422),
    ],
)
def test_create_order_validation(
    client: TestClient,
    payload: dict,
    status_code: int,
) -> None:
    response = client.post(
        "/orders",
        json=payload,
    )

    assert response.status_code == status_code
```

This efficiently verifies multiple request-validation scenarios.

---

## Parametrizing Authorization

Authorization rules often form a matrix.

```python
@pytest.mark.parametrize(
    ("role", "expected_status"),
    [
        ("admin", 204),
        ("operator", 204),
        ("viewer", 403),
    ],
)
def test_delete_order_authorization(
    client: TestClient,
    role: str,
    expected_status: int,
) -> None:
    response = client.delete(
        "/orders/order-1",
        headers=auth_headers(role),
    )

    assert response.status_code == expected_status
```

This is a practical way to make access-control rules explicit.

For multi-dimensional authorization, consider a richer case structure rather than a large positional tuple.

---

## Parametrizing State Transitions

State machines are strong candidates for parametrization.

```python
@pytest.mark.parametrize(
    ("current", "target", "allowed"),
    [
        ("pending", "paid", True),
        ("pending", "cancelled", True),
        ("paid", "refunded", True),
        ("paid", "cancelled", False),
        ("shipped", "cancelled", False),
    ],
)
def test_order_transition(
    current: str,
    target: str,
    allowed: bool,
) -> None:
    assert can_transition(current, target) is allowed
```

The parameter table becomes an executable transition matrix.

---

## Parametrizing Serialization

Different input representations can exercise the same behavior.

```python
@pytest.mark.parametrize(
    ("payload", "expected_amount"),
    [
        ({"amount": 100}, 100),
        ('{"amount": 100}', 100),
    ],
)
def test_parse_amount(
    payload: object,
    expected_amount: int,
) -> None:
    assert parse_amount(payload) == expected_amount
```

Use this only when the same contract genuinely applies across representations.

---

## Parametrizing Configuration

Configuration-dependent behavior can also be tested systematically.

```python
@pytest.mark.parametrize(
    ("environment", "debug"),
    [
        ("development", True),
        ("staging", False),
        ("production", False),
    ],
)
def test_debug_configuration(
    environment: str,
    debug: bool,
) -> None:
    config = create_config(
        environment=environment,
    )

    assert config.debug is debug
```

For security-sensitive configuration, explicitly test production-safe defaults.

---

## Parametrization and Fixtures

Parametrization can work together with fixtures.

```python
@pytest.fixture
def service() -> OrderService:
    return create_test_service()


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (100, 100),
        (500, 500),
    ],
)
def test_create_order(
    service: OrderService,
    amount: int,
    expected: int,
) -> None:
    order = service.create_order(
        customer_id="customer-1",
        amount=amount,
    )

    assert order.amount == expected
```

pytest resolves the fixture for each parameterized test invocation.

---

## Fixture Parameters vs Test Parametrization

pytest provides two related mechanisms.

### Test Parametrization

```python
@pytest.mark.parametrize("amount", [100, 500])
def test_amount(amount: int) -> None:
    ...
```

The test itself varies.

### Fixture Parametrization

```python
@pytest.fixture(
    params=["postgres", "sqlite"],
)
def database(request):
    return create_database(request.param)
```

The fixture dependency varies.

Use test parametrization when the scenario changes.

Use fixture parametrization when the underlying dependency implementation or environment changes.

---

## Parametrized Fixtures

A fixture can define multiple variants:

```python
@pytest.fixture(
    params=[
        "admin",
        "viewer",
    ],
)
def user_role(request: pytest.FixtureRequest) -> str:
    return request.param
```

Any test using `user_role` runs once for each value.

This can be useful for cross-cutting scenarios, but fixture parametrization can create hidden test multiplication.

Prefer direct test parametrization when the variation is specific to one test.

---

## Indirect Parametrization

`indirect=True` allows parameter values to be passed through a fixture.

```python
@pytest.fixture
def database(request: pytest.FixtureRequest) -> Database:
    return create_database(request.param)


@pytest.mark.parametrize(
    "database",
    ["postgres"],
    indirect=True,
)
def test_repository(database: Database) -> None:
    ...
```

The parameter `"postgres"` is supplied to the fixture rather than directly to the test.

This is useful when parameter values describe how a complex dependency should be constructed.

---

## Selective Indirect Parametrization

With multiple parameters, only selected parameters can be indirect.

```python
@pytest.mark.parametrize(
    ("database", "amount"),
    [
        ("postgres", 100),
        ("postgres", 500),
    ],
    indirect=["database"],
)
def test_order(
    database: Database,
    amount: int,
) -> None:
    ...
```

This is powerful but more complex.

Use it when fixture construction genuinely needs parameterized inputs.

---

## Cross Product of Parameter Sets

Multiple `parametrize` decorators produce combinations.

```python
@pytest.mark.parametrize(
    "role",
    ["admin", "viewer"],
)
@pytest.mark.parametrize(
    "status",
    ["pending", "paid"],
)
def test_access(
    role: str,
    status: str,
) -> None:
    ...
```

This produces four combinations:

```text
admin  × pending
admin  × paid
viewer × pending
viewer × paid
```

Mathematically:

```text
number of cases = 2 × 2 = 4
```

This becomes dangerous when dimensions grow.

---

## Avoiding Combinatorial Explosion

Suppose:

```text
5 roles
× 6 order states
× 4 API versions
× 3 databases
```

produces:

```text
5 × 6 × 4 × 3 = 360
```

test cases.

The problem is not pytest; the problem is blindly testing the Cartesian product.

Use combinations that represent meaningful requirements.

Consider:

- equivalence classes;
- boundary cases;
- representative combinations;
- pairwise testing where appropriate;
- separate focused tests for independent dimensions.

---

## Boundary Value Parametrization

Boundary conditions are excellent parametrization candidates.

```python
@pytest.mark.parametrize(
    ("amount", "valid"),
    [
        (0, False),
        (1, True),
        (9999, True),
        (10_000, False),
    ],
)
def test_amount_limit(
    amount: int,
    valid: bool,
) -> None:
    assert is_valid_amount(amount) is valid
```

This makes the application's boundary contract explicit.

---

## Equivalence Classes

Do not test every possible integer if the behavior is equivalent across large ranges.

Instead of:

```text
1
2
3
4
...
9999
```

choose representative classes:

```text
negative
zero
minimum valid
normal valid
maximum valid
above maximum
```

Parametrization is most valuable when it captures meaningful behavioral partitions.

---

## Parametrizing Strings

Input normalization can be tested efficiently:

```python
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("alice@example.com", "alice@example.com"),
        (" ALICE@example.com ", "alice@example.com"),
        ("Alice@Example.com", "alice@example.com"),
    ],
)
def test_normalize_email(
    value: str,
    expected: str,
) -> None:
    assert normalize_email(value) == expected
```

Keep normalization rules explicit and avoid mixing unrelated behavior into the same parameter table.

---

## Parametrizing Optional Values

Test optional fields explicitly:

```python
@pytest.mark.parametrize(
    ("timeout", "expected"),
    [
        (None, DEFAULT_TIMEOUT),
        (5, 5),
        (30, 30),
    ],
)
def test_timeout_configuration(
    timeout: int | None,
    expected: int,
) -> None:
    config = create_config(timeout=timeout)

    assert config.timeout == expected
```

This is particularly useful for configuration defaults.

---

## Parametrizing Collections

Collection behavior can be tested with representative inputs:

```python
@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ([], 0),
        ([1], 1),
        ([1, 2, 3], 6),
    ],
)
def test_total(
    values: list[int],
    expected: int,
) -> None:
    assert total(values) == expected
```

Avoid giant parameter datasets when a smaller representative set covers the behavior.

---

## Parametrizing Dictionaries

Complex cases can be represented with dictionaries:

```python
@pytest.mark.parametrize(
    ("payload", "expected_status"),
    [
        (
            {"amount": 100},
            201,
        ),
        (
            {"amount": -1},
            422,
        ),
        (
            {},
            422,
        ),
    ],
)
def test_create_order(
    client: TestClient,
    payload: dict,
    expected_status: int,
) -> None:
    response = client.post(
        "/orders",
        json=payload,
    )

    assert response.status_code == expected_status
```

For highly structured cases, dataclasses or dedicated case objects may be easier to maintain.

---

## Dataclass-Based Test Cases

Complex parameter sets can use dataclasses.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class OrderCase:
    amount: int
    expected_status: int


@pytest.mark.parametrize(
    "case",
    [
        OrderCase(amount=100, expected_status=201),
        OrderCase(amount=-1, expected_status=422),
    ],
)
def test_create_order(
    client: TestClient,
    case: OrderCase,
) -> None:
    response = client.post(
        "/orders",
        json={"amount": case.amount},
    )

    assert response.status_code == case.expected_status
```

This becomes useful when each case has many attributes.

---

## Named Test Cases

For complex scenarios, descriptive IDs can make failures clearer:

```python
@pytest.mark.parametrize(
    "case",
    [
        pytest.param(
            OrderCase(amount=100, expected_status=201),
            id="valid-order",
        ),
        pytest.param(
            OrderCase(amount=-1, expected_status=422),
            id="negative-amount",
        ),
    ],
)
def test_create_order(client, case) -> None:
    ...
```

CI output now identifies the business scenario rather than only displaying raw parameter values.

---

## Mutable Parameter Values

Be careful with mutable parameter values.

For example:

```python
@pytest.mark.parametrize(
    "payload",
    [
        {"items": []},
        {"items": []},
    ],
)
def test_payload(payload: dict) -> None:
    ...
```

Parameter objects may be reused across test invocations rather than automatically deep-copied.

Tests should not mutate parameter values unless they intentionally create fresh state.

Prefer immutable data or copy mutable structures when mutation is required.

---

## Parameter State Leakage

This is dangerous:

```python
@pytest.mark.parametrize(
    "items",
    [
        [],
        [],
    ],
)
def test_items(items: list[int]) -> None:
    items.append(1)
```

The test is mutating its input.

Parameter data should generally be treated as read-only.

If mutation is part of the behavior under test, explicitly create or copy the mutable object.

---

## Parameterized Test Isolation

Each parameterized case is logically an independent test invocation.

```text
test_validation[case-1]
test_validation[case-2]
test_validation[case-3]
```

However, external state can still leak between cases if fixtures or application infrastructure are shared.

Parametrization does not automatically make databases, Redis, files, or global application state isolated.

---

## Parametrization with Database Tests

Database parametrization can be useful for business rules:

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
    db_session: Session,
    status: OrderStatus,
    expected: bool,
) -> None:
    order = create_order(
        db_session,
        status=status,
    )

    assert can_cancel(order) is expected
```

Keep the database setup controlled.

If the behavior is purely domain logic, avoid introducing a database merely to support parametrization.

---

## Parametrization with PostgreSQL

Use parameterized tests for PostgreSQL-specific business cases when appropriate, but do not confuse test parametrization with database query parameterization.

These are different concepts:

```text
pytest parametrization
→ multiple test scenarios

SQL parameterization
→ safe database query values
```

For SQL:

```python
cursor.execute(
    "SELECT * FROM orders WHERE id = %s",
    (order_id,),
)
```

Never construct SQL through string interpolation merely because a test itself is parameterized.

---

## Parametrization with Redis

Cache behavior can be tested across cases:

```python
@pytest.mark.parametrize(
    ("cached", "expected"),
    [
        (True, "cached-value"),
        (False, "fresh-value"),
    ],
)
def test_get_value(
    cache: Cache,
    cached: bool,
    expected: str,
) -> None:
    ...
```

Use a real Redis integration test when TTL, atomicity, eviction, or distributed behavior matters.

---

## Parametrization with Kafka

Message-processing behavior can be represented with event variants:

```python
@pytest.mark.parametrize(
    ("event_type", "expected_action"),
    [
        ("order.created", "create"),
        ("order.cancelled", "cancel"),
        ("order.refunded", "refund"),
    ],
)
def test_event_handler(
    event_type: str,
    expected_action: str,
) -> None:
    assert handle_event(event_type) == expected_action
```

For Kafka-specific delivery and offset semantics, integration testing remains necessary.

---

## Parametrization with Celery

Retry and failure behavior can be expressed as cases:

```python
@pytest.mark.parametrize(
    ("exception", "retryable"),
    [
        (TemporaryProviderError(), True),
        (InvalidRequestError(), False),
    ],
)
def test_job_retry_policy(
    exception: Exception,
    retryable: bool,
) -> None:
    assert should_retry(exception) is retryable
```

Actual worker, broker, acknowledgment, and retry behavior should be validated separately when those infrastructure semantics matter.

---

## Parametrization and API Versioning

API compatibility tests can use parameters:

```python
@pytest.mark.parametrize(
    ("version", "expected_status"),
    [
        ("v1", 200),
        ("v2", 200),
    ],
)
def test_get_order_api(
    client: TestClient,
    version: str,
    expected_status: int,
) -> None:
    response = client.get(
        f"/api/{version}/orders/order-1",
    )

    assert response.status_code == expected_status
```

For backward compatibility, add explicit assertions for fields and semantics that must remain stable.

---

## Parametrization and Property-Based Testing

Parametrization and property-based testing solve different problems.

| Technique | Strength |
|---|---|
| Parametrization | Explicit known cases |
| Property-based testing | Broad generated input space |

Example:

```python
@pytest.mark.parametrize(
    "value",
    [0, 1, 100, 1000],
)
def test_known_boundaries(value: int) -> None:
    ...
```

versus generated inputs:

```python
@given(st.integers(min_value=0))
def test_non_negative(value: int) -> None:
    ...
```

Use explicit cases for business scenarios and property-based testing for general invariants.

---

## Parametrization and Test Naming

Parameterized tests should still have meaningful test names.

Good:

```python
def test_amount_validation(...) -> None:
    ...
```

with IDs:

```text
test_amount_validation[negative]
```

Poor:

```python
def test_data(...) -> None:
    ...
```

The test name and case ID should together communicate the behavior.

---

## Failure Reporting

pytest reports each parameter case separately.

Example:

```text
FAILED tests/test_orders.py::test_amount_validation[negative]
FAILED tests/test_orders.py::test_amount_validation[zero]
```

This makes it easy to identify the failing scenario.

Good parameter IDs significantly improve CI diagnostics.

---

## Selective Execution

A specific parameterized case can be selected using its node ID.

For example:

```bash
pytest "tests/test_orders.py::test_amount_validation[negative]"
```

This is particularly useful when one parameter case fails while all others pass.

Because shell parsing can interpret special characters, quoting node IDs is a good habit.

---

## Parametrization and CI

Large parameter matrices can significantly increase CI execution time.

For example:

```text
100 tests
× 20 parameter cases
= 2,000 test invocations
```

The test file may look small while the actual execution cost is large.

Monitor:

- test count;
- execution time;
- database usage;
- network calls;
- memory usage;
- parallelism.

Parametrization should increase meaningful coverage, not blindly multiply workload.

---

## Performance Considerations

Parameterization itself is usually inexpensive.

The expensive part is what each case executes.

This is problematic:

```text
100 parameter cases
      ↓
start application
      ↓
create database
      ↓
perform network request
```

Prefer:

```text
100 lightweight unit cases
      ↓
fast execution
```

and reserve expensive parameter matrices for scenarios where the additional coverage justifies the cost.

---

## Production-Grade Parametrization Strategy

A scalable backend test suite might use:

```text
Unit tests
 ├── boundary cases
 ├── validation cases
 ├── state transitions
 └── authorization rules

Integration tests
 ├── database variants
 ├── transaction scenarios
 └── external dependency behavior

API tests
 ├── request variants
 ├── status codes
 └── compatibility cases
```

Parametrization should be applied independently at each layer.

Do not force every variation through the same integration test.

---

## Common Mistakes

### Duplicating Nearly Identical Tests

If only the input changes, parametrization is usually preferable.

### Giant Parameter Tables

A table with dozens or hundreds of opaque cases becomes difficult to review.

Split it by behavior.

### Combinatorial Explosion

Multiple parametrization dimensions can unexpectedly multiply test execution.

Calculate the resulting case count.

### Mutable Parameters

Mutating parameter objects can introduce state leakage.

Treat parameters as immutable unless mutation is intentional.

### Poor Case IDs

Raw complex objects make CI failures difficult to interpret.

Use meaningful IDs.

### Hiding Important Differences

If two cases have substantially different behavior, forcing them into one parametrized test can reduce clarity.

Separate tests may be better.

---

## Production Pitfalls

### Expensive Integration Matrices

A large parameter matrix against PostgreSQL, Redis, Kafka, or external APIs can make CI prohibitively expensive.

Use representative combinations.

### Shared Infrastructure

Parametrized tests can still interfere through shared external resources.

Isolation must be designed separately.

### False Coverage

Testing many equivalent values does not necessarily provide more meaningful coverage.

Choose cases based on behavior, not quantity.

### Unstable External Dependencies

Do not create dozens of parameter cases that each call a live third-party service.

Use controlled fakes, sandboxes, or focused integration tests.

---

## Security Considerations

Parametrized tests are useful for security matrices.

For example:

```python
@pytest.mark.parametrize(
    ("role", "allowed"),
    [
        ("admin", True),
        ("operator", True),
        ("viewer", False),
        ("anonymous", False),
    ],
)
def test_order_access(
    role: str,
    allowed: bool,
) -> None:
    assert can_access_order(role) is allowed
```

Security test cases should cover both positive and negative authorization behavior.

Do not put real credentials, tokens, customer identifiers, or secrets into parameter tables.

---

## Reliability Considerations

Parameterized tests should remain deterministic.

Avoid parameters that depend on:

- current time;
- random values;
- external service availability;
- test execution order;
- mutable shared state.

If nondeterministic behavior must be tested, control the source of nondeterminism with fixtures or dependency injection.

---

## Best Practices

- Use parametrization when one behavior has multiple meaningful cases.
- Include expected outcomes explicitly.
- Use descriptive parameter IDs for complex cases.
- Prefer representative equivalence classes over exhaustive input enumeration.
- Test boundary values deliberately.
- Keep parameter tables readable.
- Use `pytest.param()` for case metadata and expected failures/skips.
- Use fixture parametrization when the dependency itself varies.
- Use indirect parametrization only when fixture construction requires it.
- Treat parameter values as immutable.
- Watch for Cartesian-product explosion.
- Keep expensive integration matrices small and intentional.
- Separate materially different behaviors into separate tests.
- Use parametrization for authorization and validation matrices.
- Use property-based testing for broad invariants rather than generating enormous explicit tables.
- Measure CI impact when parameter counts grow.

---

## Practical Review Checklist

### Test Design

- [ ] Does every parameter represent a meaningful scenario?
- [ ] Is the behavior identical across cases?
- [ ] Are expected outcomes explicit?
- [ ] Would separate tests communicate the intent better?

### Parameter Data

- [ ] Are boundary values covered?
- [ ] Are invalid cases represented?
- [ ] Are mutable values protected from accidental mutation?
- [ ] Are case IDs readable?

### Scalability

- [ ] How many test invocations does the matrix produce?
- [ ] Are multiple parametrization dimensions multiplying unexpectedly?
- [ ] Does each case perform expensive I/O?
- [ ] Is the resulting CI cost justified?

### Backend Reliability

- [ ] Are database state and transactions isolated?
- [ ] Are Redis keys isolated?
- [ ] Are Kafka topics/messages isolated where necessary?
- [ ] Are retries and idempotency represented?
- [ ] Are authorization boundaries tested?

### Security

- [ ] Are negative authorization cases included?
- [ ] Are production credentials excluded?
- [ ] Is sensitive test data synthetic?
- [ ] Are security-sensitive defaults tested?

---

## Interview Traps

### What Is pytest Parametrization?

It allows one test definition to execute independently against multiple explicitly defined parameter sets.

### Why Use Parametrization Instead of Copying Tests?

It centralizes common behavior, reduces duplication, and makes systematic input variations explicit.

### Does Each Parameter Become a Separate Test?

Yes, conceptually. pytest collects and reports each parameterized invocation as an individual test case.

### What Happens with Multiple `parametrize` Decorators?

Their parameter sets are combined, producing the Cartesian product.

For example:

```text
2 roles × 3 statuses = 6 cases
```

This can cause accidental test explosion.

### When Should You Avoid Parametrization?

Avoid it when cases have substantially different setup, behavior, assertions, or business meaning. Separate focused tests may be clearer.

### What Is `pytest.param()` Used For?

It attaches metadata to an individual case, such as a descriptive ID, marks, or expected-failure configuration.

### What Is Indirect Parametrization?

It passes parameter values through a fixture rather than directly into the test function, allowing the fixture to construct the actual dependency.

### Does Parametrization Guarantee Isolation?

No.

Each parameter case is a separate test invocation, but shared databases, Redis, files, global state, or broader-scoped fixtures can still leak state.

### Parametrization vs Property-Based Testing?

Parametrization explicitly defines known scenarios. Property-based testing generates many inputs to validate general invariants.

### Should You Test Every Possible Input with Parametrization?

No.

Use equivalence classes, boundaries, and representative cases. Exhaustive enumeration is usually unnecessary and can make the suite expensive without increasing meaningful confidence.

## Key Takeaways

- **Parametrization expresses one behavior across multiple meaningful scenarios:** use it for validation, state transitions, authorization, API contracts, and boundary cases.
- **Make expected outcomes explicit:** parameter tables should read like executable specifications rather than collections of unexplained inputs.
- **Control complexity:** multiple parameter dimensions create Cartesian products, so calculate test counts and avoid unnecessary combinations.
- **Keep cases isolated and diagnosable:** treat parameter data as immutable, use descriptive IDs, and remember that parametrization does not eliminate shared external-state problems.
- **Optimize for behavioral coverage, not test count:** use representative equivalence classes for explicit cases and property-based testing when broad input-space exploration is more appropriate.