# Encryption at Rest and In Transit

Encryption is the process of converting data into an unreadable format that can only be decrypted by authorized parties. AWS provides encryption capabilities for virtually every service, covering both **data at rest** (stored data) and **data in transit** (data moving between systems).

Encryption is a fundamental security control and is required by most compliance frameworks (PCI DSS, HIPAA, SOC 2, GDPR). AWS makes it straightforward to encrypt everything — the challenge is understanding the options and making the right architectural decisions.

---

# Why Encrypt?

- **Compliance** — Regulatory frameworks mandate encryption
- **Data protection** — Prevents unauthorized access even if storage is compromised
- **Defense in depth** — Additional security layer beyond access controls
- **Breach mitigation** — Encrypted data is useless without the key

---

# Encryption at Rest

Encryption at rest protects stored data on disk, in databases, and in object storage.

```text
Application Data
       │
       ▼
┌──────────────┐
│  Encryption  │
│  Engine      │
│  (AES-256)   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Encrypted   │
│  Storage     │
│  (Disk/S3)   │
└──────────────┘
```

---

## Encryption at Rest by Service

| Service | Encryption Method | Default | Key Options |
|---------|------------------|---------|-------------|
| **S3** | SSE-S3, SSE-KMS, SSE-C | SSE-S3 (auto since Jan 2023) | S3-managed, KMS, customer-provided |
| **EBS** | AES-256 | Optional (can enforce) | AWS-managed KMS or customer CMK |
| **RDS** | AES-256 | Optional at creation | AWS-managed KMS or customer CMK |
| **DynamoDB** | AES-256 | Enabled (always on) | AWS-owned, AWS-managed, customer CMK |
| **EFS** | AES-256 | Optional at creation | KMS key |
| **Aurora** | AES-256 | Optional at creation | KMS key |
| **Redshift** | AES-256 | Optional | KMS or CloudHSM |
| **Lambda** | AES-256 | Environment variables encrypted | KMS key |

---

## Server-Side Encryption Types (S3 Example)

### SSE-S3 (S3-Managed Keys)

- AWS manages both the encryption key and the master key
- Uses AES-256
- No additional cost
- Default since January 2023
- No customer control over key rotation

### SSE-KMS (KMS-Managed Keys)

- Keys managed in AWS KMS
- Customer controls key policies and rotation
- Audit trail via CloudTrail
- Additional KMS API costs
- Subject to KMS request quotas

### SSE-C (Customer-Provided Keys)

- Customer provides the encryption key with every request
- AWS performs encryption/decryption but does not store the key
- Customer must manage key storage and rotation
- Must use HTTPS (TLS)

### Client-Side Encryption

- Customer encrypts data before sending to AWS
- AWS never sees the unencrypted data
- Customer manages encryption library, keys, and process
- Maximum control but maximum responsibility

```text
Encryption Control Spectrum:

Less Control ◄──────────────────────────► More Control
   SSE-S3       SSE-KMS       SSE-C      Client-Side
```

---

## Enforcing Encryption at Rest

### S3 — Bucket Policy

```json
{
  "Effect": "Deny",
  "Principal": "*",
  "Action": "s3:PutObject",
  "Resource": "arn:aws:s3:::my-bucket/*",
  "Condition": {
    "StringNotEquals": {
      "s3:x-amz-server-side-encryption": "aws:kms"
    }
  }
}
```

### EBS — AWS Config Rule or SCP

Enforce that all new EBS volumes must be encrypted.

### RDS — Encryption at creation time

RDS encryption must be enabled when the instance is created. It cannot be added later to an existing unencrypted instance.

---

# Encryption In Transit

Encryption in transit protects data as it moves between clients, services, and endpoints.

```text
Client                    AWS Service
  │                           │
  │    TLS 1.2 / TLS 1.3     │
  │◄─────────────────────────►│
  │    Encrypted Channel      │
  │                           │
```

---

## TLS/SSL

Transport Layer Security (TLS) encrypts data between the client and the server.

- AWS endpoints support TLS 1.2 and TLS 1.3
- TLS 1.0 and 1.1 are deprecated
- AWS recommends TLS 1.2 minimum

---

## Encryption In Transit by Service

| Service | In-Transit Encryption | Configuration |
|---------|----------------------|---------------|
| **S3** | HTTPS (TLS) | Enforce with bucket policy (`aws:SecureTransport`) |
| **RDS** | SSL/TLS | Enable with parameter groups, use SSL certificates |
| **DynamoDB** | HTTPS (always) | Always encrypted — no configuration needed |
| **ELB** | HTTPS listeners | Configure SSL/TLS certificates via ACM |
| **CloudFront** | HTTPS (viewer + origin) | Configure viewer protocol and origin protocol policies |
| **API Gateway** | HTTPS (always) | Always encrypted — custom domain requires ACM cert |
| **VPN** | IPsec | Site-to-Site VPN or Client VPN |
| **Direct Connect** | MACsec or VPN overlay | Enable MACsec for physical layer encryption |

---

## Enforcing HTTPS on S3

```json
{
  "Effect": "Deny",
  "Principal": "*",
  "Action": "s3:*",
  "Resource": "arn:aws:s3:::my-bucket/*",
  "Condition": {
    "Bool": {
      "aws:SecureTransport": "false"
    }
  }
}
```

---

## AWS Certificate Manager (ACM)

ACM provides free public SSL/TLS certificates for AWS services.

- Free for public certificates used with AWS services
- Automatic renewal
- Integrates with ALB, CloudFront, API Gateway
- Cannot be exported (for AWS services only)
- Private CA available for internal certificates

```text
ACM Certificate
      │
      ├──► ALB (HTTPS Listener)
      ├──► CloudFront Distribution
      └──► API Gateway Custom Domain
```

---

# End-to-End Encryption Architecture

```text
Client
  │
  │ HTTPS (TLS 1.2+)
  │
  ▼
CloudFront (SSL Termination)
  │
  │ HTTPS (Origin Protocol)
  │
  ▼
ALB (HTTPS Listener)
  │
  │ HTTPS or HTTP (to target)
  │
  ▼
EC2 / ECS / Lambda
  │
  │ TLS / SSL
  │
  ▼
RDS (SSL Connection)
  │
  Encrypted at Rest (AES-256 / KMS)
```

---

# Key Takeaways

- Encrypt data **at rest** and **in transit** — both are required for compliance.
- AWS provides multiple encryption options ranging from fully managed (SSE-S3) to customer-controlled (SSE-C, client-side).
- KMS provides centralized key management with audit trails via CloudTrail.
- TLS 1.2+ should be the minimum for all data in transit.
- ACM provides free SSL/TLS certificates for AWS services.
- Use bucket policies and SCPs to enforce encryption requirements.
- RDS encryption must be enabled at creation time — it cannot be added later.
- S3 default encryption (SSE-S3) is enabled automatically since January 2023.

---

# Interview Questions

### Q: What is the difference between encryption at rest and in transit?

At rest protects stored data (on disk, in S3, in databases). In transit protects data moving between systems (over the network via TLS).

### Q: What are the S3 encryption options?

SSE-S3 (AWS-managed keys), SSE-KMS (KMS-managed keys), SSE-C (customer-provided keys), and client-side encryption.

### Q: Can you encrypt an existing unencrypted RDS instance?

Not directly. You must create an encrypted snapshot, restore from it, and switch traffic to the new encrypted instance.

### Q: How do you enforce HTTPS on S3?

Use a bucket policy with a condition that denies requests where `aws:SecureTransport` is `false`.

---
