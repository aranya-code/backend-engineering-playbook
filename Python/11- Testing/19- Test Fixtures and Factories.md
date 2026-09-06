# 19- Test Fixtures and Factories

## Overview

Test fixtures and factories provide reusable mechanisms for preparing test dependencies and generating controlled test data.

They solve different problems:

- **Fixtures** manage dependencies, lifecycle, configuration, and resources.
- **Factories** generate domain objects and test data.

A typical backend test architecture looks like:

```text
Test
 │
 ├── Fixtures
 │    ├── Database
 │    ├── HTTP Client
 │    ├── Redis
 │    └── Authenticated User
 │
 └── Factories
      ├── Customer
      ├── Order
      └── Payment
```

The distinction is important because fixtures answer:

> What resources does this test need, and how are they created and cleaned up?

Factories answer:

> What domain data does this test need, and how should that data be generated?

Well-designed fixtures and factories improve:

- readability;
- test isolation;
- consistency;
- maintainability;
- parallel execution;
- integration-test performance;
- CI reliability.

Poorly designed fixtures can have the opposite effect by hiding dependencies, creating excessive setup, and introducing shared mutable state.

---

## Fixtures

A pytest fixture is a reusable dependency that pytest creates and injects into a test.

```python
import pytest


@pytest.fixture
def customer():
    return Customer(
        id="customer-123",
        email="customer@example.test",
    )


def test_customer_email(customer):
    assert customer.email == "customer@example.test"
```

pytest resolves the fixture from the test function's parameter name.

```text
test_customer_email(customer)
             │
             ▼
       pytest fixture
             │
             ▼
       Customer object
```

Fixtures can provide:

- objects;
- configuration;
- database connections;
- HTTP clients;
- authentication;
- temporary files;
- external services;
- test infrastructure.

---

## Why Fixtures Exist

Without fixtures, tests often repeat setup:

```python
def test_create_order():
    db = create_database()
    client = create_client()
    user = create_user()
    ...


def test_update_order():
    db = create_database()
    client = create_client()
    user = create_user()
    ...
```

Fixtures centralize lifecycle management:

```text
Fixture
  │
  ├── setup
  ├── provide dependency
  └── cleanup
```

This reduces duplication while keeping setup behavior consistent.

---

## Fixture Dependency Injection

pytest fixtures support dependency injection.

```python
@pytest.fixture
def customer():
    return customer_factory()


@pytest.fixture
def order(customer):
    return order_factory(
        customer_id=customer.id,
    )


def test_order_belongs_to_customer(order, customer):
    assert order.customer_id == customer.id
```

The dependency graph is:

```text
customer
   │
   ▼
order
   │
   ▼
test
```

pytest resolves the graph automatically.

This allows complex test environments to be composed from smaller fixtures.

---

## Fixtures vs Factories

The distinction should remain explicit.

| Concern | Fixture | Factory |
|---|---|---|
| Dependency injection | Yes | No |
| Resource lifecycle | Yes | Usually no |
| Database connection | Yes | No |
| HTTP client | Yes | No |
| Authentication context | Yes | Can generate data |
| Domain object creation | Sometimes | Primary purpose |
| Parameterized data | Sometimes | Excellent |
| Cleanup | Yes | Usually no |
| Reusable test infrastructure | Yes | No |
| Test data generation | Secondary | Primary |

A fixture may call a factory:

```python
@pytest.fixture
def order(db_session):
    return order_factory(db_session)
```

This separation is often preferable to putting all data-generation logic directly into fixtures.

---

## Fixture Scope

pytest supports multiple fixture scopes.

| Scope | Lifetime | Typical Use |
|---|---|---|
| `function` | One test | Mutable test data |
| `class` | One test class | Class-specific resources |
| `module` | One module | Shared read-only setup |
| `package` | Package | Expensive package-level resources |
| `session` | Entire run | Infrastructure |

The default scope is `function`.

For mutable state, function scope is usually the safest choice.

---

## Function-Scoped Fixtures

```python
@pytest.fixture
def customer():
    return customer_factory()
```

Every test gets a fresh object:

```text
Test A → Customer A
Test B → Customer B
Test C → Customer C
```

This reduces state leakage.

---

## Session-Scoped Infrastructure

Expensive infrastructure can often be shared:

```python
@pytest.fixture(scope="session")
def postgres():
    database = start_postgres()

    try:
        yield database
    finally:
        database.stop()
```

The lifecycle becomes:

```text
pytest session
      │
      ▼
PostgreSQL
      │
      ├── Test 1
      ├── Test 2
      ├── Test 3
      └── Test N
      │
      ▼
shutdown
```

Infrastructure sharing is different from sharing mutable test data.

---

## Yield Fixtures

`yield` fixtures provide a natural setup/teardown boundary.

```python
@pytest.fixture
def database_connection():
    connection = create_connection()

    try:
        yield connection
    finally:
        connection.close()
```

The code before `yield` performs setup.

The code after `yield` performs cleanup.

This is especially useful for:

- database sessions;
- HTTP clients;
- Redis clients;
- temporary resources;
- background workers.

---

## Fixture Cleanup

Cleanup should happen even when the test fails.

```python
@pytest.fixture
def temporary_resource():
    resource = create_resource()

    try:
        yield resource
    finally:
        destroy_resource(resource)
```

Without deterministic cleanup, resources can leak between tests.

Typical leaks include:

- database connections;
- Redis connections;
- Kafka consumers;
- filesystem handles;
- temporary files;
- asyncio tasks;
- threads.

---

## Cleanup Ordering

Fixture teardown follows dependency relationships.

Consider:

```text
database
   │
   ▼
db_session
   │
   ▼
repository
   │
   ▼
test
```

Resources closer to the test should generally be cleaned up before their underlying infrastructure.

This prevents errors such as:

```text
database destroyed
      │
      ▼
fixture attempts DB cleanup
      │
      ▼
connection failure
```

---

## Fixture Factories

A fixture can return a function for dynamic setup.

```python
@pytest.fixture
def create_customer():
    def factory(
        *,
        email=None,
        status="active",
    ):
        return Customer(
            id=str(uuid4()),
            email=email or f"{uuid4()}@example.test",
            status=status,
        )

    return factory
```

The test can create multiple independent objects:

```python
def test_customer_statuses(create_customer):
    active = create_customer(status="active")
    suspended = create_customer(status="suspended")

    assert active.status == "active"
    assert suspended.status == "suspended"
```

This pattern is useful when setup parameters vary significantly across tests.

---

## Factories

A factory is a reusable mechanism for generating valid test data.

For a backend domain:

```text
CustomerFactory
OrderFactory
PaymentFactory
ProductFactory
UserFactory
```

A factory typically:

1. provides sensible defaults;
2. allows relevant overrides;
3. creates unique identifiers;
4. produces valid domain state;
5. optionally persists the object.

---

## Basic Factory

A simple Python factory might be:

```python
from uuid import uuid4


def customer_factory(
    *,
    email: str | None = None,
    status: str = "active",
) -> Customer:
    return Customer(
        id=str(uuid4()),
        email=email or f"{uuid4()}@example.test",
        status=status,
    )
```

Usage:

```python
customer = customer_factory()

assert customer.status == "active"
```

The default should represent a valid, commonly useful object.

---

## Factory Overrides

Factories should support explicit overrides:

```python
customer = customer_factory(
    status="suspended",
)
```

This is preferable to maintaining many specialized functions:

```python
create_active_customer()
create_suspended_customer()
create_pending_customer()
```

when the only difference is an attribute.

---

## Database Factories

A persistence-aware factory can accept a repository or session:

```python
def customer_factory(
    repository,
    *,
    email: str | None = None,
    status: str = "active",
) -> Customer:
    customer = Customer(
        id=str(uuid4()),
        email=email or f"{uuid4()}@example.test",
        status=status,
    )

    repository.save(customer)

    return customer
```

This is useful for integration tests.

However, keep persistence behavior explicit so developers know whether a factory returns an in-memory object or a persisted record.

---

## Build vs Create

Factories often benefit from distinguishing:

```text
build → construct object, do not persist

create → construct and persist
```

For example:

```python
customer = customer_factory.build(
    status="active",
)

persisted_customer = customer_factory.create(
    status="active",
)
```

The exact API depends on the factory implementation.

This distinction is valuable because unit tests often need objects without database access, while integration tests need persistent records.

---

## Factory Design Principles

A good factory should:

- create valid objects by default;
- use realistic values;
- generate unique identifiers;
- allow relevant overrides;
- avoid unnecessary dependencies;
- avoid surprising side effects;
- remain easy to understand.

A bad factory:

```text
create_order()
    ├── creates customer
    ├── creates payment
    ├── creates inventory
    ├── creates shipment
    ├── publishes Kafka event
    └── modifies Redis
```

This makes a simple test expensive and hides its dependencies.

---

## Explicit Relationships

Prefer explicit relationships:

```python
customer = customer_factory()

order = order_factory(
    customer_id=customer.id,
)
```

over a factory that silently creates the customer:

```python
order = order_factory()
```

when the relationship itself is important to the test.

Explicit setup improves readability and debugging.

---

## Nested Factories

Factories can compose other factories.

```python
def order_factory(
    *,
    customer: Customer | None = None,
) -> Order:
    customer = customer or customer_factory()

    return Order(
        id=str(uuid4()),
        customer_id=customer.id,
        status="pending",
    )
```

This is convenient, but should be used carefully.

Hidden creation of dependencies can produce unexpectedly large object graphs.

---

## Factory Graphs

A complex factory graph can become:

```text
OrderFactory
   │
   ├── CustomerFactory
   │     └── AddressFactory
   │
   ├── ProductFactory
   │
   ├── PaymentFactory
   │     └── CustomerFactory
   │
   └── InventoryFactory
```

This creates:

- slow tests;
- excessive database writes;
- hidden dependencies;
- difficult debugging.

Keep factory graphs shallow unless the domain relationship genuinely requires them.

---

## Factories and Test Isolation

Factories should produce isolated data by default.

Use unique values:

```python
email = f"{uuid4()}@example.test"
```

instead of:

```python
email = "test@example.com"
```

Unique values reduce collisions in:

- parallel tests;
- unique database constraints;
- Redis;
- Kafka;
- API integration tests.

---

## Factories and Deterministic Tests

Random identifiers are useful for uniqueness, but not every value should be random.

Prefer predictable defaults for behavior:

```python
status="active"
currency="USD"
quantity=1
```

Use randomness primarily for uniqueness.

This creates:

```text
Deterministic behavior
        +
Unique identity
        =
Reliable test data
```

---

## Factory States

For domains with common states, explicit factory states can improve readability.

For example:

```python
customer_factory(active=True)
customer_factory(suspended=True)
```

or:

```python
customer_factory(status="suspended")
```

Keep state APIs simple.

If factories accumulate dozens of state flags, the domain model may need clearer builders or specialized fixtures.

---

## Factory Boy

`factory_boy` is a popular Python library for declarative test-data factories.

Example:

```python
import factory


class CustomerFactory(factory.Factory):
    class Meta:
        model = Customer

    id = factory.LazyFunction(uuid4)
    email = factory.LazyAttribute(
        lambda obj: f"{obj.id}@example.test"
    )
    status = "active"
```

For ORM-backed applications, `factory_boy` also provides integrations for frameworks such as Django and SQLAlchemy.

Use a factory library when it meaningfully reduces repetitive test-data construction.

A small project may not need one.

---

## Factory Libraries vs Plain Python

| Approach | Advantages | Limitations |
|---|---|---|
| Plain functions | Simple, explicit | More boilerplate at scale |
| pytest fixture factory | Excellent pytest integration | Tied to pytest |
| `factory_boy` | Rich declarations and ORM support | Additional abstraction |
| Builder pattern | Highly customizable | More code |
| Faker-based generation | Realistic generated data | Can reduce determinism |

Choose the simplest approach that scales with the test suite.

---

## Faker and Generated Data

Libraries such as Faker can produce realistic data:

```python
from faker import Faker

fake = Faker()

email = fake.email()
name = fake.name()
```

Generated values are useful for:

- payload testing;
- data-volume testing;
- boundary scenarios.

However, excessive randomness can make failures difficult to reproduce.

Prefer deterministic values for assertions and use generated data where realism or uniqueness matters.

---

## Factories and API Tests

Factories can prepare API state:

```python
@pytest.mark.asyncio
async def test_get_order(
    client,
    order_factory,
):
    order = await order_factory(
        status="confirmed",
    )

    response = await client.get(
        f"/orders/{order.id}",
    )

    assert response.status_code == 200
    assert response.json()["id"] == order.id
```

The factory handles test data.

The fixture handles infrastructure.

The API test focuses on behavior.

---

## Factories and Database Tests

A database test might use:

```python
@pytest.mark.asyncio
async def test_find_active_orders(
    repository,
    order_factory,
):
    await order_factory(status="active")
    await order_factory(status="cancelled")

    orders = await repository.find_active()

    assert len(orders) == 1
    assert orders[0].status == "active"
```

This keeps the test concise while making the relevant state explicit.

---

## Factories and Authentication

Authentication fixtures and factories often work together.

```text
user_factory
     │
     ▼
User
     │
     ▼
auth_token_fixture
     │
     ▼
authenticated_client_fixture
     │
     ▼
API test
```

For example:

```python
@pytest.fixture
def authenticated_client(client, user):
    token = create_test_token(user)

    client.headers["Authorization"] = (
        f"Bearer {token}"
    )

    return client
```

The user factory controls identity data; the fixture controls the authenticated client lifecycle.

---

## Fixture Composition

A mature test suite may compose fixtures:

```python
@pytest.fixture
def customer(customer_factory):
    return customer_factory()


@pytest.fixture
def order(order_factory, customer):
    return order_factory(
        customer_id=customer.id,
    )


@pytest.fixture
def authenticated_client(client, customer):
    return authenticate(
        client,
        customer,
    )
```

This creates a dependency graph:

```text
customer_factory
       │
       ├── customer
       │      │
       │      ├── order
       │      └── authenticated_client
       │
       ▼
      test
```

Keep this graph understandable.

---

## `conftest.py`

pytest fixtures shared across a test directory are commonly placed in `conftest.py`.

Example:

```text
tests/
├── conftest.py
├── unit/
│   └── test_orders.py
└── integration/
    ├── conftest.py
    └── test_orders_api.py
```

Fixtures in a parent `conftest.py` can be available to tests below that directory.

This supports layered fixture architecture.

---

## Fixture Visibility

A useful structure is:

```text
tests/
├── conftest.py
│   ├── application
│   └── configuration
│
├── unit/
│   └── local fixtures
│
└── integration/
    └── conftest.py
        ├── database
        ├── redis
        └── kafka
```

Avoid putting every fixture into the root `conftest.py`.

Large global fixture collections become difficult to discover and maintain.

---

## Local vs Shared Fixtures

Use a local fixture when:

- only one test module needs it;
- its behavior is specialized;
- sharing would reduce clarity.

Use a shared fixture when:

- many tests need the same dependency;
- lifecycle management should be standardized;
- duplication would be significant.

Do not optimize for maximum fixture reuse.

Optimize for clear test architecture.

---

## Fixture Naming

Names should communicate what the fixture provides.

Prefer:

```python
@pytest.fixture
def authenticated_client():
    ...


@pytest.fixture
def postgres_session():
    ...
```

over:

```python
@pytest.fixture
def setup():
    ...


@pytest.fixture
def helper():
    ...
```

Tests should be understandable by reading their parameters.

---

## Avoid Giant Fixtures

Bad:

```python
@pytest.fixture
def everything():
    return {
        "database": ...,
        "redis": ...,
        "kafka": ...,
        "user": ...,
        "customer": ...,
        "order": ...,
        "payment": ...,
    }
```

This hides dependencies and creates unnecessary setup.

Prefer focused fixtures:

```python
def test_order(order, authenticated_client):
    ...
```

---

## Autouse Fixtures

Autouse fixtures execute automatically:

```python
@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    ...
```

They are appropriate for genuinely universal behavior.

Avoid using autouse to create business data.

Explicit dependencies are usually easier to understand:

```python
def test_order(order):
    ...
```

than:

```python
def test_order():
    # Hidden order fixture executes automatically.
    ...
```

---

## Fixture Scope and Mutable State

A session-scoped mutable object is dangerous:

```python
@pytest.fixture(scope="session")
def state():
    return {}
```

Test A:

```python
state["value"] = "A"
```

Test B may observe:

```python
state["value"] == "A"
```

Prefer function scope:

```python
@pytest.fixture
def state():
    return {}
```

or use an explicitly reset immutable/shared resource.

---

## Database Fixture + Factory Architecture

A useful integration-test structure is:

```text
Session
  │
  └── PostgreSQL
        │
        ▼
Function
  │
  ├── DB session
  └── Factory
        │
        ├── Customer
        ├── Order
        └── Payment
```

Infrastructure can be expensive and shared.

Data should usually be isolated per test.

---

## Transactional Factory Design

Factories that persist records should respect the test's transaction model.

Bad architecture:

```text
Test transaction
      │
      ▼
Factory opens independent connection
      │
      ▼
COMMIT
```

The factory may create durable state outside the test transaction.

Prefer passing the test-managed session:

```python
await order_factory(
    session=db_session,
)
```

This makes transaction ownership explicit.

---

## Async Fixtures

Async resources require async lifecycle management.

```python
@pytest.fixture
async def redis_client():
    client = create_redis_client()

    try:
        yield client
    finally:
        await client.close()
```

Ensure the pytest async plugin and project configuration use a consistent event-loop strategy.

Do not leave async clients or background tasks alive after the test.

---

## Async Factories

Factories that interact with asynchronous repositories can also be asynchronous:

```python
async def order_factory(
    repository,
    *,
    status="pending",
):
    order = Order(
        id=str(uuid4()),
        status=status,
    )

    await repository.save(order)

    return order
```

Keep async behavior explicit.

Do not hide expensive asynchronous operations behind a factory that appears to be a simple in-memory constructor.

---

## Fixture Performance

Fixtures can dominate test-suite runtime.

Common expensive operations include:

- starting containers;
- running migrations;
- creating large datasets;
- creating many database rows;
- initializing external clients;
- loading large files.

Measure before optimizing.

A useful design is:

```text
Session-scoped infrastructure
        +
Worker-scoped isolation
        +
Function-scoped test data
```

when the environment supports it safely.

---

## Fixture Dependency Graph Complexity

Consider:

```text
test
 └── fixture A
      └── fixture B
           └── fixture C
                └── fixture D
                     └── fixture E
```

Deep dependency graphs make failures difficult to diagnose.

Prefer shallow composition:

```text
test
 ├── database
 ├── customer
 └── order
```

unless the domain genuinely requires deeper dependencies.

---

## Fixture and Factory Ownership

Every resource should have a clear owner.

| Resource | Typical Owner |
|---|---|
| Database container | Infrastructure fixture |
| DB session | Database fixture |
| Customer record | Customer factory |
| Order record | Order factory |
| HTTP client | HTTP fixture |
| Authentication token | Auth fixture |
| Temporary file | Filesystem fixture |
| Kafka topic | Messaging fixture |
| Kafka message | Message factory/helper |
| Redis key | Redis fixture/factory |

Clear ownership prevents cleanup ambiguity.

---

## Factory Defaults

Factories should provide valid defaults:

```python
order_factory(
    status="pending",
    quantity=1,
)
```

Avoid invalid defaults unless the factory is explicitly designed for invalid-state testing.

Tests should opt into exceptional states:

```python
order_factory(
    status="cancelled",
)
```

rather than having to repair an invalid default object.

---

## Factory Defaults and Domain Invariants

If the domain requires:

```text
Order
 ├── customer_id required
 ├── quantity > 0
 └── status valid
```

the default factory should produce a valid order.

This allows tests to focus on the behavior under examination rather than reconstructing domain validity repeatedly.

---

## Overriding Nested Data

Factories should make important nested overrides possible.

For example:

```python
order_factory(
    customer_id=customer.id,
    status="confirmed",
)
```

Avoid requiring callers to modify factory-created objects after creation:

```python
order = order_factory()
order.customer_id = customer.id
order.status = "confirmed"
```

unless mutation itself is what the test intends to exercise.

---

## Factories and Invalid Data

Do not force factories to generate every invalid state through complicated flags.

Prefer direct test construction for unusual invalid objects:

```python
payload = {
    "quantity": -1,
}
```

or a dedicated helper:

```python
invalid_order_payload()
```

Factories are primarily for valid domain state.

---

## Factories for API Payloads

Domain factories and API payload factories can be separate.

```python
def order_payload_factory(
    *,
    quantity=1,
):
    return {
        "customer_id": str(uuid4()),
        "items": [
            {
                "product_id": str(uuid4()),
                "quantity": quantity,
            }
        ],
    }
```

This is useful because API payloads are not necessarily identical to database models.

Keep these concepts separate:

```text
API Request Factory
        │
        ▼
Request Schema

Domain Factory
        │
        ▼
Domain Model
```

---

## Factories for Large Test Suites

As a suite grows, establish conventions:

```text
tests/
├── factories/
│   ├── customer.py
│   ├── order.py
│   ├── payment.py
│   └── user.py
│
├── fixtures/
│   ├── database.py
│   ├── redis.py
│   └── kafka.py
│
└── conftest.py
```

The exact directory structure is project-specific.

The important principle is separating infrastructure lifecycle from data generation.

---

## Test Data Builders

For complex immutable request or domain objects, a builder can be clearer than a large factory.

For example:

```python
@dataclass
class OrderBuilder:
    customer_id: str = "customer-123"
    status: str = "pending"
    quantity: int = 1

    def with_status(self, status: str):
        return replace(self, status=status)

    def build(self) -> Order:
        return Order(
            id=str(uuid4()),
            customer_id=self.customer_id,
            status=self.status,
            quantity=self.quantity,
        )
```

Builders are useful when tests need many combinations without requiring a large factory API.

---

## Fixtures, Factories, and Dependency Injection

A clean architecture separates:

```text
Fixture
  │
  ├── supplies repository
  └── supplies database session

Factory
  │
  └── creates domain state

Test
  │
  └── verifies behavior
```

This is essentially dependency injection applied to the test environment.

It keeps infrastructure concerns separate from test intent.

---

## Security Considerations

Fixtures and factories should never silently use production resources.

Protect:

- database URLs;
- AWS credentials;
- Redis endpoints;
- Kafka clusters;
- external API keys.

Use explicit test configuration:

```python
if settings.environment == "production":
    raise RuntimeError(
        "Tests cannot run against production"
    )
```

Factories should also generate synthetic data.

Do not generate test users using real customer information.

---

## CI/CD Considerations

CI should provide predictable fixture dependencies.

A typical pipeline:

```text
CI Worker
   │
   ├── Start PostgreSQL
   ├── Start Redis
   ├── Start Kafka
   │
   ▼
Fixtures
   │
   ▼
Factories
   │
   ▼
Tests
   │
   ▼
Cleanup
```

Use isolated resources per worker when running tests in parallel.

---

## Common Mistakes

### Confusing Fixtures and Factories

A fixture manages dependencies and lifecycle.

A factory generates data.

Mixing the two can produce difficult-to-maintain setup code.

### Giant Fixtures

One fixture creates the entire application state.

This makes tests slow and hides dependencies.

### Giant Factories

One factory creates an entire object graph.

This produces expensive and surprising test setup.

### Excessive Fixture Scope

Using `session` scope for mutable objects creates shared state.

Prefer function scope unless sharing is intentional and safe.

### Hidden Dependencies

Autouse fixtures or deeply nested fixtures make tests difficult to understand.

Prefer explicit parameters.

### Factory Side Effects

A factory that publishes Kafka messages or modifies Redis unexpectedly can make unit tests behave like integration tests.

Keep side effects explicit.

### Hard-Coded Unique Fields

Using:

```text
test@example.com
```

for every factory-created user causes collisions.

Generate unique identifiers where required.

### Excessive Randomness

Random test data can make failures difficult to reproduce.

Use deterministic values for assertions and randomness primarily for uniqueness or data-volume testing.

---

## Production Pitfalls

### Slow Fixture Graphs

A single test may unintentionally start multiple services and create dozens of database rows.

Keep fixture graphs shallow and inspect expensive setup.

### Shared Mutable Session Fixtures

Session-scoped objects can retain state across hundreds of tests.

Share infrastructure, not mutable business state.

### Factory Persistence Hidden from Tests

A function named:

```python
create_order()
```

may unexpectedly execute database writes.

Make persistence semantics obvious through naming or separate `build` and `create` operations.

### Factories That Bypass Production Rules

A factory that directly inserts invalid or incomplete records may produce states that production code can never create.

Use factories to establish realistic state unless the test intentionally targets corrupted data.

### Cleanup Owned by the Wrong Layer

If a factory creates a database record but a fixture owns the transaction, cleanup responsibility becomes unclear.

Define resource ownership explicitly.

---

## Best Practices

- Keep fixtures responsible for dependencies and lifecycle.
- Keep factories responsible for data generation.
- Use function scope for mutable test state by default.
- Share expensive immutable infrastructure where safe.
- Use `yield` fixtures for deterministic cleanup.
- Keep fixture dependency graphs shallow.
- Avoid excessive `autouse` fixtures.
- Make important test dependencies explicit.
- Give factories valid, realistic defaults.
- Allow focused overrides for scenario-specific state.
- Generate unique identifiers for mutable persistent data.
- Separate `build` from `create` semantics where useful.
- Pass test-managed database sessions into persistence-aware factories.
- Keep API payload factories separate from domain-model factories.
- Avoid hidden external side effects in factories.
- Use deterministic values for assertions and controlled randomness for uniqueness.
- Measure fixture performance before introducing broader scopes.
- Design fixtures and factories for parallel execution.
- Keep test configuration incapable of accidentally reaching production.

---

## Recommended Test Architecture

A production-oriented Python test suite can use:

```text
tests/
├── conftest.py
│
├── fixtures/
│   ├── application.py
│   ├── database.py
│   ├── redis.py
│   ├── kafka.py
│   └── authentication.py
│
├── factories/
│   ├── users.py
│   ├── customers.py
│   ├── orders.py
│   └── payments.py
│
├── unit/
│   └── ...
│
├── integration/
│   └── ...
│
└── api/
    └── ...
```

The architecture separates:

```text
Infrastructure lifecycle
        │
        ▼
Fixtures
        │
        ▼
Test data
        │
        ▼
Factories
        │
        ▼
Tests
```

The exact structure can be smaller for small projects.

The architectural principle is more important than the directory names.

---

## Fixture and Factory Checklist

### Fixtures

- [ ] Does the fixture provide one clear dependency?
- [ ] Is its scope appropriate?
- [ ] Is mutable state isolated?
- [ ] Is cleanup deterministic?
- [ ] Are expensive resources intentionally shared?
- [ ] Are dependencies explicit?
- [ ] Is `autouse` genuinely necessary?

### Factories

- [ ] Are defaults valid?
- [ ] Are identifiers unique where required?
- [ ] Can important fields be overridden?
- [ ] Is persistence behavior explicit?
- [ ] Are API payloads separated from domain objects?
- [ ] Are factory graphs reasonably shallow?
- [ ] Is randomness controlled?

### Integration

- [ ] Does the factory use the test-managed database session?
- [ ] Are Redis keys isolated?
- [ ] Are Kafka resources isolated?
- [ ] Are async resources cleaned up?
- [ ] Are tests parallel-safe?
- [ ] Can test configuration reach production?

### Maintainability

- [ ] Are fixture names descriptive?
- [ ] Are factories easy to discover?
- [ ] Are dependencies understandable?
- [ ] Is setup proportional to the test?
- [ ] Are common patterns centralized without over-abstracting?

---

## Interview Traps

### What Is a pytest Fixture?

A fixture is a reusable dependency provider that can manage setup, dependency injection, scope, and cleanup for tests.

### What Is a Test Factory?

A factory is a reusable mechanism for generating valid test data or domain objects with configurable values.

### What Is the Difference Between a Fixture and a Factory?

Fixtures primarily manage dependencies and lifecycle. Factories primarily generate test data. A fixture can use a factory to create data.

### What Is the Default pytest Fixture Scope?

The default scope is `function`, meaning a new fixture instance is created for each test that requests it.

### When Should You Use Session-Scoped Fixtures?

Use session scope for expensive resources that can be safely shared, such as a disposable PostgreSQL container. Avoid using it for mutable business state unless sharing is intentional.

### Why Are Giant Fixtures Bad?

They create unnecessary setup, hide dependencies, increase execution time, and make failures harder to diagnose.

### Why Are Giant Factories Bad?

They create large object graphs and hidden dependencies. A test that needs one order may unexpectedly create customers, payments, inventory, and other resources.

### Should Factories Persist Data?

They can, especially for integration tests, but persistence should be explicit. Separating `build` from `create` semantics can make this distinction clear.

### How Do You Make Factories Parallel-Safe?

Generate unique identifiers and resource names, avoid shared mutable state, and use isolated database or infrastructure resources where required.

### Why Should Factories Use Valid Defaults?

Valid defaults reduce repetitive setup and allow tests to focus on the specific state relevant to the behavior being tested.

### Why Is Excessive Random Test Data a Problem?

Randomness can make failures difficult to reproduce and diagnose. Use deterministic values for important assertions and randomness primarily for uniqueness or data-volume testing.

### When Should You Use `factory_boy`?

Use it when declarative factories, ORM integration, sequences, relationships, or factory inheritance materially reduce test complexity. A small suite may be better served by plain Python functions.

### How Do Fixtures Improve Test Isolation?

Fixtures can create fresh resources per test and guarantee cleanup, preventing state from leaking between tests.

### What Is a Senior-Level Fixture Design Principle?

Share expensive infrastructure when safe, but isolate mutable business state. Optimize fixture scope based on measured performance without weakening test independence.

## Key Takeaways

- **Fixtures manage dependencies and lifecycle; factories generate test data:** keeping these responsibilities separate makes test setup explicit and maintainable.
- **Default to isolated mutable state:** function-scoped fixtures and unique factory-generated data reduce order-dependent and parallel-execution failures.
- **Make persistence and side effects explicit:** distinguish object construction from database creation and avoid factories that unexpectedly modify Redis, Kafka, or other external systems.
- **Control fixture complexity:** shallow dependency graphs, focused fixtures, valid factory defaults, and explicit overrides keep large test suites understandable and fast.
- **Optimize sharing deliberately:** expensive infrastructure can often be session- or worker-scoped, while mutable business state should remain isolated to the smallest practical boundary.