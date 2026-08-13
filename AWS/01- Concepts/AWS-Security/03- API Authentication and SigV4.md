# API Authentication and Signature Version 4 (SigV4)

Every API request to AWS must be authenticated and authorized. AWS uses a signing process called **Signature Version 4 (SigV4)** to verify the identity of the requester, ensure the integrity of the request, and protect against replay attacks.

SigV4 is the current standard for signing AWS API requests and is used by the AWS CLI, SDKs, and direct HTTP API calls. Understanding SigV4 is critical for debugging API issues, building custom integrations, and securing API access.

---

# How AWS Authenticates API Requests

When you make a request to an AWS service, the service must determine:

1. **Who are you?** — Authentication (via access key + signature)
2. **Are you allowed?** — Authorization (via IAM policies)
3. **Is this request valid?** — Integrity (via HMAC-SHA256 signature)
4. **Is this request current?** — Replay protection (via timestamp)

```text
Client Request
      │
      ▼
┌──────────────────┐
│ Signature        │
│ Verification     │
│                  │
│ 1. Reconstruct   │
│    canonical     │
│    request       │
│ 2. Recompute     │
│    signature     │
│ 3. Compare       │
│    signatures    │
└────────┬─────────┘
         │
    Match?
    │         │
   YES        NO
    │         │
    ▼         ▼
  Allow    AccessDenied
```

---

# Signature Version 2 vs Version 4

## SigV2 (Deprecated)

- Older signing mechanism
- Used only HMAC-SHA1 or HMAC-SHA256
- Less secure
- Limited to specific services (some S3 endpoints)
- **Deprecated** — do not use for new implementations

## SigV4 (Current Standard)

- Current AWS standard since 2014
- Uses HMAC-SHA256
- Supported by all AWS services
- Includes region and service scoping
- Supports temporary credentials (STS)
- Required for all new AWS services

| Feature | SigV2 | SigV4 |
|---------|-------|-------|
| Algorithm | HMAC-SHA1/SHA256 | HMAC-SHA256 |
| Region scoping | No | Yes |
| Service scoping | No | Yes |
| Replay protection | Basic | Timestamp-based (5 min window) |
| Temporary credentials | Limited | Full STS support |
| Status | Deprecated | Active standard |

---

# SigV4 Signing Process

The SigV4 signing process has four steps:

```text
Step 1: Create Canonical Request
              │
              ▼
Step 2: Create String to Sign
              │
              ▼
Step 3: Calculate Signing Key
              │
              ▼
Step 4: Calculate Signature
              │
              ▼
      Add to Authorization Header
```

---

## Step 1 — Create Canonical Request

A canonical request is a standardized representation of the HTTP request.

```text
CanonicalRequest =
  HTTPRequestMethod + '\n' +
  CanonicalURI + '\n' +
  CanonicalQueryString + '\n' +
  CanonicalHeaders + '\n' +
  SignedHeaders + '\n' +
  HexEncode(Hash(RequestPayload))
```

Example:

```text
GET
/
Action=ListUsers&Version=2010-05-08
content-type:application/x-www-form-urlencoded; charset=utf-8
host:iam.amazonaws.com
x-amz-date:20260707T150000Z

content-type;host;x-amz-date
e3b0c44298fc1c149afbf4c8996fb924...
```

---

## Step 2 — Create String to Sign

```text
StringToSign =
  Algorithm + '\n' +
  RequestDateTime + '\n' +
  CredentialScope + '\n' +
  HexEncode(Hash(CanonicalRequest))
```

The credential scope ties the signature to a specific date, region, and service:

```text
20260707/ap-south-1/s3/aws4_request
```

---

## Step 3 — Calculate Signing Key

The signing key is derived through a series of HMAC operations:

```text
DateKey       = HMAC-SHA256("AWS4" + SecretAccessKey, Date)
RegionKey     = HMAC-SHA256(DateKey, Region)
ServiceKey    = HMAC-SHA256(RegionKey, Service)
SigningKey    = HMAC-SHA256(ServiceKey, "aws4_request")
```

This produces a key that is scoped to a specific date, region, and service.

---

## Step 4 — Calculate Signature

```text
Signature = HexEncode(HMAC-SHA256(SigningKey, StringToSign))
```

---

## Authorization Header

The final signature is added to the HTTP Authorization header:

```text
Authorization: AWS4-HMAC-SHA256
  Credential=AKIAIOSFODNN7EXAMPLE/20260707/ap-south-1/s3/aws4_request,
  SignedHeaders=content-type;host;x-amz-date,
  Signature=fe5f80f77d5fa3beca038a248ff027d0445342fe2855ddc963176630326f1024
```

---

# Two Ways to Sign Requests

## 1. Authorization Header

The signature is included in the `Authorization` HTTP header. This is the most common method used by AWS SDKs and CLI.

## 2. Query String (Presigned URLs)

The signature is included as query string parameters. This is used for **presigned URLs** that grant temporary access.

```text
https://my-bucket.s3.amazonaws.com/my-object
  ?X-Amz-Algorithm=AWS4-HMAC-SHA256
  &X-Amz-Credential=AKIAIOSFODNN7EXAMPLE/20260707/us-east-1/s3/aws4_request
  &X-Amz-Date=20260707T150000Z
  &X-Amz-Expires=3600
  &X-Amz-Signature=fe5f80f77d5fa3beca038...
  &X-Amz-SignedHeaders=host
```

---

# SigV4 with Temporary Credentials (STS)

When using temporary credentials from AWS STS (AssumeRole, GetSessionToken), the signing process includes an additional `X-Amz-Security-Token` header containing the session token.

```text
IAM Role / Federation
        │
        ▼
  AWS STS (AssumeRole)
        │
        ▼
  Temporary Credentials
  ├── Access Key ID
  ├── Secret Access Key
  └── Session Token
        │
        ▼
  Sign Request with SigV4
  + X-Amz-Security-Token header
```

---

# Common SigV4 Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `SignatureDoesNotMatch` | Incorrect secret key or malformed canonical request | Verify credentials, check canonical request construction |
| `IncompleteSignature` | Missing required signing components | Ensure all required headers are signed |
| `InvalidSignatureException` | Clock skew or expired signature | Sync system clock (NTP), request within 5-minute window |
| `ExpiredToken` | STS temporary credentials expired | Refresh temporary credentials |
| `AccessDenied` | Valid signature but IAM policy denies the action | Check IAM policies and resource policies |
| `MissingAuthenticationToken` | No Authorization header or query string | Add SigV4 signature to the request |

---

# Debugging SigV4 Issues

## Check Clock Synchronization

AWS rejects requests where the timestamp differs from server time by more than 5 minutes.

```bash
# Sync system clock
sudo ntpdate pool.ntp.org
```

## Enable AWS CLI Debug Logging

```bash
aws s3 ls --debug 2>&1 | grep -i "canonical\|signature\|string"
```

## Verify Credential Scope

Ensure the region and service in the credential scope match the endpoint being called.

```text
# Correct for S3 in Mumbai
Credential=AKIA.../20260707/ap-south-1/s3/aws4_request

# Wrong region — will fail
Credential=AKIA.../20260707/us-east-1/s3/aws4_request
```

---

# Key Takeaways

- SigV4 is the current standard for authenticating AWS API requests.
- It uses HMAC-SHA256 and scopes signatures to a specific date, region, and service.
- The signing process has 4 steps: canonical request → string to sign → signing key → signature.
- Signatures can be delivered via Authorization header or query string (presigned URLs).
- Temporary credentials from STS require an additional session token header.
- Clock skew beyond 5 minutes will cause `InvalidSignatureException`.
- AWS SDKs and CLI handle SigV4 automatically — understanding it matters for debugging and custom integrations.

---

# Interview Questions

### Q: What is SigV4?

Signature Version 4 is AWS's current request signing protocol that uses HMAC-SHA256 to authenticate API requests, verify integrity, and prevent replay attacks.

### Q: Why does SigV4 include the region and service in the signing key?

To scope the signature so that a key derived for one service/region cannot be used to sign requests to a different service/region, limiting the blast radius of credential compromise.

### Q: What happens if the system clock is off by more than 5 minutes?

AWS will reject the request with `InvalidSignatureException` because the timestamp falls outside the acceptable window.

### Q: How are presigned URLs different from Authorization header signing?

Presigned URLs embed the signature in query string parameters instead of headers, allowing users without AWS credentials to access resources temporarily.

---
