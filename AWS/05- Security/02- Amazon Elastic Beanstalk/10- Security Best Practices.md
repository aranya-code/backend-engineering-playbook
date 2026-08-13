# 10- Security Best Practices

## Overview

Amazon Elastic Beanstalk simplifies application deployment and environment management, but production security still depends on how the environment is configured, how the application is deployed, and how surrounding AWS services are secured.

A secure Elastic Beanstalk architecture should apply defense in depth across:

```text
Identity
   ↓
IAM
   ↓
Network
   ↓
Elastic Beanstalk
   ↓
Application
   ↓
Data
   ↓
Monitoring
   ↓
Incident Response
```

The objective is not to make Elastic Beanstalk independently responsible for every security control. Instead, security boundaries should be deliberately distributed across AWS services, the application, CI/CD, and operational processes.

A practical production baseline is:

```text
Internet
   │
   ▼
Route 53 / CloudFront
   │
   ▼
AWS WAF
   │
   ▼
Application Load Balancer
   │
   ▼
Elastic Beanstalk
   │
   ├── EC2 instances
   │
   ├── Application
   │
   └── Background workers
   │
   ├───────────────┐
   ▼               ▼
PostgreSQL       Redis
   │
   ▼
Monitoring / Audit / Security Services
```

Security decisions should be based on the application's threat model, data sensitivity, compliance requirements, and operational risk.

## Security Principles

The most important Elastic Beanstalk security practices follow established backend and cloud-security principles.

| Principle | Practical application |
|---|---|
| Least privilege | Restrict IAM permissions to required actions |
| Defense in depth | Use IAM, security groups, WAF, TLS, application controls, and monitoring together |
| Minimize exposure | Keep databases and internal services private |
| Secure by default | Deny unnecessary access and explicitly allow required traffic |
| Assume breach | Design monitoring and isolation for compromised workloads |
| Encrypt sensitive data | Use TLS in transit and encryption at rest |
| Centralize secrets | Use managed secret stores rather than source code |
| Immutable deployments | Prefer controlled, repeatable application releases |
| Audit privileged activity | Monitor administrative and infrastructure changes |
| Automate controls | Enforce security through CI/CD and Infrastructure as Code |

## Identity and IAM Security

IAM is one of the most important security boundaries in an Elastic Beanstalk environment.

There are usually several identities involved:

```text
Developer
   │
   ▼
AWS IAM Identity
   │
   ├── Elastic Beanstalk service role
   ├── EC2 instance profile
   └── CI/CD deployment role
```

These identities should have different responsibilities.

### Least Privilege

Grant only the permissions required for a specific role.

Avoid policies such as:

```json
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "*"
}
```

unless there is an explicitly justified administrative requirement.

Instead, separate responsibilities:

```text
Deployment role
    └── Deployment-related permissions

Elastic Beanstalk service role
    └── Service management permissions

EC2 instance role
    └── Runtime permissions

Developer role
    └── Development and operational permissions
```

### Instance Profiles

Elastic Beanstalk EC2 instances can use an IAM instance profile to obtain temporary AWS credentials.

This is preferable to storing long-lived AWS access keys on the server.

Example application behavior:

```text
Django / FastAPI
      │
      ▼
AWS SDK
      │
      ▼
Instance Metadata / IAM Role
      │
      ▼
Temporary AWS credentials
      │
      ▼
S3 / Secrets Manager / CloudWatch
```

The application should not contain:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

as permanent credentials.

### CI/CD Access

CI/CD systems should use dedicated deployment identities.

Prefer:

```text
GitHub Actions
      │
      ▼
Federated / short-lived AWS credentials
      │
      ▼
Deployment role
      │
      ▼
Elastic Beanstalk
```

over:

```text
GitHub Actions
      │
      ▼
Permanent IAM access key
```

Long-lived credentials increase the impact of credential leakage.

## Root Account Security

The AWS account root user should not be used for normal operations.

Production environments should:

- Enable strong authentication on the root account.
- Avoid creating application credentials for root.
- Avoid using root for routine deployment operations.
- Protect root recovery information.
- Monitor sensitive root activity.

Root credentials represent an exceptionally powerful security boundary.

## Network Security

Elastic Beanstalk networking should follow the principle of minimum exposure.

A typical production architecture is:

```text
Internet
   │
   ▼
Public Subnets
   │
   └── Application Load Balancer
           │
           ▼
      Private Subnets
           │
           ├── EC2 / Elastic Beanstalk
           │
           ├── Worker instances
           │
           └── Internal services
                  │
                  ├── PostgreSQL
                  └── Redis
```

The exact subnet design depends on the application architecture, but databases and internal data services should generally not be directly reachable from the public Internet.

## Security Groups

Security groups should allow only required traffic.

For example:

```text
Internet
   │
   ▼
ALB Security Group
   ├── TCP 443 from Internet
   └── TCP 80 only if HTTP redirect is required

EC2 Security Group
   └── Application traffic only from ALB Security Group

Database Security Group
   └── PostgreSQL only from EC2/application Security Group
```

Prefer security-group references over broad CIDR-based access when communicating between AWS resources.

### Avoid Broad Rules

Avoid rules such as:

```text
TCP 5432
Source: 0.0.0.0/0
```

for PostgreSQL.

Similarly, avoid exposing Redis:

```text
TCP 6379
Source: 0.0.0.0/0
```

Internal services should have tightly restricted network paths.

## SSH Access

SSH should not be treated as the normal application-management mechanism.

Avoid:

```text
Internet
   │
   └── TCP 22 → EC2
```

for general operational access.

Where possible, use controlled management mechanisms such as AWS Systems Manager rather than exposing SSH publicly.

If SSH is required:

- Restrict the source.
- Use strong authentication.
- Avoid shared accounts.
- Monitor access.
- Remove unnecessary access paths.

## TLS and HTTPS

Production applications should use HTTPS for external traffic.

A common architecture is:

```text
Client
  │
  │ HTTPS
  ▼
ALB
  │
  │ Internal application traffic
  ▼
Elastic Beanstalk
```

TLS protects:

- Credentials.
- Authentication cookies.
- API tokens.
- Request data.
- Response data.
- Personally identifiable information.

HTTP should generally redirect to HTTPS when HTTP is intentionally exposed for redirection.

## TLS Termination

TLS can terminate at the load balancer:

```text
Client
   │
   │ HTTPS
   ▼
ALB
   │
   │ HTTP / HTTPS
   ▼
Application
```

The security properties of the internal hop should be considered separately.

For environments with strict end-to-end encryption requirements:

```text
Client
   │ HTTPS
   ▼
ALB
   │ HTTPS
   ▼
Application
```

Use the architecture required by the organization's threat model and compliance requirements.

## Security Headers

Backend applications should use appropriate HTTP security headers.

Examples include:

```text
Strict-Transport-Security
Content-Security-Policy
X-Content-Type-Options
Referrer-Policy
```

The exact policy should match the application's frontend and API behavior.

For Django, security settings should be configured deliberately rather than relying on accidental defaults.

Example:

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
```

These settings should be validated against the application's deployment topology, particularly when TLS terminates at a load balancer.

## Application Security

Elastic Beanstalk does not protect an application from application-level vulnerabilities.

Django and FastAPI applications must still defend against:

- SQL injection.
- Cross-site scripting.
- CSRF.
- Broken authorization.
- Authentication flaws.
- SSRF.
- Insecure deserialization.
- Path traversal.
- Command injection.
- Unsafe file uploads.
- Excessive API access.
- Business-logic vulnerabilities.

AWS infrastructure security and application security are complementary.

## Authorization

Authentication is not authorization.

A request may be authenticated while still being unauthorized.

For example:

```text
Authenticated user
      │
      ▼
POST /api/admin/users
      │
      ▼
Authorization check
      │
      ├── Allowed
      └── 403 Forbidden
```

Authorization must be enforced at the application layer for business operations.

Do not rely exclusively on network security groups to enforce business permissions.

## Secrets Management

Secrets should not be embedded in:

```text
Source code
Docker images
Git repositories
Elastic Beanstalk configuration files committed to Git
Application logs
CI/CD output
```

Prefer managed secret storage such as AWS Secrets Manager or Systems Manager Parameter Store where appropriate.

A production architecture can be:

```text
Application
    │
    ▼
IAM role
    │
    ▼
Secrets Manager
    │
    ▼
Database credentials
```

The application retrieves the secret using its runtime identity.

## Secret Rotation

Secrets should have a defined lifecycle:

```text
Create
  ↓
Store securely
  ↓
Use
  ↓
Rotate
  ↓
Revoke old credential
```

Database passwords, API credentials, certificates, and other sensitive values should be rotated according to risk and operational requirements.

Rotation must be tested.

A theoretically secure rotation mechanism that causes production downtime is still an operational problem.

## Environment Variables

Environment variables are useful for configuration, but they should not automatically be treated as a secret-management system.

For example:

```text
DATABASE_HOST
DATABASE_NAME
LOG_LEVEL
```

may be ordinary configuration.

Sensitive values such as:

```text
DATABASE_PASSWORD
API_SECRET
PRIVATE_KEY
```

require stronger handling.

If secrets are injected into the environment, ensure that:

- Access is restricted.
- Logs do not expose them.
- Debugging tools cannot unnecessarily expose them.
- Processes and operational users are appropriately isolated.

## Data Protection

Production data should be protected both:

```text
At rest
+
In transit
```

Typical data flows include:

```text
Client
   │ TLS
   ▼
ALB
   │
   ▼
Application
   │ TLS where required
   ▼
PostgreSQL
```

Sensitive data should also be classified so that stronger controls can be applied where necessary.

## Database Security

A production PostgreSQL deployment should generally:

- Remain private.
- Accept connections only from authorized application resources.
- Require authentication.
- Use encryption in transit where appropriate.
- Encrypt storage.
- Maintain backups.
- Restrict administrative access.
- Monitor connections and failures.

Avoid placing a production database directly on a public network path simply because the application needs to connect to it.

## Redis Security

Redis should generally be treated as an internal infrastructure component.

Avoid public Internet exposure.

A safer architecture is:

```text
Internet
   X
   │
   │ No direct access
   ▼
Application
   │
   ▼
Private Redis
```

Where supported by the deployment architecture, use authentication, encryption, network restrictions, and appropriate access controls.

## S3 Security

If Elastic Beanstalk applications use S3 for:

```text
Media
Static assets
Backups
Exports
Logs
Documents
```

apply least privilege to the application's S3 access.

For example, an application that only uploads objects to:

```text
s3://company-production-media/uploads/
```

should not automatically have permission to delete or access unrelated buckets.

Avoid public buckets unless public access is explicitly required and controlled.

## S3 Block Public Access

For private application data, S3 Block Public Access should be used where applicable.

A secure model is:

```text
Application
    │
    ▼
IAM role
    │
    ▼
Private S3 bucket
```

rather than:

```text
Application
    │
    ▼
Public bucket
```

## WAF

AWS WAF can provide an additional HTTP security layer before traffic reaches Elastic Beanstalk.

```text
Internet
   │
   ▼
AWS WAF
   │
   ▼
ALB
   │
   ▼
Elastic Beanstalk
```

Useful protections include:

- Managed rule groups.
- IP-based restrictions.
- Rate limiting.
- Request filtering.
- Application-specific rules.

WAF should complement application-level validation rather than replace it.

## Rate Limiting

Rate limiting helps protect APIs from:

- Brute-force authentication.
- Resource exhaustion.
- Scraping.
- Excessive API usage.
- Automated abuse.

Rate limits may exist at multiple layers:

```text
CloudFront / WAF
       ↓
Application / API
       ↓
Redis-backed rate limiter
```

The appropriate layer depends on the attack and the business requirement.

## DDoS Protection

DDoS protection should be considered as part of the broader AWS edge architecture.

A typical layered approach is:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
AWS WAF
  │
  ▼
ALB
  │
  ▼
Elastic Beanstalk
```

DDoS protection does not eliminate the need for application rate limiting or resource controls.

An application can be overwhelmed by legitimate-looking requests even when the underlying network remains available.

## Logging and Auditing

Security-sensitive activity should be auditable.

Important sources include:

```text
CloudTrail
CloudWatch
ALB access logs
WAF logs
VPC Flow Logs
Application logs
AWS Config
GuardDuty
```

Audit records should help answer:

```text
Who?
What?
When?
Where?
Which resource?
What was the result?
```

Do not log secrets merely to make an event easier to investigate.

## Monitoring

Security should be monitored continuously.

Useful signals include:

| Signal | Potential concern |
|---|---|
| WAF blocks increase | Attack or false-positive rule |
| Login failures increase | Credential attack |
| 403 responses increase | Authorization issue or probing |
| 5xx responses increase | Application/resource failure |
| CPU increases unexpectedly | Traffic spike or workload abuse |
| Network egress increases | Data exfiltration |
| IAM policy changes | Privilege escalation risk |
| Security group changes | Network exposure |
| Deployment outside normal window | Unauthorized change |
| GuardDuty finding | Potential threat |

Correlating signals is more valuable than reacting to individual metrics.

## Deployment Security

Application deployments should be controlled and auditable.

A production deployment should ideally follow:

```text
Developer
   │
   ▼
Pull Request
   │
   ▼
Code Review
   │
   ▼
Automated Tests
   │
   ▼
Security Checks
   │
   ▼
CI/CD
   │
   ▼
AWS Deployment Role
   │
   ▼
Elastic Beanstalk
```

Avoid allowing arbitrary developers to deploy directly to production without appropriate controls.

## Deployment Immutability

Repeatable deployments reduce configuration drift.

Prefer:

```text
Build artifact
      │
      ▼
Validated artifact
      │
      ▼
Production deployment
```

rather than manually modifying production servers after deployment.

Manual server modifications create differences that are difficult to reproduce and audit.

## Dependency Security

Python applications should continuously assess dependencies.

Example workflow:

```text
requirements.txt / lock file
          │
          ▼
Dependency scanning
          │
          ▼
Vulnerability detection
          │
          ▼
Upgrade / remediation
```

Security issues can exist in:

- Django.
- FastAPI.
- Uvicorn.
- Database drivers.
- Authentication libraries.
- HTTP libraries.
- Transitive dependencies.

Pinning or otherwise controlling dependency versions improves reproducibility, while a dependency-update process ensures vulnerabilities are not permanently frozen into the deployment.

## OS and Platform Patching

Elastic Beanstalk environments rely on platform-managed infrastructure and operating-system components.

Production environments should:

- Use supported platform versions.
- Apply security updates according to the organization's maintenance strategy.
- Plan platform upgrades.
- Test upgrades before production rollout.
- Monitor after upgrades.

Do not treat the application runtime as permanently static.

## Container Security

When using Docker with Elastic Beanstalk, container security becomes part of the deployment boundary.

Avoid:

```dockerfile
FROM python:latest
```

for production images when deterministic builds are required.

Prefer a controlled base image strategy.

Other practices include:

- Run as a non-root user where practical.
- Minimize installed packages.
- Remove unnecessary build tools from runtime images.
- Scan images for vulnerabilities.
- Do not embed secrets in images.
- Keep the image reproducible.

Example:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER appuser

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

The exact server and configuration should match the application and Elastic Beanstalk platform.

## Container Secrets

Never bake secrets into a Docker image.

Avoid:

```dockerfile
ENV DATABASE_PASSWORD="production-password"
```

or:

```dockerfile
COPY .env /app/.env
```

The resulting image can expose the secret to anyone with access to the image or its layers.

Inject configuration through an appropriate runtime secret mechanism instead.

## File System Security

Application processes should have only the filesystem access they require.

Avoid giving application code unnecessary write access to system directories.

If file uploads are required:

```text
Client
  │
  ▼
Application
  │
  ├── Validate type
  ├── Validate size
  ├── Generate safe name
  └── Store outside executable code
```

Prefer object storage such as S3 for durable user-generated files when appropriate.

## Database Credentials

Applications should not share a single unrestricted database account across all environments.

Prefer separate credentials and appropriate permissions:

```text
Development
   └── Development DB credentials

Staging
   └── Staging DB credentials

Production
   └── Production DB credentials
```

Application credentials should generally have only the database permissions required by the application.

Administrative database access should use separate privileged credentials.

## Environment Isolation

Do not allow development credentials or systems to access production resources unnecessarily.

Maintain clear boundaries:

```text
Development
    X
    │
    │ No unnecessary access
    ▼
Production
```

Separate AWS accounts are often stronger isolation boundaries than merely using different environments within one account, depending on organizational architecture.

## Security Groups vs IAM

These controls solve different problems.

| Control | Protects |
|---|---|
| IAM | AWS API/resource authorization |
| Security groups | Network connectivity |
| WAF | HTTP request filtering |
| Application authorization | Business permissions |
| Database permissions | Data-level access |

For example:

```text
IAM
 └── Can the application call S3?

Security Group
 └── Can the application connect to PostgreSQL?

Application authorization
 └── Can this user modify this resource?

Database permissions
 └── Can this database identity modify this table?
```

A secure system does not confuse these boundaries.

## High Availability and Security

Availability is part of security.

A security architecture should avoid creating a single operational dependency whose failure disables security controls or the application.

For production environments:

- Use multiple Availability Zones where appropriate.
- Use load balancing.
- Use managed databases with appropriate availability configuration.
- Monitor dependencies.
- Test recovery procedures.

Security controls should improve resilience rather than become fragile single points of failure.

## Disaster Recovery

Security incidents can require recovery as well as containment.

Protect:

```text
Application artifacts
Database backups
Configuration
Infrastructure definitions
Audit logs
Security evidence
```

Backups should be protected against:

- Accidental deletion.
- Unauthorized access.
- Corruption.
- Ransomware-like scenarios.
- Region-level failures where relevant.

Recovery procedures must be tested rather than assumed to work.

## Security and Cost

Security controls have operational costs.

Examples include:

```text
CloudWatch log ingestion
CloudTrail data events
S3 log storage
WAF requests and rules
Security tooling
Data transfer
Backup storage
```

Cost optimization should not remove controls blindly.

Instead:

```text
Risk
  ↓
Required visibility
  ↓
Retention strategy
  ↓
Appropriate storage tier
```

For example, high-volume logs may use shorter hot retention with longer-term archival.

## Production Security Baseline

A practical baseline for a production Elastic Beanstalk environment is:

```text
Identity
 ├── Least-privilege IAM
 ├── No shared administrative credentials
 └── Short-lived CI/CD access where possible

Network
 ├── Private application/database tiers where appropriate
 ├── Restricted security groups
 └── No unnecessary public ports

Transport
 ├── HTTPS
 ├── Valid TLS configuration
 └── Secure application cookies

Application
 ├── Authentication
 ├── Authorization
 ├── Input validation
 ├── Dependency security
 └── Secure file handling

Secrets
 ├── Managed secret storage
 ├── Restricted access
 └── Rotation

Edge
 ├── WAF
 ├── Rate limiting
 └── DDoS-aware architecture

Monitoring
 ├── CloudTrail
 ├── CloudWatch
 ├── Application audit logs
 ├── WAF logs
 └── Security findings

Operations
 ├── Controlled deployments
 ├── Infrastructure as Code
 ├── Incident response
 └── Tested recovery
```

## Security Review Checklist

### IAM

- [ ] Least-privilege policies are used.
- [ ] Separate roles exist for distinct responsibilities.
- [ ] Production does not depend on long-lived application credentials.
- [ ] CI/CD access is restricted.
- [ ] Privileged actions are auditable.
- [ ] Root account usage is minimized.

### Network

- [ ] Databases are not unnecessarily public.
- [ ] Redis is not publicly exposed.
- [ ] Security groups allow only required traffic.
- [ ] Public ports are minimized.
- [ ] Administrative access is restricted.
- [ ] Network flow visibility is available where required.

### Application

- [ ] Authentication is securely implemented.
- [ ] Authorization is enforced server-side.
- [ ] Sensitive endpoints have rate limits where appropriate.
- [ ] Input is validated.
- [ ] Dependencies are regularly reviewed.
- [ ] Security-sensitive actions are audited.

### Secrets

- [ ] Secrets are not committed to Git.
- [ ] Secrets are not embedded in container images.
- [ ] Managed secret storage is used where appropriate.
- [ ] Secret access uses IAM roles.
- [ ] Rotation procedures exist.
- [ ] Secrets are excluded from logs.

### Data

- [ ] Data is encrypted at rest where required.
- [ ] Data is encrypted in transit where required.
- [ ] Database access is restricted.
- [ ] Backups are protected.
- [ ] Data retention follows requirements.
- [ ] Sensitive data is classified.

### Monitoring

- [ ] CloudTrail is enabled according to requirements.
- [ ] Application logs are centralized.
- [ ] WAF activity is monitored.
- [ ] Security findings are monitored.
- [ ] Important IAM changes generate appropriate alerts.
- [ ] Audit records have suitable retention.

### Deployment

- [ ] Production deployments are controlled.
- [ ] CI/CD access is restricted.
- [ ] Code changes are reviewed.
- [ ] Dependencies are scanned.
- [ ] Container images are scanned when applicable.
- [ ] Deployment events are auditable.
- [ ] Infrastructure changes are version controlled.

### Recovery

- [ ] Database backups exist.
- [ ] Recovery procedures are documented.
- [ ] Recovery procedures are tested.
- [ ] Security evidence is retained separately where required.
- [ ] Incident-response procedures exist.

## Common Mistakes

### Using AdministratorAccess for the Application

**Problem:** A compromised application can potentially perform highly privileged AWS operations.

**Better:** Give the instance profile only the permissions required by the application.

### Exposing PostgreSQL to the Internet

**Problem:** The database becomes directly reachable by external attackers.

**Better:** Keep the database private and allow access only from the application tier.

### Storing Secrets in Git

**Problem:** Git history can preserve credentials even after the file is deleted.

**Better:** Use managed secret storage and rotate any credential that has already been exposed.

### Using Long-Lived AWS Keys on EC2

**Problem:** Compromising the server can expose reusable AWS credentials.

**Better:** Use IAM roles and temporary credentials.

### Giving CI/CD Full AWS Administrator Access

**Problem:** A compromised CI/CD pipeline becomes a full AWS-account compromise path.

**Better:** Create a narrowly scoped deployment role.

### Assuming Security Groups Protect Application Authorization

**Problem:** Network controls cannot determine whether a user is allowed to modify a specific business resource.

**Better:** Enforce authorization in Django, FastAPI, or the relevant application layer.

### Exposing Redis Publicly

**Problem:** Redis becomes an external attack surface and may expose application data.

**Better:** Keep Redis private and restrict access to the application tier.

### Logging Authentication Secrets

**Problem:** Logs become a credential-leak vector.

**Better:** Log security events without logging the secret itself.

### Relying Only on WAF

**Problem:** WAF cannot identify every application-level business-logic vulnerability.

**Better:** Combine WAF with secure application design and authorization.

### Ignoring Outbound Traffic

**Problem:** A compromised application may communicate with unexpected external systems.

**Better:** Monitor and control outbound network behavior where the threat model requires it.

### Manual Production Changes

**Problem:** Manual changes create configuration drift and reduce auditability.

**Better:** Use Infrastructure as Code and controlled deployment pipelines.

### Never Testing Recovery

**Problem:** Backups and disaster-recovery plans may appear healthy but fail during an actual incident.

**Better:** Perform controlled restoration and recovery tests.

## Interview Perspective

### What are the most important security controls for Elastic Beanstalk?

A strong answer should cover multiple layers:

```text
IAM least privilege
+
Private networking
+
Restricted security groups
+
HTTPS/TLS
+
Secrets management
+
WAF
+
CloudTrail / CloudWatch
+
Secure application code
+
Controlled deployments
+
Backup and recovery
```

The important point is defense in depth.

### How would you secure a Django application running on Elastic Beanstalk?

A production-oriented answer would include:

1. Run the application behind an ALB.
2. Use HTTPS and secure cookies.
3. Restrict security groups.
4. Keep PostgreSQL and Redis private.
5. Use IAM roles rather than static AWS credentials.
6. Store secrets in managed secret storage.
7. Apply Django authentication and authorization correctly.
8. Use WAF and rate limiting where appropriate.
9. Centralize logs and audit security events.
10. Monitor CloudTrail and infrastructure changes.
11. Use controlled CI/CD deployments.
12. Maintain backups and test recovery.

### How would you prevent a compromised EC2 instance from accessing everything in AWS?

Use layered containment:

```text
IAM
 └── Least-privilege instance role

Network
 └── Restricted outbound/inbound connectivity

Secrets
 └── No static credentials

Runtime
 └── Minimal permissions and hardened application

Monitoring
 └── CloudTrail + GuardDuty + CloudWatch

Recovery
 └── Replace compromised instances rather than manually trusting them
```

The key principle is minimizing blast radius.

### Why is least privilege important?

If a workload is compromised, the attacker's effective permissions are limited by the permissions of the compromised identity.

```text
Broad IAM role
     ↓
Large blast radius

Least-privilege IAM role
     ↓
Smaller blast radius
```

Least privilege therefore limits both accidental and malicious actions.

### How would you secure communication between an application and database?

Use:

```text
Private network path
+
Security group restrictions
+
Database authentication
+
TLS where required
+
Least-privilege database credentials
+
Managed secret storage
```

Do not rely solely on the database password.

### Why use WAF if the application already validates input?

WAF provides an additional edge-level security layer.

```text
Internet
   ↓
WAF
   ↓
ALB
   ↓
Application validation
```

WAF can block or rate-limit malicious traffic before it consumes significant application resources.

It does not replace application security.

### How do you reduce the blast radius of a compromised deployment pipeline?

Use:

- Dedicated deployment roles.
- Least-privilege IAM policies.
- Short-lived credentials.
- Protected production branches.
- Code review.
- Automated security checks.
- Environment separation.
- Deployment auditing.
- Manual approval for high-risk production changes where appropriate.

### What is defense in depth?

Defense in depth means that no single security control is expected to stop every attack.

For Elastic Beanstalk:

```text
IAM
 ↓
Network
 ↓
WAF
 ↓
TLS
 ↓
Application security
 ↓
Database controls
 ↓
Monitoring
 ↓
Incident response
```

If one layer fails, additional layers can still limit the attack.

### How would you secure an Elastic Beanstalk environment handling sensitive customer data?

Start with data classification and threat modeling, then apply:

```text
Strict IAM
Private networking
Encryption
TLS
Managed secrets
Restricted database access
WAF
Audit logging
Centralized monitoring
Backup protection
Access reviews
Incident response
```

The exact controls should be driven by the sensitivity of the data and applicable regulatory requirements.

## Key Takeaways

- Elastic Beanstalk simplifies deployment but does not eliminate application, identity, network, data, or operational security responsibilities.
- Security should be designed as defense in depth rather than relying on a single AWS service.
- IAM should follow least privilege, with separate identities for developers, CI/CD, Elastic Beanstalk, and application workloads.
- EC2 instances should use IAM roles and temporary credentials rather than long-lived AWS access keys.
- CI/CD pipelines should use dedicated, narrowly scoped deployment identities and short-lived credentials where possible.
- Production databases and Redis should generally remain private and accessible only through controlled network paths.
- Security groups should expose only required ports and should prefer resource-to-resource security-group references where appropriate.
- Administrative access should be restricted and should not require publicly exposed management ports unless explicitly justified.
- HTTPS/TLS should protect external application traffic, credentials, authentication cookies, and sensitive data.
- Django and FastAPI applications still require application-level authentication, authorization, validation, and vulnerability protection even when AWS networking is secure.
- Secrets should be stored using appropriate managed secret mechanisms rather than source code, Git repositories, container images, or logs.
- Secret rotation should be designed and tested as an operational process rather than treated as a one-time configuration.
- Sensitive data should be protected both at rest and in transit according to its classification and applicable requirements.
- WAF provides an HTTP-layer defense and should complement, not replace, application security.
- Rate limiting helps protect APIs from brute-force attacks, abuse, and resource exhaustion.
- CloudTrail, CloudWatch, WAF logs, ALB logs, VPC Flow Logs, AWS Config, GuardDuty, and application audit logs provide complementary security visibility.
- Security-sensitive application events should be logged without exposing passwords, tokens, API keys, or other secrets.
- Controlled CI/CD deployments reduce configuration drift and improve auditability.
- Infrastructure as Code makes security configuration repeatable, reviewable, and easier to enforce consistently.
- Dependency, operating-system, platform, and container security should be treated as continuous maintenance responsibilities.
- Security controls should account for outbound traffic and potential lateral movement, not only inbound Internet traffic.
- Backups and disaster recovery are security controls because compromised or corrupted systems may require restoration.
- Recovery procedures should be tested rather than assumed to work.
- Security monitoring should be integrated with reliability monitoring because attacks frequently manifest as increased CPU, latency, network traffic, database connections, queue depth, or HTTP errors.
- The strongest Elastic Beanstalk security posture combines **least-privilege IAM + private networking + restricted security groups + TLS + managed secrets + WAF + secure application design + centralized monitoring + controlled deployments + tested recovery**.