# 04- VPC Cost Optimization

## Overview

Amazon VPC cost optimization is primarily a network-architecture problem rather than a simple cost-cutting exercise. The largest savings usually come from reducing unnecessary data processing, cross-Availability Zone traffic, NAT Gateway usage, idle network resources, and inefficient traffic paths.

A production VPC should be designed around both **network requirements** and **traffic economics**.

A useful mental model is:

```text
Application Architecture
        |
        v
Traffic Patterns
        |
        v
Network Path
        |
        +------------------+
        |                  |
        v                  v
Availability Zone      AWS Service
        |                  |
        v                  v
Data Transfer        NAT / Endpoint /
                     Load Balancer
        |
        v
AWS Cost
```

The goal is not:

> Minimize every networking cost.

The goal is:

> Minimize unnecessary network cost while preserving security, availability, performance, and operational simplicity.

This distinction matters because an architecture that saves a small amount of data-transfer cost but introduces cross-AZ dependencies or removes high-availability protections can become more expensive operationally.

## Major VPC Cost Drivers

The most important VPC-related cost areas commonly include:

| Cost area | Typical cause | Optimization focus |
|---|---|---|
| NAT Gateway | Private workloads accessing external services | VPC endpoints, traffic architecture |
| Data transfer | Cross-AZ or Internet traffic | Keep high-volume traffic local |
| VPC endpoints | Endpoint hourly/data-processing charges | Use selectively based on traffic |
| Load balancers | Idle or underutilized load balancers | Consolidation and lifecycle management |
| Elastic IP addresses | Unused public IPv4 resources | Remove unused addresses |
| Transit Gateway | Inter-VPC traffic and attachments | Routing and topology optimization |
| VPN | Unused or oversized connectivity | Lifecycle and utilization |
| Network Firewall | Traffic processing | Inspect only required paths |
| CloudWatch / Flow Logs | Large network telemetry volumes | Retention and filtering strategy |
| Public IPv4 | Public IPv4 usage | Prefer private networking where appropriate |

Actual pricing varies by Region and AWS service configuration. Cost decisions should therefore be validated against the current AWS pricing model for the target Region.

## Cost Optimization Principles

A production-oriented approach can be summarized as:

```text
Measure
  |
  v
Understand Traffic
  |
  v
Identify Expensive Paths
  |
  v
Change Architecture
  |
  v
Measure Again
```

Avoid optimizing based solely on resource counts.

For example:

```text
10 NAT Gateways
```

does not automatically mean the architecture is inefficient.

If those gateways are intentionally deployed per Availability Zone to avoid cross-AZ dependencies, their additional cost may be justified.

Similarly:

```text
1 NAT Gateway
```

does not automatically mean the architecture is cost optimized.

If every private workload in multiple AZs routes through that single NAT Gateway, cross-AZ traffic and availability concerns may outweigh the apparent savings.

## NAT Gateway Cost Optimization

NAT Gateway is one of the most important VPC cost considerations for private-subnet architectures.

A common architecture is:

```text
Private EC2 / ECS / EKS
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

NAT Gateway pricing generally involves both an hourly component and data processing charges. The exact price depends on Region and current AWS pricing.

For high-volume workloads, the data-processing component can become significant.

## Why NAT Gateway Becomes Expensive

Consider:

```text
100 application instances
        |
        v
NAT Gateway
        |
        v
Internet
```

If the instances continuously download:

- Container images.
- Python packages.
- OS packages.
- Large files.
- External API responses.
- Application data.

the amount of traffic processed by the NAT Gateway can become substantial.

The correct response is not automatically to remove the NAT Gateway.

Instead, identify which traffic actually requires NAT.

## Separate AWS Service Traffic from Internet Traffic

A useful architecture is:

```text
                         Private Workload
                              |
                 +------------+------------+
                 |                         |
                 v                         v
          AWS Service Traffic        Internet Traffic
                 |                         |
                 v                         v
        VPC Endpoint Path          NAT Gateway
```

For supported AWS services, VPC endpoints can allow private communication without requiring traffic to traverse a NAT Gateway.

Common examples include services such as:

- Amazon S3.
- Amazon DynamoDB.
- Amazon ECR.
- Amazon CloudWatch services.
- AWS Systems Manager services.

The exact endpoint requirements depend on the service and Region.

## Gateway vs Interface Endpoints

AWS provides different VPC endpoint models.

| Endpoint type | Typical use | Cost consideration |
|---|---|---|
| Gateway endpoint | S3, DynamoDB | No hourly endpoint charge; evaluate route-based architecture |
| Interface endpoint | Many AWS services | Hourly per endpoint/AZ plus data processing |
| Gateway Load Balancer endpoint | Security/network appliances | Additional architecture and processing costs |

Do not create interface endpoints indiscriminately.

For low-volume traffic, an interface endpoint's fixed hourly cost can potentially exceed the NAT cost it replaces.

For high-volume traffic, private endpoint routing may provide significant benefits depending on the service and traffic pattern.

## NAT vs VPC Endpoint Decision

A simplified decision framework is:

| Traffic | Preferred starting point |
|---|---|
| S3 | Gateway endpoint where appropriate |
| DynamoDB | Gateway endpoint where appropriate |
| AWS service with interface endpoint support | Evaluate interface endpoint economics |
| Public Internet API | NAT Gateway or other appropriate egress architecture |
| Private service in another VPC | Private connectivity rather than Internet NAT |
| High-volume AWS service traffic | Analyze endpoint vs NAT processing cost |
| Low-volume occasional traffic | Compare fixed endpoint cost against NAT usage |

The correct decision depends on:

- Traffic volume.
- Number of Availability Zones.
- Number of VPCs.
- Endpoint hourly charges.
- Data-processing charges.
- Security requirements.
- Availability requirements.

## Avoid Cross-AZ NAT Traffic

Consider:

```text
AZ-A
Private Subnet
     |
     +----------------+
                      |
                      v
                  NAT Gateway
                  in AZ-A

AZ-B
Private Subnet
     |
     +--------------------> NAT Gateway in AZ-A
```

The AZ-B workload may incur cross-AZ data transfer when using the NAT Gateway in AZ-A.

A common production architecture is:

```text
AZ-A Private Subnet ---> NAT Gateway AZ-A ---> Internet

AZ-B Private Subnet ---> NAT Gateway AZ-B ---> Internet

AZ-C Private Subnet ---> NAT Gateway AZ-C ---> Internet
```

This can increase NAT Gateway hourly costs while reducing cross-AZ dependency and potentially reducing cross-AZ data-transfer costs.

The correct architecture should be selected using measured traffic volume and availability requirements.

## When a Single NAT Gateway Makes Sense

A single NAT Gateway can be reasonable when:

- The workload is low traffic.
- High availability requirements are limited.
- The environment is development or non-production.
- Cross-AZ traffic is negligible.
- Cost simplicity is more important than AZ-level independence.

It is generally less attractive for high-volume production workloads distributed across multiple AZs.

## When NAT Gateway per AZ Makes Sense

Multiple NAT Gateways are generally more appropriate when:

- Workloads are distributed across multiple AZs.
- Outbound traffic is significant.
- Cross-AZ traffic is expensive.
- High availability is required.
- Each AZ should maintain an independent egress path.

The trade-off is:

```text
More NAT Gateways
       |
       +--> Higher hourly resource cost
       |
       +--> Lower cross-AZ dependency
       |
       +--> Better AZ isolation
       |
       +--> Potentially lower data-transfer cost
```

Cost optimization must therefore consider the total architecture rather than one line item.

## Reduce Unnecessary Internet Egress

One of the simplest optimization strategies is to avoid sending traffic to the Internet when the destination does not require it.

For example:

```text
Application
    |
    +--> S3
    |
    +--> ECR
    |
    +--> CloudWatch
    |
    +--> Secrets Manager
    |
    +--> External API
```

Only the external API necessarily requires Internet-style egress.

The AWS service traffic should be evaluated for private connectivity.

## Data Transfer Cost

Data transfer can become significant in distributed architectures.

Important traffic categories include:

- Cross-AZ traffic.
- Internet egress.
- Inter-region traffic.
- Transit Gateway traffic.
- Load balancer-related processing.
- NAT Gateway processing.
- VPC endpoint processing.

A useful first question is:

> Where does the data physically travel before reaching its destination?

## Cross-AZ Traffic

Consider a backend architecture:

```text
AZ-A
API
 |
 +----> PostgreSQL in AZ-B
```

If the API continuously transfers large amounts of data to a database in another AZ, cross-AZ data-transfer costs can accumulate.

The same applies to:

```text
API -> Redis
API -> Kafka
API -> Elasticsearch/OpenSearch
API -> Internal Microservice
```

High-volume service-to-service communication should therefore be evaluated against AZ placement.

## AZ-Aware Architecture

For latency-sensitive and high-volume systems, consider:

```text
             Load Balancer
                  |
        +---------+---------+
        |                   |
        v                   v
      AZ-A                AZ-B
        |                   |
      API-A               API-B
        |                   |
      DB-A                DB-B
```

The exact database topology depends on the database technology and consistency requirements.

The principle is to understand where high-volume traffic crosses AZ boundaries.

## Cross-AZ Traffic vs High Availability

Do not optimize away multi-AZ architecture solely to reduce cost.

For production workloads:

```text
Single AZ
   |
   +--> Lower some network costs
   +--> Higher failure-domain risk

Multi-AZ
   |
   +--> Additional network costs
   +--> Better availability
```

A senior engineer evaluates:

```text
Cost
+
Availability
+
Latency
+
Failure isolation
+
Operational complexity
```

rather than optimizing a single metric.

## Load Balancer Cost Optimization

Load balancers introduce their own pricing and data-processing considerations.

Common optimization opportunities include:

- Removing unused load balancers.
- Consolidating compatible services.
- Avoiding unnecessary duplicate load balancers.
- Reviewing listener and routing architecture.
- Monitoring utilization.
- Avoiding unnecessary data-processing paths.

For example, multiple microservices do not necessarily require one load balancer each if they can safely share a load balancer using host- or path-based routing.

```text
                    ALB
                     |
        +------------+------------+
        |            |            |
        v            v            v
    /orders      /payments     /users
        |            |            |
        v            v            v
     Service A    Service B    Service C
```

The trade-off is increased blast radius and routing complexity.

Do not consolidate load balancers purely for cost if isolation requirements justify separation.

## Internal vs External Load Balancers

An internal load balancer can be appropriate for service-to-service communication inside a VPC.

An internet-facing load balancer is appropriate when external client access is required.

Avoid exposing an internal service to the public Internet simply because doing so appears operationally simpler.

Security and network architecture should remain primary constraints.

## Elastic IP and Public IPv4 Costs

Public IPv4 addresses are now a meaningful cost consideration in AWS.

Review:

- Unused Elastic IP addresses.
- Unnecessary public IPv4 assignments.
- Resources that do not require public Internet reachability.
- Public-facing architecture that can be replaced with private connectivity.

A common production pattern is:

```text
Internet
   |
   v
Public Load Balancer
   |
   v
Private Application
   |
   v
Private Database
```

rather than:

```text
Internet
   |
   v
Public EC2
   |
   v
Database
```

Private workloads can reduce exposure and may eliminate unnecessary public IPv4 requirements.

## VPC Endpoints and Cost

VPC endpoints are not automatically cheaper than NAT Gateways.

Consider:

```text
NAT Gateway
- Hourly cost
- Data processing

Interface Endpoint
- Endpoint hourly cost per AZ
- Data processing
```

For many endpoints across many AZs:

```text
10 services
x
3 Availability Zones
=
30 interface endpoints
```

The fixed endpoint cost can become significant.

Endpoint design should therefore be based on:

- Traffic volume.
- Service importance.
- Security requirements.
- Number of AZs.
- Number of services.
- NAT usage.
- Operational requirements.

## Endpoint Consolidation

Where practical, avoid creating unnecessary endpoint resources.

However, do not route traffic through another AZ solely to reduce endpoint count if that introduces substantial cross-AZ traffic or creates an availability dependency.

The optimization target is:

```text
Total Cost
=
Endpoint Cost
+
Data Transfer
+
Data Processing
+
Operational Cost
```

not merely:

```text
Number of Endpoints
```

## Transit Gateway Cost

Transit Gateway can simplify large multi-VPC architectures.

Example:

```text
VPC-A
   |
   v
Transit Gateway
   |
   +---- VPC-B
   |
   +---- VPC-C
   |
   +---- VPC-D
```

This can reduce operational complexity compared with maintaining many direct network connections.

However, Transit Gateway traffic can incur processing charges.

For high-volume traffic:

```text
VPC-A
  |
  v
Transit Gateway
  |
  v
VPC-B
```

evaluate:

- Traffic volume.
- Number of participating VPCs.
- Whether direct connectivity is possible.
- Centralized inspection requirements.
- Routing simplicity.
- Data-processing charges.

Do not remove Transit Gateway merely because it has a cost. Its architectural value can be substantial.

## Inter-VPC Traffic

High-volume microservice architectures can generate significant internal traffic.

For example:

```text
orders-vpc
    |
    v
payments-vpc
    |
    v
inventory-vpc
```

If every request transfers substantial payloads, network processing and data-transfer costs may increase.

This is another reason to design service boundaries around actual communication patterns rather than organizational boundaries alone.

## Optimize Payload Size

Application architecture can directly affect network cost.

For REST APIs:

```text
Large JSON payload
        |
        v
More bytes transferred
        |
        v
Higher network cost
```

Potential optimizations include:

- Pagination.
- Compression where appropriate.
- Avoiding unnecessary fields.
- Efficient serialization.
- Caching.
- Conditional requests.
- Binary protocols where justified.

For internal high-throughput services, gRPC can reduce some serialization overhead compared with verbose JSON APIs, although the overall cost impact depends on workload and architecture.

Do not adopt a protocol solely for cost savings without measuring the actual bottleneck.

## Caching and VPC Cost

Caching can reduce repeated network traffic.

For example:

```text
Application
    |
    +--> Redis
    |
    +--> PostgreSQL
```

A cache hit can avoid a database request and potentially reduce:

- Database traffic.
- Cross-AZ database traffic.
- Application-to-database bandwidth.
- Database compute requirements.

However, placing Redis in another AZ introduces its own network considerations.

The correct architecture depends on:

- Cache availability requirements.
- Replication topology.
- Traffic volume.
- Latency requirements.
- Failure model.

## Kafka and Network Cost

Kafka-heavy architectures can generate significant network traffic.

Example:

```text
Producer
   |
   v
Kafka
   |
   +--> Consumer A
   |
   +--> Consumer B
   |
   +--> Consumer C
```

Multiple consumers and replication can multiply traffic.

For production Kafka deployments, evaluate:

- Broker placement.
- Producer placement.
- Consumer placement.
- Replication factor.
- Cross-AZ traffic.
- Message size.
- Compression.
- Retention.
- Consumer group architecture.

Do not treat Kafka network traffic as application traffic alone. Replication and consumer patterns also matter.

## Kubernetes and Network Cost

EKS workloads can create substantial network traffic through:

- Pod-to-pod communication.
- Service communication.
- Load balancers.
- NAT Gateways.
- VPC endpoints.
- Cross-AZ traffic.

A typical path may be:

```text
Pod
 |
 v
Node / ENI
 |
 +--> Internal Service
 |
 +--> AWS Service
 |
 +--> NAT Gateway
 |
 +--> Internet
```

For cost optimization, identify the actual network path rather than assuming all Pod traffic has the same economics.

## Flow Logs and Monitoring Costs

VPC Flow Logs themselves can create additional observability costs.

Large environments may generate enormous numbers of records.

Cost drivers can include:

- Log volume.
- CloudWatch Logs ingestion.
- CloudWatch Logs storage.
- S3 storage.
- Athena query scanning.
- Data transformation.
- Long retention periods.

For high-volume environments, S3-based storage combined with Athena can be more appropriate for long-term analytical workloads.

## Athena Cost Optimization

Athena pricing is generally based on data scanned.

A query such as:

```sql
SELECT *
FROM vpc_flow_logs;
```

can scan substantially more data than necessary.

Prefer:

```sql
SELECT
    srcaddr,
    dstaddr,
    dstport,
    action
FROM vpc_flow_logs
WHERE account_id = '123456789012'
  AND region = 'ap-south-1'
  AND year = 2026
  AND month = 8
  AND day = 21
  AND action = 'REJECT';
```

The exact partition columns depend on the table design.

Good Athena optimization practices include:

- Partition data.
- Query only required columns.
- Filter partitions.
- Avoid `SELECT *`.
- Compress data.
- Use efficient formats such as Parquet where appropriate.
- Avoid repeatedly scanning historical data unnecessarily.

## Log Retention Optimization

Retention should reflect actual operational requirements.

A common model is:

```text
Recent Logs
    |
    +--> Fast access

Historical Logs
    |
    +--> Lower-cost storage

Long-Term Archive
    |
    +--> Compliance / investigation
```

Use S3 lifecycle policies where appropriate.

Avoid retaining high-volume Flow Logs in expensive hot storage indefinitely unless operational requirements justify it.

## Cost Allocation and Tagging

Network cost optimization requires ownership.

Use consistent tagging where supported:

```text
Environment
Application
Team
CostCenter
Owner
ManagedBy
```

For example:

```text
Environment = production
Application = payments
Team        = backend
CostCenter  = engineering
ManagedBy   = terraform
```

This allows network resources to be associated with business ownership.

## Cost Monitoring

Use AWS cost-management capabilities to track network spending.

Useful dimensions include:

- AWS account.
- Region.
- Service.
- Environment.
- Cost center.
- Application.
- Project.

A useful operational dashboard might track:

```text
NAT Gateway Cost
Data Transfer Cost
Transit Gateway Cost
Load Balancer Cost
Public IPv4 Cost
VPC Endpoint Cost
Flow Log / CloudWatch Cost
```

The exact cost categories exposed depend on AWS billing configuration.

## Cost Anomaly Detection

Unexpected network cost increases should trigger investigation.

Example:

```text
Normal NAT cost
       |
       v
$300 / month

Observed
       |
       v
$2,500 / month
```

Potential causes include:

- New workload.
- Large file transfer.
- Dependency installation.
- Backup job.
- Misconfigured routing.
- Infinite retry loop.
- Data exfiltration.
- New cross-AZ traffic.
- New endpoint architecture.

Cost anomalies can therefore be operational and security signals simultaneously.

## Architecture Example

Consider a production Django API:

```mermaid
flowchart TB
    Internet["Internet"]
    ALB["Public ALB"]

    subgraph AZ1["Availability Zone A"]
        API1["Django API"]
        NAT1["NAT Gateway"]
    end

    subgraph AZ2["Availability Zone B"]
        API2["Django API"]
        NAT2["NAT Gateway"]
    end

    DB["PostgreSQL"]
    REDIS["Redis"]
    S3["Amazon S3"]
    EXT["External APIs"]

    Internet --> ALB
    ALB --> API1
    ALB --> API2

    API1 --> DB
    API2 --> DB

    API1 --> REDIS
    API2 --> REDIS

    API1 --> S3
    API2 --> S3

    API1 --> NAT1
    API2 --> NAT2

    NAT1 --> EXT
    NAT2 --> EXT
```

Potential optimization opportunities include:

- S3 gateway endpoint instead of NAT for S3 traffic.
- AZ-local NAT Gateways.
- Efficient database placement.
- Redis topology aligned with availability requirements.
- Compression for large API payloads.
- Reduced external API calls through caching.
- Monitoring NAT data processing.
- Removing unused public IP resources.

The correct optimization depends on measured traffic.

## Cost Optimization Workflow

A reliable optimization process is:

```text
1. Establish baseline
        |
        v
2. Identify top network costs
        |
        v
3. Map costs to traffic
        |
        v
4. Identify unnecessary network paths
        |
        v
5. Model architectural alternatives
        |
        v
6. Validate security / availability impact
        |
        v
7. Implement through IaC
        |
        v
8. Measure post-change cost
```

Never skip the baseline.

Without a baseline, it is difficult to determine whether an optimization actually worked.

## Production Optimization Checklist

### NAT

- [ ] NAT Gateway traffic is monitored.
- [ ] High-volume AWS service traffic is evaluated for VPC endpoints.
- [ ] NAT Gateways are appropriately distributed across AZs for production requirements.
- [ ] Cross-AZ NAT traffic is understood.
- [ ] Port allocation errors are monitored.
- [ ] Unnecessary outbound Internet traffic is eliminated.

### Data Transfer

- [ ] High-volume cross-AZ traffic is identified.
- [ ] High-volume inter-region traffic is understood.
- [ ] Service placement considers traffic patterns.
- [ ] Large payloads are optimized.
- [ ] Compression is evaluated where appropriate.
- [ ] Kafka and Redis traffic patterns are understood.

### VPC Endpoints

- [ ] Gateway endpoints are used where appropriate.
- [ ] Interface endpoint costs are evaluated before deployment.
- [ ] Endpoint deployment is aligned with AZ requirements.
- [ ] Endpoint data processing is monitored.
- [ ] Unnecessary endpoints are removed.

### Infrastructure

- [ ] Unused load balancers are removed.
- [ ] Unused Elastic IP addresses are removed.
- [ ] Unnecessary public IPv4 assignments are reviewed.
- [ ] Idle VPN connections are reviewed.
- [ ] Transit Gateway usage is monitored.
- [ ] Network Firewall processing is reviewed.

### Observability

- [ ] Flow Log volume is monitored.
- [ ] Log retention is intentional.
- [ ] Athena queries are partition-aware.
- [ ] Large historical queries are optimized.
- [ ] Cost anomaly detection is configured where appropriate.

### Governance

- [ ] Network resources have ownership metadata.
- [ ] Infrastructure is managed through IaC.
- [ ] Cost changes are reviewed during architecture changes.
- [ ] Production and non-production environments are analyzed separately.

## Common Mistakes

### Optimizing for Resource Count

Reducing:

```text
3 NAT Gateways -> 1 NAT Gateway
```

may reduce hourly charges while increasing:

- Cross-AZ traffic.
- Failure-domain coupling.
- Latency.
- Operational risk.

**Avoid it:** optimize total cost and reliability together.

### Assuming VPC Endpoints Are Always Cheaper

Interface endpoints have their own pricing model.

**Avoid it:** compare endpoint hourly and data-processing costs against NAT costs for the actual workload.

### Ignoring Cross-AZ Traffic

A centralized architecture can appear simpler but generate substantial cross-AZ traffic.

**Avoid it:** map high-volume traffic flows before centralizing network dependencies.

### Ignoring Network Processing Costs

NAT Gateways, Transit Gateway, interface endpoints, and network security services can process traffic.

**Avoid it:** include data-processing charges in architecture estimates.

### Optimizing Production for Development Economics

A single NAT Gateway may be appropriate for development but unsuitable for production.

**Avoid it:** maintain environment-specific architecture and availability requirements.

### Removing Security Controls to Save Money

Security controls can introduce processing costs.

Removing them without analyzing risk is not cost optimization.

**Avoid it:** optimize placement and traffic paths while preserving required security controls.

### Ignoring Application-Level Traffic

Excessive API calls, oversized payloads, inefficient polling, and missing caching can create network costs.

**Avoid it:** treat application architecture as part of network cost optimization.

### Optimizing Without Measuring

An architectural change may reduce one AWS line item while increasing another.

**Avoid it:** compare total cost before and after the change.

## Interview Traps

### Is one NAT Gateway always cheaper?

Not necessarily.

One gateway has lower hourly resource cost, but workloads in other AZs may incur cross-AZ data-transfer costs and create a single-AZ dependency.

### Are VPC endpoints always cheaper than NAT?

No.

Gateway and interface endpoints have different pricing models. Interface endpoints can introduce fixed per-AZ costs and data-processing charges.

### What is usually the first thing to investigate when NAT costs are high?

Determine which workloads and destinations generate the traffic.

Then identify traffic that could use private AWS service connectivity, caching, better payload design, or another architectural path.

### Why can cross-AZ traffic be expensive?

Because traffic crossing Availability Zone boundaries can incur data-transfer charges and may also increase latency or introduce additional dependencies.

### Should production always have one NAT Gateway per AZ?

Not as an absolute rule.

It is a common high-availability pattern, but the right architecture depends on workload traffic, availability requirements, cost constraints, and cross-AZ economics.

### Can application code affect VPC costs?

Yes.

API payload size, request frequency, retries, caching, connection reuse, service topology, and message volume directly influence network traffic.

## Key Takeaways

- **VPC cost optimization is traffic-path optimization**, not simply reducing the number of networking resources.
- **NAT Gateway and cross-AZ traffic are major areas to investigate**, especially for high-volume private workloads.
- **VPC endpoints can reduce unnecessary NAT traffic**, but endpoint pricing, AZ deployment, and data-processing costs must be evaluated together.
- **Application architecture directly affects networking cost** through payload size, caching, retries, microservice communication, Redis usage, Kafka traffic, and external API calls.
- **Optimize with measured baselines and preserve security and availability**, validating architectural changes through cost data, telemetry, and Infrastructure as Code.