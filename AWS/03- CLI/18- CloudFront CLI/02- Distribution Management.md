# 02- Distribution Management

## Overview

Amazon CloudFront distribution management covers the lifecycle of a CloudFront distribution: creating it, inspecting its configuration, modifying origins and behaviors, managing aliases and TLS settings, deploying changes, validating propagation, and eventually disabling or deleting it.

A CloudFront distribution is a global edge configuration rather than a conventional regional resource. A configuration change is submitted through the CloudFront control plane and then propagated across the CloudFront network. This makes distribution management fundamentally different from updating a local application configuration.

For production systems, the AWS CLI is most useful for inspection, controlled automation, troubleshooting, and CI/CD integration. Long-lived infrastructure should generally be represented in Infrastructure as Code so that distribution configuration remains version-controlled and reproducible.

## Distribution Lifecycle

A typical distribution lifecycle is:

```text
Create
  │
  ▼
Configure Origins
  │
  ▼
Configure Cache Behaviors
  │
  ▼
Configure Security / TLS
  │
  ▼
Deploy
  │
  ▼
Deployed
  │
  ├── Update
  │     │
  │     ▼
  │   InProgress
  │     │
  │     ▼
  │   Deployed
  │
  └── Disable
        │
        ▼
      Deployed
        │
        ▼
      Delete
```

The important operational distinction is between an API operation being accepted and the configuration being fully deployed.

## Distribution Discovery

### List Distributions

List all distributions:

```bash
aws cloudfront list-distributions
```

Use a table for interactive inspection:

```bash
aws cloudfront list-distributions \
  --output table
```

Extract the most useful fields:

```bash
aws cloudfront list-distributions \
  --query 'DistributionList.Items[].{Id:Id,Domain:DomainName,Status:Status,Enabled:Enabled}' \
  --output table
```

List only enabled distributions:

```bash
aws cloudfront list-distributions \
  --query 'DistributionList.Items[?Enabled==`true`].{Id:Id,Domain:DomainName,Status:Status}' \
  --output table
```

### Get a Distribution

Retrieve a distribution:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC
```

Extract the CloudFront domain:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DomainName' \
  --output text
```

Check deployment status:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.Status' \
  --output text
```

Check whether the distribution is enabled:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.Enabled' \
  --output text
```

## Distribution Configuration

CloudFront exposes distribution metadata separately from the distribution configuration.

Retrieve the configuration:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC
```

Save it for inspection:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --output json > distribution-config.json
```

A production workflow should understand the two important parts of the response:

```text
Distribution configuration
        │
        ├── DistributionConfig
        │
        └── ETag
```

The `ETag` is required for safe configuration updates.

### Extract the ETag

```bash
ETAG=$(aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'ETag' \
  --output text)
```

Verify it:

```bash
echo "$ETAG"
```

Always obtain the current ETag immediately before an update rather than reusing one from an older operation.

## Optimistic Concurrency

CloudFront uses the ETag to protect configuration updates from stale writes.

Consider two engineers retrieving the same configuration:

```text
Engineer A ── get config ──> ETag ABC
Engineer B ── get config ──> ETag ABC
```

Engineer A updates the distribution:

```text
ETag ABC
   │
   ▼
Update
   │
   ▼
ETag XYZ
```

Engineer B still has `ABC` and attempts another update.

```text
Engineer B
    │
    ▼
Update with ETag ABC
    │
    ▼
Rejected because configuration changed
```

This behavior prevents an old configuration from silently overwriting a newer configuration.

## Creating a Distribution

A distribution can be created using a complete JSON configuration:

```bash
aws cloudfront create-distribution \
  --distribution-config file://distribution-config.json
```

The configuration must define the required distribution properties, including an origin and default cache behavior.

For long-lived infrastructure, prefer:

- Terraform
- AWS CloudFormation
- AWS CDK

Use direct CLI creation primarily for:

- Experiments
- Migration tooling
- Controlled automation
- Temporary environments
- Learning the CloudFront API

A production distribution should not depend on a manually maintained local JSON file that exists only on one engineer's workstation.

## Distribution Configuration Management

A practical configuration workflow is:

```text
Retrieve current configuration
          │
          ▼
Store / inspect configuration
          │
          ▼
Make minimal change
          │
          ▼
Validate configuration
          │
          ▼
Submit with current ETag
          │
          ▼
Wait for deployment
          │
          ▼
Validate production behavior
```

For example:

```bash
DISTRIBUTION_ID="E123456789ABC"

ETAG=$(aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'ETag' \
  --output text)

aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --output json > distribution-config.json
```

After modifying the configuration:

```bash
aws cloudfront update-distribution \
  --id "$DISTRIBUTION_ID" \
  --if-match "$ETAG" \
  --distribution-config file://distribution-config.json
```

Then wait:

```bash
aws cloudfront wait distribution-deployed \
  --id "$DISTRIBUTION_ID"
```

## Updating a Distribution

The core update command is:

```bash
aws cloudfront update-distribution \
  --id E123456789ABC \
  --if-match "$ETAG" \
  --distribution-config file://distribution-config.json
```

A successful API response means CloudFront accepted the configuration. It does not necessarily mean the new configuration is already active at every edge location.

Check the status:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.Status' \
  --output text
```

Use the waiter when automation depends on completed deployment:

```bash
aws cloudfront wait distribution-deployed \
  --id E123456789ABC
```

### Why Minimal Changes Matter

CloudFront configurations contain many interconnected settings.

A small change should ideally modify only the required field.

For example, if the requirement is to change a default root object, avoid simultaneously changing:

- Origins
- Cache policies
- TLS configuration
- WAF association
- Aliases
- Logging
- Security settings

unless those changes are intentionally part of the same deployment.

Smaller changes make:

- Reviews easier
- Failures easier to diagnose
- Rollbacks safer
- Configuration drift easier to identify

## Origin Management

Origins define where CloudFront retrieves content.

Inspect origins:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.Origins.Items' \
  --output json
```

List origin IDs:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.Origins.Items[].Id' \
  --output text
```

List origin domains:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.Origins.Items[].DomainName' \
  --output table
```

Typical architectures include:

```text
                     CloudFront
                         │
            ┌────────────┼────────────┐
            │            │            │
            ▼            ▼            ▼
           S3           ALB      API Gateway
            │            │            │
         Static       Django /    Backend
         content      FastAPI      APIs
```

An origin should normally be protected against direct bypass when the application requires CloudFront to be the controlled entry point.

## Origin IDs

Path-based behaviors reference origins using an origin ID.

Inspect the mapping:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.CacheBehaviors.Items[].{Path:PathPattern,Origin:TargetOriginId}' \
  --output table
```

This is useful when troubleshooting a distribution with multiple backend services.

Example:

```text
/static/*  → S3
/media/*   → S3
/api/*     → ALB
```

The request flow becomes:

```text
Client
  │
  ▼
CloudFront
  │
  ├── /static/* ──> S3
  │
  ├── /media/*  ──> S3
  │
  └── /api/*    ──> ALB ──> Django/FastAPI
```

## Cache Behavior Management

Inspect the default cache behavior:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.DefaultCacheBehavior' \
  --output json
```

Inspect ordered behaviors:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.CacheBehaviors.Items' \
  --output json
```

List path patterns:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.CacheBehaviors.Items[].PathPattern' \
  --output table
```

List behavior-to-origin mappings:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.CacheBehaviors.Items[].{Path:PathPattern,Origin:TargetOriginId}' \
  --output table
```

Cache behaviors should be designed around application semantics.

For example:

| Path | Origin | Typical caching |
|---|---|---|
| `/static/*` | S3 | Aggressive |
| `/media/*` | S3 | Long-lived |
| `/api/*` | ALB | Usually restricted |
| `/health` | ALB | Usually no caching |

Do not cache authenticated or user-specific API responses merely because CloudFront technically permits it.

## Default Root Object

Inspect the default root object:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.DefaultRootObject' \
  --output text
```

A common static website configuration might use:

```text
index.html
```

This is different from application routing. For Django, FastAPI, or another API backend, the default root object may not be relevant.

## Aliases and Custom Domains

Inspect aliases:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.Aliases' \
  --output json
```

Extract alias names:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.Aliases.Items[]' \
  --output text
```

Aliases are used to associate custom domains such as:

```text
www.example.com
api.example.com
cdn.example.com
```

Custom domain management also requires:

- DNS configuration
- A valid CloudFront-compatible ACM certificate
- Correct certificate coverage for aliases
- Appropriate TLS configuration

## Viewer Certificate Management

Inspect certificate configuration:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.ViewerCertificate' \
  --output json
```

For CloudFront viewer HTTPS, ACM certificates must be provisioned in `us-east-1`.

Check an ACM certificate:

```bash
aws acm list-certificates \
  --region us-east-1
```

Get certificate details:

```bash
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:us-east-1:123456789012:certificate/EXAMPLE \
  --region us-east-1
```

CloudFront certificate configuration should be managed carefully because certificate replacement can affect custom-domain availability if configured incorrectly.

## HTTP to HTTPS

Inspect the viewer protocol policy:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.DefaultCacheBehavior.ViewerProtocolPolicy' \
  --output text
```

A production API or website will commonly use:

```text
redirect-to-https
```

or:

```text
https-only
```

The choice depends on whether HTTP clients should be redirected or rejected.

## HTTP Methods

Inspect allowed methods:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.DefaultCacheBehavior.AllowedMethods' \
  --output json
```

For a read-only content distribution, methods may be restricted to:

```text
GET
HEAD
```

API distributions may require methods such as:

```text
GET
HEAD
OPTIONS
POST
PUT
PATCH
DELETE
```

Do not enable unnecessary methods.

For an API backend, method support should align with the actual application contract.

## Compression

Inspect compression settings:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.DefaultCacheBehavior.Compress' \
  --output text
```

Compression can reduce response transfer size for suitable content.

However, compression should be considered alongside:

- Origin behavior
- Content type
- Cache configuration
- Application-level compression
- CPU utilization

Do not assume every response benefits equally.

## Cache Policies

Inspect the cache policy attached to the default behavior:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.DefaultCacheBehavior.CachePolicyId' \
  --output text
```

Retrieve the policy:

```bash
aws cloudfront get-cache-policy \
  --id CACHE_POLICY_ID
```

Retrieve the policy configuration:

```bash
aws cloudfront get-cache-policy-config \
  --id CACHE_POLICY_ID
```

A cache policy determines which request attributes participate in cache-key construction.

Conceptually:

```text
Request
  │
  ├── Path
  ├── Query string
  ├── Headers
  └── Cookies
        │
        ▼
   Cache Policy
        │
        ▼
    Cache Key
```

An unnecessarily large cache key creates cache fragmentation.

## Origin Request Policies

Inspect the origin request policy:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.DefaultCacheBehavior.OriginRequestPolicyId' \
  --output text
```

Retrieve it:

```bash
aws cloudfront get-origin-request-policy \
  --id POLICY_ID
```

The distinction is important:

```text
Cache Policy
→ Controls cache-key inputs

Origin Request Policy
→ Controls what CloudFront forwards to the origin
```

A backend may need a header at the origin without wanting that header to fragment the cache key.

## Origin Access Control

Inspect OAC configuration:

```bash
aws cloudfront list-origin-access-controls
```

Get a specific OAC:

```bash
aws cloudfront get-origin-access-control \
  --id OAC_ID
```

OAC is commonly used for private S3 origins.

The desired architecture is:

```text
Internet
   │
   ▼
CloudFront
   │
   │ authenticated origin request
   ▼
Private S3 bucket
```

This prevents clients from bypassing CloudFront and retrieving protected S3 objects directly.

## WAF Association

Inspect the Web ACL associated with the distribution:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.WebACLId' \
  --output text
```

CloudFront-scoped WAF operations use:

```bash
--scope CLOUDFRONT
--region us-east-1
```

Example:

```bash
aws wafv2 list-web-acls \
  --scope CLOUDFRONT \
  --region us-east-1
```

WAF should be treated as an application-layer control rather than a replacement for application authentication.

## Geographic Restrictions

Inspect restrictions:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.Restrictions' \
  --output json
```

Geographic restrictions are useful for coarse-grained content distribution policies.

They should not be treated as the application's primary authorization mechanism.

For user-specific authorization, the backend should still validate:

- Identity
- Permissions
- Tenant
- Resource ownership
- Session or token validity

## Logging

Inspect standard logging configuration:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'DistributionConfig.Logging' \
  --output json
```

Logging decisions should consider:

- Incident response
- Compliance
- Privacy
- Storage costs
- Retention
- Sensitive query parameters
- Authorization material

Do not accidentally expose signed URLs, credentials, or sensitive application data through operational logs.

## Tags

List distribution tags:

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

Recommended tags commonly include:

| Tag | Example |
|---|---|
| `Environment` | `production` |
| `Application` | `backend-api` |
| `Owner` | `platform-team` |
| `CostCenter` | `engineering` |
| `ManagedBy` | `terraform` |

Tags improve operational ownership and governance.

## Cache Invalidation

Create an invalidation:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths "/index.html"
```

Invalidate several objects:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths "/index.html" "/app.js" "/styles.css"
```

Invalidate everything:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths "/*"
```

Use `/*` carefully.

For static assets, immutable filenames are usually a better deployment model:

```text
app.91f83a.js
app.2a4c9e.js
```

instead of repeatedly invalidating:

```text
app.js
```

This reduces dependence on cache invalidation and improves cache efficiency.

### List Invalidations

```bash
aws cloudfront list-invalidations \
  --distribution-id E123456789ABC
```

Extract status:

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

## CloudFront Functions

List functions:

```bash
aws cloudfront list-functions
```

Inspect a function:

```bash
aws cloudfront describe-function \
  --name normalize-request
```

CloudFront Functions are useful for lightweight edge transformations such as:

- URL normalization
- Redirects
- Header manipulation
- Simple request transformations

They should not be treated as a general-purpose backend execution environment.

## Distribution Disablement

A distribution normally must be disabled before deletion.

Retrieve its configuration:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --output json > distribution-config.json
```

Set:

```json
{
  "Enabled": false
}
```

Then retrieve a current ETag:

```bash
ETAG=$(aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'ETag' \
  --output text)
```

Update:

```bash
aws cloudfront update-distribution \
  --id E123456789ABC \
  --if-match "$ETAG" \
  --distribution-config file://distribution-config.json
```

Wait:

```bash
aws cloudfront wait distribution-deployed \
  --id E123456789ABC
```

Verify:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.Enabled' \
  --output text
```

## Distribution Deletion

After the distribution has been disabled and the change has deployed, obtain the current ETag:

```bash
ETAG=$(aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'ETag' \
  --output text)
```

Delete:

```bash
aws cloudfront delete-distribution \
  --id E123456789ABC \
  --if-match "$ETAG"
```

Do not delete a distribution as a first response to a deployment problem. In production, disabling or replacing infrastructure should be an intentional lifecycle operation.

## Distribution Deployment

CloudFront configuration propagation is asynchronous.

Check status:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.Status' \
  --output text
```

Wait:

```bash
aws cloudfront wait distribution-deployed \
  --id E123456789ABC
```

A CI/CD pipeline can use:

```bash
aws cloudfront update-distribution \
  --id "$DISTRIBUTION_ID" \
  --if-match "$ETAG" \
  --distribution-config file://distribution-config.json

aws cloudfront wait distribution-deployed \
  --id "$DISTRIBUTION_ID"
```

Avoid:

```bash
sleep 300
```

as the primary deployment synchronization mechanism.

A fixed sleep is both inefficient and unreliable because deployment duration can vary.

## Production Deployment Pattern

A robust deployment sequence is:

```text
Git commit
    │
    ▼
CI validation
    │
    ▼
Infrastructure plan
    │
    ▼
Approval
    │
    ▼
CloudFront update
    │
    ▼
Distribution InProgress
    │
    ▼
Wait for deployment
    │
    ▼
Smoke tests
    │
    ▼
Monitor edge/origin metrics
```

For example:

```bash
set -euo pipefail

DISTRIBUTION_ID="E123456789ABC"

ETAG=$(aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'ETag' \
  --output text)

aws cloudfront update-distribution \
  --id "$DISTRIBUTION_ID" \
  --if-match "$ETAG" \
  --distribution-config file://distribution-config.json

aws cloudfront wait distribution-deployed \
  --id "$DISTRIBUTION_ID"

curl --fail --silent --show-error \
  https://www.example.com/health
```

In a mature environment, the configuration itself should normally come from Infrastructure as Code rather than being edited manually inside a CI shell script.

## Distribution Inspection Script

A useful operational script:

```bash
#!/usr/bin/env bash

set -euo pipefail

DISTRIBUTION_ID="${1:?Usage: $0 <distribution-id>}"

echo "=== Distribution ==="

aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.{Id:Id,Domain:DomainName,Status:Status,Enabled:DistributionConfig.Enabled}' \
  --output table

echo
echo "=== Origins ==="

aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.Origins.Items[].{Id:Id,Domain:DomainName}' \
  --output table

echo
echo "=== Cache Behaviors ==="

aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.CacheBehaviors.Items[].{Path:PathPattern,Origin:TargetOriginId}' \
  --output table

echo
echo "=== Aliases ==="

aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.Aliases.Items[]' \
  --output text

echo
echo "=== Invalidations ==="

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

## Configuration Areas

A CloudFront distribution should be thought of as several related configuration domains:

| Area | Responsibility |
|---|---|
| Origins | Backend content sources |
| Cache behaviors | Request routing and behavior |
| Cache policies | Cache-key design |
| Origin request policies | Origin-bound request attributes |
| TLS | Viewer HTTPS and certificates |
| Aliases | Custom domain names |
| WAF | Application-layer filtering |
| OAC | Secure origin access |
| Geo restrictions | Coarse geographic access control |
| Logging | Operational visibility |
| Functions | Edge request transformation |
| Invalidation | Cache object removal |
| Tags | Governance and ownership |

Changing one area can affect the behavior of others.

For example:

```text
Cache Policy
      │
      ▼
Cache Key
      │
      ▼
Cache Hit/Miss
      │
      ▼
Origin Request Policy
      │
      ▼
Origin Request
```

A senior engineer should reason about the entire request lifecycle rather than treating each configuration field independently.

## High Availability Considerations

CloudFront is globally distributed, but the origin architecture still matters.

For example:

```text
                    CloudFront
                        │
                        ▼
                 Origin Group
                  /          \
                 /            \
                ▼              ▼
          Primary ALB     Secondary ALB
                │              │
                ▼              ▼
          App Instances   App Instances
```

CloudFront cannot compensate for an unavailable origin if the architecture does not provide an appropriate failover strategy.

Consider:

- Multiple application instances
- Multi-AZ load balancing
- Origin failover where appropriate
- Health checks
- Database availability
- Stateless application design
- Graceful degradation

## Security Considerations

Distribution management should follow least privilege.

A deployment role may require permissions such as:

```text
cloudfront:GetDistribution
cloudfront:GetDistributionConfig
cloudfront:UpdateDistribution
cloudfront:CreateInvalidation
cloudfront:ListInvalidations
```

Avoid giving every developer unrestricted CloudFront administration.

Additional controls should include:

- Private S3 origins with OAC
- HTTPS for viewers
- Appropriate TLS policy
- WAF protection
- Restricted origin access
- Secure signing keys
- IAM least privilege
- Controlled CI/CD credentials
- Audit logging

Do not place AWS access keys or private signing keys in distribution configuration files committed to Git.

## Cost Considerations

Distribution management decisions can affect cost indirectly.

Examples include:

- Excessive cache invalidations
- Poor cache hit ratios
- Unnecessary origin requests
- Excessive logging
- Large response sizes
- Unoptimized cache keys

A good cache strategy can reduce origin traffic and improve latency simultaneously.

The optimization target should not simply be "maximum caching."

The correct objective is:

```text
Correctness
    +
Security
    +
Cache efficiency
    +
Origin protection
    +
Acceptable cost
```

## Common Mistakes

### Editing a Distribution Without Retrieving Its Current ETag

Incorrect:

```bash
aws cloudfront update-distribution \
  --id E123456789ABC \
  --if-match OLD_ETAG \
  --distribution-config file://distribution-config.json
```

Use the latest ETag:

```bash
ETAG=$(aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'ETag' \
  --output text)
```

### Assuming an Update Is Immediately Live

An accepted update can still be:

```text
InProgress
```

Use:

```bash
aws cloudfront wait distribution-deployed \
  --id E123456789ABC
```

when necessary.

### Using Arbitrary Sleep Durations

Avoid:

```bash
sleep 600
```

Prefer CloudFront waiters.

### Using Full Cache Invalidation for Every Release

Avoid:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*"
```

for every static asset deployment.

Use immutable asset versioning where possible.

### Forwarding Everything to the Origin

Forwarding every cookie, header, and query string can destroy cache efficiency.

Design cache policies deliberately.

### Making S3 Public

If S3 is intended to be accessed through CloudFront, prefer OAC and a private bucket rather than relying on public bucket access.

### Treating Geo Restrictions as Authorization

Geographic restrictions are coarse-grained.

Application authorization still belongs in the application or an appropriate identity/access-control layer.

### Treating WAF as Authentication

WAF can filter requests, but it does not establish application identity or enforce business-level permissions.

### Manual Configuration Drift

If engineers repeatedly modify a production distribution through the console or ad-hoc CLI commands, the actual infrastructure can diverge from the intended configuration.

Use Infrastructure as Code for persistent environments.

## Interview Traps

### Is CloudFront a regional resource?

CloudFront is a global service. However, related resources can have regional requirements, most notably ACM certificates used for CloudFront viewer HTTPS, which must be in `us-east-1`.

### Does a successful `update-distribution` mean deployment is complete?

No.

The API operation can succeed while the distribution remains `InProgress`.

### Why does CloudFront require an ETag?

The ETag provides optimistic concurrency control so stale configurations do not silently overwrite newer changes.

### Why use OAC with S3?

OAC allows CloudFront to authenticate requests to a private S3 origin, reducing the ability for clients to bypass CloudFront and access the bucket directly.

### Does invalidation change the cache policy?

No.

Invalidation removes cached objects. Cache policy controls how requests map to cache keys.

### Should CloudFront cache all API responses?

No.

Caching API responses requires careful consideration of:

- Authentication
- User-specific data
- Authorization
- Cookies
- Headers
- Query parameters
- Cache lifetime
- Data freshness

### Should CloudFront replace Nginx?

Not necessarily.

CloudFront and Nginx operate at different layers.

A common architecture is:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
ALB
  │
  ▼
Nginx
  │
  ▼
Django / FastAPI
```

Nginx can still provide application-adjacent reverse-proxy functionality while CloudFront provides global edge delivery.

## Operational Best Practices

| Area | Production recommendation |
|---|---|
| Configuration | Manage persistent configuration as code |
| ETag | Retrieve the current ETag immediately before updates |
| Deployment | Wait for `Deployed` when required |
| Changes | Prefer small, isolated changes |
| Caching | Design cache keys deliberately |
| Assets | Prefer immutable versioned filenames |
| Invalidation | Avoid unnecessary `/*` invalidations |
| Origins | Protect origins from direct bypass |
| S3 | Prefer private buckets with OAC |
| TLS | Enforce appropriate HTTPS policy |
| WAF | Apply application-layer filtering where required |
| IAM | Use least-privilege deployment roles |
| Logging | Avoid sensitive data exposure |
| Tags | Identify owner, application, environment, and cost center |
| CI/CD | Validate configuration before deployment |
| Rollback | Preserve a known-good infrastructure state |

## Useful CLI Options

The following global options are particularly useful for operational scripts:

```bash
--output json
--output table
--output text
--query '...'
--profile production
--no-cli-pager
```

Example:

```bash
aws cloudfront list-distributions \
  --profile production \
  --no-cli-pager \
  --output table
```

For scripts:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --no-cli-pager \
  --output json
```

## Key Takeaways

- **CloudFront distribution management is asynchronous:** an accepted configuration update can remain `InProgress` until it has propagated.
- **ETags provide optimistic concurrency control:** retrieve the current ETag immediately before modifying a distribution.
- **Treat origins, cache behaviors, policies, TLS, WAF, OAC, and aliases as interconnected configuration domains.**
- **Use versioned assets and deliberate cache policies instead of relying on full-distribution invalidations for every deployment.**
- **For production infrastructure, use the AWS CLI primarily for inspection and controlled automation while keeping the desired CloudFront configuration in Infrastructure as Code.**