# 02- Authentication

## Overview

MongoDB authentication establishes the identity of a client before MongoDB evaluates what that client is allowed to do.

Authentication is one layer of MongoDB security:

```text
Network Access
      ↓
TLS
      ↓
Authentication
      ↓
Authorization
      ↓
Database Operation
```

Authentication answers:

> Who is connecting to MongoDB?

Authorization answers a different question:

> What is that authenticated identity allowed to do?

A production MongoDB deployment should use explicit authentication for applications, administrative tools, background workers, migration jobs, and other database clients.

Authentication design becomes particularly important in distributed Python systems where multiple FastAPI, Django, Celery, and microservice processes may connect to the same MongoDB deployment.

---

## Authentication Architecture

A typical application request flows through several independent controls:

```mermaid
sequenceDiagram
    participant A as Python Application
    participant T as TLS
    participant M as MongoDB
    participant Auth as Authentication
    participant Authz as Authorization

    A->>T: Establish encrypted connection
    T->>M: TLS connection
    A->>M: Authenticate credentials
    M->>Auth: Validate identity
    Auth-->>M: Authenticated user
    M->>Authz: Check privileges
    Authz-->>M: Allow / deny
    M-->>A: Database response
```

Authentication should therefore not be viewed as simply adding a username and password to a connection string.

A production authentication architecture should consider:

- identity
- authentication mechanism
- authentication database
- credentials
- TLS
- network restrictions
- authorization roles
- secret storage
- credential rotation
- connection pooling
- failure behavior
- auditing
- operational access

---

## Authentication vs Authorization

| Security Layer | Purpose | Example |
|---|---|---|
| Network control | Restrict connection sources | Application subnet only |
| TLS | Protect network traffic | Encrypted MongoDB connection |
| Authentication | Establish identity | `orders-service` |
| Authorization | Restrict operations | Read/write `orders` |
| Application authorization | Enforce business access | Tenant A cannot access Tenant B |

A client can therefore be:

```text
Network allowed
        ↓
TLS successful
        ↓
Authentication successful
        ↓
Authorization denied
```

Successful authentication does not imply successful authorization.

---

## MongoDB Users

A MongoDB user represents an identity that can authenticate to the deployment.

Production applications should generally use dedicated database users.

Example:

```text
orders-service
inventory-service
reporting-service
migration-service
backup-service
```

Avoid using a single administrator account for every application.

If an application credential is compromised, its permissions should limit the resulting blast radius.

---

## Application Identity

A useful production model is:

```text
Order Service
    │
    └── orders-service
            │
            ├── orders database
            └── required privileges

Inventory Service
    │
    └── inventory-service
            │
            ├── inventory database
            └── required privileges
```

The database identity should represent the workload rather than the individual developer deploying it.

---

## Human vs Workload Authentication

Human and workload access should be treated differently.

| Identity | Typical Use | Characteristics |
|---|---|---|
| Application user | API/service access | Automated, least privilege |
| Worker user | Celery/background jobs | Restricted to worker workload |
| Migration user | Schema/data migrations | Elevated, temporary where possible |
| Monitoring user | Observability | Read-only where possible |
| Administrator | Infrastructure operations | Highly restricted |
| Developer | Troubleshooting/development | Environment-specific |

Do not give application services administrator credentials merely because administrators use those credentials during setup.

---

## Authentication Mechanisms

MongoDB supports multiple authentication mechanisms. The appropriate mechanism depends on the deployment environment, client capabilities, security requirements, and identity infrastructure.

Common mechanisms include:

| Mechanism | Typical Use |
|---|---|
| SCRAM | Application and user authentication |
| X.509 | Certificate-based authentication |
| LDAP / enterprise identity integration | Centralized enterprise authentication |
| Kerberos | Enterprise environments using Kerberos |
| Cloud/provider-specific mechanisms | Managed identity integrations where supported |

For many application deployments, SCRAM is the practical baseline. Certificate-based and enterprise identity mechanisms become relevant when centralized identity or certificate-based authentication is required.

---

## SCRAM Authentication

SCRAM is a challenge-response authentication mechanism.

The high-level flow is:

```text
Client
  │
  │ authentication request
  ▼
MongoDB
  │
  │ challenge
  ▼
Client
  │
  │ proof derived from credentials
  ▼
MongoDB
  │
  ▼
Authentication success / failure
```

The client does not simply send the password as a plaintext MongoDB protocol value.

SCRAM authentication should still be combined with TLS in production because authentication and transport confidentiality solve different problems.

---

## SCRAM Mechanism Selection

Modern MongoDB deployments support SCRAM mechanisms such as:

- `SCRAM-SHA-1`
- `SCRAM-SHA-256`

When configuring a new production application, use the strongest mechanism supported by the MongoDB deployment and client stack, normally `SCRAM-SHA-256`.

Do not force an older mechanism simply because an existing example or legacy connection string uses it.

---

## Connection String Authentication

A typical authenticated connection string looks like:

```text
mongodb://username:password@mongodb.example.com:27017/orders?authSource=admin
```

For a replica set:

```text
mongodb://username:password@mongo-1.example.com:27017,mongo-2.example.com:27017,mongo-3.example.com:27017/orders?replicaSet=rs0&authSource=admin
```

For production, credentials should not be hard-coded into source code.

The connection string should normally be assembled or injected through a secret-management mechanism.

---

## `authSource`

`authSource` specifies the database against which MongoDB authenticates the user.

For example:

```text
mongodb://app_user:password@mongodb.example.com/orders?authSource=admin
```

This means:

```text
Target database:
    orders

Authentication database:
    admin
```

The authentication database and application database do not have to be the same.

This distinction is a frequent source of authentication failures.

---

## Authentication Database

Consider:

```text
admin
└── orders-service user

orders
└── application collections
```

The application can authenticate against `admin` and then operate against the `orders` database according to its assigned privileges.

When debugging authentication problems, verify:

- username
- password
- authentication mechanism
- `authSource`
- target database
- TLS configuration
- server topology

---

## Python Authentication with PyMongo

A production application can use a connection string:

```python
from pymongo import MongoClient

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5_000,
    connectTimeoutMS=5_000,
    socketTimeoutMS=10_000,
)

client.admin.command("ping")
```

The URI should come from runtime configuration rather than source code.

---

## Explicit Authentication Configuration

Authentication can also be configured through driver options.

For example:

```python
from pymongo import MongoClient

client = MongoClient(
    MONGODB_HOST,
    username=MONGODB_USERNAME,
    password=MONGODB_PASSWORD,
    authSource="admin",
    authMechanism="SCRAM-SHA-256",
    tls=True,
    serverSelectionTimeoutMS=5_000,
)
```

The exact configuration should match the MongoDB deployment and certificate setup.

---

## Environment-Based Configuration

For local development:

```text
MONGODB_URI=mongodb://app_user:local_password@localhost:27017/orders?authSource=admin
```

For production:

```text
MONGODB_URI=<secret-managed-value>
```

Application code should not need to know whether the value came from:

- AWS Secrets Manager
- Kubernetes Secrets
- a CI/CD secret store
- another approved secret-management system

---

## Secret Management

Credentials should be externalized:

```mermaid
flowchart LR
    SM[Secret Manager] --> APP[Python Application]
    APP --> MC[MongoClient]
    MC --> DB[(MongoDB)]
```

For AWS workloads:

```text
AWS Secrets Manager
        ↓
ECS / EKS / EC2
        ↓
Application Runtime
        ↓
MongoClient
```

For Kubernetes:

```text
Secret Store
      ↓
Pod / Workload Identity
      ↓
Application
      ↓
MongoClient
```

The mechanism can vary, but the principle remains the same:

> Database credentials are configuration secrets, not application source code.

---

## Credential Storage Anti-Patterns

Never commit:

```python
MONGODB_URI = (
    "mongodb://admin:SuperSecretPassword@"
    "mongodb.example.com/orders"
)
```

Avoid putting credentials into:

- Git repositories
- Dockerfiles
- public configuration files
- screenshots
- issue trackers
- application logs
- exception messages
- CI/CD output

Even private repositories should not be treated as secret stores.

---

## URL Encoding Credentials

MongoDB connection strings are URLs. Special characters in usernames or passwords may therefore need URL encoding.

For example, a password containing characters such as:

```text
@ : / ? # %
```

can interfere with URI parsing if not encoded correctly.

Python can safely encode credentials when constructing a URI:

```python
from urllib.parse import quote_plus

username = quote_plus(MONGODB_USERNAME)
password = quote_plus(MONGODB_PASSWORD)

uri = (
    f"mongodb://{username}:{password}"
    "@mongodb.example.com:27017/orders"
    "?authSource=admin"
)
```

In production, prefer receiving a complete, correctly configured URI from the secret-management layer rather than dynamically constructing secrets unnecessarily.

---

## Authentication and TLS

Authentication does not encrypt database traffic.

A production connection should generally use TLS:

```text
Application
    │
    │ TLS
    ▼
MongoDB
    │
    ├── Authenticate identity
    │
    └── Authorize operation
```

Without TLS, network traffic can potentially be observed or modified depending on the network environment.

---

## PyMongo TLS Configuration

Example:

```python
from pymongo import MongoClient

client = MongoClient(
    MONGODB_URI,
    tls=True,
    serverSelectionTimeoutMS=5_000,
)
```

For deployments using a private CA, configure the trusted CA appropriately.

Do not disable certificate verification merely to make a connection work.

---

## Certificate Validation

Secure TLS requires both:

```text
Encryption
+
Endpoint authentication
```

A client that accepts arbitrary certificates can be vulnerable to man-in-the-middle attacks.

Avoid production configurations equivalent to:

```python
tlsAllowInvalidCertificates=True
```

unless there is a narrowly defined, controlled operational reason and an explicit understanding of the security consequences.

---

## Authentication and Network Security

Authentication should be combined with network restrictions.

A secure architecture is:

```text
Internet
   │
   X
   │
MongoDB

Private Application Network
   │
   ▼
MongoDB
```

A database should not be publicly reachable merely because authentication is enabled.

An attacker who discovers valid credentials should still face network-level restrictions.

---

## Authentication Flow in a Python API

```mermaid
sequenceDiagram
    participant API as FastAPI / Django
    participant DB as MongoDB
    participant A as Auth Layer
    participant Z as Authorization

    API->>DB: Open MongoClient connection
    DB->>A: Authenticate service identity
    A-->>DB: Identity verified
    API->>DB: Query orders
    DB->>Z: Evaluate privileges
    Z-->>DB: Allowed
    DB-->>API: Documents
```

The MongoDB authentication session is distinct from the end-user authentication handled by the API.

---

## End-User Authentication vs MongoDB Authentication

This distinction is critical in backend systems.

Suppose:

```text
User
  ↓
FastAPI
  ↓
MongoDB
```

There are two identities:

```text
User
    ↓
Application authentication
    ↓
JWT / OAuth / session / identity provider

Application
    ↓
MongoDB authentication
    ↓
MongoDB service identity
```

The API normally does not authenticate every end user directly to MongoDB.

Instead, the application authenticates to MongoDB using its service identity and enforces end-user authorization itself.

---

## Multi-Tenant Authentication

MongoDB authentication establishes the application's database identity.

It does not automatically establish tenant identity.

For example:

```text
orders-service
    ↓
Authenticated to MongoDB
    ↓
tenant_id = tenant-a
    ↓
Query scoped to tenant-a
```

The application must still enforce:

```python
query = {
    "tenant_id": authenticated_tenant_id,
    "order_id": order_id,
}
```

A database user being authenticated does not mean the user is authorized to access every tenant.

---

## Authentication for Background Workers

Celery workers should use an appropriate MongoDB identity.

```text
FastAPI
   │
   └── orders-api user

Celery
   │
   └── orders-worker user
```

The worker may need different privileges from the API.

For example:

```text
API:
    read + insert + update

Worker:
    read + update

Migration:
    temporary elevated permissions
```

Do not automatically reuse the API credentials everywhere.

---

## Authentication for Migration Jobs

Database migrations and data backfills often require elevated permissions.

A safer pattern is:

```text
Create migration identity
        ↓
Grant required privileges
        ↓
Run migration
        ↓
Validate result
        ↓
Revoke / disable identity
```

If a long-lived migration user is required, access should still be tightly controlled and audited.

---

## Administrative Authentication

Administrative access should use a separate identity from application access.

```text
Application
    ↓
orders-service
    ↓
Limited privileges

Administrator
    ↓
admin identity
    ↓
Administrative privileges
```

This separation provides:

- clearer audit trails
- smaller application blast radius
- easier credential rotation
- safer incident response

---

## Monitoring Authentication Activity

Monitor authentication-related events such as:

- repeated failures
- unusual source addresses
- unexpected users
- unexpected authentication mechanisms
- authentication spikes
- administrative login activity

A sudden increase can indicate:

```text
Credential leak
      or
Brute-force activity
      or
Application misconfiguration
      or
Deployment failure
```

The monitoring system should correlate authentication events with application and infrastructure logs.

---

## Authentication Failure Troubleshooting

A structured approach is more effective than repeatedly changing credentials.

```text
Symptom
↓
Authentication failure
↓
Verify server reachability
↓
Verify TLS
↓
Verify username
↓
Verify password
↓
Verify authSource
↓
Verify authentication mechanism
↓
Verify user exists
↓
Verify client/driver configuration
↓
Root cause
↓
Correct configuration
↓
Prevention
```

---

## Authentication Troubleshooting Matrix

| Symptom | Likely Area |
|---|---|
| Connection refused | Network / MongoDB availability |
| Timeout | Network / DNS / server selection |
| TLS handshake failure | Certificate / TLS configuration |
| Authentication failed | Credentials / mechanism / `authSource` |
| Unauthorized | Roles / privileges |
| Works in Compass but not Python | URI / driver / TLS / auth configuration |
| Works locally but not production | Network / secrets / certificates |
| Works with admin but not app user | Authorization configuration |

---

## `mongosh` Authentication

A typical `mongosh` connection can specify the URI:

```bash
mongosh "mongodb://app_user@mongodb.example.com:27017/orders?authSource=admin"
```

The password should not be casually exposed in shell history.

Prefer mechanisms that prompt securely for credentials or use an approved secret-management workflow.

---

## Inspecting the Authenticated User

After connecting with `mongosh`, inspect the authenticated identity:

```javascript
db.runCommand({
  connectionStatus: 1
})
```

This is useful when debugging situations where:

```text
Connection succeeds
but
Expected permissions are missing
```

It helps distinguish authentication from authorization problems.

---

## Authentication Database Troubleshooting

Suppose the user was created in `admin`:

```text
admin
└── app_user
```

but the application connects to:

```text
orders
```

without specifying the correct authentication source.

The connection may fail even though:

```text
username = correct
password = correct
```

because MongoDB is authenticating against the wrong database.

Check:

```text
username
password
authSource
authentication mechanism
```

before recreating the user.

---

## Authentication Mechanism Troubleshooting

If a client explicitly requests a mechanism:

```python
MongoClient(
    MONGODB_URI,
    authMechanism="SCRAM-SHA-256",
)
```

the server and client must support the selected mechanism.

Avoid forcing authentication mechanisms unnecessarily.

Prefer the deployment's supported modern configuration and keep drivers current.

---

## Authentication and Connection Pooling

PyMongo's `MongoClient` manages connection pools.

Applications should generally create a long-lived client:

```python
client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5_000,
)
```

and reuse it.

Avoid:

```python
def request_handler():
    client = MongoClient(MONGODB_URI)
    ...
```

Creating clients repeatedly can cause:

- unnecessary connections
- authentication overhead
- connection spikes
- increased resource consumption

---

## Authentication in FastAPI

A centralized MongoDB client can be initialized during application startup.

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import MongoClient


client: MongoClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client

    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5_000,
        connectTimeoutMS=5_000,
        socketTimeoutMS=10_000,
        retryWrites=True,
    )

    client.admin.command("ping")

    yield

    client.close()


app = FastAPI(lifespan=lifespan)
```

The URI should contain the required authentication configuration.

---

## Authentication in Django

Django applications using MongoDB through PyMongo or a document-oriented integration should similarly centralize connection configuration.

A typical architecture is:

```text
Django View
    ↓
Service
    ↓
Repository
    ↓
MongoClient
    ↓
MongoDB
```

Do not place database credentials directly in views or repositories.

Use Django settings backed by environment or secret-management infrastructure.

---

## Authentication in gRPC Services

The same database authentication model applies to gRPC services.

```text
gRPC Client
     ↓
gRPC Service
     ↓
MongoClient
     ↓
MongoDB Authentication
```

The end user's gRPC identity and the service's MongoDB identity remain separate security contexts.

---

## Authentication in Microservices

A multi-service architecture may have:

```text
User Service
    ↓
users-service

Order Service
    ↓
orders-service

Payment Service
    ↓
payments-service
```

Each service should authenticate independently to MongoDB where practical.

This creates clearer boundaries around:

- access
- auditing
- credential rotation
- incident response
- least privilege

---

## Authentication and Kubernetes

Kubernetes workloads should obtain MongoDB credentials through an approved secret-management approach.

A conceptual flow is:

```text
Pod
 │
 ├── Workload Identity
 │
 ▼
Secret Provider
 │
 ▼
MongoDB Credentials
 │
 ▼
MongoClient
```

Do not embed credentials directly in container images.

Also ensure that Kubernetes RBAC does not allow unrelated workloads to retrieve the MongoDB secret.

---

## Authentication and AWS

For AWS-hosted applications:

```text
ECS / EKS / EC2
       │
       ▼
AWS Identity
       │
       ▼
Secrets Manager
       │
       ▼
MongoDB Credentials
       │
       ▼
PyMongo
       │
       ▼
MongoDB
```

The AWS identity used by the workload should have permission to retrieve only the secrets it requires.

---

## Credential Rotation

Credential rotation must account for connection pools and running application instances.

A controlled rotation can follow:

```text
Create new MongoDB credential
        ↓
Store new secret
        ↓
Deploy updated application
        ↓
Verify successful authentication
        ↓
Drain old application instances
        ↓
Revoke old credential
        ↓
Monitor authentication failures
```

Do not revoke the old credential before confirming that all relevant consumers have migrated.

---

## Zero-Downtime Credential Rotation

A safer approach can temporarily support two valid credentials:

```text
Credential A ──► Current application instances
Credential B ──► New application instances
```

Then:

```text
Deploy B
   ↓
Verify B
   ↓
Migrate all workloads
   ↓
Revoke A
```

This reduces the risk of an authentication outage during rotation.

---

## Credential Rotation Across Workers

Remember that database consumers may include more than API pods:

```text
FastAPI
Django
Celery
Airflow
Cron jobs
Migration scripts
ETL jobs
Admin tools
```

A rotation is incomplete until every required consumer has been migrated.

---

## Authentication and High Availability

MongoDB authentication must continue working during replica-set failover.

Applications should use replica-set-aware connection strings or managed deployment connection strings rather than hard-coding one primary node.

Example:

```text
mongodb://app_user:password@
mongo-1:27017,
mongo-2:27017,
mongo-3:27017/
orders?replicaSet=rs0&authSource=admin
```

The MongoDB driver can then discover the current topology.

---

## Authentication During Primary Failover

A primary election may temporarily interrupt database operations:

```text
Primary
   ↓
Failure
   ↓
Election
   ↓
New Primary
   ↓
Driver topology update
   ↓
Application continues
```

Authentication identity remains part of the client configuration.

The application should not implement its own manual primary discovery.

---

## Authentication and Read Preferences

Authentication establishes the identity used by the MongoDB client.

Read preference determines where eligible reads may be routed.

These are separate concepts:

```text
Authentication
    ↓
Who is the client?

Read Preference
    ↓
Which replica member can serve the read?
```

Do not confuse authentication with replica-set routing.

---

## Authentication and Transactions

A transaction executes under the authenticated MongoDB client/session context.

The authenticated user must have the required permissions for all operations performed inside the transaction.

For example:

```text
orders-service
    ↓
Transaction
    ├── orders update
    └── inventory update
```

The identity needs appropriate authorization for both operations.

---

## Authentication and Change Streams

A change stream consumer also requires appropriate authentication and authorization.

Example:

```text
Celery / Worker
      ↓
MongoDB authentication
      ↓
Change stream
      ↓
Event processing
```

The change-stream identity should not automatically receive unrestricted administrative permissions.

---

## Authentication and Backup

Backup operations should use appropriately scoped identities.

Separate:

```text
Application credential
        ≠
Backup credential
        ≠
Administrative credential
```

This limits the consequences of application credential compromise.

---

## Authentication Auditability

Authentication identities should make activity attributable.

Prefer:

```text
orders-service
inventory-service
migration-service
```

over:

```text
application-user
```

for every workload.

Service-specific identities make logs and incident investigations more useful.

---

## Common Authentication Mistakes

### Using the Administrator User in Applications

**Problem:** Application compromise can become full database compromise.

**Prevention:** Create a dedicated least-privilege service user.

### Omitting `authSource`

**Problem:** MongoDB authenticates against an unexpected database.

**Prevention:** Explicitly configure `authSource` when the user's authentication database differs from the target database.

### Putting Passwords in Git

**Problem:** Git history can preserve credentials long after the current file is changed.

**Prevention:** Rotate exposed credentials and move secrets to an approved secret-management system.

### Creating `MongoClient` Per Request

**Problem:** Excessive connection creation and authentication overhead.

**Prevention:** Reuse a long-lived client.

### Disabling TLS Verification

**Problem:** The client may accept an untrusted server certificate.

**Prevention:** Configure the correct CA trust chain.

### Reusing One Credential Everywhere

**Problem:** It destroys workload-level isolation.

**Prevention:** Use service-specific identities.

### Confusing User Authentication with End-User Authentication

**Problem:** Developers assume MongoDB should authenticate every API user.

**Prevention:** Normally authenticate the application service to MongoDB and enforce user authorization in the application.

### Passing User-Controlled Credentials or URI Components

**Problem:** Connection configuration can become an injection or credential-handling risk.

**Prevention:** Keep database connection configuration server-side and secret-managed.

### Logging MongoDB URIs

**Problem:** Passwords embedded in URIs can leak into logs.

**Prevention:** Redact credentials before logging configuration.

---

## Authentication Security Checklist

### Identity

- [ ] Production authentication is enabled
- [ ] Application users are dedicated identities
- [ ] Administrative users are separate
- [ ] Background workers use appropriate identities
- [ ] Migration identities are controlled
- [ ] Monitoring identities are appropriately restricted

### Credentials

- [ ] Passwords are not stored in source code
- [ ] Secrets are managed externally
- [ ] Credentials are rotated
- [ ] Old credentials are revoked after migration
- [ ] CI/CD logs do not expose credentials
- [ ] MongoDB URIs are redacted from logs

### Connection

- [ ] TLS is enabled where required
- [ ] Server certificates are validated
- [ ] `authSource` is correct
- [ ] Authentication mechanism is appropriate
- [ ] Replica-set topology is configured correctly
- [ ] Connection timeouts are configured

### Network

- [ ] MongoDB is not unnecessarily public
- [ ] Application network access is restricted
- [ ] Administrative access uses a controlled path
- [ ] Kubernetes network policies are reviewed where applicable
- [ ] AWS security groups/firewalls are appropriately restricted

### Authorization

- [ ] Authentication identities have least privilege
- [ ] Database and collection access is reviewed
- [ ] Tenant authorization is enforced at the application layer
- [ ] Administrative permissions are not granted to applications
- [ ] Authentication and authorization failures are monitored

---

## Interview Considerations

### What is the difference between authentication and authorization?

Authentication establishes identity.

Authorization determines what that identity is allowed to do.

```text
Authentication → Who are you?
Authorization  → What can you do?
```

### Why should applications use dedicated MongoDB users?

To enforce least privilege and reduce blast radius if an application credential is compromised.

### What is `authSource`?

It identifies the database used to authenticate the MongoDB user. It can differ from the database containing the application's collections.

### Does authentication encrypt MongoDB traffic?

No. Authentication establishes identity. TLS protects data in transit.

### Should every API user authenticate directly to MongoDB?

Typically no. The backend service authenticates to MongoDB using its service identity, while the API separately authenticates and authorizes end users.

### Why should `MongoClient` be reused?

Because it manages connection pools and topology information. Creating clients repeatedly can cause unnecessary connections and resource consumption.

### How should MongoDB credentials be stored in Kubernetes?

Use an appropriate secret-management mechanism, preferably integrated with workload identity and external secret management where the environment requires it. Do not embed credentials in container images.

### How should credentials be rotated without downtime?

Introduce the new credential, deploy consumers using it, verify successful authentication, then revoke the old credential after all required consumers have migrated.

---

## Authentication Troubleshooting Runbook

When an application cannot authenticate:

```text
1. Confirm MongoDB is reachable.
2. Confirm DNS resolves the intended endpoint.
3. Confirm TLS negotiation succeeds.
4. Confirm username.
5. Confirm password.
6. Confirm authSource.
7. Confirm authentication mechanism.
8. Confirm the user exists.
9. Confirm the client/driver configuration.
10. Inspect MongoDB authentication logs.
11. Test the same credentials with mongosh where appropriate.
12. Compare working and failing environments.
```

Do not immediately recreate the MongoDB user.

Recreating users can hide the actual root cause and can create unnecessary privilege or credential-management problems.

---

## Production Authentication Architecture

A mature Python application should look approximately like:

```mermaid
flowchart TB
    U[API Client] --> API[FastAPI / Django]
    API --> APPAUTH[Application Authentication]
    APPAUTH --> AUTHZ[Application Authorization]
    AUTHZ --> REPO[Repository]
    REPO --> MC[Long-Lived MongoClient]

    SM[Secret Manager] --> MC
    MC --> TLS[TLS]
    TLS --> NET[Private Network]
    NET --> DB[(MongoDB Replica Set)]

    DB --> AUDIT[Authentication / Audit Logs]
    AUDIT --> MON[Security Monitoring]
```

The important boundaries are:

```text
End User
   ↓
Application Identity
   ↓
MongoDB Identity
   ↓
MongoDB Authorization
```

Each layer has a distinct responsibility.

## Key Takeaways

- **MongoDB authentication establishes database identity; it does not replace authorization, TLS, network isolation, or application-level access control.**
- **Use dedicated, least-privilege identities for applications, workers, migrations, monitoring, and administration rather than sharing an administrator account.**
- **Treat `authSource`, authentication mechanisms, TLS configuration, and credential storage as first-class production configuration concerns.**
- **Reuse a long-lived `MongoClient`, protect credentials through external secret management, and design credential rotation to cover every MongoDB consumer.**
- **Keep end-user authentication separate from MongoDB service authentication: the application authenticates users and enforces business authorization, while the service authenticates to MongoDB with its own controlled identity.**