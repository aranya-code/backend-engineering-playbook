# 08- Cache Invalidation and Versioning

## Overview

CloudFront caching is most effective when objects can remain cached for a predictable period without requiring frequent manual intervention. The challenge is that production applications continuously change: JavaScript bundles are deployed, CSS is updated, images are replaced, API representations change, and configuration-driven content may become stale.

Two mechanisms are commonly used to handle this problem:

- **Cache invalidation** — explicitly asks CloudFront to remove cached objects.
- **Cache versioning** — changes the object's URL so CloudFront treats the new content as a different object.

For production systems, versioning is generally the preferred strategy for static, immutable assets. Invalidation remains important when content must be replaced at an existing URL, when an emergency correction is required, or when a deployment architecture cannot use content-addressed filenames.

The distinction is fundamental:

```text
Invalidation
    ↓
Remove existing cached object

Versioning
    ↓
Create a new object identity
```

A well-designed deployment pipeline often uses both:

```text
Normal deployment
    ↓
Version static assets
    ↓
Deploy
    ↓
No broad invalidation required

Exceptional change
    ↓
Explicit invalidation
    ↓
Force CloudFront to stop serving selected cached objects
```

## Why Cache Invalidation Matters

Consider a production application serving:

```text
https://cdn.example.com/static/app.js
```

CloudFront may cache the object for a long period:

```http
Cache-Control: public, max-age=31536000, immutable
```

Suppose a deployment replaces the JavaScript file with a new implementation while keeping the same URL:

```text
Before:
app.js → version A

After:
app.js → version B
```

CloudFront may continue serving version A until the cached object expires or is explicitly invalidated.

This creates a deployment consistency problem:

```text
Deployment
    │
    ▼
Origin has version B
    │
    ▼
CloudFront still has version A
    │
    ▼
Users receive different versions
```

Cache invalidation exists to resolve this mismatch when changing the object's URL is not practical.

## Cache Invalidation vs Versioning

| Technique | Mechanism | Best use case | Operational cost |
|---|---|---|---|
| Invalidation | Remove cached objects | Emergency changes, mutable URLs | Requires invalidation operation |
| Versioning | Change object URL | Static assets and immutable deployments | Requires asset/reference update |
| Short TTL | Let objects expire | Frequently changing content | More origin traffic |
| Revalidation | Check freshness with origin | Content requiring validation | Adds origin interaction |

The strongest production strategy is usually:

```text
Immutable static assets
        ↓
Versioned filenames
        ↓
Long TTL
        ↓
No routine invalidation
```

while reserving invalidations for cases where URL versioning is not appropriate.

## How CloudFront Invalidation Works

An invalidation creates a request for CloudFront to stop serving matching cached objects from its edge caches.

Conceptually:

```text
                    ┌── Edge A
                    │
Invalidation ────────┼── Edge B
                    │
                    ├── Edge C
                    │
                    └── Edge N

Matched cached objects
        ↓
No longer served as valid cached objects
```

The object remains at the origin.

An invalidation does **not** delete the object from:

- Amazon S3
- EC2
- An ALB origin
- A Django application
- A FastAPI application
- Any other origin

It affects CloudFront's cached representation.

```text
CloudFront cache
    ↓
Invalidated

Origin
    ↓
Unaffected
```

## Invalidation Request Lifecycle

A typical invalidation workflow is:

```mermaid
sequenceDiagram
    participant CI as CI/CD Pipeline
    participant CF as CloudFront
    participant Edge as Edge Caches
    participant O as Origin
    participant V as Viewer

    CI->>CF: Create invalidation
    CF->>Edge: Mark matching objects invalid
    Edge-->>CF: Invalidation processing

    V->>CF: Request object
    CF->>Edge: Cache lookup

    alt Invalidated object
        Edge-->>CF: Cache miss
        CF->>O: Fetch current object
        O-->>CF: New response
        CF->>Edge: Cache new object
        CF-->>V: New response
    else Unaffected object
        Edge-->>CF: Cache hit
        CF-->>V: Cached response
    end
```

The invalidation process is asynchronous. A production deployment should not assume that creating an invalidation means every edge immediately stops serving the old object at the exact same instant.

## Creating an Invalidation with AWS CLI

A typical AWS CLI command is:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123EXAMPLE456 \
  --paths "/static/app.js"
```

Multiple paths can be supplied:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123EXAMPLE456 \
  --paths \
    "/static/app.js" \
    "/static/app.css" \
    "/index.html"
```

A wildcard can match a broader path:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123EXAMPLE456 \
  --paths "/static/*"
```

A root-level wildcard can invalidate all matching objects:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123EXAMPLE456 \
  --paths "/*"
```

Broad invalidations should be treated as an operational tool rather than the default deployment mechanism.

## Checking an Invalidation

After creating an invalidation, retrieve its status:

```bash
aws cloudfront get-invalidation \
  --distribution-id E123EXAMPLE456 \
  --id I123EXAMPLE789
```

The invalidation progresses through CloudFront-managed states.

A deployment pipeline should avoid assuming completion immediately after the API accepts the request.

## Invalidation Paths

An invalidation path should identify the cached object or objects that need to be removed.

Examples:

```text
/static/app.js
/images/logo.png
/index.html
/api/catalog/*
```

The path should correspond to the CloudFront URL path, not an S3 filesystem path.

For example, if the viewer requests:

```text
https://cdn.example.com/static/app.js
```

the invalidation path is:

```text
/static/app.js
```

not:

```text
s3://frontend-assets/static/app.js
```

## Wildcard Invalidations

Wildcards are useful when multiple objects need to be invalidated.

For example:

```text
/static/*
```

can target objects under the `/static/` path.

A broad wildcard such as:

```text
/*
```

should be used carefully because it can invalidate a large portion of the distribution's cached content.

Before using a broad invalidation, ask:

```text
Do all cached objects actually need to be replaced?
```

If the answer is no, invalidate only the affected paths.

## Why Broad Invalidation Is Usually a Bad Deployment Strategy

Consider a deployment that changes:

```text
/static/app.js
/static/app.css
```

but invalidates:

```text
/*
```

The deployment may unnecessarily discard cached objects such as:

```text
/images/logo.svg
/images/hero.webp
/fonts/inter.woff2
/static/vendor.js
```

This reduces cache efficiency and can create a temporary increase in origin traffic.

The resulting pattern is:

```text
Deployment
    ↓
Invalidate /*
    ↓
Many cache entries removed
    ↓
Large number of cache misses
    ↓
Origin traffic spike
    ↓
Potential application load increase
```

For a large production system, this can become a self-inflicted traffic event.

## Versioning

Versioning changes the identity of an object when its content changes.

Instead of:

```text
/static/app.js
```

use:

```text
/static/app.91c3e7.js
```

When the content changes:

```text
/static/app.4d21af.js
```

becomes the new object.

CloudFront sees these as different cache keys:

```text
/static/app.91c3e7.js
/static/app.4d21af.js
```

The old object can remain cached until its TTL expires because it is no longer referenced by the current application.

## Content-Hash Versioning

A strong production pattern is content hashing.

```text
app.js
    ↓
Build
    ↓
SHA-derived identifier
    ↓
app.91c3e7.js
```

If the file content changes:

```text
app.js
    ↓
New build
    ↓
app.4d21af.js
```

The filename changes only when the content changes.

This provides an important property:

> The URL uniquely identifies a particular version of the content.

This is particularly effective for:

- JavaScript
- CSS
- Fonts
- Images
- WebAssembly
- Static JSON
- Frontend bundles

## Versioned Asset Lifecycle

```mermaid
flowchart TD
    A[Source Asset] --> B[Build Pipeline]
    B --> C[Content Hash]
    C --> D[Versioned Filename]
    D --> E[Upload to Origin]
    E --> F[Deploy HTML / Application]
    F --> G[Viewer Requests New URL]
    G --> H{CloudFront Cache}
    H -->|Hit| I[Return Cached Version]
    H -->|Miss| J[Fetch New Object]
    J --> I
```

For example:

```text
Source:
app.js

Build:
app.91c3e7.js

Upload:
s3://assets/static/app.91c3e7.js

HTML:
<script src="/static/app.91c3e7.js"></script>
```

The next deployment might produce:

```text
app.4d21af.js
```

The HTML reference changes accordingly.

## Immutable Caching

Versioned assets work especially well with immutable caching.

Example:

```http
Cache-Control: public, max-age=31536000, immutable
```

The reasoning is:

```text
Versioned URL
      ↓
Content never changes at that URL
      ↓
Safe to cache for a long period
      ↓
High cache hit ratio
      ↓
Low origin traffic
```

If the application needs a new asset, it publishes a new URL.

This avoids the need to tell every cache:

```text
"Forget the old version."
```

Instead, the application simply stops referencing the old version.

## Why `immutable` Makes Sense

Suppose:

```text
/static/app.91c3e7.js
```

contains a content hash.

If the build system guarantees that this exact URL will never point to different content, the browser and CDN can safely cache it for a long period.

The deployment model becomes:

```text
Old:
app.91c3e7.js

New:
app.4d21af.js
```

The old URL does not need to change.

This is fundamentally different from:

```text
/static/app.js
```

where the same URL points to changing content.

## HTML and Versioned Assets

HTML often requires a different caching strategy because it references the current asset versions.

For example:

```html
<script src="/static/app.4d21af.js"></script>
```

If HTML itself is aggressively cached for a long period, users may continue receiving old HTML and therefore continue requesting old assets.

A common strategy is:

```text
HTML
    ↓
Shorter TTL / controlled caching

JS/CSS/images
    ↓
Content-hashed filenames
    ↓
Long TTL
```

This creates a useful hierarchy:

```text
HTML
  ↓
Finds current asset versions

Versioned assets
  ↓
Remain immutable and highly cacheable
```

## The Deployment Ordering Problem

Asset versioning does not eliminate deployment sequencing concerns.

Consider:

```text
Version A HTML
    references
app.A.js
```

A new deployment produces:

```text
Version B HTML
    references
app.B.js
```

The deployment should generally make `app.B.js` available before exposing HTML that references it.

Safe ordering:

```text
Build app.B.js
      ↓
Upload app.B.js
      ↓
Verify availability
      ↓
Deploy HTML referencing app.B.js
```

Risky ordering:

```text
Deploy HTML referencing app.B.js
      ↓
Upload app.B.js
```

During the gap, clients can receive HTML referring to an object that does not yet exist at the origin.

## Blue-Green Deployment Considerations

For larger systems, asset versioning works well with blue-green or atomic deployments.

```text
Build
  ↓
Generate immutable assets
  ↓
Upload assets
  ↓
Deploy application
  ↓
Switch traffic
```

Because assets are immutable, old application versions can continue to reference their old assets while the new version references new assets.

This is valuable during rollback:

```text
Application B
    ↓
app.B.js

Rollback
    ↓
Application A
    ↓
app.A.js
```

Both asset versions can coexist.

## Rolling Deployments

Rolling deployments have similar benefits.

Suppose multiple application instances are running:

```text
Instance 1 → Version A
Instance 2 → Version A
Instance 3 → Version B
Instance 4 → Version B
```

If both versions use immutable asset URLs, the application can safely serve:

```text
app.A.js
app.B.js
```

during the transition.

This reduces the need for synchronized cache purges.

## Invalidation vs Versioning Architecture

```mermaid
flowchart LR
    A[Application Deployment] --> B{Content Strategy}

    B -->|Immutable Asset| C[Version URL]
    C --> D[Long TTL]
    D --> E[CloudFront Cache]

    B -->|Fixed URL| F[Invalidate Path]
    F --> G[CloudFront Removes Cached Object]
    G --> H[Next Request Fetches Origin]
```

The engineering decision should be based on whether the URL can safely change.

## When to Use Versioning

Versioning is preferred when:

- The content is static.
- The build pipeline controls asset names.
- The content can be treated as immutable.
- Long TTLs are desirable.
- The application can update references to new versions.
- Rollbacks should preserve older asset versions.

Typical examples:

```text
JavaScript bundles
CSS bundles
Images
Fonts
Static JSON
Frontend chunks
```

## When to Use Invalidation

Invalidation is appropriate when:

- The URL must remain stable.
- Content is updated at the same path.
- An emergency correction must propagate quickly.
- A deployment cannot safely change the URL.
- A stale object must be removed before its normal TTL expires.

Examples:

```text
/index.html
/config.json
/robots.txt
/.well-known/*
```

The exact strategy depends on how frequently the resource changes and whether its URL is externally fixed.

## Hybrid Strategy

A mature architecture commonly combines both mechanisms.

For example:

| Resource | Strategy | Typical TTL |
|---|---|---|
| JS bundle | Content hash | Long |
| CSS bundle | Content hash | Long |
| Images | Content hash where practical | Long |
| Fonts | Content hash | Long |
| HTML | Shorter TTL / controlled invalidation | Short |
| `robots.txt` | Fixed URL + invalidation if needed | Moderate |
| API responses | Application-specific | Varies |
| Emergency content | Explicit invalidation | N/A |

The important point is that invalidation should be an exception rather than the routine mechanism for every deployment.

## CI/CD Integration

A deployment pipeline can implement versioning automatically.

Conceptually:

```text
Git Commit
    ↓
CI Build
    ↓
Generate hashed assets
    ↓
Upload immutable assets
    ↓
Deploy application / HTML
    ↓
Optional targeted invalidation
    ↓
Smoke tests
```

A simplified GitHub Actions example might look like:

```yaml
name: Deploy Frontend

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Build
        run: npm ci && npm run build

      - name: Upload assets
        run: |
          aws s3 sync dist/ s3://example-frontend-assets/

      - name: Invalidate HTML
        run: |
          aws cloudfront create-invalidation \
            --distribution-id "${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }}" \
            --paths "/index.html"
```

The example deliberately invalidates only the HTML entry point while allowing content-hashed static assets to remain cached.

In a real pipeline, credentials should be provided through an appropriate AWS identity mechanism rather than hard-coded secrets.

## Deploying Versioned Assets to S3

A build system might produce:

```text
dist/
├── index.html
└── static/
    ├── app.91c3e7.js
    ├── app.4d21af.css
    └── vendor.72a8b1.js
```

Upload the generated assets:

```bash
aws s3 sync dist/ s3://example-frontend-assets/
```

The application then references the generated filenames.

For stronger control, separate immutable assets from mutable entry points:

```text
s3://example-frontend-assets/
├── index.html
└── static/
    ├── app.91c3e7.js
    ├── app.4d21af.css
    └── vendor.72a8b1.js
```

## Targeted HTML Invalidation

A common deployment pattern is:

```text
Hashed JS/CSS
    ↓
Long TTL
    ↓
No invalidation

index.html
    ↓
Short TTL or targeted invalidation
```

For example:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123EXAMPLE456 \
  --paths "/index.html"
```

This is much more controlled than:

```bash
aws cloudfront create-invalidation \
  --distribution-id E123EXAMPLE456 \
  --paths "/*"
```

The latter should be reserved for situations where broad invalidation is genuinely required.

## Cache Invalidation and API Deployments

APIs require more careful reasoning.

Suppose:

```text
GET /api/catalog
```

is cached by CloudFront.

The backend deployment changes the response schema:

```json
{
  "products": [...]
}
```

to:

```json
{
  "items": [...],
  "next_cursor": "..."
}
```

If an old response remains cached, clients may temporarily receive the previous representation.

Before caching APIs at CloudFront, establish:

- How long responses remain valid.
- Whether clients tolerate stale responses.
- Whether schema changes are backward compatible.
- Whether authentication affects the response.
- Whether invalidation is needed for emergency changes.

For frequently changing or personalized APIs, disabling shared caching may be safer.

## Cache Invalidation During Emergency Response

Consider a security or correctness incident where a cached resource must be removed immediately.

A controlled operational process is:

```text
Identify affected URL
       ↓
Confirm cache behavior
       ↓
Create targeted invalidation
       ↓
Monitor invalidation status
       ↓
Request object again
       ↓
Verify new response
       ↓
Monitor origin traffic and errors
```

Avoid immediately using:

```text
/*
```

unless the incident genuinely affects the entire distribution.

## Invalidation and Origin Changes

Changing the origin does not automatically imply that every cached object disappears.

For example:

```text
CloudFront
    ↓
Origin A
```

is changed to:

```text
CloudFront
    ↓
Origin B
```

Existing cached objects may still be served according to the existing cache state and configuration.

When an origin change changes the meaning of cached objects, explicitly assess whether invalidation or versioning is required.

## Cache Invalidation and Rollbacks

Versioning makes rollback safer.

Suppose:

```text
Release A
    ↓
app.A.js

Release B
    ↓
app.B.js
```

If Release B fails:

```text
Rollback
    ↓
Release A
    ↓
app.A.js
```

There is no requirement to make:

```text
app.js
```

change from B back to A.

Both objects can coexist:

```text
CloudFront
├── app.A.js
└── app.B.js
```

The application determines which version is referenced.

This is one reason immutable asset deployment is preferable to repeatedly replacing the same object.

## Browser Cache Interaction

CloudFront is not the only cache.

A typical request may pass through:

```text
Viewer Browser
      ↓
CloudFront
      ↓
Origin
```

Therefore, changing CloudFront's cache state does not necessarily remove a previously cached browser response.

For example:

```text
Browser
  ↓
Browser cache hit
```

can occur before a request reaches CloudFront.

This distinction matters during emergency debugging.

```text
CloudFront invalidation
        ↓
Removes CloudFront-side cached representation

Browser cache
        ↓
May still contain previous response
```

Cache-Control headers must therefore be designed across both browser and CDN caching layers.

## Browser and CDN TTL Design

A useful production model is:

```text
Immutable assets
    ↓
Browser: long TTL
CloudFront: long TTL

HTML
    ↓
Browser: short / controlled
CloudFront: short / controlled
```

This prevents users from being stuck with an old HTML document that references outdated assets.

## Cache Invalidation and Stale Content

Stale content can have multiple causes:

| Cause | Example |
|---|---|
| CloudFront cache | Old object at edge |
| Browser cache | Old object in user's browser |
| Origin cache | Redis or application cache |
| Application state | Old deployment instance |
| S3 object | Origin itself contains old content |
| DNS | Old endpoint resolution |

Invalidating CloudFront does not automatically fix all of these.

A correct troubleshooting process identifies which layer contains the stale state.

## Monitoring Invalidation Operations

Production CI/CD systems should capture:

- Distribution ID
- Invalidation ID
- Paths
- Creation timestamp
- Completion status
- Deployment version
- Initiating pipeline/job

For example:

```text
Deployment: release-2026.08.19.3
Distribution: E123EXAMPLE456
Invalidation: I123EXAMPLE789
Paths: /index.html
Status: Completed
```

This makes cache operations auditable during deployment and incident investigation.

## Cost and Operational Considerations

Invalidations are not a substitute for sound cache architecture.

AWS provides a quota and pricing model around invalidation operations, so high-frequency invalidation-heavy architectures should be evaluated against versioned deployment strategies.

More importantly, excessive invalidation can create operational side effects:

```text
Frequent invalidation
      ↓
Reduced cache effectiveness
      ↓
More origin requests
      ↓
Higher backend load
      ↓
Potentially higher infrastructure cost
```

Versioning avoids this repeated cache churn for immutable assets.

## Common Mistakes

### Using `/*` After Every Deployment

This defeats much of the benefit of CDN caching.

Prefer:

```text
Version assets
+
Invalidate only mutable entry points when necessary
```

### Replacing Content Under the Same URL

For example:

```text
/static/app.js
```

is overwritten on every deployment while using a one-year TTL.

This creates a mismatch between:

```text
Origin content
```

and:

```text
CloudFront content
```

Use content hashing or an appropriate invalidation strategy.

### Using Long TTLs Without Versioning

Long TTLs are excellent for immutable content but dangerous for mutable URLs.

The problem is not the long TTL itself. The problem is combining:

```text
Long TTL
+
Mutable URL
```

### Assuming Invalidation Deletes the Origin Object

It does not.

Invalidation affects CloudFront's cached representation, not the source object.

### Forgetting Browser Caches

CloudFront invalidation does not necessarily remove an object already stored in a browser cache.

### Deploying HTML Before Its Assets

If HTML references a new asset that has not yet been uploaded, clients can receive:

```text
404 Not Found
```

Upload immutable assets before publishing references to them.

### Invalidating APIs Without Understanding Semantics

An API response may depend on:

- Authorization
- Tenant
- Query strings
- Headers
- Cookies

Invalidation does not fix an incorrectly designed cache key.

### Treating Invalidation as a Correctness Mechanism

If an architecture requires invalidating hundreds of thousands of objects after every deployment, the underlying content-delivery strategy should be reconsidered.

## Production Pitfalls

### Invalidation Storms

Multiple pipelines may trigger overlapping invalidations:

```text
Deploy A → /*
Deploy B → /*
Deploy C → /*
```

This creates unnecessary cache churn and complicates operational behavior.

Use deployment coordination and targeted paths.

### Non-Atomic Asset Deployment

Uploading some assets, updating HTML, and then uploading remaining assets can expose inconsistent versions.

Prefer:

```text
Build complete artifact
        ↓
Upload immutable assets
        ↓
Verify
        ↓
Publish entry point
```

### Inconsistent Asset References

If different application components reference different asset manifests, a deployment can produce:

```text
HTML → app.B.js
API / template → app.A.js
```

Generate asset references from a single build artifact or manifest.

### Retaining Unlimited Old Assets

Versioning means old assets can accumulate in S3.

A production system should consider lifecycle management for obsolete assets.

For example:

```text
Current assets
    ↓
Keep available

Old unused assets
    ↓
Lifecycle policy
    ↓
Transition / expiration according to retention requirements
```

Do not delete old assets so aggressively that active users or rollback deployments can break.

## Security Considerations

Cache invalidation itself is not an authorization mechanism.

Protect the ability to create invalidations using least-privilege IAM permissions.

A deployment role should have only the permissions necessary for the deployment workflow.

Avoid giving application runtime identities broad CloudFront administration privileges when they do not need them.

A useful separation is:

```text
Application Runtime Role
    ↓
Application resources only

Deployment Role
    ↓
S3 deployment
+
CloudFront invalidation
```

For CI/CD systems, prefer short-lived AWS credentials or federated identity mechanisms rather than long-lived access keys.

## Reliability and Rollback

A reliable deployment should make rollback possible without depending on cache invalidation.

Versioned assets provide this property naturally:

```text
Release A
    ├── HTML A
    └── Assets A

Release B
    ├── HTML B
    └── Assets B
```

Both can coexist.

Rollback becomes:

```text
Traffic
  ↓
Release B

Incident
  ↓
Rollback
  ↓
Release A
```

The old assets remain available while the rollback occurs.

This is significantly safer than replacing a single mutable asset URL repeatedly.

## Recommended Production Strategy

For a modern web application:

```text
                    Build
                      │
                      ▼
             Content-hashed assets
                      │
                      ▼
               Upload to S3
                      │
                      ▼
                 Verify assets
                      │
                      ▼
                Publish HTML
                      │
                      ▼
                CloudFront
                      │
          ┌───────────┴───────────┐
          │                       │
    Versioned Assets            HTML
          │                       │
      Long TTL             Shorter TTL
          │                       │
     No routine             Targeted
    invalidation           invalidation
```

This architecture maximizes cache efficiency while maintaining controlled deployment propagation.

## Decision Framework

Use the following decision process:

```text
Does the URL need to remain unchanged?
          │
      ┌───┴───┐
      │       │
     No      Yes
      │       │
      ▼       ▼
 Version    Can the TTL
  asset     be safely short?
              │
          ┌───┴───┐
          │       │
         Yes      No
          │       │
          ▼       ▼
       Short TTL  Targeted
                  invalidation
```

For static assets, the answer should usually favor versioning.

For mutable externally referenced URLs, invalidation or controlled TTLs may be more appropriate.

## Interview Traps

### Does invalidation delete an S3 object?

No. It removes the matching cached representation from CloudFront; the origin object remains.

### Does invalidation happen instantly at every edge?

The invalidation request is processed asynchronously. Do not build deployment logic around an assumption of instantaneous global completion.

### Why is versioning usually better for static assets?

It creates immutable object identities, allowing long TTLs and high cache efficiency without repeatedly purging existing objects.

### Should every deployment invalidate `/*`?

No. Broad invalidation is usually unnecessary for content-hashed assets and can reduce cache efficiency.

### Does CloudFront invalidation clear browser caches?

No. Browser caching is a separate caching layer.

### What happens to old versioned assets?

They can remain available in the origin and CloudFront cache until they naturally expire or are removed according to the application's retention strategy.

### Can versioning help rollback?

Yes. Multiple immutable asset versions can coexist, allowing old application releases to reference their corresponding assets.

### Is a long TTL always bad?

No. Long TTLs are desirable for immutable content. The dangerous combination is a long TTL with a mutable URL.

## Key Takeaways

- **Version immutable assets instead of routinely invalidating them:** Content-hashed filenames allow long TTLs, high cache efficiency, and safer deployments.
- **Use invalidation for targeted mutable content:** Invalidation is appropriate when URLs must remain stable or stale content must be removed before its normal expiration.
- **Avoid broad invalidations as a deployment habit:** `/*` can unnecessarily destroy useful cached content, increase origin traffic, and reduce CDN effectiveness.
- **Deploy immutable assets before publishing references:** Upload new JavaScript, CSS, images, and other versioned assets before deploying HTML that references them.
- **Design caching across all layers:** CloudFront invalidation does not clear browser, Redis, application, or origin caches; stale-content troubleshooting must identify the actual caching layer.