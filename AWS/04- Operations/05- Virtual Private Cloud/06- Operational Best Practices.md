# 06- Operational Best Practices

## Overview

Amazon VPC is foundational infrastructure for production AWS workloads. Operational quality depends less on creating a VPC than on keeping routing, subnetting, security controls, connectivity, observability, and changes predictable over time.

A production VPC should be designed so that engineers can answer four questions quickly:

- **Where does this traffic go?**
- **Why is this traffic allowed or denied?**
- **What happens if an Availability Zone or dependency fails?**
- **How can the network be changed safely without causing an outage?**

For backend systems such as Django, FastAPI, gRPC services, workers, PostgreSQL, Redis, Kafka, and Kubernetes workloads, VPC operations become increasingly important as the system grows. Poor network operations can produce outages that look like application failures: connection timeouts, DNS failures, unreachable databases, failed deployments, unavailable AWS APIs, or unexpectedly high network costs.

A useful production model is:

```text
VPC Operations
├── Addressing
├── Routing
├── Security
├── Connectivity
├── Availability
├── Observability
├── Cost
├── Change Management
└── Disaster Recovery
```

## Operational Architecture

A production VPC commonly separates public infrastructure from private application and data workloads.

```mermaid
flowchart TB
    Internet["Internet"]

    subgraph VPC["Production VPC"]
        IGW["Internet Gateway"]

        subgraph Public["Public Subnets"]
            ALB["Application Load Balancer"]
            NAT["NAT Gateways"]
        end

        subgraph Private["Private Application Subnets"]
            API["Django / FastAPI / gRPC"]
            Workers["Celery / Background Workers"]
        end

        subgraph Data["Private Data Subnets"]
            DB["PostgreSQL"]
            Redis["Redis"]
            Kafka["Kafka"]
        end

        Endpoints["VPC Endpoints"]
    end

    Internet --> IGW
    IGW --> ALB
    ALB --> API
    API --> Workers
    API --> DB
    API --> Redis
    Workers --> Kafka
    API --> Endpoints
    API --> NAT
    NAT --> IGW
```

The exact architecture varies by workload, but the operational principle is consistent:

> Keep traffic on the most private, shortest, and most observable path that satisfies the application's requirements.

## Addressing Strategy

### Plan CIDR Blocks Before Deployment

VPC CIDR planning becomes difficult to change after dependent systems have been deployed.

Consider:

```text
VPC
10.0.0.0/16

├── Public AZ-A      10.0.0.0/24
├── Public AZ-B      10.0.1.0/24
├── Public AZ-C      10.0.2.0/24
│
├── App AZ-A         10.0.10.0/23
├── App AZ-B         10.0.12.0/23
├── App AZ-C         10.0.14.0/23
│
├── Data AZ-A        10.0.20.0/24
├── Data AZ-B        10.0.21.0/24
└── Data AZ-C        10.0.22.0/24
```

The actual ranges should be determined from:

- Expected workload growth.
- Number of Availability Zones.
- Kubernetes or container networking requirements.
- VPC peering requirements.
- Transit Gateway connectivity.
- On-premises networks.
- Other VPC CIDRs.
- Future acquisitions or multi-account integration.

### Avoid CIDR Overlap

CIDR overlap can prevent or complicate:

- VPC peering.
- Transit Gateway routing.
- VPN connectivity.
- Direct Connect routing.
- Multi-account network integration.

Treat IP address management as an architectural concern rather than a subnetting exercise.

## Route Table Management

Routing is one of the most important operational aspects of a VPC.

A route table determines where packets matching a destination CIDR are sent.

Example:

```text
Destination       Target
-----------       ----------------
10.0.0.0/16       local
0.0.0.0/0         nat-xxxxxxxx
10.20.0.0/16      tgw-xxxxxxxx
```

### Route Table Principles

Prefer:

- Explicit route-table ownership.
- One clear purpose per route table.
- Consistent naming.
- Minimal route entries.
- Infrastructure as Code.
- Controlled route propagation.
- Documented exceptions.

Avoid:

- Large numbers of manually created exceptions.
- Shared route tables with unclear ownership.
- Broad routes added only to make troubleshooting easier.
- Manual production changes without recording the reason.

### Route Specificity

AWS route selection follows the most specific matching route.

For example:

```text
10.0.0.0/16  -> NAT
10.0.20.0/24 -> Database Network
```

Traffic to:

```text
10.0.20.15
```

matches:

```text
10.0.20.0/24
```

rather than:

```text
10.0.0.0/16
```

This matters when troubleshooting unexpected traffic paths.

## Public and Private Subnet Discipline

A subnet is effectively public when its route table provides a path through an Internet Gateway.

A common production convention is:

| Subnet type | Typical workloads | Internet inbound |
|---|---|---|
| Public | Load balancers, NAT Gateways | Potentially |
| Private application | Django, FastAPI, workers, containers | No direct inbound |
| Private data | PostgreSQL, Redis, Kafka | No direct Internet access |

Do not make a subnet public simply because an application needs outbound Internet connectivity.

Use:

```text
Private Subnet
    |
    v
NAT Gateway
    |
    v
Internet Gateway
```

instead of:

```text
Private Application
    |
    v
Public IP
    |
    v
Internet
```

## Security Group Operations

Security Groups should provide the primary workload-level network access control.

Use narrow rules based on:

- Source Security Group.
- Specific CIDR ranges.
- Required ports.
- Required protocols.

For example:

```text
ALB Security Group
    |
    | TCP 443
    v
Application Security Group
    |
    | TCP 5432
    v
PostgreSQL Security Group
```

This is preferable to allowing:

```text
0.0.0.0/0 -> TCP 5432
```

### Security Group Naming

Use names that communicate intent:

```text
sg-production-alb
sg-production-api
sg-production-worker
sg-production-postgres
sg-production-redis
```

Avoid names such as:

```text
sg-test
sg-new
sg-temp
sg-final
```

Operational naming should explain ownership and purpose without requiring external documentation.

## Network ACL Operations

Network ACLs operate at the subnet boundary and are stateless.

Because they are stateless, return traffic must be explicitly permitted.

For example, if a client initiates:

```text
Client: 50000
Server: 443
```

the response uses the client's ephemeral port:

```text
Server: 443
Client: 50000
```

A restrictive Network ACL must allow the relevant return traffic.

For most application architectures, avoid using Network ACLs as the primary mechanism for detailed application authorization.

Use:

```text
Security Groups
    +
Network ACLs where subnet-level controls are justified
```

rather than attempting to reproduce every workload security rule in both layers.

## Ephemeral Port Awareness

Production troubleshooting often fails because engineers remember the destination port but forget the response port.

For example:

```text
Client
Source:      10.0.10.10:49152
Destination: 10.0.20.10:443
```

Response:

```text
Server
Source:      10.0.20.10:443
Destination: 10.0.10.10:49152
```

A restrictive stateless network filter must account for this behavior.

This is especially important when debugging:

- Load balancers.
- NAT traffic.
- External APIs.
- Database connections.
- Kubernetes networking.
- Network ACLs.

## VPC Endpoints

Use VPC endpoints when private connectivity to supported AWS services is appropriate.

Common examples include:

- S3.
- DynamoDB.
- ECR.
- Secrets Manager.
- Systems Manager.
- Other AWS services supporting PrivateLink.

The operational benefits can include:

- Reduced Internet dependency.
- Reduced NAT traffic.
- Better network isolation.
- More predictable routing.
- Potentially lower costs depending on traffic patterns.

However, interface endpoints have their own operational and financial considerations.

Before deploying them at scale, evaluate:

```text
Endpoint count
x
Availability Zones
x
Hourly cost
+
Data processing
```

## DNS Operations

Reliable DNS is critical for modern AWS systems.

Applications frequently depend on DNS for:

- AWS service endpoints.
- Database endpoints.
- Load balancers.
- Service discovery.
- Internal APIs.
- Kubernetes services.
- External SaaS systems.

VPC DNS settings should therefore be treated as infrastructure dependencies.

When diagnosing connectivity issues, distinguish:

```text
DNS resolution failure
        vs
TCP connection failure
        vs
TLS failure
        vs
Application-level failure
```

These are different failure classes.

A useful troubleshooting sequence is:

```text
DNS
 |
 v
Route
 |
 v
Security Group / NACL
 |
 v
TCP
 |
 v
TLS
 |
 v
HTTP / gRPC
 |
 v
Application
```

## NAT Gateway Operations

NAT Gateways are a common operational and cost concern.

For production workloads, evaluate:

- NAT Gateway per-AZ placement.
- Cross-AZ traffic.
- NAT data-processing volume.
- VPC endpoint opportunities.
- Unexpected outbound traffic.
- Failure behavior.

A typical resilient design is:

```text
AZ-A Application -> NAT-A -> Internet
AZ-B Application -> NAT-B -> Internet
AZ-C Application -> NAT-C -> Internet
```

A single NAT Gateway may be acceptable for lower-criticality environments, but the trade-off should be explicit.

## Load Balancer Operations

Application Load Balancers should generally be placed in public subnets when serving public Internet traffic.

Backend workloads can remain private:

```text
Internet
   |
   v
ALB
   |
   v
Private Application
```

Operational considerations include:

- Health-check configuration.
- Target registration.
- Security Group relationships.
- Listener configuration.
- TLS certificates.
- Idle timeouts.
- Access logging.
- Availability Zone coverage.

A failed target should normally be removed from service through health checks rather than requiring manual intervention.

## Database Network Operations

Databases such as PostgreSQL should normally remain private.

A common architecture is:

```text
Internet
   |
   v
ALB
   |
   v
Application
   |
   | TCP 5432
   v
PostgreSQL
```

The PostgreSQL Security Group should allow traffic from the application Security Group rather than from arbitrary CIDRs.

Avoid:

```text
0.0.0.0/0 -> TCP 5432
```

even if authentication is enabled at the database layer.

Network-level restrictions should provide defense in depth.

## Redis Network Operations

Redis should similarly remain private.

Example:

```text
Application SG
      |
      | Redis port
      v
Redis SG
```

Avoid exposing Redis directly to the Internet.

Redis is particularly sensitive because network exposure can become a severe security incident depending on configuration and workload.

## Kafka Network Operations

Kafka deployments require careful network planning because clients maintain connections to brokers and may receive broker-specific addresses.

Consider:

- Broker subnet placement.
- Security Group rules.
- DNS resolution.
- Inter-AZ traffic.
- Client-to-broker connectivity.
- Broker advertised addresses.
- Cross-AZ replication traffic.

For high-volume Kafka workloads, network architecture can have substantial cost implications.

Do not evaluate Kafka networking solely from the perspective of initial client connection.

## Kubernetes Network Operations

Kubernetes introduces additional network layers.

A typical path may look like:

```text
Internet
   |
   v
Load Balancer
   |
   v
Ingress
   |
   v
Service
   |
   v
Pod
   |
   v
Node / ENI
   |
   v
VPC
```

Troubleshooting must therefore determine where connectivity stops.

Useful questions include:

- Can the pod resolve DNS?
- Can the pod reach the service?
- Can the node reach the destination?
- Does the subnet have the required route?
- Does the Security Group allow traffic?
- Is a Network ACL blocking it?
- Is the destination private or public?
- Is traffic crossing AZs?

## VPC Flow Logs

VPC Flow Logs provide network traffic telemetry useful for troubleshooting and security analysis.

They can help answer:

```text
Who communicated?
From where?
To where?
On which port?
Was the traffic accepted or rejected?
How many bytes were transferred?
```

Use Flow Logs when network-level visibility is required.

They are particularly useful for:

- Investigating rejected connections.
- Detecting unexpected traffic.
- Troubleshooting Security Groups and NACLs.
- Investigating NAT traffic.
- Supporting security investigations.

Do not assume Flow Logs are equivalent to packet capture. They provide metadata rather than full packet payloads.

## Monitoring Strategy

Network monitoring should cover infrastructure, traffic, and application behavior.

| Layer | Examples |
|---|---|
| VPC | Flow Logs |
| NAT | Bytes and connection metrics |
| Load Balancer | Request and target metrics |
| EC2/EKS | Network throughput |
| Database | Connections and latency |
| Application | Request latency and errors |
| DNS | Resolution behavior |
| Cost | NAT and data-transfer charges |

A useful operational model is:

```text
Metrics
   +
Logs
   +
Flow Logs
   +
Application Telemetry
   +
Cost Data
```

No single telemetry source provides complete visibility.

## Alerting

Avoid alerting on every network metric.

Alerts should identify conditions that require action.

Useful examples include:

- Unexpected NAT traffic increase.
- Load balancer target failures.
- Large increases in rejected Flow Logs.
- Network connection saturation.
- Unexpected cross-AZ traffic.
- Significant data-transfer cost increases.
- DNS resolution failures.
- Sudden changes in outbound destinations.

Alert thresholds should be based on workload baselines rather than arbitrary values.

## Change Management

Network changes have a larger blast radius than many application changes.

A single route-table change can affect:

- Multiple subnets.
- Multiple applications.
- Database connectivity.
- Internet access.
- AWS service access.
- Monitoring systems.
- Deployment pipelines.

Use a controlled change process:

```mermaid
flowchart LR
    Plan["Plan"]
    Review["Peer Review"]
    Validate["Validate"]
    Deploy["Controlled Deployment"]
    Observe["Observe"]
    Rollback["Rollback"]

    Plan --> Review
    Review --> Validate
    Validate --> Deploy
    Deploy --> Observe
    Observe --> Rollback
```

Rollback should be considered before deployment.

## Infrastructure as Code

Production VPC infrastructure should generally be managed through Infrastructure as Code.

Common choices include:

- Terraform.
- AWS CloudFormation.
- AWS CDK.

Benefits include:

- Version control.
- Peer review.
- Repeatability.
- Environment consistency.
- Auditable changes.
- Easier disaster recovery.

Example Terraform structure:

```text
network/
├── main.tf
├── variables.tf
├── outputs.tf
├── routes.tf
├── subnets.tf
├── security-groups.tf
└── endpoints.tf
```

Avoid making manual console changes to production unless there is a controlled operational reason.

If an emergency console change is necessary:

1. Record the change.
2. Investigate the root cause.
3. Update Infrastructure as Code.
4. Reconcile drift.
5. Review whether the process should be improved.

## CI/CD and VPC Changes

Network infrastructure should participate in the same engineering discipline as application code.

A useful pipeline is:

```text
Pull Request
    |
    v
Lint / Validate
    |
    v
Plan
    |
    v
Peer Review
    |
    v
Apply
    |
    v
Verification
```

For Terraform, a production workflow may include:

```bash
terraform fmt -check
terraform validate
terraform plan
```

The exact CI/CD implementation depends on the infrastructure platform.

Do not automatically apply high-impact networking changes directly from an unreviewed commit.

## Environment Separation

Separate environments where appropriate:

```text
AWS Account / Environment

├── Development
├── Staging
└── Production
```

For larger organizations, separate AWS accounts are often preferable for strong isolation.

Avoid using production VPC resources for development experiments.

This reduces:

- Blast radius.
- Accidental production changes.
- Security exposure.
- Cost attribution ambiguity.

## Tagging Strategy

Use consistent tags for operational visibility.

Example:

```text
Environment = production
Application  = payments-api
Owner        = backend-platform
ManagedBy    = terraform
CostCenter   = engineering
```

Tags help with:

- Cost allocation.
- Ownership.
- Inventory.
- Automation.
- Incident response.

Tagging should be standardized rather than invented separately by each team.

## Cost Operations

Monitor network-specific costs including:

- NAT Gateway.
- Data transfer.
- Cross-AZ traffic.
- VPC endpoints.
- Transit Gateway.
- VPN.
- Direct Connect.
- Load balancers.

A network architecture can be technically correct while still being unnecessarily expensive.

For example:

```text
Application AZ-A
      |
      | Cross-AZ
      v
NAT Gateway AZ-B
      |
      v
Internet
```

may be operationally valid but economically inferior to local egress through:

```text
NAT Gateway AZ-A
```

Cost should therefore be considered during architecture reviews, not only after receiving the AWS bill.

## High Availability

High availability should be designed around failure domains.

For production systems, consider:

- Multiple Availability Zones.
- Independent NAT Gateways where justified.
- Multi-AZ load balancers.
- Multi-AZ databases.
- Redundant connectivity.
- Private routing.
- DNS resilience.
- Independent failure domains.

A common principle is:

> Do not create a single network component whose failure can simultaneously isolate otherwise independent Availability Zones.

## Disaster Recovery

VPC disaster recovery is not only about recreating the VPC.

Recovery should account for:

- CIDR configuration.
- Subnets.
- Route tables.
- Security Groups.
- Network ACLs.
- NAT Gateways.
- VPC endpoints.
- Load balancers.
- DNS.
- Transit Gateway attachments.
- VPN configuration.
- Application dependencies.

Infrastructure as Code significantly improves recovery because the network definition is version controlled.

A recovery exercise should verify that the environment can actually be recreated rather than assuming the code is correct.

## Configuration Drift

Drift occurs when deployed infrastructure differs from its declared configuration.

Examples:

```text
Terraform:
Allow TCP 443

AWS:
Allow TCP 443
Allow TCP 8080
```

The infrastructure is functioning, but the declared state is no longer authoritative.

Drift can create:

- Security vulnerabilities.
- Unexpected routing.
- Deployment failures.
- Inconsistent environments.
- Difficult incident investigations.

Regularly detect and reconcile drift.

## Troubleshooting Workflow

When an application cannot reach a destination, troubleshoot from lower-level dependencies upward.

### DNS

```bash
nslookup example.internal
```

or:

```bash
dig example.internal
```

Determine whether the hostname resolves to the expected address.

### Route

Determine:

```text
Source subnet
    |
    v
Route table
    |
    v
Destination CIDR
    |
    v
Target
```

Confirm that the route exists and is the intended route.

### Security Group

Check:

- Source.
- Destination.
- Protocol.
- Port.
- Direction.

### Network ACL

Check both directions because NACLs are stateless.

### Service

Confirm that the destination service is actually listening.

For example:

```bash
nc -vz database.internal 5432
```

### Application

Only after network connectivity is established should you focus on:

- TLS.
- Authentication.
- HTTP.
- gRPC.
- Application-level authorization.
- Database credentials.

A useful diagnostic sequence is:

```text
DNS
 ↓
Route
 ↓
NACL
 ↓
Security Group
 ↓
TCP
 ↓
TLS
 ↓
Protocol
 ↓
Application
```

## Common Operational Mistakes

### Making Databases Public for Convenience

This usually happens because engineers want to connect from a laptop quickly.

**Better approach:** use controlled access mechanisms such as VPN, bastion alternatives, Systems Manager, private connectivity, or approved administrative paths.

### Using Security Groups as the Only Security Layer

Security Groups are important but should be part of defense in depth.

Use additional controls where appropriate:

- IAM.
- NACLs.
- VPC endpoints.
- Network Firewall.
- WAF.
- Application authorization.
- Encryption.

### Allowing Broad CIDRs

Rules such as:

```text
0.0.0.0/0 -> TCP 5432
```

should generally be avoided.

Prefer workload identity through Security Group references where supported.

### Making Every Subnet Public

A workload needing outbound Internet access does not automatically need a public IP.

Use private subnets with controlled egress.

### Manually Editing Production Routes

Console changes can disappear from Infrastructure as Code and create drift.

Use IaC and controlled deployment processes.

### Ignoring Cross-AZ Traffic

Cross-AZ traffic may affect both performance and cost.

Measure network paths rather than assuming AZ boundaries are irrelevant.

### Overusing Interface Endpoints

VPC endpoints are useful, but creating dozens of endpoints without understanding their cost and usage can increase infrastructure complexity and expense.

### Treating Flow Logs as Full Packet Capture

Flow Logs provide connection metadata, not complete application payload inspection.

Use appropriate packet-level or application-level observability when required.

## Production Review Checklist

### Network Design

- [ ] CIDR ranges are documented.
- [ ] CIDRs do not overlap with required connected networks.
- [ ] Subnets are distributed across Availability Zones.
- [ ] Public and private subnet responsibilities are clear.
- [ ] Route tables have documented ownership.
- [ ] Internet access is intentionally designed.

### Security

- [ ] Databases are private.
- [ ] Redis is private.
- [ ] Kafka is private.
- [ ] Security Groups use least privilege.
- [ ] NACLs are understood and documented where used.
- [ ] Administrative access follows a controlled path.
- [ ] VPC Flow Logs are enabled where required.

### Availability

- [ ] Critical workloads span multiple AZs.
- [ ] Egress architecture has documented failure behavior.
- [ ] Load balancers span required AZs.
- [ ] Critical network dependencies have redundancy.

### Observability

- [ ] Flow Logs are available where required.
- [ ] NAT metrics are monitored.
- [ ] Load balancer metrics are monitored.
- [ ] Network-related alerts have actionable thresholds.
- [ ] DNS failures can be diagnosed.
- [ ] Cost anomalies are monitored.

### Operations

- [ ] VPC resources are managed with IaC.
- [ ] Changes are peer reviewed.
- [ ] Drift is detected.
- [ ] Production changes have rollback plans.
- [ ] Tags identify ownership and environment.
- [ ] Network documentation matches deployed infrastructure.

### Cost

- [ ] NAT traffic is monitored.
- [ ] Cross-AZ traffic is evaluated.
- [ ] VPC endpoint economics are reviewed.
- [ ] Unused network resources are removed.
- [ ] Data-transfer costs are included in architecture reviews.

## Interview Traps

### Is a subnet public because it has a public IP range?

No. Public/private classification is primarily determined by routing, specifically whether the subnet has a route to an Internet Gateway.

### Are Security Groups stateful?

Yes. Return traffic for an allowed connection is automatically permitted.

### Are Network ACLs stateful?

No. They are stateless, so inbound and outbound traffic must be considered independently.

### Why can an application have a public load balancer while remaining private?

The load balancer can be public while forwarding traffic to private application targets.

```text
Internet
   |
   v
Public ALB
   |
   v
Private Application
```

### Does a private subnet have Internet access?

It can have outbound Internet access through a NAT Gateway without accepting unsolicited inbound Internet connections.

### Why use multiple NAT Gateways?

Primarily for Availability Zone isolation and to avoid unnecessary cross-AZ dependency and traffic.

### Is a NAT Gateway a firewall?

No. NAT provides address translation and outbound connectivity. Security Groups, NACLs, AWS Network Firewall, WAF, and application-level controls solve different security problems.

## Key Takeaways

- **Treat VPC infrastructure as production software**: use IaC, version control, peer review, validation, controlled deployment, and drift detection.
- **Design around failure domains**: distribute critical workloads and network dependencies across Availability Zones according to availability requirements.
- **Troubleshoot from the network outward**: validate DNS, routes, NACLs, Security Groups, TCP, TLS, and protocol behavior before assuming an application defect.
- **Optimize for least privilege and predictable traffic paths**: keep data services private, minimize broad rules, and prefer private connectivity where appropriate.
- **Operate with telemetry and cost awareness**: Flow Logs, service metrics, application observability, and network cost data together provide the visibility required for reliable VPC operations.