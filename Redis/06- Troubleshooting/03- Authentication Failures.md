# Authentication Failures

## Overview

Authentication failures are among the most common Redis production issues after connectivity problems. Unlike a **Connection Refused** error, authentication failures occur **after a successful TCP connection has already been established**.

Typical errors include:

```text
NOAUTH Authentication required.
```

```text
WRONGPASS invalid username-password pair
```

```text
AuthenticationError
```

```text
ERR AUTH <password> called without any password configured
```

Authentication issues are usually caused by:

- Incorrect password
- Incorrect username (ACL)
- Missing AUTH command
- Wrong Redis URL
- Environment variable mistakes
- Kubernetes Secret issues
- Docker environment configuration
- AWS ElastiCache authentication configuration

This chapter explains how to diagnose and resolve Redis authentication problems in production.

---

# Authentication Workflow

```
Application

↓

TCP Connection Established

↓

AUTH Command

↓

Authentication Successful?

│

├── Yes

│

▼

Execute Commands

│

└── No

↓

Authentication Error
```

Authentication happens **after** the network connection is established.

---

# Redis Security Evolution

Older Redis versions

```
Password Only
```

Modern Redis

```
ACL

↓

Username

+

Password

↓

Permissions
```

Redis 6 introduced Access Control Lists (ACLs).

---

# Common Authentication Errors

| Error | Meaning |
|--------|---------|
| NOAUTH Authentication required | Client never authenticated |
| WRONGPASS | Password or username incorrect |
| NOPERM | Authenticated but lacks permissions |
| ERR AUTH called without password configured | AUTH used when authentication is disabled |
| AuthenticationError | Client library authentication failure |

---

# Authentication Flow

```
Client

↓

Connect

↓

AUTH

↓

Redis

↓

Access Granted
```

Without AUTH

```
Client

↓

GET user:1

↓

NOAUTH
```

---

# Step 1 — Verify Redis Requires Authentication

Run

```bash
redis-cli
```

Try

```bash
PING
```

Possible response

```text
NOAUTH Authentication required.
```

Redis expects authentication.

---

# Step 2 — Authenticate Manually

Example

```bash
redis-cli -a StrongPassword
```

Expected

```text
PONG
```

If authentication fails

```
WRONGPASS
```

Verify the configured password.

---

# Step 3 — Check redis.conf

Example

```conf
requirepass StrongPassword
```

If

```
requirepass
```

is configured,

clients must authenticate.

---

# ACL Authentication

Example

```text
Username

↓

backend

↓

Password

↓

Secret123
```

Client

```bash
AUTH backend Secret123
```

---

# Default User

Redis creates

```
default
```

automatically.

Example

```text
AUTH default StrongPassword
```

---

# View ACL Users

Command

```bash
ACL LIST
```

Example

```text
user default on >password ~* +@all
```

Useful for verifying users and permissions.

---

# Verify Permissions

Example

```bash
ACL GETUSER backend
```

Shows

- Passwords
- Commands
- Key patterns
- Enabled status

---

# Missing AUTH

Incorrect

```python
client = redis.Redis(
    host="redis"
)
```

Correct

```python
client = redis.Redis(
    host="redis",
    password="StrongPassword"
)
```

---

# Python Example (ACL)

```python
client = redis.Redis(
    host="redis",
    username="backend",
    password="StrongPassword"
)
```

---

# Redis URL

Incorrect

```text
redis://localhost:6379
```

Correct

```text
redis://:StrongPassword@localhost:6379
```

ACL

```text
redis://backend:StrongPassword@localhost:6379
```

---

# Environment Variables

Recommended

```bash
REDIS_HOST=redis

REDIS_PORT=6379

REDIS_USERNAME=backend

REDIS_PASSWORD=StrongPassword
```

Avoid hardcoding credentials.

---

# Docker Authentication

Docker Compose

```yaml
services:

  redis:
    image: redis:7
    command:
      - redis-server
      - --requirepass
      - StrongPassword
```

Application

```
Reads

↓

Environment Variables

↓

Connects
```

---

# Kubernetes Secrets

Architecture

```
Secret

↓

Application

↓

Redis Password
```

Never store passwords inside ConfigMaps.

---

# Kubernetes Verification

Check

```bash
kubectl describe secret redis-secret
```

Verify

- Secret exists
- Mounted correctly
- Environment variables populated

---

# AWS ElastiCache

Modern ElastiCache supports

- AUTH
- ACLs

Verify

- User Group
- Authentication Token
- Parameter Group

---

# Password Rotation

Production systems periodically rotate credentials.

Workflow

```
Generate Password

↓

Update Redis

↓

Update Applications

↓

Restart Services

↓

Verify
```

Avoid changing passwords manually without coordination.

---

# Authentication Retry

Poor

```
Wrong Password

↓

Infinite Retry
```

Better

```
Authentication Failure

↓

Log

↓

Alert

↓

Stop
```

Authentication errors should not trigger unlimited retries.

---

# Secret Synchronization

Problem

```
Application

↓

Old Password
```

```
Redis

↓

New Password
```

↓

Authentication Failure

Synchronize deployments carefully.

---

# Connection Pool

Incorrect credentials remain in pooled connections.

Workflow

```
Password Changed

↓

Destroy Pool

↓

Reconnect

↓

Authenticate
```

---

# Verify Application Configuration

Print configuration (excluding passwords)

Example

```
Host

Port

Username
```

Confirm the application is using the expected configuration.

---

# Logging

Typical application log

```text
AuthenticationError

WRONGPASS invalid username-password pair
```

Redis log

```text
Client closed connection
```

Correlate application and Redis logs.

---

# Diagnostic Flow

```
Authentication Failed

        │

        ▼

Connection Established?

        │

 ┌──────┴──────┐

 │             │

No            Yes

 │             │

Network     Verify Password

                │

                ▼

         Verify Username

                │

                ▼

         Verify ACL Rules

                │

                ▼

     Verify Environment Variables

                │

                ▼

          Authentication Success
```

---

# Security Best Practices

Never

```python
password = "admin123"
```

Use

- Environment variables
- Kubernetes Secrets
- AWS Secrets Manager
- HashiCorp Vault

---

# Credential Storage

Preferred architecture

```
Secrets Manager

↓

Application

↓

Redis
```

Applications should retrieve credentials securely at startup.

---

# Common Authentication Mistakes

## Hardcoded Passwords

Credentials inside source code create security risks.

---

## Wrong Username

ACL authentication requires both

- Username
- Password

---

## Old Password in Environment

Applications continue using outdated credentials.

Restart applications after updates.

---

## Missing AUTH

Connecting without authentication results in

```
NOAUTH
```

---

## Disabling Authentication

Never disable authentication in production simply to resolve connection issues.

Investigate the root cause instead.

---

# Production Checklist

```
✓ Password Configured

✓ Username Verified

✓ ACL Rules Correct

✓ Environment Variables Updated

✓ Secrets Synchronized

✓ Connection Pool Restarted

✓ Authentication Tested

✓ Logs Reviewed
```

---

# Best Practices

- Enable authentication for every production Redis deployment.
- Prefer ACLs over password-only authentication.
- Store credentials in secure secret management systems.
- Rotate passwords regularly using controlled deployment procedures.
- Never log passwords or expose credentials in application output.
- Restart connection pools after credential changes.
- Monitor authentication failures and investigate repeated attempts.
- Apply the principle of least privilege when defining ACL permissions.

---

# Performance Considerations

| Area | Recommendation |
|------|----------------|
| ACLs | Use least-privilege permissions |
| Connection Pool | Recreate after password changes |
| Secret Storage | Use dedicated secret managers |
| Logging | Log failures, never credentials |
| Password Rotation | Automate safely |
| Monitoring | Alert on repeated authentication failures |

---

# Production Considerations

For production environments:

- Integrate Redis credentials with centralized secret management platforms.
- Rotate passwords and ACL credentials on a scheduled basis.
- Audit Redis ACLs regularly to remove unnecessary permissions.
- Monitor authentication failures for potential security incidents.
- Validate authentication during deployment pipelines before releasing applications.
- Document credential rotation and emergency recovery procedures.

---

# Summary

Redis authentication failures occur after a successful network connection but before commands are executed. Most issues stem from incorrect passwords, ACL configuration, outdated secrets, or application misconfiguration. A systematic approach—verifying authentication requirements, validating credentials, checking ACLs, and confirming secret synchronization—allows engineers to resolve authentication problems quickly while maintaining strong security practices.

---

# Key Takeaways

- Authentication failures are different from connection failures.
- Use `AUTH` or ACL credentials before executing Redis commands.
- Verify passwords, usernames, and ACL permissions systematically.
- Store credentials securely using secret management solutions.
- Rotate passwords carefully and restart connection pools afterward.
- Monitor authentication failures for operational and security insights.
- Never disable authentication in production as a workaround.
- Follow least-privilege principles when configuring Redis ACLs.