# 08- Environment Variable Issues

## Overview

Environment variables are a common source of Elastic Beanstalk deployment and runtime failures. An application can deploy successfully while failing immediately at startup because a required variable is missing, incorrectly named, incorrectly formatted, or configured for the wrong environment.

For backend applications such as Django and FastAPI, environment variables commonly control:

- Database connection details
- Secret keys
- Debug mode
- Allowed hosts
- External API credentials
- Redis endpoints
- Celery configuration
- Kafka brokers
- AWS resource identifiers
- Application ports
- Environment-specific behavior

The important distinction is between **deployment configuration** and **application configuration**. Elastic Beanstalk can inject environment properties into the EC2 runtime, but the application must still read and interpret them correctly.

A typical flow is:

```text
Elastic Beanstalk Environment
        │
        │ Environment Properties
        ▼
EC2 Instance
        │
        │ Process Environment
        ▼
Gunicorn / Uvicorn
        │
        ▼
Django / FastAPI
        │
        ├── Database
        ├── Redis
        ├── External APIs
        └── AWS Services
```

A failure at any point can result in startup failures, health-check failures, incorrect application behavior, or security incidents.

## Environment Variables in Elastic Beanstalk

Elastic Beanstalk environment properties are configuration values made available to processes running inside the environment.

For example:

```text
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=false
DATABASE_HOST=database.example.internal
DATABASE_PORT=5432
REDIS_URL=redis://redis.internal:6379/0
```

Inside a Python application:

```python
import os

debug = os.getenv("DEBUG", "false").lower() == "true"
database_host = os.environ["DATABASE_HOST"]
```

The application receives these values through the operating system environment.

## Why Environment Variables Are Used

Environment variables separate application code from environment-specific configuration.

The same application artifact can run in:

```text
Development
    ↓
Staging
    ↓
Production
```

while receiving different configuration.

For example:

| Variable | Development | Production |
|---|---|---|
| `DEBUG` | `true` | `false` |
| `DATABASE_HOST` | Local PostgreSQL | RDS endpoint |
| `REDIS_URL` | Local Redis | ElastiCache |
| `LOG_LEVEL` | `DEBUG` | `INFO` |
| `DJANGO_SETTINGS_MODULE` | Development settings | Production settings |

This follows the principle:

> Build the application once and inject environment-specific configuration at runtime.

## Configuration Versus Secrets

Not every environment variable is a secret.

### Configuration

Examples:

```text
APP_ENV=production
LOG_LEVEL=INFO
DATABASE_PORT=5432
```

These usually do not require secret storage.

### Secrets

Examples:

```text
DATABASE_PASSWORD
DJANGO_SECRET_KEY
JWT_SIGNING_KEY
STRIPE_SECRET_KEY
```

These require stronger protection.

Do not treat Elastic Beanstalk environment properties as a replacement for a dedicated secrets-management strategy for sensitive credentials.

For production systems, consider:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- IAM-based access where supported
- Automatic secret rotation where appropriate

## Setting Environment Properties With the CLI

Elastic Beanstalk CLI supports environment configuration.

A common workflow is:

```bash
eb setenv APP_ENV=production DEBUG=false
```

Multiple values can be supplied:

```bash
eb setenv \
  APP_ENV=production \
  DEBUG=false \
  LOG_LEVEL=INFO
```

After changing environment properties, Elastic Beanstalk may need to update the environment and restart application processes.

Verify the environment:

```bash
eb status
```

and inspect environment configuration:

```bash
eb printenv
```

Avoid treating command output containing secrets as harmless terminal output. Shell history, CI logs, terminal recording, and shared sessions can expose credentials.

## Environment-Specific Configuration

Elastic Beanstalk environments should not accidentally share production credentials.

A practical setup is:

```text
my-app
├── development
│   ├── local database
│   └── local Redis
│
├── staging
│   ├── staging database
│   └── staging Redis
│
└── production
    ├── production database
    └── production Redis
```

Each environment should have its own configuration boundary.

For example:

```bash
eb use my-app-staging
eb setenv APP_ENV=staging
```

and:

```bash
eb use my-app-production
eb setenv APP_ENV=production
```

Always verify the active environment before changing configuration.

```bash
eb status
```

## The Most Dangerous Environment Variable Mistake

One of the most common operational errors is modifying the wrong Elastic Beanstalk environment.

For example:

```text
Developer intends:
production

Active EB environment:
staging
```

The command succeeds technically but changes the wrong environment.

Before modifying configuration:

```bash
eb status
```

Then verify the environment name and region.

A safer operational workflow is:

```text
Identify environment
        ↓
Verify AWS region
        ↓
Inspect current configuration
        ↓
Change one variable
        ↓
Verify deployment/update
        ↓
Validate application health
```

## Missing Environment Variables

Applications frequently fail because a required variable is absent.

For example:

```python
database_password = os.environ["DATABASE_PASSWORD"]
```

If the variable is missing:

```text
KeyError: 'DATABASE_PASSWORD'
```

This can prevent the application from starting.

A safer configuration strategy is to validate required configuration explicitly during startup.

Example:

```python
import os


REQUIRED_VARIABLES = (
    "DATABASE_HOST",
    "DATABASE_NAME",
    "DATABASE_USER",
    "DATABASE_PASSWORD",
)


def validate_environment() -> None:
    missing = [
        name
        for name in REQUIRED_VARIABLES
        if not os.getenv(name)
    ]

    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
```

Failing fast is preferable to allowing the application to start with invalid configuration and fail later during a request.

## `os.getenv()` Versus `os.environ[]`

Both approaches are valid but have different semantics.

### `os.getenv()`

```python
value = os.getenv("DATABASE_PORT")
```

Returns `None` if the variable does not exist.

With a default:

```python
value = os.getenv("LOG_LEVEL", "INFO")
```

### `os.environ[]`

```python
value = os.environ["DATABASE_PASSWORD"]
```

Raises `KeyError` if the variable is missing.

For mandatory configuration, explicit failure is often preferable:

```python
DATABASE_HOST = os.environ["DATABASE_HOST"]
```

For optional configuration:

```python
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
```

The important engineering decision is whether the configuration is genuinely optional.

## Empty Values Versus Missing Values

These are not always equivalent:

```text
DATABASE_PASSWORD
```

versus:

```text
DATABASE_PASSWORD=
```

A variable can exist while containing an empty string.

For example:

```python
value = os.getenv("DATABASE_PASSWORD")
```

may return:

```text
""
```

rather than:

```text
None
```

Validation should therefore consider both cases when a value is mandatory.

```python
value = os.getenv("DATABASE_PASSWORD")

if not value:
    raise RuntimeError("DATABASE_PASSWORD must be configured")
```

## Boolean Environment Variables

Environment variables are strings.

This is a common mistake:

```python
DEBUG = bool(os.getenv("DEBUG"))
```

If:

```text
DEBUG=false
```

then:

```python
bool("false")
```

is still:

```text
True
```

Use explicit parsing:

```python
DEBUG = os.getenv("DEBUG", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
```

For production systems, centralized configuration parsing is preferable to repeating this logic throughout the application.

## Integer Environment Variables

Environment variables are strings, so numeric configuration must be parsed.

Incorrect:

```python
PORT = os.getenv("PORT")
```

Correct:

```python
PORT = int(os.getenv("PORT", "8000"))
```

The same applies to:

- Timeouts
- Worker counts
- Connection pool sizes
- Retry counts
- Kafka ports
- Database ports

Example:

```python
DATABASE_PORT = int(os.environ["DATABASE_PORT"])
```

## URL Environment Variables

Connection strings should be validated carefully.

Example:

```text
DATABASE_URL=postgresql://app_user:password@db.internal:5432/app
```

Potential problems include:

- Missing scheme
- Incorrect hostname
- Incorrect port
- URL encoding problems
- Special characters in passwords
- Incorrect database name

A password containing characters such as:

```text
@
:
/
#
```

may require URL encoding when embedded in a connection URL.

Prefer a configuration library or structured database configuration when complex connection strings become difficult to manage safely.

## Django Configuration

A production Django application commonly reads configuration from environment variables.

Example:

```python
import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]
```

Example Elastic Beanstalk configuration:

```text
DJANGO_SECRET_KEY=<secret>
DEBUG=false
ALLOWED_HOSTS=api.example.com
```

A missing `ALLOWED_HOSTS` configuration can cause Django requests to fail even though the application process itself is running.

## FastAPI Configuration

FastAPI applications can use environment-driven configuration through a settings layer.

For example:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "production"
    debug: bool = False
    database_url: str
    redis_url: str

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
```

This provides centralized validation and type conversion.

The important production principle is:

> Parse configuration once and expose validated settings to the application rather than repeatedly reading raw environment variables throughout the codebase.

## Configuration Loading Architecture

A clean backend architecture is:

```mermaid
flowchart LR
    EB[Elastic Beanstalk Environment] --> ENV[Process Environment]
    ENV --> SETTINGS[Configuration Layer]
    SETTINGS --> APP[Django / FastAPI]
    SETTINGS --> DB[(PostgreSQL)]
    SETTINGS --> REDIS[(Redis)]
    SETTINGS --> EXT[External APIs]
```

The configuration layer should be responsible for:

- Reading variables
- Validating required values
- Converting types
- Applying safe defaults
- Rejecting invalid values
- Exposing typed configuration

Business logic should not need to know how environment variables are stored.

## Environment Variable Precedence

Configuration can come from multiple locations:

```text
Application defaults
        ↓
Environment-specific configuration
        ↓
Elastic Beanstalk environment properties
        ↓
Runtime environment
```

The exact precedence depends on the application and deployment mechanism.

Do not assume that a local `.env` file automatically overrides Elastic Beanstalk environment properties.

The production runtime should be treated as the source of truth for production configuration.

## `.env` Files

Local development commonly uses:

```text
.env
```

For example:

```text
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=app
DATABASE_USER=app
DATABASE_PASSWORD=local-password
```

This can be convenient locally.

However, do not commit production secrets into:

```text
.env
```

or:

```text
.ebextensions/
```

just because the file is not directly visible in application code.

Use:

```text
.env.example
```

for documenting required variable names without exposing secrets.

Example:

```text
DATABASE_HOST=
DATABASE_PORT=5432
DATABASE_NAME=
DATABASE_USER=
DATABASE_PASSWORD=
```

## Configuration Files Versus Environment Properties

Elastic Beanstalk also supports configuration through platform configuration files.

For example:

```text
.ebextensions/
```

can be used for environment configuration and resource customization.

A useful separation is:

| Configuration | Recommended location |
|---|---|
| Non-sensitive deployment configuration | Source-controlled configuration |
| Environment-specific values | Elastic Beanstalk environment properties |
| Sensitive credentials | Secrets Manager / Parameter Store |
| Local development secrets | Local `.env` |
| Shared configuration | Appropriate AWS configuration service |

Do not place credentials in source-controlled configuration files.

## Secret Leakage

Environment variables are safer than hardcoding secrets, but they are not automatically secret.

Potential exposure points include:

- Application logs
- Debug pages
- Exception traces
- CI/CD logs
- Shell history
- Process inspection
- Diagnostic scripts
- Configuration dumps
- Support bundles

Avoid:

```python
logger.info("Environment: %s", dict(os.environ))
```

This can expose database passwords, tokens, and API keys.

Instead, log only safe metadata:

```python
logger.info(
    "Application configuration loaded",
    extra={
        "app_env": settings.app_env,
        "debug": settings.debug,
    },
)
```

Never log secret values.

## Secret Rotation

If a database password changes, updating the secret store alone may not be enough.

The complete flow may be:

```text
Secret updated
    ↓
Application configuration updated
    ↓
Environment refreshed
    ↓
Application processes restarted
    ↓
New credentials loaded
    ↓
Database connection validated
```

Applications should not assume that a process automatically re-reads environment variables after startup.

Environment variables are generally loaded into the process environment when the process starts.

## Configuration Changes and Restarts

A common misconception is:

> "I changed the environment variable, so the running Python process now sees the new value."

Usually, the process must be restarted to load the new environment.

Conceptually:

```text
EB Configuration
      ↓
Process starts
      ↓
Environment variables loaded
      ↓
Python imports settings
      ↓
Application runs
```

Changing the environment property does not magically mutate the already-loaded Python configuration object.

## Diagnosing Environment Variables on Elastic Beanstalk

First identify the environment:

```bash
eb status
```

Inspect configured environment properties:

```bash
eb printenv
```

Then connect to an instance if necessary:

```bash
eb ssh
```

Inspect a non-sensitive variable:

```bash
echo "$APP_ENV"
```

Inspect whether a sensitive variable exists without printing its value:

```bash
if [ -n "${DATABASE_PASSWORD:-}" ]; then
    echo "DATABASE_PASSWORD is configured"
else
    echo "DATABASE_PASSWORD is missing"
fi
```

This is safer than:

```bash
echo "$DATABASE_PASSWORD"
```

## Checking Variable Names

Environment variable names are case-sensitive on Linux.

These are different:

```text
DATABASE_HOST
database_host
Database_Host
```

A configuration mismatch can therefore produce:

```text
KeyError
```

or:

```text
None
```

depending on how the application reads the value.

Standardize naming conventions across environments.

A common convention is:

```text
UPPER_SNAKE_CASE
```

## Common Naming Mistakes

For example, Elastic Beanstalk contains:

```text
DATABASE_URL
```

while application code expects:

```python
os.environ["DB_URL"]
```

The application will fail despite the configuration appearing correct in the AWS console.

Another common issue is a typo:

```text
DJANGO_SECRET_KEY
```

versus:

```text
DJANGO_SECRETKEY
```

Centralized configuration validation helps detect these errors early.

## Environment Variable Dependency Matrix

For production systems, document required configuration without documenting secret values.

| Variable | Required | Type | Example | Secret |
|---|---:|---|---|---:|
| `APP_ENV` | Yes | String | `production` | No |
| `DEBUG` | Yes | Boolean | `false` | No |
| `DATABASE_HOST` | Yes | String | `db.internal` | No |
| `DATABASE_PORT` | Yes | Integer | `5432` | No |
| `DATABASE_NAME` | Yes | String | `app` | No |
| `DATABASE_USER` | Yes | String | `app_user` | Usually no |
| `DATABASE_PASSWORD` | Yes | String | `<secret>` | Yes |
| `REDIS_URL` | Yes | URL | `redis://...` | Depends |
| `DJANGO_SECRET_KEY` | Yes | String | `<secret>` | Yes |

This provides an operational contract without exposing credentials.

## Configuration Validation

A robust application should validate configuration before serving traffic.

Example:

```python
import os


def required(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")

    return value


DATABASE_HOST = required("DATABASE_HOST")
DATABASE_NAME = required("DATABASE_NAME")
DATABASE_USER = required("DATABASE_USER")
DATABASE_PASSWORD = required("DATABASE_PASSWORD")
```

For more complex applications, typed configuration libraries are preferable.

Validation should include:

- Required values
- Boolean parsing
- Integer ranges
- URL formats
- Allowed environment names
- Mutually dependent variables

## Invalid Configuration Examples

A configuration layer should reject cases such as:

```text
DEBUG=production
DATABASE_PORT=postgres
APP_ENV=unknown
DATABASE_URL=not-a-url
```

Instead of discovering these problems during a production request, fail during application initialization.

For example:

```python
if settings.app_env not in {"development", "staging", "production"}:
    raise RuntimeError("Invalid APP_ENV")
```

## Configuration and Health Checks

Health checks should generally distinguish between:

- Process health
- Application health
- Dependency health

For example:

```text
/health/live
```

may only verify that the process is running.

A readiness endpoint may verify critical dependencies:

```text
/health/ready
    ↓
Database reachable?
    ↓
Redis reachable?
    ↓
Configuration valid?
```

Be careful not to make every load-balancer health check depend on slow external services. A database outage should not necessarily cause the process-level liveness mechanism to behave incorrectly.

## Environment Variables and CI/CD

CI/CD systems commonly set or update Elastic Beanstalk configuration.

A secure deployment pipeline might look like:

```text
GitHub Actions
      ↓
Build application
      ↓
Run tests
      ↓
Deploy artifact
      ↓
Elastic Beanstalk
      ↓
Environment configuration
      ↓
Application startup
      ↓
Health checks
```

Do not put secret values directly into workflow files.

Use the CI/CD platform's secret-management mechanism and avoid printing them in logs.

## Configuration Drift

Configuration drift occurs when environments no longer match their intended configuration.

For example:

```text
Production:
DEBUG=false

Staging:
DEBUG=true

Expected:
Staging-specific difference

Actual:
Several undocumented differences
```

Drift becomes dangerous when nobody knows which environment properties are intentional.

Recommended practices include:

- Define configuration as code where practical.
- Document required variables.
- Keep environment-specific differences explicit.
- Review configuration changes.
- Avoid manual production changes when automation is available.
- Audit sensitive configuration changes.

## Configuration Change Workflow

A production configuration change should be deliberate.

```text
Identify variable
      ↓
Determine impact
      ↓
Verify target environment
      ↓
Check current value
      ↓
Change configuration
      ↓
Restart / deploy if required
      ↓
Verify application health
      ↓
Verify dependent services
      ↓
Record change
```

For high-risk variables such as database credentials or security-related settings, use a controlled deployment/change-management process.

## Common Environment Variable Failures

| Symptom | Likely cause |
|---|---|
| `KeyError` during startup | Required variable missing |
| Application gets `None` | Variable missing or incorrectly accessed |
| Boolean behaves incorrectly | String parsed incorrectly |
| Database authentication fails | Wrong credentials |
| Database connection fails | Wrong host, port, or credentials |
| Django rejects requests | `ALLOWED_HOSTS` misconfigured |
| Application uses wrong database | Wrong environment configuration |
| Redis connection fails | Incorrect `REDIS_URL` |
| New secret has no effect | Process was not restarted |
| Configuration works locally but not on EB | Runtime configuration differs |
| Production uses staging service | Incorrect environment variable |
| Application crashes after deployment | Invalid startup configuration |

## Troubleshooting Workflow

Use a structured approach.

### Verify the Target Environment

```bash
eb status
```

Confirm:

- Application name
- Environment name
- Region
- Health state

### Inspect Configuration

```bash
eb printenv
```

Compare the configured variable names against the application's expected names.

### Check Required Variables

On the instance:

```bash
eb ssh
```

Then:

```bash
for variable in APP_ENV DATABASE_HOST DATABASE_PORT DATABASE_NAME; do
    if [ -n "${!variable:-}" ]; then
        echo "$variable is configured"
    else
        echo "$variable is missing"
    fi
done
```

Do not print sensitive values.

### Validate Parsing

For example:

```bash
python -c 'import os; print(os.getenv("APP_ENV"))'
```

For sensitive variables, check existence rather than value.

### Inspect Application Logs

Look for:

```text
KeyError
ValueError
ValidationError
ImproperlyConfigured
OperationalError
ConnectionError
```

A configuration problem may manifest as a database or application error rather than an obvious environment-variable error.

### Verify the Dependent Service

If:

```text
DATABASE_HOST
DATABASE_PORT
DATABASE_USER
DATABASE_PASSWORD
```

are correct, verify that the application can actually reach the database.

Configuration correctness does not guarantee network connectivity.

## Production Security Practices

### Never Hardcode Secrets

Avoid:

```python
DATABASE_PASSWORD = "production-password"
```

Use runtime configuration or a secret-management system.

### Never Commit Secrets

Avoid committing:

```text
.env
production.env
credentials.json
```

Use `.gitignore` appropriately:

```gitignore
.env
.env.*
!.env.example
```

### Avoid Secret Printing

Never run:

```bash
eb printenv
```

and paste its output into tickets, chat rooms, Git commits, or incident documents without considering that sensitive values may be present.

Treat configuration output as potentially sensitive.

### Prefer Dedicated Secret Stores

For sensitive production values, use a dedicated secret-management service when appropriate.

The architecture becomes:

```text
Secrets Manager
       ↓
Application configuration
       ↓
Elastic Beanstalk
       ↓
Application process
```

This provides stronger separation between application deployment and credential storage.

## Common Mistakes

### Using `bool(os.getenv("DEBUG"))`

This makes:

```text
DEBUG=false
```

evaluate incorrectly because `"false"` is a non-empty string.

Parse booleans explicitly.

### Providing Unsafe Defaults

Avoid:

```python
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "password")
```

A production application should fail if a critical secret is absent rather than silently using an unsafe fallback.

### Mixing Environment Names

Do not allow:

```text
APP_ENV=production
DATABASE_HOST=staging-db
```

unless this is an intentional architecture.

Environment configuration should be internally consistent.

### Reading Variables Too Early

Configuration imported at module initialization is evaluated when the process starts.

If configuration changes later, the process may continue using the old value until restarted.

### Logging Entire Configuration

Never dump:

```python
print(dict(os.environ))
```

into production logs.

### Changing Production Manually Without Recording It

Manual changes can create configuration drift and make future deployments difficult to reproduce.

### Assuming Local `.env` Exists on Elastic Beanstalk

A local development `.env` file is not automatically equivalent to Elastic Beanstalk environment properties.

Explicitly configure production runtime values.

## Interview Traps

### Are Environment Variables Automatically Secure?

No.

They are configuration delivered through the process environment, not an inherently secure secret-management mechanism.

### Are Environment Variables Strings?

Yes.

Applications must explicitly parse booleans, integers, lists, URLs, and other structured values.

### Does Changing an Environment Variable Automatically Update a Running Python Process?

Do not assume so. Processes generally receive environment variables at process startup, so configuration changes commonly require application process replacement or restart.

### Should Every Environment Variable Have a Default?

No.

Critical production configuration should generally fail fast when missing.

### Should Database Passwords Be Stored Directly in Application Code?

No.

Use runtime configuration and preferably a dedicated secrets-management system for production credentials.

### Why Does an Application Work Locally but Fail on Elastic Beanstalk?

Common reasons include:

- Missing environment variables
- Different variable names
- Different values
- Different parsing behavior
- Missing secrets
- Different database endpoints
- Different Redis endpoints
- Different AWS configuration
- Different network access
- Different startup configuration

## Operational Checklist

Before declaring an environment-variable incident resolved:

- [ ] Correct Elastic Beanstalk environment confirmed
- [ ] Correct AWS region confirmed
- [ ] Required variable names verified
- [ ] Required values configured
- [ ] Sensitive values not exposed in logs
- [ ] Boolean values parsed correctly
- [ ] Numeric values parsed correctly
- [ ] URLs validated
- [ ] Production secrets stored appropriately
- [ ] Application configuration validated at startup
- [ ] Application process restarted if required
- [ ] Database connectivity verified
- [ ] Redis connectivity verified where applicable
- [ ] Application health verified
- [ ] Load-balancer health verified
- [ ] CI/CD configuration checked
- [ ] No unexpected configuration drift introduced
- [ ] Temporary configuration changes removed
- [ ] Configuration change documented

## Key Takeaways

- Elastic Beanstalk environment properties provide runtime configuration to application processes.
- Environment variables should separate application code from environment-specific configuration.
- Environment variables are strings and must be parsed into booleans, integers, URLs, and other types.
- Missing mandatory variables should cause explicit startup failure rather than silent fallback behavior.
- Avoid unsafe defaults for secrets and critical infrastructure configuration.
- `os.environ["NAME"]` is useful for mandatory configuration because it fails when the variable is absent.
- `os.getenv()` is appropriate for optional configuration when a safe default exists.
- Never use `bool(os.getenv("DEBUG"))` for boolean parsing because `"false"` is truthy in Python.
- Environment variable names are case-sensitive on Linux.
- Configuration names must exactly match what the application expects.
- A successful Elastic Beanstalk deployment does not guarantee that runtime configuration is correct.
- Changing environment properties generally requires application processes to restart before newly loaded configuration takes effect.
- Do not assume local `.env` files exist in Elastic Beanstalk.
- Do not commit production secrets to Git.
- Do not print entire environment dictionaries or secret values into logs.
- Environment properties are configuration, not a complete replacement for dedicated secret management.
- Use AWS Secrets Manager or Systems Manager Parameter Store where appropriate for sensitive production credentials.
- Centralize configuration parsing and validation instead of repeatedly reading raw environment variables throughout application code.
- Django and FastAPI applications should fail fast when required production configuration is invalid.
- Configuration correctness and network connectivity are separate concerns; a correct database hostname does not guarantee that the instance can reach the database.
- Always verify the target Elastic Beanstalk environment before changing configuration.
- Use `eb status`, `eb printenv`, instance-level checks, and application logs to diagnose configuration failures.
- Treat production configuration changes as operational changes that should be controlled, reviewed, and auditable.
- Configuration drift between Elastic Beanstalk environments can cause difficult-to-reproduce production failures.