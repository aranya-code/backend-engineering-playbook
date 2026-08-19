# 07- Field-Level Encryption

## Overview

CloudFront field-level encryption (FLE) protects sensitive portions of HTTP POST request data before the request reaches the application origin.

The key architectural property is that **only selected request fields are encrypted**, rather than encrypting the entire HTTP request.

A typical backend architecture is:

```text
Client
  │
  │ HTTPS POST
  │ sensitive fields
  ▼
CloudFront
  │
  │ Field-Level Encryption
  │
  │ Encrypt selected fields
  ▼
Origin
  │
  │ Decrypt sensitive fields
  ▼
Application
```

This is useful when a request passes through infrastructure that should not have access to particular sensitive values.

For example, an application may receive:

```json
{
  "customer_id": "cust_123",
  "name": "Alice",
  "email": "alice@example.com",
  "card_number": "4111111111111111"
}
```

The application may need to receive the request, but intermediate systems should not need access to `card_number`.

Field-level encryption can encrypt that specific field while leaving other fields available to the application infrastructure.

> **Important:** Field-level encryption is different from HTTPS/TLS. TLS protects data in transit between network endpoints, while field-level encryption provides additional protection for selected request fields beyond the TLS connection.

## Why Field-Level Encryption Exists

HTTPS protects a request while it travels over a network connection:

```text
Client
   │
   │ encrypted TLS connection
   ▼
CloudFront
   │
   │ encrypted TLS connection
   ▼
Origin
```

However, TLS terminates at an endpoint.

Once TLS is terminated, the HTTP payload becomes available to the component processing the request.

In some architectures, multiple systems may process or inspect requests:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Load Balancer
  │
  ▼
Reverse Proxy
  │
  ▼
Application
```

Field-level encryption addresses a different security requirement:

```text
Sensitive field
      │
      ▼
Encrypted at edge
      │
      ▼
Remains encrypted
      │
      ▼
Application decrypts
```

The purpose is to minimize the number of components that can access sensitive plaintext.

## TLS vs Field-Level Encryption

These mechanisms solve different problems.

| Property | HTTPS/TLS | Field-Level Encryption |
|---|---|---|
| Protects network traffic | Yes | Indirectly |
| Encrypts entire HTTP connection | Yes | No |
| Encrypts selected fields | No | Yes |
| Protects data after TLS termination | No | Yes |
| Requires application decryption | No | Yes |
| Protects against network interception | Yes | Yes, as an additional layer |
| Useful for sensitive request fields | Yes | Specifically designed for this |
| Replaces TLS | No | No |

A production architecture can use both:

```text
Client
  │
  │ HTTPS
  ▼
CloudFront
  │
  │ FLE encrypts sensitive fields
  ▼
Origin
  │
  │ HTTPS
  ▼
Application
  │
  │ Decrypt
  ▼
Sensitive value
```

Field-level encryption should therefore be treated as **defense in depth**, not as an alternative to TLS.

## What Field-Level Encryption Protects

Field-level encryption is intended for sensitive request fields such as:

- Payment-related information
- Personally identifiable information
- Government identifiers
- Financial information
- Sensitive customer attributes
- Other application-defined confidential fields

The important distinction is that the encryption policy applies to specific fields rather than the entire payload.

For example:

```json
{
  "name": "Alice",
  "country": "IN",
  "email": "alice@example.com",
  "tax_id": "<encrypted>",
  "account_number": "<encrypted>"
}
```

The application can continue processing non-sensitive fields while treating the protected fields as encrypted data until they reach the trusted decryption boundary.

## How Field-Level Encryption Works

At a high level:

```text
                    Public Internet
                          │
                          ▼
                       Client
                          │
                          │ HTTPS
                          ▼
                     CloudFront
                          │
                 ┌────────┴────────┐
                 │                 │
           Plain fields       Sensitive fields
                 │                 │
                 │                 ▼
                 │          Encrypt with public key
                 │                 │
                 └────────┬────────┘
                          │
                          ▼
                       Origin
                          │
                          ▼
                 Authorized decryptor
                          │
                          ▼
                  Sensitive plaintext
```

The encryption boundary is deliberately separated from the decryption boundary.

The public key can be used for encryption without granting the edge or other infrastructure the ability to decrypt the data.

## Public-Key Encryption Model

Field-level encryption uses asymmetric cryptography.

Conceptually:

```text
Public Key
    │
    ▼
Encrypt
    │
    ▼
Ciphertext
    │
    ▼
Private Key
    │
    ▼
Decrypt
    │
    ▼
Plaintext
```

This is useful because the encryption side does not need access to the private decryption key.

The architecture therefore establishes a trust boundary:

```text
Encryption side
    │
    │ public key
    ▼
CloudFront
    │
    │ ciphertext
    ▼
Origin
    │
    │ private key
    ▼
Trusted decryptor
```

## Encryption Profile

A CloudFront field-level encryption configuration uses an encryption profile to define how request data should be encrypted.

The profile associates the encryption configuration with a public key and related encryption settings.

The architecture can be represented as:

```text
Public Key
    │
    ▼
Encryption Profile
    │
    ▼
Field-Level Encryption Configuration
    │
    ▼
CloudFront Distribution
```

The encryption profile establishes the cryptographic configuration used by CloudFront when encrypting selected fields.

## Configuration Components

The important conceptual components are:

| Component | Responsibility |
|---|---|
| Public key | Encrypts sensitive values |
| Encryption profile | Associates encryption behavior with a key |
| Field-level encryption configuration | Defines which fields are protected |
| Cache behavior | Determines where the configuration applies |
| CloudFront distribution | Performs edge-side request processing |
| Private key | Decrypts the protected data at the trusted boundary |
| Application | Processes decrypted values |

The private key is particularly sensitive.

It should not be exposed to CloudFront.

## Request Flow

Consider a payment form:

```json
{
  "customer_id": "cust_123",
  "email": "alice@example.com",
  "card_number": "4111111111111111",
  "amount": 2500
}
```

The desired architecture might be:

```text
customer_id ────────────────► Origin
email ──────────────────────► Origin
amount ─────────────────────► Origin

card_number
    │
    ▼
CloudFront encryption
    │
    ▼
Encrypted card_number
    │
    ▼
Origin
    │
    ▼
Trusted decryptor
```

The application can then process the encrypted value only after crossing the appropriate decryption boundary.

## Detailed Request Lifecycle

```mermaid
sequenceDiagram
    participant C as Client
    participant CF as CloudFront
    participant O as Origin
    participant D as Trusted Decryptor
    participant A as Application

    C->>CF: HTTPS POST with sensitive fields
    CF->>CF: Identify configured fields
    CF->>CF: Encrypt selected fields
    CF->>O: Forward modified request
    O->>D: Send encrypted field
    D->>D: Decrypt using private key
    D->>A: Provide plaintext to authorized application
    A-->>D: Processing result
    D-->>O: Result
    O-->>CF: HTTP response
    CF-->>C: HTTP response
```

The exact decryption architecture depends on how the application implements its private-key boundary.

## Why Encrypt at CloudFront?

Encrypting selected fields at the edge can reduce the number of systems that see plaintext.

Without field-level encryption:

```text
Client
  │
  ▼
CloudFront
  │ plaintext
  ▼
Load Balancer
  │ plaintext
  ▼
Nginx
  │ plaintext
  ▼
Application
```

With field-level encryption:

```text
Client
  │ plaintext
  ▼
CloudFront
  │
  │ encrypt
  ▼
Load Balancer
  │ ciphertext
  ▼
Nginx
  │ ciphertext
  ▼
Application / Decryptor
  │
  │ decrypt
  ▼
Plaintext
```

The latter reduces the plaintext exposure window.

## When to Use Field-Level Encryption

Use field-level encryption when:

- Only specific request fields are sensitive.
- TLS termination occurs before the trusted application boundary.
- Intermediate infrastructure should not access plaintext.
- Regulatory or organizational controls require additional protection.
- A service needs to process non-sensitive fields while keeping sensitive fields encrypted.
- The application can securely manage the corresponding private key.

Typical architecture:

```text
Client
  │
  ▼
CloudFront
  │
  ├── Non-sensitive fields ──► Normal processing
  │
  └── Sensitive fields ──────► Encrypted
                                  │
                                  ▼
                             Trusted service
```

## When Not to Use It

Field-level encryption is not automatically appropriate for every application.

It may be unnecessary when:

- TLS already satisfies the security requirement.
- The entire application stack is already inside a tightly controlled trust boundary.
- No individual request fields require special protection.
- The application cannot securely manage private keys.
- The encryption requirements are better handled by an application-specific cryptographic architecture.
- A managed payment-tokenization service is more appropriate.

Do not add cryptographic complexity merely because encryption sounds more secure.

The security requirement should determine the architecture.

## Field-Level Encryption vs Application Encryption

There are two broad approaches.

### CloudFront Field-Level Encryption

```text
Client
  │
  ▼
CloudFront
  │ encrypt selected fields
  ▼
Origin
```

### Application-Level Encryption

```text
Client
  │
  ▼
Application
  │ encrypt
  ▼
Database
```

These protect different boundaries.

| Requirement | Better fit |
|---|---|
| Protect fields between edge and origin | CloudFront FLE |
| Protect sensitive values at rest | Application/database encryption |
| Protect network traffic | TLS |
| Prevent unauthorized application users | Authorization |
| Protect database storage | Encryption at rest |
| Reduce plaintext exposure in intermediaries | Field-level encryption |

In some systems, multiple layers are appropriate:

```text
TLS
  +
CloudFront FLE
  +
Application authorization
  +
Database encryption at rest
```

## Field-Level Encryption vs Database Encryption

These are often confused.

Database encryption protects data stored in the database:

```text
Application
    │
    ▼
Encrypted database storage
```

Field-level encryption protects request data before it reaches the application origin:

```text
Client
    │
    ▼
CloudFront
    │
    ▼
Encrypted field
    │
    ▼
Application
```

They address different attack surfaces.

## Field-Level Encryption and JSON APIs

Field-level encryption is especially relevant to POST requests containing structured data.

Example:

```http
POST /api/customers
Content-Type: application/json
```

Request:

```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "national_id": "ABC123456",
  "country": "IN"
}
```

A field-level encryption policy can identify sensitive fields such as:

```text
national_id
```

The conceptual result is:

```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "national_id": "<ciphertext>",
  "country": "IN"
}
```

The application must understand how the encrypted field is represented and how to decrypt it.

## Field-Level Encryption and Django

A Django API behind CloudFront might look like:

```text
Internet
    │
    ▼
CloudFront
    │
    │ FLE
    ▼
ALB
    │
    ▼
Nginx
    │
    ▼
Django / DRF
    │
    ├── PostgreSQL
    └── Redis
```

A Django application should not assume that every incoming field is plaintext.

The serializer boundary should explicitly account for protected fields.

Conceptually:

```python
class CustomerSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    encrypted_national_id = serializers.CharField()
```

The actual decryption should occur at a controlled cryptographic boundary rather than being scattered throughout serializers, views, and business logic.

A stronger design is:

```text
HTTP request
    │
    ▼
Decryption boundary
    │
    ▼
Validated application data
    │
    ▼
Service layer
    │
    ▼
Persistence
```

This keeps cryptographic operations isolated from ordinary business logic.

## Field-Level Encryption and FastAPI

A FastAPI service can use a similar boundary:

```text
CloudFront
    │
    ▼
ALB
    │
    ▼
FastAPI
    │
    ▼
Decryption service/library
    │
    ▼
Pydantic validation
```

The important architectural principle is to decrypt before the application requires plaintext, but as late as practical.

Avoid decrypting sensitive values immediately at the infrastructure boundary and then passing plaintext through multiple internal services.

## Microservices Considerations

Field-level encryption becomes more valuable as the number of intermediate services increases.

Consider:

```text
CloudFront
   │
   ▼
API Gateway / ALB
   │
   ▼
Service A
   │
   ▼
Service B
   │
   ▼
Service C
```

If sensitive data is plaintext throughout the chain:

```text
Service A ── plaintext
Service B ── plaintext
Service C ── plaintext
```

Each service becomes part of the sensitive-data trust boundary.

A stronger architecture can keep the field encrypted until the service that actually needs it:

```text
CloudFront
   │
   │ encrypted field
   ▼
Service A
   │
   │ encrypted field
   ▼
Service B
   │
   │ decrypt only if required
   ▼
Sensitive processing
```

This follows the principle of least privilege.

## Key Management

Private-key management is one of the most important operational concerns.

The private key should:

- Never be committed to Git.
- Never be embedded in application source code.
- Never be logged.
- Never be included in container images.
- Be accessible only to services that require decryption.
- Have controlled rotation procedures.
- Have auditable access.

A production architecture might use a dedicated key-management system or secure secret-management mechanism appropriate to the cryptographic design.

Conceptually:

```text
                 Key Management
                       │
                 Private Key
                       │
                       ▼
                Trusted Decryptor
                       │
                       ▼
                  Application
```

Do not distribute the private key to every microservice simply because one service needs to decrypt the field.

## Private Key vs Public Key

The trust model should remain clear.

| Key | Purpose | Exposure |
|---|---|---|
| Public key | Encrypt data | Can be distributed to encryption side |
| Private key | Decrypt data | Must remain confidential |

The core rule is:

```text
Public key  → encrypt
Private key → decrypt
```

Compromise of the public key does not provide the ability to decrypt ciphertext.

Compromise of the private key is a significantly more serious event.

## Key Rotation

Cryptographic keys should have a lifecycle.

A typical rotation process is:

```text
Current Key
    │
    ▼
Introduce New Key
    │
    ▼
Update Encryption Configuration
    │
    ▼
New Requests Use New Key
    │
    ▼
Old Ciphertext Remains Decryptable
    │
    ▼
Retire Old Key
```

The exact rotation strategy depends on the encryption implementation.

A common operational mistake is to rotate a key without ensuring that existing encrypted values remain decryptable.

Before rotation, answer:

- Which data was encrypted with the old key?
- How long must old ciphertext remain readable?
- Which services require old-key access?
- How is key-version metadata tracked?
- What is the rollback strategy?

## Key Versioning

For long-lived encrypted data, key versioning is useful.

Conceptually:

```json
{
  "key_version": "v2",
  "ciphertext": "..."
}
```

The decryptor can then select the correct private key:

```text
Ciphertext
   │
   ▼
Key version
   │
   ├── v1 ──► Private Key v1
   │
   └── v2 ──► Private Key v2
```

Do not assume the newest key can decrypt ciphertext created with every previous key.

## Logging Considerations

Sensitive fields should never appear in logs in plaintext.

Bad:

```text
POST /payment
card_number=4111111111111111
```

Better:

```text
POST /payment
card_number=[REDACTED]
```

For encrypted values, logging ciphertext is also usually unnecessary.

Prefer:

```text
payment_request_id=req_123
customer_id=cust_123
sensitive_field=present
```

rather than:

```text
sensitive_field=<ciphertext>
```

This reduces the amount of sensitive material retained in observability systems.

## Error Handling

Field-level encryption introduces additional failure modes.

Examples include:

- Invalid encryption configuration
- Missing encryption profile
- Incorrect field configuration
- Unsupported request format
- Malformed ciphertext
- Missing private key
- Wrong private key
- Expired or rotated key
- Decryption failure
- Schema mismatch

A useful architecture separates these failures:

```text
Request
  │
  ▼
CloudFront
  │
  ├── Encryption configuration failure
  │
  └── Successfully encrypted
          │
          ▼
       Origin
          │
          ▼
      Decryption
          │
          ├── Success
          │
          └── Failure
```

Decryption failures should fail closed.

Do not silently treat a failed decryption as an empty or optional value when the field is security-critical.

## Failure Semantics

For sensitive fields:

```text
Decrypt failed
      │
      ▼
Reject request
```

Avoid:

```text
Decrypt failed
      │
      ▼
Continue with empty value
      │
      ▼
Business logic
```

Failing open can create authorization, accounting, or data-integrity vulnerabilities.

## Performance Considerations

Encryption introduces computational overhead.

The impact depends on:

- Number of encrypted fields
- Payload size
- Request volume
- Cryptographic algorithm
- Key size
- Request frequency

Field-level encryption should therefore be applied selectively.

Avoid encrypting every field when only a few fields are sensitive.

Prefer:

```text
name        → plaintext
country     → plaintext
language    → plaintext
national_id → encrypted
```

instead of:

```text
Entire payload → encrypted
```

when the requirement is specifically field-level protection.

## Payload Size

Encrypted values can be larger than their plaintext representation.

For example:

```text
Plaintext
   │
   ▼
Encryption
   │
   ▼
Ciphertext
   │
   ▼
Larger encoded representation
```

This matters for:

- HTTP request size
- Network bandwidth
- Application parsing
- Logging
- API limits
- Performance testing

Do not assume encryption is size-neutral.

## Caching Considerations

Sensitive POST data should not be treated like ordinary cacheable content.

A production CloudFront architecture should ensure that sensitive request data is not accidentally cached or reused in an inappropriate context.

The general principle is:

```text
Sensitive request
      │
      ▼
Do not expose through shared cache semantics
```

Review cache behaviors, HTTP methods, cache policies, and origin request policies carefully.

Field-level encryption does not automatically make an unsafe caching configuration safe.

## Security Threat Model

Field-level encryption can reduce exposure to:

- Intermediate request-processing components
- Accidental plaintext logging
- Unnecessary service access
- Some classes of infrastructure compromise

It does not automatically protect against:

- Compromised client applications
- Malicious authenticated users
- Compromised decryption service
- Private-key compromise
- Application vulnerabilities after decryption
- Database compromise if plaintext is stored there
- Authorization flaws

The threat model should therefore remain explicit.

```text
Threat
  │
  ├── Network interception ─────► TLS
  ├── Intermediate exposure ───► Field-Level Encryption
  ├── Unauthorized user ────────► Authentication/Authorization
  ├── Data at rest ─────────────► Storage encryption
  └── Malicious HTTP traffic ───► WAF
```

## Compliance Considerations

Field-level encryption may support compliance-oriented architectures by reducing the number of systems that handle sensitive plaintext.

For example:

```text
Sensitive data
      │
      ▼
Encrypted at edge
      │
      ▼
Only trusted service decrypts
```

This can help reduce the sensitive-data exposure boundary.

However, encryption alone does not make an architecture compliant.

Compliance programs may also require:

- Access control
- Audit logging
- Key management
- Data retention policies
- Data classification
- Incident response
- Monitoring
- Secure deletion
- Operational controls

Treat field-level encryption as one technical control within the larger compliance architecture.

## Monitoring and Observability

Monitor the cryptographic path without exposing the protected data.

Useful metrics include:

- Encryption-related request failures
- Decryption failures
- Requests containing encrypted fields
- Latency introduced by cryptographic processing
- Key-management access failures
- Configuration deployment failures

Log metadata rather than sensitive values:

```text
request_id=req_123
encrypted_fields=2
decryption_status=success
key_version=v2
```

Avoid:

```text
plaintext_sensitive_value=...
```

and generally avoid logging raw ciphertext unless there is a strong operational requirement.

## Disaster Recovery

A disaster recovery plan must include cryptographic material.

A database backup without the corresponding decryption capability may be unusable.

Consider:

```text
Database Backup
      │
      ├── Encrypted data
      │
      └── Key metadata
              │
              ▼
       Key recovery process
```

A DR plan should answer:

- Where are encryption keys stored?
- How are keys recovered?
- Who can authorize recovery?
- Can the application decrypt historical data after failover?
- Are previous key versions retained?
- Is the decryption service available in the recovery region?
- How is key access audited?

Do not treat cryptographic keys as an afterthought in disaster recovery planning.

## Multi-Region Architecture

For multi-region systems:

```text
                    CloudFront
                        │
              Field-Level Encryption
                        │
            ┌───────────┴───────────┐
            │                       │
         Region A                Region B
            │                       │
       Application             Application
            │                       │
       Decryptor                Decryptor
            │                       │
        Key access              Key access
```

Both regions need a secure and operationally consistent decryption strategy.

A common mistake is to replicate encrypted data without replicating the corresponding key-management capability.

The result can be:

```text
Region A
  └── Ciphertext + Key A → Works

Region B
  └── Ciphertext + No Key A → Cannot decrypt
```

Multi-region designs should therefore treat cryptographic keys as part of the application dependency graph.

## Kubernetes Considerations

If decryption occurs inside Kubernetes, do not distribute private keys through ordinary application configuration.

A better conceptual architecture is:

```text
CloudFront
    │
    ▼
Load Balancer
    │
    ▼
Kubernetes
    │
    ▼
Dedicated Decryption Boundary
    │
    ├── Secure key access
    └── Decryption
         │
         ▼
     Application
```

Keep decryption responsibilities narrow.

Avoid making every pod capable of decrypting highly sensitive fields unless there is a clear requirement.

## Nginx Considerations

If Nginx is deployed between CloudFront and the application:

```text
CloudFront
    │
    │ encrypted field
    ▼
Nginx
    │
    │ encrypted field
    ▼
Application
```

Nginx should not need to decrypt the field.

This is one of the architectural benefits of field-level encryption: intermediate infrastructure can route requests without requiring access to the protected plaintext.

## Celery Considerations

Avoid passing sensitive plaintext through asynchronous systems unnecessarily.

A weak architecture is:

```text
HTTP Request
   │
   ▼
Application
   │ plaintext
   ▼
Celery
   │ plaintext
   ▼
Worker
```

Every queue, broker, worker, and monitoring system can potentially become part of the sensitive-data boundary.

Prefer designs where sensitive information is:

- Minimized
- Tokenized where appropriate
- Encrypted when necessary
- Accessed only by services that need it

For example:

```text
Application
   │
   ├── Non-sensitive job metadata
   │
   └── Reference to protected data
             │
             ▼
       Trusted service
```

Do not put sensitive plaintext into Celery task arguments unless the security architecture explicitly permits it.

## Kafka Considerations

The same principle applies to event-driven architectures.

Avoid:

```json
{
  "event": "customer.updated",
  "national_id": "ABC123456"
}
```

when downstream consumers do not need the sensitive field.

Instead:

```json
{
  "event": "customer.updated",
  "customer_id": "cust_123"
}
```

Field-level encryption at CloudFront does not automatically protect data once the application decrypts it and publishes plaintext to Kafka.

The entire data lifecycle must be considered.

## Common Mistakes and Pitfalls

### Confusing FLE With TLS

**Problem:** The team assumes HTTPS and field-level encryption are interchangeable.

**Correction:** TLS protects the connection; FLE protects selected fields beyond the TLS termination boundary.

### Encrypting Everything

**Problem:** Every field is encrypted regardless of sensitivity.

**Why it is problematic:**

- More computational overhead
- Larger payloads
- More complicated processing
- Harder debugging
- Greater operational complexity

**Correction:** Encrypt only fields that require this protection.

### Logging Sensitive Data

**Problem:** The application decrypts a field and then logs it.

**Correction:** Redact sensitive values and log metadata only.

### Distributing Private Keys Everywhere

**Problem:** Every microservice receives the private key.

**Correction:** Establish a narrow decryption boundary and grant access only where required.

### Storing Private Keys in Git

**Problem:**

```text
config/
└── private-key.pem
```

**Correction:** Use controlled key-management and secret-management mechanisms.

### Forgetting Key Rotation

**Problem:** Keys are created once and never rotated.

**Correction:** Define key lifecycle, rotation, versioning, retention, and rollback procedures.

### Rotating Keys Without Historical Decryption

**Problem:** Old ciphertext becomes unreadable after rotation.

**Correction:** Retain previous keys for the required data lifetime or implement controlled re-encryption.

### Assuming FLE Protects Data at Rest

**Problem:** Encrypted request fields are stored as plaintext in PostgreSQL.

**Correction:** Treat transport, field-level, and storage encryption as separate controls.

### Decrypting Too Early

**Problem:**

```text
CloudFront
  │
  ▼
Decrypt
  │
  ▼
Nginx
  │
  ▼
Multiple services
```

**Correction:** Decrypt as close as practical to the service that actually requires plaintext.

### Sending Plaintext Through Kafka or Celery

**Problem:** Sensitive data becomes available to many consumers.

**Correction:** Minimize sensitive data propagation and use references, tokenization, or encryption where appropriate.

### Assuming FLE Solves Authorization

**Problem:** The system decrypts sensitive information for any authenticated user.

**Correction:** Authorization must still determine whether the caller is allowed to access or process the data.

## Production Best Practices

### Minimize Sensitive Data

The strongest sensitive-data architecture often starts by not collecting the data.

```text
Do not collect
      >
Encrypt
      >
Restrict access
      >
Store securely
```

Avoid unnecessary sensitive fields.

### Encrypt Only What Requires It

Use field-level encryption selectively.

```text
Public fields      → plaintext
Operational fields → plaintext
Sensitive fields   → encrypted
```

### Keep Decryption Close to the Trust Boundary

```text
CloudFront
    │
    ▼
Encrypted data
    │
    ▼
Trusted service
    │
    ▼
Decrypt
```

Avoid decrypting at the first internal hop.

### Separate Cryptographic Responsibilities

A clean architecture is:

```text
HTTP Layer
    │
    ▼
Decryption Boundary
    │
    ▼
Validation
    │
    ▼
Business Logic
    │
    ▼
Persistence
```

This makes auditing and security review easier.

### Protect Keys More Aggressively Than Data

If an attacker obtains ciphertext but not the private key, the encrypted field may remain protected.

If the private key is compromised, the security boundary can collapse.

Therefore:

```text
Private key
   │
   ▼
Highest security priority
```

## Decision Matrix

| Requirement | Recommended mechanism |
|---|---|
| Encrypt network traffic | TLS |
| Encrypt selected request fields at edge | CloudFront FLE |
| Encrypt database storage | Database/storage encryption |
| Encrypt application data before persistence | Application-level encryption |
| Restrict user access | Authentication + authorization |
| Protect S3 origin | CloudFront OAC |
| Filter malicious requests | AWS WAF |
| Protect against DDoS | AWS Shield + CloudFront |
| Reduce sensitive data in microservices | Data minimization + encryption/tokenization |
| Protect payment data | Prefer specialized payment/tokenization architecture where appropriate |

## Production Checklist

### Architecture

- [ ] Sensitive fields are explicitly identified.
- [ ] The required trust boundary is documented.
- [ ] TLS remains enabled.
- [ ] Field-level encryption is applied only where justified.
- [ ] Decryption occurs at a controlled boundary.
- [ ] Intermediate infrastructure does not require plaintext.

### Keys

- [ ] Public keys are managed appropriately.
- [ ] Private keys are protected.
- [ ] Private keys are not stored in source control.
- [ ] Key rotation is documented.
- [ ] Historical key versions are retained as required.
- [ ] Key access is auditable.
- [ ] Disaster recovery includes key recovery.

### Application

- [ ] Django/FastAPI services understand encrypted-field semantics.
- [ ] Decryption is isolated from ordinary business logic.
- [ ] Sensitive values are not logged.
- [ ] Sensitive values are not unnecessarily propagated to Celery or Kafka.
- [ ] Authorization remains enforced after decryption.

### Operations

- [ ] Encryption/decryption failures are monitored.
- [ ] Configuration is managed through IaC.
- [ ] Key-management failures generate alerts.
- [ ] Performance impact is measured.
- [ ] Failure behavior is fail-closed for security-critical fields.

### Data Lifecycle

- [ ] Sensitive data is minimized.
- [ ] Encryption is applied where required.
- [ ] Data at rest is separately protected.
- [ ] Retention requirements are documented.
- [ ] Secure deletion requirements are understood.
- [ ] Historical ciphertext remains decryptable for its required lifetime.

## Interview Traps

### Does Field-Level Encryption Replace HTTPS?

No.

TLS protects the communication channel. Field-level encryption protects selected fields beyond the TLS termination boundary.

### Does CloudFront Store the Private Key?

The private decryption key should not be exposed to CloudFront. CloudFront performs encryption using the configured public-key-based encryption mechanism; decryption belongs at the trusted application boundary.

### Does FLE Encrypt the Entire Request?

No. It is designed to encrypt configured fields rather than the entire request payload.

### Can Nginx Read the Encrypted Field?

It can route and forward the request, but it does not need access to the plaintext field.

That is one of the reasons to introduce field-level encryption.

### Does FLE Protect a PostgreSQL Database?

Not automatically.

If the application decrypts the field and stores plaintext in PostgreSQL, database-level protection remains a separate requirement.

### What Happens If the Private Key Is Lost?

Historical ciphertext encrypted under that key may become undecryptable.

This is why key backup, retention, rotation, and disaster recovery are critical.

### Should Every Microservice Have the Private Key?

No.

The private key should be restricted to services that actually require decryption.

### Does FLE Prevent a Compromised Application From Reading the Data?

No.

Once a trusted service decrypts the field, an attacker who compromises that service may potentially access the plaintext.

FLE reduces exposure across infrastructure boundaries; it does not eliminate application compromise risk.

## Key Takeaways

- **CloudFront field-level encryption protects selected request fields beyond the TLS termination boundary, reducing plaintext exposure across intermediate infrastructure.**
- **FLE complements HTTPS rather than replacing it; TLS protects the connection while field-level encryption protects specific data fields.**
- **The private decryption key is the critical trust boundary and should be tightly controlled, rotated, audited, and included in disaster recovery planning.**
- **Decrypt sensitive data as late as practical and avoid unnecessarily propagating plaintext through Nginx, microservices, Celery, Kafka, logs, or databases.**
- **Field-level encryption is one layer of a broader security architecture that should also address authorization, origin protection, data-at-rest encryption, key management, and data minimization.**