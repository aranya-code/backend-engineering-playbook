# 01- Python Project Structure

## Overview

Python project structure defines how application code, infrastructure concerns, configuration, tests, and operational assets are organized within a repository.

A good structure should make it obvious:

- where business logic belongs;
- where HTTP or RPC interfaces live;
- where database access is implemented;
- where configuration comes from;
- how dependencies flow between modules;
- how tests map to production code;
- how the application starts;
- how the system is deployed and operated.

Project structure is not primarily about choosing a fashionable directory layout. It is about creating **clear boundaries and dependency direction** so that a codebase remains understandable as it grows.

A small script can reasonably use:

```text
app.py
```

A production backend with multiple domains, databases, asynchronous workers, APIs, and infrastructure requires stronger organization.

---

## Why Project Structure Matters

Poor structure creates architectural problems gradually.

Typical symptoms include:

- business logic inside route handlers;
- database queries scattered throughout the application;
- circular imports;
- global mutable state;
- configuration accessed everywhere;
- tests that cannot isolate components;
- framework-specific code leaking into domain logic;
- unclear ownership of modules;
- difficult refactoring;
- tightly coupled services.

A good structure provides a boundary between:

```text
Transport
    ↓
Application
    ↓
Domain
    ↓
Infrastructure
```

The exact architecture can vary, but dependency direction should remain intentional.

---

## Project Structure Should Follow Responsibilities

A backend project commonly contains several responsibility categories:

| Responsibility | Examples |
|---|---|
| Transport | HTTP, REST, gRPC, CLI |
| Application | Use cases, orchestration |
| Domain | Business rules, entities, value objects |
| Infrastructure | PostgreSQL, Redis, Kafka, AWS |
| Configuration | Environment and application settings |
| Observability | Logging, metrics, tracing |
| Background processing | Celery, scheduled jobs, consumers |
| Tests | Unit, integration, API, end-to-end |
| Deployment | Docker, Kubernetes, CI/CD |

The structure should make these responsibilities discoverable.

---

## Minimal Python Project

A small library or service may only require:

```text
my-project/
├── pyproject.toml
├── README.md
├── src/
│   └── my_project/
│       ├── __init__.py
│       └── service.py
└── tests/
    └── test_service.py
```

This is appropriate when the application has limited complexity.

Do not introduce a large architectural structure before the problem requires it.

---

## Recommended Backend Structure

A production-oriented backend can use:

```text
my-service/
├── pyproject.toml
├── README.md
├── .gitignore
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── Makefile
│
├── src/
│   └── my_service/
│       ├── __init__.py
│       ├── main.py
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── dependencies.py
│       │   ├── errors.py
│       │   └── routes/
│       │       ├── __init__.py
│       │       ├── users.py
│       │       └── orders.py
│       │
│       ├── application/
│       │   ├── __init__.py
│       │   ├── users/
│       │   │   └── services.py
│       │   └── orders/
│       │       └── services.py
│       │
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── users/
│       │   │   ├── entities.py
│       │   │   └── repositories.py
│       │   └── orders/
│       │       ├── entities.py
│       │       └── repositories.py
│       │
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── database/
│       │   │   ├── models.py
│       │   │   ├── repositories.py
│       │   │   └── session.py
│       │   ├── cache/
│       │   │   └── redis.py
│       │   ├── messaging/
│       │   │   └── kafka.py
│       │   └── external/
│       │       └── clients.py
│       │
│       ├── config/
│       │   └── settings.py
│       │
│       ├── observability/
│       │   ├── logging.py
│       │   ├── metrics.py
│       │   └── tracing.py
│       │
│       └── workers/
│           ├── celery_app.py
│           └── tasks.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── api/
│   └── conftest.py
│
├── migrations/
│
├── scripts/
│
└── deploy/
    ├── Dockerfile
    └── kubernetes/
```

This is a reference architecture rather than a mandatory template. Smaller services should remove directories that do not represent real responsibilities.

---

## `src` Layout

The `src` layout places importable application code under `src/`.

```text
project/
├── pyproject.toml
├── src/
│   └── my_service/
└── tests/
```

This prevents the repository root from accidentally behaving like an installed package during development.

It helps catch packaging and import problems before deployment.

For reusable packages and production services, `src` layout is generally a strong default.

---

## `pyproject.toml`

Modern Python projects should centralize project metadata and tool configuration in `pyproject.toml`.

Example:

```toml
[project]
name = "my-service"
version = "0.1.0"
description = "Production backend service"
requires-python = ">=3.12"
dependencies = [
    "fastapi",
    "uvicorn",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "ruff",
    "mypy",
]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100

[tool.mypy]
strict = true
```

The exact dependency-management strategy may use tools such as:

- `uv`;
- Poetry;
- Hatch;
- PDM;
- pip with a lock/constraints workflow.

The important property is reproducible dependency management.

---

## Application Entry Point

The application entry point should be small.

For FastAPI:

```python
from fastapi import FastAPI

from my_service.api.routes.orders import router as orders_router
from my_service.api.routes.users import router as users_router

app = FastAPI()

app.include_router(users_router)
app.include_router(orders_router)
```

Avoid putting business logic directly into `main.py`.

The entry point should primarily compose the application.

---

## Application Composition

A useful startup flow is:

```mermaid
flowchart TD
    A[Process Starts] --> B[Load Configuration]
    B --> C[Initialize Logging]
    C --> D[Initialize Infrastructure]
    D --> E[Create Application]
    E --> F[Register Routes]
    F --> G[Register Middleware]
    G --> H[Start Server]
```

This keeps initialization responsibilities explicit.

---

## API Layer

The API layer should translate transport-level requests into application operations.

For example:

```python
from fastapi import APIRouter, Depends

from my_service.application.users.services import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/")
async def create_user(
    service: UserService = Depends(),
):
    return await service.create_user()
```

The route should not contain:

- complex business rules;
- raw SQL;
- transaction orchestration;
- large data transformations;
- external-service retry logic.

Its responsibility is primarily:

```text
HTTP request
    ↓
validation
    ↓
authentication / authorization
    ↓
application operation
    ↓
HTTP response
```

---

## Application Layer

The application layer coordinates use cases.

Example:

```python
class UserService:
    def __init__(self, repository):
        self.repository = repository

    async def create_user(self, email: str):
        user = User(email=email)

        await self.repository.save(user)

        return user
```

Application services are useful when a use case coordinates multiple operations.

For example:

```text
Create Order
    ↓
Validate request
    ↓
Load customer
    ↓
Check inventory
    ↓
Create order
    ↓
Persist transaction
    ↓
Publish event
```

The application layer orchestrates that workflow.

---

## Domain Layer

The domain layer contains business concepts and rules that should not depend unnecessarily on infrastructure.

Typical components include:

```text
domain/
├── users/
│   ├── entities.py
│   └── repositories.py
└── orders/
    ├── entities.py
    └── repositories.py
```

Example:

```python
from dataclasses import dataclass


@dataclass
class Order:
    customer_id: int
    total: int

    def can_be_submitted(self) -> bool:
        return self.total > 0
```

The domain model should not need to know whether persistence uses:

- PostgreSQL;
- Redis;
- DynamoDB;
- an in-memory repository.

This improves testability and reduces coupling.

---

## Repository Interfaces

A repository abstraction can define application-facing persistence behavior:

```python
from typing import Protocol


class UserRepository(Protocol):
    async def get_by_id(self, user_id: int):
        ...

    async def save(self, user) -> None:
        ...
```

The infrastructure layer can implement it:

```python
class PostgresUserRepository:
    async def get_by_id(self, user_id: int):
        ...

    async def save(self, user) -> None:
        ...
```

This can be valuable when the domain or application layer should remain independent of a particular persistence implementation.

Do not introduce repository abstractions mechanically. If they only wrap an ORM call without providing a meaningful boundary, they can increase complexity without improving architecture.

---

## Infrastructure Layer

Infrastructure contains integrations with external systems.

Typical examples:

```text
infrastructure/
├── database/
├── cache/
├── messaging/
└── external/
```

Examples:

- PostgreSQL;
- Redis;
- Kafka;
- S3;
- third-party REST APIs;
- gRPC clients;
- SMTP;
- cloud SDKs.

Infrastructure code should own implementation details such as:

- connection management;
- driver configuration;
- serialization;
- retries;
- timeouts;
- provider-specific errors.

---

## Dependency Direction

A strong architectural rule is:

```text
API
 ↓
Application
 ↓
Domain

Infrastructure
 ↑
implements required interfaces
```

Conceptually:

```mermaid
flowchart LR
    API[API / Transport] --> APP[Application]
    APP --> DOMAIN[Domain]
    INFRA[Infrastructure] --> APP
    INFRA --> DOMAIN
```

The exact dependency graph can differ, but infrastructure should not leak unnecessarily into domain logic.

For example, avoid making a domain entity depend directly on a PostgreSQL driver.

---

## Domain-Driven Project Structure

As systems become larger, organizing exclusively by technical layer can become difficult.

This:

```text
services/
repositories/
models/
routes/
```

can eventually produce large directories containing unrelated business domains.

A feature-oriented structure can instead use:

```text
src/my_service/
├── users/
│   ├── api.py
│   ├── service.py
│   ├── models.py
│   ├── repository.py
│   └── schemas.py
│
├── orders/
│   ├── api.py
│   ├── service.py
│   ├── models.py
│   ├── repository.py
│   └── schemas.py
│
└── payments/
    ├── api.py
    ├── service.py
    ├── repository.py
    └── schemas.py
```

This keeps related functionality together.

For larger systems, a hybrid structure is often effective:

```text
src/my_service/
├── users/
│   ├── api/
│   ├── application/
│   ├── domain/
│   └── infrastructure/
│
├── orders/
│   ├── api/
│   ├── application/
│   ├── domain/
│   └── infrastructure/
│
└── shared/
```

The right structure depends on domain boundaries and team ownership.

---

## Layered vs Feature-Oriented Structure

| Structure | Strength | Risk |
|---|---|---|
| Layered | Simple mental model | Related feature code becomes scattered |
| Feature-oriented | Strong domain locality | Boundaries can become inconsistent |
| Hybrid | Balances both | Requires architectural discipline |
| Flat | Very simple for small apps | Degrades quickly as complexity grows |

Use the simplest structure that provides clear boundaries.

---

## Django Project Structure

Django commonly separates the project configuration from domain-oriented applications.

Example:

```text
my_project/
├── manage.py
├── pyproject.toml
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── users/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── tests/
│
└── orders/
    ├── migrations/
    ├── models.py
    ├── views.py
    ├── urls.py
    └── tests/
```

For larger Django systems, additional modules can be introduced:

```text
users/
├── models.py
├── selectors.py
├── services.py
├── serializers.py
├── permissions.py
└── tests/
```

The goal is to prevent `views.py` or `models.py` from becoming an unbounded container for unrelated logic.

---

## FastAPI Project Structure

FastAPI does not impose a single architecture.

A moderate service might use:

```text
src/my_service/
├── main.py
├── api/
│   ├── dependencies.py
│   └── routes/
├── services/
├── repositories/
├── models/
├── schemas/
├── config/
└── infrastructure/
```

For larger services, domain-oriented modules usually scale better than globally shared `services/` and `repositories/` directories.

---

## Schemas vs Domain Models vs Database Models

These concepts should not automatically be represented by one class.

```text
HTTP Request
    ↓
API Schema
    ↓
Domain Model
    ↓
Persistence Model
    ↓
PostgreSQL
```

Each representation serves a different boundary.

| Model | Responsibility |
|---|---|
| API schema | External request/response contract |
| Domain model | Business behavior and invariants |
| Persistence model | Database mapping |
| Event schema | Message contract |

Combining everything into one model can create tight coupling between external APIs, business logic, and database schema.

---

## Configuration Structure

Configuration should have a dedicated boundary.

Example:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "my-service"
    database_url: str
    redis_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
```

Application code should consume validated configuration rather than repeatedly reading environment variables.

Avoid:

```python
import os

DATABASE_URL = os.environ["DATABASE_URL"]
```

throughout dozens of modules.

Centralized configuration improves:

- validation;
- testing;
- observability;
- consistency;
- deployment management.

---

## Environment Files

A repository can safely contain:

```text
.env.example
```

Example:

```dotenv
DATABASE_URL=postgresql://user:password@localhost:5432/app
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
```

Do not commit real secrets.

Production secrets should come from an appropriate secret-management mechanism such as:

- AWS Secrets Manager;
- AWS Systems Manager Parameter Store;
- Kubernetes Secrets with appropriate controls;
- a dedicated secret manager.

---

## Tests Structure

Tests should make intent and scope obvious.

A useful structure is:

```text
tests/
├── unit/
├── integration/
├── api/
└── conftest.py
```

### Unit Tests

Test isolated business behavior.

```text
tests/unit/
    test_order_service.py
```

### Integration Tests

Test interactions with real or test infrastructure.

```text
tests/integration/
    test_postgres_repository.py
    test_redis_cache.py
```

### API Tests

Test HTTP contracts and request/response behavior.

```text
tests/api/
    test_users.py
    test_orders.py
```

The exact test layout should reflect how the team thinks about test boundaries.

---

## Mapping Tests to Production Code

Avoid making the test hierarchy unnecessarily difficult to navigate.

A useful relationship is:

```text
src/my_service/users/
    service.py
    repository.py

tests/
    unit/users/
        test_service.py
    integration/users/
        test_repository.py
```

Tests should communicate what level of system behavior they verify.

---

## Background Workers

Celery workers or Kafka consumers should have explicit ownership.

Example:

```text
src/my_service/
├── workers/
│   ├── celery_app.py
│   ├── tasks.py
│   └── consumers/
│       └── orders.py
```

For domain-heavy systems:

```text
orders/
├── application/
├── domain/
├── infrastructure/
└── workers/
    └── tasks.py
```

Background tasks should call application-level operations rather than duplicating business logic already used by HTTP handlers.

---

## CLI and Management Commands

Operational commands should live in a dedicated area.

```text
scripts/
├── seed_database.py
├── backfill_orders.py
└── export_data.py
```

For Django:

```text
users/
└── management/
    └── commands/
        └── backfill_users.py
```

Scripts should use the same application services as production paths where practical.

Avoid creating a second implementation of business logic specifically for a one-off script.

---

## Database Migrations

Migrations should be treated as deployment artifacts.

Typical locations include:

```text
migrations/
```

or framework-specific migration directories.

Production considerations include:

- backward-compatible schema changes;
- migration ordering;
- transaction behavior;
- long-running migrations;
- lock acquisition;
- deployment sequencing.

A project structure should make migration ownership and execution obvious.

---

## Docker

A Python backend repository commonly contains:

```text
Dockerfile
.dockerignore
```

Example:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir .

CMD ["uvicorn", "my_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Production images should be:

- reproducible;
- minimal;
- non-root where practical;
- free of development-only secrets;
- built from pinned or locked dependencies.

---

## Docker Build Context

A useful `.dockerignore` prevents unnecessary files from entering the build context:

```text
.git
.venv
__pycache__
.pytest_cache
.mypy_cache
.ruff_cache
.env
tests
```

Whether tests are excluded depends on the build strategy, but secrets and local environments should not be copied into production images.

---

## Kubernetes

Deployment configuration may live separately:

```text
deploy/
└── kubernetes/
    ├── deployment.yaml
    ├── service.yaml
    ├── configmap.yaml
    └── ingress.yaml
```

Larger organizations may maintain deployment manifests in a separate infrastructure repository.

The key architectural principle is keeping application code distinct from environment-specific deployment configuration.

---

## CI/CD

CI configuration commonly lives at repository level:

```text
.github/
└── workflows/
    ├── test.yml
    ├── lint.yml
    └── deploy.yml
```

A typical pipeline is:

```text
Commit
  ↓
Lint
  ↓
Type Check
  ↓
Unit Tests
  ↓
Integration Tests
  ↓
Build Image
  ↓
Security Checks
  ↓
Deploy
  ↓
Smoke Tests
```

Project structure should make each stage easy to automate.

---

## Dependency Management

Dependencies should be explicitly declared.

Avoid relying on:

```text
developer machine packages
```

or undocumented global installations.

The project should define:

- runtime dependencies;
- development dependencies;
- Python version;
- lock information or reproducible constraints;
- package metadata.

Reproducibility is particularly important for CI/CD and container builds.

---

## Import Boundaries

Imports should reflect architecture.

Avoid:

```text
domain → API
domain → FastAPI
domain → HTTP client
```

when the domain does not need those dependencies.

Prefer:

```text
API
 ↓
Application
 ↓
Domain

Infrastructure
 ↓
Application / Domain contracts
```

Circular imports are often a design signal.

They can indicate:

- unclear ownership;
- excessive module coupling;
- misplaced responsibilities;
- overly large modules.

---

## `__init__.py`

`__init__.py` can:

- mark package boundaries;
- expose a controlled public API;
- initialize package-level behavior.

Avoid putting substantial application initialization in `__init__.py`.

Prefer explicit imports:

```python
from my_service.users.service import UserService
```

over creating large implicit import surfaces.

---

## Public vs Private Modules

Use naming conventions intentionally.

```text
service.py
_internal.py
```

An underscore communicates that a module or symbol is not intended as part of the public interface.

For reusable libraries, define stable public APIs and avoid forcing consumers to depend on internal module paths.

---

## Shared Modules

Large projects often create:

```text
shared/
common/
utils/
helpers/
```

These directories can become architectural dumping grounds.

Bad:

```text
utils/
├── date.py
├── database.py
├── user.py
├── order.py
├── http.py
└── random_helpers.py
```

Prefer placing functionality near the domain that owns it.

Create shared modules only when the abstraction genuinely has multiple consumers and a stable responsibility.

---

## Avoid God Modules

A module such as:

```text
utils.py
services.py
models.py
helpers.py
```

can grow indefinitely.

Warning signs include:

- hundreds of unrelated functions;
- imports from almost every package;
- frequent merge conflicts;
- unclear ownership;
- difficult unit testing.

Split modules around cohesive responsibilities.

---

## Package Naming

Use valid, predictable Python package names:

```text
my_service
order_processing
payment_gateway
```

Avoid:

```text
my-service
OrderProcessing
miscStuff
```

Repository names can differ from import package names, but the importable package should follow Python naming conventions.

---

## Naming Files by Responsibility

Good:

```text
authentication.py
repositories.py
serialization.py
configuration.py
```

Better when domain context matters:

```text
orders/repository.py
payments/client.py
users/service.py
```

Avoid vague names when a more precise responsibility is available.

---

## Dependency Injection

Project structure should support dependency injection rather than hard-coding infrastructure everywhere.

Example:

```python
class OrderService:
    def __init__(self, repository, publisher):
        self.repository = repository
        self.publisher = publisher
```

Composition happens near the application boundary:

```text
main.py
    ↓
construct dependencies
    ↓
construct services
    ↓
register routes
```

This improves testing and allows infrastructure implementations to change without rewriting business logic.

---

## Request Lifecycle

A well-structured backend commonly follows:

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Service
    participant Domain
    participant Repository
    participant DB

    Client->>API: HTTP request
    API->>Service: validated command
    Service->>Domain: apply business rules
    Service->>Repository: persist entity
    Repository->>DB: SQL
    DB-->>Repository: result
    Repository-->>Service: entity
    Service-->>API: result
    API-->>Client: HTTP response
```

Each layer has a clear responsibility.

This separation becomes especially valuable when the same application operation is invoked by:

- REST;
- gRPC;
- Celery;
- Kafka consumers;
- CLI commands.

---

## REST and gRPC

Transport-specific code should remain at the transport boundary.

```text
REST route ────────┐
                   ├──> Application Service
gRPC handler ──────┘
```

Do not duplicate business rules between REST and gRPC implementations.

Both should call the same application-level operation where appropriate.

---

## Redis and Kafka

Infrastructure integrations should remain isolated.

For example:

```text
application/
    order_service.py

infrastructure/
    cache/
        redis.py
    messaging/
        kafka.py
```

The application layer should express intent:

```text
cache order
publish OrderCreated
```

rather than becoming tightly coupled to Redis or Kafka client APIs.

---

## AWS Integration

AWS-specific implementation should generally be isolated from business logic.

Example:

```text
infrastructure/
└── aws/
    ├── s3.py
    ├── secrets.py
    └── clients.py
```

This allows application code to operate in terms of domain operations rather than provider-specific SDK calls.

It also simplifies:

- testing;
- local development;
- provider migration;
- credential management.

---

## Observability Structure

Cross-cutting operational concerns can have dedicated modules:

```text
observability/
├── logging.py
├── metrics.py
└── tracing.py
```

Observability should be initialized centrally but used intentionally throughout the application.

Examples include:

- request IDs;
- structured logs;
- Prometheus metrics;
- OpenTelemetry traces;
- database latency metrics;
- queue depth metrics.

Avoid scattering custom logging configuration across business modules.

---

## Security Boundaries

Project structure should reinforce security boundaries.

Separate concerns such as:

```text
authentication
authorization
configuration
secrets
external clients
```

Security-sensitive configuration should not be embedded in:

```text
domain/
```

or committed into:

```text
.env
```

The source repository should contain only safe examples and configuration schemas.

---

## Performance Considerations

Project structure can affect performance indirectly.

Poor structure can encourage:

- duplicate database queries;
- repeated serialization;
- unnecessary service layers;
- excessive object conversion;
- circular dependencies;
- expensive module initialization.

However, directory depth itself is not normally a meaningful runtime performance concern.

Optimize runtime behavior based on measurements rather than reducing the number of folders.

---

## Import-Time Performance

Large modules can execute significant work during import.

Avoid:

```python
# Bad pattern
client = create_expensive_client()
load_large_dataset()
initialize_large_cache()
```

at module import time unless there is a deliberate reason.

Prefer explicit application startup initialization.

This improves:

- startup behavior;
- testing;
- CLI execution;
- worker initialization;
- deployment predictability.

---

## Testing Architecture Boundaries

Architecture should be testable.

For example:

```text
Domain
  ↓
fast unit tests

Application
  ↓
unit + integration tests

Infrastructure
  ↓
integration tests

API
  ↓
API tests

Deployment
  ↓
smoke / end-to-end tests
```

If testing a simple business rule requires PostgreSQL, Redis, Kafka, and HTTP infrastructure, the dependency boundary may be too tightly coupled.

---

## Maintainability

A maintainable project structure should answer these questions quickly:

- Where is this business rule?
- Where is this API endpoint?
- Where is this database query?
- Where is this external integration?
- Where is configuration loaded?
- Where are migrations?
- Where are unit tests?
- Where is the application started?
- Where is deployment configured?

If engineers repeatedly search across unrelated directories, the architecture may need restructuring.

---

## Scalability of the Codebase

Codebase scalability is different from runtime scalability.

A repository can have excellent runtime performance but poor organizational scalability.

As teams grow, consider:

- domain ownership;
- module boundaries;
- dependency direction;
- code ownership;
- deployment ownership;
- test ownership.

A useful structure should reduce the number of unrelated modules an engineer must understand to modify one feature.

---

## Monoliths and Microservices

Project structure should not force premature microservices.

A modular monolith can use:

```text
users/
orders/
payments/
notifications/
```

with clear boundaries inside one deployable application.

This can provide many architectural benefits without introducing:

- network calls;
- distributed transactions;
- service discovery;
- independent deployments;
- operational overhead.

Split into microservices when organizational or system requirements justify it.

---

## Modular Monolith

A mature modular monolith might look like:

```text
src/my_service/
├── users/
│   ├── api/
│   ├── application/
│   ├── domain/
│   └── infrastructure/
│
├── orders/
│   ├── api/
│   ├── application/
│   ├── domain/
│   └── infrastructure/
│
├── payments/
│   ├── api/
│   ├── application/
│   ├── domain/
│   └── infrastructure/
│
└── shared/
    ├── configuration/
    └── observability/
```

This creates explicit domain boundaries while retaining a single deployment unit.

---

## Production Repository Example

A mature backend repository may ultimately resemble:

```text
order-service/
├── .github/
│   └── workflows/
│       ├── test.yml
│       └── deploy.yml
│
├── deploy/
│   ├── docker/
│   └── kubernetes/
│
├── migrations/
│
├── scripts/
│
├── src/
│   └── order_service/
│       ├── api/
│       ├── application/
│       ├── domain/
│       ├── infrastructure/
│       ├── config/
│       ├── observability/
│       └── workers/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── api/
│   └── e2e/
│
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── Makefile
├── README.md
└── pyproject.toml
```

The exact directories should be justified by actual responsibilities.

---

## What Belongs in the Repository

| Artifact | Usually committed? | Notes |
|---|---:|---|
| Source code | Yes | Core application |
| Tests | Yes | Part of the product |
| `pyproject.toml` | Yes | Project/tool configuration |
| Lock file | Usually | Depends on dependency workflow |
| Migrations | Yes | Database evolution |
| Dockerfile | Usually | Reproducible deployment |
| CI configuration | Yes | Automated delivery |
| Kubernetes manifests | Often | Depends on infrastructure strategy |
| `.env.example` | Yes | Safe configuration template |
| `.env` | No | May contain secrets |
| Virtual environment | No | Environment-specific |
| Build artifacts | No | Generated |
| Logs | No | Operational data |
| Cache directories | No | Generated |

---

## Architecture Evolution

Do not attempt to design the final architecture on day one.

A reasonable progression is:

```text
Single module
    ↓
Small package
    ↓
Layered application
    ↓
Feature-oriented modules
    ↓
Explicit domain boundaries
    ↓
Modular monolith
    ↓
Microservices where justified
```

The structure should evolve when complexity requires stronger boundaries.

---

## Common Mistakes

### Overengineering Small Projects

Creating ten architectural layers for a small script increases cognitive overhead.

Use the simplest structure that provides clear boundaries.

### Business Logic in Routes

This makes business behavior difficult to reuse and test.

Move meaningful application behavior into services or domain operations.

### Giant `utils.py`

Utilities often become a dumping ground.

Move functionality to the domain or infrastructure component that owns it.

### Global Database Connections

Creating unmanaged connections at import time can create:

- test isolation problems;
- startup issues;
- connection leaks;
- worker lifecycle problems.

Use explicit lifecycle management and connection pools.

### Global Mutable State

Global caches and registries can create concurrency and memory problems.

Keep ownership explicit.

### Circular Imports

Circular imports usually indicate poor module boundaries.

Refactor responsibilities rather than relying on import tricks.

### Mixing Framework and Domain Logic

A domain object that directly depends on FastAPI or Django internals becomes difficult to reuse and test.

### Duplicate Business Logic

If REST, gRPC, Celery, and CLI paths each implement the same business rule independently, they will eventually diverge.

### Excessive Abstractions

Not every database call needs:

```text
interface
factory
adapter
service
manager
repository
facade
```

Add abstractions when they create meaningful boundaries.

---

## Production Pitfalls

### Configuration Scattered Everywhere

Reading environment variables throughout the application makes configuration inconsistent and difficult to validate.

### Secrets in Source Control

Never commit production credentials, API keys, private certificates, or database passwords.

### Import-Time Side Effects

Expensive initialization during import can make workers, tests, and CLI commands unpredictable.

### Framework-Centric Architecture

When every component depends directly on Django or FastAPI, replacing or isolating framework behavior becomes difficult.

### Shared Module Coupling

A heavily imported `common` package can become a dependency bottleneck that makes every change risky.

### Incorrect Test Boundaries

A test suite that mocks everything can miss integration problems. A suite that requires every external system for every test becomes slow and fragile.

### Deployment Configuration Drift

Application configuration, Docker configuration, Kubernetes configuration, and CI/CD configuration must agree on:

- environment variables;
- ports;
- health checks;
- resource limits;
- startup commands.

---

## Best Practices

- Use `src` layout for substantial applications and reusable packages.
- Keep `pyproject.toml` as the central project configuration surface.
- Keep the application entry point small.
- Organize code around clear responsibilities.
- Prefer domain boundaries as the codebase grows.
- Keep transport logic separate from business logic.
- Keep infrastructure integrations isolated.
- Centralize configuration loading and validation.
- Keep secrets outside source control.
- Use dependency injection where it improves testability and boundaries.
- Keep queues, caches, database clients, and external clients lifecycle-aware.
- Keep tests organized by behavioral boundary.
- Reuse application logic across REST, gRPC, Celery, Kafka, and CLI entry points.
- Avoid generic dumping-ground modules such as `utils.py` and `common.py`.
- Avoid premature abstractions.
- Make dependency direction explicit.
- Keep deployment configuration reproducible.
- Treat migrations as versioned production artifacts.
- Design for observability from the beginning.
- Evolve structure as domain and team complexity increases.

---

## Project Structure Checklist

### Source Code

- [ ] Application code has a clear package root.
- [ ] Entry point is small and explicit.
- [ ] Business logic is not embedded in HTTP handlers.
- [ ] Infrastructure dependencies have clear ownership.
- [ ] Domain boundaries are visible.
- [ ] Circular dependencies are avoided.
- [ ] Shared modules have explicit responsibilities.

### Configuration

- [ ] Configuration is centralized.
- [ ] Configuration is validated at startup.
- [ ] `.env.example` contains only safe example values.
- [ ] Production secrets are managed externally.
- [ ] Environment-specific configuration is explicit.

### Testing

- [ ] Unit tests are fast and isolated.
- [ ] Integration tests cover important infrastructure boundaries.
- [ ] API tests cover external contracts.
- [ ] End-to-end tests cover critical workflows.
- [ ] Test fixtures do not hide important production behavior.

### Operations

- [ ] Logging is structured.
- [ ] Metrics are available for critical resources.
- [ ] Tracing exists where distributed debugging requires it.
- [ ] Health and readiness checks are defined.
- [ ] Docker builds are reproducible.
- [ ] Kubernetes resource requirements are defined where applicable.
- [ ] CI/CD validates and builds the application.
- [ ] Database migrations are version-controlled.

### Architecture

- [ ] Dependency direction is intentional.
- [ ] Transport, application, domain, and infrastructure concerns are separated where justified.
- [ ] Business logic is reusable across entry points.
- [ ] Abstractions exist because they provide real architectural value.
- [ ] Project complexity matches application complexity.

## Key Takeaways

- **Project structure is an architectural boundary:** organize code around responsibilities and domain ownership rather than arbitrary directory conventions.
- **Keep dependency direction intentional:** transport should invoke application behavior, while infrastructure details should not unnecessarily leak into domain logic.
- **Optimize for codebase scalability:** modularity, clear ownership, test boundaries, and cohesive modules become increasingly important as the application and engineering team grow.
- **Avoid both extremes:** a flat `utils.py`-style codebase becomes unmaintainable, while excessive layers and abstractions create unnecessary complexity.
- **Treat structure as evolutionary:** start simple, establish clear boundaries, and introduce modular architecture as domain, operational, and team complexity requires it.