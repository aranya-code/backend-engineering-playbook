# AWS KMS Deep Dive

AWS Key Management Service (KMS) is a fully managed service that enables you to create, manage, and control cryptographic keys used to encrypt your data across AWS services and applications. KMS is the central encryption service in AWS — almost every AWS service that supports encryption at rest integrates with KMS.

Understanding KMS deeply is essential for security architecture, compliance, and is heavily tested in AWS certifications.

---

# Why KMS?

Without a centralized key management service:

- Keys are scattered across applications and services
- No audit trail for key usage
- Manual key rotation is error-prone
- Cross-service encryption is difficult to manage
- Compliance requirements are hard to meet

KMS solves all of these problems with a single, managed service.

---

# KMS Key Types

## AWS Owned Keys

- Created and managed entirely by AWS
- Used internally by AWS services
- Customer cannot view, use, or audit these keys
- No cost
- Example: DynamoDB default encryption

## AWS Managed Keys

- Created by AWS on behalf of the customer
- Visible in KMS console (prefixed with `aws/`)
- Automatic key rotation every year
- Customer cannot manage key policies
- Free (no monthly fee, but API calls may cost)
- Example: `aws/s3`, `aws/ebs`, `aws/rds`

## Customer Managed Keys (CMKs)

- Created and managed by the customer
- Full control over key policies, grants, and rotation
- Can be enabled/disabled/deleted
- $1/month per key + API usage costs
- Supports automatic rotation (every year) or manual rotation
- **Recommended for production workloads requiring compliance**

```text
Control Spectrum:

Least Control ◄──────────────────────────► Most Control
  AWS Owned       AWS Managed       Customer Managed
```

---

# Symmetric vs Asymmetric Keys

## Symmetric Keys (AES-256)

- Single key for both encryption and decryption
- Default KMS key type
- Key material never leaves KMS unencrypted
- Used by most AWS services
- Best for: server-side encryption, envelope encryption

## Asymmetric Keys (RSA, ECC)

- Public key + private key pair
- Public key can be downloaded
- Private key never leaves KMS
- Used for: digital signatures, encryption outside AWS
- Best for: client-side encryption, code signing, TLS offloading

| Feature | Symmetric | Asymmetric |
|---------|-----------|------------|
| Keys | 1 (shared) | 2 (public + private) |
| Use case | Server-side encryption | Signatures, external encryption |
| Key export | Never | Public key only |
| AWS service integration | All services | Limited |
| Performance | Faster | Slower |

---

# Key Policies

Every KMS key has a **key policy** — a resource-based policy that controls access to the key.

Unlike most AWS resources, KMS keys are **not accessible** unless the key policy explicitly grants access, even if the caller has IAM permissions.

```text
Access Decision:

IAM Policy ALLOWS
      +
Key Policy ALLOWS
      =
ACCESS GRANTED
```

Both must allow the action. If either denies or is silent, access is denied.

---

## Default Key Policy

The default key policy grants the AWS account root user full access to the key, which enables IAM policies to grant access to other users and roles.

```json
{
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::123456789012:root"
  },
  "Action": "kms:*",
  "Resource": "*"
}
```

---

# Key Rotation

## Automatic Rotation (Customer Managed Keys)

- Rotates key material every year (configurable: 90–2560 days)
- Old key material is retained for decryption
- Key ID and ARN do not change
- Transparent to applications
- Enabled per key

## Manual Rotation

- Create a new key
- Update applications to use the new key
- Keep old key for decrypting existing data
- Use aliases to simplify rotation

```text
Automatic Rotation:

Key-abc123
├── 2024 Key Material (retained for decrypt)
├── 2025 Key Material (retained for decrypt)
└── 2026 Key Material (current, used for encrypt)
```

---

# Envelope Encryption

Envelope encryption is the technique KMS uses to encrypt data larger than 4 KB. Instead of sending all data to KMS, you request a **data key**, use it locally to encrypt data, and store the encrypted data key alongside the encrypted data.

## Why Envelope Encryption?

- KMS can only encrypt up to 4 KB directly
- Sending large data to KMS over the network is impractical
- Data keys provide better performance (local encryption)
- Reduces KMS API calls and costs

## How Envelope Encryption Works

```text
Step 1: GenerateDataKey API
┌────────────┐         ┌───────────┐
│ Application│────────►│   KMS     │
│            │         │           │
│            │◄────────│  Returns: │
│            │         │  • Plaintext Data Key  │
│            │         │  • Encrypted Data Key  │
└────────────┘         └───────────┘

Step 2: Encrypt Data Locally
┌────────────┐
│ Application│
│            │
│ Data + Plaintext Data Key
│         │
│    AES-256 Encryption
│         │
│    ▼
│ Encrypted Data
│ + Encrypted Data Key
│   (stored together)
│
│ Plaintext Data Key
│   (discarded from memory)
└────────────┘

Step 3: Decrypt (later)
┌────────────┐         ┌───────────┐
│ Application│────────►│   KMS     │
│            │ Send    │           │
│            │ Encrypted│ Decrypt  │
│            │ Data Key │ API      │
│            │◄────────│           │
│            │ Plaintext│          │
│            │ Data Key │          │
└────────────┘         └───────────┘
      │
 Decrypt data locally
 with Plaintext Data Key
```

---

# KMS Request Quotas

KMS has API request quotas that vary by region:

| Operation | Default Quota (per account per region) |
|-----------|---------------------------------------|
| Cryptographic operations | 5,500 – 30,000 requests/second |
| GenerateDataKey | Included in crypto operations |
| Describe/List operations | 5 – 30 requests/second |

Exceeding quotas results in `ThrottlingException`. Solutions:

- Use envelope encryption to reduce API calls
- Cache data keys (with security considerations)
- Request quota increases
- Use KMS key grants for temporary access

---

# KMS with AWS Services

| Service | KMS Integration | Key Types Supported |
|---------|----------------|-------------------|
| S3 | SSE-KMS | AWS managed, Customer managed |
| EBS | Volume encryption | AWS managed, Customer managed |
| RDS | Storage encryption | AWS managed, Customer managed |
| DynamoDB | Table encryption | AWS owned, AWS managed, Customer managed |
| Lambda | Environment variable encryption | AWS managed, Customer managed |
| Secrets Manager | Secret encryption | AWS managed, Customer managed |
| SQS | Message encryption | AWS managed, Customer managed |
| CloudTrail | Log file encryption | Customer managed |

---

# Cross-Account Key Sharing

KMS keys can be shared across AWS accounts using key policies and grants.

```text
Account A (Key Owner)
├── KMS Key with key policy
│   granting Account B access
│
Account B (Key User)
├── IAM role with kms:Decrypt permission
└── Uses key ARN from Account A
```

---

# KMS vs CloudHSM

| Feature | KMS | CloudHSM |
|---------|-----|----------|
| Management | Fully managed | Customer managed cluster |
| Key storage | Multi-tenant HSM | Single-tenant HSM |
| FIPS 140-2 | Level 2 | Level 3 |
| Key types | Symmetric, Asymmetric | Symmetric, Asymmetric |
| Custom key store | Supported | Required |
| Cost | Per key + API calls | Per HSM hour (~$1.50/hr) |
| Use case | Most workloads | Regulatory requirements, custom crypto |

---

# Key Takeaways

- KMS is the central encryption service in AWS.
- Three key types: AWS owned (no control), AWS managed (limited control), Customer managed (full control).
- Key policies + IAM policies together determine access — both must allow.
- Automatic key rotation is available for customer managed keys.
- Envelope encryption is used for data larger than 4 KB — use `GenerateDataKey`.
- KMS has request quotas; use envelope encryption to minimize API calls.
- CloudHSM provides FIPS 140-2 Level 3 compliance for strict regulatory requirements.

---

# Interview Questions

### Q: What is envelope encryption and why is it needed?

Envelope encryption uses a data key to encrypt data locally and then encrypts the data key with a KMS key. It's needed because KMS can only directly encrypt data up to 4 KB.

### Q: What is the difference between AWS managed and customer managed keys?

AWS managed keys are created automatically by AWS services, have automatic rotation, and limited policy control. Customer managed keys provide full control over policies, rotation, and lifecycle.

### Q: Can a KMS key be shared across accounts?

Yes, by adding cross-account permissions in the key policy and granting the other account's IAM roles appropriate KMS permissions.

### Q: What happens when you delete a KMS key?

KMS enforces a waiting period (7–30 days) before deletion. During this period, the key is disabled. After deletion, all data encrypted with the key becomes permanently undecryptable.

---
