# 03- Route Table and Routing Issues

## Overview

Route tables determine where network traffic is sent from a subnet or other VPC networking component. When VPC connectivity fails, routing is one of the first layers to inspect because a correct Security Group configuration cannot compensate for an incorrect or missing route.

A useful mental model is:

```text
Source ENI
    |
    v
Source Subnet
    |
    v
Associated Route Table
    |
    v
Longest Matching Route
    |
    v
Route Target
    |
    v
Destination
```

For production systems, routing problems commonly appear as:

- Application timeouts.
- Private workloads unable to reach the internet.
- Cross-VPC connectivity failures.
- On-premises connectivity failures.
- Load balancer targets becoming unreachable.
- AWS service access failing from private subnets.
- Traffic unexpectedly traversing a NAT Gateway.
- Traffic being sent to a Transit Gateway, peering connection, or middlebox unexpectedly.
- Asymmetric routing.

Routing should therefore be treated as an explicit architectural dependency rather than an implementation detail.

## What a Route Table Does

A VPC route table contains destination CIDR blocks and targets.

A simplified route table might look like:

| Destination | Target | Purpose |
|---|---|---|
| `10.0.0.0/16` | `local` | VPC-internal traffic |
| `0.0.0.0/0` | NAT Gateway | Private subnet outbound internet |
| `10.1.0.0/16` | Transit Gateway | Other VPC/network |
| `10.2.0.0/16` | VPC Peering | Peered VPC |
| `10.3.0.0/16` | VPN/Virtual Private Gateway | On-premises network |

The route table does not itself provide permission to communicate. It only determines the forwarding path.

The complete path also depends on:

- Security Groups.
- Network ACLs.
- Gateways.
- Network interfaces.
- Destination routing.
- Return routing.
- Application listeners.

## Route Table Association

A route table applies to subnets through associations.

```text
VPC
 |
 +--> Route Table A
 |       |
 |       +--> Subnet A
 |       +--> Subnet B
 |
 +--> Route Table B
         |
         +--> Subnet C
         +--> Subnet D
```

A subnet can have one route table association at a time.

If a subnet does not have an explicit association, it uses the VPC's main route table.

This distinction is important during troubleshooting.

An engineer might inspect a route table named:

```text
private-app-route-table
```

and see the expected NAT Gateway route, while the affected subnet is actually using the main route table.

Always verify the association instead of relying on naming conventions.

## Inspecting Route Tables

List route tables for a VPC:

```bash
aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values=vpc-0123456789abcdef0
```

A more focused query can expose associations and routes:

```bash
aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values=vpc-0123456789abcdef0 \
  --query 'RouteTables[].{
    RouteTableId:RouteTableId,
    Main:Associations[?Main==`true`].Main,
    Associations:Associations[].SubnetId,
    Routes:Routes[].{Destination:DestinationCidrBlock,Target:GatewayId}
  }'
```

For production troubleshooting, record:

- Route table ID.
- Subnet association.
- Main-table status.
- Destination.
- Target.
- Route state.
- Relevant prefix length.

## How AWS Selects a Route

When multiple routes match a destination, the most specific route wins.

For example:

```text
10.0.0.0/16   -> local
10.0.20.0/24  -> tgw-xxxxxxxx
0.0.0.0/0     -> nat-xxxxxxxx
```

Traffic destined for:

```text
10.0.20.50
```

matches all three routes conceptually, but:

```text
10.0.20.0/24
```

is more specific than:

```text
10.0.0.0/16
```

so the `/24` route is selected.

This is known as longest-prefix matching.

### Why This Matters

A route that appears to be more important because it was added later does not necessarily win.

Routing decisions are based on destination specificity, not the visual order of routes in the console.

## Route Matching Example

Consider:

```text
Destination              Target
-----------------------------------------------
10.0.0.0/16              local
10.0.10.0/24             tgw-123456789
10.0.10.128/25           eni-123456789
0.0.0.0/0                nat-123456789
```

For:

```text
10.0.10.150
```

the selected route is:

```text
10.0.10.128/25 -> eni-123456789
```

For:

```text
10.0.10.50
```

the selected route is:

```text
10.0.10.0/24 -> tgw-123456789
```

For:

```text
10.0.30.10
```

the selected route is:

```text
10.0.0.0/16 -> local
```

For:

```text
8.8.8.8
```

the selected route is:

```text
0.0.0.0/0 -> nat-123456789
```

## The Local Route

Every VPC route table contains a route representing the VPC's CIDR.

For:

```text
VPC: 10.0.0.0/16
```

the route is conceptually:

```text
10.0.0.0/16 -> local
```

This allows resources within the VPC CIDR to communicate through the VPC networking layer, subject to the applicable security controls.

A common mistake is assuming that all traffic between subnets requires an explicitly created route.

For normal same-VPC traffic, the local route provides the basic routing path.

## Same-VPC Routing

Consider:

```text
VPC: 10.0.0.0/16

Application Subnet:
10.0.10.0/24

Database Subnet:
10.0.20.0/24
```

The normal path is:

```mermaid
flowchart LR
    App[Application ENI<br/>10.0.10.25] --> RT[Route Table]
    RT --> Local["10.0.0.0/16<br/>local"]
    Local --> DB[Database ENI<br/>10.0.20.50]
```

No NAT Gateway is required.

No Internet Gateway is required.

If the connection fails, investigate:

- Security Groups.
- Network ACLs.
- Destination listener.
- Host firewall.
- DNS.
- Network interface configuration.

## Public Subnet Routing

A typical public subnet route table contains:

```text
10.0.0.0/16 -> local
0.0.0.0/0   -> Internet Gateway
```

Conceptually:

```mermaid
flowchart LR
    Instance[Public Instance] --> RT[Public Route Table]
    RT --> Local["VPC Local Route"]
    RT --> IGW[Internet Gateway]
    IGW --> Internet[Internet]
```

A route to an Internet Gateway alone does not automatically make every resource publicly reachable.

For IPv4 internet communication, the resource also needs appropriate public addressing and security controls.

## Private Subnet Routing

A common private application subnet has:

```text
10.0.0.0/16 -> local
0.0.0.0/0   -> NAT Gateway
```

The path becomes:

```mermaid
flowchart LR
    App[Private Application] --> RT[Private Route Table]
    RT --> NAT[NAT Gateway]
    NAT --> PUB[Public Subnet]
    PUB --> IGW[Internet Gateway]
    IGW --> Internet[Internet]
```

This provides outbound internet connectivity without requiring the workload itself to have a public IP.

The NAT Gateway does not make the private workload directly reachable from the internet.

## NAT Gateway Route Problems

When a private workload cannot reach an external service, verify the complete path.

Check:

```text
Private Subnet
    |
    v
Private Route Table
    |
    +--> 0.0.0.0/0 -> NAT Gateway
    |
    v
NAT Gateway
    |
    v
Public Subnet Route Table
    |
    +--> 0.0.0.0/0 -> Internet Gateway
```

A common failure is:

```text
Private Route Table
    |
    X
0.0.0.0/0 missing
```

Another is:

```text
Private Route Table
    |
    v
NAT Gateway
    |
    v
Public Subnet
    |
    X
No route to Internet Gateway
```

Both result in failed outbound connectivity.

## Internet Gateway Routing

An Internet Gateway must be attached to the VPC.

Inspect the attachment:

```bash
aws ec2 describe-internet-gateways \
  --filters Name=attachment.vpc-id,Values=vpc-0123456789abcdef0
```

Then inspect the relevant route table:

```bash
aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values=vpc-0123456789abcdef0
```

Look for:

```text
0.0.0.0/0 -> igw-xxxxxxxx
```

For IPv6, inspect for:

```text
::/0 -> igw-xxxxxxxx
```

Do not assume that an IPv4 route implies IPv6 connectivity.

## IPv4 and IPv6 Routing

IPv4 and IPv6 use separate route destinations.

Typical IPv4 default route:

```text
0.0.0.0/0
```

Typical IPv6 default route:

```text
::/0
```

An application may therefore have:

```text
IPv4 connectivity: working
IPv6 connectivity: broken
```

or the reverse.

When debugging dual-stack systems, always identify:

- Address family.
- Source address.
- Destination address.
- Matching route.
- Security controls for that address family.

## Route Tables and VPC Endpoints

VPC endpoints can change how traffic reaches AWS services.

For gateway endpoints such as S3 and DynamoDB, routes can be added to route tables.

Conceptually:

```text
Private Subnet
    |
    v
Route Table
    |
    v
VPC Endpoint
    |
    v
AWS Service
```

When endpoint-based access fails, inspect:

- Endpoint state.
- Route table association.
- Endpoint policy.
- DNS where applicable.
- Security Groups for interface endpoints.
- Network ACLs.

A common optimization is to use VPC endpoints for supported AWS service traffic instead of sending that traffic through NAT Gateways unnecessarily.

## Interface Endpoint Routing

Interface endpoints create ENIs in selected subnets.

The path is conceptually:

```text
Application
    |
    v
Private DNS
    |
    v
Interface Endpoint ENI
    |
    v
AWS Service
```

If private DNS is disabled or DNS resolution is incorrect, an application may resolve the service hostname to an address that does not follow the intended endpoint path.

Therefore, endpoint troubleshooting should include both:

```text
DNS
+
Routing
+
Security Groups
+
Endpoint Policy
```

## VPC Peering Routing

VPC peering does not automatically configure routes for your subnets.

Consider:

```text
VPC A
10.0.0.0/16
    |
    | pcx
    |
VPC B
10.1.0.0/16
```

VPC A needs:

```text
10.1.0.0/16 -> pcx-xxxxxxxx
```

VPC B needs:

```text
10.0.0.0/16 -> pcx-xxxxxxxx
```

Both directions matter.

```mermaid
flowchart LR
    A[VPC A Route Table] -->|10.1.0.0/16| P[VPC Peering]
    P --> B[VPC B]
    B -->|10.0.0.0/16 Return Route| P
```

A peering connection being in an active state does not prove that a specific subnet-to-subnet path works.

## CIDR Overlap and Routing

Overlapping CIDRs make network connectivity design difficult and can prevent straightforward routing between VPCs.

Example:

```text
VPC A: 10.0.0.0/16
VPC B: 10.0.0.0/16
```

A destination such as:

```text
10.0.20.50
```

is ambiguous from a routing perspective.

For large organizations, CIDR allocation should be centrally planned.

A practical approach is to reserve address ranges by environment or network domain:

```text
10.0.0.0/16    Production
10.1.0.0/16    Staging
10.2.0.0/16    Development
10.10.0.0/16   Shared Services
10.20.0.0/16   Network Connectivity
```

The exact scheme is organization-specific, but the important property is predictable, non-overlapping address allocation.

## Transit Gateway Routing

Transit Gateway introduces another routing layer.

A common architecture is:

```mermaid
flowchart LR
    VPC1[VPC A] --> R1[VPC A Route Table]
    R1 --> TGW[Transit Gateway]
    TGW --> TGR[TGW Route Table]
    TGR --> VPC2[VPC B]
    TGR --> OnPrem[On-Premises]
```

Troubleshooting must consider:

1. Source VPC route table.
2. Transit Gateway attachment.
3. Transit Gateway route table association.
4. Transit Gateway route propagation or static route.
5. Destination attachment.
6. Destination VPC route table.
7. Return route.

A route existing in the source VPC is insufficient if the Transit Gateway itself does not know how to forward the traffic.

## VPN Routing

For connectivity to on-premises networks, routing can involve:

- Virtual Private Gateway.
- Transit Gateway.
- Site-to-Site VPN.
- Customer Gateway.
- Dynamic routing through BGP.
- Static routes.

Example:

```text
VPC
 |
 v
Transit Gateway
 |
 v
VPN
 |
 v
Customer Gateway
 |
 v
On-Premises Network
```

When troubleshooting, identify whether routes are:

- Static.
- Dynamically propagated.
- Missing.
- More specific than expected.
- Advertised in only one direction.

Asymmetric routing is particularly important in hybrid networks.

## Asymmetric Routing

Asymmetric routing occurs when traffic takes different paths in each direction.

Example:

```text
Request:
Application -> Transit Gateway -> Firewall -> Database

Response:
Database -> Direct Route -> Application
```

The return path bypasses the stateful firewall.

This can cause connection failures even though each individual route appears valid.

Stateful middleboxes require careful routing design so that forward and return traffic follow compatible paths.

When troubleshooting complex architectures, always verify both directions.

## Network Firewall and Middlebox Routing

A centralized inspection architecture may look like:

```text
Application VPC
      |
      v
Transit Gateway
      |
      v
Inspection VPC
      |
      v
AWS Network Firewall / Appliance
      |
      v
Destination
```

The route table design must intentionally steer traffic through the inspection layer.

Typical failure modes include:

- Traffic bypassing the firewall.
- Traffic entering the firewall but lacking a return route.
- Incorrect Transit Gateway route table association.
- Missing route propagation.
- Firewall subnet routing mistakes.
- Asymmetric paths.

When a middlebox is introduced, routing complexity increases significantly.

## Blackhole Routes

AWS can display a route as a blackhole when its target is no longer usable.

Examples include routes pointing to resources that have been deleted or are unavailable.

Inspect routes:

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0
```

Look for:

```text
State: blackhole
```

A blackhole route should be treated as an infrastructure defect unless it is intentionally part of a controlled design.

Typical causes include:

- Deleted NAT Gateway.
- Deleted VPC peering connection.
- Deleted Transit Gateway attachment.
- Deleted VPN-related target.
- Infrastructure drift.

## Route Propagation

Some AWS networking architectures support route propagation.

Propagation allows routes learned from a connectivity component to appear in a route table rather than requiring every route to be manually configured.

However, route propagation must be enabled and correctly associated.

Do not assume that:

```text
VPN is connected
```

means:

```text
VPC route table automatically contains the required route
```

Validate the actual route table state.

## Troubleshooting Workflow

A reliable routing investigation follows a fixed sequence.

### Identify the Traffic

Write down:

```text
Source IP
Source subnet
Destination IP
Destination subnet
Protocol
Destination port
Address family
```

Example:

```text
10.0.10.25
    ->
10.1.20.50:5432
TCP
IPv4
```

### Identify the Source ENI

```bash
aws ec2 describe-network-interfaces \
  --filters Name=addresses.private-ip-address,Values=10.0.10.25
```

Record:

- ENI ID.
- Subnet ID.
- VPC ID.
- Security Groups.

### Identify the Associated Route Table

Determine which route table is actually associated with the source subnet.

Do not assume the main route table is being used.

### Find the Matching Route

For:

```text
10.1.20.50
```

inspect all potentially matching routes.

For example:

```text
10.0.0.0/8     -> TGW
10.1.0.0/16    -> VPC Peering
0.0.0.0/0      -> NAT
```

The `/16` route is more specific than `/8` and `/0`.

### Verify the Target

Once the matching route is identified, inspect the target.

Examples:

```text
local
igw-xxxxxxxx
nat-xxxxxxxx
tgw-xxxxxxxx
pcx-xxxxxxxx
vpce-xxxxxxxx
eni-xxxxxxxx
```

The target must exist and be in the expected state.

### Verify the Return Route

For stateful application traffic, the return path is just as important.

Example:

```text
Application
10.0.10.25
      |
      v
Destination
10.1.20.50
```

The destination side needs a route capable of returning traffic to:

```text
10.0.10.25
```

### Check Security Controls

After routing is confirmed, inspect:

- Source Security Group.
- Destination Security Group.
- Network ACLs.
- Firewall rules.
- Endpoint policies where relevant.

### Test the Actual Port

Use:

```bash
nc -vz 10.1.20.50 5432
```

rather than only:

```bash
ping 10.1.20.50
```

## Reachability Analyzer

VPC Reachability Analyzer is particularly useful when a route path contains several AWS networking components.

Use it to investigate paths involving:

- ENIs.
- Subnets.
- Route tables.
- Security Groups.
- Network ACLs.
- Transit Gateway.
- VPC peering.
- Middleboxes.

The goal is to determine whether the AWS network configuration supports the intended path and, where supported, identify the component preventing reachability.

It is especially useful when manually following routes through a large multi-VPC environment becomes error-prone.

## VPC Flow Logs and Routing

VPC Flow Logs can provide evidence about traffic observed at network interfaces.

For example:

```text
Source        Destination       Port    Action
10.0.10.25    10.1.20.50        5432    REJECT
```

Flow Logs should not be treated as a replacement for route inspection.

Use them together with:

```text
Route Tables
Security Groups
NACLs
Application Logs
Load Balancer Logs
Reachability Analyzer
```

A missing flow record can also require careful interpretation because flow logging behavior depends on where logging is enabled and which network interface observes the traffic.

## Route Table Troubleshooting Matrix

| Symptom | Likely Routing Cause | Investigation |
|---|---|---|
| Private subnet has no internet access | Missing NAT route | Inspect `0.0.0.0/0` |
| Public instance has no internet access | Missing IGW route | Inspect default route |
| Same-VPC traffic fails | Unexpected/missing route | Inspect local and more-specific routes |
| Peered VPC unreachable | Missing peering route | Inspect both VPC route tables |
| TGW destination unreachable | Missing TGW route | Inspect VPC and TGW route tables |
| On-premises unreachable | Missing propagated/static route | Inspect VPN/TGW routes |
| Traffic uses wrong path | More-specific route | Check prefix matching |
| Traffic disappears | Blackhole route | Inspect route state |
| AWS service uses NAT unexpectedly | Missing endpoint routing | Inspect endpoint and DNS |
| Response never returns | Missing/asymmetric return route | Trace both directions |
| IPv6 fails but IPv4 works | Missing IPv6 route | Inspect `::/0` and IPv6 prefixes |

## Common Routing Mistakes

### Modifying the Main Route Table Without Checking Associations

Changing the main route table can affect multiple subnets unexpectedly.

Before modifying it:

```bash
aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values=vpc-0123456789abcdef0
```

Identify all subnet associations first.

### Assuming Route Order Determines Priority

It does not.

The most specific matching prefix wins.

### Adding a Default Route to Fix Everything

A default route such as:

```text
0.0.0.0/0 -> NAT Gateway
```

does not replace intentionally designed private routes.

It can also increase cost by unnecessarily sending traffic through a NAT Gateway.

### Forgetting IPv6

Adding:

```text
0.0.0.0/0
```

does not configure:

```text
::/0
```

Dual-stack architectures require explicit consideration of both address families.

### Ignoring Return Routes

One-way routing is not sufficient for most TCP connections.

Always validate:

```text
Forward path
+
Return path
```

### Using Broad CIDRs to Work Around Routing Problems

Changing security rules to:

```text
0.0.0.0/0
```

does not fix a missing route.

Routing and authorization are separate concerns.

### Creating Overlapping Networks

CIDR overlap creates long-term routing problems across:

- VPC peering.
- Transit Gateway.
- VPN.
- Direct Connect.
- Shared services.
- Multi-account architectures.

Prevent overlap through centralized IP address management and architectural review.

## Production Best Practices

### Make Route Table Associations Explicit

Use Infrastructure as Code to define:

- Subnets.
- Route tables.
- Route associations.
- Routes.
- Gateway dependencies.

Avoid relying on accidental main-table behavior.

### Separate Route Tables by Traffic Role

A production environment may use:

```text
Public Route Table
Private Application Route Table
Private Data Route Table
Inspection Route Table
Transit Gateway Route Table
```

The exact design should reflect traffic boundaries rather than arbitrary resource grouping.

### Keep Routing Intent Documented

For important routes, document:

```text
Destination
Target
Reason
Owner
Environment
Expected traffic
```

This makes troubleshooting and change review significantly easier.

### Prefer Least-Privilege Routing

Not every subnet needs every network path.

For example:

```text
Application -> Database
Application -> Required AWS Services
Application -> Approved External Services
```

is generally preferable to unrestricted connectivity between all network segments.

### Use Infrastructure as Code

Manage routing through Terraform, CloudFormation, or the organization's approved IaC platform.

This provides:

- Version control.
- Peer review.
- Change history.
- Repeatability.
- Drift detection.
- Safer disaster recovery.

### Review Routing During Architecture Changes

Routing must be reviewed whenever introducing:

- New VPCs.
- New Availability Zones.
- Transit Gateway.
- VPC peering.
- VPN.
- Network Firewall.
- Service mesh networking.
- New private services.
- New AWS service endpoints.

A routing change can affect workloads that are not part of the immediate deployment.

## Monitoring and Auditing

Routing should be observable at multiple levels.

Useful sources include:

| Tool | Purpose |
|---|---|
| VPC Flow Logs | Network-flow visibility |
| CloudTrail | API/change auditing |
| CloudWatch | Operational metrics and alarms |
| Reachability Analyzer | Connectivity analysis |
| AWS Config | Configuration compliance |
| IaC state/history | Intended configuration |
| Application logs | Application-level failures |

CloudTrail is particularly important for determining whether a route was recently changed.

A production incident might show:

```text
Application timeout
       |
       v
Flow Logs show no expected traffic
       |
       v
CloudTrail shows route modification
       |
       v
Route removed from subnet
       |
       v
Root cause identified
```

## Change Management

Route table modifications are high-impact infrastructure changes.

Before changing production routing:

1. Identify affected subnets.
2. Identify dependent workloads.
3. Record current routes.
4. Confirm the intended destination.
5. Validate the return path.
6. Review Security Groups and NACLs.
7. Apply through the approved deployment mechanism.
8. Validate connectivity.
9. Monitor application behavior.
10. Preserve rollback information.

Avoid making undocumented console changes during incidents unless the incident procedure explicitly allows emergency changes.

## Security Considerations

Routing is part of the security architecture.

A route can expose a network path that did not previously exist.

Examples:

```text
Application Subnet
    |
    +--> Database Network
```

may be intentional, while:

```text
Database Subnet
    |
    +--> Internet Gateway
```

may represent a serious architectural problem.

Review route changes for:

- Internet exposure.
- Cross-environment connectivity.
- Cross-account access.
- On-premises reachability.
- Inspection bypass.
- Data exfiltration paths.
- Unexpected AWS service access.

Do not evaluate routing independently from Security Groups and Network ACLs.

## Scalability Considerations

As VPC architectures grow, route management becomes increasingly complex.

A small system might have:

```text
VPC
 |
 +--> Public Route Table
 +--> Private Route Table
```

A larger platform may have:

```text
                Transit Gateway
                 /     |      \
                /      |       \
              VPC A   VPC B   VPC C
                |       |       |
             Routes   Routes   Routes
                |
          Inspection Layer
                |
           On-Premises
```

At scale, consider:

- Route table count.
- Route count.
- Prefix management.
- CIDR allocation.
- Transit Gateway route tables.
- Route propagation.
- Multi-account networking.
- Centralized inspection.
- Failure domains.
- Operational ownership.

Routing should be designed as a system rather than accumulated incrementally through ad hoc route additions.

## Disaster Recovery Considerations

Routing is part of the disaster recovery plan.

Document:

- VPC CIDRs.
- Subnet CIDRs.
- Route tables.
- Route associations.
- NAT Gateway placement.
- Transit Gateway attachments.
- VPN connectivity.
- VPC peering.
- Endpoint configuration.
- Inspection paths.

A disaster recovery environment should not depend on undocumented console configuration.

Use IaC to reproduce network topology and maintain tested recovery procedures.

## Interview Traps

### "A Route Table Belongs to a VPC, So Every Subnet Uses It"

Incorrect.

Route tables are associated with subnets, and the VPC's main route table is used when a subnet does not have an explicit association.

### "The Most Recently Added Route Wins"

Incorrect.

The most specific matching route wins.

### "A NAT Gateway Can Route Traffic Between Any Two VPCs"

Incorrect.

NAT Gateway is primarily used for outbound connectivity from private resources to destinations outside their private network path. VPC peering, Transit Gateway, VPN, or other networking mechanisms are used for inter-network connectivity.

### "VPC Peering Automatically Creates Routes"

Incorrect.

The peering connection and route table configuration are separate concerns.

### "If the Request Route Exists, Connectivity Is Guaranteed"

Incorrect.

The return route, Security Groups, NACLs, firewalls, and destination listener also matter.

### "A Default Route Is Always the Best Route"

Incorrect.

More-specific private routes should be used for intended internal destinations. Sending all traffic through NAT can introduce unnecessary cost, latency, and dependency.

## Practical Diagnostic Checklist

Use this checklist during an incident:

```text
[ ] Identify source IP
[ ] Identify destination IP
[ ] Identify protocol
[ ] Identify destination port
[ ] Identify IPv4 vs IPv6
[ ] Identify source ENI
[ ] Identify source subnet
[ ] Identify associated route table
[ ] Identify matching route
[ ] Verify route target
[ ] Check route state
[ ] Check destination-side route
[ ] Check return route
[ ] Check Security Groups
[ ] Check Network ACLs
[ ] Check NAT / IGW / TGW / peering / endpoint path
[ ] Check for overlapping CIDRs
[ ] Check for asymmetric routing
[ ] Test the actual port
[ ] Inspect VPC Flow Logs
[ ] Use Reachability Analyzer where appropriate
[ ] Check application-level behavior
[ ] Record root cause and remediation
```

## Key Takeaways

- **Route tables determine the forwarding path**, and the most specific matching route takes precedence.
- **Always verify the actual subnet-to-route-table association** instead of assuming a subnet uses a named or main route table.
- **Connectivity requires both forward and return paths**; Transit Gateway, peering, VPN, NAT, and middleboxes make this especially important.
- **Treat CIDR planning and routing as architectural concerns**, particularly in multi-VPC and hybrid environments.
- **Use Flow Logs, Reachability Analyzer, CloudTrail, and IaC history together** to diagnose routing failures and safely manage production changes.