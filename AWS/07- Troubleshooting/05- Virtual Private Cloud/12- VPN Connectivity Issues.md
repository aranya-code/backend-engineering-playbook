# 12- VPN Connectivity Issues

## Overview

AWS Site-to-Site VPN provides encrypted connectivity between an AWS VPC environment and an external network such as an on-premises data center, branch office, or another cloud environment. In a typical production architecture, the VPN terminates on a Virtual Private Gateway (VGW) or Transit Gateway (TGW), while the customer side uses a Customer Gateway and compatible VPN device or software appliance.

VPN connectivity problems are often misdiagnosed because several independent states must be healthy simultaneously:

```text
Application
    |
    v
VPC Route Table
    |
    v
Transit Gateway / Virtual Private Gateway
    |
    v
IPsec VPN Tunnel
    |
    v
Customer Gateway
    |
    v
On-Premises Router / Firewall
    |
    v
Destination Network
```

A VPN tunnel being `UP` does not prove that an application can reach an on-premises service. Tunnel establishment, routing, security policy, DNS, MTU, and application-level connectivity are separate concerns.

Common VPN failures include:

- Tunnel not establishing.
- Only one tunnel being operational.
- IKE negotiation failures.
- IPsec negotiation failures.
- Incorrect pre-shared key.
- Incorrect encryption or integrity parameters.
- Dead Peer Detection failures.
- Missing AWS-side routes.
- Missing customer-side routes.
- Incorrect BGP configuration.
- Missing BGP advertisements.
- Incorrect static routes.
- Security appliance rules blocking traffic.
- Network ACL or Security Group restrictions.
- NAT interfering with VPN traffic.
- MTU or fragmentation problems.
- Asymmetric routing.
- DNS failures.
- Overlapping CIDRs.
- Transit Gateway route-table problems.
- Application listener or firewall problems.

The correct troubleshooting approach is to separate the problem into layers and validate each layer independently.

## VPN Architecture

A traditional AWS Site-to-Site VPN architecture can look like:

```mermaid
flowchart LR
    AWS[VPC]
    RT[VPC Route Table]
    VGW[Virtual Private Gateway]
    VPN[IPsec VPN]
    CGW[Customer Gateway]
    FW[On-Premises Firewall]
    ONPREM[On-Premises Network]

    AWS --> RT
    RT --> VGW
    VGW --> VPN
    VPN --> CGW
    CGW --> FW
    FW --> ONPREM
```

A Transit Gateway-based architecture changes the AWS routing layer:

```mermaid
flowchart LR
    VPC[Application VPC]
    VPCRT[VPC Route Table]
    TGW[Transit Gateway]
    TGWRT[TGW Route Table]
    VPN[VPN Attachment]
    CGW[Customer Gateway]
    ONPREM[On-Premises Network]

    VPC --> VPCRT
    VPCRT --> TGW
    TGW --> TGWRT
    TGWRT --> VPN
    VPN --> CGW
    CGW --> ONPREM
```

The second architecture is common in organizations with multiple VPCs and centralized network connectivity.

## Troubleshooting Layers

Treat VPN troubleshooting as a layered process.

| Layer | Question |
|---|---|
| Physical/underlay | Is the customer device reachable over the Internet? |
| IKE | Can the peers establish the VPN negotiation? |
| IPsec | Can the peers establish encrypted child SAs? |
| Tunnel | Are the VPN tunnels operational? |
| Routing | Does AWS know where to send traffic? |
| BGP/static routing | Are required prefixes exchanged or configured? |
| Security | Are firewalls, SGs, and NACLs permitting traffic? |
| Transport | Can TCP/UDP traffic reach the destination? |
| Application | Is the destination service listening and healthy? |
| DNS | Does the application resolve the correct destination? |

Do not jump directly to application debugging when the VPN itself is down.

## VPN Tunnel State

AWS Site-to-Site VPN commonly provides two tunnels for redundancy.

Conceptually:

```text
                    +--> Tunnel 1 -->+
AWS VPN Endpoint ---+                +--- Customer Gateway
                    +--> Tunnel 2 -->+
```

The two tunnels provide high availability.

A production environment should not depend on only one tunnel remaining operational.

Check VPN status:

```bash
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-0123456789abcdef0
```

A useful query is:

```bash
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-0123456789abcdef0 \
  --query 'VpnConnections[].{
    Id:VpnConnectionId,
    State:State,
    Type:Type,
    TransitGatewayId:TransitGatewayId,
    VirtualPrivateGatewayId:VirtualPrivateGatewayId
  }'
```

Inspect tunnel telemetry:

```bash
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-0123456789abcdef0 \
  --query 'VpnConnections[].VgwTelemetry'
```

Look for:

- Tunnel status.
- Outside IP address.
- Inside tunnel IP addresses.
- Status message.
- Accepted route counts where available.
- BGP status where applicable.

## One Tunnel Down vs Both Tunnels Down

These scenarios have different severity.

### One Tunnel Down

```text
Tunnel 1: UP
Tunnel 2: DOWN
```

Traffic may continue through the healthy tunnel.

Investigate:

- Customer device configuration.
- IKE parameters.
- IPsec parameters.
- Dead Peer Detection.
- NAT/firewall behavior.
- ISP connectivity.
- Recent configuration changes.

Treat a single failed tunnel as a reliability issue even if application traffic currently works.

### Both Tunnels Down

```text
Tunnel 1: DOWN
Tunnel 2: DOWN
```

This usually indicates a broader problem.

Investigate:

- Customer gateway reachability.
- Internet connectivity.
- AWS VPN configuration.
- IKE negotiation.
- Pre-shared keys.
- Encryption parameters.
- Firewall rules.
- Customer device state.
- Recent network changes.

## IKE Negotiation

IKE establishes the security association used to negotiate the IPsec connection.

A simplified sequence is:

```text
AWS VPN Endpoint
       |
       | IKE negotiation
       v
Customer Gateway
       |
       | Authentication
       v
Security Association
       |
       v
IPsec negotiation
```

Depending on the VPN configuration, IKE version and cryptographic parameters must match the customer device.

Common mismatches include:

- IKE version.
- Encryption algorithm.
- Integrity algorithm.
- Diffie-Hellman group.
- Authentication settings.
- Lifetime parameters.
- Pre-shared key.

When IKE negotiation fails, investigate the customer device logs before changing application routing.

## Pre-Shared Key Problems

The pre-shared key authenticates the VPN peers.

A mismatch can prevent tunnel establishment.

Typical causes:

- Incorrect PSK entered on the customer device.
- PSK changed on AWS but not on the customer device.
- Configuration copied to the wrong tunnel.
- Special characters mishandled by automation.
- Stale configuration on the customer appliance.

If the VPN configuration was recently regenerated or replaced, verify that the customer device is using the current tunnel configuration.

Do not expose pre-shared keys in:

- Git repositories.
- Terraform state accessible to unauthorized users.
- CI/CD logs.
- Chat messages.
- Incident tickets.
- Shell history where avoidable.

## IPsec Negotiation

After IKE negotiation, the peers establish the IPsec security associations used to protect traffic.

A simplified sequence is:

```text
IKE SA
  |
  v
Authentication
  |
  v
IPsec Child SA
  |
  v
Encrypted Application Traffic
```

If IKE succeeds but IPsec fails, investigate:

- Encryption algorithms.
- Integrity algorithms.
- Perfect Forward Secrecy.
- Phase 2 parameters.
- Traffic selectors.
- Lifetime settings.
- Rekey behavior.

The exact terminology varies between VPN implementations, but the important diagnostic distinction is:

```text
IKE failure
```

versus:

```text
IPsec/Child SA failure
```

## Dead Peer Detection

Dead Peer Detection (DPD) helps detect an unavailable VPN peer.

Problems may occur when:

- The customer firewall aggressively expires state.
- Intermediate NAT devices interfere with keepalives.
- The customer gateway stops responding.
- The configured DPD behavior does not match operational expectations.

Repeated tunnel flapping can indicate an underlying stability problem rather than a simple routing error.

Correlate tunnel state changes with:

- Firewall logs.
- ISP events.
- Customer device logs.
- AWS tunnel telemetry.
- Configuration changes.

## Customer Gateway Reachability

Before troubleshooting IPsec, verify that the customer gateway's public endpoint is reachable.

Check:

```text
Customer Gateway Public IP
        |
        v
Internet
        |
        v
AWS VPN Endpoint
```

Potential failures include:

- ISP outage.
- Firewall blocking IKE.
- NAT device failure.
- Incorrect public IP.
- Customer router failure.
- Incorrect interface configuration.
- Routing problems on the customer side.

The customer gateway must be reachable over the expected Internet path.

## UDP Ports and Firewall Rules

IPsec VPN commonly requires appropriate Internet-facing firewall handling.

Depending on the VPN configuration and network path, verify that required traffic such as:

- UDP 500 for IKE.
- UDP 4500 for NAT traversal.

is permitted.

Do not assume that an internal firewall rule allowing application traffic also permits VPN negotiation traffic.

For example:

```text
Application TCP 443
        |
        X
VPN negotiation still blocked
```

VPN establishment traffic and application traffic are separate flows.

## NAT Traversal

NAT can affect IPsec connectivity.

When NAT exists between the customer gateway and AWS VPN endpoint, NAT traversal may be required.

Typical path:

```text
Customer Gateway
      |
      v
NAT Device
      |
      v
Internet
      |
      v
AWS VPN Endpoint
```

Potential issues include:

- UDP 4500 blocked.
- NAT state expiration.
- Multiple VPN peers behind the same NAT.
- Incorrect firewall inspection.
- NAT rules modifying unexpected traffic.

When tunnel state changes unexpectedly, investigate the customer network path between the VPN endpoint and the Internet.

## Routing Fundamentals

A VPN tunnel transports traffic, but routing determines whether traffic enters the tunnel.

Suppose:

```text
AWS VPC
10.10.0.0/16

On-Premises
172.16.0.0/16
```

The AWS subnet route table might contain:

```text
172.16.0.0/16 -> TGW
```

or:

```text
172.16.0.0/16 -> VGW
```

depending on the architecture.

The customer network also needs a route back:

```text
10.10.0.0/16 -> VPN
```

A tunnel can be completely healthy while traffic is never sent into it.

## AWS Route Table Troubleshooting

Identify the route table used by the source subnet:

```bash
aws ec2 describe-route-tables \
  --filters \
    Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

Inspect routes:

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0 \
  --query 'RouteTables[].Routes[]'
```

Verify the on-premises destination CIDR.

For example:

```text
Destination: 172.16.0.0/16
Target:      Transit Gateway
```

or:

```text
Destination: 172.16.0.0/16
Target:      Virtual Private Gateway
```

The target must match the actual VPN architecture.

## Transit Gateway VPN Routing

With Transit Gateway, the routing path becomes:

```text
Source Subnet
    |
    v
VPC Route Table
    |
    v
Transit Gateway
    |
    v
TGW Route Table
    |
    v
VPN Attachment
    |
    v
Customer Gateway
```

Every layer must contain the required route.

A common failure is:

```text
VPC Route Table
172.16.0.0/16 -> TGW
        |
        v
TGW
        |
        X
No route to VPN attachment
```

The VPC is correctly configured, but Transit Gateway cannot forward the packet to the VPN.

## Transit Gateway Route Inspection

Inspect TGW routes:

```bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0 \
  --filters Name=type,Values=static,propagated
```

Verify:

- Destination prefix.
- Route state.
- Route type.
- VPN attachment.
- Blackhole status.

Also verify the VPN attachment:

```bash
aws ec2 describe-transit-gateway-attachments \
  --filters \
    Name=transit-gateway-id,Values=tgw-0123456789abcdef0
```

## Virtual Private Gateway Routing

When using a Virtual Private Gateway, the VPC route table must direct traffic toward the VGW.

Example:

```text
172.16.0.0/16 -> vgw-0123456789abcdef0
```

The VPN connection is associated with the VGW.

Verify:

```bash
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-0123456789abcdef0
```

Then verify the VPC route table contains the required destination.

## Static Routing

Static VPN routing requires explicit network prefixes.

Example:

```text
AWS:
172.16.0.0/16 -> VPN

On-Premises:
10.10.0.0/16 -> VPN
```

Advantages:

- Simple.
- Predictable.
- Easy to understand for small environments.

Limitations:

- Manual route maintenance.
- Poor scalability with many prefixes.
- Higher operational risk during network growth.

Static routing is appropriate for smaller and stable networks, but large hybrid environments often benefit from dynamic routing.

## Dynamic Routing With BGP

BGP allows the customer gateway and AWS VPN endpoint to exchange routes dynamically.

Conceptually:

```text
AWS VPN Endpoint
       |
       | BGP
       v
Customer Gateway
       |
       +--> Advertise on-prem prefixes
       |
       +<-- Receive AWS prefixes
```

This reduces manual route management.

For BGP troubleshooting, separate:

```text
VPN Tunnel
```

from:

```text
BGP Session
```

A tunnel can be operational while the BGP session is down.

## BGP Troubleshooting

Verify:

- BGP peer IP addresses.
- Autonomous System Numbers.
- BGP authentication if configured.
- Customer router configuration.
- Local ASN.
- Remote ASN.
- Advertised prefixes.
- Received prefixes.
- BGP timers.
- Firewall policies.
- Route filtering.

A useful mental model is:

```text
Tunnel UP
   |
   v
BGP Session?
   |
   +--> DOWN
   |      |
   |      v
   |   No dynamic routes
   |
   +--> UP
          |
          v
      Check prefixes
```

Do not conclude that routing is healthy merely because the IPsec tunnel is established.

## Missing BGP Advertisements

Suppose on-premises contains:

```text
172.16.0.0/16
172.17.0.0/16
```

but advertises only:

```text
172.16.0.0/16
```

Traffic to:

```text
172.17.0.10
```

will fail even though the VPN and BGP session are healthy.

Verify that the expected prefixes are being advertised.

Also check whether the customer router filters AWS or on-premises routes.

## Route Propagation

With dynamic routing, routes may need to propagate into the relevant AWS route table.

The expected path is:

```text
On-Premises Prefix
      |
      v
BGP
      |
      v
VPN Attachment
      |
      v
Transit Gateway / VGW
      |
      v
VPC Route Table
```

If propagation is disabled or incorrectly configured, the route may never become usable by the VPC.

## Return Routing

Always validate both directions.

Example:

```text
AWS:
10.10.1.20

On-Premises:
172.16.10.30
```

Forward:

```text
10.10.1.20
   |
   v
AWS Route Table
   |
   v
TGW/VGW
   |
   v
VPN
   |
   v
172.16.10.30
```

Return:

```text
172.16.10.30
   |
   v
On-Premises Router
   |
   v
VPN
   |
   v
TGW/VGW
   |
   v
10.10.1.20
```

A missing return route frequently manifests as a TCP timeout.

## Asymmetric Routing

Asymmetric routing occurs when the forward and return packets use different paths.

For example:

```text
Forward:
AWS -> TGW -> VPN -> Firewall A -> Server

Return:
Server -> Firewall B -> VPN -> TGW -> AWS
```

This can cause stateful firewalls to reject packets because the firewall that sees the return traffic does not have the corresponding connection state.

Symptoms can include:

- SYN reaches the destination.
- SYN-ACK leaves the destination.
- Client never completes the handshake.
- Firewall logs show unexpected traffic.
- Packet captures show different paths.

Hybrid architectures should explicitly document intended forward and return paths.

## Overlapping CIDRs

Overlapping networks are a major hybrid-connectivity problem.

Example:

```text
AWS VPC:
10.10.0.0/16

On-Premises:
10.10.0.0/16
```

The address:

```text
10.10.20.10
```

does not uniquely identify a network.

This creates routing ambiguity and can prevent the desired connectivity model.

Inspect AWS CIDRs:

```bash
aws ec2 describe-vpcs \
  --query 'Vpcs[].{
    VpcId:VpcId,
    Cidr:CidrBlock
  }'
```

Hybrid network address allocation should be centrally governed.

## Security Groups

Security Groups can still affect traffic involving VPN-connected workloads.

For example:

```text
On-Premises Client
172.16.10.20
        |
        v
AWS API
10.10.20.30:443
```

The destination Security Group must allow the intended source:

```text
Protocol: TCP
Port:     443
Source:   172.16.0.0/16
```

Inspect:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0
```

Avoid broad temporary rules such as:

```text
0.0.0.0/0 -> TCP 443
```

unless they are genuinely required by the architecture.

## Network ACLs

Network ACLs are stateless.

For TCP connectivity, both request and response traffic must be permitted.

Example:

```text
On-Premises
     |
     | TCP 443
     v
AWS Service
     |
     | TCP ephemeral port
     v
On-Premises
```

A restrictive outbound or inbound NACL can therefore cause connectivity failures even when:

- VPN is healthy.
- BGP is healthy.
- Routes are correct.
- Security Groups allow the traffic.

Inspect:

```bash
aws ec2 describe-network-acls \
  --filters \
    Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

## Firewall Troubleshooting

The customer firewall is often the most important non-AWS dependency.

Check:

- IKE traffic.
- NAT-T traffic.
- ESP if applicable to the topology.
- Application traffic.
- Return traffic.
- Source NAT.
- Destination NAT.
- VPN policy.
- Security zones.
- Route policy.
- Stateful session tracking.

Do not assume:

```text
VPN established
```

means:

```text
Application traffic permitted
```

VPN negotiation traffic and application traffic can be governed by different firewall policies.

## NAT and Source Address Translation

Unexpected NAT can break route assumptions.

Suppose AWS expects:

```text
Source: 10.10.0.0/16
```

but the customer firewall translates the source to:

```text
192.168.100.10
```

The return path may no longer match the expected routing policy.

Investigate NAT rules when:

- Flow logs show unexpected source addresses.
- Security Group rules appear correct but traffic is rejected.
- On-premises routing expects the original AWS CIDR.
- Stateful firewall behavior is inconsistent.

Avoid unnecessary NAT across private VPN connectivity unless the architecture specifically requires it.

## MTU and Fragmentation

VPN encapsulation adds overhead to packets.

The effective payload size can therefore be smaller than the underlying network MTU.

Potential symptoms:

- Small packets work.
- Large requests fail.
- TCP connections establish but transfers stall.
- HTTPS behaves inconsistently.
- gRPC streams fail under larger messages.
- PostgreSQL queries involving larger payloads behave unexpectedly.
- Packet captures show retransmissions.

Test path MTU where appropriate:

```bash
ping -M do -s 1400 172.16.10.30
```

Reduce the payload size progressively if fragmentation appears to be an issue.

Exact usable MTU depends on the complete network path and encapsulation.

## TCP Symptoms

The TCP handshake provides useful diagnostic information.

Successful:

```text
Client              Server

  SYN  ------------>

       <------------  SYN-ACK

  ACK  ------------>
```

Only SYN:

```text
Client              Server

  SYN  ------------>
       X
```

Potential causes:

- Routing failure.
- Firewall drop.
- NACL drop.
- VPN forwarding failure.
- Destination unreachable.
- Return path failure.

SYN followed by RST:

```text
SYN  ------------>
     <------------ RST
```

Usually indicates that the destination path is reachable but the destination is actively rejecting the connection, commonly because no service is listening on the requested port.

This is different from a silent packet drop.

## DNS Troubleshooting

VPN connectivity does not automatically provide DNS resolution across networks.

An AWS workload might resolve:

```text
api.internal.example.com
```

to an AWS private address while the intended service is actually hosted on-premises.

Test:

```bash
dig api.internal.example.com
```

and:

```bash
getent hosts api.internal.example.com
```

Investigate:

- Route 53 Resolver.
- Resolver endpoints.
- Conditional forwarding.
- On-premises DNS servers.
- Private hosted zones.
- Split-horizon DNS.
- DNS firewall rules.
- Security Group rules for DNS.
- UDP/TCP 53 connectivity.

Separate:

```text
DNS Resolution
```

from:

```text
IP Connectivity
```

A correct DNS response does not guarantee that the returned address is reachable.

## VPC Flow Logs

VPC Flow Logs can help determine whether traffic reaches AWS network interfaces.

For example:

```text
Source IP
Destination IP
Source Port
Destination Port
Protocol
Action
```

Interpretation:

```text
REJECT
   |
   v
Investigate filtering

ACCEPT
   |
   v
Continue toward routing/application analysis
```

An `ACCEPT` record does not mean the application successfully processed the request. It only establishes that the observed network traffic was accepted at the relevant network interface.

## Reachability Analyzer

VPC Reachability Analyzer can help analyze supported AWS-side network paths.

Use it when you need to determine whether the AWS network configuration permits a path between supported source and destination resources.

It can help identify issues involving:

- Route tables.
- Security Groups.
- Network ACLs.
- Transit Gateway.
- VPN-related AWS network components where supported.

Use it together with:

- VPN tunnel telemetry.
- BGP information.
- Customer firewall logs.
- VPC Flow Logs.
- Application-level testing.

## Packet Capture

When the configuration appears correct, packet capture can determine where packets stop.

On a Linux workload:

```bash
sudo tcpdump -ni any host 172.16.10.30 and port 443
```

For a TCP connection:

```text
SYN
SYN-ACK
ACK
```

If only SYN packets leave:

```text
SYN
SYN
SYN
```

the response path should be investigated.

If the TCP handshake succeeds but the application stalls, move the investigation upward:

```text
IP
 |
 v
TCP
 |
 v
TLS
 |
 v
HTTP/gRPC/PostgreSQL
 |
 v
Application
```

## Production Troubleshooting Workflow

### Identify the Source

Record:

```text
Source workload
Source IP
Source subnet
Source VPC
Source route table
AWS account
AWS Region
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
Destination subnet/network
Destination service
```

For hybrid environments, determine whether the destination is:

- On-premises.
- Branch office.
- Another cloud.
- Another AWS Region.
- Another VPC reached through the customer network.

### Verify the VPN Connection

```bash
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-0123456789abcdef0
```

Check both tunnels.

### Verify Tunnel Telemetry

```bash
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-0123456789abcdef0 \
  --query 'VpnConnections[].VgwTelemetry'
```

Determine:

```text
Tunnel state
Outside IP
Inside IP
Status
BGP state where applicable
```

### Verify IKE/IPsec

If the tunnel is down, inspect the customer gateway logs for:

```text
IKE negotiation
Authentication
IPsec negotiation
DPD
Rekey
```

Do not investigate application routes before the tunnel can establish.

### Verify AWS Routing

Check the source VPC route table:

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0 \
  --query 'RouteTables[].Routes[]'
```

Verify the destination CIDR points toward the expected VPN path.

### Verify Transit Gateway Routing

If TGW is used:

```bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0 \
  --filters Name=type,Values=static,propagated
```

Verify the destination prefix resolves to the VPN attachment.

### Verify BGP

If dynamic routing is used, confirm:

```text
BGP session
Advertised prefixes
Received prefixes
Route filtering
ASNs
```

A BGP session being established does not guarantee that the correct prefixes are being exchanged.

### Verify the Customer Route

Confirm the on-premises router has a route back to the AWS VPC CIDR.

For example:

```text
10.10.0.0/16 -> AWS VPN
```

### Verify Firewall Rules

Check both:

```text
VPN negotiation traffic
```

and:

```text
Application traffic
```

### Verify Security Groups

Check the destination workload's Security Group.

### Verify NACLs

Check both inbound and outbound rules.

### Test DNS

```bash
dig internal-service.example.com
```

### Test TCP

```bash
nc -vz 172.16.10.30 443
```

### Test the Application

```bash
curl -vk https://internal-service.example.com/health
```

### Check MTU

If small requests work but larger payloads fail, investigate MTU and fragmentation.

### Check Flow Logs and Firewall Logs

Correlate timestamps across:

```text
AWS Flow Logs
Customer Firewall
VPN Telemetry
BGP Logs
Application Logs
```

This correlation is often more useful than inspecting each system independently.

## Common Failure Patterns

| Symptom | Likely Cause |
|---|---|
| Both VPN tunnels down | IKE, firewall, Internet, PSK, or customer gateway issue |
| One tunnel down | Individual tunnel configuration or customer-side issue |
| Tunnel UP, no traffic | Routing or filtering |
| Tunnel UP, BGP DOWN | BGP configuration or customer routing issue |
| BGP UP, destination unreachable | Missing/incorrect prefix |
| AWS can send but receives no response | Missing customer return route or firewall |
| Small packets work, large packets fail | MTU/fragmentation |
| TCP timeout | Routing/filtering/drop |
| TCP connection refused | Destination reachable but service unavailable |
| DNS hostname fails, IP works | DNS issue |
| Some AWS subnets work, others fail | Route-table association or subnet-specific configuration |
| One VPC works, another fails | TGW/VPC route or propagation issue |
| VPN works after firewall restart | Stateful firewall/NAT/DPD issue |
| Tunnel repeatedly flaps | DPD, ISP, firewall, rekey, or unstable peer |
| Cross-account VPC cannot reach on-premises | TGW association/propagation or route configuration |
| On-premises reaches AWS but AWS cannot reach on-premises | Asymmetric or missing return routing |

## Common Mistakes and Pitfalls

### Assuming Tunnel UP Means Connectivity Works

Tunnel state only proves that the VPN control and security associations are established.

Always test routing and application traffic separately.

### Checking Only AWS Configuration

Hybrid networking is end-to-end.

A correct AWS configuration cannot compensate for:

- Missing customer routes.
- Firewall rules.
- Incorrect NAT.
- BGP filtering.
- Broken customer gateway.

### Ignoring the Return Path

Always validate:

```text
Forward Path
+
Return Path
```

A missing return route commonly causes TCP timeouts.

### Confusing BGP State With Route Availability

A BGP session can be established while the expected prefixes are missing.

Verify actual advertised and received routes.

### Opening the Firewall Completely

Avoid using unrestricted rules as a diagnostic shortcut.

Instead, identify:

```text
Source
Destination
Protocol
Port
Direction
```

and permit only the required traffic.

### Ignoring NAT

NAT can change the source address and break expected routing or security policies.

### Ignoring MTU

VPN encapsulation reduces the available payload size.

If only larger packets fail, investigate MTU before changing routing.

### Treating Both Tunnels Identically

Each tunnel has its own:

- Outside IP.
- Inside IP.
- Configuration.
- State.
- Negotiation behavior.

A problem affecting one tunnel may not affect the other.

### Testing From the Wrong Network

A successful connection from an EC2 bastion does not prove that an EKS pod, ECS task, or Lambda function has the same connectivity.

Test from the actual workload path.

### Ignoring Configuration Drift

Manual customer firewall changes can diverge from the documented VPN configuration.

Treat both AWS and customer-side network configuration as controlled infrastructure.

## High Availability

AWS Site-to-Site VPN provides two tunnels for redundancy.

A production architecture should ensure that the customer-side network can use both tunnels appropriately.

Conceptually:

```mermaid
flowchart TB
    AWS[AWS Network]
    T1[Tunnel 1]
    T2[Tunnel 2]
    FW1[Customer VPN Endpoint A]
    FW2[Customer VPN Endpoint B]
    ONPREM[On-Premises Network]

    AWS --> T1
    AWS --> T2
    T1 --> FW1
    T2 --> FW2
    FW1 --> ONPREM
    FW2 --> ONPREM
```

High availability requires more than having two tunnels configured.

Validate:

- Customer gateway redundancy.
- ISP redundancy where required.
- Firewall redundancy.
- Routing convergence.
- BGP behavior.
- Failover testing.
- Application retry behavior.
- Connection draining/recovery.

For critical systems, perform controlled tunnel-failure tests rather than assuming failover works.

## Monitoring and Observability

Monitor:

- Tunnel state.
- Tunnel state transitions.
- BGP state.
- Route counts.
- Packet counters.
- VPN latency where available.
- Network errors.
- Customer firewall events.
- Application connection failures.
- VPC Flow Logs.
- Transit Gateway metrics where applicable.

Alert on:

```text
Both tunnels down
```

and consider alerting on:

```text
One tunnel down
```

because a single tunnel failure reduces redundancy even if traffic continues.

Correlate network telemetry with application telemetry:

```text
VPN Tunnel Down
       |
       v
BGP Route Loss
       |
       v
Application Connection Errors
       |
       v
Request Failures
```

This provides a causal chain during incidents.

## Security Considerations

VPN encryption protects traffic across the Internet, but it does not automatically authorize every application connection.

Maintain layered controls:

```text
VPN Encryption
      |
      v
Routing
      |
      v
Firewall
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

Use least privilege for:

- VPN routes.
- Firewall rules.
- Security Groups.
- Administrative access.
- Customer gateway management.

Protect VPN configuration secrets, particularly:

- Pre-shared keys.
- Device credentials.
- Private keys where applicable.
- BGP authentication secrets.

Avoid storing sensitive VPN material in source repositories or unprotected operational documentation.

## Scalability Considerations

Static routing becomes increasingly difficult as the number of networks grows.

For example:

```text
5 networks
   |
   v
Static routes may be manageable

100+ networks
   |
   v
Manual routing becomes operationally expensive
```

Dynamic routing with BGP can reduce manual route management.

Transit Gateway can further centralize connectivity across:

- Multiple VPCs.
- Multiple AWS accounts.
- Multiple Regions.
- VPN connections.
- Direct Connect.
- Shared network services.

However, centralization increases the importance of:

- Route-table design.
- CIDR governance.
- Route propagation policy.
- Ownership.
- Monitoring.
- Change control.

## Infrastructure as Code

Where possible, manage AWS-side VPN infrastructure through Infrastructure as Code.

A simplified Terraform example:

```hcl
resource "aws_customer_gateway" "onprem" {
  bgp_asn    = 65000
  ip_address = "203.0.113.10"
  type       = "ipsec.1"

  tags = {
    Name = "onprem-customer-gateway"
  }
}

resource "aws_vpn_connection" "onprem" {
  customer_gateway_id = aws_customer_gateway.onprem.id
  transit_gateway_id  = aws_ec2_transit_gateway.core.id
  type                = "ipsec.1"

  static_routes_only = false

  tags = {
    Name = "onprem-vpn"
  }
}
```

Production implementations should explicitly manage related:

- Transit Gateway attachments.
- TGW route tables.
- Route propagation.
- VPC route tables.
- Customer Gateway configuration.
- Security policies.

Sensitive values should be managed using appropriate secret-management mechanisms rather than committed directly to source control.

## Cost Considerations

VPN connectivity introduces networking costs that should be evaluated alongside:

- Transit Gateway costs.
- Data processing.
- Cross-Region traffic.
- Internet data transfer.
- Direct Connect alternatives.
- Network inspection infrastructure.

For high-volume hybrid workloads, compare VPN with Direct Connect where appropriate.

A typical architectural decision considers:

```text
Bandwidth
+
Latency
+
Reliability
+
Security
+
Operational Complexity
+
Cost
```

VPN is often operationally simpler than dedicated connectivity, but its Internet-based underlay may have different performance and availability characteristics.

## Disaster Recovery

Document VPN connectivity as part of the disaster recovery architecture.

Record:

```text
VPN Connection ID
Customer Gateway
Tunnel endpoints
Tunnel configuration
BGP configuration
AWS route tables
TGW route tables
Propagation
Customer routes
Firewall rules
DNS dependencies
```

Keep customer gateway configuration reproducible.

For critical environments, test:

- Tunnel failure.
- Customer gateway failure.
- Firewall failure.
- ISP failure.
- BGP reconvergence.
- AWS route recovery.
- Application reconnection.

Do not consider VPN disaster recovery complete until failover has been tested end-to-end.

## Production Example

Consider an application hosted in AWS:

```text
AWS VPC
10.10.0.0/16
```

The application calls:

```text
On-Premises API
172.16.10.50:443
```

The VPN tunnels report:

```text
Tunnel 1: UP
Tunnel 2: UP
```

The application still receives timeouts.

The troubleshooting process finds:

```text
VPC Route:
172.16.0.0/16 -> TGW
```

The TGW route table contains:

```text
172.16.0.0/16 -> VPN Attachment
```

The VPN is operational.

BGP is established.

However, the on-premises router has no route for:

```text
10.10.0.0/16
```

Therefore:

```text
AWS Application
      |
      v
VPC Route
      |
      v
TGW
      |
      v
VPN
      |
      v
On-Premises API
      |
      X
Return route missing
```

The VPN itself is healthy. The application fails because the return path is incomplete.

This distinction is essential during incident response: **do not replace or reconfigure a healthy VPN when the actual failure is routing outside the tunnel.**

## Interview Traps

### "VPN Tunnel UP Means Traffic Can Flow"

Incorrect.

Tunnel establishment and data-plane routing are separate concerns.

### "BGP UP Means All Routes Are Available"

Incorrect.

The BGP session can be healthy while specific prefixes are absent or filtered.

### "Both Tunnels Exist, So the Connection Is Highly Available"

Not necessarily.

Customer-side firewalls, routers, ISPs, and routing convergence must also support failover.

### "AWS Route Tables Are Enough"

Incorrect.

The customer network must have the corresponding return routes.

### "VPN Encryption Replaces Security Groups"

Incorrect.

VPN provides encrypted connectivity; Security Groups and other controls still govern workload access.

### "A TCP Timeout and Connection Refused Mean the Same Thing"

Incorrect.

A timeout commonly indicates packet loss, routing, or filtering.

A refusal usually means the destination is reachable but no service is accepting the connection on that port.

### "If Ping Fails, the Application Is Unreachable"

Not necessarily.

ICMP may be intentionally blocked while TCP 443 or another application protocol remains reachable.

Test the actual application protocol.

### "VPN Is Always the Right Hybrid Connectivity Solution"

Not necessarily.

Bandwidth, latency, operational requirements, resilience, and cost may justify Direct Connect or another architecture.

## Production Troubleshooting Checklist

```text
[ ] Identify source workload
[ ] Identify source IP
[ ] Identify source subnet
[ ] Identify source VPC
[ ] Identify destination IP
[ ] Identify destination port
[ ] Identify destination network
[ ] Verify source and destination CIDRs
[ ] Check for CIDR overlap
[ ] Verify VPN connection ID
[ ] Verify customer gateway
[ ] Verify VPN attachment
[ ] Check Tunnel 1 state
[ ] Check Tunnel 2 state
[ ] Check tunnel telemetry
[ ] Check IKE negotiation
[ ] Check IPsec negotiation
[ ] Check pre-shared key
[ ] Check DPD behavior
[ ] Check NAT traversal
[ ] Check firewall rules for VPN negotiation
[ ] Check AWS VPC route table
[ ] Check TGW route table if applicable
[ ] Check VPN route propagation
[ ] Check static routes if applicable
[ ] Check BGP session if applicable
[ ] Check advertised prefixes
[ ] Check received prefixes
[ ] Check route filtering
[ ] Check customer-side return route
[ ] Check customer firewall
[ ] Check NAT/SNAT/DNAT
[ ] Check Security Groups
[ ] Check Network ACLs
[ ] Check DNS resolution
[ ] Test TCP connectivity
[ ] Test application protocol
[ ] Check MTU if large packets fail
[ ] Check VPC Flow Logs
[ ] Check customer firewall logs
[ ] Check packet captures where available
[ ] Check for asymmetric routing
[ ] Review recent infrastructure changes
[ ] Test tunnel failover
[ ] Validate application recovery behavior
```

## Key Takeaways

- **VPN tunnel health and application connectivity are separate concerns**; always validate IKE/IPsec state, routing, security controls, and application behavior independently.
- **A complete hybrid route requires both forward and return paths**, including AWS VPC/TGW routes and customer-side routing.
- **BGP being established does not guarantee correct routing**; verify the actual prefixes being advertised, received, propagated, and filtered.
- **Production VPN reliability depends on the entire path**, including both tunnels, customer gateways, firewalls, ISPs, routing convergence, and application retry behavior.
- **Troubleshoot from the network layer upward**, using tunnel telemetry, route inspection, firewall logs, Flow Logs, packet captures, and application-level tests to isolate the failing layer.