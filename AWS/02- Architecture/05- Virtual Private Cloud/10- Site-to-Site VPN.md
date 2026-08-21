# 10- Site-to-Site VPN

## Overview

AWS Site-to-Site VPN provides encrypted IPsec connectivity between an AWS network and an external network such as an enterprise data center, branch office, or corporate network.

A typical architecture connects an on-premises customer gateway to an AWS virtual private gateway or Transit Gateway:

```text
On-Premises Network
        |
        v
Customer Gateway
        |
        | IPsec VPN
        |
     Internet
        |
        v
AWS VPN Connection
        |
        v
Transit Gateway
        |
        +------------------+
        |                  |
        v                  v
 Production VPC       Shared Services VPC
```

Site-to-Site VPN is particularly useful for hybrid architectures, migration projects, backup connectivity, development environments, and organizations that need private IP connectivity without provisioning a dedicated network circuit.

VPN should be viewed as a complete network path rather than simply an encryption mechanism. Production reliability depends on routing, tunnel health, BGP or static routes, CIDR planning, firewall policy, security groups, DNS, MTU, monitoring, and application behavior.

---

## Core Components

A production AWS Site-to-Site VPN architecture normally involves several components.

| Component | Responsibility |
|---|---|
| Customer Gateway | Represents the customer's on-premises VPN device or software appliance |
| Customer Gateway Device | Actual router/firewall/VPN appliance on the customer side |
| Virtual Private Gateway | AWS-side VPN endpoint attached to a VPC |
| Transit Gateway | Central AWS routing hub for multiple VPCs and hybrid connections |
| VPN Connection | Logical IPsec connection between customer and AWS |
| VPN Tunnels | Redundant encrypted paths within the VPN connection |
| Route Tables | Determine how packets reach remote networks |
| BGP or Static Routing | Exchanges or defines reachable network prefixes |
| Security Groups | Control traffic at supported AWS resources |
| Network ACLs | Subnet-level stateless filtering |
| CloudWatch / Flow Logs | Provide operational visibility |

The two most common AWS-side designs are:

```text
VPN → Virtual Private Gateway → VPC
```

and:

```text
VPN → Transit Gateway → Multiple VPCs
```

For modern multi-VPC environments, Transit Gateway is generally the more scalable architecture.

---

## Why Site-to-Site VPN Exists

Organizations frequently need connectivity between AWS and existing infrastructure without immediately adopting dedicated connectivity.

Common requirements include:

- Accessing an on-premises PostgreSQL database from AWS.
- Connecting AWS applications to corporate APIs.
- Extending enterprise networks into AWS.
- Migrating applications incrementally.
- Providing backup connectivity for Direct Connect.
- Connecting branch offices to AWS.
- Supporting disaster-recovery environments.
- Connecting development or test environments to internal services.

For example:

```text
                    Corporate Network
                           |
                       Firewall
                           |
                    VPN Gateway
                           |
                        Internet
                           |
                    IPsec VPN Tunnel
                           |
                    AWS Transit Gateway
                       /          \
                      /            \
                     v              v
               Production VPC    Data VPC
                    |
                    v
              Django / FastAPI
```

---

## How Site-to-Site VPN Works

At a high level, the customer network and AWS establish an IPsec connection.

```text
Customer Network
      |
      v
Customer Gateway
      |
      | Internet
      |
      v
AWS VPN Endpoint
      |
      v
Transit Gateway / VGW
      |
      v
VPC
```

The VPN provides encrypted communication across the Internet.

The application does not need to understand IPsec.

For example:

```text
FastAPI
   |
   | TCP/5432
   v
172.16.20.50
```

The operating system and network infrastructure route the packet through the VPN.

The application sees an ordinary TCP connection:

```text
Application → Database
```

The network infrastructure handles:

```text
Application
    ↓
VPC routing
    ↓
VPN routing
    ↓
IPsec encryption
    ↓
Internet
    ↓
IPsec decryption
    ↓
Corporate network
    ↓
Database
```

---

## Customer Gateway

A Customer Gateway represents the customer-side endpoint configuration in AWS.

The actual customer gateway device may be:

- Enterprise router
- Firewall
- VPN appliance
- Software-based VPN appliance

Examples of customer-side technologies include:

- Cisco
- Fortinet
- Palo Alto Networks
- Juniper
- StrongSwan
- Other supported IPsec devices

The AWS configuration describes how AWS should establish connectivity with the customer-side device.

The customer gateway itself is not necessarily the physical device.

This distinction is important:

```text
Customer Gateway
    =
AWS configuration representing the customer endpoint

Customer Gateway Device
    =
Actual router/firewall/VPN appliance
```

---

## Virtual Private Gateway

A Virtual Private Gateway, or VGW, is an AWS-side VPN endpoint associated with a VPC.

The architecture is:

```text
On-Premises
    |
    v
Customer Gateway
    |
    | IPsec
    |
    v
Virtual Private Gateway
    |
    v
VPC
```

This model is appropriate for relatively simple environments where one VPC needs connectivity to an external network.

As the number of VPCs grows, Transit Gateway becomes more useful.

---

## Transit Gateway-Based VPN

Transit Gateway allows VPN connectivity to become part of a centralized network architecture.

```mermaid
flowchart LR
    ONPREM["On-Premises Network"]
    CGW["Customer Gateway"]
    VPN["Site-to-Site VPN"]
    TGW["Transit Gateway"]

    VPC1["Production VPC"]
    VPC2["Staging VPC"]
    VPC3["Shared Services VPC"]

    ONPREM --> CGW
    CGW --> VPN
    VPN --> TGW

    TGW --> VPC1
    TGW --> VPC2
    TGW --> VPC3
```

This avoids creating separate VPN architectures for every VPC.

Instead:

```text
             On-Premises
                  |
                 VPN
                  |
                  v
           Transit Gateway
            /      |      \
           v       v       v
         VPC A   VPC B   VPC C
```

Transit Gateway route tables then determine which networks can communicate.

---

## VPN Tunnels

A Site-to-Site VPN connection is designed with redundant tunnels.

Conceptually:

```text
                 AWS
                  |
          +-------+-------+
          |               |
       Tunnel 1        Tunnel 2
          |               |
          +-------+-------+
                  |
          Customer Gateway
                  |
             On-Premises
```

The tunnels provide alternative paths between the AWS and customer endpoints.

However, tunnel redundancy is not equivalent to complete end-to-end redundancy.

For example:

```text
Tunnel 1 ----+
             |
Tunnel 2 ----+---- Single Firewall
                    |
                    v
                 Single ISP
```

If the firewall or ISP fails, both tunnels can become unavailable.

Production availability must therefore be evaluated across the entire network path.

---

## IPsec

IPsec provides the security mechanism used by the VPN tunnels.

It provides encrypted network communication across an untrusted transport network.

A simplified flow is:

```text
Application Packet
       |
       v
IPsec Encryption
       |
       v
Encrypted Packet
       |
       v
Internet
       |
       v
IPsec Decryption
       |
       v
Original Packet
```

The application does not need to implement encryption itself for the VPN tunnel.

However, VPN encryption should not replace application-layer security.

Sensitive application protocols should still use appropriate encryption such as TLS.

---

## IKE and IPsec

AWS Site-to-Site VPN uses Internet Key Exchange (IKE) to establish and maintain the security association used by IPsec.

Conceptually:

```text
Customer Gateway
       |
       | IKE negotiation
       |
       v
AWS VPN Endpoint
       |
       v
IPsec Security Association
       |
       v
Encrypted Data Traffic
```

IKE is responsible for negotiating security parameters and establishing the cryptographic context used by the IPsec connection.

The exact supported cryptographic algorithms and tunnel options should be selected according to current AWS recommendations and organizational security requirements.

Avoid selecting legacy cryptographic settings merely because an older device supports them.

---

## Static Routing vs BGP

AWS Site-to-Site VPN can use static routing or dynamic routing through BGP, depending on the architecture.

| Characteristic | Static Routing | BGP |
|---|---|---|
| Route configuration | Manual | Dynamic |
| Operational complexity | Low for small networks | Better for larger networks |
| Automatic route changes | Limited | Supported through route advertisements |
| Scalability | Limited | High |
| Prefix management | Manual | Dynamic |
| Multi-path designs | More difficult | More capable |
| Best suited for | Small/simple environments | Enterprise hybrid networks |

### Static Routing

Static routing explicitly defines remote networks.

For example:

```text
AWS VPC:
10.10.0.0/16

Corporate:
172.16.0.0/16
```

The VPN configuration can define:

```text
172.16.0.0/16 → VPN
```

Static routing is easy to understand but becomes harder to operate as the network grows.

### BGP

BGP allows the customer network and AWS connectivity infrastructure to exchange routes dynamically.

For example:

```text
Corporate Router
       |
       | BGP
       |
       v
AWS VPN
```

The corporate router can advertise:

```text
172.16.0.0/16
172.17.0.0/16
172.18.0.0/16
```

AWS can advertise reachable VPC prefixes.

BGP becomes especially valuable when:

- Multiple prefixes exist.
- Multiple VPN tunnels exist.
- Direct Connect is also present.
- Failover is required.
- Network topology changes frequently.
- Multiple VPCs are connected through Transit Gateway.

---

## BGP Does Not Mean Automatic Correctness

BGP dynamically exchanges routes, but it does not guarantee that the advertised routing policy is correct.

Incorrect advertisements can cause:

- Traffic black holes
- Unexpected paths
- Asymmetric routing
- Accidental network exposure
- Failover problems

Production BGP configurations should therefore include:

- Prefix filtering
- Explicit routing policies
- Route documentation
- Monitoring
- Controlled changes
- Failure testing

Dynamic routing reduces manual configuration but increases the importance of routing governance.

---

## Routing Architecture

A complete packet path requires routes at multiple layers.

Suppose:

```text
AWS VPC:
10.10.0.0/16

On-Premises:
172.16.0.0/16
```

A request from AWS to on-premises may require:

```text
AWS Subnet Route Table
        |
        v
Transit Gateway Route Table
        |
        v
VPN Attachment
        |
        v
Customer Router
        |
        v
Corporate Route Table
        |
        v
Destination
```

The response must have the reverse route:

```text
Destination
    |
    v
Corporate Router
    |
    v
VPN
    |
    v
Transit Gateway
    |
    v
AWS VPC
```

A route in only one direction is insufficient.

---

## Example Route Tables

A private application subnet might contain:

```text
Destination       Target
---------------------------------
10.10.0.0/16      local
172.16.0.0/16     tgw-xxxxxxxx
0.0.0.0/0         nat-xxxxxxxx
```

The Transit Gateway route table might contain:

```text
Destination       Attachment
-------------------------------------
10.10.0.0/16      VPC attachment
172.16.0.0/16     VPN attachment
```

The corporate network needs a route back to:

```text
10.10.0.0/16
```

The exact routing configuration depends on whether the VPN terminates on a Transit Gateway or Virtual Private Gateway.

---

## CIDR Planning

Non-overlapping CIDRs are critical.

Good:

```text
AWS VPC:
10.10.0.0/16

Corporate:
172.16.0.0/16
```

Problematic:

```text
AWS VPC:
10.10.0.0/16

Corporate:
10.10.0.0/16
```

With overlapping CIDRs, the destination address does not uniquely identify which network should receive the traffic.

This affects:

- Routing
- VPN
- Transit Gateway
- VPC Peering
- Kubernetes
- DNS
- Security policies
- Service discovery

CIDR allocation should therefore be treated as an organizational network-design problem rather than an individual VPC configuration detail.

---

## Security Groups and VPN

VPN connectivity does not bypass Security Groups.

For example, suppose an on-premises application needs to access PostgreSQL running in AWS:

```text
On-Premises
    |
    | TCP/5432
    v
VPN
    |
    v
Transit Gateway
    |
    v
Private Subnet
    |
    v
PostgreSQL
```

The destination Security Group should allow only the required source network and port.

Conceptually:

```text
Inbound:
TCP 5432
Source: 172.16.20.0/24
```

Avoid:

```text
TCP 5432
Source: 0.0.0.0/0
```

when the database only needs to be accessed from the corporate network.

---

## Network ACLs

Network ACLs operate at the subnet level and are stateless.

This means both directions must be considered.

For example:

```text
Request:
172.16.20.10 → AWS:5432

Response:
AWS:5432 → 172.16.20.10
```

If the Network ACL blocks the return traffic, the connection can fail even if the Security Group is correct.

For most application architectures, Security Groups should provide the primary workload-level access control, while NACLs should be used intentionally for subnet-level controls.

---

## VPN and DNS

VPN provides IP connectivity, not automatic DNS integration.

Suppose an AWS application needs:

```text
postgres.corp.internal
```

The application must be able to resolve the hostname through an appropriate DNS architecture.

A hybrid DNS design might use Route 53 Resolver:

```text
AWS Application
       |
       v
Route 53 Resolver
       |
       v
VPN
       |
       v
Corporate DNS
       |
       v
postgres.corp.internal
```

A network connection can be completely healthy while DNS resolution remains broken.

Troubleshooting should therefore test DNS independently.

---

## NAT and Site-to-Site VPN

NAT and VPN solve different problems.

NAT primarily provides address translation and outbound Internet connectivity.

VPN provides encrypted connectivity between networks.

For example:

```text
Private EC2
    |
    +---- Internet → NAT Gateway
    |
    +---- Corporate Network → VPN
```

A private subnet may therefore use:

```text
0.0.0.0/0          → NAT Gateway
172.16.0.0/16      → Transit Gateway
```

The more specific corporate route takes precedence over the default Internet route.

This distinction is important when designing private application subnets.

---

## VPN as Direct Connect Backup

A common enterprise pattern is:

```mermaid
flowchart LR
    CORP["Corporate Network"]

    DX["Direct Connect"]
    VPN["Site-to-Site VPN"]

    TGW["Transit Gateway"]

    VPC["Production VPC"]

    CORP --> DX
    CORP --> VPN

    DX --> TGW
    VPN --> TGW

    TGW --> VPC
```

Direct Connect can provide the primary path while VPN provides backup connectivity.

However, failover must be explicitly validated.

Consider:

- BGP advertisements
- Route preference
- Tunnel health
- Customer router behavior
- Firewall state
- DNS behavior
- Application timeouts

Do not assume that simply creating a second connection automatically creates the desired failover behavior.

---

## VPN High Availability

High availability should be designed across failure domains.

A weak design is:

```text
                Single Router
                    |
              +-----+-----+
              |           |
           Tunnel 1    Tunnel 2
              |           |
              +-----+-----+
                    |
                   AWS
```

The router remains a single point of failure.

A stronger architecture considers:

```text
                 Corporate Network
                  /             \
                 /               \
            Router A           Router B
                 |               |
              VPN A           VPN B
                 |               |
                 +-------+-------+
                         |
                         v
                    AWS Network
```

For critical environments, also consider:

- Multiple ISPs
- Multiple firewalls
- Multiple routers
- Separate physical facilities
- Multiple connectivity paths
- Independent power and network dependencies

---

## VPN and Transit Gateway Route Tables

Transit Gateway route tables allow traffic segmentation.

For example:

```text
Production Route Table
    |
    +---- Production VPC
    +---- Corporate Network

Development Route Table
    |
    +---- Development VPC
    +---- Limited Corporate Services
```

This allows an organization to avoid creating unrestricted connectivity between every network.

A useful principle is:

```text
Connect networks intentionally.
Do not connect everything simply because it is technically possible.
```

---

## Network Segmentation Example

Consider:

```text
                 Transit Gateway
                  /           \
                 /             \
                v               v
        Production RT       Development RT
             |                   |
             v                   v
        Production VPC      Development VPC
             |                   |
             +--------+----------+
                      |
                 Corporate VPN
```

Production may require:

```text
Production → Corporate DB
```

while development may require:

```text
Development → Corporate Test API
```

These requirements should be represented through explicit routing and security policies.

---

## Backend Engineering Example

Consider a Django application running in a private subnet.

```text
                    AWS
                     |
             Private Application
                  Subnet
                     |
                  Django
                     |
                     v
             Transit Gateway
                     |
                  VPN
                     |
                     v
             Corporate Network
                     |
                     v
                PostgreSQL
```

Django might connect using:

```python
import os

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DATABASE_NAME"],
        "USER": os.environ["DATABASE_USER"],
        "PASSWORD": os.environ["DATABASE_PASSWORD"],
        "HOST": os.environ["DATABASE_HOST"],
        "PORT": os.getenv("DATABASE_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}
```

The application should treat the database as a potentially higher-latency dependency.

Production configuration should consider:

- Connection timeout
- Connection pooling
- Query timeout
- Retry behavior
- Circuit breaking
- Database failover
- Connection limits
- Observability

A VPN does not make a remote database behave like a local database.

---

## Application Resilience

Hybrid dependencies can fail independently from the application.

A request may travel through:

```text
Django
  |
  v
VPC
  |
  v
Transit Gateway
  |
  v
VPN
  |
  v
Corporate Firewall
  |
  v
PostgreSQL
```

Failures can occur at every layer.

Applications should therefore use explicit failure controls.

### Timeouts

Avoid indefinite network operations.

```python
DATABASE_OPTIONS = {
    "connect_timeout": 5,
}
```

The exact timeout should be chosen based on application requirements and network characteristics.

### Retries

Retries should be:

- Limited
- Exponential
- Jittered
- Applied only where safe
- Avoided for non-idempotent operations unless the operation is explicitly designed for retry

### Circuit Breakers

A circuit breaker can prevent an unhealthy remote service from consuming all application resources.

```text
Healthy
   |
   v
Closed
   |
   | repeated failures
   v
Open
   |
   | recovery period
   v
Half-Open
   |
   +---- success → Closed
   |
   +---- failure → Open
```

---

## VPN and gRPC

gRPC applications can operate over Site-to-Site VPN like other IP-based protocols.

```text
FastAPI / gRPC Client
        |
        v
Transit Gateway
        |
        v
VPN
        |
        v
Corporate gRPC Service
```

However, gRPC's long-lived HTTP/2 connections introduce additional operational considerations:

- Connection persistence
- Keepalive
- Idle timeouts
- Reconnection
- Load balancing
- TLS
- MTU
- Network failure detection

A routing change may affect an existing long-lived connection differently from a new connection.

Application-level reconnect behavior should therefore be tested during VPN failover.

---

## MTU and Fragmentation

VPN introduces additional packet encapsulation.

This can affect the effective MTU of the path.

A simplified packet path is:

```text
Original Packet
      |
      v
IPsec Encapsulation
      |
      v
Larger Transport Packet
      |
      v
Network Path
```

If packet sizes exceed the effective path MTU, fragmentation or packet loss can occur.

Symptoms can include:

- Small requests work.
- Large requests fail.
- TLS handshakes behave inconsistently.
- gRPC streams experience errors.
- Large API responses time out.
- TCP retransmissions increase.

Do not assume that successful `ping` tests prove that application traffic is healthy.

Validate the actual protocols and packet sizes used by the application.

---

## Monitoring

VPN should be monitored as infrastructure, not treated as a set-and-forget configuration.

Important signals include:

| Area | Examples |
|---|---|
| Tunnel health | Tunnel state, availability |
| BGP | Session state, route advertisements |
| Traffic | Bytes, packets, throughput |
| Errors | Packet drops, retransmissions |
| Latency | Round-trip latency |
| Routing | Route changes, propagation |
| Application | Connection failures, timeout rate |
| Security | Unexpected traffic, denied flows |

CloudWatch should be integrated with alerting for important VPN health signals.

VPC Flow Logs can help determine whether traffic reaches the expected network interfaces and whether AWS-side traffic is accepted or rejected.

---

## Troubleshooting Workflow

When an AWS application cannot reach an on-premises service, troubleshoot the packet path from source to destination.

### Verify DNS

```bash
dig database.corp.internal
```

Confirm:

- Name resolves.
- Address is correct.
- DNS server is reachable.

### Verify VPC Routing

Confirm that the source subnet contains the required route:

```text
172.16.0.0/16 → Transit Gateway
```

or the appropriate VGW target.

### Verify Transit Gateway Routing

Check whether the Transit Gateway route table contains the destination prefix.

### Verify VPN State

Confirm that the VPN connection and tunnels are operational.

### Verify BGP

If using BGP, verify that expected prefixes are being advertised and received.

### Verify Customer Routing

The corporate network must know how to reach the AWS VPC CIDR.

### Verify Security Groups

Confirm that the destination allows the source CIDR and required port.

### Verify NACLs

Confirm that both request and response traffic are permitted.

### Verify Firewall Rules

Check the customer-side firewall and any AWS inspection layer.

### Verify the Return Path

A successful outbound route does not guarantee a successful return route.

### Verify Application Behavior

Only after network connectivity is established should application-specific failures become the primary investigation.

---

## Useful AWS CLI Commands

List VPN connections:

```bash
aws ec2 describe-vpn-connections
```

Inspect a specific VPN connection:

```bash
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-xxxxxxxx
```

List customer gateways:

```bash
aws ec2 describe-customer-gateways
```

List Transit Gateways:

```bash
aws ec2 describe-transit-gateways
```

List Transit Gateway VPN attachments:

```bash
aws ec2 describe-transit-gateway-attachments
```

Inspect VPC route tables:

```bash
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=vpc-xxxxxxxx"
```

Inspect Transit Gateway route tables:

```bash
aws ec2 describe-transit-gateway-route-tables
```

Inspect routes in a Transit Gateway route table:

```bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-xxxxxxxx \
  --filters "Name=state,Values=active"
```

These commands are useful for operational investigation. Production configuration should preferably be managed through Infrastructure as Code and reviewed CI/CD workflows.

---

## Infrastructure as Code

VPN infrastructure should be reproducible.

A simplified Terraform configuration might look like:

```hcl
resource "aws_customer_gateway" "on_prem" {
  bgp_asn    = 65000
  ip_address = var.customer_gateway_public_ip
  type       = "ipsec.1"

  tags = {
    Name = "on-prem-cgw"
  }
}

resource "aws_vpn_connection" "on_prem" {
  customer_gateway_id = aws_customer_gateway.on_prem.id
  transit_gateway_id  = aws_ec2_transit_gateway.main.id
  type                = "ipsec.1"

  tags = {
    Name = "on-prem-vpn"
  }
}
```

A production module may additionally manage:

- Customer Gateway
- VPN Connection
- Transit Gateway
- Transit Gateway route tables
- Route propagation
- VPC route tables
- Security Groups
- Network ACLs
- CloudWatch alarms
- Flow Logs
- DNS forwarding

Secrets and cryptographic material should not be committed directly into source control.

---

## Security Considerations

VPN encryption protects traffic across the Internet, but the overall security architecture still requires layered controls.

Recommended practices include:

- Use strong cryptographic settings supported by AWS and the customer device.
- Keep customer gateway firmware and software current.
- Protect VPN configuration secrets.
- Restrict Security Groups to required sources and ports.
- Restrict corporate firewall rules.
- Segment production and non-production networks.
- Monitor route advertisements.
- Enable appropriate logging.
- Avoid broad corporate network access.
- Use TLS for sensitive application protocols.
- Review VPN configuration during security assessments.

A useful security model is:

```text
Routing
   ↓
Can traffic reach the network?

Firewall / Security Group
   ↓
Is traffic allowed?

TLS / mTLS
   ↓
Is traffic encrypted and authenticated?

Application Authorization
   ↓
Is the operation permitted?
```

Each layer solves a different problem.

---

## Cost Considerations

VPN is generally simpler than dedicated connectivity, but it is not cost-free.

Potential cost areas include:

- VPN connection charges
- Transit Gateway attachment charges
- Transit Gateway data processing
- Cross-AZ traffic
- Cross-Region traffic
- NAT Gateway traffic
- Network Firewall processing
- Data transfer

A centralized architecture can reduce operational complexity while introducing additional traffic-processing costs.

For example:

```text
VPC A
  |
  v
Transit Gateway
  |
  v
Inspection VPC
  |
  v
Transit Gateway
  |
  v
VPN
```

may result in additional processing compared with a simpler topology.

Evaluate cost using actual traffic flows rather than only the number of resources.

---

## Performance Considerations

VPN performance depends on the complete path.

Relevant factors include:

- Customer gateway capacity
- Encryption overhead
- Internet path
- VPN tunnel capacity
- Transit Gateway
- Firewall processing
- Packet size
- Application protocol
- Network latency

Do not size a VPN solely by looking at theoretical bandwidth.

Measure:

```text
Throughput
Latency
Packet loss
Jitter
CPU utilization
Tunnel utilization
Application response time
```

For large sustained workloads, Direct Connect may be more appropriate.

VPN remains useful for backup paths even when Direct Connect provides the primary connection.

---

## Disaster Recovery

VPN can serve as both primary connectivity for smaller environments and backup connectivity for larger hybrid architectures.

A common design is:

```text
Primary:
Direct Connect
        |
        v
Transit Gateway
        |
        v
VPC

Backup:
VPN
        |
        v
Transit Gateway
        |
        v
VPC
```

Disaster-recovery testing should verify:

- VPN tunnel establishment
- Route convergence
- BGP behavior
- Security policy
- DNS resolution
- Application reconnect behavior
- Database connectivity
- Connection pool recovery
- Monitoring and alerting

A failover architecture that has never been tested should not be considered reliable.

---

## Common Mistakes

### Treating VPN as a Complete Network Architecture

Creating the VPN connection does not automatically provide application connectivity.

Routes, Security Groups, NACLs, firewalls, DNS, and return paths must also be configured.

### Forgetting the Return Route

The request can reach the corporate network while the response cannot reach AWS.

Always verify both directions.

### Using Overlapping CIDRs

Overlapping address spaces create routing ambiguity.

Plan organizational CIDRs before deploying large hybrid environments.

### Assuming Two Tunnels Mean Complete Redundancy

Both tunnels can depend on the same router, firewall, ISP, or facility.

Analyze the complete failure domain.

### Using Static Routes for a Large Enterprise Network

Static routing becomes difficult to manage as the number of prefixes and connections increases.

BGP is generally more suitable for dynamic enterprise routing.

### Allowing Excessive Security Group Access

Do not allow entire corporate CIDRs to every application simply because the network is trusted.

Restrict access by workload and port.

### Ignoring DNS

Successful IP routing does not guarantee successful hostname resolution.

### Ignoring MTU

VPN encapsulation can reduce effective packet size.

Test actual application traffic, not just basic connectivity.

### Treating VPN Encryption as Application Authentication

IPsec protects the network path, but it does not replace application authentication or authorization.

### Assuming Failover Is Automatic

Creating multiple tunnels or connections does not guarantee the desired route preference and application behavior.

Test failover.

---

## Production Design Checklist

- [ ] AWS and on-premises CIDRs do not overlap.
- [ ] Customer Gateway configuration is documented.
- [ ] Customer gateway devices are appropriately redundant.
- [ ] VPN tunnels are healthy.
- [ ] Routing strategy is explicitly defined.
- [ ] BGP or static routing is intentionally selected.
- [ ] Route advertisements are controlled.
- [ ] AWS route tables contain required routes.
- [ ] Transit Gateway route tables are correctly configured.
- [ ] Corporate routers have AWS return routes.
- [ ] Security Groups permit only required traffic.
- [ ] Network ACLs are correctly configured.
- [ ] Corporate firewalls permit required traffic.
- [ ] Hybrid DNS is configured where required.
- [ ] MTU has been tested.
- [ ] VPN health is monitored.
- [ ] BGP health is monitored where applicable.
- [ ] VPC Flow Logs are enabled where appropriate.
- [ ] Application timeouts are configured.
- [ ] Retry behavior is bounded and safe.
- [ ] Connection pools are sized appropriately.
- [ ] Direct Connect backup requirements are evaluated.
- [ ] Failover has been tested.
- [ ] Disaster recovery procedures are documented.
- [ ] VPN infrastructure is managed through Infrastructure as Code.
- [ ] Configuration changes are reviewed through CI/CD.
- [ ] Network ownership and escalation paths are documented.

---

## Interview Traps

### What Is AWS Site-to-Site VPN?

It provides encrypted IPsec connectivity between an AWS network and an external network such as an on-premises data center.

### What Is the Difference Between a Customer Gateway and a Customer Gateway Device?

The Customer Gateway is the AWS-side configuration representing the external endpoint. The Customer Gateway Device is the actual router, firewall, or VPN appliance.

### How Many Tunnels Does a Typical AWS Site-to-Site VPN Connection Provide?

A VPN connection is designed with two tunnels for redundancy.

### Does Two-Tunnel VPN Guarantee High Availability?

No. Both tunnels can share the same customer router, firewall, ISP, or physical infrastructure.

### What Is the Difference Between VGW and Transit Gateway?

A Virtual Private Gateway is associated with a VPC and is suitable for simpler VPN connectivity. Transit Gateway acts as a centralized routing hub for multiple VPCs and network attachments.

### When Should You Use BGP?

BGP is particularly useful when the environment has multiple prefixes, dynamic routing requirements, multiple connectivity paths, or enterprise-scale hybrid networking.

### Does VPN Automatically Configure VPC Routes?

No. The required routing configuration must be established between the VPC, VPN endpoint, Transit Gateway or VGW, and remote network.

### Does VPN Replace Security Groups?

No. VPN provides network connectivity and encryption. Security Groups still control traffic to supported AWS resources.

### Does VPN Automatically Provide DNS Resolution?

No. DNS must be designed separately.

### Is VPN Better Than Direct Connect?

Neither is universally better. VPN is simpler and useful for rapid deployment and backup connectivity. Direct Connect is better suited to sustained enterprise connectivity requiring dedicated network paths.

### Why Can a VPN Connection Be Healthy While the Application Still Fails?

The VPN tunnel can be operational while routing, DNS, firewall rules, Security Groups, NACLs, MTU, return paths, or the destination application are broken.

### Why Is a VPN Connection Not Equivalent to an Internal VPC Network?

A VPN crosses an external network path and introduces additional latency, failure modes, routing dependencies, and bandwidth constraints.

## Key Takeaways

- AWS Site-to-Site VPN provides encrypted IPsec connectivity between AWS and external private networks, with routing and security controls required in addition to the tunnel itself.
- Production VPN architectures should account for both tunnels, customer-side infrastructure, routing, BGP or static routes, return paths, DNS, MTU, and complete failure domains.
- Transit Gateway provides the preferred scalable hub for integrating VPN connectivity with multiple VPCs and centralized network segmentation.
- VPN is commonly used as primary connectivity for smaller environments or as backup connectivity for Direct Connect in enterprise architectures.
- Reliable hybrid applications must treat VPN connectivity as a distributed-system dependency and use appropriate timeouts, bounded retries, observability, and tested failover procedures.