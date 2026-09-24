# 06- TLS and Encryption

## Overview

MongoDB security uses multiple encryption layers to protect data throughout its lifecycle.

A production deployment should distinguish between:

```text
Encryption in Transit
        ↓
TLS protects network communication

Encryption at Rest
        ↓
Protects persisted database files and storage

Encryption in Use
        ↓
Protects selected sensitive fields from database-side plaintext exposure

Application / Database Authorization
        ↓
Controls who can access the data
```

These mechanisms solve different security problems and should be designed together.

For example:

```text
FastAPI
   ↓
TLS
   ↓
MongoDB
   ↓
Encrypted storage

Sensitive field
   ↓
Queryable Encryption / CSFLE
   ↓
Encrypted value on server
```

TLS protects the connection. Encryption at rest protects stored data. Client-side field-level encryption or Queryable Encryption can protect selected sensitive fields even from parties with access to the database server.

MongoDB currently provides two principal approaches for in-use field encryption: Queryable Encryption and Client-Side Field Level Encryption (CSFLE). They should not be treated as interchangeable features because their query capabilities and operational characteristics differ. :contentReference[oaicite:0]{index=0}

---

## Encryption Layers

| Layer | Protects | Typical Threat | MongoDB Technology |
|---|---|---|---|
| Transport | Network traffic | Network interception | TLS |
| At rest | Database files | Disk or storage compromise | Encryption at rest |
| Field level | Selected sensitive fields | Database/server exposure | CSFLE |
| Queryable field encryption | Selected sensitive fields while retaining supported queries | Database-side plaintext exposure | Queryable Encryption |
| Authorization | Operations | Unauthorized database access | Roles and privileges |
| Secret management | Credentials and keys | Credential/key compromise | KMS / Secrets Manager / Vault |

A mature security architecture normally combines several of these layers instead of relying on a single encryption mechanism.

---

## Threat Model

Encryption should be selected based on the threat being addressed.

| Threat | TLS | Encryption at Rest | Field-Level Encryption |
|---|---:|---:|---:|
| Network sniffing | Yes | No | Yes, but TLS is still required |
| Stolen database files | No | Yes | Yes |
| Stolen backup files | No | Depends on backup encryption | Yes |
| Database superuser reading plaintext fields | No | No | Yes, for appropriately encrypted fields |
| Application credential compromise | No | No | Limited; application may still possess decryption keys |
| Unauthorized application operation | No | No | No; use authorization |

MongoDB documents encryption mechanisms as complementary controls rather than replacements for one another. :contentReference[oaicite:1]{index=1}

---

## TLS

TLS protects MongoDB traffic while it travels between a client and MongoDB.

Without TLS:

```text
Application
    ↓
Network
    ↓
MongoDB
```

With TLS:

```text
Application
    ↓
Encrypted TLS connection
    ↓
MongoDB
```

TLS protects against network-level interception and helps establish the identity of the server through certificate validation.

---

## TLS Handshake

A simplified connection lifecycle is:

```mermaid
sequenceDiagram
    participant App as Application
    participant DB as MongoDB

    App->>DB: TCP connection
    App->>DB: TLS ClientHello
    DB->>App: TLS ServerHello + Certificate
    App->>App: Validate certificate
    App->>DB: Key exchange / handshake
    DB->>App: TLS session established
    App->>DB: MongoDB authentication
    DB->>App: Authentication result
    App->>DB: Database operation
    DB->>App: Encrypted response
```

The exact TLS handshake depends on the negotiated protocol and cryptographic configuration, but the important backend principle is:

```text
TCP connectivity
    ↓
TLS negotiation
    ↓
Certificate validation
    ↓
Encrypted session
    ↓
MongoDB authentication
    ↓
Authorization
    ↓
Database operation
```

---

## TLS vs MongoDB Authentication

TLS and authentication are separate controls.

```text
TLS
    ↓
Is this connection protected?
Is the server identity trusted?

MongoDB Authentication
    ↓
Which database identity is connecting?
```

For example:

```text
TLS
    ↓
Valid MongoDB server certificate

SCRAM
    ↓
orders_service authenticated

Role
    ↓
orders_service can read/write orders
```

Enabling TLS does not automatically grant database access.

---

## TLS Certificate Architecture

A production certificate hierarchy commonly looks like:

```text
Certificate Authority
        │
        ├── MongoDB Server Certificate
        │
        └── Optional Client Certificates
```

For server-authenticated TLS:

```text
Application
    ↓
Trusts CA
    ↓
Receives MongoDB certificate
    ↓
Validates certificate chain
    ↓
Validates server identity
    ↓
Establishes encrypted session
```

The certificate authority should be managed independently from application credentials.

---

## MongoDB TLS Configuration

A self-managed MongoDB deployment can be configured to require TLS.

Example:

```yaml
net:
  port: 27017
  bindIp: 10.20.1.10
  tls:
    mode: requireTLS
    certificateKeyFile: /etc/mongodb/tls/server.pem
    CAFile: /etc/mongodb/tls/ca.pem
```

The actual certificate paths, CA hierarchy, and deployment configuration depend on the environment.

The important production property is:

```text
requireTLS
```

rather than allowing unintended plaintext connections.

---

## TLS Certificate Requirements

Production certificates should be:

- issued by a trusted or explicitly managed CA
- valid for the MongoDB hostname
- unexpired
- appropriately scoped
- securely stored
- rotated before expiration

The certificate's identity should correspond to the hostname used by clients.

For example:

```text
mongodb.internal.example.com
```

should resolve to MongoDB and be represented appropriately in the certificate's identity fields.

---

## Certificate Validation

Certificate validation should verify the server identity rather than simply checking that a certificate exists.

Important validation properties include:

- trusted CA
- certificate chain
- validity period
- hostname
- intended certificate usage

PyMongo verifies MongoDB's certificate when TLS is enabled. The driver supports specifying a custom CA through `tlsCAFile`. :contentReference[oaicite:2]{index=2}

---

## PyMongo TLS Configuration

A production Python application can configure TLS explicitly:

```python
from pymongo import MongoClient

client = MongoClient(
    mongodb_uri,
    tls=True,
    tlsCAFile="/etc/mongodb/tls/ca.pem",
    serverSelectionTimeoutMS=5_000,
    connectTimeoutMS=5_000,
    socketTimeoutMS=10_000,
)
```

For managed environments using publicly trusted certificates, a custom CA file may not be necessary.

For private PKI, provide the appropriate CA bundle.

---

## TLS Connection String

TLS can also be configured in the connection string:

```text
mongodb://username:password@mongodb.internal.example:27017/orders?tls=true&authSource=admin
```

Keep secrets outside source control.

A better application configuration model is:

```python
import os

mongodb_uri = os.environ["MONGODB_URI"]

client = MongoClient(
    mongodb_uri,
    tls=True,
)
```

Production deployments can inject the connection string through a secret-management system.

---

## MongoDB SRV Connections

Managed MongoDB deployments commonly use:

```text
mongodb+srv://...
```

With PyMongo, SRV connection strings enable TLS by default. :contentReference[oaicite:3]{index=3}

Even when TLS is automatically enabled, application configuration should still be reviewed to ensure certificate validation and other security settings match production requirements.

---

## Insecure TLS Settings

Development environments sometimes use options that bypass certificate validation.

Examples include:

```python
tlsAllowInvalidCertificates=True
```

or:

```python
tlsAllowInvalidHostnames=True
```

These settings weaken TLS identity verification.

MongoDB's current PyMongo documentation explicitly warns against using insecure TLS settings in production. :contentReference[oaicite:4]{index=4}

Avoid:

```python
client = MongoClient(
    mongodb_uri,
    tls=True,
    tlsAllowInvalidCertificates=True,
)
```

as a production configuration.

If certificate validation fails, fix the certificate or trust configuration instead.

---

## Common TLS Failure

A common error pattern is:

```text
certificate verify failed
```

Possible causes include:

- incorrect CA bundle
- expired certificate
- hostname mismatch
- incomplete certificate chain
- incorrect certificate purpose
- client using an unexpected trust store

Do not solve this by disabling certificate verification.

---

## TLS Protocol Compatibility

TLS failures can also result from incompatible TLS/OpenSSL versions.

For example:

```text
TLSV1_ALERT_PROTOCOL_VERSION
```

can indicate that the client-side OpenSSL stack does not support a protocol version accepted by the deployment. PyMongo's documentation notes that older operating systems may provide OpenSSL versions that cannot negotiate sufficiently modern TLS versions. :contentReference[oaicite:5]{index=5}

A production troubleshooting sequence is:

```text
Application
    ↓
Python version
    ↓
PyMongo version
    ↓
OpenSSL version
    ↓
Operating system
    ↓
MongoDB TLS configuration
```

---

## TLS and Replica Sets

TLS must be considered for both:

```text
Application → MongoDB
```

and, where configured, MongoDB's internal member communication.

A replica set might look like:

```text
              ┌──────────────┐
              │ Application  │
              └──────┬───────┘
                     │ TLS
                     ▼
               ┌───────────┐
               │  Primary  │
               └─────┬─────┘
                  TLS│
              ┌──────┴──────┐
              ▼             ▼
        ┌───────────┐ ┌───────────┐
        │ Secondary │ │ Secondary │
        └───────────┘ └───────────┘
```

Firewall rules and certificate configuration must support the complete topology.

---

## TLS and Sharding

A sharded cluster adds additional network paths:

```text
Application
    ↓
mongos
    ↓
Shard Replica Sets
```

and:

```text
mongos
    ↓
Config Server Replica Set
```

TLS requirements should therefore be evaluated across all required communication paths rather than only the application-to-`mongos` connection.

---

## TLS and Kubernetes

A Kubernetes deployment can mount certificates into application pods:

```text
Secret / External Secret
        ↓
Pod Volume
        ↓
FastAPI / Django
        ↓
PyMongo
        ↓
TLS
        ↓
MongoDB
```

Avoid storing private keys directly in Git.

Prefer:

- Kubernetes Secrets with appropriate controls
- external secret managers
- AWS Secrets Manager
- AWS Certificate Manager where applicable
- dedicated PKI systems

---

## TLS Certificate Rotation

Certificates expire.

A production rotation process should be:

```text
New certificate issued
        ↓
Deploy trusted CA / certificate
        ↓
Validate connectivity
        ↓
Switch certificate
        ↓
Monitor connections
        ↓
Retire old certificate
```

The rotation mechanism should avoid unnecessary application downtime.

---

## Certificate Rotation Failure Modes

Potential failures include:

- certificate expired
- CA not trusted
- server certificate changed unexpectedly
- hostname changed
- clients using stale CA files
- replica-set members unable to establish TLS
- rolling deployment leaving mixed trust configurations

Certificate rotation should therefore be tested before production expiration.

---

## Encryption at Rest

Encryption at rest protects MongoDB's persisted data from unauthorized access to storage media or database files.

Conceptually:

```text
Application
    ↓
MongoDB
    ↓
Encrypted Database Files
    ↓
Encrypted Storage
```

Encryption at rest does not protect network traffic.

That is the responsibility of TLS.

---

## Encryption at Rest vs TLS

| Property | TLS | Encryption at Rest |
|---|---|---|
| Protects network traffic | Yes | No |
| Protects database files | No | Yes |
| Protects backups automatically | No | Depends on backup encryption |
| Protects in-memory plaintext | No | No |
| Protects against network sniffing | Yes | No |
| Main boundary | Network | Storage |

A production system commonly needs both.

---

## Encryption at Rest Architecture

A typical architecture is:

```text
Application
    ↓
TLS
    ↓
MongoDB
    ↓
Encrypted storage engine files
    ↓
Disk / Volume
```

The storage encryption key should itself be protected.

A stronger model is:

```text
Application Data
      ↓
MongoDB Encryption
      ↓
Data Encryption Key
      ↓
Key Management System
      ↓
Master / Key Encryption Key
```

The exact implementation depends on MongoDB edition, deployment model, and key-management architecture.

---

## Key Management

Encryption is only as strong as the key-management process.

Important considerations include:

- key generation
- key storage
- key rotation
- access control
- backup
- recovery
- auditability
- separation of duties

Do not store encryption keys beside encrypted database files without an independent protection mechanism.

---

## AWS KMS

In AWS environments, a key-management service can provide centralized control over encryption keys.

Conceptually:

```text
MongoDB
   ↓
Encryption Key
   ↓
AWS KMS
   ↓
IAM-controlled key access
```

The key-management system should be protected independently from the MongoDB workload.

---

## Managed MongoDB

MongoDB Atlas can provide managed encryption and key-management capabilities depending on the selected deployment and configuration.

The architecture should still distinguish:

```text
TLS
    ↓
Transport encryption

Encryption at rest
    ↓
Storage protection

Client-side field encryption
    ↓
Application-controlled sensitive fields
```

Do not assume that enabling one automatically enables every other layer.

---

## Backup Encryption

Backups are copies of database data and therefore need their own security controls.

A secure backup architecture should consider:

```text
Production Data
    ↓
Encrypted Database
    ↓
Backup
    ↓
Encrypted Backup Storage
    ↓
Access-Controlled Recovery Environment
```

Encryption at rest for the live database does not automatically answer every question about backup protection.

Verify:

- backup encryption
- backup key ownership
- access controls
- key retention
- restore environment security

---

## Encryption in Use

Encryption in use refers to protecting sensitive fields while they are stored and processed through the database workflow.

MongoDB provides:

- Queryable Encryption
- Client-Side Field Level Encryption

Both allow applications to encrypt sensitive fields before the data is sent to MongoDB. :contentReference[oaicite:6]{index=6}

This creates a model such as:

```text
Application
    ↓
Encrypt sensitive field
    ↓
TLS
    ↓
MongoDB
    ↓
Encrypted field
```

The database server does not receive the field in normal plaintext form.

---

## When Field-Level Encryption Is Useful

Field-level encryption is particularly relevant for sensitive information such as:

- financial information
- health information
- personally identifiable information
- payment-related values
- sensitive addresses
- regulated customer attributes

MongoDB specifically documents these classes of sensitive information as potential use cases for in-use encryption. :contentReference[oaicite:7]{index=7}

Do not encrypt every field automatically. Encryption changes storage, query, indexing, operational, and application behavior.

---

## Queryable Encryption

Queryable Encryption allows selected sensitive fields to remain encrypted while supporting supported query types.

Conceptually:

```text
Application
    ↓
Plaintext value
    ↓
Client-side encryption
    ↓
Encrypted query
    ↓
MongoDB
    ↓
Encrypted storage
```

MongoDB documents Queryable Encryption as a client-side encryption approach where sensitive fields are stored as randomized encrypted data while supported queries remain possible. :contentReference[oaicite:8]{index=8}

---

## Queryable Encryption Capabilities

Current MongoDB documentation describes support for:

- equality queries
- range queries
- prefix queries
- suffix queries
- substring queries

The availability of some string query types depends on MongoDB server and driver versions; prefix, suffix, and substring support are documented as Public Preview in current documentation. Range queries require MongoDB Server 8.0 or later. :contentReference[oaicite:9]{index=9}

Do not design production dependencies around preview functionality without explicitly evaluating its maturity and compatibility.

---

## Queryable Encryption Example

Suppose a customer document contains:

```json
{
  "_id": "...",
  "name": "Customer",
  "national_id": "sensitive-value"
}
```

A Queryable Encryption architecture can keep:

```text
name
    ↓
Normal MongoDB field

national_id
    ↓
Encrypted field
```

The application can query supported encrypted fields without exposing their plaintext representation to MongoDB.

---

## Queryable Encryption and Schema Design

Encryption should be considered before creating production collections.

MongoDB documents that changing which fields are encrypted or queryable can require rebuilding encryption metadata and recreating the collection. :contentReference[oaicite:10]{index=10}

Therefore:

```text
Business requirement
    ↓
Identify sensitive fields
    ↓
Identify query requirements
    ↓
Select encryption approach
    ↓
Design schema
    ↓
Implement
```

Do not treat encryption as a purely operational toggle after the schema is already mature.

---

## Client-Side Field Level Encryption

CSFLE encrypts selected fields in the application before sending them to MongoDB.

```text
Application
    ↓
CSFLE
    ↓
Encrypted document
    ↓
MongoDB
```

MongoDB itself does not receive the plaintext value for the encrypted field. :contentReference[oaicite:11]{index=11}

This can provide strong protection against database-side plaintext exposure.

---

## Deterministic Encryption

CSFLE supports deterministic encryption.

Conceptually:

```text
plaintext A
    ↓
ciphertext X

plaintext A
    ↓
ciphertext X
```

Because the same plaintext can produce the same encrypted representation, deterministic encryption can support equality queries.

However, repeated ciphertext can reveal frequency information, particularly for low-cardinality fields. MongoDB explicitly documents this frequency-analysis risk. :contentReference[oaicite:12]{index=12}

---

## Randomized Encryption

Randomized encryption produces different ciphertext for the same plaintext.

Conceptually:

```text
plaintext A
    ↓
ciphertext X

plaintext A
    ↓
ciphertext Y
```

This improves confidentiality against frequency analysis, but prevents the same query capabilities available for deterministically encrypted CSFLE fields.

MongoDB documents randomized CSFLE encryption as unsuitable for queries that need to evaluate the encrypted field. :contentReference[oaicite:13]{index=13}

---

## Deterministic vs Randomized Encryption

| Property | Deterministic CSFLE | Randomized CSFLE |
|---|---|---|
| Same input → same ciphertext | Yes | No |
| Equality queries | Supported | Not supported |
| Frequency leakage | Higher | Lower |
| Query flexibility | Higher | Lower |
| Confidentiality | Lower than randomized for low-cardinality data | Stronger |
| Suitable for | Carefully selected searchable fields | Sensitive non-query fields |

Do not choose deterministic encryption simply because it is easier to query.

First determine whether the field's value distribution makes frequency analysis a concern.

---

## Queryable Encryption vs CSFLE

| Consideration | Queryable Encryption | CSFLE |
|---|---|---|
| Client-side encryption | Yes | Yes |
| Encrypted at server | Yes | Yes |
| Equality queries | Supported | Deterministic mode |
| Range queries | Supported | Not generally equivalent |
| Randomized ciphertext | Yes | Randomized mode available |
| Multiple keys for same field | More constrained | More flexible |
| Existing CSFLE deployments | Migration consideration | Natural fit |
| New applications | Strong candidate | Useful for specific requirements |

MongoDB's current guidance describes Queryable Encryption as the newer approach for applications requiring supported queries over encrypted data, while CSFLE remains useful for existing deployments and scenarios requiring different keys for the same field. :contentReference[oaicite:14]{index=14}

---

## Encryption Keys

Field-level encryption introduces an additional key hierarchy.

A conceptual model is:

```text
Key Management Service
        ↓
Customer Master Key
        ↓
Data Encryption Key
        ↓
Encrypted Field
```

The application needs access to the appropriate encryption keys to decrypt protected data.

Therefore:

```text
Database compromise
    ≠
Automatic access to plaintext
```

if the attacker does not also possess the required encryption keys.

MongoDB documents that applications require access to the encryption keys to decrypt in-use encrypted data. :contentReference[oaicite:15]{index=15}

---

## Key Management Services

MongoDB in-use encryption can integrate with supported key-management mechanisms.

Examples include:

- AWS KMS
- Azure Key Vault
- Google Cloud KMS
- locally managed keys

MongoDB's `mongosh` and driver documentation describe these mechanisms for managing customer master keys in in-use encryption configurations. :contentReference[oaicite:16]{index=16}

The KMS should be treated as a security-critical dependency.

---

## Key Rotation

Encryption keys should have a defined lifecycle.

A production key-management process includes:

```text
Generate
   ↓
Store securely
   ↓
Use
   ↓
Monitor
   ↓
Rotate
   ↓
Retain required historical keys
   ↓
Retire safely
```

Key rotation is not the same as deleting old keys.

Historical encrypted data may still require old key material for decryption.

---

## Encryption and Multi-Tenancy

Multi-tenant systems may have stronger requirements.

For example:

```text
Tenant A
    ↓
Tenant-specific encryption key

Tenant B
    ↓
Tenant-specific encryption key
```

This can provide stronger cryptographic isolation but introduces additional complexity:

- key management
- key rotation
- tenant provisioning
- tenant deletion
- recovery
- operational tooling
- application performance

CSFLE can be preferable in scenarios requiring different keys for the same field, according to MongoDB's current guidance. :contentReference[oaicite:17]{index=17}

---

## Encryption and Search

Encryption can fundamentally change query behavior.

Before encryption:

```javascript
{
  national_id: "123456789"
}
```

After encryption:

```text
national_id
    ↓
encrypted representation
```

The application may no longer be able to use:

- arbitrary regex searches
- unsupported comparison operators
- unrestricted sorting
- arbitrary aggregation expressions

Therefore query requirements must be evaluated before selecting the encryption mechanism.

---

## Encryption and Indexes

Encrypted fields can change indexing behavior and query performance.

Queryable Encryption uses additional encryption metadata and structures, and enabling queryability increases storage requirements and affects query performance. :contentReference[oaicite:18]{index=18}

Before encrypting a field, determine:

```text
Do we search it?
Do we sort it?
Do we index it?
Do we aggregate it?
How frequently is it accessed?
What latency is acceptable?
```

---

## Encryption and Aggregation

Aggregation pipelines can become more constrained when sensitive fields are encrypted.

For example:

```text
Normal field
    ↓
$match
$sort
$group
$project
```

may not translate directly to:

```text
Encrypted field
    ↓
Same aggregation operations
```

Only supported encrypted query and operation semantics should be assumed.

Do not encrypt a field without validating all production queries that depend on it.

---

## Encryption and Application Logging

Encryption does not automatically protect plaintext before encryption.

Consider:

```python
customer_id = request.json["national_id"]

logger.info("Received national_id=%s", customer_id)

encrypted_value = encrypt(customer_id)
```

The database field is protected, but the log contains the plaintext.

Prefer:

```python
logger.info("Processing customer identity")
```

and never log sensitive plaintext values unnecessarily.

---

## Encryption and Error Messages

The same principle applies to exceptions.

Avoid:

```python
raise ValueError(
    f"Failed processing national_id={national_id}"
)
```

because the value may appear in:

- application logs
- tracing systems
- error monitoring
- CI logs
- support dashboards

Sensitive data should be protected across the entire data lifecycle, not only in MongoDB storage.

---

## Encryption and Backups

A field-encrypted value remains encrypted when stored in backups.

This provides an additional protection layer:

```text
Application
    ↓
Field encryption
    ↓
MongoDB
    ↓
Backup
```

However, backup systems still require:

- access control
- encryption
- key protection
- retention policies
- auditability
- restore testing

Field encryption should not be used as a substitute for secure backup architecture.

---

## Encryption and Disaster Recovery

A disaster recovery environment needs access to the appropriate keys.

A restore can fail even when the database backup is valid:

```text
Backup restored
    ↓
Encrypted fields present
    ↓
Encryption keys unavailable
    ↓
Application cannot decrypt data
```

Therefore DR testing must include:

```text
Database backup
+
KMS / key access
+
Secrets
+
TLS certificates
+
Application configuration
```

---

## Python Encryption Architecture

A production Python service can be structured as:

```text
FastAPI / Django
       ↓
Service Layer
       ↓
Repository
       ↓
MongoClient
       ↓
Encryption Configuration
       ↓
MongoDB
```

Encryption configuration should be initialized during application startup rather than reconstructed for every request.

---

## FastAPI Lifecycle

A production FastAPI application should maintain database and encryption-related resources across the process lifecycle.

Conceptually:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import AsyncMongoClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncMongoClient(
        mongodb_uri,
        tls=True,
    )

    app.state.mongo_client = client

    try:
        yield
    finally:
        await client.close()


app = FastAPI(lifespan=lifespan)
```

Encryption-specific configuration should follow the same lifecycle principle.

Use the current PyMongo async APIs when an asynchronous application architecture is required. :contentReference[oaicite:19]{index=19}

---

## Synchronous vs Asynchronous Python Clients

Modern PyMongo provides both synchronous and asynchronous client APIs.

For synchronous applications:

```python
from pymongo import MongoClient

client = MongoClient(
    mongodb_uri,
    tls=True,
)
```

For asynchronous applications:

```python
from pymongo import AsyncMongoClient

client = AsyncMongoClient(
    mongodb_uri,
    tls=True,
)
```

The choice should align with the application's concurrency architecture rather than being made solely because MongoDB supports async APIs.

---

## Django Integration

Django applications using MongoDB through PyMongo or MongoEngine should treat TLS and encryption as infrastructure concerns.

Conceptually:

```text
Django
   ↓
Service / Repository
   ↓
MongoDB Driver
   ↓
TLS
   ↓
MongoDB
```

Do not assume Django's relational database configuration automatically provides MongoDB-specific encryption behavior.

Explicitly configure:

- TLS
- CA trust
- credentials
- encryption settings
- connection timeouts
- key-management configuration

---

## Docker and TLS Certificates

Certificates can be mounted into containers:

```yaml
services:
  api:
    volumes:
      - ./certs/ca.pem:/etc/mongodb/tls/ca.pem:ro
```

Production systems should avoid managing private production certificates through local bind mounts.

Prefer:

- secret volumes
- external secret stores
- workload identity
- managed certificate distribution

---

## Kubernetes Certificate Management

A Kubernetes architecture may look like:

```text
Certificate Authority
        ↓
Certificate Secret / External Secret
        ↓
Pod
        ↓
PyMongo
        ↓
TLS
        ↓
MongoDB
```

Certificate renewal should be automated where practical.

The application should be restarted or reloaded according to the certificate-management strategy when updated credentials need to be consumed.

---

## Performance Impact

Encryption introduces overhead.

Potential costs include:

- TLS handshake CPU
- encrypted network processing
- encryption/decryption CPU
- larger encrypted documents
- additional Queryable Encryption metadata
- additional storage
- query execution overhead
- key-management interactions

The correct question is not:

```text
Does encryption have overhead?
```

It does.

The engineering question is:

```text
What security boundary do we require,
and what performance budget can support it?
```

---

## TLS Performance

TLS connection establishment can be relatively expensive compared with reusing an existing connection.

Therefore:

```text
Bad
Request
  ↓
New MongoClient
  ↓
TLS handshake
  ↓
Query
  ↓
Close

Good
Application Process
  ↓
Long-lived MongoClient
  ↓
Connection Pool
  ↓
TLS connections reused
```

This is one reason long-lived `MongoClient` instances are important in Python services.

---

## Field Encryption Performance

Field-level encryption can affect:

- write latency
- read latency
- CPU
- document size
- query performance
- indexing behavior

Benchmark encrypted workloads with realistic:

- document sizes
- query rates
- concurrency
- field cardinality
- query patterns

Do not estimate encryption overhead using toy data.

---

## Encryption and Connection Pooling

A production service should normally reuse a MongoDB client.

```python
client = MongoClient(
    mongodb_uri,
    tls=True,
    maxPoolSize=100,
)
```

The appropriate pool size depends on:

- application concurrency
- request rate
- MongoDB capacity
- query latency
- number of application replicas

Do not increase pool size simply because connection establishment appears slow.

---

## Monitoring TLS

Monitor:

- TLS handshake failures
- certificate expiration
- connection failures
- connection latency
- authentication failures
- unexpected client versions
- replica-set connectivity
- application error rates

Certificate expiration should have alerting well before the actual expiration date.

---

## Monitoring Encryption

For field-level encryption, monitor:

- encryption/decryption failures
- KMS availability
- key-access failures
- increased query latency
- storage growth
- application CPU
- encrypted query failures
- schema/encryption configuration drift

A KMS outage can become an application availability issue if the application cannot obtain required encryption keys.

---

## Secret Management

Separate these assets:

```text
MongoDB Password
TLS Private Key
TLS CA
Customer Master Key
Data Encryption Key
KMS Credentials
```

They should not all be stored in the same location or protected by the same access policy.

A compromise of one secret should not automatically compromise every security layer.

---

## Key Separation

A mature architecture should use separation of duties.

For example:

```text
Application Team
    ↓
MongoDB application credential

Security / Platform
    ↓
KMS key administration

Database Operations
    ↓
MongoDB operational access
```

The exact organizational model varies, but cryptographic key administration should receive stronger controls than ordinary application configuration.

---

## Common TLS Mistakes

### Disabling Certificate Validation

**Problem:**

```python
tlsAllowInvalidCertificates=True
```

**Why it happens:** Certificate configuration is inconvenient during development.

**Risk:** Server identity verification is weakened.

**Prevention:** Fix CA and certificate configuration.

---

### Treating Private Networking as a Replacement for TLS

**Problem:** MongoDB is inside a VPC, so TLS is disabled.

**Risk:** Network isolation and transport encryption solve different problems.

**Prevention:** Use both private networking and TLS.

---

### Ignoring Certificate Expiration

**Problem:** The application suddenly loses database connectivity.

**Risk:** Preventable production outage.

**Prevention:** Monitor certificate expiration and automate rotation.

---

### Sharing TLS Private Keys

**Problem:** One certificate/private key is copied into many workloads.

**Risk:** Compromise of one workload can expose the key.

**Prevention:** Use workload-appropriate certificates and controlled secret distribution.

---

## Common Encryption Mistakes

### Encrypting Every Field

**Problem:** Application complexity and performance increase unnecessarily.

**Risk:** Queries, indexes, aggregations, and operational workflows become harder.

**Prevention:** Classify data and encrypt fields according to threat and compliance requirements.

---

### Encrypting Without Query Analysis

**Problem:** A field is encrypted and existing queries stop working.

**Risk:** Production functionality breaks.

**Prevention:** Inventory queries before enabling field encryption.

---

### Logging Plaintext Sensitive Data

**Problem:** Database storage is encrypted but logs contain plaintext.

**Risk:** Sensitive data remains exposed.

**Prevention:** Redact sensitive fields from logs, traces, errors, and metrics.

---

### Storing Encryption Keys With the Database

**Problem:** Database compromise also exposes key material.

**Risk:** Encryption loses much of its intended protection.

**Prevention:** Use independent key management and access controls.

---

### Treating KMS Availability as Irrelevant

**Problem:** Application cannot decrypt data when key-management access fails.

**Risk:** Database operations can become unavailable.

**Prevention:** Include KMS and key access in availability and disaster-recovery planning.

---

## Troubleshooting TLS

Use a layered process:

```text
Symptom
↓
Possible causes
↓
Isolation strategy
↓
Diagnostic commands
↓
Root cause
↓
Corrective action
↓
Prevention
```

### Symptom

Examples:

```text
SSL handshake failed
```

```text
certificate verify failed
```

```text
TLSV1_ALERT_PROTOCOL_VERSION
```

### Possible Causes

- expired certificate
- hostname mismatch
- incorrect CA
- incomplete CA chain
- unsupported TLS protocol
- incompatible OpenSSL version
- incorrect certificate permissions
- wrong certificate file
- MongoDB configured with incompatible TLS requirements
- client configured for the wrong hostname

### Isolation Strategy

Start with:

```text
DNS
 ↓
TCP
 ↓
TLS
 ↓
Authentication
 ↓
Authorization
```

Do not change MongoDB authorization until TLS succeeds.

### Diagnostic Commands

Check DNS:

```bash
dig mongodb.internal.example.com
```

Check TCP:

```bash
nc -vz mongodb.internal.example.com 27017
```

Inspect the TLS certificate:

```bash
openssl s_client \
  -connect mongodb.internal.example.com:27017 \
  -servername mongodb.internal.example.com \
  -showcerts
```

Inspect certificate dates:

```bash
openssl x509 \
  -in server.pem \
  -noout \
  -dates \
  -subject \
  -issuer
```

Check OpenSSL:

```bash
openssl version
```

### Root Cause

Determine which layer failed:

```text
DNS
    ↓
TCP
    ↓
Certificate exchange
    ↓
Certificate validation
    ↓
TLS negotiation
    ↓
MongoDB authentication
```

### Corrective Action

Fix the specific failing layer.

Examples:

```text
Wrong CA
    ↓
Deploy correct CA bundle
```

```text
Expired certificate
    ↓
Rotate certificate
```

```text
Hostname mismatch
    ↓
Use correct DNS name or issue correct certificate
```

```text
Unsupported protocol
    ↓
Upgrade client/OpenSSL or align supported TLS configuration
```

### Prevention

Use:

- automated certificate rotation
- certificate expiration monitoring
- supported Python/OpenSSL versions
- infrastructure-as-code
- pre-production TLS tests
- documented certificate ownership

---

## Troubleshooting Field Encryption

### Symptom

```text
Encrypted field cannot be queried
```

### Possible Causes

- field not configured as queryable
- unsupported query operator
- incorrect encryption schema
- wrong encryption keys
- driver configuration mismatch
- incompatible driver/server versions
- field encrypted using an incompatible approach

### Isolation Strategy

Determine:

```text
Which encryption mechanism?
    ↓
Queryable Encryption or CSFLE
    ↓
Which field?
    ↓
Which query type?
    ↓
Which driver?
    ↓
Which MongoDB server version?
```

### Root Cause

For example:

```text
Encrypted field
    ↓
Regex query
    ↓
Unsupported encrypted operation
```

The solution is not to disable encryption automatically. Re-evaluate the query requirement and encryption design.

### Prevention

Document for every encrypted field:

```text
Field
Encryption mechanism
Query requirements
Key ownership
Rotation process
Recovery process
Application owner
```

---

## Production Security Architecture

```mermaid
flowchart TB
    APP[FastAPI / Django / Worker]
    TLS[TLS]
    AUTH[MongoDB Authentication]
    RBAC[MongoDB Authorization]
    DB[(MongoDB)]
    ATREST[Encryption at Rest]
    KMS[KMS / Key Management]
    FE[Queryable Encryption / CSFLE]
    LOG[Logs / Monitoring]

    APP --> TLS
    TLS --> AUTH
    AUTH --> RBAC
    RBAC --> DB
    DB --> ATREST
    ATREST --> KMS

    APP --> FE
    FE --> TLS

    APP --> LOG
    DB --> LOG
    KMS --> LOG
```

The layers address different risks:

```text
TLS
    ↓
Protect network traffic

Authentication
    ↓
Establish identity

Authorization
    ↓
Restrict database operations

Encryption at rest
    ↓
Protect persisted data

Field-level encryption
    ↓
Protect selected sensitive fields

KMS
    ↓
Protect encryption keys

Monitoring
    ↓
Detect operational/security failures
```

---

## Production Encryption Checklist

### TLS

- [ ] Production MongoDB connections use TLS.
- [ ] Server certificates are validated.
- [ ] Trusted CA certificates are managed securely.
- [ ] Invalid certificate bypasses are disabled.
- [ ] Certificate expiration is monitored.
- [ ] TLS configuration is tested during deployment.

### Encryption at Rest

- [ ] Production database storage is encrypted.
- [ ] Encryption keys are independently protected.
- [ ] Backup storage is separately reviewed.
- [ ] Key access is audited.
- [ ] Key rotation is documented.
- [ ] Recovery procedures include key availability.

### Field-Level Encryption

- [ ] Sensitive fields are identified.
- [ ] Query requirements are documented before encryption.
- [ ] Queryable Encryption or CSFLE is selected intentionally.
- [ ] Encryption keys are protected independently.
- [ ] Encrypted-field queries are tested.
- [ ] Performance impact is benchmarked.
- [ ] Key rotation and recovery are tested.

### Application

- [ ] Sensitive values are not logged.
- [ ] MongoDB credentials are stored in a secret manager.
- [ ] TLS certificates are not committed to Git.
- [ ] Long-lived MongoDB clients are reused.
- [ ] Connection timeouts are configured.
- [ ] Encryption failures are observable.

### Operations

- [ ] TLS failures are monitored.
- [ ] Certificate expiration is monitored.
- [ ] KMS failures are monitored.
- [ ] Encryption configuration is version-controlled where appropriate.
- [ ] Disaster recovery includes encryption keys and certificates.
- [ ] Restore testing validates encrypted data access.

## Interview Considerations

### What does TLS protect?

TLS protects MongoDB traffic while it travels between client and server. It does not protect database files on disk.

### Does TLS encrypt MongoDB data at rest?

No. TLS protects network traffic. Encryption at rest protects persisted database data.

### Does encryption at rest protect data in application memory?

No. Once the application decrypts data, the plaintext exists in application memory.

### Why use field-level encryption?

To protect selected sensitive fields from plaintext exposure to database-side systems and storage, even when database files or server-side access are compromised.

### What is the difference between CSFLE and Queryable Encryption?

Both encrypt sensitive fields client-side, but their supported query capabilities and key/schema characteristics differ. Queryable Encryption is designed to retain supported query functionality over encrypted fields, while CSFLE provides deterministic or randomized encryption with different query and confidentiality trade-offs. :contentReference[oaicite:20]{index=20}

### Why can deterministic encryption leak information?

Because identical plaintext values can produce identical ciphertext values, which can expose frequency patterns, particularly for low-cardinality fields. :contentReference[oaicite:21]{index=21}

### Does field encryption replace TLS?

No. TLS protects network transport, while field encryption protects selected data fields. They address different threat models and should normally be used together where required.

### What happens if encryption keys are lost?

Encrypted data may become inaccessible. Key backup, recovery, rotation, and access-control procedures are therefore part of the database disaster-recovery design.

## Key Takeaways

- **TLS protects MongoDB traffic in transit, while encryption at rest protects persisted data; neither replaces authentication, authorization, or secure key management.**
- **Production TLS requires certificate validation, controlled trust stores, certificate lifecycle management, and monitoring; disabling certificate validation is not an acceptable production workaround.**
- **Queryable Encryption and CSFLE provide client-side field encryption for sensitive data, but encryption changes query capabilities, storage, performance, and schema design.**
- **Encryption keys are security-critical infrastructure: protect them independently, control access through a dedicated key-management system, and include them in backup and disaster-recovery planning.**
- **Design encryption from the data and query requirements backward: identify sensitive fields, determine required operations, select the appropriate encryption mechanism, and benchmark the resulting workload before production rollout.**