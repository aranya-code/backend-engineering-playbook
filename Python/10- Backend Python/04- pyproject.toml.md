# 04- pyproject.toml

## Overview

`pyproject.toml` is the modern configuration file for Python projects. It provides a standardized place for project metadata, dependency declarations, build configuration, optional dependency groups, and configuration consumed by development tools.

For backend engineering, `pyproject.toml` is increasingly the central configuration boundary of a repository:

```text
                    pyproject.toml
                         │
        ┌────────────────┼─────────────────┐
        ↓                ↓                 ↓
 Project metadata   Dependencies       Build system
        │                │                 │
        ↓                ↓                 ↓
 Packaging          Resolver/lock       Build artifact
        │
        ├───────────────┬────────────────┐
        ↓               ↓                ↓
      Ruff            Mypy             Pytest
```

A well-designed `pyproject.toml` makes a project easier to:

- install;
- package;
- test;
- lint;
- type-check;
- build;
- publish;
- reproduce in CI/CD;
- deploy in Docker and Kubernetes.

It does **not** replace every other configuration mechanism. Runtime secrets, deployment configuration, infrastructure configuration, and application-specific environment variables should remain separate concerns.

---

## Why `pyproject.toml` Exists

Historically, Python projects used many separate configuration files:

```text
setup.py
setup.cfg
requirements.txt
tox.ini
.flake8
mypy.ini
pytest.ini
```

Modern Python tooling can consolidate much of this configuration into:

```text
pyproject.toml
```

This reduces configuration fragmentation and gives tools a common project configuration location.

However, `pyproject.toml` is not itself a dependency manager or lockfile.

A useful distinction is:

| Component | Responsibility |
|---|---|
| `pyproject.toml` | Project metadata and declared configuration |
| Lock file | Resolved dependency graph |
| Virtual environment | Installed isolated environment |
| Package manager | Resolves and installs dependencies |
| `Dockerfile` | Builds deployment image |
| Environment variables | Runtime configuration and secrets |

---

## TOML Fundamentals

`pyproject.toml` uses TOML syntax.

Example:

```toml
[project]
name = "order-service"
version = "1.0.0"

[tool.ruff]
line-length = 100
```

The structure consists of tables:

```toml
[project]
...

[tool.ruff]
...

[tool.pytest.ini_options]
...
```

Keys can contain strings, numbers, booleans, arrays, inline tables, and other TOML-supported values.

---

## Minimal Project Configuration

A minimal modern Python project can look like:

```toml
[project]
name = "order-service"
version = "0.1.0"
requires-python = ">=3.12,<3.14"
dependencies = [
    "fastapi>=0.115,<1",
]
```

The project metadata tells packaging tools what the project is and what Python/runtime dependencies it requires.

---

## `[build-system]`

The `[build-system]` table specifies the tools required to build the project.

Example:

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"
```

This is distinct from application dependencies.

```text
Build dependencies
    ↓
Build package
    ↓
Application artifact
    ↓
Runtime dependencies
```

A build backend determines how the source tree becomes a distributable artifact such as a wheel or source distribution.

---

## Build Isolation

Modern packaging tools generally build projects in an isolated environment containing the declared build requirements.

Conceptually:

```text
Source repository
      ↓
Read [build-system]
      ↓
Create isolated build environment
      ↓
Install build requirements
      ↓
Invoke build backend
      ↓
Wheel / sdist
```

This prevents the build from accidentally depending on packages installed globally on the developer's machine.

---

## Build Backend

Common build backends include:

- setuptools;
- Hatchling;
- PDM backend;
- Poetry's build backend;
- other standards-compatible backends.

The project should explicitly declare its build backend rather than relying on whatever happens to be installed locally.

---

## `[project]`

The `[project]` table contains standardized project metadata.

A production-oriented example:

```toml
[project]
name = "order-service"
version = "1.4.0"
description = "Backend service for order processing"
readme = "README.md"
requires-python = ">=3.12,<3.14"
license = { text = "MIT" }

authors = [
    { name = "Engineering Team" },
]

dependencies = [
    "fastapi>=0.115,<1",
    "pydantic>=2.10,<3",
    "sqlalchemy>=2.0,<3",
    "asyncpg>=0.30,<1",
]
```

The exact metadata required depends on whether the project is an application, library, or publishable package.

---

## Project Name

The `name` identifies the distribution package.

```toml
[project]
name = "order-service"
```

The distribution name and Python import package do not have to be identical.

For example:

```text
Distribution:
order-service

Import:
order_service
```

This distinction is important when diagnosing installation and packaging issues.

---

## Version

A project can define its version explicitly:

```toml
version = "1.4.0"
```

For applications, the version can represent the release version.

For libraries, it is part of the public package versioning contract.

Some projects derive the version dynamically from Git tags or another source. If doing so, make the source of truth obvious and ensure the build system produces deterministic versions.

---

## Python Version

Declare the supported Python range:

```toml
requires-python = ">=3.12,<3.14"
```

This communicates runtime compatibility to packaging tools.

It also prevents accidental installation into unsupported Python versions.

A production repository should align:

```text
pyproject.toml
    ↓
CI Python version
    ↓
Docker base image
    ↓
Production runtime
```

---

## Dependencies

Runtime dependencies are declared using:

```toml
dependencies = [
    "fastapi>=0.115,<1",
    "sqlalchemy>=2.0,<3",
]
```

These describe the packages required by the application.

Do not use `pyproject.toml` to store application secrets:

```toml
# Wrong
DATABASE_PASSWORD = "super-secret"
```

Secrets belong in environment variables or a dedicated secret-management system.

---

## Version Constraints

Dependencies can use version specifiers:

```toml
dependencies = [
    "httpx>=0.27,<1",
    "pydantic>=2.10,<3",
]
```

This communicates compatibility expectations.

A lock-aware dependency manager can resolve these constraints to exact versions.

```text
pyproject.toml
    ↓
Allowed versions
    ↓
Resolver
    ↓
Exact resolved versions
```

---

## Direct vs Transitive Dependencies

Only declare packages your project intentionally depends on as direct dependencies.

For example:

```toml
dependencies = [
    "fastapi",
]
```

FastAPI may itself depend on:

```text
starlette
anyio
```

Those are transitive dependencies.

Do not normally add transitive dependencies directly just because they happen to be installed.

If your application directly imports and relies on a package, however, that package should generally be declared as a direct dependency even if another dependency happens to install it.

---

## Optional Dependencies

Optional dependency sets can be defined with:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8,<9",
    "ruff>=0.12,<1",
    "mypy>=1.17,<2",
]

docs = [
    "mkdocs>=1.6,<2",
]
```

Install an optional extra with:

```bash
python -m pip install ".[dev]"
```

Extras are particularly useful when publishing reusable libraries.

---

## Development Dependencies

For applications, development-only dependencies should not be part of the runtime dependency set.

Typical examples:

```text
pytest
ruff
mypy
coverage
mkdocs
```

The exact mechanism for managing development groups depends on the chosen project-management tool.

Modern tools such as `uv`, Poetry, PDM, and Hatch can provide richer dependency-group workflows.

---

## Dependency Groups

Some tools support dependency groups directly.

For example, a tool-specific configuration may look like:

```toml
[dependency-groups]
dev = [
    "pytest>=8,<9",
    "ruff>=0.12,<1",
    "mypy>=1.17,<2",
]
```

This is distinct from standardized `[project.optional-dependencies]`.

Use optional dependencies when they are part of the package's published interface. Use dependency groups when the dependencies primarily support development or internal workflows and the selected tool supports them.

---

## Entry Points and CLI Applications

Python packaging can expose executable commands through entry points.

Example:

```toml
[project.scripts]
orders = "order_service.cli:main"
```

After installation:

```bash
orders
```

The command maps to:

```python
def main() -> None:
    ...
```

This is preferable to requiring developers to manipulate `PYTHONPATH` or execute files from arbitrary directories.

---

## Package Discovery

When using a build backend, the backend needs to know which Python packages belong in the distribution.

With setuptools, for example:

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

Combined with:

```text
src/
└── order_service/
    ├── __init__.py
    └── main.py
```

the build system can package the application correctly.

The exact configuration depends on the selected build backend.

---

## `src` Layout

A backend project commonly uses:

```text
order-service/
├── pyproject.toml
├── README.md
├── src/
│   └── order_service/
│       ├── __init__.py
│       ├── main.py
│       ├── api/
│       ├── application/
│       ├── domain/
│       └── infrastructure/
└── tests/
```

The `src` layout helps prevent accidentally importing the working tree instead of the installed package.

This is particularly valuable when testing packaging behavior.

---

## Example Production Configuration

A setuptools-based application can look like:

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "order-service"
version = "1.0.0"
description = "Backend service for order processing"
readme = "README.md"
requires-python = ">=3.12,<3.14"

dependencies = [
    "fastapi>=0.115,<1",
    "pydantic>=2.10,<3",
    "sqlalchemy>=2.0,<3",
    "asyncpg>=0.30,<1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8,<9",
    "pytest-asyncio>=0.24,<1",
    "ruff>=0.12,<1",
    "mypy>=1.17,<2",
]

[project.scripts]
orders = "order_service.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
```

The dependency manager can then generate or maintain its own lock information.

---

## Tool Configuration

`pyproject.toml` can host configuration for many development tools.

For example:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"

[tool.mypy]
python_version = "3.12"
strict = true
```

This creates a single project-level configuration surface.

Not every tool must be configured there. Use the tool's current supported configuration mechanism.

---

## Ruff Configuration

Ruff can provide linting and formatting from one tool.

Example:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",
    "F",
    "I",
    "UP",
    "B",
]

[tool.ruff.format]
quote-style = "double"
```

CI can then run:

```bash
ruff check .
ruff format --check .
```

Keeping these settings in the repository ensures developers and CI use the same policy.

---

## Pytest Configuration

Example:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
asyncio_mode = "auto"
```

This avoids requiring every developer to remember custom command-line arguments.

The configuration should reflect the project's actual test architecture.

---

## Mypy Configuration

Example:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
```

For larger repositories, configuration can become more explicit:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
exclude = [
    "^tests/",
]
```

Do not blindly enable strict settings without understanding the project's existing typing strategy. Tightening type checking incrementally can be more practical for mature codebases.

---

## Environment Configuration

Do not treat `pyproject.toml` as the runtime configuration store.

A backend application should separate:

```text
Build configuration
    ↓
pyproject.toml

Runtime configuration
    ↓
Environment variables / config service

Secrets
    ↓
AWS Secrets Manager / Kubernetes Secrets / secret manager
```

Example:

```bash
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
LOG_LEVEL=INFO
```

The application reads these at runtime.

---

## What Belongs in `pyproject.toml`

Good candidates include:

- project metadata;
- dependency declarations;
- Python compatibility;
- build configuration;
- package discovery;
- CLI entry points;
- optional dependency interfaces;
- development-tool configuration;
- test configuration;
- linting configuration;
- formatting configuration;
- type-checking configuration.

---

## What Does Not Belong in `pyproject.toml`

Avoid storing:

- passwords;
- API keys;
- production database credentials;
- environment-specific secrets;
- Kubernetes manifests;
- AWS credentials;
- mutable operational state;
- large generated artifacts.

For example:

```toml
# Do not do this
[tool.application]
database_password = "..."
aws_access_key = "..."
```

Configuration committed to Git should generally be safe for repository access according to the project's security model.

---

## `pyproject.toml` and Lock Files

The relationship is:

```text
pyproject.toml
    │
    │ declares compatible requirements
    ↓
Dependency resolver
    │
    ↓
Lock file
    │
    │ records resolved graph
    ↓
Environment / artifact
```

Examples of lock files include:

```text
uv.lock
poetry.lock
```

The exact file depends on the project's dependency-management tool.

Do not confuse:

```text
pyproject.toml
```

with:

```text
lockfile
```

The first expresses project configuration and requirements; the second records a particular resolved dependency graph.

---

## Reproducible Development

A developer should be able to clone the repository and create an environment deterministically.

Conceptually:

```bash
git clone <repository>
cd order-service

# Create/synchronize the environment using the project's chosen tool.
uv sync
```

The resulting environment should be derived from repository-controlled configuration rather than from packages previously installed on the machine.

---

## CI/CD Integration

CI should use the same dependency metadata and lock workflow as local development.

Example:

```mermaid
flowchart LR
    A[Git Commit] --> B[pyproject.toml]
    B --> C[Lock Information]
    C --> D[Clean CI Environment]
    D --> E[Install Dependencies]
    E --> F[Test]
    F --> G[Lint]
    G --> H[Type Check]
    H --> I[Build Artifact]
    I --> J[Deploy]
```

This reduces "works locally" failures caused by dependency differences.

---

## Docker Integration

A Docker build should derive its Python environment from project-controlled dependency configuration.

Example:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir .

CMD ["uvicorn", "order_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

For lock-aware dependency managers, use the corresponding deterministic installation command instead.

---

## Docker Build Caching

For larger applications, dependency metadata should be copied before frequently changing source code when the chosen build strategy allows it.

Conceptually:

```text
Copy dependency metadata
        ↓
Install dependencies
        ↓
Copy application source
        ↓
Build final image
```

This allows Docker to reuse dependency-related layers when only application source changes.

---

## Backend Architecture Relationship

`pyproject.toml` sits below the application architecture:

```text
                    pyproject.toml
                           │
             ┌─────────────┴─────────────┐
             ↓                           ↓
      External packages             Build tooling
             │
     ┌───────┼────────┐
     ↓       ↓        ↓
   FastAPI  SQLAlchemy Redis
     │       │        │
     └───────┼────────┘
             ↓
       Backend service
             ↓
 PostgreSQL / Kafka / AWS
```

It should define what the application needs without embedding application runtime behavior.

---

## Django Example

A Django application can declare its runtime dependencies:

```toml
[project]
name = "customer-platform"
version = "1.0.0"
requires-python = ">=3.12,<3.14"

dependencies = [
    "django>=5.2,<6",
    "psycopg[binary]>=3.2,<4",
    "redis>=6,<7",
]
```

Django-specific settings remain application configuration:

```text
src/customer_platform/settings/
```

rather than being placed into `pyproject.toml`.

---

## FastAPI Example

A FastAPI service might use:

```toml
[project]
name = "payment-service"
version = "1.0.0"
requires-python = ">=3.12,<3.14"

dependencies = [
    "fastapi>=0.115,<1",
    "uvicorn[standard]>=0.34,<1",
    "pydantic>=2.10,<3",
    "sqlalchemy>=2.0,<3",
    "asyncpg>=0.30,<1",
]
```

Application configuration such as database URLs, credentials, ports, and feature flags remains runtime configuration.

---

## Library vs Application

`pyproject.toml` should reflect whether the project is an application or a reusable library.

| Concern | Application | Library |
|---|---|---|
| Published to package index | Optional | Common |
| Strict runtime dependencies | Yes | Yes |
| Optional extras | Sometimes | Common |
| Public API stability | Internal | Critical |
| Versioning | Release/deployment oriented | Consumer-facing |
| Entry points | Sometimes | Sometimes |
| Lockfile | Useful | Often handled by consumers |

Libraries should generally avoid unnecessarily restrictive dependency requirements that make them difficult for consumers to integrate.

Applications have more freedom to control the complete dependency graph.

---

## Packaging and Distribution

Build an application/library package using a compatible build frontend:

```bash
python -m build
```

This can produce:

```text
dist/
├── order_service-1.0.0-py3-none-any.whl
└── order_service-1.0.0.tar.gz
```

The wheel is generally the preferred installation artifact when available.

The build backend specified in `[build-system]` determines how these artifacts are created.

---

## Editable Installs

During development, an editable installation can be useful:

```bash
python -m pip install -e .
```

The installed distribution points back to the working source tree, allowing source changes without rebuilding the package after every modification.

This is useful for:

- application development;
- library development;
- local CLI development.

Production deployments should generally install a built artifact rather than relying on editable installs.

---

## Build Dependencies vs Runtime Dependencies

These should not be confused.

```toml
[build-system]
requires = ["setuptools>=75"]
```

is about building the package.

```toml
[project]
dependencies = [
    "fastapi>=0.115,<1",
]
```

is about running the application.

Conceptually:

```text
Build environment
    └── build-system.requires

Runtime environment
    └── project.dependencies
```

---

## Performance Considerations

`pyproject.toml` itself has negligible runtime performance impact.

The dependency choices it defines can have significant effects.

More dependencies can mean:

- longer installation times;
- larger Docker images;
- slower CI;
- greater startup/import work;
- larger memory footprints;
- more security vulnerabilities.

For backend services, dependency selection should therefore consider runtime behavior, not only API convenience.

---

## Import-Time Performance

A package can perform substantial work during import.

For example:

```python
import large_framework
```

may load many modules before the application begins serving traffic.

In serverless or frequently restarted workloads, import time can affect startup latency.

Measure startup performance when it matters rather than assuming package count alone determines startup time.

---

## Dependency Weight

Consider:

```text
Small focused dependency
        vs
Large framework ecosystem
```

The larger dependency may provide significant productivity benefits but can increase:

- transitive dependencies;
- image size;
- startup work;
- vulnerability surface.

Do not optimize dependency count blindly. Optimize the complete operational trade-off.

---

## Security Considerations

`pyproject.toml` is part of the software supply chain.

Review:

- package names;
- package sources;
- version constraints;
- optional extras;
- build dependencies;
- package ownership;
- known vulnerabilities.

A malicious or compromised package can execute code during installation or runtime.

Use trusted package repositories and appropriate CI security controls.

---

## Private Dependencies

Organizations may depend on internal packages:

```toml
dependencies = [
    "company-auth>=4,<5",
]
```

The actual package source may be a private registry.

Production CI must have controlled access to that registry.

Do not place registry credentials directly in `pyproject.toml`.

Use CI secrets, credential providers, or the package manager's secure authentication mechanisms.

---

## Dependency Source Configuration

Package indexes and authentication configuration are often environment- or tool-specific.

Avoid committing credentials such as:

```text
https://username:password@example.com/simple
```

into repository configuration.

Instead use:

```text
CI secret
    ↓
package manager configuration
    ↓
private package index
```

This prevents credential leakage through Git history and build logs.

---

## Reproducible Builds

A strong build process should make the following inputs explicit:

```text
Source commit
+
Python version
+
pyproject.toml
+
lock information
+
build backend
+
package sources
```

Then:

```text
                    ┌───────────────┐
                    │ Git commit    │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Build config  │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Dependencies  │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Build artifact│
                    └───────┬───────┘
                            ↓
                  Docker / Kubernetes
```

Production should deploy the artifact generated by CI rather than resolving new dependencies during deployment.

---

## Monorepos

A monorepo may contain multiple Python services:

```text
services/
├── orders/
├── payments/
├── inventory/
└── notifications/
```

Each service can have its own:

```text
pyproject.toml
```

This allows services to evolve independently.

A shared root configuration can be useful for common tooling, but avoid creating unnecessary coupling between independently deployable services.

---

## Microservices

In a microservice architecture:

```text
orders       → pyproject.toml
payments     → pyproject.toml
inventory    → pyproject.toml
notifications → pyproject.toml
```

Each service should own its dependency graph.

Do not force every service to use identical versions merely for organizational convenience unless there is a concrete compatibility or security reason.

---

## Configuration Ownership

A useful separation is:

| Configuration | Location |
|---|---|
| Package metadata | `pyproject.toml` |
| Runtime dependencies | `pyproject.toml` |
| Build configuration | `pyproject.toml` |
| Tool configuration | `pyproject.toml` where supported |
| Resolved dependency versions | Lock file |
| Local environment | `.venv` |
| Runtime settings | Environment/config service |
| Secrets | Secret manager |
| Container build | `Dockerfile` |
| Kubernetes deployment | Kubernetes manifests/Helm/etc. |
| CI workflow | CI configuration |

This prevents `pyproject.toml` from becoming a generic dumping ground.

---

## Common Mistakes

### Treating `pyproject.toml` as a Lock File

It declares project requirements but does not necessarily represent the exact resolved dependency graph.

Use the dependency manager's lock mechanism when reproducibility requires exact resolution.

### Putting Secrets in the File

Repository configuration is not a secret-management system.

Use environment variables or dedicated secret stores.

### Declaring Every Transitive Dependency

This creates unnecessary direct coupling.

Declare packages your project intentionally depends on.

### Omitting `requires-python`

Without an explicit supported Python range, incompatible interpreters may be used.

### Mixing Tooling Without Ownership

Using Poetry to manage dependencies, `pip freeze` to generate requirements, and another tool to synchronize environments creates ambiguity.

Choose a clear workflow.

### Installing Development Dependencies in Production

This increases image size and attack surface.

Separate runtime and development dependencies.

### Treating Build Dependencies as Runtime Dependencies

`[build-system]` and `[project]` serve different purposes.

### Using Editable Installs in Production

Editable installs depend on the source tree and are intended primarily for development.

### Blindly Copying Configuration From Another Project

Tool configuration should reflect the current repository's Python version, architecture, package layout, and quality requirements.

---

## Production Best Practices

- Keep `pyproject.toml` under version control.
- Declare supported Python versions explicitly.
- Keep runtime dependencies separate from development tooling.
- Use compatible version constraints for direct dependencies.
- Use a lock/synchronization workflow for reproducible application environments.
- Keep secrets outside repository configuration.
- Configure development tools centrally where appropriate.
- Keep package discovery explicit and test packaging behavior.
- Build production artifacts in clean CI environments.
- Do not install latest dependencies during deployment.
- Keep production containers minimal.
- Review dependency upgrades as code changes.
- Remove dependencies that are no longer required.
- Document unusual build or dependency requirements.
- Keep each independently deployable service's dependency ownership clear.

---

## Recommended Backend Project

A production-oriented repository might look like:

```text
order-service/
├── pyproject.toml
├── uv.lock
├── README.md
├── Dockerfile
├── .dockerignore
├── .gitignore
├── src/
│   └── order_service/
│       ├── __init__.py
│       ├── main.py
│       ├── api/
│       ├── application/
│       ├── domain/
│       └── infrastructure/
├── tests/
│   ├── unit/
│   └── integration/
└── migrations/
```

The responsibilities remain separated:

```text
pyproject.toml
    → project/build/dependency/tool configuration

uv.lock
    → resolved dependency graph

src/
    → application code

tests/
    → verification

Dockerfile
    → deployment image

migrations/
    → database schema evolution
```

---

## Operational Decision Framework

When changing `pyproject.toml`, ask:

1. Is this a runtime dependency or development dependency?
2. Does the application directly depend on it?
3. What Python versions does it support?
4. What transitive dependencies does it introduce?
5. Does it contain native components?
6. Does it increase startup time or memory usage?
7. Does it introduce security risk?
8. How will CI resolve and install it?
9. How will production receive it?
10. Can the resulting environment be reproduced?

This turns dependency changes into deliberate engineering decisions rather than package-install commands.

---

## Interview Traps

### Is `pyproject.toml` a Dependency Manager?

No.

It is a standardized project configuration and metadata file. Dependency managers can use it as their project configuration source.

### Is `pyproject.toml` a Lock File?

No.

It generally declares requirements. A lock file records a resolved dependency graph.

### Does `pyproject.toml` Replace Virtual Environments?

No.

It defines project requirements and configuration. A virtual environment provides an isolated installation environment.

### Does `[build-system]` Define Application Dependencies?

No.

`[build-system]` defines build requirements and the build backend. Runtime dependencies belong under `[project].dependencies`.

### Should Secrets Be Stored in It?

No.

Use runtime configuration and secret-management systems.

### Should Every Installed Package Be Listed in `dependencies`?

No.

Direct dependencies should represent the packages the project intentionally depends on. Transitive dependencies are resolved through the dependency graph.

### Can One Repository Have Multiple `pyproject.toml` Files?

Yes.

This can be appropriate for monorepos or repositories containing multiple independently packaged Python projects.

---

## Key Takeaways

- **`pyproject.toml` is the central modern configuration surface for Python projects:** use it for project metadata, dependencies, build configuration, package discovery, and supported tool configuration.
- **Separate declarations from resolution:** `pyproject.toml` expresses intended requirements, while a lock/synchronization workflow provides reproducible resolved environments.
- **Keep configuration boundaries clear:** runtime settings and secrets belong outside `pyproject.toml`; build, dependency, packaging, and development-tool configuration can belong inside it.
- **Treat dependency changes as production changes:** evaluate compatibility, transitive dependencies, security, performance, build behavior, and deployment impact.
- **Align the entire build pipeline:** Python version, `pyproject.toml`, lock information, CI, Docker images, and production artifacts should form one reproducible dependency workflow.