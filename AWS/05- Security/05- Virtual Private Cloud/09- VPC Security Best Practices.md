# 09- VPC Security Best Practices

## Overview

Amazon VPC security is not a single control. It is the combined effect of network segmentation, routing, Security Groups, Network ACLs, VPC endpoints, identity controls, encryption, logging, monitoring, and workload-level security.

A production VPC should be designed around **least privilege, explicit trust boundaries, controlled network paths, defense in depth, and observable traffic**.

A useful mental model is:

```text
                         Internet
                            |
                            v
                    Internet-facing ALB
                            |
                     Public Subnet
                            |
                            v
                  Private Application Tier
                     /             \
                    /               \
                   v                 v
                Redis             PostgreSQL
              Private Tier       Private Tier
                   |
                   v
                 Kafka
             Private Subnets
```

The security objective is not simply to make resources private. The objective is to ensure that:

- Only required traffic is permitted.
- Public exposure is intentional.
- Private workloads have controlled egress.
- Sensitive services have narrow inbound trust relationships.
- Administrative access is controlled.
- Network activity is observable.
- Security controls are reproducible through Infrastructure as Code.
- Failures and security incidents can be investigated.

For backend systems, this directly affects Django, FastAPI, REST APIs, gRPC services, Celery workers, Redis, PostgreSQL, Kafka, Docker workloads, Kubernetes clusters, and AWS-managed services.

---

## VPC Security Architecture

A production VPC commonly separates workloads by function rather than placing everything into one subnet.

```mermaid
flowchart TB
    Internet["Internet"]

    ALB["Public ALB"]

    subgraph VPC["Production VPC"]
        Public["Public Subnets"]

        subgraph App["Private Application Subnets"]
            API["Django / FastAPI"]
            Worker["Celery Workers"]
            Services["Microservices"]
        end

        subgraph Data["Private Data Subnets"]
            DB["PostgreSQL / RDS"]
            Redis["Redis"]
            Kafka["Kafka"]
        end

        NAT["NAT Gateway"]
        Endpoint["VPC Endpoints"]
    end

    Internet --> ALB
    ALB --> API
    API --> DB
    API --> Redis
    API --> Services
    Worker --> DB
    Worker --> Redis
    Services --> Kafka

    API --> NAT
    Worker --> NAT
    API --> Endpoint
    Worker --> Endpoint
```

The important boundary is not merely:

```text
Public vs Private
```

It is:

```text
Who can communicate with whom?
Over which protocol?
On which port?
Through which network path?
For what reason?
```

---

## Core Security Principles

The most important VPC security principles are:

| Principle | Practical Meaning |
|---|---|
| Least privilege | Allow only required network communication |
| Defense in depth | Use multiple independent security controls |
| Segmentation | Separate workloads according to trust and function |
| Private by default | Avoid unnecessary public exposure |
| Explicit egress | Control where sensitive workloads can connect |
| Strong identity | Prefer IAM-based access over network location alone |
| Encryption | Protect traffic and data |
| Observability | Log and analyze network behavior |
| Automation | Manage security controls through IaC |
| Continuous validation | Detect drift and unintended exposure |

A senior-level VPC design should be able to explain **why every permitted network path exists**.

---

## Private Subnets by Default

Backend workloads should generally run in private subnets when they do not require direct inbound internet connectivity.

Typical placement:

| Workload | Recommended Placement |
|---|---|
| Public ALB | Public subnet |
| Django / FastAPI | Private subnet |
| ECS services | Private subnet |
| EKS worker nodes | Private subnet |
| Celery workers | Private subnet |
| PostgreSQL | Private subnet |
| Redis | Private subnet |
| Kafka | Private subnet |
| Internal load balancer | Private subnet |

A common architecture is:

```text
Internet
   |
   v
Public ALB
   |
   v
Private API
   |
   +---- PostgreSQL
   +---- Redis
   +---- Kafka
```

The API does not need a public IP simply because users access the API from the internet.

The public-facing component should terminate external connectivity and forward traffic into the private application tier.

---

## Avoid Public IPs on Internal Workloads

A public IP increases the number of potential network paths into a resource.

For example:

```text
Bad:

Internet
   |
   +-----------------> EC2
   |
   +-----------------> Redis
   |
   +-----------------> Internal API
```

A better architecture is:

```text
Internet
   |
   v
ALB
   |
   v
Private API
   |
   v
Private Data Services
```

Do not use public IP addresses for convenience when a private connectivity model is sufficient.

Public exposure should be deliberate and justified.

---

## Network Segmentation

Segmentation limits the blast radius of a compromised workload.

Instead of:

```text
Everything
   |
   +-- Everything can communicate with everything
```

use:

```text
Web Tier
   |
   v
Application Tier
   |
   +--> Database Tier
   +--> Cache Tier
   +--> Messaging Tier
```

For example:

```text
ALB
 |
 | 443
 v
API
 |
 +-- 5432 --> PostgreSQL
 |
 +-- 6379 --> Redis
 |
 +-- 9092 --> Kafka
```

The database should not normally be reachable from arbitrary workloads.

---

## Security Groups as Primary Workload Controls

Security Groups should usually be the primary network-level control for workload communication.

For example:

```text
ALB Security Group
    |
    | TCP 443
    v
API Security Group
    |
    | TCP 5432
    v
Database Security Group
```

Prefer referencing Security Groups rather than broad CIDR ranges when the architecture supports it.

For example:

```text
Database SG
    Inbound:
        PostgreSQL 5432
        Source: API Security Group
```

This expresses the architectural relationship directly:

```text
API workloads may access PostgreSQL.
```

It is more maintainable than:

```text
Allow 10.0.0.0/16 -> 5432
```

when only a subset of the VPC should access the database.

---

## Avoid `0.0.0.0/0` Inbound Rules

One of the most common security mistakes is:

```text
TCP 5432
Source: 0.0.0.0/0
```

This exposes PostgreSQL to every IPv4 source that can reach the resource.

Similarly dangerous examples include:

```text
TCP 6379 -> 0.0.0.0/0
TCP 3306 -> 0.0.0.0/0
TCP 22   -> 0.0.0.0/0
TCP 3389 -> 0.0.0.0/0
```

Use the narrowest possible source.

Examples:

```text
ALB SG -> API SG : 443
API SG -> DB SG  : 5432
API SG -> Redis SG : 6379
Worker SG -> Kafka SG : 9092
```

---

## Security Group Chaining

Security Group references are particularly useful for service-to-service authorization.

```text
ALB SG
  |
  | 443
  v
API SG
  |
  | 5432
  v
DB SG
```

The database rule can reference the API Security Group.

This creates a logical dependency:

```text
API membership
      |
      v
Database network authorization
```

It avoids tying authorization to individual IP addresses.

This is particularly useful for:

- Auto Scaling
- ECS
- EKS
- Dynamic service discovery
- Microservices
- Blue/green deployments

---

## Control Egress, Not Only Ingress

A common mistake is to focus entirely on inbound traffic.

An attacker who compromises a workload may use outbound access for:

- Command and control
- Data exfiltration
- Malware downloads
- Credential theft
- Unauthorized API access

Consider:

```text
Compromised API
      |
      v
Internet
      |
      +-- Unknown destination
```

A mature security architecture evaluates both:

```text
Inbound authorization
+
Outbound authorization
```

For sensitive workloads, explicitly design and document required egress.

---

## Egress Strategy

A private workload may need outbound access for:

- Package repositories
- External APIs
- AWS APIs
- Container registries
- Monitoring services
- Authentication providers

Do not automatically assume:

```text
Private subnet = no internet access
```

A private subnet can use a NAT Gateway for outbound internet access.

```text
Private API
    |
    v
NAT Gateway
    |
    v
Internet Gateway
    |
    v
External API
```

For AWS services, consider VPC endpoints where appropriate.

---

## Prefer VPC Endpoints for AWS Services

VPC endpoints can reduce dependency on public internet paths for supported AWS services.

For example:

```text
Private Application
       |
       v
VPC Endpoint
       |
       v
AWS Service
```

Potential benefits include:

- Reduced public internet exposure
- More controlled network paths
- Improved architecture isolation
- Potentially lower NAT data-processing costs for applicable traffic
- Better control over AWS service access

Endpoint policies can further restrict which resources or actions are allowed through supported endpoint types.

---

## NAT Gateway Security

NAT Gateways allow private resources to initiate outbound connections without accepting unsolicited inbound internet connections through the NAT path.

```text
Private Subnet
      |
      v
NAT Gateway
      |
      v
Internet Gateway
      |
      v
Internet
```

Important considerations:

- NAT Gateway should reside in a public subnet.
- The public subnet requires a route to an Internet Gateway.
- Private subnets route internet-bound traffic to the NAT Gateway.
- NAT Gateway is not a firewall replacement.
- Security Groups and NACLs still matter.
- NAT Gateway availability and architecture should be considered across Availability Zones.

A production architecture commonly uses NAT Gateway placement that avoids unnecessary cross-AZ traffic and provides appropriate availability.

---

## Network ACLs as a Secondary Boundary

Network ACLs operate at the subnet level and are stateless.

A useful architecture is:

```text
Internet
   |
   v
Network ACL
   |
   v
Subnet
   |
   v
Security Group
   |
   v
Workload
```

NACLs can provide an additional boundary for:

- Broad subnet-level restrictions
- Explicit deny rules
- Defense in depth
- Blocking known unwanted traffic patterns

However, avoid turning NACLs into a highly complex substitute for Security Groups.

---

## NACL Rule Ordering

Network ACL rules are evaluated in ascending rule-number order.

For example:

```text
100  ALLOW TCP 443 from 10.0.0.0/16
200  DENY  TCP 443 from 10.0.50.0/24
```

The deny rule may never be reached for matching traffic because rule `100` already matches.

Therefore:

```text
Rule ordering matters.
```

Design NACLs deliberately and document the reasoning behind non-obvious rules.

---

## NACLs Are Stateless

Security Groups are stateful.

NACLs are stateless.

This distinction is critical.

Suppose:

```text
Client
10.0.10.25:49152
       |
       | TCP
       v
Server
10.0.20.15:5432
```

The return traffic is:

```text
Server
10.0.20.15:5432
       |
       v
Client
10.0.10.25:49152
```

Because NACLs are stateless, both directions must be permitted.

This is why ephemeral ports become important when designing NACL rules.

---

## Ephemeral Port Considerations

Clients normally select temporary source ports for outbound TCP connections.

For example:

```text
10.0.10.25:49152 -> 10.0.20.15:5432
```

The response returns to:

```text
10.0.10.25:49152
```

When using restrictive NACLs, ensure the return path permits the required ephemeral-port range.

Do not blindly allow every possible port without considering the workload and operating-system behavior.

Document the chosen range and validate it against the actual platform.

---

## Route Tables Are Part of Security

Routing is frequently treated as a connectivity concern rather than a security concern.

In reality, routing determines which network paths exist.

For example:

```text
Private Subnet
      |
      +-- 0.0.0.0/0 -> NAT Gateway
```

versus:

```text
Database Subnet
      |
      +-- No default internet route
```

The second design reduces unnecessary external reachability.

A secure architecture asks:

> Does this workload need a route to this destination?

not merely:

> Does the Security Group allow this traffic?

---

## Do Not Rely on Security Groups Alone

Security Groups are important but not the entire security architecture.

A robust design combines:

```text
Identity
   +
Routing
   +
Security Groups
   +
NACLs
   +
VPC Endpoints
   +
Encryption
   +
Logging
   +
Threat Detection
   +
Application Security
```

For example:

```text
Network controls
        |
        v
Application authentication
        |
        v
Authorization
        |
        v
Encryption
        |
        v
Monitoring
```

Network reachability should never be treated as equivalent to application authorization.

---

## Encryption in Transit

Private networking does not eliminate the need for encryption.

Traffic such as:

```text
API -> PostgreSQL
API -> Redis
Service A -> Service B
Service A -> Kafka
```

may still require encryption depending on the service, data sensitivity, threat model, and organizational requirements.

A private IP does not guarantee confidentiality.

Prefer TLS where supported and appropriate.

For example:

```text
Client
  |
  | HTTPS
  v
ALB
  |
  | TLS
  v
API
  |
  | TLS
  v
Database
```

For internal microservices, gRPC commonly uses HTTP/2 with TLS when secure transport is required.

---

## Database Security

Database systems should normally be isolated from public access.

For PostgreSQL:

```text
API SG
  |
  | 5432
  v
Database SG
```

Avoid:

```text
Internet
  |
  v
PostgreSQL :5432
```

Database security should combine:

- Private subnets
- Security Groups
- Strong authentication
- Encryption at rest
- Encryption in transit
- Least-privilege database users
- Credential rotation
- Monitoring
- Backups
- Network segmentation

Network controls are only one layer.

---

## Redis Security

Redis should similarly be isolated.

A common architecture is:

```text
API SG
  |
  | 6379
  v
Redis SG
```

Avoid exposing Redis directly to the internet.

Redis often contains:

- Sessions
- Cache data
- Tokens
- Rate-limit state
- Temporary application data

Even when the data is considered ephemeral, unauthorized access can compromise application behavior.

---

## Kafka Security

Kafka often has broader communication requirements than a simple request/response API.

Typical communication:

```text
Producer
   |
   | Kafka protocol
   v
Kafka
   ^
   |
Consumer
```

Security should consider:

- Broker access
- Producer authorization
- Consumer authorization
- TLS
- Authentication
- Security Groups
- Network segmentation
- Topic-level authorization where supported
- Cross-account connectivity where applicable

Do not solve Kafka security solely by opening the broker port broadly.

---

## Administrative Access

Avoid exposing SSH or RDP directly to the public internet unless there is a strong, documented reason.

Prefer controlled administrative access mechanisms such as:

- AWS Systems Manager
- Bastion architectures where required
- VPN
- Direct Connect
- Controlled administrative networks

A preferred model is:

```text
Engineer
   |
   v
Identity / Access Control
   |
   v
AWS Systems Manager
   |
   v
Private Instance
```

This avoids maintaining a permanently exposed SSH endpoint.

---

## IAM and VPC Security

Network security and IAM solve different problems.

For example:

```text
Security Group
    |
    +-- Can network traffic reach PostgreSQL?

IAM
    |
    +-- Can this AWS principal perform an AWS API operation?
```

Do not use one as a substitute for the other.

A secure backend workload typically needs both:

```text
Network authorization
+
AWS identity authorization
```

For example, an EC2 or ECS workload may require:

- Security Group access to an AWS service
- IAM permissions to perform specific API operations

Both controls must be correctly configured.

---

## Least-Privilege IAM

VPC security often depends on IAM because network resources themselves are controlled through AWS APIs.

Apply least privilege to:

- VPC administrators
- CI/CD roles
- Terraform execution roles
- Application roles
- Incident-response roles
- Logging roles

Avoid giving application workloads permissions such as:

```text
ec2:*
```

when only specific actions are required.

Infrastructure automation should also use narrowly scoped roles.

---

## VPC Endpoint Policies

VPC endpoint policies can restrict access through supported gateway endpoints.

For example, an S3 endpoint policy can restrict access to specific buckets.

Conceptually:

```text
Private Workload
      |
      v
S3 VPC Endpoint
      |
      v
Endpoint Policy
      |
      v
Allowed S3 Resources
```

This provides an additional authorization boundary.

Do not assume that having an endpoint automatically means all AWS resources should be reachable through it.

---

## Centralize Security Controls

Organizations with multiple AWS accounts should avoid independently designed security models wherever possible.

A common structure is:

```text
AWS Organization
       |
       +-- Production Account
       |
       +-- Staging Account
       |
       +-- Development Account
       |
       +-- Security Account
       |
       +-- Log Archive Account
```

Security and logging controls can be standardized through:

- AWS Organizations
- Service Control Policies
- Centralized logging
- AWS Config
- Security Hub
- GuardDuty
- CloudTrail
- Infrastructure as Code
- CI/CD policy validation

Centralization improves consistency and incident response.

---

## Security Hub and GuardDuty

Flow Logs provide raw network telemetry.

Threat-detection services provide higher-level interpretation.

Conceptually:

```text
VPC Flow Logs
       |
       +------------------+
                          |
CloudTrail --------------> GuardDuty
                          |
DNS Logs -----------------+
                          |
                          v
                     Security Findings
```

Use managed detection capabilities where they reduce the amount of custom detection logic that your engineering team must maintain.

Do not assume that Flow Logs alone provide threat detection.

---

## VPC Flow Logs

Flow Logs should be enabled where network visibility is required.

They help answer:

- What traffic occurred?
- Where did it originate?
- Where did it go?
- Which port was used?
- Was it accepted or rejected?
- How much traffic was transferred?

A useful security architecture is:

```text
VPC
 |
 v
Flow Logs
 |
 +--> CloudWatch
 |
 +--> S3
 |
 +--> Security Analytics
```

Ensure Flow Log destinations have appropriate:

- Encryption
- Retention
- Access control
- Monitoring
- Cost controls

---

## Log Correlation

No single log source provides complete security context.

For example:

```text
Flow Logs
    |
    +-- 10.0.10.25 -> 203.0.113.10:443

DNS Logs
    |
    +-- api.example.com -> 203.0.113.10

Application Logs
    |
    +-- payment request started

CloudTrail
    |
    +-- IAM role modified

GuardDuty
    |
    +-- Suspicious network activity
```

Correlation creates a much stronger security picture than inspecting one source in isolation.

---

## Monitoring Unexpected Network Paths

Maintain an expected communication model.

For example:

```text
ALB
 |
 v
API

API
 |
 +-- PostgreSQL
 +-- Redis
 +-- Kafka
 +-- External HTTPS APIs
```

If the API suddenly starts communicating with:

```text
Public IP:4444
```

that should be investigated.

Potential explanations include:

- New legitimate dependency
- Misconfiguration
- Compromised workload
- Malware
- Data exfiltration
- Unexpected deployment behavior

The baseline is what makes the anomaly meaningful.

---

## Restrict East-West Traffic

East-west traffic is communication between internal workloads.

Example:

```text
Service A
   |
   +---- Service B
   +---- Service C
   +---- Database
```

Avoid:

```text
All services
   |
   +---- Can reach every other service
```

Instead define service-specific communication:

```text
API -> User Service
API -> Payment Service
Payment Service -> PostgreSQL
Worker -> Kafka
Worker -> Redis
```

This reduces lateral movement opportunities if one service is compromised.

---

## Microservice Security Groups

For microservices, avoid creating a single shared Security Group that allows every internal service to communicate with everything.

Prefer:

```text
api-sg
payment-sg
inventory-sg
worker-sg
database-sg
redis-sg
kafka-sg
```

Then explicitly define required relationships.

For example:

```text
api-sg
    |
    +-- 443 -> payment-sg

payment-sg
    |
    +-- 5432 -> database-sg
```

The Security Group structure should reflect the architecture rather than merely the subnet layout.

---

## Kubernetes Network Security

In Kubernetes environments, VPC controls are not enough.

A production EKS architecture may need:

```text
VPC Security Groups
        +
Network ACLs
        +
Kubernetes Network Policies
        +
IAM
        +
Pod Identity
        +
Application Authentication
```

Network Policies can restrict pod-to-pod communication inside the cluster.

For example:

```text
frontend
   |
   +--> backend

backend
   |
   +--> database-proxy
```

This is more precise than relying only on VPC-level boundaries.

---

## Docker Workloads

Docker containers inherit network behavior from their runtime environment.

Do not assume that putting an application inside a container automatically makes it secure.

Security still requires:

- Proper VPC placement
- Security Groups
- IAM roles
- Secret management
- TLS
- Container isolation
- Application authorization
- Dependency security

The network layer and container layer solve different problems.

---

## Nginx as an Internal Gateway

Nginx can be used as an internal reverse proxy or gateway:

```text
ALB
 |
 v
Nginx
 |
 +--> Django
 +--> FastAPI
 +--> Internal services
```

Network security should still restrict:

```text
ALB -> Nginx
Nginx -> Backend
```

Do not assume that because Nginx is inside the VPC, every internal workload should be able to access it.

---

## Secure Service-to-Service Communication

For REST:

```text
Service A
    |
    | HTTPS
    v
Service B
```

For gRPC:

```text
Service A
    |
    | HTTP/2 + TLS
    v
Service B
```

Network controls should restrict who can establish the connection.

Application-level authentication and authorization should then determine what the caller is permitted to do.

This creates layered security:

```text
Network Reachability
        |
        v
TLS
        |
        v
Authentication
        |
        v
Authorization
```

---

## Secrets Management

Do not store credentials inside:

- Security Group descriptions
- User data
- Git repositories
- Docker images
- AMIs
- Application configuration files committed to source control

Prefer managed secret mechanisms such as:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- Kubernetes Secrets with appropriate encryption and access controls

A private subnet does not make hard-coded credentials safe.

---

## CI/CD Security

VPC security should be validated through CI/CD.

A production pipeline can include:

```text
Git Commit
    |
    v
Terraform Plan
    |
    v
Security Policy Validation
    |
    v
Review
    |
    v
Terraform Apply
```

Potential policy checks include:

- No unrestricted database ingress
- No unrestricted Redis ingress
- No unrestricted SSH ingress
- No unintended public IPs
- Required Flow Logs enabled
- Required encryption enabled
- Required VPC endpoints present
- Required tags present

Infrastructure security should be treated as code quality.

---

## Infrastructure as Code

Avoid manually creating production Security Groups and NACLs whenever possible.

A Terraform example:

```hcl
resource "aws_security_group" "api" {
  name        = "api"
  description = "API workload security group"
  vpc_id      = aws_vpc.production.id
}

resource "aws_security_group" "database" {
  name        = "database"
  description = "Database security group"
  vpc_id      = aws_vpc.production.id
}

resource "aws_vpc_security_group_ingress_rule" "database_from_api" {
  security_group_id            = aws_security_group.database.id
  referenced_security_group_id = aws_security_group.api.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}
```

This creates an explicit relationship:

```text
API SG -> Database SG : 5432
```

It is easier to review and audit than undocumented manual changes.

---

## Security Drift

Infrastructure can become less secure over time.

For example:

```text
Initial:
API SG -> DB SG : 5432

Later:
0.0.0.0/0 -> DB SG : 5432
```

The second rule may have been introduced temporarily during troubleshooting and never removed.

Prevent this through:

- Infrastructure as Code
- Configuration auditing
- AWS Config
- CI/CD policy checks
- Security Hub
- Regular reviews
- Automated remediation where appropriate

Security is an ongoing operational process, not a one-time configuration task.

---

## High Availability and Security

Security controls should not create unnecessary single points of failure.

For example:

```text
AZ-A
  |
  +-- Application
  +-- NAT strategy

AZ-B
  |
  +-- Application
  +-- NAT strategy
```

Design network infrastructure with Availability Zones in mind.

Consider:

- NAT Gateway architecture
- Load balancers
- VPC endpoints
- DNS
- Routing
- Private connectivity
- Cross-AZ dependencies

A secure architecture that fails whenever one Availability Zone fails is still a poor production architecture.

---

## Disaster Recovery

Security architecture must also work during disaster recovery.

If a workload moves to another region or account, verify that the DR environment preserves:

- Security Group rules
- NACL rules
- Route tables
- VPC endpoints
- IAM policies
- KMS permissions
- Logging
- Monitoring
- DNS controls
- Secrets access

A DR environment should not become an accidental security bypass.

---

## Multi-Account Security

Separate environments and trust boundaries when appropriate.

A common model is:

```text
Organization
 |
 +-- Security
 |
 +-- Log Archive
 |
 +-- Production
 |
 +-- Staging
 |
 +-- Development
```

Cross-account communication should be explicit.

Avoid broad trust such as:

```text
Any account -> Production database
```

Prefer:

```text
Approved workload
      |
      v
Approved network path
      |
      v
Approved production service
```

---

## VPC Peering and Transit Gateway Security

As environments grow, connectivity can become more complex.

```text
VPC A
   |
   +--------+
            |
            v
        Transit Gateway
            |
       +----+----+
       |         |
       v         v
     VPC B     VPC C
```

Do not assume that network connectivity implies authorization.

For each connected VPC, define:

- Which CIDRs can communicate
- Which routes are propagated
- Which Security Groups permit traffic
- Which workloads are trusted
- Which ports are permitted
- Whether transitive connectivity is intended

Network topology should be designed alongside security policy.

---

## IPv6 Security

IPv6 must be considered explicitly.

An IPv4-only security rule such as:

```text
0.0.0.0/0
```

does not represent the IPv6 internet.

IPv6 uses:

```text
::/0
```

Therefore, if IPv6 is enabled, review:

- Security Groups
- NACLs
- Route tables
- Internet Gateway configuration
- Egress
- Application listeners
- Load balancers
- Monitoring

Do not accidentally create an IPv6 exposure while securing only IPv4.

---

## Public Load Balancer Security

A public ALB may intentionally accept internet traffic:

```text
Internet
   |
   | HTTPS 443
   v
Public ALB
```

The ALB should then restrict backend access:

```text
ALB SG
   |
   | 443
   v
API SG
```

The API Security Group should not necessarily allow:

```text
0.0.0.0/0 -> API :443
```

if the intended architecture is:

```text
Internet -> ALB -> API
```

Allow the application tier to receive traffic from the ALB tier instead.

---

## Health Checks

Load balancer health checks are a common source of security misconfiguration.

For example:

```text
ALB
 |
 | Health check
 v
API
```

The API Security Group must permit the health-check traffic from the appropriate load balancer path.

Do not solve health-check failures by opening the backend to the entire internet.

Instead identify:

```text
Who sends the health check?
Which port?
Which protocol?
Which Security Group?
```

and permit only that path.

---

## Security Monitoring

A production VPC should have visibility into:

- Rejected network traffic
- Unexpected public exposure
- Security Group changes
- NACL changes
- Route changes
- VPC endpoint changes
- IAM changes
- CloudTrail activity
- GuardDuty findings
- Flow Log delivery
- Configuration drift

Useful telemetry includes:

```text
VPC Flow Logs
CloudTrail
AWS Config
GuardDuty
Security Hub
CloudWatch
DNS Query Logs
ALB Logs
Application Logs
```

The goal is not to collect logs indiscriminately.

The goal is to make important security events observable and actionable.

---

## Alerting Strategy

Avoid alerts such as:

```text
Every rejected connection -> page on-call
```

This produces excessive noise.

Prefer aggregated signals such as:

```text
Unexpected source
+
High rejection rate
+
Sensitive destination port
+
Short time window
```

For example:

```text
Source: unknown workload
Destination: database
Port: 5432
Rejected attempts: 20,000
Window: 5 minutes
```

This is significantly more actionable.

---

## Cost-Aware Security

Security architecture should be effective without unnecessarily increasing infrastructure cost.

Consider:

- NAT Gateway data-processing charges
- Cross-AZ traffic
- CloudWatch Logs ingestion
- CloudWatch Logs retention
- S3 storage
- Athena queries
- Security tooling
- VPC endpoint costs
- SIEM ingestion

For example, sending large volumes of AWS-service traffic through NAT when a suitable VPC endpoint exists may be unnecessary.

Similarly, keeping years of high-volume Flow Logs in expensive interactive storage may not be justified.

---

## Security Testing

Security controls should be tested rather than assumed.

Test scenarios such as:

```text
API -> DB : 5432
API -> Redis : 6379
API -> Kafka : 9092
Internet -> API : 443
Internet -> DB : 5432
Unauthorized subnet -> DB : 5432
```

Expected results should be documented.

Example:

| Traffic | Expected |
|---|---|
| Internet → ALB:443 | Allowed |
| Internet → DB:5432 | Denied |
| API → DB:5432 | Allowed |
| API → Redis:6379 | Allowed |
| Unknown workload → DB:5432 | Denied |
| Worker → Kafka:9092 | Allowed |

This turns network security into a testable property.

---

## Troubleshooting Securely

Temporary security changes are a major source of production drift.

A common pattern is:

```text
Application fails
      |
      v
Engineer opens 0.0.0.0/0
      |
      v
Application works
      |
      v
Temporary rule remains forever
```

Instead:

1. Identify the failing network path.
2. Inspect Flow Logs.
3. Check route tables.
4. Check Security Groups.
5. Check NACLs.
6. Identify the exact missing permission.
7. Add the narrowest required rule.
8. Validate.
9. Remove temporary diagnostic changes.
10. Commit the final configuration to IaC.

Never use broad network access as the default debugging technique.

---

## Common Security Mistakes

### Exposing Databases to the Internet

```text
0.0.0.0/0 -> 5432
```

Avoid it. Use private subnets and Security Group references.

### Opening All Internal Ports

```text
VPC CIDR -> ALL TCP
```

This weakens segmentation.

Define service-specific ports.

### Allowing SSH from Everywhere

```text
0.0.0.0/0 -> 22
```

Prefer controlled administrative access.

### Ignoring IPv6

Securing IPv4 while leaving IPv6 paths unrestricted can create unintended exposure.

### Treating Private Subnets as Automatically Secure

Private addressing reduces exposure but does not provide application authorization.

### Using NACLs as the Main Firewall

NACLs are useful defense-in-depth controls but are stateless and subnet-wide.

### Overcomplicating NACLs

Complex NACLs are difficult to reason about and easy to break because of rule ordering and return-path requirements.

### Ignoring Egress

A compromised application can use outbound connectivity for malicious purposes.

### Using IP Addresses Instead of Security Group Relationships

Static IP-based rules are fragile in dynamic workloads.

### Manual Production Changes

Manual changes create drift and make security state difficult to audit.

### No Flow Logs

Without network telemetry, diagnosing connectivity and investigating incidents becomes significantly harder.

### Alerting on Every Rejection

High-volume environments naturally contain rejected traffic. Alert on meaningful patterns.

---

## Production Security Review

Before deploying a production VPC, review the architecture against the following categories.

### Network Exposure

- [ ] No unnecessary public IPs
- [ ] Public load balancers are intentional
- [ ] Databases are private
- [ ] Redis is private
- [ ] Kafka is private
- [ ] Administrative access is controlled

### Security Groups

- [ ] Ingress is least privilege
- [ ] Database access uses workload-specific sources
- [ ] Redis access is restricted
- [ ] Kafka access is restricted
- [ ] No unnecessary `0.0.0.0/0` rules
- [ ] IPv6 rules reviewed
- [ ] Egress requirements documented

### Network ACLs

- [ ] NACL rules are intentionally designed
- [ ] Rule ordering is understood
- [ ] Return traffic is allowed
- [ ] Ephemeral ports are considered
- [ ] NACL complexity is manageable

### Routing

- [ ] Public routes are intentional
- [ ] Private routes are intentional
- [ ] Database subnets do not require unnecessary internet routes
- [ ] NAT architecture is appropriate
- [ ] VPC endpoints are used where beneficial

### Identity

- [ ] IAM follows least privilege
- [ ] Workloads use appropriate IAM roles
- [ ] Administrative access is controlled
- [ ] Cross-account trust is explicit

### Encryption

- [ ] TLS is used where appropriate
- [ ] Data at rest is encrypted
- [ ] Secrets are managed securely
- [ ] KMS permissions are restricted

### Observability

- [ ] VPC Flow Logs are configured
- [ ] CloudTrail is enabled
- [ ] GuardDuty is enabled where required
- [ ] DNS logging is available where required
- [ ] Security findings are monitored
- [ ] Log retention is defined

### Infrastructure Management

- [ ] VPC configuration is managed through IaC
- [ ] CI/CD validates security policies
- [ ] Configuration drift is detected
- [ ] Security changes are reviewed
- [ ] Emergency changes are documented and reconciled

---

## Security Architecture Example

A strong production backend architecture can look like:

```mermaid
flowchart TB
    Internet["Internet"]

    subgraph Public["Public Subnets"]
        ALB["Public ALB"]
        NAT["NAT Gateway"]
    end

    subgraph PrivateApp["Private Application Subnets"]
        API["Django / FastAPI"]
        Worker["Celery Workers"]
        Nginx["Internal Nginx"]
    end

    subgraph PrivateData["Private Data Subnets"]
        DB["PostgreSQL"]
        Redis["Redis"]
        Kafka["Kafka"]
    end

    Endpoint["VPC Endpoints"]
    Logs["VPC Flow Logs"]
    GuardDuty["GuardDuty"]
    CloudTrail["CloudTrail"]

    Internet --> ALB
    ALB --> API
    API --> Nginx
    Nginx --> API

    API --> DB
    API --> Redis
    Worker --> Redis
    Worker --> Kafka
    Worker --> DB

    API --> NAT
    Worker --> NAT

    API --> Endpoint
    Worker --> Endpoint

    PrivateApp --> Logs
    PrivateData --> Logs
    Public --> Logs

    Logs --> GuardDuty
    CloudTrail --> GuardDuty
```

The important property is the explicit trust model:

```text
Internet
   |
   v
ALB
   |
   v
Application
   |
   +----> Database
   +----> Redis
   +----> Kafka
   +----> Approved AWS Services
   +----> Approved External APIs
```

Each path should have a documented reason.

---

## Senior-Level Design Questions

When reviewing a VPC architecture, ask:

### Exposure

- Which resources have public IPs?
- Why do they need them?
- Can the architecture work without them?

### Segmentation

- Which workloads share subnets?
- Which workloads should never communicate?
- What happens if one application is compromised?

### Network Authorization

- Which Security Group allows this connection?
- Is the source another Security Group or a broad CIDR?
- Is the rule necessary?

### Egress

- Where can private workloads connect?
- Can compromised workloads reach arbitrary internet destinations?
- Can AWS-service access avoid NAT?

### Routing

- Which route makes this traffic possible?
- Is that route required?
- Could removing the route reduce exposure?

### Observability

- How would you detect unauthorized traffic?
- How would you investigate a timeout?
- Can you identify the workload behind an IP address?

### Identity

- Does network reachability provide too much trust?
- What IAM permissions does the workload have?
- Is application-level authorization still enforced?

### Resilience

- What happens if an Availability Zone fails?
- What happens if a NAT Gateway fails?
- Does the DR environment preserve security controls?

These questions distinguish a working VPC from a production-grade VPC architecture.

---

## Key Takeaways

- **Treat VPC security as defense in depth**: private subnets, routing, Security Groups, NACLs, IAM, encryption, VPC endpoints, logging, and threat detection each address different failure and attack modes.
- **Use least-privilege network paths**: explicitly define which workloads may communicate, on which ports and protocols, and avoid broad CIDR-based or public access rules when narrower Security Group relationships are possible.
- **Control egress as deliberately as ingress**: private workloads should have only the outbound connectivity they actually require, with VPC endpoints preferred for suitable AWS-service traffic.
- **Make security observable and reproducible**: use Flow Logs, CloudTrail, GuardDuty, Config, and centralized logging, while managing VPC security configuration through Infrastructure as Code and CI/CD validation.
- **Design for failure and compromise**: segmentation, multi-AZ architecture, controlled administrative access, encryption, and explicit trust boundaries should limit blast radius while preserving availability and recoverability.