# EC2 Instance Metadata Service (IMDS)

# What is Instance Metadata?

Instance metadata is information about a running EC2 instance that is available from within the instance itself. It is served at a special link-local address (`169.254.169.254`) and provides details like instance ID, public IP, IAM role credentials, network configuration, and User Data.

Any process running on the instance can access metadata — no authentication is required for IMDS v1.

---

# What Metadata Exposes

| Path | Returns | Example |
|------|---------|---------|
| `/meta-data/instance-id` | Instance ID | `i-0abcdef1234567890` |
| `/meta-data/instance-type` | Instance type | `m5.xlarge` |
| `/meta-data/ami-id` | AMI used to launch | `ami-0123456789abcdef0` |
| `/meta-data/local-ipv4` | Private IP address | `10.0.1.42` |
| `/meta-data/public-ipv4` | Public IP address | `54.123.45.67` |
| `/meta-data/placement/availability-zone` | AZ | `us-east-1a` |
| `/meta-data/security-groups` | SG names | `web-sg` |
| `/meta-data/iam/security-credentials/<role-name>` | **Temporary IAM credentials** | AccessKeyId, SecretAccessKey, Token |
| `/user-data` | User Data script contents | `#!/bin/bash ...` |

**Critical Security Implication**: The IAM credentials path returns live, temporary access keys for the instance's IAM role. Any process on the instance (including a compromised web application) can retrieve these credentials.

---

# IMDS v1 vs IMDS v2

## IMDS v1 (Legacy — Insecure)

Simple HTTP GET request. No authentication.

```text
curl http://169.254.169.254/latest/meta-data/instance-id
```

**Security Risk — SSRF Attacks:**

```text
Attacker's Browser
      │
      ▼
Web Application (vulnerable to Server-Side Request Forgery)
      │
      │  Attacker tricks the app into making a request to:
      │  http://169.254.169.254/latest/meta-data/iam/security-credentials/my-role
      │
      ▼
IMDS v1 returns IAM credentials to the app
      │
      ▼
Attacker extracts credentials → accesses AWS resources

This is exactly how the 2019 Capital One breach worked.
IMDS v1 has no way to distinguish between a legitimate request
from the OS and a forged request from a compromised application.
```

## IMDS v2 (Secure — Session-Oriented)

Requires a two-step process using a session token:

```text
Step 1: PUT request to get a session token (with TTL)
  TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

Step 2: GET request with token in header
  curl http://169.254.169.254/latest/meta-data/instance-id \
    -H "X-aws-ec2-metadata-token: $TOKEN"
```

**Why v2 Prevents SSRF:**
- The PUT method is required to obtain a token. Most SSRF vulnerabilities can only trigger GET requests.
- The token header (`X-aws-ec2-metadata-token`) must be present. Forged requests from web apps typically cannot set custom headers.
- Token has a configurable TTL (max 6 hours), limiting exposure window.

---

# IMDS v1 vs v2 Comparison

| Feature | IMDS v1 | IMDS v2 |
|---------|---------|---------|
| Request Method | Simple GET | PUT (token) then GET (with token) |
| Authentication | None | Session token required |
| SSRF Protection | None | Prevents most SSRF attacks |
| Header Required | No | Yes (`X-aws-ec2-metadata-token`) |
| AWS Recommendation | Disable | **Use exclusively** |

---

# Enforcing IMDS v2

To require IMDS v2 and disable v1 entirely, set `HttpTokens=required` in your launch template or on a running instance:

```text
aws ec2 modify-instance-metadata-options \
  --instance-id i-0abcdef1234567890 \
  --http-tokens required \
  --http-endpoint enabled

HttpTokens=required  → IMDS v2 only (v1 disabled)
HttpTokens=optional  → Both v1 and v2 work (default, insecure)
```

**Best Practice**: Set `HttpTokens=required` in your default launch template. Enforce this with an SCP or AWS Config rule to prevent anyone from launching instances with IMDS v1.

---

# Instance Identity Document

The Instance Identity Document is a JSON document signed by AWS that proves the identity of the instance. It can be used for third-party verification (e.g., registering with a configuration management server).

```text
curl http://169.254.169.254/latest/dynamic/instance-identity/document

Returns:
{
  "instanceId": "i-0abcdef1234567890",
  "accountId": "123456789012",
  "region": "us-east-1",
  "availabilityZone": "us-east-1a",
  "instanceType": "m5.xlarge",
  "imageId": "ami-0123456789abcdef0",
  "architecture": "x86_64"
}
```

A cryptographic signature is available at `/latest/dynamic/instance-identity/signature` to verify the document was not tampered with.

---

# Common Mistakes

- Leaving IMDS v1 enabled on production instances — this is a known attack vector for SSRF.
- Storing secrets in User Data instead of Secrets Manager — User Data is readable via IMDS.
- Not restricting metadata access using `iptables` rules for containerized workloads (containers on EC2 can access host IMDS).
- Assuming IMDS is only accessible to the OS — any process, container, or compromised application can reach 169.254.169.254.

---

# Key Takeaways

- IMDS provides instance metadata (including IAM credentials) at `169.254.169.254`.
- IMDS v1 is vulnerable to SSRF attacks. Always enforce IMDS v2 with `HttpTokens=required`.
- The IAM credentials endpoint is the highest-risk metadata path — it provides temporary AWS access keys.
- Use the Instance Identity Document for cryptographic proof of instance identity.
- Never put secrets in User Data — they are exposed through IMDS and the EC2 console.
- Enforce IMDS v2 organization-wide using SCPs or AWS Config rules.

---
