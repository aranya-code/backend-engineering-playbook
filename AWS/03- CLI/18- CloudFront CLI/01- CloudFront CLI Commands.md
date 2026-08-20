# 01- CloudFront CLI Commands

## Overview

The AWS CLI provides a repeatable interface for creating, inspecting, updating, and operating Amazon CloudFront distributions and their related security and origin resources.

CloudFront CLI work is different from simple resource-oriented services because a distribution is a relatively large configuration object. Many operations require retrieving the current configuration, modifying a specific field, and submitting the complete updated configuration with the current `ETag`. Production workflows therefore need to account for configuration versioning, optimistic concurrency, asynchronous deployments, and the difference between distribution configuration and runtime traffic behavior.

This document focuses on practical AWS CLI commands for CloudFront administration, troubleshooting, security configuration, and production operations.

## AWS CLI Prerequisites

Verify that the AWS CLI is installed:

```bash
aws --version
```

Verify the active identity:

```bash
aws sts get-caller-identity
```

Example output:

```json
{
  "UserId": "AIDAXXXXXXXXXXXXXXXX",
  "Account": "123456789012",
  "Arn": "arn:aws:iam::123456789012:user/admin"
}
```

For production automation, prefer IAM roles and short-lived credentials over long-lived access keys.

Check the configured region:

```bash
aws configure get region
```

CloudFront is a global service, so most CloudFront commands do not require a region-specific CloudFront endpoint. Related resources such as ACM certificates have regional requirements; for example, certificates used by CloudFront must be provisioned in `us-east-1`.

## Command Structure

The general AWS CLI structure is:

```bash
aws <service> <command> [options]
```

For CloudFront:

```bash
aws cloudfront <command> [options]
```

Examples:

```bash
aws cloudfront list-distributions
aws cloudfront get-distribution --id E123456789ABC
aws cloudfront get-distribution-config --id E123456789ABC
```

Use `--output table` for interactive inspection:

```bash
aws cloudfront list-distributions --output table
```

Use JSON for automation:

```bash
aws cloudfront list-distributions --output json
```

Use JMESPath queries to extract specific fields:

```bash
aws cloudfront list-distributions \
  --query 'DistributionList.Items[].{Id:Id,Domain:DomainName,Status:Status}' \
  --output table
```

## Distribution Discovery

### List Distributions

```bash
aws cloudfront list-distributions
```

List only distribution IDs and domains:

```bash
aws cloudfront list-distributions \
  --query 'DistributionList.Items[].{Id:Id,Domain:DomainName}' \
  --output table
```

List distributions with deployment status:

```bash
aws cloudfront list-distributions \
  --query 'DistributionList.Items[].{Id:Id,Domain:DomainName,Status:Status}' \
  --output table
```

A distribution can remain in an `InProgress` state while CloudFront propagates a configuration change globally.

### Get a Distribution

```bash
aws cloudfront get-distribution \
  --id E123456789ABC
```

The response contains both distribution metadata and configuration information.

Extract the CloudFront domain:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DomainName' \
  --output text
```

Extract deployment status:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.Status' \
  --output text
```

## Distribution Configuration

### Retrieve Configuration

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC
```

Save the configuration locally:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --output json > cloudfront-config.json
```

The response contains an `ETag` and the actual distribution configuration.

This distinction matters because updates require the current `ETag`.

### Extract the ETag

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'ETag' \
  --output text
```

Store it in a shell variable:

```bash
ETAG=$(aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'ETag' \
  --output text)
```

## Updating a Distribution

CloudFront distribution updates commonly follow this workflow:

```text
Get configuration
      │
      ▼
Extract ETag
      │
      ▼
Modify configuration
      │
      ▼
Submit configuration + ETag
      │
      ▼
CloudFront validates request
      │
      ▼
Distribution enters InProgress
      │
      ▼
Configuration propagates globally
```

Retrieve the configuration:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --output json > distribution.json
```

Modify the configuration while preserving the required CloudFront structure.

Then submit it:

```bash
aws cloudfront update-distribution \
  --id E123456789ABC \
  --if-match "$ETAG" \
  --distribution-config file://distribution.json
```

The `file://` prefix tells the AWS CLI to read the configuration from a local file.

### Why `ETag` Matters

CloudFront uses optimistic concurrency control.

Suppose two engineers retrieve the same configuration:

```text
Engineer A ── get config ──> ETag: ABC

Engineer B ── get config ──> ETag: ABC
```

Engineer A updates the distribution:

```text
ETag ABC → ETag XYZ
```

Engineer B then attempts to update using stale `ABC`.

CloudFront can reject the operation because the configuration has changed since it was retrieved.

This prevents one stale configuration from silently overwriting another update.

## Distribution Deployment Status

Check status:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.Status' \
  --output text
```

Typical operational interpretation:

| Status | Meaning |
|---|---|
| `Deployed` | Configuration has completed deployment |
| `InProgress` | Configuration is still propagating |

For automation, do not assume that a successful `update-distribution` API call means the new configuration is already active everywhere.

## Wait for Distribution Deployment

The AWS CLI supports waiters:

```bash
aws cloudfront wait distribution-deployed \
  --id E123456789ABC
```

This is useful in CI/CD pipelines when a later deployment step depends on the distribution reaching the deployed state.

Example:

```bash
aws cloudfront update-distribution \
  --id E123456789ABC \
  --if-match "$ETAG" \
  --distribution-config file://distribution.json

aws cloudfront wait distribution-deployed \
  --id E123456789ABC
```

Avoid using arbitrary `sleep` commands as the primary synchronization mechanism.

## Distribution Creation

CloudFront distributions require a complete distribution configuration.

A configuration can be supplied from a JSON file:

```bash
aws cloudfront create-distribution \
  --distribution-config file://distribution-config.json
```

For production systems, create the configuration from Infrastructure as Code rather than manually constructing large CLI JSON documents.

CLI-based creation is useful for:

- Learning CloudFront APIs
- Temporary environments
- Automation experiments
- Debugging
- Migration scripts

Terraform, CloudFormation, or CDK is generally easier to maintain for long-lived production infrastructure.

## Distribution Deletion

A CloudFront distribution normally must be disabled before it can be deleted.

Disable the distribution by updating its configuration:

```json
{
  "Enabled": false
}
```

Then wait for deployment:

```bash
aws cloudfront wait distribution-deployed \
  --id E123456789ABC
```

Retrieve the latest ETag:

```bash
ETAG=$(aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'ETag' \
  --output text)
```

Delete the distribution:

```bash
aws cloudfront delete-distribution \
  --id E123456789ABC \
  --if-match "$ETAG"
```

The important lifecycle is:

```text
Enabled
   │
   ▼
Update Enabled=false
   │
   ▼
Wait for deployment
   │
   ▼
Delete distribution
```

## CloudFront Origins

Inspect configured origins:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.Origins.Items' \
  --output json
```

Extract origin IDs:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.Origins.Items[].Id' \
  --output text
```

Extract origin domains:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.Origins.Items[].DomainName' \
  --output table
```

For a backend architecture, origins may include:

```text
CloudFront
   │
   ├── S3
   ├── ALB
   ├── API Gateway
   └── Custom HTTP origin
```

## Cache Behaviors

Inspect the default cache behavior:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.DefaultCacheBehavior' \
  --output json
```

Inspect path-based behaviors:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.CacheBehaviors.Items' \
  --output json
```

Extract path patterns:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.CacheBehaviors.Items[].PathPattern' \
  --output table
```

A common backend configuration might separate:

```text
/static/*
/media/*
/api/*
```

because each path can have different caching, forwarding, authorization, and origin requirements.

## Cache Invalidation

Create an invalidation:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths "/index.html"
```

Invalidate multiple paths:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths "/index.html" "/app.js" "/styles.css"
```

Invalidate an entire distribution:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths "/*"
```

The wildcard is operationally convenient but should not be the default response to every deployment.

For static assets, prefer immutable versioned filenames:

```text
app.91f83a.js
app.3a8c91d.js
```

instead of repeatedly invalidating:

```text
app.js
```

This improves cache efficiency and reduces dependence on invalidation.

### List Invalidations

```bash
aws cloudfront list-invalidations \
  --distribution-id E123456789ABC
```

Extract invalidation IDs and statuses:

```bash
aws cloudfront list-invalidations \
  --distribution-id E123456789ABC \
  --query 'InvalidationList.Items[].{Id:Id,Status:Status,Created:CreateTime}' \
  --output table
```

### Get an Invalidation

```bash
aws cloudfront get-invalidation \
  --distribution-id E123456789ABC \
  --id I123456789ABC
```

## CloudFront Cache Policies

List cache policies:

```bash
aws cloudfront list-cache-policies
```

List managed policies:

```bash
aws cloudfront list-cache-policies \
  --type managed
```

List custom policies:

```bash
aws cloudfront list-cache-policies \
  --type custom
```

Retrieve a specific policy:

```bash
aws cloudfront get-cache-policy \
  --id CACHE_POLICY_ID
```

Extract the policy configuration:

```bash
aws cloudfront get-cache-policy-config \
  --id CACHE_POLICY_ID
```

Cache policy design affects:

- Cache hit ratio
- Origin load
- Response latency
- Query-string behavior
- Cookie handling
- Header handling
- Cache fragmentation
- Security

Do not forward every request attribute simply because the origin can process it.

## Origin Request Policies

List origin request policies:

```bash
aws cloudfront list-origin-request-policies
```

Get a policy:

```bash
aws cloudfront get-origin-request-policy \
  --id POLICY_ID
```

Retrieve its configuration:

```bash
aws cloudfront get-origin-request-policy-config \
  --id POLICY_ID
```

A useful distinction is:

```text
Cache Policy
    → What contributes to the cache key

Origin Request Policy
    → What CloudFront sends to the origin
```

These are related but not interchangeable.

## CloudFront Functions

List CloudFront Functions:

```bash
aws cloudfront list-functions
```

Get function configuration:

```bash
aws cloudfront describe-function \
  --name my-function
```

Get function code:

```bash
aws cloudfront get-function \
  --name my-function
```

CloudFront Functions are designed for lightweight edge logic such as:

- URL normalization
- Header manipulation
- Redirects
- Simple request transformations

Do not treat CloudFront Functions as a replacement for a general-purpose backend runtime.

## CloudFront Key Groups

List public keys:

```bash
aws cloudfront list-public-keys
```

List key groups:

```bash
aws cloudfront list-key-groups
```

Get a key group:

```bash
aws cloudfront get-key-group \
  --id KEY_GROUP_ID
```

Key groups are relevant when implementing signed URLs and signed cookies using trusted key groups.

## Origin Access Control

List Origin Access Controls:

```bash
aws cloudfront list-origin-access-controls
```

Get an OAC:

```bash
aws cloudfront get-origin-access-control \
  --id OAC_ID
```

OAC is commonly used to allow CloudFront to access a private S3 origin.

The security model should resemble:

```text
Internet
   │
   ▼
CloudFront
   │
   │ OAC-authenticated request
   ▼
Private S3 bucket
```

The goal is to prevent users from bypassing CloudFront and accessing the bucket directly.

## AWS WAF Integration

List Web ACLs:

```bash
aws wafv2 list-web-acls \
  --scope CLOUDFRONT \
  --region us-east-1
```

For CloudFront-scoped WAF resources, use the `CLOUDFRONT` scope and the `us-east-1` region for AWS WAF API operations.

Inspect a Web ACL:

```bash
aws wafv2 get-web-acl \
  --name my-cloudfront-web-acl \
  --scope CLOUDFRONT \
  --id WEB_ACL_ID \
  --region us-east-1
```

The relationship is:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
AWS WAF
  │
  ├── Allow
  ├── Block
  ├── Count
  └── Challenge
```

## AWS Shield

AWS Shield is primarily concerned with DDoS protection rather than HTTP application filtering.

A simplified model is:

```text
Internet
    │
    ▼
AWS Edge
    │
    ├── Shield
    │
    ▼
CloudFront
    │
    ▼
Origin
```

Shield and WAF solve different problems:

| Service | Primary responsibility |
|---|---|
| AWS Shield | DDoS protection |
| AWS WAF | Application-layer request filtering |
| CloudFront | Edge delivery and traffic handling |

## Geo Restrictions

Inspect geographic restriction configuration:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.Restrictions' \
  --output json
```

Geo restrictions should be treated as a coarse access-control mechanism.

They are not a replacement for application authorization.

## TLS and Viewer Certificate

Inspect the viewer certificate:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.ViewerCertificate' \
  --output json
```

Typical production considerations include:

- HTTPS enforcement
- ACM certificate
- Supported TLS protocol versions
- Custom domain aliases
- Certificate renewal
- Redirecting HTTP to HTTPS

CloudFront ACM certificates for viewer HTTPS must be provisioned in `us-east-1`.

## Logging Configuration

Inspect distribution logging configuration:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.Logging' \
  --output json
```

Logging configuration should be evaluated alongside:

- Privacy requirements
- Compliance requirements
- Storage costs
- Retention policies
- Incident-response requirements

Do not blindly log sensitive query parameters, authorization material, or private signed URLs.

## Distribution Tags

List tags:

```bash
aws cloudfront list-tags-for-resource \
  --resource arn:aws:cloudfront::123456789012:distribution/E123456789ABC
```

Add tags:

```bash
aws cloudfront tag-resource \
  --resource arn:aws:cloudfront::123456789012:distribution/E123456789ABC \
  --tags 'Items=[{Key=Environment,Value=production},{Key=Application,Value=backend-api}]'
```

Tags are useful for:

- Ownership
- Cost allocation
- Environment identification
- Automation
- Governance

## CloudFront Origin Failover

For distributions using origin groups, inspect origin-group configuration:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.OriginGroups' \
  --output json
```

An origin group can provide failover behavior such as:

```text
             CloudFront
                 │
                 ▼
          Primary Origin
            /        \
        success     failure
          │            │
          ▼            ▼
       Response    Secondary
                    Origin
```

Origin failover should be designed around actual failure modes rather than treated as automatic disaster recovery.

## CloudFront CLI with JMESPath

JMESPath is especially useful for operational inspection.

List only production distributions:

```bash
aws cloudfront list-distributions \
  --query 'DistributionList.Items[?contains(Comment, `production`)].{Id:Id,Domain:DomainName,Status:Status}' \
  --output table
```

Extract all aliases:

```bash
aws cloudfront list-distributions \
  --query 'DistributionList.Items[].Aliases.Items[]' \
  --output text
```

Find enabled distributions:

```bash
aws cloudfront list-distributions \
  --query 'DistributionList.Items[?Enabled==`true`].{Id:Id,Domain:DomainName}' \
  --output table
```

JMESPath reduces the amount of shell processing required and is preferable to parsing human-readable CLI output.

## Practical Inspection Script

A simple production diagnostic script can inspect a distribution:

```bash
#!/usr/bin/env bash

set -euo pipefail

DISTRIBUTION_ID="${1:?Usage: $0 <distribution-id>}"

echo "Distribution:"
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.{Id:Id,Domain:DomainName,Status:Status,Enabled:DistributionConfig.Enabled}' \
  --output table

echo
echo "Origins:"
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.Origins.Items[].{Id:Id,Domain:DomainName}' \
  --output table

echo
echo "Cache Behaviors:"
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.CacheBehaviors.Items[].{Path:PathPattern,Target:TargetOriginId}' \
  --output table

echo
echo "Invalidations:"
aws cloudfront list-invalidations \
  --distribution-id "$DISTRIBUTION_ID" \
  --query 'InvalidationList.Items[].{Id:Id,Status:Status,Created:CreateTime}' \
  --output table
```

Run:

```bash
chmod +x inspect-cloudfront.sh

./inspect-cloudfront.sh E123456789ABC
```

## Production CLI Workflow

A safe manual configuration workflow is:

```text
1. Identify distribution
        │
        ▼
2. Retrieve current configuration
        │
        ▼
3. Record current ETag
        │
        ▼
4. Make minimal configuration change
        │
        ▼
5. Validate JSON/configuration
        │
        ▼
6. Update distribution with ETag
        │
        ▼
7. Wait for deployment
        │
        ▼
8. Validate behavior
        │
        ▼
9. Monitor errors and origin traffic
```

Avoid making unrelated configuration changes in the same update.

Smaller changes are easier to review, troubleshoot, and roll back.

## CI/CD Considerations

A CI/CD pipeline should distinguish between:

```text
Configuration deployment
        │
        ▼
CloudFront API accepts update
        │
        ▼
Distribution propagation
        │
        ▼
Functional validation
```

A simplified pipeline can look like:

```bash
aws cloudfront update-distribution \
  --id "$DISTRIBUTION_ID" \
  --if-match "$ETAG" \
  --distribution-config file://distribution.json

aws cloudfront wait distribution-deployed \
  --id "$DISTRIBUTION_ID"

curl --fail --silent --show-error \
  "https://www.example.com/health"
```

For larger environments, use Infrastructure as Code so the desired state is version-controlled.

## Common Mistakes

### Treating CloudFront as a regional service

CloudFront is global.

Related services can have regional constraints, however. For example, CloudFront viewer certificates from ACM must be in `us-east-1`.

### Updating with a stale ETag

Do not cache an ETag for later reuse.

Retrieve the current configuration immediately before making an update:

```bash
ETAG=$(aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'ETag' \
  --output text)
```

### Assuming API success means deployment completion

An accepted update can still be propagating.

Use:

```bash
aws cloudfront wait distribution-deployed \
  --id "$DISTRIBUTION_ID"
```

when subsequent automation depends on the completed deployment.

### Using `/*` invalidation for every deployment

This can become operationally expensive and indicates that asset versioning may be missing.

Prefer immutable asset names where practical.

### Making the S3 bucket public

CloudFront should not require a public S3 bucket for a protected architecture.

Use Origin Access Control and keep the bucket private.

### Confusing WAF with authentication

WAF can block suspicious or unauthorized-looking traffic patterns, but it does not replace application authentication and authorization.

### Forwarding everything to the origin

Forwarding all cookies, query strings, and headers can:

- Reduce cache hit ratio
- Increase origin traffic
- Increase latency
- Create cache fragmentation
- Increase security complexity

Forward only what the application actually requires.

### Editing large JSON configurations carelessly

CloudFront configuration objects are extensive. A small structural mistake can cause the entire update to fail.

Keep configurations version-controlled and validate changes before deployment.

## Operational Best Practices

| Practice | Recommendation |
|---|---|
| Configuration | Manage production configuration as code |
| Updates | Retrieve the current ETag immediately before updates |
| Deployment | Wait for distribution deployment when required |
| Caching | Design cache keys intentionally |
| Invalidation | Prefer versioned assets |
| Origin | Protect origins from direct bypass |
| S3 | Use private buckets with OAC |
| WAF | Use explicit Web ACL rules and monitor matches |
| TLS | Enforce HTTPS and maintain appropriate TLS policy |
| Credentials | Never expose private signing keys |
| Logging | Avoid logging sensitive authorization material |
| Automation | Use IAM roles and least privilege |
| Validation | Test edge behavior after configuration changes |
| Rollback | Keep previous known-good configuration available |

## Command Reference

| Task | Command |
|---|---|
| List distributions | `aws cloudfront list-distributions` |
| Get distribution | `aws cloudfront get-distribution --id ID` |
| Get configuration | `aws cloudfront get-distribution-config --id ID` |
| Update distribution | `aws cloudfront update-distribution` |
| Wait for deployment | `aws cloudfront wait distribution-deployed --id ID` |
| Create distribution | `aws cloudfront create-distribution` |
| Delete distribution | `aws cloudfront delete-distribution` |
| Create invalidation | `aws cloudfront create-invalidation` |
| List invalidations | `aws cloudfront list-invalidations` |
| Get invalidation | `aws cloudfront get-invalidation` |
| List cache policies | `aws cloudfront list-cache-policies` |
| Get cache policy | `aws cloudfront get-cache-policy` |
| List origin request policies | `aws cloudfront list-origin-request-policies` |
| Get origin request policy | `aws cloudfront get-origin-request-policy` |
| List functions | `aws cloudfront list-functions` |
| List key groups | `aws cloudfront list-key-groups` |
| List public keys | `aws cloudfront list-public-keys` |
| List OACs | `aws cloudfront list-origin-access-controls` |
| Get OAC | `aws cloudfront get-origin-access-control` |
| List distribution tags | `aws cloudfront list-tags-for-resource` |
| Add tags | `aws cloudfront tag-resource` |

## Useful Global CLI Options

These options are useful across many AWS CLI commands:

```bash
--output json
--output table
--output text
--query '...'
--profile production
--no-cli-pager
```

For example:

```bash
aws cloudfront list-distributions \
  --profile production \
  --no-cli-pager \
  --output table
```

Disable the pager in scripts:

```bash
aws cloudfront list-distributions --no-cli-pager
```

This avoids interactive behavior in CI/CD environments.

## Troubleshooting Checklist

When a CloudFront CLI operation fails, inspect the following:

```text
Authentication
    │
    ├── aws sts get-caller-identity
    │
    ▼
Permissions
    │
    ├── IAM policy
    │
    ▼
Distribution ID
    │
    ├── Correct distribution?
    │
    ▼
ETag
    │
    ├── Current?
    │
    ▼
Configuration
    │
    ├── Valid JSON?
    ├── Required fields present?
    │
    ▼
Deployment
    │
    ├── InProgress?
    └── Deployed?
```

Start with:

```bash
aws sts get-caller-identity
```

Then:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID"
```

Then:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

Finally inspect the current ETag:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'ETag' \
  --output text
```

## Interview Traps

### CloudFront vs S3

CloudFront is not a storage service.

```text
S3
→ stores objects

CloudFront
→ delivers content from origins
```

### CloudFront vs WAF

CloudFront provides global edge delivery and request handling.

WAF evaluates requests against Web ACL rules.

They complement each other.

### Invalidation vs Cache Policy

An invalidation removes cached objects from CloudFront.

A cache policy determines how CloudFront constructs and manages cache behavior.

Changing a cache policy is not equivalent to invalidating objects.

### Origin Request Policy vs Cache Policy

These control different dimensions of request processing.

```text
Cache Policy
→ cache key

Origin Request Policy
→ origin-bound request attributes
```

### CloudFront Distribution vs Origin

A distribution is the edge-facing CloudFront configuration.

An origin is the backend source from which CloudFront retrieves content.

```text
Client
  │
  ▼
Distribution
  │
  ▼
Origin
```

## Key Takeaways

- **CloudFront CLI operations are configuration-oriented:** retrieve the current configuration, use its `ETag`, make a minimal change, and update the distribution.
- **CloudFront deployments are asynchronous:** an accepted update can remain `InProgress`, so use the deployment waiter when automation depends on propagation.
- **Use JMESPath aggressively for operational inspection:** it makes large CloudFront responses easier to query and safer to consume in scripts.
- **Treat caching, invalidation, WAF, OAC, TLS, and signing as separate controls:** each solves a different operational or security problem.
- **For production, prefer Infrastructure as Code and CI/CD:** use the CLI for inspection, controlled automation, troubleshooting, and workflows where direct API interaction is justified.