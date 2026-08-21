# 02- Security Groups

## Overview

Amazon VPC Security Groups are **stateful, resource-level virtual firewalls** that control network traffic to and from supported AWS resources. They are one of the primary mechanisms for enforcing network-level access control inside a VPC.

Security Groups should be designed around **explicit workload trust relationships** rather than broad network access.

A production backend architecture commonly looks like:

```text
                         Internet
                            |
                            | HTTPS :443
                            v
                    +----------------+
                    | Load Balancer  |
                    |    ALB SG      |
                    +-------+--------+
                            |
                            | Application traffic
                            v
                    +----------------+
                    | Django/FastAPI |
                    |    App SG      |
                    +-------+--------+
                            |
                 +----------+----------+
                 |                     |
              :5432                  :6379
                 |                     |
                 v                     v
          +-------------+       +-------------+
          | PostgreSQL  |       |    Redis    |
          |    DB SG    |       |  Redis SG   |
          +-------------+       +-------------+
```

The intended trust relationships are:

```text
Internet
   |
   v
ALB SG
   |
   v
Application SG
   |
   +----> Database SG
   |
   +----> Redis SG
```

This is fundamentally different from allowing an entire VPC CIDR to communicate with every workload.

---

## What Is a Security Group?

A Security Group is a virtual firewall associated with supported AWS resources through their network interfaces.

It controls:

- Inbound traffic
- Outbound traffic
- Protocols
- Ports
- Source or destination IP ranges
- References to other Security Groups

Security Groups operate at the **resource/network-interface level**, while Network ACLs operate at the **subnet level**.

A Security Group does not inspect application payloads like an application firewall. For HTTP-specific filtering, rate limiting, SQL injection protection, bot controls, and similar concerns, services such as AWS WAF or application-level controls are more appropriate.

---

## Why Security Groups Exist

VPC routing determines whether traffic has a path to a destination. Security Groups determine whether that traffic is permitted to reach the resource.

Consider:

```text
Client
  |
  | TCP 443
  v
Application
```

Routing may make the application reachable, but the Security Group can still reject the connection.

A useful mental model is:

```text
Can traffic reach the network?
        |
        v
     Routing
        |
        v
Is the traffic allowed to reach the resource?
        |
        v
   Security Group
        |
        v
Can the application accept the request?
        |
        v
Application authentication / authorization
```

Security Groups therefore form one layer of a larger defense-in-depth architecture.

---

## Core Properties

Security Groups have several properties that are important for architecture and troubleshooting.

| Property | Security Group behavior |
|---|---|
| Scope | Resource/network-interface level |
| State | Stateful |
| Rule type | Allow only |
| Explicit deny | Not supported |
| Inbound rules | Control incoming traffic |
| Outbound rules | Control outgoing traffic |
| Default behavior | New Security Groups begin with no inbound rules and a default outbound rule |
| Association | Resources can have one or more Security Groups |
| Evaluation | Rules are evaluated as a combined allow set |
| Source/destination | CIDR, Security Group, and supported prefix-list references |
| Subnet association | No direct subnet association |

The exact capabilities can vary by AWS resource, but the core security model remains the same.

---

## Stateful Behavior

Security Groups are **stateful**.

If an allowed inbound connection is established, return traffic for that connection is automatically allowed, even if there is no corresponding explicit outbound rule for that return direction.

Likewise, when a resource initiates an allowed outbound connection, the response traffic is automatically tracked as part of that connection.

For example:

```text
Application
    |
    | TCP SYN :5432
    v
PostgreSQL
    |
    | TCP response
    v
Application
```

If the database Security Group allows the application's traffic, the response traffic is tracked automatically.

This is one of the most important differences between Security Groups and Network ACLs.

---

## Security Group Rules

A rule generally defines:

```text
Protocol
    +
Port or Port Range
    +
Source/Destination
```

For example:

```text
Protocol: TCP
Port: 443
Source: 0.0.0.0/0
```

means:

```text
Allow TCP connections from any IPv4 address to port 443.
```

A more restrictive rule could be:

```text
Protocol: TCP
Port: 5432
Source: Application SG
```

which means:

```text
Allow PostgreSQL traffic from resources associated with the Application Security Group.
```

The second design is generally preferable for internal application dependencies.

---

## Inbound Rules

Inbound rules determine which traffic can reach the resource.

For an Internet-facing ALB:

```text
ALB SG

Inbound:
TCP 443
Source: 0.0.0.0/0
```

For an application service behind that ALB:

```text
Application SG

Inbound:
TCP 8000
Source: ALB SG
```

For PostgreSQL:

```text
Database SG

Inbound:
TCP 5432
Source: Application SG
```

This creates an explicit dependency chain:

```text
Internet
   |
   | 443
   v
ALB
   |
   | 8000
   v
Application
   |
   | 5432
   v
PostgreSQL
```

The database is not exposed merely because the VPC itself has Internet connectivity.

---

## Outbound Rules

Outbound rules determine which connections a resource can initiate.

A common default Security Group configuration allows:

```text
All outbound traffic
Destination: 0.0.0.0/0
```

This is operationally convenient, but it may be broader than necessary for security-sensitive workloads.

A more restrictive architecture may allow only required destinations.

For example:

```text
Application
   |
   +----> PostgreSQL :5432
   |
   +----> Redis :6379
   |
   +----> Internal API :443
   |
   +----> Required AWS services
```

However, restricting egress too aggressively can create operational problems.

Before tightening outbound rules, identify:

- AWS APIs the workload calls
- DNS requirements
- Package repositories
- External APIs
- Monitoring endpoints
- Authentication services
- Container registries
- Time synchronization requirements
- Software update mechanisms

Security controls should be based on actual traffic requirements rather than arbitrary restrictions.

---

## Multiple Security Groups

A resource can have multiple Security Groups.

For example:

```text
Application ENI
    |
    +-- Application SG
    |
    +-- Monitoring SG
    |
    +-- Shared Service SG
```

The effective behavior is important:

> Rules from all associated Security Groups are combined, and traffic is allowed when an applicable allow rule exists.

This means adding a permissive Security Group can unintentionally expand access even when the primary Security Group looks restrictive.

### Example

Suppose:

```text
App SG:
TCP 443 from ALB SG
```

and:

```text
Debug SG:
TCP 22 from 0.0.0.0/0
```

If both are attached to the instance, SSH may be publicly reachable.

The effective security posture must therefore be evaluated across **all attached Security Groups**.

---

## Security Group References

For internal AWS communication, Security Group references are often preferable to hard-coded CIDRs.

Instead of:

```text
Database SG
TCP 5432
Source: 10.20.0.0/16
```

use:

```text
Database SG
TCP 5432
Source: Application SG
```

This expresses:

```text
Application workloads
        |
        | PostgreSQL
        v
Database workloads
```

rather than:

```text
Everything inside this CIDR
        |
        | PostgreSQL
        v
Database
```

The Security Group reference remains meaningful even when instances or IP addresses change.

---

## Security Group References vs CIDRs

| Approach | Advantages | Limitations |
|---|---|---|
| Security Group reference | Expresses workload trust | Requires resources to use appropriate SG relationships |
| CIDR | Simple and explicit network boundary | Can become broad and difficult to maintain |
| Public CIDR | Useful for intended Internet-facing services | High exposure |
| Private CIDR | Useful for network-level boundaries | Does not identify workload role |

For service-to-service communication, prefer Security Group references when they accurately represent the trust relationship.

CIDRs remain appropriate when the trust boundary is genuinely network-based.

---

## Security Group Architecture

A production backend can use role-based Security Groups:

```mermaid
flowchart LR
    INTERNET["Internet"] --> ALB["ALB<br/>ALB SG"]

    ALB --> APP["Django / FastAPI<br/>Application SG"]

    APP --> DB["PostgreSQL<br/>Database SG"]
    APP --> REDIS["Redis<br/>Redis SG"]
    APP --> KAFKA["Kafka<br/>Kafka SG"]

    WORKER["Celery Workers<br/>Worker SG"] --> DB
    WORKER --> REDIS
    WORKER --> KAFKA
```

The intended relationships are:

| Source | Destination | Port | Reason |
|---|---|---:|---|
| Internet | ALB SG | 443 | Public HTTPS |
| ALB SG | Application SG | 8000/443 | Application traffic |
| Application SG | Database SG | 5432 | PostgreSQL |
| Application SG | Redis SG | 6379 | Redis |
| Application/Worker SG | Kafka SG | Kafka listener port | Event streaming |
| Worker SG | Database SG | 5432 | Background jobs |

The exact ports depend on the application and deployment model.

---

## Application Security Group

For a Django or FastAPI service behind an ALB:

```text
Application SG

Inbound:
TCP 8000
Source: ALB SG
```

The application does not need:

```text
TCP 8000
Source: 0.0.0.0/0
```

This prevents direct Internet access to the application when the ALB is intended to be the only public entry point.

### Request Flow

```text
Client
  |
  | HTTPS :443
  v
ALB
  |
  | HTTP/TCP :8000
  v
Django/FastAPI
```

The ALB Security Group controls Internet ingress.

The Application Security Group controls traffic from the ALB.

This creates two independent boundaries.

---

## Database Security Group

A PostgreSQL database should normally be reachable only by workloads that require database access.

```text
Database SG

Inbound:
TCP 5432
Source: Application SG
```

For Celery workers that directly access PostgreSQL:

```text
Database SG

Inbound:
TCP 5432
Sources:
- Application SG
- Worker SG
```

Avoid:

```text
TCP 5432
Source: 0.0.0.0/0
```

This is an extremely high-risk configuration for a production database.

A private subnet does not justify a permissive database Security Group.

---

## Redis Security Group

For Redis:

```text
Redis SG

Inbound:
TCP 6379
Source:
- Application SG
- Worker SG
```

The Redis service remains private:

```text
Internet
   |
   X
   |
Redis
```

Applications communicate through the VPC:

```text
Application
    |
    | TCP 6379
    v
Redis
```

Security Groups should prevent unrelated workloads from reaching Redis.

---

## Kafka Security Group

Kafka typically requires multiple broker/client communication paths depending on the deployment and listener configuration.

A simplified model is:

```text
Producer SG
     |
     | Kafka listener
     v
Kafka SG
     |
     +----> Broker communication
     |
     +----> Consumer SG
```

Do not simply expose Kafka listener ports to the entire VPC without understanding which workloads actually require access.

Network controls should complement Kafka's own:

- Authentication
- Authorization
- TLS
- Topic-level access controls

---

## Security Groups and gRPC

gRPC commonly runs over HTTP/2 and therefore requires network connectivity to the appropriate service port.

For example:

```text
Service A
   |
   | TCP 50051
   v
Service B
```

The receiving service might use:

```text
Service B SG

Inbound:
TCP 50051
Source: Service A SG
```

This is preferable to:

```text
TCP 50051
Source: 10.0.0.0/8
```

when the architecture only requires Service A to communicate with Service B.

Security Groups provide network-level authorization; gRPC authentication and application authorization remain separate concerns.

---

## Security Groups and Docker

Docker containers running on EC2 do not automatically create a Security Group per container.

The Security Group is generally associated with the underlying network interface or supported AWS networking construct.

For example:

```text
EC2
 |
 +-- ENI
      |
      +-- EC2 Security Group
      |
      +-- Docker
           |
           +-- Django
           +-- Celery
           +-- Nginx
```

If fine-grained network isolation between workloads is required, the architecture must use appropriate networking controls rather than assuming Docker's container boundaries are equivalent to AWS Security Groups.

For ECS and Kubernetes, the exact networking and Security Group model depends on the networking mode and platform configuration.

---

## Security Groups and Kubernetes

With Amazon EKS, Security Groups can participate in workload-level network security depending on the configured networking model.

A typical layered model is:

```text
Internet
   |
   v
Load Balancer
   |
   v
Kubernetes Service
   |
   v
Pod
   |
   +-- Network Policy
   +-- Security Group controls where applicable
   +-- IAM / Pod Identity
   +-- Application authentication
```

Security Groups should not be treated as a replacement for Kubernetes NetworkPolicies.

The controls operate at different layers.

---

## Security Groups and Nginx

A common architecture is:

```text
Internet
   |
   v
ALB
   |
   v
Nginx
   |
   v
Django/FastAPI
```

If Nginx is directly behind the ALB:

```text
Nginx SG

Inbound:
TCP 80/443
Source: ALB SG
```

The backend application can then use:

```text
Application SG

Inbound:
TCP 8000
Source: Nginx SG
```

This creates:

```text
ALB SG
   |
   v
Nginx SG
   |
   v
Application SG
```

However, avoid adding network layers solely for security theater. Each layer should have a clear responsibility.

---

## Ephemeral Ports

One common source of confusion is ephemeral ports.

A client usually connects from an ephemeral source port to a known destination port.

For example:

```text
Application
Source: 49152
Destination: 5432
        |
        v
PostgreSQL
```

The destination service listens on a well-known port such as:

```text
5432
```

The client's operating system may select an ephemeral source port.

Because Security Groups are stateful, return traffic for an established allowed connection is tracked automatically.

This is one reason Security Group behavior differs substantially from stateless packet filtering.

---

## Security Group Evaluation

Security Groups do not process rules as a simple top-to-bottom firewall rule list.

Suppose a resource has:

```text
SG-A:
TCP 443 from 10.0.0.0/16
```

and:

```text
SG-B:
TCP 443 from 0.0.0.0/0
```

If both are attached, the second rule can permit Internet traffic.

There is no later rule that can override it with a deny rule.

This is why Security Group hygiene is critical.

---

## No Explicit Deny Rules

Security Groups support allow rules, not explicit deny rules.

If traffic does not match an applicable allow rule, it is implicitly denied.

This has an important architectural consequence.

If you need:

```text
Allow A
Deny B
```

within the same network boundary, Security Groups alone may not be sufficient.

Possible additional controls include:

- Network ACLs
- AWS WAF
- Routing isolation
- Application authorization
- Identity-based controls

The correct control depends on the type of traffic being controlled.

---

## Default Security Group

Every VPC has a default Security Group.

The default Security Group has special behavior, including allowing traffic between resources that use that same default Security Group.

For production architectures, avoid treating the default Security Group as the primary application security boundary.

Instead:

- Create purpose-specific Security Groups.
- Name them according to workload roles.
- Remove unnecessary dependencies on the default Security Group.
- Audit resources that remain attached to it.

Example naming:

```text
prod-alb-sg
prod-api-sg
prod-worker-sg
prod-postgres-sg
prod-redis-sg
prod-kafka-sg
```

---

## Security Group Naming and Ownership

A mature environment should make Security Group ownership obvious.

Useful metadata includes:

| Attribute | Example |
|---|---|
| Name | `prod-api-sg` |
| Environment | `production` |
| Application | `orders-api` |
| Owner | `backend-platform` |
| Purpose | `API ingress from ALB` |
| Managed by | `Terraform` |

Infrastructure as Code is particularly useful because Security Group changes can be reviewed through pull requests.

---

## Infrastructure as Code

A Terraform example:

```hcl
resource "aws_security_group" "api" {
  name        = "prod-api-sg"
  description = "Allow application traffic from the ALB"
  vpc_id      = var.vpc_id

  ingress {
    description     = "HTTPS/application traffic from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Required outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "prod-api-sg"
    Environment = "production"
  }
}
```

For production systems, the actual egress model should be based on the application's requirements.

Security Group definitions should be reviewed like application code because an incorrect rule can materially change the system's attack surface.

---

## AWS CLI Examples

List Security Groups:

```bash
aws ec2 describe-security-groups \
  --query 'SecurityGroups[].{ID:GroupId,Name:GroupName,VPC:VpcId}'
```

Inspect a specific Security Group:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0
```

Authorize HTTPS ingress:

```bash
aws ec2 authorize-security-group-ingress \
  --group-id sg-0123456789abcdef0 \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

Revoke the rule:

```bash
aws ec2 revoke-security-group-ingress \
  --group-id sg-0123456789abcdef0 \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

For production infrastructure, prefer Infrastructure as Code over ad-hoc CLI changes so that configuration remains reproducible and reviewable.

---

## Production Security Group Design

A production backend can use:

```text
                    Internet
                       |
                    TCP 443
                       |
                       v
                 +-----------+
                 |   ALB SG  |
                 +-----+-----+
                       |
                    TCP 8000
                       |
                       v
                 +-----------+
                 |   API SG  |
                 +--+-----+--+
                    |     |
                5432|     |6379
                    |     |
                    v     v
              +-------+ +-------+
              | DB SG | |Redis SG|
              +-------+ +-------+
```

This design has several useful properties:

- Public access terminates at the ALB.
- Application instances are not directly Internet-facing.
- PostgreSQL is reachable only by approved application workloads.
- Redis is reachable only by approved application workloads.
- Each trust boundary is explicit.

---

## Security Group Design Principles

### Separate by Workload Role

Prefer:

```text
ALB SG
API SG
Worker SG
Database SG
Redis SG
Kafka SG
```

over:

```text
everything-production-sg
```

### Prefer Explicit Dependencies

Use:

```text
Database SG <- API SG
```

when the database trusts the API workload.

### Minimize Ports

If a service requires only:

```text
TCP 443
```

do not expose:

```text
TCP 0-65535
```

### Minimize Sources

Prefer:

```text
Source: ALB SG
```

over:

```text
Source: 0.0.0.0/0
```

when the service is internal.

### Review Egress

Do not automatically assume that unrestricted outbound traffic is required.

But also avoid blocking required dependencies without understanding the application's network behavior.

---

## Security Group vs Network ACL

Security Groups and Network ACLs solve related but different problems.

| Feature | Security Group | Network ACL |
|---|---|---|
| Scope | Resource | Subnet |
| Stateful | Yes | No |
| Rules | Allow only | Allow and deny |
| Rule ordering | Not top-to-bottom | Rule number ordering |
| Typical purpose | Workload access control | Subnet-level filtering |
| Common operational complexity | Lower | Higher |
| Best fit | Application/resource boundaries | Additional subnet boundary controls |

For a typical backend platform:

```text
VPC
 |
 +-- Network ACL
 |
 +-- Subnets
      |
      +-- Security Groups
           |
           +-- Workloads
```

Do not use Network ACLs to compensate for poorly designed Security Groups.

---

## Security Group vs IAM

These controls operate at different layers.

| Control | Controls |
|---|---|
| Security Group | Network connectivity |
| IAM | AWS API/resource permissions |
| Application auth | User/service identity |
| Database permissions | Database-level access |
| WAF | HTTP/application-layer traffic |

For example:

```text
Can the API connect to S3?
        |
        +-- Network path -> VPC Endpoint / NAT
        |
        +-- AWS authorization -> IAM
```

Both network connectivity and IAM authorization may be required.

---

## Security Group vs Application Authorization

A Security Group can answer:

```text
Can Service A establish a TCP connection to Service B?
```

It cannot answer:

```text
Is this authenticated user allowed to delete this order?
```

That responsibility belongs to application-level authorization.

For a Django or FastAPI service:

```text
Network Security
      |
      v
Security Group
      |
      v
TLS
      |
      v
Authentication
      |
      v
Authorization
      |
      v
Business Logic
```

Network security and application security must therefore be designed together.

---

## Common Mistakes

### Allowing Everything

```text
Inbound:
All traffic
0.0.0.0/0
```

This effectively removes the Security Group as a useful inbound boundary.

Use specific protocols, ports, and sources.

### Exposing SSH Globally

Avoid:

```text
TCP 22
0.0.0.0/0
```

for ordinary production workloads.

Prefer controlled administrative access mechanisms and restrict administrative connectivity to approved networks or identities.

### Exposing Databases

Never assume a database is safe because it is "behind the application."

The database Security Group itself must enforce the intended access boundary.

### Using the Entire VPC CIDR Everywhere

This:

```text
10.0.0.0/16
```

may contain:

- Application servers
- Workers
- Containers
- Development workloads
- Internal tools
- Future services

Using the entire CIDR may therefore create excessive trust.

### Forgetting Multiple Attached Security Groups

A resource can inherit access from every associated Security Group.

When debugging an unexpected open port, inspect all attached Security Groups.

### Over-Restricting Egress

A developer may remove all outbound access and then discover that:

- DNS fails
- AWS APIs fail
- Package downloads fail
- External APIs fail
- Monitoring fails

Egress restrictions must be designed around actual dependencies.

### Editing Production Rules Manually

Direct console changes can create configuration drift.

Prefer:

```text
Terraform
   |
   v
Pull Request
   |
   v
Review
   |
   v
CI/CD
   |
   v
AWS
```

---

## Troubleshooting Connectivity

When an application cannot connect to a database, do not immediately change the Security Group.

Check the entire network path.

```text
Application
    |
    v
DNS resolution
    |
    v
Route table
    |
    v
Network ACL
    |
    v
Database ENI
    |
    v
Database Security Group
    |
    v
PostgreSQL listener
```

A useful troubleshooting sequence is:

1. Confirm the destination hostname resolves correctly.
2. Confirm the destination IP is expected.
3. Confirm the application has a route to the destination.
4. Inspect the application subnet route table.
5. Inspect Network ACLs if applicable.
6. Inspect all Security Groups attached to the source and destination.
7. Confirm the destination port is correct.
8. Confirm the service is actually listening.
9. Check host-level firewalls where applicable.
10. Review VPC Flow Logs and application logs.

Changing Security Groups without understanding the failure often creates a larger security problem.

---

## VPC Flow Logs and Security Groups

VPC Flow Logs can help identify whether traffic is being accepted or rejected at the network layer.

For example:

```text
Application
    |
    | TCP 5432
    v
Database
    |
    v
VPC Flow Logs
```

Flow Logs can help answer:

- Was traffic observed?
- What source and destination addresses were involved?
- What port and protocol were used?
- Was the traffic accepted or rejected?

They do not replace application logs or packet-level debugging.

---

## Monitoring and Governance

Security Groups should be continuously governed in production.

Useful controls include:

- AWS Config rules
- Security Hub
- GuardDuty
- VPC Flow Logs
- CloudTrail
- Infrastructure-as-Code review
- Periodic access reviews

Useful detection targets include:

```text
0.0.0.0/0 -> TCP 22
0.0.0.0/0 -> TCP 5432
0.0.0.0/0 -> TCP 6379
0.0.0.0/0 -> All TCP
0.0.0.0/0 -> All traffic
```

These are not automatically vulnerabilities in every architecture, but they should trigger review.

For example:

```text
0.0.0.0/0 -> TCP 443
```

may be completely appropriate for a public HTTPS load balancer.

The security review must consider **what resource owns the rule and why the exposure exists**.

---

## High Availability Considerations

Security Groups are regional VPC constructs and can be associated with resources across Availability Zones.

A multi-AZ architecture should use consistent security policy:

```text
                 ALB SG
                /      \
               /        \
          App SG       App SG
             |            |
          DB SG          DB SG
```

Avoid manually configuring different rules in different AZs unless there is a deliberate architectural reason.

Infrastructure as Code helps ensure that the same security policy is applied consistently.

---

## Scalability Considerations

Security Group architecture should scale with the number of services.

A service-oriented model:

```text
API SG
Worker SG
Payment SG
Notification SG
Database SG
Redis SG
Kafka SG
```

is generally easier to reason about than a small number of highly permissive groups.

However, excessive fragmentation can also become difficult to manage.

The goal is not:

```text
One SG per process
```

but:

```text
One SG per meaningful security boundary
```

Security Groups should represent **trust relationships**, not merely organizational naming.

---

## Security Group Dependencies

A mature architecture can be represented as a dependency graph:

```mermaid
flowchart LR
    ALB["ALB SG"]
    API["API SG"]
    WORKER["Worker SG"]
    DB["Database SG"]
    REDIS["Redis SG"]
    KAFKA["Kafka SG"]

    ALB -->|"TCP 8000"| API
    API -->|"TCP 5432"| DB
    API -->|"TCP 6379"| REDIS
    WORKER -->|"TCP 5432"| DB
    WORKER -->|"TCP 6379"| REDIS
    API -->|"Kafka listener"| KAFKA
    WORKER -->|"Kafka listener"| KAFKA
```

This graph is useful during architecture reviews because it makes the intended trust model explicit.

If the graph contains:

```text
Every service -> Every service
```

the network architecture may be overly permissive.

---

## Production Review Checklist

### Inbound

- [ ] Every inbound rule has a documented purpose.
- [ ] Public exposure is intentional.
- [ ] Internal services use specific source Security Groups where appropriate.
- [ ] Administrative ports are restricted.
- [ ] Database ports are not Internet-accessible.
- [ ] Redis and Kafka are not unintentionally exposed.

### Outbound

- [ ] Egress requirements are documented.
- [ ] External dependencies are known.
- [ ] AWS service access is understood.
- [ ] Unnecessary unrestricted egress is reviewed.

### Architecture

- [ ] Security Groups map to meaningful trust boundaries.
- [ ] Resources do not depend unnecessarily on the default Security Group.
- [ ] Multiple attached Security Groups are reviewed.
- [ ] Rules are managed through Infrastructure as Code where practical.

### Operations

- [ ] Security Group changes are audited.
- [ ] VPC Flow Logs are available where required.
- [ ] Security findings are monitored.
- [ ] Connectivity troubleshooting procedures are documented.
- [ ] Security Group ownership is known.

---

## Interview Traps

### Are Security Groups stateful?

Yes. Return traffic for an allowed connection is automatically tracked.

### Can Security Groups contain deny rules?

No. Security Groups support allow rules. Traffic that does not match an applicable allow rule is implicitly denied.

### Are Security Groups attached to subnets?

No. They are associated with resources through network interfaces. Network ACLs are associated with subnets.

### What happens when multiple Security Groups are attached?

Their rules are effectively combined. An applicable allow rule from any attached Security Group can permit traffic.

### Should database access use the VPC CIDR?

Not necessarily. When the trust relationship is workload-based, a Security Group reference is generally more precise.

### Are Security Groups enough for application security?

No. They provide network-level access control. Authentication, authorization, TLS, IAM, secrets management, WAF, logging, and other controls remain separate concerns.

### Can a Security Group explicitly deny traffic?

No. If explicit deny semantics are required, another control such as a Network ACL, WAF, routing isolation, or application authorization may be appropriate depending on the layer.

---

## Practical Architecture

A production Django/FastAPI backend might use:

```mermaid
flowchart TB
    INTERNET["Internet"]
    
    subgraph EDGE["Public Edge"]
        WAF["AWS WAF"]
        ALB["Application Load Balancer<br/>ALB SG"]
    end

    subgraph VPC["Production VPC"]
        subgraph APP["Private Application Subnets"]
            API["Django / FastAPI<br/>API SG"]
            WORKER["Celery Workers<br/>Worker SG"]
        end

        subgraph DATA["Private Data Subnets"]
            DB["PostgreSQL<br/>Database SG"]
            REDIS["Redis<br/>Redis SG"]
            KAFKA["Kafka<br/>Kafka SG"]
        end
    end

    INTERNET --> WAF
    WAF --> ALB
    ALB --> API

    API --> DB
    API --> REDIS
    API --> KAFKA

    WORKER --> DB
    WORKER --> REDIS
    WORKER --> KAFKA
```

The Security Group relationships are:

```text
ALB SG
  |
  +--> API SG : 8000

API SG
  |
  +--> Database SG : 5432
  +--> Redis SG : 6379
  +--> Kafka SG : Kafka listener

Worker SG
  |
  +--> Database SG : 5432
  +--> Redis SG : 6379
  +--> Kafka SG : Kafka listener
```

This provides a clean network trust model:

```text
Public
  |
  v
Edge
  |
  v
Application
  |
  +--> Data
  |
  +--> Messaging
```

Each boundary is explicit and independently reviewable.

---

## Key Takeaways

- Security Groups are **stateful, resource-level, allow-only virtual firewalls** and should form the primary network access-control boundary for many VPC workloads.
- Prefer **Security Group references over broad CIDRs** when expressing workload-to-workload trust relationships.
- Multiple attached Security Groups combine their effective allow rules, so the complete set of associated groups must be reviewed when assessing exposure.
- Production Security Groups should follow **least privilege** across source, destination, protocol, port, and egress while avoiding unnecessary operational complexity.
- Security Groups provide network security, not complete application security; **IAM, TLS, authentication, authorization, secrets management, monitoring, and WAF controls remain complementary layers**.