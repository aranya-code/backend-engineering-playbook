# 11- Transit Gateway Connectivity Issues

## Overview

AWS Transit Gateway (TGW) provides centralized Layer 3 connectivity between multiple VPCs, AWS accounts, Regions, and external networks. It is commonly used as the routing hub in multi-VPC and multi-account architectures where maintaining direct VPC-to-VPC connectivity would become difficult to operate.

Transit Gateway connectivity failures are rarely caused by a single component. A packet typically crosses multiple routing and security boundaries:

```text
Source Workload
      |
      v
Source Subnet Route Table
      |
      v
Transit Gateway Attachment
      |
      v
Transit Gateway Route Table
      |
      v
Destination Attachment
      |
      v
Destination Subnet Route Table
      |
      v
Security Group / NACL
      |
      v
Destination Workload
```

A healthy Transit Gateway attachment does not guarantee end-to-end connectivity. Troubleshooting must validate the complete forward and return paths.

Typical causes include:

- Missing source VPC route.
- Incorrect source subnet route-table association.
- Incorrect Transit Gateway route-table association.
- Missing route propagation.
- Incorrect static Transit Gateway route.
- Blackhole route.
- Missing destination VPC route.
- Missing return route.
- Overlapping CIDRs.
- Security Group restrictions.
- Network ACL restrictions.
- Asymmetric routing.
- DNS resolution problems.
- VPN or Direct Connect routing issues.
- Cross-Region Transit Gateway peering problems.

The most reliable troubleshooting strategy is to move through the network path one routing decision at a time rather than changing multiple resources simultaneously.

## Transit Gateway Routing Model

Transit Gateway introduces another routing layer between VPC route tables.

Consider two VPCs:

```text
VPC A
10.10.0.0/16

VPC B
10.20.0.0/16
```

The complete path requires:

```text
VPC A Route Table
10.20.0.0/16 -> TGW
        |
        v
Transit Gateway Route Table
10.20.0.0/16 -> VPC B Attachment
        |
        v
VPC B Route Table
10.10.0.0/16 -> TGW
```

The source route table alone is not sufficient.

```mermaid
flowchart LR
    Source[Source Workload]
    SourceRT[Source VPC Route Table]
    TGW[Transit Gateway]
    TGWRT[TGW Route Table]
    DestRT[Destination VPC Route Table]
    Destination[Destination Workload]

    Source --> SourceRT
    SourceRT --> TGW
    TGW --> TGWRT
    TGWRT --> DestRT
    DestRT --> Destination

    Destination -. Return Path .-> DestRT
    DestRT -.-> TGW
    TGW -.-> SourceRT
```

This distinction is the foundation of Transit Gateway troubleshooting.

## Transit Gateway Attachments

A VPC connects to Transit Gateway through a VPC attachment.

Inspect the attachment:

```bash
aws ec2 describe-transit-gateway-vpc-attachments \
  --transit-gateway-attachment-ids tgw-attach-0123456789abcdef0
```

Verify:

- Transit Gateway ID.
- VPC ID.
- Attachment ID.
- Attachment state.
- Availability Zone/subnet configuration.
- AWS account.
- Region.

The attachment should be operational before investigating routing.

A typical logical state progression is:

```text
pending
   |
   v
available
   |
   +--> deleting
   |
   +--> deleted
```

An attachment being `available` only establishes that the attachment itself is operational. It does not prove that the routing path is correct.

## VPC Attachment Subnets

A Transit Gateway VPC attachment uses selected subnets in the VPC.

These subnets provide the network interfaces through which Transit Gateway communicates with the VPC.

When troubleshooting, verify:

- The attachment belongs to the expected VPC.
- The attachment uses the intended subnets.
- The subnets are in appropriate Availability Zones.
- The source subnet has a route toward TGW.
- The destination subnet has the required return route.
- Production workloads do not depend on an unintended single-AZ network path.

A common mistake is assuming that attaching a VPC to Transit Gateway automatically updates all VPC route tables.

It does not.

## Source VPC Route Table

Suppose:

```text
Application VPC
10.10.0.0/16

Database VPC
10.20.0.0/16
```

The application subnet needs a route similar to:

```text
Destination: 10.20.0.0/16
Target:      Transit Gateway
```

Inspect the route table:

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0
```

Inspect only routes:

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0 \
  --query 'RouteTables[].Routes[]'
```

Verify that the route exists in the route table associated with the **actual source subnet**.

Do not assume the VPC's main route table is being used by every subnet.

## Identifying the Source Subnet Route Table

First identify the subnet:

```bash
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[].Instances[].{
    InstanceId:InstanceId,
    PrivateIp:PrivateIpAddress,
    SubnetId:SubnetId,
    VpcId:VpcId
  }'
```

Then inspect its route-table association:

```bash
aws ec2 describe-route-tables \
  --filters \
    Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

This is an important troubleshooting step because two subnets in the same VPC can use different route tables.

For example:

```text
Application Subnet
        |
        v
Private-App-RT
        |
        +--> 10.20.0.0/16 -> TGW


Batch Subnet
        |
        v
Private-Batch-RT
        |
        X
        No route to 10.20.0.0/16
```

The VPC may appear correctly configured while only specific workloads are affected.

## Transit Gateway Route Tables

Transit Gateway has independent route tables.

A typical routing flow is:

```text
Source VPC Route Table
10.20.0.0/16 -> TGW
        |
        v
Transit Gateway
        |
        v
TGW Route Table
10.20.0.0/16 -> VPC-B Attachment
```

Inspect TGW route tables:

```bash
aws ec2 describe-transit-gateway-route-tables
```

Search for routes:

```bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0 \
  --filters Name=type,Values=static,propagated
```

Verify:

- Destination CIDR.
- Route type.
- Route state.
- Target attachment.
- Blackhole status.
- Route specificity.

## Transit Gateway Route-Table Association

A Transit Gateway attachment is associated with a Transit Gateway route table.

Conceptually:

```text
VPC-A Attachment
       |
       v
Production TGW Route Table

VPC-B Attachment
       |
       v
Shared Services TGW Route Table
```

This association determines the Transit Gateway routing domain used by traffic arriving through the attachment.

Inspect associations:

```bash
aws ec2 get-transit-gateway-route-table-associations \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0
```

A common production failure looks like:

```text
Correct VPC attachment
        |
        v
Wrong TGW route-table association
        |
        v
Destination route unavailable
```

The attachment can therefore be healthy while the workload remains isolated.

## Route Propagation

Route propagation controls which routes from an attachment are installed into a Transit Gateway route table.

For example:

```text
VPC B
10.20.0.0/16
      |
      | Propagation
      v
TGW Route Table
10.20.0.0/16
      |
      v
VPC-B Attachment
```

Inspect propagation:

```bash
aws ec2 get-transit-gateway-route-table-propagations \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0
```

A common failure is:

```text
VPC attachment
     |
     v
Association exists
     |
     X
Destination route not propagated
```

The source VPC can therefore send traffic to TGW while TGW has no route for the destination CIDR.

## Association vs Propagation

These concepts are frequently confused.

| Concept | Purpose |
|---|---|
| Association | Determines which TGW route table an attachment uses |
| Propagation | Installs routes from an attachment into a TGW route table |
| Static route | Explicitly defines a destination and target |
| Blackhole route | Explicitly discards matching traffic |

For example:

```text
VPC A Attachment
      |
      | Association
      v
TGW Route Table A

VPC B Attachment
      |
      | Propagation
      v
TGW Route Table A
      |
      +--> 10.20.0.0/16 -> VPC B Attachment
```

Correct association does not imply correct propagation.

## Static Transit Gateway Routes

Transit Gateway routes can be explicitly configured.

Example:

```text
10.20.0.0/16 -> VPC-B Attachment
```

Static routes are useful when the network design requires deliberate routing control.

Inspect routes:

```bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0 \
  --filters Name=type,Values=static
```

Verify that the route points to the expected attachment.

A static route can be syntactically valid while being operationally incorrect:

```text
10.20.0.0/16
       |
       v
Wrong Attachment
```

This can be especially difficult to diagnose in environments containing many VPCs with similar CIDRs or naming conventions.

## Blackhole Routes

Transit Gateway can contain blackhole routes.

For example:

```text
10.50.0.0/16 -> blackhole
```

Traffic matching that route is intentionally discarded.

Blackhole routes may be useful for:

- Network isolation.
- Explicit traffic denial.
- Temporary migrations.
- Preventing access to retired networks.

They can also cause unexpected outages if created accidentally.

Always inspect the actual route matching the destination CIDR rather than checking only whether a route exists.

## Route Specificity

AWS routing uses the most specific matching route.

For example:

```text
10.20.0.0/16  -> VPC-B
10.20.10.0/24 -> blackhole
```

Traffic to:

```text
10.20.10.25
```

matches the `/24` route.

Therefore:

```text
10.20.0.0/16
```

being correctly configured does not prove that:

```text
10.20.10.25
```

will follow that route.

When troubleshooting a specific IP address, inspect overlapping and more-specific routes.

## Return Path

Transit Gateway connectivity requires a valid return path.

Suppose:

```text
Application:
10.10.1.20

Database:
10.20.2.30:5432
```

Forward path:

```text
10.10.1.20
    |
    v
VPC A Route Table
    |
    v
TGW
    |
    v
VPC B Route Table
    |
    v
10.20.2.30
```

Return path:

```text
10.20.2.30
    |
    v
VPC B Route Table
    |
    v
TGW
    |
    v
VPC A Route Table
    |
    v
10.10.1.20
```

A missing return route can produce a connection timeout even when the forward route is correct.

This is one of the most important distinctions between:

```text
"I can see the route"
```

and:

```text
"The connection works"
```

## Asymmetric Routing

Complex Transit Gateway architectures can create asymmetric paths.

For example:

```text
Forward:
VPC A -> TGW -> Inspection VPC -> VPC B

Return:
VPC B -> TGW -> VPC A
```

This can break stateful network appliances and make packet analysis difficult.

Potential symptoms include:

- SYN reaches the destination.
- SYN-ACK follows another path.
- Firewall state does not match.
- Connection times out or resets.
- Flow logs appear inconsistent.

Centralized inspection architectures should explicitly define both forward and return routing.

## CIDR Overlap

Overlapping VPC CIDRs can prevent the intended routing model from working correctly.

Example:

```text
VPC A
10.10.0.0/16

VPC B
10.10.0.0/16
```

The same address range exists in both networks.

This creates ambiguity because:

```text
10.10.20.10
```

cannot uniquely identify which VPC should receive the traffic.

Inspect VPC CIDRs:

```bash
aws ec2 describe-vpcs \
  --query 'Vpcs[].{
    VpcId:VpcId,
    Cidr:CidrBlock,
    State:State
  }'
```

In large organizations, CIDR allocation should be centrally managed before VPC creation.

CIDR planning is therefore a scalability concern, not merely a configuration detail.

## Security Groups

Transit Gateway does not bypass Security Groups.

If:

```text
Application VPC
10.10.0.0/16
```

connects to:

```text
Database VPC
10.20.0.0/16
```

on:

```text
TCP 5432
```

the destination Security Group must permit the intended source.

Inspect Security Groups:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0
```

Validate:

```text
Source CIDR
Destination Port
Protocol
Direction
```

Avoid using:

```text
0.0.0.0/0
```

as a troubleshooting shortcut.

The correct approach is to identify the actual traffic source and authorize only what is required.

## Network ACLs

Network ACLs are stateless.

If a restrictive NACL is applied to the source or destination subnet, verify both directions.

For a database connection:

```text
Client
10.10.1.20:45000
      |
      | TCP 5432
      v
Database
10.20.2.30:5432
      |
      | TCP 45000
      v
Client
```

Inspect NACLs:

```bash
aws ec2 describe-network-acls \
  --filters \
    Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

Check:

- Inbound rules.
- Outbound rules.
- Rule numbers.
- Explicit denies.
- Subnet association.

A Security Group can allow traffic while a NACL still blocks it.

## DNS Troubleshooting

Transit Gateway routes IP packets. DNS resolution is a separate dependency.

A service may be reachable by IP:

```bash
nc -vz 10.20.2.30 5432
```

while the hostname fails:

```bash
nc -vz db.internal.example.com 5432
```

Test DNS:

```bash
dig db.internal.example.com
```

or:

```bash
getent hosts db.internal.example.com
```

Investigate:

- VPC DNS support.
- VPC DNS hostnames.
- Route 53 private hosted zones.
- Route 53 Resolver.
- Resolver endpoints.
- Cross-VPC DNS architecture.
- Split-horizon DNS.
- Incorrect `A` records.
- Incorrect `AAAA` records.

Do not change Transit Gateway routes when the actual problem is DNS.

## Cross-Account Transit Gateway Connectivity

Centralized Transit Gateway architectures commonly span multiple AWS accounts.

Example:

```mermaid
flowchart LR
    Network[Network Account]
    TGW[Transit Gateway]
    App[Application Account]
    Data[Data Account]
    Shared[Shared Services Account]

    Network --> TGW
    TGW --> App
    TGW --> Data
    TGW --> Shared
```

Troubleshooting should verify:

- TGW owner account.
- VPC owner account.
- AWS RAM resource sharing.
- Attachment ownership.
- Attachment acceptance where applicable.
- Attachment state.
- TGW route-table association.
- Route propagation.
- VPC route tables.
- IAM permissions.

Ownership boundaries should be documented because the network account may control TGW configuration while application teams control VPC route tables.

## Cross-Region Connectivity

Transit Gateway can connect Regions through Transit Gateway peering.

Conceptually:

```text
Region A
VPC A
  |
TGW A
  |
  | TGW Peering
  |
TGW B
  |
VPC B
Region B
```

Validate both routing domains:

```text
VPC A
  |
TGW A Route Table
  |
TGW Peering
  |
TGW B Route Table
  |
VPC B
```

Check:

- TGW peering attachment.
- Region.
- Source TGW route.
- Destination TGW route.
- VPC route tables.
- Return path.
- CIDR overlap.
- Inter-Region traffic costs.
- Latency.

Do not troubleshoot cross-Region connectivity as though it were a single TGW route table.

## On-Premises Connectivity

Transit Gateway is frequently used as the AWS-side hub for on-premises connectivity through VPN or Direct Connect.

A typical path is:

```text
Application VPC
      |
      v
VPC Route Table
      |
      v
Transit Gateway
      |
      v
VPN / Direct Connect Attachment
      |
      v
Customer Network
      |
      v
On-Premises Service
```

A healthy VPN tunnel does not prove that an application can reach an on-premises service.

Verify:

- TGW route to the external network.
- VPN or Direct Connect attachment.
- Route propagation.
- Static routes.
- BGP state where applicable.
- Customer-side routing.
- Return route.
- Firewall policies.
- DNS.

## VPN Route Troubleshooting

For VPN connectivity, separate tunnel state from routing state.

```text
VPN Tunnel
    |
    +--> UP
```

does not necessarily mean:

```text
Application
    |
    v
On-Premises Service
    |
    X
    Route unavailable
```

Verify the destination CIDR exists in the TGW route table and is associated with the correct VPN attachment.

For BGP-based architectures, also verify that the expected prefixes are being advertised and received.

## VPC Reachability Analyzer

VPC Reachability Analyzer can help determine whether a supported AWS network path is reachable.

Use it to validate paths between source and destination network resources.

A useful model is:

```text
Source ENI
    |
    v
Reachability Analyzer
    |
    v
Destination ENI
    |
    v
Reported network path
```

It can help identify problems involving:

- Route tables.
- Security Groups.
- Network ACLs.
- Transit Gateway.
- VPC attachments.
- Other supported network components.

It should complement, rather than replace:

- Flow Logs.
- AWS CLI inspection.
- Application-level testing.
- Packet capture where available.

## VPC Flow Logs

VPC Flow Logs provide visibility into network traffic observed by supported interfaces.

Useful information includes:

```text
Source IP
Destination IP
Source Port
Destination Port
Protocol
Action
```

A simplified interpretation:

```text
No expected flow
    |
    +--> Investigate whether traffic reached the expected interface

REJECT
    |
    +--> Investigate filtering

ACCEPT
    |
    +--> Investigate destination/application behavior
```

An `ACCEPT` flow does not prove that the application successfully processed the request. It only provides evidence about network traffic observed by the relevant interface.

## Connectivity Testing

Run tests from the actual source environment whenever possible.

### DNS

```bash
dig api.internal.example.com
```

### TCP

```bash
nc -vz 10.20.2.30 5432
```

### HTTP

```bash
curl -v http://10.20.2.30:8080/health
```

### HTTPS

```bash
curl -vk https://api.internal.example.com/health
```

### PostgreSQL

```bash
psql \
  "host=db.internal.example.com port=5432 dbname=application user=app_user sslmode=require"
```

### gRPC

```bash
grpcurl \
  -vv \
  api.internal.example.com:443 \
  list
```

A test from a developer laptop does not validate the same network path used by:

- ECS tasks.
- EC2 instances.
- EKS pods.
- Lambda functions.
- Kubernetes nodes.

The network location of the test matters.

## Packet-Level Troubleshooting

When configuration appears correct, packet capture can provide additional evidence.

On a Linux workload:

```bash
sudo tcpdump -ni any host 10.20.2.30 and port 5432
```

For a successful TCP connection, you should normally observe:

```text
SYN
SYN-ACK
ACK
```

If you observe:

```text
SYN
```

but no:

```text
SYN-ACK
```

investigate:

- Routing.
- Security Groups.
- NACLs.
- Destination listener.
- Return routing.

If the TCP handshake completes but the application fails, move the investigation up the stack:

```text
Network
   |
   v
TCP
   |
   v
TLS
   |
   v
Protocol
   |
   v
Authentication
   |
   v
Application
```

## Common Failure Patterns

| Symptom | Likely Cause |
|---|---|
| TGW attachment unavailable | Attachment configuration/state |
| Source cannot reach remote VPC | Source route or TGW association |
| Some VPCs work, one VPC fails | Missing TGW route or propagation |
| One subnet works, another fails | Different route-table association |
| TGW route points to wrong VPC | Incorrect static route |
| Destination route missing | Missing propagation |
| Route exists but traffic is dropped | Security Group or NACL |
| Forward path works but response fails | Missing return route |
| Traffic reaches destination but application fails | Listener/application problem |
| Specific CIDR fails | Route specificity, overlap, or blackhole |
| IP works but hostname fails | DNS |
| Cross-account attachment fails | RAM/ownership/acceptance |
| VPN is up but service is unreachable | Routing or customer-side configuration |
| Cross-Region traffic fails | TGW peering or routing |
| TCP timeout | Network path or packet filtering |
| Connection refused | Destination reachable but service not listening |

## Systematic Troubleshooting Workflow

The following sequence minimizes unnecessary changes.

### Identify the Source

Record:

```text
Source workload
Source IP
Source subnet
Source VPC
Source route table
Source Region
Source account
```

For EC2:

```bash
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[].Instances[].{
    InstanceId:InstanceId,
    PrivateIp:PrivateIpAddress,
    SubnetId:SubnetId,
    VpcId:VpcId
  }'
```

### Identify the Destination

Record:

```text
Destination hostname
Destination IP
Destination port
Destination subnet
Destination VPC
Destination Region
Destination account
```

### Validate CIDRs

Check source and destination CIDRs:

```bash
aws ec2 describe-vpcs \
  --vpc-ids vpc-aaaaaaaaaaaaaaaaa vpc-bbbbbbbbbbbbbbbbb \
  --query 'Vpcs[].{
    VpcId:VpcId,
    Cidr:CidrBlock
  }'
```

Check for overlapping address ranges.

### Validate the Source Route

Confirm:

```text
Destination CIDR -> TGW
```

exists in the route table associated with the source subnet.

### Validate the Source Attachment

```bash
aws ec2 describe-transit-gateway-vpc-attachments \
  --filters \
    Name=transit-gateway-id,Values=tgw-0123456789abcdef0 \
    Name=vpc-id,Values=vpc-aaaaaaaaaaaaaaaaa
```

Verify:

```text
Attachment state
VPC ID
TGW ID
Attachment subnets
```

### Identify the TGW Route Table

Determine which TGW route table the source attachment is associated with.

```bash
aws ec2 get-transit-gateway-route-table-associations \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0
```

### Validate the TGW Route

Search for the destination CIDR:

```bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0 \
  --filters Name=type,Values=static,propagated
```

Verify:

```text
Destination CIDR
Target attachment
Route type
Route state
Blackhole status
```

### Validate Propagation

```bash
aws ec2 get-transit-gateway-route-table-propagations \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0
```

Determine whether the destination attachment is propagating its CIDR into the relevant TGW route table.

### Validate the Destination Route

The destination VPC needs a route back to the source CIDR:

```text
10.10.0.0/16 -> TGW
```

### Validate Security

Check:

```text
Security Group
Network ACL
Destination port
Protocol
```

### Validate DNS

If a hostname is involved:

```bash
dig api.internal.example.com
```

Confirm that the returned address belongs to the intended network.

### Validate TCP

```bash
nc -vz 10.20.2.30 5432
```

### Validate Application Protocol

If TCP succeeds:

```bash
curl -v https://api.internal.example.com/health
```

or use the appropriate PostgreSQL, gRPC, Kafka, Redis, or application-specific client.

### Inspect Network Telemetry

Use:

- VPC Flow Logs.
- Reachability Analyzer.
- CloudWatch metrics where applicable.
- VPN/BGP telemetry.
- Infrastructure change history.

### Review Recent Changes

Check recent:

- Terraform changes.
- Route changes.
- TGW association changes.
- Propagation changes.
- Security Group changes.
- NACL changes.
- DNS changes.
- VPN changes.

Network outages frequently follow an apparently unrelated infrastructure change.

## Production Example

Consider:

```text
Application VPC
10.10.0.0/16
        |
        v
Transit Gateway
        |
        v
Database VPC
10.20.0.0/16

Database:
10.20.10.25:5432
```

The application reports:

```text
connection timeout
```

Investigation finds:

```text
Source VPC route:
10.20.0.0/16 -> TGW
```

The route exists.

The VPC attachment is:

```text
available
```

The source attachment is associated with the expected TGW route table.

The destination VPC route table contains:

```text
10.10.0.0/16 -> TGW
```

Security Groups and NACLs are correct.

However, the TGW route table does not contain:

```text
10.20.0.0/16
```

The destination VPC CIDR was not propagated into the TGW route table.

Therefore:

```text
Application
   |
   v
VPC Route Table
   |
   v
TGW
   |
   X
No destination route
```

The root cause is missing Transit Gateway route propagation.

The important engineering lesson is that a correct VPC route only gets traffic to the Transit Gateway. Transit Gateway must independently determine where the destination CIDR should be forwarded.

## Common Mistakes and Pitfalls

### Assuming TGW Automatically Routes Every Attached VPC

An attachment does not mean every TGW route table can reach every other attachment.

Association and routing policies must be intentionally configured.

### Checking Only the VPC Route Table

Transit Gateway adds another routing layer.

Always validate:

```text
Source VPC Route Table
+
TGW Route Table
+
Destination VPC Route Table
```

### Confusing Association With Propagation

Association answers:

```text
Which TGW route table does this attachment use?
```

Propagation answers:

```text
Which routes from this attachment are installed into a TGW route table?
```

They are independent configuration concepts.

### Forgetting the Return Route

A working forward route does not guarantee a working connection.

Always validate both directions.

### Ignoring Route Specificity

A more-specific route can override the route you expected.

Inspect the exact destination IP and overlapping CIDRs.

### Ignoring Blackhole Routes

A blackhole route can intentionally discard traffic and can be easy to miss during an incident.

### Assuming a Healthy Attachment Means Healthy Connectivity

An available attachment does not validate:

- Routing.
- Propagation.
- Security.
- DNS.
- Application health.

### Opening Security Groups Broadly

Do not use `0.0.0.0/0` as a generic fix.

Identify the actual source CIDR and destination port.

### Assuming VPN Tunnel Health Means Application Connectivity

A VPN tunnel can be established while required routes are missing.

Separate:

```text
Tunnel State
```

from:

```text
Routing State
```

### Ignoring Asymmetric Routing

Centralized inspection and hybrid-cloud architectures can create different forward and return paths.

Validate the complete route in both directions.

### Testing From the Wrong Location

A successful connection from a bastion host does not prove that an ECS task or EKS pod can connect.

Always test from the actual workload network path.

## Security Considerations

Transit Gateway provides network routing, not application authorization.

A production request should pass through multiple controls:

```text
TGW Route Table
      |
      v
VPC Route Table
      |
      v
Security Group
      |
      v
Network ACL
      |
      v
Application Authorization
```

Define explicitly:

- Which VPCs can communicate.
- Which CIDRs are reachable.
- Which ports are reachable.
- Which environments are isolated.
- Which attachments can access which TGW route tables.
- Which teams can modify network configuration.

For example:

```text
Production -> Shared Services
Production -X-> Development

Development -> Shared Services
Development -X-> Production
```

Network segmentation should be represented through explicit route-table associations and routing policies rather than relying on undocumented assumptions.

## Scalability Considerations

Transit Gateway simplifies large network topologies, but it does not eliminate network design requirements.

As the environment grows, establish:

- Standard CIDR allocation.
- Dedicated TGW route tables.
- Environment segmentation.
- Centralized network ownership.
- AWS RAM sharing strategy.
- IaC-managed configuration.
- Explicit propagation policies.
- Standard attachment naming.
- Automated validation.
- Configuration drift detection.

A large Transit Gateway deployment should be treated as a distributed routing system.

Network changes should therefore receive the same engineering discipline as application changes:

```text
Design
  |
  v
Code
  |
  v
Review
  |
  v
Plan
  |
  v
Deploy
  |
  v
Observe
```

## High Availability

Production Transit Gateway architectures should avoid unnecessary single-AZ dependencies.

A typical VPC architecture distributes attachment subnets across Availability Zones:

```mermaid
flowchart TB
    VPC[VPC]
    AZ1[Availability Zone A]
    AZ2[Availability Zone B]
    TGW[Transit Gateway]

    VPC --> AZ1
    VPC --> AZ2
    AZ1 --> TGW
    AZ2 --> TGW
```

For critical systems:

- Distribute workloads across Availability Zones.
- Use appropriate TGW attachment subnet placement.
- Avoid single-AZ application dependencies.
- Ensure destination services are highly available.
- Test Availability Zone failure scenarios.
- Document expected routing behavior during failures.

Transit Gateway being managed by AWS does not automatically make every application architecture highly available.

## Monitoring and Observability

Monitor:

- TGW attachment state.
- TGW route-table changes.
- Route propagation.
- VPC route changes.
- Security Group changes.
- NACL changes.
- VPC Flow Logs.
- VPN tunnel state.
- BGP sessions where applicable.
- Application connection errors.
- Latency.
- Packet drops.
- Cross-Region traffic.
- Network data-transfer usage.

Correlate application failures with network changes:

```text
Application Error
       |
       v
Timestamp
       |
       v
Flow Logs
       |
       v
TGW/VPC Configuration
       |
       v
Infrastructure Change
```

This makes it possible to determine whether the failure was caused by:

- Application deployment.
- Route change.
- Security change.
- DNS change.
- Network infrastructure change.

## Infrastructure as Code

Transit Gateway configuration should generally be managed through Infrastructure as Code.

A simplified Terraform configuration:

```hcl
resource "aws_ec2_transit_gateway" "core" {
  description = "Central network transit gateway"

  tags = {
    Name = "core-tgw"
  }
}

resource "aws_ec2_transit_gateway_vpc_attachment" "app" {
  transit_gateway_id = aws_ec2_transit_gateway.core.id
  vpc_id             = aws_vpc.app.id
  subnet_ids         = aws_subnet.app_tgw[*].id

  tags = {
    Name = "app-tgw-attachment"
  }
}

resource "aws_ec2_transit_gateway_vpc_attachment" "data" {
  transit_gateway_id = aws_ec2_transit_gateway.core.id
  vpc_id             = aws_vpc.data.id
  subnet_ids         = aws_subnet.data_tgw[*].id

  tags = {
    Name = "data-tgw-attachment"
  }
}

resource "aws_route" "app_to_data" {
  route_table_id         = aws_route_table.app.id
  destination_cidr_block = aws_vpc.data.cidr_block
  transit_gateway_id     = aws_ec2_transit_gateway.core.id
}
```

Production implementations should also explicitly manage:

- TGW route tables.
- TGW associations.
- TGW propagations.
- Static routes.
- Blackhole routes where required.
- VPC route tables.
- Attachment configuration.

Avoid relying on undocumented manual configuration.

## Operational Best Practices

### Maintain a Network Inventory

Document:

```text
VPC
CIDR
AWS Account
Region
Transit Gateway
Attachment
TGW Route Table
Association
Propagation
Static Routes
Security Groups
NACLs
DNS Dependencies
VPN / Direct Connect
```

### Establish Ownership

Define ownership for:

- Transit Gateway.
- VPC attachments.
- VPC route tables.
- TGW route tables.
- Security Groups.
- NACLs.
- DNS.
- VPN.
- Direct Connect.
- On-premises routing.

Clear ownership reduces incident resolution time.

### Treat Routes as Change-Controlled Infrastructure

Network route changes can have organization-wide impact.

Use:

- Pull requests.
- Terraform plans.
- CI validation.
- Peer review.
- Change records where required.
- Automated drift detection.

### Standardize Routing Domains

A large organization might use:

```text
Production TGW Route Table
Development TGW Route Table
Shared Services TGW Route Table
Inspection TGW Route Table
On-Premises TGW Route Table
```

The exact architecture depends on security and connectivity requirements, but predictable patterns reduce troubleshooting complexity.

## Cost Considerations

Transit Gateway introduces networking costs that should be considered during architecture design.

Evaluate:

- Attachment costs.
- Data processing costs.
- Cross-Region traffic.
- Inter-Region data transfer.
- VPN usage.
- Direct Connect architecture.
- Centralized inspection traffic.

High-volume workloads can materially affect networking costs, including:

- Kafka.
- Database replication.
- Large object transfers.
- Analytics workloads.
- Backup systems.

Routing decisions should therefore consider:

```text
Reliability
+
Security
+
Performance
+
Operational Complexity
+
Cost
```

rather than optimizing only one dimension.

## Disaster Recovery Considerations

Transit Gateway dependencies should be documented as part of disaster recovery planning.

Record:

- TGW IDs.
- TGW route tables.
- VPC attachments.
- Associations.
- Propagations.
- Static routes.
- Blackhole routes.
- VPN attachments.
- Direct Connect dependencies.
- Cross-Region connectivity.
- Security controls.
- DNS dependencies.

Infrastructure recovery should be reproducible through Infrastructure as Code.

Avoid a recovery architecture where critical routes must be manually reconstructed during an outage.

## Interview Traps

### "Transit Gateway Is Just VPC Peering With More VPCs"

Not exactly.

Transit Gateway provides centralized routing, supports transitive connectivity, and allows network segmentation through separate TGW route tables.

### "An Attached VPC Can Reach Every Other Attached VPC"

Incorrect.

The relevant TGW route table must contain the required route and the VPC route tables must also be configured.

### "Association and Propagation Are the Same"

Incorrect.

Association selects the TGW route table used by an attachment.

Propagation installs routes from an attachment into a TGW route table.

### "The VPC Route Table Is Enough"

Incorrect.

Transit Gateway introduces another routing decision.

### "A Healthy TGW Attachment Means the Network Is Healthy"

Incorrect.

The attachment can be available while routes, propagation, return routing, Security Groups, NACLs, DNS, or the application are broken.

### "VPN Tunnel Up Means On-Premises Connectivity Works"

Incorrect.

Tunnel state and route availability are separate concerns.

### "Transit Gateway Prevents Asymmetric Routing"

Incorrect.

Inspection architectures, hybrid networking, and multiple TGW route tables can still produce asymmetric paths.

## Production Troubleshooting Checklist

```text
[ ] Identify source workload
[ ] Identify source IP
[ ] Identify source subnet
[ ] Identify source VPC
[ ] Identify source route table
[ ] Identify destination IP
[ ] Identify destination subnet
[ ] Identify destination VPC
[ ] Identify destination port
[ ] Verify source and destination CIDRs
[ ] Check for CIDR overlap
[ ] Verify Transit Gateway ID
[ ] Verify source VPC attachment
[ ] Verify destination VPC attachment
[ ] Verify attachment state
[ ] Verify attachment subnets/AZs
[ ] Identify source TGW route-table association
[ ] Verify TGW route-table association
[ ] Check route propagation
[ ] Check static TGW routes
[ ] Check blackhole routes
[ ] Check route specificity
[ ] Verify source VPC route to TGW
[ ] Verify TGW route to destination attachment
[ ] Verify destination VPC return route
[ ] Verify Security Groups
[ ] Verify Network ACLs
[ ] Verify DNS resolution
[ ] Test TCP connectivity
[ ] Test TLS if applicable
[ ] Test application protocol
[ ] Verify destination listener
[ ] Check VPC Flow Logs
[ ] Use Reachability Analyzer where appropriate
[ ] Check for asymmetric routing
[ ] Check VPN/BGP if hybrid connectivity is involved
[ ] Check TGW peering if cross-Region connectivity is involved
[ ] Review recent Terraform/IaC changes
[ ] Review route ownership
[ ] Review security changes
[ ] Review network data-transfer implications
```

## Key Takeaways

- **Transit Gateway troubleshooting requires validating multiple routing layers**: source VPC routes, TGW route tables, and destination VPC routes.
- **Association and propagation are different mechanisms**: association determines the TGW route table used by an attachment, while propagation installs attachment routes into TGW route tables.
- **A healthy TGW attachment does not guarantee connectivity**; route selection, return paths, Security Groups, NACLs, DNS, and application listeners must also be correct.
- **Large TGW environments should be treated as centrally managed routing infrastructure**, with deliberate segmentation, IaC, ownership, observability, and controlled change management.
- **Troubleshoot the complete forward and return path**, especially when using inspection VPCs, VPN, Direct Connect, cross-account connectivity, or cross-Region Transit Gateway peering.