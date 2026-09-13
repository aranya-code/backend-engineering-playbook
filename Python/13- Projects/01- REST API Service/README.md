# REST API Service

A production-oriented Python REST API service built with FastAPI, SQLAlchemy, and Pydantic. Demonstrates the service-layer, repository pattern, dependency injection, typed request/response schemas, and a layered architecture that separates HTTP concerns from business logic and data access.

---

## Overview

This project implements a user-management REST API that applies the engineering patterns used in real backend services: a thin HTTP layer, a service layer that owns business rules, a repository that abstracts persistence, a domain model that is independent of the framework, and a typed schema layer for request validation and response serialization.

The goal is not to be a feature-complete user service. It is to demonstrate how each architectural layer is separated, tested, and wired together in a production-oriented Python service.

---

## Architecture

```text
HTTP Request
     │
     ▼
FastAPI Routes (src/api/routes.py)
     │  validates input via Pydantic schemas
     │  injects dependencies via FastAPI DI
     ▼
UserService (src/services/user_service.py)
     │  owns business rules
     │  raises domain exceptions
     ▼
UserRepository (src/repositories/user_repository.py)
     │  owns persistence logic
     │  abstracts SQLAlchemy
     ▼
SQLAlchemy / Database
     │
     ▼
HTTP Response
     │  serialized via Pydantic schemas
```

### Layer Responsibilities

| Layer | Module | Responsibility |
|---|---|---|
| **Routes** | `src/api/routes.py` | HTTP routing, input/output schema binding, dependency wiring |
| **Dependencies** | `src/api/dependencies.py` | FastAPI dependency injection (session, service) |
| **Schemas** | `src/schemas/user.py` | Pydantic request/response models — wire format only |
| **Service** | `src/services/user_service.py` | Business rules, validation, orchestration |
| **Repository** | `src/repositories/user_repository.py` | CRUD operations, query logic, SQLAlchemy isolation |
| **Domain Model** | `src/models/user.py` | Core domain entity — independent of framework and persistence |
| **Database** | `src/database/` | Engine, session factory, connection management |
| **Config** | `src/config/settings.py` | Typed settings via Pydantic Settings |

---

## Project Structure

```text
01- REST API Service/
├── config/
│   ├── settings.yaml       # Baseline configuration reference
│   ├── pyproject.toml      # Project metadata and tooling
│   ├── .gitignore
│   └── README.md           # Configuration reference
├── scripts/
│   └── seed_database.py    # Database seed utility
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py
│   │   └── routes.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   └── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── user_repository.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py
│   └── services/
│       ├── __init__.py
│       └── user_service.py
└── tests/
    └── __init__.py
```

---

## Key Concepts Demonstrated

### Service Layer

The `UserService` owns all business rules. It does not know about HTTP, SQLAlchemy, or request schemas:

```python
class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def create_user(self, email: str, name: str) -> User:
        # Business validation
        if self._repository.get_by_email(email) is not None:
            raise ValueError("A user with this email already exists.")
        ...
```

This means business rules can be tested directly — no HTTP client, no database, no test setup beyond a mock repository.

### Repository Pattern

The `UserRepository` is the only layer that knows about SQLAlchemy. The service layer depends on the repository interface, not on ORM internals:

```python
class UserRepository:
    def __init__(self, session: Session) -> None: ...
    def get_by_id(self, user_id: UUID) -> User | None: ...
    def get_by_email(self, email: str) -> User | None: ...
    def create(self, user: User) -> User: ...
    def list_users(self, *, offset: int, limit: int) -> list[User]: ...
    def update(self, user: User) -> User: ...
    def delete(self, user_id: UUID) -> None: ...
```

### Domain Model vs. Schema Separation

`src/models/user.py` is the internal domain entity. It is not a Pydantic model and is not tied to the HTTP wire format.

`src/schemas/user.py` contains the Pydantic models (`UserCreate`, `UserUpdate`, `UserResponse`) that define what the API accepts and returns. This separation means internal representation can evolve independently of the external API contract.

### Dependency Injection

FastAPI's `Depends()` system wires the database session and service into each route without coupling route handlers to construction logic:

```python
@router.post("/users", response_model=UserResponse)
def create_user(
    body: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse: ...
```

### Typed Configuration

Settings are loaded via Pydantic Settings, which validates types at startup and supports environment-variable overrides:

```python
class Settings(BaseSettings):
    database_url: str = "sqlite:///./app.db"
    db_pool_size: int = 10
    log_level: str = "INFO"
```

### Connection Pool Awareness

The project explicitly configures SQLAlchemy's connection pool. In a multi-worker deployment, each worker process has its own pool — so effective total connections = workers × pool size. This is documented and must be accounted for when sizing database capacity.

---

## Configuration

| Setting | Default | Purpose |
|---|---|---|
| `environment` | `development` | Deployment environment name |
| `database.url` | `sqlite:///./app.db` | Database connection string |
| `database.pool.size` | `10` | Connections per pool per process |
| `database.pool.max_overflow` | `20` | Overflow connections above pool size |
| `api.prefix` | `/api` | API route prefix |
| `api.version` | `v1` | API version namespace |
| `logging.level` | `INFO` | Application log level |
| `security.authentication.enabled` | `false` | Enable authentication middleware |

Environment-variable overrides:

```bash
DATABASE_URL="postgresql+psycopg://user:password@db:5432/app"
DB_POOL_SIZE=20
LOG_LEVEL=INFO
```

See [`config/README.md`](config/README.md) for the full configuration reference.

---

## Requirements

- Python ≥ 3.12
- fastapi ≥ 0.115
- pydantic ≥ 2.10
- pydantic-settings ≥ 2.7
- sqlalchemy ≥ 2.0
- uvicorn[standard] ≥ 0.34

---

## Installation

```bash
pip install -e ".[dev]"
```

---

## Running the Service

```bash
# Start with Uvicorn directly
uvicorn src.api.routes:app --host 127.0.0.1 --port 8000

# Seed the database (SQLite)
python scripts/seed_database.py
```

API documentation is available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## Running Tests

```bash
pytest
pytest --cov=src --cov-report=term-missing

# Static analysis
ruff check src tests
mypy src
```

---

## Architecture Principles Applied

| Principle | How it appears here |
|---|---|
| Separation of concerns | HTTP, business rules, and persistence are in distinct layers |
| Dependency injection | Services and sessions injected via FastAPI `Depends()` |
| Domain model independence | `User` entity has no FastAPI or SQLAlchemy coupling |
| Schema isolation | Pydantic schemas define API contracts; domain models define business objects |
| Testability | Business logic tested without HTTP or database setup |
| Configuration as code | Typed settings validated at startup, no scattered `os.getenv()` calls |

---

## Production Considerations

| Concern | Approach |
|---|---|
| Database | Switch `database.url` to PostgreSQL; tune pool size relative to worker count |
| Authentication | Enable and configure authentication in `security` settings |
| CORS | Add allowed origins explicitly in `security.cors` settings |
| Logging | Integrate with centralized logging (CloudWatch, ELK, Datadog) |
| Secrets | Use AWS Secrets Manager, Kubernetes Secrets, or equivalent — never commit credentials |
| Scaling | Run multiple Uvicorn workers; ensure pool × workers fits within database connection limit |

---

## Navigation

| # | Section |
|---|---|
| [01](../01-%20Fundamentals/README.md) | Fundamentals |
| [02](../02-%20Object%20Oriented%20Programming/README.md) | Object Oriented Programming |
| [03](../03-%20Intermediate%20Python/README.md) | Intermediate Python |
| [04](../04-%20Error%20Handling/README.md) | Error Handling |
| [05](../05-%20Files%20and%20Serialization/README.md) | Files and Serialization |
| [06](../06-%20Type%20System/README.md) | Type System |
| [07](../07-%20Dataclasses%20and%20Data%20Modeling/README.md) | Dataclasses and Data Modeling |
| [08](../08-%20Concurrency%20and%20Parallelism/README.md) | Concurrency and Parallelism |
| [09](../09-%20Memory%20and%20Performance/README.md) | Memory and Performance |
| [10](../10-%20Backend%20Python/README.md) | Backend Python |
| [11](../11-%20Testing/README.md) | Testing |
| [12](../12-%20Interview%20Preparation/README.md) | Interview Preparation |
| **13** | **Projects** |
| ↳ [01](README.md) | REST API Service |
| ↳ [02](../02-%20Async%20API%20Client/README.md) | Async API Client |
| ↳ [03](../03-%20Background%20Job%20System/README.md) | Background Job System |
| ↳ [04](../04-%20Concurrent%20Data%20Processor/README.md) | Concurrent Data Processor |
| ↳ [05](../05-%20Webhook%20Processing%20Service/README.md) | Webhook Processing Service |
