# 04- Secrets and Encryption

## Overview

Secrets and encryption are separate but complementary security controls for ECS workloads.

**Secrets management** protects sensitive configuration such as database passwords, API keys, OAuth credentials, and application secrets.

**Encryption** protects data from unauthorized disclosure while it is stored or transmitted.

A production ECS architecture should avoid embedding secrets in Docker images, source code, task-definition JSON, or plaintext configuration files. Instead, sensitive values should be managed through services such as AWS Secrets Manager or AWS Systems Manager Parameter Store, with access controlled through IAM.

A typical architecture is:

```text
                         ECS Task
                            |
              +-------------+-------------+
              |                           |
              v                           v
       Secrets Manager                 KMS
              |                           |
              |                           |
              +-------------+-------------+
                            |
                            v
                    Encrypted Secret
                            |
                            v
                     Application
```

The security model should address four separate questions:

| Question | Security Control |
|---|---|
| Where is the secret stored? | Secrets Manager / Parameter Store |
| Who can access it? | IAM |
| How is it protected at rest? | KMS encryption |
| How is it protected in transit? | TLS |

## Secrets vs Encryption

Secrets management and encryption solve different problems.

### Secrets Management

Secrets management answers:

> Where should sensitive credentials live, and which workload is allowed to retrieve them?

Examples:

- PostgreSQL password
- Third-party API key
- OAuth client secret
- JWT signing secret
- External service credentials

### Encryption

Encryption answers:

> How do we prevent unauthorized parties from reading protected data while it is stored or transmitted?

Examples:

- RDS encryption at rest
- S3 server-side encryption
- TLS between services
- Encrypted EBS volumes
- Encrypted ECS-related configuration

The two controls often work together:

```text
Secret
   |
   v
Secrets Manager
   |
   v
KMS Encryption
   |
   v
Encrypted Storage
   |
   v
IAM Authorization
   |
   v
ECS Application
```

## Why Secrets Should Not Be Embedded in Containers

A common but insecure pattern is:

```dockerfile
ENV DATABASE_PASSWORD=super-secret-password
```

The problem is that container images are artifacts that can be:

- Stored in registries
- Downloaded by CI/CD systems
- Cached
- Inspected
- Shared
- Retained for long periods
- Reused across environments

Once a secret becomes part of an image, removing it from the current Dockerfile does not necessarily remove it from historical image layers.

Similarly, avoid:

```python
DATABASE_PASSWORD = "super-secret-password"
```

or:

```text
DATABASE_PASSWORD=super-secret-password
```

inside source-controlled files.

A better architecture is:

```text
Source Code
    |
    X
    |
    X---- No production secrets
    |
    v
Docker Image
    |
    X
    |
    X---- No production secrets
    |
    v
ECS Task
    |
    v
Secrets Manager
```

## AWS Secrets Manager

AWS Secrets Manager is designed for storing and retrieving sensitive values.

Typical ECS secrets include:

```text
prod/orders-api/database
prod/orders-api/stripe
prod/orders-api/oauth
prod/orders-api/jwt
```

A secret can contain a structured JSON document:

```json
{
  "username": "orders_app",
  "password": "example-password",
  "host": "orders-db.example.internal",
  "port": 5432,
  "database": "orders"
}
```

Applications can retrieve secrets through supported ECS integrations or directly through the AWS SDK.

## When to Use Secrets Manager

Secrets Manager is a strong choice when the workload requires:

- Sensitive credentials
- Secret rotation
- Centralized secret management
- Fine-grained IAM access
- Integration with AWS services
- Auditability of secret access

It is particularly useful for production credentials that need controlled lifecycle management.

## Systems Manager Parameter Store

AWS Systems Manager Parameter Store can also provide centralized configuration and secret storage.

It supports different parameter types, including encrypted `SecureString` parameters.

Conceptually:

```text
ECS Application
      |
      v
Parameter Store
      |
      v
KMS
```

Parameter Store is often useful when applications have a mixture of configuration values and sensitive parameters.

A simplified distinction is:

| Requirement | Common Choice |
|---|---|
| Application configuration | Parameter Store |
| Sensitive secrets | Secrets Manager |
| Secret rotation workflows | Secrets Manager |
| Simple encrypted parameters | Parameter Store |
| Centralized environment configuration | Either, depending on requirements |

The correct choice depends on the application's operational and security requirements.

## ECS Secret Injection

ECS can reference secrets from supported AWS secret stores in the task definition.

For example:

```json
{
  "containerDefinitions": [
    {
      "name": "api",
      "image": "123456789012.dkr.ecr.ap-south-1.amazonaws.com/orders-api:8f31c2a",
      "secrets": [
        {
          "name": "DATABASE_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:ap-south-1:123456789012:secret:prod/orders-api/database-password"
        }
      ]
    }
  ]
}
```

The resulting runtime model is:

```text
ECS Task
   |
   v
Task Definition
   |
   v
Secret Reference
   |
   v
Secrets Manager
   |
   v
Container Environment
   |
   v
Application
```

The secret is not stored directly in the task-definition JSON as plaintext.

## Execution Role and Secret Injection

When ECS retrieves a secret as part of starting the task, the ECS runtime needs appropriate permissions through the task execution role.

Conceptually:

```text
ECS Runtime
     |
     v
Execution Role
     |
     v
Secrets Manager
     |
     v
Secret
     |
     v
Container
```

This is different from application code explicitly calling Secrets Manager.

For ECS-injected secrets:

```text
ECS Runtime
    |
    v
Execution Role
```

For application-initiated secret retrieval:

```text
Application
    |
    v
Task Role
    |
    v
Secrets Manager
```

The IAM role must match the actual retrieval mechanism.

## Application-Initiated Secret Retrieval

An application can retrieve a secret through the AWS SDK.

For Python:

```python
import boto3

secrets_manager = boto3.client("secretsmanager")

response = secrets_manager.get_secret_value(
    SecretId="prod/orders-api/database",
)

secret = response["SecretString"]
```

The application's task role needs permission to call:

```text
secretsmanager:GetSecretValue
```

on the required secret.

Example:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadDatabaseSecret",
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:ap-south-1:123456789012:secret:prod/orders-api/database-*"
    }
  ]
}
```

Do not grant:

```text
secretsmanager:*
```

when the application only needs `GetSecretValue`.

## ECS Secrets and Environment Variables

ECS can expose injected secrets to the application as environment variables.

For example:

```text
DATABASE_PASSWORD
STRIPE_API_KEY
JWT_SECRET
```

This is convenient for applications such as Django and FastAPI because they already commonly consume configuration through environment variables.

For Django:

```python
import os

DATABASE_PASSWORD = os.environ["DATABASE_PASSWORD"]
```

For FastAPI:

```python
import os

JWT_SECRET = os.environ["JWT_SECRET"]
```

However, environment variables are not a universal security boundary.

They can potentially become exposed through:

- Application debugging
- Process inspection
- Diagnostic tooling
- Accidental logging
- Error reports
- Misconfigured monitoring

The important principle is:

> Secrets should be protected throughout their entire lifecycle, not only while stored.

## Secret Access Boundaries

Each ECS service should generally access only the secrets it requires.

For example:

```text
Orders API
    |
    +---- prod/orders-api/database

Payment Service
    |
    +---- prod/payment/stripe

Notification Worker
    |
    +---- prod/notification/email
```

Avoid:

```text
All ECS Services
       |
       v
All Production Secrets
```

A compromised notification worker should not automatically have access to database credentials belonging to the order service.

## Secret Naming and Organization

Use consistent naming conventions.

For example:

```text
/<environment>/<service>/<purpose>
```

Examples:

```text
/prod/orders-api/database
/prod/orders-api/external-api
/prod/payment/stripe
/staging/orders-api/database
/dev/orders-api/database
```

Consistent naming makes:

- IAM policies easier to scope
- Auditing easier
- Secret discovery easier
- Environment separation clearer
- Automation simpler

Avoid ambiguous names such as:

```text
my-secret
database
password
secret1
```

## Environment Isolation

Secrets must be isolated between environments.

Prefer:

```text
Development
    |
    +-- /dev/orders-api/database

Staging
    |
    +-- /staging/orders-api/database

Production
    |
    +-- /prod/orders-api/database
```

The development task role should not be able to retrieve:

```text
/prod/*
```

For stronger isolation, use separate AWS accounts for major environments.

## Secret Rotation

Secret rotation means replacing credentials periodically or when compromise is suspected.

A typical lifecycle is:

```text
Application
    |
    v
Current Secret
    |
    v
Rotation Process
    |
    v
New Credential
    |
    v
Secret Updated
    |
    v
Application Uses New Value
```

Rotation is particularly important for:

- Database credentials
- API keys
- Service credentials
- Long-lived third-party credentials

Rotation should be designed carefully because changing a credential can temporarily break applications that still use the old value.

## Rotation and ECS Deployments

When secrets are injected into containers as environment variables, the secret value is typically established when the container starts.

Changing the secret does not necessarily mean an already-running process immediately receives the new value.

A common operational model is:

```text
Secret Rotation
      |
      v
New Secret Version
      |
      v
Restart / Replace ECS Tasks
      |
      v
New Tasks Receive Updated Secret
```

This makes deployment behavior part of secret rotation design.

For applications that retrieve secrets dynamically through the AWS SDK, the application can implement controlled refresh behavior instead.

## Secret Rotation for Database Credentials

Consider a PostgreSQL database:

```text
ECS
 |
 v
Secrets Manager
 |
 v
PostgreSQL Credentials
 |
 v
RDS PostgreSQL
```

A robust rotation process must coordinate:

1. Database credential update.
2. Secret update.
3. Application credential refresh.
4. Existing connection handling.
5. New connection establishment.
6. Failure and rollback behavior.

Do not rotate database credentials without understanding connection pooling.

For Django, PostgreSQL connections may remain open through connection pooling or persistent connections.

For FastAPI, SQLAlchemy pools may hold existing database connections.

Rotation therefore needs to consider connection lifetime rather than only the secret value.

## KMS and Encryption

AWS KMS provides managed cryptographic key infrastructure for AWS services and applications.

A useful mental model is:

```text
Data
 |
 v
Encryption Operation
 |
 v
KMS Key
 |
 v
Encrypted Data
```

In many AWS services, the service performs the actual encryption/decryption operation while KMS controls or protects the cryptographic key material.

KMS can be used with services such as:

- Secrets Manager
- S3
- RDS
- EBS
- ECR
- SQS
- SNS
- CloudWatch Logs
- Parameter Store

The exact encryption integration varies by service.

## AWS-Managed vs Customer-Managed KMS Keys

AWS services commonly support AWS-owned or AWS-managed encryption mechanisms, while some use cases require customer-managed KMS keys.

| Option | Operational Control | Typical Use |
|---|---|---|
| AWS-owned keys | Lowest | Default service-managed encryption |
| AWS-managed KMS keys | More visibility/control | Service encryption with AWS-managed lifecycle |
| Customer-managed KMS keys | Highest control | Custom access policies, compliance, cross-account requirements |

Customer-managed keys provide more control but also create additional operational responsibility.

You must manage:

- Key policies
- IAM permissions
- Key rotation settings
- Grants where applicable
- Cross-account access
- Deletion safeguards
- Monitoring

Do not introduce customer-managed KMS keys merely because they sound more secure. Use them when their additional control is actually required.

## KMS Key Policies

KMS authorization can involve both IAM policies and the KMS key policy.

A simplified flow is:

```text
ECS Task
   |
   v
IAM Policy
   |
   v
AWS Service
   |
   v
KMS Key Policy
   |
   v
KMS Authorization
```

For customer-managed keys, the key policy is particularly important.

A common production troubleshooting mistake is to verify:

```text
secretsmanager:GetSecretValue
```

and stop there.

If the secret uses a customer-managed KMS key, the complete authorization chain must also permit the required KMS operation.

## KMS Least Privilege

Do not grant broad KMS access unnecessarily.

Avoid:

```json
{
  "Effect": "Allow",
  "Action": "kms:*",
  "Resource": "*"
}
```

Prefer narrowly scoped operations such as the required encryption or decryption permissions on a specific key.

The exact KMS permissions depend on whether the application or an AWS service performs the cryptographic operation.

## Encryption at Rest

Production ECS architectures commonly rely on encryption at rest across multiple services.

Typical resources include:

```text
ECS Workload
    |
    +---- ECR Image
    |
    +---- Secrets Manager
    |
    +---- RDS
    |
    +---- S3
    |
    +---- EBS / EFS
    |
    +---- CloudWatch Logs
```

Encryption should be enabled according to organizational security and compliance requirements.

Important questions include:

- Which data is sensitive?
- Which services store it?
- Which KMS key protects it?
- Who can decrypt it?
- How are keys managed?
- What happens if a key becomes unavailable?

## Encryption in Transit

Encryption at rest does not protect data while it travels between systems.

Use TLS for sensitive communication paths.

A typical backend architecture is:

```text
Client
   |
   | HTTPS
   v
ALB
   |
   | TLS where required
   v
ECS
   |
   | TLS
   +---- PostgreSQL
   |
   +---- Redis
   |
   +---- External APIs
```

Private networking does not automatically mean traffic is encrypted.

A private VPC controls reachability. TLS protects the data in transit.

These are different controls.

## TLS Between ALB and ECS

A common architecture terminates TLS at the Application Load Balancer:

```text
Client
   |
   | HTTPS
   v
ALB
   |
   | HTTP
   v
ECS
```

This can be acceptable depending on the security requirements and network architecture.

For higher-security environments, TLS can also be used between the ALB and ECS:

```text
Client
   |
   | HTTPS
   v
ALB
   |
   | HTTPS
   v
ECS
```

The decision should consider:

- Threat model
- Compliance requirements
- Certificate management
- Operational complexity
- Internal network trust assumptions

## TLS for Service-to-Service Communication

Microservices communicating through REST or gRPC may require TLS:

```text
Orders Service
      |
      | HTTPS / TLS
      v
Payment Service
```

For highly sensitive systems, mutual TLS can provide stronger service identity:

```text
Orders Service
      |
      | mTLS
      v
Payment Service
```

TLS protects the transport channel, while application authorization determines what the service is permitted to do.

Do not treat TLS as a replacement for authorization.

## Database Encryption

A production ECS application commonly connects to a managed database such as Amazon RDS.

The architecture may be:

```text
ECS
 |
 | TLS
 v
RDS PostgreSQL
 |
 v
Encrypted Storage
 |
 v
KMS
```

Database security should therefore address:

- Encryption at rest
- TLS in transit
- Credential management
- IAM or database authentication where applicable
- Network access
- Database-level authorization
- Backup encryption

Encryption alone does not prevent an application with valid database credentials from reading sensitive data.

## S3 Encryption

S3 objects can be encrypted at rest using server-side encryption.

The application architecture can be:

```text
ECS
 |
 | HTTPS
 v
S3
 |
 v
Encrypted Object
 |
 v
KMS where applicable
```

The task role should still restrict access to the required bucket and object paths.

Encryption does not replace IAM.

For example:

```text
Encryption
    +
IAM Authorization
    +
Bucket Policy
```

provides a stronger security boundary than encryption alone.

## ECR Image Encryption

Container images stored in Amazon ECR should be protected through appropriate repository access controls and encryption.

The security lifecycle becomes:

```text
CI/CD
  |
  v
ECR
  |
  | Encrypted Image Storage
  v
ECS
```

The execution role should be permitted to retrieve only the images and repositories required by the deployment architecture.

Image encryption does not replace vulnerability scanning or image provenance controls.

## Secrets in CI/CD

CI/CD systems frequently need access to credentials.

Avoid putting production secrets directly into:

- Git repositories
- Docker build arguments
- Dockerfiles
- Build logs
- Generated artifacts

A better architecture is:

```text
GitHub Actions
      |
      v
OIDC
      |
      v
AWS IAM Role
      |
      v
AWS Resources
```

For deployment, prefer short-lived AWS credentials through OIDC rather than long-lived access keys.

If a pipeline genuinely needs an application secret, retrieve it through an appropriate secret-management mechanism and prevent it from being printed into logs.

## Docker Build Secrets

Never use a normal Docker `ARG` or `ENV` instruction as a secure mechanism for build secrets.

Avoid:

```dockerfile
ARG NPM_TOKEN
RUN npm config set //registry.example.com/:_authToken=$NPM_TOKEN
```

Build arguments can potentially become visible through image metadata or build history depending on how they are used.

If a build genuinely requires a secret, use the container build system's supported secret mechanism and ensure the secret does not persist in the resulting image.

The preferred production architecture is often to avoid requiring secrets during image creation entirely.

## Secret Leakage Through Logs

A technically secure secret store can still be undermined by application logging.

Avoid:

```python
logger.info("Database configuration: %s", database_config)
```

if `database_config` contains credentials.

Also avoid logging:

```text
Authorization headers
JWT tokens
API keys
Passwords
Session cookies
Database URLs containing credentials
```

Use structured logging with explicit fields and redaction rules.

For example:

```python
logger.info(
    "Database connection established",
    extra={
        "database_host": database_host,
        "database_name": database_name,
    },
)
```

Do not log the password.

## Secret Leakage Through Error Handling

Exceptions can accidentally expose credentials.

For example, a malformed database URL can contain:

```text
postgresql://user:password@host/database
```

If that exception reaches application logs, the password may be exposed.

Production applications should sanitize:

- Connection strings
- HTTP headers
- Query parameters
- Request bodies
- Exception messages
- Third-party API responses

before sending them to CloudWatch or other logging systems.

## Secret Access Auditing

Sensitive secret access should be auditable.

A production security architecture should be able to determine:

```text
Who accessed the secret?
        |
        v
Which identity?
        |
        v
Which secret?
        |
        v
When?
        |
        v
From which workload/account?
```

AWS audit mechanisms can help track access and administrative changes.

Monitoring should focus on unexpected patterns, such as a service suddenly accessing secrets belonging to another application.

## Secret Rotation and Availability

Secret rotation introduces an availability concern.

Suppose:

```text
Application
    |
    v
Old Password
    |
    X
Database now requires new password
```

If all application tasks still use the old secret, requests can fail.

A production rotation strategy should consider:

- Overlapping credentials where supported
- Graceful task replacement
- Connection pool behavior
- Deployment timing
- Health checks
- Rollback
- Rotation failure

Security changes should not unintentionally create an outage.

## Disaster Recovery for Secrets

Secrets are production data and should be included in disaster-recovery planning.

Consider:

- Secret replication requirements
- AWS region failure
- Account recovery
- KMS key dependencies
- Database credential recovery
- External API credential recovery
- Application bootstrap requirements

A disaster-recovery design should answer:

> Can the application start in the recovery environment without requiring manual access to secrets from the failed environment?

For multi-region architectures, secret replication and KMS design must be considered together.

## Multi-Region Secrets

A multi-region architecture may look like:

```text
                 Secrets Management
                       |
             +---------+---------+
             |                   |
             v                   v
        Region A             Region B
             |                   |
             v                   v
        ECS Tasks             ECS Tasks
```

Secrets should be available in the required recovery region.

Do not assume that a secret stored in one region automatically provides the desired recovery behavior in another region.

The design must account for:

- Secret replication
- KMS keys
- IAM policies
- Region-specific resource ARNs
- Deployment configuration
- Rotation behavior

## Encryption and Disaster Recovery

Encryption keys are part of the recovery architecture.

A backup is only useful if the recovery environment can decrypt it.

Consider:

```text
Encrypted Backup
       |
       v
KMS Key
       |
       v
Recovery Environment
```

If access to the required key is lost, encrypted backups may become unusable.

Therefore disaster recovery planning should include:

- Key availability
- Key policies
- Cross-account access
- Backup encryption
- Key deletion protection
- Recovery testing

## Security for Django

A Django application on ECS typically consumes secrets such as:

```text
DJANGO_SECRET_KEY
DATABASE_PASSWORD
EMAIL_PASSWORD
THIRD_PARTY_API_KEY
```

A production configuration might use environment variables populated from ECS secret references:

```python
import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DATABASE_PASSWORD = os.environ["DATABASE_PASSWORD"]
```

Do not commit:

```python
SECRET_KEY = "production-secret"
```

to source control.

Also ensure that Django's production security settings are configured appropriately, including:

- `DEBUG=False`
- Secure cookies
- HTTPS enforcement
- Proper `ALLOWED_HOSTS`
- CSRF configuration
- Secure session handling

Secrets management protects credentials; Django security configuration protects the application itself.

## Security for FastAPI

A FastAPI service can similarly consume secrets through environment variables or controlled runtime retrieval.

For example:

```python
import os

DATABASE_URL = os.environ["DATABASE_URL"]
JWT_SECRET = os.environ["JWT_SECRET"]
```

Sensitive configuration should not be embedded in the Docker image.

FastAPI applications should also avoid exposing secrets through:

- OpenAPI examples
- Error responses
- Debug endpoints
- Request logging
- Health-check responses

A health endpoint should return operational status rather than sensitive configuration.

## Secrets and Redis

Redis credentials should be handled like any other sensitive credential.

```text
ECS
 |
 | Secret
 v
Secrets Manager
 |
 v
Redis Credential
 |
 v
Private Redis
```

Do not place Redis passwords in source code or Dockerfiles.

If Redis traffic contains sensitive data, evaluate encryption in transit and the appropriate authentication mechanism supported by the chosen Redis service.

## Secrets and Kafka

Kafka credentials and certificates should also be treated as secrets.

A secure architecture may look like:

```text
ECS Consumer
    |
    v
Secrets Manager
    |
    +-- Username / Password
    +-- Certificate Material
    |
    v
Kafka / Amazon MSK
```

Do not distribute Kafka credentials broadly across all services.

Each consumer should receive only the credentials and topic access it requires.

## Common Mistakes

### Hard-Coding Secrets

```python
API_KEY = "production-secret"
```

This creates a source-control and artifact-security problem.

**Better:** store the secret in Secrets Manager or another approved secret-management system.

### Putting Secrets in Docker Images

Secrets in Dockerfiles or image layers can persist after the source is changed.

**Better:** inject secrets at runtime.

### Logging Secrets

Debugging code can accidentally print environment variables or request headers.

**Better:** explicitly redact sensitive fields.

### Using One Secret for Every Environment

This creates unnecessary coupling and makes compromise more damaging.

**Better:** separate development, staging, and production secrets.

### Giving Every ECS Service Access to Every Secret

This violates least privilege.

**Better:** grant each task role access only to required secrets.

### Forgetting KMS Permissions

A secret encrypted with a customer-managed key can fail to decrypt even when the Secrets Manager permission appears correct.

**Better:** verify both Secrets Manager and KMS authorization.

### Assuming Secret Rotation Is Instant

Running containers may continue using the secret value they received at startup.

**Better:** design task replacement or dynamic secret refresh into the rotation strategy.

### Treating Encryption as Authorization

Encryption protects data from unauthorized disclosure, but it does not determine which application is allowed to access the plaintext.

**Better:** combine encryption with IAM, resource policies, network controls, and application authorization.

### Exposing Secrets Through Logs

A secret can leak even when the storage system is perfectly configured.

**Better:** sanitize logs, exceptions, traces, and diagnostics.

### Using Long-Lived CI/CD Credentials

Static AWS credentials increase compromise and rotation risk.

**Better:** use OIDC and short-lived IAM role credentials for supported CI/CD systems.

## Production Checklist

| Area | Recommended Practice |
|---|---|
| Secret storage | Secrets Manager or Parameter Store |
| Source code | No production secrets |
| Docker images | No embedded secrets |
| ECS | Use runtime secret injection where appropriate |
| IAM | Restrict secret access by task role |
| Execution role | Use only required ECS runtime permissions |
| Application retrieval | Use task-role permissions |
| Encryption at rest | Enable according to security requirements |
| Encryption in transit | Use TLS for sensitive traffic |
| KMS | Scope access to required keys |
| Logging | Redact secrets and credentials |
| Rotation | Define and test a rotation process |
| Deployment | Replace tasks when required to consume new secrets |
| Environments | Separate dev, staging, and production secrets |
| CI/CD | Prefer OIDC and short-lived credentials |
| Disaster recovery | Include secrets and KMS dependencies |
| Multi-region | Plan secret and key availability |
| Auditing | Monitor secret access and administrative changes |

## Interview Traps

### What Is the Difference Between Secrets Manager and KMS?

Secrets Manager stores and manages sensitive values.

KMS manages cryptographic keys and cryptographic authorization used by AWS services and applications.

They often work together:

```text
Secrets Manager
      |
      v
KMS
      |
      v
Encrypted Secret
```

### Where Should an ECS Application's Database Password Be Stored?

Typically in Secrets Manager or an appropriate encrypted parameter store, not in source code, Docker images, or plaintext task-definition configuration.

### Which Role Retrieves an ECS-Injected Secret?

The ECS task execution role is involved when ECS retrieves the secret as part of task startup/configuration.

If the application itself calls Secrets Manager, the task role needs the corresponding permission.

### Does Encryption at Rest Protect Data in Transit?

No.

Encryption at rest protects stored data.

TLS protects data while it travels between systems.

Both may be required.

### Does a Private Subnet Eliminate the Need for TLS?

No.

A private subnet controls network reachability. It does not inherently encrypt application traffic.

### Why Can a Secret Rotation Cause an ECS Outage?

A running task may continue using an old secret value while the underlying credential has already changed.

The rotation process must coordinate credential changes with task replacement, connection pools, or dynamic secret refresh.

### Why Is KMS Important in Disaster Recovery?

Encrypted backups, secrets, and other protected resources may depend on KMS keys.

If the recovery environment cannot use the required key, encrypted data may not be recoverable.

## Key Takeaways

- Store production credentials in **Secrets Manager or an appropriate encrypted parameter store**, never in source code, Docker images, or plaintext configuration committed to version control.
- Use **IAM to restrict secret access** so each ECS workload can retrieve only the secrets it actually requires.
- Treat **KMS, encryption at rest, and TLS encryption in transit as complementary controls** rather than substitutes for IAM or application authorization.
- Design secret rotation and disaster recovery together, because **credential changes, running ECS tasks, connection pools, KMS keys, and regional recovery** all affect availability.
- Protect secrets throughout their entire lifecycle, including **logs, exceptions, CI/CD pipelines, runtime environment variables, backups, and operational tooling**.