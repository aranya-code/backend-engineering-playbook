# 17- Secrets and Credential Management

## Overview

Secrets and credentials are authentication material that grants access to systems, data, or privileged operations.

Typical examples include:

- Database passwords
- API keys
- OAuth client secrets
- Access tokens
- Refresh tokens
- TLS private keys
- Encryption keys
- Cloud credentials
- Webhook signing secrets
- SSH keys
- Service-account credentials

For backend systems, credential management is not simply a matter of storing passwords securely. It covers the complete lifecycle:

```text
Generate
   ↓
Store
   ↓
Distribute
   ↓
Use
   ↓
Rotate
   ↓
Revoke
   ↓
Audit
   ↓
Delete
```

A production system should minimize both:

```text
Who can obtain a credential
```

and:

```text
How long the credential remains useful
```

The central principle is:

> Secrets should be centrally managed, minimally exposed, short-lived where practical, and rotated without unnecessary downtime.

---

## Secrets vs Credentials

The terms are related but not identical.

| Concept | Meaning | Example |
|---|---|---|
| Secret | Sensitive value that must remain confidential | Encryption key |
| Credential | Information used to authenticate | Username + password |
| Token | Credential representing authorization or identity | OAuth access token |
| API key | Static credential identifying/authorizing a caller | Third-party API key |
| Certificate | Identity credential based on public-key cryptography | mTLS client certificate |
| Private key | Secret cryptographic key | TLS private key |

A single system may use several of these simultaneously.

---

## Why Credential Management Matters

A leaked database password can provide direct access to production data.

A leaked AWS credential may provide access to:

```text
S3
RDS
Secrets Manager
KMS
CloudWatch
EC2
IAM
```

depending on its permissions.

A leaked JWT signing key can potentially allow forged tokens.

A leaked webhook secret can allow unauthorized event generation.

Therefore:

```text
Credential compromise
        ↓
Potential privilege escalation
        ↓
Data access
        ↓
System compromise
```

The impact depends heavily on the credential's permissions.

---

## Credential Lifecycle

A mature credential lifecycle looks like:

```mermaid
stateDiagram-v2
    [*] --> Generated
    Generated --> Stored
    Stored --> Distributed
    Distributed --> Active
    Active --> Rotating
    Rotating --> Active
    Active --> Revoked
    Revoked --> Deleted
    Deleted --> [*]
```

Every credential should have:

- Owner
- Purpose
- Scope
- Expiration or rotation policy
- Storage location
- Consumers
- Revocation mechanism
- Audit trail

---

## Credential Classification

Not every secret has the same risk.

| Credential | Typical risk | Recommended approach |
|---|---|---|
| Local development secret | Medium | Local secret store/environment |
| Production DB password | High | Secret manager |
| AWS workload credential | High | Workload identity |
| TLS private key | High | Managed certificate/secret store |
| Encryption key | Critical | KMS/HSM/key-management system |
| Temporary access token | Lower duration | Short TTL |
| CI/CD deployment credential | High | OIDC/short-lived identity |

Risk should influence:

```text
Storage
Access control
Expiration
Rotation
Auditing
```

---

## Static vs Short-Lived Credentials

### Static Credential

```text
Password
    ↓
Stored
    ↓
Used repeatedly
    ↓
Rotated periodically
```

Examples:

- Database passwords
- API keys
- Long-lived access keys

### Short-Lived Credential

```text
Request identity
    ↓
Credential issued
    ↓
Used for limited period
    ↓
Expires
```

Short-lived credentials reduce the usefulness of stolen credentials.

Prefer them where the platform supports them.

---

## Machine Identity

Modern cloud systems should prefer workload identity over long-lived credentials.

Instead of:

```text
Application
    ↓
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

prefer:

```text
Application
    ↓
Workload identity
    ↓
Cloud IAM
    ↓
Temporary credentials
```

This eliminates many static-secret distribution problems.

---

## AWS IAM Roles

For workloads running on AWS, IAM roles are generally preferable to embedding long-lived AWS access keys.

Conceptually:

```text
ECS / EKS / EC2 workload
        ↓
IAM role
        ↓
Temporary credentials
        ↓
AWS API
```

Permissions should still follow least privilege.

Identity-based authentication does not eliminate authorization requirements.

---

## Kubernetes Workload Identity

Kubernetes workloads can use cloud workload identity mechanisms instead of storing long-lived cloud credentials in Kubernetes Secrets.

Architecture:

```text
Pod
 ↓
Service Account Identity
 ↓
Cloud IAM
 ↓
Temporary Credentials
 ↓
AWS Service
```

For AWS EKS, mechanisms such as IAM Roles for Service Accounts and EKS Pod Identity can be used depending on the deployment model.

---

## Database Credentials

Applications should use dedicated database credentials.

For example:

```text
app_runtime
    ↓
Application queries

app_migration
    ↓
Schema changes

app_reporting
    ↓
Read-only reporting
```

Do not use:

```text
postgres superuser
```

for normal application traffic.

---

## Database Credential Storage

A production architecture commonly looks like:

```text
Application
    ↓
Secret Manager
    ↓
Database credential
    ↓
Connection pool
    ↓
PostgreSQL
```

The secret should not normally be committed to:

```text
Git
Docker image
Application source
Terraform state without appropriate protection
Public CI logs
```

---

## Secret Managers

Common options include:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- Kubernetes Secrets with appropriate controls
- HashiCorp Vault
- Cloud-provider secret-management services

A secret manager typically provides:

- Centralized storage
- Access control
- Encryption
- Auditing
- Rotation integration
- Versioning
- Controlled retrieval

---

## AWS Secrets Manager

AWS Secrets Manager is useful for storing application credentials and other secrets.

Typical flow:

```text
Application
    ↓
IAM authorization
    ↓
AWS Secrets Manager
    ↓
Secret value
    ↓
PostgreSQL / External API
```

The application should have permission to retrieve only the secrets it actually needs.

---

## Parameter Store vs Secrets Manager

A simplified comparison:

| Capability | Parameter Store | Secrets Manager |
|---|---|---|
| Configuration storage | Strong | Strong |
| Secret storage | Yes | Yes |
| Automatic rotation integrations | More limited | Stronger |
| Secret lifecycle features | Good | Strong |
| Typical use | Configuration + parameters | Credentials + secrets |

The exact feature set depends on the service tier and integration.

Do not treat every configuration value as a secret.

---

## Configuration vs Secret

Example:

```text
LOG_LEVEL=INFO
```

is configuration.

```text
DATABASE_PASSWORD=...
```

is a secret.

Similarly:

```text
DATABASE_HOST=db.internal
```

may not itself be secret, while:

```text
DATABASE_PASSWORD=...
```

is.

Separating these concepts improves operational clarity.

---

## Environment Variables

Environment variables are commonly used to inject configuration and secrets at runtime.

Example:

```python
import os

database_url = os.environ["DATABASE_URL"]
```

This is preferable to hard-coding a credential in source code.

However, environment variables are **not inherently secure**.

They can potentially be exposed through:

- Process inspection
- Debugging
- Crash dumps
- Misconfigured logging
- Container metadata
- Deployment tooling

For high-sensitivity secrets, use a proper secret-management architecture.

---

## Secret Injection

A typical deployment flow is:

```text
Secret Manager
      ↓
Deployment platform
      ↓
Application runtime
      ↓
Secret available to process
```

The application should retrieve only what it needs.

Avoid copying the entire secret store into every service.

---

## Secret Exposure Surface

A secret can leak through more locations than source code.

```mermaid
flowchart TB
    SM[Secret Manager] --> App[Application]
    App --> Logs[Logs]
    App --> Trace[Tracing]
    App --> Error[Error Tracking]
    App --> Dump[Crash Dump]
    App --> Image[Container Image]
    App --> CI[CI/CD]
```

The objective is to prevent accidental propagation.

---

## Source Control

Never commit production secrets.

Dangerous examples include:

```text
.env
credentials.json
aws-credentials
private.key
database-password.txt
```

Use `.gitignore` for local secret files, but do not rely on `.gitignore` as the primary security control.

If a secret has already been committed:

```text
Remove file
    +
Revoke credential
    +
Rotate credential
    +
Investigate exposure
```

Deleting the file in a later commit does not invalidate the secret.

---

## Secret Scanning

CI/CD should scan repositories for accidentally committed secrets.

Useful controls include:

```text
Developer commit
    ↓
Secret scanning
    ↓
Pull request checks
    ↓
CI validation
```

Secret scanning is a detection mechanism, not a replacement for proper secret management.

---

## Secret Rotation

Rotation replaces an active credential with a new credential.

For example:

```text
Password A
    ↓
Create Password B
    ↓
Deploy application using B
    ↓
Validate
    ↓
Revoke Password A
```

A production rotation strategy should avoid unnecessary downtime.

---

## Zero-Downtime Rotation

For credentials that support multiple valid versions:

```text
Credential A active
       ↓
Credential B created
       ↓
Application accepts B
       ↓
All instances migrated
       ↓
Credential A revoked
```

This is safer than:

```text
Revoke A
   ↓
Deploy B
```

which can create an outage.

---

## Database Password Rotation

Database password rotation can be challenging with connection pools.

Example:

```text
Secret Manager
     ↓
New DB password
     ↓
Application instances reload
     ↓
New connections use new password
     ↓
Old pooled connections drain
     ↓
Old password revoked
```

The application should be designed to handle connection recreation during rotation.

---

## Connection Pools and Secret Rotation

Persistent database connections may continue using credentials established before rotation.

Therefore:

```text
Password rotated
```

does not necessarily mean:

```text
Every existing TCP connection immediately fails
```

The exact behavior depends on the authentication mechanism and connection lifecycle.

Pool recycling and controlled deployment can help ensure connections eventually use the new credential.

---

## Application Restart vs Dynamic Secret Reload

Two common strategies exist.

### Restart-Based

```text
Rotate secret
    ↓
Restart / redeploy application
    ↓
New secret loaded
```

Simple and predictable.

### Dynamic Reload

```text
Rotate secret
    ↓
Application detects new version
    ↓
Reloads credential
    ↓
New connections use new secret
```

More flexible but operationally more complex.

Choose based on availability requirements.

---

## Secret Versioning

Secret managers commonly support multiple versions.

A conceptual lifecycle is:

```text
Version 1 → Previous
Version 2 → Current
```

Versioning helps with:

- Rotation
- Rollback
- Staged deployments
- Auditing

Do not leave obsolete credentials active indefinitely simply because previous versions exist.

---

## Secret Revocation

Rotation and revocation are related but different.

### Rotation

```text
Old credential
    ↓
New credential
```

### Revocation

```text
Credential
    ↓
No longer valid
```

Revocation is critical during incidents.

Examples:

```text
Compromised API key → Revoke
Compromised AWS credential → Disable/revoke
Leaked DB password → Rotate/revoke
Compromised certificate → Revoke/replace according to PKI process
```

---

## Credential Scope

Credentials should have the smallest possible permissions.

Example:

```text
Order Service
    ↓
Can read/write orders
```

rather than:

```text
Order Service
    ↓
Can administer entire PostgreSQL database
```

This is the principle of least privilege applied to credentials.

---

## Service-Specific Credentials

In a microservice architecture:

```text
Order Service
    ↓
order_db_user

Payment Service
    ↓
payment_db_user

Reporting Service
    ↓
reporting_db_user
```

This limits cross-service access.

If one credential is compromised, unrelated systems remain better protected.

---

## Shared Credentials

Avoid:

```text
10 services
   ↓
one database password
```

because:

- Rotation becomes harder
- Attribution becomes difficult
- Compromise affects many services
- Least privilege becomes difficult

Prefer service-specific identities wherever practical.

---

## Database Role Ownership

Do not make the runtime database user the owner of every object unless there is a deliberate reason.

A safer separation is:

```text
app_owner
    ↓
Owns database objects

app_runtime
    ↓
Uses required privileges

app_migration
    ↓
Performs schema changes
```

This reduces the consequences of application compromise.

---

## API Keys

Third-party APIs frequently use API keys.

A production API-key architecture is:

```text
Application
    ↓
Secret Manager
    ↓
API key
    ↓
HTTPS
    ↓
Third-party API
```

The key should not appear in:

- Source code
- Logs
- URLs
- Error messages
- Client-side JavaScript unless intentionally public

---

## API Keys in URLs

Avoid:

```text
https://api.example.com/data?api_key=secret
```

URLs can be captured by:

- Reverse-proxy logs
- Browser history
- Monitoring systems
- Referrer headers
- APM systems

Prefer authenticated headers when supported.

---

## OAuth Client Secrets

OAuth applications may use:

```text
client_id
client_secret
```

The `client_id` is often not secret.

The `client_secret` is.

Never expose a confidential OAuth client secret in browser or mobile application code where it cannot be kept confidential.

---

## JWT Signing Keys

JWT signing keys require particularly strong protection.

For symmetric signing:

```text
Secret key
    ↓
Sign JWT
```

Anyone who obtains the signing secret may potentially create valid tokens.

For asymmetric signing:

```text
Private key
    ↓
Sign JWT

Public key
    ↓
Verify JWT
```

The private signing key must remain tightly controlled.

---

## Private Keys

TLS and signing private keys are high-value secrets.

Protect them with:

- Restricted permissions
- Secret managers
- KMS/HSM where appropriate
- Managed certificate services
- Controlled deployment mechanisms

Never store private keys in public repositories.

---

## Encryption Keys vs Secrets

Encryption keys often require stronger lifecycle controls than ordinary application credentials.

For example:

```text
Database password
    ↓
Secret Manager

Encryption key
    ↓
KMS / HSM / Dedicated key-management system
```

Do not treat a high-value encryption key as an ordinary `.env` variable without a strong justification.

---

## Secret Access Authorization

Secret access should itself be authorized.

For example:

```text
Order Service
    ↓ IAM
orders/database
```

but:

```text
Order Service
    ✗
payments/database
```

The secret manager becomes another authorization boundary.

---

## Secret Naming

Use predictable, non-sensitive names.

For example:

```text
production/orders/database
production/orders/payment-api
production/reporting/database
```

Do not embed secret values into secret names.

Names should identify:

```text
Environment
Service
Purpose
```

---

## Environment Separation

Production and non-production secrets should be separate.

Avoid:

```text
development
    ↓
same database credential
    ↓
production
```

Prefer:

```text
Development → Development credentials
Staging    → Staging credentials
Production → Production credentials
```

A staging compromise should not automatically provide production access.

---

## CI/CD Credentials

CI/CD systems frequently require access to:

```text
Cloud
Container registry
Kubernetes
Database migrations
Secret manager
```

Long-lived credentials should be avoided when short-lived workload identity is available.

For AWS deployments, OIDC-based federation can allow CI systems to obtain temporary AWS credentials without storing long-lived AWS access keys.

---

## GitHub Actions Example

A conceptual secure architecture is:

```text
GitHub Actions
      ↓ OIDC
AWS IAM role
      ↓
Temporary credentials
      ↓
AWS services
```

This is preferable to storing a permanent AWS access key and secret in repository secrets when the deployment platform supports this model.

---

## Docker Secrets

Avoid baking secrets into Docker images.

Dangerous:

```dockerfile
ENV DATABASE_PASSWORD=production-secret
```

The secret can become part of image configuration or build history.

Prefer runtime injection:

```text
Image
  ↓
No production secrets

Runtime
  ↓
Secret injection
```

---

## Kubernetes Secrets

Kubernetes Secrets provide a Kubernetes API abstraction for sensitive configuration.

Example:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
type: Opaque
stringData:
  username: app_runtime
  password: example
```

This example is suitable for illustrating the API shape, but production secret values should not normally be committed directly to Git.

Kubernetes Secret objects require appropriate RBAC and storage protection.

---

## Kubernetes External Secret Pattern

A stronger production pattern is:

```text
AWS Secrets Manager
        ↓
External secret integration
        ↓
Kubernetes
        ↓
Pod
```

This keeps the authoritative secret in a dedicated secret-management system.

The exact integration can vary by platform and tooling.

---

## Secret Injection into Pods

A pod may consume a secret through:

```text
Environment variable
```

or:

```text
Mounted file
```

Each has trade-offs.

Environment variables are convenient but can be exposed through process/debugging mechanisms.

Mounted files can provide clearer filesystem-level controls and support certain reload strategies.

---

## Secret Rotation in Kubernetes

A production rotation flow might be:

```text
Secret Manager
      ↓
New secret version
      ↓
External secret synchronization
      ↓
Pod reload / restart
      ↓
New connections
      ↓
Old credential revoked
```

The deployment must ensure the application can transition without service interruption.

---

## Secret Rotation in Django

Django applications should read secrets from runtime configuration rather than source code.

For example:

```python
import os

DATABASE_URL = os.environ["DATABASE_URL"]
```

The deployment system can provide a new value during rotation.

Do not place production credentials directly in:

```text
settings.py
```

or committed configuration files.

---

## Secret Rotation in FastAPI

FastAPI services can use runtime configuration loaded from the deployment environment or a secret manager.

For example:

```python
import os

DATABASE_URL = os.environ["DATABASE_URL"]
```

For complex deployments, a configuration layer can abstract the secret source from application business logic.

---

## Secret Handling in Celery

Celery workers often require credentials for:

```text
PostgreSQL
Redis
External APIs
AWS
Kafka
```

Workers should receive only the secrets required for their jobs.

Do not give every worker access to the complete application secret set.

---

## Secret Handling in Kafka

Kafka authentication credentials should be managed separately from message payloads.

Avoid placing:

```text
username
password
```

inside event messages.

Transport credentials belong to the broker/client security configuration.

---

## Secret Handling in Redis

Redis credentials should not be included in cache values or application payloads.

Avoid:

```json
{
  "user": "123",
  "redis_password": "..."
}
```

Credentials belong to the runtime configuration and secret-management layer.

---

## Secret Leakage Through Logs

The following is dangerous:

```python
logger.info("Connecting with config=%s", config)
```

if `config` contains credentials.

Also avoid logging:

```text
Authorization headers
DATABASE_URL
AWS credentials
API keys
JWT signing secrets
```

Use structured logging with explicit allowlists.

---

## Secret Leakage Through Exceptions

Avoid errors such as:

```text
Connection failed:
postgres://user:password@db.internal/app
```

Redact credentials before logging exceptions.

Production diagnostics should identify the failure without exposing authentication material.

---

## Secret Leakage Through Traces

Distributed tracing can accidentally capture:

```text
HTTP headers
Query parameters
Environment variables
Request bodies
```

Configure tracing systems to exclude sensitive fields.

Never assume that an APM platform is an appropriate secret store.

---

## Secret Leakage Through Metrics

Metrics should not contain secrets.

Avoid:

```text
api_request_total{api_key="secret"}
```

Labels are frequently stored for long periods and may be broadly accessible.

Use non-sensitive dimensions such as:

```text
service
endpoint
status
region
```

---

## Secret Leakage Through Crash Dumps

Crash diagnostics can contain process memory, environment variables, and request context.

Review:

- Core dumps
- Error trackers
- Debuggers
- Profilers
- Heap snapshots

Sensitive processes should have appropriate diagnostic controls.

---

## Secret Retrieval Frequency

Fetching secrets on every request is usually unnecessary.

Avoid:

```text
HTTP request
    ↓
Secret Manager
    ↓
Database password
```

for every API call.

Prefer:

```text
Application startup / controlled refresh
    ↓
Secret retrieval
    ↓
In-memory use
```

while considering rotation requirements.

---

## Caching Secrets in Memory

Applications often need to hold secrets in memory while using them.

This is generally unavoidable.

The goal is to minimize:

- Exposure duration
- Access scope
- Copies
- Logging
- Debugging visibility

Do not unnecessarily duplicate secrets across objects, caches, queues, or persistent storage.

---

## Secret Rotation and Availability

Rotation must not create outages.

A safe process considers:

```text
Credential creation
      ↓
Application compatibility
      ↓
Deployment
      ↓
Connection refresh
      ↓
Validation
      ↓
Old credential revocation
```

Always identify the rollback strategy before revoking the old credential.

---

## Emergency Credential Rotation

When compromise is suspected:

```text
Detect
  ↓
Contain
  ↓
Revoke / rotate
  ↓
Deploy replacement
  ↓
Verify access
  ↓
Investigate
  ↓
Audit
```

Do not wait for the normal rotation schedule if a credential is known or suspected to be compromised.

---

## Secret Rotation Failure Modes

Common failures include:

| Failure | Result |
|---|---|
| New secret created but app not updated | Authentication failures |
| Old secret revoked too early | Outage |
| Some pods use old secret | Inconsistent behavior |
| Connection pool not refreshed | Old connections persist |
| Secret manager permission broken | Application startup failure |
| New credential has incorrect permissions | Runtime authorization failures |

Rotation should therefore be tested as an operational workflow.

---

## High Availability

Secret management is part of application availability.

If:

```text
Application startup
    ↓
Secret Manager unavailable
```

the application may fail to initialize.

Production systems should understand:

- Secret-manager availability
- Credential caching
- Startup behavior
- Rotation behavior
- Regional dependencies
- Failover behavior

Do not create an unnecessary hard dependency on a remote secret retrieval call for every request.

---

## Disaster Recovery

DR environments need access to the credentials required to operate.

A recovery plan should verify:

```text
Application deployment
+
IAM identity
+
Secret access
+
Database credentials
+
Encryption keys
+
External API credentials
```

A database backup is not enough if the recovered application cannot authenticate to required services.

---

## Multi-Region Secrets

For multi-region systems, determine whether secrets need:

```text
Regional replication
```

or:

```text
Centralized access
```

Consider:

- Latency
- Availability
- Failover
- Key dependencies
- Regional isolation
- Access policies

Do not assume that a secret stored in one region is automatically available to a failover environment.

---

## Secret Access Auditing

Record access to high-value secrets where the platform supports it.

Useful audit information includes:

```text
Who / workload
Which secret
When
Operation
Success / failure
Source identity
```

Avoid logging the secret value itself.

---

## Secret Inventory

Maintain an inventory such as:

| Secret | Owner | Consumers | Rotation | Storage |
|---|---|---|---|---|
| Orders DB credential | Platform | Order API/worker | Scheduled | Secrets Manager |
| Payment API key | Payments | Payment service | Provider-defined | Secrets Manager |
| JWT signing key | Identity | Auth service | Controlled | KMS/secure store |
| CI deployment identity | Platform | CI/CD | Short-lived | OIDC |

This makes incident response and credential rotation substantially easier.

---

## Credential Ownership

Every production credential should have an owner.

Ownership answers:

```text
Who rotates it?
Who approves access?
Who responds if compromised?
Who verifies recovery?
```

A secret without an owner becomes operational debt.

---

## Secret Naming and Ownership Convention

A useful naming pattern is:

```text
<environment>/<service>/<purpose>
```

For example:

```text
production/orders/database
production/orders/payment-api
staging/orders/database
```

Ownership metadata can be maintained alongside infrastructure definitions.

---

## Least Privilege

Secret access should follow the same principle as database access.

For example:

```text
Order Service
    ↓
orders/database
```

should not imply:

```text
Order Service
    ↓
payments/database
    ↓
identity/signing-key
    ↓
infrastructure/admin-credentials
```

The service should receive only the credentials necessary for its responsibilities.

---

## Secret Sprawl

Secret sprawl occurs when the same secret is copied into many systems.

Example:

```text
DB password
 ├── GitHub secret
 ├── Docker .env
 ├── Kubernetes Secret
 ├── Developer laptop
 ├── CI config
 └── Documentation
```

Every copy increases the attack surface.

Prefer a single authoritative secret store with controlled distribution.

---

## Credential Duplication

If ten services use the same credential:

```text
Credential compromise
       ↓
10 services affected
```

Service-specific credentials reduce this blast radius.

The trade-off is increased credential-management complexity.

Automated provisioning and rotation are therefore important at scale.

---

## Secret Rotation Frequency

There is no universal rotation interval.

Rotation should consider:

- Credential type
- Exposure risk
- Provider support
- Compliance requirements
- Operational cost
- Detection capability
- Credential lifetime

Short-lived credentials are often preferable to relying solely on frequent manual rotation of long-lived credentials.

---

## Secrets in Infrastructure as Code

Infrastructure-as-code can accidentally expose secrets.

Avoid plaintext values such as:

```hcl
password = "production-secret"
```

especially where state files may retain the value.

Use appropriate secret references and protect state storage with strong access controls and encryption.

---

## Secrets in Terraform State

Terraform state can contain sensitive values even when variables are marked sensitive.

For example:

```hcl
variable "database_password" {
  type      = string
  sensitive = true
}
```

`sensitive = true` primarily affects display/redaction behavior; it does not mean the value is absent from state.

Protect the state backend accordingly.

---

## CI/CD Secret Handling

CI/CD systems should:

- Mask secrets in logs
- Restrict secret access by environment
- Use short-lived identities where possible
- Avoid exposing secrets to untrusted pull requests
- Separate production deployment permissions
- Audit privileged workflows

Never print all environment variables during debugging.

Avoid:

```bash
env
```

in production CI jobs when secrets are present.

---

## Pull Request Security

Be careful when running CI against untrusted code.

A malicious pull request may attempt to:

```text
Read environment variables
Access cloud credentials
Call secret-management APIs
Exfiltrate deployment secrets
```

Production secrets should not be automatically exposed to untrusted workflows.

---

## Developer Workstations

Developers should use separate credentials for local environments.

Avoid:

```text
Developer laptop
    ↓
Production database password
```

Prefer:

```text
Developer
    ↓
Local / development credentials
```

Production access should be exceptional and controlled.

---

## Local Development

A common pattern is:

```text
.env.local
```

for local secrets, with:

```text
.env.local
```

excluded from source control.

Example:

```text
DATABASE_URL=postgresql://app_runtime:local-password@localhost:5432/app
```

This is appropriate for local development but should not become the production secret-management architecture.

---

## Production Secret Management Architecture

```mermaid
flowchart TB
    Dev[Developer] --> Git[Source Control]
    Git --> CI[CI/CD]
    CI --> OIDC[Workload Identity]
    OIDC --> IAM[AWS IAM]

    IAM --> SM[AWS Secrets Manager]
    IAM --> KMS[AWS KMS]

    SM --> API[Django / FastAPI]
    API --> DB[(PostgreSQL)]
    API --> Redis[(Redis)]
    API --> Kafka[Kafka]

    SM --> Worker[Celery Worker]
```

The application receives only the secrets its workload identity is authorized to retrieve.

---

## Production Credential Flow

```text
Deployment
    ↓
Workload identity established
    ↓
Application authorized to secret store
    ↓
Required secret retrieved
    ↓
Application establishes secure connection
    ↓
Secret remains in controlled runtime memory
    ↓
Credential rotated
    ↓
Application refreshes
    ↓
Old credential revoked
```

This is substantially safer than distributing static credentials manually.

---

## Security Checklist

- [ ] Production secrets are stored in an approved secret-management system.
- [ ] Secrets are never committed to source control.
- [ ] Secret scanning is enabled in CI/CD.
- [ ] Database credentials use dedicated least-privileged roles.
- [ ] Application services do not use database superusers.
- [ ] Production and non-production credentials are separated.
- [ ] Services use separate credentials where practical.
- [ ] Cloud workloads prefer short-lived workload identity.
- [ ] CI/CD avoids long-lived cloud access keys where possible.
- [ ] Secret access is controlled by least privilege.
- [ ] High-value secret access is auditable.
- [ ] Secrets are not logged.
- [ ] Secrets are not included in traces or metrics.
- [ ] Secrets are not embedded in Docker images.
- [ ] Infrastructure state containing secrets is protected.
- [ ] Kubernetes secret access is restricted.
- [ ] Secret rotation is automated where practical.
- [ ] Rotation supports zero-downtime operation where required.
- [ ] Old credentials are revoked after successful rotation.
- [ ] Emergency credential revocation procedures exist.
- [ ] Secret ownership is documented.
- [ ] Secret consumers are documented.
- [ ] DR environments can access required credentials.
- [ ] Secret-management dependencies are included in availability planning.
- [ ] Developers do not receive unnecessary production credentials.
- [ ] OAuth client secrets remain server-side.
- [ ] JWT signing private keys are strongly protected.
- [ ] TLS private keys are strongly protected.
- [ ] Encryption keys use appropriate key-management controls.

---

## Common Mistakes

### Hard-Coding Secrets

**Problem:** Credentials become part of source code and potentially Git history.

**Better:** Use runtime secret injection.

### Storing Secrets Only in Environment Variables

**Problem:** Environment variables can still leak through processes, debugging, crash reports, and deployment tooling.

**Better:** Use a proper secret-management system and minimize runtime exposure.

### Sharing One Database Credential Across Services

**Problem:** One compromised service can affect unrelated workloads.

**Better:** Use service-specific database roles where practical.

### Using Database Superuser Credentials

**Problem:** Application compromise becomes database administration compromise.

**Better:** Use dedicated runtime roles with minimum privileges.

### Rotating by Revoking First

**Problem:** Applications can lose access before receiving the replacement credential.

**Better:** Create the new credential, deploy it, validate it, then revoke the old credential.

### Forgetting Connection Pools

**Problem:** Applications may continue using existing connections while new connections require the new credential.

**Better:** Include pool lifecycle and connection recycling in the rotation plan.

### Putting Secrets in Docker Images

**Problem:** Secrets can persist in image layers and registries.

**Better:** Inject secrets at runtime.

### Committing Kubernetes Secrets

**Problem:** Base64 encoding is not encryption and Git history is persistent.

**Better:** Keep authoritative secrets in a managed secret store and control Kubernetes access.

### Exposing Secrets in CI Logs

**Problem:** CI logs can have long retention and broad access.

**Better:** Mask secrets and avoid commands that dump environment/configuration.

### Putting API Keys in URLs

**Problem:** URLs are frequently logged and stored by infrastructure.

**Better:** Use secure headers or provider-supported authentication mechanisms.

### Treating Secret Rotation as a Manual Task

**Problem:** Manual rotation is easy to forget and difficult to coordinate.

**Better:** Automate rotation and validation where supported.

### Giving Every Service Access to Every Secret

**Problem:** A compromised service gains a much larger blast radius.

**Better:** Scope secret-manager permissions by service and purpose.

---

## Senior-Level Design Questions

When designing credential management, ask:

### Where is the authoritative secret stored?

There should normally be one controlled source of truth.

### Who can retrieve it?

Use workload identity and least privilege.

### How long is the credential valid?

Prefer short-lived credentials where practical.

### How is it rotated?

Define:

```text
Generate
Deploy
Validate
Switch
Revoke
```

### How is compromise handled?

Know how to immediately:

```text
Disable
Rotate
Revoke
Audit
```

### Where could the secret leak?

Review:

```text
Source control
CI/CD
Logs
Tracing
Metrics
Containers
Kubernetes
Crash dumps
Backups
Developer machines
```

### What happens during failover?

Verify that standby or replacement workloads can obtain required credentials.

### What happens during disaster recovery?

Verify the complete chain:

```text
Workload identity
    ↓
Secret access
    ↓
Database/API authentication
    ↓
Application startup
```

---

## Credential Management Decision Framework

```text
Does the workload need a credential?
        │
        ├── No → Do not create one
        │
        └── Yes
             ↓
     Can workload identity be used?
             │
             ├── Yes → Prefer short-lived identity
             │
             └── No → Managed secret
                         ↓
                  Least-privileged scope
                         ↓
                    Secure storage
                         ↓
                  Controlled distribution
                         ↓
                  Rotation strategy
                         ↓
                  Revocation strategy
                         ↓
                       Audit
```

The strongest credential is often the one the workload does not need to possess.

---

## Interview Traps

### Are environment variables a secret-management system?

No. They are a delivery mechanism. Environment variables can still be exposed through processes, logs, debugging, and deployment tooling.

### Why should applications avoid database superusers?

Because a compromised application credential would otherwise have administrative access to the database.

### Why are short-lived credentials safer?

A stolen credential has a limited useful lifetime, reducing the window in which an attacker can use it.

### What is workload identity?

A mechanism that gives a workload an authenticated identity and allows it to obtain authorized temporary credentials without embedding long-lived secrets.

### Why should different microservices use different credentials?

It limits blast radius, improves attribution, and enables service-specific least privilege.

### What is the safest way to rotate a database password?

Where the database/authentication mechanism supports it, create the replacement credential, deploy it to consumers, validate new connections, allow existing connections to transition, and then revoke the old credential.

### Why is secret rotation an availability concern?

A poorly coordinated rotation can invalidate credentials before applications have switched to the replacement, causing widespread authentication failures.

### Why are CI/CD systems high-risk?

They often have access to production deployment identities, cloud APIs, registries, databases, and secret stores. A compromised pipeline can therefore become a production compromise path.

### Does base64-encoding a Kubernetes Secret encrypt it?

No. Base64 is an encoding mechanism, not encryption. Kubernetes Secret storage and access require appropriate platform-level protection.

### Where should encryption keys be stored?

High-value encryption keys should generally use dedicated key-management mechanisms such as KMS or HSM-backed systems rather than being treated like ordinary application configuration.

### What is secret sprawl?

Secret sprawl occurs when credentials are copied into many repositories, environments, configuration files, pipelines, containers, and machines, increasing the number of places from which they can leak.

### What is the senior-level approach to credential management?

Treat credentials as managed security assets with defined ownership, scope, lifecycle, identity, storage, rotation, revocation, auditing, HA, and DR behavior. Minimize static secrets and prefer workload identity and short-lived credentials wherever practical.

## Key Takeaways

- **Prefer workload identity and short-lived credentials** over long-lived static secrets whenever the platform supports them.
- **Store unavoidable secrets centrally and enforce least privilege**, using dedicated database roles, service-specific credentials, and tightly scoped secret-manager permissions.
- **Design rotation as a zero-downtime lifecycle**, including replacement credential creation, application rollout, connection-pool transition, validation, and old-credential revocation.
- **Treat every secret exposure path as a security boundary**: source control, CI/CD, logs, traces, metrics, containers, Kubernetes, backups, and developer environments.
- **Credential management is also an availability and DR concern**; production systems must be able to retrieve, rotate, revoke, and recover required credentials without creating outages.