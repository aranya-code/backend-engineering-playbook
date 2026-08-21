# 01- VPC Security Overview

## Overview

VPC security is the combination of **network isolation, traffic control, identity-aware access, encryption, monitoring, and operational controls** used to protect workloads running inside an Amazon VPC.

A secure VPC is not simply a VPC with private subnets. Production security requires multiple independent controls working together:

```text
                         Internet
                            |
                         Route 53
                            |
                         CloudFront
                            |
                            v
                           WAF
                            |
                            v
                         ALB/NLB
                            |
                +-----------+-----------+
                |                       |
             AZ-A                    AZ-B
                |                       |
        Private App Subnet       Private App Subnet
                |                       |
          Django/FastAPI           Django/FastAPI
                |                       |
                +-----------+-----------+
                            |
                    Private Data Tier
                            |
                  +---------+---------+
                  |                   |
              PostgreSQL            Redis
```

The security model should assume that every layer can fail or be misconfigured. Network controls reduce the attack surface, but application authentication, authorization, TLS, secrets management, logging, and identity controls remain necessary.

---

## Security Model of a VPC

A useful way to reason about VPC security is to separate controls by layer.

| Layer | Primary control | Security purpose |
|---|---|---|
| Network boundary | VPC | Defines the network environment |
| Network segmentation | Subnets | Separates workloads by network role |
| Routing | Route tables | Controls where traffic can go |
| Resource traffic control | Security Groups | Stateful allow rules |
| Subnet traffic control | Network ACLs | Stateless subnet-level filtering |
| Internet boundary | Internet Gateway / NAT Gateway | Controls Internet connectivity paths |
| Private AWS access | VPC Endpoints | Avoids unnecessary Internet paths |
| Application edge | ALB, CloudFront, WAF | Controls and inspects application ingress |
| Identity | IAM | Controls AWS API access |
| Encryption | TLS, IPsec, KMS | Protects data in transit and at rest |
| Visibility | VPC Flow Logs, CloudTrail | Supports detection and investigation |
| Host/application | OS and application controls | Protects workloads after network access |
| Secrets | Secrets Manager / Parameter Store | Protects credentials and configuration |

Security is strongest when these controls are layered rather than relying on a single mechanism.

---

## Defense in Depth

A production backend should not depend on one security boundary.

For example, consider a PostgreSQL database:

```text
Internet
   |
   X  No direct route
   |
Public/Private Network Boundary
   |
   v
Application Security Group
   |
   v
Database Security Group
   |
   v
PostgreSQL
```

The database should generally have:

- No public IP
- No route to an Internet Gateway
- A restrictive Security Group
- Restricted administrative access
- Encryption at rest
- TLS for database connections where required
- Authentication and authorization
- Monitoring and audit controls

If one control is accidentally weakened, the remaining controls should still limit the blast radius.

---

## VPC Isolation

A VPC provides a logical network boundary, but isolation is only useful when routing and access controls are designed correctly.

A typical production environment may use:

```text
VPC
 |
 +-- Public Subnets
 |     |
 |     +-- Load Balancers
 |
 +-- Private Application Subnets
 |     |
 |     +-- Django
 |     +-- FastAPI
 |     +-- Celery
 |     +-- Kubernetes workloads
 |
 +-- Private Data Subnets
       |
       +-- PostgreSQL
       +-- Redis
```

The key principle is **do not expose a workload merely because connectivity is convenient**.

For example, an application server normally does not need:

```text
0.0.0.0/0 -> application server
```

Instead:

```text
Internet
   |
   v
Load Balancer
   |
   v
Application
```

The load balancer becomes the controlled ingress point.

---

## Public and Private Subnets

A subnet is public when its route table provides a path through an Internet Gateway and the workload has the necessary public addressing.

A private subnet does not have a direct route to an Internet Gateway.

A common production layout is:

```text
                    Internet
                       |
                       v
                Internet Gateway
                       |
              +--------+--------+
              |                 |
        Public Subnet A    Public Subnet B
              |                 |
             ALB               ALB
              |                 |
              +--------+--------+
                       |
                Private Subnets
                  /         \
                 /           \
          Application A   Application B
                 \           /
                  \         /
                  Database
```

Private workloads may still need outbound access for:

- Package repositories
- External APIs
- Container image registries
- Operating-system updates
- AWS APIs

That traffic can be provided through a NAT Gateway or, where supported, through VPC endpoints.

---

## Security Groups

Security Groups are the primary resource-level network access control mechanism for many AWS workloads.

They are:

- Stateful
- Associated with resources or network interfaces
- Allow-list based
- Evaluated before traffic reaches the resource

A common application architecture is:

```text
Internet
   |
   v
ALB SG
   |
   | TCP 443
   v
Application SG
   |
   | TCP 5432
   v
Database SG
```

The application Security Group should not normally allow PostgreSQL traffic from the entire VPC or Internet.

Instead, the database Security Group can reference the application Security Group as the source.

### Example

```text
Database SG

Inbound:
TCP 5432
Source: Application SG
```

This is preferable to:

```text
TCP 5432
Source: 10.0.0.0/16
```

because the first rule expresses an architectural dependency rather than trusting an entire CIDR range.

### Stateful Behavior

If an application initiates:

```text
Application -> Database
```

the response traffic is automatically allowed by the stateful behavior of the Security Group.

This differs from Network ACLs, which are stateless.

---

## Security Group Design Principles

Use separate Security Groups for distinct roles.

| Security Group | Typical inbound source |
|---|---|
| ALB SG | Internet or trusted upstream |
| Application SG | ALB SG |
| Worker SG | Internal application services |
| Database SG | Application SG |
| Redis SG | Application/worker SG |
| Internal service SG | Specific service SG |

Avoid creating one large Security Group such as:

```text
backend-production-sg
```

and attaching it to every resource.

That approach makes dependency boundaries unclear and often leads to unnecessarily broad access.

---

## Network ACLs

Network ACLs operate at the subnet boundary.

They are:

- Stateless
- Associated with subnets
- Rule-number based
- Support allow and deny rules

Because they are stateless, return traffic must be explicitly permitted.

For example:

```text
Client
  |
  | TCP 443
  v
Subnet
  |
  v
Server
  |
  | TCP ephemeral port
  v
Client
```

The appropriate return traffic must be permitted by the Network ACL.

### Security Group vs Network ACL

| Property | Security Group | Network ACL |
|---|---|---|
| Scope | Resource/network interface | Subnet |
| State | Stateful | Stateless |
| Rules | Allow | Allow and deny |
| Return traffic | Automatically tracked | Must be explicitly allowed |
| Typical use | Workload access control | Subnet-level boundary control |
| Operational complexity | Lower | Higher |

For most application architectures, Security Groups should provide the primary workload-level controls. Network ACLs should be introduced intentionally rather than used as a default source of complex filtering rules.

---

## Route Tables as Security Controls

Route tables are not firewalls, but routing decisions have direct security implications.

Consider:

```text
Private App Subnet
       |
       +-- 0.0.0.0/0 --> NAT Gateway
       |
       +-- 10.20.0.0/16 --> Transit Gateway
       |
       +-- AWS service prefixes --> VPC Endpoint
```

Each route creates a possible traffic path.

A senior-level VPC review therefore asks:

- Which destinations can this subnet reach?
- Which networks can reach this subnet?
- Does traffic leave the AWS network unnecessarily?
- Can this subnet reach production systems?
- Can a compromised workload pivot into another environment?
- Is the route required?

Routing should be designed together with Security Groups and network segmentation.

---

## Internet Gateway Security

An Internet Gateway provides Internet connectivity for a VPC.

It does not automatically make every resource public.

A resource generally requires the appropriate:

- Route to the Internet Gateway
- Public IPv4 address or equivalent Internet-reachable addressing
- Security Group rules
- Network ACL rules

This distinction is important:

```text
VPC + Internet Gateway
```

does not mean:

```text
Every resource = publicly reachable
```

Security depends on the combination of routing, addressing, and access controls.

---

## NAT Gateway Security

NAT Gateway allows resources in private subnets to initiate connections to external destinations without allowing unsolicited inbound connections through the NAT path.

Typical architecture:

```text
Private Application
       |
       v
Private Route Table
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

NAT Gateway is primarily an **egress mechanism**, not an inbound access mechanism.

### Production Considerations

For multi-AZ production workloads, a common design is:

```text
AZ-A                         AZ-B
 |                            |
Private App                  Private App
 |                            |
NAT-A                        NAT-B
 |                            |
 +-------------+--------------+
               |
          Internet Gateway
```

Using a single NAT Gateway for all AZs can introduce:

- A cross-AZ dependency
- Additional cross-AZ traffic
- A larger failure domain
- Potential performance bottlenecks

Cost optimization should therefore be evaluated against availability and traffic patterns rather than applied blindly.

---

## VPC Endpoints

VPC endpoints provide private connectivity to supported AWS services.

They are particularly useful for reducing unnecessary Internet/NAT dependency.

For example:

```text
Private Application
       |
       v
VPC Endpoint
       |
       v
Amazon S3
```

This can be preferable to:

```text
Private Application
       |
       v
NAT Gateway
       |
       v
Internet Gateway
       |
       v
AWS Service
```

Endpoint policies and Security Groups should still be reviewed carefully.

VPC endpoints are particularly useful for private workloads that frequently access AWS services such as S3, ECR, CloudWatch, Secrets Manager, or other supported AWS APIs.

---

## Application Edge Security

The VPC is only one part of Internet-facing security.

A common backend architecture is:

```text
                    Internet
                       |
                       v
                   CloudFront
                       |
                       v
                      WAF
                       |
                       v
                      ALB
                       |
                       v
                Private Application
```

### CloudFront

Can provide:

- Edge delivery
- TLS termination
- Caching
- DDoS protection integration
- Geographic distribution

### AWS WAF

Can provide controls such as:

- IP filtering
- Rate-based rules
- Managed rule groups
- Request inspection
- Application-layer filtering

### Load Balancer

Provides controlled application ingress and can terminate TLS before forwarding traffic to private workloads.

---

## Encryption

Private networking and encryption solve different problems.

A private route does not necessarily mean traffic is encrypted.

For example:

```text
Application
    |
    | Private VPC network
    v
PostgreSQL
```

provides network isolation but does not by itself establish application-level encryption.

Depending on the requirement, use:

- TLS for application traffic
- TLS for database connections
- HTTPS for APIs
- IPsec for Site-to-Site VPN
- AWS-managed encryption mechanisms
- KMS-backed encryption for supported services

For service-to-service communication, especially in microservice architectures, consider TLS even when services communicate over private VPC networking.

---

## IAM and VPC Security

VPC security and IAM security are complementary.

IAM controls access to AWS APIs and resources.

For example:

```text
Developer
   |
   v
IAM
   |
   v
AWS API
   |
   v
VPC Resource
```

Network access alone should not determine whether an identity can perform an operation.

A compromised EC2 instance, container, or workload should have only the IAM permissions it requires.

Use:

- IAM roles instead of long-lived credentials
- Least-privilege policies
- Short-lived credentials
- Service-specific roles
- Permission boundaries where appropriate
- Centralized identity controls

---

## VPC Security and Microservices

A microservices architecture often contains:

```text
              API Gateway / ALB
                     |
          +----------+----------+
          |          |          |
       Service A  Service B  Service C
          |          |          |
          +----------+----------+
                     |
              Internal Services
```

Security Groups can represent service boundaries.

For example:

```text
Service A SG
    |
    +----> Service B SG : 8080
```

instead of:

```text
Service A
    |
    +----> 10.0.0.0/16 : 8080
```

This makes the intended trust relationship explicit.

For gRPC services, the same principle applies:

```text
Service A
   |
   | TCP 50051
   v
Service B
```

The Security Group should restrict access to known callers.

---

## Kubernetes and VPC Security

For Kubernetes workloads, VPC security becomes more complex because pods may participate directly in the VPC networking model depending on the networking configuration.

Security should therefore exist at multiple layers:

```text
Internet
   |
   v
AWS Edge Controls
   |
   v
Load Balancer
   |
   v
Kubernetes
   |
   +-- Network Policies
   |
   +-- Security Groups
   |
   +-- IAM / Pod Identity
   |
   +-- Application Authentication
```

Do not assume that a Kubernetes namespace or private subnet is sufficient isolation.

Network policies, IAM, workload identity, and application-level authorization remain important.

---

## VPC Flow Logs

VPC Flow Logs provide visibility into network traffic metadata.

They are useful for:

- Troubleshooting connectivity
- Investigating rejected traffic
- Identifying unexpected communication
- Security investigations
- Detecting unusual traffic patterns
- Validating network architecture

A simplified flow is:

```text
Workload
   |
   v
Network Interface
   |
   v
VPC Flow Logs
   |
   v
CloudWatch Logs / S3
   |
   v
Analysis / Detection
```

Flow Logs do not provide full packet captures. They provide network flow metadata.

Operationally, ensure logs are retained according to the organization's security and compliance requirements.

---

## Logging and Detection

A production VPC security strategy should combine multiple sources.

| Source | Useful for |
|---|---|
| VPC Flow Logs | Network traffic analysis |
| CloudTrail | AWS API activity |
| WAF logs | Web request inspection |
| Load Balancer logs | HTTP/TLS request visibility |
| Application logs | Business/application behavior |
| GuardDuty | Threat detection |
| Security Hub | Security findings aggregation |
| AWS Config | Configuration compliance |

The objective is not simply to collect logs, but to make security events actionable.

A useful operational pipeline is:

```text
AWS Services
     |
     +---- Flow Logs
     +---- CloudTrail
     +---- WAF Logs
     +---- Application Logs
     |
     v
Centralized Logging
     |
     v
Detection / Alerting
     |
     v
Incident Response
```

---

## Secrets and Credentials

Network isolation should never be used as a replacement for secret management.

Avoid:

```text
DATABASE_PASSWORD = "production-password"
```

inside:

- Git repositories
- Dockerfiles
- Container images
- Application source code
- CI/CD configuration files without secret protection

Prefer managed secret systems such as:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- IAM roles
- Short-lived credentials

A Django or FastAPI application should obtain secrets through its runtime configuration mechanism rather than embedding credentials in source code.

---

## Database Security

A production PostgreSQL architecture should generally resemble:

```text
Internet
   |
   X
   |
Load Balancer
   |
   v
Application
   |
   | TCP 5432
   v
PostgreSQL
```

The database should normally:

- Remain private
- Avoid public IP exposure
- Accept connections only from required application workloads
- Use strong authentication
- Encrypt connections where required
- Encrypt storage
- Have backups enabled
- Be monitored
- Use least-privilege database roles

Avoid:

```text
Database SG
TCP 5432
0.0.0.0/0
```

This is one of the most serious common VPC security misconfigurations.

---

## Redis Security

Redis should also remain private.

A common design is:

```text
Application SG
      |
      | TCP 6379
      v
Redis SG
```

Do not expose Redis directly to the Internet.

The same principle applies to:

- Kafka
- RabbitMQ
- Elasticsearch/OpenSearch
- Internal gRPC services
- Administrative services

Internal does not mean automatically trusted.

---

## Kafka Security

For Kafka-based architectures:

```text
Application
    |
    v
Kafka
    |
    +--> Consumer
    |
    +--> Consumer
```

Security should address:

- Network access
- Authentication
- Authorization
- Encryption in transit
- Encryption at rest
- Topic-level permissions
- Broker access
- Client credentials

A private subnet reduces exposure but does not replace Kafka-level authorization.

---

## Security Group Reference Architecture

A practical backend design may use:

```text
                 Internet
                    |
                    v
                 ALB SG
                    |
                 TCP 443
                    |
                    v
                 App SG
                /      \
               /        \
        TCP 5432       TCP 6379
             |             |
             v             v
          DB SG         Redis SG
             |
             v
        PostgreSQL
```

This creates explicit trust relationships:

```text
Internet -> ALB
ALB -> Application
Application -> Database
Application -> Redis
```

Unnecessary paths should not exist.

---

## Least Privilege

Least privilege applies to networking as well as IAM.

Bad:

```text
Application SG
  -> 0.0.0.0/0
  -> All TCP
```

Better:

```text
Application SG
  -> ALB SG
  -> TCP 443
```

And:

```text
Database SG
  -> Application SG
  -> TCP 5432
```

The goal is to minimize:

- Source networks
- Destination networks
- Ports
- Protocols
- Identities
- Trust relationships

---

## Security Architecture Review

A senior engineer should review a VPC using questions such as:

### Exposure

- Which resources have public IP addresses?
- Which resources are Internet reachable?
- Which ports are exposed?
- Is the exposure intentional?

### Routing

- Where can each subnet send traffic?
- Which networks can be reached?
- Are there unnecessary routes?
- Can workloads reach production networks they do not need?

### Access Control

- Which Security Groups permit traffic?
- Are Security Group references used where possible?
- Are Network ACLs introducing unexpected behavior?
- Are administrative ports restricted?

### Identity

- Which IAM role does each workload use?
- Can a compromised workload access unrelated AWS services?
- Are long-lived credentials present?

### Encryption

- Is TLS used where required?
- Are databases encrypted?
- Are secrets encrypted?
- Are VPN connections encrypted?

### Monitoring

- Are Flow Logs enabled where appropriate?
- Are AWS API calls logged?
- Are security findings centralized?
- Are alerts actionable?

---

## Common Mistakes

### Exposing Databases

**Mistake:**

```text
PostgreSQL
  |
  +-- Public IP
  +-- 5432 from 0.0.0.0/0
```

**Why it happens:** Developers want convenient remote database access.

**Better approach:** Keep the database private and provide controlled administrative access through mechanisms such as a bastionless management path, Systems Manager where supported, VPN, or controlled corporate connectivity.

### Allowing Entire VPC CIDRs

**Mistake:**

```text
TCP 5432
10.0.0.0/16
```

**Why it happens:** It is simpler than defining workload-specific trust.

**Better approach:** Reference the application Security Group when the architecture supports it.

### Assuming Private Means Secure

Private subnets reduce exposure but do not provide complete security.

A compromised application can still attack:

- Other internal services
- Metadata endpoints
- Databases
- AWS APIs
- Internal corporate networks

Segmentation and least privilege remain necessary.

### Using Security Groups as the Only Security Layer

Security Groups are important, but they do not replace:

- IAM
- Application authentication
- Authorization
- TLS
- Secrets management
- Logging
- Detection
- Patch management

### Overly Broad Egress

Allowing:

```text
0.0.0.0/0
All traffic
```

for every workload may be operationally convenient but can increase the impact of a compromised service.

Where practical, constrain egress based on actual requirements.

---

## Production Security Checklist

### Network

- [ ] Production workloads are segmented by role.
- [ ] Databases are private.
- [ ] Public exposure is intentional.
- [ ] CIDRs are documented.
- [ ] Routing is reviewed.
- [ ] Unnecessary routes are removed.

### Security Groups

- [ ] Inbound rules use least privilege.
- [ ] Security Group references are used where appropriate.
- [ ] Database ports are restricted.
- [ ] Administrative ports are restricted.
- [ ] Unnecessary outbound access is evaluated.

### Identity

- [ ] Workloads use IAM roles.
- [ ] Long-lived credentials are avoided.
- [ ] Permissions follow least privilege.
- [ ] Administrative access is centrally controlled.

### Encryption

- [ ] TLS is used for sensitive network communication.
- [ ] Database connections use encryption where required.
- [ ] Storage encryption is enabled.
- [ ] Secrets are stored in managed secret systems.

### Monitoring

- [ ] VPC Flow Logs are configured where appropriate.
- [ ] CloudTrail is enabled.
- [ ] WAF and load balancer logging is configured where required.
- [ ] Security findings are monitored.
- [ ] Alerts have clear operational ownership.

### Resilience

- [ ] Critical workloads span multiple AZs.
- [ ] Security controls are consistent across AZs.
- [ ] Hybrid connectivity has appropriate redundancy.
- [ ] Disaster recovery procedures include network dependencies.

---

## Interview Traps

### "Are private subnets secure?"

Not automatically.

A private subnet reduces direct Internet exposure, but internal traffic can still be malicious or excessive.

### "Does a Security Group deny traffic?"

Security Groups are allow-list based. Traffic that does not match an applicable allow rule is implicitly denied.

### "Are Network ACLs stateful?"

No. Network ACLs are stateless.

### "Does NAT Gateway allow inbound Internet traffic?"

NAT Gateway is designed for outbound connectivity initiated from private resources. It is not a general inbound Internet access mechanism.

### "Is VPC traffic automatically encrypted?"

Do not assume that private routing means application-layer encryption. Encryption requirements must be handled explicitly.

### "Is IAM enough for VPC security?"

No. IAM controls AWS API permissions; network controls govern network reachability. Both are required.

---

## Practical Security Architecture

A production backend can combine the controls as follows:

```mermaid
flowchart TB
    INTERNET["Internet"]
    EDGE["CloudFront / WAF"]
    ALB["Application Load Balancer"]
    
    subgraph VPC["Production VPC"]
        subgraph APP["Private Application Subnets"]
            APP1["Django / FastAPI"]
            APP2["Celery / Workers"]
            APP3["Microservices"]
        end

        subgraph DATA["Private Data Subnets"]
            DB["PostgreSQL"]
            REDIS["Redis"]
            KAFKA["Kafka"]
        end

        ENDPOINTS["VPC Endpoints"]
        NAT["NAT Gateway"]
        LOGS["VPC Flow Logs"]
    end

    IAM["IAM / Workload Identity"]
    CLOUDTRAIL["CloudTrail"]
    SECURITY["Detection / Security Monitoring"]

    INTERNET --> EDGE
    EDGE --> ALB
    ALB --> APP1
    ALB --> APP3

    APP1 --> DB
    APP1 --> REDIS
    APP2 --> KAFKA
    APP3 --> KAFKA

    APP1 --> ENDPOINTS
    APP2 --> ENDPOINTS
    APP3 --> NAT

    APP1 -.-> LOGS
    APP2 -.-> LOGS
    APP3 -.-> LOGS

    IAM -.-> APP1
    IAM -.-> APP2
    IAM -.-> APP3

    LOGS --> SECURITY
    CLOUDTRAIL --> SECURITY
```

The architecture demonstrates defense in depth:

```text
Network Isolation
        +
Routing Controls
        +
Security Groups
        +
Identity
        +
Encryption
        +
Secrets Management
        +
Logging
        +
Detection
        +
Application Security
```

No single control is expected to provide complete protection.

---

## Key Takeaways

- VPC security is a **defense-in-depth system** combining network isolation, routing, Security Groups, identity, encryption, monitoring, and application controls.
- **Security Groups should express explicit workload trust relationships**, while Network ACLs provide stateless subnet-level filtering when required.
- Private subnets reduce Internet exposure but do not automatically make workloads secure; **least privilege, IAM, TLS, secrets management, and application authorization remain necessary**.
- Production VPCs should minimize public exposure, restrict database and internal-service access, use private AWS connectivity where appropriate, and maintain strong observability.
- Senior-level VPC security design focuses on **attack surface, blast radius, trust boundaries, failure modes, and operational detectability**, not merely whether resources are placed in private subnets.