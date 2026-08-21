# 13- Direct Connect and VPN Encryption

## Overview

Hybrid AWS architectures commonly use **AWS Direct Connect** as a private connectivity path and **AWS Site-to-Site VPN** as an encrypted backup or complementary path. These technologies solve different networking problems, and their security properties should be understood independently.

Direct Connect provides a dedicated network connection between an AWS environment and an external network. It does not automatically provide application-layer encryption or IPsec encryption for every traffic flow.

Site-to-Site VPN uses **IPsec** to encrypt traffic across an IP network, typically the public Internet. It provides confidentiality and integrity for traffic traversing the VPN tunnels.

A production hybrid architecture may therefore look like:

```text
                         Corporate Network
                                |
                         Enterprise Firewall
                                |
                 +--------------+--------------+
                 |                             |
                 v                             v
          Direct Connect                 Internet
          Private Path                       |
                 |                            v
                 |                     IPsec VPN
                 |                            |
                 +-------------+--------------+
                               |
                               v
                        Transit Gateway
                               |
                    +----------+----------+
                    |          |          |
                    v          v          v
                  VPC A      VPC B      VPC C
```

The important distinction is:

```text
Direct Connect
    =
Private connectivity

VPN
    =
Encrypted IPsec connectivity
```

A private network path and an encrypted network path are not interchangeable security concepts.

---

## Security Model

A useful way to reason about hybrid connectivity is to separate the security properties being provided.

| Property | Direct Connect | Site-to-Site VPN |
|---|---|---|
| Dedicated/private connectivity | Yes | No |
| IPsec tunnel encryption | Not inherent | Yes |
| Traffic confidentiality | Depends on encryption configuration | Provided by IPsec |
| Traffic integrity | Depends on protocol/configuration | Provided by IPsec |
| Authentication | Depends on higher-level protocols and configuration | IPsec authentication |
| Application-layer TLS | Supported | Supported |
| Internet traversal | No | Typically yes |
| Network-level encryption | Requires appropriate Direct Connect encryption capability | Built into IPsec |
| Suitable as VPN backup | Yes | Yes |

Direct Connect should therefore not be described simply as "encrypted networking."

A more accurate architecture statement is:

> Direct Connect provides private connectivity, while IPsec VPN provides encrypted network tunnels.

---

## Why Encryption Still Matters Over Direct Connect

It is common to hear:

> "Direct Connect is private, so encryption is unnecessary."

That is an incomplete security decision.

Direct Connect traffic does not inherently mean that every byte transmitted is cryptographically protected from end to end.

For sensitive workloads, encryption requirements should be evaluated independently of transport.

Examples include:

- Customer data
- Financial information
- Credentials
- Personally identifiable information
- Internal authentication traffic
- Database traffic
- Service-to-service communication

An organization may therefore choose:

```text
Direct Connect
      |
      v
Private network path
      |
      v
TLS
      |
      v
Application
```

instead of relying solely on the privacy of the underlying connectivity.

---

## Encryption Layers

Production systems commonly use defense in depth.

```text
Application
    |
    | TLS / mTLS
    v
Transport
    |
    | TCP
    v
Network
    |
    | IP
    v
VPN / Direct Connect
    |
    v
Physical / Provider Network
```

Each layer provides different security properties.

| Layer | Example | Primary purpose |
|---|---|---|
| Application | mTLS | Application identity and encryption |
| Transport | TLS | Confidentiality and integrity |
| Network | IPsec | Network-level encryption |
| Connectivity | Direct Connect | Private network transport |
| Access control | Security Groups | Traffic authorization |
| Identity | IAM / application auth | Authentication and authorization |

Senior-level network design avoids treating one security mechanism as a replacement for every other mechanism.

---

## Site-to-Site VPN and IPsec

AWS Site-to-Site VPN establishes encrypted tunnels using IPsec.

Conceptually:

```text
Corporate Router
       |
       | Encrypted IPsec tunnel
       |
       v
    Internet
       |
       | Encrypted IPsec tunnel
       |
       v
AWS VPN Endpoint
       |
       v
Transit Gateway / Virtual Private Gateway
       |
       v
VPC
```

The public network carries encrypted packets rather than the original application payload in plaintext.

A simplified packet flow is:

```text
Application Data
      |
      v
IP Packet
      |
      v
IPsec Encapsulation
      |
      v
Encrypted Packet
      |
      v
Internet
      |
      v
IPsec Decapsulation
      |
      v
Original IP Packet
      |
      v
Application
```

---

## What IPsec Provides

IPsec is a suite of protocols and mechanisms designed to secure IP communication.

The primary security properties are:

### Confidentiality

The payload is encrypted so that intermediate network operators cannot normally inspect the protected application traffic.

### Integrity

The receiver can detect whether protected traffic has been modified.

### Authentication

The endpoints establish trust using configured authentication mechanisms.

### Replay Protection

IPsec can detect and reject replayed packets using sequence information and anti-replay mechanisms.

These properties make IPsec suitable for protecting network traffic across an untrusted transport such as the public Internet.

---

## IPsec Tunnel Architecture

A simplified tunnel looks like:

```text
Private Network A
10.20.0.0/16
      |
      v
Customer Gateway
      |
      | Outer IP header
      | Encrypted inner payload
      |
      v
Internet
      |
      v
AWS VPN Endpoint
      |
      v
10.0.0.0/16
Private AWS Network
```

The outer packet provides transport information required to deliver the encrypted packet between VPN endpoints.

The protected inner packet contains the original private network traffic.

Conceptually:

```text
Outer Header
+
Encrypted Inner Packet
```

The intermediate Internet does not need to understand the private destination inside the encrypted payload.

---

## IPsec Components

IPsec deployments involve several concepts that are useful when troubleshooting VPNs.

| Concept | Purpose |
|---|---|
| IKE | Negotiates security associations |
| IKE Phase 1 | Establishes the secure management/authentication channel |
| IKE Phase 2 | Establishes IPsec security associations for data |
| IPsec | Protects data traffic |
| Encryption algorithm | Provides confidentiality |
| Integrity algorithm | Detects modification |
| Authentication | Establishes peer trust |
| PFS | Strengthens key separation |
| Rekeying | Replaces cryptographic keys |

Modern production configurations should use strong, mutually supported cryptographic algorithms and avoid obsolete algorithms.

---

## IKE Negotiation

Before protected data can flow, the VPN endpoints need to establish the cryptographic parameters.

A simplified sequence is:

```text
Customer Gateway                    AWS VPN
       |                               |
       | -------- IKE negotiation ---->|
       |                               |
       |<------- Authentication -------|
       |                               |
       |<------ Security parameters -->|
       |                               |
       |====== IPsec tunnel ===========|
       |                               |
       |------ Encrypted traffic ----->|
```

If IKE negotiation fails, the IPsec tunnel cannot become operational.

Possible causes include:

- Authentication mismatch
- Unsupported algorithms
- Incorrect configuration
- Network reachability problems
- Firewall restrictions
- Incorrect peer addresses
- Parameter incompatibility

---

## IKE Phase 1

IKE Phase 1 establishes a secure control channel between the VPN peers.

The peers negotiate parameters such as:

- Encryption algorithm
- Integrity algorithm
- Diffie-Hellman group
- Authentication mechanism
- Lifetime

The exact supported options depend on the AWS VPN configuration and customer gateway implementation.

A simplified model is:

```text
Customer Gateway
      |
      | IKE
      v
AWS VPN Endpoint
      |
      v
Secure IKE SA
```

The IKE security association protects subsequent negotiation.

---

## IKE Phase 2

IKE Phase 2 establishes the security associations used to protect application traffic.

Conceptually:

```text
IKE Phase 1
     |
     v
Secure control channel
     |
     v
IKE Phase 2
     |
     v
IPsec Security Association
     |
     v
Encrypted application traffic
```

If Phase 1 succeeds but Phase 2 fails, the VPN may appear partially operational while data traffic remains unavailable.

This distinction is important during troubleshooting.

---

## Perfect Forward Secrecy

Perfect Forward Secrecy, commonly abbreviated **PFS**, provides stronger key independence.

The goal is to ensure that compromise of a long-term key does not automatically expose historical session traffic encrypted with independently derived session keys.

Conceptually:

```text
Long-Term Authentication
          |
          v
     Key Exchange
          |
          v
     Session Key A
          |
          v
      Traffic A

Later:

     Key Exchange
          |
          v
     Session Key B
          |
          v
      Traffic B
```

Session keys should not simply be reused indefinitely.

PFS is particularly relevant for sensitive enterprise traffic and should be considered as part of the organization's cryptographic policy.

---

## Direct Connect Encryption

Direct Connect and VPN should not be treated as equivalent.

Direct Connect can provide private connectivity without automatically turning every packet into an IPsec-encrypted packet.

For workloads requiring encryption over Direct Connect, AWS provides supported options for encrypting Direct Connect traffic depending on the connection architecture and service capabilities.

The design should explicitly determine whether encryption is required:

```text
Direct Connect
      |
      +---- Private transport only
      |
      +---- Supported link-level encryption
      |
      +---- Application TLS
      |
      +---- Additional VPN overlay where appropriate
```

The correct choice depends on compliance, threat model, performance requirements, and operational complexity.

---

## MACsec for Direct Connect

For supported Direct Connect configurations, **MACsec** can provide Layer 2 encryption for traffic between compatible customer infrastructure and AWS infrastructure.

Conceptually:

```text
Customer Router
      |
      | MACsec protected Ethernet traffic
      |
      v
Direct Connect
      |
      v
AWS
```

MACsec operates at the Ethernet layer rather than creating an IPsec tunnel between application networks.

This distinction matters:

```text
MACsec
  =
Layer 2 link encryption

IPsec
  =
Network-layer encrypted tunnel
```

MACsec is therefore particularly relevant when the requirement is to encrypt the Direct Connect link itself.

Availability and exact support depend on the Direct Connect connection type, location, hardware, and AWS regional capabilities.

---

## Direct Connect + IPsec Overlay

An organization may also use VPN-style encryption over a private Direct Connect path in architectures where that design is appropriate.

Conceptually:

```text
Application
    |
    v
IPsec
    |
    v
Direct Connect
    |
    v
Private network
```

This can provide defense in depth:

```text
Private connectivity
+
Cryptographic protection
```

However, adding an overlay increases operational complexity and may introduce:

- Additional MTU considerations
- Additional routing complexity
- Encryption overhead
- More failure modes
- More monitoring requirements
- More troubleshooting complexity

Do not add encryption layers simply because they sound more secure. The design should satisfy a specific security or compliance requirement.

---

## TLS Over Direct Connect

For application-level security, TLS remains highly relevant.

Example:

```text
Django
   |
 HTTPS / TLS
   |
   v
Corporate API
```

The underlying transport may be:

```text
Direct Connect
```

or:

```text
VPN
```

The application security model remains consistent.

This is often preferable because application-layer encryption remains effective even if the network topology changes.

---

## mTLS for Service-to-Service Communication

Microservices communicating across a hybrid network can use mutual TLS.

For example:

```text
AWS Service
     |
     | mTLS
     |
     v
Corporate Service
```

Both sides authenticate using certificates.

This provides:

- Encryption
- Service identity
- Mutual authentication
- Protection against unauthorized clients

A typical architecture could be:

```text
FastAPI
   |
   | mTLS
   v
Corporate gRPC Service
   |
   v
PostgreSQL
```

The network layer still provides connectivity, but service identity is enforced at the application layer.

---

## Database Encryption

Database traffic should be considered separately from network encryption.

For PostgreSQL:

```text
Django / FastAPI
      |
      | TLS
      v
PostgreSQL
```

Even if the traffic travels through Direct Connect:

```text
Application
      |
      | TLS
      v
Direct Connect
      |
      v
Corporate PostgreSQL
```

This provides defense in depth.

If VPN becomes active:

```text
Application
      |
      | TLS
      v
IPsec VPN
      |
      v
Corporate PostgreSQL
```

The database still receives encrypted application traffic.

---

## Encryption and AWS Service Architecture

A hybrid environment may contain:

```text
AWS
 |
 +-- Django
 +-- FastAPI
 +-- EKS
 +-- Redis
 +-- Kafka
 +-- Celery
 |
 +-- Transit Gateway
 |
 +-- Direct Connect
 +-- VPN
 |
Corporate
 |
 +-- PostgreSQL
 +-- Active Directory
 +-- Internal APIs
 +-- Kafka
```

Each communication path should have an explicit security requirement.

| Traffic | Recommended consideration |
|---|---|
| Django → Corporate API | TLS |
| FastAPI → gRPC service | TLS / mTLS |
| Application → PostgreSQL | PostgreSQL TLS |
| Application → Redis | TLS where supported/required |
| Kafka clients → Kafka | TLS and authentication |
| AWS → Corporate network | Direct Connect / VPN |
| Administrative access | Strong authentication + encryption |
| Backup traffic | Encryption in transit and at rest |

---

## Encryption in Transit vs Encryption at Rest

These are separate controls.

### Encryption in Transit

Protects data while it moves:

```text
Application
    |
    | TLS / IPsec
    v
Network
    |
    v
Database
```

### Encryption at Rest

Protects stored data:

```text
Application
    |
    v
Database
    |
    v
Encrypted Storage
```

A production security architecture often requires both.

```text
             Data
               |
       +-------+-------+
       |               |
       v               v
   In Transit        At Rest
       |               |
    TLS/IPsec       Storage Encryption
```

---

## Direct Connect and VPN Security Comparison

| Characteristic | Direct Connect | VPN |
|---|---|---|
| Primary purpose | Private connectivity | Encrypted connectivity |
| Transport | Dedicated connectivity | IP network / Internet |
| IPsec encryption | No by default | Yes |
| Link-level encryption | Supported options such as MACsec where applicable | Not applicable |
| Application TLS | Recommended where required | Recommended where required |
| Public Internet dependency | No | Typically yes |
| Encryption overhead | Depends on chosen mechanism | IPsec processing |
| Operational complexity | Network/provider dependent | Tunnel and crypto configuration |
| Backup suitability | Primary | Common backup |

---

## Performance Implications

Encryption has a computational cost.

A simplified model is:

```text
Application
    |
    v
Encryption
    |
    v
Network
```

CPU resources may be required to encrypt and decrypt traffic.

The practical impact depends on:

- Throughput
- Packet size
- Encryption algorithms
- Hardware acceleration
- Network appliance capacity
- Instance type
- Number of tunnels
- Traffic patterns

For high-throughput systems, benchmark the actual architecture rather than assuming encryption will or will not become a bottleneck.

---

## MTU and Fragmentation

Encapsulation adds overhead.

For IPsec:

```text
Original packet
     |
     +---- IPsec headers/trailers
     |
     v
Larger packet
```

If the resulting packet exceeds the available path MTU, fragmentation or packet-size problems can occur.

This can manifest as:

- Large requests failing
- TLS handshakes behaving unexpectedly
- gRPC streams becoming unstable
- Database connections appearing unreliable
- Certain APIs working while larger payloads fail

This is why MTU problems are often mistaken for application problems.

---

## Path MTU Discovery

Applications may send larger packets than the VPN path can carry efficiently.

A useful diagnostic approach is to test progressively smaller packets and inspect fragmentation behavior.

For Linux:

```bash
ping -M do -s 1400 <destination>
```

The appropriate payload size depends on the actual path and encapsulation overhead.

Do not blindly copy a specific MTU value into production. Determine the effective MTU for the actual network path.

---

## Encryption and Latency

VPN encryption can introduce additional processing and may use a path with different network characteristics from Direct Connect.

A common architecture is:

```text
Normal:
Application
   |
Direct Connect
   |
Corporate

Failure:
Application
   |
IPsec VPN
   |
Internet
   |
Corporate
```

The backup path may therefore have:

- Higher latency
- Different jitter
- Lower bandwidth
- Different packet-loss characteristics

Applications should tolerate these changes.

---

## Encryption and Failover

Encryption configuration must be compatible with the HA strategy.

Suppose:

```text
Primary:
Direct Connect + TLS

Backup:
VPN + IPsec + TLS
```

This is a strong layered design:

```text
                    +-- Direct Connect --+
                    |                    |
Application -- TLS -+                    +-- Corporate
                    |                    |
                    +-- IPsec VPN -------+
```

The application remains protected regardless of which network path is active.

---

## VPN Tunnel Redundancy

A Site-to-Site VPN connection generally provides two tunnels.

Conceptually:

```text
Corporate Gateway
      |
      +--------- Tunnel A --------- AWS
      |
      +--------- Tunnel B --------- AWS
```

The tunnels should be monitored independently.

A healthy VPN connection should not be interpreted as:

```text
Both tunnels definitely healthy
```

Validate each tunnel and the routing state associated with it.

---

## Authentication and Key Management

VPN security depends on cryptographic credentials being managed correctly.

Common considerations include:

- Pre-shared keys
- Certificate-based authentication where supported
- Key rotation
- Secrets storage
- Access control
- Configuration management
- Audit logging

Do not store VPN secrets directly in:

- Git repositories
- Public CI/CD logs
- Docker images
- Terraform state without appropriate protection
- Application source code

Secrets should be managed through appropriate secret-management systems and access controls.

---

## Infrastructure as Code

Hybrid network configuration should preferably be managed through infrastructure as code.

For example, Terraform can manage supported AWS VPN resources.

```hcl
resource "aws_vpn_connection" "corporate" {
  customer_gateway_id = aws_customer_gateway.corporate.id
  transit_gateway_id  = aws_ec2_transit_gateway.network.id
  type                = "ipsec.1"

  static_routes_only = false

  tags = {
    Name = "corporate-vpn"
  }
}
```

The actual production configuration should also account for:

- BGP
- Routing
- Tunnel options
- Security controls
- Monitoring
- Secrets
- Dependencies
- Change management

Never treat a VPN resource definition as the complete network configuration.

---

## Secrets and CI/CD

CI/CD systems should not expose VPN credentials.

Avoid:

```text
GitHub Actions
      |
      v
echo "$VPN_PSK"
```

in a way that allows the secret to appear in logs.

Prefer:

```text
CI/CD
  |
  v
Secret Manager / Protected Secret
  |
  v
Deployment Process
```

Infrastructure pipelines should also restrict who can modify:

- VPN configuration
- Customer gateways
- Routing policies
- Encryption parameters
- Direct Connect settings

Network configuration changes can affect the security boundary of an entire organization.

---

## Security Groups and Network Controls

Encryption does not replace authorization.

For example:

```text
IPsec VPN
    |
    v
Transit Gateway
    |
    v
VPC
    |
    v
Security Group
```

The VPN can establish a secure tunnel while Security Groups still restrict which resources can communicate.

A secure architecture therefore combines:

```text
Encryption
+
Routing
+
Firewalling
+
Security Groups
+
Authentication
+
Authorization
```

---

## Route Filtering

Security should also be considered at the routing layer.

Suppose the corporate network advertises:

```text
10.0.0.0/8
```

when AWS only expects:

```text
10.20.0.0/16
```

The broader route can unintentionally expose or redirect traffic.

Use controlled prefix advertisements and route filtering.

A production design should explicitly document:

```text
Advertised AWS prefixes
Advertised corporate prefixes
Allowed routes
Preferred routes
Backup routes
```

---

## DNS Security

Encryption does not automatically secure DNS.

Hybrid environments often depend on:

```text
AWS
 |
Route 53 Resolver
 |
DNS forwarding
 |
Corporate DNS
```

or the reverse direction.

Validate:

- DNS resolution through Direct Connect
- DNS resolution through VPN
- Resolver forwarding
- Split-horizon DNS
- DNS timeouts
- DNS access controls

An application may have a healthy network route but still fail because the hostname cannot be resolved.

---

## Monitoring Encryption Health

Monitor both tunnel state and cryptographic negotiation.

Useful indicators include:

- VPN tunnel state
- IKE negotiation state
- IPsec security association state
- Tunnel uptime
- Rekey events
- Authentication failures
- Packet counters
- Packet loss
- Tunnel throughput
- Latency
- Route changes

A monitoring architecture can be:

```text
VPN / DX
   |
   v
CloudWatch / Network Monitoring
   |
   v
Alerting
   |
   v
Incident Response
```

Monitoring should distinguish between:

```text
Tunnel down
```

and:

```text
Tunnel up but application unavailable
```

---

## Logging and Auditing

Security-sensitive network changes should be auditable.

Capture relevant events such as:

- VPN configuration changes
- Direct Connect changes
- Route changes
- Transit Gateway changes
- Customer gateway changes
- IAM activity
- Infrastructure deployment events

AWS CloudTrail can provide audit visibility for supported AWS API activity.

Network telemetry can be complemented by:

- VPC Flow Logs
- Transit Gateway Flow Logs where applicable
- Firewall logs
- Application logs
- VPN operational metrics

The objective is to correlate:

```text
Configuration Change
        |
        v
Network Event
        |
        v
Application Impact
```

---

## Compliance Considerations

Encryption requirements should be derived from:

- Data classification
- Regulatory requirements
- Contractual requirements
- Organizational security standards
- Threat model

Examples of requirements may include:

```text
Sensitive data
    |
    +---- Encryption in transit
    |
    +---- Encryption at rest
    |
    +---- Strong authentication
    |
    +---- Key rotation
    |
    +---- Audit logging
```

Do not assume that "private connectivity" automatically satisfies an organization's encryption requirement.

---

## Common Mistakes

### Assuming Direct Connect Is Automatically Encrypted

Direct Connect provides private connectivity but should not automatically be treated as end-to-end cryptographic protection.

### Treating VPN as the Only Security Control

IPsec encrypts network traffic but does not replace application authentication or authorization.

### Encrypting Everything Without a Requirement

Additional encryption layers can increase:

- CPU usage
- MTU complexity
- Operational complexity
- Troubleshooting difficulty

Apply encryption deliberately.

### Ignoring Application TLS

A private network is not necessarily a substitute for application-layer encryption.

### Forgetting MTU Overhead

IPsec encapsulation changes packet size and can create fragmentation problems.

### Using Weak Cryptographic Parameters

Avoid obsolete algorithms and configurations that do not meet current organizational security requirements.

### Hardcoding Pre-Shared Keys

Secrets should never be embedded directly into source code or committed to repositories.

### Forgetting Key Rotation

Long-lived credentials increase security exposure.

### Ignoring VPN Tunnel Redundancy

One tunnel may fail while another remains healthy. Monitor both independently.

### Not Testing Rekeying

A tunnel can work for hours or days and fail when a cryptographic lifetime or rekey event occurs.

### Assuming Encryption Solves Authorization

Encrypted traffic can still reach an unauthorized service if routing and access controls are too permissive.

### Ignoring DNS

Applications can fail even when the encrypted network path is healthy if DNS resolution is unavailable.

---

## Production Design Patterns

### Pattern: Direct Connect + TLS

```text
AWS
 |
 | TLS
 v
Direct Connect
 |
 v
Corporate
```

Use when:

- Direct Connect is the preferred private path
- Application-level encryption is required
- VPN is not required for the primary workload

### Pattern: Direct Connect + VPN Backup

```text
             +-- Direct Connect --+
             |                    |
AWS -- TLS --+                    +-- Corporate
             |                    |
             +---- IPsec VPN -----+
```

Use when:

- Direct Connect is primary
- VPN provides disaster recovery connectivity
- Application traffic should remain encrypted

### Pattern: Direct Connect + Link Encryption + TLS

```text
AWS
 |
 | Application TLS
 |
 | Link-level encryption
 |
Direct Connect
 |
Corporate
```

Use when:

- Compliance requires link-level encryption
- Direct Connect infrastructure supports the required encryption capability
- Application-layer encryption is also required

### Pattern: VPN + TLS

```text
AWS
 |
 | TLS
 |
 | IPsec
 |
Internet
 |
Corporate
```

Use when:

- VPN is the primary connectivity mechanism
- Internet transport is required
- Application-level encryption is also required

---

## Troubleshooting Workflow

When encrypted hybrid connectivity fails, isolate the problem by layer.

```text
Application
    |
    v
DNS
    |
    v
Security Group / Firewall
    |
    v
Route
    |
    v
Transit Gateway
    |
    v
VPN / Direct Connect
    |
    v
BGP / IKE / IPsec
    |
    v
Underlying connectivity
```

### VPN Troubleshooting

Check:

1. Customer gateway reachability.
2. VPN tunnel state.
3. IKE negotiation.
4. IPsec security association.
5. BGP session.
6. Route propagation.
7. Transit Gateway routing.
8. Security Groups.
9. Network ACLs.
10. Corporate firewall rules.
11. DNS resolution.
12. Application connectivity.

### Direct Connect Troubleshooting

Check:

1. Direct Connect connection state.
2. Virtual interface state.
3. BGP session.
4. Advertised prefixes.
5. Learned routes.
6. Direct Connect Gateway associations.
7. Transit Gateway routing.
8. Corporate router configuration.
9. Firewall rules.
10. Application-level encryption.

---

## Security Architecture Example

A production hybrid backend platform might use:

```mermaid
flowchart LR
    APP["Django / FastAPI"]
    TLS["TLS / mTLS"]

    TGW["Transit Gateway"]
    DX["Direct Connect"]
    VPN["IPsec VPN"]

    CORP["Corporate Network"]
    FW["Corporate Firewall"]
    DB["PostgreSQL"]
    API["Internal APIs"]

    APP --> TLS
    TLS --> TGW

    TGW --> DX
    TGW --> VPN

    DX --> FW
    VPN --> FW

    FW --> DB
    FW --> API
```

The architecture provides multiple layers:

```text
Application
    |
TLS / mTLS
    |
Transit Gateway
    |
+---+---+
|       |
DX     VPN
|       |
+---+---+
    |
Firewall
    |
Corporate Services
```

This separation makes it possible to maintain application security even when the underlying network path changes.

---

## Production Checklist

- [ ] Encryption requirements are explicitly documented.
- [ ] Direct Connect is not incorrectly treated as automatic end-to-end encryption.
- [ ] VPN tunnels use approved IPsec configurations.
- [ ] IKE parameters are compatible on both sides.
- [ ] Strong cryptographic algorithms are used.
- [ ] PFS requirements are defined where applicable.
- [ ] Key rotation procedures are documented.
- [ ] Pre-shared keys and other secrets are securely stored.
- [ ] Secrets are excluded from source control.
- [ ] Direct Connect encryption requirements are evaluated.
- [ ] MACsec requirements are evaluated where supported and appropriate.
- [ ] Application TLS is enabled where required.
- [ ] mTLS is considered for sensitive service-to-service communication.
- [ ] Database connections use encryption where required.
- [ ] Kafka encryption and authentication are configured where required.
- [ ] Redis encryption requirements are evaluated.
- [ ] VPN and Direct Connect paths have been tested independently.
- [ ] MTU and fragmentation behavior has been tested.
- [ ] DNS resolution works through the intended connectivity paths.
- [ ] Security Groups enforce least-privilege access.
- [ ] Corporate firewall rules are consistent with the security model.
- [ ] Route advertisements are restricted to required prefixes.
- [ ] VPN tunnel health is monitored independently.
- [ ] IKE and IPsec failures are observable.
- [ ] CloudTrail and network logging provide appropriate audit visibility.
- [ ] Failover does not bypass security controls.
- [ ] Failback has been tested.
- [ ] Application reconnection behavior has been tested.
- [ ] Compliance requirements have been mapped to technical controls.

---

## Interview Traps

### Is Direct Connect Encrypted by Default?

No. Direct Connect provides private connectivity. Encryption requirements must be evaluated separately, including supported link-level encryption capabilities and application-layer encryption.

### Does VPN Replace TLS?

No. IPsec protects network traffic, while TLS protects application communication. They operate at different layers.

### What Does IPsec Provide?

IPsec can provide confidentiality, integrity, authentication, and replay protection for network traffic.

### What Is the Difference Between MACsec and IPsec?

MACsec operates at Layer 2 and protects Ethernet links. IPsec operates at the network layer and protects IP traffic.

### Why Can VPN Cause MTU Problems?

IPsec adds encapsulation overhead, reducing the effective payload size available on the path.

### Does Encryption Guarantee Authorization?

No. Encryption protects traffic; it does not determine whether a client is authorized to access a resource.

### Why Use TLS Over Direct Connect?

Because private connectivity does not necessarily provide the cryptographic guarantees required by the application's security or compliance model.

### Why Use Both IPsec and TLS?

Defense in depth. IPsec protects the network path while TLS protects application communication independently of the underlying network transport.

### Can a VPN Tunnel Be Up While the Application Is Down?

Yes. Tunnel health does not prove that routing, DNS, firewall rules, application ports, or application protocols are functioning.

### Why Is Key Management Important?

Cryptographic security depends on secure credential storage, controlled access, rotation, and protection against accidental disclosure.

## Key Takeaways

- Direct Connect provides private connectivity, while Site-to-Site VPN provides IPsec-based encrypted network connectivity; neither should be treated as a universal replacement for application-layer security.
- Use layered security deliberately: Direct Connect or VPN for connectivity, IPsec or supported link encryption for network protection, and TLS/mTLS for application-level confidentiality and service identity.
- IPsec introduces cryptographic negotiation, encapsulation, MTU overhead, key management, and operational considerations that must be included in production design.
- Encryption does not replace routing, Security Groups, firewalls, authentication, authorization, DNS security, or monitoring.
- A production hybrid design should validate encryption, key rotation, tunnel health, MTU behavior, failover, application reconnection, and end-to-end security controls.