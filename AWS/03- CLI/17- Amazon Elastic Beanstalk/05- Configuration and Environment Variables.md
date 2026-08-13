# 05- Configuration and Environment Variables

## Overview

Elastic Beanstalk configuration controls how an application environment is provisioned, deployed, and operated. Environment variables provide runtime configuration to the application without hard-coding environment-specific values into the source code.

For backend applications such as Django and FastAPI, this separation is fundamental:

```text
Application Code
      │
      ├── Application Behavior
      │
      └── Reads Configuration
                │
                ▼
        Environment Variables
                │
                ▼
       Elastic Beanstalk Environment
                │
        ┌───────┴────────┐
        ▼                ▼
   Runtime Config    AWS Services
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          PostgreSQL   Redis      S3
```

A production Elastic Beanstalk environment typically has configuration for:

- Application runtime settings
- Environment variables
- Instance and Auto Scaling settings
- Load balancer behavior
- Health checks
- Deployment policy
- Networking
- Logging
- Security
- Platform settings

The key engineering principle is to keep **application code immutable while environment configuration remains externally configurable**.

## Configuration Layers

Elastic Beanstalk configuration can originate from several places.

| Configuration mechanism | Primary purpose | Typical use |
|---|---|---|
| Environment properties | Runtime application configuration | `DATABASE_URL`, `LOG_LEVEL` |
| `.ebextensions` | Environment customization | Packages, options, files, commands |
| `.platform` | Platform hooks and deployment customization | Startup/deployment hooks |
| Elastic Beanstalk console | Interactive environment configuration | Operational changes |
| EB CLI | Developer/operator configuration | Environment management |
| AWS CLI / API | Automation | CI/CD and infrastructure tooling |
| Infrastructure as Code | Reproducible infrastructure | Terraform, CloudFormation, CDK |

A mature production setup should minimize undocumented console-only configuration.

## Environment Variables

Environment variables are key-value pairs exposed to the application process.

For example:

```text
APP_ENV=production
LOG_LEVEL=INFO
DATABASE_URL=...
REDIS_URL=...
```

The application reads them at runtime.

In Python:

```python
import os

app_env = os.environ["APP_ENV"]
log_level = os.getenv("LOG_LEVEL", "INFO")
```

For Django:

```python
import os

DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
```

For FastAPI:

```python
import os

DATABASE_URL = os.environ["DATABASE_URL"]
```

The application should not need to know whether the values came from Elastic Beanstalk, Docker, Kubernetes, or another runtime.

## Why Environment Variables Matter

Hard-coding environment-specific configuration creates deployment and security problems.

Avoid:

```python
DATABASE_HOST = "prod-db.example.internal"
```

Prefer:

```python
DATABASE_HOST = os.environ["DATABASE_HOST"]
```

This allows the same artifact to move through:

```text
Development
     ↓
Staging
     ↓
Production
```

without modifying the application source code.

This is especially important for CI/CD because the artifact should ideally be built once and promoted across environments.

## Setting Environment Variables with EB CLI

Use:

```bash
eb setenv APP_ENV=production
```

Multiple variables can be configured together:

```bash
eb setenv \
  APP_ENV=production \
  LOG_LEVEL=INFO \
  DJANGO_SETTINGS_MODULE=config.settings.production
```

Verify the configured values:

```bash
eb printenv
```

A safer operational workflow is:

```bash
eb status
eb setenv APP_ENV=production LOG_LEVEL=INFO
eb printenv
eb health
```

Be careful when using commands containing sensitive values because shell history, terminal recordings, CI logs, or process tooling may expose them.

## Setting Environment Variables with AWS CLI

Environment variables can also be managed through the Elastic Beanstalk API.

For example:

```bash
aws elasticbeanstalk update-environment \
  --environment-name orders-api-production \
  --option-settings \
    Namespace=aws:elasticbeanstalk:application:environment,OptionName=APP_ENV,Value=production \
    Namespace=aws:elasticbeanstalk:application:environment,OptionName=LOG_LEVEL,Value=INFO
```

This approach is useful for automation and CI/CD pipelines.

For repeated infrastructure configuration, Infrastructure as Code is generally preferable to embedding large configuration changes directly into shell scripts.

## Viewing Environment Variables

Use:

```bash
eb printenv
```

This is useful for verifying runtime configuration after deployment.

Example:

```bash
eb printenv
```

Be careful when sharing this output.

Environment variables may contain:

- Database credentials
- API tokens
- Internal endpoints
- Encryption configuration
- Third-party credentials

Never paste production environment output into public repositories, tickets, or unrestricted chat channels.

## Environment-Specific Configuration

A typical backend system might use:

| Variable | Development | Staging | Production |
|---|---|---|---|
| `APP_ENV` | `development` | `staging` | `production` |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `INFO` |
| `DATABASE_HOST` | Local | Staging DB | Production DB |
| `REDIS_URL` | Local Redis | Staging Redis | Production Redis |
| `DJANGO_DEBUG` | `true` | `false` | `false` |
| `SECRET_KEY` | Dev secret | Secret store | Secret store |

The application binary or source artifact should remain the same wherever practical.

## Configuration Precedence

When working with Elastic Beanstalk, configuration can be supplied through different mechanisms.

A useful conceptual model is:

```text
Application Defaults
        ↓
Environment Configuration
        ↓
Environment Variables
        ↓
Runtime Configuration
```

The exact precedence depends on the configuration mechanism and platform behavior.

Do not assume that a value defined in one configuration layer automatically overrides every other source. Validate the effective configuration in the target environment.

## `.ebextensions`

The `.ebextensions` directory can contain YAML or JSON configuration files.

Example:

```text
.ebextensions/
└── 01-application.config
```

A configuration file can define Elastic Beanstalk environment options.

Example:

```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    APP_ENV: production
    LOG_LEVEL: INFO
```

This is useful when configuration should travel with the application source.

However, sensitive credentials should not be committed to source control merely because `.ebextensions` supports environment properties.

## Configuration Files in `.ebextensions`

A more complete configuration might look like:

```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    APP_ENV: production
    LOG_LEVEL: INFO
    DJANGO_SETTINGS_MODULE: config.settings.production
```

The advantage is reproducibility:

```text
Git Repository
      ↓
.ebextensions
      ↓
Elastic Beanstalk Deployment
      ↓
Environment Configuration
```

The limitation is that configuration committed to the repository becomes part of the source-controlled deployment process.

Do not store secrets directly in committed configuration files.

## `.platform`

The `.platform` directory is commonly used for platform-specific customization and deployment hooks.

A project might contain:

```text
.platform/
├── hooks/
└── nginx/
```

The exact directory structure depends on the platform customization being performed.

Use `.platform` when the requirement involves platform-level behavior rather than simple application configuration.

Examples include:

- Deployment hooks
- Application server configuration
- Nginx customization
- Platform-specific scripts

Avoid using platform hooks for configuration that could be represented cleanly as environment properties.

## Configuration Through the Elastic Beanstalk Console

Environment properties can also be configured from the Elastic Beanstalk environment configuration interface.

This is useful for:

- Emergency operational changes
- Initial experimentation
- Inspecting current configuration
- One-off administrative operations

However, console-only changes can introduce configuration drift.

For production systems:

```text
Console Change
      ↓
Environment State Changes
      ↓
Repository Does Not Reflect Change
      ↓
Configuration Drift
```

Prefer version-controlled configuration for stable settings.

## Configuration Drift

Configuration drift occurs when the actual environment differs from the intended configuration stored in source control or Infrastructure as Code.

Example:

```text
Git:
LOG_LEVEL=INFO

Production Environment:
LOG_LEVEL=DEBUG
```

The application may behave differently from what engineers expect.

Prevent drift by:

- Version-controlling configuration
- Reviewing changes
- Automating deployments
- Limiting manual console changes
- Periodically auditing environment configuration

## Configuration and CI/CD

A CI/CD pipeline should separate:

```text
Application Artifact
        +
Environment Configuration
        +
Secrets
```

For example:

```mermaid
flowchart LR
    A[Git Commit] --> B[Build]
    B --> C[Test]
    C --> D[Application Artifact]

    E[Environment Configuration] --> F[Deployment]
    G[Secret Store] --> F

    D --> F
    F --> H[Elastic Beanstalk]
    H --> I[Application Runtime]
```

The deployment artifact should not contain environment-specific credentials.

## Configuration and Django

A production Django application commonly reads configuration from environment variables.

Example:

```python
import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

DATABASE_URL = os.environ["DATABASE_URL"]
```

For production:

```text
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<secret>
DJANGO_ALLOWED_HOSTS=api.example.com
DATABASE_URL=<database connection>
```

Do not use:

```python
DEBUG = True
```

as a production default.

A safer approach is to require production configuration explicitly.

## Configuration and FastAPI

FastAPI applications can use environment-driven configuration through Pydantic Settings.

Example:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
```

Elastic Beanstalk can provide the production values through environment properties.

This creates a clean separation:

```text
FastAPI Code
    ↓
Settings Layer
    ↓
Environment Variables
    ↓
Elastic Beanstalk
```

## Local `.env` Files vs Elastic Beanstalk

A common development workflow is:

```text
Local:
.env
  ↓
Python application

Production:
Elastic Beanstalk environment properties
  ↓
Python application
```

A local `.env` file should generally be excluded from Git:

```gitignore
.env
.env.*
!.env.example
```

An example configuration can be committed:

```text
.env.example
```

For example:

```dotenv
APP_ENV=development
LOG_LEVEL=INFO
DATABASE_URL=
REDIS_URL=
```

Do not commit actual production credentials.

## Secrets Management

Not all environment variables are equally sensitive.

| Configuration | Example | Sensitivity |
|---|---|---|
| Application environment | `APP_ENV=production` | Low |
| Log level | `LOG_LEVEL=INFO` | Low |
| Database host | `db.internal` | Medium |
| Database password | `********` | High |
| API token | `********` | High |
| Django secret key | `********` | High |
| Encryption key | `********` | Critical |

Sensitive values should be managed using services such as:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store

The preferred architecture is:

```text
Elastic Beanstalk
       │
       │ IAM permissions
       ▼
Secret Manager / Parameter Store
       │
       ▼
Application Runtime
```

The application should receive access to only the secrets it actually requires.

## IAM and Configuration Access

The Elastic Beanstalk instance profile or deployment identity should follow least privilege.

A common production separation is:

```text
Developer
   │
   ▼
CI/CD Identity
   │
   ├── Deploy Elastic Beanstalk
   │
   └── Manage required configuration

Elastic Beanstalk Instance Role
   │
   ├── Read required secrets
   ├── Write required logs
   └── Access required AWS services
```

Do not give the application runtime broad administrative permissions merely because it needs access to one secret or one S3 bucket.

## Configuration Validation

Configuration should be validated during application startup.

For example:

```python
import os


def required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")

    return value


DATABASE_URL = required_env("DATABASE_URL")
DJANGO_SECRET_KEY = required_env("DJANGO_SECRET_KEY")
```

Failing fast is generally preferable to allowing an application to start in an invalid configuration state.

For a production service:

```text
Missing Critical Configuration
          ↓
Startup Validation
          ↓
Process Fails
          ↓
Elastic Beanstalk Detects Failure
```

This is safer than allowing the application to run partially configured.

## Configuration Validation in CI/CD

CI/CD can validate non-secret configuration structure before deployment.

For example:

```bash
python manage.py check --deploy
```

For FastAPI, application startup or dedicated configuration tests can validate required settings.

The CI pipeline should detect:

- Missing required variables
- Invalid values
- Unsupported combinations
- Incorrect application configuration

Secrets themselves should not be printed merely to validate their presence.

## Sensitive Configuration in Logs

Avoid:

```python
print(os.environ)
```

or logging entire configuration objects.

Bad:

```text
DATABASE_URL=postgres://user:password@db.example.com/app
SECRET_KEY=...
API_TOKEN=...
```

Prefer:

```text
Application configuration loaded successfully
```

If diagnostic logging is required, redact sensitive fields.

## Environment Variable Naming

Use predictable names.

For example:

```text
APP_ENV
LOG_LEVEL
DATABASE_URL
REDIS_URL
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
AWS_REGION
```

Avoid inconsistent names such as:

```text
db
DATABASE
databaseHost
DB_HOST_VALUE
```

A consistent naming convention makes configuration easier to audit and automate.

## Avoid Configuration Explosion

Do not create hundreds of independent environment variables without a clear reason.

Poor configuration design:

```text
FEATURE_A_ENABLED
FEATURE_B_ENABLED
FEATURE_C_ENABLED
FEATURE_D_TIMEOUT
FEATURE_E_TIMEOUT
...
```

As configuration grows, consider whether some values belong in:

- Application configuration files
- A database-backed configuration service
- Parameter Store
- Secrets Manager
- Feature-flag infrastructure
- Infrastructure as Code

Environment variables are a runtime configuration mechanism, not a replacement for every configuration system.

## Configuration Changes and Deployments

Some configuration changes can affect application behavior immediately or cause environment processes to restart.

Treat configuration changes as production changes.

For example:

```bash
eb setenv LOG_LEVEL=DEBUG
```

can increase logging volume significantly.

This can affect:

- CloudWatch log volume
- Application performance
- Storage
- Monitoring costs

Production configuration changes should therefore be reviewed and monitored.

## Configuration and Scaling

Environment variables are replicated across Elastic Beanstalk instances as part of the environment configuration.

This is useful because all instances should receive consistent application configuration:

```text
Elastic Beanstalk Environment
          │
     ┌────┼────┐
     ▼    ▼    ▼
 Instance Instance Instance
    │        │        │
    └── Same Runtime Configuration ──┘
```

Do not store mutable application state inside environment variables or local instance files.

State should reside in appropriate external services such as:

- PostgreSQL
- Redis
- S3
- DynamoDB
- Kafka

depending on the workload.

## Configuration and Secrets Rotation

Secret rotation introduces an important operational consideration.

A database password may change:

```text
Old Secret
    ↓
Rotation
    ↓
New Secret
```

Applications must be able to obtain the new credential without requiring unsafe manual edits on individual instances.

A production design should consider:

- Secret rotation mechanism
- Application restart behavior
- Connection pool behavior
- Deployment timing
- Rollback behavior
- IAM permissions

Do not assume that changing a secret automatically updates every already-open database connection.

## Configuration Auditability

Production configuration should be auditable.

A useful model is:

```text
Git Commit
    ↓
Configuration Change
    ↓
CI/CD
    ↓
Elastic Beanstalk
    ↓
CloudTrail / AWS Logs
    ↓
Audit Trail
```

For sensitive or regulated environments, configuration changes should have:

- Identifiable actor
- Timestamp
- Change reason
- Review or approval
- Reproducible configuration

## Operational Troubleshooting

When an application behaves differently after a configuration change:

### Check Environment

```bash
eb status
```

### Inspect Environment Variables

```bash
eb printenv
```

### Check Events

```bash
eb events
```

### Check Health

```bash
eb health
```

### Retrieve Logs

```bash
eb logs
```

Then compare the effective production configuration against the expected configuration.

## Common Configuration Mistakes

### Hard-Coding Secrets

Bad:

```python
DATABASE_PASSWORD = "production-password"
```

Why it fails:

- Credentials enter source control
- Rotation becomes difficult
- Secrets can leak through repository history

Use a secret-management system instead.

### Committing `.env`

Bad:

```text
.env
```

containing:

```dotenv
DATABASE_PASSWORD=production-password
```

Use `.gitignore` and keep only an example file in the repository.

### Using `DEBUG=true` in Production

This can expose sensitive diagnostic information.

Production Django applications should explicitly configure:

```text
DJANGO_DEBUG=false
```

### Printing Environment Variables

This can leak credentials into logs.

Never dump the complete process environment for debugging.

### Relying Only on Console Configuration

Console changes can create configuration drift.

Prefer version-controlled configuration and automated deployment.

### Giving the Application Administrator Permissions

An application needing one secret does not need unrestricted AWS access.

Use least-privilege IAM policies.

### Treating Configuration as Static Forever

Configuration changes are operational changes. They can affect availability, cost, performance, and security.

Monitor important changes.

## Configuration Best Practices

| Practice | Recommendation |
|---|---|
| Source control | Keep non-sensitive configuration definitions versioned |
| Secrets | Use Secrets Manager or Parameter Store |
| Local development | Use `.env` or equivalent local configuration |
| Production | Use Elastic Beanstalk environment configuration |
| Validation | Fail fast on missing critical settings |
| Naming | Use consistent environment variable names |
| IAM | Apply least privilege |
| Logging | Never log sensitive configuration |
| Drift | Minimize undocumented console changes |
| CI/CD | Validate configuration before deployment |
| Rotation | Design for credential rotation |
| Rollback | Keep configuration changes reversible |

## Production Configuration Pattern

A practical backend deployment architecture is:

```mermaid
flowchart TD
    A[Git Repository] --> B[CI/CD Pipeline]
    B --> C[Application Artifact]
    B --> D[Configuration]
    E[AWS Secrets Manager / Parameter Store] --> F[Runtime Secret Access]

    C --> G[Elastic Beanstalk]
    D --> G
    G --> H[Application Instances]
    F --> H

    H --> I[Django / FastAPI]
    I --> J[PostgreSQL]
    I --> K[Redis]
    I --> L[S3 / AWS Services]
```

The application artifact contains code, while the environment supplies configuration and secrets.

## Production Checklist

Before deploying a new configuration:

```text
[ ] Configuration change reviewed
[ ] Correct AWS account verified
[ ] Correct Elastic Beanstalk environment verified
[ ] No secrets committed to Git
[ ] Required variables present
[ ] Sensitive values stored securely
[ ] IAM permissions follow least privilege
[ ] Application startup validation enabled
[ ] Configuration does not expose secrets in logs
[ ] Rollback procedure understood
[ ] Health monitoring enabled
```

After the change:

```text
[ ] eb status
[ ] eb printenv
[ ] eb health
[ ] eb events
[ ] Application health endpoint
[ ] Error rate
[ ] Latency
[ ] Resource utilization
```

## Interview Traps

### Why use environment variables instead of hard-coding configuration?

They separate application code from environment-specific runtime configuration and allow the same application artifact to be deployed across environments.

### Should secrets always be stored as environment variables?

Not necessarily. Environment variables are convenient for runtime configuration, but sensitive credentials should preferably be sourced from dedicated secret-management systems with appropriate IAM controls.

### What is the difference between configuration and secrets?

Configuration describes application behavior, while secrets are sensitive credentials or cryptographic material that require stronger access controls and lifecycle management.

### Why is configuration drift dangerous?

The running environment can behave differently from the configuration represented in source control, making deployments harder to reproduce and incidents harder to diagnose.

### Why should an application fail fast when a required variable is missing?

Starting with invalid configuration can produce partial failures, corrupted state, or misleading health signals. Failing during startup makes the problem explicit.

### Should environment variables contain application state?

No. Environment variables are configuration, not a persistence mechanism. Mutable state belongs in appropriate external storage systems.

### Why should environment variables not be printed in logs?

Because production configuration can contain credentials, tokens, connection strings, and other sensitive information.

### What is the role of `.ebextensions`?

It provides version-controlled Elastic Beanstalk configuration and customization. It should not be used as a reason to commit secrets into the repository.

## Key Takeaways

- Environment variables separate application code from environment-specific runtime configuration.
- Use the same application artifact across development, staging, and production wherever practical.
- `eb setenv` can configure Elastic Beanstalk environment properties, while `eb printenv` can verify them.
- `.ebextensions` and `.platform` provide additional mechanisms for version-controlled Elastic Beanstalk customization.
- Do not commit production credentials into `.ebextensions`, `.env`, or application source code.
- Use AWS Secrets Manager or Systems Manager Parameter Store for sensitive configuration where appropriate.
- Apply least-privilege IAM permissions to both deployment identities and application instance roles.
- Validate required configuration during application startup and fail fast when critical values are missing.
- Never log complete environment variables or sensitive configuration values.
- Minimize console-only configuration changes because they create configuration drift.
- Treat production configuration changes as operational changes that can affect availability, performance, security, and cost.
- Environment variables should contain configuration, not mutable application state.
- Design secret rotation and configuration changes with application restarts, connection pools, and rollback behavior in mind.
- Configuration management is part of the deployment architecture, not merely an application convenience.