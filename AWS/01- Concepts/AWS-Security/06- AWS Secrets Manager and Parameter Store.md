# AWS Secrets Manager and Parameter Store

Managing secrets — database credentials, API keys, tokens, certificates — is one of the most critical security challenges in cloud applications. AWS provides two services for this: **AWS Secrets Manager** and **AWS Systems Manager Parameter Store**. Both store sensitive configuration data, but they serve different purposes, have different feature sets, and different pricing models.

Choosing the right service depends on your requirements for automatic rotation, cross-account access, cost, and integration complexity.

---

# Why Secret Management Matters

Hardcoding secrets in application code or configuration files creates severe security risks:

- Secrets exposed in version control (Git leaks)
- No audit trail for secret access
- No automatic rotation
- Secrets scattered across services
- Credential reuse across environments

```text
Anti-Pattern:                   Best Practice:

Application Code               Application Code
├── DB_PASSWORD="abc123"        ├── secret_arn = "arn:aws:..."
├── API_KEY="xyz789"            │
└── Committed to Git ✗          ▼
                                Secrets Manager / Parameter Store
                                ├── Encrypted with KMS
                                ├── Audit trail via CloudTrail
                                └── Automatic rotation
```

---

# AWS Secrets Manager

## Overview

AWS Secrets Manager is purpose-built for storing, rotating, and managing secrets with built-in integrations for RDS, Redshift, and DocumentDB.

## Key Features

- **Automatic rotation** with Lambda functions
- **Built-in RDS/Aurora/Redshift rotation** (native support)
- **Cross-account access** via resource policies
- **Versioning** (AWSCURRENT, AWSPREVIOUS, AWSPENDING)
- **Encrypted with KMS** (AWS managed or customer managed key)
- **CloudTrail auditing** for every access
- **Replication** to other regions

## How Secrets Manager Works

```text
Application
     │
     │ GetSecretValue API
     ▼
┌──────────────────┐
│ Secrets Manager  │
│                  │
│ Secret Value     │
│ (Encrypted with  │
│  KMS Key)        │
│                  │
│ Rotation Lambda  │──► RDS/Aurora
│ (Automatic)      │    (Update Password)
└──────────────────┘
```

## Automatic Rotation

Secrets Manager can automatically rotate secrets on a schedule (e.g., every 30 days).

For supported databases (RDS, Aurora, Redshift, DocumentDB):

```text
Rotation Flow:

1. Secrets Manager invokes rotation Lambda
2. Lambda creates new credentials in the database
3. Lambda stores new credentials in Secrets Manager (AWSPENDING)
4. Lambda tests the new credentials
5. Lambda marks new credentials as AWSCURRENT
6. Previous credentials become AWSPREVIOUS
```

## Pricing

- **$0.40 per secret per month**
- **$0.05 per 10,000 API calls**
- Rotation Lambda invocations billed separately

---

# AWS Systems Manager Parameter Store

## Overview

SSM Parameter Store is a general-purpose configuration and secret store that supports hierarchical organization, versioning, and KMS encryption.

## Key Features

- **Hierarchical storage** with paths (`/prod/db/password`)
- **Two tiers**: Standard (free) and Advanced (paid)
- **Three parameter types**: String, StringList, SecureString
- **KMS encryption** for SecureString parameters
- **Version history** (up to 100 versions)
- **CloudTrail auditing**
- **IAM-based access control**
- **Notifications** via EventBridge on parameter changes

## Parameter Types

| Type | Description | Encryption |
|------|------------|------------|
| **String** | Plain text value | No |
| **StringList** | Comma-separated values | No |
| **SecureString** | Encrypted value | KMS |

## Parameter Hierarchy

```text
/myapp/
├── /prod/
│   ├── db/
│   │   ├── host     = "prod-db.example.com"
│   │   ├── port     = "5432"
│   │   └── password = "encrypted" (SecureString)
│   └── api/
│       └── key      = "encrypted" (SecureString)
├── /staging/
│   ├── db/
│   │   ├── host     = "staging-db.example.com"
│   │   └── password = "encrypted"
│   └── api/
│       └── key      = "encrypted"
```

Access by path:

```bash
# Get all parameters for production database
aws ssm get-parameters-by-path \
  --path "/myapp/prod/db" \
  --with-decryption
```

## Standard vs Advanced Tier

| Feature | Standard | Advanced |
|---------|----------|---------|
| Max parameters | 10,000 | 100,000 |
| Max value size | 4 KB | 8 KB |
| Parameter policies | No | Yes (expiration, notification) |
| Cost | **Free** | $0.05 per advanced parameter per month |
| Throughput | 40 TPS (default) | 1,000 TPS (higher throughput) |

---

# Secrets Manager vs Parameter Store

| Feature | Secrets Manager | Parameter Store (SecureString) |
|---------|----------------|-------------------------------|
| **Primary purpose** | Secret management | Configuration + secrets |
| **Automatic rotation** | ✅ Built-in | ❌ Manual (build your own) |
| **RDS integration** | ✅ Native rotation | ❌ No |
| **Cross-account access** | ✅ Resource policies | ❌ Must use IAM roles |
| **Hierarchy** | ❌ Flat | ✅ Path-based hierarchy |
| **Versioning** | ✅ (CURRENT/PREVIOUS/PENDING) | ✅ (up to 100 versions) |
| **KMS encryption** | ✅ Always encrypted | ✅ SecureString only |
| **Max size** | 64 KB | 4 KB (Standard) / 8 KB (Advanced) |
| **CloudFormation** | ✅ Dynamic reference | ✅ Dynamic reference |
| **Cost** | $0.40/secret/month + API | Free (Standard) |
| **Replication** | ✅ Cross-region | ❌ No |

---

# When to Use Which

## Use Secrets Manager When:

- You need **automatic secret rotation**
- You manage **RDS/Aurora/Redshift credentials**
- You need **cross-account secret sharing**
- You need **cross-region replication**
- Compliance requires automatic credential rotation

## Use Parameter Store When:

- You need **hierarchical configuration management**
- You want **free** secret storage (Standard tier)
- You have **simple secrets** that don't need rotation
- You need **environment-specific configurations** (dev/staging/prod)
- You have a mix of **secrets and non-secret configuration**

## Use Both Together

A common production pattern:

```text
Parameter Store                Secrets Manager
├── /app/prod/                 ├── prod/db/master-password
│   ├── log-level = "INFO"     ├── prod/api/third-party-key
│   ├── feature-flags = "..."  └── prod/cache/auth-token
│   ├── endpoint = "..."           (Auto-rotated)
│   └── timeout = "30"
│   (Configuration)            (Rotated Secrets)
```

---

# Key Takeaways

- Never hardcode secrets in application code or configuration files.
- **Secrets Manager** is best for secrets requiring automatic rotation (especially database credentials).
- **Parameter Store** is best for hierarchical configuration and simple secrets (free tier available).
- Both services encrypt data with KMS and provide CloudTrail audit trails.
- Use Parameter Store for configuration + Secrets Manager for rotated secrets in production.
- Secrets Manager costs $0.40/secret/month; Parameter Store Standard tier is free.

---

# Interview Questions

### Q: When would you choose Secrets Manager over Parameter Store?

When you need automatic rotation of database credentials (RDS, Aurora), cross-account sharing, or cross-region replication.

### Q: Can Parameter Store rotate secrets automatically?

No. Parameter Store does not have built-in rotation. You must implement your own rotation logic using Lambda and EventBridge.

### Q: What is the cost difference?

Secrets Manager charges $0.40 per secret per month. Parameter Store Standard tier is free for up to 10,000 parameters.

### Q: How do you organize parameters in Parameter Store?

Using hierarchical paths like `/app/environment/service/parameter` and accessing them with `GetParametersByPath`.

---
