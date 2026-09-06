# README

## Overview

The `11- Testing` section covers the engineering practices required to build reliable, maintainable, and production-ready Python systems.

Testing is treated as an engineering discipline rather than a collection of test commands. The focus is on understanding **what to test, where to test it, how to isolate dependencies, how to validate real infrastructure behavior, and how to build confidence without creating an unnecessarily slow or brittle test suite**.

The section progresses from testing fundamentals through pytest, fixtures, mocking, asynchronous testing, integration testing, API and database testing, isolation, coverage, and overall testing strategy.

```text
                         Python Testing
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
          Test Core       Test Tools       Test Design
             │                │                │
             ▼                ▼                ▼
       Fundamentals      unittest/pytest   Fixtures/Mocks
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                    Integration Boundaries
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
           Database           API           Async/Messaging
              │               │                │
              └───────────────┼────────────────┘
                              ▼
                       Isolation + Coverage
                              │
                              ▼
                     Testing Strategy
```

---

## Navigation

| # | File | Topic |
|---|---|---|
| 01 | [Testing Fundamentals](01-%20Testing%20Fundamentals.md) | Testing purpose, test pyramid, AAA pattern, isolation, fixtures, mocks |
| 02 | [unittest](02-%20unittest.md) | `TestCase`, discovery, assertions, setup/teardown, async testing |
| 03 | [pytest](03-%20pytest.md) | Primary framework: fixtures, markers, parametrization, `conftest.py` |
| 04 | [Test Discovery](04-%20Test%20Discovery.md) | Collection vs execution, naming conventions, node IDs, monorepos |
| 05 | [Assertions](05-%20Assertions.md) | Equality, exceptions, API/database/mock assertions, behavioral contracts |
| 06 | [Fixtures](06-%20Fixtures.md) | Fixture scopes, `yield`, cleanup, `conftest.py`, database/Redis fixtures |
| 07 | [Parametrization](07-%20Parametrization.md) | `pytest.mark.parametrize`, boundary testing, fixture parametrization |
| 08 | [Mocking](08-%20Mocking.md) | Test doubles: stubs, fakes, spies, mocks, patching strategy |
| 09 | [unittest.mock](09-%20unittest.mock.md) | `Mock`, `MagicMock`, `AsyncMock`, `patch`, `create_autospec` reference |
| 10 | [patch and patch.object](10-%20patch%20and%20patch.object.md) | Name lookup rules, patching imported functions, async patching |
| 11 | [MagicMock](11-%20MagicMock.md) | Magic methods, protocol mocking, context managers, async iterators |
| 12 | [Dependency Mocking](12-%20Dependency%20Mocking.md) | DI, protocols, FastAPI overrides, Django boundaries, concurrency mocking |
| 13 | [Testing Exceptions](13-%20Testing%20Exceptions.md) | `pytest.raises`, exception chaining, API error translation, retryable errors |
| 14 | [Testing Async Code](14-%20Testing%20Async%20Code.md) | `pytest.mark.asyncio`, `AsyncMock`, TaskGroup, cancellation, streaming |
| 15 | [Integration Testing](15-%20Integration%20Testing.md) | Real dependencies: PostgreSQL, Redis, Kafka, Docker, CI/CD |
| 16 | [API Testing](16-%20API%20Testing.md) | HTTP/RPC contracts, auth, validation, status codes, FastAPI, Django |
| 17 | [Database Testing](17-%20Database%20Testing.md) | Isolation strategies, constraints, transactions, ORM, connection pools |
| 18 | [Test Isolation](18-%20Test%20Isolation.md) | Test independence, state cleanup, parallel-safe suites |
| 19 | [Test Fixtures and Factories](19-%20Test%20Fixtures%20and%20Factories.md) | `factory_boy`, build vs create, nested factories, async factories |
| 20 | [Code Coverage](20-%20Code%20Coverage.md) | `coverage.py`, `pytest-cov`, thresholds, exclusions, CI integration |
| 21 | [Testing Strategies](21-%20Testing%20Strategies.md) | Pyramid strategy, risk-based testing, mutation testing, CI/CD |

---

## Section Structure

```text
11- Testing/
│
├── 01- Testing Fundamentals.md
├── 02- unittest.md
├── 03- pytest.md
├── 04- Test Discovery.md
├── 05- Assertions.md
├── 06- Fixtures.md
├── 07- Parametrization.md
├── 08- Mocking.md
├── 09- unittest.mock.md
├── 10- patch and patch.object.md
├── 11- MagicMock.md
├── 12- Dependency Mocking.md
├── 13- Testing Exceptions.md
├── 14- Testing Async Code.md
├── 15- Integration Testing.md
├── 16- API Testing.md
├── 17- Database Testing.md
├── 18- Test Isolation.md
├── 19- Test Fixtures and Factories.md
├── 20- Code Coverage.md
├── 21- Testing Strategies.md
└── README.md
```

---

## Testing Philosophy

The objective of testing is not to maximize:

- test count;
- code coverage percentage;
- number of mocks;
- number of assertions;
- number of end-to-end scenarios.

The objective is to provide **appropriate confidence for the risk being tested**.

A useful principle is:

> Test behavior at the lowest-cost layer that provides sufficient confidence, then use broader tests where real integration or system behavior matters.

For example:

```text
Pure business rule
       │
       ▼
Unit test

SQL correctness
       │
       ▼
Database integration test

HTTP contract
       │
       ▼
API test

Cross-service compatibility
       │
       ▼
Contract test

Critical business workflow
       │
       ▼
E2E test
```

---

## Test Layers

The playbook uses multiple testing layers.

| Layer | Primary purpose | Typical dependencies | Speed |
|---|---|---|---|
| Unit | Isolated behavior | None or mocks | Very fast |
| Component | Application composition | Controlled dependencies | Fast |
| Integration | Real dependency semantics | PostgreSQL, Redis, Kafka, etc. | Moderate |
| API | External HTTP/RPC behavior | Application + selected infrastructure | Moderate |
| Contract | Service compatibility | Provider/consumer interfaces | Moderate |
| E2E | Complete workflows | Full environment | Slow |
| Performance | Latency and capacity | Production-like environment | Expensive |
| Security | Security properties | Application/environment | Variable |

These layers are complementary.

A unit test cannot replace a PostgreSQL integration test when PostgreSQL-specific transaction or constraint behavior matters.

An E2E test should not replace dozens of fast unit tests for a simple business rule.

---

## Documentation Map

### Testing Fundamentals

**`01- Testing Fundamentals.md`**

Establishes the foundation for testing Python systems.

Covers:

- testing purpose;
- test pyramid;
- test types;
- Arrange/Act/Assert;
- deterministic tests;
- isolation;
- fixtures;
- factories;
- mocks and fakes;
- integration and API testing;
- database and message testing;
- coverage;
- CI/CD;
- security and reliability testing.

Use this as the starting point for the section.

---

### unittest

**`02- unittest.md`**

Covers Python's standard-library testing framework.

Topics include:

- `TestCase`;
- test discovery;
- assertions;
- fixtures;
- setup and teardown;
- cleanup;
- test suites;
- loaders;
- runners;
- `TestResult`;
- skipping;
- `subTest`;
- `unittest.mock`;
- async testing;
- integration testing;
- CI/CD.

It is particularly useful when working with existing codebases built around the standard library.

---

### pytest

**`03- pytest.md`**

Covers pytest as the primary modern Python testing framework.

Topics include:

- test discovery;
- assertions;
- fixtures;
- fixture scopes;
- parametrization;
- markers;
- `conftest.py`;
- dependency injection;
- mocking;
- async testing;
- API testing;
- database testing;
- integration testing;
- CI/CD;
- coverage;
- performance and reliability.

pytest is the main framework used for the practical testing patterns in this section.

---

### Test Discovery

**`04- Test Discovery.md`**

Explains how test frameworks identify tests.

Topics include:

- collection vs execution;
- pytest naming conventions;
- `test_*.py`;
- `*_test.py`;
- test classes and functions;
- `testpaths`;
- `python_files`;
- `python_functions`;
- `python_classes`;
- root directory;
- node IDs;
- `--collect-only`;
- collection errors;
- import behavior;
- monorepos;
- CI diagnostics;
- custom collection.

Understanding discovery is important when tests unexpectedly do not run.

---

### Assertions

**`05- Assertions.md`**

Covers assertions as executable behavioral contracts.

Topics include:

- equality;
- identity;
- `None`;
- collections;
- nested structures;
- exceptions;
- API responses;
- database state;
- mock interactions;
- floating-point comparisons;
- `Decimal`;
- datetime assertions;
- assertion helpers;
- negative testing;
- idempotency;
- concurrency;
- async behavior.

The emphasis is on asserting meaningful behavior rather than implementation details.

---

### Fixtures

**`06- Fixtures.md`**

Explains pytest fixtures and dependency injection.

Topics include:

- fixture creation;
- dependency resolution;
- fixture scopes;
- `yield`;
- cleanup;
- finalizers;
- fixture factories;
- `conftest.py`;
- autouse fixtures;
- `tmp_path`;
- `monkeypatch`;
- database fixtures;
- Redis;
- Kafka;
- HTTP clients;
- authentication;
- parallel testing.

The central design principle is:

> Fixtures should make dependencies and resource ownership explicit.

---

### Parametrization

**`07- Parametrization.md`**

Covers pytest parametrization for testing multiple scenarios efficiently.

Topics include:

- `pytest.mark.parametrize`;
- expected results;
- `pytest.param`;
- IDs;
- exceptions;
- boundary testing;
- equivalence classes;
- API scenarios;
- authorization;
- state transitions;
- serialization;
- fixture parametrization;
- indirect parametrization;
- Cartesian-product risks.

Parametrization is particularly useful when many inputs exercise the same behavioral contract.

---

### Mocking

**`08- Mocking.md`**

Introduces test doubles and mocking strategy.

Covers:

- dummy objects;
- stubs;
- fakes;
- spies;
- mocks;
- `Mock`;
- `MagicMock`;
- `AsyncMock`;
- `spec`;
- `spec_set`;
- `autospec`;
- return values;
- side effects;
- interaction assertions;
- patching;
- external HTTP;
- databases;
- Redis;
- Kafka;
- Celery;
- AWS dependencies.

The key principle is to isolate dependencies without creating unrealistic tests.

---

### unittest.mock

**`09- unittest.mock.md`**

Provides deeper coverage of Python's `unittest.mock` implementation.

Topics include:

- `Mock`;
- `MagicMock`;
- `AsyncMock`;
- `call`;
- `method_calls`;
- `mock_calls`;
- `spec`;
- `spec_set`;
- `create_autospec`;
- `patch`;
- `patch.object`;
- `patch.dict`;
- `patch.multiple`;
- `new`;
- `new_callable`;
- `create=True`;
- property patching;
- class patching;
- async behavior;
- context managers;
- iterators;
- concurrency;
- cleanup.

This file is the detailed reference when mock behavior itself becomes important.

---

### patch and patch.object

**`10- patch and patch.object.md`**

Explains Python patching and, most importantly, Python name lookup.

The critical rule is:

> Patch the name where the code under test looks it up, not necessarily where the dependency was originally defined.

Topics include:

- `patch`;
- `patch.object`;
- context managers;
- decorators;
- manual patchers;
- constructors;
- imported functions;
- builtins;
- environment variables;
- `patch.dict`;
- async patching;
- classes;
- properties;
- `autospec`;
- `spec_set`;
- `create=True`.

This is one of the most important concepts for avoiding misleading mocks.

---

### MagicMock

**`11- MagicMock.md`**

Covers `MagicMock` and Python protocol/magic-method behavior.

Topics include:

- `__len__`;
- `__getitem__`;
- `__setitem__`;
- `__contains__`;
- `__iter__`;
- context managers;
- async context managers;
- async iterators;
- numeric protocols;
- comparison behavior;
- file-like objects;
- HTTP responses;
- database cursors;
- Redis clients;
- Kafka clients;
- Celery;
- AWS clients.

The main caution is to avoid using `MagicMock` where a simple value, `Mock`, fake, or real object would provide a more realistic test.

---

### Dependency Mocking

**`12- Dependency Mocking.md`**

Focuses on isolating application dependencies.

Topics include:

- dependency injection;
- constructor injection;
- protocols;
- patching;
- import semantics;
- mock specifications;
- external HTTP;
- PostgreSQL;
- Redis;
- Kafka;
- Celery;
- AWS;
- filesystem;
- environment;
- authentication;
- FastAPI dependency overrides;
- Django boundaries;
- transactions;
- retries;
- idempotency;
- concurrency.

The goal is to make application behavior testable without coupling tests to unnecessary infrastructure.

---

### Testing Exceptions

**`13- Testing Exceptions.md`**

Covers failure behavior as part of the application contract.

Topics include:

- `pytest.raises`;
- exception types;
- exception messages;
- structured exception attributes;
- custom exception hierarchies;
- exception chaining;
- `__cause__`;
- `__context__`;
- cleanup;
- API error translation;
- FastAPI;
- Django;
- gRPC;
- PostgreSQL;
- Redis;
- Kafka;
- Celery;
- retryable vs non-retryable errors;
- async cancellation;
- background tasks.

Reliable systems must test not only how operations succeed, but how they fail and recover.

---

### Testing Async Code

**`14- Testing Async Code.md`**

Covers testing of asyncio-based Python applications.

Topics include:

- async test execution;
- `pytest.mark.asyncio`;
- `AsyncMock`;
- await assertions;
- async context managers;
- async iterators;
- FastAPI;
- Django async;
- async PostgreSQL;
- async Redis;
- gRPC;
- concurrent tasks;
- timeouts;
- cancellation;
- `TaskGroup`;
- `ExceptionGroup`;
- task cleanup;
- streaming;
- queues;
- backpressure;
- race conditions.

A central principle is:

> Async tests must explicitly own and clean up the tasks and resources they create.

---

### Integration Testing

**`15- Integration Testing.md`**

Covers tests that validate interactions between multiple components using real or production-representative boundaries.

Topics include:

- test environments;
- PostgreSQL;
- migrations;
- constraints;
- transactions;
- connection pools;
- Redis;
- Kafka;
- HTTP;
- FastAPI;
- authentication;
- multi-tenancy;
- gRPC;
- external services;
- Docker;
- CI/CD;
- parallel testing;
- test data;
- cache-aside;
- outbox patterns;
- Celery;
- webhooks.

Integration testing is where infrastructure semantics that mocks cannot reproduce should be validated.

---

### API Testing

**`16- API Testing.md`**

Covers testing of externally visible HTTP and RPC interfaces.

Topics include:

- request lifecycle;
- Nginx/load balancers;
- authentication;
- authorization;
- validation;
- status codes;
- schemas;
- serialization;
- CRUD behavior;
- persistence;
- idempotency;
- pagination;
- filtering;
- sorting;
- error contracts;
- dependency failures;
- FastAPI;
- Django;
- OpenAPI;
- versioning;
- rate limiting;
- payload limits;
- streaming;
- WebSockets;
- performance.

API tests should validate the contract consumers actually depend on.

---

### Database Testing

**`17- Database Testing.md`**

Covers testing persistence and database semantics.

Topics include:

- test database isolation;
- transaction rollback;
- truncation;
- schema-per-worker;
- database-per-worker;
- disposable databases;
- migrations;
- repository testing;
- unique constraints;
- foreign keys;
- check constraints;
- PostgreSQL data types;
- JSONB;
- timezone behavior;
- `Decimal`;
- joins;
- N+1 queries;
- indexes;
- transactions;
- isolation levels;
- row locks;
- deadlocks;
- optimistic locking;
- triggers;
- ORM behavior;
- connection pools;
- factories;
- CI/CD.

A key principle is:

> If production depends on PostgreSQL semantics, test those semantics against PostgreSQL.

---

### Test Isolation

**`18- Test Isolation.md`**

Explains how to prevent tests from influencing one another.

Covers:

- test independence;
- fixture isolation;
- cleanup;
- database transactions;
- truncation;
- worker isolation;
- Redis keys;
- Kafka topics;
- filesystem state;
- environment variables;
- global state;
- mocks;
- caches;
- time;
- randomness;
- UUIDs;
- background tasks;
- threads;
- processes;
- parallel execution;
- Docker;
- Kubernetes;
- AWS resources.

Isolation is essential for deterministic and parallel-safe test suites.

---

### Test Fixtures and Factories

**`19- Test Fixtures and Factories.md`**

Explains the distinction and interaction between test infrastructure and test data.

Core model:

```text
Fixture
  │
  ├── dependency injection
  ├── lifecycle
  ├── setup
  └── cleanup

Factory
  │
  ├── valid defaults
  ├── unique data
  ├── overrides
  └── optional persistence
```

Topics include:

- fixture scopes;
- yield fixtures;
- fixture factories;
- `conftest.py`;
- database fixtures;
- domain factories;
- `build` vs `create`;
- nested factories;
- factory graphs;
- API payload factories;
- authentication;
- async factories;
- `factory_boy`;
- deterministic data;
- parallel-safe data;
- fixture ownership.

The recommended separation is:

> Fixtures manage resources; factories create data.

---

### Code Coverage

**`20- Code Coverage.md`**

Covers coverage measurement and interpretation.

Topics include:

- line coverage;
- branch coverage;
- coverage.py;
- pytest-cov;
- `pyproject.toml`;
- coverage thresholds;
- exclusions;
- `pragma: no cover`;
- CI integration;
- differential coverage;
- async coverage;
- multiprocessing;
- subprocesses;
- API coverage;
- database coverage;
- Kafka coverage;
- security paths;
- performance overhead.

The central principle is:

> Coverage is a diagnostic signal for identifying untested code paths, not a direct measure of test quality.

---

### Testing Strategies

**`21- Testing Strategies.md`**

Provides the broader engineering strategy for designing a complete test suite.

Topics include:

- testing pyramid;
- unit tests;
- component tests;
- integration tests;
- API tests;
- contract tests;
- E2E tests;
- smoke tests;
- regression tests;
- boundary testing;
- state transitions;
- authorization;
- multi-tenancy;
- idempotency;
- retries;
- transactions;
- external services;
- Kafka;
- Redis;
- Celery;
- async systems;
- property-based testing;
- mutation testing;
- concurrency;
- security;
- reliability;
- performance;
- CI/CD;
- risk-based testing.

The key strategic principle is:

> Choose the lowest-cost test layer that provides sufficient confidence, then add broader tests where integration, compatibility, deployment, or business risk requires them.

---

## Recommended Learning Order

The files are numbered to provide a progressive path.

### Foundation

Start with:

```text
01- Testing Fundamentals
02- unittest
03- pytest
04- Test Discovery
05- Assertions
```

This establishes the testing model, frameworks, discovery, and behavioral assertions.

### Test Construction

Continue with:

```text
06- Fixtures
07- Parametrization
08- Mocking
09- unittest.mock
10- patch and patch.object
11- MagicMock
12- Dependency Mocking
```

This section focuses on constructing maintainable and isolated tests.

### Failure and Async Behavior

Then study:

```text
13- Testing Exceptions
14- Testing Async Code
```

These are particularly important for backend systems where failures, cancellation, timeouts, and asynchronous dependencies are normal operating conditions.

### Real Infrastructure

Next:

```text
15- Integration Testing
16- API Testing
17- Database Testing
18- Test Isolation
```

This moves testing from isolated application behavior toward production-like system boundaries.

### Test Engineering

Finish with:

```text
19- Test Fixtures and Factories
20- Code Coverage
21- Testing Strategies
```

These topics address maintainability, measurement, governance, and overall testing architecture.

---

## Core Testing Architecture

A production Python backend should generally follow this model:

```text
                         Production System
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
             ▼                  ▼                  ▼
        Business Logic       APIs             Infrastructure
             │                  │                  │
             ▼                  ▼                  ▼
          Unit Tests         API Tests       Integration Tests
             │                  │                  │
             └──────────────────┼──────────────────┘
                                ▼
                         Contract Tests
                                │
                                ▼
                           E2E Tests
                                │
                                ▼
                       Deployment / Smoke
```

Each layer provides a different type of confidence.

---

## Backend Testing Boundaries

For a typical Python backend:

```text
                     Client
                       │
                       ▼
                 Nginx / LB
                       │
                       ▼
                FastAPI / Django
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Auth          Service      Validation
                       │
                       ▼
                  Repository
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
        PostgreSQL    Redis     Kafka
             │                   │
             │                   ▼
             │                Celery
             │                   │
             └───────────────────┘
```

Testing should align with these boundaries.

For example:

| Boundary | Preferred test |
|---|---|
| Business rule | Unit |
| Service composition | Component |
| HTTP contract | API |
| PostgreSQL behavior | Integration |
| Redis semantics | Integration |
| Kafka processing | Integration |
| Service compatibility | Contract |
| Full workflow | E2E |
| Deployment health | Smoke |

---

## Test Isolation Principles

A reliable test suite should satisfy:

```text
Independent
     +
Deterministic
     +
Repeatable
     +
Parallel-safe
     +
Clean
     =
Trustworthy Test Suite
```

Tests should not depend on:

- execution order;
- previous test state;
- developer machine state;
- production infrastructure;
- uncontrolled wall-clock timing;
- random values without reproducibility;
- leaked background tasks.

---

## Fixtures and Factories

A useful mental model:

```text
                 Test
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
    Fixtures             Factories
        │                   │
        ▼                   ▼
 Infrastructure          Test Data
        │                   │
 ┌──────┼──────┐       ┌────┼────┐
 ▼      ▼      ▼       ▼    ▼    ▼
DB    Redis   HTTP    User Order Payment
```

This separation keeps resource lifecycle independent from business-data construction.

---

## Mocking Strategy

Use mocks selectively.

```text
Can behavior be tested without dependency?
          │
       Yes ─────────────► Unit test
          │
          No
          ▼
Does dependency semantics matter?
          │
       Yes ─────────────► Integration test
          │
          No
          ▼
Use controlled mock/fake
```

Prefer real dependencies when their behavior is central to correctness.

Avoid mocking an entire application into a test that only verifies that mocks returned expected values.

---

## Coverage Strategy

Coverage should support the testing strategy:

```text
Tests
 │
 ├── Unit
 ├── Component
 ├── Integration
 ├── API
 └── E2E
      │
      ▼
Coverage Measurement
      │
      ▼
Missing-path Analysis
      │
      ▼
Risk-based Test Improvements
```

A high coverage percentage is useful only when accompanied by meaningful assertions and appropriate integration coverage.

---

## CI/CD Strategy

A production-oriented pipeline can use progressively broader tests:

```text
Pull Request
     │
     ▼
Lint + Type Check
     │
     ▼
Fast Unit Tests
     │
     ▼
Component / API Tests
     │
     ▼
Integration Tests
     │
     ▼
Coverage + Quality Gates
     │
     ▼
Contract Tests
     │
     ▼
Build Container
     │
     ▼
Deployment Validation
     │
     ▼
Smoke / Critical E2E
```

The pipeline should optimize for both:

- fast developer feedback;
- sufficient deployment confidence.

---

## Test Environment Strategy

Use different environments for different confidence levels.

| Environment | Main purpose |
|---|---|
| Local | Fast development |
| CI | Repeatable automated validation |
| Integration | Real infrastructure semantics |
| Staging | Production-like system validation |
| Production | Health, smoke, and operational validation |

Avoid making local development depend on an unnecessarily large distributed environment.

At the same time, ensure CI or staging tests the infrastructure semantics that cannot be reproduced locally.

---

## Production Concerns

Testing strategy should account for production characteristics.

### Reliability

Test:

- retries;
- timeouts;
- idempotency;
- duplicate messages;
- transaction rollback;
- dependency failures;
- graceful shutdown.

### Security

Test:

- authentication;
- authorization;
- tenant isolation;
- input validation;
- token expiration;
- privilege boundaries;
- sensitive-data exposure.

### Scalability

Test where appropriate:

- concurrency;
- connection pools;
- queue throughput;
- pagination;
- database query performance;
- memory usage.

### Observability

Validate important:

- error classification;
- metrics;
- traces;
- structured logs.

### High Availability

Test behavior around:

- dependency failure;
- worker restart;
- service restart;
- database failover where practical;
- retry and recovery.

### Disaster Recovery

For critical systems, test:

- backup restoration;
- infrastructure recreation;
- configuration recovery;
- database recovery;
- application recovery.

---

## Common Anti-Patterns

### The Test Count Metric

More tests do not automatically mean more confidence.

### The Coverage Metric

High coverage does not guarantee correct assertions.

### The Mock Everything Strategy

Mocks can hide integration defects.

### The E2E Everything Strategy

Large E2E suites become slow and difficult to diagnose.

### The Giant Fixture

Large hidden setup creates coupling and slows the suite.

### The Shared Mutable Fixture

Shared state creates order-dependent failures.

### The Random Data Everywhere Strategy

Uncontrolled randomness makes failures difficult to reproduce.

### The Retry Until Green Strategy

Repeated retries can hide flaky tests and real defects.

### The Sleep-Based Synchronization Strategy

Arbitrary sleeps create slow and nondeterministic async tests.

### The Production Database Test Strategy

Automated tests must never accidentally target production infrastructure.

---

## Testing Decision Framework

When adding a test, ask:

1. **What behavior am I protecting?**
2. **What failure would this test detect?**
3. **What is the lowest-cost layer that can validate it?**
4. **Does the behavior depend on real infrastructure semantics?**
5. **What state must be isolated?**
6. **Does the test need deterministic time or randomness?**
7. **Can it safely run in parallel?**
8. **Does the test assert behavior rather than implementation details?**
9. **Will a future engineer understand why this test exists?**
10. **Does this test improve production confidence enough to justify its maintenance cost?**

---

## Recommended Test Suite Characteristics

A mature Python backend test suite should be:

| Characteristic | Expected behavior |
|---|---|
| Fast | Common developer feedback is quick |
| Deterministic | Same code produces predictable results |
| Isolated | Tests do not depend on one another |
| Parallel-safe | Tests can run concurrently |
| Layered | Different test types cover different risks |
| Realistic | Important infrastructure semantics are tested |
| Maintainable | Fixtures and factories remain understandable |
| Observable | Failures are easy to diagnose |
| Secure | No production secrets or data |
| CI-friendly | Failures produce reliable pipeline results |

---

## Practical Tooling

Common commands for this section include:

```bash
pytest
```

```bash
pytest -q
```

```bash
pytest -x
```

```bash
pytest -k "order"
```

```bash
pytest -m integration
```

```bash
pytest --collect-only
```

```bash
pytest --cov=src --cov-report=term-missing
```

For unittest:

```bash
python -m unittest
```

```bash
python -m unittest discover
```

The exact commands depend on repository configuration.

---

## Relationship to Other Python Sections

Testing depends on concepts introduced elsewhere in the Python Forge Playbook.

```text
01- Fundamentals
       │
       ▼
02- OOP
       │
       ▼
03- Intermediate Python
       │
       ▼
04- Error Handling
       │
       ▼
05- Files / Serialization
       │
       ▼
06- Type System
       │
       ▼
07- Data Modeling
       │
       ▼
08- Concurrency
       │
       ▼
09- Memory / Performance
       │
       ▼
10- Backend Python
       │
       ▼
11- Testing
       │
       ▼
12- Interview Preparation
```

Testing should therefore be used to reinforce concepts from the earlier sections rather than treated as an isolated topic.

Examples:

- exceptions → exception testing;
- asyncio → async testing;
- dataclasses → factory design;
- type protocols → dependency mocking;
- databases → integration testing;
- HTTP → API testing;
- concurrency → race-condition testing;
- performance → performance testing.

---

## Senior Engineering Perspective

At a senior level, testing becomes an architectural concern.

Good testability usually correlates with:

- explicit dependencies;
- clear boundaries;
- small cohesive components;
- deterministic behavior;
- controlled side effects;
- well-defined domain invariants;
- observable failures.

Difficult-to-test code can indicate production design problems.

For example:

```text
Global state
     +
Hidden dependencies
     +
Large service objects
     +
Direct infrastructure calls
     +
Implicit side effects
     │
     ▼
Difficult tests
     │
     ▼
Slow / brittle feedback
```

Improving testability can therefore improve the production architecture itself.

---

## Recommended Engineering Standard

For production Python services:

- Use pytest for modern test suites unless project constraints require another framework.
- Keep unit tests fast and deterministic.
- Use fixtures for dependency and lifecycle management.
- Use factories for realistic, isolated test data.
- Use mocks only where isolation or interaction verification provides value.
- Test real PostgreSQL semantics with PostgreSQL.
- Test real Redis/Kafka behavior where their semantics affect correctness.
- Test HTTP and RPC contracts explicitly.
- Test authentication and authorization independently.
- Test retries, timeouts, idempotency, and failure paths.
- Treat async cancellation and cleanup as testable behavior.
- Keep tests isolated and parallel-safe.
- Use coverage to find blind spots rather than optimize a vanity percentage.
- Keep E2E tests limited to critical workflows.
- Make CI failures deterministic and actionable.
- Never allow automated tests to use production credentials or production data.

---

## Section Completion Checklist

Before considering the testing section complete, verify that you understand:

### Foundations

- [ ] Unit vs component vs integration vs API vs E2E
- [ ] Arrange/Act/Assert
- [ ] Deterministic testing
- [ ] Test discovery
- [ ] Assertions

### pytest

- [ ] Fixtures
- [ ] Fixture scopes
- [ ] `conftest.py`
- [ ] Parametrization
- [ ] Markers
- [ ] Test selection

### Mocking

- [ ] `Mock`
- [ ] `MagicMock`
- [ ] `AsyncMock`
- [ ] `spec`
- [ ] `autospec`
- [ ] `patch`
- [ ] `patch.object`
- [ ] Patch-where-used
- [ ] Dependency injection
- [ ] Mock vs fake

### Backend Testing

- [ ] Exception testing
- [ ] Async testing
- [ ] Database testing
- [ ] API testing
- [ ] Integration testing
- [ ] Kafka testing
- [ ] Redis testing
- [ ] Celery/background-job testing
- [ ] Transaction testing
- [ ] Retry/idempotency testing

### Test Engineering

- [ ] Test isolation
- [ ] Fixtures and factories
- [ ] Code coverage
- [ ] CI/CD testing
- [ ] Parallel execution
- [ ] Flaky-test diagnosis
- [ ] Risk-based testing
- [ ] Contract testing
- [ ] E2E strategy
- [ ] Security testing
- [ ] Performance testing

## Key Takeaways

- **Testing is a layered engineering discipline:** unit, component, integration, API, contract, and E2E tests provide different forms of confidence and should be used according to risk.
- **Fixtures and factories solve different problems:** fixtures manage dependencies and lifecycle, while factories generate controlled and isolated test data.
- **Real infrastructure matters:** PostgreSQL, Redis, Kafka, transactions, concurrency, and service contracts require integration-level validation when their semantics affect production behavior.
- **Test quality depends on determinism and isolation:** shared state, uncontrolled timing, excessive mocking, random data, and flaky infrastructure undermine confidence regardless of coverage.
- **The goal is production confidence, not test metrics:** coverage, test count, and CI speed are useful signals, but behavior, failure handling, security, reliability, and business risk determine whether a test strategy is effective.