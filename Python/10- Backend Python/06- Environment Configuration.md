# 06- Environment Configuration

## Overview

Environment configuration is the mechanism used to provide an application with values that vary between execution environments without changing application code.

Typical environments include:

```text
Local development
      ↓
Testing
      ↓
CI
      ↓
Staging
      ↓
Production
```

The same Python application may need different:

- database URLs;
- Redis endpoints;
- Kafka brokers;
- API endpoints;
- logging levels;
- feature flags;
- worker settings;
- security configuration;
- cloud resource identifiers.

A production backend should separate **application code**, **configuration**, and **secrets**:

```text
Application code
    ↓
Configuration interface
    ↓
Environment / config source
    ├── non-secret settings
    └── secrets
```

The goal is not to make every value an environment variable. The goal is to make configuration explicit, validated, secure, testable, and appropriate for the deployment environment.

---

## Configuration vs Code

Configuration represents values that can vary independently of application logic.

For example:

```python
DATABASE_POOL_SIZE = 20
```

might be configuration when the appropriate value depends on deployment capacity.

The code should define the behavior:

```python
pool = create_pool(size=settings.database_pool_size)
```

while the environment determines the value:

```text
Local      → 5
Staging    → 10
Production → 50
```

This avoids creating separate code branches for each environment.

---

## Configuration vs Secrets

Not all configuration is secret.

| Category | Example | Secret? |
|---|---|---:|
| Environment | `production` | No |
| Log level | `INFO` | No |
| Port | `8000` | No |
| Feature flag | `ENABLE_V2=true` | Usually no |
| Database hostname | `postgres.internal` | Usually no |
| Database password | `...` | Yes |
| API key | `...` | Yes |
| JWT signing key | `...` | Yes |
| AWS credentials | `...` | Yes |

Secrets require stronger controls than ordinary configuration.

---

## Twelve-Factor Configuration Principle

A common backend design principle is to keep environment-specific configuration outside the application artifact.

Conceptually:

```text
Same artifact
    +
different environment configuration
    ↓
different deployment behavior
```

For example:

```text
order-service:1.8.0

Local:
DATABASE_URL=postgresql://localhost/orders

Production:
DATABASE_URL=postgresql://prod-db/orders
```

The application image does not need to be rebuilt merely because the database endpoint changes.

---

## Configuration Sources

Common configuration sources include:

- environment variables;
- command-line arguments;
- configuration files;
- Kubernetes ConfigMaps;
- Kubernetes Secrets;
- AWS Secrets Manager;
- AWS Systems Manager Parameter Store;
- secret/configuration services;
- platform-provided metadata.

A mature application can support multiple sources while maintaining one configuration interface inside the Python code.

---

## Configuration Precedence

If multiple sources are supported, define their precedence explicitly.

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

The exact precedence should be documented and consistent.

Ambiguous precedence is a common source of deployment bugs.

---

## Environment Variables

Python reads environment variables through `os.environ` or `os.getenv()`.

Example:

```python
import os

log_level = os.getenv("LOG_LEVEL", "INFO")
```

For a production application, avoid scattering these calls throughout the codebase.

Prefer a centralized configuration layer.

---

## Centralized Configuration

Instead of:

```python
import os

timeout = int(os.getenv("HTTP_TIMEOUT", "5"))
```

throughout multiple modules, define one configuration object:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    log_level: str = "INFO"
    http_timeout_seconds: float = 5.0

    model_config = SettingsConfigDict(
        env_prefix="APP_",
    )


settings = Settings()
```

Application code then uses:

```python
from order_service.config import settings

timeout = settings.http_timeout_seconds
```

This provides a single configuration boundary.

---

## Why Centralize Configuration

Centralization provides:

- validation;
- type conversion;
- consistent defaults;
- discoverability;
- testability;
- easier dependency injection;
- fewer duplicated parsing rules.

Without centralization:

```text
module A → reads LOG_LEVEL
module B → reads LOG_LEVEL differently
module C → applies another default
```

The application develops inconsistent configuration semantics.

---

## Configuration Object

A configuration object should represent the settings the application actually understands.

Example:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    database_url: str
    database_pool_size: int = 10

    redis_url: str
    request_timeout_seconds: float = 5.0

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        extra="ignore",
    )
```

The application can then consume:

```python
settings.database_url
settings.database_pool_size
settings.redis_url
```

rather than reading raw environment variables everywhere.

---

## Type Conversion

Environment variables are strings.

For example:

```text
APP_DEBUG=false
APP_DATABASE_POOL_SIZE=20
APP_TIMEOUT=2.5
```

Python initially receives:

```python
"false"
"20"
"2.5"
```

A configuration library can convert these to:

```python
False
20
2.5
```

This is important because:

```python
os.getenv("APP_DEBUG")
```

returns a string, not a Boolean.

---

## Boolean Configuration

Avoid naïve parsing:

```python
bool(os.getenv("APP_DEBUG"))
```

because:

```python
bool("false")  # True
```

A configuration system should perform explicit Boolean parsing.

For example, Pydantic Settings can validate:

```text
false → False
true  → True
```

according to its supported parsing rules.

---

## Required vs Optional Configuration

Distinguish between:

```python
database_url: str
```

and:

```python
log_level: str = "INFO"
```

The first requires an explicit value.

The second has a safe default.

Production-critical configuration should generally fail fast when missing rather than silently using an unsafe default.

---

## Fail Fast

Consider:

```python
class Settings(BaseSettings):
    database_url: str
```

If the value is missing, configuration validation should fail during application startup.

This is preferable to:

```text
Application starts
      ↓
Receives request
      ↓
Attempts database connection
      ↓
Fails unexpectedly
```

Instead:

```text
Application starts
      ↓
Validate configuration
      ↓
Invalid configuration
      ↓
Fail startup
```

This makes deployment failures explicit and observable.

---

## Startup Validation

A backend application should validate configuration before becoming ready.

```mermaid
sequenceDiagram
    participant K as Kubernetes
    participant A as Application
    participant C as Configuration
    participant DB as PostgreSQL

    K->>A: Start container
    A->>C: Load configuration
    C-->>A: Validate values
    A->>DB: Initialize dependencies
    DB-->>A: Connection available
    A-->>K: Readiness = Ready
```

If configuration is invalid, the application should fail or remain unready rather than serving partially functional traffic.

---

## Configuration Lifecycle

A typical application lifecycle is:

```text
Process start
    ↓
Load configuration
    ↓
Parse values
    ↓
Validate values
    ↓
Construct application dependencies
    ↓
Start server
    ↓
Serve requests
```

Configuration should normally be immutable for the lifetime of a process unless the application explicitly supports dynamic configuration reloads.

---

## `.env` Files

A `.env` file can provide local development configuration:

```dotenv
APP_ENVIRONMENT=development
APP_LOG_LEVEL=DEBUG
APP_DATABASE_URL=postgresql://localhost/orders
APP_REDIS_URL=redis://localhost:6379/0
```

A configuration library can load this file during local development.

`.env` files are convenient but should not automatically be treated as production secret stores.

---

## `.env.example`

Commit a sanitized template:

```dotenv
APP_ENVIRONMENT=development
APP_LOG_LEVEL=INFO
APP_DATABASE_URL=postgresql://localhost/orders
APP_REDIS_URL=redis://localhost:6379/0
APP_EXTERNAL_API_KEY=
```

This documents expected configuration without exposing actual credentials.

---

## `.gitignore`

Actual local environment files containing secrets should generally be ignored:

```gitignore
.env
.env.*
!.env.example
```

The exact pattern should be chosen carefully because some projects intentionally commit environment-specific non-secret files.

The important rule is:

> Never commit real secrets merely because the file is convenient.

---

## Local Development

A typical local setup might be:

```text
Developer
    ↓
.venv
    ↓
.env
    ↓
Python configuration object
    ↓
FastAPI / Django
    ↓
Local PostgreSQL / Redis
```

For example:

```dotenv
APP_ENVIRONMENT=development
APP_LOG_LEVEL=DEBUG
APP_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/orders
APP_REDIS_URL=redis://localhost:6379/0
```

Local configuration should be easy to create and safe to share as a template.

---

## Testing Configuration

Tests should avoid depending accidentally on a developer's environment.

A test suite should provide explicit configuration:

```python
import os

os.environ["APP_ENVIRONMENT"] = "test"
```

However, setting environment variables globally in arbitrary test modules can create test-order dependencies.

Prefer fixture-based or dependency-injection approaches when the configuration architecture supports them.

---

## Configuration Injection

Application components can receive configuration explicitly.

```python
class PaymentClient:
    def __init__(self, base_url: str, timeout: float) -> None:
        self.base_url = base_url
        self.timeout = timeout
```

Composition code can provide:

```python
client = PaymentClient(
    base_url=settings.payment_api_url,
    timeout=settings.request_timeout_seconds,
)
```

This makes the component easier to test than having it read global environment variables itself.

---

## Dependency Injection in FastAPI

FastAPI applications can expose configuration through dependencies.

```python
from functools import lru_cache

from fastapi import Depends, FastAPI
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "order-service"


@lru_cache
def get_settings() -> Settings:
    return Settings()


app = FastAPI()


@app.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"service": settings.service_name}
```

Caching the configuration object avoids repeatedly parsing environment configuration during requests.

The configuration object should not be mutated after initialization.

---

## Django Configuration

Django commonly separates configuration from code through settings modules.

For example:

```text
config/
└── settings/
    ├── base.py
    ├── development.py
    └── production.py
```

Environment variables can provide deployment-specific values:

```python
import os

DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"
```

For larger applications, use centralized typed configuration where appropriate rather than scattering environment parsing across settings and application modules.

---

## Configuration Namespaces

Prefixing environment variables helps avoid collisions.

For example:

```text
APP_DATABASE_URL
APP_REDIS_URL
APP_LOG_LEVEL
APP_HTTP_TIMEOUT
```

rather than generic names such as:

```text
URL
TIMEOUT
PASSWORD
```

Namespacing becomes especially valuable when several applications, workers, or tools share a process environment.

---

## Configuration Naming

Prefer names that communicate meaning:

```text
APP_DATABASE_POOL_SIZE
APP_REQUEST_TIMEOUT_SECONDS
APP_KAFKA_CONSUMER_GROUP
```

Avoid ambiguous values:

```text
APP_TIMEOUT=10
```

unless the unit and scope are obvious.

Prefer:

```text
APP_REQUEST_TIMEOUT_SECONDS=10
```

Explicit units reduce operational mistakes.

---

## URLs and Structured Configuration

Some configuration values naturally contain structured data:

```text
postgresql://user:password@host:5432/orders
redis://host:6379/0
```

Treat these values carefully because URLs can contain credentials.

Prefer dedicated typed URL parsing when the configuration library supports it.

Do not log full connection URLs if they may contain passwords or tokens.

---

## Secrets

Secrets include:

- database passwords;
- API keys;
- OAuth client secrets;
- JWT signing keys;
- encryption keys;
- private certificates;
- cloud credentials.

They should not be stored in:

```text
Git
Dockerfile
Docker image layers
application logs
source code
public configuration files
```

Use a dedicated secret-management mechanism.

---

## Kubernetes ConfigMaps

Kubernetes `ConfigMap` is appropriate for non-sensitive configuration.

Conceptually:

```text
ConfigMap
    ↓
Pod environment
    ↓
Python configuration
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
```

Do not use a ConfigMap for passwords or other sensitive credentials.

---

## Kubernetes Secrets

Sensitive configuration can be supplied through Kubernetes Secrets.

Conceptually:

```text
Kubernetes Secret
       ↓
Pod environment / mounted file
       ↓
Python application
```

Kubernetes Secrets provide a mechanism for representing sensitive configuration, but production security still depends on:

- RBAC;
- encryption at rest;
- cluster security;
- access controls;
- secret rotation;
- workload isolation.

A Kubernetes Secret should not be treated as automatically equivalent to a dedicated enterprise secret-management system.

---

## AWS Secrets Manager

AWS Secrets Manager is suitable for storing and retrieving sensitive values such as:

```text
Database credentials
API credentials
Encryption secrets
Third-party integration secrets
```

A production architecture might be:

```text
EKS / ECS workload
       ↓
IAM identity
       ↓
AWS Secrets Manager
       ↓
Secret
       ↓
Application configuration
```

Use workload identity mechanisms rather than embedding long-lived AWS access keys in environment variables when the deployment platform supports a stronger identity model.

---

## AWS Systems Manager Parameter Store

Parameter Store can be useful for:

- non-secret operational parameters;
- environment configuration;
- secure parameters where appropriate.

A typical separation is:

```text
Parameter Store
    → operational configuration

Secrets Manager
    → sensitive credentials/secrets
```

The exact choice depends on requirements such as rotation, access patterns, cost, and application architecture.

---

## Secret Rotation

A secret should not necessarily be considered permanent.

For example:

```text
Database password
      ↓
Rotation
      ↓
New credential
      ↓
Application refresh
```

If an application only reads secrets once at startup, rotation may require:

- process restart;
- rolling deployment;
- explicit configuration reload.

If live rotation is required, design and test the refresh mechanism explicitly.

Do not assume environment variables automatically update when a secret changes.

---

## Environment Variables Are Process State

Environment variables belong to a process environment.

At startup:

```text
Operating system
    ↓
Environment
    ↓
Python process
```

The application reads those values.

Changing the configuration source later does not automatically mutate values already loaded into the process.

This is why many production systems apply configuration changes through controlled restarts or rolling deployments.

---

## Immutable Configuration

Prefer:

```python
settings = Settings()
```

followed by read-only usage.

Avoid:

```python
settings.database_url = "..."
```

during request processing.

Mutable global configuration can create:

- race conditions;
- inconsistent requests;
- difficult debugging;
- unexpected behavior across workers.

If dynamic configuration is required, use an explicit configuration-management design.

---

## Dynamic Configuration

Some systems need configuration changes without redeployment.

Examples include:

- feature flags;
- traffic controls;
- rate limits;
- experimentation parameters.

A dynamic configuration architecture might be:

```text
Configuration service
        ↓
Application cache
        ↓
Request processing
```

This is fundamentally different from static startup configuration.

Dynamic configuration requires decisions about:

- polling;
- push notifications;
- cache TTL;
- consistency;
- rollback;
- failure behavior.

Do not turn every environment variable into dynamically reloadable state.

---

## Feature Flags

Feature flags are configuration with application-level behavior implications.

Example:

```text
APP_ENABLE_NEW_CHECKOUT=true
```

For simple static deployments, an environment variable can be sufficient.

For high-scale systems requiring runtime changes:

```text
Feature flag service
        ↓
Application
        ↓
Request
```

The system must define what happens if the feature-flag service is unavailable.

---

## Configuration Defaults

Defaults should be safe and intentional.

Good:

```python
log_level: str = "INFO"
request_timeout_seconds: float = 5.0
```

Potentially dangerous:

```python
database_password: str = ""
jwt_secret: str = "development-secret"
```

Security-sensitive configuration should generally have no production-safe default.

---

## Environment-Specific Behavior

Avoid excessive branching:

```python
if environment == "production":
    ...
elif environment == "staging":
    ...
else:
    ...
```

Prefer configuration-driven behavior:

```python
client = PaymentClient(
    base_url=settings.payment_api_url,
    timeout=settings.payment_timeout,
)
```

This keeps environment differences in configuration rather than application logic.

---

## Configuration Validation

Validation should cover:

- required values;
- data types;
- allowed ranges;
- URLs;
- enumerated environments;
- mutually dependent settings.

For example:

```python
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: Literal["development", "staging", "production"]
    database_pool_size: int = 10
    request_timeout_seconds: float = 5.0
```

The application should reject invalid values rather than continuing with ambiguous behavior.

---

## Cross-Field Validation

Some settings are valid only in combination.

For example:

```text
TLS enabled
    +
certificate path required
```

or:

```text
Kafka enabled
    +
broker list required
```

These constraints should be validated at startup.

Do not wait until the first production request to discover an invalid configuration combination.

---

## Configuration Schema

A mature configuration object can act as a schema:

```text
Configuration source
        ↓
Parsing
        ↓
Validation
        ↓
Typed Settings
        ↓
Application
```

This creates a strong boundary between untrusted external configuration and internal application state.

---

## Logging Configuration

Logging should be configurable without changing source code.

Example:

```dotenv
APP_LOG_LEVEL=INFO
```

Production commonly uses structured logs and a controlled log level.

Avoid logging:

```text
DATABASE_URL
API_KEY
Authorization headers
JWT tokens
passwords
```

Configuration debugging should redact sensitive values.

---

## Observability

Configuration errors should be observable.

Useful signals include:

- startup failure counts;
- readiness failures;
- configuration validation errors;
- secret retrieval failures;
- dependency initialization failures.

Do not expose secret values in error messages.

For example:

```text
Invalid configuration: APP_DATABASE_POOL_SIZE must be > 0
```

is appropriate.

This is dangerous:

```text
Invalid DATABASE_URL: postgresql://admin:secret@...
```

---

## Configuration and Health Checks

Health endpoints should distinguish between:

```text
Liveness
    → process is alive

Readiness
    → process can serve traffic
```

If mandatory configuration is invalid, the process may fail startup or remain unready.

Do not create health checks that expose sensitive configuration values.

---

## Configuration and Kubernetes Readiness

A typical Kubernetes lifecycle is:

```text
Container starts
    ↓
Configuration validation
    ↓
Dependency initialization
    ↓
Readiness probe passes
    ↓
Traffic received
```

This prevents traffic from being sent to an application that cannot operate correctly.

---

## Configuration and Graceful Shutdown

Configuration often affects resource lifecycle:

```text
Database pool
Redis client
Kafka consumer
HTTP client
Celery worker
```

At shutdown:

```text
Stop accepting work
    ↓
Finish / cancel in-flight work
    ↓
Close clients
    ↓
Close connection pools
    ↓
Exit
```

Configuration should not be re-read unpredictably during shutdown.

---

## Configuration in Background Workers

Celery and Kafka consumers often share configuration concepts with API services:

```text
API
 ├── DATABASE_URL
 ├── REDIS_URL
 └── LOG_LEVEL

Worker
 ├── DATABASE_URL
 ├── REDIS_URL
 ├── BROKER_URL
 └── LOG_LEVEL
```

Shared configuration should be modeled deliberately.

Do not create a huge global settings object containing every setting for every service if services can remain independently configured.

---

## Configuration and PostgreSQL

Typical PostgreSQL settings include:

```text
DATABASE_URL
DATABASE_POOL_SIZE
DATABASE_POOL_TIMEOUT
DATABASE_SSL_MODE
```

Configuration should account for the relationship between:

```text
Application workers
        ×
Connections per worker
        ×
Replicas
        ↓
Total PostgreSQL connections
```

For example:

```text
8 pods
×
4 worker processes
×
10 connections
=
320 potential connections
```

The configuration is therefore an infrastructure-capacity decision, not merely an application detail.

---

## Configuration and Redis

Redis configuration might include:

```text
REDIS_URL
REDIS_SOCKET_TIMEOUT
REDIS_MAX_CONNECTIONS
```

Connection limits should account for:

```text
pods
× workers
× clients
× connection pool size
```

Over-provisioning pools can exhaust Redis capacity even when application traffic is moderate.

---

## Configuration and Kafka

Kafka consumers may require:

```text
KAFKA_BOOTSTRAP_SERVERS
KAFKA_GROUP_ID
KAFKA_TOPIC
KAFKA_SECURITY_PROTOCOL
```

Configuration errors can cause:

- consumers joining the wrong group;
- reading the wrong topic;
- connecting to the wrong cluster;
- authentication failures.

Validate these values before starting the worker.

---

## Configuration and HTTP Clients

External services often need:

```text
PAYMENT_API_URL
PAYMENT_TIMEOUT_SECONDS
PAYMENT_MAX_RETRIES
PAYMENT_API_KEY
```

Separate endpoint configuration from credentials:

```text
PAYMENT_API_URL       → non-secret
PAYMENT_API_KEY       → secret
```

Timeout and retry configuration should be explicitly bounded.

Never allow an environment variable to accidentally configure infinite retries in a production service.

---

## Configuration and Networking

Configuration often determines network topology:

```text
Python service
    ↓
Nginx / Load Balancer
    ↓
REST / gRPC service
    ↓
Database / cache / broker
```

Examples:

```text
DATABASE_HOST
REDIS_HOST
KAFKA_BOOTSTRAP_SERVERS
PAYMENT_API_URL
```

These values should reflect the deployment environment without requiring source-code changes.

---

## Configuration Security

Environment variables are convenient but are not inherently secret.

Depending on the platform, environment values can potentially be exposed through:

- process inspection;
- debugging interfaces;
- crash dumps;
- logs;
- container metadata;
- misconfigured observability systems.

For highly sensitive secrets, consider whether mounted secret files, SDK-based secret retrieval, or a dedicated secret-management integration provides a stronger security model.

---

## Avoid Secret Leakage

Never do:

```python
logger.info("Application settings: %s", settings)
```

if the object contains secrets.

Instead expose only safe metadata:

```python
logger.info(
    "Application configured",
    extra={
        "environment": settings.environment,
        "log_level": settings.log_level,
    },
)
```

Secrets should be redacted by design rather than manually removed after logging.

---

## Configuration and Source Control

Commit:

```text
pyproject.toml
.env.example
configuration schemas
safe defaults
documentation
```

Usually do not commit:

```text
.env
production credentials
private keys
access tokens
database passwords
```

Git history matters. A secret committed and later deleted can remain recoverable from previous commits.

---

## Configuration and CI/CD

CI should explicitly provide the configuration required for each stage.

Example:

```text
Pull Request
    ↓
Test configuration
    ↓
Unit tests
    ↓
Integration tests
    ↓
Build
    ↓
Deployment configuration
    ↓
Staging
    ↓
Production
```

CI secrets should come from the CI platform's secret-management capabilities rather than repository files.

---

## Configuration Drift

Configuration drift occurs when environments unexpectedly diverge.

Example:

```text
Staging:
APP_REQUEST_TIMEOUT_SECONDS=5

Production:
APP_REQUEST_TIMEOUT_SECONDS=60
```

This may be intentional, but it should be documented.

A better approach is to define configuration as code where appropriate and track environment-specific differences explicitly.

---

## Configuration Versioning

Application code and configuration often evolve together.

If version `2.0` requires:

```text
NEW_PAYMENT_API_URL
```

the deployment process should ensure the configuration exists before version `2.0` receives traffic.

For breaking configuration changes:

```text
Deploy compatible configuration
        ↓
Deploy application
        ↓
Migrate / switch behavior
        ↓
Remove obsolete configuration
```

This reduces deployment ordering failures.

---

## Configuration Rollbacks

Rollback should account for configuration compatibility.

Suppose:

```text
Version 2 → requires NEW_API_URL
Version 1 → does not
```

Removing `NEW_API_URL` immediately may be safe, but changing an existing setting may break both versions.

During rolling deployments, maintain backward-compatible configuration until all old replicas are gone.

---

## High Availability

Configuration must support rolling deployment.

For example:

```text
Old version
    ↓
New configuration
    ↓
New version
    ↓
Old version terminated
```

Configuration changes should not require all replicas to restart simultaneously unless planned.

Avoid configuration designs that create a single-point-of-failure configuration service without caching or fallback behavior.

---

## Disaster Recovery

A disaster-recovery plan should answer:

- Where are non-secret configuration definitions stored?
- Where are secrets stored?
- Can workloads retrieve them after infrastructure recreation?
- Are IAM permissions recoverable?
- Are private configuration services available?
- Can the application be rebuilt from source and configuration?
- How are configuration versions restored?

Configuration is part of the service's recoverability model.

---

## Cost Considerations

Configuration management affects cost through:

- secret-manager API calls;
- configuration-service requests;
- application startup time;
- cache behavior;
- operational complexity.

Do not query a remote secret store on every API request.

Prefer:

```text
Startup
   ↓
Retrieve secret
   ↓
Keep in controlled process memory
   ↓
Use for requests
```

unless dynamic rotation requirements require a different design.

---

## Configuration Caching

Remote configuration should generally be cached appropriately.

For example:

```text
AWS Secrets Manager
        ↓
Startup retrieval
        ↓
Application memory
        ↓
Requests
```

This avoids:

```text
10,000 requests
    ↓
10,000 secret-manager calls
```

which can create unnecessary latency, cost, and an additional runtime dependency.

---

## Production Configuration Example

A production service might receive:

```dotenv
APP_ENVIRONMENT=production
APP_LOG_LEVEL=INFO
APP_DATABASE_POOL_SIZE=20
APP_REQUEST_TIMEOUT_SECONDS=5
APP_REDIS_MAX_CONNECTIONS=50
```

Secrets are provided separately:

```text
APP_DATABASE_URL
APP_REDIS_URL
PAYMENT_API_KEY
JWT_SIGNING_KEY
```

The application converts these external values into a validated internal configuration model.

---

## Recommended Configuration Architecture

```mermaid
flowchart TD
    A[Source Repository] --> B[pyproject.toml / Config Schema]
    C[Local .env] --> E[Configuration Loader]
    D[CI / Platform Configuration] --> E
    F[Kubernetes ConfigMap] --> E
    G[Secrets Manager] --> E

    E --> H[Parse]
    H --> I[Validate]
    I --> J[Typed Settings]
    J --> K[Application Dependencies]
    K --> L[FastAPI / Django]
    K --> M[PostgreSQL]
    K --> N[Redis]
    K --> O[Kafka]
```

The key boundary is:

```text
External configuration
        ↓
Validated internal representation
        ↓
Application
```

---

## Recommended Project Structure

A FastAPI-style project might use:

```text
src/
└── order_service/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── api/
    ├── application/
    ├── domain/
    └── infrastructure/
```

`config.py` owns configuration parsing and validation.

Application components consume typed settings rather than reading raw environment variables.

---

## Common Mistakes

### Reading Environment Variables Everywhere

Bad:

```python
timeout = int(os.getenv("TIMEOUT", "5"))
```

in many modules.

This duplicates parsing and defaults.

Centralize configuration.

### Using Strings for Everything

Environment variables are strings, but application configuration should have appropriate types.

### Using Unsafe Defaults

Do not default production credentials or signing keys to development values.

### Committing `.env`

Local environment files frequently contain secrets.

Use `.env.example` for documentation and ignore real secret-bearing files.

### Logging Configuration Objects

Configuration may contain credentials.

Log only safe fields.

### Treating Environment Variables as Automatically Secure

Environment variables can leak through process inspection, diagnostics, logs, or platform misconfiguration.

### Dynamically Re-reading Configuration Without a Design

Changing configuration while requests are running can create inconsistent behavior.

### Using Configuration for Application Logic

Do not create large environment-specific branches when a configuration value can express the difference cleanly.

---

## Production Pitfalls

### Configuration Missing at Startup

If validation happens only when a request reaches a code path, deployment errors become runtime incidents.

Validate mandatory configuration before readiness.

### Configuration Drift

Manual environment changes can create differences that are difficult to reproduce.

Prefer declarative deployment configuration and controlled changes.

### Secret Rotation Without Application Support

Rotating a secret in the secret store does not necessarily update a running process.

Define whether restart or live reload is required.

### Overly Large Global Settings Objects

A single settings class containing every possible configuration value can create coupling across services and workers.

Keep configuration scoped to the application or component where practical.

### Remote Configuration on Every Request

This adds latency, cost, and an additional failure dependency.

Cache static configuration.

### Configuration Changes During Rolling Deployments

Ensure old and new application versions can coexist with the deployed configuration during rollout.

---

## Best Practices

- Centralize configuration loading and validation.
- Use typed configuration objects.
- Fail fast on missing or invalid required configuration.
- Keep secrets separate from ordinary configuration.
- Use `.env.example` for local-development documentation.
- Never commit real credentials.
- Avoid logging sensitive configuration.
- Prefix environment variables to avoid collisions.
- Make units explicit in configuration names.
- Keep environment-specific behavior configuration-driven.
- Use Kubernetes ConfigMaps for appropriate non-secret configuration.
- Use Kubernetes Secrets or dedicated secret-management systems for sensitive values.
- Prefer workload identity over long-lived cloud credentials.
- Cache configuration retrieved from remote systems.
- Design secret rotation explicitly.
- Validate configuration before readiness.
- Keep configuration changes backward-compatible during rolling deployments.
- Track configuration changes through CI/CD where practical.
- Scope configuration to the services that actually need it.

---

## Configuration Checklist

### Design

- [ ] Configuration is separated from application logic.
- [ ] Configuration ownership is explicit.
- [ ] Required and optional values are distinguished.
- [ ] Configuration has appropriate types.
- [ ] Defaults are safe.

### Security

- [ ] Secrets are not committed to Git.
- [ ] Secrets are not logged.
- [ ] Secret access uses appropriate IAM/RBAC.
- [ ] Private credentials are rotated.
- [ ] Production configuration sources are protected.

### Runtime

- [ ] Configuration is validated at startup.
- [ ] Invalid configuration prevents readiness.
- [ ] Configuration is not mutated during normal request processing.
- [ ] Remote configuration is appropriately cached.
- [ ] Secret rotation behavior is documented.

### Deployment

- [ ] Local, CI, staging, and production configuration are explicit.
- [ ] Environment-specific differences are intentional.
- [ ] Rolling deployments remain configuration-compatible.
- [ ] Production artifacts do not contain environment-specific secrets.
- [ ] Disaster recovery includes configuration and secret access.

### Backend Infrastructure

- [ ] Database pool sizes account for worker and replica counts.
- [ ] Redis connection limits account for total application concurrency.
- [ ] Kafka configuration identifies the correct cluster, topic, and consumer group.
- [ ] External API timeouts and retries are bounded.
- [ ] Kubernetes readiness reflects configuration validity.

## Interview Traps

### Are Environment Variables Only for Secrets?

No.

They are commonly used for environment-specific configuration, both secret and non-secret.

### Are Environment Variables Secure by Default?

No.

They are convenient configuration inputs, not inherently secure secret storage.

### Should Every Configuration Value Be an Environment Variable?

No.

Use the simplest appropriate configuration mechanism. Stable project metadata belongs in project configuration, while deployment-specific values often belong in environment or platform configuration.

### Why Validate Configuration at Startup?

To fail fast before the service accepts traffic, making deployment errors explicit rather than turning them into runtime failures.

### Why Use a Typed Settings Object?

It centralizes parsing, validation, defaults, and access patterns and prevents raw environment-variable handling from spreading throughout the codebase.

### Should Secrets Be Loaded on Every Request?

Usually no.

Static secrets should generally be loaded and cached appropriately, unless the architecture explicitly requires dynamic retrieval or rotation.

### Does Updating a Secret Automatically Update Environment Variables?

Usually no.

A running process generally retains the values it received. Secret rotation therefore requires an explicit refresh or restart strategy.

### Should Configuration Be Mutable?

Usually no.

Static application configuration should be treated as immutable after startup. Dynamic configuration requires explicit consistency, caching, failure, and rollout semantics.

### Why Does Database Pool Configuration Matter at the Infrastructure Level?

Because total connections are multiplied across workers and replicas:

```text
workers × pool size × replicas
```

A locally reasonable pool can overwhelm PostgreSQL at production scale.

## Key Takeaways

- **Centralize and validate configuration:** convert external strings into a typed configuration model and fail fast before the service becomes ready.
- **Separate configuration from secrets:** ordinary deployment settings and sensitive credentials have different storage, access, logging, and rotation requirements.
- **Keep the application artifact environment-independent:** use configuration to adapt the same code/image to local, staging, and production environments.
- **Treat configuration as an operational dependency:** database pools, Redis limits, Kafka settings, timeouts, feature flags, and cloud resources directly affect reliability, scalability, and cost.
- **Design configuration changes for production:** support secure secret rotation, configuration versioning, rolling deployments, observability, and disaster recovery rather than relying on manual environment changes.