# 08- Security and Authentication Questions

## Overview

MongoDB security is a layered system covering authentication, authorization, network controls, encryption, auditing, credential management, and operational controls.

A production MongoDB deployment should not rely on a single security mechanism:

```text
Client
  ↓
TLS
  ↓
Network Controls
  ↓
MongoDB Authentication
  ↓
Authorization
  ↓
Database / Collection
  ↓
Application-Level Validation
```

For backend engineers, the important distinction is:

- **Authentication** answers: "Who are you?"
- **Authorization** answers: "What are you allowed to do?"
- **Encryption** answers: "Can someone who obtains the traffic or storage read it?"
- **Network security** answers: "Who can reach the database?"
- **Auditing and monitoring** answer: "What happened and who performed it?"

MongoDB security should be designed together with application architecture, service ownership, Kubernetes networking, AWS infrastructure, secret management, and operational processes.

---

## MongoDB Security Model

A practical production security model has multiple layers:

| Layer | Primary control |
|---|---|
| Network | Private networking, firewall rules, security groups |
| Transport | TLS |
| Authentication | SCRAM, X.509, other supported mechanisms |
| Authorization | Roles and privileges |
| Data protection | Encryption at rest |
| Application | Input validation, authorization, safe query construction |
| Secrets | Secret manager / Kubernetes Secret |
| Auditing | Database activity and security events |
| Monitoring | Failed authentication, unusual access, configuration changes |
| Operations | Patch management, backups, incident response |

No single layer should be considered sufficient.

---

## Authentication vs Authorization

Authentication verifies identity.

Example:

```text
username = order-service
password = ********
```

MongoDB verifies whether the credentials are valid.

Authorization then determines what that identity can do:

```text
order-service
    ↓
orders database
    ↓
read/write orders
```

It should not automatically have:

```text
admin database
user administration
cluster administration
```

---

## Authentication Flow

A simplified application request looks like:

```mermaid
sequenceDiagram
    participant API as Backend API
    participant DB as MongoDB

    API->>DB: TLS connection
    API->>DB: Authentication credentials
    DB->>DB: Verify identity
    DB->>DB: Resolve roles
    DB-->>API: Authentication result
    API->>DB: Database operation
    DB->>DB: Authorization check
    DB-->>API: Result / authorization error
```

Authentication happens before MongoDB can authorize operations for that identity.

---

## MongoDB Users

MongoDB users have:

- Username.
- Authentication mechanism.
- Password or certificate credentials depending on mechanism.
- Roles.
- Authentication database.

Example:

```javascript
use admin

db.createUser({
  user: "order-service",
  pwd: passwordPrompt(),
  roles: [
    {
      role: "readWrite",
      db: "orders"
    }
  ]
})
```

The exact authentication database and deployment configuration should be consistent with the application's connection configuration.

---

## Authentication Database

MongoDB users are associated with an authentication database.

For example:

```text
User:
order-service

Authentication database:
admin

Application database:
orders
```

The user can authenticate against `admin` while having privileges on `orders`.

A connection string can therefore specify an authentication source explicitly:

```text
mongodb://order-service:<password>@mongo.example.com/orders?authSource=admin
```

Do not assume the database in the URI is automatically the authentication database.

---

## SCRAM Authentication

SCRAM is a common username/password authentication mechanism for MongoDB deployments.

Common mechanisms include:

```text
SCRAM-SHA-1
SCRAM-SHA-256
```

Modern deployments should generally prefer the strongest mechanism supported by the deployment and compatible clients.

SCRAM avoids sending the plaintext password as part of normal authentication exchange.

However, authentication should still be protected by TLS.

---

## Why TLS Is Still Required With SCRAM

A common misconception is:

> "SCRAM means TLS is unnecessary."

Authentication and transport encryption solve different problems.

```text
SCRAM
→ Authentication protocol

TLS
→ Encryption + server identity + transport integrity
```

Use TLS for production connections, especially across networks.

---

## X.509 Authentication

MongoDB can support certificate-based authentication using X.509.

The conceptual flow is:

```text
Client certificate
       ↓
TLS connection
       ↓
Certificate identity
       ↓
MongoDB authorization
```

X.509 can be useful in environments requiring certificate-based machine identity.

It introduces additional operational requirements:

- Certificate issuance.
- Certificate rotation.
- CA management.
- Revocation strategy.
- Secure private-key storage.

For large environments, certificate lifecycle management must be automated.

---

## Service Accounts

A microservice should generally use its own MongoDB identity.

Example:

```text
order-api
payment-worker
reporting-service
notification-worker
```

Instead of:

```text
application-user
```

shared across every service.

Service-specific identities provide:

- Least privilege.
- Better auditing.
- Easier credential rotation.
- Better incident investigation.
- Reduced blast radius.

---

## Least Privilege

A service should receive only the permissions required for its workload.

Example:

```text
order-api
    ↓
readWrite
    ↓
orders database
```

It should not receive:

```text
root
dbOwner on every database
cluster administration
user administration
```

unless those capabilities are genuinely required.

---

## Built-In Roles

MongoDB provides built-in roles for common privilege patterns.

Examples include:

```text
read
readWrite
dbAdmin
dbOwner
userAdmin
clusterAdmin
root
```

The important engineering question is not:

> "Which role is easiest?"

It is:

> "What is the smallest privilege set required by this workload?"

---

## Common Built-In Roles

| Role | Typical purpose |
|---|---|
| `read` | Read data |
| `readWrite` | Read and modify data |
| `dbAdmin` | Database administration |
| `dbOwner` | Broad database-level privileges |
| `userAdmin` | User/role administration |
| `clusterAdmin` | Cluster administration |
| `root` | Broad administrative privileges |

Avoid assigning `root` to application services.

---

## Custom Roles

Built-in roles may be broader than required.

MongoDB supports custom roles.

Example:

```javascript
use admin

db.createRole({
  role: "ordersApplicationRole",
  privileges: [
    {
      resource: {
        db: "orders",
        collection: "orders"
      },
      actions: [
        "find",
        "insert",
        "update"
      ]
    }
  ],
  roles: []
})
```

Then assign the role:

```javascript
db.grantRolesToUser(
  "order-service",
  [
    {
      role: "ordersApplicationRole",
      db: "admin"
    }
  ]
)
```

The exact privileges should be derived from actual application operations and tested before production rollout.

---

## Database-Level Permissions

A role can be scoped to a database:

```text
orders
customers
analytics
```

For example:

```javascript
{
  role: "readWrite",
  db: "orders"
}
```

does not automatically grant the same privilege on every database.

This is an important mechanism for reducing blast radius.

---

## Collection-Level Permissions

For stricter service isolation, privileges can target specific collections.

Example conceptual model:

```text
order-service
    ↓
orders.orders
    ├── find
    ├── insert
    └── update
```

while denying access to:

```text
orders.audit_logs
orders.payment_data
```

Collection-level privileges are useful when multiple logical workloads share a database.

---

## Authorization Model

MongoDB authorization can be viewed as:

```text
Authenticated Identity
        ↓
Assigned Roles
        ↓
Privileges
        ↓
Resource
        ↓
Allowed Action?
```

Example:

```text
order-service
     ↓
readWrite@orders
     ↓
orders.orders
     ↓
find
     ↓
ALLOW
```

---

## Application Authorization vs MongoDB Authorization

These are different layers.

Application authorization:

```text
Can this user modify order #123?
```

MongoDB authorization:

```text
Can order-api perform update operations on orders.orders?
```

The application should enforce user-level permissions.

MongoDB should enforce service/database-level permissions.

---

## Example: Multi-Tenant Application

Suppose one service handles:

```text
Tenant A
Tenant B
Tenant C
```

MongoDB authorization might enforce:

```text
order-service
    ↓
readWrite
    ↓
orders database
```

The application still needs to enforce:

```text
tenant_id == authenticated_user.tenant_id
```

MongoDB role-based authorization alone does not automatically enforce row/document-level tenant ownership.

---

## Network Security

MongoDB should generally not be directly exposed to the public internet.

Preferred architecture:

```mermaid
flowchart LR
    Internet["Internet"]
    LB["Load Balancer / API Gateway"]
    API["Backend Service"]
    DB["Private MongoDB"]

    Internet --> LB
    LB --> API
    API --> DB
```

Avoid:

```text
Internet
   ↓
Public MongoDB port
```

unless there is a specific, carefully controlled architecture requiring it.

---

## AWS Network Security

In AWS, a common design is:

```text
Public / Private Application Tier
          ↓
      VPC Network
          ↓
Private MongoDB / Atlas Private Connectivity
```

Use appropriate:

- VPC security groups.
- Private subnets.
- Network ACLs where required.
- Private DNS.
- VPC peering or PrivateLink-style connectivity where supported.
- Restricted ingress rules.

The database should only be reachable from trusted application networks.

---

## Kubernetes Network Security

For Kubernetes workloads:

```text
Pod
 ↓
Kubernetes NetworkPolicy
 ↓
VPC / node networking
 ↓
MongoDB
```

NetworkPolicy can reduce which workloads are allowed to communicate with MongoDB.

Do not rely solely on Kubernetes networking controls; MongoDB authentication and authorization should remain enabled.

---

## Bind Address and Exposure

A MongoDB server's network configuration controls which interfaces accept connections.

Development environments may use:

```yaml
net:
  bindIp: 127.0.0.1
```

Production deployments require carefully designed network exposure.

Avoid casually changing:

```text
127.0.0.1
```

to:

```text
0.0.0.0
```

without simultaneously implementing authentication, firewall restrictions, and TLS.

---

## TLS

TLS protects MongoDB network traffic against:

- Eavesdropping.
- Traffic modification.
- Unauthorized interception.

Production traffic should use TLS for:

```text
Application → MongoDB
MongoDB → MongoDB
Administrative connections
```

where applicable to the deployment architecture.

---

## TLS Server Validation

Clients should validate the MongoDB server certificate.

In Python, a TLS-enabled client configuration can look like:

```python
from pymongo import MongoClient

client = MongoClient(
    "mongodb://order-service:password@mongo.example.com/orders",
    tls=True,
    tlsCAFile="/etc/ssl/certs/mongodb-ca.pem",
    serverSelectionTimeoutMS=5_000,
)
```

Do not disable certificate verification merely to solve a development certificate problem.

Avoid patterns equivalent to:

```python
tlsAllowInvalidCertificates=True
```

in production.

---

## TLS Certificate Rotation

Certificates expire.

Production operations should define:

```text
Certificate issuance
       ↓
Secure distribution
       ↓
Application reload
       ↓
Validation
       ↓
Old certificate retirement
```

For Kubernetes, certificates can be managed through the organization's certificate-management tooling and mounted securely into workloads.

---

## Encryption at Rest

Encryption at rest protects stored database files and backups from unauthorized access to underlying storage.

It addresses a different threat from TLS:

```text
TLS
→ protects data in transit

Encryption at rest
→ protects stored data
```

Managed MongoDB platforms commonly provide storage encryption, while self-managed deployments require explicit infrastructure and MongoDB configuration decisions.

---

## Client-Side Field-Level Encryption

For highly sensitive fields, application-level or client-side encryption can provide stronger isolation.

Conceptually:

```text
Application
   ↓
Encrypt sensitive field
   ↓
MongoDB
   ↓
Encrypted value
```

MongoDB stores ciphertext rather than the plaintext value for protected fields.

This is different from encryption at rest, where the database/storage layer protects the underlying storage.

---

## When to Consider Field-Level Encryption

Potential use cases include:

- Highly sensitive personal data.
- Financial information.
- Regulated information.
- Data where database administrators should not have direct plaintext access.

Trade-offs include:

- More complex key management.
- Query limitations depending on encryption mode and field.
- Application complexity.
- Key rotation requirements.
- Operational overhead.

Do not encrypt every field without a threat-model-driven reason.

---

## Secret Management

Never hard-code MongoDB credentials:

```python
MONGO_URI = "mongodb://admin:SuperSecretPassword@mongo:27017"
```

Use environment variables or, preferably, a managed secret mechanism.

Example:

```python
import os

MONGO_URI = os.environ["MONGO_URI"]
```

For production:

```text
AWS Secrets Manager
        ↓
Deployment system
        ↓
Kubernetes Secret / runtime configuration
        ↓
Application
```

The exact mechanism should match the organization's security architecture.

---

## Kubernetes Secrets

A Kubernetes deployment can consume a MongoDB connection string through a Secret:

```yaml
env:
  - name: MONGO_URI
    valueFrom:
      secretKeyRef:
        name: mongodb-credentials
        key: uri
```

Do not commit the actual secret to Git.

Remember that Kubernetes Secrets are not automatically equivalent to a full external secret-management solution. Apply appropriate encryption-at-rest and RBAC controls to the cluster.

---

## AWS Secrets Manager

A production application can retrieve credentials from AWS Secrets Manager.

Conceptually:

```text
AWS Secrets Manager
        ↓
IAM workload identity
        ↓
Application
        ↓
MongoDB
```

This avoids embedding long-lived credentials directly in deployment manifests.

Where possible, prefer workload identity mechanisms over static cloud credentials.

---

## Credential Rotation

A production credential lifecycle should look like:

```text
Create credential
      ↓
Store securely
      ↓
Deploy
      ↓
Monitor
      ↓
Rotate
      ↓
Validate new credential
      ↓
Retire old credential
```

Applications should be designed so credentials can be rotated without unnecessary downtime.

---

## Shared Credentials Are a Security Risk

Bad architecture:

```text
service-a ──┐
service-b ──┼──> shared-mongodb-user
worker   ───┘
```

If that credential leaks, all workloads are affected.

Prefer:

```text
service-a → mongo-user-a
service-b → mongo-user-b
worker    → mongo-user-worker
```

Each identity should have the smallest required privileges.

---

## Password Rotation

Passwords should be:

- Strong.
- Randomly generated.
- Stored in a secret manager.
- Rotated periodically according to organizational policy.
- Removed from source control.
- Removed from logs.

Do not print MongoDB URIs into logs because connection strings can contain credentials.

---

## Connection String Security

Avoid logging:

```text
mongodb://user:password@host/db
```

Instead, sanitize:

```python
def sanitize_mongo_uri(uri: str) -> str:
    return uri.split("@")[-1]
```

In production logging, prefer structured metadata such as:

```json
{
  "database_host": "mongo.internal",
  "database_name": "orders"
}
```

rather than logging credentials.

---

## Authentication Failure Monitoring

Monitor:

- Failed login attempts.
- Authentication failures by user.
- Repeated failures from a source.
- Unknown users.
- Privilege errors.
- Unexpected administrative operations.

A sudden spike may indicate:

```text
Credential rotation problem
Misconfiguration
Expired credential
Brute-force attempt
Compromised workload
```

---

## Auditing

MongoDB auditing can provide visibility into security-relevant operations depending on deployment edition and configuration.

Useful events include:

- Authentication activity.
- Authorization failures.
- User creation.
- Role changes.
- Database administration.
- Configuration changes.
- Data access activity where configured.

Audit logs should be protected from modification by ordinary application identities.

---

## Audit Log Architecture

A production architecture can look like:

```mermaid
flowchart LR
    Mongo["MongoDB"]
    Audit["Audit Logs"]
    Collector["Log Collector"]
    SIEM["SIEM / Security Platform"]

    Mongo --> Audit
    Audit --> Collector
    Collector --> SIEM
```

Audit retention should align with organizational and regulatory requirements.

---

## Security Monitoring

Security monitoring should combine:

```text
Authentication events
+
Authorization failures
+
Network activity
+
Audit logs
+
Application logs
+
Infrastructure alerts
```

A database security incident rarely appears as one isolated signal.

---

## MongoDB Security and Application Logs

Avoid leaking:

```text
Passwords
Connection strings
Access tokens
Encryption keys
Sensitive documents
```

into application logs.

For errors:

```python
except Exception:
    logger.exception(
        "MongoDB operation failed",
        extra={
            "collection": "orders",
            "operation": "update",
        },
    )
    raise
```

Log enough context for diagnosis without exposing secrets or sensitive document contents.

---

## MongoDB Security and Backups

Backups contain database data and must be treated as sensitive assets.

A secure backup strategy includes:

```text
Encrypted backup
       ↓
Restricted access
       ↓
Retention policy
       ↓
Integrity verification
       ↓
Restore testing
```

A secure production database with insecure backups is still a security problem.

---

## Backup Access Control

The identity performing backups should not automatically have unrestricted administrative access to the production database.

Use dedicated operational identities where practical.

Apply:

- Least privilege.
- Separate credentials.
- Strong authentication.
- Encryption.
- Audit logging.

---

## Security and Disaster Recovery

During disaster recovery, restore:

```text
Data
+
Indexes
+
Users
+
Roles
+
TLS configuration
+
Network controls
+
Application secrets
+
Audit configuration
```

A recovery plan that restores only data may produce a functional but insecure environment.

---

## MongoDB Security in Docker

A local development environment may use:

```yaml
services:
  mongodb:
    image: mongo:latest
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
```

For production:

- Pin tested image versions.
- Do not use development credentials.
- Do not publish MongoDB publicly.
- Use secure secrets.
- Enable authentication.
- Configure TLS where required.
- Restrict network access.
- Scan images.
- Apply security updates.

---

## Docker Security Mistake

Avoid:

```yaml
ports:
  - "27017:27017"
```

on a production host without a specific reason and network restrictions.

Publishing a database port makes it reachable from networks allowed by the host firewall.

Prefer private networking whenever possible.

---

## MongoDB Atlas Security

For managed MongoDB deployments, security commonly involves:

```text
Database Users
+
Network Access Controls
+
TLS
+
Encryption at Rest
+
Private Connectivity
+
Auditing / Monitoring
+
Secret Management
```

Do not treat a managed database as automatically secure simply because the infrastructure is managed.

Application-level authorization and credential hygiene remain necessary.

---

## MongoDB Security Architecture

A production architecture can look like:

```mermaid
flowchart TB
    Client["External Client"]
    Gateway["Nginx / API Gateway"]
    API["FastAPI / Django Service"]
    Secret["Secret Manager"]
    Network["Private Network / Security Groups"]
    Mongo["MongoDB / Atlas"]
    Audit["Audit / Security Monitoring"]

    Client --> Gateway
    Gateway --> API
    API --> Network
    Network --> Mongo
    Secret --> API
    Mongo --> Audit
    API --> Audit
```

The database is not directly exposed to external clients.

---

## Python Authentication Configuration

Use a secure connection configuration:

```python
from pymongo import MongoClient

client = MongoClient(
    "mongodb://order-service:password@mongo.internal:27017/orders?authSource=admin",
    tls=True,
    tlsCAFile="/etc/ssl/certs/mongodb-ca.pem",
    serverSelectionTimeoutMS=5_000,
    connectTimeoutMS=5_000,
    retryWrites=True,
)
```

Production configuration should come from a secret-management system rather than source code.

---

## PyMongo Error Handling

Authentication failures should be handled separately from ordinary query failures.

```python
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError

try:
    client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=5_000,
    )
    client.admin.command("ping")
except OperationFailure as exc:
    logger.error("MongoDB authentication or authorization failure")
    raise
except ServerSelectionTimeoutError:
    logger.error("MongoDB server selection timed out")
    raise
```

Do not blindly retry authentication failures indefinitely.

---

## FastAPI Security Architecture

A typical FastAPI application should have:

```text
HTTP Authentication
       ↓
Application Authorization
       ↓
Service Layer
       ↓
Repository
       ↓
MongoDB Service Identity
       ↓
MongoDB Authorization
```

The authenticated end user and MongoDB service account are different identities.

---

## Django Security Architecture

For Django:

```text
Django Authentication
       ↓
Permission Checks
       ↓
Service Layer
       ↓
Repository / PyMongo
       ↓
MongoDB Service Identity
```

Do not grant MongoDB administrative privileges merely because Django administrators exist.

Application administrators are not automatically database administrators.

---

## MongoDB and gRPC

In a microservice environment:

```text
Service A
   ↓ gRPC
Service B
   ↓
MongoDB
```

Service B should own the MongoDB credentials and data-access policy.

Service A should not normally receive Service B's database credentials.

This keeps the database behind the owning service boundary.

---

## MongoDB and Kafka

A common event-driven architecture is:

```text
MongoDB
   ↓
Change Stream
   ↓
Consumer
   ↓
Kafka
   ↓
Other Services
```

Security must cover every boundary:

```text
MongoDB authentication
Kafka authentication
TLS
Consumer authorization
Secret management
```

Do not assume that securing MongoDB automatically secures the event pipeline.

---

## MongoDB and Redis

Redis should not be used as a security bypass around MongoDB.

For example:

```text
MongoDB authorization
     ≠
Redis authorization
```

If sensitive MongoDB data is cached in Redis, apply equivalent security controls to the cache:

- Authentication.
- TLS where required.
- Network isolation.
- Least privilege.
- Encryption at rest where supported.
- Sensitive-data minimization.

---

## Common Security Mistakes

| Mistake | Risk | Better approach |
|---|---|---|
| Public MongoDB port | Unauthorized access attempts | Private networking |
| Shared DB user | Large blast radius | Service-specific users |
| `root` for application | Excessive privileges | Least privilege |
| Credentials in Git | Credential compromise | Secret manager |
| TLS disabled in production | Traffic exposure | TLS with certificate validation |
| TLS verification disabled | MITM risk | Validate certificates |
| Secrets in logs | Credential leakage | Structured sanitized logs |
| No backup encryption | Data exposure | Encrypt backups |
| No audit monitoring | Poor incident visibility | Centralized audit/security monitoring |
| App-only authorization | Direct DB misuse | DB + app authorization |
| No credential rotation | Long-lived compromise | Automated rotation |
| Publicly accessible Atlas/database | Expanded attack surface | Network restrictions/private connectivity |

---

## Interview Question: What Is the Difference Between Authentication and Authorization?

A strong answer:

> Authentication verifies the identity of a MongoDB client. Authorization determines what that authenticated identity is allowed to do based on roles and privileges.

Example:

```text
Authentication:
order-service is valid

Authorization:
order-service may read/write orders.orders
```

---

## Interview Question: How Would You Secure MongoDB in Production?

A strong senior-level answer should cover multiple layers:

```text
Private network
      +
TLS
      +
Authentication
      +
Least-privilege authorization
      +
Service-specific identities
      +
Secret management
      +
Encryption at rest
      +
Auditing
      +
Monitoring
      +
Secure backups
```

The key is defense in depth rather than a single configuration switch.

---

## Interview Question: Why Should Application Services Not Use `root`?

Because `root` provides extremely broad privileges.

If an application credential is compromised:

```text
root credential leaked
       ↓
potential access to many databases
       ↓
administrative operations
       ↓
large blast radius
```

A narrowly scoped service account limits the potential impact.

---

## Interview Question: Why Is TLS Needed If SCRAM Is Enabled?

SCRAM authenticates the client.

TLS protects the communication channel and provides server certificate validation.

Therefore:

```text
SCRAM + TLS
```

provides substantially stronger transport security than treating authentication alone as transport protection.

---

## Interview Question: How Do You Secure MongoDB Credentials in Kubernetes?

A strong answer includes:

1. Store credentials in an approved secret-management system.
2. Inject them into the workload securely.
3. Do not commit secrets to Git.
4. Restrict Kubernetes RBAC access to secrets.
5. Rotate credentials.
6. Avoid logging connection strings.
7. Use MongoDB TLS.
8. Use a separate MongoDB identity per workload where practical.

---

## Interview Question: How Do You Secure a Multi-Tenant MongoDB Application?

Use multiple layers:

```text
Network isolation
        ↓
MongoDB service authentication
        ↓
Least-privilege database role
        ↓
Application authorization
        ↓
tenant_id filtering
        ↓
Schema validation
        ↓
Audit / monitoring
```

MongoDB roles generally provide service-level authorization; tenant-level authorization usually belongs in the application/domain layer unless a more specialized architecture is used.

---

## Interview Scenario: MongoDB Is Suddenly Receiving Thousands of Authentication Failures

Investigate:

```text
Authentication logs
        ↓
Source addresses
        ↓
MongoDB usernames
        ↓
Recent deployments
        ↓
Credential rotation
        ↓
Network exposure
```

Possible causes include:

- Expired credentials.
- Incorrect secret deployment.
- Application retry loop.
- Brute-force activity.
- Compromised credentials.
- Incorrect connection configuration.

Do not immediately disable authentication to "restore service."

---

## Interview Scenario: A Developer Requests `root` Access

Evaluate the actual requirement:

```text
What operation is required?
        ↓
Which database?
        ↓
Which collection?
        ↓
Which MongoDB actions?
```

Create or use the smallest role capable of performing the required operation.

Administrative access should be separately controlled from application access.

---

## Interview Scenario: MongoDB Is Accessible From the Internet

Treat this as a security incident or high-priority exposure until proven otherwise.

Investigate:

```text
Network exposure
       ↓
Authentication status
       ↓
TLS configuration
       ↓
User accounts
       ↓
Audit logs
       ↓
Access history
```

Then:

- Restrict network access.
- Rotate potentially exposed credentials.
- Review audit logs.
- Validate user roles.
- Investigate unauthorized access.
- Document the incident.
- Add preventive controls.

---

## Security Troubleshooting Methodology

### Symptom

```text
Application cannot authenticate to MongoDB.
```

### Possible Causes

- Wrong username.
- Wrong password.
- Incorrect `authSource`.
- User does not exist.
- User lacks required role.
- TLS certificate failure.
- Network connectivity problem.
- Secret rotation mismatch.

### Isolation Strategy

Separate the problem into:

```text
Network
  ↓
TLS
  ↓
Authentication
  ↓
Authorization
  ↓
Application query
```

### Diagnostic Commands

Test connectivity:

```bash
mongosh "mongodb://order-service@mongo.internal:27017/orders?authSource=admin"
```

Check server selection from Python:

```python
client.admin.command("ping")
```

Check authenticated identity where appropriate:

```javascript
db.runCommand({
  connectionStatus: 1
})
```

### Root Cause

Determine whether failure occurs at:

```text
TCP connection
TLS handshake
Authentication
Authorization
Query execution
```

### Corrective Action

Apply the smallest required correction:

- Fix secret.
- Fix `authSource`.
- Grant required role.
- Correct certificate configuration.
- Restrict or permit network access appropriately.

### Prevention

Use:

- Automated configuration validation.
- Secret rotation testing.
- TLS monitoring.
- Least-privilege role definitions.
- Authentication monitoring.
- Production smoke tests.

---

## Authorization Troubleshooting

### Symptom

```text
Authentication succeeds but an operation returns "not authorized".
```

### Possible Causes

- Missing role.
- Wrong database.
- Wrong collection.
- Incorrect custom privilege.
- Authentication source confusion.
- Application using a different identity than expected.

### Isolation Strategy

Verify:

```text
Authenticated username
        ↓
Assigned roles
        ↓
Role database
        ↓
Target database
        ↓
Target collection
        ↓
Required action
```

### Corrective Action

Grant only the missing privilege.

Avoid solving an authorization problem with:

```text
grant root
```

---

## TLS Troubleshooting

### Symptom

```text
TLS connection fails.
```

### Possible Causes

- Expired certificate.
- Wrong CA.
- Hostname mismatch.
- Missing CA file.
- Unsupported TLS configuration.
- Certificate rotation mismatch.

### Isolation Strategy

Check:

```text
Certificate validity
       ↓
CA chain
       ↓
Hostname
       ↓
Client configuration
       ↓
Server configuration
```

### Prevention

Monitor certificate expiration and automate certificate rotation.

---

## Security Incident Response

If credentials may have leaked:

```text
Identify exposure
      ↓
Restrict access
      ↓
Rotate credentials
      ↓
Review audit logs
      ↓
Assess affected resources
      ↓
Restore least privilege
      ↓
Verify application
      ↓
Document incident
```

Do not simply change the password and assume the incident is resolved.

Investigate whether the compromised identity was actually used.

---

## Production Security Checklist

### Authentication

- Use authenticated connections.
- Use modern supported authentication mechanisms.
- Use separate service identities.
- Rotate credentials.
- Avoid shared application credentials.

### Authorization

- Apply least privilege.
- Avoid `root` for applications.
- Scope permissions by database or collection.
- Review custom roles.
- Separate application and administrative identities.

### Network

- Keep MongoDB private.
- Restrict inbound traffic.
- Use security groups/firewalls.
- Use Kubernetes NetworkPolicies where applicable.
- Prefer private connectivity for managed deployments.

### Transport

- Enable TLS.
- Validate server certificates.
- Monitor certificate expiration.
- Automate certificate rotation.

### Secrets

- Use AWS Secrets Manager, Kubernetes-integrated secret management, or an equivalent approved system.
- Never commit credentials to Git.
- Never log connection strings.
- Rotate secrets.

### Data

- Encrypt storage and backups.
- Consider field-level encryption for highly sensitive data.
- Restrict backup access.
- Test restore procedures.

### Monitoring

- Monitor authentication failures.
- Monitor authorization failures.
- Collect audit logs where required.
- Alert on unexpected administrative activity.
- Centralize security events.

---

## Senior-Level Security Checklist

Before approving a MongoDB production architecture, ask:

- Is MongoDB reachable from the public internet?
- Which identities can authenticate?
- Which services use each identity?
- What is the minimum role required?
- Is TLS enforced?
- How are certificates rotated?
- Where are credentials stored?
- How are credentials rotated?
- Are credentials present in logs?
- Are backups encrypted?
- Who can restore backups?
- Who can administer users and roles?
- Are audit events collected?
- How are authentication failures detected?
- What is the blast radius of one compromised service account?
- Can credentials be revoked without application redesign?
- How is MongoDB access controlled from Kubernetes?
- How is MongoDB access controlled from AWS?
- How are security incidents investigated?

---

## Key Takeaways

- **MongoDB security is defense in depth**: private networking, TLS, authentication, authorization, encryption, secret management, auditing, monitoring, and secure backups must work together.
- **Authentication and authorization are separate controls**; production services should use dedicated identities with the minimum database and collection privileges they require.
- **Never expose MongoDB unnecessarily or use `root` credentials in application workloads**; minimize network exposure and blast radius.
- **Treat credentials, TLS certificates, backups, and audit logs as security-sensitive assets** with controlled storage, rotation, access, monitoring, and recovery procedures.
- **Senior MongoDB security design extends beyond database configuration** into FastAPI/Django authorization, Kubernetes networking, AWS IAM and networking, microservice ownership, incident response, and operational governance.