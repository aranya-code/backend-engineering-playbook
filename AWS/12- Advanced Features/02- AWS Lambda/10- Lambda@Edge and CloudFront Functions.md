# 10- Lambda@Edge and CloudFront Functions

## Overview

Amazon CloudFront supports lightweight code execution at the edge of its global content delivery network (CDN). This allows applications to inspect or modify HTTP requests and responses close to viewers, reducing unnecessary origin requests and enabling request-level logic before traffic reaches an application backend.

Two services address different edge-computing requirements:

- **CloudFront Functions:** Lightweight JavaScript functions designed for high-volume, latency-sensitive HTTP request and response transformations.
- **Lambda@Edge:** Lambda functions associated with specific CloudFront distribution events, supporting more complex processing and additional runtime capabilities.

Both can improve performance and implement edge-level controls, but they have different execution models, supported events, runtime capabilities, deployment workflows, and operational constraints.

For backend engineers, the key architectural decision is whether logic belongs at the CDN edge, in an origin-facing Lambda function, or in the core application service.

## How Edge Computing Works with CloudFront

CloudFront caches content at edge locations and forwards requests to an origin when required. Edge functions can execute at defined points in the request lifecycle.

Typical use cases include:

- URL normalization and redirects.
- Request-header manipulation.
- Lightweight access checks.
- Cache-key normalization.
- Request routing and origin selection.
- Response-header security policies.
- Device or language-based content selection.

### Request lifecycle

```mermaid
flowchart TD
    A[Viewer Request] --> B[CloudFront Edge Location]
    B --> C{Viewer Request Function?}
    C -->|CloudFront Function| D[Normalize or Inspect Request]
    C -->|None| E[Continue Processing]
    D --> E
    E --> F{Cache Hit?}
    F -->|Yes| G[Cached Response]
    F -->|No| H{Origin Request Function?}
    H -->|Lambda@Edge| I[Origin Request Processing]
    H -->|None| J[Origin]
    I --> J
    J --> K[Origin Response]
    K --> L{Origin Response Function?}
    L -->|Lambda@Edge| M[Modify Origin Response]
    L -->|None| N[Continue Response]
    M --> N
    N --> O[Viewer Response Processing]
    O --> P[Viewer]
    G --> P
```

The actual invocation path depends on the function associations and cache behavior configured on the CloudFront distribution. Not every request invokes every event type.

**Important distinction:** A viewer request occurs when CloudFront receives a request from a viewer. An origin request occurs when CloudFront forwards a request to the origin. Cache behavior determines whether an origin request is needed.

This distinction affects correctness and cost. For example, origin-request logic generally runs only when CloudFront needs to contact the origin, whereas viewer-request logic can run for every applicable viewer request.

## CloudFront Functions

CloudFront Functions execute lightweight JavaScript code within CloudFront's edge infrastructure. They are designed for short-running operations that can be completed with limited execution resources.

### How they work

A function is associated with a CloudFront distribution behavior and an eligible event type. When CloudFront reaches that event, it executes the published function against the request or response object.

CloudFront Functions support:

- Viewer request events.
- Viewer response events.
- Request and response manipulation through the CloudFront Functions event model.
- Lightweight authentication-related checks and request validation.
- URI normalization, redirects, and header transformations.

They are not general-purpose Lambda functions and do not expose the full Lambda execution environment.

### Appropriate use cases

Use CloudFront Functions for:

- Redirecting legacy URLs.
- Normalizing paths and query parameters.
- Rewriting a URI before cache lookup.
- Adding or removing simple headers.
- Implementing lightweight viewer-request checks.
- Selecting a URL or behavior based on request attributes.

Avoid using them for workloads that require database access, arbitrary network calls, filesystem operations, heavy computation, or complex application dependencies.

### Example: URL normalization

The following function redirects a legacy route to a canonical route while preserving the query string.

```javascript
function handler(event) {
    var request = event.request;
    var uri = request.uri;

    if (uri === "/legacy-products") {
        var query = request.querystring || {};
        var queryString = Object.keys(query)
            .map(function (key) {
                var value = query[key];

                if (value.multiValue) {
                    return value.multiValue.map(function (item) {
                        return encodeURIComponent(key) + "=" +
                            encodeURIComponent(item.value);
                    }).join("&");
                }

                return encodeURIComponent(key) + "=" +
                    encodeURIComponent(value.value);
            })
            .join("&");

        return {
            statusCode: 301,
            statusDescription: "Moved Permanently",
            headers: {
                location: {
                    value: "/products" +
                        (queryString ? "?" + queryString : "")
                }
            }
        };
    }

    return request;
}
```

This is an illustrative transformation. Before deploying it, verify the exact CloudFront Functions event structure and the desired query-string encoding behavior, including duplicate keys and parameters without values.

For a permanent redirect, confirm that the destination is genuinely canonical. Browsers and intermediary caches can retain permanent redirects.

## Lambda@Edge

Lambda@Edge allows Lambda functions to execute in response to CloudFront events. It supports more complex edge processing than CloudFront Functions, including selected use cases that require the Lambda runtime and its broader programming capabilities.

Lambda@Edge is useful when edge logic needs capabilities that CloudFront Functions do not provide, subject to Lambda@Edge's supported runtime, event, and deployment constraints.

### Supported CloudFront event types

| Event type | When it executes | Typical use |
|---|---|---|
| Viewer request | Before CloudFront evaluates the cache key | Authentication checks, request rewriting, request validation |
| Origin request | Before forwarding a cache miss or applicable request to the origin | Dynamic origin selection, origin-facing request manipulation |
| Origin response | After receiving a response from the origin | Origin-response transformations and metadata adjustments |
| Viewer response | Before returning a response to the viewer | Response-header changes and response transformations |

Not every Lambda@Edge event supports the same request or response operations. Payload restrictions and event-specific rules apply.

For example, origin-request and origin-response functions can access origin-facing context that is unavailable at the viewer-request stage. The choice of event should follow the data needed by the function and the desired effect on cache behavior.

### Important deployment constraints

Lambda@Edge differs from a standard regional Lambda deployment:

- The function must be created in **US East (N. Virginia), `us-east-1`**.
- A published numbered Lambda version is associated with the CloudFront distribution, not `$LATEST` or an alias.
- The function must meet Lambda@Edge's runtime and configuration requirements.
- Lambda@Edge has restrictions on supported triggers, networking, environment configuration, and other Lambda features.
- Deployment and replication to CloudFront edge locations take time.
- Changes to the association can require distribution deployment to complete before the new behavior is active.

Do not assume that every feature supported by a normal Lambda function is available in Lambda@Edge. Check the current AWS compatibility documentation before designing around VPC access, environment variables, layers, container images, extensions, or other advanced capabilities.

Reference: [Lambda@Edge restrictions and limitations](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-at-the-edge-function-restrictions.html).

````markdown
## CloudFront Functions versus Lambda@Edge

The choice depends on execution requirements, event location, latency sensitivity, and operational complexity.

| Capability | CloudFront Functions | Lambda@Edge |
|---|---|---|
| Primary purpose | Lightweight, high-scale edge logic | More complex edge processing |
| Language | JavaScript | Supported Node.js and Python runtimes |
| Event types | Viewer request, viewer response, and supported connection-request use cases | Viewer request, viewer response, origin request, origin response |
| Network access | No general network access | Network access is supported, subject to restrictions |
| Filesystem access | No | Available within Lambda's supported execution model |
| Request body access | No | Supported with the event's body-inclusion option and applicable size limits |
| Execution latency | Designed for submillisecond execution | Higher overhead; execution duration can be up to 30 seconds |
| Maximum function code size | 10 KB | 50 MB compressed, including libraries |
| Maximum memory | 2 MB | Event-dependent; up to 10 GB for origin events |
| CloudFront KeyValueStore | Supported with JavaScript runtime 2.0 | Not supported |
| VPC attachment | Not applicable | Not supported |
| Deployment | Managed through CloudFront | Created in `us-east-1`, published, then associated with CloudFront |
| Operational complexity | Lower | Higher |

The values above describe documented service limits and capabilities; confirm current quotas and restrictions before designing around them.

References: [CloudFront Functions versus Lambda@Edge](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions-choosing.html), [CloudFront Functions restrictions](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-function-restrictions.html), and [Lambda@Edge restrictions](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-at-the-edge-function-restrictions.html).

### Decision examples

Choose CloudFront Functions when:

- A redirect can be decided from the URL and request metadata.
- A request needs simple normalization before cache lookup.
- A small, frequently executed transformation must operate at very high request volume.
- A lightweight edge policy does not need a network call.

Choose Lambda@Edge when:

- The function needs supported network access.
- Origin selection requires more complex logic.
- A request or response transformation needs body access within the supported limits.
- The logic requires Python or Node.js runtime capabilities unavailable in CloudFront Functions.

Choose a regional Lambda behind API Gateway or another origin when the operation requires application-level business logic, database transactions, complex authorization, or centralized service integration. Edge execution is not automatically the best location for every request-processing task.

## Cache Behavior and Function Placement

Edge functions can affect caching, origin load, correctness, and security. The event association must be chosen based on when the information becomes available and whether the transformation should affect the cache key.

### Viewer request

A viewer-request function runs before CloudFront performs its cache lookup.

This is useful for:

- Canonicalizing request URIs.
- Redirecting legacy paths.
- Rewriting paths based on request attributes.
- Rejecting invalid requests before cache processing.

A viewer-request rewrite can change which cache object CloudFront looks up. If two different incoming URLs are normalized to the same URI, they can share a cache entry, provided the rest of the cache key is also equivalent.

Do not normalize away a query parameter, header, or cookie that changes the response content unless the cache policy and application semantics explicitly support that behavior.

### Origin request

An origin-request Lambda@Edge function runs when CloudFront forwards an applicable request to the origin.

It can be useful for:

- Selecting an origin based on request metadata.
- Modifying origin-facing headers.
- Routing cache misses to different backend services.
- Applying transformations that do not need to execute for every cache hit.

Because the function is associated with an origin-facing event, it generally does not run for a normal cache hit. This can reduce invocation volume, but it also means the logic cannot be relied upon to run for every viewer request.

### Response events

Origin-response functions can transform responses received from the origin. Viewer-response functions can transform responses before CloudFront returns them to viewers, subject to event-specific restrictions.

A key limitation is that a Lambda@Edge viewer-response function cannot change the HTTP status code. Some viewer-response events also do not occur for certain CloudFront-generated responses or status codes.

Use the correct event type for the transformation, and verify the behavior against the current event documentation.

Reference: [How Lambda@Edge works with requests and responses](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-edge-event-request-response.html).

## Practical Example: Lambda@Edge Redirect

The following Python example redirects a legacy URL to a canonical path. It demonstrates the Lambda@Edge event structure and response format.

```python
def lambda_handler(event, context):
    request = event["Records"][0]["cf"]["request"]
    uri = request["uri"]

    if uri == "/legacy-products":
        querystring = request.get("querystring", "")

        location = "/products"
        if querystring:
            location = f"{location}?{querystring}"

        return {
            "status": "301",
            "statusDescription": "Moved Permanently",
            "headers": {
                "location": [
                    {
                        "key": "Location",
                        "value": location,
                    }
                ],
                "cache-control": [
                    {
                        "key": "Cache-Control",
                        "value": "max-age=3600",
                    }
                ],
            },
        }

    return request
```

### Engineering considerations

- The function expects the Lambda@Edge CloudFront event format, not an API Gateway event.
- The query string is already represented in the CloudFront request structure. Validate encoding and parameter handling for the application's actual requirements.
- A `301` redirect may be cached by browsers and intermediaries. Use `302` or `307` when the redirect is temporary.
- Do not construct redirect destinations directly from untrusted host or query parameters without validation; otherwise, an open-redirect vulnerability may result.
- The function should be tested with real event fixtures covering canonical paths, query strings, unexpected methods, and malformed inputs.

## CloudFront KeyValueStore

CloudFront KeyValueStore provides a managed key-value data store that CloudFront Functions can access when using JavaScript runtime 2.0.

It is useful when a lightweight edge function needs dynamic configuration without embedding every value directly in the function code.

Possible use cases include:

- Redirect mappings.
- Feature flags.
- Routing configuration.
- Small sets of edge-managed lookup data.

KeyValueStore is not a general-purpose database. It is not a replacement for DynamoDB, Redis, or an application database when the workload requires transactions, complex queries, or application-managed persistence.

### When it helps

Without a separate data store, changing a mapping embedded in code generally requires publishing an updated function and managing the associated deployment.

With KeyValueStore, supported data updates can be managed independently of the function code. This can simplify operational changes to redirect tables or routing configuration.

The function still needs explicit handling for missing keys, malformed values, and safe fallback behavior.

Reference: [CloudFront KeyValueStore](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/kvs-with-functions.html).

## Security and Authorization

Edge functions execute in a globally distributed request path. An incorrect authorization rule or unsafe transformation can affect traffic across many locations, so changes should be treated as production application changes.

### Security practices

- Validate input and normalize data before using it in routing decisions.
- Avoid open redirects by restricting destinations to known hosts and paths.
- Do not trust viewer-supplied headers as proof of identity.
- Use cryptographic verification when implementing signed tokens or requests.
- Avoid embedding secrets in function code or distribution configuration.
- Keep authorization logic consistent with the origin's security model.
- Test failure behavior and ensure that malformed requests do not bypass authorization.
- Use least-privilege IAM permissions for Lambda@Edge deployment and execution.
- Review logs for accidental exposure of tokens, cookies, and personal data.

### Edge authentication versus application authorization

A lightweight edge check can reject obviously invalid requests before they reach the origin. However, it should not replace authoritative authorization for sensitive operations unless the complete authentication and authorization design explicitly supports that model.

For example, a function that checks for the presence of an `Authorization` header does not prove that the token is valid. The origin or a trusted authentication component must validate the token's signature, expiration, issuer, audience, and relevant permissions.

Similarly, an edge cache must not serve a user-specific response to another user because the cache key ignores the identity or authorization context.

## IAM and Deployment Permissions

Lambda@Edge requires both permissions to configure the distribution association and an execution role that Lambda can assume.

The execution role's trust policy must allow the Lambda service principals required by Lambda@Edge, including `lambda.amazonaws.com` and `edgelambda.amazonaws.com`.

The deployment identity needs the appropriate Lambda and CloudFront permissions to publish a function version and update the distribution. The initial configuration may also require permission to create the service-linked role used by Lambda@Edge.

Do not grant broad administrator permissions to the runtime execution role merely to make deployment succeed. Deployment permissions and runtime permissions serve different purposes and should be separated.

Reference: [Set up IAM permissions and roles for Lambda@Edge](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-edge-permissions.html).

## Deployment Workflow

CloudFront Functions and Lambda@Edge have different deployment workflows.

### CloudFront Functions

A typical workflow is:

1. Create the function.
2. Implement and test the JavaScript handler.
3. Publish the function to the `LIVE` stage.
4. Associate the published function with the desired CloudFront distribution behavior.
5. Wait for the distribution deployment to complete.
6. Validate the behavior using representative HTTP requests.
7. Monitor errors and function compute utilization.

Publishing a function and associating it with a distribution are separate operations. A successful function test does not prove that the production distribution is using the intended version.

### Lambda@Edge

A typical workflow is:

1. Create the Lambda function in `us-east-1`.
2. Use a supported runtime and ZIP deployment package.
3. Configure the execution role and required permissions.
4. Test the function using representative CloudFront event fixtures.
5. Publish a numbered Lambda version.
6. Associate that version with a CloudFront distribution behavior and event.
7. Wait for CloudFront distribution deployment and function replication.
8. Run end-to-end tests against the distribution.
9. Monitor invocation errors, latency, and distribution behavior.

Changes to `$LATEST` do not update a published version already associated with CloudFront. Publish a new version and update the association when releasing code changes.

### Operational considerations

- Distribution updates can take time to deploy globally.
- A successful control-plane API call does not necessarily mean the new configuration is already active everywhere.
- Maintain a known-good version and a rollback procedure.
- Verify that the intended function association is active after deployment.
- Avoid frequent production updates that change unrelated distribution settings.
- Use Infrastructure as Code where practical to manage function associations and distribution configuration consistently.

## Monitoring and Troubleshooting

Edge-function failures can affect requests before they reach the application origin. Diagnosis should distinguish function execution failures from CloudFront configuration problems and origin failures.

### Common failure scenarios

| Symptom | Possible cause | Diagnostic approach |
|---|---|---|
| HTTP 502 after deployment | Invalid event response, malformed headers, or unsupported response mutation | Inspect function logs and validate the returned event structure |
| Redirect loop | Redirect rule repeatedly matches the destination path | Test canonicalization and redirect destinations |
| Incorrect cache results | Cache key ignores a response-varying request attribute | Review cache policy and URI/header/cookie transformations |
| Lambda@Edge association fails | Wrong Region, unqualified function ARN, or unsupported configuration | Verify `us-east-1`, published version ARN, and restrictions |
| Function changes are not visible | Distribution deployment is incomplete or the old version remains associated | Inspect distribution status and function associations |
| Origin request function is not invoked | Cache hit prevents the origin request | Confirm cache behavior and test a cache miss |
| High latency or errors | Excessive edge logic, network dependency failure, or malformed request processing | Inspect execution metrics and test each dependency independently |

### CloudFront Functions monitoring

Monitor:

- Function invocations.
- Function errors.
- Compute utilization.
- Distribution-level HTTP status codes.
- Cache hit ratio and origin request volume.

Compute utilization helps identify functions that are approaching their execution budget. A high value should trigger code review and testing with representative inputs.

### Lambda@Edge monitoring

Monitor:

- Lambda invocation errors and duration.
- CloudFront HTTP 5xx responses.
- Origin latency and error rates.
- Distribution deployment state.
- Logs in the relevant AWS Regions.
- Concurrency and throttling where applicable.

Lambda@Edge execution and logs are distributed across AWS Regions. Investigations may require checking the Regions where the function was invoked rather than looking only in `us-east-1`.

Reference: [CloudFront monitoring](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/monitoring-using-cloudwatch.html).

## Cost and Performance Considerations

CloudFront Functions and Lambda@Edge have different pricing models and operational profiles. Evaluate the current regional pricing and applicable CloudFront pricing before choosing a design.

CloudFront Functions are generally suited to high-volume, lightweight processing. Lambda@Edge is appropriate when additional runtime capabilities justify its greater execution and deployment overhead.

Consider the following cost drivers:

- Number of viewer requests.
- Frequency of cache misses and origin-facing function invocations.
- Function execution duration and memory allocation.
- Logging volume and retention.
- Additional network or origin requests caused by function logic.
- Cache hit ratio and the resulting origin load.

A viewer-request function may run for every applicable request, while an origin-request function usually runs only when CloudFront forwards the request to the origin. The difference can be material for high-traffic distributions.

Do not add a network call to every viewer request merely to avoid a small amount of application logic at the origin. The added latency, dependency failure modes, and invocation cost may outweigh the benefit.

## Common Architectural Mistakes

### Using Lambda@Edge for ordinary backend processing

A database-backed CRUD operation or complex business transaction usually belongs in a regional backend service.

**Better approach:** Use CloudFront for caching and request-level transformations, then route application requests to API Gateway, an Application Load Balancer, or another suitable origin.

### Running authorization only at the edge

A lightweight edge check can be useful, but trusting an unverified header or token can create a security bypass.

**Better approach:** Validate identity and permissions using a trusted authentication design, and ensure that cache behavior cannot expose protected responses.

### Choosing the wrong event type

Viewer-request and origin-request events run at different points in the cache lifecycle.

**Better approach:** Define whether the transformation must happen before cache lookup, only when contacting the origin, or before returning a response. Test cache hits and misses separately.

### Treating edge code as a normal regional Lambda function

Lambda@Edge does not support every standard Lambda feature, and CloudFront Functions have a much more restricted runtime.

**Better approach:** Verify the supported runtime, event type, networking, environment configuration, deployment package, and other restrictions before implementation.

### Ignoring cache-key correctness

If a response varies by language, tenant, authorization, or another request attribute, an incomplete cache key can return the wrong content.

**Better approach:** Use cache policies and request normalization deliberately. Do not remove response-varying inputs from the cache key without a safe alternative.

## Production Readiness Checklist

- [ ] Select CloudFront Functions for lightweight request transformations and Lambda@Edge only when its additional capabilities are required.
- [ ] Choose the event type based on the cache lifecycle and the data needed by the function.
- [ ] Validate request inputs and avoid unsafe redirects.
- [ ] Verify cache-key correctness for content that varies by request attributes.
- [ ] Test success, failure, cache-hit, and cache-miss paths.
- [ ] Confirm supported runtimes and service restrictions.
- [ ] Use least-privilege IAM permissions.
- [ ] Deploy through version-controlled configuration and a repeatable release process.
- [ ] Wait for distribution deployment to complete before declaring a release successful.
- [ ] Monitor function errors, compute utilization, latency, cache hit ratio, and HTTP 5xx responses.
- [ ] Keep a rollback procedure and a known-good published version.
- [ ] Review current service quotas and pricing for expected request volume.

## Key Takeaways

- CloudFront Functions are best for lightweight, synchronous JavaScript transformations at viewer-facing events; Lambda@Edge supports more complex request and response processing.
- Event placement affects caching, invocation frequency, origin load, and correctness; viewer-request and origin-request functions are not interchangeable.
- Lambda@Edge must be created in `us-east-1`, published as a numbered version, and deployed with the required IAM permissions and supported configuration.
- Edge logic must account for security, cache-key correctness, redirects, event-specific response restrictions, and distributed deployment behavior.
- Use edge functions for CDN-level concerns and keep complex business operations in an appropriate backend service unless a clearly justified edge requirement exists.