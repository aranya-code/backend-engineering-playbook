# 14- Dependency Caching

## Overview

GitHub-hosted runners are provisioned as clean environments for workflow jobs. Without caching, every run may need to download the same Python, Node.js, or other package dependencies again, increasing network usage, workflow duration, and CI cost. Dependency caching stores reusable files between workflow runs so subsequent jobs can restore them instead of downloading everything from the package registry. :chatgpt-content-reference{index="0"}

Caching is an optimization, not a correctness mechanism. A workflow must remain fully functional when a cache is unavailable, stale, partially restored, or evicted.

For backend CI/CD pipelines, caching is particularly useful for:

- Python package downloads
- Node.js package downloads
- Java/Maven or Gradle dependencies
- Go modules
- Docker build layers
- Intermediate build outputs
- Tool-specific package-manager caches

A typical Python CI pipeline can therefore become:

```text
GitHub-hosted runner
        |
        v
Checkout repository
        |
        v
Restore dependency cache
        |
   +----+----+
   |         |
 Hit       Miss
   |         |
   |    Download packages
   |         |
   +----+----+
        |
        v
Install / reuse dependencies
        |
        v
Run tests
        |
        v
Save updated cache
```

The important engineering principle is:

> Cache expensive-to-recreate inputs, but never make correctness depend on the cache.

---

## Why Dependency Caching Matters

A GitHub-hosted runner does not preserve the installed dependency state of a previous workflow run. If a Python application has 100 packages, every fresh runner may need to download those packages again.

For example:

```text
Without cache:

Run 1 → Download dependencies → Install → Test
Run 2 → Download dependencies → Install → Test
Run 3 → Download dependencies → Install → Test
Run 4 → Download dependencies → Install → Test
```

With a correctly designed cache:

```text
Run 1 → Cache miss → Download → Install → Save cache
Run 2 → Cache hit  → Restore → Install → Test
Run 3 → Cache hit  → Restore → Install → Test
Run 4 → Cache hit  → Restore → Install → Test
```

The improvement depends on dependency size, network latency, package registry performance, runner type, and how often the workflow executes.

Caching is especially valuable for:

- large Python dependency graphs
- Node.js projects with large dependency trees
- monorepos with multiple services
- matrix workflows
- integration-test pipelines
- repositories with frequent pull requests
- Docker builds with expensive dependency installation

The existing CI/CD notes use the same basic pattern: cache pip's package cache using a key derived from the operating system and dependency file hash before installing the requirements. :chatgpt-content-reference{index="1"}

---

## Cache vs Artifact

Caching and artifacts both store files, but they solve different problems.

| Concern | Dependency Cache | Artifact |
|---|---|---|
| Primary purpose | Speed up future workflow runs | Preserve or transfer workflow outputs |
| Typical contents | Package-manager cache, build cache | Binaries, reports, logs, packages |
| Expected lifecycle | Reusable and disposable | Explicitly produced output |
| Can workflow depend on it? | No | Workflow may intentionally consume it |
| Typical example | `~/.cache/pip` | `coverage.xml` |
| Cross-job data transfer | Possible, but usually not the primary purpose | Primary use case |
| Missing data | Workflow should regenerate it | May represent a missing required output |
| Immutability | Cache entries are immutable | Artifact versions are separate objects |
| Production promotion | Usually inappropriate | Appropriate for build outputs |

GitHub explicitly recommends caches for reusable dependencies and intermediate outputs, while artifacts are intended for files produced by a workflow that need to be retained or passed between jobs. :chatgpt-content-reference{index="2"}

A useful rule is:

```text
Can I regenerate this cheaply and safely?
        |
       Yes
        |
        v
      Cache

Is this an output that must be preserved or promoted?
        |
       Yes
        |
        v
     Artifact
```

---

## How GitHub Actions Caching Works

The core caching mechanism is provided by `actions/cache`.

A cache operation has three important inputs:

```yaml
- uses: actions/cache@v6
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

The important concepts are:

- `path` — files or directories to store and restore.
- `key` — exact cache identity.
- `restore-keys` — fallback prefixes used when an exact key does not exist.
- `cache-hit` — output indicating whether the primary key matched exactly.

GitHub's current cache action supports separate restore/save operations as well as the combined cache action. Current `actions/cache@v6` uses the newer cache service and Node.js 24 runtime; self-hosted runners must satisfy the corresponding runner requirements. :chatgpt-content-reference{index="3"}

---

## Cache Lifecycle

A simplified lifecycle is:

```mermaid
flowchart TD
    A[Workflow starts] --> B[Evaluate cache key]
    B --> C{Exact cache exists?}

    C -->|Yes| D[Restore exact cache]
    C -->|No| E[Search prefix matches]

    E --> F{Fallback cache exists?}
    F -->|Yes| G[Restore partial cache]
    F -->|No| H[Start without cache]

    D --> I[Install or reuse dependencies]
    G --> I
    H --> I

    I --> J[Run workflow]
    J --> K{Job succeeds?}

    K -->|Yes| L[Save new cache if needed]
    K -->|No| M[Do not rely on cache update]

    L --> N[Future workflow run]
    M --> N
```

GitHub first searches for an exact key, then evaluates prefix matches and configured restore keys. If no exact cache is found, a fallback cache can be restored; after a successful run, a new cache can be created with the requested key. Existing cache contents cannot be modified in place. :chatgpt-content-reference{index="4"}

---

## Cache Keys

A cache key determines which cache entry should be restored.

A good key normally includes:

- operating system
- runtime version
- package manager
- dependency file hash
- application or service identifier when required

For example:

```yaml
key: ${{ runner.os }}-python-3.12-pip-${{ hashFiles('requirements.txt') }}
```

This produces a cache identity conceptually similar to:

```text
Linux
  +
Python 3.12
  +
pip
  +
requirements.txt hash
```

If `requirements.txt` changes, the hash changes and therefore the cache key changes.

### Why `hashFiles()` Matters

`hashFiles()` is particularly useful for dependency caches because the dependency definition becomes part of cache identity.

```yaml
key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

Conceptually:

```text
requirements.txt
       |
       v
   SHA-256 hash
       |
       v
Cache key
```

For example:

```text
requirements.txt
       ↓
d5ea0750...
       ↓
Linux-pip-d5ea0750...
```

This prevents a dependency change from silently reusing a cache associated with an older dependency definition. GitHub specifically documents `hashFiles()` as a mechanism for creating new caches when dependency files change. :chatgpt-content-reference{index="5"}

---

## Designing a Good Cache Key

A production cache key should distinguish environments where cached content may not be interchangeable.

A useful pattern is:

```text
<OS>-<runtime>-<package-manager>-<service>-<dependency-hash>
```

Example:

```yaml
key: ${{ runner.os }}-python-${{ matrix.python-version }}-pip-api-${{ hashFiles('api/requirements.txt') }}
```

This matters in a Python matrix:

```yaml
strategy:
  matrix:
    python-version:
      - "3.11"
      - "3.12"
      - "3.13"
```

The caches should not accidentally be treated as one universal dependency environment.

A more complete key might be:

```yaml
key: ${{ runner.os }}-python-${{ matrix.python-version }}-pip-${{ hashFiles('requirements.txt') }}
```

### Cache Key Components

| Component | Why it matters |
|---|---|
| `runner.os` | Separates OS-specific cache contents |
| Python version | Prevents incompatible runtime-specific data |
| Package manager | Separates pip/npm/etc. caches |
| Service name | Prevents unrelated services sharing a cache |
| Dependency hash | Invalidates cache when dependencies change |
| Architecture, when relevant | Prevents incompatible binaries from being reused |

---

## Restore Keys

`restore-keys` provide fallback matching when the primary key does not exist.

Example:

```yaml
- name: Restore pip cache
  uses: actions/cache@v6
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-python-${{ matrix.python-version }}-pip-${{ hashFiles('requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-python-${{ matrix.python-version }}-pip-
      ${{ runner.os }}-python-${{ matrix.python-version }}-
```

The lookup becomes conceptually:

```text
Exact:
Linux-python-3.12-pip-ABC123

Fallback:
Linux-python-3.12-pip-
        ↓
Linux-python-3.12-
```

Restore keys can improve reuse, but they must not cause incompatible dependencies to be treated as identical.

GitHub searches restore keys sequentially and can restore the most recently created matching cache for a prefix. :chatgpt-content-reference{index="6"}

---

## Exact Cache Hit vs Partial Restore

The distinction between a cache hit and a partial restore matters operationally.

```text
Exact key match
      |
      v
cache-hit = true
```

Whereas:

```text
Primary key missing
      |
      v
restore-key matched
      |
      v
cache-hit != true
```

The `cache-hit` output represents an exact match for the requested primary key. A fallback restoration does not represent an exact dependency state. :chatgpt-content-reference{index="7"}

For example:

```yaml
- name: Restore pip cache
  id: pip-cache
  uses: actions/cache@v6
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-python-${{ matrix.python-version }}-pip-${{ hashFiles('requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-python-${{ matrix.python-version }}-pip-

- name: Show cache status
  run: |
    echo "Exact cache hit: ${{ steps.pip-cache.outputs.cache-hit }}"
```

Do not interpret a restored fallback cache as proof that the dependency state is fully current.

---

## Python Dependency Caching

Python workflows commonly use pip.

The uploaded CI/CD example uses an explicit pip cache:

```yaml
- name: Cache pip dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-loan-${{ hashFiles('loan-service/requirements.txt') }}
```

followed by:

```yaml
- name: Install dependencies
  working-directory: loan-service
  run: |
    pip install -r requirements.txt
```

:chatgpt-content-reference{index="8"}

The modern preferred approach for straightforward Python projects is often to use `actions/setup-python`'s built-in dependency caching:

```yaml
name: Python CI

on:
  pull_request:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: requirements.txt

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

For standard package managers, GitHub documents the `setup-*` actions as the simpler mechanism for enabling dependency caching. `setup-python` supports pip, pipenv, and Poetry caching. :chatgpt-content-reference{index="9"}

### Multiple Requirement Files

For a repository such as:

```text
services/
    api/
        requirements.txt
    worker/
        requirements.txt
```

the cache dependency path may need to account for multiple dependency files:

```yaml
- name: Set up Python
  uses: actions/setup-python@v6
  with:
    python-version: "3.12"
    cache: pip
    cache-dependency-path: |
      services/api/requirements.txt
      services/worker/requirements.txt
```

For more complex monorepos, explicit `actions/cache` configuration may provide finer control.

---

## Poetry and Pipenv

Python projects using Poetry can also use `setup-python` caching.

Example:

```yaml
- name: Set up Python
  uses: actions/setup-python@v6
  with:
    python-version: "3.12"
    cache: poetry
    cache-dependency-path: poetry.lock

- name: Install dependencies
  run: poetry install --no-interaction
```

For Pipenv:

```yaml
- name: Set up Python
  uses: actions/setup-python@v6
  with:
    python-version: "3.12"
    cache: pipenv
    cache-dependency-path: Pipfile.lock

- name: Install dependencies
  run: pipenv install --deploy
```

The lockfile should participate in cache identity whenever it defines the actual dependency graph.

---

## Django CI Example

A Django project commonly needs:

- Python
- pip dependencies
- PostgreSQL
- Redis
- pytest or Django tests

Caching should reduce dependency-download overhead without hiding integration problems.

```yaml
name: Django CI

on:
  pull_request:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: app_test
          POSTGRES_USER: app
          POSTGRES_PASSWORD: app
        ports:
          - 5432:5432
        options: >-
          --health-cmd="pg_isready -U app -d app_test"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: requirements.txt

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r requirements.txt

      - name: Run migrations
        env:
          DATABASE_URL: postgresql://app:app@localhost:5432/app_test
          REDIS_URL: redis://localhost:6379/0
        run: python manage.py migrate --noinput

      - name: Run tests
        env:
          DATABASE_URL: postgresql://app:app@localhost:5432/app_test
          REDIS_URL: redis://localhost:6379/0
        run: pytest
```

The cache accelerates dependency retrieval, while PostgreSQL and Redis remain real integration dependencies.

This distinction is important:

```text
Dependency cache
    ↓
Performance optimization

PostgreSQL / Redis service
    ↓
Application correctness
```

---

## FastAPI CI Example

FastAPI projects follow the same pattern.

```yaml
name: FastAPI CI

on:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: requirements.txt

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r requirements.txt

      - name: Run tests
        run: pytest -q
```

The cache should accelerate package installation without changing the test environment's functional requirements.

---

## Node.js Dependency Caching

Node.js workflows can cache npm, Yarn, or pnpm package-manager data.

A modern approach is:

```yaml
- name: Set up Node.js
  uses: actions/setup-node@v6
  with:
    node-version: "22"
    cache: npm
    cache-dependency-path: package-lock.json

- name: Install dependencies
  run: npm ci
```

For npm:

```text
package-lock.json
        |
        v
     hash
        |
        v
Cache identity
```

Use `npm ci` in CI when a lockfile is committed because it installs the dependency graph described by the lockfile rather than modifying it during the build.

GitHub documents `setup-node` as supporting dependency caching for npm, Yarn, and pnpm. :chatgpt-content-reference{index="10"}

---

## Explicit Node Cache

For cases requiring custom cache behavior:

```yaml
- name: Cache npm
  id: npm-cache
  uses: actions/cache@v6
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-

- name: Install dependencies
  run: npm ci
```

Do not automatically cache `node_modules` merely because it appears faster.

Package-manager caches are generally safer because the package manager remains responsible for reconstructing the working dependency tree.

---

## Cache the Package Manager vs Installed Dependencies

There is an important distinction:

```text
Package-manager cache
    ↓
Downloaded packages / archives
    ↓
Package manager installs dependencies
```

versus:

```text
node_modules / virtual environment / site-packages
    ↓
Restore complete installed environment
```

Caching the package-manager cache is usually easier to reason about.

| Strategy | Advantages | Risks |
|---|---|---|
| Cache package-manager files | Safer, portable within expected environment | Installation still runs |
| Cache installed dependencies | Potentially faster | Runtime/version/platform sensitivity |
| Cache build output | Useful for expensive builds | Invalidation can be difficult |
| Cache everything | Maximum apparent reuse | High staleness and correctness risk |

The correct choice depends on the package manager and build system.

---

## Dependency Cache and Matrix Builds

Matrix testing can multiply dependency downloads.

Example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version:
          - "3.11"
          - "3.12"
          - "3.13"

    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
          cache-dependency-path: requirements.txt

      - name: Install dependencies
        run: python -m pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

The runtime version should participate in the cache identity when cached data can differ between Python versions.

Conceptually:

```text
              requirements.txt
                     |
          +----------+----------+
          |          |          |
       Python      Python      Python
        3.11        3.12        3.13
          |          |          |
       Cache A    Cache B    Cache C
```

Avoid creating a single cache shared blindly across incompatible runtime environments.

---

## Docker Build Cache

Docker caching is related to dependency caching but should be treated as a separate optimization layer.

For example:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

Docker can reuse the dependency-installation layer when `requirements.txt` has not changed.

The dependency flow becomes:

```text
Dockerfile
   |
   +--> requirements.txt unchanged
   |        |
   |        v
   |   Reuse dependency layer
   |
   +--> application source changed
            |
            v
       Rebuild later layers
```

For production Docker builds, BuildKit/Buildx caching can be used to persist reusable build layers in a registry or other supported cache backend.

A typical GitHub Actions build can use:

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v4

- name: Build image
  uses: docker/build-push-action@v7
  with:
    context: .
    push: false
    tags: backend-api:${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

Docker layer caching should not replace GitHub dependency caching blindly. They operate at different levels:

```text
GitHub dependency cache
        ↓
Package-manager downloads

Docker layer cache
        ↓
Docker build layers
```

---

## Cache Key Design for Docker

A Docker cache should reflect inputs that affect build layers.

A common architecture is:

```text
Dockerfile
requirements.txt
package-lock.json
source code
       |
       v
BuildKit
       |
       +--> reusable dependency layers
       |
       +--> application layers
       |
       v
Docker image
```

For a production image:

```text
Source
  ↓
Buildx
  ↓
Cached build layers
  ↓
Immutable image
  ↓
Container registry
```

The final image remains the deployable artifact. A Docker cache is only an optimization used while producing that artifact.

---

## Cache Security

Caches must be treated as potentially sensitive shared state.

Do not cache:

```text
.env
credentials
AWS credentials
private keys
tokens
service-account files
application secrets
database passwords
```

Bad example:

```yaml
- name: Cache application directory
  uses: actions/cache@v6
  with:
    path: .
    key: application-${{ github.sha }}
```

This can accidentally capture files that should never be persisted in a cache.

GitHub explicitly recommends not storing sensitive information such as credentials or access tokens in cache paths. Workflows that can read a cache receive its contents as-is. :chatgpt-content-reference{index="11"}

Prefer narrowly scoped paths:

```yaml
path: ~/.cache/pip
```

instead of:

```yaml
path: .
```

---

## Cache Poisoning

Cache poisoning is an important CI/CD supply-chain risk.

A simplified attack path is:

```text
Untrusted workflow
       |
       v
Writes malicious cache
       |
       v
Trusted workflow restores cache
       |
       v
Malicious content consumed
       |
       v
Potential code execution
```

A cache should therefore not be treated as a trusted artifact merely because GitHub stored it.

GitHub documents cache isolation and restrictions for low-trust workflows. Pull requests from forks may be able to restore caches while having restricted cache-write access. Explicitly granting write-capable cache access to untrusted workflows can reintroduce cache-poisoning risk. :chatgpt-content-reference{index="12"}

### Security Rules

- Never store secrets in caches.
- Keep cache paths narrowly scoped.
- Avoid caching generated credentials.
- Be careful with caches restored by untrusted pull requests.
- Do not execute arbitrary restored files without validation.
- Prefer package-manager caches over whole workspace caches.
- Treat restored cache contents as untrusted input.
- Use read-only cache access for low-trust workflows where appropriate.

---

## Pull Requests From Forks

Fork-based pull requests deserve additional attention.

A simplified model is:

```text
External contributor
        |
        v
Fork
        |
        v
Pull Request
        |
        v
Workflow
        |
        +--> Cache read
        |
        +--> Restricted cache write
```

The security boundary matters because a malicious contributor should not be able to populate a cache that a privileged production workflow later trusts.

GitHub applies restrictions to cache access for low-trust workflow triggers, and fork pull requests may restore caches from permitted scopes without being able to write new caches. :chatgpt-content-reference{index="13"}

Do not weaken those restrictions simply to improve cache performance.

---

## Cache Access Modes

Current GitHub Actions cache functionality supports explicit cache access modes.

| Mode | Restore | Save |
|---|---:|---:|
| `read` | Yes | No |
| `write` | Yes | Yes |
| `write-only` | No | Yes |
| `none` | No | No |

This is useful when designing workflows with different trust levels. :chatgpt-content-reference{index="14"}

For example, a security-sensitive workflow can intentionally use restore-only behavior where supported instead of allowing an untrusted workflow to populate shared caches.

---

## Cache Immutability

An existing cache cannot be modified in place.

If:

```text
Cache key:
Linux-pip-ABC
```

already exists, a workflow cannot simply replace its contents under that same cache identity.

Instead, a new dependency state should produce a new key:

```text
Linux-pip-ABC
        ↓
requirements changed
        ↓
Linux-pip-DEF
```

This property makes dependency-file hashing particularly important.

---

## Cache Retention and Eviction

Caches are disposable storage.

GitHub's current cache documentation states that a repository can have up to 10 GB of caches, with older caches evicted when the limit is reached; caches that have not been accessed recently are also subject to eviction. :chatgpt-content-reference{index="15"}

Therefore:

```text
Cache unavailable
      ↓
Workflow continues
      ↓
Dependencies regenerated
      ↓
New cache created
```

Do not design a deployment pipeline where:

```text
Cache unavailable
      ↓
Production deployment impossible
```

That would make an optimization a reliability dependency.

---

## Cache Hit and Miss Observability

A cache should be observable.

For explicit cache actions:

```yaml
- name: Restore cache
  id: cache
  uses: actions/cache@v6
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

- name: Report cache result
  run: |
    echo "Cache hit: ${{ steps.cache.outputs.cache-hit }}"
```

Useful operational metrics include:

- cache hit rate
- cache miss rate
- dependency installation duration
- total workflow duration
- cache restore duration
- cache upload duration
- cache storage consumption
- matrix-specific cache behavior

A high cache miss rate may indicate:

- unstable dependency files
- overly specific cache keys
- unnecessary runtime dimensions
- incorrect dependency paths
- frequent lockfile changes
- insufficient reuse across workflows

A cache hit is not automatically good if restoring it takes longer than downloading the dependencies.

---

## Performance Trade-Offs

Caching introduces its own cost.

The workflow may spend time:

```text
Download cache
      ↓
Decompress cache
      ↓
Extract files
```

instead of:

```text
Download packages
      ↓
Install packages
```

For small dependencies, caching may provide little benefit.

The right decision should be based on measurement:

```text
Without cache
    ↓
Dependency install = 45s

With cache
    ↓
Cache restore = 8s
Dependency install = 12s
Total = 20s
```

Caching is useful here.

But:

```text
Without cache
    ↓
Install = 8s

With cache
    ↓
Restore = 7s
Install = 4s
Total = 11s
```

The cache provides little or negative value.

---

## Monorepo Caching

Monorepos require careful cache boundaries.

Example:

```text
services/
├── users/
│   └── requirements.txt
├── payments/
│   └── requirements.txt
└── notifications/
    └── requirements.txt
```

Avoid:

```yaml
key: ${{ runner.os }}-python-${{ hashFiles('**/requirements.txt') }}
```

if every service should have independent cache behavior and one service changes frequently.

A service-specific key may be better:

```yaml
key: ${{ runner.os }}-users-pip-${{ hashFiles('services/users/requirements.txt') }}
```

This prevents unrelated dependency changes from invalidating caches for other services.

---

## Multi-Service CI Architecture

For a backend monorepo:

```mermaid
flowchart LR
    A[Repository] --> B[Users Service]
    A --> C[Payments Service]
    A --> D[Notification Service]

    B --> B1[Users Dependency Cache]
    C --> C1[Payments Dependency Cache]
    D --> D1[Notification Dependency Cache]

    B1 --> E[Users Tests]
    C1 --> F[Payments Tests]
    D1 --> G[Notification Tests]
```

This is often more efficient than maintaining one enormous shared cache.

The correct granularity depends on:

- dependency overlap
- repository size
- matrix size
- cache storage usage
- invalidation frequency
- build duration
- service ownership

---

## Caching in Reusable Workflows

Reusable CI workflows can centralize caching conventions.

Example:

```yaml
name: Reusable Python CI

on:
  workflow_call:
    inputs:
      python-version:
        required: true
        type: string
      dependency-file:
        required: true
        type: string

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: ${{ inputs.python-version }}
          cache: pip
          cache-dependency-path: ${{ inputs.dependency-file }}

      - name: Install dependencies
        run: python -m pip install -r "${{ inputs.dependency-file }}"

      - name: Run tests
        run: pytest
```

Repositories can then consume the same CI design:

```yaml
jobs:
  test:
    uses: company/platform-workflows/.github/workflows/python-ci.yml@v1
    with:
      python-version: "3.12"
      dependency-file: requirements.txt
```

Caching policy becomes part of the reusable workflow's engineering contract.

---

## Caching and Build Once, Promote Many

Dependency caches should never be confused with deployment artifacts.

A production pipeline should preferably follow:

```text
Source
  ↓
Test
  ↓
Build
  ↓
Immutable artifact
  ↓
Staging
  ↓
Approval
  ↓
Production
```

Not:

```text
Source
  ↓
Build for staging

Source
  ↓
Build again for production
```

The cache helps make the build faster:

```text
Dependency cache
       ↓
Faster build
       ↓
Immutable artifact
       ↓
Promote same artifact
```

The artifact remains the source of truth for deployment.

The existing AWS CI/CD notes similarly emphasize versioned images and promoting known build outputs rather than relying on mutable `latest` tags. :chatgpt-content-reference{index="16"}

---

## Caching and AWS Deployments

A GitHub Actions pipeline deploying to AWS may look like:

```text
Pull Request
     |
     v
Dependency Cache
     |
     v
Tests
     |
     v
Docker Build
     |
     v
Docker Build Cache
     |
     v
Container Image
     |
     v
Amazon ECR
     |
     v
Staging
     |
     v
Production
```

Caching should improve the speed of:

- dependency installation
- Docker builds
- test setup

It should not determine which image is deployed.

For example:

```text
Git SHA
  ↓
Docker image
  ↓
ECR
  ↓
ECS deployment
```

is a deployment identity.

The cache is not.

---

## Common Misconfiguration: Cache Key Does Not Include Dependencies

Bad:

```yaml
key: python-dependencies
```

This key never changes when:

```text
requirements.txt
```

changes.

A better design is:

```yaml
key: ${{ runner.os }}-python-${{ hashFiles('requirements.txt') }}
```

The dependency definition now participates in cache identity.

---

## Common Misconfiguration: Cache Key Is Too Specific

This is also problematic:

```yaml
key: ${{ runner.os }}-${{ github.sha }}-${{ hashFiles('requirements.txt') }}
```

If every commit generates a unique cache:

```text
Commit A → Cache A
Commit B → Cache B
Commit C → Cache C
Commit D → Cache D
```

the cache may have very poor reuse.

A commit SHA can be useful for artifact identity, but it is usually not necessary for dependency-cache identity.

Prefer:

```yaml
key: ${{ runner.os }}-python-${{ matrix.python-version }}-${{ hashFiles('requirements.txt') }}
```

---

## Common Misconfiguration: Caching Secrets

Bad:

```yaml
- uses: actions/cache@v6
  with:
    path: .
    key: full-workspace-${{ github.sha }}
```

If the workspace contains:

```text
.env
credentials.json
aws-config
private-key.pem
```

those files can become part of the cache.

Prefer explicit paths:

```yaml
path: ~/.cache/pip
```

---

## Common Misconfiguration: Treating Cache Hits as Correctness

Bad:

```yaml
if: steps.cache.outputs.cache-hit == 'true'
run: pytest
```

A cache hit only means that the requested cache key matched.

It does not prove:

- the dependency is secure
- the dependency is available
- the cache is logically correct
- the application is healthy
- the test environment is valid

Dependency installation and validation should still follow the project's package-management requirements.

---

## Common Misconfiguration: Caching the Entire Virtual Environment

Caching:

```text
.venv/
```

can sometimes provide speed improvements, but it increases sensitivity to:

- Python version
- OS
- architecture
- installed native libraries
- virtual-environment paths
- package metadata
- build tools

For most Python CI pipelines, caching pip's package-manager cache is easier to maintain.

Use installed-environment caching only when the performance benefit justifies the additional complexity and the cache key fully represents the environment.

---

## Troubleshooting Cache Misses

### Symptom

Every workflow run reports a cache miss.

### Possible Causes

- Dependency hash changes every run.
- Wrong dependency file path.
- Cache key includes unstable data.
- Different runtime versions generate different keys.
- Cache was evicted.
- Workflow is running under a different branch or cache scope.
- Cache path is incorrect.

### Isolation Strategy

Inspect:

```yaml
- name: Show dependency file
  run: |
    ls -la
    sha256sum requirements.txt
```

For an explicit cache:

```yaml
- name: Restore cache
  id: cache
  uses: actions/cache@v6
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

- name: Show cache status
  run: |
    echo "cache-hit=${{ steps.cache.outputs.cache-hit }}"
```

### Corrective Action

Verify:

```text
dependency path
      ↓
hashFiles()
      ↓
cache key
      ↓
cache path
```

---

## Troubleshooting: Cache Restores but Dependencies Still Download

### Symptom

The workflow reports a cache restoration but package installation still downloads packages.

### Possible Causes

- Only some package-manager files were cached.
- The cached directory is not the directory used by the package manager.
- The dependency set changed.
- A partial cache was restored.
- The package manager needs additional metadata.
- Native packages require platform-specific builds.

### Investigation

For pip:

```bash
python -m pip cache dir
python -m pip cache info
```

For npm:

```bash
npm config get cache
npm cache verify
```

The configured cache path should correspond to the path being cached.

---

## Troubleshooting: Incorrect Dependencies After a Change

### Symptom

The workflow uses old dependency data.

### Possible Causes

- Dependency file is not part of the key.
- Incorrect `hashFiles()` path.
- Restore key is too broad.
- Installed dependencies are being cached directly.
- Lockfile changes are not included.

### Corrective Action

Use the dependency definition or lockfile in the key:

```yaml
key: ${{ runner.os }}-python-${{ matrix.python-version }}-${{ hashFiles('**/poetry.lock') }}
```

For Node:

```yaml
key: ${{ runner.os }}-node-${{ hashFiles('package-lock.json') }}
```

For Python:

```yaml
key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

---

## Troubleshooting: Cache Works Locally but Not in Actions

Local and GitHub-hosted runner environments are different.

Possible differences include:

- OS
- CPU architecture
- Python version
- Node.js version
- package-manager version
- native libraries
- filesystem paths
- environment variables

A cache should therefore be designed around the actual GitHub Actions runner environment rather than local development assumptions.

---

## Troubleshooting Model

For production incidents, use:

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

For cache problems, collect:

- workflow run ID
- branch
- event type
- runner OS
- runtime version
- dependency file
- computed cache key
- cache-hit output
- restore duration
- dependency installation duration
- package-manager cache path

This turns a vague "cache is broken" report into an observable failure domain.

---

## Production Best Practices

### Keep Cache Scope Narrow

Cache exactly what needs to be reused.

Prefer:

```yaml
path: ~/.cache/pip
```

over:

```yaml
path: .
```

### Hash Dependency Definitions

Use:

```yaml
hashFiles('requirements.txt')
```

or the appropriate lockfile.

### Include Environment Dimensions

When necessary, include:

```text
OS
runtime version
architecture
package manager
service
```

### Keep Caches Disposable

The workflow must still work after:

```text
cache eviction
cache miss
cache corruption
cache unavailability
```

### Avoid Sensitive Data

Never use caches as secret storage.

### Measure the Benefit

Monitor:

```text
cache restore time
cache hit rate
dependency install time
total workflow duration
```

### Prefer Native Setup-Action Caching When Sufficient

For standard package managers, use:

```yaml
actions/setup-python
actions/setup-node
actions/setup-java
actions/setup-go
```

with their supported cache configuration where it satisfies the workflow's requirements. GitHub documents this approach as the minimal configuration for supported package managers. :chatgpt-content-reference{index="17"}

### Use Explicit `actions/cache` When You Need Control

Use the explicit cache action when you need:

- custom paths
- custom keys
- multiple dependency locations
- advanced restore behavior
- separate restore/save phases
- custom cache lifecycle control

---

## Cache Strategy Comparison

| Strategy | Use When | Main Benefit | Main Risk |
|---|---|---|---|
| `setup-python` cache | Standard Python project | Minimal configuration | Less customization |
| `setup-node` cache | Standard Node project | Simple package-manager caching | Less customization |
| `actions/cache` | Custom cache requirements | Full control | More configuration |
| Docker layer cache | Docker builds | Faster image builds | Layer invalidation complexity |
| Installed environment cache | Highly optimized CI | Potentially very fast | Environment incompatibility |
| Whole workspace cache | Rare specialized cases | Maximum reuse | Security and staleness risk |

---

## Cache and CI Reliability

A reliable pipeline should behave correctly under all of these conditions:

```text
Cache hit
Cache miss
Partial cache restore
Cache eviction
Cache unavailable
Dependency change
Runtime change
Runner change
```

A good architecture is therefore:

```mermaid
flowchart TD
    A[Workflow Start] --> B{Cache Available?}

    B -->|Yes| C[Restore Dependencies]
    B -->|No| D[Download Dependencies]

    C --> E[Install / Validate]
    D --> E

    E --> F[Run Tests]
    F --> G{Tests Pass?}

    G -->|Yes| H[Produce Artifact]
    G -->|No| I[Fail Workflow]

    H --> J[Deploy]
```

The cache affects performance, not correctness.

---

## Cache and High-Scale CI

Large organizations may run thousands of workflow jobs across:

- pull requests
- branches
- release builds
- scheduled tests
- matrix combinations
- multiple services

Poor cache design can increase storage and reduce reuse.

For example:

```text
Bad:
commit × branch × Python version × service
```

may create an excessive number of cache entries.

A more controlled strategy is:

```text
OS × runtime × service × dependency hash
```

where those dimensions actually affect the dependency environment.

The goal is not maximum cache count.

The goal is maximum useful reuse with safe invalidation.

---

## Cache and Cost Optimization

Caching can reduce:

- dependency network traffic
- workflow execution time
- runner utilization
- package registry requests

But caching itself consumes storage and transfer resources.

Monitor the trade-off:

```text
Cost without cache
    =
runner time
+
dependency download time

Cost with cache
    =
cache storage
+
cache transfer
+
cache restore time
+
runner time
```

Caching should therefore be evaluated using actual workflow metrics rather than assumed to be beneficial.

---

## Cache and Disaster Recovery

Caches should never be considered disaster-recovery data.

Do not store:

- production database backups
- deployment state
- critical binaries without another copy
- security credentials
- infrastructure state
- irreplaceable build outputs

Use appropriate systems for durable data:

```text
Build output
    → Artifact / Registry

Container image
    → ECR / Container Registry

Infrastructure state
    → Terraform backend

Production secret
    → AWS Secrets Manager / equivalent

Dependency cache
    → GitHub Actions cache
```

The cache is disposable by design.

---

## Dependency Caching in a Production Pipeline

A mature backend pipeline can combine several optimization layers:

```text
Pull Request
      |
      v
Checkout
      |
      v
Dependency Cache
      |
      +-------------------+
      |                   |
      v                   v
Unit Tests          Integration Tests
                          |
                  PostgreSQL + Redis
      |                   |
      +---------+---------+
                |
                v
         Security Scanning
                |
                v
          Docker Build
                |
                v
       Docker Layer Cache
                |
                v
          Docker Image
                |
                v
              ECR
                |
                v
            Staging
                |
                v
            Approval
                |
                v
          Production
```

The important distinction is:

```text
Dependency cache
    → speeds dependency preparation

Docker build cache
    → speeds image construction

Artifact / image
    → represents deployable output
```

These should not be conflated.

---

## Interview Traps

### Why is a cache not an artifact?

Because a cache is intended to accelerate regeneration of reusable data, while an artifact represents a workflow output that may need to be retained, inspected, or passed to another job.

### Why should a dependency file be part of the cache key?

Because dependency changes must invalidate the previous dependency state.

### Why include Python version in a cache key?

Because cached dependency data can depend on the runtime version and native package environment.

### What happens when there is no cache?

The workflow should regenerate the dependencies normally.

### Should secrets be cached?

No. Cache contents should be treated as accessible to workflows that can restore them.

### Why can `restore-keys` be dangerous?

A broad restore key may restore an older or less-specific cache. The dependency installation process must still reconcile the environment correctly.

### Should you cache `node_modules`?

Not automatically. Package-manager caches are generally easier to maintain and allow the package manager to reconstruct the installed environment.

### Is a cache hit proof that dependencies are valid?

No. It only indicates that the cache key matched the requested cache identity.

### Can a cache replace Docker image promotion?

No. The cache accelerates image construction. The immutable image should be promoted between environments.

### Can a cache be used for disaster recovery?

No. Caches are disposable and subject to eviction.

---

## Production Checklist

### Cache Design

- [ ] Cache only reusable data.
- [ ] Keep cache paths narrowly scoped.
- [ ] Include dependency files or lockfiles in cache identity.
- [ ] Include runtime and OS dimensions when necessary.
- [ ] Avoid unstable values in cache keys.
- [ ] Avoid unnecessarily broad restore keys.

### Python

- [ ] Use `setup-python` caching for standard projects.
- [ ] Specify `cache-dependency-path` for non-standard dependency locations.
- [ ] Use explicit `actions/cache` when custom control is required.
- [ ] Include Python version in explicit cache keys when appropriate.

### Node.js

- [ ] Use `setup-node` caching where appropriate.
- [ ] Cache npm/Yarn/pnpm package-manager data.
- [ ] Use lockfiles for cache invalidation.
- [ ] Prefer deterministic installation such as `npm ci` in CI.

### Docker

- [ ] Separate dependency caching from Docker layer caching.
- [ ] Use Buildx/BuildKit for advanced Docker caching.
- [ ] Do not treat build cache as the deployable artifact.
- [ ] Promote immutable images rather than rebuilding per environment.

### Security

- [ ] Never cache secrets.
- [ ] Never cache credentials.
- [ ] Treat restored cache contents as untrusted.
- [ ] Consider fork and pull-request cache boundaries.
- [ ] Avoid granting unnecessary cache-write access.
- [ ] Keep low-trust workflows isolated from trusted cache state.

### Reliability

- [ ] Workflow succeeds without a cache.
- [ ] Cache misses do not break deployments.
- [ ] Dependency changes invalidate stale caches.
- [ ] Cache performance is measured.
- [ ] Cache storage is monitored.
- [ ] Cache is never treated as durable production state.

## Key Takeaways

- Dependency caching is a performance optimization that reduces repeated package downloads; workflow correctness must never depend on a cache being present.
- Design cache keys around the actual dependency environment, especially OS, runtime version, service boundaries, and dependency or lockfile hashes.
- Prefer `setup-python`, `setup-node`, and other setup actions' native caching for standard package-manager workflows; use `actions/cache` when finer control is required. :chatgpt-content-reference{index="18"}
- Treat caches as untrusted, disposable state: never store secrets, and apply particular caution to fork-based pull requests and cache-poisoning risks. :chatgpt-content-reference{index="19"}
- Keep dependency caches, Docker build caches, and deployable artifacts separate: caches accelerate builds, while immutable artifacts and container images provide the inputs for reliable promotion and rollback.