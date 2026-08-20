# 03- Cache Invalidation Commands

## Overview

CloudFront cache invalidation explicitly removes cached objects from CloudFront edge caches before their normal expiration time. It is primarily an operational mechanism for handling content that has changed but retains the same URL.

For backend engineering, invalidation matters most when deploying:

- Static frontend assets
- Images and media
- Configuration files
- API responses that were intentionally cached
- Content whose URL cannot be versioned

The important distinction is that **cache invalidation is not the same as cache policy configuration**. A cache policy determines how CloudFront caches requests and constructs cache keys. An invalidation tells CloudFront which cached objects should be removed.

A typical deployment looks like:

```text
                    Deployment
                        │
                        ▼
                New application
                   / static asset
                        │
                        ▼
                Same URL or path
                        │
                        ▼
                  CloudFront
                        │
                 Cached object
                        │
                        ▼
                 Invalidation
                        │
                        ▼
               Edge cache removal
                        │
                        ▼
             Next request → Origin
```

For production systems, invalidation should be used deliberately. **Immutable, versioned asset names are usually preferable to repeatedly invalidating `/*`.**

## How CloudFront Invalidation Works

When a client requests an object, CloudFront may serve it from an edge cache:

```text
Client
  │
  │ GET /app.js
  ▼
CloudFront Edge
  │
  ├── Cache HIT ───────► Return cached app.js
  │
  └── Cache MISS
          │
          ▼
        Origin
          │
          ▼
      Store object
          │
          ▼
       Client
```

An invalidation changes the cache state for matching objects:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Invalidation applies to /app.js
  │
  ▼
Cached object is no longer served as valid
  │
  ▼
Next request
  │
  ▼
Origin fetch
  │
  ▼
New object cached
```

The invalidation does not modify the origin object. If the origin still contains the old content, CloudFront can fetch that old content again after the invalidation.

Therefore:

> **Deploy the new origin content before or as part of the invalidation workflow.**

## When to Use Invalidation

Use invalidation when:

- A URL must remain unchanged.
- An object was cached with incorrect content.
- A deployment replaced content at a stable path.
- Emergency cache removal is required.
- Cache headers cannot be changed quickly.
- A versioned asset strategy is not practical.

Example:

```text
https://cdn.example.com/config.json
```

If `config.json` changes but its URL cannot change, invalidation may be appropriate.

## When Not to Use Invalidation

Do not use invalidation as the default deployment strategy for every static asset.

Instead of:

```text
/app.js
```

prefer:

```text
/app.7f3c1a.js
```

Then a new deployment produces:

```text
/app.91e8d4.js
```

The URLs are different, so the new object naturally gets a new cache entry.

This approach provides:

- Better cache efficiency
- Long cache lifetimes
- Lower dependency on invalidation
- Safer rollouts
- Easier rollback
- Better CDN performance

## Invalidation Command

The primary AWS CLI command is:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths "/app.js"
```

The distribution ID identifies the CloudFront distribution.

The path identifies the cached object to invalidate.

## Invalidate a Single Object

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths "/index.html"
```

For a nested object:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths "/assets/config.json"
```

For an API endpoint:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths "/api/catalog"
```

API invalidation should be used carefully because it indicates that the API response is being cached by CloudFront.

## Invalidate Multiple Objects

Multiple paths can be supplied:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths \
    "/index.html" \
    "/app.js" \
    "/styles.css"
```

This is preferable to invalidating the entire distribution when only a small number of objects changed.

Example deployment:

```text
Changed:
  /index.html
  /manifest.json
  /app.js

Unchanged:
  /assets/logo.svg
  /assets/fonts/*
  /assets/images/*
```

Invalidate only the changed paths:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths \
    "/index.html" \
    "/manifest.json" \
    "/app.js"
```

## Wildcard Invalidation

CloudFront supports wildcard paths.

Invalidate an entire directory:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths "/assets/*"
```

Invalidate everything:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths "/*"
```

`/*` is powerful but should not become the default deployment mechanism.

A full invalidation can be appropriate for:

- Emergency remediation
- Major content replacement
- Incorrectly cached site-wide content
- Recovery from a deployment mistake

It is generally a poor choice for routine deployments where only a few objects changed.

## Path Matching

Invalidation paths are URL paths, not filesystem paths.

Correct:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths "/images/logo.png"
```

The leading `/` is part of the URL path.

A wildcard can match multiple objects:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths "/images/*"
```

The invalidation target should correspond to the CloudFront request path, not the physical path on the origin.

For example:

```text
Public URL:
https://cdn.example.com/static/app.js

Origin:
s3://frontend-production/static/app.js
```

The invalidation path is:

```text
/static/app.js
```

not:

```text
s3://frontend-production/static/app.js
```

## Invalidate Query String Variants

CloudFront cache behavior can involve query strings.

For example:

```text
/product?id=10
/product?id=20
/product?id=30
```

Whether these represent separate cached objects depends on the cache policy and cache-key configuration.

A wildcard can be used when all matching variants should be invalidated:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --paths "/product*"
```

The exact behavior should be validated against the distribution's cache-key configuration.

Do not assume that invalidating `/product` automatically means every possible query-string variant is treated exactly as expected in every caching configuration.

## Create Invalidation with a JSON Batch

The CLI can submit an invalidation batch using JSON.

Example:

```json
{
  "Paths": {
    "Quantity": 3,
    "Items": [
      "/index.html",
      "/app.js",
      "/styles.css"
    ]
  },
  "CallerReference": "release-2026-08-19-001"
}
```

Create it:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123456789ABC \
  --invalidation-batch file://invalidation.json
```

This approach is useful when invalidation paths are generated programmatically.

The `CallerReference` should be unique for a new invalidation request.

## Generate a Caller Reference

A shell deployment can generate a unique caller reference:

```bash
CALLER_REFERENCE="release-$(date +%Y%m%d%H%M%S)-${GITHUB_SHA:-manual}"
```

Generate the JSON:

```bash
cat > invalidation.json <<EOF
{
  "Paths": {
    "Quantity": 2,
    "Items": [
      "/index.html",
      "/manifest.json"
    ]
  },
  "CallerReference": "$CALLER_REFERENCE"
}
EOF
```

Submit it:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --invalidation-batch file://invalidation.json
```

## Capture the Invalidation ID

The create operation returns an invalidation ID.

Example:

```bash
INVALIDATION_ID=$(
  aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --paths "/index.html" \
    --query 'Invalidation.Id' \
    --output text
)

echo "$INVALIDATION_ID"
```

The ID can then be used to inspect the invalidation.

## Check Invalidation Status

Retrieve a specific invalidation:

```bash
aws cloudfront get-invalidation \
  --distribution-id E123456789ABC \
  --id I123456789ABC
```

Extract its status:

```bash
aws cloudfront get-invalidation \
  --distribution-id E123456789ABC \
  --id I123456789ABC \
  --query 'Invalidation.Status' \
  --output text
```

Typical operational states include:

```text
InProgress
Completed
```

A completed invalidation means CloudFront has processed the invalidation request.

## Wait for an Invalidation

The AWS CLI provides a waiter:

```bash
aws cloudfront wait invalidation-completed \
  --distribution-id E123456789ABC \
  --id I123456789ABC
```

This is preferable to:

```bash
sleep 300
```

A fixed sleep introduces unnecessary delays when propagation completes sooner and can still be insufficient when it takes longer.

## List Invalidations

List invalidations for a distribution:

```bash
aws cloudfront list-invalidations \
  --distribution-id E123456789ABC
```

Display useful fields:

```bash
aws cloudfront list-invalidations \
  --distribution-id E123456789ABC \
  --query 'InvalidationList.Items[].{Id:Id,Status:Status,Created:CreateTime}' \
  --output table
```

Get the latest invalidation:

```bash
aws cloudfront list-invalidations \
  --distribution-id E123456789ABC \
  --query 'InvalidationList.Items[0].{Id:Id,Status:Status,Created:CreateTime}' \
  --output table
```

## Inspect Invalidation Paths

Retrieve the complete invalidation:

```bash
aws cloudfront get-invalidation \
  --distribution-id E123456789ABC \
  --id I123456789ABC
```

Extract paths:

```bash
aws cloudfront get-invalidation \
  --distribution-id E123456789ABC \
  --id I123456789ABC \
  --query 'Invalidation.InvalidationBatch.Paths.Items[]' \
  --output text
```

This is useful when investigating why an expected object was or was not included in an invalidation request.

## Production Deployment Pattern

A robust static asset deployment can look like:

```text
Build
  │
  ▼
Generate versioned assets
  │
  ▼
Upload assets to origin
  │
  ├───────────────┐
  │               │
  ▼               ▼
Immutable      Stable files
assets         such as index.html
  │               │
  │               ▼
  │          Targeted invalidation
  │               │
  └───────┬───────┘
          ▼
      CloudFront
          │
          ▼
     Smoke testing
```

For example:

```bash
set -euo pipefail

DISTRIBUTION_ID="E123456789ABC"

aws s3 sync ./dist s3://frontend-production \
  --delete

INVALIDATION_ID=$(
  aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --paths "/index.html" "/manifest.json" \
    --query 'Invalidation.Id' \
    --output text
)

aws cloudfront wait invalidation-completed \
  --distribution-id "$DISTRIBUTION_ID" \
  --id "$INVALIDATION_ID"
```

This pattern assumes that immutable assets are already content-hashed and therefore do not need invalidation.

## Static Frontend Deployment

A modern frontend deployment might produce:

```text
dist/
├── index.html
├── manifest.json
└── assets/
    ├── app-a91f2e.js
    ├── vendor-7f18c4.js
    └── styles-21ca8d.css
```

The deployment strategy can be:

```text
index.html
    │
    └── invalidate

manifest.json
    │
    └── invalidate

assets/*
    │
    └── immutable URLs
```

Command:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths \
    "/index.html" \
    "/manifest.json"
```

This is significantly better than:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*"
```

for every release.

## Cache Invalidation vs Versioned URLs

| Strategy | Cache efficiency | Operational complexity | Typical use |
|---|---:|---:|---|
| Single-object invalidation | High | Low | Stable critical files |
| Directory invalidation | Medium | Low | Limited content groups |
| `/*` invalidation | Low | Very low | Emergency or broad replacement |
| Versioned filenames | Very high | Medium | Static assets |
| Content-hashed assets | Very high | Medium | Modern frontend builds |

Versioned URLs are usually the preferred strategy for immutable assets.

## Cache-Control and Invalidation

Invalidation and `Cache-Control` solve different problems.

`Cache-Control` defines how long a response can be cached.

Example:

```http
Cache-Control: public, max-age=31536000, immutable
```

This is appropriate for content-hashed assets such as:

```text
/app.91f83a.js
```

For a mutable document such as:

```text
/index.html
```

a shorter cache lifetime may be appropriate.

The architectural pattern is often:

```text
Immutable assets
→ long TTL
→ versioned filenames
→ no routine invalidation

Mutable entry points
→ shorter TTL
→ targeted invalidation when necessary
```

## Invalidation and Cache Policies

Cache policy determines whether requests can share a cache entry.

Invalidation removes matching cached objects.

They operate at different stages of cache management:

```text
Request
  │
  ▼
Cache Policy
  │
  ▼
Cache Key
  │
  ▼
Cached Object
  │
  ├── HIT ──► Response
  │
  └── MISS ─► Origin
```

An invalidation acts on the existing cached object:

```text
Existing Cache Entry
        │
        ▼
   Invalidation
        │
        ▼
Entry no longer served as valid
```

Changing the cache policy is not equivalent to invalidating existing objects.

## Invalidation and Origin Content

An invalidation does not deploy content.

Incorrect deployment order:

```text
Invalidate
   │
   ▼
CloudFront requests origin
   │
   ▼
Origin still has old version
   │
   ▼
Old version becomes cached again
```

Correct sequence:

```text
Deploy new origin content
   │
   ▼
Verify origin content
   │
   ▼
Invalidate stable cached paths
   │
   ▼
CloudFront retrieves new content
```

For example:

```bash
curl --fail --silent \
  https://origin.example.com/index.html
```

Then invalidate:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/index.html"
```

## Invalidation in CI/CD

A GitHub Actions workflow can perform targeted invalidation:

```yaml
- name: Invalidate CloudFront
  env:
    AWS_REGION: us-east-1
    DISTRIBUTION_ID: ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }}
  run: |
    set -euo pipefail

    INVALIDATION_ID=$(
      aws cloudfront create-invalidation \
        --distribution-id "$DISTRIBUTION_ID" \
        --paths "/index.html" "/manifest.json" \
        --query 'Invalidation.Id' \
        --output text
    )

    aws cloudfront wait invalidation-completed \
      --distribution-id "$DISTRIBUTION_ID" \
      --id "$INVALIDATION_ID"
```

For production:

- Use GitHub OIDC rather than long-lived AWS access keys.
- Restrict the deployment role to the required CloudFront and origin permissions.
- Store distribution identifiers as controlled environment configuration.
- Avoid granting broad administrator access to CI.
- Make invalidation paths deterministic from the deployment artifact.

## Invalidation from Python

A deployment service can use `boto3`.

```python
import boto3

cloudfront = boto3.client("cloudfront")

response = cloudfront.create_invalidation(
    DistributionId="E123456789ABC",
    InvalidationBatch={
        "Paths": {
            "Quantity": 2,
            "Items": [
                "/index.html",
                "/manifest.json",
            ],
        },
        "CallerReference": "release-20260819-001",
    },
)

invalidation_id = response["Invalidation"]["Id"]

print(f"Created invalidation: {invalidation_id}")
```

A production implementation should generate a genuinely unique caller reference, handle AWS API errors, and avoid embedding credentials in source code.

Use IAM roles, workload identity, or the execution environment's credential provider chain.

## API Response Handling

A successful `create-invalidation` response indicates that CloudFront accepted the invalidation request.

It does not mean that every edge cache has already processed it.

Therefore, automation that requires completion should use:

```bash
aws cloudfront wait invalidation-completed \
  --distribution-id "$DISTRIBUTION_ID" \
  --id "$INVALIDATION_ID"
```

For workflows that do not require synchronous completion, the deployment can submit the invalidation and monitor it separately.

## Invalidation Monitoring

At minimum, monitor:

- Invalidation ID
- Creation time
- Status
- Paths
- Deployment version
- CI/CD job
- Distribution ID

Example:

```bash
aws cloudfront list-invalidations \
  --distribution-id "$DISTRIBUTION_ID" \
  --query 'InvalidationList.Items[].{Id:Id,Status:Status,Created:CreateTime}' \
  --output table
```

For production observability, correlate invalidations with:

- Deployment IDs
- Git commit SHA
- Application release version
- CloudFront metrics
- Origin errors
- Cache hit ratio
- Application health checks

## Cost and Operational Considerations

Invalidations are a useful control-plane operation, but a system that depends heavily on them is often signaling a cache-management design problem.

Common causes include:

- Mutable URLs for immutable assets
- Excessively long TTLs for frequently changing content
- Deployments that overwrite stable filenames
- Lack of content hashing
- Full `/*` invalidations after every deployment

A better design is usually:

```text
Immutable content
      │
      ▼
Versioned URL
      │
      ▼
Long cache lifetime
      │
      ▼
No invalidation required
```

while mutable content uses:

```text
Stable URL
    │
    ▼
Appropriate TTL
    │
    ▼
Targeted invalidation when necessary
```

## Common Mistakes

### Invalidating Before Deploying the New Content

Bad:

```text
Invalidate
→ Deploy
```

Better:

```text
Deploy
→ Verify
→ Invalidate
```

Otherwise CloudFront can refill its cache with the old origin content.

### Invalidating `/*` on Every Deployment

Bad:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*"
```

This is simple but wasteful for routine deployments.

Prefer targeted paths or versioned assets.

### Invalidating the Origin Path

Incorrect:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "s3://frontend-production/index.html"
```

Correct:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/index.html"
```

### Assuming Invalidation Changes the Origin

It does not.

If the origin still contains the old object, CloudFront can fetch the old content again.

### Using Invalidation to Fix Incorrect Cache Keys

If users receive the wrong representation because the cache key is incorrectly designed, invalidation may only provide temporary relief.

Fix the cache policy.

For example, if responses vary by a required query parameter but that parameter is absent from the cache key, the underlying issue is cache-key design.

### Using Long TTLs on Mutable API Responses

A long-lived cached API response can become stale even if invalidation exists.

Before caching API responses, establish:

- What identifies the response?
- Which request attributes affect it?
- How long can it be stale?
- Can the object be invalidated?
- Does authentication affect the response?
- Is the response user-specific?

## Troubleshooting

### New Content Is Not Visible

Check the origin first:

```bash
curl -I https://origin.example.com/index.html
```

Then inspect the CloudFront response:

```bash
curl -I https://www.example.com/index.html
```

Compare:

```text
Origin response
        │
        ├── Correct
        │
        ▼
CloudFront response
        │
        ├── Incorrect
        │
        ▼
Inspect cache/invalidation behavior
```

### Check Invalidation Status

```bash
aws cloudfront get-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --id "$INVALIDATION_ID" \
  --query 'Invalidation.Status' \
  --output text
```

### Check Distribution Status

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.Status' \
  --output text
```

### Inspect Response Headers

```bash
curl -I https://www.example.com/app.js
```

Headers such as `Age`, `Cache-Control`, and CloudFront-specific response headers can help determine whether the response is being served from a cache and how it is configured.

Do not diagnose a cache problem solely from the browser. Validate the actual HTTP response path.

## Production Invalidation Checklist

Before issuing an invalidation:

- [ ] Confirm the new object exists at the origin.
- [ ] Confirm the CloudFront distribution ID.
- [ ] Confirm the exact URL paths that changed.
- [ ] Prefer targeted paths over `/*`.
- [ ] Prefer versioned filenames for immutable assets.
- [ ] Confirm the cache policy and cache-key behavior.
- [ ] Generate a unique caller reference when using an invalidation batch.
- [ ] Capture the invalidation ID.
- [ ] Wait for completion when the deployment requires synchronous validation.
- [ ] Run smoke tests after completion.
- [ ] Record the invalidation against the deployment or release.

## Command Reference

| Operation | Command |
|---|---|
| Create single invalidation | `aws cloudfront create-invalidation --distribution-id ID --paths "/file"` |
| Create multiple invalidations | `aws cloudfront create-invalidation --distribution-id ID --paths "/a" "/b"` |
| Invalidate directory | `aws cloudfront create-invalidation --distribution-id ID --paths "/assets/*"` |
| Invalidate everything | `aws cloudfront create-invalidation --distribution-id ID --paths "/*"` |
| List invalidations | `aws cloudfront list-invalidations --distribution-id ID` |
| Get invalidation | `aws cloudfront get-invalidation --distribution-id ID --id INVALIDATION_ID` |
| Check status | `aws cloudfront get-invalidation --distribution-id ID --id INVALIDATION_ID --query 'Invalidation.Status' --output text` |
| Wait for completion | `aws cloudfront wait invalidation-completed --distribution-id ID --id INVALIDATION_ID` |

## Interview Traps

### Does invalidation delete the object from S3?

No.

Invalidation affects CloudFront's cached copies. It does not delete or modify the origin object.

### Does invalidation change the TTL?

No.

Invalidation and TTL are different mechanisms.

### Does invalidation guarantee that the next request gets the desired content?

Only if the origin contains the desired content and the request maps to the intended cache object.

### Why are versioned assets better?

Versioned assets naturally create new cache keys, allowing aggressive caching without requiring invalidation for every release.

### Is `/*` always wrong?

No.

It can be appropriate for emergency remediation or broad content replacement. It is simply a poor default for routine deployments.

### Does invalidation fix every stale-content problem?

No.

Stale content can result from:

- Incorrect cache policy
- Incorrect cache key
- Incorrect origin content
- Application-level caching
- Browser caching
- Proxy caching
- Service-worker caching

CloudFront invalidation only addresses CloudFront's cached objects.

## Key Takeaways

- **Invalidate URL paths, not origin filesystem or S3 paths:** CloudFront invalidation operates on request paths such as `/index.html`.
- **Deploy the new origin content before invalidating stable URLs:** otherwise CloudFront can refill its cache with the old content.
- **Prefer immutable, content-hashed assets over repeated invalidation:** versioned URLs provide better cache efficiency and simpler deployments.
- **Use targeted invalidations for mutable content and reserve `/*` for broad or emergency cases.**
- **An invalidation request is asynchronous:** capture the invalidation ID and use `aws cloudfront wait invalidation-completed` when deployment automation requires completion.