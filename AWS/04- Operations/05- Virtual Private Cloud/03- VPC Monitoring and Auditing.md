# 03- VPC Monitoring and Auditing

## Overview

Amazon VPC monitoring and auditing provide the operational visibility required to understand network health, detect security-relevant activity, troubleshoot connectivity failures, and maintain an auditable record of infrastructure changes.

A production VPC should not be treated as a static network configuration. Routes, security groups, network ACLs, endpoints, NAT gateways, load balancers, compute workloads, and IAM-controlled infrastructure changes continuously affect the network's behavior.

A useful operational model is:

```text
                    AWS VPC
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
   CloudWatch      VPC Flow Logs   CloudTrail
        |              |              |
        v              v              v
 Metrics/Logs       Traffic       API Activity
        |           Metadata           |
        +--------------+--------------+
                       |
                       v
              Security / Operations
                       |
          +------------+------------+
          |                         |
          v                         v
     Troubleshooting          Audit / Detection
```

The key distinction is:

| Capability | Primary question |
|---|---|
| CloudWatch Metrics | Is the service or network component behaving abnormally? |
| CloudWatch Logs | What operational events or application/network logs occurred? |
| VPC Flow Logs | Who communicated with whom, over which protocol/port, and was the flow accepted or rejected? |
| CloudTrail | Who changed an AWS resource or called an AWS API? |
| AWS Config | What is the current or historical configuration state? |
| Athena | How can large amounts of S3-based Flow Log data be analyzed with SQL? |
| GuardDuty / Security Hub | Is AWS detecting suspicious activity or security findings? |

Senior-level VPC operations requires correlating these signals rather than relying on a single telemetry source.

## Monitoring vs Auditing

Monitoring and auditing solve different problems.

### Monitoring

Monitoring focuses on the current and recent health of the environment.

Typical questions include:

- Is a NAT Gateway experiencing abnormal traffic?
- Are rejected connections increasing?
- Is a load balancer receiving traffic?
- Is a network path failing?
- Is a workload generating unexpected traffic?
- Are network-related errors increasing?

### Auditing

Auditing focuses on accountability and configuration history.

Typical questions include:

- Who changed a Security Group?
- Who modified a route table?
- Who deleted a VPC endpoint?
- When was a Network ACL changed?
- Which IAM principal created a NAT Gateway?
- What configuration existed before an incident?

The distinction is important:

```text
Monitoring
    |
    +--> What is happening?

Auditing
    |
    +--> What changed?
    |
    +--> Who changed it?
    |
    +--> When did it change?
```

## Core VPC Observability Architecture

A production AWS environment should generally combine multiple telemetry sources.

```mermaid
flowchart TB
    subgraph VPC["Amazon VPC"]
        EC2["EC2 / ECS / EKS"]
        ALB["Load Balancers"]
        NAT["NAT Gateway"]
        VPCE["VPC Endpoints"]
        SG["Security Groups"]
        NACL["Network ACLs"]
        RT["Route Tables"]
    end

    CW["Amazon CloudWatch"]
    FLOW["VPC Flow Logs"]
    CT["AWS CloudTrail"]
    CONFIG["AWS Config"]
    S3["Amazon S3"]
    ATHENA["Amazon Athena"]
    GD["Amazon GuardDuty"]
    SH["AWS Security Hub"]

    EC2 --> CW
    ALB --> CW
    NAT --> CW
    VPCE --> CW

    VPC --> FLOW
    FLOW --> S3
    S3 --> ATHENA

    VPC --> CT
    CT --> S3

    VPC --> CONFIG

    FLOW --> GD
    CT --> GD
    GD --> SH
    CONFIG --> SH

    CW --> SH
```

The exact architecture depends on organizational requirements, but the important principle is to collect enough telemetry to reconstruct both **network behavior** and **configuration changes**.

## CloudWatch for VPC Monitoring

Amazon CloudWatch is the primary AWS-native service for metrics, alarms, dashboards, and logs.

VPC components expose different metrics depending on the resource.

Commonly monitored components include:

- NAT Gateways.
- Network Load Balancers.
- Application Load Balancers.
- Transit Gateway.
- VPN connections.
- Client VPN.
- VPC endpoints.
- Network Firewall.
- EC2 network interfaces.
- Application workloads.

The exact metrics available depend on the service.

## NAT Gateway Monitoring

NAT Gateway monitoring is especially important for private-subnet architectures.

A common architecture is:

```text
Private Subnet
     |
     v
Route Table
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

If a NAT Gateway becomes a bottleneck or a workload unexpectedly generates large outbound traffic, the application may experience performance or cost problems.

Useful NAT Gateway metrics include:

- `BytesInFromSource`
- `BytesOutToDestination`
- `BytesInFromDestination`
- `BytesOutToSource`
- `PacketsInFromSource`
- `PacketsOutToDestination`
- `ActiveConnectionCount`
- `ConnectionAttemptCount`
- `ConnectionEstablishedCount`
- `ErrorPortAllocation`
- `IdleTimeoutCount`

The exact interpretation should be based on the AWS service metric semantics.

## NAT Gateway Operational Signals

A sudden increase in:

```text
BytesOutToDestination
```

may indicate:

- A new deployment.
- Large package downloads.
- Data synchronization.
- Backup traffic.
- Unexpected external communication.
- Compromised workloads.

A spike in:

```text
ErrorPortAllocation
```

requires particular attention because it can indicate that the NAT Gateway is unable to allocate source ports for new connections.

Potential causes include:

- Excessive concurrent connections.
- Poor connection reuse.
- Large-scale outbound workloads.
- Many workloads sharing a NAT Gateway.

Do not automatically solve this by adding NAT Gateways. First identify the traffic pattern.

## NAT Gateway Cost Monitoring

NAT Gateway traffic can become a significant operational cost.

A common architecture:

```text
100 Private Instances
        |
        v
Single NAT Gateway
        |
        v
Internet
```

may be operationally simple but can create:

- High data-processing costs.
- A concentrated failure domain.
- A high-volume outbound traffic path.

For high-volume AWS service traffic, evaluate whether VPC endpoints can avoid unnecessary NAT traversal.

For example:

```text
Private Workload
      |
      +----> S3 VPC Endpoint
      |
      +----> ECR VPC Endpoint
      |
      +----> CloudWatch Endpoint
      |
      +----> NAT Gateway ----> Public Internet
```

The correct architecture depends on service support, traffic patterns, cost, and security requirements.

## VPC Flow Logs

VPC Flow Logs capture metadata about network traffic.

They are useful for:

- Connectivity troubleshooting.
- Security investigation.
- Rejected-traffic analysis.
- Traffic baselining.
- Network architecture validation.
- Incident response.

Flow Logs can be delivered to destinations such as:

- Amazon CloudWatch Logs.
- Amazon S3.
- Amazon Data Firehose.

A typical analysis path is:

```text
VPC
 |
 v
Flow Logs
 |
 +--> CloudWatch Logs --> Interactive operational analysis
 |
 +--> S3 --> Athena --> Historical analysis
```

Flow Logs do not provide packet payloads. They should therefore be treated as network metadata rather than packet capture.

## Flow Log Monitoring Strategy

A useful operational model is to classify traffic into:

```text
ACCEPT
  |
  +--> Expected traffic
  +--> Unexpected traffic

REJECT
  |
  +--> Misconfiguration
  +--> Intentional blocking
  +--> Security investigation
```

Do not treat every `REJECT` record as an incident.

For example, a database Security Group intentionally blocking public traffic will naturally produce rejected connection attempts.

The useful signal comes from **unexpected deviations from the expected traffic model**.

## Rejected Traffic Baselines

A production team should establish normal rejected-traffic levels.

For example:

```text
Normal:
REJECT = 10,000 flows/hour

Observed:
REJECT = 1,200,000 flows/hour
```

The absolute number is not enough to determine whether the system is compromised.

Investigate:

- Source addresses.
- Destination addresses.
- Destination ports.
- Protocol.
- VPC.
- Subnet.
- Interface.
- Time window.
- Recent infrastructure changes.

## CloudTrail for VPC Auditing

AWS CloudTrail records AWS API activity.

For VPC auditing, CloudTrail can answer questions such as:

```text
Who changed this Security Group?
Who deleted this route?
Who created this VPC endpoint?
Who modified the Network ACL?
Who changed the subnet configuration?
```

This is fundamentally different from Flow Logs.

```text
Flow Logs
    |
    +--> Network behavior

CloudTrail
    |
    +--> AWS API activity
```

For incident investigation, both may be required.

## Example: Security Group Investigation

Suppose an application suddenly cannot reach PostgreSQL.

Flow Logs show:

```text
srcaddr -> database
dstport = 5432
action = REJECT
```

That tells you the network flow is being rejected.

CloudTrail can then help determine whether the Security Group changed.

The investigation becomes:

```text
Application Timeout
       |
       v
Flow Logs
       |
       v
REJECT :5432
       |
       v
Security Group / NACL Investigation
       |
       v
CloudTrail
       |
       v
Who changed the configuration?
```

This is much stronger than changing rules until the application starts working.

## CloudTrail Events Worth Auditing

For VPC operations, pay attention to API activity involving:

- VPC creation/deletion.
- Subnet changes.
- Route table changes.
- Internet Gateway operations.
- NAT Gateway operations.
- Security Group changes.
- Network ACL changes.
- VPC endpoint changes.
- Elastic IP allocation/release.
- Transit Gateway changes.
- VPN configuration.
- Network Firewall configuration.

The exact API event names depend on the AWS resource and operation.

## CloudTrail Event Investigation

A CloudTrail event contains information such as:

- Event time.
- AWS Region.
- Event source.
- Event name.
- User identity.
- Source IP.
- Request parameters.
- Response elements.
- AWS account.
- Session information.

A conceptual event looks like:

```json
{
  "eventSource": "ec2.amazonaws.com",
  "eventName": "AuthorizeSecurityGroupIngress",
  "awsRegion": "ap-south-1",
  "sourceIPAddress": "203.0.113.10"
}
```

The actual CloudTrail event contains substantially more metadata.

When investigating an incident, the identity information is often as important as the configuration change itself.

## AWS Config for Configuration Auditing

AWS Config provides a configuration-history perspective.

It can help determine:

```text
What is the current configuration?
What did the configuration look like previously?
Did a resource become non-compliant?
```

This complements CloudTrail:

| Tool | Main strength |
|---|---|
| CloudTrail | API activity and actor |
| AWS Config | Resource configuration state and history |
| Flow Logs | Network traffic behavior |
| CloudWatch | Metrics and operational telemetry |

A mature investigation frequently correlates all four.

## CloudTrail vs Config

Consider a Security Group change.

CloudTrail can tell you:

```text
User X
performed API operation Y
at time Z
```

AWS Config can help establish:

```text
Security Group
before -> configuration A
after  -> configuration B
```

The distinction matters because an audit investigation often needs both **who changed it** and **what changed**.

## VPC Monitoring Dashboard

A production dashboard should focus on actionable signals rather than displaying every available metric.

A useful VPC dashboard can contain:

| Area | Example signal |
|---|---|
| NAT | Bytes processed |
| NAT | Connection attempts |
| NAT | Port allocation errors |
| Load Balancer | Request count |
| Load Balancer | HTTP errors |
| VPN | Tunnel state |
| Transit Gateway | Bytes / packets |
| Flow Logs | Rejected traffic |
| Infrastructure | Resource count |
| Security | Security findings |
| Changes | Recent network API activity |

The goal is not to create a dashboard containing hundreds of graphs.

The goal is to answer:

> Is the network healthy, and if not, where should the investigation begin?

## Monitoring by Layer

A useful architecture is to monitor each networking layer separately.

```text
Application
    |
    v
Load Balancer
    |
    v
Network Interface
    |
    v
Security Group
    |
    v
Network ACL
    |
    v
Route Table
    |
    v
NAT / IGW / Endpoint
    |
    v
Destination
```

The observability strategy should map to the same layers.

| Layer | Primary telemetry |
|---|---|
| Application | Application logs and metrics |
| Load Balancer | CloudWatch metrics + access logs |
| ENI / workload | CloudWatch + Flow Logs |
| Security Group | CloudTrail + Flow Logs |
| Network ACL | CloudTrail + Flow Logs |
| Route tables | CloudTrail + Config |
| NAT Gateway | CloudWatch + Flow Logs |
| VPC Endpoint | CloudWatch where supported + CloudTrail + Flow Logs |
| Internet path | Flow Logs + service metrics |
| AWS API activity | CloudTrail |
| Configuration state | AWS Config |

## Monitoring a REST API in a Private Subnet

Consider a FastAPI service deployed on private subnets:

```mermaid
flowchart LR
    Client["Client"]
    ALB["Application Load Balancer"]
    API["FastAPI / Django"]
    DB["PostgreSQL"]
    Redis["Redis"]
    NAT["NAT Gateway"]
    Internet["External APIs"]

    Client --> ALB
    ALB --> API
    API --> DB
    API --> Redis
    API --> NAT
    NAT --> Internet
```

Operational monitoring should answer:

- Is the ALB receiving requests?
- Are requests reaching the application?
- Are application instances healthy?
- Is the API reaching PostgreSQL?
- Is Redis reachable?
- Is outbound traffic through NAT behaving normally?
- Are connections being rejected?
- Did a network configuration change recently?

The VPC telemetry becomes part of the complete backend observability model.

## Monitoring Microservices

For microservices:

```text
orders
  |
  +--> payments
  |
  +--> inventory
  |
  +--> Kafka
  |
  +--> PostgreSQL
```

Flow Logs can validate actual network communication.

Application telemetry can explain why the service made the request.

CloudTrail can explain infrastructure changes.

The combined model is:

```text
Application Metrics
       +
Application Logs
       +
Distributed Traces
       +
VPC Flow Logs
       +
CloudTrail
       +
AWS Config
       |
       v
Complete Incident Context
```

Network monitoring should therefore complement application observability rather than replace it.

## Kubernetes Considerations

In Kubernetes environments running on Amazon EKS, network monitoring becomes more complex because AWS network interfaces and Kubernetes abstractions coexist.

A useful investigation may need to correlate:

```text
Pod
 |
 v
Node
 |
 v
ENI
 |
 v
Subnet
 |
 v
VPC
```

Depending on the networking configuration, a Pod may use VPC-native networking and receive an address associated with an AWS network interface.

For an unexpected connection, the investigation should therefore correlate:

- Pod identity.
- Namespace.
- Node.
- ENI.
- Private IP.
- Security Group.
- Subnet.
- VPC Flow Log record.

This is why IP-only monitoring becomes insufficient at scale.

## Security Monitoring

VPC monitoring should be integrated with security detection.

Potential security signals include:

- Unexpected outbound connections.
- Repeated rejected connections.
- Unusual administrative-port traffic.
- Unexpected cross-account communication.
- Unexpected Internet destinations.
- Sudden traffic-volume increases.
- Unexpected changes to Security Groups.
- Unexpected changes to route tables.
- Disabled or modified logging.
- New public network exposure.

AWS security services such as GuardDuty and Security Hub can complement native VPC telemetry.

The principle is:

```text
Telemetry
   |
   v
Detection
   |
   v
Finding
   |
   v
Investigation
   |
   v
Remediation
```

## Public Exposure Auditing

A common production risk is accidental public exposure.

Potential exposure paths include:

```text
Internet
   |
   v
Internet Gateway
   |
   v
Public Subnet
   |
   v
Load Balancer / EC2
```

or:

```text
Internet
   |
   v
Publicly reachable workload
   |
   v
Overly permissive Security Group
```

Auditing should evaluate:

- Public IP addresses.
- Internet Gateway routes.
- Security Group ingress.
- Network ACL rules.
- Load balancer exposure.
- Publicly accessible endpoints.
- Intended vs unintended exposure.

Do not assume that a private subnet alone guarantees application isolation. The complete route and resource configuration determines reachability.

## Security Group Change Monitoring

A Security Group change should be treated as an auditable infrastructure event.

Particularly sensitive changes include:

```text
0.0.0.0/0 -> TCP 22
0.0.0.0/0 -> TCP 3389
0.0.0.0/0 -> Database Port
0.0.0.0/0 -> Internal Service Port
```

Not every broad rule is automatically wrong. Public HTTP/HTTPS access may be intentional for a load balancer.

The correct question is:

> Does the rule match the intended architecture and security policy?

## Network ACL Auditing

Network ACLs are subnet-level stateless controls.

Audit changes to:

- Inbound rules.
- Outbound rules.
- Rule numbers.
- Allow/deny actions.
- Associated subnets.

Because Network ACLs are stateless, both inbound and outbound behavior must be considered.

A change that allows inbound traffic but blocks the corresponding return path can cause confusing connectivity failures.

## Route Table Auditing

Route changes can be more dangerous than they initially appear.

For example:

```text
10.0.0.0/16 -> local
0.0.0.0/0  -> NAT Gateway
```

Changing:

```text
0.0.0.0/0 -> NAT Gateway
```

to:

```text
0.0.0.0/0 -> Internet Gateway
```

can materially change the exposure model.

Route-table changes should therefore be:

- Audited.
- Reviewed.
- Managed through Infrastructure as Code.
- Correlated with deployment activity.

## Infrastructure as Code

Production VPC configuration should preferably be managed through Infrastructure as Code.

Common approaches include:

- AWS CloudFormation.
- AWS CDK.
- Terraform.

A mature workflow looks like:

```text
Git
 |
 v
Pull Request
 |
 v
CI Validation
 |
 v
Plan / Diff
 |
 v
Approval
 |
 v
Deployment
 |
 v
CloudTrail
 |
 v
AWS Config
```

This creates an important distinction between:

```text
Expected change
```

and:

```text
Unexpected console/API change
```

If the infrastructure state changes without a corresponding source-control change, that should be investigated.

## Detecting Configuration Drift

Drift occurs when the actual AWS environment diverges from the expected configuration.

Examples:

```text
Git / IaC:
Security Group allows 443

AWS:
Security Group allows 443 + 22 from 0.0.0.0/0
```

or:

```text
IaC:
Private subnet route -> NAT Gateway

AWS:
Private subnet route -> unexpected target
```

Configuration auditing helps identify these differences.

AWS Config can contribute configuration-state visibility, while IaC tooling can provide the desired-state definition.

## Audit Logging Architecture

For larger organizations, centralized audit storage is usually preferable.

```mermaid
flowchart TB
    Accounts["AWS Accounts"]
    CT["CloudTrail"]
    FLOW["VPC Flow Logs"]
    CONFIG["AWS Config"]

    Accounts --> CT
    Accounts --> FLOW
    Accounts --> CONFIG

    CT --> AuditS3["Central Audit S3"]
    FLOW --> FlowS3["Central Flow Log S3"]
    CONFIG --> ConfigStore["Configuration History"]

    FlowS3 --> Athena["Athena"]
    AuditS3 --> Athena

    Athena --> Security["Security Analysis"]
    Athena --> Operations["Operations Analysis"]
```

The centralized model makes cross-account investigations easier and reduces the risk of relying on logs stored only inside the affected account.

## Log Retention

Retention should be based on operational and compliance requirements.

A practical model may separate:

```text
Hot / Recent
    |
    +--> Fast operational investigation

Warm
    |
    +--> Historical troubleshooting

Cold / Archive
    |
    +--> Long-term audit requirements
```

Do not retain every log indefinitely without evaluating:

- Cost.
- Regulatory requirements.
- Security requirements.
- Query requirements.
- Data sensitivity.
- Incident-response needs.

S3 lifecycle policies can be used to transition or expire objects according to the organization's retention policy.

## Protecting Audit Logs

Audit logs are security-sensitive because an attacker who compromises an environment may attempt to destroy evidence.

Recommended controls include:

- Separate logging accounts where appropriate.
- Restrictive bucket policies.
- Encryption.
- Versioning where appropriate.
- Object Lock when regulatory requirements justify it.
- Limited write/delete permissions.
- CloudTrail monitoring.
- Access logging or equivalent audit controls.
- Explicit retention policies.

A useful architectural principle is:

> The system generating the audit data should not have unrestricted authority to delete its own audit history.

## Alerting Strategy

Not every telemetry event should generate an alert.

A useful hierarchy is:

```text
Metric
  |
  v
Threshold
  |
  v
Alert
  |
  v
Investigation
```

For example:

```text
NAT port allocation errors
        |
        v
Sustained increase
        |
        v
Alert
        |
        v
Inspect connection patterns
```

Compare this with:

```text
One rejected connection
```

which normally should not page an engineer.

Alerting should focus on:

- Sustained anomalies.
- Service-impacting conditions.
- Security-relevant events.
- Policy violations.
- High-confidence infrastructure changes.

## High Availability Considerations

Monitoring should account for failure domains.

For example, a production application may use:

```text
AZ-A
  |
  +--> Private Subnet
  +--> NAT Gateway

AZ-B
  |
  +--> Private Subnet
  +--> NAT Gateway
```

Monitoring should verify that each Availability Zone has the expected network path.

A single shared NAT Gateway can simplify architecture but creates a concentrated dependency.

When designing for high availability, monitor:

- Per-AZ traffic.
- Per-AZ NAT behavior.
- Load balancer target health.
- Route-table consistency.
- Endpoint availability.
- Cross-AZ traffic.

## Disaster Recovery

Network monitoring and auditing are also important during disaster recovery.

A DR environment should preserve enough telemetry to answer:

- What network resources existed?
- What routes were configured?
- Which Security Groups were applied?
- Which traffic patterns existed?
- Which API changes occurred?
- What failed before the recovery event?

Audit data should therefore not exist only in the primary workload environment.

Centralized logging and durable storage improve recovery investigations.

## Common Mistakes

### Monitoring Only Application Metrics

An API can report:

```text
Database connection timeout
```

without explaining whether the cause is:

- Security Group.
- Network ACL.
- Route table.
- DNS.
- NAT.
- Database listener.
- Application configuration.

**Avoid it:** include network telemetry in the incident workflow.

### Treating Flow Logs as Packet Capture

Flow Logs contain network metadata, not packet payloads.

**Avoid it:** use appropriate packet/network diagnostics when packet-level inspection is required.

### Relying Only on CloudTrail

CloudTrail tells you about AWS API activity, not whether an application successfully communicated over the network.

**Avoid it:** correlate CloudTrail with Flow Logs and service telemetry.

### Relying Only on AWS Config

AWS Config provides configuration-state visibility but does not replace traffic telemetry or API audit history.

**Avoid it:** use Config, CloudTrail, and Flow Logs together.

### Creating Too Many Alerts

Alerting on every rejected connection produces noise.

**Avoid it:** alert on meaningful anomalies and sustained conditions.

### Ignoring Cost Metrics

A network can be healthy while generating excessive NAT or cross-AZ costs.

**Avoid it:** include network cost drivers in operational dashboards.

### Monitoring Aggregate Traffic Only

A healthy aggregate traffic graph can hide a single workload generating abnormal traffic.

**Avoid it:** monitor by VPC, subnet, interface, workload, and application where possible.

### Allowing Console Changes Without Governance

Manual changes can create configuration drift.

**Avoid it:** prefer IaC and audit exceptions through CloudTrail.

### Storing Audit Data in the Same Failure Domain

If an account is compromised, local audit data may be at risk.

**Avoid it:** consider centralized and access-controlled audit storage.

## Production Monitoring Checklist

### Network Health

- [ ] NAT Gateway metrics are monitored.
- [ ] Load balancer health and traffic metrics are monitored.
- [ ] VPN or Transit Gateway health is monitored where applicable.
- [ ] VPC Flow Logs are enabled for required resources.
- [ ] Rejected traffic has an operational baseline.
- [ ] Important network paths have documented expectations.

### Security

- [ ] Security Group changes are audited.
- [ ] Network ACL changes are audited.
- [ ] Route-table changes are audited.
- [ ] Unexpected public exposure is detectable.
- [ ] High-risk ingress changes are monitored.
- [ ] Security findings are integrated into the security workflow.

### Auditing

- [ ] CloudTrail is enabled for required accounts and Regions.
- [ ] CloudTrail logs are protected.
- [ ] AWS Config is enabled where configuration history is required.
- [ ] Configuration drift can be detected.
- [ ] Infrastructure changes are associated with source control.

### Operations

- [ ] Dashboards focus on actionable signals.
- [ ] Alerts have clear ownership.
- [ ] Queryable historical Flow Logs are available.
- [ ] Athena queries use efficient partitioning.
- [ ] Logs have defined retention.
- [ ] Network telemetry can be correlated with application telemetry.

### Reliability

- [ ] Network dependencies are monitored per Availability Zone.
- [ ] DR environments have appropriate audit visibility.
- [ ] Centralized logs survive workload failures.
- [ ] Network changes are tested before production deployment.

## Practical Incident Workflow

When a backend service reports a network failure, use a structured workflow:

1. Identify the affected workload and destination.
2. Confirm whether the failure is isolated or widespread.
3. Check application and load balancer telemetry.
4. Inspect VPC Flow Logs for the relevant source, destination, port, and protocol.
5. Inspect Security Groups and Network ACLs.
6. Inspect route tables and network endpoints.
7. Check CloudTrail for recent network configuration changes.
8. Check AWS Config for configuration-state changes or drift.
9. Correlate the incident with deployments or infrastructure changes.
10. Apply the smallest safe remediation.
11. Verify traffic recovery.
12. Preserve relevant audit evidence.

This approach avoids the common anti-pattern of immediately modifying Security Groups until the symptom disappears.

## Example: Diagnosing a PostgreSQL Timeout

Suppose a Django or FastAPI application cannot connect to PostgreSQL.

```text
Application
    |
    | TCP :5432
    v
PostgreSQL
```

Start with Flow Logs:

```text
Source IP
Destination IP
Destination Port = 5432
Protocol = TCP
Action = ACCEPT / REJECT
```

Then inspect:

```text
Security Group
       |
       v
Network ACL
       |
       v
Route Table
       |
       v
Database
```

Finally check CloudTrail:

```text
Was any network configuration changed immediately before the incident?
```

If Flow Logs show `REJECT` and CloudTrail shows a Security Group change immediately before the failure, the investigation has a strong evidence chain.

## Example: Unexpected Outbound Traffic

Suppose a worker service normally communicates with:

```text
PostgreSQL
Redis
Kafka
S3
```

but Flow Logs show a sudden increase in external traffic.

Investigation:

```mermaid
sequenceDiagram
    participant Worker
    participant ENI
    participant Flow as VPC Flow Logs
    participant Athena
    participant CT as CloudTrail
    participant Ops as Operations

    Worker->>ENI: Outbound connection
    ENI->>Flow: Flow metadata
    Flow->>Athena: Store/query records
    Athena->>Ops: Unexpected destination detected
    Ops->>CT: Check recent changes
    CT-->>Ops: Configuration/API history
    Ops->>Worker: Investigate workload
```

Possible explanations include:

- New application dependency.
- Package download.
- Data synchronization.
- Deployment behavior.
- Misconfiguration.
- Compromised workload.

The network evidence should be correlated with application and infrastructure evidence before remediation.

## Interview Traps

### What is the difference between Flow Logs and CloudTrail?

Flow Logs describe network traffic metadata.

CloudTrail describes AWS API activity.

```text
Flow Logs  -> Network behavior
CloudTrail -> AWS API activity
```

### What is the difference between CloudTrail and AWS Config?

CloudTrail answers:

```text
Who performed an API operation?
```

AWS Config helps answer:

```text
What was the resource configuration?
```

They complement each other.

### Can CloudWatch tell you who changed a Security Group?

CloudWatch itself is not the authoritative source for AWS API actor auditing.

CloudTrail is designed for that purpose.

### Do Flow Logs prove an application request succeeded?

No.

They provide network-flow information. Application success requires application/service-level telemetry.

### Should every rejected Flow Log record generate an alert?

No.

Rejected traffic can be completely normal. Alerting should focus on meaningful anomalies and policy violations.

### Why monitor NAT Gateway traffic?

Because NAT Gateways are critical outbound dependencies and can introduce both availability and cost considerations.

### Why is VPC monitoring not enough by itself?

Because network behavior must be correlated with application behavior, infrastructure state, API activity, and security findings.

## Key Takeaways

- **VPC monitoring and auditing require multiple telemetry sources**: CloudWatch, VPC Flow Logs, CloudTrail, AWS Config, and security services answer different operational questions.
- **Flow Logs explain network behavior, while CloudTrail and Config explain infrastructure changes and configuration state**; combining them creates a much stronger incident-investigation model.
- **Production monitoring should focus on actionable signals**, including rejected traffic, NAT behavior, network dependencies, public exposure, configuration drift, and meaningful anomalies rather than raw telemetry volume.
- **Network observability must integrate with backend observability**, correlating VPC behavior with Django/FastAPI services, databases, Redis, Kafka, load balancers, Kubernetes workloads, deployments, and application logs.
- **Protect and centralize audit data where appropriate**, enforce least privilege and retention policies, and prefer Infrastructure as Code so expected changes can be distinguished from unauthorized or accidental changes.