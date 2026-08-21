# 03- Security Group Rules and Chaining

## Overview

Security Group rules define the network-level trust boundaries between AWS workloads. In production VPC architectures, the most useful pattern is not simply opening ports between CIDR ranges, but **chaining Security Groups according to application dependencies**.

A typical backend system can model traffic as:

```text
Internet
   |
   | TCP 443
   v
ALB SG
   |
   | TCP 8000
   v
API SG
   |
   +---- TCP 5432 ----> PostgreSQL SG
   |
   +---- TCP 6379 ----> Redis SG
   |
   +---- Kafka --------> Kafka SG
```

The important idea is that a Security Group rule can use another Security Group as its source or destination. This allows the security model to follow **workload identity and architecture**, rather than depending on changing private IP addresses.

For senior-level VPC design, Security Group chaining should be understood as a form of **network-level dependency modeling**:

```text
ALB SG
  |
  v
API SG
  |
  +----> Database SG
  |
  +----> Redis SG
  |
  +----> Messaging SG
```

Each arrow represents an explicitly permitted network relationship.

---

## Security Group Rules

A Security Group rule defines an allowed traffic path using attributes such as:

- Protocol
- Port or port range
- Source for inbound rules
- Destination for outbound rules
- Security Group reference
- CIDR range
- Prefix list where supported

For example:

```text
Protocol: TCP
Port: 5432
Source: API SG
```

means that resources associated with the API Security Group are allowed to establish PostgreSQL connections to resources protected by the destination Security Group.

A rule should therefore answer three questions:

```text
Who can communicate?
        +
What protocol?
        +
Which destination port?
```

For production systems, avoid designing rules around "whatever happens to work." Every rule should correspond to an intentional application dependency.

---

## Rule Evaluation Model

Security Groups are **stateful** and support allow rules rather than explicit deny rules.

If a packet matches an applicable inbound allow rule, the connection can proceed subject to the rest of the network path and the destination application.

When multiple Security Groups are attached to a resource, their effective allow rules are combined.

For example:

```text
Resource
 |
 +-- SG-A
 |    +-- TCP 443 from 10.0.0.0/16
 |
 +-- SG-B
      +-- TCP 22 from 0.0.0.0/0
```

The resource can receive:

```text
TCP 443 from 10.0.0.0/16
TCP 22  from anywhere
```

There is no later deny rule that can override the SSH rule.

This makes Security Group composition an important part of security review.

---

## Inbound and Outbound Chaining

Security Group chaining can be viewed from both sides of a connection.

Suppose:

```text
API SG
   |
   | TCP 5432
   v
DB SG
```

The database Security Group can contain:

```text
Inbound:
TCP 5432
Source: API SG
```

The API Security Group may have an outbound policy that permits the required database traffic.

Conceptually:

```text
API
 |
 | outbound
 v
API SG
 |
 | network path
 v
DB SG
 |
 | inbound TCP 5432
 v
PostgreSQL
```

Because Security Groups are stateful, response traffic for an allowed connection is tracked automatically.

---

## Why Security Group Chaining Matters

CIDR-based rules express network location:

```text
10.20.0.0/16
```

Security Group references express workload relationships:

```text
API SG
```

The second is usually more useful when designing service-oriented architectures.

Consider an API deployed across multiple Availability Zones:

```text
AZ-A                  AZ-B

API-1                  API-2
10.20.1.10             10.20.2.10
   \                     /
    \                   /
     +---- DB SG ------+
```

If the database trusts:

```text
API SG
```

new API instances can be added without modifying the database rule for every new private IP.

The trust relationship is therefore decoupled from instance addressing.

---

## Security Group References

A Security Group reference can be used when the traffic relationship is based on AWS resources associated with the referenced Security Group.

For example:

```text
Database SG

Inbound:
TCP 5432
Source:
API SG
```

This represents:

```text
API workload
     |
     | PostgreSQL
     v
Database workload
```

rather than:

```text
Anything in 10.20.0.0/16
     |
     | PostgreSQL
     v
Database
```

This distinction becomes increasingly important as infrastructure grows.

---

## CIDR Rules vs Security Group Rules

| Design | Meaning | Typical use |
|---|---|---|
| `0.0.0.0/0` | Any IPv4 source | Public endpoints |
| VPC CIDR | Any resource in the CIDR | Broad network trust |
| Subnet CIDR | Resources in a subnet range | Network-based boundaries |
| Security Group reference | Resources associated with the SG | Workload-based trust |
| Prefix list | Managed network destinations | Shared AWS/network services |

A strong default is:

> Use the narrowest source representation that accurately expresses the intended trust boundary.

If the requirement is "only the API service," use the API Security Group.

If the requirement is genuinely "this entire trusted network range," a CIDR may be appropriate.

---

## Basic Security Group Chain

A standard three-tier backend architecture can use:

```text
                         Internet
                            |
                         TCP 443
                            |
                            v
                    +---------------+
                    |     ALB       |
                    |    ALB SG     |
                    +-------+-------+
                            |
                         TCP 8000
                            |
                            v
                    +---------------+
                    | Django/FastAPI|
                    |    API SG     |
                    +-------+-------+
                            |
                         TCP 5432
                            |
                            v
                    +---------------+
                    |  PostgreSQL   |
                    |     DB SG     |
                    +---------------+
```

Rules:

```text
ALB SG
  Inbound:
    TCP 443 from 0.0.0.0/0

API SG
  Inbound:
    TCP 8000 from ALB SG

DB SG
  Inbound:
    TCP 5432 from API SG
```

This creates a one-directional trust model:

```text
Internet
   |
   v
ALB
   |
   v
API
   |
   v
Database
```

The database does not need to trust the Internet or the entire VPC.

---

## Multi-Service Chaining

Real backend platforms usually have more dependencies.

For example:

```mermaid
flowchart LR
    INTERNET["Internet"] --> ALB["ALB SG"]
    ALB --> API["API SG"]

    API --> DB["PostgreSQL SG"]
    API --> REDIS["Redis SG"]
    API --> KAFKA["Kafka SG"]

    WORKER["Celery Worker SG"] --> DB
    WORKER --> REDIS
    WORKER --> KAFKA
```

The resulting trust relationships are:

| Source SG | Destination SG | Protocol/Port | Purpose |
|---|---|---|---|
| Internet | ALB SG | TCP 443 | Public HTTPS |
| ALB SG | API SG | TCP 8000 | API traffic |
| API SG | DB SG | TCP 5432 | PostgreSQL |
| API SG | Redis SG | TCP 6379 | Redis |
| API SG | Kafka SG | Kafka listener | Event publishing/consuming |
| Worker SG | DB SG | TCP 5432 | Database access |
| Worker SG | Redis SG | TCP 6379 | Celery broker/cache |
| Worker SG | Kafka SG | Kafka listener | Event processing |

This model scales better than using one large "production SG."

---

## Three-Tier Security Group Chaining

The classic three-tier architecture is:

```text
Presentation Tier
        |
        v
Application Tier
        |
        v
Data Tier
```

Mapped to Security Groups:

```text
ALB SG
  |
  v
Application SG
  |
  v
Database SG
```

The rules become:

```text
ALB SG
  -> Application SG

Application SG
  -> Database SG
```

The database does not trust the ALB directly.

This distinction matters because the database should trust the component that actually requires database access.

---

## Chaining with Redis

Suppose a FastAPI application uses Redis for:

- Caching
- Rate limiting
- Session storage
- Celery
- Distributed locks

The architecture may be:

```text
API SG
   |
   | TCP 6379
   v
Redis SG
```

Redis SG:

```text
Inbound:
TCP 6379
Source: API SG
```

If Celery workers also require Redis:

```text
Worker SG
   |
   | TCP 6379
   v
Redis SG
```

The Redis Security Group can therefore contain:

```text
TCP 6379 from API SG
TCP 6379 from Worker SG
```

This is preferable to:

```text
TCP 6379 from VPC CIDR
```

when only the API and workers require Redis.

---

## Chaining with PostgreSQL

A typical architecture:

```text
Django API
    |
    | 5432
    v
PostgreSQL
```

Security Groups:

```text
API SG
     |
     | TCP 5432
     v
DB SG
```

Database rule:

```text
Inbound:
TCP 5432
Source: API SG
```

If background workers access the database:

```text
              +--> API SG
              |
DB SG <-------+
              |
              +--> Worker SG
```

The DB Security Group can allow:

```text
TCP 5432 from API SG
TCP 5432 from Worker SG
```

Do not automatically add the entire application subnet CIDR when only two workload roles need database access.

---

## Chaining with Kafka

Kafka introduces additional complexity because clients and brokers may communicate using one or more configured listeners.

At a conceptual level:

```text
API SG
   |
   | Kafka listener
   v
Kafka SG
```

and:

```text
Worker SG
   |
   | Kafka listener
   v
Kafka SG
```

The Security Group must allow the actual listener ports used by the Kafka deployment.

Security Groups alone do not provide:

- Kafka authentication
- Topic authorization
- Encryption
- Producer/consumer identity

Those should be handled through Kafka's security configuration and appropriate AWS networking controls.

---

## Chaining with gRPC

Suppose:

```text
Order Service
       |
       | TCP 50051
       v
Payment Service
```

Security Groups can represent:

```text
Payment SG

Inbound:
TCP 50051
Source: Order SG
```

This means the network layer allows:

```text
Order workload
      |
      v
Payment workload
```

The gRPC layer can then enforce:

- TLS
- Service identity
- Authentication
- Authorization
- Request-level permissions

Security Group chaining should therefore be viewed as **network authorization**, not complete service authorization.

---

## Service-to-Service Microservice Chaining

Consider:

```text
API
 |
 +--> User Service
 |
 +--> Order Service
 |
 +--> Payment Service
 |
 +--> Notification Service
```

A naive Security Group design might allow:

```text
VPC CIDR -> every service
```

A more controlled design can model actual dependencies:

```mermaid
flowchart LR
    API["API SG"] --> USER["User SG"]
    API --> ORDER["Order SG"]
    ORDER --> PAYMENT["Payment SG"]
    ORDER --> NOTIFY["Notification SG"]
```

The rules express the service graph.

For example:

```text
User SG:
TCP 50051 from API SG

Order SG:
TCP 50052 from API SG

Payment SG:
TCP 50053 from Order SG

Notification SG:
TCP 50054 from Order SG
```

This reduces accidental lateral connectivity.

---

## Security Group Chaining as a Trust Graph

A useful senior-level abstraction is to treat Security Groups as nodes in a graph.

```text
Node = Security Group
Edge = Allowed network dependency
```

Example:

```text
ALB SG
  |
  v
API SG
  |
  +------> DB SG
  |
  +------> Redis SG
  |
  +------> Kafka SG

Worker SG
  |
  +------> DB SG
  |
  +------> Redis SG
  |
  +------> Kafka SG
```

This graph can be reviewed independently of the underlying IP addresses.

A security review can then ask:

- Why does API SG need access to DB SG?
- Why does Worker SG need access to Kafka SG?
- Why does Service A need access to Service B?
- Is any edge unnecessary?
- Are there unexpected bidirectional dependencies?
- Are any broad CIDRs hiding unintended edges?

This is a useful architecture-review technique.

---

## Avoiding Bidirectional Trust

Consider:

```text
API SG <----> DB SG
```

If both directions are broadly allowed, the architecture may be more permissive than required.

Most application dependencies are directional:

```text
API
 |
 v
Database
```

The database normally does not initiate connections back to the API.

Security design should therefore reflect the actual connection direction.

Stateful return traffic does not require you to model the response as a separate application-level dependency.

---

## Security Group Chaining and Stateful Return Traffic

Suppose:

```text
API
 |
 | SYN -> TCP 5432
 v
Database
```

The database responds:

```text
Database
 |
 | SYN/ACK
 v
API
```

Because the Security Group is stateful, the return traffic is automatically tracked as part of the established connection.

You do not normally need to create a separate rule simply to permit the response packet.

This is an important interview and troubleshooting concept.

---

## Nested or Recursive Trust

Security Group references should not be interpreted as recursive permission inheritance.

Suppose:

```text
API SG
   |
   v
DB SG
```

and:

```text
DB SG
   |
   v
Audit SG
```

This does not mean:

```text
API SG -> Audit SG
```

automatically.

Security Group references describe the specific traffic relationship defined by the rule. They do not create arbitrary transitive trust.

A useful mental model is:

```text
A -> B
B -> C

does not imply:

A -> C
```

This prevents Security Group references from becoming an accidental form of transitive authorization.

---

## Cross-Security-Group Design

When workloads have different responsibilities, separate their Security Groups.

For example:

```text
ALB SG
API SG
Worker SG
Admin SG
Database SG
Redis SG
Kafka SG
```

Avoid:

```text
Production SG
```

containing every workload.

A single shared Security Group can make it difficult to determine:

- Who can access the database?
- Which workloads can receive SSH?
- Which services can communicate?
- Which application owns a rule?
- Which rule can be safely removed?

Role-oriented Security Groups make those questions easier to answer.

---

## Shared Security Groups

There are legitimate cases for sharing a Security Group.

For example, multiple API instances with the same security policy may use:

```text
API SG
```

This is desirable when the workloads genuinely share the same trust boundary.

However, sharing should not become a shortcut for unrelated services.

Use:

```text
API-1 + API-2 + API-3 -> API SG
```

when they have equivalent network exposure.

Avoid:

```text
API + Worker + Admin + Database -> Shared SG
```

when these workloads have materially different security requirements.

---

## Security Group Chaining Across Availability Zones

Security Group references work well with multi-AZ architectures.

For example:

```text
AZ-A                         AZ-B

API-1                        API-2
  |                            |
  +-----------+----------------+
              |
            API SG
              |
              v
            DB SG
              |
              v
       PostgreSQL Multi-AZ
```

The database trusts the workload role, not a specific Availability Zone.

This makes scaling and failover easier.

When API instances move between AZs, the Security Group relationship remains unchanged.

---

## Security Group Chaining Across Accounts

Cross-account architectures require additional consideration.

A common architecture is:

```text
Account A
API SG
   |
   | Cross-account connectivity
   v
Account B
Database SG
```

Whether a Security Group reference can be used depends on the supported AWS networking relationship and configuration.

For architectures involving:

- VPC peering
- Transit Gateway
- Shared VPC
- AWS RAM
- Multiple AWS accounts

validate the exact cross-account Security Group reference capabilities for the chosen architecture.

Do not assume that a Security Group reference behaves identically across every VPC connectivity model.

---

## Rule Direction

A common mistake is confusing:

```text
Source
```

and:

```text
Destination
```

For an inbound database rule:

```text
DB SG

Inbound:
TCP 5432
Source: API SG
```

The source is the client.

The destination is the resource protected by the DB SG.

Conceptually:

```text
API SG
   |
   | source
   v
DB SG
   |
   | destination
   v
PostgreSQL
```

For an outbound rule:

```text
API SG

Outbound:
TCP 5432
Destination: DB network
```

The API is the connection initiator.

---

## Least-Privilege Rule Design

A production rule should be as specific as practical.

A useful model is:

```text
Least privilege =
minimum source
+
minimum destination
+
minimum protocol
+
minimum port
+
minimum required direction
```

For example:

```text
TCP 5432
Source: API SG
Destination: Database SG
```

is significantly more precise than:

```text
All traffic
Source: VPC CIDR
Destination: VPC CIDR
```

The more precise rule is easier to audit and less likely to enable lateral movement.

---

## Common Mistakes

### Using `0.0.0.0/0` for Internal Services

Avoid:

```text
Redis:
TCP 6379 from 0.0.0.0/0
```

or:

```text
PostgreSQL:
TCP 5432 from 0.0.0.0/0
```

Public exposure of internal services is rarely justified.

### Using the Entire VPC CIDR

This:

```text
10.0.0.0/16
```

may include many unrelated workloads.

If only the API requires access, use:

```text
API SG
```

where appropriate.

### Creating One Security Group for Everything

This destroys meaningful workload boundaries.

Instead:

```text
ALB SG
API SG
Worker SG
DB SG
Redis SG
```

### Forgetting Egress

A correctly configured destination inbound rule does not automatically mean the source workload's egress policy permits the connection.

When egress is restricted, verify both sides.

### Assuming SG References Are Recursive

If:

```text
A -> B
B -> C
```

do not assume:

```text
A -> C
```

### Assuming Security Groups Provide Application Authorization

A Security Group can control:

```text
TCP connectivity
```

It cannot determine:

```text
whether user X can perform operation Y
```

### Adding Rules Until Connectivity Works

This creates security drift.

A better process is:

```text
Understand dependency
        |
        v
Identify source
        |
        v
Identify destination
        |
        v
Identify protocol/port
        |
        v
Add narrow rule
        |
        v
Test
        |
        v
Document
```

---

## Troubleshooting a Chained Rule

Suppose:

```text
API SG
   |
   | TCP 5432
   v
DB SG
```

but the API cannot connect.

Check:

```text
API
 |
 +-- DNS resolution
 |
 +-- Route table
 |
 +-- Network ACL
 |
 +-- API SG egress
 |
 +-- DB SG ingress
 |
 +-- Database listener
 |
 +-- Database authentication
```

A useful troubleshooting table:

| Layer | Question |
|---|---|
| DNS | Does the hostname resolve to the expected address? |
| Routing | Is there a route to the destination? |
| Egress | Can the source initiate the connection? |
| Ingress | Does the destination allow the source SG? |
| NACL | Is subnet-level traffic permitted? |
| Service | Is PostgreSQL actually listening on `5432`? |
| Authentication | Are credentials and database permissions valid? |

Do not assume every connection failure is a Security Group problem.

---

## AWS CLI Inspection

List Security Groups:

```bash
aws ec2 describe-security-groups \
  --query 'SecurityGroups[].{ID:GroupId,Name:GroupName,VPC:VpcId}'
```

Inspect a Security Group:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0
```

Inspect only inbound rules:

```bash
aws ec2 describe-security-group-rules \
  --filters Name=group-id,Values=sg-0123456789abcdef0
```

A useful operational workflow is:

```text
Resource
   |
   v
Find ENI
   |
   v
Find attached Security Groups
   |
   v
Inspect inbound/outbound rules
   |
   v
Trace source/destination relationship
```

---

## Infrastructure as Code

Security Group chaining should ideally be represented explicitly in Infrastructure as Code.

Terraform example:

```hcl
resource "aws_security_group" "api" {
  name        = "prod-api-sg"
  description = "API workload security group"
  vpc_id      = var.vpc_id
}

resource "aws_security_group" "database" {
  name        = "prod-database-sg"
  description = "PostgreSQL workload security group"
  vpc_id      = var.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "database_from_api" {
  security_group_id            = aws_security_group.database.id
  referenced_security_group_id = aws_security_group.api.id

  ip_protocol = "tcp"
  from_port   = 5432
  to_port     = 5432
  description = "PostgreSQL access from API workloads"
}
```

This is preferable to embedding application subnet CIDRs directly when the trust relationship is workload-based.

The resulting infrastructure code documents the architecture:

```text
database_from_api
```

is much more informative than:

```text
allow_5432_from_10_20_0_0_16
```

---

## Production Architecture

A mature backend platform can model its network dependencies as:

```mermaid
flowchart TB
    INTERNET["Internet"]

    subgraph EDGE["Edge"]
        ALB["Application Load Balancer<br/>ALB SG"]
    end

    subgraph APP["Application Tier"]
        API["Django / FastAPI<br/>API SG"]
        WORKER["Celery Worker<br/>Worker SG"]
    end

    subgraph DATA["Data Tier"]
        DB["PostgreSQL<br/>DB SG"]
        REDIS["Redis<br/>Redis SG"]
        KAFKA["Kafka<br/>Kafka SG"]
    end

    INTERNET -->|"443"| ALB
    ALB -->|"8000"| API

    API -->|"5432"| DB
    API -->|"6379"| REDIS
    API -->|"Kafka listener"| KAFKA

    WORKER -->|"5432"| DB
    WORKER -->|"6379"| REDIS
    WORKER -->|"Kafka listener"| KAFKA
```

This creates a clear trust graph:

```text
Internet
   |
   v
ALB
   |
   v
API
   |
   +----> PostgreSQL
   |
   +----> Redis
   |
   +----> Kafka

Celery Worker
   |
   +----> PostgreSQL
   |
   +----> Redis
   |
   +----> Kafka
```

The important design property is not the number of Security Groups.

It is that each relationship represents an actual architectural dependency.

---

## Security Review Checklist

### Rule Design

- [ ] Every rule has a documented purpose.
- [ ] Source and destination are intentional.
- [ ] Protocol and ports are minimized.
- [ ] Public exposure is deliberate.
- [ ] Internal services use Security Group references where appropriate.
- [ ] Broad VPC CIDR rules have a justified reason.

### Chaining

- [ ] ALB trusts only intended public traffic.
- [ ] Application workloads trust only intended upstream components.
- [ ] Database access is restricted to workloads that require it.
- [ ] Redis access is restricted to required clients.
- [ ] Kafka access is restricted to required producers and consumers.
- [ ] Service-to-service dependencies are explicit.

### Operations

- [ ] Rules are managed through Infrastructure as Code.
- [ ] Security Group ownership is documented.
- [ ] Changes are reviewed through CI/CD where practical.
- [ ] VPC Flow Logs are available where required.
- [ ] Unexpected connectivity is investigated across the complete network path.

---

## Interview Traps

### Does `A SG -> B SG` automatically mean B can initiate connections to A?

No. The rule represents the specific permitted traffic relationship. Security Groups are stateful for return traffic, but statefulness does not create arbitrary bidirectional application trust.

### If A can access B and B can access C, can A access C?

No.

```text
A -> B
B -> C
```

does not imply:

```text
A -> C
```

### Why are Security Group references preferable to IP addresses?

They express workload identity and remain stable as instances are replaced or scaled.

### Are Security Group rules evaluated top-to-bottom?

No. Security Groups do not behave like ordered allow/deny firewall rule lists. Applicable allow rules are combined.

### Can a Security Group explicitly deny another Security Group?

No. Security Groups support allow rules only.

### Does a Security Group replace application authentication?

No. It controls network connectivity. Application authentication and authorization remain separate security layers.

### Does a Security Group reference work identically in every AWS networking architecture?

No. Cross-VPC and cross-account behavior depends on the specific connectivity mechanism and AWS-supported configuration. Validate the capabilities of the chosen architecture.

---

## Key Takeaways

- Security Group chaining models **workload-to-workload trust relationships** and is generally more precise than broad CIDR-based access.
- A well-designed rule identifies the **source, destination, protocol, port, and required direction** with the least privilege necessary.
- Security Group references are not recursively transitive: `A → B` and `B → C` does not imply `A → C`.
- Production architectures should use separate Security Groups for meaningful trust boundaries such as ALBs, APIs, workers, databases, Redis, and Kafka.
- Treat Security Group rules as an **architecture dependency graph** and manage them through Infrastructure as Code so security changes remain reviewable, reproducible, and auditable.