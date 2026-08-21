# 08- VPC Flow Logs and Security Analysis

## Overview

Amazon VPC Flow Logs provide network-level visibility into traffic flowing to and from network interfaces in a VPC. They are primarily used for connectivity troubleshooting, security investigation, traffic analysis, and validating the behavior of network controls such as Security Groups and Network ACLs.

A Flow Log records metadata about network flows rather than packet contents. Typical information includes source and destination addresses, source and destination ports, protocol, packet and byte counts, timestamps, network interface identifiers, and whether the traffic was accepted or rejected.

For production backend systems, Flow Logs should be treated as one layer of an observability and security architecture:

```text
Application Logs
    |
    +-- What did the application do?

Load Balancer Logs
    |
    +-- What HTTP traffic reached the edge?

VPC Flow Logs
    |
    +-- What network traffic was observed?

CloudTrail
    |
    +-- What AWS API operations occurred?

DNS Query Logs
    |
    +-- What hostnames were resolved?

GuardDuty
    |
    +-- Does AWS detect suspicious activity?
```

The most important engineering distinction is:

> VPC Flow Logs provide network-flow telemetry. They are not packet captures, application logs, or a complete intrusion-detection system.

A mature architecture combines Flow Logs with application telemetry, CloudTrail, DNS logging, GuardDuty, load-balancer logs, and infrastructure metadata.

---

## Why VPC Flow Logs Matter

Network failures frequently appear to application developers as generic errors:

```text
Connection timeout
Connection refused
DNS failure
TLS timeout
502 Bad Gateway
503 Service Unavailable
```

The application error alone may not reveal whether the problem exists in:

- DNS
- Routing
- Security Groups
- Network ACLs
- NAT Gateway
- VPC endpoints
- Load balancers
- The destination service
- The application itself

Flow Logs provide an additional layer of evidence.

For example:

```text
Django / FastAPI
      |
      | TCP 5432
      v
RDS PostgreSQL
      |
      v
VPC Flow Logs
      |
      +-- ACCEPT
      |
      +-- REJECT
```

If the application reports a PostgreSQL connection timeout and Flow Logs show repeated rejected connections from the application ENI to the database address on port `5432`, the investigation can focus on the network security path.

If Flow Logs show accepted traffic, the problem may instead be:

- PostgreSQL availability
- Connection exhaustion
- Authentication
- TLS configuration
- Application timeout configuration
- Database-side controls
- Application-level connection pooling

Flow Logs therefore help narrow the failure domain.

---

## What VPC Flow Logs Capture

A Flow Log record describes network traffic observed by AWS.

A simplified record can be thought of as:

```text
Source IP
Destination IP
Source Port
Destination Port
Protocol
Timestamp
Packets
Bytes
Action
Network Interface
```

For example:

```text
10.0.10.25:48214
        |
        | TCP
        v
10.0.20.15:5432
```

The corresponding record might conceptually indicate:

```text
srcaddr=10.0.10.25
dstaddr=10.0.20.15
srcport=48214
dstport=5432
protocol=6
action=ACCEPT
```

Modern Flow Log formats support additional metadata such as:

- Account ID
- VPC ID
- Subnet ID
- Availability Zone
- Instance ID
- Interface ID
- Flow direction
- Traffic path
- TCP flags
- Log status
- AWS service metadata where supported

The exact fields available depend on the configured Flow Log format.

---

## What Flow Logs Do Not Capture

Flow Logs operate below the application layer.

They do not normally provide:

- HTTP method
- HTTP URL
- HTTP headers
- HTTP request body
- SQL statements
- gRPC method names
- TLS payload contents
- Application exception details
- User identity
- Application authentication information

For example, Flow Logs can show:

```text
10.0.10.25 -> 10.0.20.15:443
```

but they cannot tell you that the application sent:

```text
POST /api/payments
```

with a particular JSON body.

For application-level visibility, use the appropriate application and service telemetry.

| Requirement | Appropriate Source |
|---|---|
| Network source/destination | VPC Flow Logs |
| HTTP request details | ALB/API/application logs |
| SQL statements | Database/application telemetry |
| AWS API activity | CloudTrail |
| DNS queries | Route 53 Resolver query logging |
| AWS threat findings | GuardDuty |
| Packet-level inspection | Traffic Mirroring / packet-analysis tooling |

---

## Flow Log Scope

Flow Logs can be configured for different scopes.

| Scope | Typical Use |
|---|---|
| VPC | Broad network visibility |
| Subnet | Visibility for a workload tier |
| Network interface | Targeted investigation |

A VPC-level Flow Log is often a good production baseline because new ENIs can be created as workloads scale.

For example:

```text
Production VPC
    |
    +-- Public Subnets
    |      |
    |      +-- ALB ENIs
    |
    +-- Private Application Subnets
    |      |
    |      +-- ECS/EKS/EC2 ENIs
    |
    +-- Database Subnets
           |
           +-- RDS ENIs
```

A targeted ENI-level Flow Log can be useful when investigating a specific workload without expanding logging scope unnecessarily.

---

## Traffic Types

When configuring a Flow Log, traffic can be captured as:

| Type | Purpose |
|---|---|
| `ACCEPT` | Accepted traffic |
| `REJECT` | Rejected traffic |
| `ALL` | Both accepted and rejected traffic |

For production security analysis, `ALL` is often the most useful because rejected traffic can reveal:

- Unauthorized connection attempts
- Misconfigured applications
- Port scanning
- Network reconnaissance
- Incorrect Security Group rules
- Incorrect Network ACL rules

For example:

```text
10.0.10.25 -> 10.0.20.15:5432 ACCEPT
10.0.50.12 -> 10.0.20.15:5432 REJECT
```

The second record is evidence of blocked traffic, not proof of an attack.

---

## ACCEPT Does Not Mean Safe

A common misconception is:

```text
ACCEPT = trusted
```

That is incorrect.

`ACCEPT` indicates that the traffic was accepted at the relevant network layer represented by the Flow Log.

A compromised workload can generate legitimate-looking traffic:

```text
Compromised EC2
      |
      | TCP 443
      v
External destination
      |
      v
ACCEPT
```

The traffic can be accepted while still being malicious.

Therefore:

```text
ACCEPT != trusted
```

Flow Logs provide evidence about network behavior, not intent.

---

## REJECT Does Not Mean Attack

The reverse assumption is also incorrect:

```text
REJECT = attack
```

A rejected connection may simply be caused by:

- Incorrect application configuration
- Incorrect Security Group rule
- Incorrect Network ACL
- Stale service configuration
- Health check configuration
- Deployment changes
- An application attempting an unavailable service

For example:

```text
ECS application
    |
    | TCP 5432
    v
RDS
    |
    +-- REJECT
```

This could be a simple database Security Group misconfiguration.

Context is required before classifying traffic as malicious.

---

## Flow Log Aggregation

Flow Logs are aggregated network-flow records rather than synchronous packet events.

Conceptually:

```mermaid
flowchart LR
    Traffic["Network Traffic"]
    Capture["Traffic Observation"]
    Aggregate["Flow Aggregation"]
    Delivery["Log Delivery"]

    Traffic --> Capture
    Capture --> Aggregate
    Aggregate --> Delivery

    Delivery --> CW["CloudWatch Logs"]
    Delivery --> S3["Amazon S3"]
    Delivery --> FH["Kinesis Data Firehose"]
```

The aggregation interval controls how frequently traffic records are generated.

Supported aggregation intervals include:

- 1 minute
- 10 minutes

For Nitro-based network interfaces, the effective aggregation behavior can differ because AWS uses shorter aggregation intervals for those interfaces.

Aggregation interval should not be confused with delivery latency.

A one-minute aggregation interval does not mean the record will become available exactly one minute later.

---

## Flow Log Delivery Is Not Real-Time

Flow Log delivery is best effort.

This has an important operational consequence:

> Do not build synchronous application behavior that depends on the immediate availability of Flow Log records.

For example, this is a poor design:

```text
HTTP Request
    |
    v
Wait for Flow Log
    |
    v
Determine whether request is safe
```

Flow Logs are better suited for:

```text
Traffic
    |
    v
Flow Logs
    |
    v
Operational / Security Analysis
```

For real-time security controls, use mechanisms designed for enforcement or near-real-time detection.

---

## Flow Log Record Fields

Common fields include:

| Field | Meaning |
|---|---|
| `version` | Flow Log record format version |
| `account-id` | AWS account associated with the traffic |
| `interface-id` | Network interface |
| `srcaddr` | Source address |
| `dstaddr` | Destination address |
| `srcport` | Source port |
| `dstport` | Destination port |
| `protocol` | IP protocol |
| `packets` | Packet count |
| `bytes` | Byte count |
| `start` | Flow start time |
| `end` | Flow end time |
| `action` | `ACCEPT` or `REJECT` |
| `log-status` | Logging status |
| `vpc-id` | VPC identifier |
| `subnet-id` | Subnet identifier |
| `instance-id` | Instance identifier where applicable |
| `flow-direction` | Traffic direction where available |
| `traffic-path` | Network path metadata where supported |

Not every field is populated for every resource or traffic type.

A value of `-` can indicate that a field is unavailable or not applicable.

---

## Security Analysis Architecture

A production environment can send Flow Logs to multiple analysis systems.

```mermaid
flowchart TB
    VPC["Production VPC"]

    VPC --> Flow["VPC Flow Logs"]

    Flow --> CW["CloudWatch Logs"]
    Flow --> S3["S3"]
    Flow --> Firehose["Kinesis Data Firehose"]

    CW --> Insights["CloudWatch Logs Insights"]
    S3 --> Athena["Amazon Athena"]
    Firehose --> SIEM["SIEM / Security Analytics"]

    GuardDuty["Amazon GuardDuty"]
    CloudTrail["AWS CloudTrail"]
    DNS["DNS Query Logs"]

    Insights --> Analysis["Security / Operations Analysis"]
    Athena --> Analysis
    SIEM --> Analysis
    GuardDuty --> Analysis
    CloudTrail --> Analysis
    DNS --> Analysis
```

Each component solves a different problem.

| Component | Primary Purpose |
|---|---|
| VPC Flow Logs | Network-flow telemetry |
| CloudWatch Logs | Operational querying |
| S3 | Durable log storage |
| Athena | SQL-based historical analysis |
| Firehose | Streaming delivery |
| GuardDuty | Managed threat detection |
| CloudTrail | AWS API activity |
| DNS query logs | DNS-level context |

---

## CloudWatch Logs

CloudWatch Logs is useful when engineers need to investigate current or recent network behavior.

A common architecture is:

```text
VPC Flow Logs
      |
      v
CloudWatch Log Group
      |
      v
CloudWatch Logs Insights
```

Typical questions include:

- Which connections were rejected?
- Which ports are receiving traffic?
- Which source addresses generate the most rejected connections?
- Which workloads communicate with a specific destination?
- Did network traffic change after a deployment?

CloudWatch is particularly useful for interactive operational troubleshooting.

---

## CloudWatch Logs Insights

A Flow Log query should be based on the actual fields configured in the log format.

For example:

```text
fields @timestamp, srcAddr, dstAddr, srcPort, dstPort, protocol, action
| filter action = "REJECT"
| sort @timestamp desc
| limit 100
```

To identify rejected destination ports:

```text
fields dstPort, action
| filter action = "REJECT"
| stats count() as reject_count by dstPort
| sort reject_count desc
| limit 20
```

To identify source addresses generating rejected traffic:

```text
fields srcAddr, action
| filter action = "REJECT"
| stats count() as reject_count by srcAddr
| sort reject_count desc
| limit 20
```

These queries are useful for finding patterns rather than analyzing individual packets.

---

## S3 for Long-Term Analysis

S3 is well suited to long-term storage and large-scale analysis.

A typical architecture is:

```text
VPC Flow Logs
      |
      v
S3
      |
      +---- Athena
      |
      +---- Security Analytics
      |
      +---- Long-Term Archive
```

S3 is useful when:

- Logs need long retention.
- Traffic volumes are high.
- Historical analysis is required.
- Security teams need centralized datasets.
- Athena-based SQL queries are useful.
- Logs must be integrated with downstream analytics systems.

For large environments, S3 can provide a more scalable historical repository than keeping every record in an interactive log platform indefinitely.

---

## Athena Analysis

Once Flow Logs are stored in a queryable S3 structure, Athena can be used for SQL analysis.

For example, identifying high-volume source addresses:

```sql
SELECT
    srcaddr,
    SUM(bytes) AS total_bytes
FROM vpc_flow_logs
GROUP BY srcaddr
ORDER BY total_bytes DESC
LIMIT 20;
```

Finding rejected destination ports:

```sql
SELECT
    dstport,
    COUNT(*) AS rejected_connections
FROM vpc_flow_logs
WHERE action = 'REJECT'
GROUP BY dstport
ORDER BY rejected_connections DESC
LIMIT 20;
```

Finding high-volume destinations:

```sql
SELECT
    dstaddr,
    SUM(bytes) AS total_bytes
FROM vpc_flow_logs
GROUP BY dstaddr
ORDER BY total_bytes DESC
LIMIT 20;
```

The actual table schema depends on the configured S3 format and Athena table definition.

---

## Query Efficiency

Flow Logs can become very large.

Avoid unnecessarily scanning the entire dataset:

```sql
SELECT *
FROM vpc_flow_logs;
```

Prefer:

```sql
SELECT
    srcaddr,
    dstaddr,
    dstport,
    action,
    bytes
FROM vpc_flow_logs
WHERE year = 2026
  AND month = 8
  AND day = 21;
```

The exact partition columns depend on the S3/Athena implementation.

For large historical datasets, use:

- Time partitioning
- Columnar formats where appropriate
- Predicate filtering
- Minimal column selection
- Appropriate compression
- Query-result reuse where useful

This reduces both query time and cost.

---

## Identifying Top Talkers

A top talker is a source or destination generating an unusually large amount of traffic.

Example:

```text
Source             Bytes
-------------------------
10.0.10.20          2 GB
10.0.10.21          3 GB
10.0.10.22          4 GB
10.0.10.23         48 GB  <-- investigate
```

A high-volume host is not automatically malicious.

Possible legitimate explanations include:

- Database replication
- Backup operations
- Batch processing
- Data exports
- Container image downloads
- Analytics workloads
- Large file transfers
- Service-to-service traffic

Security analysis should identify anomalies and then correlate them with workload ownership and expected behavior.

---

## Detecting Port Scanning

Repeated connection attempts against many ports can indicate scanning.

Example:

```text
10.0.50.25 -> 10.0.20.10:22    REJECT
10.0.50.25 -> 10.0.20.10:80    REJECT
10.0.50.25 -> 10.0.20.10:443   REJECT
10.0.50.25 -> 10.0.20.10:5432  REJECT
10.0.50.25 -> 10.0.20.10:6379  REJECT
```

A useful detection strategy is to aggregate by:

```text
source address
+
destination address
+
number of distinct destination ports
+
time window
```

However, legitimate security scanners and monitoring systems can produce the same pattern.

Maintain allow-lists for known security tooling where appropriate.

---

## Detecting Unexpected PostgreSQL Access

PostgreSQL commonly listens on:

```text
5432
```

A production analysis should identify unexpected sources attempting to reach database ports.

Example:

```text
Source       Destination     Port    Action
------------------------------------------------
10.0.10.20   10.0.20.15      5432    ACCEPT
10.0.10.21   10.0.20.15      5432    ACCEPT
10.0.50.20   10.0.20.15      5432    REJECT
10.0.60.30   10.0.20.15      5432    REJECT
```

The first two may be expected application workloads.

The rejected connections could indicate:

- Incorrect application configuration
- An unauthorized workload
- Security scanning
- Network reconnaissance
- A compromised workload

Correlate the source IP or ENI with the resource inventory before making a security determination.

---

## Detecting Unexpected Redis Access

Redis commonly uses port `6379`.

A typical production architecture is:

```text
API Services
    |
    | TCP 6379
    v
Redis
```

If an unexpected subnet attempts to connect:

```text
Unknown workload
      |
      | TCP 6379
      v
Redis
      |
      +-- REJECT
```

this deserves investigation.

Redis should generally not be exposed to arbitrary workloads.

Flow Logs can help detect attempted access, while Security Groups and other controls enforce the intended access policy.

---

## Flow Logs and Security Groups

Consider:

```text
API
 |
 | TCP 5432
 v
RDS PostgreSQL
```

If the API cannot connect, inspect:

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
Network ACL
 |
 v
Destination
```

Flow Logs provide evidence of observed traffic.

For example:

```text
srcaddr=10.0.10.25
dstaddr=10.0.20.15
dstport=5432
action=REJECT
```

This indicates that the traffic was rejected, but Flow Logs should not be treated as a direct mapping to one specific Security Group rule.

Inspect the complete network path.

---

## Flow Logs and Network ACLs

Network ACLs operate at the subnet boundary.

A simplified path is:

```text
Application Subnet
      |
      v
Subnet Routing
      |
      v
Network ACL
      |
      v
Destination Subnet
```

If a NACL blocks traffic, Flow Logs can help reveal the resulting rejected traffic.

Remember that NACLs are stateless.

For a TCP connection, return traffic must independently satisfy the applicable NACL rules.

This is particularly important when ephemeral ports are involved.

---

## Flow Logs and Ephemeral Ports

A typical TCP connection looks like:

```text
Client
10.0.10.25:49152
        |
        | TCP
        v
Server
10.0.20.15:5432
```

The client chooses an ephemeral source port.

The response flows in the opposite direction:

```text
Server
10.0.20.15:5432
        |
        | TCP
        v
Client
10.0.10.25:49152
```

Because Security Groups are stateful, the response is automatically allowed when the connection is permitted.

Network ACLs are stateless, so the corresponding return traffic must be allowed by the NACL rules.

Flow Logs can help diagnose these asymmetric rule mistakes.

---

## Flow Logs and NAT Gateways

Private workloads often use a NAT Gateway for outbound internet access:

```mermaid
flowchart LR
    App["Private Application"]
    NAT["NAT Gateway"]
    IGW["Internet Gateway"]
    Internet["External Service"]

    App --> NAT
    NAT --> IGW
    IGW --> Internet
```

A useful investigation may involve:

```text
Application ENI
      |
      v
NAT Gateway path
      |
      v
External destination
```

For example:

```text
10.0.10.25 -> external-service:443
```

If outbound traffic fails, inspect:

- Private subnet route table
- NAT Gateway availability
- NAT subnet route table
- Internet Gateway
- Security Groups
- Network ACLs
- Flow Logs

For NAT-related investigations, identify the relevant ENIs and network path rather than looking only at the application log.

---

## Flow Logs and VPC Endpoints

Private workloads can access AWS services without traversing the public internet through VPC endpoints.

For an interface endpoint:

```text
Application
    |
    | TCP 443
    v
Endpoint ENI
    |
    v
AWS Service
```

Flow Logs can help investigate:

- Endpoint connectivity
- Endpoint ENI access
- Security Group configuration
- Unexpected endpoint traffic
- Application connectivity failures

For gateway endpoints such as S3 and DynamoDB, routing behavior differs because traffic is handled through route tables rather than an endpoint ENI.

Always identify the actual endpoint type before interpreting the network path.

---

## Flow Logs and Load Balancers

Consider:

```text
Client
  |
  v
ALB
  |
  v
ECS
  |
  v
RDS
```

Flow Logs can help inspect network connectivity between:

```text
ALB -> ECS
ECS -> RDS
```

For HTTP-level information, use ALB access logs.

For application behavior, use Django, FastAPI, or service logs.

The telemetry layers complement each other:

| Layer | Example Question |
|---|---|
| Flow Logs | Did the TCP connection occur? |
| ALB logs | Which HTTP request reached the ALB? |
| Application logs | What did Django/FastAPI do? |
| Database logs | What happened inside PostgreSQL? |

---

## Flow Logs and DNS

Flow Logs primarily expose IP-level communication.

They do not replace DNS query logging.

For example:

```text
DNS Query Logs
    |
    +-- worker.internal -> api.example.com
    |
    v
Resolved IP
203.0.113.25

VPC Flow Logs
    |
    +-- 10.0.10.25 -> 203.0.113.25:443
```

Correlating these sources can answer:

```text
Which hostname did this workload resolve?
Which IP did it connect to?
```

This is particularly useful for outbound security investigations.

---

## Security Investigation Workflow

A disciplined investigation should move from network evidence to resource identity and then to application context.

```mermaid
flowchart TD
    Event["Suspicious Network Event"]
    Flow["Inspect VPC Flow Logs"]
    Source["Identify Source ENI / IP"]
    Destination["Identify Destination"]
    Port["Analyze Port / Protocol"]
    Resource["Identify Owning Workload"]
    App["Inspect Application Logs"]
    DNS["Inspect DNS Logs"]
    Trail["Inspect CloudTrail"]
    Guard["Inspect GuardDuty"]
    Decision["Determine Cause / Risk"]

    Event --> Flow
    Flow --> Source
    Flow --> Destination
    Flow --> Port
    Source --> Resource
    Resource --> App
    Resource --> DNS
    Resource --> Trail
    Resource --> Guard
    Destination --> Decision
    Port --> Decision
    App --> Decision
    DNS --> Decision
    Trail --> Decision
    Guard --> Decision
```

A practical sequence is:

1. Identify the source.
2. Identify the destination.
3. Identify the port and protocol.
4. Determine whether traffic was accepted or rejected.
5. Identify the owning workload.
6. Determine whether the communication is expected.
7. Inspect Security Groups, NACLs, and routing.
8. Correlate application logs.
9. Correlate DNS logs where relevant.
10. Check CloudTrail and GuardDuty for additional evidence.
11. Escalate to incident response if compromise is suspected.

---

## Detecting Potential Data Exfiltration

Flow Logs can help identify suspicious outbound traffic patterns.

Potential indicators include:

- Unexpected external destinations
- Large outbound byte volumes
- Sudden changes in traffic patterns
- Unexpected destination ports
- Long-lived external connections
- Workloads communicating directly with public IPs
- Unexpected cross-account or cross-VPC communication

Example:

```text
Normal:

Application
   |
   +-- PostgreSQL
   +-- Redis
   +-- S3
   +-- Payment API


Potential anomaly:

Application
   |
   +-- Unknown public IP:4444
   +-- Unknown public IP:4444
   +-- Unknown public IP:4444
```

This does not establish exfiltration.

It identifies a network behavior requiring investigation.

---

## Security Analysis Should Be Baseline-Based

Static rules alone are often insufficient for meaningful security analysis.

Instead, establish expected communication patterns.

Example:

```text
API subnet
    |
    +-- RDS:5432
    +-- Redis:6379
    +-- External APIs:443

Worker subnet
    |
    +-- Kafka:9092
    +-- Redis:6379
    +-- S3
```

An unexpected communication such as:

```text
API -> Kafka:9092
```

may be legitimate or suspicious depending on the architecture.

The important point is that the security system understands the expected topology.

---

## Application Example

Consider a Django backend:

```mermaid
flowchart LR
    Client["Client"]
    ALB["Application Load Balancer"]
    Django["Django / FastAPI"]
    Redis["Redis"]
    RDS["PostgreSQL"]
    S3["S3"]
    Payment["Payment API"]

    Client --> ALB
    ALB --> Django
    Django --> Redis
    Django --> RDS
    Django --> S3
    Django --> Payment
```

Suppose the application reports:

```text
Payment provider timeout
```

A useful investigation is:

```text
Application Logs
    |
    +-- Timeout to payment API

DNS Logs
    |
    +-- Correct hostname resolution

VPC Flow Logs
    |
    +-- Application -> payment API:443 ACCEPT

Route / NACL / SG
    |
    +-- No obvious network rejection

External Service
    |
    +-- Provider outage
```

Flow Logs did not identify the entire root cause.

They helped eliminate one class of network failures.

That is an important production use case.

---

## Kubernetes and EKS

For EKS workloads, Flow Logs provide VPC-level network visibility around the underlying network interfaces.

Conceptually:

```text
Pod
 |
 v
Node / ENI
 |
 v
VPC
 |
 v
Destination
```

Flow Logs generally do not provide Kubernetes identity such as:

```text
namespace
pod name
container name
service name
```

Correlate Flow Logs with:

- Kubernetes metadata
- EKS/VPC CNI information
- Container logs
- Kubernetes audit logs
- Load balancer logs
- Runtime security telemetry

Flow Logs should therefore be considered a network telemetry layer rather than a complete Kubernetes network-observability system.

---

## Configuring Flow Logs

For production environments, Flow Log configuration should generally be managed through Infrastructure as Code.

A conceptual AWS CLI example for a CloudWatch Logs destination is:

```bash
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-0123456789abcdef0 \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/flow-logs/production
```

The required IAM configuration depends on the destination and deployment model.

For production systems, validate:

- Correct VPC
- Correct region
- Correct destination
- Correct IAM permissions
- Correct traffic type
- Correct log format
- Correct retention policy

Do not rely on manually configured production Flow Logs when the infrastructure is otherwise managed through CI/CD and Infrastructure as Code.

---

## S3 Destination

An S3 destination can be used for durable storage and historical analysis.

Conceptually:

```bash
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-0123456789abcdef0 \
  --traffic-type ALL \
  --log-destination-type s3 \
  --log-destination arn:aws:s3:::company-vpc-flow-logs
```

Production S3 configuration should consider:

- Server-side encryption
- Bucket policy
- Least-privilege access
- Lifecycle policies
- Retention
- Centralized logging architecture
- Monitoring
- Cross-account access controls where appropriate

Flow Logs contain infrastructure metadata and should not be treated as ordinary application data.

---

## Custom Flow Log Formats

A custom format can include the fields required by the organization's operational and security workflows.

For example:

```text
${version}
${account-id}
${vpc-id}
${subnet-id}
${interface-id}
${srcaddr}
${dstaddr}
${srcport}
${dstport}
${protocol}
${packets}
${bytes}
${start}
${end}
${action}
${log-status}
```

The exact field names and availability should be validated against the current AWS Flow Logs record format supported by the target environment.

A useful principle is:

> Do not optimize the log schema only for today's dashboards. Preserve fields required for future incident investigation.

---

## One-Minute vs Ten-Minute Aggregation

| Aggregation | Advantage | Trade-off |
|---|---|---|
| 1 minute | Finer-grained network visibility | Potentially more records |
| 10 minutes | Lower record volume | Coarser temporal analysis |

For security investigations where timing matters, shorter aggregation can be valuable.

However:

```text
Aggregation interval
!=
Delivery latency
```

A one-minute aggregation interval does not guarantee one-minute end-to-end visibility.

---

## Cost Considerations

Flow Logs can produce significant data volumes in large VPCs.

Cost drivers include:

- Traffic volume
- Number of interfaces
- Number of VPCs
- CloudWatch ingestion
- CloudWatch storage
- S3 storage
- Athena query volume
- Firehose processing
- Downstream SIEM ingestion
- Retention duration

A production architecture should explicitly define:

```text
Collection
    +
Retention
    +
Query requirements
    +
Security requirements
    +
Cost constraints
```

Do not automatically retain every record in the most expensive system indefinitely.

---

## S3 Cost Optimization

For large historical datasets, S3 is generally a strong foundation because storage and analytics can be separated.

A scalable architecture is:

```text
Flow Logs
    |
    v
S3
    |
    v
Partitioned Dataset
    |
    v
Athena
```

Use:

- Time-based partitioning
- Compression
- Columnar formats where appropriate
- Lifecycle policies
- Targeted Athena queries

Avoid repeatedly scanning years of Flow Logs when the investigation concerns a five-minute window.

---

## Monitoring the Flow Log Pipeline

Logging infrastructure itself must be monitored.

Monitor:

```text
Flow Log Configuration
        |
        v
Delivery
        |
        v
Destination
        |
        v
Query / Analysis
```

Useful operational checks include:

- Flow Log configuration status
- Delivery failures
- Missing log data
- Unexpected volume drops
- Unexpected volume spikes
- CloudWatch ingestion anomalies
- S3 delivery gaps
- Destination permission failures
- Retention-policy drift

A security control that silently stops producing telemetry is an operational risk.

---

## Detecting Logging Gaps

Consider:

```text
00:00 -> Logs present
00:05 -> Logs present
00:10 -> Logs present
00:15 -> No logs
00:20 -> No logs
```

Possible explanations include:

- No traffic occurred
- Delivery failed
- Logging configuration changed
- Resource was replaced
- Destination access failed
- Query boundaries are incorrect
- Data is delayed

Do not immediately conclude:

```text
No logs = No traffic
```

First validate the logging pipeline.

---

## High Availability

Flow Logs are not part of the application's request-serving path.

The application must continue functioning if the Flow Log destination becomes temporarily unavailable.

Do not build:

```text
HTTP Request
   |
   v
Flow Log availability
   |
   v
Application response
```

Instead:

```text
Application
    |
    +---- Request path
    |
    +---- Independent telemetry path
                 |
                 v
             Flow Logs
```

Critical security programs should use multiple telemetry sources rather than depending on one logging mechanism.

---

## Disaster Recovery and Retention

Flow Log retention should align with:

- Incident-response requirements
- Security policies
- Compliance requirements
- Operational needs
- Storage cost
- Legal requirements

A common architecture is:

```text
Production VPC
      |
      v
Flow Logs
      |
      v
Central S3 Logging Account
      |
      +-- Lifecycle policies
      +-- Encryption
      +-- Restricted access
      +-- Long-term retention
```

For organizations with multiple AWS accounts, centralized logging can simplify security analysis and reduce fragmented investigation workflows.

---

## Security of Flow Log Data

Flow Logs can reveal:

- Internal IP addresses
- Network topology
- Service relationships
- Destination ports
- Traffic volumes
- Workload communication patterns
- AWS resource metadata

Protect the logs accordingly.

Recommended controls include:

- Encryption at rest
- Least-privilege access
- Restricted S3 bucket policies
- Controlled CloudWatch permissions
- Appropriate retention
- Centralized security-account access
- Monitoring access to sensitive log repositories
- Infrastructure-as-Code management

The logging system itself should be considered part of the security boundary.

---

## Common Mistakes

### Treating Flow Logs as Packet Capture

Flow Logs contain flow metadata.

They do not provide complete packet contents.

If packet-level inspection is required, use appropriate packet-analysis mechanisms such as VPC Traffic Mirroring where supported and justified.

### Expecting Real-Time Detection

Flow Log aggregation and delivery are not equivalent to a real-time packet stream.

Use appropriate real-time security controls for immediate enforcement.

### Assuming `REJECT` Means Attack

A rejection can be caused by a simple misconfiguration.

Always establish context.

### Assuming `ACCEPT` Means Safe

Accepted traffic can still be malicious.

Network controls determine connectivity, not intent.

### Ignoring Return Traffic

NACLs are stateless.

A connection can fail because the forward direction is allowed while return traffic is blocked.

### Looking Only at IP Addresses

An IP address alone may not identify the workload responsible for the traffic.

Correlate addresses with:

- ENIs
- Instances
- ECS tasks
- EKS nodes
- Load balancers
- NAT Gateways
- VPC endpoints

### Ignoring DNS

Flow Logs can show an IP address but not necessarily the hostname that resolved to it.

Correlate with DNS query logs when hostname context matters.

### Alerting on Every Rejection

High-volume environments naturally produce rejected traffic.

Use thresholds, aggregation, baselines, and context.

### Keeping Everything in CloudWatch Forever

Large historical datasets can become expensive and difficult to analyze.

Use an appropriate storage and analytics strategy.

### Assuming Missing Logs Mean Missing Traffic

Validate delivery and configuration before drawing conclusions.

---

## Production Troubleshooting Workflow

For an application connectivity problem:

```text
Application Error
      |
      v
DNS
      |
      v
Route
      |
      v
Security Group
      |
      v
Network ACL
      |
      v
NAT / Endpoint / Load Balancer
      |
      v
VPC Flow Logs
      |
      v
Destination
```

For security analysis:

```text
Security Event
      |
      v
Flow Logs
      |
      +-- Source
      +-- Destination
      +-- Port
      +-- Protocol
      +-- Bytes
      +-- Action
      |
      v
Resource Identification
      |
      +-- Application Logs
      +-- DNS Logs
      +-- CloudTrail
      +-- GuardDuty
      |
      v
Investigation
```

---

## Backend Engineering Example

Consider a production backend:

```text
                    Internet
                       |
                       v
                     ALB
                       |
                       v
              Django / FastAPI
                 /    |     \
                /     |      \
               v      v       v
            Redis   RDS     S3
                     |
                     v
                PostgreSQL
```

Suppose users report:

```text
API requests are timing out.
```

The investigation could proceed:

```text
1. Application logs
   -> request timeout

2. DNS
   -> expected hostname resolves correctly

3. Flow Logs
   -> application -> database:5432 REJECT

4. Security Group
   -> application SG is not allowed by database SG

5. Fix
   -> add the intended SG-to-SG rule

6. Validation
   -> new Flow Logs show ACCEPT
```

This is a realistic production use case for Flow Logs because the logs provide network evidence that narrows the failure domain.

---

## Infrastructure as Code

Flow Log configuration should be version-controlled alongside the VPC.

A Terraform implementation can conceptually look like:

```hcl
resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  name              = "/aws/vpc/flow-logs/production"
  retention_in_days = 30
}

resource "aws_flow_log" "production" {
  vpc_id          = aws_vpc.production.id
  traffic_type    = "ALL"
  log_destination = aws_cloudwatch_log_group.vpc_flow_logs.arn

  tags = {
    Name        = "production-vpc-flow-logs"
    Environment = "production"
  }
}
```

The exact IAM configuration and provider arguments depend on the selected Flow Log destination and current AWS provider behavior.

The important engineering properties are:

- Reproducibility
- Code review
- Environment consistency
- Drift detection
- Automated deployment
- Auditable configuration

---

## Operational Baselines

Security analysis becomes more useful when expected traffic patterns are documented.

For example:

```text
API Subnet
    |
    +-- PostgreSQL:5432
    +-- Redis:6379
    +-- HTTPS:443

Worker Subnet
    |
    +-- Kafka:9092
    +-- Redis:6379
    +-- S3

Database Subnet
    |
    +-- PostgreSQL:5432
```

An unexpected connection:

```text
API -> Kafka:9092
```

may be legitimate or suspicious.

Without an architecture baseline, the security system cannot easily distinguish the two.

---

## Flow Logs and Microservices

Microservice architectures generate significant east-west traffic:

```text
Service A
    |
    +---- Service B
    |
    +---- Service C
    |
    +---- Redis
    |
    +---- Kafka
    |
    +---- PostgreSQL
```

Flow Logs can help answer:

- Which services communicate?
- Which connections are rejected?
- Are services communicating across unexpected subnets?
- Which workloads generate the most traffic?
- Did a deployment introduce a new network dependency?

However, Flow Logs do not inherently understand:

```text
service-a
service-b
payment-service
inventory-service
```

Application and orchestration metadata must be correlated with network telemetry.

---

## Interview Traps

### Are VPC Flow Logs packet captures?

No. They provide aggregated network-flow metadata.

### Can Flow Logs show HTTP URLs?

No. They operate below the application layer.

### Does `ACCEPT` mean the traffic is secure?

No. It means the traffic was accepted at the relevant network layer.

### Does `REJECT` mean an attack occurred?

No. It only indicates rejected traffic.

### Can Flow Logs replace Security Groups?

No.

Security Groups enforce traffic policy; Flow Logs provide visibility into traffic behavior.

### Can Flow Logs replace Network ACLs?

No.

NACLs provide subnet-level stateless filtering; Flow Logs provide telemetry.

### Can Flow Logs replace CloudTrail?

No.

```text
Flow Logs -> Network traffic
CloudTrail -> AWS API activity
```

### Can Flow Logs replace GuardDuty?

No.

GuardDuty provides managed threat detection; Flow Logs provide network telemetry for your own analysis.

### Do Flow Logs provide application identity?

Not directly.

You need correlation with infrastructure and application metadata.

### Can Flow Logs be used for historical analysis?

Yes. S3 plus Athena is a common architecture for large-scale historical analysis.

---

## Production Checklist

Before considering VPC Flow Logs production-ready, verify:

- [ ] Correct VPC, subnet, or ENI scope
- [ ] `ALL`, `ACCEPT`, or `REJECT` selected intentionally
- [ ] Required fields included
- [ ] Appropriate aggregation interval selected
- [ ] Correct destination configured
- [ ] Required IAM permissions configured
- [ ] CloudWatch or S3 destination protected
- [ ] Encryption configured
- [ ] Retention policy configured
- [ ] Access restricted using least privilege
- [ ] Operational queries tested
- [ ] Rejected-traffic analysis tested
- [ ] High-volume traffic analysis tested
- [ ] Logging pipeline monitored
- [ ] Delivery failures detected
- [ ] Application telemetry can be correlated
- [ ] DNS telemetry is available where required
- [ ] CloudTrail and GuardDuty are integrated into security investigations where appropriate
- [ ] Long-term retention requirements are documented
- [ ] Cost impact is understood
- [ ] Configuration is managed through Infrastructure as Code

---

## Key Takeaways

- **VPC Flow Logs provide network-flow telemetry, not packet captures or application-layer logs**; use them to understand connectivity, traffic patterns, and network behavior.
- `ACCEPT` does not mean trusted and `REJECT` does not automatically mean malicious; Flow Logs must be correlated with workload identity, application logs, DNS, CloudTrail, and security telemetry.
- Use Flow Logs to investigate **Security Groups, Network ACLs, routes, NAT Gateways, VPC endpoints, load balancers, unexpected ports, and suspicious network behavior**.
- **CloudWatch Logs is well suited to operational investigation, while S3 plus Athena is well suited to scalable historical analysis**; choose the destination based on volume, retention, query, security, and cost requirements.
- Treat Flow Logs as one layer of a broader security architecture alongside **GuardDuty, CloudTrail, DNS logging, application telemetry, and infrastructure metadata**.