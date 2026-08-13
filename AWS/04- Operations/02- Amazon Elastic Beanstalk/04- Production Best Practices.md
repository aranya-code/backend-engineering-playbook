# 04- Production Best Practices

## Overview

Amazon Elastic Beanstalk is suitable for production backend workloads when the environment is treated as an operational platform rather than simply a deployment shortcut. Production reliability depends on correct application configuration, instance sizing, networking, health checks, deployment strategy, observability, security, and controlled infrastructure changes.

A production Elastic Beanstalk architecture commonly looks like:

```text
                         Internet
                            │
                            ▼
                    Route 53 / DNS
                            │
                            ▼
                    Application Load
                       Balancer
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
        EC2 Instance                  EC2 Instance
        Elastic Beanstalk             Elastic Beanstalk
              │                           │
        Nginx / App                    Nginx / App
              │                           │
              └─────────────┬─────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
           PostgreSQL                  Redis
           RDS / Aurora              ElastiCache
```

The goal is not to eliminate infrastructure concerns. It is to establish sensible defaults and operational controls so that application teams can deploy and operate services consistently.

## Production Architecture Principles

A production Elastic Beanstalk environment should generally follow these principles:

| Area | Production recommendation |
|---|---|
| Compute | Use Auto Scaling with appropriate instance types |
| Availability | Deploy across multiple Availability Zones |
| Traffic | Use a load-balanced environment |
| Database | Prefer Amazon RDS or another managed database |
| Caching | Use ElastiCache when caching is required |
| Secrets | Use AWS Secrets Manager or Systems Manager Parameter Store |
| Logging | Centralize application and infrastructure logs |
| Monitoring | Combine metrics, health signals, logs, and alarms |
| Deployment | Use controlled, repeatable CI/CD deployments |
| Security | Apply least-privilege IAM and restrictive network rules |
| TLS | Terminate HTTPS at the load balancer where appropriate |
| DNS | Use Route 53 or another managed DNS provider |
| Recovery | Maintain rollback and disaster-recovery procedures |
| Configuration | Treat environment configuration as controlled infrastructure |

## Environment Separation

Do not use a single Elastic Beanstalk environment for every stage.

A typical setup is:

```text
Development
    │
    ▼
Staging
    │
    ▼
Production
```

Each environment should have independent:

- Configuration
- Secrets
- Databases
- IAM permissions
- Scaling policies
- Monitoring
- Deployment controls

For example:

```text
my-api-dev
my-api-staging
my-api-production
```

This prevents a development experiment from directly affecting production infrastructure.

## Application Configuration

Application configuration should be externalized from application code.

Typical configuration includes:

```text
DATABASE_HOST
DATABASE_PORT
DATABASE_NAME
REDIS_URL
DJANGO_SETTINGS_MODULE
LOG_LEVEL
ENVIRONMENT
```

Example Python configuration:

```python
import os

DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.environ.get("REDIS_URL")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")
```

Do not hard-code environment-specific values:

```python
DATABASE_HOST = "production-db.example.internal"
```

Configuration should be supplied through Elastic Beanstalk environment configuration or an appropriate secrets/configuration service.

## Secrets Management

Secrets should not be committed to Git or embedded directly into application source code.

Avoid:

```python
SECRET_KEY = "hard-coded-production-secret"
DATABASE_PASSWORD = "production-password"
```

Prefer a managed secret source and inject configuration into the application securely.

Common options include:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- Elastic Beanstalk environment configuration for non-sensitive configuration

A useful distinction is:

| Configuration | Recommended storage |
|---|---|
| Application mode | Environment configuration |
| Log level | Environment configuration |
| Database password | Secrets Manager / Parameter Store |
| API credentials | Secrets Manager |
| Encryption keys | Dedicated secret/key management |
| Feature flags | Appropriate configuration system |

## IAM Least Privilege

Elastic Beanstalk relies on IAM roles for platform operations and application access.

Do not give the application broad administrative permissions simply because it simplifies development.

Bad:

```text
Application role
    ↓
AdministratorAccess
```

Prefer:

```text
Application
    ↓
IAM Role
    ├── Read required S3 objects
    ├── Read required secrets
    └── Publish required metrics
```

Every permission should have a business or operational reason.

Separate:

- Elastic Beanstalk service roles
- EC2 instance profiles
- CI/CD deployment roles
- Developer roles
- Read-only operational roles

This also improves auditability.

## Network Architecture

Production environments should normally run inside an appropriately designed VPC.

A typical architecture is:

```text
                         Internet
                            │
                            ▼
                    Public Subnets
                    ┌──────────────┐
                    │     ALB      │
                    └──────┬───────┘
                           │
                  ┌────────┴────────┐
                  ▼                 ▼
             Private Subnet    Private Subnet
                  │                 │
                  ▼                 ▼
                EC2-A             EC2-B
                  │                 │
                  └────────┬────────┘
                           │
                           ▼
                    Database Subnets
                           │
                           ▼
                         RDS
```

The exact subnet design depends on application requirements, but production systems should avoid exposing databases directly to the public internet.

## Security Groups

Security groups should represent actual communication requirements.

For example:

```text
Internet
   │
   │ HTTPS :443
   ▼
ALB Security Group
   │
   │ Application port
   ▼
EC2 Security Group
   │
   │ PostgreSQL :5432
   ▼
RDS Security Group
```

Avoid:

```text
RDS
└── 0.0.0.0/0 :5432
```

Prefer allowing database traffic only from the application security group.

## Load Balancing

For production APIs, a load-balanced Elastic Beanstalk environment is generally preferable to a single-instance environment.

A load balancer provides:

- Traffic distribution
- Instance health integration
- Horizontal scaling
- Failure isolation
- TLS termination options

Request flow:

```text
Client
  │
  ▼
Application Load Balancer
  │
  ├── EC2 Instance A
  ├── EC2 Instance B
  └── EC2 Instance C
```

If one instance becomes unhealthy, traffic can be redirected to healthy instances.

## Auto Scaling

Auto Scaling should be based on actual application behavior rather than arbitrary instance counts.

Important parameters include:

- Minimum instances
- Maximum instances
- Desired capacity
- Scaling metrics
- Scaling thresholds
- Cooldown or stabilization behavior

For example:

```text
Minimum: 2
Desired: 2
Maximum: 8
```

Two instances provide baseline redundancy while allowing the environment to scale under load.

Do not assume CPU utilization alone represents application load.

An API may be constrained by:

- Database connections
- External APIs
- Memory
- Network throughput
- Request latency
- Worker capacity

## Instance Sizing

Choose EC2 instance types based on measured workload characteristics.

Consider:

| Resource | Symptoms of insufficient capacity |
|---|---|
| CPU | High CPU, increased latency |
| Memory | OOM kills, process restarts |
| Network | Throughput saturation |
| Disk | Slow writes, application failures |
| Connections | Database connection exhaustion |

Do not immediately scale vertically when performance degrades.

First identify the bottleneck.

## Database Architecture

For production workloads, the application database should generally be a managed database service rather than a database running on an Elastic Beanstalk instance.

Example:

```text
Elastic Beanstalk
       │
       │ PostgreSQL
       ▼
Amazon RDS
```

Benefits include:

- Managed backups
- Automated maintenance capabilities
- Multi-AZ options
- Monitoring integration
- Easier operational management

Application instances should remain stateless where practical.

## Database Connection Management

A common production failure is exhausting database connections.

For example:

```text
8 EC2 instances
×
20 application connections
=
160 database connections
```

The actual safe number depends on database capacity and the rest of the workload.

Django configuration should therefore be designed with connection behavior in mind.

Example:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ["DB_HOST"],
        "PORT": os.environ.get("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}
```

Connection pooling may also be appropriate for high-throughput systems.

## Application Statelessness

Elastic Beanstalk works particularly well when application instances are stateless.

Avoid storing critical application state only on the local filesystem.

Bad:

```text
EC2 Instance A
└── /var/app/uploads
```

If the instance disappears, the data may disappear with it.

Prefer:

```text
Application
   │
   ├── Files ───────► S3
   ├── Sessions ────► Redis / Database
   ├── Database ────► RDS
   └── Cache ───────► ElastiCache
```

Stateless instances make scaling and replacement much safer.

## File Storage

User-generated files should generally not depend on EC2 local storage.

For a Django application:

```text
Django
  │
  ▼
Object storage
  │
  ▼
Amazon S3
```

This allows instances to be replaced without losing application data.

It also makes horizontal scaling easier because every instance can access the same durable storage.

## Background Processing

Long-running tasks should not block synchronous API requests.

A common backend architecture is:

```text
Client
  │
  ▼
Django / FastAPI
  │
  ├── Immediate response
  │
  └── Queue
        │
        ▼
      Celery
        │
        ▼
     Worker
        │
        ▼
     Database / External API
```

Redis or another suitable broker can be used depending on requirements.

Avoid running CPU-intensive or long-running background work directly inside web request processes.

## Deployment Strategy

Production deployments should be repeatable and automated.

A typical flow is:

```text
Git
 │
 ▼
CI Pipeline
 │
 ├── Tests
 ├── Static checks
 ├── Build artifact
 └── Security checks
 │
 ▼
Elastic Beanstalk
 │
 ▼
Staging
 │
 ▼
Production
```

Deployment should not depend on an engineer manually modifying an EC2 instance.

## Immutable and Controlled Deployments

Avoid modifying production instances manually.

For example, do not use:

```bash
ssh production-instance
sudo pip install package
sudo vim application.py
```

Such changes create configuration drift.

Instead:

```text
Source Control
     ↓
Build
     ↓
Test
     ↓
Deploy
     ↓
Elastic Beanstalk
```

If a production instance needs manual modification to remain healthy, the underlying deployment process should usually be corrected.

## Database Migrations

Database migrations require special care during deployments.

A migration may affect every application instance.

A safer deployment model considers compatibility between:

```text
Old application
       +
New database schema
       +
New application
```

Prefer backward-compatible migrations where practical.

For example:

```text
Phase 1:
Add nullable column

Phase 2:
Deploy application using new column

Phase 3:
Backfill data

Phase 4:
Enforce constraints if required
```

Avoid migrations that require all application instances to stop simultaneously unless downtime is explicitly acceptable.

## Health Checks

Health checks should test whether the application can actually serve traffic.

A basic endpoint might be:

```text
GET /health
```

However, a health endpoint should be designed carefully.

A simple liveness check:

```text
Application process is running
        ↓
HTTP 200
```

A deeper readiness check might validate:

```text
Application
   │
   ├── Database connectivity
   ├── Required dependency availability
   └── Configuration validity
```

Do not make every health check dependent on slow external services.

A failing third-party API should not necessarily make the entire application appear unavailable.

## Monitoring and Observability

Production monitoring should combine:

```text
Metrics
+
Logs
+
Health
+
Traces where applicable
+
Alerts
```

Important signals include:

- Request rate
- Error rate
- Latency
- HTTP 4xx
- HTTP 5xx
- CPU utilization
- Memory utilization
- Instance count
- Database connections
- Database CPU
- Queue depth
- Background task failures

A useful operational model is:

```text
Golden Signals
├── Latency
├── Traffic
├── Errors
└── Saturation
```

## Logging

Logs should be structured and centralized.

Example:

```json
{
  "timestamp": "2026-08-13T10:30:00Z",
  "level": "ERROR",
  "service": "orders-api",
  "request_id": "abc123",
  "operation": "create_order",
  "status_code": 500,
  "error": "DatabaseError"
}
```

Avoid logging:

- Passwords
- API tokens
- Access keys
- Authorization headers
- Database credentials
- Sensitive personal information

Production logging should optimize for both diagnostic value and security.

## Alerting

Alerts should represent actionable conditions.

Good:

```text
HTTP 5xx rate > 5% for 5 minutes
```

Weak:

```text
One ERROR log occurred
```

Good alerts should provide:

- Condition
- Severity
- Affected environment
- Useful context
- Escalation path

Alert fatigue reduces operational effectiveness, so thresholds should be based on service behavior and business impact.

## HTTPS and TLS

Production applications should use HTTPS.

Typical flow:

```text
Client
  │
  │ HTTPS
  ▼
Application Load Balancer
  │
  │ HTTP or HTTPS
  ▼
Elastic Beanstalk Instances
```

TLS termination at the load balancer can simplify certificate management.

Use managed certificates where appropriate and redirect HTTP traffic to HTTPS.

Applications should also correctly handle proxy headers and secure-cookie configuration when operating behind a load balancer.

For Django, production security settings commonly include:

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

These settings should be enabled only when the deployment architecture correctly communicates the original HTTPS request to Django.

## DNS

Use a managed DNS solution such as Route 53 for production domains where appropriate.

A typical architecture is:

```text
api.example.com
       │
       ▼
Route 53
       │
       ▼
Application Load Balancer
       │
       ▼
Elastic Beanstalk
```

Avoid embedding environment-specific IP addresses into application configuration.

Load balancer addresses can change as infrastructure evolves.

## Caching

Redis or another cache can reduce database load and improve latency.

Example:

```text
Client
  ↓
API
  ↓
Redis
  ├── Cache hit → Response
  │
  └── Cache miss
          ↓
       PostgreSQL
```

Caching should be applied based on measured bottlenecks.

Consider:

- Cache invalidation
- TTL
- Memory limits
- Key design
- Stampede protection
- Failure behavior

Do not make the entire application dependent on the cache unless the architecture explicitly supports that dependency.

## Security Hardening

Production Elastic Beanstalk environments should minimize unnecessary exposure.

Recommended practices include:

- HTTPS
- Private database subnets
- Restrictive security groups
- Least-privilege IAM
- Secret management
- Regular dependency updates
- Controlled administrative access
- Centralized auditing
- Log protection
- Security monitoring

Do not expose administrative services unnecessarily.

For example:

```text
Internet → SSH :22
```

should not be the default management model for production instances.

Prefer controlled administrative access mechanisms appropriate to the environment.

## Dependency Management

Pin production dependencies to controlled versions.

Example:

```text
Django==5.2.3
gunicorn==23.0.0
psycopg[binary]==3.2.9
redis==6.2.0
```

The exact versions should be selected and tested according to the application's compatibility requirements.

Avoid deploying untested dependency upgrades directly to production.

Use CI to validate:

```text
Dependency update
      ↓
Tests
      ↓
Security checks
      ↓
Staging
      ↓
Production
```

## Python Application Configuration

A production Django or FastAPI application should separate:

```text
Source code
+
Environment configuration
+
Secrets
+
Infrastructure configuration
```

For Django, production configuration commonly includes:

```python
DEBUG = False

ALLOWED_HOSTS = [
    "api.example.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://api.example.com",
]
```

Do not use:

```python
DEBUG = True
ALLOWED_HOSTS = ["*"]
```

as a production default.

## Web Server and Application Server

A Python backend should generally run behind an appropriate production application server.

For example:

```text
ALB
 │
 ▼
Nginx
 │
 ▼
Gunicorn
 │
 ▼
Django
```

or:

```text
ALB
 │
 ▼
Nginx
 │
 ▼
Uvicorn
 │
 ▼
FastAPI
```

The exact Elastic Beanstalk platform configuration determines the supported deployment model.

The important principle is that the production process model should be explicitly configured and monitored rather than relying on a development server.

## Worker and Process Capacity

Application performance depends on process and worker configuration.

For a Python web application, capacity may depend on:

```text
Instance CPU
+
Instance memory
+
Web workers
+
Threads
+
Database connections
+
Request latency
```

Increasing worker count indefinitely can make the system worse by increasing:

- Memory consumption
- Database connections
- CPU contention
- Context switching

Worker sizing should be based on load testing and observed resource usage.

## Graceful Shutdown

Production applications should handle process termination gracefully.

During deployments or scaling events:

```text
Instance receives termination signal
        ↓
Stop accepting new work
        ↓
Finish active requests
        ↓
Close resources
        ↓
Process exits
```

Poor shutdown handling can cause:

- Dropped requests
- Partial jobs
- Duplicate processing
- Failed deployments

Background workers should also implement appropriate graceful shutdown behavior.

## Reliability and High Availability

A production environment should avoid a single point of failure where practical.

For example:

```text
Availability Zone A       Availability Zone B
       │                         │
       ▼                         ▼
     EC2-A                     EC2-B
       │                         │
       └──────────┬──────────────┘
                  ▼
                  ALB
```

Use multiple instances and Availability Zones when the workload requires high availability.

A single-instance environment may be acceptable for development or low-criticality workloads but should not be assumed to provide production-grade redundancy.

## Disaster Recovery

Production readiness includes recovery planning.

Identify:

- Database backup strategy
- Recovery Point Objective
- Recovery Time Objective
- Application artifact availability
- Infrastructure recreation process
- Secret recovery process
- DNS recovery
- Dependency recovery

A disaster recovery workflow might be:

```text
Infrastructure failure
        ↓
Provision replacement environment
        ↓
Restore configuration
        ↓
Restore / reconnect database
        ↓
Deploy application
        ↓
Validate health
        ↓
Restore traffic
```

A backup is useful only if the recovery procedure has been validated.

## Rollback Strategy

Every production deployment should have a rollback strategy.

Possible mechanisms include:

- Previous application version
- Deployment rollback
- Environment swap strategies
- Re-deployment of a known-good artifact

A rollback should be fast enough for the application's operational requirements.

The key principle is:

```text
Known-good version
        ↓
Always recoverable
```

Do not assume that the latest source code can reproduce the exact previous production state.

## Infrastructure as Code

Production environments should be reproducible.

Use infrastructure-as-code mechanisms where appropriate, such as:

- CloudFormation
- AWS CDK
- Terraform

Store infrastructure configuration in version control.

Example:

```text
Git Repository
│
├── application/
├── .ebextensions/
├── .platform/
├── infrastructure/
└── CI/CD configuration
```

This reduces configuration drift and improves recovery.

## Elastic Beanstalk Configuration

Elastic Beanstalk configuration should be version-controlled where practical.

Common configuration mechanisms include:

```text
.ebextensions/
.platform/
Environment configuration
CI/CD configuration
Infrastructure as Code
```

Avoid making undocumented production changes through the console.

If a configuration change matters to production, it should ideally be reproducible.

## Configuration Drift

Configuration drift occurs when production differs from the configuration represented in source control or infrastructure definitions.

Example:

```text
Git configuration
    │
    └── Worker count = 4

Production
    │
    └── Worker count = 8
```

The discrepancy may remain invisible until the environment is recreated.

The solution is to make configuration changes through controlled processes and periodically verify actual state against intended state.

## Cost Optimization

Production optimization should consider both performance and cost.

Important cost drivers include:

- EC2 instance size
- Number of instances
- Load balancer usage
- RDS capacity
- Data transfer
- CloudWatch logs
- NAT Gateway usage
- ElastiCache
- S3 storage
- Monitoring configuration

Do not optimize cost by blindly reducing capacity.

Instead:

```text
Measure
  ↓
Identify waste
  ↓
Optimize
  ↓
Load test
  ↓
Validate reliability
```

An inexpensive system that cannot meet its availability or latency requirements is not production-optimized.

## Performance Testing

Load test the application before relying on Auto Scaling in production.

Measure:

```text
Requests/second
Latency
Error rate
CPU
Memory
Database connections
Database latency
Queue depth
```

Example:

```text
100 RPS
  ↓
200 RPS
  ↓
500 RPS
  ↓
1000 RPS
```

Observe where the first significant bottleneck appears.

The bottleneck may be the database rather than Elastic Beanstalk itself.

## Capacity Planning

Capacity planning should connect traffic to infrastructure limits.

For example:

```text
Traffic
  ↓
Application workers
  ↓
Database connections
  ↓
Database capacity
```

If each instance can safely process 200 requests/second and production requires 500 requests/second, the theoretical minimum is more than two instances once redundancy and headroom are considered.

Capacity planning should include:

- Peak traffic
- Growth rate
- Failure scenarios
- Deployment capacity
- Database limits
- External dependency limits

## Operational Runbooks

Production environments should have documented procedures for common incidents.

Useful runbooks include:

```text
High 5xx rate
Database connectivity failure
502 / 503 responses
Unhealthy instances
Deployment rollback
High CPU
High memory
Auto Scaling failure
SSL certificate issue
DNS issue
CloudFormation failure
Environment configuration drift
```

A runbook should contain:

- Detection
- Diagnostic commands
- Relevant dashboards
- Expected symptoms
- Remediation steps
- Escalation criteria
- Rollback procedure

## Change Management

Infrastructure changes should be controlled.

A production change should ideally have:

```text
Change
  ↓
Review
  ↓
Testing
  ↓
Deployment
  ↓
Monitoring
  ↓
Validation
```

Avoid making multiple unrelated infrastructure changes simultaneously.

If something fails, a small change set makes root-cause analysis much easier.

## Observability During Changes

Always monitor the environment during deployments and configuration changes.

Watch:

```text
Health
5xx rate
Latency
CPU
Memory
Instance count
Database connections
Application logs
Elastic Beanstalk events
```

A deployment is not complete merely because the deployment command succeeds.

The real validation is:

```text
Deployment succeeds
        +
Application remains healthy
        +
Traffic succeeds
        +
Latency remains acceptable
```

## Production Checklist

```text
[ ] Separate development, staging, and production environments
[ ] Production uses a load-balanced environment where appropriate
[ ] Multiple instances are configured for required availability
[ ] Instances span multiple Availability Zones where required
[ ] Auto Scaling limits are defined
[ ] Instance types are validated through load testing
[ ] Application is stateless where practical
[ ] Persistent files are stored outside instance-local storage
[ ] Database uses an appropriate managed architecture
[ ] Database connection limits are understood
[ ] Security groups follow least privilege
[ ] Database is not publicly exposed unnecessarily
[ ] HTTPS is enabled
[ ] DNS is managed appropriately
[ ] Secrets are not committed to source control
[ ] IAM roles follow least privilege
[ ] CI/CD deployments are repeatable
[ ] Production deployments use tested artifacts
[ ] Database migrations are deployment-safe
[ ] Health checks are configured correctly
[ ] Application logs are centralized
[ ] Metrics and alarms are configured
[ ] CloudTrail auditing is enabled according to requirements
[ ] Request correlation IDs are available
[ ] Sensitive data is excluded from logs
[ ] Application dependencies are controlled
[ ] Configuration is version-controlled where practical
[ ] Configuration drift is minimized
[ ] Rollback procedures are documented
[ ] Database backups are configured
[ ] Disaster recovery procedures are documented
[ ] Recovery procedures have been tested
[ ] Incident runbooks exist
[ ] Performance has been load tested
[ ] Capacity planning includes failure scenarios
[ ] CloudWatch and infrastructure costs are monitored
[ ] Production changes are reviewed and auditable
```

## Common Production Mistakes

### Running a Single Instance

A single instance creates a direct availability dependency on one EC2 instance.

**Avoid it:** use multiple instances and a load-balanced environment when availability requirements justify it.

### Storing Files Locally

Instance-local storage does not provide durable shared storage for horizontally scaled applications.

**Avoid it:** use services such as Amazon S3 for persistent object storage.

### Using Hard-Coded Secrets

Secrets embedded in source code can leak through Git history, logs, or deployment artifacts.

**Avoid it:** use managed secret storage and runtime configuration.

### Using Broad IAM Permissions

Giving applications administrative permissions increases the blast radius of a compromised application.

**Avoid it:** define narrowly scoped IAM policies.

### Manual Production Changes

Manual changes create configuration drift and make recovery unpredictable.

**Avoid it:** use CI/CD and infrastructure-as-code workflows.

### No Rollback Plan

A deployment can succeed technically while the application becomes unhealthy.

**Avoid it:** maintain a known-good version and test rollback procedures.

### Ignoring Database Capacity

Scaling EC2 instances does not automatically scale the database.

**Avoid it:** monitor database connections, CPU, storage, latency, and query performance.

### Treating Auto Scaling as a Performance Solution

Auto Scaling addresses capacity changes, not every type of bottleneck.

**Avoid it:** determine whether the constraint is CPU, memory, database, network, queueing, or an external dependency.

### Overloading Health Checks

A health check that depends on every downstream service can incorrectly mark healthy application instances as unhealthy.

**Avoid it:** distinguish liveness and readiness requirements and keep health checks fast and intentional.

### No Centralized Logs

Local logs can disappear when instances are terminated.

**Avoid it:** centralize logs and define appropriate retention.

## Interview Traps

### Is Elastic Beanstalk Serverless?

No. Elastic Beanstalk is a managed application deployment platform that provisions and manages underlying AWS resources such as EC2 instances, load balancers, and Auto Scaling components.

### Does Elastic Beanstalk Automatically Make an Application Highly Available?

No.

High availability depends on the environment configuration, including multiple instances, Availability Zones, load balancing, database architecture, and application design.

### Does Auto Scaling Fix Slow Database Queries?

No.

Auto Scaling may add application capacity, but the database can remain the bottleneck.

### Should Application State Be Stored on the EC2 Instance?

Generally no for horizontally scaled production applications.

Persistent state should be moved to appropriate managed services such as RDS, S3, or ElastiCache.

### Why Is Statelessness Important?

Stateless applications can be replaced and scaled without losing critical application state.

### Why Use Infrastructure as Code?

It makes infrastructure changes reproducible, reviewable, version-controlled, and easier to recover.

### Is a Successful Deployment Command Proof That Production Is Healthy?

No.

The application must be validated through health checks, metrics, logs, error rates, and real traffic behavior.

### Why Is a Rollback Strategy Necessary?

Because a deployment can introduce runtime failures even when build and deployment steps complete successfully.

## Key Takeaways

- Treat Elastic Beanstalk as a production platform, not merely a deployment command.
- Separate development, staging, and production environments.
- Use load balancing and multiple instances when availability requirements demand them.
- Design environments for failure rather than assuming EC2 instances will remain permanent.
- Keep application instances stateless wherever practical.
- Store persistent data in appropriate managed services such as RDS, S3, and ElastiCache.
- Use Auto Scaling based on measured workload behavior and understand that scaling application instances does not automatically solve database or external dependency bottlenecks.
- Protect production environments with least-privilege IAM, restrictive security groups, HTTPS, and managed secret storage.
- Keep application configuration separate from source code and avoid hard-coded environment-specific values.
- Use repeatable CI/CD deployments instead of manually modifying production instances.
- Treat database migrations as part of the deployment architecture and design them for compatibility during rolling changes.
- Centralize logs and combine them with metrics, health signals, and alerts.
- Use CloudTrail to audit AWS control-plane activity and Elastic Beanstalk events to understand environment operations.
- Make production infrastructure reproducible through configuration management and infrastructure as code.
- Minimize configuration drift by ensuring production changes are controlled and represented in version-controlled configuration where practical.
- Maintain tested rollback and disaster-recovery procedures.
- Load test before production and use measured capacity planning rather than guessing instance sizes.
- Monitor the entire dependency chain: load balancer, application, database, cache, queues, and external services.
- A production deployment is successful only when the application remains healthy under real traffic after the change.
- Production readiness is ultimately the combination of **reliability, security, observability, scalability, recoverability, and controlled operations**.