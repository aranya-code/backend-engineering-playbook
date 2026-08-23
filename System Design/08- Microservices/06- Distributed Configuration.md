# 06- Distributed Configuration

## Overview

Distributed configuration is the practice of managing application configuration centrally or consistently across multiple services, environments, and deployment instances.

In a monolithic application, configuration can often be represented by a small set of environment variables:

```text
Application
    |
    +-- DATABASE_URL
    +-- REDIS_URL
    +-- LOG_LEVEL
    +-- FEATURE_FLAG
```

In a microservices architecture, configuration becomes significantly more complex:

```text
                    Configuration System
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
        Order Service  Payment Service  User Service
             |             |             |
             v             v             v
          Config       Config          Config
```

Each service may require:

- Database endpoints
- Cache configuration
- Kafka brokers
- External API endpoints
- Timeout values
- Retry policies
- Feature flags
- Rate limits
- Operational thresholds
- Environment-specific behavior
- Credentials and other secrets

Distributed configuration provides a controlled mechanism for supplying these values without embedding environment-specific infrastructure details directly into application code.

The key architectural distinction is between **configuration**, which controls application behavior, and **secrets**, which contain sensitive credentials or cryptographic material. They often use related infrastructure but should have different access controls, storage policies, rotation strategies, and audit requirements.

## Why Distributed Configuration Exists

Hardcoding configuration creates tight coupling between code and deployment infrastructure.

Bad:

```python
DATABASE_HOST = "10.20.4.15"
REDIS_HOST = "10.20.5.21"
PAYMENT_API = "https://payments.production.internal"
```

Changing environments then requires modifying application code.

A better approach is:

```text
Application Code
      |
      | reads configuration
      v
Configuration Source
      |
      +--> Development
      +--> Staging
      +--> Production
```

The same application artifact can then be deployed into multiple environments:

```text
                  Same Docker Image
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
        Development   Staging   Production
             |           |           |
           Config      Config      Config
```

This improves deployment consistency and supports immutable application artifacts.

## Configuration vs Secrets

Not every configuration value should be treated identically.

| Type | Example | Typical Storage |
|---|---|---|
| Static configuration | `LOG_LEVEL=INFO` | Environment/config file |
| Runtime configuration | `REQUEST_TIMEOUT=3` | Config service |
| Feature flag | `ENABLE_NEW_CHECKOUT=true` | Feature/config system |
| Credential | Database password | Secrets manager |
| API token | External API token | Secrets manager |
| Encryption key | Application key | KMS/secrets system |
| Certificate | TLS private key | Secrets/certificate manager |

A useful rule is:

> Configuration controls behavior; secrets grant access.

Secrets should never be committed to Git repositories or stored in ordinary configuration files without appropriate protection.

## Configuration Sources

Common configuration sources include:

- Environment variables
- Configuration files
- Kubernetes ConfigMaps
- Kubernetes Secrets
- AWS Systems Manager Parameter Store
- AWS Secrets Manager
- AWS AppConfig
- HashiCorp Vault
- Consul
- Cloud-native service configuration systems

The appropriate choice depends on:

- Deployment platform
- Security requirements
- Update frequency
- Configuration size
- Audit requirements
- Availability requirements
- Operational complexity

## Static Configuration

Some configuration rarely changes.

Examples:

```text
SERVICE_NAME=payment-service
LOG_LEVEL=INFO
HTTP_PORT=8000
```

These values can often be injected during deployment.

For Docker:

```yaml
services:
  payment-service:
    image: company/payment-service:2026.08
    environment:
      SERVICE_NAME: payment-service
      LOG_LEVEL: INFO
      HTTP_PORT: "8000"
```

Static configuration is simple and generally preferable when dynamic updates are not required.

## Environment Variables

Environment variables are one of the most common configuration mechanisms.

Example:

```bash
DATABASE_URL=postgresql://app_user:password@postgres:5432/orders
REDIS_URL=redis://redis:6379/0
LOG_LEVEL=INFO
PAYMENT_TIMEOUT_SECONDS=3
```

Python:

```python
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
PAYMENT_TIMEOUT_SECONDS = float(
    os.getenv("PAYMENT_TIMEOUT_SECONDS", "3")
)
```

For production systems, configuration should generally be parsed and validated at startup rather than repeatedly accessed throughout the application.

## Configuration Validation

Invalid configuration should cause the service to fail fast.

For FastAPI/Python applications, a typed settings layer is preferable to manually reading environment variables throughout the codebase.

For example:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    database_url: str
    redis_url: str
    payment_timeout_seconds: float = 3.0
    log_level: str = "INFO"


settings = Settings()
```

A production deployment with a missing required variable should fail during startup instead of failing later when a request reaches the affected code path.

## Fail-Fast Configuration

Consider:

```text
Application starts
      |
      v
Validate configuration
      |
   +--+--+
   |     |
 Valid  Invalid
   |     |
   v     v
Serve  Stop
traffic startup
```

Failing early is usually better than:

```text
Application starts
      |
      v
Traffic received
      |
      v
Database connection attempted
      |
      v
Missing configuration
      |
      v
500 error
```

Configuration errors are deployment errors and should normally be detected during startup.

## Centralized Configuration

As the number of services increases, configuration may become difficult to manage independently.

For example:

```text
Git Repository
    |
    +-- order-service
    +-- payment-service
    +-- inventory-service
    +-- notification-service
```

Each service may have:

```text
.env
config.yaml
deployment.yaml
```

This can lead to configuration drift.

Centralized configuration provides a shared source of truth:

```mermaid
flowchart LR
    Git[Configuration Repository]
    Store[Configuration Store]

    Order[Order Service]
    Payment[Payment Service]
    Inventory[Inventory Service]

    Git --> Store
    Store --> Order
    Store --> Payment
    Store --> Inventory
```

Centralization improves consistency but introduces another critical dependency.

## Configuration Repository

A configuration repository can store non-sensitive environment configuration.

Example:

```text
config/
├── development/
│   ├── order.yaml
│   └── payment.yaml
├── staging/
│   ├── order.yaml
│   └── payment.yaml
└── production/
    ├── order.yaml
    └── payment.yaml
```

Example:

```yaml
payment:
  timeout_seconds: 3
  max_connections: 100
  retry:
    max_attempts: 2
    backoff_seconds: 0.2
```

Secrets should not be stored in plaintext in the same repository.

## Configuration Versioning

Configuration should be versioned when changes affect application behavior.

For example:

```text
Version 41
    PAYMENT_TIMEOUT=3

Version 42
    PAYMENT_TIMEOUT=5
```

Versioning provides:

- Auditability
- Rollback
- Change history
- Reproducibility
- Safer deployments

A production incident should allow engineers to answer:

> Which configuration was active when the incident occurred?

## Configuration Rollbacks

Configuration changes can cause production incidents even when application code is unchanged.

Example:

```text
Deployment
    |
    v
Configuration changed
    |
    v
Timeout increased
    |
    v
Connection pool saturation
    |
    v
Latency increases
```

A configuration system should therefore support rollback or an equivalent recovery mechanism.

## Push vs Pull Configuration

Distributed configuration can be delivered using two broad approaches.

### Pull Model

The application periodically retrieves configuration.

```text
Application
    |
    | GET configuration
    v
Configuration Store
```

Advantages:

- Simple application lifecycle
- Service controls refresh timing
- No persistent connection required

Limitations:

- Configuration changes may not be immediate
- Applications must handle refresh failures
- Polling creates additional load

### Push Model

The configuration system notifies applications about changes.

```text
Configuration Store
        |
        | update event
        v
Application
```

Advantages:

- Faster propagation
- Lower polling overhead

Limitations:

- More operational complexity
- Requires reliable notification delivery
- Applications must handle missed updates

Neither model is universally superior.

## Startup-Time Configuration

For many backend services, configuration only needs to be loaded at startup.

```text
Container starts
      |
      v
Load configuration
      |
      v
Validate configuration
      |
      v
Initialize dependencies
      |
      v
Start server
```

This is often the safest default.

For example:

```text
DATABASE_URL
REDIS_URL
KAFKA_BROKERS
```

can be loaded once when the process starts.

A configuration change then requires a new deployment or restart.

This makes application state easier to reason about.

## Dynamic Configuration

Some settings benefit from runtime updates.

Examples:

- Feature flags
- Rate limits
- Sampling percentages
- Operational thresholds
- Circuit breaker settings
- Rollout percentages

For example:

```text
FEATURE_NEW_CHECKOUT=10%
```

can allow a gradual rollout without redeploying every service.

Dynamic configuration should be introduced selectively.

Not every setting should be dynamically reloadable.

## Dynamic Configuration Risks

Runtime configuration introduces consistency problems.

Suppose three instances receive an update at different times:

```text
Instance A -> version 12
Instance B -> version 12
Instance C -> version 11
```

The application may temporarily behave differently depending on which instance handles the request.

This can cause difficult-to-debug behavior.

Therefore, dynamic configuration should define:

- Propagation guarantees
- Maximum staleness
- Version semantics
- Rollback behavior
- Refresh failure behavior

## Configuration Propagation

A configuration update may propagate through several layers:

```mermaid
sequenceDiagram
    participant Admin as Operator
    participant Store as Config Store
    participant A as Service Instance A
    participant B as Service Instance B
    participant C as Service Instance C

    Admin->>Store: Update configuration
    A->>Store: Refresh
    Store-->>A: Version 42
    B->>Store: Refresh
    Store-->>B: Version 42
    C->>Store: Refresh
    Store-->>C: Version 42
```

Propagation is rarely instantaneous in distributed systems.

Production systems should define an acceptable configuration propagation window.

## Configuration Consistency

Configuration consistency is particularly important for settings that influence correctness.

Examples:

```text
Database schema version
Authentication policy
Payment behavior
Feature compatibility
Message format
```

A configuration change that affects multiple services may require coordinated rollout.

For example:

```text
Producer v2
    |
    | new message format
    v
Kafka
    |
    v
Consumer v1
```

Changing configuration without considering compatibility can break downstream consumers.

Configuration is therefore part of system compatibility, not merely deployment metadata.

## Feature Flags

Feature flags are a common form of distributed configuration.

Example:

```text
new_checkout_enabled = false
```

The service can then evaluate:

```python
if feature_flags.new_checkout_enabled:
    return checkout_v2()
return checkout_v1()
```

Feature flags can support:

- Canary releases
- Gradual rollouts
- Emergency disablement
- A/B testing
- Operational controls

However, feature flags create state and should be treated as production configuration with ownership and lifecycle management.

## Feature Flag Lifecycle

A feature flag should not remain indefinitely.

A typical lifecycle is:

```text
Created
   |
   v
Disabled
   |
   v
Canary
   |
   v
Gradual Rollout
   |
   v
Fully Enabled
   |
   v
Removed
```

Permanent feature flags increase complexity and create conditional code that must eventually be removed.

## Configuration and Kubernetes

Kubernetes supports configuration through ConfigMaps and Secrets.

Example ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: payment-config
data:
  LOG_LEVEL: "INFO"
  PAYMENT_TIMEOUT_SECONDS: "3"
```

Deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: payment
  template:
    metadata:
      labels:
        app: payment
    spec:
      containers:
        - name: payment
          image: company/payment-service:2026.08
          envFrom:
            - configMapRef:
                name: payment-config
```

This separates configuration from the container image.

## Kubernetes ConfigMap Limitations

ConfigMaps are useful for ordinary configuration but should not be treated as a full configuration-management platform.

Important considerations include:

- Configuration size limits
- Update propagation behavior
- Application reload behavior
- Namespace isolation
- Access permissions
- Configuration versioning

If the application only reads configuration at startup, updating a ConfigMap does not automatically mean the running process will change its behavior.

## Kubernetes Secrets

Sensitive values should use Kubernetes Secrets or, preferably in many production environments, integration with an external secrets manager.

Example:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: payment-secrets
type: Opaque
stringData:
  DATABASE_PASSWORD: "replace-me"
```

The example value is intentionally illustrative. Real credentials should not be committed to source control.

Kubernetes Secrets provide controlled secret objects, but the security of the overall system also depends on:

- API server access controls
- RBAC
- Encryption at rest
- Node security
- Workload permissions
- Secret exposure through logs or process inspection

## AWS Parameter Store

AWS Systems Manager Parameter Store can provide centrally managed parameters.

Typical hierarchy:

```text
/app/payment/production/database-url
/app/payment/production/redis-url
/app/payment/production/timeout
```

Applications can retrieve parameters using AWS APIs.

Conceptually:

```text
ECS / EC2 / EKS
       |
       v
SSM Parameter Store
       |
       v
Configuration
```

Parameter Store is useful for centralized configuration and can also support secure parameters.

## AWS Secrets Manager

Secrets Manager is designed specifically for secrets and supports capabilities such as secret rotation.

Typical examples include:

- Database credentials
- API credentials
- OAuth client secrets
- Signing secrets

A useful separation is:

```text
Parameter Store
    |
    +--> Ordinary configuration

Secrets Manager
    |
    +--> Sensitive credentials
```

The exact choice depends on the required security, rotation, integration, and operational characteristics.

## AWS AppConfig

AWS AppConfig is designed for application configuration and controlled runtime configuration changes.

It can be useful for:

- Feature flags
- Runtime settings
- Gradual configuration deployment
- Validation
- Controlled rollout

A mature configuration architecture may therefore look like:

```text
Application
    |
    +--> AppConfig      -> dynamic configuration
    |
    +--> Parameter Store -> static parameters
    |
    +--> Secrets Manager -> secrets
```

This separation makes configuration responsibilities clearer.

## Configuration Precedence

Multiple configuration sources may exist.

For example:

```text
Defaults
   |
   v
Config File
   |
   v
Environment Variables
   |
   v
Runtime Configuration
```

A service should define explicit precedence rules.

For example:

```text
Default < Config File < Environment < Runtime Override
```

Without a documented precedence model, engineers may not know which value is actually active.

## Configuration Schema

Configuration should have a schema.

Example:

```yaml
payment:
  timeout_seconds: 3
  max_connections: 100
  retries: 2
```

A schema can validate:

- Required fields
- Data types
- Allowed values
- Minimum/maximum values
- Nested structure
- Compatibility

For example:

```python
from pydantic import BaseModel, Field


class PaymentSettings(BaseModel):
    timeout_seconds: float = Field(gt=0, le=30)
    max_connections: int = Field(gt=0, le=1000)
    retries: int = Field(ge=0, le=5)
```

Configuration validation prevents invalid operational values from silently reaching production.

## Immutable vs Mutable Configuration

| Type | Examples | Recommended Approach |
|---|---|---|
| Immutable | Port, service identity | Deployment configuration |
| Environment-specific | Database endpoint | Environment/config store |
| Operational | Log level, timeout | Config system |
| Dynamic | Feature flags | Runtime configuration |
| Sensitive | Passwords, tokens | Secrets manager |

The more frequently configuration changes, the more carefully its consistency and failure behavior must be designed.

## Configuration and CI/CD

Configuration management should integrate with CI/CD.

A deployment pipeline can validate:

```text
Git Commit
    |
    v
Configuration Validation
    |
    v
Security Checks
    |
    v
Integration Tests
    |
    v
Deploy
    |
    v
Health Checks
```

Configuration should be tested before production rollout.

Useful checks include:

- Schema validation
- Required-variable validation
- Environment validation
- Secret-reference validation
- Policy validation
- Compatibility validation

## Configuration Drift

Configuration drift occurs when instances or environments no longer use the expected configuration.

Example:

```text
Production
    |
    +--> Instance A: timeout=3
    +--> Instance B: timeout=3
    +--> Instance C: timeout=10
```

This creates non-deterministic behavior.

Prevent drift with:

- Declarative configuration
- Versioned configuration
- Automated deployment
- Configuration reconciliation
- Infrastructure as Code
- Centralized observability

## Configuration and Infrastructure as Code

Infrastructure configuration and application configuration overlap but are not identical.

Tools such as Terraform can define infrastructure:

```text
VPC
RDS
EKS
Load Balancer
IAM
```

Application configuration may define:

```text
Timeout
Feature flag
Log level
Kafka consumer settings
```

A mature platform separates these concerns while maintaining automated delivery.

## Configuration Security

Configuration systems must follow least privilege.

For example:

```text
Order Service
    |
    +--> Can read order configuration
    +--> Can read payment endpoint
    X--> Cannot read database root credentials
    X--> Cannot read unrelated service secrets
```

Security controls should include:

- IAM/RBAC
- Encryption at rest
- Encryption in transit
- Audit logs
- Least-privilege access
- Secret rotation
- Access reviews
- Environment isolation

Never expose sensitive configuration through:

- Application logs
- Error messages
- Metrics labels
- Traces
- Debug endpoints
- `/config` HTTP endpoints

## Configuration and Logging

Avoid:

```python
logger.info("Loaded configuration: %s", settings)
```

because the object may contain secrets.

Prefer:

```python
logger.info(
    "Configuration loaded",
    extra={
        "service": settings.service_name,
        "log_level": settings.log_level,
    },
)
```

Only explicitly safe fields should be logged.

## High Availability

A centralized configuration system can become a critical dependency.

If:

```text
Application
    |
    v
Config Store
```

is required during every request, configuration-store downtime can become application downtime.

Prefer loading critical configuration at startup and caching it locally when possible:

```text
Startup
   |
   v
Config Store
   |
   v
Local Application Memory
   |
   v
Requests
```

For dynamic configuration, define behavior when refresh fails.

For example:

```text
Refresh failed
    |
    v
Use last known good configuration
    |
    v
Emit alert
```

This is often safer than immediately disabling the application.

## Disaster Recovery

Configuration is part of application state and should be included in disaster recovery planning.

Consider:

- Configuration backups
- Version history
- Cross-region replication
- Recovery procedures
- Access to secrets after regional failure
- IAM recovery
- Dependency ordering
- Configuration rollback

A disaster recovery plan that restores databases but cannot restore configuration is incomplete.

## Monitoring

Monitor both configuration infrastructure and configuration behavior.

Useful metrics include:

- Configuration fetch latency
- Configuration fetch failures
- Refresh frequency
- Configuration version
- Configuration age
- Propagation latency
- Invalid configuration attempts
- Secret access failures
- Configuration rollback events

For dynamic configuration, expose a safe version identifier:

```text
config_version=42
```

Do not expose the configuration contents themselves.

## Configuration Change Auditing

Every production configuration change should ideally have:

```text
Who
What
When
Why
Previous version
New version
```

For example:

```text
Operator: deployment-system
Change: PAYMENT_TIMEOUT
Old: 3
New: 5
Reason: downstream latency increase
Timestamp: 2026-08-23T10:30:00Z
```

Auditability becomes especially important during incident investigation.

## Performance Considerations

Configuration retrieval should not become a hot-path dependency.

Avoid:

```text
HTTP Request
    |
    v
Config Store
    |
    v
Database
```

for every application request.

Prefer:

```text
Application Startup
       |
       v
Config Store
       |
       v
Local Memory
       |
       v
HTTP Requests
```

For dynamic settings:

```text
Config Store
       |
       | periodic refresh
       v
Local Cache
       |
       v
Request Processing
```

The refresh interval should be chosen based on business requirements rather than arbitrary low polling intervals.

## Operational Failure Scenarios

| Failure | Recommended Behavior |
|---|---|
| Config store unavailable at startup | Fail startup for mandatory configuration |
| Config refresh fails | Use last known good configuration where safe |
| Invalid configuration | Reject update |
| Secret unavailable | Fail startup or disable affected capability |
| Configuration version mismatch | Prevent unsafe rollout |
| Partial propagation | Monitor and reconcile |
| Configuration rollback | Restore previous known-good version |
| Expired secret | Rotate and alert before expiration |

The correct behavior depends on whether the configuration is required for correctness or merely operational optimization.

## Common Mistakes

### Hardcoding Environment-Specific Values

Bad:

```python
DATABASE_HOST = "prod-db.internal"
```

This couples the application to a specific environment.

### Storing Secrets in Git

Bad:

```yaml
database_password: "SuperSecretPassword"
```

Use a secrets manager instead.

### Treating All Configuration as Dynamic

Dynamic configuration introduces consistency and operational complexity.

Only make settings dynamic when the business or operational requirement justifies it.

### Fetching Configuration on Every Request

This adds latency and creates unnecessary dependency on the configuration service.

Cache configuration appropriately.

### No Configuration Validation

Invalid values should be rejected before they reach production.

### No Configuration Versioning

Without versions, rollback and incident investigation become difficult.

### Logging Entire Configuration Objects

This can leak credentials and tokens.

Log only explicitly safe configuration metadata.

### Ignoring Configuration Drift

Different instances using different configuration can produce inconsistent behavior.

### No Rollback Mechanism

A configuration change can cause an outage even when the application binary is unchanged.

### No Ownership

Every production configuration value should have an identifiable owner and documented purpose.

## Production Best Practices

- Treat configuration as a first-class production artifact.
- Separate configuration from application code.
- Separate ordinary configuration from secrets.
- Validate configuration at startup.
- Use typed configuration schemas.
- Version important configuration changes.
- Support rollback for production changes.
- Use centralized configuration when the operational complexity justifies it.
- Prefer platform-native solutions such as Kubernetes ConfigMaps, AWS Parameter Store, AWS AppConfig, and AWS Secrets Manager where appropriate.
- Keep critical configuration cached locally after startup.
- Avoid configuration-store calls in request hot paths.
- Define explicit configuration precedence.
- Monitor configuration propagation and refresh failures.
- Protect configuration with least-privilege access controls.
- Never log secrets.
- Include configuration in disaster recovery planning.
- Test configuration changes through CI/CD.
- Detect and remediate configuration drift.
- Assign ownership to important configuration values.
- Remove obsolete feature flags and stale configuration.

## Configuration Strategy by Requirement

| Requirement | Recommended Approach |
|---|---|
| Simple local development | `.env` / environment variables |
| Docker deployment | Environment variables / mounted configuration |
| Kubernetes static configuration | ConfigMap |
| Kubernetes secrets | Secret or external secrets integration |
| AWS application parameters | Parameter Store |
| AWS secrets | Secrets Manager |
| Runtime feature flags | AppConfig or dedicated feature-flag platform |
| Large multi-service platform | Centralized configuration service |
| Highly sensitive enterprise secrets | Dedicated secrets manager such as Vault or cloud-native secret management |
| Infrastructure configuration | Infrastructure as Code |
| Application behavior | Application configuration system |

The goal is not to centralize everything. The goal is to make configuration **predictable, secure, versioned, observable, and operationally manageable**.

## Interview Traps

### "Environment Variables Are Distributed Configuration"

Environment variables are a configuration delivery mechanism.

They do not automatically provide:

- Central management
- Versioning
- Dynamic updates
- Audit history
- Configuration propagation

### "ConfigMaps Are Secret Stores"

Kubernetes ConfigMaps are intended for non-sensitive configuration.

Secrets require stronger protection and access controls.

### "Dynamic Configuration Is Always Better"

Dynamic updates reduce deployment friction but increase consistency and operational complexity.

Use them selectively.

### "Configuration Changes Cannot Break Production"

They can.

Timeouts, connection limits, feature flags, routing rules, and retry policies can all cause production failures.

### "Configuration Does Not Need Disaster Recovery"

Critical configuration is part of the system's operational state.

A production recovery plan should account for restoring both infrastructure and configuration.

### "Centralized Configuration Removes All Configuration Problems"

Centralization reduces duplication and drift but introduces a shared dependency.

The configuration system itself must be highly available and observable.

## Key Takeaways

- **Distributed configuration separates application behavior from environment-specific infrastructure and allows the same application artifact to run consistently across environments.**
- **Separate ordinary configuration from secrets, using typed validation, least-privilege access, encryption, auditing, and dedicated secret-management systems for sensitive values.**
- **Load mandatory configuration at startup and cache it locally; avoid making a centralized configuration service a synchronous dependency on every request.**
- **Dynamic configuration and feature flags require explicit versioning, propagation semantics, validation, observability, and rollback because distributed instances can temporarily observe different values.**
- **Treat configuration as a production artifact: version it, test it through CI/CD, monitor drift and propagation, define ownership, and include critical configuration in disaster recovery planning.**