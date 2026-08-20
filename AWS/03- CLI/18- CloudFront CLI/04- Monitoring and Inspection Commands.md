# 04- Monitoring and Inspection Commands

## Overview

CloudFront monitoring and inspection are operational activities used to verify distribution configuration, deployment state, cache behavior, origin connectivity, security configuration, and runtime performance.

For production systems, the AWS CLI is especially useful because it provides deterministic access to CloudFront configuration and can be incorporated into deployment pipelines, incident-response scripts, health checks, and operational tooling.

A useful mental model is to inspect CloudFront from the edge toward the backend:

```text
Client
  │
  ▼
DNS
  │
  ▼
CloudFront Distribution
  │
  ├── TLS
  ├── WAF
  ├── Cache Behavior
  ├── Cache Policy
  ├── Origin Request Policy
  └── Response Headers Policy
          │
          ▼
        Origin
          │
          ├── S3
          ├── ALB
          ├── API Gateway
          └── Custom HTTP Origin
                  │
                  ▼
             Application
                  │
             ┌────┴────┐
             ▼         ▼
        PostgreSQL    Redis
```

The objective is not simply to determine whether CloudFront is "up". The important operational questions are:

- Is the distribution deployed?
- Is it enabled?
- Which origins are configured?
- Which cache behaviors are active?
- Which policies are attached?
- Is HTTPS configured correctly?
- Is WAF associated?
- Are invalidations running or failing?
- Is traffic being served from cache?
- Is CloudFront reaching the origin?
- Is the origin responding slowly or with errors?
- Did a recent configuration or application deployment cause the problem?

## AWS CLI Prerequisites

Verify the AWS CLI:

```bash
aws --version
```

Verify the current AWS identity:

```bash
aws sts get-caller-identity
```

This is particularly important when working across multiple AWS accounts.

Check the configured profile:

```bash
aws configure list
```

Use a specific profile when required:

```bash
aws cloudfront list-distributions \
  --profile production
```

CloudFront is a global service. CloudFront API operations should not be treated like regional operations for services such as EC2 or RDS.

## List CloudFront Distributions

List all distributions:

```bash
aws cloudfront list-distributions
```

For operational inspection, reduce the response to useful fields:

```bash
aws cloudfront list-distributions \
  --query 'DistributionList.Items[].{Id:Id,Domain:DomainName,Status:Status,Enabled:Enabled}' \
  --output table
```

Example:

```text
---------------------------------------------------------------
|                     ListDistributions                      |
+------------------+--------------------------+-------+------+
| Id               | Domain                   |Status |Enabled|
+------------------+--------------------------+-------+------+
| E123456789ABC    | d123example.cloudfront.net |Deployed|True|
+------------------+--------------------------+-------+------+
```

Useful fields include:

| Field | Purpose |
|---|---|
| `Id` | Identifies the CloudFront distribution |
| `DomainName` | CloudFront-provided hostname |
| `Status` | Distribution configuration deployment state |
| `Enabled` | Whether the distribution is enabled |
| `ARN` | Resource identifier used by IAM and other integrations |

## Inspect a Distribution

Retrieve a distribution:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC
```

The response contains:

- Distribution metadata
- Distribution configuration
- Origins
- Cache behaviors
- Viewer certificate
- Logging configuration
- Web ACL association
- Price class
- HTTP version
- IPv6 configuration
- Other distribution-level settings

For production troubleshooting, use `--query` to extract only the relevant fields.

## Check Distribution Status

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.Status' \
  --output text
```

Typical result:

```text
Deployed
```

A distribution can temporarily be in a non-deployed state after a configuration change while CloudFront propagates the new configuration.

Check status and enabled state together:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.{Status:Status,Enabled:DistributionConfig.Enabled}' \
  --output table
```

### Important Distinction

`Deployed` does not mean that the application is healthy.

It only indicates that the CloudFront distribution configuration has been deployed.

For example:

```text
CloudFront Status = Deployed
        │
        ├── Origin could still be returning 500
        ├── ALB could still be unhealthy
        ├── Django could still be failing
        ├── PostgreSQL could still be unavailable
        └── WAF could still be blocking legitimate traffic
```

## Inspect the Distribution Domain

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DomainName' \
  --output text
```

Test the endpoint:

```bash
curl -I https://d123example.cloudfront.net
```

For a custom domain:

```bash
curl -I https://cdn.example.com
```

## Inspect Distribution ARN

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.ARN' \
  --output text
```

The ARN is useful when working with:

- IAM
- Resource policies
- WAF
- Automation
- Infrastructure-as-code
- Resource tagging

## Inspect Origins

Origins determine where CloudFront retrieves content when it cannot satisfy a request from its cache.

List origins:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.Origins.Items[].{Id:Id,Domain:DomainName}' \
  --output table
```

For a more detailed inspection:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.Origins.Items[]' \
  --output json
```

Important origin attributes include:

- Origin ID
- Origin domain
- Origin path
- Origin protocol policy
- Connection attempts
- Connection timeout
- Origin Shield configuration
- Origin Access Control association

## Inspect Origin Access Control

When CloudFront accesses private S3 content, Origin Access Control is a common security mechanism.

Inspect the origin configuration:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.Origins.Items[].{Id:Id,Domain:DomainName,OAC:OriginAccessControlId}' \
  --output table
```

Inspect the OAC directly:

```bash
aws cloudfront get-origin-access-control \
  --id OAC_ID
```

This is useful when investigating:

- S3 `403` responses
- CloudFront-to-S3 authentication problems
- Bucket policy changes
- Migration from legacy Origin Access Identity

## Inspect Cache Behaviors

Inspect the default cache behavior:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.DefaultCacheBehavior' \
  --output json
```

Extract the important fields:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.DefaultCacheBehavior.{Origin:TargetOriginId,ViewerProtocolPolicy:ViewerProtocolPolicy,CachePolicy:CachePolicyId,OriginRequestPolicy:OriginRequestPolicyId,ResponseHeadersPolicy:ResponseHeadersPolicyId}' \
  --output table
```

Inspect additional path-based behaviors:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.CacheBehaviors.Items[].{Path:PathPattern,Origin:TargetOriginId,ViewerProtocolPolicy:ViewerProtocolPolicy,CachePolicy:CachePolicyId,OriginRequestPolicy:OriginRequestPolicyId}' \
  --output table
```

Typical application routing might contain:

```text
/api/*
/static/*
/media/*
/images/*
```

This inspection is valuable when a request appears to be reaching the wrong origin.

## Inspect Cache Policy

Retrieve a cache policy:

```bash
aws cloudfront get-cache-policy \
  --id CACHE_POLICY_ID
```

Extract TTL values:

```bash
aws cloudfront get-cache-policy \
  --id CACHE_POLICY_ID \
  --query 'CachePolicy.CachePolicyConfig.{Name:Name,MinTTL:MinTTL,DefaultTTL:DefaultTTL,MaxTTL:MaxTTL}' \
  --output table
```

Inspect the complete policy:

```bash
aws cloudfront get-cache-policy \
  --id CACHE_POLICY_ID \
  --output json
```

Cache policy inspection is important when investigating:

- Low cache hit rates
- Unexpected cache misses
- Stale content
- Query-string variation
- Cookie variation
- Header variation

## List Cache Policies

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

Produce a compact table:

```bash
aws cloudfront list-cache-policies \
  --type custom \
  --query 'CachePolicyList.Items[].{Id:Id,Name:CachePolicy.CachePolicyConfig.Name}' \
  --output table
```

## Inspect Origin Request Policy

Retrieve an origin request policy:

```bash
aws cloudfront get-origin-request-policy \
  --id ORIGIN_REQUEST_POLICY_ID
```

Extract its name:

```bash
aws cloudfront get-origin-request-policy \
  --id ORIGIN_REQUEST_POLICY_ID \
  --query 'OriginRequestPolicy.OriginRequestPolicyConfig.Name' \
  --output text
```

The distinction between cache policy and origin request policy is important:

```text
Cache Policy
    │
    └── Controls what differentiates cached objects

Origin Request Policy
    │
    └── Controls what information CloudFront sends to the origin
```

A request attribute can be forwarded to the origin without necessarily becoming part of the cache key.

## Inspect Response Headers Policy

List response headers policies:

```bash
aws cloudfront list-response-headers-policies
```

Inspect a specific policy:

```bash
aws cloudfront get-response-headers-policy \
  --id RESPONSE_HEADERS_POLICY_ID
```

This is useful when validating:

- CORS headers
- Security headers
- Custom response headers

## Inspect TLS Configuration

Retrieve the viewer certificate configuration:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.ViewerCertificate' \
  --output json
```

Inspect the ACM certificate:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.ViewerCertificate.ACMCertificateArn' \
  --output text
```

Inspect the minimum TLS protocol:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.ViewerCertificate.MinimumProtocolVersion' \
  --output text
```

TLS inspection is useful for diagnosing:

- Certificate errors
- Incorrect custom domains
- Unsupported TLS clients
- Unexpected protocol behavior
- Security-policy violations

## Inspect Viewer Protocol Policy

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.DefaultCacheBehavior.ViewerProtocolPolicy' \
  --output text
```

Common values include:

```text
allow-all
redirect-to-https
https-only
```

For public web applications, `redirect-to-https` or `https-only` is normally preferable to allowing plaintext HTTP.

## Inspect WAF Association

Check whether the distribution has an associated Web ACL:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.WebACLId' \
  --output text
```

If a Web ACL is associated, inspect it separately using AWS WAF commands.

A CloudFront request failure can originate from WAF filtering rather than the application.

## Inspect Logging Configuration

Inspect distribution logging:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.Logging' \
  --output json
```

For relevant fields:

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.Logging.{Enabled:Enabled,Bucket:Bucket,Prefix:Prefix,IncludeCookies:IncludeCookies}' \
  --output table
```

Logging should be evaluated against:

- Security requirements
- Privacy requirements
- Retention policies
- S3 lifecycle policies
- Storage costs
- Access control

## Inspect IPv6 Configuration

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.IsIPV6Enabled' \
  --output text
```

For public applications, IPv6 support is generally desirable unless there is a specific compatibility or architectural requirement not to use it.

## Inspect HTTP Version

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.HttpVersion' \
  --output text
```

The viewer-side protocol and origin-side protocol are separate concerns.

For example:

```text
Browser
   │
   │ HTTP/2 or HTTP/3
   ▼
CloudFront
   │
   │ HTTPS
   ▼
ALB
   │
   ▼
Django / FastAPI
```

Do not assume the protocol negotiated with the viewer is identical to the protocol used toward the origin.

## Inspect Price Class

```bash
aws cloudfront get-distribution \
  --id E123456789ABC \
  --query 'Distribution.DistributionConfig.PriceClass' \
  --output text
```

Price class affects the geographic set of edge locations used for content delivery and therefore has both cost and latency implications.

## Inspect Distribution Tags

Retrieve distribution tags:

```bash
aws cloudfront list-tags-for-resource \
  --resource arn:aws:cloudfront::123456789012:distribution/E123456789ABC
```

Useful tags include:

```text
Environment = production
Application = customer-api
Owner       = platform
ManagedBy   = terraform
```

Tags improve:

- Resource inventory
- Ownership
- Cost allocation
- Automation
- Incident response

## Inspect Invalidations

List invalidations:

```bash
aws cloudfront list-invalidations \
  --distribution-id E123456789ABC
```

Use a compact table:

```bash
aws cloudfront list-invalidations \
  --distribution-id E123456789ABC \
  --query 'InvalidationList.Items[].{Id:Id,Status:Status,Created:CreateTime}' \
  --output table
```

Inspect a specific invalidation:

```bash
aws cloudfront get-invalidation \
  --distribution-id E123456789ABC \
  --id INVALIDATION_ID
```

Check only its status:

```bash
aws cloudfront get-invalidation \
  --distribution-id E123456789ABC \
  --id INVALIDATION_ID \
  --query 'Invalidation.Status' \
  --output text
```

Wait for completion:

```bash
aws cloudfront wait invalidation-completed \
  --distribution-id E123456789ABC \
  --id INVALIDATION_ID
```

Using a waiter is preferable to implementing an arbitrary sleep in CI/CD.

## Inspect Distribution Configuration

Retrieve the current distribution configuration:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  > cloudfront-config.json
```

Inspect it with `jq`:

```bash
jq '.DistributionConfig' cloudfront-config.json
```

Inspect the default cache behavior:

```bash
jq '.DistributionConfig.DefaultCacheBehavior' cloudfront-config.json
```

Inspect origins:

```bash
jq '.DistributionConfig.Origins.Items' cloudfront-config.json
```

This is useful for:

- Configuration audits
- Incident response
- Change reviews
- Troubleshooting
- Building automation

## Inspect the Distribution ETag

CloudFront configuration updates use an ETag for optimistic concurrency.

Retrieve it:

```bash
aws cloudfront get-distribution-config \
  --id E123456789ABC \
  --query 'ETag' \
  --output text
```

The ETag represents the configuration version returned by CloudFront.

The operational pattern is:

```text
Get current configuration
          │
          ▼
      Receive ETag
          │
          ▼
    Modify configuration
          │
          ▼
Submit update with ETag
          │
          ▼
CloudFront validates version
```

This prevents an update based on an obsolete configuration version from silently overwriting a newer change.

## CloudWatch Metrics

CloudFront integrates with Amazon CloudWatch for operational metrics.

List CloudFront metrics:

```bash
aws cloudwatch list-metrics \
  --namespace AWS/CloudFront
```

Filter by distribution:

```bash
aws cloudwatch list-metrics \
  --namespace AWS/CloudFront \
  --dimensions Name=DistributionId,Value=E123456789ABC
```

Common CloudFront metrics include:

| Metric | Operational purpose |
|---|---|
| `Requests` | Request volume |
| `BytesDownloaded` | Download traffic |
| `BytesUploaded` | Upload traffic |
| `4xxErrorRate` | Client-side error rate |
| `5xxErrorRate` | Server-side error rate |
| `TotalErrorRate` | Combined error rate |
| `CacheHitRate` | Cache effectiveness |
| `OriginLatency` | Origin response latency |

Metric availability and dimensions should be verified against the current CloudFront/CloudWatch configuration before embedding them into automation.

## Query Cache Hit Rate

Example CloudWatch query:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name CacheHitRate \
  --dimensions Name=DistributionId,Value=E123456789ABC Name=Region,Value=Global \
  --start-time 2026-08-20T00:00:00Z \
  --end-time 2026-08-20T01:00:00Z \
  --period 300 \
  --statistics Average
```

A declining cache hit rate can indicate:

- Cache-key fragmentation
- Excessive query-string variation
- Cookies included in cache keys
- Headers included unnecessarily
- Short TTLs
- Content that is inherently difficult to cache

## Query 4xx Errors

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name 4xxErrorRate \
  --dimensions Name=DistributionId,Value=E123456789ABC Name=Region,Value=Global \
  --start-time 2026-08-20T00:00:00Z \
  --end-time 2026-08-20T01:00:00Z \
  --period 300 \
  --statistics Average
```

A 4xx increase can indicate:

- Invalid URLs
- Incorrect routing
- Missing objects
- Authorization failures
- WAF filtering
- Application-level client errors

Do not automatically classify all 4xx responses as CloudFront failures.

## Query 5xx Errors

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name 5xxErrorRate \
  --dimensions Name=DistributionId,Value=E123456789ABC Name=Region,Value=Global \
  --start-time 2026-08-20T00:00:00Z \
  --end-time 2026-08-20T01:00:00Z \
  --period 300 \
  --statistics Average
```

A CloudFront 5xx spike should normally trigger investigation of the complete request path:

```text
CloudFront
    │
    ▼
ALB / Origin
    │
    ▼
Nginx
    │
    ▼
Django / FastAPI
    │
    ├── PostgreSQL
    ├── Redis
    └── Downstream APIs
```

## Query Origin Latency

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name OriginLatency \
  --dimensions Name=DistributionId,Value=E123456789ABC Name=Region,Value=Global \
  --start-time 2026-08-20T00:00:00Z \
  --end-time 2026-08-20T01:00:00Z \
  --period 300 \
  --statistics Average
```

High origin latency can be caused by:

- Slow Django or FastAPI handlers
- Database contention
- Redis latency
- Downstream API latency
- ALB saturation
- Container resource exhaustion
- Kubernetes scheduling pressure
- Connection pool exhaustion

CloudFront is often the first visible layer of a deeper backend problem.

## Query Request Volume

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name Requests \
  --dimensions Name=DistributionId,Value=E123456789ABC Name=Region,Value=Global \
  --start-time 2026-08-20T00:00:00Z \
  --end-time 2026-08-20T01:00:00Z \
  --period 300 \
  --statistics Sum
```

Traffic should be correlated with:

- ALB requests
- Application requests
- PostgreSQL connections
- Redis operations
- Kafka throughput
- Kubernetes CPU and memory utilization

## Inspect HTTP Responses with `curl`

The AWS CLI is best for AWS-side configuration. `curl` is better for verifying what a real client receives.

Basic inspection:

```bash
curl -I https://cdn.example.com/app.js
```

Verbose inspection:

```bash
curl -vI https://cdn.example.com/app.js
```

Follow redirects:

```bash
curl -IL https://cdn.example.com/app.js
```

Inspect headers without downloading the response body:

```bash
curl -sSI https://cdn.example.com/app.js
```

Useful response information includes:

- HTTP status
- `Age`
- `Cache-Control`
- `ETag`
- `Last-Modified`
- `Content-Type`
- Security headers
- CORS headers
- CloudFront response headers

## Compare CloudFront and Origin

When investigating stale or unexpected content, compare both paths:

```bash
curl -I https://cdn.example.com/app.js
curl -I https://origin.example.com/app.js
```

Conceptually:

```text
Origin Response
      │
      ├── Status
      ├── ETag
      ├── Last-Modified
      └── Cache-Control
      │
      ▼
CloudFront
      │
      ├── Cache Policy
      ├── Cache Key
      └── Cached Object
      │
      ▼
Viewer Response
```

This helps distinguish an origin problem from a CloudFront caching problem.

## Inspect DNS

DNS problems can look like CloudFront problems.

Use:

```bash
dig cdn.example.com
```

Or:

```bash
nslookup cdn.example.com
```

For more detail:

```bash
dig cdn.example.com CNAME
```

Verify that the custom hostname resolves through the expected CloudFront configuration.

For HTTPS troubleshooting:

```bash
curl -vI https://cdn.example.com
```

This can expose hostname and certificate-related problems that a simple AWS CLI configuration query will not.

## Inspect TLS with OpenSSL

For lower-level TLS inspection:

```bash
openssl s_client \
  -connect cdn.example.com:443 \
  -servername cdn.example.com
```

This is useful for investigating:

- Certificate chains
- Server certificate selection
- TLS handshake failures
- SNI behavior
- Protocol negotiation

For production troubleshooting, use `-servername` because modern TLS deployments depend on SNI.

## Production Troubleshooting Flow

A reliable troubleshooting process should move from the client-facing edge toward the origin:

```mermaid
flowchart TD
    A[Client reports failure] --> B[Check DNS]
    B --> C[Check TLS]
    C --> D[Inspect HTTP response]
    D --> E[Check distribution status]
    E --> F[Inspect cache behavior]
    F --> G[Inspect cache and origin request policies]
    G --> H[Check WAF]
    H --> I[Check CloudWatch metrics]
    I --> J[Check origin]
    J --> K[Check application]
    K --> L[Check database and dependencies]
```

This prevents an engineer from immediately assuming that the backend application is responsible.

## Production Monitoring Architecture

CLI inspection should complement persistent observability:

```text
                     CloudFront
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
      CloudWatch       Logs            WAF
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  Observability
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Dashboards       Alerts      Incident Response
```

The CLI is particularly valuable for:

- Incident response
- Deployment verification
- Configuration audits
- Ad-hoc inspection
- CI/CD validation
- Operational scripts

It should not be the only production monitoring mechanism.

## Recommended Production Signals

At minimum, monitor:

| Signal | Why it matters |
|---|---|
| Request count | Detect traffic changes and unexpected load |
| 4xx error rate | Detect routing, authorization, WAF, and client problems |
| 5xx error rate | Detect origin and infrastructure failures |
| Cache hit rate | Measure caching effectiveness |
| Origin latency | Detect backend performance degradation |
| Bytes downloaded | Understand traffic and cost drivers |
| Distribution deployment status | Detect incomplete configuration changes |
| WAF activity | Detect malicious or unexpectedly blocked requests |
| Origin health | Separate CDN failures from backend failures |

## Common Inspection Patterns

### Distribution Health

```bash
DISTRIBUTION_ID="E123456789ABC"

aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.{Id:Id,Domain:DomainName,Status:Status,Enabled:DistributionConfig.Enabled}' \
  --output table
```

### Origins

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.Origins.Items[].{Id:Id,Domain:DomainName}' \
  --output table
```

### Cache Behaviors

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.CacheBehaviors.Items[].{Path:PathPattern,Origin:TargetOriginId,CachePolicy:CachePolicyId,OriginRequestPolicy:OriginRequestPolicyId}' \
  --output table
```

### TLS

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.ViewerCertificate.{Certificate:ACMCertificateArn,MinimumTLS:MinimumProtocolVersion}' \
  --output table
```

### WAF

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.WebACLId' \
  --output text
```

### Invalidations

```bash
aws cloudfront list-invalidations \
  --distribution-id "$DISTRIBUTION_ID" \
  --query 'InvalidationList.Items[].{Id:Id,Status:Status,Created:CreateTime}' \
  --output table
```

## Useful `jq` Inspection

For large CloudFront configurations, `jq` makes local inspection much easier.

Extract origins:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" |
jq '.DistributionConfig.Origins.Items[]'
```

Extract the default cache behavior:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" |
jq '.DistributionConfig.DefaultCacheBehavior'
```

Extract path-based behaviors:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" |
jq '.DistributionConfig.CacheBehaviors.Items[]'
```

Extract TLS configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" |
jq '.DistributionConfig.ViewerCertificate'
```

This is often more practical than reading the complete JSON response manually.

## Operational Troubleshooting Examples

### High 5xx Rate

Start with:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.Status' \
  --output text
```

Then inspect:

```bash
curl -vI https://cdn.example.com/api/health
```

Then inspect origin latency and error metrics.

If CloudFront is deployed but origin latency and 5xx errors increased simultaneously, investigate the origin infrastructure and application rather than repeatedly changing CloudFront configuration.

### Low Cache Hit Rate

Inspect:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.DefaultCacheBehavior.{CachePolicy:CachePolicyId,OriginRequestPolicy:OriginRequestPolicyId}' \
  --output table
```

Then inspect the cache policy:

```bash
aws cloudfront get-cache-policy \
  --id "$CACHE_POLICY_ID"
```

Look for unnecessary variation caused by:

- Cookies
- Query strings
- Headers

The correct response is usually to improve cache-key design, not to repeatedly invalidate the distribution.

### Stale Content

Compare origin and CloudFront:

```bash
curl -I https://origin.example.com/app.js
curl -I https://cdn.example.com/app.js
```

Inspect cache headers:

```bash
curl -sSI https://cdn.example.com/app.js
```

Then inspect invalidations:

```bash
aws cloudfront list-invalidations \
  --distribution-id "$DISTRIBUTION_ID" \
  --output table
```

The long-term fix should normally be correct cache-control and asset versioning rather than frequent wildcard invalidations.

## Common Mistakes

### Assuming `Deployed` Means the Application Is Healthy

A deployed distribution can still route requests to an unhealthy origin.

Always separate:

```text
Configuration state
        ≠
Runtime health
```

### Inspecting Only the Console

The console is useful for visual inspection, but CLI commands are easier to:

- Reproduce
- Automate
- Script
- Capture during incidents
- Integrate with CI/CD

### Treating All 5xx Responses as CloudFront Failures

A 5xx response can originate from:

- CloudFront
- ALB
- Nginx
- Django
- FastAPI
- PostgreSQL-dependent application code
- Downstream services

Trace the complete request path.

### Ignoring Cache Hit Rate

A low cache hit rate increases origin traffic and can expose backend bottlenecks that were previously hidden by cached responses.

### Using Wildcard Invalidations as a Normal Deployment Strategy

Frequent `/*` invalidations can increase operational overhead and undermine the benefits of caching.

Prefer immutable, versioned assets where practical:

```text
/app.8f42c1.js
/app.a17b91.css
```

Then a new deployment can publish a new asset rather than forcing every edge location to discard the previous object.

### Confusing Cache Policy with Origin Request Policy

These solve different problems.

A cache policy determines how requests map to cached objects.

An origin request policy determines which request information is forwarded to the origin.

### Ignoring WAF

A legitimate request blocked by WAF can look like an application authorization problem.

When appropriate, correlate CloudFront behavior with WAF activity.

## Interview Traps

### Is CloudFront a monitoring service?

No. CloudFront is a content delivery service that exposes operational metrics and integrates with CloudWatch.

### Does `Deployed` mean the origin is healthy?

No. It means the distribution configuration has been deployed.

### How would you investigate a CloudFront 5xx spike?

A practical sequence is:

1. Verify distribution deployment status.
2. Test the endpoint directly with `curl`.
3. Inspect CloudFront 5xx and origin-latency metrics.
4. Check the origin such as ALB, Nginx, or Kubernetes ingress.
5. Check Django or FastAPI application health.
6. Check PostgreSQL, Redis, and downstream dependencies.
7. Check WAF activity.
8. Correlate the incident with recent deployments or configuration changes.

### How would you investigate stale content?

Inspect:

```text
Origin
  │
  ▼
Cache-Control
  │
  ▼
Cache Policy
  │
  ▼
Cache Key
  │
  ▼
CloudFront Object
  │
  ▼
Viewer Response
```

Only after understanding the caching behavior should you decide whether invalidation is appropriate.

### How would you investigate a sudden drop in cache hit rate?

Check:

- Cache policy changes
- Query-string behavior
- Cookie behavior
- Header behavior
- TTL configuration
- Traffic composition
- Recent deployments

A cache hit-rate drop is often a cache-key design problem rather than a CloudFront availability problem.

## Production Inspection Checklist

When investigating a CloudFront issue:

- [ ] Verify the AWS account and identity.
- [ ] Confirm the distribution ID.
- [ ] Check distribution status.
- [ ] Check whether the distribution is enabled.
- [ ] Verify DNS resolution.
- [ ] Test the CloudFront hostname with `curl`.
- [ ] Inspect TLS configuration.
- [ ] Inspect origins.
- [ ] Inspect default and path-based cache behaviors.
- [ ] Inspect cache policies.
- [ ] Inspect origin request policies.
- [ ] Check WAF association.
- [ ] Check invalidation history.
- [ ] Check CloudWatch request metrics.
- [ ] Check CloudWatch 4xx and 5xx rates.
- [ ] Check cache hit rate.
- [ ] Check origin latency.
- [ ] Check origin health.
- [ ] Correlate findings with recent deployments.
- [ ] Inspect application and database metrics when required.

## Command Reference

| Operation | Command |
|---|---|
| List distributions | `aws cloudfront list-distributions` |
| Inspect distribution | `aws cloudfront get-distribution --id ID` |
| Get distribution configuration | `aws cloudfront get-distribution-config --id ID` |
| Check status | `aws cloudfront get-distribution --id ID --query 'Distribution.Status' --output text` |
| Inspect origins | `aws cloudfront get-distribution --id ID --query 'Distribution.DistributionConfig.Origins.Items[]'` |
| Inspect cache behaviors | `aws cloudfront get-distribution --id ID --query 'Distribution.DistributionConfig.CacheBehaviors.Items[]'` |
| Get cache policy | `aws cloudfront get-cache-policy --id POLICY_ID` |
| Get origin request policy | `aws cloudfront get-origin-request-policy --id POLICY_ID` |
| Get response headers policy | `aws cloudfront get-response-headers-policy --id POLICY_ID` |
| Get OAC | `aws cloudfront get-origin-access-control --id OAC_ID` |
| List invalidations | `aws cloudfront list-invalidations --distribution-id ID` |
| Get invalidation | `aws cloudfront get-invalidation --distribution-id ID --id INVALIDATION_ID` |
| List CloudWatch metrics | `aws cloudwatch list-metrics --namespace AWS/CloudFront` |
| Test HTTP response | `curl -I https://cdn.example.com/path` |
| Inspect verbose HTTP/TLS | `curl -vI https://cdn.example.com/path` |
| Inspect DNS | `dig cdn.example.com` |
| Inspect TLS | `openssl s_client -connect cdn.example.com:443 -servername cdn.example.com` |

## Key Takeaways

- **Use CloudFront CLI inspection to verify configuration state:** distributions, origins, cache behaviors, policies, TLS, WAF, OAC, and invalidations should be inspectable without relying exclusively on the AWS Console.
- **Separate deployment state from runtime health:** a `Deployed` CloudFront distribution does not imply a healthy origin or backend application.
- **Correlate edge and backend telemetry:** request volume, cache hit rate, 4xx/5xx rates, and origin latency become significantly more useful when analyzed with ALB, Nginx, Django, FastAPI, PostgreSQL, and Redis metrics.
- **Use `curl`, DNS tools, AWS CLI, and CloudWatch together:** reliable CloudFront troubleshooting requires both configuration inspection and observation of actual client behavior.
- **Automate repeatable inspection:** CLI commands are well suited to CI/CD validation, incident-response scripts, configuration audits, and operational tooling, while persistent production monitoring should remain centered on CloudWatch, logs, dashboards, and alerts.