# 01- VPC Flow Logs

## Overview

Amazon VPC Flow Logs provide network traffic metadata for interfaces and other supported VPC resources. They are primarily an observability and security-analysis mechanism rather than a packet-capture system.

Flow Logs are valuable because a connectivity failure or security incident often cannot be explained from application logs alone. An API may report a timeout, while the underlying network reason could be a rejected Security Group rule, a rejected Network ACL rule, an incorrect route, an unexpected source address, or an incorrect destination port.

Flow Logs provide a record of network traffic metadata that can be analyzed alongside:

- Security Group configuration
- Network ACL configuration
- Route tables
- Application logs
- Load balancer logs
- CloudTrail events
- DNS logs
- AWS security findings
- Infrastructure as Code history

A production backend architecture should treat network telemetry as part of its operational model:

```text
Application
    |
    v
Network Request
    |
    +--> Routing
    |
    +--> Security Groups
    |
    +--> Network ACLs
    |
    v
Network Interface
    |
    v
VPC Flow Logs
    |
    +--> CloudWatch Logs
    |
    +--> Amazon S3
    |
    +--> Security Analysis
    |
    +--> Troubleshooting
```

## What VPC Flow Logs Capture

A flow log records metadata about IP traffic flowing to and from network interfaces or supported VPC resources.

It does **not** provide the complete contents of the packets.

Typical information includes:

| Field | Purpose |
|---|---|
| Source address | Identifies the source of the traffic |
| Destination address | Identifies the destination |
| Source port | Identifies the originating transport port |
| Destination port | Identifies the destination service port |
| Protocol | Identifies TCP, UDP, ICMP, and other supported protocols |
| Packets | Number of packets in the flow |
| Bytes | Amount of data transferred |
| Start time | Beginning of the aggregation interval |
| End time | End of the aggregation interval |
| Action | Whether the traffic was accepted or rejected |
| Log status | Whether the flow log was successfully recorded |

The exact fields available depend on the selected flow-log format and AWS capabilities.

A simplified record can be thought of as:

```text
source -> destination : protocol/port : packets/bytes : ACCEPT/REJECT
```

For example:

```text
10.0.10.25:49152
        |
        | TCP
        v
10.0.20.50:5432
        |
        +--> ACCEPT
```

This can indicate that a workload in an application subnet successfully generated traffic toward PostgreSQL.

## Why Flow Logs Exist

Network connectivity problems are often difficult to diagnose because multiple independent controls can affect traffic.

Consider:

```text
FastAPI
   |
   v
ALB
   |
   v
Application ENI
   |
   v
PostgreSQL
```

An API request timing out does not immediately tell you whether:

- The route is missing.
- The Security Group blocks the connection.
- A NACL rejects the traffic.
- The application is not listening.
- PostgreSQL is unavailable.
- The destination is incorrect.
- The application is connecting to the wrong port.
- A network path is unexpectedly unavailable.

Flow Logs provide network-level evidence that helps narrow the problem.

## Flow Logs vs Packet Capture

Flow Logs should not be confused with packet capture.

| Capability | VPC Flow Logs | Packet Capture |
|---|---|---|
| Traffic metadata | Yes | Yes |
| Full packet payload | No | Potentially |
| Source/destination | Yes | Yes |
| Ports | Yes | Yes |
| Protocol | Yes | Yes |
| Packet-level inspection | No | Yes |
| Application payload | No | Potentially |
| Operational overhead | Relatively low | Higher |
| Typical use | Network visibility and analysis | Deep protocol debugging |

For most production AWS environments, Flow Logs are the first layer of network telemetry.

## Where Flow Logs Apply

Flow Logs can be configured at supported AWS resource scopes such as:

- VPC
- Subnet
- Network interface

The scope determines which traffic is captured.

A VPC-level configuration is generally useful when centralized visibility is required, while narrower scopes can be useful for targeted investigation or reducing unnecessary data volume.

The important engineering question is not simply:

> "Are Flow Logs enabled?"

It is:

> "Do the enabled Flow Logs provide sufficient coverage for the traffic that must be investigated?"

## Flow Log Architecture

A typical production design sends Flow Logs to a centralized destination.

```mermaid
flowchart LR
    ENI["Network Interfaces"]
    FL["VPC Flow Logs"]

    ENI --> FL

    FL --> CW["CloudWatch Logs"]
    FL --> S3["Amazon S3"]

    CW --> Alert["Operational / Security Analysis"]
    S3 --> Athena["Athena / SQL Analysis"]
    S3 --> SIEM["Security Analytics / SIEM"]
```

### CloudWatch Logs

CloudWatch Logs are useful when:

- Near-real-time operational analysis is required.
- Logs need to be queried with CloudWatch tooling.
- Alerts and dashboards are integrated into CloudWatch.
- Engineers need convenient access during incidents.

### Amazon S3

S3 is useful when:

- Large volumes of historical logs must be retained.
- Long-term retention is required.
- Logs will be queried with Athena.
- Centralized security data lakes are used.
- Cost-efficient archival is important.

A mature architecture may use both.

## Flow Log Lifecycle

The logical lifecycle is:

```mermaid
sequenceDiagram
    participant W as Workload
    participant N as VPC Network
    participant F as Flow Logs
    participant D as Log Destination
    participant A as Analyst

    W->>N: Send network traffic
    N->>N: Evaluate network path
    N->>F: Record flow metadata
    F->>D: Deliver flow record
    A->>D: Query traffic
    D-->>A: Return matching flows
```

Flow Logs therefore observe network traffic rather than actively controlling it.

## Accepted and Rejected Traffic

One of the most useful Flow Log fields is the traffic action.

Typical values include:

```text
ACCEPT
REJECT
```

### ACCEPT

An accepted flow indicates that the recorded traffic was accepted by the relevant network controls for the logged traffic path.

It does **not** mean:

- The application accepted the request.
- Authentication succeeded.
- Authorization succeeded.
- The destination service was healthy.
- The application processed the request successfully.

For example:

```text
Client
  |
  | TCP :443
  v
ALB
  |
  +--> Network traffic ACCEPTED
  |
  v
Application
  |
  +--> HTTP 500
```

The Flow Log can show successful network delivery while the application still fails.

### REJECT

A rejected flow indicates that traffic was rejected by a relevant network control.

This is particularly useful for investigating:

- Security Group configuration
- Network ACL rules
- Unexpected traffic
- Port scanning
- Misconfigured clients
- Incorrect application destinations

A rejected flow should be treated as evidence, not automatically as an incident.

For example:

```text
10.0.10.25 -> 10.0.20.50:5432 -> REJECT
```

This may indicate:

- Missing Security Group authorization.
- A restrictive NACL.
- Incorrect destination.
- A client connecting to the wrong port.

## Traffic Aggregation

Flow Logs are records of network flows rather than a packet-by-packet trace.

AWS aggregates traffic information over an interval before publishing records.

This distinction matters during troubleshooting.

If an application performs:

```text
TCP SYN
TCP SYN/ACK
TCP ACK
HTTP request
HTTP response
```

you should not expect Flow Logs to behave like a packet analyzer showing each packet as a separate detailed record.

Instead, Flow Logs provide aggregated metadata about the observed flow.

This makes them suitable for:

- Connectivity analysis
- Traffic patterns
- Security investigation
- Network baselining

but not for reconstructing an entire TCP conversation.

## Traffic Analysis Example

Suppose an application server at:

```text
10.0.10.25
```

connects to PostgreSQL at:

```text
10.0.20.50:5432
```

A useful investigation starts with:

```text
Source:
10.0.10.25

Destination:
10.0.20.50

Destination Port:
5432

Protocol:
TCP

Action:
ACCEPT / REJECT
```

If the flow is rejected:

```text
10.0.10.25 -> 10.0.20.50:5432 -> REJECT
```

inspect:

1. Application Security Group.
2. Database Security Group.
3. Network ACLs.
4. Route tables.
5. Subnet placement.
6. Actual destination IP.
7. Actual destination port.
8. IPv4 vs IPv6 path.

If the flow is accepted but the application times out, continue upward into:

- DNS
- TCP connection behavior
- Database availability
- Application configuration
- Connection pools
- TLS
- Authentication
- Application logs

This prevents treating Flow Logs as the complete diagnostic system.

## Security Analysis

Flow Logs are useful for identifying traffic that deviates from expected architecture.

Suppose the intended architecture is:

```text
ALB
 |
 v
API
 |
 v
PostgreSQL
```

Expected traffic might be:

```text
ALB -> API :443
API -> PostgreSQL :5432
```

Unexpected traffic might look like:

```text
API -> Internet :22
API -> Database :6379
Database -> Internet :443
Unknown -> API :8080
```

These patterns can indicate:

- Misconfiguration
- Excessive permissions
- Compromised workloads
- Unauthorized services
- Incorrect deployment configuration
- Unexpected software behavior

Flow Logs therefore become more valuable when combined with an expected network architecture.

## Detecting Unexpected Ports

Suppose application servers should only communicate with:

```text
443
5432
6379
9092
```

A query or analysis pipeline can identify other destination ports.

Conceptually:

```text
Expected:
443
5432
6379
9092

Observed:
443
5432
6379
9092
22      <-- investigate
4444    <-- investigate
8080    <-- investigate
```

Unexpected traffic is not automatically malicious. It should be correlated with:

- Deployment changes
- New services
- Maintenance activity
- Container images
- Infrastructure changes
- Security findings

## Detecting Repeated Rejections

Repeated rejected traffic can reveal either configuration problems or suspicious activity.

Example:

```text
10.0.10.25 -> 10.0.20.50:5432 -> REJECT
10.0.10.25 -> 10.0.20.50:5432 -> REJECT
10.0.10.25 -> 10.0.20.50:5432 -> REJECT
```

Possible causes:

- Missing Security Group rule.
- Incorrect source Security Group.
- Incorrect subnet NACL.
- Wrong database endpoint.
- Application configuration error.

The same pattern from an unknown external source against many ports may instead indicate scanning.

## Troubleshooting Network Connectivity

A disciplined troubleshooting process should move from network path to application behavior.

```text
Application Error
      |
      v
Is DNS correct?
      |
      v
Is destination IP correct?
      |
      v
Does routing exist?
      |
      v
Do Flow Logs show traffic?
      |
      +---- REJECT --> Inspect SG/NACL
      |
      +---- ACCEPT --> Continue
      |
      v
Does the destination service listen?
      |
      v
Does TLS/authentication succeed?
      |
      v
Does the application succeed?
```

### Example: PostgreSQL Timeout

Suppose Django reports:

```text
connection timed out
```

Do not immediately change the database Security Group.

Check:

```text
Django workload
    |
    +--> DNS resolution
    |
    +--> Destination IP
    |
    +--> Route table
    |
    +--> Flow Logs
    |
    +--> Security Group
    |
    +--> NACL
    |
    +--> PostgreSQL listener
```

If Flow Logs show:

```text
10.0.10.25 -> 10.0.20.50:5432 REJECT
```

network access is a strong candidate.

If they show:

```text
10.0.10.25 -> 10.0.20.50:5432 ACCEPT
```

the investigation should move toward the destination and application layers.

## Flow Logs and Security Groups

Flow Logs do not replace Security Group inspection.

Security Groups answer:

```text
What traffic should be allowed?
```

Flow Logs answer:

```text
What traffic was observed and what was its recorded action?
```

Together:

```text
Security Policy
      |
      v
Security Group
      |
      v
Actual Network Traffic
      |
      v
Flow Logs
```

This distinction is important during incident response.

## Flow Logs and Network ACLs

NACLs are stateless, so troubleshooting rejected traffic can require analyzing both directions.

For example:

```text
Application
10.0.10.25:49152
       |
       | request
       v
Database
10.0.20.50:5432
       |
       | response
       v
Application
10.0.10.25:49152
```

A restrictive NACL must allow the relevant traffic in both directions.

Flow Logs can help reveal which direction is being rejected.

## Centralized Logging

Production environments commonly have multiple VPCs and AWS accounts.

A centralized architecture can look like:

```text
Account A / VPC A
        |
        +--> Flow Logs
        |
Account B / VPC B
        |
        +--> Flow Logs
        |
Account C / VPC C
        |
        +--> Flow Logs
        |
        v
Central Logging Account
        |
        +--> S3
        +--> CloudWatch
        +--> SIEM
        +--> Security Analytics
```

Centralization provides:

- Consistent retention.
- Cross-account investigation.
- Central security monitoring.
- Easier compliance management.
- Reduced dependence on individual application teams.

Access to centralized logs should itself be protected using least-privilege IAM.

## Storage Destination Considerations

| Destination | Best For | Advantages | Trade-offs |
|---|---|---|---|
| CloudWatch Logs | Operational investigation | Convenient querying and integration | Can become expensive at high volume |
| S3 | Long-term retention | Durable, scalable, cost-efficient storage | Requires additional query/analysis tooling |
| Central SIEM | Security operations | Correlation and alerting | Additional platform and ingestion costs |

The right destination depends on:

- Traffic volume
- Retention requirements
- Compliance
- Query frequency
- Security operations
- Cost constraints

## Cost Considerations

Flow Logs generate additional logging volume.

High-volume VPC environments can produce substantial data because of:

- Large numbers of interfaces.
- High traffic rates.
- Many VPCs.
- Many accounts.
- Long retention periods.
- Verbose custom fields.

Production cost controls include:

- Define retention requirements explicitly.
- Avoid retaining all data in expensive hot storage indefinitely.
- Archive long-term data to S3 where appropriate.
- Compress and partition data for analytical workloads.
- Centralize analysis rather than duplicating pipelines unnecessarily.
- Monitor log ingestion and storage costs.

Security telemetry should not be disabled solely because it generates cost without first evaluating its operational and compliance value.

## Querying Flow Logs in CloudWatch

For CloudWatch Logs, filtering can be used to find rejected traffic.

Conceptually:

```text
REJECT
```

can be filtered to identify rejected network flows.

A more useful investigation may filter on:

```text
source address
destination address
destination port
protocol
action
```

For example:

```text
Source = 10.0.10.25
Destination = 10.0.20.50
Port = 5432
Action = REJECT
```

The exact query syntax depends on the log format and destination.

## Querying Flow Logs in S3

S3-backed Flow Logs are well suited to analytical workloads.

A common architecture is:

```text
VPC Flow Logs
      |
      v
S3
      |
      v
AWS Glue Catalog
      |
      v
Athena
      |
      v
SQL Analysis
```

This allows questions such as:

```sql
SELECT
    srcaddr,
    dstaddr,
    dstport,
    action,
    SUM(bytes) AS total_bytes
FROM vpc_flow_logs
WHERE action = 'REJECT'
GROUP BY
    srcaddr,
    dstaddr,
    dstport,
    action;
```

The exact schema and field names depend on how the Flow Logs are configured and cataloged.

## Security Investigation Workflow

A practical incident workflow is:

### Identify the Workload

Determine:

- Instance
- ENI
- ECS task
- EKS node or workload
- Load balancer
- Subnet
- VPC
- AWS account

### Establish Expected Traffic

Document the intended path:

```text
Source
  |
  v
Route
  |
  v
Destination
```

Then determine expected:

- Source
- Destination
- Protocol
- Port
- Direction

### Search Flow Logs

Look for:

- ACCEPT
- REJECT
- Unexpected source
- Unexpected destination
- Unexpected ports
- Unusual traffic volume

### Correlate With Other Telemetry

Combine Flow Logs with:

- CloudTrail
- Application logs
- ALB logs
- DNS logs
- Container logs
- Kubernetes audit logs
- Security findings

### Determine Root Cause

Classify the issue as:

- Network configuration
- Application configuration
- Infrastructure change
- Security event
- Expected traffic
- Unknown behavior

## Security Considerations

Flow Logs contain sensitive network metadata.

They may reveal:

- Internal IP addresses
- Network topology
- Service relationships
- Port usage
- Traffic patterns
- Infrastructure structure

Protect them accordingly.

Recommended controls include:

- Restrict log access with IAM.
- Encrypt log storage.
- Use appropriate retention policies.
- Protect centralized logging accounts.
- Prevent unauthorized deletion.
- Monitor changes to logging configuration.
- Separate security operations access from application access where appropriate.

Flow Logs should not become a source of sensitive infrastructure information for users who do not need it.

## High Availability and Reliability

Flow Logs should be treated as an observability dependency rather than a runtime dependency.

If the logging destination becomes temporarily unavailable:

```text
Application Traffic
        |
        v
VPC Network
        |
        +--> Application continues operating
        |
        +--> Flow Log delivery may be affected
```

The application should not depend on Flow Logs for request processing.

However, production environments should design logging so that network telemetry remains available during incidents, including incidents involving:

- Application failure
- Network misconfiguration
- Security events
- Infrastructure failure

Centralized storage and durable retention are therefore important for forensic analysis.

## Monitoring and Alerting

Do not alert on every rejected flow.

Production alerting should focus on meaningful patterns.

Useful signals include:

- Sudden increase in rejected traffic.
- New external sources.
- Unexpected destination ports.
- Unexpected east-west communication.
- Traffic from sensitive subnets to unexpected destinations.
- Significant changes in traffic volume.
- Repeated connection attempts against administrative ports.

A useful model is:

```text
Raw Flow Logs
      |
      v
Aggregation
      |
      v
Baseline
      |
      v
Anomaly Detection
      |
      v
Security / Operational Alert
```

This avoids overwhelming engineers with low-value alerts.

## Production Architecture Example

Consider a production Django/FastAPI platform:

```mermaid
flowchart TB
    Internet["Internet"]
    ALB["Application Load Balancer"]

    subgraph VPC["Production VPC"]
        subgraph App["Private Application Subnets"]
            API["Django / FastAPI"]
            Celery["Celery Workers"]
        end

        subgraph Data["Private Data Subnets"]
            RDS["PostgreSQL"]
            Redis["Redis"]
        end

        NAT["NAT Gateway"]
        VPCE["VPC Endpoints"]
        FL["VPC Flow Logs"]
    end

    Logs["Central Log Storage"]

    Internet --> ALB
    ALB --> API
    API --> RDS
    API --> Redis
    Celery --> RDS
    API --> NAT
    Celery --> VPCE

    API --> FL
    Celery --> FL
    RDS --> FL
    Redis --> FL

    FL --> Logs
```

The Flow Logs complement application observability.

A complete request investigation might therefore use:

```text
ALB Access Logs
       +
Application Logs
       +
Database Metrics
       +
VPC Flow Logs
       +
CloudTrail
```

No single telemetry source provides the entire picture.

## Common Mistakes

### Treating Flow Logs as Packet Capture

Flow Logs provide network metadata, not complete packet contents.

**Avoid it:** use Flow Logs for traffic-level analysis and dedicated packet-capture tooling when packet-level debugging is actually required.

### Assuming ACCEPT Means Application Success

An accepted network flow does not mean the application processed the request successfully.

**Avoid it:** correlate network telemetry with application and service logs.

### Enabling Logs Without a Retention Strategy

Large environments can accumulate significant log volumes.

**Avoid it:** define retention, archival, query, and deletion requirements before production rollout.

### Logging Without Analysis

Collecting Flow Logs but never querying or alerting on them creates telemetry without operational value.

**Avoid it:** establish useful dashboards, queries, baselines, and incident procedures.

### Ignoring IPv6

Security analysis that considers only IPv4 can miss IPv6 traffic.

**Avoid it:** include both address families when IPv6 is enabled.

### Using Broad Access to Flow Logs

Network telemetry can reveal sensitive infrastructure information.

**Avoid it:** protect log destinations using least-privilege IAM and encryption.

### Treating REJECT as Automatically Malicious

Rejected traffic can simply indicate a misconfigured application.

**Avoid it:** correlate the source, destination, timing, expected architecture, and recent infrastructure changes.

## Interview Traps

### Are Flow Logs a Firewall?

No.

Flow Logs provide visibility into network traffic. They do not replace Security Groups, NACLs, routing controls, or application authorization.

### Do Flow Logs Capture Packet Contents?

No.

They record flow metadata rather than complete packet payloads.

### Does ACCEPT Mean the Application Accepted the Request?

No.

It indicates network-level acceptance for the recorded flow. Application-level authentication, authorization, validation, and processing happen separately.

### Can Flow Logs Help Troubleshoot Security Group Problems?

Yes.

They can provide evidence that traffic was accepted or rejected and help identify source, destination, protocol, and port.

### Do Flow Logs Replace Application Logs?

No.

They operate at different layers.

```text
Flow Logs
    |
    v
Network Behavior

Application Logs
    |
    v
Application Behavior
```

Both are required for complete production troubleshooting.

## Operational Best Practices

- Enable Flow Logs for production environments where network visibility is required.
- Select a scope that provides sufficient coverage without unnecessary duplication.
- Use a centralized logging architecture for multi-account environments.
- Define retention and archival requirements.
- Protect log destinations with least-privilege IAM.
- Encrypt stored telemetry.
- Monitor logging configuration changes.
- Build reusable queries for common incidents.
- Establish expected network communication patterns.
- Investigate meaningful anomalies rather than every rejected packet.
- Correlate Flow Logs with application, load balancer, DNS, and CloudTrail telemetry.
- Include IPv4 and IPv6 traffic in security analysis where applicable.
- Use Infrastructure as Code to manage Flow Log configuration consistently.
- Test troubleshooting procedures before production incidents occur.

## CLI Reference

The AWS CLI can be used to inspect and manage Flow Log resources.

List Flow Logs:

```bash
aws ec2 describe-flow-logs
```

Describe a specific VPC:

```bash
aws ec2 describe-vpcs \
  --vpc-ids vpc-0123456789abcdef0
```

Describe network interfaces:

```bash
aws ec2 describe-network-interfaces \
  --filters Name=vpc-id,Values=vpc-0123456789abcdef0
```

These commands are useful when correlating Flow Log records with the underlying VPC resources.

## Infrastructure as Code Considerations

Flow Log configuration should generally be managed through Infrastructure as Code in production.

A Terraform-style design might conceptually include:

```hcl
resource "aws_flow_log" "production" {
  vpc_id = aws_vpc.production.id

  traffic_type = "ALL"

  log_destination_type = "s3"
  log_destination      = aws_s3_bucket.vpc_flow_logs.arn
}
```

The exact configuration should be adapted to the organization's:

- AWS provider version
- Logging destination
- IAM model
- Encryption requirements
- Retention policy
- Multi-account architecture

Infrastructure as Code provides:

- Repeatability
- Reviewability
- Change history
- Consistent environments
- Easier disaster recovery

## Validation Checklist

Before considering Flow Logs production-ready, verify:

- [ ] The intended VPCs, subnets, or interfaces are covered.
- [ ] The traffic type being captured is intentional.
- [ ] The destination is correctly configured.
- [ ] Log delivery works.
- [ ] IAM permissions follow least privilege.
- [ ] Log storage is encrypted where required.
- [ ] Retention is explicitly defined.
- [ ] Long-term archival is defined where required.
- [ ] CloudWatch or S3 analysis workflows exist.
- [ ] Common troubleshooting queries are documented.
- [ ] Security teams can access required telemetry.
- [ ] Application teams have only the access they need.
- [ ] Flow Logs are correlated with other security telemetry.
- [ ] Logging configuration is managed through Infrastructure as Code.
- [ ] Alerts focus on meaningful network anomalies.

## Key Takeaways

- **VPC Flow Logs provide network telemetry, not packet capture**; they expose flow metadata useful for troubleshooting, security analysis, and traffic baselining.
- **ACCEPT and REJECT describe network-level behavior**, not application success or failure.
- **Flow Logs are most effective when correlated** with Security Groups, NACLs, route tables, application logs, load balancer logs, and CloudTrail.
- **Production Flow Logs require operational design** covering scope, destination, retention, cost, IAM, encryption, centralized analysis, and alerting.
- **Network visibility is part of production security**: logs should be managed as durable, protected telemetry and incorporated into incident-response workflows.