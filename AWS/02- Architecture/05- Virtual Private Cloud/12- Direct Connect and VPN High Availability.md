# 12- Direct Connect and VPN High Availability

## Overview

Hybrid AWS environments should treat network connectivity as a production dependency with explicit availability, failover, and recovery requirements.

A common enterprise architecture uses **AWS Direct Connect as the primary connectivity path** and **Site-to-Site VPN as a backup path**. This combination provides a private primary network path while retaining an Internet-based alternative when the primary connectivity infrastructure becomes unavailable.

The architecture can be summarized as:

```text
                         Corporate Network
                                |
                         Enterprise Router
                         /               \
                        /                 \
                       v                   v
              Direct Connect           Internet
                    Primary                |
                       |                    v
                       |              Site-to-Site VPN
                       |                  Backup
                       |                    |
                       v                    v
              Direct Connect       Transit Gateway
                  Gateway                 |
                       \                  /
                        \                /
                         +------v-------+
                                |
                         Transit Gateway
                                |
                 +--------------+--------------+
                 |              |              |
                 v              v              v
              VPC A           VPC B           VPC C
```

The important engineering principle is that **having two connectivity mechanisms does not automatically create high availability**.

High availability requires:

- Independent failure domains
- Deliberate routing policy
- BGP configuration
- Correct route propagation
- Sufficient backup capacity
- Health monitoring
- Tested failover
- Application-level retry and recovery behavior

A production design should answer four questions:

1. What is the primary network path?
2. What is the backup path?
3. How does traffic detect and switch away from a failed path?
4. Can the backup path actually support the workload during failure?

---

## Why Hybrid Network High Availability Matters

A hybrid application may depend on services across both AWS and an enterprise network.

For example:

```text
AWS
 |
 +-- Django API
 |
 +-- Redis
 |
 +-- Celery Workers
 |
 +-- EKS
 |
 +-- Transit Gateway
       |
       v
   Direct Connect
       |
       v
Corporate Network
 |
 +-- PostgreSQL
 +-- Active Directory
 +-- Internal APIs
 +-- Kafka
```

If the Direct Connect path fails and there is no backup:

```text
AWS Application
      |
      X
      |
Corporate Service
```

the application may experience:

- Connection timeouts
- Increased request latency
- Failed database queries
- Failed background jobs
- Kafka consumer failures
- Authentication failures
- Service degradation
- Complete application outage

A backup VPN can provide an alternate path:

```text
AWS Application
      |
      +---------------- Direct Connect
      |
      +---------------- VPN
```

The objective is not merely to maintain network connectivity. The objective is to maintain **application availability**.

---

## High Availability Requirements

Before designing the network, define the availability requirements.

Important parameters include:

| Requirement | Example |
|---|---|
| RTO | 5 minutes |
| RPO | Application-dependent |
| Maximum network downtime | 30 seconds |
| Peak traffic | 2 Gbps |
| Normal traffic | 500 Mbps |
| Backup capacity | 2 Gbps |
| Required encryption | TLS / IPsec |
| Primary path | Direct Connect |
| Backup path | Site-to-Site VPN |
| Availability target | 99.9%+ |
| Failure domains | Multiple |

The architecture should then be designed backward from those requirements.

For example:

```text
RTO = 5 minutes
        |
        v
Failover must be automated
        |
        v
Routes must converge automatically
        |
        v
BGP must detect path failure
        |
        v
Backup VPN must be operational
```

---

## Primary and Secondary Connectivity

A common production pattern is:

```text
Primary:
Direct Connect

Secondary:
Site-to-Site VPN
```

The normal traffic path is:

```text
AWS
 |
 v
Transit Gateway
 |
 v
Direct Connect Gateway
 |
 v
Direct Connect
 |
 v
Corporate Network
```

During Direct Connect failure:

```text
AWS
 |
 v
Transit Gateway
 |
 v
Site-to-Site VPN
 |
 v
Internet
 |
 v
Corporate Network
```

The routing system determines which path is preferred.

---

## Recommended Architecture

For a multi-VPC environment, Transit Gateway provides a centralized routing layer.

```mermaid
flowchart TB
    CORP["Corporate Network"]
    R1["Enterprise Router A"]
    R2["Enterprise Router B"]

    DX1["Direct Connect A"]
    DX2["Direct Connect B"]

    DXGW["Direct Connect Gateway"]
    TGW["Transit Gateway"]

    VPN1["VPN Tunnel A"]
    VPN2["VPN Tunnel B"]

    VPC1["Production VPC"]
    VPC2["Shared Services VPC"]
    VPC3["Data VPC"]

    CORP --> R1
    CORP --> R2

    R1 --> DX1
    R2 --> DX2

    DX1 --> DXGW
    DX2 --> DXGW

    DXGW --> TGW

    R1 --> VPN1
    R2 --> VPN2

    VPN1 --> TGW
    VPN2 --> TGW

    TGW --> VPC1
    TGW --> VPC2
    TGW --> VPC3
```

This architecture provides multiple potential paths:

```text
Corporate
   |
   +---- Direct Connect A
   |
   +---- Direct Connect B
   |
   +---- VPN A
   |
   +---- VPN B
```

The exact number of paths should be determined by business requirements and failure-domain analysis.

---

## Failure Domains

Redundancy is only useful when the redundant components do not fail together.

Consider:

```text
Router A
   |
Direct Connect A
   |
Provider A
   |
Facility A
```

and:

```text
Router B
   |
Direct Connect B
   |
Provider A
   |
Facility A
```

Although there are two Direct Connect connections, a provider or facility failure can still affect both.

A stronger design might separate:

```text
Path A:
Router A
    |
Provider A
    |
Facility A
    |
Direct Connect A
```

from:

```text
Path B:
Router B
    |
Provider B
    |
Facility B
    |
Direct Connect B
```

The goal is **failure-domain independence**, not simply component duplication.

---

## Direct Connect Redundancy

A single Direct Connect connection is a single connectivity dependency.

```text
Corporate
    |
Router
    |
Direct Connect
    |
AWS
```

Potential failures include:

- Customer router
- Cross-connect
- Connectivity provider
- Direct Connect location
- Physical network
- AWS connectivity path

A redundant architecture introduces another independent connection:

```text
                    Corporate
                   /         \
                  /           \
             Router A       Router B
                |              |
                v              v
             DX-A            DX-B
                |              |
                +------+-------+
                       |
                       v
                  AWS Network
```

For critical workloads, the two paths should be evaluated for:

- Different routers
- Different interfaces
- Different providers
- Different facilities
- Different physical routes
- Different power domains

---

## VPN Redundancy

AWS Site-to-Site VPN provides two tunnels for a VPN connection.

Conceptually:

```text
Corporate Router
       |
       +------ VPN Tunnel A ------+
       |                          |
       +------ VPN Tunnel B ------+---- Transit Gateway
```

The two tunnels provide tunnel-level redundancy.

However, the customer-side device, Internet connection, or upstream provider may still represent a shared failure domain.

For stronger resilience:

```text
Corporate
   |
   +---- Internet Provider A ---- VPN
   |
   +---- Internet Provider B ---- VPN
```

The customer-side architecture must therefore be considered together with AWS-side tunnel redundancy.

---

## Direct Connect + VPN Failover

The most common hybrid high-availability model is:

```text
                         AWS
                          |
                   Transit Gateway
                    /           \
                   /             \
                  v               v
        Direct Connect          VPN
             Primary            Backup
                  \               /
                   \             /
                    +-----+-----+
                          |
                   Corporate Network
```

Under normal operation:

```text
AWS
 |
 v
Direct Connect
 |
 v
Corporate
```

During failure:

```text
AWS
 |
 v
VPN
 |
 v
Corporate
```

The transition should be controlled through routing rather than manual intervention.

---

## BGP and Failover

BGP is central to dynamic Direct Connect routing.

A simplified model is:

```text
AWS Router
    |
    | BGP
    |
    v
Customer Router
```

The customer and AWS exchange network prefixes.

For example:

```text
Customer advertises:
172.16.0.0/16

AWS advertises:
10.0.0.0/16
```

If the Direct Connect BGP session fails, the corresponding routes can be withdrawn.

The routing system can then select the backup VPN path if its routes remain available.

---

## Route Preference

A high-availability architecture needs deterministic route preference.

Conceptually:

```text
Primary:
Direct Connect

Secondary:
VPN
```

Normal routing:

```text
Destination: 172.16.0.0/16

Preferred:
Direct Connect

Backup:
VPN
```

When Direct Connect fails:

```text
Destination: 172.16.0.0/16

Preferred:
VPN
```

The exact implementation depends on the AWS and customer routing architecture.

Do not rely on undocumented or accidental routing behavior.

---

## Asymmetric Routing

Asymmetric routing occurs when the request and response use different paths.

For example:

```text
AWS
 |
 | Direct Connect
 v
Corporate
 |
 | VPN
 v
AWS
```

This can create problems with:

- Stateful firewalls
- NAT
- Network inspection appliances
- Connection tracking
- Troubleshooting
- Application latency

A high-availability design should explicitly consider both forward and return routing.

The intended path should be:

```text
Request:
AWS → Primary → Corporate

Response:
Corporate → Primary → AWS
```

When the primary path fails:

```text
Request:
AWS → Backup → Corporate

Response:
Corporate → Backup → AWS
```

---

## Route Withdrawal

When a BGP session fails, routes associated with that session can be withdrawn.

Conceptually:

```text
Before failure:

AWS
 |
 +---- DX ----> Corporate
 |
 +---- VPN ---> Corporate

DX preferred
```

After DX failure:

```text
BGP session down
       |
       v
DX routes withdrawn
       |
       v
VPN becomes preferred
```

This enables automated failover.

However, route convergence is not instantaneous.

Applications must tolerate the transition.

---

## Route Convergence

Failover consists of several stages:

```text
Physical Failure
      |
      v
Failure Detection
      |
      v
BGP Session Detection
      |
      v
Route Withdrawal
      |
      v
Route Recalculation
      |
      v
Backup Path Selection
      |
      v
Application Reconnect
```

The total outage duration depends on all of these stages.

Therefore:

```text
Network HA
≠
Instantaneous failover
```

Application design must account for the convergence window.

---

## Application-Level Failover

Network failover alone does not guarantee application recovery.

Consider a Django application maintaining a PostgreSQL connection:

```text
Django
   |
   v
PostgreSQL
   |
Direct Connect
```

If Direct Connect fails, existing TCP connections may remain broken even after VPN routing becomes available.

The application may need to:

- Detect connection failure
- Close stale connections
- Reconnect
- Retry safe operations
- Respect timeouts
- Avoid duplicate writes

For Django:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "application",
        "USER": "application",
        "PASSWORD": "secret",
        "HOST": "postgres.corp.internal",
        "PORT": "5432",
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "connect_timeout": 5,
        },
    }
}
```

Network failover does not automatically repair a TCP connection that was established before the path changed.

---

## Retry Design

Retries should be used carefully.

For idempotent operations:

```text
Request
  |
  v
Network failure
  |
  v
Retry
  |
  v
Success
```

For non-idempotent operations:

```text
POST /payment
      |
      v
Network failure
      |
      X
Response unknown
```

Blindly retrying may result in duplicate operations.

Production applications should use:

- Idempotency keys
- Request timeouts
- Exponential backoff
- Jitter
- Circuit breakers
- Transaction boundaries

For example:

```text
Timeout
   |
   v
Is operation idempotent?
   |
 +---+---+
 |       |
Yes      No
 |       |
 v       v
Retry   Reconcile
```

---

## Direct Connect Failure Scenarios

### Customer Router Failure

```text
Router A
   X
Direct Connect
```

If Router B and Direct Connect B remain available, traffic can fail over.

### Direct Connect Connection Failure

```text
DX-A
 X
```

BGP should withdraw the associated routes.

### Provider Failure

If the connectivity provider fails, a second provider can provide a genuinely independent path.

### Direct Connect Location Failure

Multiple Direct Connect locations may be required for stronger resilience.

### AWS-Side Failure

A redundant connection and alternate path can reduce the blast radius.

### Corporate Firewall Failure

Even perfect AWS connectivity cannot bypass a failed corporate firewall.

### Internet Failure

If VPN is the backup path and the corporate Internet provider fails, VPN failover cannot succeed.

This is why failure-domain analysis must include the entire path.

---

## Failure Matrix

| Failure | DX Primary | VPN Backup | Expected Result |
|---|---:|---:|---|
| DX connection failure | Down | Up | VPN takes over |
| DX router failure | Down | Up | VPN or secondary DX |
| DX provider failure | Down | Up | VPN takes over |
| Internet failure | Up | Down | Direct Connect remains primary |
| Corporate router failure | Down | Depends | Depends on router redundancy |
| VPN tunnel failure | Up | Down | Direct Connect remains primary |
| Both DX paths fail | Down | Up | VPN remains available |
| DX + VPN failure | Down | Down | Hybrid connectivity unavailable |
| Corporate firewall failure | Up | Up | Traffic may still fail |
| Transit Gateway route failure | Up | Up | Both paths may fail |

This matrix should be validated against the actual production architecture.

---

## Backup Capacity Planning

The VPN backup must be capable of carrying the required failure workload.

Suppose:

```text
Normal traffic = 300 Mbps
Peak traffic   = 800 Mbps
```

and the VPN backup can only sustain:

```text
100 Mbps
```

Then the architecture technically has a backup path but does not provide meaningful service continuity.

A better design evaluates:

```text
Required backup capacity
≥
Critical workload traffic
```

For some systems, the requirement may be:

```text
Backup capacity
≥
100% of peak traffic
```

For others, degraded service may be acceptable:

```text
Backup capacity
≥
Critical traffic only
```

The correct value depends on the business requirements.

---

## Capacity During Failure

Capacity planning should include:

```text
Normal traffic
+
Peak traffic
+
Growth
+
Replication
+
Background jobs
+
Failure traffic
```

For example:

```text
Normal:
500 Mbps

Peak:
1.5 Gbps

Replication:
500 Mbps

Required failover capacity:
≥ 2 Gbps
```

Do not assume that a backup link only needs to support average traffic.

---

## Traffic Prioritization During Failure

When the backup path has less capacity than the primary, traffic may need to be prioritized.

Example:

```text
VPN Capacity = 1 Gbps

Priority 1:
API traffic

Priority 2:
Database traffic

Priority 3:
Authentication

Priority 4:
Monitoring

Priority 5:
Bulk replication
```

During failover:

```text
Critical traffic
       |
       v
VPN
       |
       +---- API
       +---- Database
       +---- Authentication

Bulk replication
       |
       v
Throttled / paused
```

This requires cooperation between network and application teams.

---

## Transit Gateway Routing

Transit Gateway provides centralized routing for multiple VPCs.

A hybrid architecture might be:

```text
                 Transit Gateway
                /       |       \
               /        |        \
              v         v         v
       Production    Shared      Data
          VPC        Services     VPC
                         |
                         v
                  Direct Connect
                         |
                         v
                    Corporate
```

VPN attachments can also connect to the Transit Gateway.

```text
Direct Connect
      |
      v
Transit Gateway
      ^
      |
     VPN
```

This simplifies centralized connectivity and allows multiple VPCs to use the same hybrid routing architecture.

---

## Route Table Segmentation

Transit Gateway route tables should be designed intentionally.

For example:

```text
Production TGW Route Table
    |
    +---- Production VPC
    +---- Corporate
    +---- Shared Services

Development TGW Route Table
    |
    +---- Development VPC
    +---- Shared Services
```

This allows network segmentation.

Avoid creating unrestricted connectivity such as:

```text
Every VPC
   ↕
Every VPC
   ↕
Corporate
```

unless the organization explicitly requires it.

---

## Multi-Account High Availability

Large AWS organizations often use multiple accounts:

```text
AWS Organization
 |
 +-- Network Account
 |
 +-- Production Account
 |
 +-- Development Account
 |
 +-- Security Account
 |
 +-- Data Account
```

A centralized networking account can host shared network infrastructure such as:

- Transit Gateway
- Direct Connect Gateway associations
- VPN architecture
- Network inspection
- Centralized logging

Application accounts can then attach VPCs to the shared network architecture.

This separates:

```text
Network ownership
```

from:

```text
Application ownership
```

which can reduce operational coupling.

---

## Multi-Region Considerations

For multi-region architectures, hybrid connectivity needs explicit regional routing.

Example:

```text
                    Corporate
                    /       \
                   /         \
                  v           v
             AWS Region A   AWS Region B
                  |             |
                 VPC           VPC
```

Possible requirements include:

- Regional Direct Connect connectivity
- Transit Gateway in each region
- Inter-region Transit Gateway connectivity
- VPN backup
- Regional route policies
- Application-level failover

Do not assume that connectivity to one AWS Region automatically provides the desired resilience for every other Region.

---

## Encryption Considerations

Direct Connect and VPN have different security characteristics.

| Property | Direct Connect | VPN |
|---|---|---|
| Private network path | Yes | No, uses Internet |
| IPsec | Not inherent | Yes |
| TLS compatibility | Yes | Yes |
| Link-level encryption options | Available for supported configurations | Not applicable |
| Application encryption | Still recommended where required | Still recommended where required |

A common design is:

```text
Primary:
Direct Connect

Backup:
VPN

Application:
TLS
```

The backup path may therefore have stronger network-level encryption while the primary uses a private connectivity path.

The security requirements should be defined independently of the transport path.

---

## Monitoring Strategy

High availability requires monitoring the **state of the entire path**.

Monitor:

```text
Direct Connect
     |
     v
VIF
     |
     v
BGP
     |
     v
Direct Connect Gateway
     |
     v
Transit Gateway
     |
     v
VPN
     |
     v
Customer Router
     |
     v
Application
```

Important metrics include:

- Direct Connect connection state
- VIF state
- BGP session state
- VPN tunnel state
- Tunnel telemetry
- Transit Gateway metrics
- Network traffic
- Packet loss
- Latency
- Route changes
- Application timeout rate
- Database connection errors

---

## Failure Detection

A useful monitoring model is:

```text
Path Health
    |
    +---- Direct Connect
    |       |
    |       +---- Connection
    |       +---- VIF
    |       +---- BGP
    |
    +---- VPN
    |       |
    |       +---- Tunnel A
    |       +---- Tunnel B
    |
    +---- Application
            |
            +---- TCP
            +---- HTTP
            +---- Database
```

Monitoring should distinguish between:

```text
Network path failure
```

and:

```text
Application failure
```

A BGP session being healthy does not mean that the database is reachable.

---

## Synthetic Health Checks

Infrastructure monitoring should be supplemented with end-to-end tests.

For example:

```text
AWS Test Instance
       |
       v
Corporate DNS
       |
       v
Corporate API
       |
       v
Expected response
```

A synthetic test can detect failures that infrastructure metrics may not expose.

For database connectivity:

```bash
nc -vz postgres.corp.internal 5432
```

For an HTTP service:

```bash
curl --fail --connect-timeout 5 \
  https://internal-api.corp.internal/health
```

These tests should be run from appropriate private AWS network locations.

---

## Failover Testing

A high-availability architecture should be tested deliberately.

Do not wait for the first real failure to discover that:

```text
VPN credentials expired
```

or:

```text
BGP routes were never configured correctly
```

or:

```text
VPN capacity is insufficient
```

A controlled test can validate:

```text
Normal
  |
  v
Direct Connect
  |
  v
Disable primary path
  |
  v
BGP route withdrawal
  |
  v
VPN becomes active
  |
  v
Application reconnects
  |
  v
Restore Direct Connect
  |
  v
Traffic returns to primary
```

---

## Failback

Failback is as important as failover.

A common failure scenario is:

```text
DX fails
 |
 v
VPN becomes active
 |
 v
DX recovers
 |
 v
Traffic should return to DX
```

Without deterministic routing policy, traffic may remain on the backup path.

This can cause:

- Unexpected VPN costs
- Reduced bandwidth
- Higher latency
- Unnecessary Internet dependency
- Capacity pressure

Failback should therefore be explicitly tested.

---

## Maintenance Windows

High availability allows planned maintenance without requiring full service interruption.

For example:

```text
Primary DX
    |
Maintenance
    X
    |
Backup VPN
    |
Application remains available
```

The maintenance procedure should include:

1. Confirm backup path health.
2. Confirm backup capacity.
3. Confirm routes.
4. Confirm application health.
5. Drain or disable the primary path.
6. Perform maintenance.
7. Restore the primary path.
8. Verify BGP convergence.
9. Verify traffic returns to the primary.
10. Confirm application metrics normalize.

---

## Application Connection Pools

Network failover can invalidate existing connections.

For PostgreSQL:

```text
Connection Pool
      |
      +-- Connection A → Broken
      +-- Connection B → Broken
      +-- Connection C → Broken
```

The application must eventually create new connections over the restored path.

This is particularly important for:

- Django
- SQLAlchemy
- Celery workers
- Long-running Python processes
- gRPC clients
- Kafka clients

Applications should use reasonable connection timeouts and lifecycle management.

---

## gRPC Considerations

Long-lived gRPC connections can behave differently from short-lived HTTP requests.

Consider:

```text
FastAPI
  |
  | Long-lived gRPC
  v
Corporate Service
```

If Direct Connect fails, an existing TCP connection can break.

The gRPC client must be able to:

- Detect channel failure
- Reconnect
- Resolve the endpoint
- Retry appropriate RPCs
- Avoid duplicate non-idempotent operations

Network failover therefore needs to be validated at the protocol level.

---

## Kafka Considerations

Kafka is particularly sensitive to advertised broker addresses.

A hybrid Kafka architecture might be:

```text
AWS Consumer
     |
     v
Direct Connect
     |
     v
Kafka Cluster
```

During failover:

```text
AWS Consumer
     |
     v
VPN
     |
     v
Kafka Cluster
```

The backup path must provide access not only to the bootstrap endpoint but also to the broker addresses advertised to clients.

Test:

- Bootstrap connection
- Broker connectivity
- Metadata retrieval
- Producer operations
- Consumer operations
- Reconnection after path failure

---

## Celery Considerations

Celery workers can also depend on hybrid network services.

For example:

```text
AWS Celery Worker
      |
      v
Corporate RabbitMQ
```

If the connection breaks:

```text
Celery Worker
      |
      X
Broker
```

Workers need appropriate broker reconnect behavior.

The same general principle applies to Redis-backed Celery deployments.

Avoid assuming that network restoration automatically restores every application connection.

---

## Security Considerations

High availability must not become an excuse for broad network access.

For example:

```text
Primary:
Direct Connect

Backup:
VPN
```

does not mean:

```text
Allow all corporate traffic
```

Security should remain consistent across both paths.

Use:

- Least-privilege Security Groups
- Network ACLs where appropriate
- Corporate firewalls
- Network segmentation
- Route filtering
- Prefix controls
- TLS
- Authentication
- Authorization
- Centralized logging

A particularly important rule is:

> The backup path should enforce the same security policy as the primary path.

Otherwise, failover can silently create a security boundary violation.

---

## Common Mistakes

### Treating Two Paths as Automatically Highly Available

Two network paths can still share:

- Router
- Provider
- Facility
- Firewall
- Internet provider
- Power
- Routing configuration

Analyze the entire failure domain.

### Building a VPN Backup Without Testing It

A configured VPN that has never been tested is not a reliable backup.

### Ignoring Backup Capacity

A 100 Mbps backup path cannot preserve a 2 Gbps workload.

### Forgetting BGP Policy

Incorrect route preference can cause VPN to become primary unexpectedly.

### Forgetting Failback

Traffic may remain on the backup path after Direct Connect recovers.

### Ignoring Existing TCP Connections

Network failover does not transparently repair every established connection.

### Ignoring Asymmetric Routing

Different forward and return paths can break stateful firewalls.

### Making VPN Less Secure Than Direct Connect

The backup path should not bypass required security controls.

### Not Testing Application Protocols

Testing ping alone does not validate:

- PostgreSQL
- gRPC
- Kafka
- HTTPS
- Redis
- Celery

Test the actual application dependency.

### Monitoring Only Infrastructure

A healthy BGP session does not prove application availability.

### Ignoring DNS

DNS resolution can fail independently of network connectivity.

### Designing Only for Failover

Failback is equally important because the backup path may have lower capacity and higher latency.

---

## Operational Runbook

A production runbook should contain the following information.

### Normal State

```text
Primary:
Direct Connect

Secondary:
VPN

Preferred Route:
Direct Connect
```

### Direct Connect Failure

```text
1. Confirm DX failure.
2. Confirm BGP state.
3. Confirm VPN health.
4. Confirm VPN route availability.
5. Verify application connectivity.
6. Monitor traffic migration.
7. Investigate DX failure.
```

### During VPN Operation

Monitor:

- VPN capacity
- Application latency
- Packet loss
- Error rate
- Database connections
- API failures
- Queue backlogs

### Recovery

```text
1. Restore Direct Connect.
2. Confirm BGP session.
3. Confirm routes.
4. Confirm primary path preference.
5. Confirm traffic returns to DX.
6. Verify application health.
7. Confirm VPN remains available as backup.
8. Document incident findings.
```

---

## Production Checklist

- [ ] Direct Connect is configured as the intended primary path.
- [ ] VPN is configured as the intended backup path.
- [ ] Failure domains have been documented.
- [ ] Direct Connect connections are independently designed where required.
- [ ] Customer routers are redundant where required.
- [ ] Internet connectivity for VPN is redundant where required.
- [ ] BGP is configured and monitored.
- [ ] Route preference is deterministic.
- [ ] Prefix advertisements are controlled.
- [ ] Return routes are verified.
- [ ] Transit Gateway route tables are explicitly designed.
- [ ] VPN routes are available during Direct Connect failure.
- [ ] Backup VPN capacity has been tested.
- [ ] Application connection timeout behavior is configured.
- [ ] Database reconnect behavior has been tested.
- [ ] gRPC reconnect behavior has been tested where applicable.
- [ ] Kafka broker connectivity has been tested where applicable.
- [ ] Celery broker reconnect behavior has been tested where applicable.
- [ ] DNS works through both paths.
- [ ] Security controls apply consistently to both paths.
- [ ] Monitoring covers Direct Connect, VPN, BGP, routing, and applications.
- [ ] Synthetic health checks exist.
- [ ] Failover has been tested.
- [ ] Failback has been tested.
- [ ] Maintenance procedures use the backup path.
- [ ] Disaster recovery procedures document connectivity dependencies.
- [ ] Network ownership is documented.
- [ ] Incident escalation procedures are documented.

---

## Interview Traps

### Does Having Direct Connect and VPN Automatically Provide HA?

No. High availability requires independent failure domains, correct routing, sufficient backup capacity, monitoring, and tested failover.

### Why Use VPN as a Backup for Direct Connect?

VPN provides an alternate connectivity path over the Internet when Direct Connect is unavailable.

### How Does AWS Know Which Path to Prefer?

Routing and BGP policy determine path selection. The architecture should explicitly establish the desired primary and backup behavior.

### What Happens When Direct Connect Fails?

The Direct Connect routing session or associated routes can become unavailable, allowing the backup VPN path to become preferred if routing is configured correctly.

### Is Failover Instantaneous?

No. Failure detection, route withdrawal, convergence, and application reconnection all take time.

### Does Route Failover Repair Existing TCP Connections?

No. Existing connections can remain broken and applications may need to reconnect.

### Why Is Backup Capacity Important?

Because the backup path must carry the required workload during a primary-path failure.

### Why Can Two Direct Connect Connections Still Fail Together?

They may share a router, provider, facility, physical path, or other infrastructure.

### What Is Asymmetric Routing?

It occurs when traffic travels through different paths in each direction. Stateful firewalls and network appliances can reject or mishandle such traffic.

### Why Is Failback Important?

If traffic remains on the VPN after Direct Connect recovers, the environment may experience unnecessary latency, cost, and capacity constraints.

### Should the Backup VPN Have Different Security Rules?

No. The security policy should remain consistent across primary and backup paths.

### Does a Healthy BGP Session Prove Application Availability?

No. DNS, routes, firewalls, Security Groups, application protocols, databases, and application state can still fail.

### Why Test PostgreSQL, Kafka, and gRPC Separately?

Each protocol has different connection lifecycle and reconnection behavior. Network-level connectivity alone does not validate application-level resilience.

## Key Takeaways

- Direct Connect + Site-to-Site VPN is a common hybrid HA pattern, but redundancy only provides resilience when the underlying failure domains are genuinely independent.
- BGP, route preference, route withdrawal, and convergence determine whether traffic can move automatically from Direct Connect to VPN and back.
- Backup capacity must be sized for the required failure workload, not merely average traffic.
- Network failover does not automatically recover existing TCP, PostgreSQL, gRPC, Kafka, Redis, or Celery connections; applications must implement appropriate timeout and reconnection behavior.
- High availability is incomplete until failover, failback, security controls, monitoring, and end-to-end application connectivity have been tested under realistic failure conditions.