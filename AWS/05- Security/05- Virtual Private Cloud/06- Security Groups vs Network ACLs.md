# 06- Security Groups vs Network ACLs

## Overview

AWS VPC security is primarily enforced through multiple network-control layers. Two foundational controls are **Security Groups** and **Network Access Control Lists (NACLs)**.

Both control network traffic, but they operate at different layers of the VPC networking model:

- **Security Groups** are stateful, resource-level virtual firewalls.
- **Network ACLs** are stateless, subnet-level traffic filters.
- Security Groups primarily express **who can communicate with a resource**.
- NACLs primarily express **which traffic can enter or leave a subnet**.

The distinction matters because production VPC designs frequently use both.

A typical backend architecture may look like:

```text
Internet
    |
    v
Application Load Balancer
    |
    v
Application Subnets
    |
    +----> PostgreSQL
    |
    +----> Redis
    |
    +----> Kafka
```

Security Groups can express relationships such as:

```text
ALB Security Group
        |
        | TCP 8000
        v
API Security Group
        |
        | TCP 5432
        v
Database Security Group
```

NACLs provide an additional subnet boundary:

```text
Public Subnet
      |
    NACL
      |
Private Application Subnet
      |
    NACL
      |
Database Subnet
```

A senior-level VPC design does not treat Security Groups and NACLs as interchangeable. It assigns each control a clear responsibility.

---

## Core Difference

The most important distinction is **statefulness**.

| Property | Security Group | Network ACL |
|---|---|---|
| Scope | Network interface/resource | Subnet |
| Stateful | Yes | No |
| Rules | Allow only | Allow and deny |
| Rule evaluation | All applicable rules | Lowest numbered matching rule |
| Direction | Inbound/outbound | Inbound/outbound |
| Return traffic | Automatically handled by state | Must be explicitly permitted |
| Source by Security Group | Supported | Not supported |
| Typical use | Workload-level access control | Subnet-level network boundary |
| Association | Network interfaces | Subnets |
| Primary design goal | Resource isolation | Subnet traffic filtering |

The practical rule is:

> Use Security Groups to define application communication relationships; use NACLs when subnet-level traffic filtering or explicit deny behavior is required.

---

## Security Groups

A Security Group is a stateful virtual firewall associated with supported VPC resources through network interfaces.

For an EC2-based backend:

```text
EC2 Instance
    |
    +-- Network Interface
            |
            +-- Security Group
```

Security Groups commonly define:

```text
Source
Protocol
Port
```

For example:

```text
TCP
Port: 5432
Source: API Security Group
```

This expresses:

> Allow PostgreSQL traffic from resources associated with the API Security Group.

That is generally more robust than hardcoding an application subnet CIDR when the security relationship is between workloads.

---

## Why Security Groups Exist

Security Groups provide resource-oriented network access control.

Suppose a production architecture contains:

```text
ALB
 |
 v
API
 |
 +----> PostgreSQL
 |
 +----> Redis
```

The desired policy is:

```text
ALB SG -> API SG
API SG -> PostgreSQL SG
API SG -> Redis SG
```

This models the architecture directly.

Instead of saying:

```text
Allow 10.20.10.0/24 -> 5432
```

you can express:

```text
Allow API SG -> PostgreSQL SG
```

This is particularly useful when instances, tasks, or pods are dynamically replaced.

---

## Security Group Statefulness

Security Groups are stateful.

Suppose an API connects to PostgreSQL:

```text
API
10.20.10.25:49152
      |
      | TCP
      | destination 5432
      v
PostgreSQL
10.20.20.15:5432
```

If the Security Group rules allow the connection, the response traffic is automatically recognized as part of the established flow:

```text
PostgreSQL
10.20.20.15:5432
      |
      | TCP
      | destination 49152
      v
API
10.20.10.25:49152
```

You do not normally need to create an explicit Security Group rule for every ephemeral return port.

This is one of the most important differences from NACLs.

---

## Security Group Rule Evaluation

Security Groups do not operate like traditional ordered ACLs.

If multiple Security Groups are associated with a network interface, their rules are effectively combined.

For example:

```text
SG-A:
ALLOW TCP 443 from 10.20.0.0/16

SG-B:
ALLOW TCP 22 from 10.30.0.0/16
```

An interface associated with both groups can receive traffic permitted by either applicable rule.

There is no explicit deny rule that overrides an allow rule inside a Security Group.

To remove access, remove the corresponding allow rule or change the architecture.

---

## Network ACLs

A Network ACL is a stateless subnet-level filter.

The relationship is:

```text
VPC
 |
 +-- Subnet A
 |      |
 |      +-- NACL
 |
 +-- Subnet B
        |
        +-- NACL
```

A subnet is associated with one NACL at a time, while one NACL can be associated with multiple subnets.

NACLs evaluate traffic crossing the subnet boundary.

They support:

- Allow rules
- Deny rules
- Inbound rules
- Outbound rules
- Protocol matching
- Port ranges
- CIDR-based source/destination matching

---

## NACL Statelessness

NACLs do not track connection state.

Suppose:

```text
API:49152
    |
    | TCP/5432
    v
DB:5432
```

The request must be allowed.

The response:

```text
DB:5432
    |
    | TCP/49152
    v
API:49152
```

must also be allowed.

Therefore, a restrictive NACL needs rules that account for both directions.

This is where ephemeral ports become important.

---

## NACL Rule Ordering

NACL rules are evaluated in ascending rule-number order.

For example:

```text
100  ALLOW TCP 443 from 10.20.0.0/16
110  DENY  TCP ALL from 10.20.0.0/16
```

Traffic matching rule `100` is allowed before rule `110` can apply.

A rule with a lower number has higher precedence.

A common mistake is to add a broad deny before a specific allow:

```text
100 DENY ALL
200 ALLOW TCP 443
```

The allow rule is never reached for matching traffic because the earlier deny wins.

---

## Default NACL

AWS provides a default NACL for a VPC.

The default NACL allows all inbound and outbound traffic by default.

A custom NACL starts with a more restrictive configuration and can be explicitly associated with subnets.

Production environments should avoid assuming that the default NACL is automatically an adequate security architecture.

Whether a custom NACL is necessary depends on the organization's security model and compliance requirements.

---

## Default Security Group

A VPC also has a default Security Group.

Its behavior is different from the default NACL.

The default Security Group permits communication between resources associated with the same default Security Group, while outbound traffic is allowed by default unless changed.

Do not confuse:

```text
Default NACL
```

with:

```text
Default Security Group
```

They have different semantics and operate at different scopes.

---

## Request Flow Through Both Controls

A simplified inbound request looks like:

```mermaid
flowchart LR
    C["Client"] --> NACL1["Subnet NACL"]
    NACL1 --> SG1["Load Balancer Security Group"]
    SG1 --> ALB["Application Load Balancer"]
    ALB --> NACL2["Application Subnet NACL"]
    NACL2 --> SG2["API Security Group"]
    SG2 --> API["Django / FastAPI"]
```

The exact packet-processing order inside AWS networking should not be interpreted as a literal packet traversal sequence from this conceptual diagram. The important design point is that both subnet-level and resource-level controls can affect whether communication succeeds.

For troubleshooting, think in terms of:

```text
Route
  +
NACL
  +
Security Group
  +
Application
```

rather than assuming that one control replaces another.

---

## Security Group vs NACL Architecture

A production design might use:

```mermaid
flowchart TB
    Internet["Internet"] --> ALB["Application Load Balancer"]

    subgraph Public["Public Subnets"]
        ALBNACL["Public Subnet NACL"]
        ALBSG["ALB Security Group"]
        ALB
    end

    subgraph Private["Private Application Subnets"]
        APINACL["Application Subnet NACL"]
        APISG["API Security Group"]
        API["Django / FastAPI"]
    end

    subgraph Database["Private Database Subnets"]
        DBNACL["Database Subnet NACL"]
        DBSG["Database Security Group"]
        DB["PostgreSQL"]
    end

    ALB --> APINACL
    APINACL --> APISG
    APISG --> API
    API --> DBNACL
    DBNACL --> DBSG
    DBSG --> DB
```

The Security Groups describe workload relationships.

The NACLs provide subnet-level controls around the workload tiers.

---

## When to Use Security Groups

Security Groups are the default choice for most application-level network access control.

Use them for:

- EC2 workloads
- Load balancers
- ECS tasks
- RDS databases
- ElastiCache resources
- Other supported VPC resources

Typical rules include:

```text
ALB SG -> API SG : TCP 8000
API SG -> DB SG  : TCP 5432
API SG -> Redis SG : TCP 6379
```

This model scales well as infrastructure becomes dynamic.

---

## When to Use NACLs

NACLs are useful when you need subnet-level filtering.

Common reasons include:

- Explicit deny rules
- Broad subnet boundary controls
- Additional defense in depth
- Network segmentation requirements
- Compliance requirements
- Blocking known CIDR ranges
- Controlling traffic before it reaches individual workloads

For example:

```text
Database subnet
    |
    +-- NACL
         |
         +-- DENY known malicious CIDR
```

However, adding NACLs purely because they are available can increase operational complexity without providing meaningful additional protection.

---

## Typical Production Pattern

A common architecture is:

```text
Internet
    |
    v
ALB
    |
    | Security Group
    v
API Subnet
    |
    | Security Group
    v
Database
```

With NACLs providing an additional subnet boundary:

```text
Internet
    |
 Public NACL
    |
    v
ALB
    |
 Application NACL
    |
    v
API
    |
 Database NACL
    |
    v
PostgreSQL
```

The Security Groups should normally contain the primary application authorization rules.

The NACLs should remain simple enough to reason about and operate safely.

---

## Security Group Referencing

One of the strongest features of Security Groups is that a rule can reference another Security Group.

For example:

```text
DB Security Group

Inbound:
TCP 5432
Source: API Security Group
```

This means:

```text
Any resource associated with API SG
        |
        | TCP 5432
        v
Any resource associated with DB SG
```

This is more resilient than tying the rule to a fixed instance IP.

When application instances are replaced, autoscaled, or rescheduled, the Security Group relationship remains meaningful.

---

## CIDR-Based Security Group Rules

Security Groups can also use CIDR ranges.

For example:

```text
TCP 443
Source: 10.20.0.0/16
```

This can be appropriate when access is genuinely network-based.

Use CIDRs when the policy is:

> Any host in this trusted network may access this service.

Use Security Group references when the policy is:

> This workload class may access this service.

That distinction improves architecture clarity.

---

## Security Group Chaining

Security Groups can represent a chain of service dependencies.

For example:

```text
ALB SG
  |
  v
API SG
  |
  +----> DB SG
  |
  +----> Redis SG
  |
  +----> Kafka SG
```

Rules might be:

| Destination SG | Protocol | Port | Source SG |
|---|---|---:|---|
| API SG | TCP | 8000 | ALB SG |
| DB SG | TCP | 5432 | API SG |
| Redis SG | TCP | 6379 | API SG |
| Kafka SG | TCP | 9092/9094 as configured | API SG |

This approach maps network authorization to service architecture.

---

## NACLs and Ephemeral Ports

Because NACLs are stateless, return traffic frequently targets an ephemeral port.

For example:

```text
API:
10.20.10.25:49152

DB:
10.20.20.15:5432
```

Request:

```text
49152 -> 5432
```

Response:

```text
5432 -> 49152
```

The corresponding NACL rules must account for the return traffic.

This is a frequent source of connectivity failures when teams introduce restrictive custom NACLs.

---

## Comparison by Traffic Direction

| Scenario | Security Group | NACL |
|---|---|---|
| Allow inbound HTTPS | Yes | Yes |
| Allow outbound HTTPS | Yes | Yes |
| Explicit deny | No | Yes |
| Automatically recognize return traffic | Yes | No |
| Match Security Group source | Yes | No |
| Match CIDR | Yes | Yes |
| Match port range | Yes | Yes |
| Filter at subnet boundary | Indirectly | Yes |
| Require return-path rule | No | Yes |

---

## Security Group vs NACL for Backend Services

Consider:

```text
Django API
    |
    +---- PostgreSQL
    |
    +---- Redis
    |
    +---- Kafka
```

A reasonable Security Group design is:

```text
Django SG
    |
    +---- TCP 5432 -> PostgreSQL SG
    |
    +---- TCP 6379 -> Redis SG
    |
    +---- TCP 9092/9094 -> Kafka SG as configured
```

The application Security Group does not need to explicitly allow each ephemeral return port because the Security Group is stateful.

If NACLs are also restrictive, their rules must account for the return traffic.

---

## Security Implications

Security Groups and NACLs should be treated as complementary controls.

A layered design might look like:

```text
                    Security Boundary
                           |
             +-------------+-------------+
             |                           |
         NACL Layer                 SG Layer
       Subnet controls            Workload controls
             |                           |
             +-------------+-------------+
                           |
                      Application
```

This supports defense in depth.

However, defense in depth is useful only when each layer has a clear purpose.

Do not create dozens of NACL rules simply to duplicate every Security Group rule.

---

## Explicit Deny Use Cases

NACLs are particularly useful when an explicit deny is required.

For example:

```text
100 DENY TCP ALL
    Source: 203.0.113.0/24

200 ALLOW TCP 443
    Source: 0.0.0.0/0
```

The deny rule blocks the specified CIDR before the broader HTTPS allow rule.

This capability is not available in Security Groups.

For more advanced threat detection and centralized traffic inspection, organizations may also use dedicated AWS network security services rather than relying on NACLs for every security requirement.

---

## Operational Complexity

Security Groups generally scale more naturally with dynamic application infrastructure.

Consider an autoscaling service:

```text
API Instance 1
API Instance 2
API Instance 3
...
API Instance N
```

All instances can share:

```text
API Security Group
```

The database can simply permit:

```text
API SG -> DB SG
```

No per-instance IP rule management is required.

NACLs operate at the subnet boundary, so changes affect all resources in the associated subnet.

This makes NACL modifications potentially higher-impact.

---

## High Availability Considerations

Equivalent subnets across Availability Zones should normally have consistent network-control policies.

For example:

```text
AZ-A                    AZ-B

API Subnet A             API Subnet B
    |                         |
 API NACL                 API NACL
    |                         |
 API SG                   API SG
```

Avoid accidental differences such as:

```text
AZ-A NACL:
ALLOW TCP 443

AZ-B NACL:
DENY TCP 443
```

unless the difference is intentional.

Infrastructure as Code is strongly recommended for managing production NACLs and Security Groups.

---

## Infrastructure as Code

Network controls should generally be version-controlled.

A Terraform Security Group example:

```hcl
resource "aws_security_group" "api" {
  name        = "api"
  description = "Security group for API workloads"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Application traffic from ALB"
    protocol        = "tcp"
    from_port       = 8000
    to_port         = 8000
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Outbound application traffic"
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "api"
  }
}
```

The exact egress policy should be tightened according to the application's actual requirements.

For NACLs, define explicit rule numbers and document their purpose.

---

## Practical Security Group Example

Suppose:

```text
ALB
  |
  v
Django API
  |
  v
PostgreSQL
```

A reasonable relationship is:

```text
ALB SG
    |
    | TCP 8000
    v
API SG
    |
    | TCP 5432
    v
DB SG
```

The database should not generally allow:

```text
0.0.0.0/0 -> TCP 5432
```

Instead, it should permit the specific application security boundary.

---

## Practical NACL Example

Suppose a private application subnet needs to communicate with a database subnet.

The conceptual traffic is:

```text
API:ephemeral -> DB:5432
DB:5432 -> API:ephemeral
```

A restrictive NACL must account for:

```text
Inbound request
Outbound request
Inbound response
Outbound response
```

The exact rules should be derived from:

- Actual subnet CIDRs
- Actual ephemeral-port ranges
- Required protocols
- Routing
- NAT or firewall paths
- IPv4/IPv6 requirements

Avoid copying a generic NACL rule set into production without validating the actual traffic matrix.

---

## Troubleshooting Methodology

When traffic fails, inspect the controls systematically.

### Identify Source and Destination

```text
Source:
10.20.10.25

Destination:
10.20.20.15

Protocol:
TCP

Destination port:
5432
```

### Check Routing

Verify that the route tables provide a valid path.

### Check NACL

Inspect:

- Inbound rule
- Outbound rule
- Rule ordering
- CIDR
- Protocol
- Port range
- Return path

### Check Security Group

Inspect:

- Inbound rules
- Outbound rules
- Security Group references
- Associated network interfaces

### Check Application

Verify the destination service is listening:

```bash
ss -lntp
```

### Check Flow Logs

Use VPC Flow Logs to determine whether traffic is being accepted or rejected and to correlate observed ports and addresses.

---

## Common Failure Pattern

An engineer may configure:

```text
API SG:
ALLOW -> DB SG TCP 5432
```

The application still times out.

The Security Group appears correct.

The issue may be:

```text
API subnet NACL
        |
        X
Return traffic blocked
```

The Security Group is stateful, but the NACL is not.

This is why checking only Security Groups is insufficient when restrictive NACLs are present.

---

## Common Mistakes

### Using NACLs Instead of Security Groups

NACLs are not a replacement for resource-level Security Groups.

### Treating NACLs as Stateful

A permitted outbound request does not automatically permit the return traffic.

### Opening Database Ports to the Internet

Avoid:

```text
0.0.0.0/0 -> TCP 5432
```

for production databases unless there is an exceptional, explicitly justified architecture.

### Forgetting NACL Rule Ordering

A lower-numbered deny can override a later allow.

### Overly Complex NACLs

Excessive rules create operational risk.

### Using IP Addresses Everywhere

Security Group references are usually more resilient for workload relationships.

### Assuming Security Group Deny Rules Exist

Security Groups support allow rules; they do not provide explicit deny rules.

### Modifying Production NACLs Without Testing

A NACL change can affect every resource in the associated subnet.

### Ignoring Return Traffic

This is especially dangerous with stateless NACLs and ephemeral ports.

---

## Interview Traps

### Which is stateful?

Security Groups are stateful. NACLs are stateless.

### Which supports explicit deny rules?

NACLs.

### Which operates at subnet level?

NACLs.

### Which is associated with network interfaces?

Security Groups.

### Can a Security Group reference another Security Group?

Yes, where supported by the VPC networking context.

### Can a NACL reference a Security Group?

No. NACL rules use network-level attributes such as CIDRs, protocols, and ports.

### Does a Security Group require explicit ephemeral return-port rules?

No, because it is stateful.

### Does a NACL require return-path rules?

Yes, because it is stateless.

### What happens if multiple Security Groups allow traffic?

The applicable allow rules are effectively combined.

### What happens if a lower-numbered NACL rule matches?

That rule takes precedence over later matching rules.

---

## Security Group and NACL Decision Matrix

| Requirement | Preferred Control | Reason |
|---|---|---|
| API -> PostgreSQL | Security Group | Workload relationship |
| ALB -> API | Security Group | Service-to-service authorization |
| API -> Redis | Security Group | Resource-level control |
| Block a specific CIDR | NACL | Explicit deny capability |
| Subnet-level boundary | NACL | Subnet scope |
| Dynamic autoscaling workloads | Security Group | SG references survive instance replacement |
| Stateful return traffic | Security Group | Connection tracking |
| Broad subnet filtering | NACL | Network boundary |
| Defense in depth | Both | Different control scopes |

---

## Production Best Practices

### Prefer Security Groups for Application Authorization

Design rules around service relationships:

```text
ALB SG -> API SG
API SG -> DB SG
API SG -> Redis SG
```

### Keep NACLs Simple

Use NACLs for clearly defined subnet-level policies rather than duplicating every Security Group rule.

### Minimize CIDR Scope

Prefer:

```text
10.20.10.0/24
```

over:

```text
0.0.0.0/0
```

when the architecture permits it.

### Use Explicit Rule Documentation

Each non-obvious rule should have a meaningful description.

### Manage Through IaC

Use Terraform, CloudFormation, or another controlled deployment mechanism.

### Monitor Changes

Network-policy changes should be auditable and observable.

### Test Before Production

Validate:

- Expected traffic
- Unexpected traffic
- Return traffic
- Cross-AZ communication
- Failure scenarios
- NACL rule ordering

### Design Around Least Privilege

Permit only the protocols, ports, sources, and destinations required by the architecture.

---

## Security Group vs NACL Mental Model

Use this mental model:

```text
Security Group
"What resources are allowed to communicate?"

NACL
"What traffic is allowed across this subnet boundary?"
```

For example:

```text
ALB -> API
```

is primarily a workload relationship.

Use:

```text
ALB SG -> API SG
```

Whereas:

```text
Block this CIDR from entering the application subnet
```

is a subnet-level traffic policy.

Use:

```text
NACL DENY
```

This distinction prevents many production design mistakes.

---

## Key Takeaways

- **Security Groups are stateful, resource-level controls** and should normally be the primary mechanism for expressing application and service-to-service access.
- **NACLs are stateless, subnet-level controls** that support explicit allow and deny rules and require both directions of a flow to be permitted.
- Security Group references are well suited to dynamic architectures such as **Django/FastAPI, ECS, EC2, and microservices**, because workload relationships remain meaningful as instances change.
- NACLs are best used for **clear subnet-level policies, explicit denies, and defense in depth**, not as a duplicate implementation of every Security Group rule.
- Production VPC security should use **least privilege, simple NACLs, precise Security Group relationships, Infrastructure as Code, monitoring, and systematic traffic-flow troubleshooting**.