# 13- Flow Log Based Troubleshooting

## Overview

VPC Flow Logs are a network-observability mechanism for capturing metadata about IP traffic associated with supported AWS networking resources. They are one of the most useful tools for diagnosing connectivity failures because they provide evidence about whether traffic was observed, which endpoints were involved, which protocol and ports were used, and whether the traffic was accepted or rejected.

Flow Logs are especially valuable when an application reports symptoms such as:

- Connection timeout.
- Connection refused.
- Intermittent connectivity.
- Unable to reach a private service.
- Unable to reach an external API.
- Database connection failures.
- Redis or Kafka connectivity failures.
- Cross-VPC communication failures.
- VPN or Transit Gateway communication failures.

The critical distinction is that Flow Logs provide **flow-level metadata**, not packet captures. They do not show application payloads or provide a complete packet-by-packet representation of a connection.

A production troubleshooting workflow therefore treats Flow Logs as one layer of evidence:

```text
Application Logs
       |
       v
DNS Resolution
       |
       v
IP Connectivity
       |
       v
Route Tables
       |
       v
Security Groups / NACLs
       |
       v
VPC Flow Logs
       |
       v
TGW / VPN / Peering / NAT
       |
       v
Remote Network
       |
       v
Destination Application
```

The goal is not simply to find a `REJECT` record. The goal is to determine **where the network path actually fails**.

## Why Flow Logs Matter

A connectivity error at the application layer does not identify the failed network component.

For example:

```text
FastAPI
   |
   | HTTPS request
   v
10.20.20.30:443
   |
   X
timeout
```

The timeout could be caused by:

- DNS resolving to the wrong address.
- Missing route.
- Incorrect Transit Gateway route.
- Missing VPC peering route.
- VPN routing failure.
- Security Group configuration.
- Network ACL configuration.
- Remote firewall.
- Destination host failure.
- Return-path failure.

Flow Logs help establish what AWS observed around the relevant network interface.

This changes troubleshooting from:

```text
"Something is wrong with the network."
```

to:

```text
"Traffic from ENI X to destination Y on TCP port 443
was observed and was rejected."
```

That is significantly more actionable.

## Flow Log Architecture

A common production architecture sends Flow Logs to CloudWatch Logs for operational troubleshooting and optionally to Amazon S3 for long-term analysis.

```mermaid
flowchart LR
    Workload[EC2 / ENI / Network Traffic]
    FlowLogs[VPC Flow Logs]
    CloudWatch[CloudWatch Logs]
    S3[S3]
    Insights[CloudWatch Logs Insights]
    Athena[Athena]
    Engineer[Engineer / SOC / Platform Team]

    Workload --> FlowLogs
    FlowLogs --> CloudWatch
    FlowLogs --> S3
    CloudWatch --> Insights
    S3 --> Athena
    Insights --> Engineer
    Athena --> Engineer
```

CloudWatch is generally convenient for interactive incident investigation.

S3 is useful when the organization needs:

- Long-term retention.
- Large-scale analysis.
- Athena queries.
- Centralized security analytics.
- Historical network investigations.

## What a Flow Log Record Represents

A Flow Log record contains metadata about a network flow.

A typical custom record may contain fields such as:

```text
version
account-id
interface-id
srcaddr
dstaddr
srcport
dstport
protocol
packets
bytes
start
end
action
log-status
```

Example:

```text
2 123456789012 eni-0123456789abcdef0
10.10.10.20 10.20.20.30
49152 443 6
10 6000
1720000000 1720000005
ACCEPT OK
```

Important fields include:

| Field | Purpose |
|---|---|
| `interface-id` | Identifies the network interface associated with the traffic |
| `srcaddr` | Source IP address |
| `dstaddr` | Destination IP address |
| `srcport` | Source port |
| `dstport` | Destination port |
| `protocol` | IP protocol |
| `packets` | Number of packets observed |
| `bytes` | Number of bytes observed |
| `start` | Start timestamp |
| `end` | End timestamp |
| `action` | `ACCEPT` or `REJECT` |
| `log-status` | Indicates logging status |

The exact fields available depend on the configured Flow Log format.

## Flow Logs Are Not Packet Captures

This distinction is important for production troubleshooting.

| Capability | VPC Flow Logs | Packet Capture |
|---|---:|---:|
| Source IP | Yes | Yes |
| Destination IP | Yes | Yes |
| Source port | Yes | Yes |
| Destination port | Yes | Yes |
| Protocol | Yes | Yes |
| Flow action | Yes | No |
| Packet payload | No | Potentially |
| HTTP request body | No | Potentially |
| TCP packet sequence | No | Yes |
| TCP flags | Depends on configured fields | Yes |
| TLS payload | No | Usually encrypted |
| Packet-level timing | No | Yes |
| Long-term centralized analysis | Good | More operationally expensive |

Use Flow Logs when you need to answer:

> "Was traffic observed, where was it going, and what did the network report?"

Use packet capture when you need to answer:

> "What exactly happened at the packet level?"

Do not use Flow Logs as a substitute for packet capture.

## Flow Log Scope

Flow Logs can be configured at supported VPC, subnet, or network-interface scopes.

The scope determines which traffic is represented.

For broad observability:

```text
VPC
 |
 +--> Subnet A
 +--> Subnet B
 +--> Subnet C
```

For targeted troubleshooting:

```text
Specific ENI
 |
 +--> Relevant workload traffic
```

When investigating a single production workload, identifying its ENI is often the most useful starting point.

## Identify the Relevant Network Interface

For EC2 workloads, identify the network interface before searching logs.

```bash
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[].Instances[].NetworkInterfaces[].{
    InterfaceId:NetworkInterfaceId,
    PrivateIp:PrivateIpAddress,
    SubnetId:SubnetId,
    VpcId:VpcId,
    SecurityGroups:Groups[].GroupId
  }'
```

Example:

```text
InterfaceId: eni-0123456789abcdef0
PrivateIp:   10.10.10.20
SubnetId:    subnet-0123456789abcdef0
VpcId:       vpc-0123456789abcdef0
```

The ENI provides a useful correlation point between:

- Workload.
- Subnet.
- VPC.
- Security Groups.
- Flow Logs.

## Establish the Five-Tuple

Before querying Flow Logs, establish the network five-tuple:

```text
Source IP
Destination IP
Source Port
Destination Port
Protocol
```

Example:

```text
Source IP:        10.10.10.20
Destination IP:   10.20.20.30
Source Port:      49152
Destination Port: 443
Protocol:         TCP
```

This prevents broad searches from producing misleading results.

For a backend incident, record the exact connection target:

```text
10.20.20.30:443/TCP
```

rather than simply:

```text
"the API is unreachable"
```

## Establish the Incident Window

Always establish:

```text
Incident start
Incident end
Timezone
```

Prefer UTC for distributed systems.

For example:

```text
Start: 2026-08-23 05:30:00 UTC
End:   2026-08-23 05:35:00 UTC
```

Flow Logs are not necessarily available instantaneously. Account for log-delivery latency when investigating recent incidents.

Do not conclude that traffic did not exist merely because the corresponding record is not immediately visible.

## Understanding ACCEPT

An `ACCEPT` record means the flow was accepted at the relevant network layer represented by the Flow Log.

It does **not** mean:

```text
HTTP 200
```

It does not prove:

```text
TLS handshake succeeded
```

It does not prove:

```text
PostgreSQL authentication succeeded
```

It does not prove:

```text
Redis command succeeded
```

For example:

```text
Flow Log:
ACCEPT

Application:
Connection timeout
```

Possible remaining causes include:

- Return-path failure.
- Remote firewall.
- Destination service failure.
- Protocol-level failure.
- Application timeout.
- VPN problem.
- Transit Gateway routing problem.
- DNS mismatch.

Treat `ACCEPT` as:

> "The observed network flow was permitted at this layer."

Do not treat it as:

> "The request succeeded."

## Understanding REJECT

A `REJECT` record indicates that the observed flow was rejected.

Example:

```text
10.10.10.20 -> 10.20.20.30:443/TCP
REJECT
```

This is strong evidence that the investigation should focus on network controls and configuration.

Potential areas include:

- Security Groups.
- Network ACLs.
- Routing-related behavior.
- Other applicable network filtering mechanisms.

However, the Flow Log record does not automatically tell you:

```text
"Security Group sg-123 rule 40 caused the failure."
```

You must correlate the flow with the actual infrastructure configuration.

## A Flow Log Troubleshooting Model

Use this model during incidents:

```mermaid
flowchart TD
    Incident[Connectivity Incident]
    FiveTuple[Establish Five-Tuple]
    ENI[Identify ENI]
    Logs[Query Flow Logs]
    Action{ACCEPT or REJECT?}
    Reject[Investigate AWS Network Controls]
    Accept[Investigate Complete Path]
    Route[Validate Routing]
    Security[Validate SG / NACL]
    Return[Validate Return Path]
    Remote[Validate Remote Network]
    App[Validate Destination Application]

    Incident --> FiveTuple
    FiveTuple --> ENI
    ENI --> Logs
    Logs --> Action
    Action -->|REJECT| Reject
    Reject --> Security
    Reject --> Route
    Action -->|ACCEPT| Accept
    Accept --> Return
    Accept --> Remote
    Accept --> App
```

This is more reliable than randomly changing Security Groups or route tables.

## Querying CloudWatch Logs

When Flow Logs are delivered to CloudWatch Logs, CloudWatch Logs Insights can be used to investigate traffic.

A conceptual query is:

```text
fields @timestamp, interfaceId, srcAddr, dstAddr, srcPort, dstPort, protocol, action
| filter interfaceId = "eni-0123456789abcdef0"
| sort @timestamp desc
| limit 100
```

The field names must match the Flow Log format configured in the environment.

For rejected traffic:

```text
fields @timestamp, interfaceId, srcAddr, dstAddr, srcPort, dstPort, protocol, action
| filter interfaceId = "eni-0123456789abcdef0"
| filter action = "REJECT"
| sort @timestamp desc
| limit 100
```

For a destination:

```text
fields @timestamp, srcAddr, dstAddr, srcPort, dstPort, action
| filter dstAddr = "10.20.20.30"
| sort @timestamp desc
| limit 100
```

For HTTPS:

```text
fields @timestamp, srcAddr, dstAddr, srcPort, dstPort, action
| filter dstPort = 443
| sort @timestamp desc
| limit 100
```

For PostgreSQL:

```text
fields @timestamp, srcAddr, dstAddr, srcPort, dstPort, action
| filter dstPort = 5432
| sort @timestamp desc
| limit 100
```

For Redis:

```text
fields @timestamp, srcAddr, dstAddr, srcPort, dstPort, action
| filter dstPort = 6379
| sort @timestamp desc
| limit 100
```

## Finding Rejected Traffic

A useful operational query groups rejected traffic by destination:

```text
fields srcAddr, dstAddr, dstPort, action
| filter action = "REJECT"
| stats count() by dstAddr, dstPort
| sort count() desc
```

This can expose recurring network-control problems.

Example:

```text
Destination      Port    Rejections
10.20.10.50      443     18291
10.20.20.30      5432     9182
10.20.30.40      6379     2103
```

If a single destination dominates the rejected traffic, investigate that dependency first.

## Finding Top Talkers

Flow Logs can also identify high-volume communication patterns.

Conceptually:

```text
stats sum(bytes) by srcAddr, dstAddr
```

This is useful for detecting:

- Unexpected large transfers.
- Chatty services.
- Misconfigured applications.
- Unexpected cross-network communication.
- Potential data-exfiltration patterns.
- Unexpected service dependencies.

Flow Logs therefore have value beyond incident troubleshooting.

They can support network-capacity analysis and security investigations.

## Source and Destination Analysis

For every important flow, explicitly document:

```text
Source
Destination
Protocol
Port
Direction
```

Example:

```text
Source:
10.10.10.20:49152

Destination:
10.20.20.30:443

Protocol:
TCP
```

Then ask:

1. Is the destination IP correct?
2. Is the destination port correct?
3. Is the protocol correct?
4. Does the source subnet have a route?
5. Does the destination have a return route?
6. Are Security Groups allowing the connection?
7. Are NACLs allowing both directions?
8. Is an intermediate component involved?
9. Is the destination application listening?

## TCP Connectivity Analysis

For a TCP connection:

```text
Client
  |
  | SYN
  v
Server
  |
  | SYN-ACK
  v
Client
  |
  | ACK
  v
Server
```

Flow Logs do not provide a complete packet-level reconstruction by default.

However, they can help determine whether traffic is being observed in the expected directions.

For example:

```text
Client -> Server
```

is visible, but expected reverse traffic is absent.

Potential causes include:

- Return route missing.
- Remote firewall.
- VPN problem.
- Asymmetric routing.
- Destination host failure.

Do not conclude that the remote host is definitely down without checking the complete path.

## One-Way Traffic

One-way traffic is especially important in hybrid environments.

Example:

```text
AWS:
10.10.10.20

On-Premises:
172.16.10.30
```

Observed:

```text
10.10.10.20 -> 172.16.10.30
```

but no corresponding:

```text
172.16.10.30 -> 10.10.10.20
```

Possible causes include:

- Missing return route.
- Customer firewall.
- VPN route problem.
- BGP propagation issue.
- Asymmetric routing.
- Remote host failure.

Investigate both sides of the connection.

## Security Group Troubleshooting

Security Groups are stateful.

Suppose:

```text
Application:
10.10.10.20

Database:
10.20.20.30:5432
```

The database Security Group should permit the expected inbound TCP connection.

Inspect the Security Group:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0
```

Validate:

```text
Protocol: TCP
Port:     5432
Source:   expected workload
```

Prefer narrowly scoped sources.

For AWS-to-AWS communication, Security Group references are often preferable to broad CIDR ranges when the architecture supports them.

## Network ACL Troubleshooting

Network ACLs are stateless.

Therefore, both directions must be explicitly allowed.

Example:

```text
Client:
10.10.10.20:49152
       |
       | TCP 443
       v
Server:
10.10.20.30:443
```

The response travels:

```text
Server:
10.10.20.30:443
       |
       | TCP 49152
       v
Client:
10.10.10.20:49152
```

A restrictive NACL that permits inbound port `443` but blocks the return traffic can create connectivity failures.

Inspect the NACL:

```bash
aws ec2 describe-network-acls \
  --filters \
    Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

Check:

- Rule number.
- Rule evaluation order.
- Protocol.
- Port range.
- Source/destination CIDR.
- Allow/deny action.
- Both directions.

## Ephemeral Ports

A frequent NACL mistake is focusing only on the server's listening port.

Consider:

```text
Client: 10.10.10.20:49152
Server: 10.10.20.30:443
```

The client initiates:

```text
49152 -> 443
```

The server's response uses:

```text
443 -> 49152
```

The client-side ephemeral port range is operating-system dependent.

Do not blindly open a universal range without verifying the actual workload requirements.

For restrictive production NACLs, explicitly document why the selected ephemeral range is required.

## Route Table Troubleshooting

Flow Logs should always be correlated with route tables.

Inspect routes:

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0 \
  --query 'RouteTables[].Routes[]'
```

For a destination such as:

```text
10.20.0.0/16
```

verify the route points to the intended target.

Possible targets include:

```text
Internet Gateway
NAT Gateway
Transit Gateway
Virtual Private Gateway
VPC Peering Connection
Network Interface
```

The correct target depends on the network architecture.

## NAT Gateway Troubleshooting

A common private-subnet architecture is:

```text
Private Application Subnet
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

If a FastAPI service cannot call an external API:

```text
api.example.com:443
```

check:

- DNS resolution.
- Private subnet route.
- NAT Gateway route.
- NAT Gateway state and metrics.
- Public subnet route.
- Internet Gateway.
- Security Groups.
- NACLs.
- Remote endpoint.
- Application timeout.

Flow Logs should be combined with NAT Gateway metrics and route-table inspection.

## Internet Gateway Troubleshooting

For public workloads:

```text
EC2
 |
 v
Subnet Route Table
 |
 v
Internet Gateway
 |
 v
Internet
```

The relevant route normally includes:

```text
0.0.0.0/0 -> Internet Gateway
```

The workload also needs the appropriate public addressing model for the architecture.

Validate:

```text
Route table
Security Group
NACL
Public addressing
Application listener
Remote endpoint
```

A Flow Log `ACCEPT` does not prove that the public service is reachable from the Internet.

## VPC Peering Troubleshooting

For VPC peering:

```text
VPC A
10.10.0.0/16
   |
   v
VPC Peering
   |
   v
VPC B
10.20.0.0/16
```

Verify both sides:

```text
VPC A:
10.20.0.0/16 -> Peering Connection

VPC B:
10.10.0.0/16 -> Peering Connection
```

If Flow Logs show source traffic but the destination workload does not show expected traffic, investigate:

- Peering connection state.
- Route tables.
- Security Groups.
- NACLs.
- Return routes.
- Overlapping CIDRs.

Flow Logs are evidence about observed traffic; they do not replace route-table validation.

## Transit Gateway Troubleshooting

Transit Gateway introduces an additional routing layer:

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
TGW Route Table
      |
      v
Destination Attachment
      |
      v
Destination VPC
```

A source Flow Log record can establish that the workload generated traffic.

It does not prove that the Transit Gateway selected the intended attachment.

Inspect Transit Gateway routes:

```bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0 \
  --filters Name=type,Values=static,propagated
```

Check:

- Route destination.
- Route state.
- Attachment.
- Blackhole routes.
- Route-table association.
- Route propagation.

## VPN Troubleshooting

For hybrid connectivity:

```text
AWS Workload
     |
     v
VPC Route Table
     |
     v
VGW / TGW
     |
     v
VPN
     |
     v
Customer Gateway
     |
     v
On-Premises
```

Flow Logs can establish that AWS workloads are generating traffic.

They cannot prove that the traffic successfully crossed the encrypted VPN tunnel.

Correlate Flow Logs with:

- VPN tunnel status.
- BGP state.
- Route propagation.
- Customer router logs.
- Customer firewall logs.
- On-premises packet captures.
- Application logs.

## DNS Troubleshooting

DNS failures can appear to be network failures.

Consider:

```text
Application
    |
    v
api.internal.example.com
    |
    X
DNS resolution failure
```

If the hostname cannot be resolved, the application may never attempt a connection to the intended IP.

Test DNS separately:

```bash
dig api.internal.example.com
```

Then test the resulting IP:

```bash
nc -vz 10.20.20.30 443
```

This separates:

```text
DNS failure
```

from:

```text
IP connectivity failure
```

Do not expect Flow Logs to explain a failure that occurs entirely before network traffic is generated.

## Kubernetes and EKS Troubleshooting

Kubernetes introduces additional network layers:

```text
Pod
 |
 v
Node
 |
 v
CNI / ENI
 |
 v
VPC
 |
 v
Destination
```

When troubleshooting EKS, identify:

- Pod IP.
- Node.
- Relevant ENI.
- CNI/networking model.
- Security Groups.
- NetworkPolicies.
- Route tables.
- Flow Logs.

Do not assume that an EC2 instance-level IP tells the entire story for pod networking.

A Kubernetes `NetworkPolicy` failure can occur independently of VPC Security Groups and NACLs.

## Load Balancer Troubleshooting

For an Application Load Balancer:

```text
Client
  |
  v
ALB
  |
  v
Target
```

There are at least two important network paths:

```text
Client -> ALB
```

and:

```text
ALB -> Target
```

A failure on one path does not imply a failure on the other.

For target connectivity, investigate:

- Load balancer Security Group.
- Target Security Group.
- Target subnet NACL.
- Target route.
- Target port.
- Health-check configuration.
- Application listener.

Correlate Flow Logs with ALB access logs and target-health information.

## PostgreSQL Troubleshooting

For:

```text
FastAPI
   |
   v
PostgreSQL:5432
```

use Flow Logs to investigate the network layer.

The complete troubleshooting path is:

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
Flow Logs
 |
 v
PostgreSQL listener
 |
 v
PostgreSQL authentication
```

A Flow Log `ACCEPT` does not prove PostgreSQL authentication succeeded.

For connection-level troubleshooting on the database host:

```bash
ss -lntp | grep 5432
```

Then investigate PostgreSQL-specific configuration such as:

```text
listen_addresses
pg_hba.conf
TLS configuration
connection limits
database availability
```

## Redis Troubleshooting

For:

```text
Django / FastAPI
      |
      v
Redis:6379
```

validate:

- DNS.
- Route.
- Security Group.
- NACL.
- Flow Logs.
- Redis endpoint.
- TLS configuration where applicable.
- Redis service availability.

Again, `ACCEPT` only establishes network-layer evidence. It does not prove the Redis protocol operation succeeded.

## Kafka Troubleshooting

Kafka connectivity can involve multiple broker endpoints.

A client may successfully reach a bootstrap broker and then fail to reach a broker advertised in cluster metadata.

```text
Application
     |
     v
Bootstrap Broker
     |
     v
Metadata
     |
     v
Broker 2
     |
     v
Broker 3
```

Flow Logs can help distinguish:

```text
Application -> Bootstrap Broker
```

from:

```text
Application -> Advertised Broker
```

This is particularly useful when investigating incorrect Kafka listener or network-advertisement configuration.

## Correlating Flow Logs With Application Logs

The most effective troubleshooting combines network and application telemetry.

Suppose an application reports:

```text
2026-08-23T05:31:43Z
Connection timeout to 10.20.20.30:443
```

Search Flow Logs around the same time.

Possible result:

```text
10.10.10.20 -> 10.20.20.30:443
REJECT
```

The investigation should focus on AWS network controls.

Another result:

```text
10.10.10.20 -> 10.20.20.30:443
ACCEPT
```

Now investigate:

- Return traffic.
- Remote firewall.
- VPN/TGW path.
- Destination service.
- TLS.
- Application behavior.

The key principle is:

> Correlate timestamps and network identities rather than troubleshooting each telemetry source independently.

## Missing Flow Log Records

Absence of a Flow Log record is not automatically proof that traffic did not occur.

Possible causes include:

- Flow Logs are not enabled.
- Incorrect Flow Log scope.
- Wrong ENI.
- Wrong time window.
- Incorrect query.
- Log-delivery latency.
- Logging-status issues.
- Traffic associated with a different network interface.

Before concluding that traffic never occurred, verify:

```text
Flow Log configuration
Scope
ENI
Timestamp
Destination
Query
Log status
```

## Log Status

The `log-status` field provides information about the availability of flow-log data.

Common statuses include:

```text
OK
NODATA
SKIPDATA
```

Do not interpret every absence of data as:

```text
No network traffic occurred.
```

The logging status and the configured Flow Log scope must be considered.

## Flow Logs and Security Investigations

Flow Logs can provide valuable network evidence during security incidents.

Useful questions include:

- Which hosts communicated with an unexpected IP?
- Which ports were accessed?
- When did communication begin?
- Which internal systems communicated with a suspicious endpoint?
- How much data was transferred?
- Were there repeated rejected connections?

For example:

```text
Workload:
10.10.10.20

Unexpected destination:
203.0.113.50:443
```

Flow Logs can establish the network communication pattern.

For complete security investigations, correlate with:

- CloudTrail.
- GuardDuty.
- DNS logs.
- Endpoint telemetry.
- Application logs.
- Firewall logs.
- SIEM data.

Flow Logs are one evidence source, not a complete security solution.

## Data Protection

Flow Logs contain infrastructure metadata that can be sensitive.

They may reveal:

- Internal IP addresses.
- Network topology.
- Service relationships.
- Ports.
- Communication patterns.
- External destinations.

Protect Flow Logs using:

- Least-privilege IAM.
- Encryption.
- Controlled log access.
- Appropriate retention policies.
- Access auditing.
- Centralized security controls where appropriate.

Do not treat Flow Logs as public or non-sensitive operational data.

## Retention Strategy

A common production model is:

```text
Flow Logs
    |
    +--> CloudWatch Logs
    |       |
    |       +--> Short/medium-term troubleshooting
    |
    +--> S3
            |
            +--> Long-term retention
            |
            +--> Athena
            |
            +--> Security analytics
```

Retention should reflect:

- Incident-response requirements.
- Compliance.
- Security requirements.
- Operational requirements.
- Cost.

Avoid indefinite retention without a defined business or operational reason.

## Cost Considerations

Flow Logs generate additional logging and storage costs.

Cost drivers include:

- Traffic volume.
- Number of network interfaces.
- Retention period.
- CloudWatch Logs ingestion.
- CloudWatch Logs storage.
- S3 storage.
- SIEM ingestion.
- Query volume.

Do not solve cost problems by blindly disabling network telemetry.

Instead consider:

```text
Scope
+
Retention
+
Aggregation
+
Storage destination
+
Query strategy
```

Optimize the logging architecture while preserving the telemetry required for production operations.

## Production Architecture Example

Consider a backend platform:

```mermaid
flowchart LR
    Internet[Internet]
    ALB[Application Load Balancer]
    API[FastAPI Service]
    Worker[Celery Workers]
    Redis[Redis]
    DB[PostgreSQL]
    Kafka[Kafka]
    NAT[NAT Gateway]
    TGW[Transit Gateway]
    Flow[VPC Flow Logs]

    Internet --> ALB
    ALB --> API
    API --> Redis
    API --> DB
    API --> Kafka
    API --> NAT
    Worker --> Redis
    Worker --> DB
    Worker --> Kafka
    API --> TGW
    Flow -. network evidence .-> API
    Flow -. network evidence .-> Worker
    Flow -. network evidence .-> DB
```

Suppose API requests fail because PostgreSQL connections time out.

A senior engineer should not immediately change PostgreSQL Security Groups.

Instead:

```text
1. Identify API ENI.
2. Identify PostgreSQL endpoint/IP.
3. Establish TCP 5432 five-tuple.
4. Check DNS.
5. Query Flow Logs.
6. Determine ACCEPT/REJECT.
7. Check API subnet route.
8. Check PostgreSQL route.
9. Check Security Groups.
10. Check NACLs.
11. Check return traffic.
12. Check PostgreSQL listener.
13. Check PostgreSQL logs.
```

This creates an evidence-driven investigation.

## Production Troubleshooting Procedure

### Establish the Five-Tuple

Record:

```text
Source IP
Destination IP
Source Port
Destination Port
Protocol
```

### Identify the ENI

Determine:

```text
ENI
Subnet
VPC
Security Groups
```

### Establish the Incident Window

Record:

```text
Start
End
Timezone
```

### Confirm Flow Log Configuration

Verify:

```text
Enabled
Correct scope
Correct destination
Correct log group/bucket
```

### Search Flow Logs

Start with:

```text
ENI
+
Destination
+
Port
+
Timestamp
```

### Interpret the Action

```text
REJECT
```

Focus on network controls.

```text
ACCEPT
```

Continue through the rest of the path.

### Validate Routing

Inspect:

```text
VPC route table
TGW route table
Peering route
VPN route
NAT route
```

where applicable.

### Validate Security

Inspect:

```text
Security Groups
NACLs
Firewalls
Kubernetes NetworkPolicies
```

where applicable.

### Validate Return Traffic

Always investigate:

```text
Destination -> Source
```

for stateful protocols such as TCP.

### Validate the Remote Network

For hybrid connectivity:

```text
VPN
BGP
Customer firewall
Customer router
Remote host
```

### Validate the Application

Finally verify the destination service:

```text
TCP
TLS
HTTP
gRPC
PostgreSQL
Redis
Kafka
```

depending on the workload.

## Troubleshooting Decision Matrix

| Flow Log Observation | Likely Investigation Area |
|---|---|
| `REJECT` | Security controls and routing |
| `ACCEPT`, no application response | Return path, remote network, service, protocol |
| No record | Scope, ENI, timestamp, logging status, delivery latency |
| Forward traffic only | Return route, remote firewall, asymmetric routing |
| Repeated rejects | Security Group, NACL, route or firewall configuration |
| Correct TCP flow, application error | Application/service layer |
| Correct AWS flow, no remote response | Remote network or destination |
| DNS failure with no connection | DNS configuration rather than IP networking |
| Traffic reaches wrong destination | DNS, route, service discovery, or configuration |
| Sudden traffic increase | Application behavior, deployment, security event, or misconfiguration |

## Common Mistakes

### Treating ACCEPT as Application Success

Incorrect:

```text
Flow Log = ACCEPT
therefore
application = healthy
```

Correct:

```text
Flow Log = ACCEPT
therefore
network flow was accepted at the relevant layer
```

Continue investigating the application path.

### Treating REJECT as a Complete Diagnosis

A `REJECT` record does not automatically identify the exact failed rule.

Correlate it with:

```text
Route tables
Security Groups
NACLs
Other network controls
```

### Searching Only by IP

An IP address may not be enough to uniquely identify a workload.

Prefer:

```text
ENI
+
IP
+
five-tuple
+
timestamp
```

### Ignoring Return Traffic

TCP connectivity requires bidirectional communication.

Always investigate:

```text
Client -> Server
Server -> Client
```

### Assuming Missing Records Mean No Traffic

Check:

```text
Flow Log scope
ENI
Time range
Query
Log status
Delivery latency
```

### Using Flow Logs as Packet Captures

Flow Logs are not packet captures.

Use packet-level tooling when the investigation requires:

- TCP flags.
- Packet sequence.
- Retransmissions.
- MTU problems.
- Protocol payload.
- Detailed packet timing.

### Ignoring Ephemeral Ports

Restrictive NACLs can fail because return traffic uses client-side ephemeral ports.

### Ignoring DNS

If DNS resolution fails, there may be no network connection to the intended destination.

### Ignoring Container Networking

For Kubernetes and containerized workloads, determine how pod/container traffic maps to VPC interfaces before interpreting Flow Logs.

### Making Changes Before Collecting Evidence

A common operational mistake is changing:

```text
Security Group
Route Table
NACL
```

before confirming the failure.

This can:

- Hide the original cause.
- Introduce a second failure.
- Break unrelated workloads.
- Make incident timelines harder to reconstruct.

Collect evidence first whenever the incident permits it.

## Interview Traps

### "Flow Logs Capture Every Packet"

Incorrect.

Flow Logs represent summarized network-flow information.

### "ACCEPT Means the Application Responded"

Incorrect.

It only establishes network-layer evidence.

### "REJECT Means the Security Group Blocked It"

Not necessarily.

Investigate all relevant network controls.

### "No Flow Log Means No Traffic"

Incorrect.

Verify scope, interface, logging status, time window, and delivery.

### "Flow Logs Replace tcpdump"

Incorrect.

They operate at different levels of network observability.

### "Flow Logs Tell You Which Security Group Rule Failed"

Not directly.

You must correlate the traffic with the applicable infrastructure configuration.

### "A Successful Connection to a Kafka Bootstrap Broker Proves Kafka Networking Works"

Incorrect.

The client may still fail to reach brokers advertised in metadata.

### "A Successful TCP Connection Proves PostgreSQL Works"

Incorrect.

TCP connectivity does not prove database authentication or application-level success.

## Security and Operational Best Practices

Use Flow Logs as a permanent part of production network observability rather than enabling them only during incidents.

Recommended practices:

- Enable Flow Logs for production network environments.
- Standardize Flow Log formats.
- Centralize logs where appropriate.
- Protect log destinations with least-privilege IAM.
- Encrypt stored logs.
- Configure explicit retention.
- Maintain reusable Logs Insights queries.
- Use UTC consistently.
- Document important ENI-to-service mappings.
- Monitor logging failures.
- Correlate Flow Logs with application logs.
- Correlate network events with infrastructure changes.
- Include Flow Log investigation steps in incident runbooks.
- Periodically test the troubleshooting workflow.

Useful reusable queries should cover:

```text
Rejected traffic
Specific ENI
Specific source
Specific destination
Specific port
Top talkers
Top destinations
Incident time window
Unexpected external destinations
```

## Production Troubleshooting Checklist

```text
[ ] Identify source workload
[ ] Identify source IP
[ ] Identify destination IP
[ ] Identify source port
[ ] Identify destination port
[ ] Identify protocol
[ ] Identify relevant ENI
[ ] Identify VPC
[ ] Identify subnet
[ ] Establish incident time window
[ ] Confirm Flow Logs are enabled
[ ] Confirm correct Flow Log scope
[ ] Confirm correct destination
[ ] Confirm log-status
[ ] Search for the relevant flow
[ ] Determine ACCEPT or REJECT
[ ] Check traffic direction
[ ] Check return traffic
[ ] Check VPC route table
[ ] Check Transit Gateway routes if applicable
[ ] Check VPC peering routes if applicable
[ ] Check VPN routes if applicable
[ ] Check NAT routes if applicable
[ ] Check Security Groups
[ ] Check Network ACLs
[ ] Check firewalls
[ ] Check Kubernetes NetworkPolicies if applicable
[ ] Check DNS
[ ] Check remote network
[ ] Check destination listener
[ ] Check application logs
[ ] Check packet capture if required
[ ] Correlate timestamps
[ ] Check recent infrastructure changes
[ ] Check unexpected traffic patterns
[ ] Document the confirmed failure layer
```

## Key Takeaways

- **VPC Flow Logs provide flow-level network evidence, not packet captures**; use them to establish endpoints, ports, protocols, direction, and network-level acceptance or rejection.
- **`ACCEPT` does not prove application success and `REJECT` does not identify the exact failed configuration rule**; correlate Flow Logs with routes, Security Groups, NACLs, and the application path.
- **Build investigations around the ENI, five-tuple, and incident timestamp** to avoid ambiguous log searches and incorrect conclusions.
- **Always investigate bidirectional traffic and the complete network path**, especially for TCP, NAT Gateway, Transit Gateway, VPC peering, VPN, and restrictive NACL configurations.
- **Combine Flow Logs with DNS, routing, application, firewall, VPN, load balancer, and service-specific telemetry** to identify the actual failure layer rather than treating Flow Logs as a standalone diagnosis.