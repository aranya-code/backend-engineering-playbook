# 09- Matrix Include and Exclude

## Overview

GitHub Actions matrix strategies are useful when the same job must run across multiple configurations such as Python versions, operating systems, databases, framework versions, or deployment targets.

A basic matrix generates the Cartesian product of its dimensions. `include` and `exclude` provide controlled ways to modify that generated set:

```text
Base Matrix
    │
    ├── exclude → Remove combinations
    │
    └── include → Add or extend combinations
                     │
                     ▼
              Final Matrix
                     │
                     ▼
             Matrix Job Runs
```

This is important in production CI because real test environments are rarely a perfect Cartesian product. Some combinations may be unsupported, expensive, unnecessary, or require special configuration.

For example, a backend may normally test:

```text
Python:   3.11, 3.12, 3.13
Database: PostgreSQL, MySQL
```

The basic matrix produces six jobs. However, perhaps MySQL is only supported on Python 3.11 and 3.12, while Python 3.13 requires an additional experimental dependency.

`include` and `exclude` allow the matrix to represent those real-world constraints without duplicating entire workflows.

---

## Matrix Expansion Model

Consider:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
    database: ["postgres", "mysql"]
```

GitHub Actions conceptually expands this into:

| Python | Database |
|---|---|
| 3.11 | postgres |
| 3.11 | mysql |
| 3.12 | postgres |
| 3.12 | mysql |

The matrix job is therefore not one execution. It is a collection of independent job executions.

Each execution receives its own `matrix` context:

```yaml
${{ matrix.python-version }}
${{ matrix.database }}
```

This expansion happens before the individual matrix jobs execute.

---

## Why `exclude` Exists

`exclude` removes specific combinations from the generated Cartesian product.

Use it when:

- A combination is unsupported.
- A combination is redundant.
- A dependency does not support a particular runtime.
- A platform/database combination cannot be tested.
- A specific configuration is too expensive.
- A known incompatibility should not block the entire matrix.

### Basic Example

```yaml
name: Backend Tests

on:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
        database: ["postgres", "mysql"]

        exclude:
          - python-version: "3.13"
            database: "mysql"

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}

      - name: Run tests
        run: pytest
```

The original six combinations become five:

| Python | Database | Result |
|---|---|---|
| 3.11 | postgres | Run |
| 3.11 | mysql | Run |
| 3.12 | postgres | Run |
| 3.12 | mysql | Run |
| 3.13 | postgres | Run |
| 3.13 | mysql | Excluded |

The exclusion is based on the complete combination:

```yaml
- python-version: "3.13"
  database: "mysql"
```

---

## How `exclude` Matching Works

An `exclude` entry matches matrix properties.

For example:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest]
    python: ["3.11", "3.12"]

    exclude:
      - os: windows-latest
        python: "3.11"
```

The generated matrix is:

```text
ubuntu-latest + Python 3.11
ubuntu-latest + Python 3.12
windows-latest + Python 3.12
```

The following combination is removed:

```text
windows-latest + Python 3.11
```

The exclusion should describe the dimensions necessary to identify the combinations that must be removed.

---

## Excluding Multiple Combinations

Multiple exclusions can be specified:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    python: ["3.11", "3.12", "3.13"]

    exclude:
      - os: windows-latest
        python: "3.11"

      - os: macos-latest
        python: "3.11"

      - os: windows-latest
        python: "3.13"
```

This allows the matrix to represent platform-specific support.

However, large numbers of exclusions can indicate that the base matrix does not accurately represent the application's supported combinations.

---

## When to Prefer `exclude`

Use `exclude` when the matrix is fundamentally a Cartesian product and only a relatively small number of combinations are invalid.

A useful mental model is:

```text
Most combinations are valid
        │
        ▼
Generate broad matrix
        │
        ▼
Remove exceptional combinations
        │
        ▼
Final matrix
```

For example:

```text
3 Python versions
×
3 operating systems
=
9 combinations

2 combinations unsupported

9 - 2 = 7 jobs
```

This is easier to maintain than manually listing all seven valid combinations.

---

## Why `include` Exists

`include` allows additional configuration to be associated with matrix combinations or allows additional matrix combinations to be added.

It is useful when some combinations require extra metadata:

```text
Python 3.11 + PostgreSQL
    → standard configuration

Python 3.12 + PostgreSQL
    → standard configuration

Python 3.13 + PostgreSQL
    → experimental configuration
```

The additional information can be exposed through the matrix context.

---

## Adding Metadata with `include`

Consider:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]

    include:
      - python-version: "3.12"
        experimental: true
```

The additional property can then be accessed as:

```yaml
${{ matrix.experimental }}
```

This is useful for conditional behavior.

For example:

```yaml
- name: Run experimental checks
  if: ${{ matrix.experimental == true }}
  run: pytest tests/experimental
```

The matrix can therefore carry configuration in addition to its primary dimensions.

---

## Adding Environment-Specific Configuration

A production-oriented example is associating deployment metadata with a matrix dimension:

```yaml
strategy:
  matrix:
    environment:
      - name: staging
        region: us-east-1
      - name: production
        region: us-east-2
```

For more complex configuration, JSON-based matrices are often easier to generate dynamically. For statically defined workflows, simple scalar dimensions plus `include` are generally easier to review.

A common pattern is:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]

    include:
      - python-version: "3.13"
        allow-failure: true
```

Then:

```yaml
continue-on-error: ${{ matrix.allow-failure || false }}
```

This allows an experimental runtime to behave differently without creating an entirely separate job definition.

---

## Adding a New Combination with `include`

`include` can also introduce a combination that did not exist in the original Cartesian product.

Example:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]

    include:
      - python-version: "3.13"
        experimental: true
```

The original matrix contains:

```text
3.11
3.12
```

The resulting matrix can contain:

```text
3.11
3.12
3.13
```

The important distinction is that `3.13` was not generated by the original matrix dimension.

This makes `include` useful for controlled exceptions and special cases.

---

## `include` as Matrix Metadata

One of the most useful production patterns is to attach metadata to a normal matrix combination.

For example:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]

    include:
      - python-version: "3.13"
        experimental: true
        coverage: false
```

The job can use:

```yaml
- name: Run tests
  run: pytest

- name: Upload coverage
  if: ${{ matrix.coverage != false }}
  run: pytest --cov=. --cov-report=xml
```

This allows one workflow to represent different execution policies.

---

## `include` with Multiple Dimensions

Consider:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest]
    python: ["3.11", "3.12"]

    include:
      - os: ubuntu-latest
        python: "3.12"
        test-type: integration

      - os: windows-latest
        python: "3.12"
        test-type: compatibility
```

The added properties can be used by steps:

```yaml
- name: Run integration tests
  if: ${{ matrix.test-type == 'integration' }}
  run: pytest tests/integration

- name: Run compatibility tests
  if: ${{ matrix.test-type == 'compatibility' }}
  run: pytest tests/compatibility
```

This pattern is useful when a particular combination needs additional behavior.

---

## `include` vs `exclude`

| Feature | `include` | `exclude` |
|---|---|---|
| Primary purpose | Add or modify matrix configuration | Remove combinations |
| Adds combinations | Yes | No |
| Adds metadata | Yes | No |
| Reduces matrix size | No | Yes |
| Useful for exceptions | Yes | Yes |
| Typical use | Experimental flags, regions, special configuration | Unsupported combinations |
| Main risk | Hidden configuration complexity | Excessive exclusion rules |

The two mechanisms solve opposite problems:

```text
include → Add or enrich
exclude → Remove
```

---

## Combining `include` and `exclude`

Both can be used in the same matrix.

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest]
    python: ["3.11", "3.12", "3.13"]

    exclude:
      - os: windows-latest
        python: "3.13"

    include:
      - os: ubuntu-latest
        python: "3.13"
        experimental: true
```

This represents:

```text
Ubuntu + Python 3.11
Ubuntu + Python 3.12
Ubuntu + Python 3.13 → experimental
Windows + Python 3.11
Windows + Python 3.12
Windows + Python 3.13 → excluded
```

This is a useful pattern when most combinations follow normal rules but a few require special handling.

---

## Matrix Include Semantics

`include` should not be treated simply as "append these rows."

GitHub Actions attempts to apply an `include` object to existing matrix combinations where its properties can be added without overwriting the original matrix values.

For example:

```yaml
strategy:
  matrix:
    fruit: [apple, pear]
    animal: [cat, dog]

    include:
      - color: green
```

The `color` property can be added to the generated combinations because it does not conflict with the existing matrix values.

Conceptually:

```text
apple + cat  + green
apple + dog  + green
pear  + cat  + green
pear  + dog  + green
```

A value that conflicts with an existing matrix value cannot simply overwrite that value for the generated combination. In such cases, the include object can become an additional combination rather than modifying the existing combinations.

This distinction is important when debugging unexpectedly large matrices.

---

## Prefer Explicit Configuration for Complex Matrices

When every combination has substantially different configuration, an enormous combination of `include` and `exclude` rules becomes difficult to reason about.

For example:

```yaml
strategy:
  matrix:
    include:
      - python: "3.11"
        os: ubuntu-latest
        database: postgres
        cache: true

      - python: "3.12"
        os: ubuntu-latest
        database: postgres
        cache: true

      - python: "3.13"
        os: ubuntu-latest
        database: postgres
        cache: false

      - python: "3.12"
        os: windows-latest
        database: mysql
        cache: true
```

This can be appropriate when the supported configuration set is intentionally sparse.

The trade-off is:

| Strategy | Advantage | Limitation |
|---|---|---|
| Cartesian matrix | Compact and easy to extend | May generate invalid combinations |
| Matrix + `exclude` | Efficient for a few exceptions | Can become exclusion-heavy |
| Matrix + `include` | Good for metadata and special cases | Semantics require careful review |
| Explicit `include` list | Precise control | More verbose and less scalable |

---

## Backend Testing Example

A realistic Python backend may support:

```text
Python:
3.11
3.12
3.13

Database:
PostgreSQL
MySQL

OS:
Ubuntu
Windows
```

A naive Cartesian matrix creates:

```text
3 × 2 × 2 = 12 jobs
```

Suppose:

- Windows is not used for database integration tests.
- Python 3.13 + MySQL is unsupported.
- Python 3.13 should be marked experimental.

The matrix can be modeled as:

```yaml
name: Backend CI

on:
  pull_request:

jobs:
  test:
    runs-on: ${{ matrix.os }}

    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
        database: [postgres, mysql]
        os: [ubuntu-latest, windows-latest]

        exclude:
          - os: windows-latest
            database: postgres

          - os: windows-latest
            database: mysql

          - python-version: "3.13"
            database: mysql

        include:
          - python-version: "3.13"
            database: postgres
            experimental: true

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest

      - name: Run experimental tests
        if: ${{ matrix.experimental == true }}
        run: pytest tests/experimental
```

In a real repository, database services and OS-specific setup would be added according to the supported test architecture.

The important design principle is that the matrix describes the supported test space rather than blindly testing every theoretical combination.

---

## `include` for Service Configuration

A matrix can also describe service-specific metadata.

For example:

```yaml
strategy:
  matrix:
    include:
      - database: postgres
        image: postgres:16
        service-port: 5432

      - database: mysql
        image: mysql:8.4
        service-port: 3306
```

The job can consume:

```yaml
${{ matrix.database }}
${{ matrix.image }}
${{ matrix.service-port }}
```

This can be useful when integration testing different database engines.

However, if the configuration becomes large, dynamically generated JSON or separate reusable workflows may be easier to maintain.

---

## Matrix Conditions

`include` metadata can drive conditions without creating separate jobs.

Example:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]

    include:
      - python-version: "3.13"
        experimental: true
```

Then:

```yaml
- name: Run stable test suite
  if: ${{ matrix.experimental != true }}
  run: pytest

- name: Run experimental test suite
  if: ${{ matrix.experimental == true }}
  run: pytest --run-experimental
```

This is preferable to duplicating the entire job when only a few steps differ.

---

## `include` and `continue-on-error`

Experimental combinations can be isolated from stable configurations.

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]

    include:
      - python-version: "3.13"
        experimental: true

continue-on-error: ${{ matrix.experimental == true }}
```

This means failures in the experimental configuration can be treated differently from failures in stable configurations.

Use this deliberately.

A production pipeline should not accidentally make a critical test non-blocking merely because it was added through `include`.

---

## `include` and `fail-fast`

`fail-fast` controls matrix cancellation behavior; it does not change how `include` or `exclude` construct the matrix.

For example:

```yaml
strategy:
  fail-fast: false

  matrix:
    python-version: ["3.11", "3.12", "3.13"]

    include:
      - python-version: "3.13"
        experimental: true
```

With:

```yaml
fail-fast: false
```

a failure in one matrix job does not cause the remaining matrix jobs to be automatically cancelled.

This is often appropriate for CI because complete matrix results provide better diagnostic information.

---

## `include` and `max-parallel`

`max-parallel` controls how many matrix jobs can execute simultaneously.

```yaml
strategy:
  max-parallel: 3

  matrix:
    python-version: ["3.11", "3.12", "3.13"]
    database: [postgres, mysql]
```

`include` and `exclude` determine the final matrix size; `max-parallel` controls execution concurrency.

These are different concerns:

```text
include/exclude
      │
      ▼
Final number of matrix combinations
      │
      ▼
max-parallel
      │
      ▼
Maximum concurrent executions
```

This distinction matters when matrix jobs consume expensive self-hosted runners or external database capacity.

---

## Matrix Size and Cost

Matrix expansion can multiply CI cost quickly.

For:

```text
4 Python versions
× 3 operating systems
× 3 databases
× 2 dependency modes
```

the theoretical matrix contains:

```text
4 × 3 × 3 × 2 = 72 jobs
```

Adding one more dimension:

```text
4 × 3 × 3 × 2 × 2 = 144 jobs
```

Before adding a dimension, evaluate:

- Execution time.
- Runner consumption.
- GitHub Actions minutes.
- External service usage.
- Database startup cost.
- Docker image pulls.
- Cache effectiveness.
- Diagnostic value.
- Actual support requirements.

A matrix should represent meaningful compatibility coverage, not every possible combination.

---

## Matrix Design for Python Backends

A common backend matrix is:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
```

When database compatibility also matters:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
    database: [postgres, mysql]
```

Then use `exclude` for unsupported combinations:

```yaml
exclude:
  - python-version: "3.13"
    database: mysql
```

Use `include` when one supported combination requires special behavior:

```yaml
include:
  - python-version: "3.13"
    database: postgres
    experimental: true
```

This produces a compact representation of the supported compatibility model.

---

## Matrix Design for Django

Django projects often need compatibility testing across:

- Python versions.
- Django versions.
- PostgreSQL versions.
- MySQL versions.

A matrix can quickly become expensive.

Instead of testing every possible combination:

```yaml
matrix:
  python: ["3.11", "3.12", "3.13"]
  django: ["5.2", "6.0"]
  database: [postgres, mysql]
```

consider defining the actual supported compatibility space.

For example:

```yaml
strategy:
  matrix:
    include:
      - python: "3.11"
        django: "5.2"
        database: postgres

      - python: "3.12"
        django: "5.2"
        database: postgres

      - python: "3.12"
        django: "6.0"
        database: postgres

      - python: "3.13"
        django: "6.0"
        database: postgres
        experimental: true
```

This is more verbose but can be substantially clearer when compatibility is intentionally selective.

---

## Matrix Design for FastAPI

FastAPI applications often have fewer framework compatibility dimensions, so a typical matrix may focus on Python and dependency/runtime compatibility:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]

    include:
      - python-version: "3.13"
        experimental: true
```

The pipeline can then run:

```text
Lint
  │
  ├── Python 3.11 tests
  ├── Python 3.12 tests
  └── Python 3.13 tests
          │
          ▼
       Build
```

The matrix should generally remain focused on compatibility dimensions that provide measurable value.

---

## Matrix + Database Services

When testing PostgreSQL or MySQL, each matrix job should have an isolated service environment.

A simplified PostgreSQL example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
        options: >-
          --health-cmd "pg_isready -U test_user -d test_db"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}

      - run: pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://test_user:postgres@localhost:5432/test_db
        run: pytest
```

Each matrix execution receives its own job environment and service container.

This prevents one matrix job from relying on another matrix job's database state.

---

## Matrix + `needs`

Matrix jobs can participate in dependency graphs.

For example:

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}
      - run: pytest

  build:
    needs: test
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - run: docker build -t backend:${{ github.sha }} .
```

The `build` job depends on the matrix job as a whole.

Conceptually:

```text
             ┌── Python 3.11 ──┐
             │                 │
Pull Request ├── Python 3.12 ──┼──► Build
             │                 │
             └── Python 3.13 ──┘
```

The build should not start until the required matrix executions have completed successfully.

---

## Matrix + Artifacts

A common pattern is to give each matrix job a unique artifact name:

```yaml
- name: Upload coverage
  uses: actions/upload-artifact@v4
  with:
    name: coverage-${{ matrix.python-version }}
    path: coverage.xml
```

Avoid using a fixed artifact name:

```yaml
name: coverage
```

when multiple matrix jobs produce separate outputs that must be retained.

Unique naming makes downstream aggregation and debugging easier.

---

## Matrix + Dynamic Configuration

Static `include` and `exclude` rules are appropriate when the compatibility model changes infrequently.

For more dynamic systems, generate a JSON matrix:

```yaml
jobs:
  generate-matrix:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.matrix.outputs.value }}

    steps:
      - name: Generate matrix
        id: matrix
        shell: bash
        run: |
          matrix='{"include":[{"python":"3.11","database":"postgres"},{"python":"3.12","database":"postgres"}]}'
          echo "value=$matrix" >> "$GITHUB_OUTPUT"

  test:
    needs: generate-matrix
    runs-on: ubuntu-latest

    strategy:
      matrix: ${{ fromJSON(needs.generate-matrix.outputs.matrix) }}

    steps:
      - run: |
          echo "Python: ${{ matrix.python }}"
          echo "Database: ${{ matrix.database }}"
```

For generated configurations, validate the source data carefully.

Do not allow arbitrary pull request content to determine privileged CI behavior without appropriate validation and security boundaries.

---

## Static vs Dynamic Matrix Configuration

| Approach | Best Use |
|---|---|
| Simple matrix | Stable Cartesian combinations |
| `exclude` | Small number of unsupported combinations |
| `include` | Special combinations or metadata |
| Explicit `include` list | Sparse compatibility matrix |
| Dynamic JSON matrix | Configuration generated from repository or external data |
| Reusable workflow | Standardized matrix execution across repositories |

A senior-level design should select the least complex mechanism that accurately models the supported configuration space.

---

## Security Considerations

Matrix values can influence:

- Shell commands.
- Docker tags.
- Artifact names.
- AWS deployment parameters.
- File paths.
- Environment selection.
- Dependency installation.
- Test infrastructure.

Do not assume that matrix values are automatically safe merely because they originate from workflow YAML.

For example, avoid constructing shell commands unnecessarily:

```yaml
run: ./deploy.sh ${{ matrix.environment }}
```

If the value can be influenced externally, validate it before using it in a shell command.

Prefer explicit mappings when privileged operations are involved.

For example:

```yaml
env:
  AWS_REGION: us-east-1
```

is easier to audit than dynamically constructing privileged deployment parameters from untrusted data.

---

## Matrix and Production Deployment

Matrix strategies are generally more appropriate for compatibility testing than for unrestricted production deployment.

A deployment matrix such as:

```yaml
matrix:
  environment:
    - staging
    - production
```

should not automatically imply that both environments deploy concurrently.

Production deployment normally requires:

- Environment protection.
- Required approvals.
- Deployment concurrency.
- Immutable artifacts.
- Explicit promotion.
- Health checks.
- Rollback procedures.

A safer architecture is:

```text
PR
 │
 ├── Matrix Tests
 │
 ▼
Build Immutable Artifact
 │
 ▼
Staging
 │
 ▼
Validation
 │
 ▼
Production Approval
 │
 ▼
Production
```

The matrix validates compatibility; environment controls govern deployment.

---

## Matrix and Immutable Artifacts

A common mistake is rebuilding an application separately for every matrix or environment.

A stronger CI/CD design is:

```text
Matrix Testing
      │
      ▼
Build Once
      │
      ▼
Immutable Artifact
      │
      ├──► Staging
      │
      └──► Production
```

For Docker:

```text
Source
  │
  ▼
Docker Build
  │
  ▼
Image tagged with commit SHA
  │
  ▼
Amazon ECR
  │
  ├──► Staging
  │
  └──► Production
```

The matrix should establish compatibility and confidence; the deployment pipeline should promote the validated artifact.

---

## Common Mistakes

### Creating an Oversized Cartesian Product

```yaml
matrix:
  python: ["3.10", "3.11", "3.12", "3.13"]
  os: [ubuntu-latest, windows-latest, macos-latest]
  database: [postgres, mysql, mariadb]
  mode: [unit, integration, e2e]
```

This can create dozens or hundreds of jobs.

**Why it happens:**

Every dimension multiplies the total number of executions.

**Avoid it by:**

- Testing only supported combinations.
- Using `exclude`.
- Using explicit `include` lists for sparse compatibility.
- Separating expensive E2E tests from broad compatibility tests.

---

### Using Too Many Exclusions

A matrix such as:

```yaml
matrix:
  os: [...]
  python: [...]
  database: [...]

exclude:
  - ...
  - ...
  - ...
  - ...
  - ...
  - ...
  - ...
```

may technically work but become difficult to reason about.

If most combinations are invalid, define the valid combinations explicitly with `include`.

---

### Using `include` Without Understanding Its Semantics

It is easy to assume:

```yaml
include:
  - python: "3.13"
```

always means "append exactly one row."

Depending on the matrix values, an `include` entry may instead be applied as additional metadata to existing combinations.

For complex matrices, verify the resulting combinations rather than relying on intuition.

---

### Making Experimental Tests Non-Blocking Accidentally

This is dangerous:

```yaml
continue-on-error: ${{ matrix.experimental == true }}
```

if `experimental` is missing or incorrectly assigned.

The result can be a pipeline that silently stops treating important tests as required.

Keep experimental behavior explicit and review it as part of CI governance.

---

### Repeating Job Definitions

If the only difference between two configurations is:

```text
Python 3.11
Python 3.12
```

do not create two nearly identical jobs.

Use a matrix.

Duplicated jobs increase maintenance cost and eventually drift apart.

---

### Using Matrix for Unrelated Workflows

Matrix is not a general replacement for workflow orchestration.

For example, these are usually separate lifecycle stages:

```text
test
security-scan
build
deploy
rollback
```

Do not force them into a single matrix simply because they are all CI/CD operations.

---

## Troubleshooting Matrix Problems

### Symptom: Expected Job Does Not Run

**Possible causes:**

- The combination was excluded.
- The combination was never generated.
- `include` did not create the expected combination.
- A job-level `if` condition evaluated to false.
- An upstream `needs` dependency failed.

**Isolation strategy:**

Inspect the workflow definition and enumerate the expected matrix combinations.

Check:

```yaml
strategy:
  matrix:
    ...
```

Then inspect:

```yaml
exclude:
  ...

include:
  ...
```

Also inspect job-level conditions.

---

### Symptom: Too Many Matrix Jobs

**Possible causes:**

- Unexpected Cartesian product.
- `include` created additional combinations.
- A new matrix dimension was added.
- An exclusion rule is missing.

**Isolation strategy:**

Calculate the theoretical Cartesian product:

```text
dimension A
× dimension B
× dimension C
```

Then account for exclusions and inclusions.

For example:

```text
3 Python versions
× 2 databases
× 2 operating systems
= 12 combinations
```

If the workflow produces more jobs than expected, inspect `include` semantics and additional combinations.

---

### Symptom: Matrix Job Uses Wrong Configuration

**Possible causes:**

- Incorrect `matrix` property.
- `include` metadata was applied differently than expected.
- A shell variable was confused with a GitHub expression.
- A hard-coded value overrides the matrix value.

Check:

```yaml
- name: Print matrix configuration
  run: |
    echo "Python: ${{ matrix.python-version }}"
    echo "Database: ${{ matrix.database }}"
    echo "OS: ${{ matrix.os }}"
```

For sensitive values, do not print the value merely for debugging.

---

### Symptom: One Matrix Failure Cancels Other Jobs

Check:

```yaml
strategy:
  fail-fast: false
```

If `fail-fast` is enabled, a matrix failure can cause in-progress or queued matrix jobs to be cancelled according to the strategy behavior.

Use `fail-fast: false` when complete compatibility results are more valuable than saving runner time.

---

### Symptom: Matrix CI Is Too Slow

Investigate:

- Matrix size.
- `max-parallel`.
- Runner availability.
- Dependency installation.
- Docker image pulls.
- Service startup time.
- Cache hit rate.
- Test suite duration.

The solution may be:

```yaml
strategy:
  max-parallel: 6
```

but increasing parallelism is only useful when runner and downstream infrastructure capacity can support it.

---

## Production Matrix Design Pattern

A mature backend CI pipeline can separate broad compatibility testing from expensive integration testing:

```text
                         Pull Request
                              │
                              ▼
                       Static Analysis
                              │
                              ▼
                     Matrix Unit Tests
                  ┌───────────┼───────────┐
                  │           │           │
              Python 3.11  Python 3.12  Python 3.13
                  │           │           │
                  └───────────┼───────────┘
                              │
                              ▼
                     Integration Tests
                              │
                    ┌─────────┴─────────┐
                    │                   │
               PostgreSQL             MySQL
                    │                   │
                    └─────────┬─────────┘
                              │
                              ▼
                         Security Scan
                              │
                              ▼
                           Build
                              │
                              ▼
                      Immutable Artifact
```

`include` and `exclude` should make the compatibility model explicit rather than allowing the matrix to become an uncontrolled combination generator.

---

## Matrix Architecture Considerations

Matrix design has implications beyond YAML.

### Reliability

More matrix jobs increase the number of independent failure points.

If:

```text
20 matrix jobs
```

run on every pull request, the workflow has more opportunities for:

- Runner failures.
- Dependency failures.
- External service failures.
- Network failures.
- Flaky tests.

Separate infrastructure failures from application failures before treating a matrix failure as a code regression.

### Scalability

Matrix parallelism scales CI throughput, but the bottleneck can move to:

- GitHub-hosted runner availability.
- Self-hosted runner capacity.
- Docker registries.
- PostgreSQL/MySQL startup.
- Package registries.
- AWS APIs.
- External test services.

Increasing matrix size without capacity planning can make CI slower rather than faster.

### Cost

Every additional matrix combination can consume:

- Runner minutes.
- Storage.
- Artifact retention.
- Cache storage.
- External service resources.

Matrix dimensions should therefore have a measurable testing purpose.

---

## Matrix with Reusable Workflows

Reusable workflows can centralize matrix execution patterns.

A repository-specific workflow can provide:

```yaml
jobs:
  ci:
    uses: organization/platform-workflows/.github/workflows/python-ci.yml@v1
    with:
      python-versions: '["3.11", "3.12", "3.13"]'
```

The reusable workflow can own the detailed matrix implementation.

This is useful for organizations with many Python services because:

```text
Repository A ─┐
Repository B ─┼──► Reusable CI Workflow ──► Matrix Tests
Repository C ─┘
```

The trade-off is that matrix behavior becomes part of the shared workflow contract and must therefore be versioned and changed carefully.

---

## Matrix Governance

For larger organizations, define clear ownership of:

- Supported Python versions.
- Supported operating systems.
- Supported databases.
- Experimental versions.
- Excluded combinations.
- Required test coverage.
- Matrix execution cost.
- Shared reusable workflows.

Avoid silently changing the supported matrix because doing so changes the CI contract for developers.

For reusable workflows, version changes explicitly:

```yaml
uses: organization/platform-workflows/.github/workflows/python-ci.yml@v1
```

rather than having every repository consume an uncontrolled moving reference.

---

## Senior-Level Design Guidelines

When designing a matrix, ask:

1. What compatibility dimension is being tested?
2. Which combinations are actually supported?
3. Which combinations are intentionally unsupported?
4. Can a Cartesian product represent the support model accurately?
5. Should `exclude` remove a few exceptional combinations?
6. Should `include` attach metadata or add special combinations?
7. Would an explicit `include` list be clearer?
8. How much runner capacity will the matrix consume?
9. Which tests belong in every combination?
10. Which tests should run only in selected combinations?
11. Does the matrix affect deployment behavior?
12. Are matrix values ever used in privileged operations?
13. Can failures be diagnosed independently?
14. Is the matrix maintainable as versions change?

The key engineering decision is not "How do I write `include`?"

It is:

> What is the smallest matrix that provides meaningful confidence in the supported production configuration space?

---

## Interview Traps

### "`include` Always Adds One New Matrix Job"

Not necessarily.

`include` can add properties to compatible existing combinations or introduce additional combinations depending on the values involved.

---

### "`exclude` Can Create New Combinations"

No.

`exclude` removes combinations from the generated matrix.

---

### "`include` and `exclude` Are Equivalent to `if`"

No.

They operate at matrix construction/configuration time, while `if` controls whether a job or step executes.

Use:

```yaml
exclude:
```

when the combination should not exist.

Use:

```yaml
if:
```

when the job exists but execution of a particular job or step depends on a condition.

---

### "A Larger Matrix Is Always Better"

No.

A larger matrix increases coverage but also increases:

- Cost.
- Runtime.
- Failure surface.
- Maintenance complexity.
- Infrastructure demand.

The matrix should reflect meaningful compatibility requirements.

---

### "Use `exclude` Until Every Invalid Combination Is Removed"

Not always.

If the valid configuration space is sparse, an explicit `include` list can be easier to understand and maintain.

---

### "Matrix Configuration Is Only a CI Concern"

Not entirely.

Matrix values can affect:

- Dependency versions.
- Database versions.
- Docker images.
- AWS deployment targets.
- Artifact names.
- Test infrastructure.

Therefore matrix design can have security, cost, reliability, and operational implications.

---

## Production Checklist

### Matrix Modeling

- [ ] Matrix dimensions represent meaningful compatibility requirements.
- [ ] Unsupported combinations are explicitly identified.
- [ ] `exclude` is used for a small number of exceptional combinations.
- [ ] `include` is used for metadata or intentional special combinations.
- [ ] Sparse matrices use explicit combinations where appropriate.
- [ ] Matrix size has been calculated before deployment.

### Testing

- [ ] Python compatibility is covered where required.
- [ ] Database compatibility is covered where required.
- [ ] Integration services are isolated per job.
- [ ] Test artifacts have unique names.
- [ ] Experimental combinations are explicitly identified.
- [ ] Experimental failures cannot silently weaken required checks.

### Performance and Cost

- [ ] Matrix parallelism is appropriate.
- [ ] `max-parallel` matches runner capacity.
- [ ] Dependency caching is configured where useful.
- [ ] Expensive E2E tests are not unnecessarily multiplied.
- [ ] External service capacity is considered.
- [ ] Matrix execution cost is monitored.

### Security

- [ ] Matrix values are not blindly inserted into privileged shell commands.
- [ ] Deployment environments are protected independently of matrix logic.
- [ ] AWS credentials are not stored as unnecessary long-lived secrets.
- [ ] OIDC is used for AWS authentication where applicable.
- [ ] Untrusted pull request data cannot control privileged matrix behavior.

### Maintainability

- [ ] Matrix rules are understandable to reviewers.
- [ ] Excessive `include`/`exclude` complexity is avoided.
- [ ] Shared matrix logic is centralized when appropriate.
- [ ] Reusable workflow versions are controlled.
- [ ] Supported compatibility combinations are documented.

## Key Takeaways

- `exclude` removes specific combinations from a generated Cartesian-product matrix, while `include` adds or enriches matrix configuration.
- Use `exclude` for a small number of unsupported combinations and prefer explicit `include` combinations when the valid configuration space is sparse.
- `include` is especially useful for attaching metadata such as `experimental`, database configuration, deployment targets, or test behavior to selected matrix combinations.
- Matrix size directly affects CI runtime, runner capacity, cost, and failure surface, so compatibility coverage should be designed deliberately rather than maximized blindly.
- Treat matrix configuration as part of the CI/CD architecture: secure its values, isolate test infrastructure, control concurrency, and keep production deployment promotion separate from compatibility testing.