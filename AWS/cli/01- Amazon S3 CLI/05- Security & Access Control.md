# S3 Security & Access Control

Amazon S3 is one of the most widely used storage services in AWS, making it a frequent target for security misconfigurations.

Many well-known cloud security incidents have occurred because S3 buckets were accidentally exposed to the public.

Understanding S3 security is essential for every Backend Engineer, DevOps Engineer, and Cloud Engineer.

This chapter covers:

- Block Public Access
- IAM Policies
- Bucket Policies
- Object Ownership
- Access Control Lists (ACLs)
- Encryption
- Cross-Account Access
- Security Best Practices

---

# S3 Security Layers

Amazon S3 uses multiple layers of security.

```text
                AWS Account
                     │
                     ▼
          IAM User / IAM Role
                     │
                     ▼
              IAM Policies
                     │
                     ▼
             Bucket Policies
                     │
                     ▼
        Block Public Access
                     │
                     ▼
          Object Ownership
                     │
                     ▼
          Object Encryption
                     │
                     ▼
               S3 Objects
```

Each layer provides additional protection.

---

# Block Public Access

Block Public Access is the first line of defense for S3.

AWS strongly recommends enabling it for almost every bucket.

It prevents accidental public exposure even if:

- Bucket Policies allow public access
- ACLs allow public access

---

## Check Block Public Access

```bash
aws s3api get-public-access-block \
--bucket company-backups
```

Example output:

```json
{
    "PublicAccessBlockConfiguration": {
        "BlockPublicAcls": true,
        "IgnorePublicAcls": true,
        "BlockPublicPolicy": true,
        "RestrictPublicBuckets": true
    }
}
```

---

## Enable Block Public Access

```bash
aws s3api put-public-access-block \
--bucket company-backups \
--public-access-block-configuration \
BlockPublicAcls=true,\
IgnorePublicAcls=true,\
BlockPublicPolicy=true,\
RestrictPublicBuckets=true
```

This configuration is recommended for almost every production bucket.

---

# IAM Policies

IAM Policies determine **who** can perform actions on S3 resources.

Example:

```json
{
    "Version":"2012-10-17",
    "Statement":[
        {
            "Effect":"Allow",
            "Action":[
                "s3:GetObject"
            ],
            "Resource":"arn:aws:s3:::company-backups/*"
        }
    ]
}
```

This policy allows downloading objects but not uploading or deleting them.

---

# Bucket Policies

Bucket Policies are attached directly to an S3 bucket.

Unlike IAM Policies, they control access to that specific bucket.

Retrieve a bucket policy:

```bash
aws s3api get-bucket-policy \
--bucket company-backups
```

Apply a bucket policy:

```bash
aws s3api put-bucket-policy \
--bucket company-backups \
--policy file://policy.json
```

---

# IAM Policy vs Bucket Policy

| IAM Policy | Bucket Policy |
|------------|---------------|
| Attached to Users, Groups, or Roles | Attached to Buckets |
| Controls identity permissions | Controls bucket access |
| Applies across AWS | Applies only to one bucket |

In production, both are often used together.

---

# Object Ownership

Historically, uploaded objects could be owned by different AWS accounts.

Modern S3 introduces **Bucket Owner Enforced** ownership.

Benefits:

- Simplifies permissions
- Eliminates ACL management
- Bucket owner owns every uploaded object

AWS recommends enabling this setting.

---

## Check Object Ownership

```bash
aws s3api get-bucket-ownership-controls \
--bucket company-backups
```

---

## Configure Bucket Owner Enforced

```bash
aws s3api put-bucket-ownership-controls \
--bucket company-backups \
--ownership-controls \
Rules=[{ObjectOwnership=BucketOwnerEnforced}]
```

---

# Access Control Lists (ACLs)

ACLs are the original S3 permission model.

Examples:

- private
- public-read
- public-read-write

Modern AWS environments rarely rely on ACLs.

AWS recommends:

- Bucket Owner Enforced
- Bucket Policies
- IAM Policies

instead of ACLs.

---

## View Bucket ACL

```bash
aws s3api get-bucket-acl \
--bucket company-backups
```

---

## View Object ACL

```bash
aws s3api get-object-acl \
--bucket company-backups \
--key report.pdf
```

---

# Public vs Private Buckets

Private Bucket

✔ Recommended

- Internal applications
- Backups
- Databases
- Logs

Public Bucket

Suitable for:

- Static websites
- Public downloads
- Documentation
- Public datasets

Never make a bucket public unless it is required.

---

# Server-Side Encryption

Encrypt objects automatically during upload.

---

## SSE-S3

```bash
aws s3 cp report.pdf \
s3://company-backups \
--sse AES256
```

AWS manages encryption keys.

---

## SSE-KMS

```bash
aws s3 cp report.pdf \
s3://company-backups \
--sse aws:kms
```

Specify a customer-managed key:

```bash
aws s3 cp report.pdf \
s3://company-backups \
--sse aws:kms \
--sse-kms-key-id alias/company-key
```

SSE-KMS provides:

- Key rotation
- Audit logging
- Fine-grained access control

---

# Cross-Account Access

A bucket can grant access to another AWS account.

Typical approaches:

- Bucket Policy
- IAM Role
- AWS Organizations
- Cross-account AssumeRole

Avoid sharing Access Keys between accounts.

---

# Verify Bucket Encryption

```bash
aws s3api get-bucket-encryption \
--bucket company-backups
```

Example output:

```json
{
    "ServerSideEncryptionConfiguration": {
        ...
    }
}
```

---

# Security Troubleshooting

## AccessDenied

Possible causes:

- Missing IAM permission
- Bucket Policy denial
- KMS permission
- Object Ownership
- SCP restriction

Always verify:

```bash
aws sts get-caller-identity
```

before changing policies.

---

## All Public Access Blocked

Error:

```text
AccessDenied
```

Check:

```bash
aws s3api get-public-access-block \
--bucket company-backups
```

The Block Public Access configuration may be preventing a policy change.

---

## KMS Permission Denied

Uploading succeeds?

Downloading fails?

Check:

- IAM permissions
- KMS Key Policy
- Key grants

---

# Security Checklist

Before using an S3 bucket in production:

- □ Block Public Access enabled
- □ Bucket encrypted
- □ Bucket Owner Enforced enabled
- □ Least Privilege IAM Policies
- □ No unnecessary ACLs
- □ Bucket Policy reviewed
- □ MFA enabled for administrators
- □ Logging enabled
- □ Versioning configured if required

---

# Production Workflow

Deploying sensitive application data.

```text
Create Bucket
      │
      ▼
Enable Block Public Access
      │
      ▼
Enable Encryption
      │
      ▼
Configure IAM Policy
      │
      ▼
Configure Bucket Policy
      │
      ▼
Verify Ownership
      │
      ▼
Upload Objects
```

Security should be configured before storing production data.

---

# Architecture Note

S3 authorization evaluates multiple policy layers.

```text
Request
      │
      ▼
IAM Authentication
      │
      ▼
IAM Policy
      │
      ▼
Bucket Policy
      │
      ▼
Block Public Access
      │
      ▼
Object Ownership
      │
      ▼
Encryption
      │
      ▼
Access Granted / Denied
```

Understanding this evaluation order simplifies troubleshooting.

---

# Interview Note

### Question

**What is the difference between an IAM Policy and a Bucket Policy?**

### Answer

An IAM Policy is attached to an IAM User, Group, or Role and defines what actions that identity can perform. A Bucket Policy is attached directly to an S3 bucket and defines which principals can access that specific bucket and under what conditions. AWS evaluates both policies together when authorizing requests.

---

# Key Takeaways

- Enable Block Public Access for production buckets.
- Prefer IAM Policies and Bucket Policies over ACLs.
- Use Bucket Owner Enforced whenever possible.
- Encrypt objects using SSE-S3 or SSE-KMS.
- Apply the Principle of Least Privilege.
- Verify security settings before uploading sensitive data.
- Understand how IAM Policies, Bucket Policies, and Block Public Access work together.

---
