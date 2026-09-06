# 20- Code Coverage

## Overview

Code coverage measures which parts of a codebase are executed while tests run. In Python projects, the most common implementation is `coverage.py`, often integrated with pytest through `pytest-cov`.

Coverage is useful as a **test-suite diagnostic**, not as a direct measure of test quality.

A test suite can achieve 95% line coverage while failing to verify important behavior:

```text
                    Test Suite
                        │
                        ▼
                 Coverage Measurement
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
       Executed code          Unexecuted code
             │                     │
             ▼                     ▼
       Coverage report       Missing test paths
```

The engineering goal is not:

> Maximize the percentage.

The goal is:

> Ensure important production behavior and failure paths are exercised by meaningful tests, while using coverage to identify blind spots.

For backend systems, coverage is particularly useful around:

- business rules;
- API handlers;
- authentication and authorization;
- validation;
- error handling;
- transaction boundaries;
- retry logic;
- state transitions;
- serialization;
- background jobs;
- message consumers;
- concurrency-sensitive code.

---

## What Code Coverage Measures

Coverage tools instrument Python execution and record which code locations are executed during a test run.

Common coverage metrics include:

| Metric | What it measures | Primary use |
|---|---|---|
| Statement/line coverage | Executable lines executed | Basic coverage visibility |
| Branch coverage | Decision paths exercised | Conditional logic |
| Function coverage | Functions/methods executed | API/component visibility |
| File/module coverage | Files containing executed code | Package-level visibility |
| Missing lines | Lines not executed | Finding test gaps |

Line coverage answers:

> Did execution reach this line?

Branch coverage answers:

> Did tests exercise the relevant outcomes of this decision?

Branch coverage is generally more informative for backend code with substantial conditional behavior.

---

## Line Coverage

Consider:

```python
def calculate_discount(total: float) -> float:
    if total >= 100:
        return total * 0.10

    return 0.0
```

A test using:

```python
def test_large_order_discount():
    assert calculate_discount(150) == 15
```

executes the discount branch but does not exercise the `else` path.

Line coverage may identify the unexecuted return statement.

The important issue is not the percentage itself. The issue is that one business behavior remains untested.

---

## Branch Coverage

Branch coverage considers decision outcomes.

```python
def classify_order(total: float) -> str:
    if total >= 100:
        return "large"

    return "standard"
```

There are two meaningful outcomes:

```text
total >= 100
   │
   ├── True  → "large"
   │
   └── False → "standard"
```

Tests should exercise both:

```python
@pytest.mark.parametrize(
    ("total", "expected"),
    [
        (100, "large"),
        (99.99, "standard"),
    ],
)
def test_classify_order(total, expected):
    assert classify_order(total) == expected
```

Branch coverage helps reveal cases where a line may technically execute but not all logical paths are exercised.

---

## Coverage Is Not Correctness

High coverage does not guarantee a high-quality test suite.

This test:

```python
def test_order():
    create_order()
```

may execute many lines while asserting almost nothing.

A meaningful test verifies behavior:

```python
def test_order_rejects_negative_quantity():
    with pytest.raises(ValueError, match="quantity"):
        create_order(quantity=-1)
```

Coverage measures execution.

Tests measure behavior.

Both matter, but they answer different questions.

---

## Coverage Workflow

A typical Python workflow is:

```text
Application Code
       │
       ▼
     pytest
       │
       ▼
 coverage.py instrumentation
       │
       ▼
Execution Data
       │
       ├── Terminal Report
       ├── HTML Report
       ├── XML Report
       └── LCOV / CI tooling
```

The common tools are:

- `coverage.py` for coverage measurement;
- `pytest-cov` for pytest integration;
- CI systems for enforcing project thresholds.

---

## Installing Coverage Tools

For pytest projects:

```bash
python -m pip install pytest pytest-cov
```

Run tests with coverage:

```bash
pytest --cov=src
```

Generate a terminal report:

```bash
pytest --cov=src --cov-report=term-missing
```

Generate HTML:

```bash
pytest --cov=src --cov-report=html
```

The HTML report is useful for inspecting individual files and identifying exactly which lines remain uncovered.

---

## Coverage Configuration

Modern Python projects can centralize configuration in `pyproject.toml`.

```toml
[tool.coverage.run]
branch = true
source = ["src"]
parallel = true

[tool.coverage.report]
show_missing = true
skip_covered = true
fail_under = 85

[tool.coverage.html]
directory = "htmlcov"
```

The exact configuration depends on the repository layout.

The important principle is to keep coverage policy version-controlled and reproducible.

---

## Measuring the Correct Source

Avoid accidentally measuring:

- virtual environments;
- generated files;
- test code;
- migrations when not relevant;
- vendored dependencies;
- build artifacts.

For a `src` layout:

```toml
[tool.coverage.run]
source = ["src"]
```

For a package:

```toml
[tool.coverage.run]
source = ["src/myservice"]
```

Explicit source configuration makes the reported percentage more meaningful.

---

## Excluding Files

Some files may legitimately be outside the intended coverage target.

Examples include:

- generated code;
- migration files;
- compatibility shims;
- development-only scripts.

Use explicit configuration rather than allowing accidental exclusion.

```toml
[tool.coverage.run]
source = ["src"]
omit = [
    "src/myservice/migrations/*",
    "src/myservice/generated/*",
]
```

Exclusions should be reviewed carefully.

Excluding difficult code merely to improve the percentage defeats the purpose of coverage.

---

## Excluding Specific Lines

Coverage.py supports explicit exclusions.

```python
if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable
```

Another example:

```python
def unreachable_state() -> None:
    raise AssertionError("unreachable")  # pragma: no cover
```

Use exclusions sparingly.

A `# pragma: no cover` annotation should mean:

> This code is intentionally outside the meaningful test-coverage target.

It should not mean:

> This code is difficult to test.

---

## Coverage Thresholds

Coverage thresholds can prevent large regressions.

```toml
[tool.coverage.report]
fail_under = 85
```

If measured coverage falls below the threshold, the command fails.

This is useful in CI:

```text
Pull Request
     │
     ▼
Run tests
     │
     ▼
Measure coverage
     │
     ├── >= threshold → pass
     │
     └── < threshold  → fail
```

A threshold is a guardrail, not a quality guarantee.

---

## Choosing a Coverage Threshold

There is no universally correct percentage.

| Threshold | Typical interpretation |
|---|---|
| 60–70% | Basic visibility |
| 70–80% | Reasonable baseline for many systems |
| 80–90% | Strong engineering target |
| 90%+ | High coverage requirement |
| 100% | Often expensive and not necessarily useful |

A mature project should consider:

- business criticality;
- codebase maturity;
- test pyramid;
- risk profile;
- branch complexity;
- legacy code;
- generated code;
- deployment frequency.

An 85% threshold with strong behavioral tests can be more valuable than 98% coverage obtained through shallow assertions.

---

## Coverage and Critical Paths

Coverage should be risk-driven.

A payment authorization component may deserve stronger coverage than:

```text
CLI formatting helper
```

A useful prioritization model is:

```text
Business impact
      ×
Failure probability
      ×
Operational blast radius
      │
      ▼
Testing priority
```

High-value areas often include:

- payment processing;
- authorization;
- data mutation;
- transaction handling;
- message processing;
- retries;
- state transitions;
- security boundaries.

---

## Coverage and Error Paths

Error handling is frequently under-tested.

Consider:

```python
def fetch_customer(repository, customer_id):
    try:
        return repository.get(customer_id)
    except CustomerNotFoundError:
        raise CustomerAPIError("Customer not found")
```

A test should exercise the failure path:

```python
def test_missing_customer_is_translated(repository):
    repository.get.side_effect = CustomerNotFoundError

    with pytest.raises(CustomerAPIError, match="Customer not found"):
        fetch_customer(repository, "customer-123")
```

Coverage can reveal whether error branches are being executed at all.

---

## Coverage and API Testing

For FastAPI or Django APIs, coverage should include important request paths:

```text
HTTP Request
     │
     ▼
Authentication
     │
     ▼
Authorization
     │
     ▼
Validation
     │
     ▼
Service Layer
     │
     ▼
Database / Cache / Queue
     │
     ▼
Response
```

Test coverage should include relevant outcomes such as:

- successful requests;
- malformed input;
- authentication failures;
- authorization failures;
- missing resources;
- conflict responses;
- dependency failures;
- transaction failures;
- serialization errors where applicable.

A single successful `200 OK` test rarely provides sufficient behavioral coverage.

---

## Coverage and Database Code

Database-backed code requires special care.

A line may execute:

```python
await repository.save(order)
```

without testing:

- unique constraints;
- foreign keys;
- transaction rollback;
- concurrent writes;
- PostgreSQL-specific behavior;
- connection failures.

Coverage cannot validate those database semantics.

Use integration tests with the real database technology when those behaviors matter.

---

## Coverage and Mocks

Mocks can increase code coverage without validating real integrations.

For example:

```python
repository.save = AsyncMock()
```

may execute application code successfully.

It does not prove that:

- SQL is valid;
- transactions work;
- constraints are respected;
- connection pooling behaves correctly.

Use mocks for unit-level behavior and integration tests for real boundaries.

---

## Coverage and Async Code

Async functions must actually execute to be covered.

Incorrect:

```python
async def test_order():
    create_order()
```

Correct:

```python
@pytest.mark.asyncio
async def test_order():
    await create_order()
```

Coverage should include important async behavior such as:

- successful completion;
- exceptions;
- cancellation;
- timeouts;
- concurrent execution;
- cleanup.

Coverage does not prove that concurrency behavior is race-free.

---

## Coverage and Background Jobs

Celery tasks and other background jobs should be tested through the appropriate layer.

```python
@app.task
def process_order(order_id: str):
    ...
```

Unit tests can execute the task function directly.

Integration tests can validate:

```text
Producer
   │
   ▼
Queue
   │
   ▼
Worker
   │
   ▼
Task
   │
   ▼
Database / External Service
```

Coverage of the task function does not prove that the queue, worker configuration, acknowledgment behavior, or retry semantics work correctly.

---

## Coverage and Kafka Consumers

For Kafka consumers, code coverage can show that message-handling branches execute.

It does not validate:

- partition assignment;
- offset management;
- consumer group behavior;
- redelivery;
- ordering;
- rebalance behavior.

Use integration tests for Kafka-specific semantics.

---

## Coverage and Conditional Logic

Coverage becomes particularly valuable when code contains many conditions:

```python
if authenticated:
    if authorized:
        if resource_exists:
            if not already_processed:
                process()
```

Line coverage alone can hide combinations of outcomes.

For complex logic, combine:

- branch coverage;
- parametrization;
- state-transition testing;
- property-based testing where appropriate;
- integration tests.

Do not blindly attempt every possible combination if the state space is enormous.

---

## Coverage and Parametrization

pytest parametrization works well for exercising branches.

```python
@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("pending", True),
        ("confirmed", True),
        ("cancelled", False),
        ("failed", False),
    ],
)
def test_order_is_processable(status, expected):
    assert is_processable(status) is expected
```

This improves behavioral coverage while keeping the test concise.

---

## Coverage and Property-Based Testing

Coverage and property-based testing solve different problems.

| Technique | Primary purpose |
|---|---|
| Coverage | Identify executed/unexecuted code |
| Example-based tests | Verify known scenarios |
| Parametrization | Verify structured input combinations |
| Property-based testing | Explore broad input spaces |
| Mutation testing | Evaluate whether tests detect code changes |

A high-coverage suite can still have weak assertions.

Mutation testing can expose this problem by deliberately changing code and checking whether tests fail.

---

## Coverage Reports

Common report formats include:

| Format | Use |
|---|---|
| Terminal | Local development and CI logs |
| HTML | Developer investigation |
| XML | CI/code-quality integrations |
| JSON | Automation and custom tooling |
| LCOV | Tooling that consumes LCOV data |

Examples:

```bash
pytest \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=html \
  --cov-report=xml
```

Avoid generating unnecessary formats on every local run if they add overhead.

---

## Inspecting Missing Coverage

A terminal report can identify missing lines:

```text
Name                         Stmts   Miss  Cover   Missing
----------------------------------------------------------
src/orders/service.py           42      4    90%   71-74
src/orders/repository.py        31      2    94%   55, 61
```

The useful question is:

> Why are lines 71–74 not covered?

Possible answers:

- missing test;
- dead code;
- intentionally excluded code;
- unreachable defensive branch;
- environment-specific path.

Do not automatically add a test merely to eliminate the number.

---

## Differential Coverage

Overall coverage can hide newly introduced untested code.

For example:

```text
Existing code:
90% coverage

New pull request:
+500 lines
+50 lines without tests

Overall:
89.2%
```

The overall percentage may still look acceptable.

Differential coverage focuses on changed code:

```text
Changed lines
     │
     ▼
Coverage check
     │
     ├── adequately tested → pass
     └── insufficient      → review/fail
```

This is particularly useful in large legacy repositories.

---

## Coverage in CI/CD

A typical CI pipeline:

```text
Pull Request
     │
     ▼
Install dependencies
     │
     ▼
Run unit tests
     │
     ▼
Run integration tests
     │
     ▼
Collect coverage
     │
     ▼
Enforce policy
     │
     ├── Pass → merge/deploy pipeline
     └── Fail → review
```

Coverage should normally be collected from the same test suite used to validate the change.

---

## Coverage in Parallel CI

Large test suites may run across multiple workers.

Coverage data then needs to be combined.

With coverage.py:

```toml
[tool.coverage.run]
parallel = true
```

After parallel execution:

```bash
coverage combine
coverage report
```

The exact workflow depends on the CI runner and test distribution strategy.

A common failure is producing separate coverage files but never combining them, resulting in an incomplete report.

---

## Coverage and Docker

A containerized test environment should keep coverage configuration reproducible.

Example:

```dockerfile
RUN python -m pip install --no-cache-dir \
    pytest \
    pytest-cov
```

Run:

```bash
pytest --cov=src --cov-report=term-missing
```

For CI, coverage artifacts such as HTML reports can be persisted separately from the test container.

Do not ship development coverage tooling unnecessarily in the production runtime image.

---

## Coverage and Kubernetes

Coverage is generally collected during CI rather than inside production Kubernetes workloads.

Avoid instrumenting production pods solely to obtain test coverage.

Production observability answers different questions:

- Which endpoints receive traffic?
- Which errors occur?
- Which code paths are expensive?
- Which services are failing?

Test coverage answers:

- Which code paths did the test suite execute?

They should not be conflated.

---

## Coverage and Microservices

For a microservice architecture, coverage should generally be evaluated per service.

```text
Service A
 ├── tests
 └── coverage

Service B
 ├── tests
 └── coverage

Service C
 ├── tests
 └── coverage
```

A global percentage across unrelated services can hide weaknesses in a critical service.

Track coverage close to the ownership and deployment boundary.

---

## Coverage and Code Quality Gates

Coverage can be combined with:

- linting;
- type checking;
- unit tests;
- integration tests;
- security scanning;
- dependency scanning.

Example:

```text
CI Quality Gate
 ├── Ruff
 ├── Mypy / Pyright
 ├── pytest
 ├── Coverage threshold
 ├── Integration tests
 └── Security checks
```

Coverage should be one signal among several.

---

## Coverage and Dead Code

Uncovered code may indicate dead code.

For example:

```python
def legacy_handler():
    ...
```

If no test or production execution uses it, investigate whether the code should exist.

Do not automatically add a test to preserve dead code.

Possible actions:

1. test it if it is required;
2. remove it if obsolete;
3. document why it is intentionally excluded.

---

## Coverage and Generated Code

Generated code can distort coverage.

Examples:

- OpenAPI-generated clients;
- protobuf-generated classes;
- migration files;
- generated serializers.

Exclude generated artifacts when they are not part of the project's maintained source behavior.

```toml
[tool.coverage.run]
omit = [
    "src/generated/*",
]
```

The exclusion should be explicit and documented through repository conventions.

---

## Coverage and Defensive Code

Some defensive branches may be extremely difficult to trigger:

```python
try:
    ...
except MemoryError:
    ...
```

Not every defensive branch requires a test.

The decision should consider:

- production importance;
- feasibility of simulation;
- risk;
- whether the branch contains meaningful behavior.

Avoid forcing artificial tests solely for percentage improvement.

---

## Coverage and Security Testing

Coverage can help identify untested security boundaries.

Important areas include:

- authentication failures;
- authorization failures;
- tenant isolation;
- input validation;
- privilege escalation paths;
- sensitive-data handling;
- token expiration;
- rate-limit behavior.

However, coverage does not prove that a system is secure.

Security testing may require:

- integration tests;
- negative tests;
- dependency scanning;
- static analysis;
- penetration testing;
- threat-model-driven tests.

---

## Coverage and Reliability

Reliability-sensitive paths should have meaningful tests even when coverage is already high.

Examples:

```text
Database timeout
Connection failure
Kafka redelivery
Redis unavailable
External API timeout
Transaction rollback
Task cancellation
Graceful shutdown
```

Coverage should help identify whether these paths execute during tests.

It cannot prove that failure recovery is correct without assertions.

---

## Coverage and Performance

Coverage instrumentation adds runtime overhead.

This matters for large suites.

For example:

```text
Normal test execution
        │
        ▼
   Application

Coverage-enabled execution
        │
        ▼
Instrumented application
        │
        ▼
Coverage data collection
```

The exact overhead depends on the workload and configuration.

Practical guidance:

- run coverage in CI;
- use normal pytest runs during rapid local development when speed matters;
- avoid unnecessary report generation;
- measure large-suite performance before optimizing coverage configuration.

---

## Coverage and Memory

Coverage collection stores execution information.

Large repositories, many workers, or long-running processes can increase resource usage.

For test suites involving:

- multiprocessing;
- subprocesses;
- large test counts;
- generated code;

verify that coverage data is collected and combined correctly without excessive disk or memory consumption.

---

## Coverage for Subprocesses

Coverage becomes more complicated when tests launch separate Python processes.

For example:

```python
subprocess.run(
    [sys.executable, "-m", "worker"],
    check=True,
)
```

The child process is separate from the pytest process.

If subprocess coverage matters, configure coverage collection appropriately and ensure the resulting data files are combined.

Do not assume that executing a child process automatically contributes to the parent process's coverage report.

---

## Coverage and Multiprocessing

Similarly, multiprocessing creates independent Python processes.

Coverage collection must account for process boundaries.

A project using multiprocessing heavily should verify its coverage setup rather than assuming:

```text
pytest process
    │
    ├── worker process
    ├── worker process
    └── worker process
```

will automatically produce one complete report.

---

## Coverage and Dynamic Python

Python allows dynamic behavior such as:

- `eval`;
- `exec`;
- runtime code generation;
- dynamic imports;
- metaprogramming.

Coverage measurement may not map cleanly to all dynamically generated code.

Production code should generally avoid unnecessary runtime code generation because it complicates:

- testing;
- debugging;
- observability;
- static analysis;
- coverage interpretation.

---

## Coverage for Django

For Django applications, focus coverage on maintained application behavior:

```text
Django
 ├── Views
 ├── Services
 ├── Models
 ├── Serializers
 ├── Permissions
 ├── Tasks
 └── Management commands
```

Do not interpret model line coverage as proof that database behavior is correct.

Use Django integration tests where framework and database semantics matter.

---

## Coverage for FastAPI

FastAPI applications can combine:

- unit tests for service logic;
- API tests for request/response behavior;
- integration tests for PostgreSQL/Redis/Kafka;
- coverage measurement across the application package.

A strong strategy might look like:

```text
FastAPI endpoint
      │
      ├── API test
      │
      ▼
Service
      │
      ├── Unit test
      │
      ▼
Repository
      │
      └── Integration test
              │
              ▼
          PostgreSQL
```

Coverage complements these layers rather than replacing them.

---

## Coverage and REST APIs

API coverage should consider behavioral dimensions, not just endpoint count.

For an endpoint:

```text
POST /orders
```

test relevant outcomes:

| Scenario | Example |
|---|---|
| Valid request | `201 Created` |
| Invalid payload | `400` / `422` |
| Unauthenticated | `401` |
| Unauthorized | `403` |
| Missing dependency | Appropriate `5xx`/mapped error |
| Duplicate resource | `409` where applicable |
| Database failure | Error handling path |
| Idempotent retry | Same business result |

A report showing that the route handler executed does not establish that these behaviors were tested.

---

## Coverage and gRPC

For gRPC services, coverage should include relevant:

- successful RPCs;
- validation failures;
- authentication failures;
- authorization failures;
- domain errors;
- timeout handling;
- cancellation;
- serialization behavior.

As with REST, transport-level coverage does not replace integration testing of the actual gRPC boundary.

---

## Coverage Governance

A mature team should define a clear policy.

Example:

```text
Coverage Policy
 ├── Measure maintained production source
 ├── Enable branch coverage
 ├── Enforce minimum threshold
 ├── Review meaningful uncovered paths
 ├── Exclude generated code explicitly
 └── Prevent coverage-only gaming
```

Avoid changing the threshold simply because a release introduces difficult code.

Instead, discuss whether the new behavior has appropriate tests.

---

## Common Mistakes

### Treating 100% as the Goal

100% coverage can encourage low-value tests.

**Better:** prioritize meaningful behavioral and branch coverage.

### Testing Only Happy Paths

Successful requests often cover only the easiest branch.

**Better:** test validation, authorization, failures, retries, and boundary conditions.

### Measuring Tests Instead of Production Code

Including test code can inflate the metric.

**Better:** configure coverage around maintained application source.

### Ignoring Branch Coverage

Line coverage may miss logical outcomes.

**Better:** enable branch coverage for backend services with meaningful conditional behavior.

### Using `pragma: no cover` Excessively

Excluding difficult code makes the metric meaningless.

**Better:** exclude only genuinely intentional non-target code.

### Assuming Coverage Proves Integration Correctness

A mocked PostgreSQL call can produce high application coverage.

**Better:** use real integration tests for database, Kafka, Redis, HTTP, and other critical boundaries.

### Optimizing Tests for the Percentage

Developers may write tests that execute lines without meaningful assertions.

**Better:** optimize for behavior and risk coverage.

### Forgetting Child Processes

Subprocesses and multiprocessing may not automatically contribute to the main coverage data.

**Better:** explicitly configure and validate multi-process coverage collection.

### Enforcing Coverage Without Stable Configuration

Different developers may measure different source paths or exclusions.

**Better:** version coverage configuration in `pyproject.toml`.

---

## Production Pitfalls

### Coverage Threshold as a Quality Substitute

A threshold can prevent regression but cannot evaluate assertion quality.

### Coverage Gaming

Examples include:

- adding meaningless tests;
- excessive exclusions;
- testing implementation details;
- lowering thresholds;
- excluding difficult modules.

These practices increase the metric while reducing its value.

### Overly Aggressive Thresholds

A 100% requirement can create maintenance overhead for low-risk code and encourage artificial tests.

### Ignoring Changed Code

Overall coverage can remain high while newly introduced code is untested.

Use changed-code or differential coverage where practical.

### Treating All Code Equally

Critical authorization or payment logic may deserve stronger testing than administrative tooling.

Use risk-based testing priorities.

---

## Recommended Configuration

A reasonable starting point for a pytest-based backend service is:

```toml
[tool.coverage.run]
branch = true
source = ["src"]
parallel = true

[tool.coverage.report]
show_missing = true
skip_covered = true
fail_under = 85
exclude_also = [
    "if TYPE_CHECKING:",
]

[tool.coverage.html]
directory = "htmlcov"
```

The exact threshold and exclusions should be adapted to the project.

Run locally:

```bash
pytest --cov=src --cov-report=term-missing
```

Generate HTML:

```bash
pytest \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=html
```

Generate CI-friendly XML:

```bash
pytest \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=xml
```

---

## Recommended Coverage Strategy

A practical backend strategy is:

```text
                    Code Coverage
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Unit Tests    Integration     API Tests
          │              │              │
          ▼              ▼              ▼
     Business logic   DB/Redis/Kafka   HTTP behavior
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  Coverage Report
                         │
                         ▼
                  Risk-based Review
```

Use coverage to answer:

1. What important code is not exercised?
2. Which branches are missing?
3. Did this change introduce untested behavior?
4. Are error paths tested?
5. Are critical business rules covered?
6. Are integration boundaries tested at the appropriate layer?

Do not use it to answer:

> Is the application correct?

That requires the complete testing strategy.

---

## Coverage Review Checklist

### Configuration

- [ ] Is coverage configuration version-controlled?
- [ ] Is production source explicitly configured?
- [ ] Is branch coverage enabled?
- [ ] Are exclusions minimal and justified?
- [ ] Is the threshold appropriate for the repository?

### Test Quality

- [ ] Are tests asserting behavior?
- [ ] Are important error paths exercised?
- [ ] Are authorization and validation paths covered?
- [ ] Are boundary conditions tested?
- [ ] Are state transitions covered?

### Integration

- [ ] Are database semantics tested with PostgreSQL where required?
- [ ] Are Redis and Kafka behaviors tested at integration level?
- [ ] Are external API boundaries tested appropriately?
- [ ] Are transaction and retry paths tested?

### CI/CD

- [ ] Does CI fail when the threshold is violated?
- [ ] Is coverage generated consistently?
- [ ] Are parallel coverage files combined?
- [ ] Are coverage artifacts available for investigation?
- [ ] Is changed-code coverage considered for large repositories?

### Governance

- [ ] Are critical modules prioritized?
- [ ] Are generated files excluded intentionally?
- [ ] Are `no cover` annotations reviewed?
- [ ] Is coverage prevented from becoming a vanity metric?

---

## Interview Traps

### Is 100% Code Coverage Required?

No. High coverage can be useful, but 100% execution does not guarantee correct assertions or meaningful behavior testing.

### What Is the Difference Between Line and Branch Coverage?

Line coverage measures whether executable lines ran. Branch coverage additionally considers whether decision outcomes were exercised.

### Does High Coverage Mean the Code Is Well Tested?

No. Coverage measures execution, not assertion quality, correctness, integration behavior, or security.

### Why Is Branch Coverage Valuable?

It exposes untested outcomes of conditional logic that line coverage can overlook.

### Should You Mock Dependencies When Measuring Coverage?

Mocks are appropriate for unit tests, but coverage obtained through mocks does not validate the real dependency. Integration tests are still required for important external semantics.

### Why Use `fail_under`?

It turns coverage into a CI quality gate that prevents coverage from falling below an agreed baseline.

### Should Generated Code Be Covered?

Usually not when it is generated and not maintained directly by the project. It should be explicitly excluded from the coverage target.

### Why Can Coverage Be Missing for Multiprocessing Code?

Coverage data is process-local. Child processes may require separate collection and later combination.

### What Is Differential Coverage?

It evaluates coverage of changed code rather than relying only on the aggregate repository percentage.

### What Is the Senior-Level View of Coverage?

Coverage is a feedback signal for identifying untested code paths. Test strategy should remain risk-driven and behavior-focused rather than percentage-driven.

## Key Takeaways

- **Coverage measures execution, not correctness:** meaningful assertions, failure-path testing, and integration testing remain essential even with high coverage.
- **Prefer branch-aware, risk-driven coverage:** critical business rules, authorization, transactions, retries, and failure paths deserve stronger testing than low-risk utility code.
- **Keep coverage configuration reproducible:** define source paths, branches, exclusions, reports, and thresholds in version-controlled project configuration.
- **Use coverage as a CI guardrail, not a vanity metric:** thresholds and differential coverage can prevent regressions without encouraging meaningless tests.
- **Respect process and integration boundaries:** multiprocessing, subprocesses, databases, Kafka, Redis, and external services require appropriate coverage configuration and dedicated integration tests.