# 03- Multi-AZ VPC Architecture

## Overview

Multi-AZ VPC architecture distributes network infrastructure and application workloads across multiple Availability Zones within an AWS Region to reduce dependency on a single failure domain.

An Availability Zone is an isolated location within a Region with independent infrastructure. A VPC itself spans the Region, while subnets are associated with individual Availability Zones.

A production backend architecture should therefore be designed around multiple AZs when availability requirements justify the additional infrastructure and cost.

A typical architecture looks like:

```text
                         Internet
                            |
                            v
                    Internet Gateway
                            |
                +-----------+-----------+
                |                       |
           Public Subnet A         Public Subnet B
                |                       |
             ALB/NAT                 ALB/NAT
                |                       |
        +-------+-------+       +-------+-------+
        |               |       |               |
   Private App A   Private Data A  Private App B  Private Data B
        |               |       |               |
        +-------+-------+       +-------+-------+
                |                       |
                +-----------+-----------+
                            |
                    Shared AWS Services
```

The goal is not simply to deploy the same resources twice. A true Multi-AZ design must consider:

- Failure domains
- Routing
- Load balancing
- NAT architecture
- Database availability
- Stateful dependencies
- Cross-AZ traffic
- IP capacity
- Security boundaries
- DNS
- Monitoring
- Disaster recovery
- Operational procedures

---

## Why Multi-AZ Architecture Exists

A single-AZ deployment has an inherent failure-domain dependency.

```text
VPC
 |
 +-- AZ A
      |
      +-- Application
      +-- Database
      +-- Redis
```

If AZ A experiences a significant infrastructure failure, all of those workloads may become unavailable.

A Multi-AZ design distributes critical components:

```text
VPC
 |
 +-- AZ A
 |    |
 |    +-- Application
 |    +-- Database Component
 |
 +-- AZ B
      |
      +-- Application
      +-- Database Component
```

This allows the application to continue operating when one AZ becomes unavailable, assuming the application and its dependencies are themselves designed for failover.

Multi-AZ is therefore an architectural property of the complete system, not merely a subnet configuration.

---

## Region and Availability Zone Relationship

The hierarchy is:

```text
AWS Region
 |
 +-- Availability Zone A
 |     |
 |     +-- Subnets
 |
 +-- Availability Zone B
 |     |
 |     +-- Subnets
 |
 +-- Availability Zone C
       |
       +-- Subnets
```

The VPC exists at the Region level.

Subnets are AZ-specific.

Therefore:

```text
VPC
 |
 +-- Subnet A -> AZ A
 +-- Subnet B -> AZ B
 +-- Subnet C -> AZ C
```

A subnet cannot span multiple Availability Zones.

---

## Core Multi-AZ Principle

The most important principle is:

> Do not make one Availability Zone a mandatory dependency for another Availability Zone unless the dependency is intentional.

For example, this architecture introduces cross-AZ dependency:

```text
App A
 |
 v
NAT Gateway B
 |
 v
Internet
```

when a NAT Gateway is available locally in AZ A.

A more resilient architecture is:

```text
App A --> NAT A --> Internet

App B --> NAT B --> Internet
```

This reduces dependency on another AZ for outbound connectivity.

---

## Reference Multi-AZ VPC Architecture

A common production layout is:

```text
VPC: 10.10.0.0/16

                    Internet
                       |
                       v
                Internet Gateway
                       |
             +---------+---------+
             |                   |
            AZ A                AZ B
             |                   |
      +------+-------+    +------+-------+
      |      |       |    |      |       |
    Public  App    Data Public  App     Data
      |      |       |    |      |       |
      |      |       |    |      |       |
     NAT     |       |   NAT     |       |
      |      |       |    |      |       |
      +------+-------+    +------+-------+
             |                   |
             +---------+---------+
                       |
                 AWS Services
```

A typical subnet allocation might be:

| AZ | Public | Application | Data |
|---|---|---|---|
| AZ A | `10.10.0.0/20` | `10.10.16.0/20` | `10.10.32.0/20` |
| AZ B | `10.10.48.0/20` | `10.10.64.0/20` | `10.10.80.0/20` |

These ranges are examples. CIDR allocation should be based on actual capacity requirements.

---

## Multi-AZ Subnet Design

A subnet is associated with one AZ.

Therefore, Multi-AZ subnet architecture requires equivalent subnet roles in multiple AZs.

```text
AZ A
├── Public A
├── Application A
└── Data A

AZ B
├── Public B
├── Application B
└── Data B
```

Keeping the topology symmetric has operational advantages.

For example:

```text
Public A  -> Public Route Table
Public B  -> Public Route Table

App A     -> App Route Table A
App B     -> App Route Table B

Data A    -> Data Route Table
Data B    -> Data Route Table
```

Symmetry makes failure analysis and infrastructure automation easier.

---

## Public Subnets Across AZs

Public-facing load balancers should generally use multiple AZs.

```text
                    Internet
                       |
                       v
              Application Load Balancer
                    /       \
                   /         \
             Public A       Public B
                |               |
              AZ A             AZ B
```

The load balancer can distribute requests to application targets across AZs.

This allows the application tier to continue serving traffic when one AZ loses capacity.

---

## Application Tier Across AZs

Stateless application workloads are especially suitable for Multi-AZ deployment.

For example:

```text
                Application Load Balancer
                       /       \
                      /         \
                     v           v
                 App A         App B
                  AZ A          AZ B
                   |             |
                   +------+------+
                          |
                      Database
```

Django, FastAPI, REST APIs, gRPC services, and Celery workers can generally be distributed across AZs when their state is externalized.

The application instances should avoid storing critical state locally.

Prefer:

```text
Application
   |
   +-- PostgreSQL
   +-- Redis
   +-- S3
   +-- Kafka
```

over:

```text
Application
   |
   +-- Local filesystem state
   +-- Local session state
   +-- Local persistent queue
```

---

## Stateless Application Design

Multi-AZ architecture works best when application instances are interchangeable.

For example:

```text
Request 1 -> App A
Request 2 -> App B
Request 3 -> App A
Request 4 -> App B
```

The application should not depend on a particular instance.

For Django applications, this typically means:

- Store sessions in an appropriate shared backend when required.
- Store uploaded files in object storage rather than local disk.
- Use a shared database.
- Use Redis or another appropriate shared service for cache/state where required.
- Keep application instances replaceable.

For FastAPI and microservices, the same principle applies.

---

## Load Balancing Across AZs

A Multi-AZ application typically uses a load balancer.

```mermaid
flowchart TB
    CLIENT["Clients"]
    ALB["Application Load Balancer"]

    subgraph AZA["Availability Zone A"]
        APP_A["Application A"]
    end

    subgraph AZB["Availability Zone B"]
        APP_B["Application B"]
    end

    CLIENT --> ALB
    ALB --> APP_A
    ALB --> APP_B
```

Health checks are critical.

If App A becomes unhealthy, the load balancer should stop routing new traffic to it.

The architecture therefore combines:

```text
Multi-AZ placement
+
Health checks
+
Load balancing
+
Automatic scaling
```

rather than relying on AZ redundancy alone.

---

## Health Checks

A health check should represent actual application readiness.

A weak health check might only verify:

```text
HTTP 200
```

while the application cannot reach its database.

A better architecture may distinguish:

```text
Liveness
    |
    +-- Is the process running?

Readiness
    |
    +-- Can the application serve requests?
```

For example, readiness may verify critical dependencies without making the health endpoint excessively expensive.

Be careful with dependency-heavy health checks because an external dependency failure can otherwise cause cascading removal of healthy instances.

---

## NAT Gateway Multi-AZ Architecture

A common production design uses one NAT Gateway per AZ.

```text
                    Internet Gateway
                     /            \
                    /              \
                 NAT A            NAT B
                  |                 |
               App A             App B
```

Route tables:

```text
App A Route Table
-----------------
10.10.0.0/16 -> local
0.0.0.0/0    -> NAT A
```

```text
App B Route Table
-----------------
10.10.0.0/16 -> local
0.0.0.0/0    -> NAT B
```

This keeps each application's normal egress path within its AZ.

---

## Why AZ-Local NAT Matters

Consider:

```text
App A
 |
 v
NAT B
 |
 v
Internet Gateway
```

If AZ B becomes unavailable, App A may lose outbound internet access even though App A itself is healthy.

With:

```text
App A -> NAT A
App B -> NAT B
```

the application tiers are more isolated from each other's AZ failures.

There is an explicit cost tradeoff because additional NAT Gateways introduce additional hourly and data-processing costs.

---

## Single NAT Gateway Tradeoff

A lower-cost architecture may use one NAT Gateway:

```text
App A ----+
          |
          v
      NAT Gateway
          |
          v
     Internet
          ^
          |
App B ----+
```

This may be acceptable for:

- Development
- Testing
- Low-criticality workloads
- Cost-sensitive environments

It is usually less desirable for highly available production workloads because it creates a concentrated egress dependency.

The correct choice depends on the required availability target and cost constraints.

---

## Database Multi-AZ Architecture

Database availability must be considered separately from application availability.

A common mistake is:

```text
App A -> DB A
App B -> DB A
```

This makes both application AZs dependent on one database failure domain.

A managed database architecture may instead provide Multi-AZ capabilities:

```text
App A ----+
          |
          v
       Database
       /      \
    AZ A      AZ B
```

The exact implementation depends on the database service and configuration.

For example, Amazon RDS Multi-AZ deployments provide managed availability mechanisms, while read replicas and Aurora have different replication and failover characteristics.

Do not assume that "two database instances" automatically means the same thing as Multi-AZ high availability.

---

## Database Connection Behavior During Failover

Application architecture must account for database failover.

A failover can involve:

```text
Current database endpoint
          |
          v
     Failover event
          |
          v
New primary
```

Applications may temporarily experience:

- Connection failures
- Connection resets
- Timeouts
- Retry requirements

Django, SQLAlchemy, psycopg, and other database clients should use sensible connection management and retry strategies appropriate to the operation.

Do not blindly retry every database operation.

A retry strategy must consider transaction semantics and idempotency.

---

## Redis Multi-AZ Architecture

Redis availability depends on the deployment model.

For managed Redis services, use the service's supported high-availability architecture rather than manually treating two independent Redis instances as a replicated cluster.

Conceptually:

```text
Application
    |
    v
Redis Endpoint
    |
    +---- Primary
    |
    +---- Replica
```

The application should generally connect through the appropriate service endpoint rather than hardcoding an individual node.

---

## Kafka Multi-AZ Architecture

Kafka is naturally suited to distributed broker placement.

Example:

```text
Kafka Cluster

AZ A          AZ B          AZ C
 |             |             |
Broker A      Broker B      Broker C
```

Replication across AZs helps protect partitions from a single-AZ failure.

However, Multi-AZ Kafka architecture introduces:

- Cross-AZ replication traffic
- Latency considerations
- Storage replication costs
- Partition placement requirements

For high-throughput Kafka systems, availability and network cost must be evaluated together.

---

## ECS Multi-AZ Architecture

ECS services can distribute tasks across multiple AZs.

```text
                 ALB
              /       \
             /         \
         ECS Task    ECS Task
            AZ A        AZ B
```

The service scheduler should maintain desired task capacity across the available infrastructure.

Subnet capacity must account for task scaling.

For example:

```text
AZ A App Subnet
    |
    +-- Task 1
    +-- Task 2
    +-- Task 3

AZ B App Subnet
    |
    +-- Task 4
    +-- Task 5
    +-- Task 6
```

Avoid allowing all tasks to accumulate in one AZ when the workload requires AZ resilience.

---

## EKS Multi-AZ Architecture

EKS worker infrastructure should generally span multiple AZs for production workloads.

```text
VPC
 |
 +-- AZ A
 |    |
 |    +-- Nodes
 |    +-- Pods
 |
 +-- AZ B
 |    |
 |    +-- Nodes
 |    +-- Pods
 |
 +-- AZ C
      |
      +-- Nodes
      +-- Pods
```

Kubernetes scheduling mechanisms can help distribute workloads, including:

- Pod topology spread constraints
- Pod anti-affinity
- Node groups across AZs

The cluster's VPC subnet capacity must be sufficient for expected node and pod growth.

---

## Stateful vs Stateless Workloads

Multi-AZ architecture is easier for stateless services.

| Workload | Multi-AZ Approach |
|---|---|
| Django API | Multiple instances/tasks |
| FastAPI | Multiple instances/tasks |
| Nginx | Multiple instances or managed load balancing |
| Celery | Multiple workers |
| PostgreSQL | Managed HA / replication architecture |
| Redis | Managed HA deployment |
| Kafka | Multi-broker replication |
| S3 | AWS-managed regional durability |
| Local filesystem | Avoid as persistent state |

The architecture must account for the failure semantics of each component.

---

## Cross-AZ Traffic

Multi-AZ does not mean all traffic should remain within one AZ.

Some cross-AZ traffic is expected:

```text
App A
 |
 v
Database service
 |
 v
Database component in another AZ
```

The design should understand:

- Latency
- Data transfer charges
- Failure behavior
- Replication traffic
- Application dependency patterns

Do not optimize away necessary cross-AZ replication simply to reduce cost.

Availability requirements take precedence when the workload is critical.

---

## AZ-Aware Architecture

A mature architecture understands which dependencies are AZ-local and which are regional.

Example:

```text
AZ A
 |
 +-- App A
 +-- NAT A

AZ B
 |
 +-- App B
 +-- NAT B

Regional
 |
 +-- S3
 +-- Regional AWS Services
```

Some services are inherently regional while others use AZ-specific infrastructure behind regional endpoints.

Do not assume that every AWS service maps directly to a single subnet or AZ.

---

## DNS and Multi-AZ

DNS plays an important role in Multi-AZ architectures.

For example:

```text
api.example.com
        |
        v
Load Balancer
        |
   +----+----+
   |         |
 App A     App B
```

The application should generally use stable service endpoints rather than hardcoded instance IP addresses.

For internal services:

```text
orders.internal
        |
        v
Internal Load Balancer
        |
   +----+----+
   |         |
Orders A   Orders B
```

DNS abstraction allows infrastructure to change without requiring application configuration changes.

---

## Security Group Architecture

Security Groups should model application relationships rather than AZs.

For example:

```text
ALB SG
  |
  | HTTPS
  v
Application SG
  |
  | PostgreSQL
  v
Database SG
```

Do not create separate Security Groups merely because resources happen to be in different AZs.

AZ placement and security relationships are separate concerns.

---

## Network Failure Domains

A useful design model is:

```text
Region
 |
 +-- AZ A
 |    |
 |    +-- Public subnet
 |    +-- App subnet
 |    +-- Data subnet
 |
 +-- AZ B
      |
      +-- Public subnet
      +-- App subnet
      +-- Data subnet
```

Then ask:

> What happens if everything in AZ A disappears?

A production system should have a concrete answer.

For example:

```text
AZ A fails
    |
    +-- ALB continues using AZ B
    +-- App B continues serving
    +-- NAT B provides egress
    +-- Database fails over appropriately
    +-- Redis fails over appropriately
    +-- Kafka retains replicated partitions
```

If the answer contains a manual emergency procedure for every critical dependency, the system may not actually provide automatic high availability.

---

## AZ Failure Scenario

Consider:

```text
                    ALB
                   /   \
                  /     \
               App A   App B
                AZ A    AZ B
                  \      /
                   \    /
                   Database
```

If AZ A fails:

```text
                    ALB
                     |
                     v
                   App B
                    |
                    v
                 Database
```

The application should continue serving traffic if:

- App B has sufficient capacity.
- The ALB can route to App B.
- Database connectivity remains available.
- Required caches and queues remain available.
- App B can access external dependencies.
- DNS continues functioning.
- Security Groups and routes remain correct.

This is why Multi-AZ must be tested as a complete failure scenario.

---

## Capacity During AZ Failure

One of the most overlooked aspects of Multi-AZ architecture is capacity planning.

Suppose normal capacity is:

```text
AZ A: 10 instances
AZ B: 10 instances
```

Total:

```text
20 instances
```

If AZ A fails, AZ B must be capable of handling the required production load.

If AZ B can only handle:

```text
10 instances
```

then the architecture is redundant but not necessarily capacity-resilient.

A better design reserves sufficient capacity to absorb the failure.

For autoscaling workloads, evaluate:

```text
Normal load
+
AZ failure load
+
Scaling time
+
Available capacity
```

---

## Load Balancer and Capacity Distribution

For an application that normally runs:

```text
AZ A: 4 tasks
AZ B: 4 tasks
```

an AZ failure leaves:

```text
AZ B: 4 tasks
```

If production traffic requires 8 tasks, the system must be able to scale rapidly enough after the failure.

This means:

- Subnet IP capacity must exist.
- ECS/EKS capacity must exist.
- Auto Scaling policies must respond.
- Database capacity must tolerate the increased load.
- NAT capacity must be sufficient.

---

## Multi-AZ and Auto Scaling

Auto Scaling should be designed around failure recovery.

Example:

```text
Normal:
AZ A -> 4 instances
AZ B -> 4 instances

AZ A failure:

AZ B -> 4 existing
       + 4 replacement
       = 8 instances
```

This requires:

- Capacity in AZ B
- Subnet IP availability
- Instance capacity
- Correct launch configuration
- Healthy load balancer targets

Multi-AZ architecture and Auto Scaling therefore complement each other.

---

## Deployment Strategy

Deployments should avoid simultaneously removing capacity from all AZs.

A poor deployment:

```text
AZ A -> old version removed
AZ B -> old version removed
```

A safer approach maintains serving capacity during rollout.

For example:

```text
AZ A -> deploy new version
AZ B -> continue serving old version

then

AZ B -> deploy new version
```

The exact strategy depends on the deployment platform.

Blue/green and rolling deployments can both be used to preserve availability.

---

## Multi-AZ and CI/CD

CI/CD pipelines should treat AZ redundancy as part of the deployment architecture.

A deployment should verify:

- Target health
- Desired capacity
- Running capacity
- AZ distribution
- Load balancer health
- Application readiness
- Database connectivity

Do not declare a deployment successful simply because the new containers or instances started.

The system must remain capable of serving traffic.

---

## Disaster Recovery vs Multi-AZ

Multi-AZ and disaster recovery are related but different.

| Capability | Multi-AZ | Disaster Recovery |
|---|---|---|
| AZ failure | Designed to handle | Yes |
| Region failure | Usually not | Yes |
| Application redundancy | Yes | Usually |
| Regional replication | Not necessarily | Often |
| Backup strategy | Not sufficient | Required |
| Cross-region architecture | Not required | Often required |

Multi-AZ primarily protects against failures within a Region.

It does not automatically provide protection from:

- Region-wide outages
- Data corruption
- Accidental deletion
- Application bugs
- Security incidents

---

## Multi-Region vs Multi-AZ

Multi-AZ:

```text
Region
 |
 +-- AZ A
 +-- AZ B
 +-- AZ C
```

Multi-Region:

```text
Region A
 |
 +-- AZ A
 +-- AZ B

Region B
 |
 +-- AZ A
 +-- AZ B
```

Multi-Region introduces significantly more complexity:

- Data replication
- DNS failover
- Deployment synchronization
- IAM
- Secrets
- Networking
- Observability
- Cost

Do not introduce Multi-Region architecture unless the availability or disaster recovery requirements justify it.

---

## Monitoring Multi-AZ Systems

Monitor the health of each AZ independently.

Useful dimensions include:

- AZ
- Subnet
- Instance
- Target group
- Load balancer
- NAT Gateway
- Database
- ECS service
- EKS node group

Key signals include:

```text
Healthy targets by AZ
Instances/tasks by AZ
Available IPs by AZ
NAT traffic by AZ
Error rate by AZ
Latency by AZ
Database health
Redis health
Kafka broker health
```

An aggregate "everything is healthy" metric can hide an AZ imbalance.

---

## Detecting AZ Imbalance

Suppose:

```text
AZ A: 90% of tasks
AZ B: 10% of tasks
```

The application may technically be Multi-AZ but operationally behave like a single-AZ system.

Monitor distribution explicitly.

For example:

```text
Task distribution:
AZ A = 50%
AZ B = 50%
```

Exact percentages depend on capacity and scheduling behavior, but large unexpected imbalances should be investigated.

---

## Observability During Failure

When troubleshooting an AZ incident, examine:

```text
1. Load balancer target health
2. Application capacity
3. Subnet IP availability
4. NAT Gateway health
5. Database endpoint availability
6. Redis availability
7. Kafka broker health
8. DNS behavior
9. Security Group rules
10. Route tables
```

VPC Flow Logs can help identify network-level failures, while application logs and metrics explain higher-level failures.

---

## Cost Considerations

Multi-AZ architecture increases cost because it often requires additional:

- NAT Gateways
- Load balancer capacity
- Compute capacity
- Database resources
- Redis resources
- Kafka brokers
- Cross-AZ traffic

The correct question is not:

> Can we make this cheaper?

It is:

> Which availability requirement are we paying to satisfy?

For critical production systems, removing redundancy purely to reduce cost can create a much larger operational risk.

---

## Cost Optimization Without Destroying Resilience

Cost optimization can still be performed safely.

Consider:

- Right-size NAT traffic
- Use VPC endpoints where economically justified
- Reduce unnecessary cross-AZ traffic
- Right-size compute
- Use appropriate database capacity
- Remove unused endpoints
- Avoid unnecessary subnet proliferation
- Use autoscaling for variable workloads

Do not remove a second AZ solely because it is more expensive without reassessing the availability target.

---

## Common Mistakes

### Two Subnets in One AZ

Creating two subnets does not create Multi-AZ resilience.

```text
AZ A
├── App Subnet A
└── App Subnet B
```

Both remain inside the same failure domain.

### Multi-AZ Network, Single-AZ Database

The application may be redundant while its critical dependency is not.

### One NAT Gateway for Critical Production

This can create a single egress failure domain.

### Insufficient Capacity

Having an application in two AZs does not guarantee that one AZ can handle the other AZ's traffic.

### Hardcoded IP Addresses

Instance replacement and failover make hardcoded addresses fragile.

### Shared Local State

State stored on one application instance can disappear during failover.

### Ignoring Cross-AZ Costs

Highly distributed architectures can generate significant cross-AZ traffic.

### Assuming Multi-AZ Means Multi-Region

It does not.

### No Failure Testing

An architecture diagram does not prove resilience.

---

## Production Failure Test

A meaningful Multi-AZ test should simulate loss of one AZ's application capacity.

Validate:

```text
[ ] Traffic continues
[ ] ALB removes unhealthy targets
[ ] Remaining AZ has sufficient capacity
[ ] Auto Scaling adds capacity
[ ] Application can reach database
[ ] Application can reach Redis
[ ] Application can reach AWS services
[ ] NAT egress continues
[ ] DNS continues functioning
[ ] No unexpected Security Group blocks
[ ] Error rate remains within acceptable limits
[ ] Recovery time meets requirements
```

For mature systems, failure testing should be automated or incorporated into controlled resilience exercises.

---

## Production Architecture Example

Consider a Django and FastAPI platform with:

- Public REST API
- Internal gRPC services
- Celery workers
- PostgreSQL
- Redis
- Kafka
- S3
- Secrets Manager
- External payment APIs

A production architecture could look like:

```mermaid
flowchart TB
    INTERNET["Internet"]
    ALB["Public ALB"]

    subgraph VPC["Production VPC"]
        subgraph AZA["AZ A"]
            PUBA["Public Subnet A"]
            APPA["Private App A"]
            DATAA["Private Data A"]
            NATA["NAT Gateway A"]
        end

        subgraph AZB["AZ B"]
            PUBB["Public Subnet B"]
            APPB["Private App B"]
            DATAB["Private Data B"]
            NATB["NAT Gateway B"]
        end

        DB["PostgreSQL HA"]
        REDIS["Redis HA"]
        KAFKA["Kafka Cluster"]
        S3["S3 Gateway Endpoint"]
        SECRETS["Secrets Manager Endpoint"]
    end

    INTERNET --> ALB

    ALB --> APPA
    ALB --> APPB

    APPA --> DB
    APPB --> DB

    APPA --> REDIS
    APPB --> REDIS

    APPA --> KAFKA
    APPB --> KAFKA

    APPA --> S3
    APPB --> S3

    APPA --> SECRETS
    APPB --> SECRETS

    APPA --> NATA
    APPB --> NATB
```

The important architectural properties are:

```text
Multi-AZ application capacity
+
Multi-AZ egress
+
Highly available stateful dependencies
+
Private application workloads
+
Controlled public ingress
+
Private AWS service connectivity
```

---

## Infrastructure as Code

Multi-AZ topology should be reproducible through Infrastructure as Code.

A practical structure might be:

```text
networking/
├── vpc.tf
├── availability_zones.tf
├── subnets.tf
├── route_tables.tf
├── nat_gateways.tf
├── endpoints.tf
├── security_groups.tf
└── outputs.tf
```

Application infrastructure can consume subnet IDs rather than embedding network topology into application configuration.

For example:

```hcl
module "vpc" {
  source = "./modules/vpc"

  vpc_cidr = "10.10.0.0/16"

  availability_zones = [
    "ap-south-1a",
    "ap-south-1b"
  ]
}
```

Keep environment-specific configuration separate from reusable network modules.

---

## Architecture Review Checklist

Before approving a Multi-AZ VPC architecture, verify:

```text
[ ] Critical workloads span multiple AZs
[ ] Equivalent subnet roles exist across AZs
[ ] CIDR ranges provide sufficient capacity
[ ] Application workloads are stateless where possible
[ ] Load balancers span required AZs
[ ] NAT architecture matches availability requirements
[ ] Database architecture supports required failover
[ ] Redis architecture supports required failover
[ ] Kafka replication spans failure domains where required
[ ] ECS/EKS capacity is distributed
[ ] Each AZ has sufficient subnet IP capacity
[ ] Auto Scaling can absorb an AZ failure
[ ] Route tables provide correct AZ-local paths
[ ] Security Groups permit required traffic
[ ] DNS does not depend on individual instances
[ ] Cross-AZ traffic and cost are understood
[ ] Monitoring identifies AZ-specific failures
[ ] Failure scenarios have been tested
[ ] Infrastructure is reproducible through IaC
[ ] Disaster recovery requirements are separately addressed
```

---

## Interview Traps

### Does a VPC span multiple AZs?

Yes. A VPC is Regional and can contain subnets in multiple AZs.

### Can a subnet span multiple AZs?

No. A subnet belongs to exactly one AZ.

### Does deploying two application servers create Multi-AZ resilience?

Only if those servers are actually distributed across different AZs and the rest of the architecture can tolerate the failure of one AZ.

### Why deploy NAT Gateways in multiple AZs?

To avoid making private subnet egress dependent on a single AZ.

### Is Multi-AZ the same as Multi-Region?

No. Multi-AZ protects primarily against AZ-level failures within a Region. Multi-Region addresses regional failure and disaster recovery requirements.

### Why does statelessness matter?

Stateless workloads can be replaced or redistributed across AZs without losing critical local state.

### Does Multi-AZ guarantee zero downtime?

No. It reduces failure impact. Application capacity, health checks, database failover, retry behavior, DNS, and deployment architecture still determine the actual recovery behavior.

### Why can a Multi-AZ system still fail during an AZ outage?

Because a dependency may remain single-AZ, the surviving AZ may lack capacity, or routing, DNS, security, or application behavior may prevent successful failover.

### Why is cross-AZ traffic important?

It can introduce latency and data transfer costs and can affect architecture decisions for high-throughput systems.

### How do you prove a Multi-AZ architecture works?

Test the failure scenario rather than relying solely on the architecture diagram.

## Key Takeaways

- Multi-AZ architecture distributes critical infrastructure across independent Availability Zone failure domains, but redundancy must include the application's dependencies, not just its compute instances.
- Production Multi-AZ designs commonly use symmetric subnet layouts, multi-AZ load balancing, AZ-aware NAT architecture, and highly available stateful services.
- Capacity planning is essential: the surviving AZ must have enough compute, IP addresses, network bandwidth, and dependency capacity to handle the required load after an AZ failure.
- Multi-AZ improves availability within a Region but does not replace backups, disaster recovery, or Multi-Region architecture.
- The only reliable way to validate Multi-AZ resilience is to test realistic AZ failure scenarios and verify traffic routing, capacity recovery, dependency failover, security, DNS, and application behavior.