# 08- Matrix Strategy Issues

## Overview

GitHub Actions matrix strategy is one of the primary mechanisms for running the same job across multiple configurations such as Python versions, operating systems, databases, or application variants.

A matrix is powerful because it converts one logical job definition into multiple job executions:

```text
One Job Definition
       ↓
Matrix Expansion
       ↓
Multiple Job Instances
       ↓
Parallel Execution
       ↓
Aggregated Pipeline Result
```

For backend systems, common matrix dimensions include:

- Python versions
- Django versions
- Database engines
- PostgreSQL versions
- MySQL versions
- Operating systems
- Dependency versions
- Application configurations
- Architecture or runtime variants

The main operational risk is that matrix size grows multiplicatively.

For example:

```yaml
matrix:
  python: ["3.11", "3.12", "3.13"]
  database: ["postgres", "mysql"]
  os: [ubuntu-latest, windows-latest]
```

creates:

```text
3 × 2 × 2 = 12 jobs
```

A matrix therefore needs to be designed as a capacity, cost, reliability, and failure-isolation mechanism rather than merely a YAML convenience.

---

## Matrix Execution Model

A matrix job starts as one logical job:

```yaml
jobs:
  test:
    strategy:
      matrix:
        python: ["3.11", "3.12"]
```

GitHub expands it into separate executions:

```text
test[python=3.11]
test[python=3.12]
```

Each matrix combination receives its own:

- Runner
- Workspace
- Environment
- Steps
- Logs
- Result
- Matrix context

The jobs are independent unless connected through workflow dependencies.

---

## Basic Matrix

```yaml
name: CI

on:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python: ["3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}

      - run: |
          python --version
          python -m pip install -r requirements.txt
          pytest
```

This is useful when the same test suite must be validated against several Python runtimes.

---

## Why Matrix Jobs Fail

Matrix failures usually belong to one of several domains:

| Failure Domain | Typical Symptoms |
|---|---|
| Matrix definition | Invalid YAML or invalid combinations |
| Matrix expansion | Unexpected number of jobs |
| `include` / `exclude` | Wrong or missing combinations |
| Expression evaluation | Matrix values unavailable where expected |
| Dependencies | Incorrect `needs` relationships |
| Services | Database/Redis unavailable |
| Environment | Matrix value not passed correctly |
| Runner capacity | Queued or unavailable jobs |
| Resource limits | Excessive parallelism |
| Flaky tests | Same matrix cell fails intermittently |
| Dependency compatibility | One version combination fails |
| Dynamic matrix | Invalid JSON or generated configuration |
| Outputs | Missing or ambiguous matrix output |
| Artifacts | Name collisions between matrix jobs |
| Deployment | Multiple matrix cells accidentally deploy |

Troubleshooting should therefore start with identifying the matrix cell that failed.

---

## Matrix Context

Within a matrix job, values are available through:

```yaml
${{ matrix.<key> }}
```

Example:

```yaml
strategy:
  matrix:
    python: ["3.11", "3.12"]

steps:
  - name: Show Python version
    run: echo "Testing Python ${{ matrix.python }}"
```

For a matrix containing:

```yaml
matrix:
  python: ["3.11", "3.12"]
  database: ["postgres", "mysql"]
```

values are:

```yaml
${{ matrix.python }}
${{ matrix.database }}
```

---

## Inspecting the Matrix Cell

Use explicit diagnostic output:

```yaml
- name: Show matrix configuration
  env:
    PYTHON_VERSION: ${{ matrix.python }}
    DATABASE: ${{ matrix.database }}
  run: |
    echo "Python: $PYTHON_VERSION"
    echo "Database: $DATABASE"
```

Prefer passing values through environment variables when shell execution is involved.

---

## Multiple Matrix Dimensions

Example:

```yaml
strategy:
  matrix:
    python: ["3.11", "3.12", "3.13"]
    database: ["postgres", "mysql"]
```

This creates:

```text
3.11 + postgres
3.11 + mysql
3.12 + postgres
3.12 + mysql
3.13 + postgres
3.13 + mysql
```

Total:

```text
3 × 2 = 6 jobs
```

---

## Matrix Cardinality

Matrix size is:

```text
Product of all dimension sizes
```

For:

```yaml
python:   3 values
database: 2 values
os:       2 values
```

the number of jobs is:

```text
3 × 2 × 2 = 12
```

With four dimensions:

```text
3 × 2 × 2 × 3 = 36
```

This multiplication is one of the most important production considerations when designing matrices.

---

## Matrix Explosion

A large matrix can cause:

- Long queue times
- High runner consumption
- Higher CI cost
- Increased downstream database load
- Registry pressure
- More logs and artifacts
- More flaky test opportunities
- More difficult failure diagnosis

Avoid adding matrix dimensions simply because they are technically possible.

---

## Test Matrix vs Compatibility Matrix

These are related but different.

### Test Matrix

Used to validate supported configurations.

```text
Python versions
+
Database versions
+
Operating systems
```

### Compatibility Matrix

Used to determine whether combinations are supported.

For example:

```text
Python 3.11 + Django 5.2
Python 3.12 + Django 5.2
Python 3.13 + Django 5.2
```

A compatibility matrix may require `include` and `exclude` to represent supported combinations accurately.

---

## `include`

`include` can add or extend matrix combinations.

Example:

```yaml
strategy:
  matrix:
    python: ["3.11", "3.12"]
    include:
      - python: "3.12"
        experimental: true
```

The resulting matrix can contain additional metadata.

Use `include` when a specific combination needs additional variables or special behavior.

---

## Matrix Metadata

Example:

```yaml
strategy:
  matrix:
    python: ["3.11", "3.12"]
    include:
      - python: "3.12"
        allow_failure: true
```

Then:

```yaml
continue-on-error: ${{ matrix.allow_failure || false }}
```

This can be useful for experimental compatibility testing.

However, do not use `continue-on-error` to hide known production failures indefinitely.

---

## `exclude`

Use `exclude` to remove invalid or unsupported combinations.

Example:

```yaml
strategy:
  matrix:
    python: ["3.11", "3.12", "3.13"]
    django: ["5.2", "6.0"]

    exclude:
      - python: "3.11"
        django: "6.0"
```

This is appropriate when a combination is intentionally unsupported.

---

## `include` and `exclude` Failure Pattern

### Symptom

An unexpected matrix cell runs.

### Possible Causes

- Incorrect `include`
- Incorrect `exclude`
- Combination does not exactly match expected matrix properties
- Generated matrix differs from the static matrix

### Isolation Strategy

Temporarily inspect the matrix values:

```yaml
- name: Matrix diagnostics
  env:
    MATRIX: ${{ toJSON(matrix) }}
  run: echo "$MATRIX"
```

### Prevention

Keep matrix definitions small, explicit, and documented.

---

## `fail-fast`

By default, matrix strategy can cancel in-progress matrix jobs when one fails.

Configure explicitly:

```yaml
strategy:
  fail-fast: false
  matrix:
    python: ["3.11", "3.12", "3.13"]
```

This is useful when every matrix result is valuable for diagnosis.

---

## When to Use `fail-fast: false`

Use it when:

- You want complete compatibility information
- Multiple Python versions must be validated
- Failures may be independent
- You need to diagnose all failing environments in one run

Example:

```text
3.11 → failed
3.12 → failed
3.13 → passed
```

This gives more information than stopping after the first failure.

---

## When Fail-Fast Is Useful

Fail-fast can reduce wasted compute when:

```text
A fundamental failure makes remaining matrix cells irrelevant
```

For example:

```text
Repository cannot install dependencies
```

If every matrix cell will fail for the same infrastructure reason, continuing all jobs may waste resources.

---

## `max-parallel`

Control concurrent matrix executions:

```yaml
strategy:
  max-parallel: 2
  matrix:
    python: ["3.11", "3.12", "3.13", "3.14"]
```

This limits simultaneous matrix workers.

---

## Why `max-parallel` Matters

A matrix can overload downstream dependencies.

Example:

```text
20 matrix jobs
   ↓
20 PostgreSQL containers
   ↓
20 concurrent test suites
```

This can produce:

- Database connection exhaustion
- CPU contention
- Memory pressure
- Network saturation
- Runner queue pressure

`max-parallel` can act as a simple backpressure mechanism.

---

## Matrix and PostgreSQL

Example:

```yaml
jobs:
  integration:
    runs-on: ubuntu-latest

    strategy:
      fail-fast: false
      max-parallel: 3

      matrix:
        python: ["3.11", "3.12"]
        postgres: ["16", "17"]

    services:
      postgres:
        image: postgres:${{ matrix.postgres }}
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: testdb
        options: >-
          --health-cmd "pg_isready -U postgres -d testdb"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}

      - name: Install dependencies
        run: python -m pip install -r requirements.txt

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
        run: pytest tests/integration
```

This produces:

```text
Python 3.11 + PostgreSQL 16
Python 3.11 + PostgreSQL 17
Python 3.12 + PostgreSQL 16
Python 3.12 + PostgreSQL 17
```

---

## Matrix and Redis

Redis is often a service dependency rather than a test dimension.

Example:

```yaml
services:
  redis:
    image: redis:7
```

Use a matrix dimension only when Redis versions themselves are part of the compatibility contract.

Avoid:

```text
Python × PostgreSQL × Redis × OS
```

unless every combination has meaningful coverage.

---

## Matrix and Django

A practical Django compatibility matrix might test:

```text
Python
+
Django
+
PostgreSQL
```

But the complete Cartesian product may be unnecessarily large.

Prefer a supported compatibility matrix:

```yaml
strategy:
  matrix:
    include:
      - python: "3.11"
        django: "5.2"
      - python: "3.12"
        django: "5.2"
      - python: "3.13"
        django: "6.0"
```

This represents real supported combinations instead of testing invalid combinations.

---

## Matrix and FastAPI

FastAPI applications often have fewer framework compatibility dimensions, but a matrix can still validate:

```text
Python versions
Dependency versions
Database versions
Operating systems
```

Use the matrix to represent actual support guarantees.

---

## Matrix and `needs`

Matrix jobs can depend on another job:

```yaml
jobs:
  prepare:
    runs-on: ubuntu-latest
    steps:
      - run: echo "prepare"

  test:
    needs: prepare
    strategy:
      matrix:
        python: ["3.11", "3.12"]
    runs-on: ubuntu-latest

    steps:
      - run: python --version
```

The `prepare` job must complete successfully before the matrix is expanded for execution.

---

## Matrix Fan-Out

A common architecture is:

```text
             ┌── Python 3.11
             │
Prepare ─────┼── Python 3.12
             │
             └── Python 3.13
```

This is called fan-out.

It is useful for parallel compatibility testing.

---

## Matrix Fan-In

After matrix execution, another job can aggregate the result:

```text
Python 3.11 ──┐
Python 3.12 ──┼── Aggregate
Python 3.13 ──┘
```

Example:

```yaml
jobs:
  test:
    strategy:
      matrix:
        python: ["3.11", "3.12", "3.13"]
    runs-on: ubuntu-latest
    steps:
      - run: pytest

  report:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: echo "All matrix jobs completed"
```

---

## Matrix Outputs

Matrix outputs require careful design.

A matrix job may execute multiple times, so a single job output name does not naturally represent multiple independent values.

For example:

```text
test[python=3.11]
test[python=3.12]
test[python=3.13]
```

If every cell writes:

```text
result=passed
```

there is no meaningful single value unless the results are aggregated deliberately.

Prefer:

```text
Matrix jobs
   ↓
Artifacts / uniquely named outputs
   ↓
Aggregation job
```

---

## Matrix Output Collision

### Problem

Multiple matrix jobs attempt to publish the same artifact name:

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: test-report
```

### Result

Reports can conflict or become difficult to associate with the matrix cell.

### Better

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: test-report-python-${{ matrix.python }}
```

For multiple dimensions:

```yaml
name: report-${{ matrix.python }}-${{ matrix.database }}
```

---

## Artifact Naming

A production matrix should encode the dimensions that identify the result.

Example:

```text
coverage-python-3.11-postgres-16
coverage-python-3.12-postgres-17
```

This improves:

- Debugging
- Traceability
- Artifact discovery
- Incident analysis

---

## Matrix Caching

Caches should also account for matrix dimensions when they affect dependencies.

A poor cache key:

```yaml
key: dependencies
```

can cause unrelated configurations to share cache state.

A better approach uses relevant dimensions:

```yaml
key: >-
  deps-${{ runner.os }}-${{ matrix.python }}-${{
  hashFiles('**/requirements*.txt')
  }}
```

---

## Cache Failure Pattern

### Symptom

One matrix cell behaves differently from another even though the source is identical.

### Possible Causes

- Incorrect cache key
- Cross-version dependency cache
- Stale dependency cache
- Missing OS/runtime dimension

### Isolation

Temporarily disable the cache.

If the failure disappears, inspect:

```text
Cache key
Restore keys
Dependency lock files
Runtime version
OS
```

---

## Matrix and Docker

Docker builds can also use matrix dimensions:

```yaml
strategy:
  matrix:
    platform:
      - linux/amd64
      - linux/arm64
```

However, building the same image independently for every matrix cell can be expensive.

For production container publishing, prefer dedicated Buildx multi-platform builds when the goal is platform support rather than application test compatibility.

---

## Matrix and Build Once, Deploy Many

Avoid this architecture:

```text
Matrix Test
    ↓
Build per matrix cell
    ↓
Deploy per matrix cell
```

unless each cell genuinely represents a different deployable artifact.

Prefer:

```text
Matrix Tests
    ↓
Validated
    ↓
Single Build
    ↓
Immutable Artifact
    ↓
Staging
    ↓
Production
```

Testing dimensions and deployment dimensions should usually be separated.

---

## Matrix and Deployment Safety

Never accidentally create:

```text
Python 3.11 → Production
Python 3.12 → Production
Python 3.13 → Production
```

because a deployment job inherits a matrix.

A production deployment should generally happen once after compatibility validation.

Use:

```text
Matrix Testing
      ↓
Fan-In
      ↓
Build
      ↓
Deploy
```

---

## Matrix and Concurrency

Matrix execution and deployment concurrency solve different problems.

Matrix:

```text
How many configurations should be tested?
```

Concurrency:

```text
How many workflow/deployment executions may overlap?
```

A production pipeline might use:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

while the test job uses:

```yaml
strategy:
  max-parallel: 4
```

---

## Matrix and Self-Hosted Runners

Matrix jobs can target different runner classes.

Example:

```yaml
runs-on: ${{ matrix.runner }}

strategy:
  matrix:
    runner:
      - ubuntu-latest
      - [self-hosted, linux, private-network]
```

Be careful when matrix expansion increases demand for specialized runners.

A matrix that works with GitHub-hosted runners may become blocked if only two self-hosted runners are available.

---

## Runner Capacity Planning

If:

```text
Matrix size = 30
```

but:

```text
Available specialized runners = 5
```

then at most approximately five jobs can execute concurrently, depending on runner availability and labels.

Use:

```yaml
max-parallel: 5
```

when deliberate throttling is appropriate.

Do not use `max-parallel` as a substitute for proper runner autoscaling.

---

## Matrix and Service Capacity

Consider:

```text
12 matrix jobs
×
PostgreSQL service
×
Redis service
×
Application process
```

The real resource demand can be much larger than the matrix count suggests.

For integration tests, consider:

- Database connection limits
- CPU
- Memory
- Disk
- Network
- Service startup time
- Test data isolation

---

## Matrix and Flaky Tests

A matrix often exposes platform-specific flakiness.

Example:

```text
3.11 → pass
3.12 → pass
3.13 → intermittent failure
```

Do not immediately mark the matrix cell as allowed to fail.

First determine whether the issue is:

- Application compatibility
- Dependency incompatibility
- Timing
- Service readiness
- Test isolation
- Runner differences
- Resource contention

---

## `continue-on-error` in a Matrix

A controlled experimental cell can use:

```yaml
strategy:
  matrix:
    python: ["3.12", "3.13"]
    include:
      - python: "3.13"
        experimental: true

continue-on-error: ${{ matrix.experimental || false }}
```

This can be useful for pre-release runtimes.

It should not be used to hide a failing supported production configuration.

---

## Matrix Failure Investigation

Use the following process:

```text
Identify failing matrix cell
        ↓
Compare against passing cells
        ↓
Identify changed dimension
        ↓
Reproduce only failing combination
        ↓
Inspect dependencies/environment
        ↓
Determine deterministic vs flaky
        ↓
Fix root cause
        ↓
Restore full matrix
```

This is significantly faster than repeatedly running the entire matrix blindly.

---

## Failure Domain: Matrix Definition

### Symptom

Workflow fails before meaningful test execution.

### Possible Causes

- Invalid matrix syntax
- Invalid expression
- Unsupported matrix value
- Incorrect `include`
- Incorrect `exclude`

### Isolation

Start with the smallest matrix:

```yaml
matrix:
  python: ["3.12"]
```

Then add dimensions incrementally.

### Prevention

Validate matrix configuration before expanding it across many dimensions.

---

## Failure Domain: Unexpected Job Count

### Symptom

You expected six jobs but GitHub created twelve.

### Possible Causes

Cartesian multiplication.

Example:

```text
3 Python versions
×
2 databases
×
2 operating systems
=
12 jobs
```

### Corrective Action

Calculate matrix cardinality before adding dimensions.

---

## Failure Domain: Invalid Combination

### Symptom

A configuration that should not run is executed.

### Possible Causes

- Missing `exclude`
- Incorrect `include`
- Unsupported combination not represented explicitly

### Corrective Action

Represent the supported compatibility set directly when the Cartesian product does not match reality.

---

## Failure Domain: Missing Matrix Value

### Symptom

A step sees an empty or unexpected matrix value.

### Possible Causes

- Wrong matrix key
- Incorrect expression
- Value generated incorrectly
- `include` metadata not applied as expected

### Diagnostic

```yaml
- name: Diagnostics
  env:
    MATRIX: ${{ toJSON(matrix) }}
  run: echo "$MATRIX"
```

---

## Failure Domain: Dynamic Matrix

Dynamic matrices commonly use JSON.

Example:

```yaml
jobs:
  generate:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.generate.outputs.matrix }}

    steps:
      - id: generate
        shell: bash
        run: |
          matrix='{"python":["3.11","3.12"],"database":["postgres"]}'
          echo "matrix=$matrix" >> "$GITHUB_OUTPUT"

  test:
    needs: generate
    strategy:
      matrix: ${{ fromJSON(needs.generate.outputs.matrix) }}

    runs-on: ubuntu-latest

    steps:
      - run: |
          echo "Python: ${{ matrix.python }}"
          echo "Database: ${{ matrix.database }}"
```

---

## Dynamic Matrix Failure

### Symptom

Matrix generation fails before test jobs start.

### Possible Causes

- Invalid JSON
- Incorrect output formatting
- Missing job output
- Incorrect `needs`
- Incorrect `fromJSON()`
- Empty generated value

### Isolation

Inspect the generated output:

```yaml
- name: Show generated matrix
  env:
    MATRIX: ${{ steps.generate.outputs.matrix }}
  run: |
    printf '%s\n' "$MATRIX"
```

Validate JSON independently:

```bash
printf '%s' "$MATRIX" | jq .
```

---

## Dynamic Matrix Security

Do not blindly convert untrusted input into a matrix.

Dangerous:

```text
User Input
 ↓
Generated JSON
 ↓
Dynamic Matrix
 ↓
Privileged Job
```

Prefer:

```text
Input
 ↓
Validation
 ↓
Allowlisted Values
 ↓
JSON
 ↓
Matrix
```

This is particularly important when matrix values influence:

- Shell commands
- Docker tags
- Deployment targets
- AWS resources
- Runner labels
- Artifact names

---

## Matrix and Shell Injection

Avoid directly embedding uncontrolled matrix values into shell commands.

Instead of:

```yaml
run: deploy --environment ${{ matrix.environment }}
```

prefer controlled environment passing:

```yaml
env:
  DEPLOY_ENVIRONMENT: ${{ matrix.environment }}
run: |
  ./deploy.sh "$DEPLOY_ENVIRONMENT"
```

The matrix itself should also contain only validated values.

---

## Matrix and Docker Image Tags

Do not blindly create image tags from arbitrary matrix values.

Example:

```yaml
env:
  IMAGE_TAG: ${{ matrix.python }}
```

Validate the value before using it in a registry operation.

For production artifacts, prefer immutable identifiers such as:

```text
Git commit SHA
```

over environment-controlled mutable values.

---

## Matrix and AWS

Avoid using arbitrary matrix values to select privileged AWS resources.

Dangerous architecture:

```text
Dynamic Matrix
 ↓
AWS account
 ↓
Production role
```

Prefer explicit mappings:

```yaml
include:
  - environment: staging
    role_arn: arn:aws:iam::111111111111:role/staging-deploy
```

and ensure the workflow permissions and IAM trust policy enforce the same boundary.

---

## Matrix and Reusable Workflows

A matrix can invoke a reusable workflow:

```yaml
jobs:
  deploy:
    strategy:
      matrix:
        environment:
          - staging
          - production

    uses: org/platform/.github/workflows/deploy.yml@v1
    with:
      environment: ${{ matrix.environment }}
```

This requires careful governance.

Production should not become an accidental matrix cell simply because environments are represented as data.

For deployment pipelines, separate approval and promotion boundaries are usually clearer.

---

## Matrix and Reusable Workflow Outputs

A reusable workflow may return structured outputs, but matrix fan-out creates multiple executions.

Prefer:

```text
Matrix
 ↓
Artifacts / structured result
 ↓
Aggregator
 ↓
Single deployment decision
```

rather than attempting to make one matrix cell determine the entire pipeline state.

---

## Matrix and Artifacts

Use unique artifact names:

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: junit-${{ matrix.python }}-${{ matrix.database }}
    path: reports/junit.xml
```

This makes each result independently inspectable.

---

## Matrix and Test Reports

A production testing workflow may generate:

```text
JUnit XML
Coverage XML
HTML coverage
Application logs
Database logs
Screenshots
Traces
```

Each matrix cell should produce uniquely identifiable artifacts.

Example:

```text
reports/
├── python-3.11/
│   └── junit.xml
└── python-3.12/
    └── junit.xml
```

---

## Matrix Report Aggregation

A common architecture is:

```text
Matrix Tests
 ├── Python 3.11 → report
 ├── Python 3.12 → report
 └── Python 3.13 → report
          ↓
    Upload artifacts
          ↓
    Aggregation job
          ↓
    Combined report
```

This preserves per-cell diagnostics while allowing centralized reporting.

---

## Matrix and Coverage

Coverage can vary across matrix cells.

For example:

```text
Python 3.11 → 91%
Python 3.12 → 92%
Python 3.13 → 90%
```

Do not accidentally overwrite reports by using the same artifact or output name.

Aggregate deliberately.

---

## Matrix and Dependency Caching

For Python:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: ${{ matrix.python }}
    cache: pip
    cache-dependency-path: requirements.txt
```

This keeps dependency caching aligned with the selected Python runtime.

For more complex dependency graphs, ensure lock files and matrix dimensions that affect dependencies are represented appropriately.

---

## Matrix and Operating Systems

Example:

```yaml
strategy:
  matrix:
    os:
      - ubuntu-latest
      - windows-latest
      - macos-latest

runs-on: ${{ matrix.os }}
```

This is useful when cross-platform support is a product requirement.

Do not add operating systems merely because they are available.

Each additional OS increases:

```text
Execution time
Cost
Failure surface
Maintenance
Diagnostic complexity
```

---

## Platform-Specific Dependencies

Python projects may have native dependencies whose behavior differs by OS.

Examples include:

- Database drivers
- Cryptography libraries
- System packages
- Compilers
- File path behavior
- Shell behavior

When an OS matrix cell fails, compare:

```text
Python version
OS
Architecture
Native dependencies
Shell
Environment variables
```

---

## Matrix and Shell Differences

Ubuntu commonly uses:

```text
bash
```

Windows may use:

```text
PowerShell
```

A shell-specific step can therefore fail only on one matrix cell.

Prefer portable Python commands where practical:

```yaml
run: python -m pytest
```

rather than relying heavily on shell-specific syntax.

---

## Matrix and Timeouts

Large matrix jobs can hide slow cells.

Use explicit timeouts where appropriate:

```yaml
jobs:
  test:
    timeout-minutes: 20
```

This prevents one pathological matrix cell from consuming runner capacity indefinitely.

---

## Matrix and Retries

Retries should be used carefully.

A failed matrix cell should first be classified:

```text
Deterministic failure
```

versus:

```text
Transient infrastructure failure
```

Retrying deterministic application failures wastes CI capacity and can hide regressions.

---

## Matrix and Flaky Tests

If one cell repeatedly fails intermittently:

```text
3.13 → fail
3.13 → pass
3.13 → fail
```

investigate:

- Race conditions
- Timing assumptions
- Test isolation
- Resource exhaustion
- Service readiness
- Dependency behavior
- Parallel test execution

Do not permanently mark the cell as non-blocking without understanding why it is flaky.

---

## Matrix and Cost

Approximate CI compute grows with:

```text
Matrix cardinality
×
Average job duration
×
Number of workflow executions
```

For example:

```text
12 cells
×
10 minutes
=
120 runner-minutes
```

A pull request workflow running this matrix on every change can become expensive at scale.

---

## PR Matrix vs Nightly Matrix

A useful production pattern is:

```text
Pull Request
    ↓
Small high-value matrix

Nightly
    ↓
Expanded compatibility matrix

Release
    ↓
Full supported matrix
```

This balances developer feedback time against compatibility coverage.

---

## Selective Matrix Design

Example:

```text
PR:
Python 3.12 + PostgreSQL 17

Nightly:
Python 3.11/3.12/3.13
+
PostgreSQL 16/17
+
MySQL

Release:
Full supported compatibility matrix
```

The exact policy depends on the project's support contract.

---

## Matrix and Monorepos

A monorepo may generate matrix configurations based on changed services.

Example:

```text
Changed services
      ↓
Planning job
      ↓
JSON matrix
      ↓
Only affected test jobs
```

This can dramatically reduce unnecessary CI work.

The planning job must validate generated values before they reach privileged execution.

---

## Matrix and Microservices

For multiple services:

```text
service-a
service-b
service-c
```

a dynamic matrix can test only affected services.

Each matrix cell can carry:

```text
service
python
test-suite
dockerfile
artifact-name
```

Use structured JSON rather than fragile string parsing.

---

## Failure Domain: Service Container

### Symptom

Only some matrix cells fail to connect to PostgreSQL or Redis.

### Possible Causes

- Service startup timing
- Health check failure
- Different test data
- Port assumptions
- Resource contention
- Environment-specific configuration

### Isolation

Print:

```text
matrix values
service configuration
health status
connection target
```

Then reproduce only the failing cell.

---

## Failure Domain: Dependency Compatibility

### Symptom

One Python version fails while others pass.

Example:

```text
3.11 → pass
3.12 → pass
3.13 → fail
```

### Possible Causes

- Unsupported dependency
- Native extension issue
- Deprecated API
- Runtime-specific behavior
- Lockfile incompatibility

### Corrective Action

Compare:

```text
Python runtime
Package versions
Lock file
OS
Compiler
Native libraries
```

Do not remove the matrix cell simply to make CI green if that runtime is officially supported.

---

## Failure Domain: Runner Capacity

### Symptom

Matrix jobs remain queued.

### Possible Causes

- Runner capacity
- Self-hosted runner shortage
- Runner labels do not match
- Organization limits
- Excessive matrix cardinality

### Checks

```bash
gh run list
```

Then inspect runner configuration and availability through repository or organization Actions settings.

For self-hosted infrastructure, also inspect:

```text
Runner registration
Labels
Runner groups
Autoscaling
Network connectivity
Runner health
```

---

## Failure Domain: Matrix Job Cancellation

### Symptom

Some matrix cells become cancelled after another cell fails.

### Possible Cause

`fail-fast` behavior.

### Check

```yaml
strategy:
  fail-fast: false
```

If complete diagnostics are required, disable fail-fast intentionally.

---

## Failure Domain: `needs` and Skipped Jobs

### Symptom

The matrix itself succeeds, but a downstream job is skipped.

### Possible Causes

- One matrix cell failed
- `needs` dependency is not satisfied
- Conditional expression evaluates false
- Previous job was cancelled
- Status function behavior is misunderstood

Inspect:

```text
Matrix job results
↓
needs context
↓
if condition
```

---

## Failure Domain: Artifact Collision

### Symptom

Reports from matrix cells are missing or ambiguous.

### Possible Causes

- Same artifact name
- Same output path
- Shared workspace assumptions
- Aggregation overwriting files

Use matrix-specific names and paths.

---

## Failure Domain: Cache Contamination

### Symptom

Only one matrix combination has inconsistent dependencies.

### Possible Causes

- Cache key missing runtime dimension
- Broad restore key
- Stale cache
- OS mismatch

Test with cache disabled before changing application dependencies.

---

## Failure Domain: Dynamic JSON

### Symptom

`fromJSON()` fails.

### Checks

Generate the matrix JSON and validate it:

```bash
jq .
```

Example:

```bash
printf '%s' "$MATRIX_JSON" | jq empty
```

Then inspect:

```yaml
${{ needs.generate.outputs.matrix }}
```

and verify that the job output exists.

---

## Matrix Debugging Template

Use a temporary diagnostic step:

```yaml
- name: Matrix diagnostics
  env:
    MATRIX: ${{ toJSON(matrix) }}
    RUNNER_OS: ${{ runner.os }}
    RUNNER_ARCH: ${{ runner.arch }}
  run: |
    echo "Matrix: $MATRIX"
    echo "Runner OS: $RUNNER_OS"
    echo "Runner architecture: $RUNNER_ARCH"
    python --version
```

Do not print secrets.

---

## Reproduce a Single Matrix Cell

Once a failure is isolated:

```text
Full matrix
    ↓
Identify failed cell
    ↓
Run only failed configuration
```

For example:

```yaml
strategy:
  matrix:
    python: ["3.13"]
    database: ["postgres"]
```

This shortens the feedback loop while debugging.

Restore the full matrix after the fix.

---

## Production Matrix Architecture

```mermaid
flowchart TD
    A[Pull Request] --> B[Planning]

    B --> C[Matrix Generation]

    C --> D1[Python 3.11]
    C --> D2[Python 3.12]
    C --> D3[Python 3.13]

    D1 --> E[Integration Tests]
    D2 --> E
    D3 --> E

    E --> F[Coverage and Reports]
    F --> G[Fan-In]

    G --> H[Build Immutable Artifact]
    H --> I[Staging]
    I --> J[Approval]
    J --> K[Production]
```

The important architectural boundary is:

```text
Matrix = validation
```

rather than:

```text
Matrix = deployment
```

---

## Production Pipeline Pattern

A mature backend pipeline can use:

```text
Pull Request
    ↓
Lint
    ↓
Unit Tests
    ↓
Matrix Integration Tests
    ├── Python versions
    ├── Database versions
    └── Required compatibility combinations
    ↓
Security Scan
    ↓
Fan-In
    ↓
Docker Build
    ↓
Immutable Image
    ↓
ECR
    ↓
Staging
    ↓
Approval
    ↓
Production
    ↓
Monitoring
    ↓
Rollback
```

The matrix validates compatibility without producing multiple production artifacts unnecessarily.

---

## Matrix Design Rules

### Keep Dimensions Meaningful

Every dimension should correspond to a supported or intentionally tested configuration.

### Calculate Cardinality Before Implementation

Use:

```text
dimension₁ × dimension₂ × dimension₃
```

before committing the matrix.

### Separate Compatibility From Deployment

Testing multiple configurations does not mean deploying multiple configurations.

### Control Parallelism

Use:

```yaml
max-parallel
```

when downstream capacity requires backpressure.

### Use `fail-fast` Deliberately

Choose based on whether complete diagnostic coverage or early resource conservation matters.

### Make Artifacts Unique

Include matrix dimensions in artifact names.

### Keep Dynamic Matrices Validated

Validate generated JSON and allowed values.

### Treat Matrix Inputs as Untrusted Until Validated

Especially when generated from external or contributor-controlled data.

---

## Common Mistakes

### Testing Every Possible Combination

The Cartesian product often contains combinations nobody supports.

### Adding Dimensions Without Capacity Planning

A matrix can silently multiply CI cost.

### Using the Same Artifact Name

This makes results difficult to identify.

### Sharing Broad Caches

Incorrect cache keys can create cross-cell contamination.

### Deploying From a Matrix

This can accidentally create multiple deployments.

### Hiding Failures With `continue-on-error`

Use it for explicitly experimental combinations, not known supported failures.

### Using Dynamic Matrices Without Validation

Generated JSON can break the entire downstream workflow.

### Ignoring Service Capacity

Matrix parallelism can overload PostgreSQL, Redis, Kafka, or other dependencies.

### Treating Every Matrix Failure as an Application Bug

The failure may originate from the runner, dependency cache, service readiness, or infrastructure.

---

## Security Considerations

Matrix values can influence:

- Shell commands
- File paths
- Docker tags
- Artifact names
- AWS resources
- Deployment targets
- Runner selection

Therefore:

```text
Matrix value
   ↓
Validate
   ↓
Allowlist
   ↓
Use safely
```

For privileged jobs, do not allow arbitrary matrix data to determine:

```text
AWS account
IAM role
production environment
runner group
deployment target
```

---

## High Availability and Reliability

A matrix can improve compatibility confidence, but it can also increase failure surface.

Reliability considerations include:

- Deterministic dependencies
- Stable runner images
- Explicit service readiness
- Controlled concurrency
- Unique artifacts
- Reliable caches
- Timeouts
- Retry policies
- Failure isolation
- Clear aggregation

The goal is not maximum matrix size.

The goal is meaningful coverage with predictable execution.

---

## Disaster Recovery

Matrix configuration is part of CI/CD infrastructure.

Keep critical matrix definitions:

- Version controlled
- Reviewable
- Reproducible
- Documented
- Validated

If a generated matrix depends on external configuration, retain enough metadata to reconstruct the failed execution.

For production incidents, record:

```text
Commit SHA
Workflow run
Matrix cell
Runner
Dependency versions
Artifact digest
Deployment environment
```

This supports reproducibility and rollback.

---

## Monitoring and Observability

Track:

- Matrix job duration
- Queue time
- Failure rate by matrix cell
- Flaky failure rate
- Cache hit rate
- Service startup time
- Artifact generation failures
- Runner utilization
- Cost per workflow
- Most frequently failing configurations

A useful operational view is:

```text
Matrix Cell
    ↓
Pass / Fail / Cancelled
    ↓
Duration
    ↓
Failure Domain
    ↓
Trend
```

Repeated failures in one cell can reveal compatibility regressions before production impact.

---

## GitHub CLI Operations

List recent workflow runs:

```bash
gh run list
```

View a specific run:

```bash
gh run view <run-id>
```

View failed logs:

```bash
gh run view <run-id> --log-failed
```

Rerun failed jobs:

```bash
gh run rerun <run-id> --failed
```

List workflows:

```bash
gh workflow list
```

Trigger a workflow manually:

```bash
gh workflow run <workflow-file.yml>
```

These commands are useful for matrix incident investigation and controlled reruns.

---

## Operational Debugging Sequence

When a matrix workflow fails:

```text
1. Identify the failed matrix cell.
2. Determine whether other cells passed.
3. Compare the failing dimension against passing cells.
4. Inspect runner and environment differences.
5. Inspect dependency versions.
6. Inspect service readiness.
7. Inspect cache behavior.
8. Inspect artifacts and logs.
9. Reproduce only the failing cell.
10. Fix the root cause.
11. Restore the complete matrix.
12. Monitor subsequent runs.
```

This approach avoids wasting time debugging unrelated matrix combinations.

---

## Senior Troubleshooting Scenarios

### Scenario: 12 Jobs Suddenly Become 36

Calculate matrix cardinality.

If:

```text
Python = 3
Database = 2
OS = 2
Architecture = 3
```

then:

```text
3 × 2 × 2 × 3 = 36
```

The likely problem is matrix expansion, not runner instability.

---

### Scenario: Only Python 3.13 Fails

Compare:

```text
Python version
Dependency resolution
Native libraries
OS
Compiler
Application compatibility
```

Then isolate:

```yaml
matrix:
  python: ["3.13"]
```

Do not remove the supported runtime from the matrix without determining the compatibility cause.

---

### Scenario: Integration Tests Fail Randomly

Check:

```text
max-parallel
service readiness
database connection limits
test isolation
shared external dependencies
runner resource pressure
```

Then compare failures by matrix cell.

---

### Scenario: Matrix Tests Pass but Deployment Runs Multiple Times

The deployment job probably inherits the matrix.

Refactor:

```text
Matrix Tests
    ↓
Single Fan-In Job
    ↓
Single Deployment
```

Do not let compatibility dimensions leak into the deployment topology.

---

### Scenario: Dynamic Matrix Fails Before Any Test Runs

Inspect:

```text
Generator step
GITHUB_OUTPUT
Job outputs
needs
JSON
fromJSON()
```

Validate the generated JSON independently with `jq`.

---

### Scenario: CI Becomes Too Expensive

Measure:

```text
Matrix cardinality
×
Average duration
×
Workflow frequency
```

Then reduce low-value combinations, move broad compatibility testing to scheduled workflows, and use targeted PR matrices.

---

## Interview Questions

### How does a GitHub Actions matrix work?

Explain:

```text
Logical job
→ Matrix expansion
→ Independent job executions
→ Parallel scheduling
```

Each combination has its own runner execution and result.

### How do you calculate matrix size?

Multiply the number of values in each matrix dimension.

### When would you use `include`?

For additional metadata or specific combinations that do not fit a simple Cartesian product.

### When would you use `exclude`?

To remove unsupported combinations from the generated matrix.

### What does `fail-fast` do?

It controls whether other matrix executions may be cancelled when a matrix job fails.

### Why use `max-parallel`?

To limit simultaneous matrix execution and protect runner or downstream service capacity.

### How would you debug one failing matrix cell?

Reduce the matrix to that exact combination and compare it against passing cells.

### How do you prevent matrix artifacts from colliding?

Include matrix dimensions in artifact names and paths.

### How would you test Python and PostgreSQL compatibility?

Use a controlled matrix such as:

```text
Python × PostgreSQL
```

while keeping only supported combinations.

### Should every matrix combination deploy?

Usually no. Matrix testing should validate configurations, followed by a single build and controlled artifact promotion.

### How would you optimize a large matrix?

Consider:

- PR vs nightly matrices
- Supported combinations only
- Dynamic change detection
- `max-parallel`
- Caching
- Targeted compatibility coverage
- Separate release matrices

---

## Interview Scenario: Design a Production Matrix

Requirement:

```text
Python 3.11, 3.12, 3.13
PostgreSQL 16, 17
Redis
Django application
```

A reasonable architecture is:

```text
Python × PostgreSQL
        ↓
Redis service
        ↓
pytest
        ↓
Coverage
        ↓
Artifacts
        ↓
Fan-In
```

Do not add Redis as a matrix dimension unless Redis version compatibility is itself being tested.

---

## Interview Scenario: Protect Production

Requirement:

```text
Three Python versions must be tested.
Only one production deployment is allowed.
```

Design:

```text
Matrix Test
 ├── Python 3.11
 ├── Python 3.12
 └── Python 3.13
        ↓
    Fan-In
        ↓
      Build
        ↓
 Immutable Artifact
        ↓
    Production
```

Add deployment concurrency separately.

---

## Interview Scenario: AWS Deployment

Requirement:

```text
Run compatibility tests
Build Docker image
Push to ECR
Deploy to ECS
```

Do not give AWS deployment privileges to every matrix worker.

Prefer:

```text
Matrix Tests
    ↓
Build
    ↓
ECR
    ↓
Deployment Job
```

The deployment job can use:

```text
id-token: write
+
AWS OIDC
+
restricted IAM role
```

---

## Interview Scenario: Self-Hosted Runner

Requirement:

```text
Matrix tests need private PostgreSQL.
```

Consider:

```text
Private runner group
+
Appropriate labels
+
Network access
+
Runner capacity
+
Ephemeral runners where appropriate
```

Then control matrix concurrency so the database and runner fleet are not overloaded.

---

## Reference Architecture

```mermaid
flowchart TB
    A[Pull Request] --> B[Planning / Change Detection]

    B --> C[Matrix Generation]

    C --> D[Matrix Test Jobs]

    D --> D1[Python]
    D --> D2[Database]
    D --> D3[OS / Compatibility]

    D1 --> E[Reports]
    D2 --> E
    D3 --> E

    E --> F[Artifact Storage]
    F --> G[Fan-In Validation]

    G --> H[Docker Build]
    H --> I[ECR]

    I --> J[Staging]
    J --> K[Approval]
    K --> L[Production]

    L --> M[Monitoring]
    M --> N[Rollback]
```

The matrix belongs primarily in the validation stage.

---

## Production Checklist

### Matrix Definition

```text
[ ] Every dimension represents meaningful coverage
[ ] Unsupported combinations are excluded
[ ] Matrix cardinality is known
[ ] Dynamic matrices validate generated data
```

### Performance

```text
[ ] max-parallel is appropriate
[ ] Runner capacity is sufficient
[ ] Downstream services can handle parallelism
[ ] CI cost is monitored
```

### Reliability

```text
[ ] fail-fast behavior is intentional
[ ] Flaky cells are investigated
[ ] Timeouts are configured
[ ] Service readiness is reliable
[ ] Caches are correctly scoped
```

### Artifacts

```text
[ ] Artifact names are matrix-specific
[ ] Reports do not overwrite each other
[ ] Matrix metadata is preserved
[ ] Aggregation is explicit
```

### Security

```text
[ ] Matrix values are validated
[ ] Untrusted input cannot select privileged targets
[ ] Production deployment is not accidentally matrix-expanded
[ ] AWS roles are isolated from test jobs
[ ] Self-hosted runner labels are controlled
```

### Operations

```text
[ ] Matrix failures are easy to identify
[ ] Logs identify the matrix cell
[ ] CI duration is monitored
[ ] Queue time is monitored
[ ] Failed cells can be reproduced independently
```

## Key Takeaways

- A GitHub Actions matrix is a fan-out mechanism that expands one logical job into independent executions; its size grows multiplicatively across dimensions, so cardinality and capacity must be planned explicitly.
- Use `include`, `exclude`, `fail-fast`, and `max-parallel` deliberately to represent supported configurations, control diagnostic behavior, and protect runner and downstream service capacity.
- Troubleshoot matrix failures by isolating the failing cell and comparing it with passing cells across runtime, dependencies, services, caches, runners, and environment configuration.
- Keep matrix validation separate from deployment: test supported combinations in parallel, then fan in to a single immutable build and controlled staging/production promotion.
- Treat dynamic matrix values, artifact names, deployment targets, AWS resources, and runner selection as security-sensitive inputs that must be validated and constrained.