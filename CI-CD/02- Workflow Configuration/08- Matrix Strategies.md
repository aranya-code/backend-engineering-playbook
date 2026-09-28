# 08- Matrix Strategies

## Overview

GitHub Actions matrix strategies provide controlled fan-out: one logical job definition can execute multiple job instances using different combinations of configuration values.

For backend CI/CD, matrices are useful when the same validation must run across multiple:

- Python versions
- Operating systems
- Database versions
- Framework versions
- Dependency configurations
- Feature configurations
- Service combinations

A typical Python backend pipeline can use a matrix like:

```text
                         Test Job
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
          Python 3.11   Python 3.12   Python 3.13
              │             │             │
              ▼             ▼             ▼
           pytest        pytest        pytest
              │             │             │
              └─────────────┼─────────────┘
                            ▼
                       Test Results
```

The matrix is not a replacement for workflow design. It is a mechanism for generating parallel job instances from a declared set of dimensions.

A production pipeline should use matrices deliberately because the number of combinations can grow quickly.

---

## Why Matrix Strategies Exist

Without a matrix, testing multiple Python versions often leads to repetitive jobs:

```yaml
jobs:
  test-python-311:
    runs-on: ubuntu-latest
    steps:
      - run: pytest

  test-python-312:
    runs-on: ubuntu-latest
    steps:
      - run: pytest

  test-python-313:
    runs-on: ubuntu-latest
    steps:
      - run: pytest
```

The workflow duplicates the same logic.

A matrix moves the varying configuration into data:

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    runs-on: ubuntu-latest

    steps:
      - run: pytest
```

GitHub Actions expands this into separate job executions.

Conceptually:

```text
matrix:
  python-version:
    3.11
    3.12
    3.13

            ↓ expansion

test[3.11]
test[3.12]
test[3.13]
```

The job definition remains shared while the matrix values vary.

---

## Matrix Execution Model

A matrix belongs to a job's `strategy` configuration.

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    runs-on: ubuntu-latest
```

GitHub Actions creates one job execution for each matrix combination.

For one dimension:

```yaml
matrix:
  python-version: ["3.11", "3.12", "3.13"]
```

there are three combinations:

```text
python-version=3.11
python-version=3.12
python-version=3.13
```

For two dimensions:

```yaml
matrix:
  python-version: ["3.11", "3.12"]
  database: ["postgres", "mysql"]
```

the Cartesian product produces four combinations:

| Python | Database |
|---|---|
| 3.11 | PostgreSQL |
| 3.11 | MySQL |
| 3.12 | PostgreSQL |
| 3.12 | MySQL |

The number of jobs therefore grows multiplicatively.

For dimensions with sizes:

```text
Python = 3
Database = 2
OS = 2
```

the theoretical matrix contains:

```text
3 × 2 × 2 = 12 jobs
```

This is one of the most important operational characteristics of matrix strategies.

---

## Basic Matrix

A minimal Python testing matrix:

```yaml
name: Python CI

on:
  pull_request:

jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v5

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

The matrix value is accessed through:

```yaml
${{ matrix.python-version }}
```

The matrix context exists for the individual matrix job instance.

---

## Matrix Context

The `matrix` context exposes values for the current matrix combination.

Example:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]

steps:
  - name: Show Python version
    run: echo "Testing Python ${{ matrix.python-version }}"
```

For the first job:

```text
matrix.python-version = 3.11
```

For the second:

```text
matrix.python-version = 3.12
```

Matrix values can be used in:

- `runs-on`
- `name`
- `env`
- `if`
- action inputs
- shell commands
- job outputs
- cache keys
- artifact names

Example:

```yaml
- name: Upload coverage
  uses: actions/upload-artifact@v4
  with:
    name: coverage-python-${{ matrix.python-version }}
    path: coverage.xml
```

Unique artifact names are important when multiple matrix jobs upload similarly named files.

---

## Naming Matrix Jobs

The job identifier remains the same, but GitHub distinguishes matrix combinations.

You can make the workflow UI easier to understand with a dynamic job name:

```yaml
jobs:
  test:
    name: Python ${{ matrix.python-version }} / ${{ matrix.database }}
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
        database: [postgres, mysql]

    runs-on: ubuntu-latest
```

This produces readable executions such as:

```text
Python 3.11 / postgres
Python 3.11 / mysql
Python 3.12 / postgres
Python 3.12 / mysql
```

Clear matrix job names significantly improve CI troubleshooting.

---

## Multiple Dimensions

Multiple dimensions are useful when compatibility depends on more than one variable.

Example:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
    database: [postgres, mysql]
```

A backend test might configure services conditionally:

```yaml
jobs:
  integration-test:
    name: Python ${{ matrix.python-version }} / ${{ matrix.database }}

    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
        database: [postgres, mysql]

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v5

      - uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        env:
          DATABASE_ENGINE: ${{ matrix.database }}
        run: pytest
```

This approach is appropriate when every combination represents a meaningful compatibility target.

It is wasteful when the application only supports specific combinations.

---

## Matrix and Service Containers

A matrix can be combined with PostgreSQL, MySQL, or Redis service containers.

For example:

```yaml
jobs:
  integration-test:
    name: Python ${{ matrix.python-version }} / PostgreSQL ${{ matrix.postgres-version }}

    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
        postgres-version: ["15", "16"]

    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:${{ matrix.postgres-version }}
        env:
          POSTGRES_USER: app
          POSTGRES_PASSWORD: test-password
          POSTGRES_DB: app_test
        options: >-
          --health-cmd "pg_isready -U app -d app_test"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
```

The resulting combinations are:

```text
Python 3.11 + PostgreSQL 15
Python 3.11 + PostgreSQL 16
Python 3.12 + PostgreSQL 15
Python 3.12 + PostgreSQL 16
```

This is valuable for compatibility testing, but the cost grows rapidly.

---

## Matrix with Django

A Django application may test supported Python versions against a supported PostgreSQL range:

```yaml
jobs:
  test:
    name: Django tests / Python ${{ matrix.python-version }} / PostgreSQL ${{ matrix.postgres-version }}

    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
        postgres-version: ["15", "16"]

    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:${{ matrix.postgres-version }}
        env:
          POSTGRES_USER: django
          POSTGRES_PASSWORD: django
          POSTGRES_DB: django_test
        options: >-
          --health-cmd "pg_isready -U django -d django_test"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v5

      - uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run migrations and tests
        env:
          DATABASE_URL: postgresql://django:django@localhost:5432/django_test
        run: |
          python manage.py migrate
          pytest
```

This tests actual database integration rather than only Python-level compatibility.

---

## `include`

`include` adds or extends matrix combinations.

Example:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
    database: [postgres]

    include:
      - python-version: "3.13"
        database: postgres
        experimental: true
```

This can introduce an additional combination with metadata.

The added value can be consumed by the job:

```yaml
- name: Run experimental tests
  if: matrix.experimental == true
  run: pytest
```

A more useful production pattern is to attach environment-specific metadata:

```yaml
strategy:
  matrix:
    include:
      - python-version: "3.11"
        database: postgres
        allowed-to-fail: false

      - python-version: "3.12"
        database: postgres
        allowed-to-fail: false

      - python-version: "3.13"
        database: postgres
        allowed-to-fail: true
```

The exact behavior still needs to be expressed through job configuration such as `continue-on-error`.

---

## `exclude`

`exclude` removes combinations that should not be tested.

Example:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
    database: [postgres, mysql]

    exclude:
      - python-version: "3.11"
        database: mysql
```

The original four combinations become:

```text
3.11 + postgres
3.12 + postgres
3.12 + mysql
```

Use `exclude` when the Cartesian product is mostly valid but contains a small number of unsupported combinations.

---

## `include` vs `exclude`

| Feature | Purpose |
|---|---|
| `include` | Add metadata or additional combinations |
| `exclude` | Remove generated combinations |
| Multiple dimensions | Generate Cartesian product |
| Dynamic matrix | Generate dimensions at runtime |

A useful design rule:

```text
Mostly valid combinations
    ↓
matrix + exclude

Specific supported combinations
    ↓
matrix.include
```

If most combinations are invalid, a large `exclude` list becomes difficult to maintain. In that case, explicitly describing supported combinations with `include` is often clearer.

---

## Explicit Combination Matrices

When compatibility is irregular, use `include` directly.

```yaml
strategy:
  matrix:
    include:
      - python-version: "3.11"
        database: postgres
      - python-version: "3.12"
        database: postgres
      - python-version: "3.12"
        database: mysql
      - python-version: "3.13"
        database: postgres
```

This produces exactly the combinations required.

It avoids creating invalid combinations and then removing them.

---

## `fail-fast`

`fail-fast` controls whether GitHub Actions should cancel in-progress or queued matrix jobs when a matrix job fails.

Example:

```yaml
strategy:
  fail-fast: true
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
```

With:

```yaml
fail-fast: true
```

a failure in one matrix job can cause other in-progress or queued matrix jobs to be cancelled.

With:

```yaml
fail-fast: false
```

other matrix combinations continue executing even if one fails.

### When to Use `fail-fast: true`

Use it when:

- Fast feedback matters.
- A failure in one combination makes the remaining tests less useful.
- The matrix represents homogeneous validation.

### When to Use `fail-fast: false`

Use it when:

- You need complete compatibility information.
- Failures may be independent.
- Different OS/database combinations provide diagnostic value.
- You are investigating a compatibility regression.

For pull requests, `fail-fast: true` can reduce wasted CI time. For compatibility or release validation, `false` can provide a more complete failure picture.

---

## `continue-on-error` and Matrix Jobs

`continue-on-error` has different semantics from `fail-fast`.

`fail-fast` controls the behavior of other matrix executions after a failure.

`continue-on-error` controls whether a particular job failure is treated as non-fatal.

Example:

```yaml
strategy:
  fail-fast: false
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
    experimental: [false]
    include:
      - python-version: "3.13"
        experimental: true

continue-on-error: ${{ matrix.experimental }}
```

The experimental combination can fail without making the overall workflow fail.

This should be used carefully.

A production compatibility target should not be marked experimental simply to make the pipeline green.

---

## `max-parallel`

A matrix can generate many concurrent jobs.

`max-parallel` limits how many matrix jobs run simultaneously.

```yaml
strategy:
  max-parallel: 2
  matrix:
    python-version: ["3.11", "3.12", "3.13", "3.14"]
```

Without a limit, GitHub Actions can execute multiple combinations concurrently subject to the available concurrency capacity.

With:

```yaml
max-parallel: 2
```

at most two matrix jobs from that strategy execute simultaneously.

### Why Limit Parallelism?

Useful reasons include:

- Reducing resource pressure.
- Avoiding excessive external API load.
- Protecting shared test infrastructure.
- Controlling self-hosted runner capacity.
- Reducing concurrency-related test flakiness.
- Controlling CI cost.

The trade-off is longer execution time.

---

## Matrix Cost Model

Matrix size should be treated as an operational parameter.

For:

```text
Python = 3 versions
Database = 2 versions
OS = 2 versions
```

the matrix produces:

```text
3 × 2 × 2 = 12 jobs
```

If each job consumes 8 minutes:

```text
12 × 8 = 96 runner-minutes
```

Parallel execution reduces wall-clock duration but does not eliminate compute consumption.

Adding another dimension can increase cost dramatically:

```text
3 × 2 × 2 × 2 = 24 jobs
```

Therefore, matrix design should be based on actual compatibility requirements rather than "test everything."

---

## Matrix and Job Dependencies

A matrix job can be a dependency of another job.

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}
      - run: pytest

  build:
    needs: test
    runs-on: ubuntu-latest

    steps:
      - run: echo "All matrix tests passed"
```

Conceptually:

```text
              test[3.11]
             /          \
Build ←─────              \
             \          /
              test[3.12]
```

The dependent job normally waits for the required matrix executions to complete successfully.

This creates a fan-out/fan-in pattern:

```text
             ┌── test[3.11] ──┐
Build Input ─┼── test[3.12] ──┼── Build
             └── test[3.13] ──┘
```

---

## Matrix and `needs` with Partial Failure

When matrix jobs can fail intentionally, downstream behavior becomes more complex.

For example:

```yaml
continue-on-error: ${{ matrix.experimental }}
```

means an experimental failure may not block downstream execution.

Production pipelines should distinguish:

```text
Required matrix combinations
        ↓
Must pass

Experimental combinations
        ↓
Informational / allowed to fail
```

Do not make all matrix combinations non-blocking merely to improve pipeline throughput.

---

## Matrix Outputs

Matrix jobs can produce outputs, but there is an important architectural consideration: a matrix job has multiple executions.

A job-level output does not naturally represent a single scalar value when multiple matrix executions write the same output name.

For example:

```yaml
jobs:
  build:
    strategy:
      matrix:
        target: [linux, windows]

    outputs:
      artifact: ${{ steps.build.outputs.artifact }}

    steps:
      - id: build
        run: echo "artifact=result-${{ matrix.target }}" >> "$GITHUB_OUTPUT"
```

Both matrix executions conceptually produce an `artifact` output.

Do not design downstream workflows assuming that a matrix job's output automatically represents all matrix results as a collection.

When multiple values are required, use an explicit aggregation pattern.

---

## Aggregating Matrix Results

A robust pattern is:

```text
Matrix jobs
    ↓
Individual artifacts / outputs
    ↓
Aggregation job
    ↓
Single structured result
```

For example:

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    runs-on: ubuntu-latest

    steps:
      - run: |
          mkdir -p results
          echo "Python ${{ matrix.python-version }} passed" \
            > "results/${{ matrix.python-version }}.txt"

      - uses: actions/upload-artifact@v4
        with:
          name: result-${{ matrix.python-version }}
          path: results/

  aggregate:
    needs: test
    runs-on: ubuntu-latest

    steps:
      - uses: actions/download-artifact@v5
        with:
          pattern: result-*
          merge-multiple: true

      - name: Display results
        run: cat *.txt
```

Artifacts are often a better transport mechanism for many matrix-generated files than attempting to encode all values into job outputs.

---

## Dynamic Matrices

A static matrix is appropriate when supported combinations change infrequently.

Example:

```yaml
matrix:
  python-version: ["3.11", "3.12", "3.13"]
```

A dynamic matrix is useful when the combinations are generated from configuration.

The common pattern is:

```text
Generate configuration
        ↓
Serialize as JSON
        ↓
Job output
        ↓
fromJSON()
        ↓
Matrix expansion
```

This separates matrix definition from the workflow that executes the matrix.

---

## JSON-Based Dynamic Matrix

Example:

```yaml
jobs:
  generate-matrix:
    runs-on: ubuntu-latest

    outputs:
      matrix: ${{ steps.matrix.outputs.matrix }}

    steps:
      - id: matrix
        shell: bash
        run: |
          matrix='{
            "include": [
              {"python-version": "3.11", "database": "postgres"},
              {"python-version": "3.12", "database": "postgres"},
              {"python-version": "3.12", "database": "mysql"}
            ]
          }'

          echo "matrix=$matrix" >> "$GITHUB_OUTPUT"

  test:
    needs: generate-matrix
    strategy:
      matrix: ${{ fromJSON(needs.generate-matrix.outputs.matrix) }}

    runs-on: ubuntu-latest

    steps:
      - name: Display combination
        run: |
          echo "Python: ${{ matrix.python-version }}"
          echo "Database: ${{ matrix.database }}"
```

The important mechanism is:

```yaml
${{ fromJSON(needs.generate-matrix.outputs.matrix) }}
```

The output contains structured JSON, which is converted into a matrix definition.

---

## Generating a Matrix from Repository Configuration

A production system may keep compatibility data in a file:

```json
{
  "include": [
    {
      "python-version": "3.11",
      "database": "postgres"
    },
    {
      "python-version": "3.12",
      "database": "postgres"
    },
    {
      "python-version": "3.12",
      "database": "mysql"
    }
  ]
}
```

A workflow can read and expose this configuration:

```yaml
jobs:
  generate-matrix:
    runs-on: ubuntu-latest

    outputs:
      matrix: ${{ steps.matrix.outputs.matrix }}

    steps:
      - uses: actions/checkout@v5

      - id: matrix
        shell: bash
        run: |
          matrix="$(jq -c . .github/test-matrix.json)"
          echo "matrix=$matrix" >> "$GITHUB_OUTPUT"
```

Then:

```yaml
jobs:
  test:
    needs: generate-matrix

    strategy:
      matrix: ${{ fromJSON(needs.generate-matrix.outputs.matrix) }}

    runs-on: ubuntu-latest
```

This is useful when compatibility policy is maintained separately from workflow implementation.

---

## Dynamic Matrix Security

Dynamic matrices introduce a trust boundary.

Avoid constructing matrix configuration directly from untrusted pull request content.

For example, do not allow arbitrary pull request text to determine:

```text
shell commands
Docker images
repository names
deployment targets
AWS resources
```

A matrix should generally be generated from trusted repository configuration or tightly validated data.

A safe pattern is:

```text
Trusted repository configuration
        ↓
Validation
        ↓
JSON matrix
        ↓
GitHub Actions
```

rather than:

```text
Untrusted PR input
        ↓
JSON
        ↓
Matrix
        ↓
Shell command
```

---

## Matrix and `hashFiles()`

Matrix values can participate in cache keys.

Example:

```yaml
- name: Cache Python dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('**/requirements*.txt') }}
    restore-keys: |
      pip-${{ runner.os }}-${{ matrix.python-version }}-
```

This prevents Python 3.11 and Python 3.12 jobs from accidentally sharing incompatible dependency caches.

A good cache key usually includes every input that materially changes the cached content.

---

## Matrix-Specific Artifact Naming

Matrix jobs must avoid artifact-name collisions.

Bad:

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: reports/
```

Multiple matrix jobs are attempting to produce the same artifact name.

Prefer:

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: test-results-python-${{ matrix.python-version }}
    path: reports/
```

For multiple dimensions:

```yaml
name: test-results-${{ matrix.python-version }}-${{ matrix.database }}
```

This makes the artifact traceable to the matrix combination.

---

## Matrix and Test Coverage

Each matrix execution should produce independently identifiable coverage data.

Example:

```yaml
- name: Run tests
  run: |
    pytest \
      --cov=app \
      --cov-report=xml:coverage.xml

- name: Upload coverage
  uses: actions/upload-artifact@v4
  with:
    name: coverage-${{ matrix.python-version }}
    path: coverage.xml
```

Do not blindly merge coverage reports from incompatible test environments.

If a single aggregate coverage result is required, explicitly define how reports are combined and which matrix combinations contribute to the metric.

---

## Matrix and Docker Builds

Matrices can build Docker images for different targets.

Example:

```yaml
strategy:
  matrix:
    platform:
      - linux/amd64
      - linux/arm64
```

This can be useful for multi-platform images.

However, Docker Buildx is generally more appropriate for producing one multi-platform image manifest than treating every architecture as an unrelated application build.

For example:

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build multi-platform image
  uses: docker/build-push-action@v6
  with:
    context: .
    platforms: linux/amd64,linux/arm64
    push: true
    tags: ghcr.io/example/backend:${{ github.sha }}
```

Use a matrix when each combination requires independent workflow behavior. Use Buildx's platform support when the objective is simply a multi-platform container image.

---

## Matrix and Operating Systems

Testing across operating systems can reveal platform-specific behavior.

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest]
    python-version: ["3.11", "3.12"]

runs-on: ${{ matrix.os }}
```

This produces four combinations.

For a Linux-focused backend, testing Windows may provide little value unless the project explicitly supports it.

Matrix dimensions should reflect supported product behavior, not theoretical possibilities.

---

## Matrix and Environment Variables

Matrix values can be mapped into environment variables:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]

steps:
  - name: Run tests
    env:
      PYTHON_VERSION: ${{ matrix.python-version }}
    run: pytest
```

For structured configuration, it can be cleaner to use explicit environment variables:

```yaml
env:
  DATABASE_ENGINE: ${{ matrix.database }}
```

Avoid using environment variables when the value should instead remain a workflow expression.

---

## Matrix with Conditional Steps

A matrix value can control individual steps.

```yaml
strategy:
  matrix:
    include:
      - python-version: "3.11"
        run-performance: false

      - python-version: "3.12"
        run-performance: true
```

Then:

```yaml
- name: Run performance tests
  if: matrix.run-performance
  run: pytest tests/performance
```

This is useful when only selected matrix combinations should perform expensive validation.

It avoids creating a separate workflow when the difference is small and closely related to the matrix dimension.

---

## Matrix with Conditional Jobs

A matrix can also influence whether a job executes.

```yaml
jobs:
  deploy:
    if: github.ref == 'refs/heads/main'
    strategy:
      matrix:
        environment: [staging, production]

    runs-on: ubuntu-latest
```

However, deployment matrices should be treated carefully.

A matrix can unintentionally create:

```text
deploy[staging]
deploy[production]
```

simultaneously.

For sequential promotion:

```text
Build
  ↓
Staging
  ↓
Approval
  ↓
Production
```

separate jobs with explicit `needs` and environments are generally easier to reason about than a deployment matrix.

---

## Matrix and Reusable Workflows

Matrices can call reusable workflows.

Example:

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    uses: organization/.github/.github/workflows/python-ci.yml@v1

    with:
      python-version: ${{ matrix.python-version }}
```

This allows the organization to centralize CI implementation while allowing repositories to define their compatibility matrix.

Conceptually:

```text
Repository A ──┐
Repository B ──┼──> Reusable CI Workflow
Repository C ──┘
                    │
                    ├── Python 3.11
                    ├── Python 3.12
                    └── Python 3.13
```

This is particularly useful for organizations maintaining many Python services.

---

## Matrix and Reusable Workflow Outputs

When a matrix calls reusable workflows, output handling becomes more subtle because multiple executions exist.

Do not assume a single workflow output automatically represents all matrix results.

Prefer:

```text
Matrix execution
    ↓
Individual result
    ↓
Artifact or structured record
    ↓
Aggregation job
```

This makes the data model explicit.

---

## Matrix and Concurrency

Matrix parallelism and GitHub Actions concurrency solve different problems.

| Mechanism | Purpose |
|---|---|
| Matrix | Generate multiple job combinations |
| `max-parallel` | Limit concurrent matrix jobs |
| `concurrency` | Coordinate workflow/job executions |
| `fail-fast` | Cancel other matrix jobs after failure |
| `needs` | Define job dependencies |

For example:

```yaml
strategy:
  fail-fast: false
  max-parallel: 3
  matrix:
    python-version: ["3.11", "3.12", "3.13", "3.14"]
```

This controls the matrix itself.

A separate concurrency group can control duplicate workflow executions:

```yaml
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

Do not confuse these mechanisms.

---

## Matrix and Self-Hosted Runners

A large matrix can overwhelm a self-hosted runner pool.

Example:

```text
Matrix
 ├── Python 3.11
 ├── Python 3.12
 ├── Python 3.13
 ├── PostgreSQL 15
 ├── PostgreSQL 16
 └── Windows
```

If only two matching runners exist, the matrix jobs will queue.

Use:

```yaml
strategy:
  max-parallel: 2
```

when explicit control is needed.

Runner labels can also be selected dynamically:

```yaml
strategy:
  matrix:
    runner: [linux, windows]

runs-on: ${{ matrix.runner }}
```

The labels must correspond to the configured runner labels.

For untrusted pull request code, self-hosted runners require particular caution because workloads may have access to the runner host or private network resources.

---

## Matrix and External Services

Matrix jobs can unintentionally create load against shared services.

For example:

```text
10 matrix jobs
      ↓
same PostgreSQL server
      ↓
connection spike
```

or:

```text
10 jobs
   ↓
same external API
   ↓
rate limiting
```

Consider:

- `max-parallel`
- isolated service containers
- dedicated test databases
- test data isolation
- API mocks
- rate-limit handling
- ephemeral infrastructure

The matrix should increase test coverage without creating an uncontrolled dependency load.

---

## Matrix Data Isolation

Parallel matrix jobs must not assume shared mutable state.

Avoid:

```text
Matrix Job A ──┐
Matrix Job B ──┼──> same test database/schema
Matrix Job C ──┘
```

unless the test design explicitly supports concurrent execution.

Prefer:

```text
Job A → isolated database
Job B → isolated database
Job C → isolated database
```

or unique namespaces:

```text
test-${{ github.run_id }}-${{ matrix.python-version }}
```

This prevents one matrix execution from corrupting another execution's state.

---

## Matrix and Database Testing

For database compatibility testing, a matrix can combine:

```yaml
strategy:
  matrix:
    database:
      - postgres-15
      - postgres-16
```

A more scalable architecture can map versions to images:

```yaml
strategy:
  matrix:
    include:
      - database: postgres
        version: "15"

      - database: postgres
        version: "16"

      - database: mysql
        version: "8.0"
```

Then:

```yaml
services:
  database:
    image: ${{ matrix.database == 'postgres' && format('postgres:{0}', matrix.version) || format('mysql:{0}', matrix.version) }}
```

For complex service configuration, explicit `include` records can be easier to maintain than deeply nested expressions.

---

## Matrix and Caching

Caching is especially important when a matrix repeats dependency installation.

A useful Python cache key includes:

```text
OS
Python version
Dependency lockfile
```

Example:

```yaml
- name: Set up Python
  uses: actions/setup-python@v6
  with:
    python-version: ${{ matrix.python-version }}
    cache: pip
    cache-dependency-path: |
      requirements.txt
      requirements-dev.txt
```

The Python version matters because packages containing compiled extensions may not be interchangeable between Python runtimes.

For explicit caching:

```yaml
- name: Cache pip
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('**/requirements*.txt') }}
```

Avoid sharing caches across incompatible matrix dimensions.

---

## Matrix and Security

Matrix values can affect commands, artifact paths, image names, and deployment targets.

Treat matrix values as configuration, not automatically trusted input.

Avoid constructing shell commands from untrusted data:

```yaml
- run: pytest tests/${{ matrix.test-path }}
```

If `matrix.test-path` can originate from untrusted content, command construction may create injection risks.

Prefer environment-variable boundaries where practical:

```yaml
- name: Run tests
  env:
    TEST_PATH: ${{ matrix.test-path }}
  run: |
    pytest "$TEST_PATH"
```

Even then, validate that the value represents an expected path.

The strongest approach is to generate matrix values from trusted repository configuration.

---

## Matrix and Secrets

Matrix values should not contain secrets.

Avoid:

```yaml
matrix:
  database-password:
    - super-secret-value
```

Matrix configuration is workflow configuration and should not be treated as a secret store.

Use:

```yaml
env:
  DATABASE_PASSWORD: ${{ secrets.DATABASE_PASSWORD }}
```

or environment-scoped secrets where appropriate.

If different matrix combinations require different credentials, use an explicit mapping strategy rather than embedding credentials in the matrix.

---

## Matrix and Artifacts

Artifacts are appropriate for preserving matrix-specific outputs.

Typical outputs include:

- Coverage reports
- JUnit XML
- Logs
- Build packages
- Test results
- Generated documentation
- Diagnostic files

Example:

```yaml
- name: Upload test report
  uses: actions/upload-artifact@v4
  if: ${{ !cancelled() }}
  with:
    name: pytest-${{ matrix.python-version }}
    path: |
      test-results.xml
      coverage.xml
    retention-days: 7
```

Artifacts preserve execution results.

Caches exist to accelerate future workflows.

They are not interchangeable.

---

## Matrix and Test Reporting

A production test matrix should make failures attributable to specific combinations.

Prefer:

```text
Python 3.11 / PostgreSQL 15
    FAILED

Python 3.11 / PostgreSQL 16
    PASSED

Python 3.12 / PostgreSQL 15
    PASSED

Python 3.12 / PostgreSQL 16
    FAILED
```

rather than:

```text
Integration tests failed
```

Use matrix values in:

- Job names
- Artifact names
- Logs
- Test report metadata
- Cache keys

This significantly reduces diagnosis time.

---

## Matrix Failure Troubleshooting

Use the standard failure-domain model:

```text
Symptom
    ↓
Possible Causes
    ↓
Isolation Strategy
    ↓
Commands / Checks
    ↓
Root Cause
    ↓
Corrective Action
    ↓
Prevention
```

### Matrix Generates Unexpected Number of Jobs

**Possible causes**

- Multiple dimensions create a Cartesian product.
- `include` adds combinations.
- `exclude` does not remove the expected combination.
- Dynamic JSON contains unexpected entries.

**Isolation**

Calculate the expected matrix size manually.

For example:

```text
Python = 3
Database = 2
OS = 2

Expected = 3 × 2 × 2 = 12
```

Then inspect the generated configuration.

**Prevention**

Prefer explicit `include` when only a small subset of combinations is valid.

---

### Matrix Job Is Not Running

**Possible causes**

- Job-level `if` evaluates to false.
- Matrix combination was excluded.
- `needs` dependency failed.
- Workflow was cancelled.
- Concurrency cancelled the workflow.

Check:

```yaml
if: ...
```

and:

```yaml
needs:
  - previous-job
```

Also inspect the workflow run graph.

---

### Matrix Jobs Are Too Slow

**Possible causes**

- `max-parallel` is too low.
- Runner capacity is insufficient.
- Dependency installation dominates execution.
- Service containers take too long to initialize.
- Matrix is testing unnecessary combinations.

**Corrections**

- Improve dependency caching.
- Increase runner capacity where appropriate.
- Adjust `max-parallel`.
- Reduce redundant combinations.
- Use more targeted integration matrices.

---

### Matrix Jobs Exhaust CI Capacity

A matrix such as:

```text
4 Python versions
× 3 databases
× 2 operating systems
× 2 dependency modes
```

creates:

```text
48 jobs
```

That can be expensive and operationally noisy.

Use:

```yaml
max-parallel: 4
```

and reconsider whether all 48 combinations provide meaningful coverage.

---

### Matrix Output Is Unexpected

**Possible causes**

- Multiple matrix executions write the same output.
- Downstream job expects one value but receives only one matrix result.
- JSON is malformed.
- Output contains shell-escaping problems.

For collections of results, prefer artifacts or an explicit aggregation job.

---

### Dynamic Matrix Fails to Expand

Check the generated JSON:

```bash
jq . matrix.json
```

Validate that the output is valid JSON before passing it to:

```yaml
fromJSON(...)
```

A malformed output can cause the matrix job to fail before any matrix execution begins.

---

## Production Matrix Design

A production CI matrix should normally be divided into tiers.

### Fast PR Matrix

```text
Python supported versions
+
Primary database
+
Unit/integration tests
```

Keep feedback fast.

### Extended Compatibility Matrix

```text
Python versions
+
Database versions
+
Selected operating systems
```

Run on pull requests or scheduled workflows depending on execution cost.

### Release Matrix

```text
Supported Python versions
+
Supported databases
+
Critical integration tests
+
Security validation
+
Build verification
```

Run before a release or production promotion.

This avoids making every pull request execute the most expensive possible matrix.

---

## Scheduled Compatibility Testing

Some compatibility combinations do not need to run on every pull request.

For example:

```yaml
on:
  pull_request:

  schedule:
    - cron: "0 2 * * 1"
```

The pull request workflow can use a small matrix while the scheduled workflow executes the full compatibility matrix.

This creates:

```text
Pull Request
    ↓
Fast Matrix
    ↓
Developer Feedback

Scheduled
    ↓
Extended Matrix
    ↓
Compatibility Monitoring
```

The choice should be based on failure detection requirements and CI cost.

---

## Matrix Architecture

A mature matrix architecture separates compatibility definition from execution.

```mermaid
flowchart TD
    CONFIG[Trusted Compatibility Configuration]
    CONFIG --> GENERATE[Generate Matrix JSON]
    GENERATE --> MATRIX[Matrix Expansion]

    MATRIX --> PY311[Python 3.11]
    MATRIX --> PY312[Python 3.12]
    MATRIX --> PY313[Python 3.13]

    PY311 --> TEST1[Tests]
    PY312 --> TEST2[Tests]
    PY313 --> TEST3[Tests]

    TEST1 --> AGGREGATE[Aggregate Results]
    TEST2 --> AGGREGATE
    TEST3 --> AGGREGATE

    AGGREGATE --> BUILD[Build]
```

This architecture is particularly useful when supported combinations are maintained centrally.

---

## Matrix in a Production CI Pipeline

A complete backend pipeline might use matrix testing like this:

```text
Pull Request
     │
     ▼
Lint
     │
     ▼
Matrix Tests
     │
     ├── Python 3.11
     ├── Python 3.12
     └── Python 3.13
             │
             ▼
      Integration Tests
             │
             ├── PostgreSQL
             └── Redis
             │
             ▼
       Aggregate Results
             │
             ▼
           Build
             │
             ▼
        Docker Image
             │
             ▼
             ECR
```

The matrix should validate compatibility before the immutable artifact is produced.

---

## Matrix Design Trade-Offs

| Decision | Advantage | Limitation |
|---|---|---|
| More dimensions | Greater compatibility coverage | Rapid job growth |
| `fail-fast: true` | Faster failure feedback | Less diagnostic information |
| `fail-fast: false` | Complete failure visibility | More runner consumption |
| High `max-parallel` | Lower wall-clock time | More resource pressure |
| Low `max-parallel` | Controlled resource use | Longer execution |
| Static matrix | Simple and predictable | Requires workflow edits |
| Dynamic matrix | Centralized flexible configuration | More complexity |
| `include` | Precise combinations | More verbose |
| Cartesian matrix | Concise configuration | Can create unwanted combinations |
| Full compatibility matrix on PRs | Early detection | Slower and more expensive CI |
| Extended matrix on schedule | Lower PR cost | Delayed compatibility feedback |

---

## Common Mistakes

### Testing Every Possible Combination

A large matrix is not automatically better.

If:

```text
Python × Database × OS × Dependency Mode
```

produces dozens of jobs, determine whether every combination represents a supported product configuration.

Test the compatibility contract, not every theoretical combination.

### Forgetting Cartesian Product Behavior

This:

```yaml
matrix:
  python: ["3.11", "3.12"]
  database: [postgres, mysql]
```

does not produce two jobs.

It produces four.

### Reusing Artifact Names

Every matrix execution should produce unique artifact names.

### Sharing Mutable Test Infrastructure

Parallel jobs should not unintentionally modify the same database, filesystem, or external service state.

### Ignoring Cache Dimensions

A Python 3.11 cache should not be reused blindly by Python 3.13.

### Using Dynamic Matrix Data from Untrusted Input

A matrix can influence execution behavior. Treat dynamically generated configuration as a security boundary.

### Making Experimental Jobs Non-Blocking Indiscriminately

`continue-on-error` should represent an intentional compatibility policy, not a mechanism for hiding failures.

### Using a Matrix for Sequential Deployment

Deployment promotion is generally easier to reason about with explicit dependencies:

```text
Staging
   ↓
Approval
   ↓
Production
```

rather than:

```text
matrix:
  environment:
    - staging
    - production
```

which naturally creates parallel executions unless additional dependency design is introduced.

---

## Performance and Scalability

Matrix performance depends on four variables:

```text
Matrix Size
    +
Job Duration
    +
Parallel Capacity
    +
External Dependency Capacity
```

A useful optimization sequence is:

1. Remove combinations that do not represent supported configurations.
2. Cache dependencies.
3. Reduce unnecessary setup work.
4. Increase parallelism when runner capacity permits.
5. Use service containers or isolated test infrastructure appropriately.
6. Move expensive compatibility testing to scheduled or release workflows.

Do not optimize only for wall-clock duration.

A workflow that finishes quickly by launching 50 expensive jobs may be less operationally efficient than a slightly slower workflow with a carefully designed matrix.

---

## Reliability Considerations

Matrix jobs should be deterministic and independently repeatable.

Avoid tests that depend on execution order:

```text
test[3.11] must run before test[3.12]
```

unless that dependency is explicitly modeled.

Prefer:

```text
test[3.11] ── independent
test[3.12] ── independent
test[3.13] ── independent
```

Then aggregate the results.

If a matrix combination requires a dependency, encode it through `needs` or a separate orchestration design rather than relying on execution order.

---

## High Availability and Failure Isolation

A matrix naturally provides failure isolation because each combination runs independently.

For example:

```text
Python 3.11 ── PASS
Python 3.12 ── FAIL
Python 3.13 ── PASS
```

The failure can be localized to Python 3.12.

However, matrix isolation does not protect against shared infrastructure failures.

If every matrix job depends on the same external database:

```text
                 ┌── Test A
Shared Database ─┼── Test B
                 └── Test C
```

a database outage can make every matrix job fail.

For critical integration testing, isolate or make shared dependencies highly available where practical.

---

## Security Considerations

Matrix strategies should follow the same security principles as the rest of the workflow.

### Keep Matrix Configuration Trusted

Prefer repository-controlled configuration:

```text
.github/
    test-matrix.json
```

over dynamically evaluating arbitrary external input.

### Avoid Secrets in Matrix Values

Use the secrets context:

```yaml
env:
  API_TOKEN: ${{ secrets.API_TOKEN }}
```

rather than embedding sensitive values into matrix configuration.

### Quote Shell Inputs

If a matrix value reaches a shell:

```yaml
- name: Run selected tests
  env:
    TEST_TARGET: ${{ matrix.test-target }}
  run: pytest "$TEST_TARGET"
```

Validate the value when it can originate outside trusted repository configuration.

### Restrict Deployment Matrices

A matrix that controls deployments can multiply the blast radius of a configuration error.

Prefer explicit deployment jobs for critical environments.

---

## Monitoring and Operations

Monitor matrix behavior over time.

Useful operational metrics include:

- Matrix job count
- Average matrix duration
- Failure rate per combination
- Retry frequency
- Queue time
- Cache hit rate
- Service-container startup time
- Runner utilization
- CI compute consumption

A recurring failure such as:

```text
Python 3.12 + PostgreSQL 16
```

should be visible as a specific compatibility problem rather than appearing only as a generic workflow failure.

Matrix-specific job names and artifacts make this correlation easier.

---

## Senior-Level Matrix Design

At senior level, the question is not:

> "How do I create a matrix?"

The important questions are:

- What compatibility contract are we validating?
- Which combinations are actually supported?
- Which combinations need to run on every pull request?
- Which combinations can run on a schedule?
- How many jobs will the matrix create?
- What is the CI cost?
- Can the runner fleet handle the concurrency?
- Are shared dependencies isolated?
- How are results aggregated?
- How are matrix failures reported?
- Can matrix configuration be trusted?
- Does the matrix interact with deployment or production environments?
- Which combinations are required for release approval?

A mature design treats the matrix as a compatibility model:

```text
Supported Compatibility Contract
            │
            ▼
     Matrix Definition
            │
            ▼
       Job Expansion
            │
      ┌─────┼─────┐
      ▼     ▼     ▼
   Target Target Target
      │     │     │
      └─────┼─────┘
            ▼
      Result Aggregation
            │
            ▼
       Build / Release
```

The matrix is therefore part of CI architecture, not merely YAML convenience.

---

## Interview Traps

### What Is the Difference Between Matrix and Parallel Jobs?

A matrix is a declarative mechanism for generating multiple job instances from combinations of configuration values.

Parallel jobs can be created manually without a matrix.

Matrix strategies reduce duplication and make compatibility dimensions explicit.

### What Happens with Two Matrix Dimensions?

GitHub Actions generates combinations from the dimensions.

For:

```yaml
python: ["3.11", "3.12"]
database: [postgres, mysql]
```

the result is:

```text
3.11 + postgres
3.11 + mysql
3.12 + postgres
3.12 + mysql
```

### What Is `fail-fast`?

It controls whether GitHub Actions cancels other matrix executions when one fails.

It does not mean "make the failing job successful."

### What Is `max-parallel`?

It limits the number of matrix jobs that can execute concurrently for that strategy.

It does not reduce the total number of matrix combinations.

### `fail-fast` vs `continue-on-error`

`fail-fast` controls other matrix executions.

`continue-on-error` controls whether a particular job failure is treated as non-fatal.

They solve different problems.

### Static vs Dynamic Matrix

A static matrix is simple and predictable.

A dynamic matrix is useful when supported combinations come from configuration or another job.

Dynamic matrices introduce additional complexity around:

- JSON serialization
- outputs
- validation
- security
- debugging

### Why Not Put All Environments in a Deployment Matrix?

A deployment matrix naturally represents independent combinations.

Production promotion is often sequential and authorization-sensitive:

```text
Staging
   ↓
Validation
   ↓
Approval
   ↓
Production
```

Explicit jobs with `needs` and environment protection usually make this dependency clearer.

### How Would You Reduce a 60-Job Matrix?

First determine whether all combinations are actually supported.

Then consider:

```text
Remove invalid combinations
        ↓
Use include/exclude
        ↓
Split fast and extended matrices
        ↓
Schedule expensive compatibility tests
        ↓
Use max-parallel
        ↓
Improve caching
```

Do not simply reduce coverage without understanding what compatibility the product promises.

---

## Production Checklist

- [ ] Matrix dimensions represent supported compatibility requirements.
- [ ] Cartesian-product growth has been calculated.
- [ ] Invalid combinations are excluded.
- [ ] `include` is used for irregular compatibility sets.
- [ ] `fail-fast` behavior is intentional.
- [ ] `continue-on-error` is limited to explicitly non-blocking combinations.
- [ ] `max-parallel` matches runner and dependency capacity.
- [ ] Matrix job names identify the relevant combination.
- [ ] Cache keys include relevant matrix dimensions.
- [ ] Artifact names are unique per matrix combination.
- [ ] Test databases and mutable infrastructure are isolated.
- [ ] Dynamic matrices are generated from trusted configuration.
- [ ] Matrix values are not used to expose secrets.
- [ ] Shell inputs derived from matrix values are handled safely.
- [ ] Expensive compatibility testing is separated from fast PR validation where appropriate.
- [ ] Matrix results are aggregated explicitly when required.
- [ ] Downstream jobs depend on the correct matrix completion state.
- [ ] Matrix behavior is observable through job names, artifacts, and logs.
- [ ] Deployment matrices are avoided when sequential promotion is required.

---

## Key Takeaways

- Matrix strategies generate independent job executions from declared configuration dimensions, making compatibility testing concise and repeatable.
- Matrix size grows multiplicatively across dimensions, so supported combinations, CI cost, runner capacity, and external dependency load must be considered together.
- `include`, `exclude`, `fail-fast`, `continue-on-error`, and `max-parallel` solve different problems and should be configured deliberately.
- Dynamic matrices are powerful for centrally managed compatibility data but require explicit JSON handling, validation, output management, and security controls.
- Production-grade matrix design treats compatibility as an engineering contract and integrates testing, caching, artifacts, aggregation, observability, and release gating into the broader CI/CD architecture.