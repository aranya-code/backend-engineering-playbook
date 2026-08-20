# 12- TLS and SSL Errors

## Overview

TLS errors in CloudFront occur when HTTPS negotiation fails between a client and CloudFront, or between CloudFront and an origin.

For a standard CloudFront HTTPS request, there can be two distinct TLS connections:

```text
Client
   │
   │ TLS connection
   ▼
CloudFront
   │
   │ TLS connection
   ▼
HTTPS Origin
```

These connections are independently configured and must be diagnosed separately.

The most common mistake is treating every TLS problem as a certificate problem. In production, TLS failures can originate from:

- Incorrect CloudFront alternate domain names
- Certificate hostname mismatches
- Incorrect certificate region
- Expired or invalid certificates
- Unsupported TLS versions
- Incorrect origin protocol configuration
- Origin certificate problems
- SNI compatibility issues
- DNS pointing to the wrong distribution
- Incomplete certificate chains
- Private or inaccessible origins
- TLS policy incompatibilities
- Application or load balancer configuration

The first diagnostic question should therefore be:

> **Which TLS connection is failing: client → CloudFront or CloudFront → origin?**

## TLS Architecture

A typical production architecture looks like:

```mermaid
sequenceDiagram
    participant C as Client
    participant D as CloudFront
    participant O as HTTPS Origin

    C->>D: TLS ClientHello
    D->>C: TLS negotiation + certificate
    C->>D: HTTPS request
    D->>O: TLS ClientHello
    O->>D: TLS negotiation + certificate
    D->>O: HTTPS request
    O-->>D: HTTPS response
    D-->>C: HTTPS response
```

CloudFront terminates the viewer TLS connection.

If the origin protocol is HTTPS, CloudFront then establishes a separate TLS connection to the origin.

Therefore:

```text
Viewer certificate
    ≠
Origin certificate
```

A valid CloudFront certificate does not guarantee that CloudFront can establish TLS with the origin.

## Client-to-CloudFront TLS

The viewer-facing TLS connection protects:

```text
https://cdn.example.com
```

The CloudFront distribution must have a certificate that covers the hostname used by clients.

For example:

```text
Client:
https://cdn.example.com

Certificate:
*.example.com
```

The certificate must be valid for the requested hostname.

A certificate for:

```text
api.example.com
```

does not cover:

```text
cdn.example.com
```

unless the certificate also contains the appropriate wildcard or SAN entry.

## CloudFront Alternate Domain Names

When a custom domain is used with CloudFront, the distribution must be configured with the corresponding alternate domain name.

For example:

```text
cdn.example.com
```

must be associated with the intended CloudFront distribution.

A common production failure is:

```text
DNS
  │
  ▼
CloudFront Distribution A

Certificate / hostname configuration
  │
  ▼
CloudFront Distribution B
```

The DNS, alternate domain name, certificate, and intended distribution must all align.

## Certificate Region

CloudFront viewer certificates using AWS Certificate Manager must be in:

```text
us-east-1
```

This is a CloudFront-specific operational requirement.

A certificate created in another AWS Region may be valid for other AWS services but cannot be used as the viewer certificate for a CloudFront distribution.

Check ACM certificates in `us-east-1`:

```bash
aws acm list-certificates \
  --region us-east-1
```

Describe a specific certificate:

```bash
aws acm describe-certificate \
  --region us-east-1 \
  --certificate-arn "$CERTIFICATE_ARN"
```

## Certificate Status

The certificate should be in an appropriate issued state.

Inspect:

```bash
aws acm describe-certificate \
  --region us-east-1 \
  --certificate-arn "$CERTIFICATE_ARN" \
  --query 'Certificate.{Status:Status,DomainName:DomainName,NotAfter:NotAfter,Type:Type}'
```

Check:

- Status
- Expiration
- Domain names
- Subject Alternative Names
- Validation state
- Renewal configuration

## Certificate Hostname Mismatch

Suppose the client requests:

```text
https://cdn.example.com
```

but the certificate only covers:

```text
api.example.com
```

The TLS handshake can fail before the HTTP request reaches the application.

Typical browser errors include certificate-name mismatch messages.

The fix is not an application change.

The certificate must contain a matching hostname, and that certificate must be associated with the CloudFront distribution.

## Wildcard Certificates

A wildcard certificate such as:

```text
*.example.com
```

can cover:

```text
cdn.example.com
api.example.com
static.example.com
```

but does not cover arbitrary deeper levels such as:

```text
media.cdn.example.com
```

unless another matching SAN or wildcard is present.

Do not assume that one wildcard covers every hostname beneath a domain.

## Subject Alternative Names

A certificate can contain multiple SANs:

```text
example.com
www.example.com
cdn.example.com
api.example.com
```

When troubleshooting hostname mismatches, inspect the complete certificate SAN list rather than checking only the primary domain.

## Inspect the Public Certificate

From a Linux/macOS environment:

```bash
openssl s_client \
  -connect cdn.example.com:443 \
  -servername cdn.example.com \
  -showcerts </dev/null
```

The `-servername` option is important because it sends the Server Name Indication used during TLS negotiation.

Inspect the certificate:

```bash
openssl s_client \
  -connect cdn.example.com:443 \
  -servername cdn.example.com \
  </dev/null 2>/dev/null |
  openssl x509 -noout \
    -subject \
    -issuer \
    -dates \
    -ext subjectAltName
```

Verify:

```text
Subject
Issuer
Not Before
Not After
Subject Alternative Name
```

## SNI and Hostname Selection

Modern HTTPS relies heavily on Server Name Indication (SNI).

A client can tell the server which hostname it wants during TLS negotiation:

```text
Client
  │
  │ ClientHello
  │ SNI = cdn.example.com
  ▼
CloudFront
  │
  │ Select certificate
  ▼
TLS handshake
```

Using:

```bash
openssl s_client \
  -connect cdn.example.com:443 \
  -servername cdn.example.com
```

is therefore more representative of a real HTTPS request than connecting without SNI.

## Viewer TLS Policy

CloudFront supports configurable viewer security policies that determine which TLS versions and cryptographic protocols can be used for the viewer connection.

A production system should generally use a modern TLS security policy appropriate for the application's supported clients.

Do not select an outdated TLS policy merely to make old clients work without understanding the security implications.

The trade-off is:

```text
Stricter TLS policy
      │
      ├── Better security
      └── Potentially less legacy-client compatibility
```

## TLS Version Mismatch

A client may fail to connect when it supports only older TLS versions while CloudFront requires a newer version.

Conversely, weakening the CloudFront TLS policy to support an obsolete client may reduce the security posture of the entire public endpoint.

Before changing the policy, identify:

- Client population
- Browser versions
- Mobile SDK versions
- Embedded devices
- Corporate proxies
- Legacy integrations

Prefer upgrading clients over weakening the distribution's security policy.

## Inspect CloudFront Configuration

Retrieve the distribution configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

The configuration can be used to verify:

- Viewer certificate
- Alternate domain names
- Viewer protocol policy
- TLS security policy
- Distribution status

For targeted inspection with AWS CLI and `jq`:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" |
jq '.DistributionConfig | {
  Aliases,
  ViewerCertificate,
  DefaultCacheBehavior
}'
```

## Viewer Protocol Policy

CloudFront can control whether viewers may use:

```text
HTTP
HTTPS
HTTP → HTTPS redirect
HTTPS only
```

For production applications, HTTPS should generally be the canonical protocol.

A common configuration is:

```text
HTTP request
    │
    ▼
CloudFront
    │
    └── 301/redirect → HTTPS
```

For APIs and security-sensitive endpoints, consider whether redirects are appropriate for the client type. Some API clients should be configured to use HTTPS directly rather than relying on redirects.

## CloudFront-to-Origin TLS

The second TLS connection is:

```text
CloudFront
    │
    │ HTTPS
    ▼
Origin
```

The origin might be:

- Application Load Balancer
- Network Load Balancer
- API service
- EC2 application
- Kubernetes ingress
- Another HTTPS endpoint

CloudFront must be able to establish a valid TLS connection to that origin.

## Origin Protocol Policy

CloudFront cache behaviors can use an origin protocol policy such as:

```text
HTTP only
HTTPS only
Match viewer
```

For secure production workloads:

```text
CloudFront → HTTPS origin
```

is generally preferable.

This protects traffic between CloudFront and the origin rather than only protecting client-to-CloudFront traffic.

## Two Independent TLS Trust Boundaries

Consider:

```text
Browser
   │
   │ TLS #1
   ▼
CloudFront
   │
   │ TLS #2
   ▼
Application Load Balancer
```

A browser may successfully establish TLS #1 while CloudFront fails TLS #2.

Therefore:

```text
Valid browser certificate
        ≠
Valid origin certificate
```

This distinction is one of the most important CloudFront TLS troubleshooting concepts.

## Origin Certificate Hostname Matching

CloudFront validates the origin's TLS certificate when connecting over HTTPS.

Suppose the configured origin is:

```text
origin.example.com
```

but the origin presents a certificate only for:

```text
api.example.com
```

The origin TLS connection may fail.

The certificate must match the hostname CloudFront uses for the origin connection.

## Origin Hostname vs Viewer Hostname

These hostnames can be different:

```text
Viewer:
cdn.example.com

Origin:
internal-api.example.com
```

The certificates and DNS configuration must be correct for their respective roles.

Do not assume the certificate covering the public CloudFront hostname also needs to cover the origin hostname.

## ALB as a CloudFront Origin

A common architecture is:

```text
Internet
   │
   ▼
CloudFront
   │
   │ HTTPS
   ▼
Application Load Balancer
   │
   ▼
Django / FastAPI
```

The ALB listener certificate must cover the hostname CloudFront uses when establishing the TLS connection.

For example:

```text
CloudFront origin:
alb-origin.example.com

ALB certificate:
*.example.com
```

This can work if the certificate correctly covers the configured origin hostname.

## Origin Server Name Indication

When using HTTPS origins, the hostname used by CloudFront for the origin connection is significant.

Inspect the configured origin:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" |
jq '.DistributionConfig.Origins.Items[] | {
  Id,
  DomainName,
  CustomHeaders
}'
```

Verify that the configured origin domain is the hostname for which the origin certificate is valid.

## DNS Problems

TLS failures can be caused by DNS pointing to an unexpected endpoint.

Check DNS:

```bash
dig +short cdn.example.com
```

For more detail:

```bash
dig cdn.example.com
```

The DNS record should point to the intended CloudFront distribution.

For a CloudFront distribution, a DNS alias or CNAME normally resolves the application hostname to the CloudFront distribution hostname.

## DNS and Certificate Mismatch

A common failure looks like:

```text
cdn.example.com
       │
       ▼
Unexpected endpoint
       │
       ▼
Certificate for another hostname
       │
       ▼
TLS failure
```

This can happen during:

- DNS migrations
- Blue/green deployments
- Distribution replacement
- Certificate rotation
- Multi-account migrations

Always verify DNS before assuming the certificate itself is broken.

## TLS Troubleshooting Flow

```mermaid
flowchart TD
    A[HTTPS request fails] --> B{Can client establish TLS with CloudFront?}

    B -->|No| C[Inspect DNS and viewer certificate]
    C --> D[Check hostname coverage]
    C --> E[Check ACM certificate status]
    C --> F[Check TLS security policy]
    C --> G[Check SNI and client compatibility]

    B -->|Yes| H{Can CloudFront establish TLS with origin?}

    H -->|No| I[Inspect origin TLS]
    I --> J[Check origin certificate]
    I --> K[Check origin hostname]
    I --> L[Check origin protocol policy]
    I --> M[Check origin TLS compatibility]

    H -->|Yes| N[Inspect HTTP status and application]
```

## Systematic Troubleshooting Workflow

### Identify the Failing TLS Leg

Start with:

```text
Client → CloudFront
```

or:

```text
CloudFront → Origin
```

Do not debug both simultaneously.

### Verify DNS

```bash
dig cdn.example.com
```

Confirm the hostname resolves to the expected CloudFront distribution.

### Inspect Viewer Certificate

```bash
aws acm describe-certificate \
  --region us-east-1 \
  --certificate-arn "$CERTIFICATE_ARN"
```

Verify hostname coverage and certificate status.

### Test SNI

```bash
openssl s_client \
  -connect cdn.example.com:443 \
  -servername cdn.example.com \
  </dev/null
```

Look for certificate and verification information.

### Verify CloudFront Configuration

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

Confirm:

- Alternate domain names
- Viewer certificate
- TLS security policy
- Viewer protocol policy

### Test the Origin Directly

If the origin is public and safely testable:

```bash
curl -v \
  --connect-timeout 10 \
  "https://origin.example.com/health"
```

For a TLS-specific test:

```bash
openssl s_client \
  -connect origin.example.com:443 \
  -servername origin.example.com \
  -showcerts </dev/null
```

This helps determine whether the origin itself presents a valid certificate.

### Verify Origin Certificate

Check:

- Hostname
- Expiration
- Issuer
- Certificate chain
- TLS versions
- SNI
- Listener configuration

### Verify CloudFront Origin Protocol

Confirm whether the distribution uses:

```text
HTTP only
HTTPS only
Match viewer
```

If HTTPS is expected, ensure the configured origin behavior actually uses HTTPS.

## Certificate Chain Problems

A certificate can be valid on the origin but still fail validation if the server does not present the required certificate chain.

Inspect the presented chain:

```bash
openssl s_client \
  -connect origin.example.com:443 \
  -servername origin.example.com \
  -showcerts </dev/null
```

Look for:

```text
Certificate chain
```

A common production mistake is installing only the leaf certificate and omitting the necessary intermediate certificate.

## Origin Certificate Renewal

Automatic ACM certificate renewal is preferable when supported by the architecture.

For manually managed certificates, monitor:

```text
Expiration date
Renewal status
Deployment status
```

Certificate expiration should be treated as an operational dependency, not something discovered from customer reports.

## Certificate Rotation

A safe certificate rotation should avoid unnecessary downtime.

Typical process:

```text
Issue new certificate
       ↓
Validate domain ownership
       ↓
Associate certificate with CloudFront
       ↓
Wait for deployment
       ↓
Validate HTTPS endpoint
       ↓
Monitor
       ↓
Retire old certificate when safe
```

Do not delete the old certificate before confirming that no active CloudFront configuration still depends on it.

## CloudFront Deployment State

CloudFront configuration changes are distributed globally.

After modifying a distribution, inspect its status:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.Status'
```

A configuration change may not be immediately visible at every edge location.

Avoid interpreting a short period of mixed behavior during a deployment as definitive evidence that the configuration is incorrect.

## ACM Certificate Validation

When using ACM certificates, verify that domain validation has completed.

Inspect:

```bash
aws acm describe-certificate \
  --region us-east-1 \
  --certificate-arn "$CERTIFICATE_ARN" \
  --query 'Certificate.DomainValidationOptions[].{
    Domain:DomainName,
    Status:ValidationStatus,
    Method:ValidationMethod
  }'
```

DNS validation is generally preferable for automated renewal.

## Certificate Permissions and Account Boundaries

In multi-account AWS environments, certificate ownership and CloudFront distribution ownership may be separated.

Verify:

- AWS account
- Certificate ARN
- CloudFront distribution account
- IAM permissions
- ACM region

A certificate existing in the wrong account or region can lead to deployment and configuration failures.

## Private Origins

If the origin is private, TLS troubleshooting must be separated from network reachability.

For example:

```text
CloudFront
   │
   ▼
Private Load Balancer
   │
   ▼
Private application
```

A TLS error may actually be preceded by:

- Security group restrictions
- Network ACLs
- Routing problems
- DNS resolution problems
- Private connectivity configuration

First establish whether CloudFront can reach the origin endpoint at all.

## CloudFront Origin Access and TLS

For S3 origins, the TLS model differs from a custom HTTPS origin.

A typical architecture is:

```text
Client
  │
  │ HTTPS
  ▼
CloudFront
  │
  ▼
S3
```

For private S3 content, CloudFront access-control mechanisms should be configured appropriately.

Do not troubleshoot an S3 authorization problem as an origin TLS problem merely because the browser reports an HTTPS-related error.

## TLS Errors vs HTTP Errors

TLS failures occur before normal HTTP application processing.

Conceptually:

```text
TCP connection
     ↓
TLS handshake
     ↓
HTTP request
     ↓
CloudFront processing
     ↓
Origin request
     ↓
Application response
```

If TLS negotiation fails:

```text
HTTP request may never exist.
```

This is why Django or FastAPI logs may show nothing for some viewer-side TLS failures.

## Useful Diagnostic Commands

| Purpose | Command |
|---|---|
| DNS resolution | `dig cdn.example.com` |
| Viewer TLS | `openssl s_client -connect cdn.example.com:443 -servername cdn.example.com` |
| Origin TLS | `openssl s_client -connect origin.example.com:443 -servername origin.example.com` |
| HTTPS request | `curl -v https://cdn.example.com/` |
| Certificate details | `openssl x509 -noout -subject -issuer -dates -ext subjectAltName` |
| CloudFront configuration | `aws cloudfront get-distribution-config --id "$DISTRIBUTION_ID"` |
| Distribution status | `aws cloudfront get-distribution --id "$DISTRIBUTION_ID"` |
| ACM certificates | `aws acm list-certificates --region us-east-1` |
| ACM certificate details | `aws acm describe-certificate --region us-east-1 --certificate-arn "$CERTIFICATE_ARN"` |

## Verbose `curl` Inspection

Use:

```bash
curl -v \
  --connect-timeout 10 \
  --max-time 30 \
  "https://cdn.example.com/"
```

Useful information includes:

```text
* Connected to ...
* TLSv1.3 ...
* Server certificate:
* SSL certificate verify ok.
> GET /
< HTTP/2 200
```

The exact protocol negotiated depends on client and server capabilities.

## Testing Specific TLS Versions

OpenSSL can be used to test compatibility:

```bash
openssl s_client \
  -connect cdn.example.com:443 \
  -servername cdn.example.com \
  -tls1_2 </dev/null
```

And where supported by the local OpenSSL version:

```bash
openssl s_client \
  -connect cdn.example.com:443 \
  -servername cdn.example.com \
  -tls1_3 </dev/null
```

This is useful for diagnosing client compatibility and security-policy behavior.

## Security Considerations

TLS configuration should protect both network legs where HTTPS is required:

```text
Client
  │
  │ TLS
  ▼
CloudFront
  │
  │ TLS
  ▼
Origin
```

Production recommendations include:

- Use HTTPS for public endpoints.
- Prefer modern TLS versions.
- Avoid obsolete TLS versions unless a documented compatibility requirement exists.
- Use certificates with correct hostname coverage.
- Automate certificate renewal.
- Monitor expiration.
- Protect private keys.
- Avoid disabling certificate verification at origins.
- Use secure origin connections for sensitive data.
- Restrict origin access independently of TLS.
- Validate certificate changes through CI/CD where practical.

## Common Mistakes

### Certificate Exists but Is in the Wrong Region

CloudFront viewer certificates from ACM must be in `us-east-1`.

**Fix:** inspect ACM in `us-east-1`.

### Certificate Covers the Wrong Hostname

A certificate for:

```text
api.example.com
```

does not automatically cover:

```text
cdn.example.com
```

**Fix:** inspect SANs and wildcard coverage.

### Forgetting SNI

Testing without SNI can produce misleading results when multiple certificates or virtual hosts are involved.

**Fix:**

```bash
openssl s_client \
  -connect cdn.example.com:443 \
  -servername cdn.example.com
```

### Debugging the Origin When Viewer TLS Is Broken

If the browser cannot establish TLS with CloudFront, origin configuration is irrelevant to that request.

**Fix:** identify the failing TLS leg first.

### Assuming CloudFront and Origin Use the Same Certificate

They do not need to.

**Fix:** validate the viewer certificate and origin certificate independently.

### Using an Invalid Origin Hostname

CloudFront may connect to:

```text
origin.internal.example.com
```

while the origin certificate covers only:

```text
api.example.com
```

**Fix:** ensure the origin hostname and certificate coverage align.

### Missing Intermediate Certificate

An origin may serve an incomplete certificate chain.

**Fix:** configure the origin to present the complete required chain.

### Weakening TLS to Fix One Legacy Client

Changing the entire distribution to support an obsolete client can unnecessarily reduce security.

**Fix:** determine whether the client can be upgraded or isolated before weakening the policy.

### Assuming DNS Is Correct

During migrations, DNS can point to an old or incorrect endpoint.

**Fix:**

```bash
dig cdn.example.com
```

and verify the destination.

### Deleting Certificates Too Early

Removing a certificate that is still referenced by a deployed or partially deployed configuration can create operational failures.

**Fix:** verify CloudFront configuration and deployment state before certificate deletion.

## Production Incident Checklist

When a CloudFront HTTPS endpoint suddenly starts failing:

```text
[ ] Identify affected hostname
[ ] Identify whether viewer or origin TLS is failing
[ ] Check DNS
[ ] Check certificate expiration
[ ] Check certificate hostname coverage
[ ] Check ACM certificate region
[ ] Check CloudFront viewer certificate
[ ] Check TLS security policy
[ ] Test with curl -v
[ ] Test with openssl + SNI
[ ] Check CloudFront distribution deployment state
[ ] Test origin TLS independently
[ ] Verify origin hostname
[ ] Verify origin certificate
[ ] Check certificate chain
[ ] Check load balancer / ingress TLS configuration
[ ] Check recent certificate rotations
[ ] Check recent DNS changes
[ ] Check recent CloudFront configuration changes
```

## Monitoring and Alerting

Certificate expiration should be monitored before it becomes an incident.

Useful alerts include:

| Alert | Recommended purpose |
|---|---|
| Certificate expiration | Detect upcoming renewal failures |
| CloudFront 4xx increase | Detect viewer-side failures |
| CloudFront 5xx increase | Detect origin-side failures |
| TLS handshake failures | Detect protocol/certificate problems |
| Origin connection failures | Detect CloudFront-to-origin issues |
| DNS changes | Detect unexpected routing changes |
| CloudFront configuration changes | Detect unintended deployment changes |

Track changes alongside deployments so an increase in TLS errors can be correlated with:

```text
Certificate deployment
DNS change
CloudFront configuration change
Origin certificate change
Load balancer change
```

## CI/CD Considerations

TLS configuration should be treated as infrastructure code where practical.

A deployment pipeline should validate:

- Certificate ARN
- Region
- Alternate domain names
- CloudFront distribution
- Origin hostname
- Origin protocol policy
- TLS security policy

For example:

```text
Pull Request
     │
     ▼
Infrastructure validation
     │
     ├── Certificate exists
     ├── Correct region
     ├── Hostname matches
     ├── Distribution matches
     └── Origin HTTPS configured
             │
             ▼
        Deployment
             │
             ▼
       Smoke tests
             │
             ▼
      TLS verification
```

A post-deployment smoke test can include:

```bash
curl -fsS \
  --connect-timeout 10 \
  "https://cdn.example.com/health"
```

For certificate-specific verification:

```bash
openssl s_client \
  -connect cdn.example.com:443 \
  -servername cdn.example.com \
  </dev/null 2>/dev/null |
  openssl x509 -noout \
    -subject \
    -issuer \
    -dates \
    -ext subjectAltName
```

## High Availability Considerations

CloudFront provides globally distributed edge delivery, but TLS configuration remains a critical dependency.

For production:

- Use ACM-managed certificates where appropriate.
- Enable automated renewal.
- Monitor renewal status.
- Keep infrastructure configuration reproducible.
- Test certificate rotations before production.
- Avoid manual certificate changes without change tracking.
- Maintain documented rollback procedures.

Certificate rotation should be designed as a normal operational workflow rather than an emergency-only procedure.

## Cost Considerations

TLS itself is not usually the dominant CloudFront cost driver.

The operational cost of TLS failures is more significant:

```text
Certificate failure
      ↓
HTTPS outage
      ↓
Application unavailable
      ↓
Customer impact
      ↓
Incident response
```

Automated certificate management, monitoring, and deployment validation generally provide more value than optimizing TLS configuration for small cost differences.

## Interview Perspective

A strong answer to:

> "CloudFront is returning TLS errors. How would you troubleshoot the issue?"

should begin by separating the two TLS connections:

```text
Client → CloudFront
CloudFront → Origin
```

Then:

1. Verify DNS for the affected hostname.
2. Check whether the viewer certificate covers the hostname.
3. Confirm the ACM certificate is in `us-east-1`.
4. Check certificate status and expiration.
5. Inspect the CloudFront alternate domain names.
6. Check the viewer TLS security policy.
7. Test with `curl -v`.
8. Test with `openssl s_client` using SNI.
9. If viewer TLS succeeds, inspect CloudFront-to-origin TLS.
10. Verify the origin hostname matches the origin certificate.
11. Check the origin certificate chain and expiration.
12. Verify the origin protocol policy.
13. Test the origin independently.
14. Check recent DNS, certificate, load balancer, and CloudFront changes.
15. Check whether the failure is actually TLS or an HTTP/WAF/origin error.

The senior-level distinction is:

> **CloudFront TLS troubleshooting is a two-hop problem. Never assume that a valid viewer certificate proves that the CloudFront-to-origin TLS connection is healthy.**

## Key Takeaways

- **CloudFront TLS has two independent connections:** troubleshoot client-to-CloudFront and CloudFront-to-origin separately.
- **Viewer certificates must match the public hostname and use ACM in `us-east-1`:** DNS, alternate domain names, certificate SANs, and CloudFront configuration must align.
- **Origin TLS has its own trust requirements:** the origin hostname, certificate, certificate chain, TLS policy, and HTTPS configuration must be compatible.
- **Use protocol-level diagnostics:** `dig`, `curl -v`, and `openssl s_client -servername` can quickly distinguish DNS, certificate, SNI, and TLS negotiation failures.
- **Treat certificates as production infrastructure:** automate renewal, monitor expiration, validate rotations, and include TLS checks in CI/CD and deployment smoke tests.