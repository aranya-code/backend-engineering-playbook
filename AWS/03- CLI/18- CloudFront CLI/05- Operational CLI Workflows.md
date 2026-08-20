# 05- Operational CLI Workflows

## Overview

CloudFront operational work is rarely a single AWS CLI command. Production tasks usually involve a sequence of inspection, validation, change, deployment, verification, and rollback steps.

A reliable workflow treats CloudFront as part of an end-to-end request path rather than as an isolated AWS service:

```text
Client
  │
  ▼
DNS
  │
  ▼
CloudFront
  │
  ├── WAF
  ├── TLS
  ├── Cache Behavior
  ├── Cache Policy
  └── Origin Request Policy
          │
          ▼
       Origin
          │
          ├── S3
          ├── ALB
          └── Application
                  │
                  ├── Django / FastAPI
                  ├── Redis
                  └── PostgreSQL
```

The AWS CLI is particularly valuable for operational workflows because commands can be:

- Reproduced consistently
- Executed during incidents
- Integrated into CI/CD
- Wrapped in shell scripts
- Used for pre-deployment validation
- Used for post-deployment verification
- Combined with `jq`, `curl`, and CloudWatch
- Audited through command history and CI logs

The important principle is:

> **Inspect first, change deliberately, verify afterward.**

## AWS CLI Setup

Verify the CLI installation:

```bash
aws --version
```

Verify the active identity:

```bash
aws sts get-caller-identity
```

Check the configured profile:

```bash
aws configure list
```

Use an explicit profile for production:

```bash
aws cloudfront list-distributions \
  --profile production
```

Define common variables:

```bash
export AWS_PROFILE="production"
export DISTRIBUTION_ID="E123456789ABC"
export DOMAIN="cdn.example.com"
```

Using variables reduces copy/paste errors and makes operational scripts reusable.

## Basic Distribution Health Workflow

The first workflow for most CloudFront incidents is to establish whether the distribution itself is correctly deployed.

### Check Distribution Status

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.{Id:Id,Domain:DomainName,Status:Status,Enabled:DistributionConfig.Enabled}' \
  --output table
```

A healthy configuration deployment normally reports:

```text
Status = Deployed
Enabled = True
```

However:

```text
Deployed != Application Healthy
```

A deployed CloudFront distribution can still route requests to an unhealthy ALB, Nginx instance, Kubernetes ingress, Django application, FastAPI application, or S3 configuration.

### Verify the CloudFront Endpoint

```bash
curl -I "https://$DOMAIN"
```

For detailed HTTP information:

```bash
curl -vI "https://$DOMAIN"
```

Follow redirects:

```bash
curl -IL "https://$DOMAIN"
```

### Verify DNS

```bash
dig "$DOMAIN"
```

Check the CNAME specifically:

```bash
dig "$DOMAIN" CNAME
```

The workflow should establish:

```text
AWS Configuration
       │
       ▼
Distribution Deployed
       │
       ▼
DNS Resolves Correctly
       │
       ▼
TLS Negotiates
       │
       ▼
HTTP Request Succeeds
```

## Distribution Inspection Workflow

Before modifying a distribution, inspect the current configuration.

Retrieve it:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  > cloudfront-config.json
```

Inspect the configuration with `jq`:

```bash
jq '.DistributionConfig' cloudfront-config.json
```

Inspect the ETag:

```bash
jq -r '.ETag' cloudfront-config.json
```

The ETag is important when updating CloudFront configuration because it represents the configuration version being modified.

A production workflow should avoid changing a distribution based on an outdated configuration snapshot.

## Configuration Change Workflow

A safe configuration workflow is:

```mermaid
flowchart TD
    A[Identify Distribution] --> B[Get Current Configuration]
    B --> C[Capture ETag]
    C --> D[Review Configuration]
    D --> E[Modify Configuration]
    E --> F[Validate JSON]
    F --> G[Submit Update]
    G --> H[Wait for Deployment]
    H --> I[Test CloudFront Endpoint]
    I --> J[Verify Metrics]
```

### Retrieve Configuration

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  > cloudfront-config.json
```

### Capture ETag

```bash
ETAG=$(jq -r '.ETag' cloudfront-config.json)

echo "$ETAG"
```

### Extract the Editable Configuration

The `get-distribution-config` response contains the ETag and configuration.

For update operations, work from the distribution configuration rather than blindly modifying the entire API response.

```bash
jq '.DistributionConfig' cloudfront-config.json \
  > distribution-config.json
```

### Validate JSON

```bash
jq empty distribution-config.json
```

If validation succeeds, the command produces no output.

### Update the Distribution

A configuration update requires the current ETag:

```bash
aws cloudfront update-distribution \
  --id "$DISTRIBUTION_ID" \
  --if-match "$ETAG" \
  --distribution-config file://distribution-config.json
```

The exact configuration must match the current CloudFront API schema and required fields.

Do not construct a partial distribution configuration unless the API operation explicitly supports that form.

## Waiting for Distribution Deployment

CloudFront configuration changes are asynchronous.

After an update, inspect status:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.Status' \
  --output text
```

For automation, poll until the distribution is deployed:

```bash
while true; do
  STATUS=$(aws cloudfront get-distribution \
    --id "$DISTRIBUTION_ID" \
    --query 'Distribution.Status' \
    --output text)

  echo "CloudFront status: $STATUS"

  if [ "$STATUS" = "Deployed" ]; then
    break
  fi

  sleep 30
done
```

A bounded polling loop is preferable to waiting indefinitely.

Example with a timeout:

```bash
MAX_ATTEMPTS=40
ATTEMPT=0

while [ "$ATTEMPT" -lt "$MAX_ATTEMPTS" ]; do
  STATUS=$(aws cloudfront get-distribution \
    --id "$DISTRIBUTION_ID" \
    --query 'Distribution.Status' \
    --output text)

  echo "Attempt $((ATTEMPT + 1)): $STATUS"

  if [ "$STATUS" = "Deployed" ]; then
    echo "Distribution deployed."
    exit 0
  fi

  ATTEMPT=$((ATTEMPT + 1))
  sleep 30
done

echo "Timed out waiting for CloudFront deployment."
exit 1
```

## Cache Invalidation Workflow

Invalidation is an operational mechanism for removing cached objects before their normal TTL expires.

A common deployment workflow is:

```text
Deploy Application
       │
       ▼
Publish New Assets
       │
       ▼
Invalidate Required Paths
       │
       ▼
Wait for Completion
       │
       ▼
Request Through CloudFront
       │
       ▼
Verify New Content
```

### Create an Invalidation

Invalidate one object:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/app.js"
```

Invalidate multiple objects:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/app.js" "/app.css" "/index.html"
```

Invalidate a directory:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/static/*"
```

Invalidate everything:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*"
```

Wildcard invalidations should not be the default deployment strategy.

### Capture the Invalidation ID

```bash
INVALIDATION_ID=$(aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/index.html" \
  --query 'Invalidation.Id' \
  --output text)

echo "$INVALIDATION_ID"
```

### Monitor the Invalidation

```bash
aws cloudfront get-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --id "$INVALIDATION_ID" \
  --query 'Invalidation.Status' \
  --output text
```

### Wait for Completion

```bash
aws cloudfront wait invalidation-completed \
  --distribution-id "$DISTRIBUTION_ID" \
  --id "$INVALIDATION_ID"
```

Then verify the content:

```bash
curl -I "https://$DOMAIN/index.html"
```

## Deployment Workflow for Static Assets

A better production pattern is immutable asset naming.

Instead of:

```text
/static/app.js
```

prefer:

```text
/static/app.8f42c1.js
```

A deployment then becomes:

```text
Build
  │
  ▼
Generate hashed assets
  │
  ▼
Upload assets to S3
  │
  ▼
Deploy application
  │
  ▼
Publish new HTML
  │
  ▼
Verify CloudFront
```

The advantage is that old and new assets can coexist safely.

For example:

```text
/static/app.8f42c1.js
/static/app.91ab32.js
```

The HTML references the correct version.

This reduces dependence on invalidations and allows long-lived cache TTLs for immutable assets.

## Origin Troubleshooting Workflow

When CloudFront returns an error, determine whether the origin is responsible.

First inspect the configured origin:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.Origins.Items[].{Id:Id,Domain:DomainName}' \
  --output table
```

Test CloudFront:

```bash
curl -vI "https://$DOMAIN/api/health"
```

Then test the origin independently where the architecture permits:

```bash
curl -vI "https://origin.example.com/api/health"
```

The comparison is:

```text
                 CloudFront
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   CloudFront URL          Origin URL
          │                     │
          ▼                     ▼
      Response              Response
          │                     │
          └──────────┬──────────┘
                     ▼
                 Compare
```

If the origin itself returns `500`, changing CloudFront configuration is unlikely to solve the underlying problem.

## API Origin Troubleshooting

For Django or FastAPI APIs, test an explicit health endpoint:

```bash
curl -fsS \
  -o /dev/null \
  -w '%{http_code}\n' \
  "https://$DOMAIN/api/health"
```

A successful HTTP response:

```text
200
```

can then be correlated with application metrics.

For a JSON health endpoint:

```bash
curl -fsS "https://$DOMAIN/api/health"
```

A more complete test:

```bash
curl -fsS \
  -H "Accept: application/json" \
  "https://$DOMAIN/api/health"
```

For APIs behind CloudFront, also inspect whether query strings, headers, cookies, or authorization information are being handled according to the intended cache and origin-request policies.

## Cache Behavior Troubleshooting Workflow

Inspect the default cache behavior:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.DefaultCacheBehavior.{Origin:TargetOriginId,ViewerProtocolPolicy:ViewerProtocolPolicy,CachePolicy:CachePolicyId,OriginRequestPolicy:OriginRequestPolicyId,ResponseHeadersPolicy:ResponseHeadersPolicyId}' \
  --output table
```

Inspect path-specific behaviors:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.CacheBehaviors.Items[].{Path:PathPattern,Origin:TargetOriginId,CachePolicy:CachePolicyId,OriginRequestPolicy:OriginRequestPolicyId}' \
  --output table
```

This is particularly useful when:

```text
/api/*
```

should route to an API origin while:

```text
/static/*
```

should route to S3.

Incorrect path ordering or behavior configuration can cause requests to reach the wrong origin.

## Cache Performance Workflow

Start by inspecting the configured cache policy:

```bash
CACHE_POLICY_ID=$(aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.DefaultCacheBehavior.CachePolicyId' \
  --output text)

echo "$CACHE_POLICY_ID"
```

Retrieve it:

```bash
aws cloudfront get-cache-policy \
  --id "$CACHE_POLICY_ID" \
  --query 'CachePolicy.CachePolicyConfig.{Name:Name,MinTTL:MinTTL,DefaultTTL:DefaultTTL,MaxTTL:MaxTTL}' \
  --output table
```

Then inspect CloudWatch cache hit rate.

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name CacheHitRate \
  --dimensions Name=DistributionId,Value="$DISTRIBUTION_ID" Name=Region,Value=Global \
  --start-time 2026-08-20T19:00:00Z \
  --end-time 2026-08-20T20:00:00Z \
  --period 300 \
  --statistics Average
```

A low cache hit rate should trigger investigation of:

- Cache key design
- Query strings
- Cookies
- Headers
- TTLs
- Content characteristics
- Recent policy changes

Do not automatically solve a low cache hit rate with a larger cache or more origin capacity. The root cause may be unnecessary cache-key fragmentation.

## 4xx Investigation Workflow

Query the CloudFront 4xx rate:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name 4xxErrorRate \
  --dimensions Name=DistributionId,Value="$DISTRIBUTION_ID" Name=Region,Value=Global \
  --start-time 2026-08-20T19:00:00Z \
  --end-time 2026-08-20T20:00:00Z \
  --period 300 \
  --statistics Average
```

Then test the affected URL:

```bash
curl -vI "https://$DOMAIN/problematic-path"
```

Inspect WAF association:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.WebACLId' \
  --output text
```

Potential causes include:

| Cause | Typical investigation |
|---|---|
| Missing object | Check origin/object existence |
| Wrong path behavior | Inspect cache behaviors |
| Authorization failure | Inspect application and WAF |
| WAF block | Inspect AWS WAF logs/metrics |
| Incorrect origin | Inspect target origin |
| Client error | Inspect request and API response |

## 5xx Investigation Workflow

Start with the metric:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name 5xxErrorRate \
  --dimensions Name=DistributionId,Value="$DISTRIBUTION_ID" Name=Region,Value=Global \
  --start-time 2026-08-20T19:00:00Z \
  --end-time 2026-08-20T20:00:00Z \
  --period 300 \
  --statistics Average
```

Check origin latency:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name OriginLatency \
  --dimensions Name=DistributionId,Value="$DISTRIBUTION_ID" Name=Region,Value=Global \
  --start-time 2026-08-20T19:00:00Z \
  --end-time 2026-08-20T20:00:00Z \
  --period 300 \
  --statistics Average
```

Then test the endpoint:

```bash
curl -vI "https://$DOMAIN/api/health"
```

Follow the dependency chain:

```text
CloudFront 5xx
     │
     ▼
Origin / ALB
     │
     ▼
Nginx / Ingress
     │
     ▼
Django / FastAPI
     │
     ├── PostgreSQL
     ├── Redis
     └── Downstream APIs
```

A senior-level troubleshooting approach correlates all of these signals rather than modifying CloudFront immediately.

## WAF Investigation Workflow

Check the Web ACL association:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.WebACLId' \
  --output text
```

If a Web ACL is associated, retrieve the relevant WAF configuration using AWS WAF commands.

The request flow becomes:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
AWS WAF
  │
  ├── Allow ───────► Cache / Origin
  │
  └── Block
```

When legitimate users suddenly receive errors after a security change, correlate:

- CloudFront response codes
- WAF rule matches
- WAF sampled requests
- Recent rule changes
- Client request characteristics

Do not disable the entire Web ACL as a first response unless the incident requires an emergency containment action and the change is governed appropriately.

## Origin Access Control Troubleshooting

For S3 origins, inspect the configured OAC:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.Origins.Items[].{Origin:Id,Domain:DomainName,OAC:OriginAccessControlId}' \
  --output table
```

Inspect the OAC:

```bash
aws cloudfront get-origin-access-control \
  --id "$OAC_ID"
```

A common failure pattern is:

```text
CloudFront
    │
    │ signed request
    ▼
S3
    │
    └── Bucket policy rejects request
             │
             ▼
          403
```

When this occurs, inspect both:

- CloudFront origin configuration
- S3 bucket policy

Changing only one side may leave the integration broken.

## TLS Troubleshooting Workflow

Inspect the viewer certificate:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.ViewerCertificate' \
  --output json
```

Check the minimum TLS version:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.ViewerCertificate.MinimumProtocolVersion' \
  --output text
```

Test TLS:

```bash
openssl s_client \
  -connect "$DOMAIN:443" \
  -servername "$DOMAIN"
```

Test HTTP behavior:

```bash
curl -vI "https://$DOMAIN"
```

The combination of AWS configuration inspection and client-side TLS testing is much more reliable than inspecting only the certificate in the AWS Console.

## Distribution Deployment Workflow in CI/CD

A deployment pipeline can use CloudFront CLI operations as verification gates.

Conceptually:

```mermaid
flowchart LR
    A[Build] --> B[Deploy Application]
    B --> C[Update CloudFront if required]
    C --> D[Wait for Deployed]
    D --> E[Invalidate Required Paths]
    E --> F[Wait for Invalidation]
    F --> G[HTTP Smoke Test]
    G --> H[Verify Metrics]
```

Example shell workflow:

```bash
#!/usr/bin/env bash

set -euo pipefail

DISTRIBUTION_ID="${DISTRIBUTION_ID:?DISTRIBUTION_ID is required}"
DOMAIN="${DOMAIN:?DOMAIN is required}"

echo "Waiting for CloudFront deployment..."

for _ in {1..40}; do
  STATUS=$(aws cloudfront get-distribution \
    --id "$DISTRIBUTION_ID" \
    --query 'Distribution.Status' \
    --output text)

  echo "Distribution status: $STATUS"

  if [[ "$STATUS" == "Deployed" ]]; then
    break
  fi

  sleep 30
done

STATUS=$(aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.Status' \
  --output text)

if [[ "$STATUS" != "Deployed" ]]; then
  echo "CloudFront deployment did not complete."
  exit 1
fi

echo "CloudFront deployment completed."

INVALIDATION_ID=$(aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/index.html" \
  --query 'Invalidation.Id' \
  --output text)

echo "Created invalidation: $INVALIDATION_ID"

aws cloudfront wait invalidation-completed \
  --distribution-id "$DISTRIBUTION_ID" \
  --id "$INVALIDATION_ID"

echo "Invalidation completed."

HTTP_STATUS=$(curl -sS \
  -o /dev/null \
  -w '%{http_code}' \
  "https://$DOMAIN/index.html")

if [[ "$HTTP_STATUS" != "200" ]]; then
  echo "Smoke test failed with HTTP $HTTP_STATUS."
  exit 1
fi

echo "CloudFront smoke test passed."
```

For a production pipeline, add:

- Explicit AWS credentials through the CI platform's identity mechanism
- Timeouts
- Structured logging
- Deployment identifiers
- Environment validation
- Rollback handling
- Alerting
- Least-privilege IAM permissions

## Post-Deployment Verification

After a CloudFront-related deployment, verify at multiple layers.

### Configuration

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.{Status:Status,Enabled:DistributionConfig.Enabled}' \
  --output table
```

### HTTP

```bash
curl -fsSI "https://$DOMAIN/"
```

### API

```bash
curl -fsS \
  -H "Accept: application/json" \
  "https://$DOMAIN/api/health"
```

### Cache Headers

```bash
curl -sSI "https://$DOMAIN/static/app.js"
```

### Metrics

Check:

- Requests
- 4xx error rate
- 5xx error rate
- Cache hit rate
- Origin latency

A deployment should not be considered successful solely because the CloudFront distribution reaches `Deployed`.

## Rollback Workflow

CloudFront configuration rollback should be treated differently from application rollback.

First capture the current configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  > cloudfront-before-change.json
```

Before applying a change, preserve the previous known-good configuration.

A rollback pattern is:

```text
Current Production
       │
       ▼
Known-Good Configuration
       │
       ▼
Apply Change
       │
       ▼
Verify
       │
   ┌───┴───┐
   │       │
 Healthy  Failure
   │       │
   ▼       ▼
 Keep    Restore
         Previous
         Config
```

Do not attempt an emergency rollback from memory.

Use the previously captured, reviewed configuration whenever possible.

## Safe Rollback Considerations

When restoring configuration:

- Verify the configuration belongs to the correct distribution.
- Verify the AWS account.
- Preserve required fields.
- Use the current ETag.
- Review security settings before applying.
- Confirm origin configuration.
- Confirm certificates.
- Confirm WAF association.
- Wait for deployment.
- Run post-rollback smoke tests.

An application rollback may require:

```text
Docker image rollback
Kubernetes deployment rollback
Django application rollback
```

while a CloudFront rollback may require:

```text
Distribution configuration rollback
Cache behavior rollback
Origin rollback
Policy association rollback
```

These should be coordinated when the incident involves both infrastructure and application changes.

## Emergency Disable Workflow

Disabling a distribution is a high-impact operation and should not be used as a routine troubleshooting technique.

The configuration workflow is:

```text
Get Current Config
       │
       ▼
Set Enabled = false
       │
       ▼
Validate Configuration
       │
       ▼
Update Distribution
       │
       ▼
Wait for Deployment
       │
       ▼
Verify Result
```

Because this changes public traffic behavior, it should require explicit operational approval in production.

## Security-Aware CLI Workflows

Do not place long-lived AWS access keys directly into shell scripts:

```bash
# Avoid
AWS_ACCESS_KEY_ID="..."
AWS_SECRET_ACCESS_KEY="..."
```

Prefer short-lived credentials through:

- IAM roles
- CI/CD workload identity
- AWS IAM Identity Center
- Instance roles
- Container/task roles

Check the current identity before destructive operations:

```bash
aws sts get-caller-identity
```

This simple command can prevent a production change from being executed against the wrong AWS account.

Use explicit profiles where appropriate:

```bash
aws cloudfront get-distribution \
  --profile production \
  --id "$DISTRIBUTION_ID"
```

## Production Automation Principles

### Make Scripts Fail Fast

Use:

```bash
set -euo pipefail
```

This reduces the chance that a failed AWS command is silently ignored.

### Validate Required Variables

```bash
: "${DISTRIBUTION_ID:?DISTRIBUTION_ID is required}"
: "${AWS_PROFILE:?AWS_PROFILE is required}"
```

### Avoid Unbounded Loops

Do not use:

```bash
while true; do
  ...
done
```

for deployment automation without a timeout.

Prefer bounded retries:

```bash
for attempt in {1..40}; do
  ...
done
```

### Verify Before Destructive Operations

Before creating an invalidation or modifying a distribution:

```bash
aws sts get-caller-identity
```

Then:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID"
```

This adds a low-cost verification step before a high-impact action.

## Common Operational Mistakes

### Changing Configuration Without Capturing the Current State

A common failure pattern is:

```text
Modify
  ↓
Deploy
  ↓
Problem
  ↓
"What was the previous configuration?"
```

Avoid this by capturing the configuration before modification.

### Assuming CLI Commands Are Atomic

CloudFront changes are asynchronous. A successful `update-distribution` API response does not mean all edge locations have immediately switched to the new configuration.

Always verify deployment state.

### Sleeping for an Arbitrary Duration

Avoid:

```bash
sleep 300
```

and assuming the change is complete.

Use status inspection or AWS waiters where supported.

### Invalidating Everything for Every Deployment

Avoid treating:

```bash
--paths "/*"
```

as a default deployment operation.

Prefer versioned assets and targeted invalidation.

### Updating a Stale Configuration

CloudFront configuration changes use version information through ETags.

Always obtain a current configuration before making a change.

### Running Production Commands Against the Wrong Account

Always verify:

```bash
aws sts get-caller-identity
```

before high-impact operations.

### Treating CloudFront as the Entire Application

CloudFront is one layer in the architecture.

A production incident can involve:

```text
DNS
 ↓
CloudFront
 ↓
WAF
 ↓
ALB
 ↓
Nginx / Ingress
 ↓
Django / FastAPI
 ↓
Redis / PostgreSQL / Kafka / External APIs
```

Troubleshooting must follow the complete request path.

## Operational Command Matrix

| Workflow | Primary command | Verification |
|---|---|---|
| Check identity | `aws sts get-caller-identity` | Confirm account and principal |
| Inspect distribution | `aws cloudfront get-distribution` | Configuration and status |
| Capture configuration | `aws cloudfront get-distribution-config` | Save JSON and ETag |
| Update distribution | `aws cloudfront update-distribution` | Wait for `Deployed` |
| Create invalidation | `aws cloudfront create-invalidation` | Wait for completion |
| Inspect invalidation | `aws cloudfront get-invalidation` | Check status |
| Test endpoint | `curl -I` | HTTP status and headers |
| Test TLS | `openssl s_client` | Certificate and handshake |
| Test DNS | `dig` | Expected DNS record |
| Inspect WAF association | `get-distribution` | Web ACL ID |
| Inspect cache policy | `get-cache-policy` | TTL and cache-key configuration |
| Inspect origin | `get-distribution` | Origin target and settings |
| Inspect metrics | `cloudwatch get-metric-statistics` | Error, cache, and latency trends |

## Incident Response Workflow

A practical CloudFront incident workflow can be reduced to:

```mermaid
flowchart TD
    A[Incident Detected] --> B[Verify AWS Account]
    B --> C[Check Distribution Status]
    C --> D[Test DNS]
    D --> E[Test TLS]
    E --> F[Test CloudFront HTTP Response]
    F --> G[Inspect WAF]
    G --> H[Inspect Cache Behavior]
    H --> I[Inspect CloudWatch Metrics]
    I --> J[Test Origin]
    J --> K[Inspect Application Dependencies]
    K --> L{Root Cause Identified?}
    L -->|Yes| M[Apply Minimal Change]
    L -->|No| N[Continue Cross-Layer Investigation]
    M --> O[Wait for Deployment]
    O --> P[Smoke Test]
    P --> Q[Monitor Metrics]
```

The emphasis should be on **minimal change**. Avoid modifying several CloudFront settings simultaneously because that destroys causal information and makes rollback more difficult.

## Production Best Practices

- Use explicit AWS profiles or workload identities.
- Verify AWS account identity before production changes.
- Capture current configuration before modifying distributions.
- Treat CloudFront changes as asynchronous operations.
- Wait for deployment completion.
- Use targeted invalidations when necessary.
- Prefer immutable asset versioning for static content.
- Use CloudWatch metrics for persistent monitoring.
- Use `curl` to verify real client behavior.
- Correlate CloudFront metrics with origin and application metrics.
- Use least-privilege IAM permissions.
- Keep operational scripts version-controlled.
- Add timeouts to automation.
- Log distribution IDs, deployment identifiers, and timestamps.
- Review security-sensitive changes before deployment.
- Preserve known-good configurations for rollback.

## Interview Perspective

### How would you safely change a CloudFront distribution from the CLI?

A production-oriented answer is:

1. Verify the AWS account and identity.
2. Retrieve the current distribution configuration.
3. Capture the current ETag.
4. Review and modify the configuration.
5. Validate the resulting configuration.
6. Submit the update using the current ETag.
7. Wait until the distribution is deployed.
8. Run HTTP smoke tests.
9. Monitor CloudWatch metrics.
10. Roll back using a known-good configuration if verification fails.

### How would you deploy static assets without relying heavily on invalidation?

Use content-addressed or versioned filenames:

```text
app.8f42c1.js
app.91ab32.js
```

Then configure long cache lifetimes for immutable assets and update the HTML reference to the new version.

This provides better cache efficiency and reduces operational dependence on invalidation.

### What would you check if CloudFront is returning 5xx?

Check:

```text
Distribution Status
       ↓
CloudFront HTTP Response
       ↓
CloudFront 5xx Rate
       ↓
Origin Latency
       ↓
ALB / Origin
       ↓
Nginx / Ingress
       ↓
Application
       ↓
Dependencies
```

The goal is to identify which layer introduced the failure rather than assuming CloudFront itself is broken.

### Why is ETag important?

CloudFront uses the ETag returned with the current distribution configuration to prevent an update from unintentionally overwriting a newer configuration version.

The workflow is effectively optimistic concurrency control:

```text
Read Version
    ↓
Modify
    ↓
Write If Version Still Matches
```

## Key Takeaways

- **Treat CloudFront operations as workflows, not isolated commands:** inspect the current state, make the smallest necessary change, wait for asynchronous deployment, and verify real client behavior.
- **Protect production changes with explicit verification:** confirm the AWS account, distribution ID, current configuration, and ETag before modifying a distribution.
- **Use targeted cache invalidation and immutable assets:** invalidation is useful for urgent cache changes, while versioned assets provide a more scalable deployment model.
- **Troubleshoot across the entire request path:** CloudFront, WAF, ALB, Nginx, Django/FastAPI, Redis, PostgreSQL, and downstream services can all contribute to an observed edge failure.
- **Automate verification, not just deployment:** production workflows should wait for deployment, execute smoke tests, inspect metrics, enforce timeouts, and preserve known-good state for rollback.