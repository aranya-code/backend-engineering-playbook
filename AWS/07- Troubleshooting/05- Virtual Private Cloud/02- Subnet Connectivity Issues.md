# 02- Subnet Connectivity Issues

## Overview

Subnet connectivity problems are rarely caused by the subnet alone. A subnet is one component of a larger VPC networking path that includes route tables, network interfaces, Security Groups, Network ACLs, gateways, VPC endpoints, DNS, and the destination service.

A reliable troubleshooting process therefore starts by reconstructing the actual network path rather than immediately modifying a firewall rule.

```text
Source Workload
      |
      v
Source ENI
      |
      v
Source Subnet
      |
      +--> Route Table
      |
      +--> Network ACL
      |
      v
AWS Networking Component
      |
      v
Destination Subnet
      |
      +--> Network ACL
      |
      +--> Destination ENI
      |
      +--> Security Group
      |
      v
Destination Service
```

For backend systems, this distinction matters because an application such as Django, FastAPI, PostgreSQL, Redis, or a gRPC service can report a timeout even when the application itself is healthy. The failure may exist several layers below the application.

A useful troubleshooting principle is:

> Identify the first layer where expected network behavior differs from actual network behavior.

## Connectivity Model

For a source workload to communicate successfully with a destination, several independent conditions must be satisfied.

| Layer | Question |
|---|---|
| Application | Is the destination service running and listening? |
| DNS | Does the hostname resolve to the expected address? |
| ENI | Is the workload using the expected network interface and IP? |
| Subnet | Is the resource attached to the expected subnet? |
| Routing | Is there a route toward the destination? |
| Security Group | Does the workload-level policy permit the connection? |
| Network ACL | Do subnet-level rules permit both directions? |
| Gateway/Endpoint | Is the required network service available? |
| Return path | Can the destination send traffic back? |

A connectivity test should therefore answer a specific question.

For example:

```text
Can 10.0.10.25 establish TCP connectivity to
10.0.20.50:5432?
```

This is much more useful than asking:

```text
Why can't my application connect?
```

## Start With the Traffic Path

Before changing any AWS configuration, identify:

- Source workload.
- Source IP.
- Source ENI.
- Source subnet.
- Destination workload.
- Destination IP.
- Destination subnet.
- Protocol.
- Destination port.
- Expected network path.
- Expected return path.

Example:

| Attribute | Value |
|---|---|
| Source | FastAPI service |
| Source IP | `10.0.10.25` |
| Source subnet | `10.0.10.0/24` |
| Destination | PostgreSQL |
| Destination IP | `10.0.20.50` |
| Destination subnet | `10.0.20.0/24` |
| Protocol | TCP |
| Destination port | `5432` |
| Expected path | VPC local route |

For internet-bound traffic, the path may instead be:

```text
Private Application
      |
      v
Private Subnet
      |
      v
Private Route Table
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

For same-VPC communication:

```text
Application Subnet
      |
      v
VPC Local Route
      |
      v
Database Subnet
```

The NAT Gateway should not be inserted into a path that only requires normal same-VPC routing.

## Subnet and ENI Verification

A resource's subnet should be determined from its network interface rather than from assumptions based on deployment configuration or resource names.

Inspect an ENI:

```bash
aws ec2 describe-network-interfaces \
  --network-interface-ids eni-0123456789abcdef0
```

Important fields include:

- `SubnetId`
- `VpcId`
- `PrivateIpAddress`
- `Groups`
- `AvailabilityZone`
- `Status`

Inspect the subnet:

```bash
aws ec2 describe-subnets \
  --subnet-ids subnet-0123456789abcdef0
```

Check:

- VPC ID.
- CIDR block.
- Availability Zone.
- Available IP addresses.
- Intended workload role.
- Route table association.

A common production mistake is troubleshooting the route table for the subnet an engineer *expects* the workload to use rather than the subnet actually associated with the workload's ENI.

## Route Table Troubleshooting

A subnet's routing determines where traffic goes after leaving the network interface.

A typical public subnet might have:

```text
10.0.0.0/16 -> local
0.0.0.0/0   -> Internet Gateway
```

A private application subnet might have:

```text
10.0.0.0/16 -> local
0.0.0.0/0   -> NAT Gateway
```

Inspect route tables:

```bash
aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values=vpc-0123456789abcdef0
```

Verify:

- Destination CIDR.
- Target.
- Route state.
- Subnet association.
- More-specific routes.

### Longest Prefix Match

AWS routing uses the most specific matching route.

Consider:

```text
10.0.0.0/16   -> local
10.0.20.0/24  -> tgw-xxxxxxxx
0.0.0.0/0     -> nat-xxxxxxxx
```

Traffic destined for:

```text
10.0.20.50
```

matches both `10.0.0.0/16` and `10.0.20.0/24`, but the `/24` route is more specific and therefore takes precedence.

This is a common cause of unexpected routing in larger VPCs.

## Route Table Association Problems

A route table is associated with subnets. A subnet without an explicit association uses the VPC's main route table.

This can produce subtle failures when engineers assume that every subnet uses a custom route table.

Inspect route tables:

```bash
aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values=vpc-0123456789abcdef0
```

Look for:

```text
Associations
    |
    +--> Explicit subnet association
    |
    +--> Main route table association
```

Infrastructure as Code should make important subnet-to-route-table associations explicit.

Avoid relying on route table names such as:

```text
private-route-table
```

as proof that a subnet actually uses that table.

## Same-VPC Subnet Connectivity

Suppose:

```text
VPC: 10.0.0.0/16

Application:
10.0.10.25

Database:
10.0.20.50
```

The normal route is:

```text
10.0.10.25
    |
    v
10.0.0.0/16 -> local
    |
    v
10.0.20.50
```

No NAT Gateway is required.

No Internet Gateway is required.

The traffic remains within the VPC.

If this connection fails, inspect:

1. Source and destination VPC IDs.
2. Source and destination IPs.
3. Route tables.
4. Security Groups.
5. Network ACLs.
6. Destination listener.
7. Host-level firewall where applicable.

## Public and Private Subnet Troubleshooting

A subnet is considered public when its route table provides a route to an Internet Gateway.

For IPv4:

```text
0.0.0.0/0 -> Internet Gateway
```

A private subnet does not have direct internet routing through an Internet Gateway.

It may still provide outbound internet access through a NAT Gateway:

```text
Private Subnet
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

Therefore:

> Private does not mean isolated.

It usually means the workload does not have a direct route that makes it publicly reachable from the internet.

Never determine whether a subnet is public or private solely from its name.

## Security Group Troubleshooting

Security Groups are associated with network interfaces.

```text
Subnet
  |
  v
ENI
  |
  +--> Security Group A
  +--> Security Group B
```

For an application-to-database connection, a preferred rule is often:

```text
Database Security Group

Protocol: TCP
Port:     5432
Source:   sg-application
```

This is generally more precise than:

```text
Protocol: TCP
Port:     5432
Source:   10.0.0.0/16
```

Security Group references express the intended workload relationship rather than merely trusting an entire CIDR range.

### Security Group Troubleshooting Questions

- Is the correct Security Group attached to the destination ENI?
- Is the destination port allowed?
- Is the source Security Group correctly referenced?
- Is outbound traffic permitted by the source Security Group?
- Are there multiple ENIs with different Security Groups?
- Is the application actually using the expected ENI?

Security Groups are stateful, so response traffic for an allowed connection is automatically handled by the Security Group.

## Network ACL Troubleshooting

Network ACLs operate at the subnet level and are stateless.

For a TCP connection:

```text
Application
10.0.10.25:45000
      |
      | TCP/5432
      v
Database
10.0.20.50:5432
```

The response travels in the opposite direction:

```text
Database
10.0.20.50:5432
      |
      | TCP/45000
      v
Application
10.0.10.25:45000
```

If Network ACLs are restrictive, both directions must be explicitly permitted.

This is a common reason for timeouts when Security Groups appear correct.

### Ephemeral Ports

Client applications normally select an ephemeral source port.

For example:

```text
10.0.10.25:45000 -> 10.0.20.50:5432
```

The return traffic targets:

```text
10.0.10.25:45000
```

Therefore, Network ACL rules must account for the client's ephemeral source port range.

Do not blindly assume one universal ephemeral range. Validate the operating system and workload behavior before designing restrictive ACL rules.

## DNS Troubleshooting

Connectivity failures frequently originate from DNS rather than routing.

Suppose an application uses:

```text
postgres.internal.example.com
```

Resolve it first:

```bash
dig postgres.internal.example.com
```

or:

```bash
getent hosts postgres.internal.example.com
```

Verify:

- Expected private IP.
- Route 53 private hosted zones.
- VPC DNS support.
- VPC DNS hostnames where required.
- Resolver configuration.
- DNS record correctness.
- DNS caching behavior.

A route to the wrong destination is still a failed network path.

## TCP Connectivity Testing

Test the actual destination port rather than relying on generic network tests.

For PostgreSQL:

```bash
nc -vz 10.0.20.50 5432
```

For HTTP:

```bash
curl -v http://10.0.20.50:8080/health
```

For HTTPS:

```bash
curl -vk https://service.internal.example.com/health
```

For PostgreSQL:

```bash
pg_isready \
  --host=10.0.20.50 \
  --port=5432
```

For TLS diagnostics:

```bash
openssl s_client \
  -connect service.internal.example.com:443 \
  -servername service.internal.example.com
```

Protocol-specific testing helps isolate networking from application-level behavior.

## Why Ping Is Often Misleading

`ping` uses ICMP and does not validate TCP connectivity.

A service can correctly reject ICMP while accepting TCP:

```text
ping 10.0.20.50
    |
    X ICMP blocked

nc -vz 10.0.20.50 5432
    |
    +--> TCP connection succeeds
```

Therefore, use `ping` only when ICMP behavior itself is relevant.

For backend troubleshooting, test the actual protocol and port.

## NAT Gateway Troubleshooting

For private subnet internet connectivity, inspect the complete path:

```mermaid
flowchart LR
    App[Private Application] --> RT[Private Route Table]
    RT --> NAT[NAT Gateway]
    NAT --> PUB[Public Subnet Route Table]
    PUB --> IGW[Internet Gateway]
    IGW --> Internet[Internet]
```

Verify:

1. Private subnet route table.
2. `0.0.0.0/0` route.
3. NAT Gateway state.
4. NAT Gateway subnet.
5. NAT Gateway's public addressing.
6. Public subnet route table.
7. Internet Gateway attachment.
8. Security Group egress.
9. Network ACLs.
10. DNS resolution.

A common incorrect assumption is:

```text
Private Subnet
    |
    v
NAT Gateway
    |
    v
Internet
```

The Internet Gateway and the routing of the NAT Gateway's subnet are also part of the path.

## VPC Endpoint Connectivity

Private workloads can access supported AWS services through VPC endpoints without traversing a NAT Gateway.

An interface endpoint can produce a path such as:

```text
Private Application
      |
      v
Interface Endpoint ENI
      |
      v
AWS Service
```

When endpoint access fails, inspect:

- Endpoint state.
- Endpoint type.
- DNS configuration.
- Endpoint subnet placement.
- Endpoint Security Group.
- Network ACLs.
- Endpoint policy.
- IAM permissions.

A successful network connection does not guarantee an authorized AWS API operation.

For example:

```text
Network connectivity
        |
        v
Endpoint reachable
        |
        v
IAM / Endpoint Policy
        |
        X Access denied
```

## Cross-Availability-Zone Connectivity

Resources in different Availability Zones can communicate through the VPC when the routing and security configuration permits it.

Example:

```text
us-east-1a                 us-east-1b

App Subnet                 App Subnet
10.0.10.0/24               10.0.11.0/24
      |                          |
      +---------- VPC -----------+
```

Cross-AZ architecture should also account for:

- Latency.
- Cross-AZ data transfer cost.
- Failure isolation.
- Stateful service placement.
- Load-balancing behavior.

For highly available systems, multi-AZ deployment is usually desirable, but traffic patterns should be intentionally designed.

## VPC Peering Connectivity

For peered VPCs:

```text
VPC A
10.0.0.0/16
    |
    | VPC Peering
    |
VPC B
10.1.0.0/16
```

VPC A needs a route such as:

```text
10.1.0.0/16 -> pcx-xxxxxxxx
```

VPC B needs the return route:

```text
10.0.0.0/16 -> pcx-xxxxxxxx
```

Then validate:

- Peering state.
- Non-overlapping CIDRs.
- Route tables.
- Security Groups.
- Network ACLs.
- Return routing.

An `active` peering connection does not automatically make every subnet reachable.

## Transit Gateway Troubleshooting

A larger architecture may use:

```text
VPC A
   |
   v
Transit Gateway
   |
   +----> VPC B
   |
   +----> VPC C
   |
   +----> On-Premises
```

Investigate:

- VPC attachment state.
- Transit Gateway route table association.
- Transit Gateway route propagation.
- Static routes.
- VPC route tables.
- Return routes.
- Security controls.

At this scale, troubleshooting should include the complete routing domain rather than only the source VPC.

## Load Balancer Connectivity

A load-balanced application introduces another network hop:

```text
Client
  |
  v
Load Balancer
  |
  v
Target ENI
  |
  v
Application
```

If a target is unhealthy, inspect:

- Target IP.
- Target port.
- Target Security Group.
- Load balancer Security Group.
- Network ACLs.
- Target subnet.
- Application listener.
- Health-check configuration.
- Application response.

For example:

```bash
curl -v http://10.0.20.50:8080/health
```

If direct connectivity succeeds but the load balancer health check fails, investigate the load balancer-to-target path rather than the client-to-load-balancer path.

## ECS and Docker Considerations

ECS tasks using `awsvpc` networking have task-level network interfaces and therefore participate directly in VPC networking.

The diagnostic path is:

```text
ECS Task
   |
   v
Task ENI
   |
   v
Subnet
   |
   v
Route Table
   |
   v
Security Controls
```

Inspect the actual task network interface when debugging.

For Docker workloads running directly on EC2, also consider:

- Container port mappings.
- Docker bridge networking.
- Host networking.
- Host firewall.
- Application bind address.
- Container listener configuration.

A service bound only to:

```text
127.0.0.1
```

will not be reachable through the host's private IP.

## EKS Considerations

EKS adds Kubernetes networking controls on top of VPC networking.

A simplified path is:

```text
Pod
 |
 v
Kubernetes Networking
 |
 v
Node / ENI
 |
 v
VPC Subnet
 |
 v
Route / Security Controls
 |
 v
Destination
```

When debugging EKS connectivity, inspect:

- Pod IP.
- Node IP.
- ENI.
- Subnet.
- Route table.
- Security Group.
- Network ACL.
- Kubernetes Service.
- Endpoint objects.
- NetworkPolicy.
- CoreDNS.

A valid VPC route does not guarantee that a Kubernetes NetworkPolicy allows the connection.

## VPC Flow Logs

VPC Flow Logs provide network-flow metadata that can help identify accepted and rejected traffic.

A conceptual record might show:

```text
Source:       10.0.10.25
Destination:  10.0.20.50
Source Port:  45000
Dest Port:    5432
Protocol:     TCP
Action:       REJECT
```

This can narrow the investigation to the network security or routing layer.

Flow Logs are not packet captures. They do not provide the full contents of network packets.

Correlate flow records with:

- Route tables.
- Security Groups.
- Network ACLs.
- Application logs.
- Load balancer logs.
- DNS events.

## Reachability Analyzer

VPC Reachability Analyzer is useful for complex AWS paths where manually reasoning through every component becomes difficult.

It can help analyze supported paths involving:

- ENIs.
- Subnets.
- Route tables.
- Security Groups.
- Network ACLs.
- Transit Gateway.
- VPC peering.
- Middleboxes.

Use it when the expected path is known but the actual blocking component is unclear.

The goal is not simply to confirm that a connection fails, but to identify where the network model differs from the expected architecture.

## Subnet IP Exhaustion

Connectivity-related incidents can also originate from insufficient subnet address capacity.

Inspect:

```bash
aws ec2 describe-subnets \
  --subnet-ids subnet-0123456789abcdef0 \
  --query 'Subnets[].{Subnet:SubnetId,CIDR:CidrBlock,AvailableIPs:AvailableIpAddressCount}'
```

This is particularly important for:

- ECS.
- EKS.
- Lambda VPC workloads.
- EC2 Auto Scaling.
- Load balancers.
- High-density microservices.

Symptoms include:

- New ECS tasks failing to start.
- EKS pods remaining pending.
- Lambda scaling failures.
- EC2 launch failures.
- Load balancer provisioning failures.
- Deployment failures that appear unrelated to networking.

Existing workloads may remain healthy while new workloads cannot obtain network interfaces.

## Practical Troubleshooting Example

Consider:

```text
VPC: 10.0.0.0/16

Application:
  Subnet: 10.0.10.0/24
  IP:     10.0.10.25

Database:
  Subnet: 10.0.20.0/24
  IP:     10.0.20.50
  Port:   5432
```

The application reports:

```text
connection timed out
```

### Resolve the Hostname

```bash
dig db.internal.example.com
```

Expected:

```text
10.0.20.50
```

If DNS returns a different address, investigate DNS before changing routing.

### Test the TCP Port

```bash
nc -vz 10.0.20.50 5432
```

A timeout indicates that the connection is not completing at the TCP layer.

### Inspect the Route Table

Verify the application subnet has:

```text
10.0.0.0/16 -> local
```

### Inspect Security Groups

The database Security Group should allow the intended source.

For example:

```text
TCP 5432
Source: sg-application
```

### Inspect Network ACLs

Verify both forward and return traffic.

### Verify the Database Listener

On the database host:

```bash
ss -lntp | grep 5432
```

The service should be listening on the expected network address and port.

### Inspect Flow Logs

Search for:

```text
10.0.10.25 -> 10.0.20.50:5432
```

A `REJECT` record provides evidence that traffic was rejected at an observed network interface.

## Diagnostic Command Reference

| Purpose | Command |
|---|---|
| Inspect VPC | `aws ec2 describe-vpcs` |
| Inspect subnet | `aws ec2 describe-subnets` |
| Inspect route tables | `aws ec2 describe-route-tables` |
| Inspect ENI | `aws ec2 describe-network-interfaces` |
| Resolve DNS | `dig`, `nslookup`, `getent hosts` |
| Test TCP | `nc -vz` |
| Test HTTP | `curl -v` |
| Test PostgreSQL | `pg_isready` |
| Inspect listening ports | `ss -lntp` |
| Test TLS | `openssl s_client` |

## Troubleshooting Decision Tree

```mermaid
flowchart TD
    A[Connectivity Failure] --> B[Identify Source and Destination]
    B --> C[Resolve DNS if Hostname Used]
    C --> D{Expected Destination IP?}
    D -->|No| E[Fix DNS]
    D -->|Yes| F[Identify Source and Destination ENIs]
    F --> G[Inspect Source Route Table]
    G --> H{Matching Route?}
    H -->|No| I[Fix Route]
    H -->|Yes| J[Inspect Return Route]
    J --> K{Return Path Valid?}
    K -->|No| L[Fix Return Route]
    K -->|Yes| M[Inspect Security Groups]
    M --> N{Traffic Allowed?}
    N -->|No| O[Fix Security Group]
    N -->|Yes| P[Inspect Network ACLs]
    P --> Q{Both Directions Allowed?}
    Q -->|No| R[Fix NACL]
    Q -->|Yes| S[Test Actual Port]
    S --> T{TCP Connection Works?}
    T -->|No| U[Inspect Flow Logs / Reachability Analyzer]
    T -->|Yes| V[Inspect Application Layer]
```

## Common Failure Patterns

| Symptom | Likely Areas |
|---|---|
| DNS hostname does not resolve | Route 53, VPC DNS, resolver |
| `Connection timed out` | Routing, NACL, Security Group, firewall |
| `Connection refused` | Destination service or listener |
| Internet access fails from private subnet | NAT Gateway, route table, IGW |
| AWS API access fails | Endpoint, endpoint policy, IAM |
| Only one subnet fails | Route table, NACL, subnet association |
| New tasks cannot start | Subnet IP exhaustion |
| Load balancer target unhealthy | Target port, SG, NACL, listener |
| Same VPC communication fails | Route, SG, NACL, application listener |
| Cross-VPC communication fails | Peering/TGW routes, CIDR overlap, SG/NACL |

## Common Mistakes

### Assuming a Private Subnet Cannot Access the Internet

A private subnet can provide outbound internet access through a NAT Gateway.

The important distinction is that it does not have direct internet routing through an Internet Gateway.

### Assuming Same VPC Means Automatic Application Connectivity

The VPC local route provides the network path, but Security Groups, Network ACLs, DNS, and application listeners can still prevent successful communication.

### Troubleshooting the Wrong Route Table

Always verify the actual subnet association.

Do not rely on naming conventions.

### Treating Security Groups as Subnet Controls

Security Groups protect network interfaces. Network ACLs operate at the subnet boundary.

### Forgetting Return Traffic

Network ACLs are stateless. Return traffic needs explicit permission.

### Testing Only With Ping

ICMP success or failure does not establish whether TCP, HTTP, PostgreSQL, Redis, or gRPC traffic works.

### Opening Everything to Test

Avoid temporarily changing a rule to:

```text
0.0.0.0/0
```

without a controlled incident procedure and explicit rollback.

A broad security change can hide the actual root cause and create an unnecessary security exposure.

### Ignoring IP Exhaustion

A subnet can be correctly routed and secured while still being unable to accept additional network interfaces.

## Production Best Practices

### Make Network Boundaries Explicit

Use clear subnet roles such as:

```text
Public
Private Application
Private Data
```

and explicitly define routing between them.

### Use Least-Privilege Security Groups

Prefer:

```text
Application SG
      |
      | TCP/5432
      v
Database SG
```

rather than broad CIDR-based access where a Security Group reference is appropriate.

### Use Multiple Availability Zones

Production workloads should generally be distributed across multiple Availability Zones where the service architecture supports it.

Consider:

- Route consistency.
- NAT Gateway placement.
- Cross-AZ traffic.
- Failure isolation.
- Data transfer cost.
- Stateful service behavior.

### Design Subnets for Growth

Reserve sufficient address space for:

- Auto Scaling.
- ECS tasks.
- EKS pods.
- Lambda ENIs.
- Load balancers.
- Future services.

Subnet sizing is a capacity-planning decision, not merely an initial deployment detail.

### Manage Networking Through IaC

Use Terraform, CloudFormation, or an equivalent approved mechanism for:

- VPCs.
- Subnets.
- Route tables.
- Route associations.
- Security Groups.
- Network ACLs.
- NAT Gateways.
- VPC endpoints.

This makes network configuration versioned, reviewable, and reproducible.

### Centralize Observability

Use the appropriate combination of:

- VPC Flow Logs.
- CloudTrail.
- CloudWatch.
- Load balancer access logs.
- Application logs.
- DNS query logging where appropriate.

Correlate network events with application events using timestamps and request identifiers where available.

## Security Considerations

Troubleshooting should never weaken the intended security architecture unnecessarily.

Prefer:

- Least-privilege Security Groups.
- Private subnets for internal services.
- VPC endpoints where appropriate.
- Restricted Network ACLs when subnet-level filtering is actually required.
- Temporary diagnostic changes with explicit rollback.
- IaC-managed configuration.
- Documented incident procedures.

Avoid:

- Publicly exposing private databases.
- Opening database ports to `0.0.0.0/0`.
- Disabling security controls without a controlled test.
- Making undocumented production console changes.
- Leaving temporary rules in place.

## Scalability Considerations

Subnet architecture becomes increasingly important as backend workloads scale.

A multi-AZ architecture might look like:

```text
                    VPC
                     |
          +----------+----------+
          |                     |
         AZ-a                  AZ-b
          |                     |
     App Subnet             App Subnet
          |                     |
       ECS/EKS               ECS/EKS
          |                     |
     Data Subnet             Data Subnet
```

At scale, consider:

- IP address capacity.
- ENI consumption.
- Availability Zone distribution.
- NAT Gateway placement.
- Cross-AZ traffic.
- Route table complexity.
- Transit Gateway routing.
- VPC endpoint usage.
- AWS service quotas.

Subnet design should therefore be reviewed alongside application scaling architecture.

## Incident Runbook

Use the following sequence during a production connectivity incident:

```text
1. Identify the source workload.
2. Identify the source ENI and subnet.
3. Identify the destination workload.
4. Identify the destination IP and port.
5. Resolve DNS if a hostname is used.
6. Verify the source subnet's effective route table.
7. Verify the destination return path.
8. Inspect Security Groups.
9. Inspect Network ACLs.
10. Validate NAT, Internet Gateway, VPC endpoint, peering, or Transit Gateway paths.
11. Test the actual protocol and port.
12. Inspect VPC Flow Logs.
13. Use Reachability Analyzer for complex paths.
14. Verify the destination listener.
15. Check application-level logs.
16. Record the root cause and remediation.
```

The most effective troubleshooting approach is to move from lower-level network primitives toward higher-level application behavior while avoiding unrelated configuration changes.

## Interview Traps

### "A Private Subnet Cannot Access the Internet"

Incorrect.

A private subnet can access the internet through a NAT Gateway for outbound traffic.

### "Security Groups Are Attached to Subnets"

Incorrect.

Security Groups are associated with network interfaces.

### "Network ACLs Are Stateful"

Incorrect.

Network ACLs are stateless and require appropriate rules for both directions.

### "Same VPC Means No Routing Is Required"

The VPC local route normally provides same-VPC connectivity, but routing is still part of the packet path and other controls can block the traffic.

### "NAT Gateway Is Required for Internal VPC Traffic"

Incorrect.

Resources communicating inside the same VPC normally use the VPC local route.

### "An Active VPC Peering Connection Means All Subnets Can Communicate"

Incorrect.

Both sides require appropriate routes, and Security Groups and Network ACLs still apply.

## Key Takeaways

- **Trace the complete network path** from the source ENI to the destination instead of treating the subnet as the root cause.
- **Verify effective routing and return routing**, including longest-prefix matching and explicit subnet route-table associations.
- **Separate routing from security controls**: Security Groups are stateful ENI-level controls, while Network ACLs are stateless subnet-level controls.
- **Test the actual protocol and port** and use VPC Flow Logs or Reachability Analyzer when the network path is unclear.
- **Treat subnet capacity, multi-AZ design, NAT paths, endpoints, and observability as production concerns**, not merely deployment details.