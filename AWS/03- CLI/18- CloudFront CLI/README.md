# README.md

## Overview

This section contains production-oriented AWS CLI workflows for managing, inspecting, troubleshooting, and operating Amazon CloudFront distributions.

The commands are organized around practical operational tasks rather than individual AWS API operations. The goal is to make CloudFront administration reproducible through the CLI and suitable for local development, incident response, CI/CD pipelines, and production operations.

## Quick Navigation

| # | Topic | Coverage |
|---|---|---|
| 01 | [CloudFront CLI Commands](01-%20CloudFront%20CLI%20Commands.md) | Core CloudFront CLI commands, distribution inspection, origins, behaviors, policies, and common operations. |
| 02 | [Distribution Management](02-%20Distribution%20Management.md) | Distribution creation, inspection, configuration updates, deployment status, and lifecycle management. |
| 03 | [Cache Invalidation Commands](03-%20Cache%20Invalidation%20Commands.md) | Creating, inspecting, waiting for, and operationally managing CloudFront cache invalidations. |
| 04 | [Monitoring and Inspection Commands](04-%20Monitoring%20and%20Inspection%20Commands.md) | Distribution health, CloudWatch metrics, cache behavior, origins, WAF, TLS, and troubleshooting commands. |
| 05 | [Operational CLI Workflows](05-%20Operational%20CLI%20Workflows.md) | End-to-end production workflows for deployment, validation, incident response, rollback, and operational automation. |

## Command Coverage

The CLI material covers the main operational layers of CloudFront:

```text
CloudFront CLI
│
├── Distribution Management
│   ├── Inspect distributions
│   ├── Retrieve configuration
│   ├── Update configuration
│   └── Monitor deployment state
│
├── Cache Operations
│   ├── Create invalidations
│   ├── Inspect invalidations
│   └── Wait for invalidation completion
│
├── Inspection & Monitoring
│   ├── Distribution status
│   ├── Origins
│   ├── Cache behaviors
│   ├── Cache policies
│   ├── WAF association
│   ├── TLS configuration
│   └── CloudWatch metrics
│
└── Operational Workflows
    ├── Deployment verification
    ├── Smoke testing
    ├── Incident response
    ├── Rollback
    └── CI/CD automation
```

## Recommended Reading Order

The files are intentionally ordered from individual commands toward complete operational workflows.

### Core CLI Knowledge

Start with [01- CloudFront CLI Commands.md](./01-%20CloudFront%20CLI%20Commands.md) to establish familiarity with the CloudFront CLI surface and commonly used commands.

### Distribution Management

Continue with [02- Distribution Management.md](./02-%20Distribution%20Management.md) to understand how CloudFront distribution configuration is inspected and managed programmatically.

### Cache Operations

Use [03- Cache Invalidation Commands.md](./03-%20Cache%20Invalidation%20Commands.md) to understand cache invalidation and its role in application and static-asset deployments.

### Monitoring and Troubleshooting

Read [04- Monitoring and Inspection Commands.md](./04-%20Monitoring%20and%20Inspection%20Commands.md) for operational inspection and troubleshooting across CloudFront, origins, WAF, TLS, and CloudWatch.

### Production Workflows

Finish with [05- Operational CLI Workflows.md](./05-%20Operational%20CLI%20Workflows.md) to combine the individual commands into repeatable deployment, incident-response, verification, and rollback workflows.

## Operational Model

CloudFront CLI operations should generally follow this pattern:

```text
Identify
   │
   ▼
Inspect
   │
   ▼
Validate
   │
   ▼
Change
   │
   ▼
Wait
   │
   ▼
Verify
   │
   ▼
Monitor
```

For production operations, avoid treating a successful AWS CLI API response as proof that the desired system state has been reached. CloudFront configuration changes and invalidations are asynchronous operations and require explicit verification.

## Common Operational Commands

Verify the active AWS identity before production operations:

```bash
aws sts get-caller-identity
```

List distributions:

```bash
aws cloudfront list-distributions
```

Inspect a distribution:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID"
```

Retrieve the current distribution configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

Create an invalidation:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/index.html"
```

Inspect an invalidation:

```bash
aws cloudfront get-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --id "$INVALIDATION_ID"
```

## Production CLI Principles

### Verify the AWS Account

Before high-impact operations:

```bash
aws sts get-caller-identity
```

Use explicit profiles where appropriate:

```bash
aws cloudfront get-distribution \
  --profile production \
  --id "$DISTRIBUTION_ID"
```

### Inspect Before Changing

Capture the current configuration before modifying a distribution:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  > cloudfront-config.json
```

This provides a known reference point for review and rollback.

### Use Automation Carefully

CloudFront operations are well suited to CI/CD automation, but production scripts should include:

- Explicit AWS account/profile selection
- Least-privilege IAM permissions
- Input validation
- Bounded retries
- Deployment-state checks
- Smoke tests
- Failure handling
- Logging
- Rollback procedures

### Prefer Immutable Assets

For static applications, prefer versioned assets such as:

```text
app.8f42c1.js
app.91ab32.js
```

over repeatedly invalidating the same path:

```text
app.js
```

This improves cache efficiency and reduces operational dependence on invalidation.

## CloudFront in the Backend Request Path

CloudFront CLI operations are most useful when understood in the context of the complete backend architecture:

```mermaid
flowchart LR
    A[Client] --> B[DNS]
    B --> C[CloudFront]
    C --> D[AWS WAF]
    C --> E[Cache]
    E --> F[S3 / ALB / Custom Origin]
    F --> G[Nginx / Ingress]
    G --> H[Django / FastAPI]
    H --> I[Redis]
    H --> J[PostgreSQL]
    H --> K[Kafka / External Services]
```

A CloudFront incident therefore may originate outside CloudFront itself.

For example:

```text
CloudFront 5xx
     │
     ▼
Origin
     │
     ▼
ALB / Nginx / Ingress
     │
     ▼
Django / FastAPI
     │
     ├── Redis
     ├── PostgreSQL
     └── External APIs
```

The CLI should be used to validate each relevant layer rather than changing CloudFront configuration prematurely.

## CLI Tooling

These tools are particularly useful alongside the AWS CLI:

| Tool | Primary use |
|---|---|
| `aws` | AWS resource management and inspection |
| `jq` | JSON filtering and configuration inspection |
| `curl` | HTTP and cache behavior testing |
| `dig` | DNS inspection |
| `openssl` | TLS and certificate inspection |
| CloudWatch CLI | Metrics and operational signals |
| Shell scripts | Repeatable operational workflows |

Example:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.{Id:Id,Domain:DomainName,Status:Status}' \
  --output table
```

Combining `--query` with structured output is preferable to manually parsing large AWS API responses during incidents.

## Production Checklist

Before modifying a production CloudFront distribution:

- [ ] Verify the AWS account with `aws sts get-caller-identity`
- [ ] Confirm the distribution ID
- [ ] Inspect the current distribution configuration
- [ ] Capture the current ETag
- [ ] Review origins and cache behaviors
- [ ] Review security-sensitive configuration
- [ ] Validate the intended change
- [ ] Apply the smallest necessary modification
- [ ] Wait for deployment
- [ ] Run HTTP smoke tests
- [ ] Verify relevant CloudWatch metrics
- [ ] Preserve the previous configuration for rollback

## Related CloudFront Security Documentation

The CLI workflows complement the CloudFront security material in:

`05- Security/04- CloudFront`

That section covers topics such as:

- Origin Access Control
- Geo Restrictions
- Field-Level Encryption
- Signed URLs and Signed Cookies
- Security Best Practices

The CLI and security sections should be used together when operational changes involve access control, origins, authentication, or edge security.

## Key Takeaways

- **Use the CLI as an operational interface:** inspect, change, wait, verify, and monitor rather than treating individual commands as isolated actions.
- **Organize operations around workflows:** distribution management, invalidation, monitoring, troubleshooting, deployment, and rollback should be reproducible.
- **Verify production context before making changes:** confirm the AWS account, distribution ID, current configuration, and required permissions.
- **Troubleshoot the complete request path:** CloudFront is only one layer between clients and backend systems such as ALB, Nginx, Django, FastAPI, Redis, and PostgreSQL.
- **Automate safely:** production CLI workflows should use bounded retries, explicit verification, smoke tests, least-privilege credentials, and known-good rollback state.