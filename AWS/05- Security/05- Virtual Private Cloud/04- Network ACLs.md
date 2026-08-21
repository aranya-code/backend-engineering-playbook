# 04- Network ACLs

## Overview

A Network Access Control List (NACL) is a subnet-level network traffic filter in Amazon VPC. NACLs control inbound and outbound traffic crossing the boundary of a subnet.

The key distinction from Security Groups is that NACLs are **stateless** and support both **allow and deny** rules.

```text
                    VPC
                     |
          +----------+----------+
          |                     |
     Public Subnet         Private Subnet
          |                     |
      Public NACL          Private NACL
          |                     |
        ALB / EC2          API / DB
```

NACLs are most useful as an additional network security boundary rather than as the primary firewall for individual applications.

A typical production design uses multiple layers:

```text
Internet / Network
        |
        v
   Route Tables
        |
        v
      NACL
        |
        v
 Security Group
        |
        v
 Application
        |
        v
Application Authentication
```

Each layer addresses a different failure or attack mode.

---

## What a Network ACL Is

A Network ACL is a collection of numbered rules associated with one or more VPC subnets.

Each rule specifies characteristics such as:

- Rule number
- Protocol
- Port range
- Source or destination CIDR
- Allow or deny action
- Inbound or outbound direction

For example:

```text
Inbound

Rule   Protocol   Port    Source          Action
100    TCP        443     0.0.0.0/0       ALLOW
200    TCP        22      10.0.0.0/16     ALLOW
300    TCP        443     203.0.113.0/24  DENY
```

NACL rules operate at the subnet boundary. They are therefore broader than Security Group rules.

---

## Why NACLs Exist

Security Groups provide fine-grained controls around workloads and network interfaces. NACLs provide a broader subnet-level boundary.

This distinction is useful when an organization wants to enforce a policy regardless of which individual resources are deployed in a subnet.

For example:

```text
Application Subnet
       |
       +-- API server
       +-- Worker
       +-- Internal service
       +-- Future workload
```

A subnet-level NACL can apply a common network policy to all of them.

Typical use cases include:

- Defense in depth
- Explicit CIDR-based denies
- Subnet-level segmentation
- Blocking known malicious address ranges
- Compliance controls
- Protecting sensitive subnet classes
- Emergency network blocking during incidents

NACLs should generally complement Security Groups rather than replace them.

---

## NACL vs Security Group

| Property | Network ACL | Security Group |
|---|---|---|
| Scope | Subnet | ENI / workload |
| Stateful | No | Yes |
| Allow rules | Yes | Yes |
| Deny rules | Yes | No |
| Rule ordering | Lowest matching rule wins | All applicable rules evaluated |
| Source/destination | CIDR-based | CIDR and supported Security Group references |
| Association | Subnet | Network interface/resource |
| Return traffic | Must be explicitly permitted | Automatically handled |
| Typical purpose | Coarse network boundary | Fine-grained workload access |

A useful mental model is:

```text
NACL
= subnet firewall

Security Group
= workload firewall
```

---

## Stateless Traffic Filtering

NACLs are stateless.

This means the NACL does not remember that an outbound packet created an established connection.

Consider:

```text
Client
10.0.1.10:49152
        |
        | TCP destination port 443
        v
Server
10.0.2.20:443
```

The response is sent back to:

```text
10.0.1.10:49152
```

The return packet must independently satisfy the applicable NACL rules.

Conceptually:

```mermaid
sequenceDiagram
    participant C as Client
    participant CN as Client Subnet NACL
    participant SN as Server Subnet NACL
    participant S as Server

    C->>CN: TCP request
    CN->>SN: Forward packet
    SN->>S: Deliver packet
    S->>SN: TCP response
    SN->>CN: Return packet
    CN->>C: Deliver response
```

This is fundamentally different from a stateful Security Group.

---

## Stateful Security Groups vs Stateless NACLs

Consider:

```text
API -> PostgreSQL:5432
```

A Security Group can allow:

```text
TCP 5432
Source: API Security Group
```

The response traffic is automatically tracked as part of the connection.

With NACLs:

```text
API subnet
    |
    | request
    v
Database subnet
    |
    | response
    v
API subnet
```

both directions must be permitted.

This is why NACL configuration frequently requires explicit consideration of ephemeral ports.

---

## NACL Rule Evaluation

NACL rules are evaluated in ascending numerical order.

Example:

```text
100 DENY  203.0.113.10/32
200 ALLOW 0.0.0.0/0
```

Traffic from `203.0.113.10` matches rule 100 and is denied.

Now consider:

```text
100 ALLOW 0.0.0.0/0
200 DENY  203.0.113.10/32
```

The deny rule is ineffective for that traffic because rule 100 already matches.

The general rule is:

```text
Specific rules
      |
      v
Broad rules
```

Use lower rule numbers for policies that must take precedence.

---

## Rule Numbering Strategy

Avoid consuming rule numbers sequentially without gaps.

Prefer:

```text
100
200
300
400
```

over:

```text
1
2
3
4
```

The gaps make future changes easier.

For example:

```text
100 DENY known malicious CIDR
200 ALLOW internal application traffic
300 ALLOW HTTPS
```

A future rule can be inserted between existing policies without redesigning the complete rule numbering scheme.

---

## Default NACL

Every VPC includes a default NACL.

The default NACL allows all inbound and outbound traffic unless modified.

Conceptually:

```text
Inbound:
ALLOW 0.0.0.0/0

Outbound:
ALLOW 0.0.0.0/0
```

This permissive behavior does not make the VPC resources automatically public.

Internet reachability still depends on other components such as:

- Route tables
- Internet Gateway
- Public IP addressing
- Security Groups
- Application listeners

The default NACL is therefore only one component of the overall network security model.

---

## Custom NACLs

A custom NACL provides an independently managed subnet-level policy.

For example:

```text
Application NACL

Inbound:
ALLOW required internal application traffic
ALLOW required health-check traffic
DENY everything else

Outbound:
ALLOW required response traffic
ALLOW required dependencies
DENY everything else
```

A restrictive custom NACL should be introduced only after the application's traffic matrix is understood.

Otherwise, seemingly harmless rules can break:

- DNS
- HTTPS
- Health checks
- Monitoring
- Package installation
- AWS service access
- Database connections
- Internal APIs

---

## Subnet Association

A subnet is associated with one NACL at a time.

One NACL can be associated with multiple subnets.

```text
NACL-A
  |
  +---- Public Subnet A
  |
  +---- Public Subnet B

NACL-B
  |
  +---- Private Subnet A
  |
  +---- Private Subnet B
```

This is useful when multiple subnets share the same security requirements.

However, it also creates operational coupling.

Changing NACL-A affects every subnet associated with it.

Therefore, do not share a NACL across unrelated subnet roles simply to reduce the number of NACL objects.

---

## Designing NACLs by Subnet Role

A production VPC may separate workloads into:

```text
Internet
   |
   v
Public Subnets
   |
   v
Application Subnets
   |
   v
Database Subnets
```

Each subnet class can have a distinct NACL policy.

| Subnet | NACL Role |
|---|---|
| Public | Control broad public-facing traffic |
| Application | Restrict application subnet traffic |
| Database | Add a subnet-level boundary around data stores |
| Management | Restrict administrative network access |
| Inspection | Protect traffic around network inspection components |

The exact rules should be derived from actual application and infrastructure traffic.

---

## NACL and Routing

Routing and NACL filtering solve different problems.

A route answers:

> Where should this packet go?

A NACL answers:

> Is this traffic allowed to cross the subnet boundary?

For example:

```text
Source
  |
  v
Route Table
  |
  v
NACL
  |
  v
Destination
```

A valid NACL rule cannot create connectivity when no route exists.

Likewise, a valid route does not bypass a NACL deny.

When debugging connectivity, treat routing and filtering as separate control planes.

---

## NACL and Security Group Interaction

For traffic to reach an application, multiple controls may need to permit it.

Example:

```text
Internet
   |
   v
Public Subnet NACL
   |
   v
ALB Security Group
   |
   v
ALB
   |
   v
API Security Group
   |
   v
API
```

A simplified request path is:

```text
Route
  AND
NACL
  AND
Security Group
  AND
Application listener
```

A permissive Security Group does not override a NACL deny.

A permissive NACL does not override a Security Group restriction.

This layered behavior is important when diagnosing connectivity failures.

---

## Ephemeral Ports

Ephemeral ports are temporary client-side ports used for network connections.

Example:

```text
Client
10.0.1.10:49152

Server
10.0.2.20:443
```

The request is:

```text
10.0.1.10:49152
        |
        v
10.0.2.20:443
```

The response is addressed back to:

```text
10.0.1.10:49152
```

Because NACLs are stateless, the relevant return traffic must be permitted.

The required ephemeral port range depends on the clients and operating systems involved.

Do not blindly copy a port range without understanding the traffic pattern.

---

## Example: Public HTTPS Application

Suppose an internet-facing ALB is deployed in a public subnet.

The intended request is:

```text
Internet
   |
   | TCP 443
   v
ALB
```

A simplified inbound NACL policy could allow:

```text
TCP 443
Source: 0.0.0.0/0
Action: ALLOW
```

The corresponding return traffic must also be allowed by the outbound NACL.

The important point is not a specific port template but the traffic model:

```text
Request
  +
Response
```

must both be evaluated.

---

## Example: ALB to API

Suppose an ALB forwards requests to an API running on port `8000`.

```text
ALB Subnet
    |
    | TCP 8000
    v
API Subnet
```

The API Security Group might allow:

```text
TCP 8000
Source: ALB Security Group
```

The API subnet NACL operates at a different level and can allow traffic from the ALB subnet CIDR.

Conceptually:

```text
Security Group:
ALB SG -> API SG

NACL:
ALB subnet CIDR -> API subnet CIDR
```

The two controls should be designed independently.

---

## Example: Application to PostgreSQL

Consider:

```text
Application Subnet
10.20.10.0/24

Database Subnet
10.20.20.0/24
```

The application connects to PostgreSQL:

```text
10.20.10.x
    |
    | TCP 5432
    v
10.20.20.x
```

A database subnet NACL can restrict inbound PostgreSQL traffic to the application CIDR:

```text
TCP 5432
Source: 10.20.10.0/24
Action: ALLOW
```

The database response traffic must also satisfy the corresponding outbound policy.

The DB Security Group should still provide the primary workload-level control.

---

## NACL and NAT Gateway

A common private-subnet architecture is:

```text
Private Application Subnet
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

The application subnet NACL applies to traffic crossing the subnet boundary.

When debugging Internet access from a private subnet, inspect:

- Private subnet route table
- NAT Gateway
- NACL
- Security Group
- DNS
- Destination connectivity

A NAT Gateway does not eliminate the need to correctly configure subnet-level filtering.

---

## NACL and VPC Peering

VPC peering provides private connectivity between VPCs.

Example:

```text
VPC A
10.10.0.0/16
    |
    | VPC Peering
    v
VPC B
10.20.0.0/16
```

The destination subnet NACL must allow the required traffic.

The source subnet's outbound NACL must also permit the request and return path.

Additionally, both VPCs require appropriate routes and Security Group rules.

The full path is therefore:

```text
Source Route
    |
    v
Source NACL
    |
    v
VPC Peering
    |
    v
Destination Route
    |
    v
Destination NACL
    |
    v
Security Group
    |
    v
Application
```

---

## NACL and Transit Gateway

In a centralized AWS network:

```text
VPC A
  |
  v
Transit Gateway
  |
  +---- VPC B
  |
  +---- VPC C
```

NACLs remain subnet-level controls.

They do not replace:

- VPC route tables
- Transit Gateway route tables
- Security Groups
- Network Firewall or other inspection controls

A packet can traverse several independent control planes:

```text
Source Subnet
     |
     v
Source NACL
     |
     v
VPC Route Table
     |
     v
Transit Gateway
     |
     v
Destination VPC Route Table
     |
     v
Destination NACL
     |
     v
Destination ENI
```

This is why centralized network architectures require systematic troubleshooting.

---

## IPv4 and IPv6

NACL policies must account for the IP protocol family.

IPv4:

```text
0.0.0.0/0
```

IPv6:

```text
::/0
```

An IPv4 rule does not automatically provide the equivalent IPv6 policy.

For dual-stack environments, explicitly design and review both.

A common security mistake is securing IPv4 while leaving IPv6 traffic subject to a different or unintended policy.

---

## NACLs and EKS

Amazon EKS environments introduce additional networking layers:

```text
Internet
   |
   v
Load Balancer
   |
   v
EKS Networking
   |
   v
Nodes / Pods
```

NACLs operate at the subnet level rather than at the Kubernetes Service or Pod policy level.

Depending on the EKS networking configuration, restrictive NACLs can affect:

- Pod-to-pod communication
- Node communication
- Load balancer health checks
- DNS
- AWS API access
- Container image retrieval
- Monitoring agents
- Ephemeral return traffic

Use Security Groups and Kubernetes NetworkPolicies for their respective responsibilities rather than trying to encode all application policy into subnet NACLs.

---

## NACLs and Network Inspection

Enterprise networks may include:

- AWS Network Firewall
- Third-party firewalls
- IDS/IPS systems
- Inspection VPCs
- Transit Gateway architectures

A traffic path might look like:

```mermaid
flowchart LR
    APP["Application Subnet"] --> NACL1["Application NACL"]
    NACL1 --> RT1["VPC Route Table"]
    RT1 --> TGW["Transit Gateway"]
    TGW --> FW["Network Inspection"]
    FW --> TGW2["Transit Gateway"]
    TGW2 --> RT2["Destination Route Table"]
    RT2 --> NACL2["Destination NACL"]
    NACL2 --> DB["Destination Subnet"]
```

NACLs are only one layer in this architecture.

When designing such systems, document the complete packet path and the responsibility of each security control.

---

## VPC Flow Logs and NACL Troubleshooting

VPC Flow Logs provide network traffic metadata and are useful when investigating connectivity.

They can help identify:

- Unexpected source addresses
- Unexpected destination addresses
- Rejected traffic
- Incorrect ports
- Network segmentation problems
- Potential scanning
- Security Group or NACL configuration problems

A practical debugging workflow is:

```text
Application failure
       |
       v
Identify source/destination
       |
       v
Check route
       |
       v
Check NACL
       |
       v
Check Security Group
       |
       v
Check Flow Logs
       |
       v
Check application listener
```

Flow Logs are an observability mechanism; they do not themselves permit or deny traffic.

---

## Infrastructure as Code

NACL configuration should generally be managed through Infrastructure as Code.

A Terraform example:

```hcl
resource "aws_network_acl" "application" {
  vpc_id = var.vpc_id

  tags = {
    Name = "prod-application-nacl"
  }
}

resource "aws_network_acl_rule" "application_ingress" {
  network_acl_id = aws_network_acl.application.id

  rule_number = 100
  egress      = false

  protocol    = "tcp"
  rule_action = "allow"

  cidr_block = var.load_balancer_subnet_cidr
  from_port  = 8000
  to_port    = 8000
}

resource "aws_network_acl_rule" "application_egress" {
  network_acl_id = aws_network_acl.application.id

  rule_number = 100
  egress      = true

  protocol    = "-1"
  rule_action = "allow"

  cidr_block = var.vpc_cidr
}
```

The exact policy should be derived from the application's traffic requirements.

Avoid using unrestricted outbound access merely because it is operationally convenient.

---

## Production NACL Design Process

A reliable design process starts with the traffic matrix rather than with individual firewall rules.

### Identify the Source

```text
API subnet
```

### Identify the Destination

```text
Database subnet
```

### Identify the Protocol and Port

```text
TCP 5432
```

### Identify Both Directions

```text
API -> DB:5432
DB -> API:ephemeral
```

### Identify CIDRs

```text
API:
10.20.10.0/24

DB:
10.20.20.0/24
```

### Design NACL Rules

```text
Database inbound:
TCP 5432
Source: 10.20.10.0/24

Database outbound:
Required return traffic
Destination: 10.20.10.0/24
```

### Validate Other Layers

Check:

```text
Route table
NACL
Security Group
Application listener
Application authorization
```

This is significantly safer than repeatedly opening ports until the application starts working.

---

## Common NACL Mistakes

### Treating NACLs as Stateful

Incorrect:

```text
Inbound 443 allowed
=
response automatically allowed
```

NACLs are stateless.

Both directions must be considered.

### Forgetting Ephemeral Ports

Allowing only:

```text
TCP 443
```

may permit the initial direction while blocking the response.

### Incorrect Rule Ordering

Incorrect:

```text
100 ALLOW 0.0.0.0/0
200 DENY  203.0.113.10/32
```

Correct:

```text
100 DENY  203.0.113.10/32
200 ALLOW 0.0.0.0/0
```

### Making NACLs Too Restrictive

Overly restrictive rules can unexpectedly break:

- DNS
- HTTPS
- Monitoring
- Health checks
- Package repositories
- AWS service communication
- Internal APIs
- NAT traffic

### Using NACLs Instead of Security Groups

NACLs and Security Groups have different responsibilities.

A production architecture commonly uses both:

```text
NACL
+
Security Group
```

### Forgetting IPv6

Dual-stack environments require explicit IPv4 and IPv6 security policies.

### Sharing NACLs Across Unrelated Subnets

A shared NACL couples the security policies of its associated subnets.

Separate policies should use separate NACLs when necessary.

---

## Troubleshooting Checklist

When a connection fails, inspect the complete path.

```text
Source
  |
  v
DNS
  |
  v
Route Table
  |
  v
Source NACL
  |
  v
Destination Route
  |
  v
Destination NACL
  |
  v
Security Group
  |
  v
Application
```

Use this checklist:

- [ ] Source address is correct.
- [ ] Destination address is correct.
- [ ] DNS resolves correctly.
- [ ] A valid route exists.
- [ ] Source subnet NACL permits outbound traffic.
- [ ] Destination subnet NACL permits inbound traffic.
- [ ] Destination subnet NACL permits the response path.
- [ ] Source Security Group permits required egress when egress is restricted.
- [ ] Destination Security Group permits required ingress.
- [ ] Application is listening on the expected port.
- [ ] IPv4/IPv6 behavior is intentional.
- [ ] VPC Flow Logs have been inspected when necessary.

---

## Security Considerations

NACLs provide defense in depth but are not a complete application security mechanism.

They can help reduce:

- Unwanted CIDR-based access
- Accidental subnet exposure
- Some lateral movement paths
- Impact from overly permissive workload-level rules

They cannot provide:

- User authentication
- Application authorization
- API authorization
- Database authorization
- TLS encryption
- Service identity

For example:

```text
NACL
  |
  | Network access permitted
  v
PostgreSQL
  |
  | Database authentication
  v
Database User
  |
  | Database authorization
  v
Database Objects
```

Network reachability is not equivalent to application permission.

---

## High Availability

NACLs are associated with subnets, so they naturally participate in multi-AZ architectures.

A production application may use:

```text
                ALB
                 |
        +--------+--------+
        |                 |
       AZ-A              AZ-B
        |                 |
   Public Subnet      Public Subnet
        |                 |
    NACL-A             NACL-A
        |                 |
   Application        Application
```

Equivalent subnet roles should generally have equivalent NACL policies.

When designing multi-AZ systems:

- Keep equivalent subnet policies consistent.
- Test traffic in every Availability Zone.
- Test failover paths.
- Verify health checks across AZs.
- Ensure return traffic works regardless of the selected AZ.
- Avoid rules that accidentally make one AZ behave differently.

A highly available application requires highly available network policy.

---

## Disaster Recovery

NACL configuration should be reproducible in disaster recovery environments.

For example:

```text
Region A
  |
  +-- VPC
  +-- Subnets
  +-- Route Tables
  +-- NACLs
  +-- Security Groups

Region B
  |
  +-- VPC
  +-- Subnets
  +-- Route Tables
  +-- NACLs
  +-- Security Groups
```

Use Infrastructure as Code so that the security model can be recreated consistently.

Do not depend on undocumented manual changes in the production environment.

A DR environment should reproduce the network security policy rather than merely reproduce the compute resources.

---

## Performance and Scalability

NACLs are generally not an application-level performance bottleneck.

The larger concern is operational complexity.

A network path such as:

```text
Application
    |
    v
NACL
    |
    v
Firewall
    |
    v
Transit Gateway
    |
    v
NACL
    |
    v
Database
```

contains multiple independent policy layers.

Each additional layer increases:

- Configuration complexity
- Troubleshooting complexity
- Change-management requirements
- Potential failure points

Senior-level network design balances:

```text
Security
+
Reliability
+
Performance
+
Operational simplicity
```

Do not add network controls simply because they are available. Each control should provide a clear security, compliance, or architectural benefit.

---

## Cost Considerations

NACLs are not normally the major cost driver in VPC architectures.

The larger network costs usually come from surrounding services and traffic patterns, such as:

- NAT Gateways
- Transit Gateways
- Network Firewall
- Cross-AZ traffic
- Cross-region traffic
- Inspection architectures

Therefore, NACL decisions should be evaluated as part of the complete network architecture.

Avoid adding additional network hops solely to simplify NACL configuration.

---

## Production Best Practices

### Keep Rules Minimal

Use the smallest rule set that satisfies the required network policy.

### Prefer Specific Rules Before Broad Rules

For example:

```text
100 DENY known malicious CIDR
200 ALLOW required CIDR
```

### Model Both Directions

Document:

```text
Request path
+
Response path
```

### Avoid Unnecessary Public CIDRs

Do not use:

```text
0.0.0.0/0
```

unless broad public access is genuinely required.

### Use Infrastructure as Code

Manage NACLs through:

- Terraform
- CloudFormation
- CI/CD
- Code review

### Document Ownership

For important rules, record:

- Purpose
- Application
- Environment
- Owner
- Dependency

### Test Changes

Validate changes against:

- Application connectivity
- Load balancer health checks
- DNS
- Monitoring
- Internal APIs
- External APIs
- Database traffic
- NAT traffic

### Monitor Network Behavior

Use VPC Flow Logs and other network observability mechanisms to investigate unexpected traffic.

---

## Interview Traps

### Are NACLs stateful?

No. NACLs are stateless.

### Are Security Groups stateful?

Yes.

### Can NACLs explicitly deny traffic?

Yes.

### Can Security Groups explicitly deny traffic?

No.

### Are NACLs attached directly to EC2 instances?

No. NACLs are associated with subnets.

### Can a subnet have multiple NACLs?

No. A subnet is associated with one NACL at a time.

### Can one NACL protect multiple subnets?

Yes.

### How are NACL rules evaluated?

Numbered rules are evaluated from the lowest rule number upward. The first matching rule determines the action.

### Does a later deny override an earlier allow?

No. If the earlier allow matches, the later deny is not evaluated.

### Do NACLs replace Security Groups?

No. They operate at different network boundaries and are commonly used together.

### Why are ephemeral ports important?

Because NACLs are stateless and return traffic may use client-side ephemeral ports.

### Can NACL rules reference Security Groups?

No. NACLs use network-level addressing such as CIDR blocks.

---

## Practical Mental Model

For network troubleshooting, think in layers:

```text
Can the destination be reached?
        |
        v
Routing

Can traffic cross the subnet boundary?
        |
        v
NACL

Can the workload receive the traffic?
        |
        v
Security Group

Is the service listening?
        |
        v
Application

Is the caller authorized?
        |
        v
Application Authentication / Authorization
```

This prevents the common mistake of treating every connectivity problem as a Security Group problem.

---

## Key Takeaways

- NACLs are **stateless, subnet-level network filters** that support both explicit allow and deny rules.
- NACL rules are evaluated by **ascending rule number**, so specific policies must precede broader matching policies.
- Because NACLs are stateless, production designs must account for **both request and response traffic**, including ephemeral ports.
- Security Groups should normally provide **workload-level controls**, while NACLs provide an additional subnet-level defense-in-depth boundary.
- Treat NACLs as Infrastructure as Code and troubleshoot the complete path across **routing, NACLs, Security Groups, and application behavior**.