# 10- VPC Peering Connectivity Issues

## Overview

VPC peering provides private network connectivity between two VPCs using private IP addresses. It is commonly used when workloads in separate VPCs, AWS accounts, or Regions need direct network communication without traversing the public internet.

A peering connection by itself does **not** make the VPCs reachable. Connectivity depends on several independent components:

- The VPC peering connection must be active.
- The source subnet route table must contain a route to the peer CIDR.
- The destination subnet route table must contain a return route.
- Security Groups must permit the traffic.
- Network ACLs must permit the traffic.
- The CIDR ranges must not overlap.
- DNS behavior must be configured correctly when hostnames are used.
- The target service must actually listen on the requested port.
- Cross-Region and cross-account prerequisites must be satisfied.

The most common troubleshooting mistake is treating:

```text
VPC Peering = Connectivity
```

as if it were true.

The correct mental model is:

```text
Peering Connection
       +
Source Route
       +
Destination Route
       +
Security Groups
       +
Network ACLs
       +
Application Listener
       =
End-to-End Connectivity
```

## VPC Peering Architecture

Consider two VPCs:

```text
VPC A
10.10.0.0/16
    |
    | VPC Peering
    |
VPC B
10.20.0.0/16
```

A workload in VPC A:

```text
10.10.1.20
```

needs to reach a PostgreSQL database in VPC B:

```text
10.20.2.30:5432
```

The traffic flow is:

```mermaid
flowchart LR
    App[Application<br/>10.10.1.20]
    RouteA[Route Table A<br/>10.20.0.0/16]
    Peer[VPC Peering]
    RouteB[Route Table B<br/>10.10.0.0/16]
    SG[Database Security Group]
    DB[(PostgreSQL<br/>10.20.2.30:5432)]

    App --> RouteA
    RouteA --> Peer
    Peer --> RouteB
    RouteB --> SG
    SG --> DB
```

Every layer must agree that the traffic is valid.

## How VPC Peering Works

A VPC peering connection creates a private networking relationship between two VPCs.

It can connect:

- VPCs in the same AWS account.
- VPCs in different AWS accounts.
- VPCs in different AWS Regions.

Traffic remains on the AWS network rather than being routed through the public internet.

However, peering does not automatically modify existing route tables.

For example:

```text
VPC A
10.10.0.0/16

VPC B
10.20.0.0/16
```

A route must explicitly direct traffic toward the peer:

```text
Destination: 10.20.0.0/16
Target:      pcx-0123456789abcdef0
```

The return direction also requires a route:

```text
Destination: 10.10.0.0/16
Target:      pcx-0123456789abcdef0
```

## Peering Connection States

Inspect the peering connection:

```bash
aws ec2 describe-vpc-peering-connections \
  --vpc-peering-connection-ids pcx-0123456789abcdef0
```

The connection must be in an appropriate active state before traffic can flow.

Typical lifecycle:

```text
pending-acceptance
        |
        v
      active
        |
        v
   provisioning
        |
        v
      deleted
```

For cross-account peering, the requester creates the connection and the accepter must explicitly accept it.

For cross-Region peering, the Region of each VPC must be considered when inspecting and managing the connection.

## First Troubleshooting Principle

When VPC peering connectivity fails, troubleshoot from the source workload outward:

```text
Application
    |
    v
DNS
    |
    v
Destination IP
    |
    v
Source Route Table
    |
    v
VPC Peering
    |
    v
Destination Route Table
    |
    v
Security Group
    |
    v
Network ACL
    |
    v
Target Listener
    |
    v
Application
```

This prevents unrelated layers from being changed unnecessarily.

## CIDR Overlap

VPC peering requires non-overlapping IPv4 CIDR ranges.

For example:

```text
VPC A: 10.10.0.0/16
VPC B: 10.20.0.0/16
```

is valid.

But:

```text
VPC A: 10.10.0.0/16
VPC B: 10.10.0.0/16
```

creates an overlapping address space and cannot be used for standard VPC peering.

Another subtle example:

```text
VPC A: 10.10.0.0/16
VPC B: 10.10.20.0/24
```

also overlaps because the `/24` lies inside the `/16`.

Before designing peering, inspect the CIDRs:

```bash
aws ec2 describe-vpcs \
  --vpc-ids vpc-aaaaaaaaaaaaaaaaa vpc-bbbbbbbbbbbbbbbbb \
  --query 'Vpcs[].{VpcId:VpcId,Cidr:CidrBlock}'
```

For large organizations, CIDR planning should happen before VPC creation rather than being solved after the environment has grown.

## Route Table Requirements

This is the most common VPC peering connectivity failure.

Suppose:

```text
VPC A = 10.10.0.0/16
VPC B = 10.20.0.0/16
```

A workload in VPC A needs to reach:

```text
10.20.2.30
```

The source subnet's route table must contain:

```text
Destination       Target
10.20.0.0/16      pcx-...
```

The destination subnet's route table must contain the reverse route:

```text
Destination       Target
10.10.0.0/16      pcx-...
```

The route is not automatically added when the peering connection becomes active.

## Inspect Route Tables

List route tables:

```bash
aws ec2 describe-route-tables
```

Inspect routes for a specific route table:

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0
```

A useful filtered query:

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0 \
  --query 'RouteTables[].Routes[]'
```

Verify:

- Destination CIDR.
- Target.
- Route state.
- Associated subnet.
- Correct VPC.

## Route Table Association Matters

A common mistake is adding the correct route to the wrong route table.

For example:

```text
Route Table A
    |
    +--> Peering route exists

Subnet A-1
    |
    +--> Route Table A

Subnet A-2
    |
    +--> Route Table A-2
          |
          X
          No peering route
```

An EC2 instance in subnet A-2 will not use the route from Route Table A.

Always verify the route table associated with the **actual source subnet**.

Inspect subnet associations:

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0 \
  --query 'RouteTables[].Associations'
```

## Destination Route Table

The reverse route is equally important.

For:

```text
10.10.1.20 -> 10.20.2.30:5432
```

the return traffic must have a path:

```text
10.20.2.30
     |
     v
Destination Route Table
     |
     v
10.10.0.0/16 -> pcx-...
     |
     v
VPC A
```

If the destination subnet has no route back to VPC A, the connection can fail even though the source route is correct.

This is especially easy to miss when the destination is:

- RDS.
- EC2.
- Internal load balancer.
- ECS task.
- EKS node.
- Private service.

## Route Precedence

AWS routing uses the most specific matching route.

Consider:

```text
10.20.0.0/16 -> pcx-...
10.20.2.0/24 -> local
```

Traffic to:

```text
10.20.2.30
```

matches the more specific `/24` route.

This can produce unexpected behavior when multiple routes exist.

When troubleshooting, inspect all relevant routes rather than checking only whether a peering route exists.

## Local Route vs Peering Route

Every VPC route table contains a local route for the VPC's own CIDR.

Example:

```text
10.10.0.0/16 -> local
```

This route cannot simply be replaced with a peering route to reach another VPC with the same CIDR.

This is another reason overlapping CIDRs are fundamentally incompatible with normal VPC peering.

## Security Group Requirements

Security Groups are stateful firewalls attached to resources such as:

- EC2 instances.
- ENIs.
- RDS instances.
- Load balancers.
- ECS tasks.

Suppose VPC A contains an application and VPC B contains PostgreSQL.

The database Security Group might need:

```text
Type: PostgreSQL
Protocol: TCP
Port: 5432
Source: 10.10.0.0/16
```

Example:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0
```

Do not assume that establishing the peering connection automatically bypasses Security Groups.

It does not.

## Security Group Referencing Across Peering

Security Group references can be used in supported VPC peering scenarios, but operational behavior depends on the peering architecture and Region configuration.

When troubleshooting, verify whether the rule uses:

```text
Security Group ID
```

or:

```text
CIDR
```

For cross-account or cross-Region designs, CIDR-based rules may be easier to reason about operationally, but the security model should still follow least privilege.

Avoid broad rules such as:

```text
0.0.0.0/0
```

when the actual dependency is:

```text
10.10.0.0/16
```

## Network ACL Requirements

Network ACLs are stateless.

If VPC peering traffic is allowed in one direction, the return path must also be allowed.

For example:

```text
Application
10.10.1.20:45000
        |
        | TCP 5432
        v
Database
10.20.2.30:5432
        |
        | TCP 45000
        v
Application
```

A restrictive NACL must permit the relevant traffic in both directions.

Inspect NACLs:

```bash
aws ec2 describe-network-acls
```

Look for:

- Inbound rules.
- Outbound rules.
- Rule numbers.
- Allow/deny behavior.
- Subnet associations.

## Stateful vs Stateless Filtering

| Component | Stateful | Return Traffic Automatically Allowed |
|---|---:|---:|
| Security Group | Yes | Yes |
| Network ACL | No | No |
| VPC Route Table | N/A | N/A |
| VPC Peering | N/A | N/A |

This distinction is critical during troubleshooting.

If a Security Group permits:

```text
TCP 5432 from 10.10.0.0/16
```

the return traffic is handled by the stateful firewall.

A NACL requires explicit consideration of the return path.

## DNS Across VPC Peering

VPC peering provides network connectivity, not automatic DNS name resolution for arbitrary private names.

A service might be reachable by IP:

```text
10.20.2.30:5432
```

while its expected hostname:

```text
db.internal.example.com
```

does not resolve from VPC A.

If DNS is part of the architecture, verify:

- Private hosted zone associations.
- Route 53 Resolver behavior.
- DNS resolution settings.
- Cross-VPC DNS configuration.
- Service discovery.

Test from the source workload:

```bash
dig db.internal.example.com
```

Then compare:

```bash
dig +short db.internal.example.com
```

with the expected destination.

## VPC Peering Is Not Transitive

This is one of the most important VPC peering concepts.

Suppose:

```text
VPC A <----> VPC B <----> VPC C
```

VPC peering does **not** automatically allow:

```text
VPC A ----> VPC B ----> VPC C
```

The network path is not transitively routed through VPC B.

This architecture:

```mermaid
flowchart LR
    A[VPC A]
    B[VPC B]
    C[VPC C]

    A <--> B
    B <--> C

    A -.->|No automatic transit| C
```

does not provide A-to-C connectivity.

For larger topologies, consider:

- AWS Transit Gateway.
- AWS Cloud WAN.
- Carefully designed routing architectures.

Do not create increasingly complex peering meshes to simulate a transit network.

## Full Mesh Complexity

With `N` VPCs, a full mesh can require:

```text
N × (N - 1) / 2
```

peering relationships.

Examples:

| VPCs | Potential Peering Connections |
|---:|---:|
| 2 | 1 |
| 3 | 3 |
| 5 | 10 |
| 10 | 45 |
| 20 | 190 |
| 50 | 1,225 |

The operational burden grows quickly.

For a small number of VPCs, direct peering may be appropriate.

For large environments, centralized connectivity is usually easier to operate.

## Cross-Account Peering

Cross-account peering introduces another operational boundary.

Typical flow:

```text
Account A
   |
   | Create peering request
   v
Account B
   |
   | Accept request
   v
Active Peering
```

Verify:

- Requester VPC ID.
- Accepter VPC ID.
- AWS account IDs.
- Regions.
- Peering state.
- Route tables on both sides.
- Security policies on both sides.

A peering request remaining in:

```text
pending-acceptance
```

is not a routing problem.

The connection must first be accepted.

## Cross-Region Peering

Cross-Region peering allows private connectivity between VPCs in different AWS Regions.

Example:

```text
us-east-1
VPC A
10.10.0.0/16
     |
     | VPC Peering
     |
us-west-2
VPC B
10.20.0.0/16
```

When troubleshooting, verify the Region of each VPC and inspect the peering connection from the correct AWS Region context.

Useful commands include:

```bash
aws ec2 describe-vpcs \
  --region us-east-1 \
  --vpc-ids vpc-aaaaaaaaaaaaaaaaa
```

and:

```bash
aws ec2 describe-vpcs \
  --region us-west-2 \
  --vpc-ids vpc-bbbbbbbbbbbbbbbbb
```

Cross-Region connectivity also introduces:

- Inter-Region latency.
- Regional failure considerations.
- Cross-Region data transfer costs.
- Region-specific service behavior.

## IPv6 Considerations

Do not assume that IPv4 and IPv6 peering behavior are identical.

If the application uses IPv6, verify:

- IPv6 CIDR blocks.
- IPv6 routes.
- Security Group IPv6 rules.
- NACL IPv6 rules.
- Application listener.
- DNS `AAAA` records.

Test address families separately where appropriate:

```bash
curl -4 https://service.internal.example.com
curl -6 https://service.internal.example.com
```

A working IPv4 path does not prove that the IPv6 path is configured correctly.

## Application Listener Verification

If DNS, routes, and firewall rules are correct, verify that the destination service is actually listening.

From the destination host:

```bash
ss -lntp
```

For PostgreSQL:

```bash
ss -lntp | grep 5432
```

For an HTTP service:

```bash
ss -lntp | grep 8080
```

A common failure pattern is:

```text
VPC peering:      active
Route:            correct
Security Group:   correct
NACL:             correct
Application:      not listening
```

Do not continue changing network configuration when the actual problem is an application listener.

## Connectivity Testing

### Test DNS

```bash
getent hosts db.internal.example.com
```

### Test TCP

```bash
nc -vz db.internal.example.com 5432
```

### Test PostgreSQL

```bash
psql \
  "host=db.internal.example.com port=5432 dbname=application user=app_user sslmode=require"
```

### Test HTTPS

```bash
curl -v https://api.internal.example.com
```

These tests progressively validate more layers.

## Layered Connectivity Model

| Layer | Test | Failure Suggests |
|---|---|---|
| DNS | `dig`, `getent` | DNS/configuration |
| IP reachability | Reachability Analyzer | AWS network path |
| TCP | `nc` | Routing/SG/NACL/listener |
| TLS | `curl -v` | TLS/certificate |
| Database | `psql` | DB configuration/auth |
| HTTP | `curl` | Application/load balancer |
| gRPC | `grpcurl` | Service/listener/TLS/application |

For gRPC:

```bash
grpcurl \
  -vv \
  api.internal.example.com:443 \
  list
```

Use the appropriate command for the protocol rather than relying on ICMP.

## VPC Reachability Analyzer

AWS VPC Reachability Analyzer is useful for determining whether a network path exists between AWS resources.

It can help analyze paths involving:

- EC2 instances.
- ENIs.
- Load balancers.
- NAT gateways.
- Internet gateways.
- VPC peering.
- Transit gateways.
- Route tables.
- Security Groups.
- Network ACLs.

The important benefit is that it evaluates the configured AWS network path rather than relying exclusively on manual inspection.

When the path is reported as unreachable, inspect the component identified by the analysis before modifying unrelated infrastructure.

## Flow Logs

VPC Flow Logs can help determine whether traffic is reaching network interfaces and whether it is being accepted or rejected.

Enable them according to your operational and security requirements.

Useful information includes:

```text
source address
destination address
source port
destination port
protocol
action
```

A rejected flow can indicate:

- Security Group behavior.
- NACL behavior.
- Other network configuration issues.

Flow Logs should complement, not replace, route and firewall analysis.

## Route Table Troubleshooting Example

Consider:

```text
VPC A
10.10.0.0/16

Application:
10.10.1.20

VPC B
10.20.0.0/16

Database:
10.20.2.30:5432
```

The application cannot connect.

### Step 1: Check Peering

```bash
aws ec2 describe-vpc-peering-connections \
  --vpc-peering-connection-ids pcx-0123456789abcdef0
```

Confirm the connection is active.

### Step 2: Check Source Route

```text
10.20.0.0/16 -> pcx-...
```

must exist in the route table associated with the application subnet.

### Step 3: Check Destination Route

```text
10.10.0.0/16 -> pcx-...
```

must exist in the route table associated with the database subnet.

### Step 4: Check Security Group

The database Security Group must allow:

```text
TCP 5432
Source: 10.10.0.0/16
```

or an appropriately scoped source.

### Step 5: Check NACL

Ensure the subnet NACLs permit the required traffic and return traffic.

### Step 6: Test TCP

```bash
nc -vz 10.20.2.30 5432
```

### Step 7: Check PostgreSQL

If TCP works but the database connection fails, inspect:

- PostgreSQL listener.
- Authentication.
- Database user.
- SSL configuration.
- PostgreSQL access controls.
- Application credentials.

At this point, continuing to modify VPC routes is unlikely to solve the problem.

## Common Failure Patterns

| Symptom | Likely Cause |
|---|---|
| Peering stuck in pending state | Accepter has not accepted request |
| Peering active but no connectivity | Missing route |
| One subnet works, another fails | Wrong route-table association |
| One direction works, return traffic fails | Missing reverse route |
| Timeout | Route, SG, NACL, or listener |
| Connection refused | Destination reachable but application not listening |
| DNS fails | Hosted zone/resolver configuration |
| IP works but hostname fails | DNS problem |
| A-to-B works but A-to-C through B fails | Non-transitive peering |
| Cross-account fails | Incorrect account/acceptance configuration |
| IPv4 works, IPv6 fails | IPv6 route/firewall/listener |
| Peering is active but application cannot connect | Higher-layer configuration |

## Common Mistakes

### Creating the Peering Connection and Stopping There

Creating a peering connection does not automatically update all relevant route tables.

Always configure and verify both directions.

### Adding the Route to the Wrong Route Table

A route can be perfectly configured but completely irrelevant if the source subnet uses a different route table.

### Forgetting the Return Route

TCP is bidirectional.

The destination needs a path back to the source.

### Assuming Peering Is Transitive

```text
A <-> B <-> C
```

does not automatically create:

```text
A <-> C
```

Use Transit Gateway or another appropriate architecture when transit routing is required.

### Using Overlapping CIDRs

Overlapping CIDRs make direct routing ambiguous and prevent normal VPC peering.

Use deliberate CIDR allocation across the organization.

### Opening Security Groups to the Internet

Do not solve an internal connectivity problem by adding:

```text
0.0.0.0/0
```

to a database Security Group.

Use the peer VPC CIDR or an appropriately scoped security identity.

### Ignoring NACLs

Security Groups are not the only firewall layer.

A restrictive subnet NACL can still block traffic.

### Testing From the Wrong Source

Testing from another VPC or from a laptop does not validate the production path.

Run tests from the actual workload environment.

### Confusing Timeout With Connection Refused

A timeout often indicates that traffic is being dropped or has no valid path.

A connection refusal often indicates that the destination is reachable but no process is accepting the connection on that port.

This is not absolute, but it is a useful diagnostic distinction.

### Hard-Coding Service IP Addresses

AWS-managed resources can change IP addresses.

Use DNS or service discovery instead of hard-coding dynamic infrastructure addresses.

## Security Considerations

VPC peering creates a private network path, but it does not automatically grant application access.

Use least privilege at every layer:

```text
VPC Peering
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
Application Authorization
```

A production design should explicitly define:

- Which CIDRs can communicate.
- Which ports are permitted.
- Which services are exposed.
- Which accounts own the resources.
- Which teams can modify routes.
- Which DNS names are accessible.
- Which traffic should be logged.

Avoid treating peering as a trusted security boundary.

A peered VPC should be considered another network that requires explicit access control.

## Scalability Considerations

VPC peering works well for limited point-to-point connectivity.

It becomes increasingly difficult to manage when the number of VPCs grows.

For example:

```text
Application VPC
    |
    +--> Database VPC
    |
    +--> Analytics VPC
    |
    +--> Shared Services VPC
    |
    +--> Security VPC
```

As the number of VPCs increases, operational complexity grows across:

- Peering connections.
- Route tables.
- Security Groups.
- DNS.
- Account ownership.
- Monitoring.
- Incident response.

For many VPCs, evaluate centralized networking.

## VPC Peering vs Transit Gateway

| Characteristic | VPC Peering | Transit Gateway |
|---|---|---|
| Connectivity model | Point-to-point | Centralized routing |
| Transitive routing | No | Yes |
| Small environments | Excellent fit | Can be unnecessary |
| Large environments | More difficult | Better fit |
| Route management | Distributed | Centralized |
| Operational complexity | Grows with peering count | More centralized |
| Multi-VPC architecture | Limited | Strong |
| Cost model | Generally simple | Additional service and processing costs |
| Network topology | Mesh-like | Hub-and-spoke |

The right choice depends on scale, routing requirements, operational ownership, and cost.

## High Availability

VPC peering itself does not require you to build separate redundant peering connections between the same VPCs.

AWS manages the underlying infrastructure of the peering connection.

However, the workloads and network architecture around the connection still need to be highly available.

For example:

```text
VPC A
+-----------------------+
| AZ-A                  |
| Application           |
+-----------+-----------+
            |
            |
       VPC Peering
            |
            |
+-----------+-----------+
| VPC B                  |
| AZ-A     AZ-B         |
| DB/Service             |
+-----------------------+
```

Production workloads should generally distribute critical resources across Availability Zones.

For multi-Region peering, consider regional failure scenarios separately.

## Monitoring and Operations

Monitor:

- Peering connection state.
- Route changes.
- Security Group changes.
- NACL changes.
- VPC Flow Logs.
- Reachability Analyzer findings.
- Application connection failures.
- DNS failures.
- Cross-Region latency.
- Data transfer costs.

Infrastructure changes should preferably be made through Infrastructure as Code and reviewed through CI/CD.

This makes route and security changes auditable.

## Cost Considerations

VPC peering can incur AWS data transfer charges depending on the traffic pattern and whether the peering is intra-Region or inter-Region.

For production designs, account for:

- Cross-Region data transfer.
- High-volume service-to-service traffic.
- Database replication.
- Kafka traffic.
- Large object transfers.
- Backup traffic.

A network architecture that is technically correct can still be financially inefficient.

For high-volume communication, evaluate whether the chosen topology and AWS networking service are appropriate.

## Disaster Recovery Considerations

Document VPC peering as part of the recovery architecture.

Record:

- Requester VPC.
- Accepter VPC.
- AWS accounts.
- Regions.
- CIDRs.
- Peering connection ID.
- Route tables.
- Security Groups.
- NACLs.
- DNS dependencies.
- Dependent services.

Manage peering and routes through IaC where practical.

A disaster recovery environment should not depend on undocumented manually created routes.

## Infrastructure as Code

A simplified Terraform configuration might look like:

```hcl
resource "aws_vpc_peering_connection" "app_to_data" {
  vpc_id      = aws_vpc.app.id
  peer_vpc_id = aws_vpc.data.id
  auto_accept = true

  tags = {
    Name = "app-to-data"
  }
}

resource "aws_route" "app_to_data" {
  route_table_id            = aws_route_table.app.id
  destination_cidr_block    = aws_vpc.data.cidr_block
  vpc_peering_connection_id = aws_vpc_peering_connection.app_to_data.id
}

resource "aws_route" "data_to_app" {
  route_table_id            = aws_route_table.data.id
  destination_cidr_block    = aws_vpc.app.cidr_block
  vpc_peering_connection_id = aws_vpc_peering_connection.app_to_data.id
}
```

In production, route creation should be tied to explicit subnet and route-table ownership rather than relying on assumptions about default associations.

## Production Troubleshooting Checklist

```text
[ ] Identify source workload
[ ] Identify destination workload
[ ] Identify source VPC
[ ] Identify destination VPC
[ ] Verify CIDRs do not overlap
[ ] Verify requester VPC
[ ] Verify accepter VPC
[ ] Verify AWS accounts
[ ] Verify Regions
[ ] Verify peering connection state
[ ] Confirm peering connection is active
[ ] Identify source subnet
[ ] Identify destination subnet
[ ] Identify source route table
[ ] Verify source route to destination CIDR
[ ] Verify destination return route
[ ] Check route specificity
[ ] Check route-table associations
[ ] Check Security Groups
[ ] Check destination port
[ ] Check Network ACLs
[ ] Check DNS resolution
[ ] Check private hosted zones if hostnames are used
[ ] Test TCP connectivity
[ ] Test TLS if applicable
[ ] Test application protocol
[ ] Verify destination listener
[ ] Check VPC Flow Logs
[ ] Use Reachability Analyzer where appropriate
[ ] Verify IPv4/IPv6 behavior
[ ] Check cross-Region behavior if applicable
[ ] Check for non-transitive routing assumptions
[ ] Review recent IaC/network changes
[ ] Check data transfer implications
```

## Interview Traps

### "Active Peering Means Traffic Can Flow"

Incorrect.

Routes, Security Groups, NACLs, DNS, and application listeners still determine end-to-end connectivity.

### "VPC Peering Is Transitive"

Incorrect.

Peering provides direct connectivity between the two peered VPCs only.

### "Only the Source Route Is Required"

Incorrect.

The destination must also have a return path.

### "Security Groups Are Automatically Shared"

Incorrect.

Peering does not automatically grant network access between resources.

### "VPCs Can Have Any CIDRs Because They Are Separate"

Incorrect.

Overlapping CIDRs prevent standard VPC peering.

### "A Timeout and Connection Refused Mean the Same Thing"

Incorrect.

They often indicate different layers of failure.

### "Peering Is the Best Solution for Any Number of VPCs"

Incorrect.

At larger scale, Transit Gateway or another centralized networking architecture may be more appropriate.

## Key Takeaways

- **An active VPC peering connection does not guarantee connectivity**; both source and destination route tables, Security Groups, NACLs, DNS, and application listeners must be correct.
- **Always verify routing in both directions** and confirm that the actual source and destination subnets use the route tables containing the required peering routes.
- **VPC peering is non-transitive**; designs requiring VPC A to communicate through VPC B to VPC C generally require Transit Gateway or another transit-capable architecture.
- **Troubleshoot layer by layer**: validate CIDRs and peering state, then routes, firewall controls, DNS, TCP, TLS, and finally the application protocol.
- **Treat peering as production network infrastructure** with deliberate CIDR planning, least-privilege security, IaC, monitoring, high availability, and explicit cost and disaster recovery considerations.