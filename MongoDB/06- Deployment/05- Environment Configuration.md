# 05- Environment Configuration

## Overview

MongoDB environment configuration defines how an application connects to MongoDB across development, testing, staging, and production without coupling database credentials, topology, or operational settings to application source code.

A robust configuration strategy separates:

- Application code
- Environment-specific configuration
- Secrets
- MongoDB topology
- Driver behavior
- Deployment configuration

The same Python application should be deployable across environments with configuration changes rather than source-code changes.

```mermaid
flowchart LR
    Config[Environment Configuration]
    Secrets[Secret Store]
    App[Python / Django / FastAPI]
    Driver[MongoDB Driver]
    Mongo[MongoDB]

    Config --> App
    Secrets --> App
    App --> Driver
    Driver --> Mongo
```

The goal is not to expose every MongoDB option as an environment variable. Configuration should expose settings that are operationally meaningful while keeping application configuration understandable and maintainable.

## Environment Separation

Typical environments include:

| Environment | Purpose | MongoDB characteristics |
|---|---|---|
| Development | Local development | Local MongoDB or Docker |
| Test | Automated tests | Isolated database or ephemeral instance |
| Staging | Production-like validation | Dedicated cluster and credentials |
| Production | Live workload | Highly available, secured, monitored deployment |

Each environment should have independent:

- Database credentials
- Database names where appropriate
- Connection strings
- Network access
- Secret stores
- Backup policies
- Monitoring configuration
- Resource limits

Avoid using production MongoDB credentials in development or staging.

## Configuration vs Secrets

Not every environment variable is a secret.

| Configuration | Secret |
|---|---|
| Database name | Password |
| Pool size | Connection URI containing password |
| Timeout | TLS private key |
| Log level | API credential |
| Feature flag | Client certificate private key |
| Retry count | Encryption key |

A connection URI can become a secret when it contains credentials.

For example:

```text
mongodb://orders_api:password@mongo.internal:27017/orders
```

should be treated as sensitive.

A URI without embedded credentials may be less sensitive, but network topology can still be considered infrastructure information.

## Configuration Hierarchy

A production application commonly receives configuration through several layers:

```text
Source Code
    ↓
Configuration Defaults
    ↓
Environment Variables
    ↓
Secret Injection
    ↓
Container / Kubernetes Configuration
    ↓
Runtime
```

The application should define safe defaults where appropriate while requiring critical values explicitly.

For example:

```python
import os

database_name = os.environ["MONGODB_DATABASE"]
```

is preferable to silently falling back to:

```python
database_name = os.getenv("MONGODB_DATABASE", "production")
```

for a critical production setting.

A missing production database name should normally cause startup failure rather than silently connecting to an unintended database.

## Environment Variable Naming

Use predictable names.

A practical MongoDB configuration set is:

```text
MONGODB_URI
MONGODB_DATABASE

MONGODB_SERVER_SELECTION_TIMEOUT_MS
MONGODB_CONNECT_TIMEOUT_MS
MONGODB_SOCKET_TIMEOUT_MS
MONGODB_WAIT_QUEUE_TIMEOUT_MS

MONGODB_MAX_POOL_SIZE
MONGODB_MIN_POOL_SIZE
MONGODB_MAX_CONNECTING

MONGODB_RETRY_WRITES
MONGODB_RETRY_READS
```

Do not create dozens of environment variables for settings that are never expected to change between environments.

Configuration should represent meaningful operational boundaries.

## `.env` Files

`.env` files are useful for local development.

Example:

```dotenv
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=orders_dev

MONGODB_SERVER_SELECTION_TIMEOUT_MS=5000
MONGODB_CONNECT_TIMEOUT_MS=5000
MONGODB_SOCKET_TIMEOUT_MS=10000

MONGODB_MAX_POOL_SIZE=50
MONGODB_MIN_POOL_SIZE=5
MONGODB_WAIT_QUEUE_TIMEOUT_MS=2000
```

The file should normally be excluded from Git:

```gitignore
.env
.env.*
!.env.example
```

An example configuration can be committed:

```dotenv
MONGODB_URI=
MONGODB_DATABASE=
MONGODB_SERVER_SELECTION_TIMEOUT_MS=5000
MONGODB_CONNECT_TIMEOUT_MS=5000
MONGODB_SOCKET_TIMEOUT_MS=10000
MONGODB_MAX_POOL_SIZE=100
MONGODB_MIN_POOL_SIZE=10
MONGODB_WAIT_QUEUE_TIMEOUT_MS=2000
```

Do not put real passwords into `.env.example`.

## Environment-Specific Configuration

Avoid creating separate application implementations such as:

```text
config_dev.py
config_staging.py
config_prod.py
```

when the only difference is values.

Prefer a common configuration model:

```text
Application
    |
    +-- Development values
    +-- Test values
    +-- Staging values
    +-- Production values
```

This reduces configuration drift.

Environment-specific behavior should exist only where the behavior genuinely differs.

## Configuration Object in Python

A typed configuration object provides validation and centralized access.

```python
import os
from dataclasses import dataclass


def get_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


@dataclass(frozen=True)
class MongoSettings:
    uri: str
    database: str
    server_selection_timeout_ms: int
    connect_timeout_ms: int
    socket_timeout_ms: int
    wait_queue_timeout_ms: int
    max_pool_size: int
    min_pool_size: int


def load_mongo_settings() -> MongoSettings:
    return MongoSettings(
        uri=os.environ["MONGODB_URI"],
        database=os.environ["MONGODB_DATABASE"],
        server_selection_timeout_ms=get_int(
            "MONGODB_SERVER_SELECTION_TIMEOUT_MS",
            5000,
        ),
        connect_timeout_ms=get_int(
            "MONGODB_CONNECT_TIMEOUT_MS",
            5000,
        ),
        socket_timeout_ms=get_int(
            "MONGODB_SOCKET_TIMEOUT_MS",
            10000,
        ),
        wait_queue_timeout_ms=get_int(
            "MONGODB_WAIT_QUEUE_TIMEOUT_MS",
            2000,
        ),
        max_pool_size=get_int(
            "MONGODB_MAX_POOL_SIZE",
            100,
        ),
        min_pool_size=get_int(
            "MONGODB_MIN_POOL_SIZE",
            10,
        ),
    )
```

The important property is centralized validation.

Instead of:

```python
os.getenv("MONGODB_URI")
```

being scattered throughout the application, configuration is loaded once and passed to the infrastructure layer.

## Configuration Validation

Fail fast when required configuration is missing or invalid.

Example:

```python
settings = load_mongo_settings()

if settings.max_pool_size < settings.min_pool_size:
    raise ValueError(
        "MONGODB_MAX_POOL_SIZE must be greater than or equal to "
        "MONGODB_MIN_POOL_SIZE"
    )
```

Additional validation can include:

- Positive timeout values
- Valid pool sizes
- Required database name
- Required URI
- Environment-specific restrictions
- TLS requirements in production

A configuration error should be visible during startup rather than discovered under production traffic.

## PyMongo Configuration

A MongoDB client can be constructed from centralized settings.

```python
from pymongo import MongoClient


def create_mongo_client(settings: MongoSettings) -> MongoClient:
    return MongoClient(
        settings.uri,
        serverSelectionTimeoutMS=settings.server_selection_timeout_ms,
        connectTimeoutMS=settings.connect_timeout_ms,
        socketTimeoutMS=settings.socket_timeout_ms,
        waitQueueTimeoutMS=settings.wait_queue_timeout_ms,
        maxPoolSize=settings.max_pool_size,
        minPoolSize=settings.min_pool_size,
    )
```

Reuse the client for the lifetime of the process.

Do not create a new client per request:

```python
# Avoid
def get_orders():
    client = MongoClient(os.environ["MONGODB_URI"])
    ...
```

Instead:

```text
Application Process
        |
        +-- One MongoClient
                |
                +-- Connection Pool
                        |
                        +-- MongoDB
```

## Connection String Configuration

A local development URI may be:

```text
mongodb://localhost:27017
```

A replica-set URI might be:

```text
mongodb://mongo-1.internal:27017,mongo-2.internal:27017,mongo-3.internal:27017/orders?replicaSet=rs0
```

An Atlas deployment commonly uses:

```text
mongodb+srv://...
```

The application should not need different code paths merely because the URI scheme changes.

```python
client = MongoClient(settings.uri)
```

The topology is a configuration concern.

## Authentication Database

The database containing the MongoDB user is not necessarily the same as the application's database.

For example:

```text
Application database:
orders

Authentication database:
admin
```

The URI can explicitly specify:

```text
mongodb://orders_api:password@mongo.internal:27017/orders?authSource=admin
```

A common configuration failure is assuming that:

```text
database = orders
```

automatically means the user must exist in `orders`.

Authentication configuration should be explicit.

## TLS Configuration

Production configuration should normally require TLS when MongoDB is accessed across networks where unencrypted traffic is not acceptable.

Example:

```text
MONGODB_URI=mongodb://...
MONGODB_TLS=true
MONGODB_TLS_CA_FILE=/etc/mongodb/ca.pem
```

Application code:

```python
client = MongoClient(
    settings.uri,
    tls=settings.tls,
    tlsCAFile=settings.tls_ca_file,
)
```

Do not expose insecure development shortcuts in production configuration.

Avoid:

```python
tlsAllowInvalidCertificates=True
```

as a way to bypass certificate problems.

The correct solution is to fix:

- CA configuration
- Certificate chain
- Hostname configuration
- Certificate expiration
- Certificate rotation

## Production and Development TLS

It is reasonable for local development to use:

```text
MongoDB
    ↓
localhost
    ↓
No TLS
```

while production uses:

```text
Application
    ↓
TLS
    ↓
Private Network
    ↓
MongoDB
```

The configuration system should make this distinction explicit rather than hiding it inside application logic.

## Pool Configuration

Connection pool values should be configurable because workload characteristics differ between environments.

Example:

```dotenv
# Development
MONGODB_MAX_POOL_SIZE=20
MONGODB_MIN_POOL_SIZE=2
```

```dotenv
# Production
MONGODB_MAX_POOL_SIZE=100
MONGODB_MIN_POOL_SIZE=10
```

The production values should be derived from load testing and capacity planning.

Remember that total connection pressure depends on the entire application fleet:

```text
Application Instances
        ×
Connections per Pool
        =
Potential Database Connection Pressure
```

Multiple worker processes inside one container or host can each maintain their own MongoDB client and pool.

## Timeout Configuration

Different timeout values serve different purposes.

| Setting | Purpose |
|---|---|
| Server selection timeout | Time allowed to select a suitable MongoDB server |
| Connection timeout | Time allowed to establish a connection |
| Socket timeout | Time allowed for socket operations |
| Wait queue timeout | Time allowed waiting for a pool connection |

Example:

```dotenv
MONGODB_SERVER_SELECTION_TIMEOUT_MS=5000
MONGODB_CONNECT_TIMEOUT_MS=5000
MONGODB_SOCKET_TIMEOUT_MS=10000
MONGODB_WAIT_QUEUE_TIMEOUT_MS=2000
```

Timeouts should be aligned with the application's latency budget.

If an API request has a 10-second timeout, allowing an internal database operation to wait indefinitely is usually a poor design.

## Retry Configuration

PyMongo provides retry behavior for supported operations.

A configuration may explicitly define:

```dotenv
MONGODB_RETRY_WRITES=true
MONGODB_RETRY_READS=true
```

Retry behavior must be considered together with:

- HTTP retries
- Celery retries
- Kafka consumers
- Transaction retries
- Client-side retries

Avoid retry amplification:

```text
HTTP Client
    ↓ retry
API
    ↓ retry
Service
    ↓ retry
MongoDB Driver
    ↓ retry
MongoDB
```

A temporary database failure can become a much larger load spike if every layer independently retries aggressively.

## Environment Configuration for FastAPI

FastAPI applications can load MongoDB configuration during startup.

A configuration object can be created before the application starts serving traffic.

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import MongoClient


settings = load_mongo_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = create_mongo_client(settings)

    client.admin.command("ping")

    app.state.mongo_client = client
    app.state.mongo_db = client[settings.database]

    try:
        yield
    finally:
        client.close()


app = FastAPI(lifespan=lifespan)
```

The startup health check should be used deliberately. In some architectures, failing startup because MongoDB is temporarily unavailable may be preferable; in others, the service may need to start and degrade gracefully.

The decision should match the service's availability model.

## Async FastAPI Applications

Using an async web framework does not automatically make a blocking MongoDB client asynchronous.

If using synchronous PyMongo:

```text
FastAPI async endpoint
        ↓
Blocking MongoDB operation
        ↓
MongoDB
```

the application must account for the blocking behavior.

For an application designed around asynchronous MongoDB access, use the current PyMongo asynchronous API where appropriate rather than assuming the synchronous client is interchangeable with an async client.

The important configuration principle remains the same:

```text
Environment
    ↓
Typed Configuration
    ↓
MongoDB Client
    ↓
Application
```

## Environment Configuration for Django

Django applications can centralize MongoDB settings.

```python
import os

MONGODB_URI = os.environ["MONGODB_URI"]
MONGODB_DATABASE = os.environ["MONGODB_DATABASE"]
```

A repository or service layer should consume these settings rather than having views construct clients.

```text
Django View
    ↓
Service
    ↓
Repository
    ↓
MongoDB Client
```

This keeps environment configuration independent from business logic.

## Docker Configuration

Docker Compose is useful for local MongoDB development.

Example:

```yaml
services:
  mongodb:
    image: mongo:8
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: local-development-password
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

  api:
    build: .
    environment:
      MONGODB_URI: mongodb://admin:local-development-password@mongodb:27017/?authSource=admin
      MONGODB_DATABASE: orders_dev
    depends_on:
      - mongodb

volumes:
  mongodb_data:
```

The important Docker networking rule is that containers communicate using the service name:

```text
mongodb
```

rather than:

```text
localhost
```

Inside the API container:

```text
mongodb://mongodb:27017
```

refers to the MongoDB container.

`localhost` refers to the API container itself.

## Docker Secret Handling

Do not treat environment variables as inherently secure.

For local development, they are often adequate.

For production, credentials should preferably be injected through the deployment platform's secret-management mechanism.

Avoid:

```yaml
environment:
  MONGODB_URI: mongodb://admin:real-production-password@...
```

inside a committed production Compose or Kubernetes file.

## Kubernetes Configuration

Kubernetes separates configuration and secrets.

A simplified deployment can use:

```yaml
env:
  - name: MONGODB_DATABASE
    value: orders

  - name: MONGODB_URI
    valueFrom:
      secretKeyRef:
        name: mongodb-credentials
        key: uri
```

Non-sensitive configuration can use ConfigMaps:

```yaml
envFrom:
  - configMapRef:
      name: api-config
```

Secrets can be injected through:

- Environment variables
- Mounted files
- External secret controllers
- Cloud secret integrations

The choice should consider secret rotation, process behavior, and operational requirements.

## AWS Secret Management

For AWS deployments, database credentials can be stored in services such as:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store

A common architecture is:

```mermaid
flowchart LR
    Secrets[AWS Secrets Manager]
    Workload[ECS / EKS / EC2 Application]
    Config[Runtime Configuration]
    Driver[PyMongo]
    Mongo[MongoDB Atlas / MongoDB]

    Secrets --> Workload
    Config --> Workload
    Workload --> Driver
    Driver --> Mongo
```

The application should not log the retrieved secret.

Secret access should itself follow least privilege.

## CI/CD Configuration

CI/CD pipelines commonly need MongoDB configuration for:

- Integration tests
- Migration/index jobs
- Deployment validation
- Smoke tests

Use environment-specific CI secrets.

For example:

```text
CI
 |
 +-- MONGODB_URI_TEST
 +-- MONGODB_DATABASE_TEST
```

Do not print secrets for debugging:

```bash
echo "$MONGODB_URI"
```

A safer diagnostic is:

```bash
echo "MongoDB URI is configured"
```

without revealing its contents.

## Testing Configuration

Automated tests should not accidentally connect to production.

A test configuration might use:

```dotenv
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=orders_test
```

or an isolated ephemeral MongoDB environment.

Tests should make database selection explicit.

A dangerous pattern is:

```python
database = os.getenv("MONGODB_DATABASE", "orders")
```

when `orders` could be a production database.

For tests, fail if the expected test configuration is missing.

## Environment Safety Checks

Production configuration can include explicit environment identification.

```dotenv
APP_ENV=production
```

Then application startup can validate dangerous combinations.

```python
if settings.app_env == "production" and settings.database.endswith("_test"):
    raise RuntimeError(
        "Production application cannot use a test database"
    )
```

Additional safeguards can prevent:

- Production application using development MongoDB
- Test application using production MongoDB
- Development application using production credentials
- Staging services writing to production

## Configuration Precedence

If multiple configuration sources exist, define precedence explicitly.

A common model is:

```text
Hard-coded safe defaults
        ↓
Environment variables
        ↓
Secret injection
        ↓
Deployment-specific overrides
```

Avoid having multiple libraries silently override each other.

For example:

```text
.env
↓
Shell environment
↓
Docker Compose
↓
Kubernetes
↓
Application defaults
```

The final effective configuration should be understandable.

## Configuration Inspection

Applications should provide safe diagnostics.

For example:

```python
def configuration_summary(settings: MongoSettings) -> dict:
    return {
        "database": settings.database,
        "max_pool_size": settings.max_pool_size,
        "min_pool_size": settings.min_pool_size,
        "server_selection_timeout_ms": (
            settings.server_selection_timeout_ms
        ),
        "tls_enabled": settings.tls,
        "environment": settings.app_env,
    }
```

Never include:

```text
password
full authenticated URI
private key
secret token
```

in diagnostic output.

A `/health` endpoint should also avoid returning credentials or internal connection strings.

## Configuration Validation at Startup

A production startup sequence can look like:

```mermaid
sequenceDiagram
    participant App as Application
    participant Config as Configuration
    participant Secrets as Secret Store
    participant Mongo as MongoDB

    App->>Config: Load configuration
    Config->>Secrets: Resolve secrets
    Secrets-->>Config: Credentials
    Config-->>App: Validated settings
    App->>Mongo: Create MongoClient
    Mongo-->>App: Connection / topology
    App->>Mongo: Ping / health validation
    Mongo-->>App: Success
    App->>App: Start serving traffic
```

The application should validate configuration before accepting production traffic.

## Configuration and Health Checks

A MongoDB health check should answer the question appropriate to the deployment.

A basic connectivity check:

```python
client.admin.command("ping")
```

does not prove that:

- Required collections exist
- Required indexes exist
- The application user has every required permission
- Queries are performant
- Backups are working
- Replica-set health is acceptable

Health checks should therefore be separated into appropriate categories.

| Check | Purpose |
|---|---|
| Liveness | Process is alive |
| Readiness | Service can accept traffic |
| Dependency health | MongoDB is reachable |
| Operational monitoring | MongoDB is healthy over time |

## Configuration and Index Deployment

Indexes should not be created implicitly on every application startup.

Avoid:

```python
def startup():
    collection.create_index(...)
```

for large production deployments unless the behavior is intentionally designed and understood.

A dedicated migration or deployment step is usually easier to control:

```text
CI/CD
   ↓
Database Change Job
   ↓
Index / Validation Change
   ↓
Verification
   ↓
Application Deployment
```

This makes database changes observable and auditable.

## Configuration and Schema Evolution

Environment configuration should not be confused with database schema configuration.

Environment configuration controls runtime behavior:

```text
MONGODB_URI
MONGODB_DATABASE
MONGODB_MAX_POOL_SIZE
```

Schema configuration controls database structure and rules:

```text
Indexes
Validation Rules
Collections
Document Transformations
```

Keep the deployment process for both explicit.

## Production Configuration Example

A production environment might conceptually contain:

```dotenv
APP_ENV=production

MONGODB_URI=mongodb+srv://...
MONGODB_DATABASE=orders

MONGODB_SERVER_SELECTION_TIMEOUT_MS=5000
MONGODB_CONNECT_TIMEOUT_MS=5000
MONGODB_SOCKET_TIMEOUT_MS=10000
MONGODB_WAIT_QUEUE_TIMEOUT_MS=2000

MONGODB_MAX_POOL_SIZE=100
MONGODB_MIN_POOL_SIZE=10
MONGODB_MAX_CONNECTING=2

MONGODB_RETRY_WRITES=true
MONGODB_RETRY_READS=true
```

The exact values should come from workload testing rather than being copied blindly.

## Configuration Matrix

A useful operational configuration matrix might look like:

| Setting | Development | Test | Staging | Production |
|---|---|---|---|---|
| MongoDB | Local/Docker | Isolated | Dedicated | HA deployment |
| TLS | Optional | Optional/required | Required | Required |
| Credentials | Local secrets | CI secrets | Secret manager | Secret manager |
| Pool size | Small | Small | Load-tested | Load-tested |
| Timeouts | Relaxed | Short | Production-like | SLA-driven |
| Backups | Usually unnecessary | Usually unnecessary | Required where realistic | Required |
| Monitoring | Basic | Test metrics | Full | Full |
| Database access | Developer machine | CI workload | Restricted | Restricted |

## Common Mistakes

### Hard-Coded Connection Strings

```python
MongoClient("mongodb://admin:password@...")
```

**Why it happens:** Local development is convenient.

**Why it is dangerous:** Credentials become part of source code and can leak through Git history.

**Better approach:** Inject the URI through environment-specific configuration or a secret manager.

### Using `localhost` Inside Containers

```text
mongodb://localhost:27017
```

**Why it happens:** The application works outside Docker.

**Why it fails:** Inside a container, `localhost` refers to that container.

**Better approach:** Use the Docker service name or configured hostname.

### Sharing Production Credentials With Developers

**Why it happens:** Developers need realistic data.

**Why it is dangerous:** It expands the attack surface and creates accidental write/delete risks.

**Better approach:** Use synthetic or sanitized data and separate credentials.

### Using One Database Name Everywhere

```text
orders
```

for development, staging, and production.

**Why it happens:** Configuration is not environment-aware.

**Risk:** Accidental cross-environment access.

**Better approach:** Use explicit environment-specific databases or clusters.

### Logging the MongoDB URI

```python
logger.info("MongoDB URI: %s", settings.uri)
```

**Risk:** Passwords can enter application logs.

**Better approach:** Log sanitized configuration metadata.

### Over-Configuring Through Environment Variables

Creating an environment variable for every MongoDB option creates configuration complexity.

Prefer:

```text
Meaningful operational settings
```

over:

```text
Every possible MongoDB option
```

### Creating a MongoClient Per Request

This defeats connection pooling and increases connection establishment overhead.

Create the client once per application process and reuse it.

## Production Pitfalls

| Pitfall | Impact | Prevention |
|---|---|---|
| Missing `authSource` | Authentication failures | Make authentication database explicit |
| Incorrect TLS CA | Connection failures | Validate certificates in staging |
| Excessive pool size | Connection exhaustion | Capacity-plan across all instances |
| No timeout | Hanging requests | Configure bounded timeouts |
| Aggressive retries | Load amplification | Use bounded retries and backoff |
| Shared credentials | Security exposure | Separate identities per environment |
| Secret in Git | Credential compromise | Secret scanning and protected stores |
| Production defaults in tests | Data corruption | Explicit test configuration |
| Configuration drift | Environment-specific failures | Centralize and validate configuration |
| Startup without validation | Late failures | Validate critical configuration early |

## Security Considerations

Production MongoDB environment configuration should enforce:

- No credentials in source control
- No credentials in application logs
- TLS where required
- Certificate validation
- Least-privilege MongoDB users
- Separate credentials per environment
- Secret rotation
- Restricted network access
- Secret-manager access controlled by workload identity
- Secret scanning in CI/CD

Configuration files should also be reviewed for indirect leaks.

For example, this may reveal sensitive infrastructure information:

```text
mongodb://production-mongo-01.internal.example.com:27017
```

Even without credentials, infrastructure details may be inappropriate for public repositories.

## Scalability Considerations

Configuration should account for application scaling.

If there are:

```text
20 API instances
```

and each instance can maintain:

```text
100 connections per MongoDB server
```

the database may experience substantial connection pressure.

The effective capacity model should therefore include:

```text
Application Replicas
×
Processes per Replica
×
MongoDB Pool Configuration
×
Eligible MongoDB Servers
```

The exact number of active connections depends on topology and driver behavior, but the principle is critical:

> Pool sizing is a fleet-level capacity decision, not just an application-instance setting.

## Reliability Considerations

Environment configuration should support predictable failure behavior.

Important settings include:

- Timeouts
- Retry behavior
- Read preference
- Write concern
- Connection pooling
- TLS
- Replica-set discovery

A resilient configuration should fail quickly enough to protect application resources while allowing transient MongoDB failures to recover when safe.

## Monitoring Configuration

Monitor configuration-related failures such as:

- Authentication failures
- TLS failures
- Server-selection failures
- Connection pool exhaustion
- Timeout rates
- Retry rates
- Connection counts
- Replica-set topology changes

A configuration change that increases pool size or timeout values can have production consequences even when no application source code changes.

## Cost Considerations

Environment configuration can affect infrastructure cost.

Examples:

- Larger connection pools can require larger MongoDB capacity.
- Higher minimum pool sizes create more persistent connections.
- Larger instances may be required for working-set capacity.
- Separate staging clusters increase infrastructure cost.
- Cross-region deployments increase network and storage costs.
- Managed secret and monitoring services add operational cost.

Cost optimization should never remove security or recovery capabilities without explicitly evaluating the resulting risk.

## Troubleshooting

### Application Connects to the Wrong Database

```text
Symptom
↓
Application appears healthy but reads or writes unexpected data
↓
Possible causes
↓
Wrong MONGODB_URI
Wrong MONGODB_DATABASE
Incorrect environment variable
Configuration precedence issue
Production credentials used in another environment
↓
Isolation strategy
↓
Inspect sanitized effective configuration and verify the deployment environment
↓
Diagnostic commands
```

```bash
printenv | grep '^MONGODB_'
```

Only use this in a controlled environment where sensitive variables are not exposed. Never paste credentials into logs or tickets.

```text
Root cause
↓
Incorrect effective runtime configuration
↓
Corrective action
↓
Fix the environment configuration and redeploy
↓
Prevention
↓
Add startup validation and environment-specific safety checks
```

### Authentication Failure

```text
Symptom
↓
MongoDB rejects application authentication
↓
Possible causes
↓
Wrong credentials
Wrong authSource
Credential rotation mismatch
Incorrect secret injection
Malformed URI
↓
Isolation strategy
↓
Validate secret source, username, authSource, and connection configuration without exposing the password
↓
Diagnostic commands
```

```bash
mongosh "$MONGODB_URI" --eval 'db.runCommand({ connectionStatus: 1 })'
```

```text
Root cause
↓
Authentication configuration mismatch
↓
Corrective action
↓
Correct secret or authentication configuration
↓
Prevention
↓
Validate credentials in staging and automate controlled rotation
```

### Container Cannot Reach MongoDB

```text
Symptom
↓
Application works locally but fails inside Docker
↓
Possible causes
↓
Using localhost
Incorrect service name
Port mismatch
Container network configuration
MongoDB not ready
↓
Isolation strategy
↓
Check container networking and resolve the MongoDB service from the application container
↓
Diagnostic commands
```

```bash
docker compose exec api getent hosts mongodb
```

```bash
docker compose exec api sh
```

```text
Root cause
↓
Application is using an invalid container-network address
↓
Corrective action
↓
Use the MongoDB service hostname and correct internal port
↓
Prevention
↓
Test the complete Docker topology rather than only the host-based connection
```

### Configuration Works in Staging but Fails in Production

```text
Symptom
↓
Application works in staging but fails after production deployment
↓
Possible causes
↓
Missing secret
Different TLS requirements
Different DNS
Different network policy
Different replica-set topology
Different authentication configuration
Different pool or timeout settings
↓
Isolation strategy
↓
Compare sanitized effective configuration and infrastructure assumptions
↓
Diagnostic commands
↓
Application startup logs
Deployment configuration
MongoDB topology inspection
Health checks
↓
Root cause
↓
Environment-specific configuration or infrastructure difference
↓
Corrective action
↓
Align intended configuration and infrastructure assumptions
↓
Prevention
↓
Use production-like staging and automated configuration validation
```

## Operational Best Practices

- Treat MongoDB configuration as code where practical.
- Keep secrets outside source control.
- Validate required configuration during startup.
- Keep environment-specific values external to application logic.
- Reuse one MongoDB client per application process.
- Size connection pools using fleet-level capacity planning.
- Configure bounded timeouts.
- Treat retries as part of an end-to-end resilience strategy.
- Use separate MongoDB identities for different environments.
- Require TLS in production deployments where appropriate.
- Keep development and production network paths separate.
- Test configuration changes in staging.
- Monitor connection and timeout behavior after configuration changes.
- Document the effective production configuration.
- Review configuration during MongoDB upgrades and infrastructure changes.

## Interview Focus

| Question | Key point |
|---|---|
| Why externalize MongoDB configuration? | It separates deployment-specific values and secrets from application code |
| Should every MongoDB option become an environment variable? | No; expose meaningful operational settings and keep configuration manageable |
| Why should MongoDB credentials not be committed to Git? | Git history and repositories can expose long-lived credentials |
| Why use a typed configuration object? | It centralizes validation and prevents configuration access from being scattered |
| Why is `localhost` wrong inside a Docker container? | `localhost` refers to the current container, not another service |
| Why should a MongoDB client be reused? | It provides connection pooling and avoids repeated connection establishment |
| Why configure timeouts? | They prevent stalled database operations from consuming application resources indefinitely |
| What is `authSource`? | The database against which the MongoDB user authenticates |
| Why separate test and production configuration? | It prevents accidental access to production data |
| Why should pool size be planned across the fleet? | Every application process can maintain its own pool |
| Why should production configuration be validated at startup? | Invalid configuration should fail before serving incorrect or unsafe traffic |
| Why should configuration changes be monitored? | Runtime settings such as pools, timeouts, and retries can materially affect production behavior |

## Key Takeaways

- **Separate MongoDB configuration from application code, and treat credentials, connection URIs, and cryptographic material as secrets rather than ordinary configuration.**
- **Use explicit environment-specific configuration with centralized validation so development, testing, staging, and production cannot accidentally share unsafe database settings.**
- **Configure MongoDB connection pools, timeouts, retries, TLS, authentication, and topology deliberately based on workload and reliability requirements.**
- **Production configuration must be validated and monitored at runtime, with special attention to connection pressure, authentication failures, timeout behavior, and configuration drift.**
- **Use secret managers and deployment-native configuration mechanisms for production while keeping local `.env` workflows isolated from real production credentials.**