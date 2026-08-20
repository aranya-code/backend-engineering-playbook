# 04- 502 Bad Gateway Errors

## Overview

A `502 Bad Gateway` from Amazon CloudFront generally means CloudFront could not successfully communicate with the configured origin or could not successfully execute request-processing logic at the edge.

The important distinction is that a CloudFront-generated `502` is different from an origin application returning a normal `502` response.

For example:

```text
Client
  │
  │ HTTPS
  ▼
CloudFront
  │
  ├── Cache lookup
  ├── Cache behavior
  ├── CloudFront Function / Lambda@Edge
  │
  ▼
Origin
  │
  ├── ALB
  ├── EC2
  ├── Nginx
  ├── API Gateway
  └── Application
```

CloudFront documents several common causes of `502`, including origin TLS negotiation failures, invalid or mismatched origin certificates, unsupported protocols or ciphers, incorrect origin ports, DNS resolution failures, Lambda@Edge validation errors, CloudFront Function validation errors, and origin-specific failures. :contentReference[oaicite:0]{index=0}

A production investigation should therefore determine:

1. Whether CloudFront generated the `502`.
2. Whether CloudFront could resolve the origin.
3. Whether CloudFront could establish a TCP connection.
4. Whether TLS negotiation succeeded.
5. Whether the origin accepted the request.
6. Whether edge code failed before the origin request.
7. Whether the origin itself returned a `502`.

## What a CloudFront 502 Means

At a high level:

```text
Viewer
   │
   ▼
CloudFront
   │
   │ cannot successfully communicate with origin
   ▼
502 Bad Gateway
```

CloudFront returns `502` when it cannot serve the requested object because it was unable to connect successfully to the origin. :contentReference[oaicite:1]{index=1}

This differs from a `504`.

| Status | Typical CloudFront interpretation |
|---|---|
| `502` | Connection, TLS, DNS, port, edge-function, or origin communication problem |
| `503` | Service unavailable or origin/service capacity problem |
| `504` | Origin did not respond within the applicable timeout or returned `504` |
| `500` | Origin or CloudFront internal server error |
| `404` | Resource was not found |

A `502` should therefore immediately shift the investigation toward the **CloudFront-to-origin path**.

## Request Lifecycle

For a custom origin, the request path can be understood as:

```mermaid
sequenceDiagram
    participant C as Client
    participant CF as CloudFront
    participant DNS as Public DNS
    participant O as Origin
    participant APP as Application

    C->>CF: HTTPS request
    CF->>DNS: Resolve origin hostname
    DNS-->>CF: Origin IP
    CF->>O: TCP connection
    O-->>CF: TCP connection
    CF->>O: TLS handshake
    O-->>CF: TLS certificate / handshake
    CF->>O: HTTP request
    O->>APP: Forward request
    APP-->>O: Response
    O-->>CF: HTTP response
    CF-->>C: HTTP response
```

A `502` can occur before the HTTP request ever reaches the application.

For example:

```text
CloudFront
    │
    ├── DNS resolution ── X
    │
    ├── TCP connection ── X
    │
    ├── TLS handshake ── X
    │
    ├── HTTP request ───── X
    │
    └── Edge function ──── X
```

This is why checking only Django, FastAPI, or Nginx application logs can be misleading.

## First Diagnostic Step

Reproduce the exact CloudFront URL.

```bash
curl -sv https://cdn.example.com/api/users
```

Inspect only response headers:

```bash
curl -sS -D - -o /dev/null \
  https://cdn.example.com/api/users
```

Record:

- HTTP status
- Response headers
- `X-Cache`
- `Via`
- Request URL
- Hostname
- Timestamp
- HTTP method
- Whether the request is reproducible
- Whether all paths or only specific paths fail

If the response includes:

```text
X-Cache: Error from cloudfront
```

that is useful evidence that CloudFront generated the error rather than simply passing through a normal origin response. AWS specifically documents this behavior for several CloudFront-origin TLS failures. :contentReference[oaicite:2]{index=2}

## Determine Whether the Origin Is Reachable

The first infrastructure question is:

> Can the CloudFront edge reach the configured origin?

CloudFront custom origins require a publicly resolvable DNS name that routes traffic over the internet. :contentReference[oaicite:3]{index=3}

Check DNS from a public network:

```bash
dig origin.example.com
```

Or:

```bash
nslookup origin.example.com
```

Check the complete DNS path:

```bash
dig origin.example.com +short
```

For DNS authority:

```bash
dig example.com NS +short
```

If CloudFront reports `NonS3OriginDnsError`, investigate the origin's public DNS configuration. AWS recommends performing this troubleshooting from a computer connected to the public internet because CloudFront resolves the origin using public DNS. :contentReference[oaicite:4]{index=4}

## DNS Failure

A typical failure looks like:

```text
CloudFront
    │
    │ Resolve origin.example.com
    ▼
Public DNS
    │
    └── No valid answer
            │
            ▼
       502 NonS3OriginDnsError
```

Potential causes include:

- Missing DNS record
- Incorrect CNAME
- Broken delegated zone
- Incorrect nameservers
- DNS provider outage
- Stale or incorrect DNS configuration
- Origin hostname no longer exists

Verify:

```bash
dig origin.example.com A
dig origin.example.com AAAA
dig origin.example.com CNAME
```

Also inspect authoritative nameservers when required:

```bash
dig example.com NS +short
```

Then query an authoritative nameserver:

```bash
dig origin.example.com @ns-123.awsdns-45.com
```

## Private Origins and DNS

A common architectural mistake is assuming that CloudFront can directly connect to an arbitrary private hostname inside a VPC.

The origin must be reachable using the supported CloudFront origin architecture.

For a typical application:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
Public ALB
   │
   ▼
Private EC2 / ECS / EKS
```

The backend instances themselves can remain private while the load balancer provides the externally reachable origin endpoint.

Do not simply point CloudFront at an internal-only hostname and expect normal public CloudFront origin connectivity.

## Verify the Configured Origin

Inspect the distribution:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

Inspect only origins:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.Origins.Items[*].{Id:Id,DomainName:DomainName,OriginPath:OriginPath,ProtocolPolicy:CustomOriginConfig.OriginProtocolPolicy,HTTPPort:CustomOriginConfig.HTTPPort,HTTPSPort:CustomOriginConfig.HTTPSPort}'
```

Verify:

- Origin domain
- Origin path
- HTTP port
- HTTPS port
- Origin protocol policy
- Minimum origin TLS protocol
- Origin request policy
- Origin groups
- Origin access configuration where applicable

A surprisingly large number of `502` incidents are caused by an origin configuration that does not match the actual backend infrastructure.

## Origin Ports

For custom origins, CloudFront can connect using configured HTTP and HTTPS ports.

Typical defaults are:

```text
HTTP  → 80
HTTPS → 443
```

Custom ports are also supported.

If CloudFront is configured for:

```text
HTTPS port: 8443
```

but the origin only listens on:

```text
443
```

the connection can fail.

Check the origin directly:

```bash
curl -vk https://origin.example.com:8443/health
```

On a server where you have access:

```bash
ss -lntp
```

Verify that the expected service is listening.

## Security Groups and Firewalls

For ALB, EC2, or other custom origins, verify that network controls allow CloudFront traffic.

Typical architecture:

```text
CloudFront
    │
    ▼
Internet-facing ALB
    │
    ▼
EC2 / ECS
```

Check:

- ALB security group
- EC2 security group
- Network ACLs
- Host firewall
- WAF rules
- Reverse-proxy restrictions
- Provider-level firewall rules

Do not assume that because the origin works from your laptop, CloudFront can necessarily reach it under the same conditions.

## TLS Between CloudFront and Origin

One of the most important causes of CloudFront `502` is an origin TLS failure.

For HTTPS origins:

```text
CloudFront
    │
    │ TLS handshake
    ▼
Origin
```

The origin certificate must satisfy CloudFront's requirements.

AWS specifically notes that a certificate mismatch between the origin domain and certificate can cause a `502`. :contentReference[oaicite:5]{index=5}

Common problems include:

- Expired certificate
- Self-signed certificate
- Invalid certificate
- Missing intermediate certificate
- Incorrect certificate chain
- Certificate hostname mismatch
- Unsupported TLS protocol
- Unsupported cipher
- Incorrect SNI behavior

## Certificate Hostname Matching

Suppose CloudFront is configured with:

```text
Origin Domain Name:
origin.example.com
```

The origin certificate must cover:

```text
origin.example.com
```

For example:

```text
Subject Alternative Names:
origin.example.com
api.example.com
```

is valid for the origin.

But:

```text
Subject Alternative Names:
other.example.com
```

does not cover:

```text
origin.example.com
```

CloudFront can return `502` when the certificate does not match the configured origin domain. :contentReference[oaicite:6]{index=6}

## Viewer Host Header Versus Origin Hostname

A subtle production issue occurs when CloudFront forwards the viewer `Host` header to the origin.

Suppose:

```text
Viewer:
api.example.com

CloudFront origin:
internal-api.example.net
```

If CloudFront forwards:

```http
Host: api.example.com
```

the origin's TLS configuration may select a certificate for `api.example.com`.

If the origin is instead configured for:

```text
internal-api.example.net
```

the certificate and SNI behavior must be consistent with the request CloudFront makes.

AWS explicitly notes that if an origin request policy forwards the viewer `Host` header, the origin certificate must match that host header; otherwise CloudFront can return `502`. :contentReference[oaicite:7]{index=7}

## Inspect the Certificate With OpenSSL

Test the origin certificate:

```bash
openssl s_client \
  -connect origin.example.com:443
```

For SNI-sensitive configurations:

```bash
openssl s_client \
  -connect origin.example.com:443 \
  -servername origin.example.com
```

Inspect certificate details:

```bash
openssl s_client \
  -connect origin.example.com:443 \
  -servername origin.example.com \
  -showcerts
```

Check:

- Certificate subject
- SANs
- Expiration
- Issuer
- Certificate chain
- TLS version
- Cipher
- SNI behavior

AWS recommends `openssl s_client` as part of troubleshooting CloudFront-to-origin SSL/TLS failures. :contentReference[oaicite:8]{index=8}

## Certificate Chain Problems

An origin may have a certificate that looks valid in a browser but still fail from CloudFront if the server does not present the required certificate chain.

For example:

```text
Server certificate
      │
      ▼
Intermediate CA
      │
      ▼
Root CA
```

The origin must provide the appropriate certificate chain.

A missing intermediate certificate can cause CloudFront to drop the connection and return `502`. :contentReference[oaicite:9]{index=9}

This is particularly common when certificates are manually installed on:

- Nginx
- Apache
- EC2
- Kubernetes ingress
- Custom reverse proxies

## TLS Protocol Compatibility

CloudFront and the origin must agree on supported TLS protocols and cipher suites.

Check the origin:

```bash
openssl s_client \
  -connect origin.example.com:443 \
  -tls1_2
```

If supported by the environment, test specific protocol versions during diagnosis.

Production recommendation:

- Use modern TLS versions.
- Remove obsolete TLS configurations.
- Keep the origin's supported cipher configuration aligned with CloudFront.
- Avoid custom cryptographic restrictions unless there is a clear requirement.

AWS documents unsupported protocol or cipher negotiation as another cause of CloudFront `502`. :contentReference[oaicite:10]{index=10}

## ALB Origin

A common architecture is:

```text
Client
   │
   ▼
CloudFront
   │
   ▼
Application Load Balancer
   │
   ▼
ECS / EC2 / EKS
   │
   ▼
Django / FastAPI
```

If CloudFront returns `502`, verify the ALB independently.

```bash
curl -sv \
  https://alb.example.com/health
```

Check:

- ALB DNS
- Listener
- Listener protocol
- Listener port
- Target group health
- Security groups
- TLS certificate
- Host-based routing
- Path-based routing

A healthy ALB does not necessarily mean CloudFront is correctly communicating with it, because CloudFront may use a different hostname, path, or TLS/SNI configuration.

## ALB Host-Based Routing

Suppose the ALB has:

```text
Host: api.example.com → API target group
Host: admin.example.com → Admin target group
```

CloudFront may send a different `Host` header depending on the origin request configuration.

The result can be:

```text
Expected:
Host: api.example.com

Actual:
Host: origin.example.net
```

The ALB can therefore select a different listener rule.

When debugging, inspect:

- Viewer host
- CloudFront forwarded host
- Origin domain
- ALB listener rules
- Application routing

## Nginx Origin

For Nginx-backed applications:

```text
CloudFront
    ↓
ALB / EC2
    ↓
Nginx
    ↓
Gunicorn / Uvicorn
    ↓
Django / FastAPI
```

Check Nginx:

```bash
sudo nginx -t
```

Inspect logs:

```bash
sudo tail -f /var/log/nginx/error.log
```

and:

```bash
sudo tail -f /var/log/nginx/access.log
```

If CloudFront produces a `502` but Nginx has no corresponding request, the failure likely occurred before Nginx.

If Nginx logs the request and produces an error, continue downstream.

## Django and FastAPI Origins

If the origin is an application server, test it independently.

Django behind Gunicorn:

```bash
curl -sv \
  http://127.0.0.1:8000/health
```

FastAPI:

```bash
curl -sv \
  http://127.0.0.1:8000/health
```

If the local application is healthy but CloudFront returns `502`, inspect the layers between them:

```text
CloudFront
    ↓
ALB
    ↓
Target
    ↓
Nginx
    ↓
Gunicorn/Uvicorn
    ↓
Application
```

The objective is to locate the first failing boundary.

## CloudFront Functions

CloudFront Functions can execute during viewer request and viewer response processing.

A function can cause a `502` if it violates CloudFront's function validation requirements.

For example, AWS documents cases where a CloudFront Function attempts to modify a read-only header, resulting in a `502` after deployment. :contentReference[oaicite:11]{index=11}

If the distribution uses CloudFront Functions:

```bash
aws cloudfront list-functions
```

Inspect a function:

```bash
aws cloudfront describe-function \
  --name "$FUNCTION_NAME"
```

When an error begins immediately after an edge-function deployment, compare:

```text
Previous function version
        │
        ▼
New function version
        │
        ▼
502 begins
```

This temporal relationship is strong evidence that edge processing should be investigated first.

## Lambda@Edge Validation Errors

Lambda@Edge can also result in CloudFront `502` responses when the function response is invalid.

Potential issues include:

- Invalid response structure
- Invalid header values
- Invalid status
- Incorrect body encoding
- Invalid function output
- Incorrect event handling

AWS explicitly identifies Lambda validation errors as a CloudFront `502` cause. :contentReference[oaicite:12]{index=12}

If Lambda@Edge is involved, inspect:

- CloudWatch logs
- Function version
- Trigger event
- Returned object structure
- Header modifications
- Deployment timing

## API Gateway Origin

API Gateway can also be used behind CloudFront.

Typical architecture:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
API Gateway
  │
  ▼
Lambda / Backend
```

If CloudFront reports `502`, test API Gateway independently:

```bash
curl -sv \
  https://api-id.execute-api.region.amazonaws.com/stage/health
```

Check:

- API Gateway endpoint
- Stage
- Route
- Integration
- Custom domain
- TLS configuration
- Origin configuration
- CloudFront path mapping

A CloudFront error should not automatically be attributed to API Gateway without independently verifying the API endpoint.

## Origin Protocol Policy

CloudFront controls how it communicates with the origin.

Typical policies include:

```text
HTTP only
HTTPS only
Match viewer
```

For production APIs, HTTPS between CloudFront and the origin is generally preferable.

A mismatch can produce connection failures.

For example:

```text
CloudFront:
HTTPS → origin:443

Origin:
HTTP service only
```

or:

```text
CloudFront:
HTTP → origin:80

Infrastructure:
HTTPS-only
```

Inspect:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.Origins.Items[*].CustomOriginConfig'
```

## Origin Timeout Versus 502

Do not confuse connection failure with slow origin responses.

CloudFront's origin connection and response timeout settings affect failure behavior.

For example:

```text
CloudFront
    │
    │ cannot establish connection
    ▼
502
```

versus:

```text
CloudFront
    │
    │ connection established
    ▼
Origin
    │
    │ application is too slow
    ▼
504
```

AWS documents `504` for cases where the origin does not respond before the applicable timeout or returns `504`. :contentReference[oaicite:13]{index=13}

This distinction is useful during incident triage.

## Origin Connection Settings

Inspect the configured origin connection settings:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.Origins.Items[*].{Id:Id,Domain:DomainName,HTTPPort:CustomOriginConfig.HTTPPort,HTTPSPort:CustomOriginConfig.HTTPSPort,Protocol:CustomOriginConfig.OriginProtocolPolicy,MinTLS:CustomOriginConfig.OriginSSLProtocols}'
```

CloudFront supports configurable connection timeout and connection attempts for custom origins. AWS documents a default connection timeout of 10 seconds and up to three connection attempts. :contentReference[oaicite:14]{index=14}

Do not increase timeout values blindly to hide a failing origin.

Timeout tuning should be based on:

- Application latency
- Network characteristics
- Failure behavior
- User experience
- Origin capacity

## Origin Groups and Failover

If the distribution uses origin groups:

```text
                ┌── Primary Origin
CloudFront ─────┤
                └── Secondary Origin
```

verify:

- Primary origin health
- Failover criteria
- Secondary origin configuration
- Secondary DNS
- TLS certificate
- Data consistency

An incorrectly configured secondary origin can turn a recoverable primary-origin failure into a complete outage.

## Check Origin Logs

A critical diagnostic question is:

> Did the origin receive the request?

If the answer is **no**, investigate:

- DNS
- Network
- Port
- TLS
- CloudFront edge processing
- Origin configuration

If the answer is **yes**, inspect:

- HTTP response
- Nginx
- ALB
- Application logs
- Backend dependencies

This gives a useful decision tree:

```mermaid
flowchart TD
    A[CloudFront returns 502] --> B{Did origin receive request?}

    B -->|No| C{Can CloudFront resolve origin?}
    C -->|No| D[Fix DNS]
    C -->|Yes| E{Can CloudFront connect?}

    E -->|No| F[Check port firewall security groups]
    E -->|Yes| G{Does TLS handshake succeed?}

    G -->|No| H[Fix certificate TLS SNI or cipher]
    G -->|Yes| I[Check edge processing]

    B -->|Yes| J[Inspect ALB Nginx application]
    J --> K[Identify origin-side failure]
```

## Check CloudFront Distribution Configuration

Use:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

Important fields include:

| Configuration | Why it matters |
|---|---|
| `DomainName` | Determines the origin endpoint |
| `OriginPath` | Changes the effective request path |
| `OriginProtocolPolicy` | Controls HTTP/HTTPS communication |
| `HTTPPort` | Controls origin HTTP connection |
| `HTTPSPort` | Controls origin HTTPS connection |
| `OriginSslProtocols` | Controls supported origin TLS protocols |
| `OriginRequestPolicyId` | Controls forwarded request information |
| Cache behavior | Determines which origin handles the request |
| Functions/Lambda@Edge | May modify or reject requests |
| Origin groups | May determine failover behavior |

## Use AWS CLI for Fast Triage

A compact distribution inspection:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.{Status:Status,DomainName:DomainName,Enabled:DistributionConfig.Enabled}'
```

Inspect origins:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.Origins.Items[*].{Id:Id,Domain:DomainName,Path:OriginPath}'
```

Inspect origin protocol settings:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.Origins.Items[*].CustomOriginConfig'
```

Inspect error configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.CustomErrorResponses'
```

## Compare CloudFront With the Origin

CloudFront:

```bash
curl -sv \
  https://cdn.example.com/api/health
```

Origin:

```bash
curl -sv \
  https://origin.example.com/api/health
```

If the origin requires a particular `Host` header:

```bash
curl -sv \
  https://origin.example.com/api/health \
  -H 'Host: api.example.com'
```

This is particularly useful when ALB or Nginx routing depends on the host.

## TLS Comparison

Test the origin directly:

```bash
openssl s_client \
  -connect origin.example.com:443 \
  -servername origin.example.com
```

Then verify:

```text
Certificate valid?
Certificate expired?
SAN matches?
Chain complete?
TLS protocol supported?
Cipher supported?
SNI correct?
```

If this test fails, fix the origin TLS configuration before changing unrelated CloudFront settings.

## Cached 502 Responses

CloudFront can cache certain origin `5xx` responses, including `502`, depending on the configuration. AWS documents `502` among the HTTP `4xx`/`5xx` responses CloudFront can cache. :contentReference[oaicite:15]{index=15}

This creates an important incident pattern:

```text
Origin failure
    ↓
CloudFront receives 502
    ↓
502 cached
    ↓
Origin fixed
    ↓
CloudFront may still serve cached error
```

Therefore, after fixing an origin problem, determine whether the failing response can still be cached.

Inspect custom error configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.CustomErrorResponses'
```

## Invalidate After Fixing the Origin

If an error response is cached and immediate recovery is required, invalidate the affected path.

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/api/health"
```

For emergency broad recovery:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*"
```

Use broad invalidation carefully. It should not become the default response to every origin incident.

## Monitoring 502 Errors

A production monitoring strategy should distinguish:

```text
Viewer errors
    │
    ├── 4xx
    └── 5xx
          │
          ├── 500
          ├── 502
          ├── 503
          └── 504
```

Track at least:

- CloudFront `5xx` error rate
- `502` rate
- Origin health
- ALB target health
- Application latency
- TLS certificate expiration
- DNS health
- Deployment events
- Edge-function deployments

A sudden `502` increase immediately following a certificate, DNS, origin, or edge-function deployment is particularly significant.

## Production Incident Workflow

### Confirm the Failure

```bash
curl -sS -D - -o /dev/null \
  https://cdn.example.com/api/health
```

Confirm:

```text
HTTP 502
```

### Determine Whether CloudFront Generated It

Inspect:

```text
X-Cache
Via
Response headers
```

Look for evidence such as:

```text
X-Cache: Error from cloudfront
```

### Inspect the Origin

```bash
dig origin.example.com
```

Then:

```bash
curl -sv \
  https://origin.example.com/api/health
```

### Check TLS

```bash
openssl s_client \
  -connect origin.example.com:443 \
  -servername origin.example.com
```

### Check CloudFront Configuration

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

Verify:

- Origin hostname
- Port
- Protocol
- TLS
- Origin path
- Request policies
- Edge functions

### Check Infrastructure

Verify:

- Security groups
- Firewalls
- ALB
- Target health
- Nginx
- Application process
- Kubernetes ingress if applicable

### Check Logs

Trace:

```text
CloudFront
    ↓
ALB
    ↓
Nginx
    ↓
Application
```

Identify the first layer that does not behave as expected.

### Check Cached Errors

If the origin is now healthy but CloudFront still returns `502`, determine whether an error response is cached.

### Invalidate Only If Appropriate

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/api/health"
```

### Verify From the Public Internet

```bash
curl -fsS \
  https://cdn.example.com/api/health \
  -o /dev/null
```

Then monitor the `502` rate to ensure the incident is actually resolved.

## Common Production Pitfalls

### Checking Only Application Logs

A TLS handshake failure occurs before Django or FastAPI receives the request.

**Avoid it:** investigate DNS, TCP, TLS, and origin connectivity before assuming an application bug.

### Using the Viewer Certificate to Debug Origin TLS

There are two different TLS connections:

```text
Viewer ──TLS──> CloudFront
CloudFront ──TLS──> Origin
```

A valid viewer certificate does not prove that the origin certificate is valid.

**Avoid it:** inspect the origin certificate independently.

### Ignoring SNI

An origin hosting multiple domains may return different certificates depending on SNI.

**Avoid it:** use:

```bash
openssl s_client \
  -connect origin.example.com:443 \
  -servername origin.example.com
```

### Forgetting Host Header Forwarding

Forwarding the viewer `Host` header can change both ALB routing and origin TLS behavior.

**Avoid it:** explicitly document the expected host at every hop.

### Changing TLS Settings Without Testing

Randomly changing TLS policies can mask the actual problem and weaken security.

**Avoid it:** verify certificate, hostname, chain, protocol, and cipher compatibility first.

### Assuming ALB Health Means CloudFront Health

An ALB can be healthy while CloudFront is unable to connect because of:

- DNS
- certificate mismatch
- port configuration
- network restrictions
- origin hostname mismatch

**Avoid it:** test the exact CloudFront-to-origin configuration.

### Increasing Timeouts to Fix Connection Failures

Timeouts primarily address slow or incomplete responses, not certificate or DNS failures.

**Avoid it:** distinguish `502` connection failures from `504` timeout behavior.

### Invalidating Before Fixing the Origin

An invalidation cannot repair:

```text
Broken TLS
Broken DNS
Closed port
Invalid certificate
Unhealthy origin
```

**Avoid it:** fix the underlying origin problem first.

### Ignoring Edge Code

If the incident starts immediately after a CloudFront Function or Lambda@Edge deployment, edge logic is a high-priority suspect.

**Avoid it:** correlate deployment timestamps with error rates and inspect edge-function logs/configuration.

## Security Considerations

Origin connectivity should not be solved by unnecessarily opening infrastructure.

Prefer:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
Controlled origin
   │
   ▼
Private application targets
```

For ALB-based architectures:

- Restrict backend security groups appropriately.
- Use HTTPS to the origin.
- Maintain valid publicly trusted certificates.
- Avoid obsolete TLS protocols.
- Do not disable certificate validation to bypass a `502`.
- Keep origin infrastructure protected even when CloudFront is the public entry point.

A common anti-pattern is:

```text
502
 ↓
Open firewall to everyone
 ↓
Problem disappears
```

This may restore connectivity while creating a much larger security problem.

## High Availability Considerations

For critical applications, avoid a single fragile origin dependency.

A resilient architecture may use:

```mermaid
flowchart LR
    C[Clients] --> CF[CloudFront]

    CF --> P[Primary Origin]
    CF --> S[Secondary Origin]

    P --> P1[Application Fleet]
    S --> S1[Application Fleet]
```

Consider:

- Multiple application instances
- Multi-AZ ALB deployment
- Healthy target groups
- Origin failover where appropriate
- Automated certificate renewal
- DNS health monitoring
- Infrastructure-as-code
- Deployment rollback procedures

High availability does not eliminate configuration failures. It reduces the impact of individual infrastructure failures.

## Disaster Recovery Considerations

For CloudFront-backed APIs, disaster recovery should include more than the CDN distribution.

Document recovery procedures for:

- CloudFront distribution
- DNS
- Origin certificates
- ALB
- Application infrastructure
- Database
- Secrets
- Edge functions
- Infrastructure-as-code

Store CloudFront configuration in version-controlled infrastructure definitions where possible.

A recovery process should be reproducible:

```text
Infrastructure definition
        ↓
Origin infrastructure
        ↓
TLS configuration
        ↓
CloudFront configuration
        ↓
DNS
        ↓
Smoke tests
```

## Interview Perspective

A strong answer to:

> "CloudFront is returning 502. How would you troubleshoot it?"

should not begin with "restart the server."

A production-oriented answer is:

1. Reproduce the request and inspect CloudFront response headers.
2. Determine whether CloudFront generated the `502` or forwarded it from the origin.
3. Verify public DNS resolution for the configured origin.
4. Verify the origin port and network reachability.
5. Test the origin directly.
6. If HTTPS is used, inspect the origin certificate, SANs, chain, SNI, TLS protocols, and ciphers.
7. Check whether the forwarded `Host` header changes routing or certificate selection.
8. Check ALB, Nginx, and application logs to determine whether the request reached the origin.
9. Check CloudFront Functions and Lambda@Edge if deployed.
10. Inspect origin groups and failover configuration if applicable.
11. Check whether CloudFront has cached the `502`.
12. Fix the underlying issue and invalidate the affected path only when necessary.
13. Verify the recovery from the public CloudFront endpoint.

The core mental model is:

```text
502
 │
 ├── DNS?
 │
 ├── TCP?
 │
 ├── Port?
 │
 ├── TLS?
 │    ├── Certificate?
 │    ├── SAN?
 │    ├── Chain?
 │    ├── SNI?
 │    └── Protocol/Cipher?
 │
 ├── Edge Function?
 │
 ├── Origin?
 │    ├── ALB?
 │    ├── Nginx?
 │    └── Application?
 │
 └── Cached error?
```

## Key Takeaways

- **CloudFront `502` usually indicates an origin communication problem:** investigate DNS, connectivity, ports, TLS, edge processing, and origin configuration before debugging application code.
- **Origin TLS is a major failure boundary:** verify certificate validity, hostname/SAN matching, certificate chain, SNI, TLS protocols, and supported ciphers.
- **Trace the request across every layer:** determine whether CloudFront reached the ALB, Nginx, Django/FastAPI, or other origin before changing configuration.
- **Distinguish `502` from `504`:** connection and TLS failures commonly produce `502`, while slow or incomplete origin responses are typically associated with `504`.
- **Fix the root cause before invalidating caches:** CloudFront can cache `502` responses, so verify cache state after the origin is repaired and invalidate only when appropriate.