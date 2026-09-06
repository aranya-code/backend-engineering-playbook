# 07- Configuration Management

## Overview

Configuration management is the disciplined process of defining, validating, distributing, changing, and operating the configuration required by a backend system.

It is broader than simply reading environment variables.

A production configuration system answers:

- What configuration does the application require?
- Where does each value come from?
- Which values are secrets?
- What are the valid types and ranges?
- What is the precedence when multiple sources exist?
- When is configuration loaded?
- Can configuration change while the process is running?
- How are configuration changes deployed and rolled back?
- How are configuration errors observed?
- How does configuration behave across multiple replicas?

A useful architecture is:

```text
Configuration Sources
    ├── defaults
    ├── environment variables
    ├── configuration files
    ├── Kubernetes ConfigMaps
    ├── Kubernetes Secrets
    └── AWS configuration / secret services
             │
             ↓
       Configuration Loader
             │
             ↓
       Parse + Validate
             │
             ↓
       Typed Settings
             │
             ↓
      Application Components
```

The objective is to create a **predictable configuration boundary** between the deployment environment and application code.

---

## Configuration Management vs Environment Configuration

Environment configuration focuses primarily on obtaining environment-specific values.

Configuration management includes the larger lifecycle:

```text
Define
  ↓
Load
  ↓
Parse
  ↓
Validate
  ↓
Distribute
  ↓
Observe
  ↓
Change
  ↓
Roll out
  ↓
Rollback
```

The distinction matters because a production system needs more than:

```python
os.getenv("DATABASE_URL")
```

It needs controlled behavior around that value.

---

## Configuration Categories

A backend application typically has several configuration categories.

| Category | Examples | Typical source |
|---|---|---|
| Application | service name, environment | Environment/config file |
| Infrastructure | database host, Redis endpoint | Platform configuration |
| Performance | pool sizes, timeouts | Environment/config management |
| Security | TLS settings, allowed origins | Secure configuration |
| Secrets | passwords, API keys | Secret manager |
| Feature flags | feature enablement | Environment/flag service |
| Observability | log level, metrics settings | Environment/configuration |
| Deployment | replica count, resources | Kubernetes/IaC |
| Build | package versions, tooling | `pyproject.toml` |

The configuration boundary should reflect these different responsibilities.

---

## Configuration Sources

Common sources include:

```text
Static defaults
      ↓
Configuration files
      ↓
Environment variables
      ↓
Kubernetes ConfigMap
      ↓
Kubernetes Secret
      ↓
AWS Secrets Manager / Parameter Store
      ↓
Dynamic configuration service
```

Not every application needs every source.

A small service might need only:

```text
defaults + environment variables
```

A larger platform may require:

```text
defaults
+
environment configuration
+
secret management
+
feature flags
```

Avoid introducing a remote configuration service without a concrete operational requirement.

---

## Configuration Precedence

If multiple sources exist, precedence must be explicit.

For example:

```text
Built-in defaults
        ↓
Configuration file
        ↓
Environment variables
        ↓
Secret manager
        ↓
Explicit runtime overrides
```

The exact order depends on the application architecture.

What matters is that engineers can predict which value wins.

Ambiguous precedence causes difficult production bugs such as:

```text
Developer expects:
DATABASE_POOL_SIZE=20

Application actually uses:
configuration file → 10
```

---

## Configuration Schema

A configuration schema defines:

- required values;
- optional values;
- types;
- defaults;
- allowed values;
- ranges;
- relationships between settings.

Example:

```python
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: Literal["development", "staging", "production"]
    log_level: str = "INFO"

    database_url: str
    database_pool_size: int = 10

    redis_url: str
    request_timeout_seconds: float = 5.0

    model_config = SettingsConfigDict(
        env_prefix="APP_",
    )
```

The configuration schema becomes an explicit contract between deployment infrastructure and application code.

---

## Why Typed Configuration Matters

Environment variables are strings:

```text
APP_DATABASE_POOL_SIZE=20
APP_DEBUG=false
```

The application should not have to manually parse these values everywhere.

A typed configuration layer converts them into:

```python
settings.database_pool_size  # int
settings.request_timeout_seconds  # float
```

This provides:

- type safety;
- centralized validation;
- predictable defaults;
- better IDE support;
- easier testing;
- clearer configuration contracts.

---

## Configuration Validation

Validation should occur before the application serves traffic.

Examples of validation rules:

```text
DATABASE_POOL_SIZE > 0
REQUEST_TIMEOUT > 0
ENVIRONMENT ∈ {development, staging, production}
PORT ∈ valid range
DATABASE_URL is valid
```

For example:

```python
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_pool_size: int = Field(default=10, gt=0)
    request_timeout_seconds: float = Field(default=5.0, gt=0)
```

Invalid configuration should produce a startup error rather than a partially functional service.

---

## Fail-Fast Configuration

Prefer:

```text
Container starts
    ↓
Configuration validation
    ↓
Invalid configuration
    ↓
Process exits
```

over:

```text
Container starts
    ↓
Application appears healthy
    ↓
First request
    ↓
Configuration error
    ↓
500 response
```

Fail-fast behavior makes deployment failures easier to detect and prevents invalid instances from receiving production traffic.

---

## Configuration Lifecycle

A typical backend process follows:

```mermaid
sequenceDiagram
    participant K as Kubernetes
    participant A as Application
    participant C as Config
    participant S as Secret Store
    participant DB as PostgreSQL

    K->>A: Start container
    A->>C: Load configuration
    C->>S: Retrieve required secrets
    S-->>C: Secret values
    C->>C: Parse and validate
    C-->>A: Typed settings
    A->>DB: Initialize database resources
    DB-->>A: Ready
    A-->>K: Readiness = Ready
```

Configuration should be validated before the application declares itself ready.

---

## Static vs Dynamic Configuration

Configuration can be classified by whether it changes during process lifetime.

### Static Configuration

Loaded at startup:

```text
DATABASE_URL
DATABASE_POOL_SIZE
REDIS_URL
LOG_LEVEL
```

Changing it usually requires a restart or redeployment.

### Dynamic Configuration

Can change while the application is running:

```text
Feature flags
Rate limits
Experiment configuration
Traffic controls
```

Dynamic configuration requires additional semantics around:

- consistency;
- caching;
- refresh;
- failure;
- rollback;
- concurrency.

Do not make configuration dynamic simply because it is technically possible.

---

## Startup Configuration

Static configuration is commonly loaded once:

```python
settings = Settings()
```

Then components receive the validated configuration.

```python
database = Database(
    url=settings.database_url,
    pool_size=settings.database_pool_size,
)
```

This makes configuration behavior deterministic during the process lifetime.

---

## Configuration Injection

Prefer explicit dependency injection over direct environment access.

Instead of:

```python
class PaymentClient:
    def charge(self, amount: int) -> None:
        api_url = os.getenv("PAYMENT_API_URL")
        ...
```

prefer:

```python
class PaymentClient:
    def __init__(self, api_url: str, timeout: float) -> None:
        self.api_url = api_url
        self.timeout = timeout
```

Composition code supplies:

```python
payment_client = PaymentClient(
    api_url=settings.payment_api_url,
    timeout=settings.payment_timeout_seconds,
)
```

This improves:

- testability;
- modularity;
- dependency visibility;
- configuration isolation.

---

## Configuration Boundaries

A strong architecture has a narrow configuration boundary:

```text
Environment / platform
        ↓
Configuration loader
        ↓
Validated Settings
        ↓
Application composition root
        ↓
Domain / services / infrastructure
```

Domain code should generally not know whether a value came from:

```text
environment variable
AWS Secrets Manager
Kubernetes Secret
test fixture
```

It should receive the value it needs through an explicit interface.

---

## Configuration and Dependency Injection

Configuration often participates in dependency injection.

Example:

```python
class OrderRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
```

The composition layer controls construction:

```python
repository = OrderRepository(settings.database_url)
```

This keeps configuration concerns out of business logic.

---

## Configuration Scope

Avoid creating one enormous settings object containing every setting used by every application component.

Instead, consider logical grouping:

```python
class DatabaseSettings:
    ...


class RedisSettings:
    ...


class KafkaSettings:
    ...


class Settings:
    database: DatabaseSettings
    redis: RedisSettings
    kafka: KafkaSettings
```

The exact design should match application complexity.

For a small service, a single settings model may be clearer.

---

## Configuration Ownership

Every important configuration value should have an owner.

For example:

| Configuration | Owner |
|---|---|
| Database URL | Platform/application |
| Database pool size | Backend/platform |
| Kafka topic | Event platform/application |
| API key | Security/application |
| Log level | Operations |
| Feature flag | Product/application |
| Kubernetes replica count | Platform/deployment |

Ownership prevents configuration from becoming an unmanaged collection of arbitrary environment variables.

---

## Configuration Naming

Use explicit names:

```text
APP_DATABASE_POOL_SIZE
APP_REQUEST_TIMEOUT_SECONDS
APP_REDIS_MAX_CONNECTIONS
APP_KAFKA_CONSUMER_GROUP
```

Avoid ambiguous names:

```text
APP_TIMEOUT=10
APP_LIMIT=20
APP_HOST=...
```

Explicit names reduce operational mistakes.

Units should be part of names where ambiguity is possible:

```text
APP_TIMEOUT_SECONDS
APP_MAX_PAYLOAD_BYTES
APP_RETRY_DELAY_MS
```

---

## Configuration Namespacing

Use application-specific prefixes:

```text
APP_
ORDER_SERVICE_
PAYMENT_SERVICE_
```

For example:

```text
ORDER_SERVICE_DATABASE_URL
ORDER_SERVICE_REDIS_URL
ORDER_SERVICE_LOG_LEVEL
```

This is particularly useful when multiple services or tools share the same environment.

---

## Defaults

Defaults should be safe and intentional.

Good:

```python
log_level: str = "INFO"
request_timeout_seconds: float = 5.0
database_pool_size: int = 10
```

Avoid dangerous security defaults:

```python
jwt_secret: str = "development-secret"
database_password: str = ""
```

Critical production configuration should normally be required explicitly.

---

## Environment-Specific Configuration

Prefer configuration values over environment-specific code branches.

Avoid:

```python
if settings.environment == "production":
    timeout = 30
else:
    timeout = 5
```

Prefer:

```python
timeout = settings.request_timeout_seconds
```

Then configure:

```text
Development → 5
Staging     → 10
Production  → 30
```

This keeps deployment policy outside application logic.

---

## Configuration Files

Configuration files can be useful for stable, non-secret defaults.

For example:

```yaml
http:
  timeout_seconds: 5

logging:
  level: INFO
```

However, configuration files introduce questions around:

- precedence;
- environment-specific overrides;
- packaging;
- secret exposure;
- deployment synchronization.

Use them when they provide clear value rather than introducing files solely because the format is familiar.

---

## `.env` Files

`.env` files are useful for local development:

```dotenv
APP_ENVIRONMENT=development
APP_LOG_LEVEL=DEBUG
APP_DATABASE_URL=postgresql://localhost/orders
APP_REDIS_URL=redis://localhost:6379/0
```

They provide convenient local configuration without modifying source code.

They should not automatically be treated as production configuration infrastructure.

---

## `.env.example`

Commit a safe template:

```dotenv
APP_ENVIRONMENT=development
APP_LOG_LEVEL=INFO
APP_DATABASE_URL=
APP_REDIS_URL=
APP_PAYMENT_API_URL=
APP_PAYMENT_API_KEY=
```

This documents required configuration while leaving sensitive values empty.

---

## Secrets Management

Secrets require a stronger lifecycle:

```text
Create
  ↓
Store securely
  ↓
Authorize access
  ↓
Inject / retrieve
  ↓
Use
  ↓
Rotate
  ↓
Revoke
```

Examples include:

- PostgreSQL credentials;
- Redis credentials;
- API keys;
- JWT signing keys;
- encryption keys;
- OAuth client secrets.

Never place these directly into source code.

---

## Kubernetes Configuration

Kubernetes commonly separates:

```text
ConfigMap → non-sensitive configuration
Secret    → sensitive configuration
```

Example:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: order-service-config
data:
  APP_ENVIRONMENT: "production"
  APP_LOG_LEVEL: "INFO"
  APP_REQUEST_TIMEOUT_SECONDS: "5"
```

A Secret can provide sensitive values.

```text
Kubernetes
    ├── ConfigMap
    └── Secret
           ↓
          Pod
           ↓
     Python process
```

Kubernetes Secret security still depends on cluster configuration, RBAC, encryption, and operational controls.

---

## AWS Configuration

AWS applications can use services such as:

```text
AWS Systems Manager Parameter Store
AWS Secrets Manager
```

A common separation is:

```text
Parameter Store
    → operational parameters

Secrets Manager
    → sensitive secrets
```

The application can retrieve secrets using its workload identity rather than storing long-lived AWS credentials in the application.

---

## Workload Identity

Prefer platform-native identities where possible.

Conceptually:

```text
EKS / ECS workload
       ↓
IAM identity
       ↓
AWS Secrets Manager
```

instead of:

```text
Application
       ↓
hard-coded AWS access key
       ↓
AWS Secrets Manager
```

Workload identity reduces credential-management burden and limits the impact of credential leakage.

---

## Secret Rotation

Secret rotation changes credentials without changing application code.

For example:

```text
Old DB credential
      ↓
Rotation
      ↓
New DB credential
      ↓
Application refresh/restart
      ↓
Old credential revoked
```

If configuration is loaded only at startup, a rolling restart may be the simplest and safest refresh strategy.

Live secret refresh requires explicit implementation and testing.

---

## Configuration and Rolling Deployments

Configuration changes must remain compatible with rolling deployments.

Suppose:

```text
Version A → OLD_API_URL
Version B → NEW_API_URL
```

During deployment, both versions may run simultaneously.

A safe migration may be:

```text
Deploy configuration supporting both
        ↓
Deploy Version B
        ↓
Shift traffic
        ↓
Remove Version A
        ↓
Remove obsolete configuration
```

Avoid configuration changes that make old and new replicas incompatible during rollout.

---

## Configuration Versioning

Configuration should evolve alongside application contracts.

For breaking changes:

```text
Old application
      +
Old configuration
```

must remain valid until the old application is removed.

Treat configuration changes with the same discipline as API or database schema changes.

---

## Configuration and Database Capacity

Database configuration directly affects infrastructure capacity.

For example:

```text
8 Kubernetes pods
×
4 worker processes
×
10 database connections
=
320 possible connections
```

A pool size that looks reasonable for one process can overwhelm PostgreSQL at deployment scale.

Configuration review should therefore consider:

```text
replicas
×
workers
×
connections per worker
```

---

## Configuration and Redis Capacity

The same reasoning applies to Redis:

```text
replicas
×
workers
×
Redis connections
```

For example:

```text
10 pods
×
4 workers
×
20 connections
=
800 possible connections
```

Connection-pool configuration must be evaluated against Redis capacity and actual concurrency.

---

## Configuration and Kafka

Kafka configuration can affect correctness as well as performance.

Important values include:

```text
KAFKA_BOOTSTRAP_SERVERS
KAFKA_TOPIC
KAFKA_CONSUMER_GROUP
KAFKA_SECURITY_PROTOCOL
```

An incorrect consumer group can cause messages to be processed differently than expected.

An incorrect topic or cluster can result in data being read from or written to the wrong system.

Validate these values during worker startup.

---

## Configuration and HTTP Clients

External integrations commonly require:

```text
PAYMENT_API_URL
PAYMENT_TIMEOUT_SECONDS
PAYMENT_MAX_RETRIES
PAYMENT_API_KEY
```

Separate:

```text
Endpoint → ordinary configuration
Credential → secret
```

Timeouts and retry counts should be bounded.

Avoid configuration such as:

```text
MAX_RETRIES=999999
```

because operationally unsafe configuration can turn a transient failure into a traffic or resource amplification problem.

---

## Configuration and Feature Flags

Feature flags allow behavior to change without rebuilding the application.

Static flag:

```text
APP_ENABLE_NEW_CHECKOUT=true
```

Dynamic flag:

```text
Feature Flag Service
        ↓
Application
        ↓
Request
```

Dynamic flags introduce consistency and availability concerns.

Define:

- refresh interval;
- cache TTL;
- default behavior;
- failure behavior;
- rollout strategy;
- rollback mechanism.

---

## Configuration and Caching

Remote configuration should usually be cached.

Instead of:

```text
Request
  ↓
Secrets Manager
  ↓
Database request
```

prefer:

```text
Application startup
  ↓
Secrets Manager
  ↓
In-memory configuration
  ↓
Requests
```

This reduces:

- latency;
- cloud API calls;
- cost;
- runtime dependencies.

Dynamic configuration may require periodic refresh rather than startup-only loading.

---

## Configuration and Concurrency

Static configuration should generally be immutable.

This is safe:

```python
timeout = settings.request_timeout_seconds
```

This is dangerous:

```python
settings.request_timeout_seconds = calculate_new_timeout()
```

during concurrent request processing.

Mutable global configuration can produce inconsistent behavior across:

- threads;
- asyncio tasks;
- worker processes;
- replicas.

Dynamic configuration requires explicit synchronization and consistency semantics.

---

## Configuration Across Processes

A backend may run:

```text
Pod
 ├── worker 1
 ├── worker 2
 ├── worker 3
 └── worker 4
```

Each process generally has its own Python memory.

Changing an in-memory configuration object in one worker does not automatically update the others.

For multi-process dynamic configuration:

```text
Central source
      ↓
Each worker refreshes
```

or:

```text
Restart / rolling deployment
      ↓
All workers load new configuration
```

The latter is often simpler for static configuration.

---

## Configuration Across Replicas

Similarly:

```text
Pod A → configuration A
Pod B → configuration A
Pod C → configuration A
```

should generally remain consistent for static configuration.

Configuration rollout should be controlled through the deployment platform rather than manually changing individual pods.

---

## Configuration and Nginx

Nginx may have its own configuration:

```text
Nginx
    ↓
Load balancer / reverse proxy
    ↓
Python application
```

Examples include:

- upstream addresses;
- TLS configuration;
- request limits;
- timeouts.

These values are infrastructure configuration, not Python application settings.

Keep ownership boundaries clear.

---

## Configuration and Docker

Docker builds should not bake environment-specific secrets into images.

Avoid:

```dockerfile
ENV DATABASE_PASSWORD=secret
```

because image layers and metadata can expose sensitive values.

Prefer runtime injection:

```text
Docker image
      +
runtime configuration
      ↓
container
```

The same image should be usable across environments whenever practical.

---

## Configuration and CI/CD

CI/CD should manage configuration deliberately.

A typical flow is:

```mermaid
flowchart LR
    A[Git Commit] --> B[Build Artifact]
    B --> C[Test]
    C --> D[Security Checks]
    D --> E[Staging Configuration]
    E --> F[Staging]
    F --> G[Production Configuration]
    G --> H[Production Deployment]
```

CI should not accidentally inherit a developer's local `.env`.

Production secrets should come from controlled CI/CD or runtime secret-management mechanisms.

---

## Configuration Drift

Configuration drift occurs when environments differ unexpectedly.

Example:

```text
Staging:
TIMEOUT=5

Production:
TIMEOUT=60
```

This is acceptable if intentional.

The problem is:

```text
Staging:
TIMEOUT=5

Production:
TIMEOUT=60
```

with nobody knowing why.

Use declarative infrastructure/configuration and version-controlled deployment definitions where appropriate.

---

## Configuration Auditing

For production systems, track:

- who changed configuration;
- what changed;
- when it changed;
- why it changed;
- which deployment consumed it;
- whether the change was rolled back.

This is particularly important for:

- security settings;
- feature flags;
- database connection settings;
- traffic controls;
- rate limits.

---

## Observability

Configuration systems should expose safe operational metadata.

For example:

```text
service=order-service
environment=production
config_version=2026-09-06.3
```

Do not expose:

```text
DATABASE_PASSWORD
JWT_SECRET
API_KEY
```

Metrics can help identify configuration-related incidents:

```text
configuration_validation_failures
secret_retrieval_failures
configuration_refresh_failures
readiness_failures
```

---

## Health Checks

Health endpoints should not expose configuration values.

A good readiness endpoint communicates:

```text
Application configured correctly
+
required dependencies initialized
```

without returning:

```json
{
  "database_password": "...",
  "redis_url": "..."
}
```

Liveness and readiness should remain separate concepts.

---

## Error Handling

Configuration errors should be explicit.

Good:

```text
APP_DATABASE_POOL_SIZE must be greater than zero
```

Bad:

```text
Connection failed for postgresql://admin:password@db.internal
```

Errors should identify the configuration problem without leaking secrets.

---

## Testing Configuration

Configuration should be tested independently.

Test:

- missing required values;
- invalid types;
- invalid ranges;
- invalid URLs;
- invalid environment names;
- incompatible settings;
- secret retrieval failures;
- default values.

Example:

```python
import pytest
from pydantic import ValidationError

from order_service.config import Settings


def test_database_pool_size_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment="test",
            database_url="postgresql://localhost/orders",
            redis_url="redis://localhost:6379/0",
            database_pool_size=0,
        )
```

Configuration validation tests should be deterministic and independent of production infrastructure.

---

## Testing Configuration-Dependent Components

Prefer dependency injection:

```python
def create_payment_client(settings: Settings) -> PaymentClient:
    return PaymentClient(
        base_url=settings.payment_api_url,
        timeout=settings.payment_timeout_seconds,
    )
```

Tests can then construct controlled settings without modifying the process environment.

---

## Configuration Contract Testing

For larger systems, configuration can be treated as a contract.

For example:

```text
Deployment configuration
        ↓
Configuration schema
        ↓
Application startup
```

CI can validate required configuration keys and acceptable formats before deployment.

This prevents avoidable failures after a container has already reached production.

---

## Security Considerations

Configuration management is part of the security boundary.

Follow these principles:

- never commit secrets;
- never log secrets;
- use least-privilege access;
- use short-lived cloud credentials where practical;
- restrict access to production configuration;
- separate secret and non-secret configuration;
- rotate credentials;
- audit sensitive configuration changes;
- avoid secrets in Docker image layers;
- protect CI/CD secrets;
- avoid exposing configuration through health endpoints.

---

## High Availability

Configuration infrastructure itself can become a dependency.

If the application requires a remote configuration service on every request:

```text
Application
    ↓
Config service
    ↓
Request processing
```

then a configuration-service outage can become an application outage.

Prefer startup retrieval and caching for static configuration.

For dynamic configuration, define a safe degraded mode.

---

## Reliability

Configuration should have predictable failure behavior.

For example:

```text
Secret service unavailable at startup
    ↓
Application fails startup
```

may be preferable to:

```text
Secret service unavailable
    ↓
Application silently uses insecure default
```

For dynamic configuration:

```text
Configuration service unavailable
    ↓
Use last known valid configuration
```

may be appropriate if explicitly designed and safe.

Never invent fallback behavior for security-critical configuration.

---

## Disaster Recovery

Configuration must be included in disaster-recovery planning.

Recovery should account for:

```text
Source code
+
configuration definitions
+
secret store
+
IAM/RBAC
+
container image
+
private registries
+
deployment manifests
```

A service that can rebuild its code but cannot retrieve its required secrets is not fully recoverable.

---

## Cost Considerations

Configuration architecture can create operational cost.

Examples:

```text
Remote secret lookup per request
        ↓
High API call volume
        ↓
Higher cost + latency
```

Prefer:

```text
Startup retrieval
        ↓
In-memory cache
        ↓
Requests
```

when the security and rotation requirements allow it.

Dynamic configuration should be introduced when its operational value justifies its additional complexity.

---

## Production Configuration Checklist

### Schema

- [ ] Required values are explicit.
- [ ] Types are validated.
- [ ] Ranges are validated.
- [ ] Allowed values are constrained.
- [ ] Unsafe defaults are avoided.
- [ ] Cross-field requirements are validated.

### Security

- [ ] Secrets are stored outside source control.
- [ ] Secrets are not logged.
- [ ] Secret access uses least privilege.
- [ ] Credentials can be rotated.
- [ ] Docker images contain no embedded production secrets.
- [ ] CI/CD secrets are protected.

### Deployment

- [ ] Configuration is supplied independently of application code.
- [ ] Configuration changes are versioned or auditable.
- [ ] Rolling deployments support old and new versions.
- [ ] Production replicas receive consistent configuration.
- [ ] Rollback behavior is defined.

### Runtime

- [ ] Configuration is validated before readiness.
- [ ] Static configuration is immutable after startup.
- [ ] Remote configuration is appropriately cached.
- [ ] Dynamic configuration has explicit refresh semantics.
- [ ] Configuration errors are observable without exposing secrets.

### Infrastructure

- [ ] Database pool sizes account for replicas and workers.
- [ ] Redis connection limits account for total concurrency.
- [ ] Kafka topics and consumer groups are explicitly configured.
- [ ] HTTP timeouts and retries are bounded.
- [ ] Kubernetes ConfigMaps and Secrets are used appropriately.
- [ ] AWS workload identity is preferred over long-lived credentials.

---

## Common Mistakes

### Treating Configuration as Global Mutable State

A mutable global settings object can create unpredictable behavior across concurrent execution.

Prefer immutable configuration after startup.

### Scattering `os.getenv()` Calls

Repeated environment parsing creates duplicated defaults and inconsistent validation.

Centralize configuration loading.

### Putting Secrets in Configuration Files

A configuration file committed to Git is not an appropriate secret store.

Use a secret-management system.

### Using Unsafe Defaults

Security-critical values should not silently fall back to development credentials.

### Validating Too Late

Configuration should be validated before accepting traffic.

### Making Everything Dynamic

Dynamic configuration introduces consistency, caching, failure, and rollout complexity.

Use it only when required.

### Logging the Settings Object

Settings objects often contain secrets.

Log only safe metadata.

### Using Generic Variable Names

Names such as:

```text
TIMEOUT
URL
PASSWORD
```

are ambiguous.

Prefer namespaced and explicit configuration names.

---

## Production Pitfalls

### Configuration Drift

Manual changes to individual environments create undocumented differences.

Use controlled, auditable configuration deployment.

### Secret Rotation Without Refresh Strategy

Rotating a secret does not automatically update a running Python process.

Define restart or refresh behavior.

### Remote Configuration as a Hard Runtime Dependency

Fetching configuration on every request creates unnecessary latency and a new availability dependency.

Cache static values.

### Configuration Incompatible With Rolling Deployments

Old and new replicas can coexist temporarily.

Ensure configuration changes are backward-compatible during rollout.

### Incorrect Connection Pool Sizing

Per-process values must be multiplied by worker and replica counts.

### Environment-Specific Code Branches

Excessive `if production` logic makes behavior harder to test and reason about.

Prefer explicit configuration values.

---

## Recommended Configuration Architecture

For a production backend:

```text
                 Configuration Sources
                          │
          ┌───────────────┼────────────────┐
          ↓               ↓                ↓
       Defaults       Environment      Secret Store
          │               │                │
          └───────────────┼────────────────┘
                          ↓
                 Configuration Loader
                          ↓
                    Parse + Validate
                          ↓
                   Typed Settings
                          ↓
                 Application Factory
                          ↓
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
     FastAPI           PostgreSQL         Redis
        │
        ↓
      Kafka / External APIs / Workers
```

This architecture keeps configuration concerns concentrated at the application boundary while allowing infrastructure and runtime systems to provide the actual values.

---

## Configuration Management Principles

A senior backend design should follow these principles:

### Explicit

Every important setting should have a clear name, type, owner, and source.

### Validated

Invalid configuration should fail before production traffic reaches the instance.

### Immutable

Static configuration should not change unpredictably during process execution.

### Secure

Secrets should have dedicated storage, access control, rotation, and auditing.

### Reproducible

The same application version should be deployable with known configuration across environments.

### Observable

Configuration failures should be visible without exposing sensitive values.

### Backward-Compatible

Configuration changes should account for rolling deployments and mixed application versions.

### Minimal

Do not introduce a configuration system more complicated than the application's requirements justify.

---

## Interview Traps

### Is Configuration Management the Same as Environment Variables?

No.

Environment variables are one configuration source. Configuration management covers definition, validation, precedence, distribution, change management, security, observability, and lifecycle.

### Should Configuration Be Mutable?

Usually not for static settings.

Static configuration should normally be loaded and validated at startup. Dynamic configuration requires explicit refresh and consistency semantics.

### Why Validate Configuration at Startup?

It fails deployment errors early and prevents incorrectly configured instances from accepting traffic.

### Why Not Read Secrets From AWS Secrets Manager on Every Request?

It adds latency, cost, and an availability dependency. Static secrets can usually be loaded and cached appropriately.

### Are Kubernetes Secrets Automatically Secure?

No.

They provide a mechanism for sensitive configuration, but actual security depends on RBAC, encryption, cluster access, workload isolation, and secret lifecycle controls.

### Why Is Configuration Part of Scalability?

Settings such as connection pools, worker counts, batch sizes, concurrency limits, and timeouts directly determine resource consumption.

### Why Should Environment-Specific Logic Be Minimized?

Because configuration should describe deployment differences while application code should describe behavior. Excessive environment branching creates multiple behavioral variants of the same application.

### Why Is Configuration Versioning Important?

Because application versions and configuration versions form a compatibility contract, especially during rolling deployments and rollback.

## Key Takeaways

- **Configuration management is a lifecycle, not an environment-variable lookup:** define, validate, distribute, observe, change, and roll back configuration deliberately.
- **Create a strong configuration boundary:** centralize parsing and validation into typed settings, then inject configuration into application components rather than reading environment variables throughout the codebase.
- **Treat static configuration as immutable and secrets as security-sensitive:** use dedicated secret-management systems, least-privilege access, rotation, and safe logging practices.
- **Design configuration for distributed production systems:** account for replicas, workers, connection pools, rolling deployments, dynamic refresh, configuration drift, and infrastructure capacity.
- **Make configuration failures observable and recoverable:** fail fast on invalid startup configuration, define safe behavior for dynamic configuration failures, and include configuration and secret access in disaster-recovery planning.