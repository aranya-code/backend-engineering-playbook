# 05- Network Security

## Overview

Network security for Amazon ECS is primarily about controlling **who can reach a workload, from where, on which ports, and through which network path**.

An ECS task should rarely be treated as an independently trusted endpoint. A production architecture typically places application tasks inside private subnets, exposes them through a controlled load-balancing layer, and restricts access between application and data tiers using security groups.

A typical production architecture is:

```text
                           Internet
                              |
                              | HTTPS 443
                              v
                       +--------------+
                       |     WAF      |
                       +--------------+
                              |
                              v
                    +-------------------+
                    |   Public ALB      |
                    +-------------------+
                              |
                              | Application Port
                              v
                    +-------------------+
                    | Private ECS Tasks |
                    +-------------------+
                       |             |
                       |             |
                TCP 5432        TCP 6379
                       |             |
                       v             v
                +----------+   +----------+
                | RDS      |   | Redis    |
                +----------+   +----------+
```

The security model should combine:

- VPC isolation
- Subnet placement
- Security groups
- Load balancer controls
- Network routing
- TLS
- Private connectivity
- Application-level authorization
- Monitoring and network visibility

Network security reduces the attack surface, but it does not replace IAM or application security.

## ECS Network Security Model

A useful mental model is:

```text
Network Reachability
        |
        v
Can the packet reach the workload?
        |
        v
Security Group
        |
        v
Is the source allowed on this port?
        |
        v
Load Balancer / Service Boundary
        |
        v
Application Authentication
        |
        v
Application Authorization
```

Each layer answers a different question.

| Layer | Primary Security Question |
|---|---|
| VPC | Which network contains the workload? |
| Subnet | Where is the workload placed? |
| Route table | Where can traffic go? |
| Security group | Which sources can connect? |
| Load balancer | Through which controlled entry point? |
| TLS | Is traffic protected in transit? |
| Application auth | Who is making the request? |
| Application authorization | What may the caller do? |

## Private vs Public ECS Tasks

For most production APIs, ECS tasks should be deployed in private subnets rather than directly exposed to the internet.

### Public Task Architecture

```text
Internet
   |
   v
ECS Task
```

The task becomes directly reachable and requires significantly more careful exposure management.

### Private Task Architecture

```text
Internet
   |
   v
ALB
   |
   v
Private ECS Task
```

The task is not directly reachable from the public internet.

This architecture provides a cleaner security boundary and allows the ALB to become the controlled public entry point.

## Public and Private Subnets

A common architecture separates resources into different subnet tiers:

```text
VPC
 |
 +-- Public Subnets
 |      |
 |      +-- ALB
 |
 +-- Private Application Subnets
 |      |
 |      +-- ECS Tasks
 |
 +-- Private Data Subnets
        |
        +-- RDS
        +-- Redis
```

The exact topology depends on workload requirements, but application and database resources should generally not require public IP addresses.

### Typical Placement

| Resource | Typical Placement |
|---|---|
| Internet-facing ALB | Public subnets |
| ECS API tasks | Private subnets |
| ECS workers | Private subnets |
| RDS | Private subnets |
| ElastiCache / Redis | Private subnets |
| Internal ALB | Private subnets |

## Security Groups

Security groups are stateful virtual firewalls associated with AWS resources such as ECS task network interfaces, load balancers, and databases.

A security group controls inbound and outbound traffic based on:

- Protocol
- Port
- Source
- Destination

A production ECS architecture often uses separate security groups for each tier.

```text
Internet
   |
   | HTTPS 443
   v
ALB Security Group
   |
   | TCP 8000
   v
ECS Security Group
   |
   +---- TCP 5432 ----> RDS Security Group
   |
   +---- TCP 6379 ----> Redis Security Group
```

## Security Group References

Where possible, reference another security group rather than using broad CIDR ranges.

For example:

```text
ALB-SG
   |
   | TCP 8000
   v
ECS-SG
```

The ECS security group can allow traffic from the ALB security group.

Similarly:

```text
ECS-SG
   |
   | TCP 5432
   v
RDS-SG
```

This expresses the intended architecture directly:

> ECS tasks may connect to PostgreSQL.

Instead of:

```text
0.0.0.0/0 -> TCP 5432
```

which exposes the database broadly.

## Security Group Design

A clean design might use:

```text
sg-alb
    |
    +-- Inbound: HTTPS from Internet
    +-- Outbound: Application port to sg-ecs

sg-ecs
    |
    +-- Inbound: Application port from sg-alb
    +-- Outbound: Required application dependencies

sg-rds
    |
    +-- Inbound: 5432 from sg-ecs

sg-redis
    |
    +-- Inbound: 6379 from sg-ecs
```

This creates explicit trust relationships between tiers.

## Why Security Group References Are Better

Consider two approaches.

### CIDR-Based Rule

```text
10.0.0.0/16 -> TCP 5432
```

This allows any resource in the VPC CIDR to potentially connect, subject to other controls.

### Security Group-Based Rule

```text
sg-ecs -> TCP 5432 -> sg-rds
```

This limits the intended source to resources associated with the ECS security group.

The second model better represents application architecture.

It also remains more stable as ECS tasks scale because task IP addresses change dynamically.

## ECS Task Network Interfaces

With the `awsvpc` network mode, ECS tasks receive their own elastic network interfaces and private IP addresses.

Conceptually:

```text
ECS Task
   |
   v
Task ENI
   |
   +-- Private IP
   +-- Security Groups
   +-- Subnet
```

This makes the task a first-class network endpoint inside the VPC.

It also means network security must be designed around the task's security groups and subnet placement rather than relying on a shared host network boundary.

## `awsvpc` Network Mode

`awsvpc` provides each task with its own network identity.

This is especially important for:

- Fargate
- Fine-grained security groups
- Microservices
- Service-to-service communication
- Private IP-based connectivity

A simplified flow is:

```text
ECS Service
    |
    v
Task
    |
    v
ENI
    |
    +-- Private IP
    +-- Security Groups
    +-- Subnet
```

For production ECS workloads, this provides a clean model for network isolation.

## Load Balancer as the Public Boundary

For HTTP and HTTPS APIs, an Application Load Balancer is commonly used as the public entry point.

```text
Client
  |
  | HTTPS
  v
ALB
  |
  | Target Group
  v
ECS Service
  |
  v
ECS Tasks
```

The ECS tasks do not need public IP addresses.

The ALB handles:

- Client connections
- TLS termination where configured
- Health checks
- Routing
- Target registration
- Traffic distribution

This creates a clear separation between public ingress and application workloads.

## ALB Security Group

The ALB security group should allow only the required public ports.

For a typical HTTPS API:

```text
Internet
    |
    | TCP 443
    v
ALB Security Group
```

HTTP port 80 may also be allowed if it is explicitly used for HTTP-to-HTTPS redirection.

Avoid exposing unnecessary ports such as:

```text
22
3306
5432
6379
8000
8080
```

to the internet.

The ALB should generally expose only the ports required for client traffic.

## ECS Security Group

The ECS security group should generally accept application traffic from the ALB security group rather than from the internet.

For example:

```text
Source:
    sg-alb

Protocol:
    TCP

Port:
    8000
```

The result is:

```text
Internet
   |
   X
   |
ECS Task
```

and:

```text
ALB
   |
   v
ECS Task
```

This prevents direct internet access to the application task even though the application itself is listening on a network port.

## Database Security Groups

A PostgreSQL database should generally accept connections only from the application tier.

```text
ECS-SG
   |
   | TCP 5432
   v
RDS-SG
```

Avoid:

```text
0.0.0.0/0 -> 5432
```

The same principle applies to MySQL:

```text
ECS-SG
   |
   | TCP 3306
   v
RDS-SG
```

and Redis:

```text
ECS-SG
   |
   | TCP 6379
   v
Redis-SG
```

## Network Segmentation

Network segmentation limits lateral movement after a compromise.

Consider:

```text
Internet
   |
   v
ALB
   |
   v
API Tier
   |
   +----> Worker Tier
   |
   +----> Database Tier
   |
   +----> Cache Tier
```

A compromised API task should not automatically have unrestricted access to every internal workload.

Use separate security groups and controlled network paths for:

- APIs
- Workers
- Databases
- Caches
- Internal services

## Service-to-Service Networking

Microservices often communicate using REST or gRPC.

For example:

```text
Orders Service
      |
      | gRPC
      v
Payments Service
```

Network security should determine whether Orders can reach Payments.

But connectivity alone should not imply authorization.

The complete model is:

```text
Network Access
      +
Service Identity
      +
Application Authorization
```

A security group can answer:

> Can Orders connect to Payments?

It cannot answer:

> Is this particular request allowed to refund an order?

That decision belongs to the application authorization layer.

## Internal Load Balancers

Internal Application Load Balancers can provide controlled access between private services.

```text
ECS Service A
      |
      v
Internal ALB
      |
      v
ECS Service B
```

This can be useful when:

- Services need stable internal endpoints
- Routing rules are required
- Multiple service instances exist
- Centralized health checking is useful
- HTTP/gRPC traffic needs controlled entry

For simple service-to-service communication, direct private service discovery may be sufficient.

The architecture should not introduce a load balancer solely because it is available.

## Service Discovery

ECS services can use service discovery mechanisms to communicate through private DNS names.

Conceptually:

```text
orders.internal
      |
      v
Private DNS
      |
      v
Orders ECS Tasks
```

Another service can connect using:

```text
http://orders.internal
```

or an appropriate protocol and port.

Security groups should still restrict which services can connect.

Service discovery provides **location**, not authorization.

## Egress Security

Inbound traffic is only half of network security.

ECS tasks also make outbound connections to:

- AWS APIs
- Databases
- Redis
- External APIs
- Package or artifact services
- Message brokers

A production architecture should understand and control outbound access where appropriate.

```text
ECS Task
   |
   +---- RDS
   +---- Redis
   +---- SQS
   +---- S3
   +---- External APIs
```

Unrestricted outbound internet access can increase the impact of a compromised application.

## NAT Gateway

Private ECS tasks often need outbound internet access for certain external dependencies.

A common architecture is:

```text
Private ECS Subnet
       |
       v
Route Table
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

The ECS task remains private and does not receive a public IP, while the NAT Gateway provides controlled outbound connectivity.

NAT Gateway usage introduces cost and availability considerations.

## VPC Endpoints

Where AWS services support VPC endpoints, private connectivity can reduce the need for internet/NAT paths.

For example:

```text
ECS
 |
 +---- VPC Endpoint ----> S3
 |
 +---- VPC Endpoint ----> ECR
 |
 +---- VPC Endpoint ----> Secrets Manager
 |
 +---- VPC Endpoint ----> SSM
```

The exact endpoint types and supported services depend on AWS service capabilities.

VPC endpoints can improve:

- Network isolation
- Traffic control
- Reliability of AWS service access
- Reduced NAT dependency
- Security posture

They can also introduce additional infrastructure and cost.

## NAT Gateway vs VPC Endpoint

| Requirement | NAT Gateway | VPC Endpoint |
|---|---|---|
| Access public internet | Yes | No |
| Access supported AWS services privately | Not required | Yes |
| Requires public NAT infrastructure | Yes | No |
| Useful for external APIs | Yes | No |
| Reduces NAT dependency | No | Yes |
| Service-specific access control | Limited | Stronger options depending on endpoint type |
| Additional cost | Yes | Yes, depending on endpoint type |

For AWS-only workloads, private VPC endpoints can significantly reduce unnecessary internet traversal.

## VPC Endpoint Security

Interface endpoints use security groups.

A typical pattern is:

```text
ECS-SG
   |
   | HTTPS 443
   v
VPC Endpoint SG
   |
   v
AWS Service
```

The endpoint security group should allow only the required source security groups.

Endpoint policies can also restrict access to supported services and resources where applicable.

## Internet-Facing vs Internal Services

Not every ECS service should be public.

For example:

```text
Public
  |
  +-- API Gateway / ALB
          |
          v
      Public API
          |
          v
      Internal Services
          |
          +-- Payments
          +-- Orders
          +-- Notifications
```

Internal services should generally remain private unless external accessibility is explicitly required.

This reduces exposure and simplifies the security model.

## WAF at the Edge

AWS WAF can provide application-layer filtering in front of supported AWS resources such as an Application Load Balancer.

A typical flow is:

```text
Internet
   |
   v
WAF
   |
   v
ALB
   |
   v
ECS
```

WAF can help address threats such as:

- Common malicious request patterns
- Excessive request rates
- Known attack signatures
- Application-layer abuse

WAF does not replace security groups.

Security groups control network connectivity, while WAF evaluates application-layer HTTP traffic.

## TLS and Network Security

Network security should distinguish between:

```text
Reachability
    |
    v
Security Groups / Routing

Confidentiality
    |
    v
TLS

Authorization
    |
    v
Application / IAM
```

A private network does not automatically encrypt traffic.

For sensitive communication:

```text
Client
   |
   | HTTPS
   v
ALB
   |
   | HTTPS where required
   v
ECS
   |
   | TLS
   v
RDS / Redis / Internal Service
```

The required level of encryption should be based on the threat model and organizational requirements.

## TLS Termination

A common architecture is:

```text
Client
   |
   | HTTPS
   v
ALB
   |
   | HTTP
   v
ECS
```

TLS terminates at the ALB.

This simplifies certificate management because the ALB handles the public certificate.

For stronger internal transport protection:

```text
Client
   |
   | HTTPS
   v
ALB
   |
   | HTTPS
   v
ECS
```

This adds certificate and operational complexity but provides encrypted traffic through the internal network path.

## Network ACLs

Network ACLs operate at the subnet level and are stateless.

Security groups are stateful and operate at the network-interface/resource boundary.

| Feature | Security Group | Network ACL |
|---|---|---|
| Scope | Resource / ENI | Subnet |
| Stateful | Yes | No |
| Rules | Allow only | Allow and deny |
| Typical ECS use | Primary workload control | Additional subnet-level control |
| Return traffic | Automatically handled | Must be explicitly considered |

Security groups are usually the primary network access mechanism for ECS workloads.

Network ACLs can provide additional subnet-level controls but should not be made unnecessarily complex.

## Security Groups vs Network ACLs

A common mistake is attempting to implement all network security using network ACLs.

For ECS:

```text
Security Groups
    |
    +-- ALB access
    +-- ECS access
    +-- RDS access
    +-- Redis access
```

should generally carry the primary workload-level authorization.

Network ACLs can provide an additional defense layer where organizational or architectural requirements justify them.

Complex ACLs can create difficult troubleshooting scenarios because they are stateless and subnet-wide.

## Route Tables

Route tables determine where traffic is sent.

A simplified architecture:

```text
Private ECS Subnet
       |
       v
Route Table
       |
       +---- VPC Local Route
       |
       +---- NAT Gateway
       |
       +---- VPC Endpoint
```

Routing determines reachability but does not replace security groups.

A valid route does not automatically mean traffic is allowed.

The packet must satisfy both routing and security controls.

## Security Group Egress

Default security group configurations often allow broad outbound access.

For high-security workloads, consider whether unrestricted egress is necessary.

For example:

```text
ECS
 |
 +-- PostgreSQL
 +-- Redis
 +-- SQS
 +-- S3
 +-- Specific APIs
```

Instead of:

```text
ECS
 |
 +-- Anywhere on the Internet
```

Restricting egress can reduce the impact of:

- Data exfiltration
- Command-and-control communication
- Malware callbacks
- Unexpected external API access

However, overly restrictive egress rules can break legitimate application dependencies.

The right level depends on the workload.

## Egress Filtering Trade-Off

| Approach | Security | Operational Complexity |
|---|---|---|
| Allow all outbound | Lower | Low |
| Restrict major destinations | Higher | Medium |
| Strict allowlist | Highest potential control | High |

A strict egress allowlist requires the engineering team to understand all application dependencies.

It can be valuable for sensitive workloads but should be introduced deliberately.

## ECS Workers and Network Security

Background workers such as Celery workers running on ECS require network isolation just like API tasks.

For example:

```text
SQS
 |
 v
Worker ECS Tasks
 |
 +---- PostgreSQL
 +---- Redis
 +---- S3
```

The worker does not need inbound public access merely because it needs outbound access to AWS services.

A common mistake is exposing worker ports to the internet even though the workers only consume messages.

A worker can often have:

```text
Inbound:
    None from Internet

Outbound:
    Required application dependencies
```

## ECS and Kafka

An ECS Kafka consumer might use:

```text
ECS Consumer
     |
     | TLS
     v
Kafka / MSK
```

Security should cover:

- Network reachability
- Broker authentication
- TLS
- Topic-level authorization
- Security groups
- Private subnets

The ECS security group should allow broker traffic only to the required Kafka endpoints and ports.

Do not expose Kafka brokers directly to the public internet unless there is a specific architecture requiring it.

## ECS and Redis

Redis should normally remain private:

```text
Internet
   |
   X
   |
Redis
```

Instead:

```text
ECS
 |
 v
Redis
```

Security groups should restrict Redis access to application workloads that actually need it.

For example:

```text
ECS-API-SG
    |
    +---- TCP 6379 ----> Redis-SG

ECS-Worker-SG
    |
    +---- TCP 6379 ----> Redis-SG
```

Only workloads that genuinely require Redis should receive access.

## ECS and PostgreSQL

For RDS PostgreSQL:

```text
ECS-SG
    |
    | TCP 5432
    v
RDS-SG
```

The database should generally:

- Remain private
- Avoid public accessibility
- Allow traffic only from trusted application security groups
- Use TLS where required
- Use strong authentication
- Use encryption at rest

Network access should be restricted independently from database authorization.

## Network Security for Django

A Django application typically has:

```text
Internet
   |
   v
ALB
   |
   v
Django ECS Tasks
   |
   +---- PostgreSQL
   +---- Redis
   +---- S3
```

The task security group should not expose Django's application port directly to the internet.

Instead:

```text
Internet
   |
   v
ALB-SG
   |
   v
ECS-SG
```

Django should also enforce application-level controls such as:

- Authentication
- Authorization
- CSRF protection
- HTTPS enforcement
- Secure cookies
- Request validation

Network security is one layer of the architecture.

## Network Security for FastAPI

A FastAPI service might use:

```text
Client
   |
   | HTTPS
   v
ALB
   |
   v
FastAPI ECS
   |
   +---- PostgreSQL
   +---- Redis
   +---- SQS
```

The FastAPI container should not need a public IP for normal API traffic.

The ALB provides the controlled entry point.

FastAPI should still enforce:

- Authentication
- Authorization
- Input validation
- Rate limiting where appropriate
- Request size limits
- Secure error handling

## Network Security for gRPC

gRPC commonly uses HTTP/2 and TLS.

A service-to-service architecture might be:

```text
Orders ECS
    |
    | gRPC / TLS
    v
Payments ECS
```

The security groups can restrict which ECS service can reach the Payments service.

Application-level service identity can then determine whether the request is authorized.

For sensitive systems, mTLS can provide mutual service authentication.

## VPC Flow Logs

VPC Flow Logs provide visibility into network traffic metadata.

Conceptually:

```text
VPC
 |
 v
Flow Logs
 |
 v
CloudWatch / S3
 |
 v
Analysis
```

Flow Logs can help investigate:

- Unexpected connections
- Rejected traffic
- Connectivity failures
- Unexpected network destinations
- Security group behavior
- Potential lateral movement

They do not provide full packet payloads.

## Network Monitoring

Production network monitoring should answer:

- Which workload is connecting to which destination?
- Which ports are being used?
- Which connections are rejected?
- Are tasks communicating with unexpected addresses?
- Is outbound traffic increasing unexpectedly?

Useful signals include:

- VPC Flow Logs
- ALB access logs
- CloudWatch metrics
- ECS service events
- Application logs
- AWS security findings

Monitoring should focus on actionable behavior rather than collecting data without a response strategy.

## Network Security and High Availability

Network security should not accidentally create a single point of failure.

A production architecture should generally distribute critical resources across multiple Availability Zones.

```text
                 ALB
          +-------+-------+
          |               |
          v               v
       AZ-A             AZ-B
          |               |
       ECS-A            ECS-B
          |               |
          +-------+-------+
                  |
                 RDS
```

Security groups should be consistently configured across all Availability Zones.

Avoid designing a security architecture where only one subnet, NAT path, or network component is available for a critical workload.

## NAT Gateway High Availability

If private ECS tasks require internet egress, a common multi-AZ architecture uses NAT Gateway resources appropriately across Availability Zones.

```text
Private Subnet AZ-A
       |
       v
NAT Gateway AZ-A
       |
       v
Internet

Private Subnet AZ-B
       |
       v
NAT Gateway AZ-B
       |
       v
Internet
```

Using a single NAT Gateway for multiple Availability Zones may reduce cost but can introduce a cross-AZ dependency and a potential failure or traffic concentration point.

The correct architecture depends on availability and cost requirements.

## Cost Considerations

Network security architecture has cost implications.

Potential costs include:

- NAT Gateway
- VPC endpoints
- Load balancers
- Data transfer
- Flow Logs
- WAF
- Cross-AZ traffic

For example, moving AWS service traffic through NAT unnecessarily can increase costs.

A security architecture should therefore consider:

```text
Security
   +
Availability
   +
Performance
   +
Cost
```

rather than optimizing only one dimension.

## Network Security and Disaster Recovery

Disaster recovery requires network controls to exist in the recovery environment as well.

Consider:

```text
Primary Region
    |
    +-- VPC
    +-- Subnets
    +-- Security Groups
    +-- ALB
    +-- ECS
    +-- Database

Recovery Region
    |
    +-- VPC
    +-- Subnets
    +-- Security Groups
    +-- ALB
    +-- ECS
    +-- Database
```

Infrastructure-as-code is particularly valuable because it allows network configuration to be reproduced consistently.

Security groups, routes, endpoint configuration, and load balancer rules should not exist only as manually configured production state.

## Infrastructure as Code

Network security configuration should ideally be managed through:

- Terraform
- AWS CloudFormation
- AWS CDK

For example, Terraform can express security group relationships explicitly:

```hcl
resource "aws_vpc_security_group_ingress_rule" "ecs_from_alb" {
  security_group_id            = aws_security_group.ecs.id
  referenced_security_group_id = aws_security_group.alb.id

  from_port   = 8000
  to_port     = 8000
  ip_protocol = "tcp"
}
```

This makes security configuration:

- Reviewable
- Reproducible
- Version-controlled
- Testable
- Easier to audit

## Common Network Security Mistakes

### Public ECS Tasks Without a Requirement

Giving every ECS task a public IP increases exposure.

**Better:** place application tasks in private subnets and expose them through an ALB where appropriate.

### Allowing `0.0.0.0/0` to Databases

For example:

```text
0.0.0.0/0 -> 5432
```

This creates unnecessary exposure.

**Better:** allow PostgreSQL traffic from the application security group.

### Allowing the Internet Directly to ECS Ports

For example:

```text
0.0.0.0/0 -> 8000
```

**Better:** allow application traffic from the ALB security group.

### Using Large CIDR Ranges Instead of Security Group References

Broad CIDRs can permit unintended workloads to connect.

**Better:** use security group references where the architecture allows it.

### Exposing Redis Publicly

Redis should normally be private.

**Better:** allow only required ECS workloads to access the Redis security group.

### Assuming Private Subnets Encrypt Traffic

Private routing controls reachability, not confidentiality.

**Better:** use TLS for sensitive communication.

### Ignoring Outbound Traffic

A compromised task may use unrestricted egress for data exfiltration or command-and-control communication.

**Better:** understand and restrict egress where the workload justifies it.

### Overusing Network ACLs

Complex stateless ACL rules can make connectivity difficult to troubleshoot.

**Better:** use security groups as the primary resource-level control and introduce ACL restrictions deliberately.

### Using One Security Group for Everything

A single shared security group can blur service boundaries.

**Better:** separate ALB, ECS, database, cache, and other meaningful tiers.

### Creating a Single-AZ Network Dependency

A network security design that depends on one NAT Gateway or subnet can undermine high availability.

**Better:** design critical network paths across Availability Zones where required.

## Production Network Security Checklist

| Area | Recommended Practice |
|---|---|
| ECS placement | Private subnets for application tasks where appropriate |
| Public access | Expose controlled ingress through ALB/WAF |
| Task IPs | Avoid public IPs unless explicitly required |
| ALB | Expose only required ports |
| ECS SG | Allow application traffic from trusted sources |
| Database SG | Allow database traffic only from application SGs |
| Redis SG | Allow cache traffic only from required workloads |
| Security groups | Prefer SG references over broad CIDRs |
| Egress | Review and restrict where appropriate |
| NAT | Use only where internet egress is required |
| VPC endpoints | Prefer private AWS-service connectivity where appropriate |
| TLS | Protect sensitive traffic in transit |
| Network ACLs | Use as an additional subnet-level control when justified |
| Flow Logs | Enable where monitoring and investigation require them |
| WAF | Protect internet-facing HTTP workloads where appropriate |
| Availability | Distribute critical networking across AZs |
| IaC | Version-control network security configuration |
| DR | Reproduce security groups, routes, and endpoints in recovery environments |

## Interview Traps

### Does a Private Subnet Make an ECS Task Secure?

No.

It reduces direct internet exposure but does not replace security groups, IAM, TLS, application authorization, container security, or monitoring.

### Why Use Security Group References Instead of IP Addresses?

ECS task IP addresses can change as tasks scale or are replaced.

Security group references express the intended trust relationship without requiring manual updates for individual task IPs.

### What Is the Difference Between a Security Group and a Network ACL?

Security groups are stateful and operate at the resource/network-interface level.

Network ACLs are stateless and operate at the subnet level.

Security groups are typically the primary workload-level network control for ECS.

### Should ECS Tasks Have Public IP Addresses?

Usually not for production APIs that can be reached through an ALB.

Private tasks reduce direct exposure and provide a cleaner security boundary.

### Does a Security Group Provide Authentication?

No.

It controls network connectivity.

Authentication and authorization must be implemented separately.

### Why Can a Private ECS Task Need a NAT Gateway?

A private task may need outbound access to external services that are not available through private AWS connectivity.

NAT provides outbound internet access without assigning the task a public IP.

### Why Use VPC Endpoints?

They can provide private connectivity to supported AWS services, reducing unnecessary traversal through NAT or public internet paths.

### Should Every ECS Service Use the Same Security Group?

Not necessarily.

Separate security groups can provide clearer service boundaries and more precise access control.

### Is HTTPS Required Between Private ECS Services?

It depends on the threat model, compliance requirements, and architecture.

Private networking controls reachability, while TLS provides confidentiality and integrity in transit. Sensitive service-to-service communication may require TLS even inside the VPC.

## Key Takeaways

- Use **private ECS tasks, controlled ingress, and narrowly scoped security groups** to minimize direct network exposure.
- Prefer **security group references between application tiers** instead of broad CIDR rules, especially for ALB-to-ECS, ECS-to-RDS, and ECS-to-Redis traffic.
- Network security has multiple layers: **routing controls reachability, security groups control connectivity, TLS protects traffic, and application authorization controls actions**.
- Treat outbound traffic as a security boundary as well; use **NAT and VPC endpoints deliberately** and restrict egress when the workload requires stronger isolation.
- Build network security for **high availability, observability, cost efficiency, and disaster recovery**, preferably through version-controlled infrastructure as code.