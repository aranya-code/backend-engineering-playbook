# 15- Common Production VPC Failures

## Overview

Amazon VPC failures are rarely caused by a single AWS component in isolation. Production connectivity depends on the interaction between subnet routing, route tables, Security Groups, Network ACLs, DNS, NAT Gateways, Internet Gateways, VPC endpoints, Transit Gateway, VPC peering, VPN connectivity, load balancers, and application-level behavior.

A useful production model is:

```text
Application
    |
    v
DNS
    |
    v
TCP / UDP
    |
    v
Route Table
    |
    v
Network Path
    |
    +--> Internet Gateway
    +--> NAT Gateway
    +--> VPC Endpoint
    +--> VPC Peering
    +--> Transit Gateway
    +--> VPN / Direct Connect
    |
    v
Network ACL
    |
    v
Security Group
    |
    v
Destination
```

The actual path depends on the architecture, but the troubleshooting principle remains consistent:

> Identify the exact source, destination, protocol, and intended network path before changing infrastructure.

Production VPC incidents generally fall into a small number of categories:

| Failure category | Typical symptom |
|---|---|
| Routing | Timeout, unreachable destination |
| Security Group | Connection blocked |
| Network ACL | Intermittent-looking or asymmetric connectivity failure |
| DNS | Hostname does not resolve or resolves incorrectly |
| NAT Gateway | Private workloads cannot reach external services |
| Internet Gateway | Public resources cannot reach the Internet |
| VPC Endpoint | Private workload cannot access AWS service |
| VPC Peering | Cross-VPC communication fails |
| Transit Gateway | Multi-VPC connectivity fails |
| VPN | Hybrid connectivity fails |
| Load Balancer | Client or target connectivity fails |
| MTU / fragmentation | Some requests work while larger responses fail |
| Ephemeral ports | Return traffic blocked by restrictive NACL |
| Application | Network path works but service still fails |

The goal of troubleshooting is not simply to restore connectivity. A senior engineer should determine **which layer failed, why it failed, what changed, and how to prevent recurrence**.

## A Layered VPC Troubleshooting Model

VPC incidents are easier to diagnose when treated as layers.

```mermaid
flowchart TD
    A[Application Request]
    B[DNS Resolution]
    C[TCP / UDP Connectivity]
    D[Route Selection]
    E[Network Path]
    F[Network ACL]
    G[Security Group]
    H[Destination Service]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
```

The practical sequence is:

```text
DNS
  |
  v
IP
  |
  v
Route
  |
  v
AWS network path
  |
  v
NACL
  |
  v
Security Group
  |
  v
TCP
  |
  v
TLS / protocol
  |
  v
Application
```

Do not jump directly from:

```text
Application timeout
```

to:

```text
Security Group change
```

That creates unnecessary risk and often hides the actual root cause.

## Common Production Failure Patterns

The following failures occur frequently in production VPC environments.

| Failure | Primary investigation |
|---|---|
| No route to destination | Route tables |
| Private subnet cannot reach Internet | NAT Gateway and route tables |
| Public instance cannot reach Internet | Internet Gateway, public IP, routes, SG/NACL |
| AWS API unavailable from private subnet | VPC endpoint or NAT |
| Cross-VPC connectivity failure | Peering or Transit Gateway |
| On-premises connectivity failure | VPN, BGP, TGW, routes |
| DNS name fails | VPC DNS configuration and Route 53 |
| TCP timeout | Route, NACL, SG, return path |
| ALB cannot reach target | Target SG, route, NACL, target listener |
| Large packets fail | MTU, fragmentation, VPN path |
| Some connections fail randomly | Ephemeral ports, NACLs, asymmetric routing |
| Reachability succeeds but application fails | TCP/protocol/application layers |
| EKS service cannot communicate | VPC routing, CNI, SG, NetworkPolicy |
| PostgreSQL connection fails | Route, SG, NACL, listener, authentication |
| Redis connection fails | Route, SG, NACL, endpoint/listener |
| Kafka connectivity fails | DNS, routes, SG, listener advertisement |

## The Most Important Troubleshooting Rule

Always identify four things first:

```text
Source
Destination
Protocol
Port
```

For example:

```text
Source:
FastAPI EC2 instance

Destination:
PostgreSQL EC2 instance

Protocol:
TCP

Port:
5432
```

Then identify:

```text
Source VPC
Source subnet
Source ENI
Destination VPC
Destination subnet
Destination ENI
```

Without this information, network troubleshooting becomes guesswork.

## Failure: Missing or Incorrect Route

### What Happens

A route table determines where traffic matching a destination CIDR should go.

For example:

```text
Destination:
10.20.0.0/16

Target:
Transit Gateway
```

If the source subnet's route table does not contain a route covering the destination, the packet cannot follow the intended path.

### Typical Symptoms

- Connection timeout.
- `No route to host`.
- Cross-VPC service unavailable.
- Private subnet cannot access external resources.
- Application health checks fail.

### Example

```text
Application VPC
10.10.0.0/16

Database VPC
10.20.0.0/16
```

Required source route:

```text
10.20.0.0/16 -> Transit Gateway
```

Inspect routes:

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0 \
  --query 'RouteTables[].Routes[]'
```

Check:

- Destination CIDR.
- Target.
- Route state.
- Route-table association.
- More-specific routes.
- Blackhole routes.

### Production Pitfall

A route can exist but still be ineffective because the subnet is associated with a different route table.

Always verify:

```text
Subnet
  |
  v
Route Table Association
  |
  v
Expected Route
```

## Failure: Incorrect Route Precedence

AWS route selection follows the most specific matching route.

For example:

```text
10.0.0.0/8       -> Transit Gateway
10.20.0.0/16     -> VPC Peering
```

Traffic to:

```text
10.20.10.30
```

matches both routes, but the `/16` route is more specific.

This can produce unexpected paths when overlapping or highly specific routes are introduced.

### Troubleshooting

Look for:

- More-specific routes.
- Prefix list routes.
- Blackhole routes.
- Propagated routes.
- Static routes.

Do not inspect only the default route.

## Failure: Security Group Blocking Traffic

Security Groups are stateful virtual firewalls.

For:

```text
Application -> PostgreSQL:5432
```

the database Security Group must permit the intended inbound connection.

Example conceptual rule:

```text
Protocol: TCP
Port: 5432
Source: Application Security Group
```

Inspect:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0
```

### Preferred Production Pattern

Use workload-specific Security Groups:

```text
api-sg
   |
   | TCP 5432
   v
database-sg
```

rather than:

```text
database-sg
   |
   | TCP 5432
   v
0.0.0.0/0
```

### Common Mistake

Opening the destination port to the entire Internet simply because an application cannot connect.

This may restore connectivity while creating a serious security exposure.

First determine:

```text
Actual source
Expected port
Expected protocol
Expected trust boundary
```

## Failure: Network ACL Blocking Traffic

Network ACLs are stateless.

This distinction is critical.

Suppose:

```text
Client:
10.10.10.20:49152

Server:
10.20.10.30:5432
```

The initial request is:

```text
10.10.10.20:49152
        |
        v
10.20.10.30:5432
```

The response uses the client's ephemeral port:

```text
10.20.10.30:5432
        |
        v
10.10.10.20:49152
```

A restrictive NACL must permit both directions appropriately.

Inspect:

```bash
aws ec2 describe-network-acls \
  --filters \
    Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

### Common Production Failure

A team permits:

```text
TCP 5432
```

but forgets that return traffic may use an ephemeral destination port.

This can result in failed TCP connections even though the Security Group appears correct.

## Failure: Private Subnet Cannot Reach the Internet

A private subnet generally uses a NAT Gateway for outbound Internet access.

Expected path:

```text
Private EC2
    |
    v
Private Route Table
    |
    | 0.0.0.0/0
    v
NAT Gateway
    |
    v
Public Subnet
    |
    v
Internet Gateway
    |
    v
Internet
```

### Required Components

Check:

```text
Private subnet route
NAT Gateway
NAT Gateway subnet
Public subnet route
Internet Gateway
Elastic IP
Security Group
NACL
```

The private route table should contain:

```text
0.0.0.0/0 -> nat-xxxxxxxx
```

The NAT Gateway's subnet should have:

```text
0.0.0.0/0 -> igw-xxxxxxxx
```

### Common Mistake

Creating a NAT Gateway but forgetting the route from the private subnet.

A NAT Gateway does not automatically become the default route.

## Failure: NAT Gateway Is Unavailable

NAT Gateway problems can result from:

- Deleted NAT Gateway.
- Wrong route table.
- NAT Gateway in an unsuitable subnet.
- Incorrect Internet Gateway configuration.
- NACL restrictions.
- Exhausted or problematic source port behavior.
- Regional architecture problems.

Inspect:

```bash
aws ec2 describe-nat-gateways \
  --nat-gateway-ids nat-0123456789abcdef0
```

Check:

```text
State
Subnet
VPC
Connectivity
Route tables
CloudWatch metrics
```

### High Availability Recommendation

Do not make a single NAT Gateway a hidden regional dependency for all production workloads when availability requirements justify zonal redundancy.

A common architecture is:

```text
AZ-A Private Subnet -> NAT Gateway A -> IGW
AZ-B Private Subnet -> NAT Gateway B -> IGW
```

Each private subnet uses the NAT Gateway in its corresponding Availability Zone where practical.

This reduces dependence on a single Availability Zone.

## Failure: Public Subnet Cannot Reach the Internet

A subnet is not "public" merely because it is named public.

A public subnet normally has a route such as:

```text
0.0.0.0/0 -> Internet Gateway
```

and the workload must have appropriate public addressing.

Check:

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0 \
  --query 'RouteTables[].Routes[]'
```

Then inspect the instance:

```bash
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[].Instances[].{
    PrivateIp:PrivateIpAddress,
    PublicIp:PublicIpAddress,
    Subnet:SubnetId,
    Vpc:VpcId
  }'
```

A valid Internet Gateway route does not automatically provide a public IP.

## Failure: Internet Gateway Connectivity

For Internet-facing traffic, verify:

```text
Route Table
    |
    v
Internet Gateway
    |
    v
Public Addressing
    |
    v
Security Group
    |
    v
NACL
```

Typical mistakes include:

- Missing default route.
- Wrong route-table association.
- No public IPv4 address where required.
- Security Group denying traffic.
- NACL denying traffic.
- Destination service unavailable.

## Failure: VPC Endpoint Connectivity

Private workloads often access AWS services through VPC endpoints.

For example:

```text
Private EC2
    |
    v
VPC Endpoint
    |
    v
AWS Service
```

Instead of:

```text
Private EC2
    |
    v
NAT Gateway
    |
    v
Internet
    |
    v
AWS Service
```

Endpoint failures can be caused by:

- Incorrect endpoint configuration.
- Wrong endpoint policy.
- Security Group restrictions for interface endpoints.
- Incorrect private DNS configuration.
- Route table configuration for gateway endpoints.
- NACL restrictions.
- DNS resolution problems.

### Interface Endpoint

For interface endpoints, inspect:

```text
Endpoint ENI
Security Group
Private DNS
Subnet
NACL
```

### Gateway Endpoint

For gateway endpoints, inspect:

```text
Route table
Endpoint association
Endpoint policy
```

## Failure: VPC Peering Connectivity

VPC peering requires appropriate routes on both sides.

Example:

```text
VPC A
10.10.0.0/16
    |
    v
PCX
    |
    v
VPC B
10.20.0.0/16
```

Routes should conceptually be:

```text
VPC A:
10.20.0.0/16 -> pcx

VPC B:
10.10.0.0/16 -> pcx
```

Check:

- Peering connection state.
- Route tables.
- Security Groups.
- NACLs.
- CIDR overlap.
- Return path.

### Production Pitfall

A peering connection being `active` does not automatically mean workloads can communicate.

Peering is connectivity infrastructure, not an automatic routing configuration for every subnet.

## Failure: Transit Gateway Connectivity

Transit Gateway introduces another routing layer.

```text
VPC A
   |
   v
VPC Attachment
   |
   v
Transit Gateway
   |
   v
TGW Route Table
   |
   v
VPC B Attachment
   |
   v
VPC B
```

Failures may result from:

- Missing VPC route.
- Incorrect TGW route.
- Incorrect attachment association.
- Missing propagation.
- Blackhole route.
- Incorrect destination CIDR.
- Security Group restrictions.
- NACL restrictions.

Inspect routes:

```bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0 \
  --filters Name=type,Values=static,propagated
```

A common senior-level mistake is checking only the VPC route table and forgetting the Transit Gateway route table.

## Failure: VPN Connectivity

Hybrid connectivity has additional failure domains:

```text
AWS VPC
   |
   v
Transit Gateway / VGW
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

Potential causes:

- VPN tunnel down.
- Incorrect routes.
- BGP failure.
- Incorrect advertised prefixes.
- Missing return route.
- On-premises firewall.
- MTU issues.
- Security Group.
- NACL.

Always validate both:

```text
AWS -> On-Premises
On-Premises -> AWS
```

A working VPN tunnel does not automatically imply application-level connectivity.

## Failure: DNS Resolution

DNS failures can appear as network failures.

For example:

```bash
curl https://internal-api.example.com
```

may fail because:

```text
internal-api.example.com
```

does not resolve correctly.

Test DNS independently:

```bash
dig internal-api.example.com
```

Then test the resulting address:

```bash
nc -vz 10.20.10.30 443
```

Finally:

```bash
curl -v https://internal-api.example.com
```

This separates:

```text
DNS
```

from:

```text
TCP
```

from:

```text
TLS / HTTP
```

## Failure: ALB Cannot Reach Targets

A common architecture is:

```text
Client
  |
  v
Application Load Balancer
  |
  v
EC2 / ECS / EKS
```

The client-to-ALB path and ALB-to-target path are separate.

A common failure is:

```text
Client -> ALB       SUCCESS
ALB -> Target       FAILURE
```

Investigate:

- Target Security Group.
- ALB Security Group.
- Target port.
- Target listener.
- Target subnet.
- NACL.
- Route table.
- Health-check configuration.

Do not troubleshoot only the client-facing path.

## Failure: EKS Network Connectivity

EKS adds Kubernetes networking layers.

```text
Pod
 |
 v
VPC CNI
 |
 v
ENI
 |
 v
VPC
 |
 v
AWS Network
```

Possible failure points include:

- Security Group.
- Route table.
- NACL.
- Pod IP allocation.
- NetworkPolicy.
- DNS.
- Service configuration.
- Kubernetes CNI configuration.

A VPC-level path can be valid while a Kubernetes NetworkPolicy blocks the connection.

Conversely, a NetworkPolicy can be correct while the underlying AWS route is broken.

## Failure: PostgreSQL Connectivity

A backend application may report:

```text
connection timeout
```

Do not assume PostgreSQL itself is broken.

Troubleshoot:

```text
DNS
  |
  v
Route
  |
  v
Security Group
  |
  v
NACL
  |
  v
TCP 5432
  |
  v
PostgreSQL listener
  |
  v
Authentication
```

Test TCP:

```bash
nc -vz db.internal.example.com 5432
```

Test PostgreSQL readiness:

```bash
pg_isready \
  -h db.internal.example.com \
  -p 5432
```

If TCP succeeds but authentication fails, stop changing VPC configuration.

The failure has moved to the database/application layer.

## Failure: Redis Connectivity

For Redis:

```text
Application
    |
    v
Redis:6379
```

Check:

```text
DNS
Route
Security Group
NACL
Redis endpoint
TLS requirements
Authentication
```

For a private AWS-managed Redis deployment, verify the service's network placement and Security Group configuration rather than exposing Redis publicly.

## Failure: Kafka Connectivity

Kafka introduces a particularly important distinction:

```text
Client -> Bootstrap Broker
```

does not necessarily mean:

```text
Client -> Every Advertised Broker
```

A client may successfully connect to the bootstrap endpoint and then fail when connecting to broker addresses returned by Kafka metadata.

Investigate:

- DNS.
- Security Groups.
- Route tables.
- NACLs.
- Broker listener configuration.
- Advertised addresses.
- Cross-VPC connectivity.
- Transit Gateway or peering.
- TLS configuration.

A network engineer should validate every broker endpoint that clients are expected to reach.

## Failure: gRPC Connectivity

For gRPC:

```text
Service A
    |
    | TCP 443
    v
Service B
```

Network success does not prove:

```text
TLS success
```

or:

```text
HTTP/2 success
```

or:

```text
gRPC method success
```

Test progressively:

```text
DNS
  |
  v
TCP
  |
  v
TLS
  |
  v
HTTP/2
  |
  v
gRPC
```

## Failure: Reachability Analyzer Says Reachable

This is an important production scenario.

Suppose:

```text
Reachability Analyzer:
Reachable

Application:
Timeout
```

Do not conclude that the tool is wrong.

Investigate layers above network configuration:

```text
Flow Logs
TCP test
DNS
TLS
Application listener
Application logs
Remote firewall
Protocol configuration
```

For example:

```text
Reachability:
SUCCESS

nc:
SUCCESS

curl:
FAILURE

Conclusion:
Network path works.
Investigate TLS / HTTP / application.
```

## Failure: Reachability Analyzer Says Unreachable

When analysis reports a blocking component:

```text
Source
  |
  v
Route
  |
  v
NACL
  X
Destination
```

inspect the identified component directly.

Do not blindly modify multiple resources.

Use:

```text
Analysis
  |
  v
Identify blocker
  |
  v
Inspect configuration
  |
  v
Make minimal change
  |
  v
Re-run analysis
  |
  v
Test workload
```

## Failure: Asymmetric Routing

Asymmetric routing occurs when the forward and return paths differ.

Example:

```text
Forward:
VPC A -> Transit Gateway -> VPC B

Return:
VPC B -> VPN -> On-Premises -> VPC A
```

This can cause problems with stateful network devices.

During troubleshooting, explicitly map:

```text
Forward path
Return path
```

Do not assume the return path is symmetrical.

## Failure: MTU and Fragmentation

MTU problems are less obvious than simple routing failures.

Symptoms may include:

- Small requests work.
- Large responses fail.
- TLS connections behave inconsistently.
- gRPC streams fail.
- VPN traffic behaves differently from local VPC traffic.
- Some HTTP requests hang.

This can occur when different network paths have different MTU characteristics.

For example:

```text
Application
    |
    v
VPC
    |
    v
VPN
    |
    v
On-Premises
```

The VPN path may impose different packet-size constraints than direct VPC communication.

When basic routing and firewall checks pass but larger payloads fail, investigate MTU and fragmentation.

## Failure: Ephemeral Port Restrictions

Clients typically use ephemeral source ports.

Example:

```text
Client:
10.10.10.20:49152

Server:
10.20.10.30:5432
```

The response is sent toward:

```text
10.10.10.20:49152
```

A restrictive NACL that only permits destination port `5432` can incorrectly block the return traffic.

This is one of the most common NACL-related production mistakes.

## Failure: Blackhole Routes

A route can exist while its target is unavailable.

Examples include routes associated with resources that have been deleted or become invalid.

Transit Gateway can also contain blackhole routes.

Inspect route state rather than checking only whether a route entry exists.

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0 \
  --query 'RouteTables[].Routes[].{
    Destination:DestinationCidrBlock,
    GatewayId:GatewayId,
    TransitGatewayId:TransitGatewayId,
    NatGatewayId:NatGatewayId,
    State:State
  }'
```

A route with an unexpected `blackhole` state requires investigation.

## Failure: Wrong Route Table Association

One of the easiest mistakes to miss is assuming a subnet uses a particular route table.

Verify:

```text
Subnet
   |
   v
Route Table Association
   |
   v
Actual Route Table
```

Inspect subnet associations:

```bash
aws ec2 describe-route-tables \
  --filters Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

Do not diagnose routing using a route table that is not actually associated with the affected subnet.

## Failure: CIDR Overlap

Overlapping CIDRs can prevent or complicate connectivity between networks.

Example:

```text
VPC A:
10.0.0.0/16

VPC B:
10.0.0.0/16
```

Both networks use the same address space.

This creates fundamental routing ambiguity for direct connectivity architectures.

Avoid CIDR overlap when designing:

- VPC peering.
- Transit Gateway architectures.
- Hybrid VPN connectivity.
- Multi-account networking.
- Multi-region networks.

CIDR planning is therefore an architectural concern, not merely a subnetting detail.

## Failure: Incorrect Security Group References

Security Group references are useful for workload-to-workload communication.

For example:

```text
api-sg
   |
   | TCP 5432
   v
db-sg
```

However, Security Group references have scope and architecture constraints.

When traffic crosses networking boundaries such as VPC peering or Transit Gateway, verify that the intended Security Group referencing behavior is supported for the architecture.

Do not assume:

```text
source SG reference
```

works identically across every AWS networking topology.

## Failure: Default Route Removed

A surprisingly common production incident is accidental removal or replacement of:

```text
0.0.0.0/0
```

from a route table.

This can break:

- NAT access.
- Internet access.
- Package downloads.
- External API calls.
- Container image pulls.
- Monitoring agents.
- Dependency access.

Infrastructure-as-code and change review should protect critical routes from accidental modification.

## Failure: VPC DNS Configuration

VPC DNS behavior depends on VPC-level DNS settings and the resolver architecture.

If workloads cannot resolve internal names, inspect:

- `enableDnsSupport`.
- `enableDnsHostnames`.
- Route 53 private hosted zones.
- Resolver rules.
- Resolver endpoints.
- DHCP options where relevant.
- Security controls around DNS traffic.

Inspect VPC attributes:

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --attribute enableDnsSupport
```

And:

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --attribute enableDnsHostnames
```

## Failure: VPC Flow Logs Misinterpreted

Flow Logs are extremely useful but have limitations.

They provide network flow metadata rather than application payloads.

A flow record can help determine:

```text
Source
Destination
Port
Protocol
Action
Bytes
Packets
```

It cannot tell you:

```text
HTTP request body
SQL query
gRPC method
TLS payload
```

A flow log `ACCEPT` does not mean the application succeeded.

A flow log `REJECT` is strong evidence that traffic was rejected by the relevant network control, but it still requires correlation with the architecture and timestamps.

## Failure: No Return Traffic

A common debugging pattern is:

```text
Client -> Server
```

with no response.

Possible causes include:

- Server Security Group.
- Server NACL.
- Return route.
- Server application not listening.
- Intermediate firewall.
- Asymmetric routing.

Use Flow Logs and application-level tests to determine whether:

```text
SYN
```

was observed and whether:

```text
SYN-ACK
```

returned.

## Failure: Load Balancer Health Checks Fail

Health checks can fail even when the application appears reachable from another location.

For example:

```text
Developer laptop -> Application: SUCCESS
ALB -> Application: FAILURE
```

The source networks are different.

The ALB's Security Group and subnet path must be considered.

Check:

```text
ALB subnet
Target subnet
ALB Security Group
Target Security Group
NACL
Target listener
Health-check path
```

Never use a successful developer request as proof that the ALB path is correct.

## Failure: Container Workload Cannot Reach Dependency

For Docker or ECS workloads:

```text
Container
   |
   v
Task ENI
   |
   v
VPC
   |
   v
Dependency
```

Check the actual task ENI and Security Group.

Do not assume the EC2 host's network configuration completely represents the task's network identity when using `awsvpc` networking.

## Failure: CI/CD Deployment Breaks Network Access

A deployment may introduce network failures indirectly.

Examples:

- New subnet.
- New route table.
- New Security Group.
- New VPC endpoint.
- Changed NAT route.
- Changed DNS configuration.
- Changed EKS node group.
- Changed ECS task networking.

A deployment pipeline should therefore validate infrastructure changes, not only application tests.

A useful deployment flow is:

```text
Code Change
    |
    v
Unit Tests
    |
    v
Infrastructure Validation
    |
    v
Deployment
    |
    v
Network Smoke Tests
    |
    v
Application Smoke Tests
```

## Systematic Troubleshooting Workflow

Use the following sequence for production incidents.

### Identify the Failure

Record:

```text
Source
Destination
Protocol
Port
Timestamp
Availability Zone
VPC
Subnet
Workload
```

### Validate DNS

```bash
dig service.internal.example.com
```

If DNS fails, resolve that layer before assuming routing is broken.

### Validate the Network Path

Use Reachability Analyzer when the source and destination are supported.

Determine:

```text
Reachable
```

or:

```text
Blocked
```

### Inspect Routing

Check:

```text
Source route table
Destination route table
TGW routes
Peering routes
NAT routes
Internet Gateway routes
Endpoint routes
```

### Inspect Security Controls

Check:

```text
Security Groups
Network ACLs
Endpoint policies
NetworkPolicies where applicable
```

### Inspect Runtime Traffic

Use VPC Flow Logs to determine whether traffic was observed and whether it was accepted or rejected.

### Test from the Actual Workload

Examples:

```bash
nc -vz db.internal.example.com 5432
```

```bash
curl -v https://api.internal.example.com
```

```bash
pg_isready -h db.internal.example.com -p 5432
```

### Validate the Destination

Check:

```text
Listening socket
Service health
Application logs
Authentication
Protocol
TLS
```

### Validate External Networks

If traffic leaves the VPC:

```text
VPN
Direct Connect
Internet
External firewall
Remote service
```

must also be considered.

## Diagnostic Flow

```mermaid
flowchart TD
    Start[Connectivity Failure]
    Identify[Identify Source Destination Protocol Port]
    DNS{DNS Works?}
    Reach[Run Reachability Analysis]
    Path{AWS Path Reachable?}
    Route[Inspect Routes]
    SG[Inspect Security Groups]
    NACL[Inspect NACLs]
    Flow[Inspect VPC Flow Logs]
    TCP[Test TCP Connectivity]
    App[Test Protocol/Application]
    External[Inspect External Network]

    Start --> Identify
    Identify --> DNS
    DNS -->|No| DNSFix[Fix DNS]
    DNS -->|Yes| Reach
    Reach --> Path
    Path -->|No| Route
    Route --> SG
    SG --> NACL
    NACL --> Flow
    Path -->|Yes| Flow
    Flow --> TCP
    TCP --> App
    App --> External
```

## Production Troubleshooting Checklist

```text
[ ] Identify source workload
[ ] Identify destination workload
[ ] Identify source ENI
[ ] Identify destination ENI
[ ] Identify source subnet
[ ] Identify destination subnet
[ ] Identify source VPC
[ ] Identify destination VPC
[ ] Identify protocol
[ ] Identify destination port
[ ] Validate DNS
[ ] Validate source route table
[ ] Validate destination route table
[ ] Check route precedence
[ ] Check blackhole routes
[ ] Check NAT Gateway if applicable
[ ] Check Internet Gateway if applicable
[ ] Check VPC endpoint if applicable
[ ] Check VPC peering if applicable
[ ] Check Transit Gateway if applicable
[ ] Check VPN if applicable
[ ] Check Security Groups
[ ] Check Network ACLs
[ ] Check return path
[ ] Check VPC Flow Logs
[ ] Run TCP connectivity test
[ ] Run protocol-specific test
[ ] Check destination listener
[ ] Check application logs
[ ] Check Kubernetes NetworkPolicy if applicable
[ ] Check external firewall if applicable
[ ] Check MTU if symptoms indicate fragmentation
[ ] Check recent infrastructure changes
[ ] Apply minimal remediation
[ ] Re-run diagnostics
[ ] Validate from the actual workload
[ ] Document root cause
[ ] Document preventive control
```

## Common Mistakes

### Opening `0.0.0.0/0` to Fix a Connectivity Problem

This can hide the actual cause while creating an unnecessary security exposure.

Find the real source and required port instead.

### Checking Only Security Groups

A Security Group cannot compensate for:

- Missing route.
- Incorrect TGW route.
- Broken peering route.
- NACL denial.
- DNS failure.
- Missing NAT Gateway.
- Broken VPN.

### Checking Only the Forward Path

Always investigate the return path.

### Assuming "Private Subnet" Means "No Internet"

Private subnets can access the Internet through NAT Gateways.

The key distinction is whether the subnet has a direct route to an Internet Gateway versus using NAT for outbound access.

### Assuming a Route Table Is Global to the VPC

Route tables are associated with subnets.

Different subnets can use different routing behavior.

### Ignoring NACL Statelessness

Security Groups are stateful; NACLs are stateless.

This difference is fundamental during troubleshooting.

### Ignoring DNS

A DNS failure can look exactly like a service outage from the application's perspective.

### Treating AWS Network Reachability as Application Health

A valid network path does not prove:

```text
TLS
HTTP
gRPC
PostgreSQL
Redis
Kafka
```

will work.

### Changing Multiple Network Controls Simultaneously

Changing the route, Security Group, NACL, and endpoint simultaneously destroys the ability to identify which change fixed the issue.

Make the smallest justified change.

## Senior-Level Diagnostic Principles

### Separate Control Plane From Data Plane

AWS configuration describes the intended network.

Runtime telemetry shows what actually happened.

Think in terms of:

```text
Control Plane
    |
    +--> Route configuration
    +--> Security Groups
    +--> NACLs
    +--> TGW configuration
    +--> Endpoint configuration

Data Plane
    |
    +--> Actual packets
    +--> Flow Logs
    +--> TCP behavior
    +--> Application traffic
```

Both are required for reliable diagnosis.

### Establish Evidence Before Making Changes

A production incident should follow:

```text
Observe
  |
  v
Measure
  |
  v
Hypothesize
  |
  v
Validate
  |
  v
Change
  |
  v
Verify
```

Not:

```text
Guess
  |
  v
Change
  |
  v
Hope
```

### Diagnose the Smallest Failure Domain

If:

```text
nc -> SUCCESS
```

there is little value in continuing to modify VPC routing.

Move upward:

```text
TLS
Protocol
Application
Authentication
```

Likewise, if Reachability Analyzer identifies a missing route, do not start debugging application code.

## Security Considerations

Production VPC troubleshooting often requires broad visibility into network infrastructure.

Use separate permissions for:

```text
Network observation
```

and:

```text
Network modification
```

Prefer least-privilege IAM.

Avoid granting incident responders unrestricted ability to modify:

- Route tables.
- Security Groups.
- NACLs.
- Transit Gateway routes.
- VPN configuration.

Diagnostic access should not automatically imply administrative access.

Protect flow logs and network topology information because they reveal infrastructure structure and communication patterns.

## Reliability and High Availability

A production VPC should avoid unnecessary single points of failure.

Consider:

```text
Multi-AZ subnets
Multi-AZ NAT architecture
Redundant application paths
Redundant VPN tunnels
Transit Gateway design
Multiple load balancer subnets
Endpoint redundancy
```

For critical dependencies, explicitly document:

```text
Primary path
Failure path
Expected failover behavior
```

A network architecture is only highly available if the applications can continue communicating with their dependencies after an infrastructure failure.

## Monitoring Considerations

Use multiple observability layers.

| Layer | Examples |
|---|---|
| DNS | Route 53, resolver telemetry |
| Network configuration | Reachability Analyzer, AWS CLI |
| Traffic | VPC Flow Logs |
| NAT | CloudWatch NAT Gateway metrics |
| VPN | Tunnel and tunnel-health metrics |
| TGW | Transit Gateway metrics |
| Load Balancer | ALB/NLB metrics |
| Application | Application metrics and logs |
| Kubernetes | CNI, NetworkPolicy, pod metrics |
| Database | PostgreSQL metrics and logs |

The strongest production setup correlates these layers rather than depending on a single monitoring signal.

## Cost Considerations

Network failures can also create unexpected AWS costs.

Examples include:

- Excessive NAT Gateway usage.
- Cross-AZ traffic.
- Cross-region traffic.
- Unnecessary Internet egress.
- Excessive Flow Log ingestion.
- Excessive CloudWatch retention.
- Incorrect routing through centralized inspection infrastructure.

When troubleshooting recurring network architecture problems, investigate both:

```text
Reliability
```

and:

```text
Cost
```

A technically functional network can still be poorly designed.

## Disaster Recovery Considerations

DR environments must have independently validated network paths.

Verify:

```text
VPC CIDRs
Route tables
TGW attachments
VPN connectivity
VPC endpoints
DNS
Security Groups
NACLs
Application dependencies
```

Do not assume:

```text
Primary VPC configuration
=
DR VPC configuration
```

Perform connectivity validation before a disaster occurs.

## Interview Traps

### "Security Groups Are the First Thing to Check"

Not always.

First identify:

```text
DNS
Route
Network path
NACL
Security Group
Application
```

### "NACLs Are Stateful"

Incorrect.

Network ACLs are stateless.

### "Security Groups Apply to Subnets"

Incorrect.

Security Groups are associated with network interfaces/resources, while NACLs operate at the subnet boundary.

### "A NAT Gateway Provides Internet Access Automatically"

Incorrect.

The private subnet route table must point traffic to the NAT Gateway, and the NAT Gateway must have the appropriate public-side path.

### "A Public Subnet Automatically Gives Instances Public IPs"

Incorrect.

Public routing and public addressing are separate concerns.

### "A Transit Gateway Automatically Connects All VPCs"

Incorrect.

Attachments, route tables, associations, propagation, and routes must be correctly configured.

### "VPC Peering Creates Routes Automatically"

Incorrect.

Appropriate routes must exist on both sides.

### "Flow Logs Prove the Application Worked"

Incorrect.

Flow Logs provide network flow metadata, not application success.

### "Reachability Analyzer Replaces Runtime Testing"

Incorrect.

It validates network configuration; workload-level tests validate actual runtime behavior.

## Recommended Production Operating Model

Treat VPC networking as production infrastructure with the same engineering discipline applied to application code.

Maintain:

```text
Infrastructure as Code
        |
        v
Peer-reviewed changes
        |
        v
Automated validation
        |
        v
Controlled deployment
        |
        v
Network smoke tests
        |
        v
Continuous observability
```

Document critical communication paths.

For example:

| Source | Destination | Protocol | Port | Network Path |
|---|---|---:|---:|---|
| API | PostgreSQL | TCP | 5432 | Private VPC |
| API | Redis | TCP | 6379 | Private VPC |
| Worker | Kafka | TCP | 9092/appropriate listener | TGW |
| Private EC2 | S3 | HTTPS | 443 | VPC Endpoint |
| Private EC2 | External API | HTTPS | 443 | NAT Gateway |
| VPC A | VPC B | TCP | Application-specific | TGW/Peering |
| AWS | On-premises | Application-specific | Application-specific | VPN/DX |

This turns troubleshooting from an ad-hoc activity into an operational process.

## Key Takeaways

- **Most production VPC failures occur at the interaction between routing, network controls, and network path components**, so troubleshoot the complete path rather than a single Security Group.
- **Always establish source, destination, protocol, and port first**, then validate DNS, routing, network controls, runtime traffic, and the application in that order.
- **NACLs are stateless while Security Groups are stateful**, making return traffic and ephemeral ports especially important when diagnosing NACL-related failures.
- **Complex architectures require end-to-end path analysis** across NAT Gateways, VPC endpoints, peering, Transit Gateway, VPN, load balancers, Kubernetes networking, and hybrid networks.
- **Production troubleshooting should be evidence-driven**: observe, measure, validate the hypothesis, make the smallest justified change, verify the result, and document the root cause.