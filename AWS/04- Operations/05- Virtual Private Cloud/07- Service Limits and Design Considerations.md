# 07- Service Limits and Design Considerations

## Overview

Amazon VPC quotas are hard constraints or configurable service limits that define how much network infrastructure an AWS account or Region can consume. They affect the number of VPCs, subnets, routes, Security Groups, network interfaces, NAT Gateways, endpoints, and other networking resources that can exist or be attached.

These limits matter because network architecture often scales indirectly. A microservices platform may start with a few services and eventually create hundreds or thousands of network interfaces, Security Group rules, routes, endpoints, and subnets. An architecture that works at small scale can therefore fail operationally when it approaches a quota.

The important engineering principle is:

> Treat AWS quotas as architectural constraints, not administrative details.

A quota can influence:

- VPC topology.
- CIDR planning.
- Subnet sizing.
- Multi-account architecture.
- Multi-Region architecture.
- Kubernetes capacity.
- Microservice isolation.
- Route-table design.
- Security Group design.
- VPC endpoint architecture.
- NAT Gateway architecture.
- Network automation.
- Disaster recovery.

AWS documents VPC quotas per Region unless otherwise specified, and many quotas are adjustable. The applied quota for a specific account can differ from the documented default, so production planning should use the account's actual Service Quotas values rather than assuming the default. :contentReference[oaicite:0]{index=0}

## Quotas vs Design Constraints

Not every constraint should be treated the same way.

| Type | Meaning | Engineering response |
|---|---|---|
| Adjustable quota | Can generally be increased through Service Quotas | Request increase before capacity is needed |
| Fixed quota | Cannot normally be increased | Design around it |
| Per-Region quota | Applies independently in each Region | Include Region in capacity planning |
| Per-resource quota | Applies to an individual VPC, route table, SG, etc. | Distribute or redesign resources |
| Account-level quota | Shared across resources in an account | Include all workloads in capacity planning |
| Performance-related quota | Increase may have performance implications | Test before increasing |

A quota increase is not automatically an architectural solution.

For example, increasing the number of routes in a route table may allow a system to deploy, but hundreds of additional routes can increase operational complexity and may have network-performance implications. AWS explicitly notes that increasing some VPC quotas can affect network performance. :contentReference[oaicite:1]{index=1}

## Important VPC Quotas

The following are representative AWS VPC quota defaults documented currently. Always verify the applied quota for the target account and Region before making capacity decisions.

| Resource | Default quota | Adjustable | Important consideration |
|---|---:|---|---|
| VPCs per Region | 5 | Yes | Increase also affects Internet Gateway quota |
| Subnets per VPC | 200 | Yes | Important for large multi-AZ designs |
| IPv4 CIDR blocks per VPC | 5 | Yes, up to 50 | Primary and secondary CIDRs count |
| IPv6 CIDR blocks per VPC | 5 | Yes | Plan address expansion |
| NAT Gateways per AZ | 5 | Yes | Pending, active, and deleting gateways count |
| Route tables per VPC | 200 | Yes | Main route table counts |
| Non-propagated routes per route table | 500 | Yes, up to 1,000 | Performance implications at higher limits |
| Propagated routes per route table | 100 | No | Consider summarization/default routes |
| Network ACLs per VPC | 200 | Yes | One NACL can serve multiple subnets |
| NACL rules per direction | 20 | Yes, up to 40 | Increasing can affect performance |
| Network interfaces per Region | 5,000 | Yes | Enforced per AZ; capacity can become critical |
| Security Groups per Region | 2,500 | Yes | Large platforms need lifecycle management |
| Rules per Security Group, per direction | 60 | Yes | Separate IPv4/IPv6 accounting applies |
| Security Groups per network interface | 5 | Yes, up to 16 | Combined rule capacity is constrained |
| Gateway VPC endpoints per Region | 20 | Yes | Endpoint strategy matters at scale |

These values are documented by AWS and can change; use the AWS VPC quotas documentation and Service Quotas for current values. :contentReference[oaicite:2]{index=2}

## Why Quotas Become Architectural Problems

Quotas usually become visible through indirect scaling.

Consider a Kubernetes platform:

```text
Microservices
     |
     v
Pods
     |
     v
Network Interfaces / IP Addresses
     |
     v
Subnets
     |
     v
VPC Address Capacity
```

The application team may think:

> "We need 2,000 more pods."

The network architecture must instead ask:

```text
How many IP addresses?
How many ENIs?
Which subnets?
Which Availability Zones?
Which Security Groups?
How many rules?
How much route-table capacity?
How much NAT traffic?
How many endpoints?
```

The network therefore needs capacity planning based on the infrastructure generated by the application.

## VPC Capacity Planning

Before deploying a large production platform, estimate:

```text
VPC count
+
CIDR capacity
+
Subnet count
+
IP address capacity
+
Network interface capacity
+
Security Group capacity
+
Security Group rule capacity
+
Route capacity
+
NAT capacity
+
Endpoint capacity
```

A simple capacity model might look like:

```text
Required ENIs
=
EC2 ENIs
+
Load Balancer ENIs
+
EKS-related ENIs
+
Lambda ENIs
+
RDS ENIs
+
Interface Endpoint ENIs
+
Other managed-service ENIs
```

The exact resource behavior depends on the AWS service and networking mode.

## CIDR Planning

CIDR capacity is one of the hardest constraints to repair after deployment.

AWS allows secondary IPv4 CIDR blocks to be associated with a VPC, but the blocks must satisfy AWS addressing and routing constraints. Existing VPC CIDR blocks cannot simply be resized in place. :contentReference[oaicite:3]{index=3}

For example:

```text
VPC
10.0.0.0/16

Application
10.0.0.0/18

Data
10.0.64.0/20

Public
10.0.80.0/20
```

Do not allocate every available address simply because it is currently unused.

Instead, reserve address space for:

- Future subnets.
- Additional Availability Zones.
- Kubernetes workloads.
- Private endpoints.
- Network appliances.
- Future services.
- VPC expansion.

### CIDR Overlap

CIDR overlap becomes particularly dangerous when introducing:

- VPC Peering.
- Transit Gateway.
- Site-to-Site VPN.
- Direct Connect.
- Multi-account networking.
- Hybrid cloud.
- Acquired company networks.

A VPC that is isolated today may need to communicate with another network tomorrow.

Therefore:

> CIDR planning should consider the organization's entire network estate, not only the current VPC.

## Subnet Capacity

The subnet quota is only one part of subnet capacity.

The more important question is often:

> Does the subnet contain enough usable IP addresses for the workload?

For example:

```text
VPC CIDR
10.0.0.0/16

        |
        +-- AZ-A
        |    +-- Public
        |    +-- Application
        |    +-- Data
        |
        +-- AZ-B
        |    +-- Public
        |    +-- Application
        |    +-- Data
        |
        +-- AZ-C
             +-- Public
             +-- Application
             +-- Data
```

A small subnet can become an availability problem before the VPC reaches its subnet quota.

Monitor:

- Available IP addresses.
- IP allocation rate.
- Peak workload capacity.
- Deployment spikes.
- Autoscaling behavior.
- Managed-service IP consumption.

## Network Address Usage

AWS provides Network Address Usage information for evaluating how network resources consume VPC address capacity.

This is especially relevant for high-density environments such as:

- Amazon EKS.
- Large EC2 fleets.
- Load balancers.
- NAT Gateways.
- VPC endpoints.
- Lambda networking.
- Transit Gateway attachments.

Network Address Usage can help identify address pressure before an application experiences deployment failures. :contentReference[oaicite:4]{index=4}

## Route Table Limits

Route tables are a common scaling constraint in complex network architectures.

AWS currently documents a default of 500 non-propagated routes per route table, adjustable up to 1,000, while propagated routes have a separate quota of 100. AWS also notes that higher route counts can affect network performance. :contentReference[oaicite:5]{index=5}

A route table with hundreds of individual network prefixes is often a design signal.

For example:

```text
10.1.0.0/16
10.2.0.0/16
10.3.0.0/16
...
10.250.0.0/16
```

may indicate that the architecture is carrying too many individual routes.

Possible design alternatives include:

- Route summarization.
- Transit Gateway.
- Default routes.
- Prefix lists.
- Better CIDR allocation.
- Hierarchical network architecture.

### Longest Prefix Matching

AWS selects the most specific matching route.

For example:

```text
10.0.0.0/8       -> Transit Gateway
10.20.0.0/16     -> VPC Peering
10.20.10.0/24    -> Network Interface
```

Traffic to:

```text
10.20.10.15
```

matches:

```text
10.20.10.0/24
```

This becomes important when troubleshooting route conflicts.

## Security Group Scaling

Security Groups can become difficult to manage before the numerical quota is reached.

AWS currently documents:

```text
60 inbound rules
60 outbound rules
```

as the default per Security Group, with separate IPv4 and IPv6 accounting. A network interface can have five Security Groups by default, adjustable up to 16, while the combination of rules and Security Groups per interface is constrained by an overall limit. :contentReference[oaicite:6]{index=6}

The architectural mistake is often:

```text
One Security Group
    |
    +-- Service A
    +-- Service B
    +-- Service C
    +-- Service D
    +-- Service E
    +-- ...
```

This produces large rule sets and unclear ownership.

Prefer grouping resources by:

- Application role.
- Security boundary.
- Traffic pattern.
- Lifecycle.

For example:

```text
ALB SG
   |
   v
API SG
   |
   +----> PostgreSQL SG
   |
   +----> Redis SG
```

## Security Group Rule Explosion

Microservices can generate large numbers of relationships.

A naive model might produce:

```text
Service A -> B
Service A -> C
Service A -> D

Service B -> C
Service B -> D
Service B -> E

Service C -> D
Service C -> E
...
```

As the number of services increases, the number of relationships can grow rapidly.

Avoid modeling every service as an independent network island unless the security requirements justify it.

Use:

- Security Group references.
- Shared security boundaries.
- Service discovery.
- Application-layer authorization.
- IAM.
- API gateways or load balancers where appropriate.

Network security should not become a substitute for application architecture.

## Prefix Lists

Customer-managed prefix lists can simplify repeated network references.

Instead of maintaining:

```text
CIDR A
CIDR B
CIDR C
CIDR D
```

across many resources, a prefix list can represent a controlled collection of network prefixes.

This can improve:

- Centralized management.
- Consistency.
- Change management.
- Security Group configuration.
- Route-table management.

However, prefix-list entries can count toward resource quotas based on the prefix list's maximum size, so they should not be treated as free quota abstraction. AWS documents a default maximum of 1,000 entries per customer-managed prefix list and explains how references consume resource quota. :contentReference[oaicite:7]{index=7}

## Network ACL Limits

Network ACLs have relatively small default rule quotas.

AWS currently documents:

```text
20 inbound rules
20 outbound rules
```

with increases available up to 40 per direction, with potential network-performance implications. :contentReference[oaicite:8]{index=8}

This reinforces an important design principle:

> Do not attempt to implement a complete microservice authorization matrix using NACLs.

NACLs are subnet-level, stateless controls.

Security Groups are generally more appropriate for workload-level access control.

## NAT Gateway Capacity Planning

NAT Gateway architecture involves both quotas and cost.

AWS currently documents a default of five NAT Gateways per Availability Zone. NAT Gateways in `pending`, `active`, or `deleting` states count against the quota. :contentReference[oaicite:9]{index=9}

For a production architecture:

```text
AZ-A
Application -> NAT-A

AZ-B
Application -> NAT-B

AZ-C
Application -> NAT-C
```

This provides better AZ isolation than routing every private subnet through a NAT Gateway in a different AZ.

At large scale, evaluate:

```text
NAT Gateway count
+
NAT throughput requirements
+
Cross-AZ data transfer
+
NAT data processing
+
VPC endpoint opportunities
```

## Network Interface Limits

Network interfaces are easy to underestimate because many AWS managed services create them automatically.

AWS currently documents a default regional ENI quota of 5,000, with the quota enforced per Availability Zone. :contentReference[oaicite:10]{index=10}

Potential ENI consumers include:

- EC2.
- EKS.
- Load balancers.
- Lambda.
- VPC interface endpoints.
- RDS.
- Network appliances.
- Other managed services.

A deployment can therefore consume network capacity without engineers explicitly creating ENIs.

Monitor ENI growth in high-density environments.

## VPC Endpoint Scaling

VPC endpoints reduce dependence on public Internet paths and can be valuable for private workloads.

However, endpoint architecture introduces additional resources and costs.

Consider:

```text
Service count
x
AWS services accessed
x
Availability Zones
x
Endpoint type
```

Interface endpoints create network interfaces and therefore participate in network-capacity planning.

Gateway endpoints have different architectural characteristics and are available for supported services such as Amazon S3 and DynamoDB.

Do not create endpoints automatically for every AWS service without understanding traffic patterns and operational requirements.

## Multi-VPC Architecture

A common early-stage architecture is:

```text
One Account
    |
    +-- One VPC
```

A larger organization may evolve toward:

```text
AWS Organization
|
+-- Network Account
|     |
|     +-- Transit Gateway
|
+-- Production Account
|     |
|     +-- Production VPC
|
+-- Staging Account
|     |
|     +-- Staging VPC
|
+-- Development Account
      |
      +-- Development VPC
```

This provides stronger isolation but introduces additional network components and quotas.

The decision should consider:

- Security boundaries.
- Team ownership.
- Compliance.
- Blast radius.
- Cost.
- Routing complexity.
- Operational maturity.

Do not create one VPC per microservice merely because microservices are independently deployable.

## Transit Gateway Considerations

Transit Gateway is useful when many VPCs and networks need centralized connectivity.

Without centralized routing:

```text
VPC-A <-> VPC-B
VPC-A <-> VPC-C
VPC-A <-> VPC-D
VPC-B <-> VPC-C
...
```

The connectivity model becomes difficult to manage.

A hub-and-spoke model can simplify this:

```text
             VPC-A
               |
               |
VPC-B ---- Transit Gateway ---- VPC-C
               |
               |
             VPC-D
```

The trade-off is that centralized networking introduces another critical infrastructure layer.

Capacity planning should therefore include:

- Attachments.
- Route tables.
- Routes.
- Throughput.
- Cross-AZ traffic.
- Inter-Region connectivity.
- Operational ownership.

## Shared VPC Considerations

AWS VPC sharing allows subnets to be shared across AWS accounts.

This can provide centralized network ownership while allowing application teams to deploy resources.

However, shared VPCs introduce ownership and quota considerations.

AWS documents a default of 100 participant accounts per VPC and 100 subnets that can be shared with an account. :contentReference[oaicite:11]{index=11}

A shared VPC architecture should explicitly define:

```text
Network ownership
Application ownership
Security ownership
Route ownership
Endpoint ownership
Incident responsibility
Quota responsibility
```

Without clear ownership, troubleshooting becomes difficult.

## Multi-Account Quota Planning

AWS Organizations can isolate workloads across accounts.

This can also distribute certain account-level quotas.

For example:

```text
Production Account
    |
    +-- Production VPCs

Analytics Account
    |
    +-- Analytics VPCs

Development Account
    |
    +-- Development VPCs
```

This is often preferable to forcing every workload into one account.

However, account separation does not eliminate network design constraints. Cross-account connectivity introduces additional routing and security considerations.

## Service Quota Management

Use AWS Service Quotas rather than maintaining a spreadsheet of assumed limits.

The Service Quotas service provides the ability to view default and applied quota values and request increases for supported quotas. :contentReference[oaicite:12]{index=12}

A production process should include:

```text
Architecture
    |
    v
Capacity Estimate
    |
    v
Quota Check
    |
    v
Quota Increase Request
    |
    v
Deployment
```

Do this before a major launch rather than after deployment starts failing.

## CLI Inspection

The AWS CLI can be used to inspect resources and quotas.

For example:

```bash
aws service-quotas list-service-quotas \
  --service-code vpc \
  --region us-east-1
```

To retrieve a specific quota:

```bash
aws service-quotas get-service-quota \
  --service-code vpc \
  --quota-code <quota-code> \
  --region us-east-1
```

Resource inspection can also be performed through the VPC API.

For example:

```bash
aws ec2 describe-vpcs \
  --region us-east-1
```

```bash
aws ec2 describe-subnets \
  --region us-east-1
```

```bash
aws ec2 describe-route-tables \
  --region us-east-1
```

```bash
aws ec2 describe-security-groups \
  --region us-east-1
```

The actual quota code should be obtained from Service Quotas rather than hard-coded from memory.

## Quota Monitoring

A production environment should monitor quota utilization for resources that can become deployment blockers.

Useful candidates include:

- VPCs.
- Subnets.
- Network interfaces.
- Routes.
- Security Groups.
- Security Group rules.
- NAT Gateways.
- Elastic IP addresses.
- VPC endpoints.
- Network addresses.

A practical policy is to alert before capacity becomes critical.

For example:

```text
< 70%   Normal
70-80%   Review
80-90%   Capacity planning
> 90%    Immediate action
```

These thresholds are operational policies, not AWS defaults. Choose thresholds based on deployment lead time and workload growth.

AWS Trusted Advisor service-limit checks use 80% as a yellow threshold and 100% as red, illustrating the value of monitoring before hard exhaustion. :contentReference[oaicite:13]{index=13}

## Capacity Planning for CI/CD

Infrastructure pipelines can temporarily consume quotas.

For example:

```text
Terraform Apply
    |
    +-- Create new NAT Gateway
    +-- Create new ENIs
    +-- Create new route tables
    +-- Create new endpoints
    +-- Create new Security Groups
```

A replacement deployment may temporarily create old and new resources at the same time.

Therefore:

> Plan for peak resource consumption during deployment, not only steady-state consumption.

This is particularly important for blue/green deployments and large infrastructure changes.

## Quotas and Disaster Recovery

Disaster recovery environments can fail because the recovery Region does not have enough quota.

Consider:

```text
Primary Region
    |
    +-- Production VPC
    +-- 3 AZs
    +-- 300 ENIs
    +-- 100 routes
```

versus:

```text
DR Region
    |
    +-- Small baseline
    +-- Insufficient quotas
```

If the DR environment must scale rapidly, preconfigure:

- Required quota increases.
- CIDR allocations.
- Subnets.
- Route tables.
- Security Groups.
- NAT architecture.
- Endpoint requirements.
- Service-specific quotas.

A disaster recovery plan should therefore include quota readiness.

## Quotas and High Availability

Quotas can become hidden single points of failure.

For example, if an Availability Zone reaches a network-interface quota:

```text
AZ-A
ENI capacity exhausted
       |
       v
New workload cannot launch
```

Even if:

```text
AZ-B
AZ-C
```

still have capacity, the scheduler or service may not automatically solve the problem.

Monitor capacity by Availability Zone when quotas are AZ-scoped.

## Quotas and Kubernetes

Kubernetes environments deserve special attention because network resource consumption can grow with workload density.

Consider:

```text
Pods
 |
 +-- IP addresses
 |
 +-- ENIs
 |
 +-- Security Groups
 |
 +-- Load balancers
 |
 +-- Subnets
```

Before scaling an EKS cluster, evaluate:

- Available subnet IPs.
- ENI capacity.
- Pod density.
- Load balancer growth.
- Security Group rules.
- NAT traffic.
- Endpoint capacity.

A Kubernetes autoscaler should not be allowed to scale blindly into a network quota.

## Quotas and Lambda

Lambda functions configured for VPC access can consume network resources.

A system with many VPC-connected functions should therefore account for:

```text
Functions
    |
    v
Network Interfaces / IP usage
    |
    v
Subnet capacity
```

This matters particularly when a large number of functions are deployed concurrently.

## Quotas and Load Balancers

Load balancers and their associated network interfaces consume network resources.

A platform with many independently deployed services may eventually create a large number of:

- ALBs.
- NLBs.
- Target groups.
- Listener resources.
- Network interfaces.
- Security Group rules.

Do not automatically create one Internet-facing load balancer per microservice.

Where appropriate, consider:

```text
Internet
    |
    v
Shared ALB
    |
    +-- /users   -> Users Service
    +-- /orders  -> Orders Service
    +-- /billing -> Billing Service
```

versus:

```text
Internet
 |
 +-- ALB Users
 +-- ALB Orders
 +-- ALB Billing
 +-- ALB ...
```

The correct architecture depends on security, ownership, isolation, traffic, and availability requirements.

## Quotas and Network Automation

Automation should fail safely when quotas are near exhaustion.

A deployment system can perform preflight checks:

```text
Terraform Plan
      |
      v
Quota Check
      |
      +---- Capacity OK ----> Apply
      |
      +---- Capacity Low ---> Block / Review
```

This is preferable to discovering a quota problem halfway through deployment.

For critical environments, consider maintaining a capacity inventory containing:

```text
Resource
Current usage
Applied quota
Utilization %
Growth rate
Expected launch demand
Required headroom
```

## Production Design Principles

### Leave Headroom

Do not design production infrastructure to operate at 95% of a quota.

Growth, failover, deployments, and temporary resources can create short-term spikes.

### Design for Peak Usage

Calculate capacity for:

- Normal traffic.
- Peak traffic.
- Autoscaling.
- Deployment overlap.
- Failure recovery.
- Disaster recovery.

### Prefer Horizontal Distribution

Where architecture permits, distribute resources across:

- Availability Zones.
- Accounts.
- VPCs.
- Regions.

Do this only when the operational model justifies the additional complexity.

### Reduce Resource Churn

Frequent creation and deletion of network resources can create operational instability and temporarily consume quotas.

Prefer stable infrastructure with controlled changes.

### Automate Quota Checks

Quota inspection should be part of production readiness and large-scale deployment processes.

### Document Exceptions

If an architecture depends on a quota increase, document:

```text
Quota
Current value
Required value
Reason
Expected growth
Owner
Region
Review date
```

## Common Mistakes

### Assuming AWS Defaults Are Universal

Quota values can differ by service, Region, account state, and applied quota.

**Better approach:** inspect the actual Service Quotas configuration for the target account and Region.

### Requesting a Quota Increase During an Incident

A quota increase may require review and may not be immediate.

**Better approach:** request increases before planned growth or major launches.

### Solving Every Problem by Increasing the Quota

A higher quota does not fix poor architecture.

For example:

```text
500 routes
   |
   v
Request 1,000 routes
```

may be less appropriate than redesigning the routing model.

### Ignoring Temporary Resources

Blue/green deployments can temporarily double resources.

**Better approach:** calculate deployment-time peak usage.

### Ignoring Availability Zone Scope

Some quotas are regional while others are effectively constrained per Availability Zone.

**Better approach:** inspect the quota definition and measure capacity at the relevant scope.

### Treating CIDR Capacity as Easily Expandable

Secondary CIDR blocks exist, but CIDR changes have routing and connectivity constraints.

**Better approach:** plan address space before deployment.

### Creating Excessive Security Groups

More Security Groups do not automatically provide better security.

AWS recommends creating the minimum number of Security Groups needed and using each for resources with similar functions and security requirements. :contentReference[oaicite:14]{index=14}

### Building One Giant Route Table

A huge route table can become difficult to reason about and may approach route quotas.

**Better approach:** design routing domains deliberately.

## Interview Traps

### Are AWS service quotas the same in every Region?

Not necessarily. Many VPC quotas are documented per Region, and the applied quota must be checked for the target Region and account.

### Can all VPC quotas be increased?

No. Some are adjustable and some are fixed.

### Is increasing a quota always safe?

No. Some quota increases can introduce performance or operational implications.

### What happens when a quota is exhausted?

The resource operation generally fails. Existing resources do not automatically disappear to make room for the new resource.

### Why should quotas be considered during architecture design?

Because resource limits can determine whether an architecture can scale, deploy, recover, or fail over successfully.

### Why can a VPC run out of capacity even when the subnet quota is not exhausted?

Because IP addresses, network interfaces, routes, Security Groups, or other resources can reach their own limits independently.

### Why should DR Regions have quota planning?

Because a DR environment may need to create a large number of resources during an incident. A quota shortage in the recovery Region can prevent recovery even when the infrastructure definition is correct.

## Production Readiness Checklist

### Addressing

- [ ] VPC CIDRs are documented.
- [ ] CIDRs do not overlap with required connected networks.
- [ ] Secondary CIDR strategy is defined.
- [ ] Subnets have sufficient IP capacity.
- [ ] Future Availability Zones are considered.
- [ ] Kubernetes or other high-density workloads have address headroom.

### Routing

- [ ] Route-table count is monitored.
- [ ] Route count per table is monitored.
- [ ] Routing domains are clearly defined.
- [ ] Route summarization is considered where appropriate.
- [ ] Transit Gateway requirements are documented.
- [ ] Route growth is included in capacity planning.

### Security

- [ ] Security Group count is monitored.
- [ ] Security Group rules are monitored.
- [ ] Security Group relationships are intentionally designed.
- [ ] NACL rule counts remain manageable.
- [ ] Prefix-list usage is understood.
- [ ] Network security does not rely on unnecessarily large rule sets.

### Network Interfaces

- [ ] ENI utilization is monitored.
- [ ] Capacity is evaluated per Availability Zone where applicable.
- [ ] EKS and Lambda networking requirements are included.
- [ ] Interface endpoint growth is included.
- [ ] Load balancer growth is included.

### NAT and Endpoints

- [ ] NAT Gateway quotas are known.
- [ ] NAT architecture is distributed appropriately.
- [ ] NAT traffic is monitored.
- [ ] Cross-AZ traffic is evaluated.
- [ ] VPC endpoint requirements are documented.
- [ ] Endpoint growth is included in capacity planning.

### Operations

- [ ] Service Quotas are checked before major deployments.
- [ ] Required quota increases are requested in advance.
- [ ] Quota utilization is monitored.
- [ ] Deployment-time peak resource usage is understood.
- [ ] DR Region quotas are validated.
- [ ] Capacity ownership is documented.

## Key Takeaways

- **AWS quotas are architectural constraints**: design VPCs with quota capacity, growth, deployment spikes, and failure recovery in mind.
- **Plan capacity across multiple dimensions**: CIDRs, subnet IPs, ENIs, routes, Security Groups, NAT Gateways, endpoints, and Availability Zones can each become independent bottlenecks.
- **Do not treat quota increases as the default solution**: excessive routes, rules, or resources may indicate an architecture that should be simplified instead.
- **Automate quota awareness**: inspect actual Service Quotas, monitor utilization, request increases before launches, and include quota checks in infrastructure operations.
- **Include quotas in DR and scaling design**: a system cannot reliably scale or recover if the target account or Region lacks sufficient network capacity.