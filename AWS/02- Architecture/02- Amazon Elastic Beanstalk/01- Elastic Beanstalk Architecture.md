# 01- Elastic Beanstalk Architecture

## Overview

AWS Elastic Beanstalk is an application deployment and infrastructure orchestration service rather than a compute service itself. It provisions and manages the AWS resources required to run an application, while exposing a higher-level environment abstraction to the engineering team.

A typical production architecture combines Elastic Beanstalk with services such as:

- Amazon EC2 for application compute
- Elastic Load Balancing for traffic distribution
- EC2 Auto Scaling for capacity management
- Amazon S3 for application-version artifacts
- AWS CloudFormation for infrastructure provisioning
- IAM for permissions
- Amazon CloudWatch for metrics, logs, and alarms
- Amazon SNS for operational notifications
- Amazon RDS or another managed database for persistent application data
- Amazon Route 53 for DNS
- AWS Certificate Manager for TLS certificates
- AWS WAF and CloudFront when edge protection and caching are required

The important architectural mindset is:

```text
Elastic Beanstalk
        │
        ▼
Infrastructure Orchestration
        │
        ├── EC2
        ├── Auto Scaling
        ├── Load Balancing
        ├── CloudFormation
        ├── S3
        ├── IAM
        └── CloudWatch
```

This distinction matters because production troubleshooting rarely ends at the Elastic Beanstalk console. Engineers often need to inspect the underlying load balancer, Auto Scaling group, EC2 instances, networking, IAM permissions, CloudFormation events, and application logs.

## High-Level Architecture

A common production request path is:

```text
Client
  │
  ▼
Route 53
  │
  ▼
Application Load Balancer
  │
  ▼
Elastic Beanstalk Environment
  │
  ├── EC2 Instance
  ├── EC2 Instance
  └── EC2 Instance
```

The compute layer is normally managed through an Auto Scaling group:

```text
                    Elastic Beanstalk
                           │
                           ▼
                 Application Environment
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
      Application Load             Auto Scaling
          Balancer                    Group
             │                           │
             │                ┌──────────┼──────────┐
             │                ▼          ▼          ▼
             └────────────► EC2       EC2        EC2
                              │          │          │
                              └──────────┼──────────┘
                                         ▼
                                   Application
```

For a backend API, the application instances may run a stack such as:

```text
ALB
 │
 ▼
Nginx
 │
 ▼
Gunicorn / Uvicorn
 │
 ▼
Django / FastAPI
 │
 ├── PostgreSQL
 ├── Redis
 └── Amazon S3
```

The exact application stack depends on the selected Elastic Beanstalk platform.

## Elastic Beanstalk as an Orchestration Layer

Elastic Beanstalk should not be thought of as a replacement for EC2, Auto Scaling, or a load balancer.

Instead, it provides an environment-level abstraction over multiple AWS resources.

Conceptually:

```text
Developer
   │
   ▼
Elastic Beanstalk
   │
   ├── Infrastructure provisioning
   ├── Application deployment
   ├── Environment configuration
   ├── Capacity management
   ├── Health monitoring
   └── Platform management
```

The resulting infrastructure can contain:

```text
CloudFormation
      │
      ├── VPC / Networking
      ├── Security Groups
      ├── Load Balancer
      ├── Auto Scaling Group
      ├── EC2 Instances
      └── Supporting resources
```

This abstraction reduces the amount of infrastructure that application teams must manage manually, but it does not remove the need to understand the underlying AWS architecture.

## Core AWS Services

| Service | Architectural Responsibility |
|---|---|
| Elastic Beanstalk | Environment and application orchestration |
| CloudFormation | Infrastructure provisioning and resource management |
| EC2 | Application compute |
| Auto Scaling | Capacity management and instance replacement |
| Elastic Load Balancing | Traffic distribution and health checks |
| S3 | Application-version artifact storage |
| IAM | Permissions and service access |
| CloudWatch | Metrics, logs, alarms, and observability |
| SNS | Notifications |
| Route 53 | DNS resolution |
| RDS | Managed relational database |
| Secrets Manager | Application secret management |
| ACM | TLS certificate management |
| WAF | Web-layer request filtering |

The exact resources created depend on environment configuration, platform, deployment mode, and enabled features.

## CloudFormation and Resource Provisioning

Elastic Beanstalk uses AWS infrastructure resources underneath the environment abstraction. CloudFormation is an important part of the provisioning model.

A simplified environment creation flow is:

```text
Create Environment
        │
        ▼
Elastic Beanstalk
        │
        ▼
Infrastructure Provisioning
        │
        ▼
AWS Resources
        │
        ├── Load Balancer
        ├── Auto Scaling Group
        ├── EC2 Instances
        ├── Security Groups
        └── Supporting Resources
```

CloudFormation becomes particularly important during infrastructure failures.

For example:

```text
Elastic Beanstalk Environment Creation
              │
              ▼
      CloudFormation Failure
              │
              ▼
      Resource Not Created
              │
              ▼
     Environment Creation Fails
```

When an environment fails to create or update, inspecting infrastructure events can provide information that is not obvious from the application deployment output.

## EC2 Application Layer

The EC2 instances ultimately execute the application workload.

A typical instance contains:

```text
EC2 Instance
    │
    ├── Operating System
    ├── Runtime
    ├── Application Dependencies
    ├── Application Code
    ├── Web Server / Process Manager
    └── Application Processes
```

For a Django application:

```text
EC2
 │
 ├── Amazon Linux
 ├── Python
 ├── Nginx
 ├── Gunicorn
 └── Django
```

For FastAPI:

```text
EC2
 │
 ├── Amazon Linux
 ├── Python
 ├── Nginx
 ├── Uvicorn / Gunicorn
 └── FastAPI
```

The EC2 layer should generally be treated as disposable.

Application state should not depend on a particular instance surviving indefinitely.

## Auto Scaling Architecture

A load-balanced Elastic Beanstalk environment normally uses an Auto Scaling group to maintain application capacity.

The basic model is:

```text
                Auto Scaling Group
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
           EC2-A     EC2-B     EC2-C
```

The Auto Scaling group maintains capacity according to environment configuration and scaling policies.

If an instance becomes unhealthy:

```text
EC2 Instance Failure
        │
        ▼
Instance Removed
        │
        ▼
Auto Scaling Launches Replacement
        │
        ▼
New EC2 Instance
        │
        ▼
Application Becomes Available
```

This is one of the reasons production environments should not depend on a single EC2 instance.

### Scaling

A simplified scaling flow is:

```text
Traffic Increase
      │
      ▼
Higher Resource Utilization
      │
      ▼
CloudWatch Metrics
      │
      ▼
Scaling Policy
      │
      ▼
Auto Scaling
      │
      ▼
Additional EC2 Instances
```

Scaling should be based on metrics that represent actual application demand. CPU utilization can be useful, but latency, request count, queue depth, and application-specific metrics may provide better signals depending on the workload.

## Elastic Load Balancer

Production Elastic Beanstalk environments commonly use an Application Load Balancer.

The ALB provides:

- Traffic distribution
- Target health checks
- Listener management
- HTTP/HTTPS routing
- TLS termination
- Integration with deployment and scaling workflows

The request flow is:

```text
Client
  │
  ▼
Application Load Balancer
  │
  ├── EC2-A
  ├── EC2-B
  └── EC2-C
```

The ALB prevents clients from needing to know which individual EC2 instance handles a request.

### Health Checks

The ALB continuously checks whether registered targets are healthy.

A backend might expose:

```text
GET /health
```

Example:

```json
{
  "status": "healthy"
}
```

A health endpoint should be intentionally designed.

A basic liveness endpoint may verify that the application process is responding. A deeper readiness check can verify critical dependencies, but overly expensive health checks can themselves create load and failure amplification.

## Multi-AZ Architecture

A production environment should normally distribute application capacity across multiple Availability Zones.

Example:

```text
                    Application Load Balancer
                         /            \
                        /              \
                       ▼                ▼
                  Availability      Availability
                     Zone A             Zone B
                       │                  │
                   EC2-A1              EC2-B1
                   EC2-A2              EC2-B2
```

If one Availability Zone experiences a failure, traffic can continue through healthy resources in another zone.

The architecture therefore changes from:

```text
Single AZ
   │
   ▼
EC2
```

to:

```text
             Load Balancer
              /         \
             ▼           ▼
          AZ-A          AZ-B
           │             │
         EC2            EC2
```

### Why Multi-AZ Matters

Multi-AZ deployment improves:

- Availability
- Fault tolerance
- Instance replacement options
- Resilience against AZ-level failures
- Operational flexibility during maintenance

Multi-AZ does not automatically make the entire application highly available. Dependencies such as databases, caches, queues, DNS, and external services must also be considered.

## Single-Instance Architecture

For development or experimentation, a single-instance environment can be useful:

```text
User
 │
 ▼
EC2
 │
 ▼
Application
```

Advantages:

- Low cost
- Simple configuration
- Fast deployment
- Easy debugging

Limitations:

- Single point of failure
- No meaningful application-level redundancy
- Limited scaling capability
- Maintenance can cause downtime

A single-instance environment should therefore not be treated as a production architecture for an availability-sensitive backend.

## Load-Balanced Production Architecture

A more appropriate production topology is:

```text
                         Users
                           │
                           ▼
                        Route 53
                           │
                           ▼
                 Application Load Balancer
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
           EC2-A         EC2-B         EC2-C
             │             │             │
             └─────────────┼─────────────┘
                           │
                           ▼
                     Backend Service
                           │
                  ┌────────┴────────┐
                  ▼                 ▼
             RDS PostgreSQL       Redis
```

For stateful dependencies, the architecture should keep persistent state outside the application instances.

## Application Version and S3 Flow

Elastic Beanstalk application versions are represented by deployable application artifacts. S3 is used as the backing storage for application-version artifacts.

A simplified deployment flow is:

```text
Developer
   │
   ▼
Application Artifact
   │
   ▼
Amazon S3
   │
   ▼
Elastic Beanstalk Application Version
   │
   ▼
Environment Deployment
   │
   ▼
EC2 Instances
```

This separation is important because the deployment artifact should be reproducible and independently identifiable from the running environment.

A production deployment should therefore avoid relying on an engineer's local machine as the only source of the deployable artifact.

## IAM Architecture

Elastic Beanstalk environments use IAM roles and permissions to allow AWS resources and services to perform required operations.

Common concepts include:

```text
Elastic Beanstalk
       │
       ├── Service Role
       │
       └── EC2 Instance Profile
```

The service role enables Elastic Beanstalk to perform management operations against AWS resources.

The EC2 instance profile provides AWS permissions to applications and processes running on the instances.

For example:

```text
EC2
 │
 ▼
Instance Profile
 │
 ├── CloudWatch access
 ├── S3 access
 └── Other explicitly required AWS APIs
```

Permissions should follow least privilege.

Avoid giving an application:

```text
AdministratorAccess
```

when it only requires access to a specific S3 bucket or a limited set of AWS APIs.

## Networking Architecture

A production deployment typically operates inside a VPC.

A common topology is:

```text
VPC
│
├── Public Subnet A
│     └── Load Balancer
│
├── Public Subnet B
│     └── Load Balancer
│
├── Private Subnet A
│     └── EC2
│
├── Private Subnet B
│     └── EC2
│
├── Private Database Subnet A
│     └── RDS
│
└── Private Database Subnet B
      └── RDS
```

The precise subnet placement depends on the Elastic Beanstalk environment and VPC design.

A common production principle is:

```text
Internet
   │
   ▼
Public Load Balancer
   │
   ▼
Private Application Instances
   │
   ▼
Private Database
```

This reduces the attack surface and prevents direct public access to application instances and databases.

## Request Lifecycle

For a Django backend, a production request can travel through several layers:

```text
Client
  │
  ▼
Route 53
  │
  ▼
Application Load Balancer
  │
  ▼
EC2 Instance
  │
  ▼
Nginx
  │
  ▼
Gunicorn
  │
  ▼
Django
  │
  ├── PostgreSQL
  ├── Redis
  └── S3
```

For FastAPI:

```text
Client
  │
  ▼
Route 53
  │
  ▼
Application Load Balancer
  │
  ▼
EC2 Instance
  │
  ▼
Nginx
  │
  ▼
Uvicorn / Gunicorn
  │
  ▼
FastAPI
```

The response follows the reverse path back toward the client.

Understanding this lifecycle is critical when diagnosing failures because an HTTP error does not necessarily originate in the application itself.

For example:

```text
502
 │
 ├── ALB
 ├── Nginx
 ├── Gunicorn / Uvicorn
 └── Application
```

Each layer must be investigated independently.

## Deployment Lifecycle

A simplified deployment lifecycle is:

```text
Developer
    │
    ▼
Build Artifact
    │
    ▼
S3
    │
    ▼
Application Version
    │
    ▼
Elastic Beanstalk Environment
    │
    ▼
Deployment Strategy
    │
    ▼
EC2 Instances
    │
    ▼
Health Validation
    │
    ▼
Production Traffic
```

The deployment strategy determines how existing and new application instances are handled.

Common strategies include:

- All at once
- Rolling
- Rolling with additional batch
- Immutable
- Blue/green
- Traffic splitting

For production systems, the choice should be based on failure tolerance, rollback requirements, deployment duration, and cost.

## Production Architecture

A practical backend architecture can combine Elastic Beanstalk with managed AWS services:

```text
                           Users
                             │
                             ▼
                          Route 53
                             │
                             ▼
                         CloudFront
                             │
                             ▼
                            WAF
                             │
                             ▼
                  Application Load Balancer
                             │
             ┌───────────────┼───────────────┐
             ▼               ▼               ▼
           EC2-A           EC2-B           EC2-C
             │               │               │
             └───────────────┼───────────────┘
                             │
                    Elastic Beanstalk
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         PostgreSQL        Redis           S3
            RDS
```

Observability operates alongside the request path:

```text
Application
    │
    ├── Metrics ───────► CloudWatch
    │
    ├── Logs ──────────► CloudWatch Logs
    │
    └── Events ────────► Operational Alerts
                              │
                              ▼
                             SNS
```

This separation is important: the application handles business requests while managed services provide persistence, storage, observability, and operational capabilities.

## Backend Application Design Considerations

Elastic Beanstalk works particularly well when the application is designed to be horizontally scalable.

### Stateless Application Instances

Application instances should avoid storing user-specific state locally.

Prefer:

```text
EC2-A ─┐
EC2-B ─┼──► Shared Persistent Services
EC2-C ─┘
```

rather than:

```text
EC2-A ──► Local Session
EC2-B ──► Local Session
EC2-C ──► Local Session
```

Persistent state should generally be moved to appropriate managed services.

Examples:

| Requirement | Preferred Location |
|---|---|
| Relational data | Amazon RDS / Aurora |
| Object uploads | Amazon S3 |
| Distributed cache | Redis |
| Application artifacts | Amazon S3 |
| Secrets | AWS Secrets Manager |
| Logs | CloudWatch Logs |

### User Uploads

Do not design production systems around EC2 local disk for durable user uploads.

Instead:

```text
Client
  │
  ▼
Application
  │
  ▼
Amazon S3
```

Instances may be replaced, scaled in, or recreated. Persistent user data should therefore live outside the instance lifecycle.

## Monitoring Architecture

CloudWatch provides the observability layer around the environment.

A simplified model is:

```text
Application / Infrastructure
          │
          ▼
      CloudWatch
          │
     ┌────┼────┐
     ▼    ▼    ▼
 Metrics Logs Alarms
             │
             ▼
          Actions
```

Useful production signals include:

- CPU utilization
- Request count
- Latency
- HTTP error rates
- Instance health
- Load balancer target health
- Application logs
- Deployment events
- Auto Scaling activity

Memory utilization may require additional monitoring configuration because it is not automatically available as a standard EC2 metric in the same way as CPU utilization.

## Health Monitoring

Health should be evaluated at multiple layers:

```text
Infrastructure
     │
     ▼
Load Balancer
     │
     ▼
EC2 Instance
     │
     ▼
Application Process
     │
     ▼
Application Dependency
```

For example:

```text
ALB Target
   │
   ├── Network reachable
   ├── Port accepting connections
   ├── Health endpoint responding
   └── Application process operational
```

A green environment does not eliminate the need for application-level monitoring. Business-level failures can occur while infrastructure remains technically healthy.

## Security Architecture

A production Elastic Beanstalk architecture should apply defense in depth.

```text
Internet
   │
   ▼
CloudFront / WAF
   │
   ▼
ALB
   │
   ▼
Application Instances
   │
   ▼
Private Database
```

Key practices include:

- HTTPS for external traffic
- TLS certificates managed through ACM
- Private application instances where appropriate
- Private database connectivity
- Security groups with minimal allowed traffic
- IAM least privilege
- Secrets Manager for sensitive configuration
- CloudTrail for API activity auditing
- Appropriate logging and monitoring

Avoid:

```text
Internet
   │
   ▼
Public EC2
   │
   ▼
Public Database
```

unless there is an explicit and justified architectural requirement.

## Reliability Considerations

A reliable Elastic Beanstalk architecture should assume that individual resources will fail.

Design for:

```text
Instance Failure
       ↓
Replacement

AZ Failure
       ↓
Traffic Continues In Another AZ

Deployment Failure
       ↓
Rollback

Application Failure
       ↓
Health Detection + Recovery

Database Failure
       ↓
Managed Recovery / Backup / Restore
```

Reliability is therefore a combination of:

- Redundancy
- Health checks
- Automated recovery
- Safe deployments
- Backups
- Monitoring
- Tested recovery procedures

## Cost Considerations

The cost of an Elastic Beanstalk environment is primarily driven by the AWS resources it provisions and uses rather than by application deployment alone.

Important cost drivers include:

- EC2 instance count and instance type
- Load balancers
- NAT gateways
- Data transfer
- RDS
- S3
- CloudWatch logs and metrics
- CloudFront
- WAF
- Additional environments used for staging or blue/green deployment

A development environment might use:

```text
Single Instance
```

while production may require:

```text
ALB
+
Multiple EC2 Instances
+
Multi-AZ
+
RDS
+
Observability
```

Blue/green deployments can temporarily increase infrastructure cost because two environments may coexist during a release.

Cost optimization should therefore never remove required redundancy merely to reduce the infrastructure bill.

## Troubleshooting the Architecture

When an Elastic Beanstalk environment fails, debug from the infrastructure boundary toward the application.

A useful sequence is:

```text
CloudFormation
      │
      ▼
Elastic Beanstalk Events
      │
      ▼
Environment Health
      │
      ▼
Load Balancer
      │
      ▼
Target Health
      │
      ▼
EC2 Instance
      │
      ▼
Platform / Web Server Logs
      │
      ▼
Application Logs
      │
      ▼
Dependencies
```

For a failed deployment:

```text
Deployment Failure
      │
      ├── Elastic Beanstalk Events
      ├── CloudFormation Events
      ├── Deployment Logs
      ├── Platform Hooks
      ├── EC2 Instance State
      └── Application Startup
```

For a `502`:

```text
502 Bad Gateway
      │
      ├── ALB listener
      ├── Target health
      ├── Security groups
      ├── Instance port
      ├── Nginx
      ├── Gunicorn / Uvicorn
      └── Application process
```

For a database connectivity failure:

```text
Application
    │
    ▼
EC2 Security Group
    │
    ▼
Database Security Group
    │
    ▼
Network / Subnet / Routing
    │
    ▼
RDS Endpoint
    │
    ▼
Database
```

The important principle is to avoid treating every application failure as an application-code problem.

## Common Architectural Mistakes

### Running Production on a Single Instance

```text
Single Instance
     │
     ▼
Single Point of Failure
```

Use multiple instances across Availability Zones when availability requirements justify it.

### Storing Persistent Data on EC2

Instances are replaceable infrastructure.

Avoid using instance-local storage as the authoritative location for user uploads or other durable application state.

### Making the Database Public

A backend database should generally be reachable only from the application tier and required administrative paths.

### Giving Excessive IAM Permissions

Avoid broad administrator permissions when the application requires only a small set of APIs.

### Skipping Health Checks

A load balancer cannot reliably route traffic if the health-check endpoint does not represent application readiness.

### Treating Elastic Beanstalk as a Black Box

Elastic Beanstalk simplifies infrastructure management but does not eliminate the underlying AWS resources.

Senior engineers should understand:

```text
Beanstalk
   ↓
CloudFormation
   ↓
ALB + Auto Scaling + EC2
   ↓
Application
```

### Deploying Without a Rollback Strategy

A successful deployment mechanism is incomplete if the team cannot safely recover from a bad release.

Deployment architecture should explicitly define:

```text
Deploy
  ↓
Validate
  ↓
Detect Failure
  ↓
Rollback
```

## Production Architecture Example

For a Django REST API:

```text
                           Internet
                              │
                              ▼
                           Route 53
                              │
                              ▼
                          CloudFront
                              │
                              ▼
                             WAF
                              │
                              ▼
                   Application Load Balancer
                              │
                  ┌───────────┼───────────┐
                  ▼           ▼           ▼
                EC2-A       EC2-B       EC2-C
                  │           │           │
                  └───────────┼───────────┘
                              │
                         Django / DRF
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
       RDS PostgreSQL       Redis              S3
             │
             ▼
        Persistent Data

Observability:
EC2 / ALB / Application
          │
          ▼
     CloudWatch
          │
          ▼
         SNS
```

A CI/CD workflow can sit outside the runtime request path:

```text
GitHub
   │
   ▼
GitHub Actions
   │
   ├── Build
   ├── Test
   ├── Security Scan
   └── Package
         │
         ▼
        S3
         │
         ▼
Elastic Beanstalk
         │
         ▼
Deployment Strategy
         │
         ▼
Health Validation
         │
         ▼
Production
```

This architecture separates:

- Runtime traffic
- Infrastructure management
- Persistent data
- Artifact storage
- Observability
- Deployment automation

That separation makes the system easier to scale and operate.

## Senior Engineer Perspective

The important architectural insight is that Elastic Beanstalk is not the complete production architecture.

It is an orchestration layer around a larger AWS system:

```text
                    Elastic Beanstalk
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   Infrastructure       Application      Operations
          │                │                │
     ┌────┼────┐       ┌───┼───┐       ┌───┼────┐
     ▼    ▼    ▼       ▼   ▼   ▼       ▼   ▼    ▼
    EC2  ALB   ASG    Django FastAPI  CW  IAM  S3
```

A senior backend engineer should be able to answer questions such as:

- Which AWS resource is actually serving the request?
- Where is the application artifact stored?
- What happens when an EC2 instance fails?
- How does the load balancer determine target health?
- What happens when a deployment fails?
- Where should persistent application state live?
- Which IAM role grants an operation permission?
- Which layer should be investigated for a `502` or `503`?
- How does the system behave during an Availability Zone failure?
- How can the deployment be rolled back safely?
- Which components create the largest operational or financial risk?

The key architectural mindset is:

```text
Do not troubleshoot only Elastic Beanstalk.

Troubleshoot the AWS architecture
that Elastic Beanstalk manages.
```

## Key Takeaways

- Elastic Beanstalk is an application deployment and infrastructure orchestration layer, not a standalone compute service.
- EC2 instances execute the application workload.
- Auto Scaling manages application capacity and instance replacement.
- Application Load Balancers distribute traffic and perform target health checks.
- Multi-AZ deployment improves availability and fault tolerance.
- Application versions are backed by Amazon S3 artifacts.
- CloudFormation is important for understanding infrastructure provisioning and environment failures.
- IAM roles provide the permissions required by Elastic Beanstalk-managed resources and applications.
- CloudWatch provides the foundation for infrastructure and application observability.
- Production applications should remain as stateless as practical and keep persistent state in managed services.
- Databases, uploads, secrets, and application artifacts should not depend on the lifecycle of an individual EC2 instance.
- A production architecture should combine load balancing, Auto Scaling, appropriate networking, security controls, monitoring, backups, and safe deployment strategies.
- Effective troubleshooting requires understanding the underlying AWS resources rather than treating Elastic Beanstalk as a black box.