# README

## Overview

This folder contains interview-focused AWS EC2 material designed to move from core service knowledge to senior-level operational and architecture reasoning.

The documents are organized around the areas most commonly required when discussing EC2 in backend engineering interviews:

- Core EC2 concepts
- Networking and security
- Storage
- Auto Scaling and load balancing
- Scenario-based troubleshooting
- Production architecture and operational decisions

The emphasis is on understanding **why a particular design or troubleshooting approach is appropriate**, not memorizing isolated AWS facts.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Quick Revision](./01-%20Quick%20Revision.md) | High-density EC2 revision covering the concepts most likely to be tested |
| 02 | [02- Core EC2 Interview Questions](./02-%20Core%20EC2%20Interview%20Questions.md) | Fundamental EC2 questions covering instances, AMIs, lifecycle, pricing, metadata, and core architecture |
| 03 | [03- Networking and Security Questions](./03-%20Networking%20and%20Security%20Questions.md) | VPC networking, Security Groups, NACLs, IP addressing, ports, load balancers, and EC2 security |
| 04 | [04- Storage Questions](./04-%20Storage%20Questions.md) | EBS, snapshots, instance store, EFS, IOPS, storage performance, backup, and recovery |
| 05 | [05- Auto Scaling and Load Balancing Questions](./05-%20Auto%20Scaling%20and%20Load%20Balancing%20Questions.md) | ASGs, Launch Templates, health checks, scaling policies, ALB/NLB, deployment, and capacity management |
| 06 | [06- Scenario Based Questions](./06-%20Scenario%20Based%20Questions.md) | Production-style incidents involving connectivity, health checks, scaling, storage, deployments, and recovery |

## Interview Preparation Structure

| File | Focus |
|---|---|
| `01- Quick Revision.md` | High-density EC2 revision covering the concepts most likely to be tested |
| `02- Core EC2 Interview Questions.md` | Fundamental EC2 questions covering instances, AMIs, lifecycle, pricing, metadata, and core architecture |
| `03- Networking and Security Questions.md` | VPC networking, Security Groups, NACLs, IP addressing, ports, load balancers, and EC2 security |
| `04- Storage Questions.md` | EBS, snapshots, instance store, EFS, IOPS, storage performance, backup, and recovery |
| `05- Auto Scaling and Load Balancing Questions.md` | ASGs, Launch Templates, health checks, scaling policies, ALB/NLB, deployment, and capacity management |
| `06- Scenario Based Questions.md` | Production-style incidents involving connectivity, health checks, scaling, storage, deployments, dependencies, and recovery |

## Recommended Study Order

Follow the material in this order:

```text
Quick Revision
      |
      v
Core EC2
      |
      v
Networking & Security
      |
      v
Storage
      |
      v
Auto Scaling & Load Balancing
      |
      v
Scenario-Based Questions
```

Start with `01- Quick Revision.md` when refreshing the topic before an interview.

Use the remaining documents progressively when deeper preparation is required.

The scenario-based document should be treated as the senior-level practice layer because it requires combining multiple EC2 concepts rather than answering individual definition-based questions.

## What to Know at Each Level

| Level | Expected Knowledge |
|---|---|
| Intermediate | EC2 lifecycle, instance types, AMIs, EBS, Security Groups, SSH, public/private networking |
| Strong Backend Engineer | ALB, ASG, health checks, Launch Templates, multi-AZ architecture, storage, monitoring |
| Senior Engineer | Failure isolation, scaling behavior, dependency bottlenecks, deployment strategies, recovery, capacity planning |
| Production-Level | Observability, immutable infrastructure, security boundaries, cost controls, DR, automation, incident response |

## Core Areas to Master

### EC2 Fundamentals

Be able to explain:

- Instance lifecycle
- Instance types and workload selection
- AMIs
- Instance metadata
- User Data
- Instance store
- EBS
- Purchasing options
- Availability Zones
- Instance health

The important interview distinction is between understanding what a feature does and explaining when it should or should not be used.

### Networking

Understand the complete request path:

```text
Client
  |
  v
DNS
  |
  v
Load Balancer
  |
  v
Security Group
  |
  v
ENI
  |
  v
EC2
  |
  v
Application
```

Be comfortable reasoning about:

- VPCs
- Subnets
- Route tables
- Internet Gateway
- NAT Gateway
- Security Groups
- NACLs
- Public and private IP addresses
- Elastic IPs
- Ports
- ALB
- NLB
- DNS
- TLS termination
- Connectivity failures

### Storage

Know how to select between:

```text
EBS
EFS
Instance Store
S3
RDS
```

Be able to reason about:

- Durability
- Performance
- IOPS
- Throughput
- Availability Zone constraints
- Snapshots
- Backups
- Encryption
- Database storage
- Persistent application data
- Storage failure recovery

### Auto Scaling

Understand:

- Minimum capacity
- Desired capacity
- Maximum capacity
- Launch Templates
- AMIs
- Health checks
- Instance replacement
- Scaling policies
- Target tracking
- Step scaling
- Scheduled scaling
- Warm-up behavior
- Scaling delays
- Capacity planning
- Multi-AZ distribution

A senior-level answer should explain what happens **after** EC2 scales, including the impact on databases, caches, queues, and external dependencies.

### Load Balancing

Know the relationship between:

```text
ALB
 |
Target Group
 |
EC2
 |
Application
```

Be comfortable explaining:

- Listeners
- Target groups
- Health checks
- Target registration
- HTTP/HTTPS
- Path-based routing
- Host-based routing
- TLS termination
- Connection draining
- Sticky sessions
- 502 vs 504 failures
- ALB vs NLB use cases

### Troubleshooting

Use a layered approach:

```text
DNS
 |
Network
 |
Load Balancer
 |
Security Group / NACL
 |
EC2
 |
Operating System
 |
Process
 |
Application
 |
Database / Redis / External Service
```

For every scenario, determine:

1. What is failing?
2. What is the scope?
3. Which layer owns the failure?
4. What evidence confirms the hypothesis?
5. What is the safest mitigation?
6. How can the failure be prevented?

## Backend Engineering Connections

EC2 interview questions become more valuable when connected to real backend systems.

### Django and FastAPI

Be able to discuss:

```text
ALB
 |
EC2
 |
Nginx
 |
Gunicorn / Uvicorn
 |
Django / FastAPI
 |
PostgreSQL
 |
Redis
```

Relevant topics include:

- Worker processes
- CPU and memory utilization
- Connection pooling
- Health endpoints
- Graceful shutdown
- Deployment
- Application logging
- Horizontal scaling

### Docker

Understand:

```text
EC2
 |
Docker
 |
Application Container
```

Be prepared to troubleshoot:

- Container startup failures
- Port mappings
- Application binding
- Container memory limits
- Container logs
- Health checks
- Image versioning

### Microservices

Be able to reason about:

- Security Group boundaries
- Service-to-service communication
- Internal load balancing
- gRPC
- REST
- Redis
- Kafka
- Database connections
- Timeouts
- Retries
- Circuit breakers

### CI/CD

Understand how EC2 participates in deployment workflows:

```text
Git
 |
CI
 |
Build
 |
AMI / Artifact
 |
Launch Template
 |
ASG
 |
ALB
 |
Healthy Application
```

Be able to explain rolling deployments, instance refresh, rollback, health validation, and backward-compatible database migrations.

## Scenario Answer Framework

For scenario-based questions, avoid jumping directly to a fix.

Use this structure:

```text
Symptom
   |
   v
Scope
   |
   v
Evidence
   |
   v
Isolation
   |
   v
Root Cause
   |
   v
Mitigation
   |
   v
Validation
   |
   v
Prevention
```

For example, if an API is unreachable:

```text
Is DNS resolving?
        |
        v
Can the client reach the load balancer?
        |
        v
Are targets healthy?
        |
        v
Can ALB reach EC2?
        |
        v
Is the application listening?
        |
        v
Is the application responding?
        |
        v
Are dependencies healthy?
```

This approach demonstrates operational maturity rather than memorized troubleshooting commands.

## High-Value Interview Distinctions

These distinctions are frequently useful when answering EC2 questions:

| Distinction | Key Idea |
|---|---|
| Running vs healthy | `running` does not mean the application is healthy |
| System vs instance status check | Different failure layers |
| Security Group vs NACL | Stateful resource-level rules vs stateless subnet-level rules |
| Public IP vs Internet access | Routing and security configuration are also required |
| EBS vs instance store | Persistent block storage vs ephemeral local storage |
| EBS vs EFS | Block storage vs shared filesystem |
| EBS vs S3 | Block storage vs object storage |
| ALB health vs EC2 health | Application target health vs instance-level health |
| Vertical vs horizontal scaling | Larger instances vs more instances |
| CPU scaling vs demand scaling | Resource utilization is not always the best scaling signal |
| Timeout vs refusal | Different failure points in the network/application path |
| Instance replacement vs repair | Immutable infrastructure often favors replacement |
| Application health vs infrastructure health | A healthy host can still serve broken requests |

## Production Architecture Mental Model

A common production EC2 backend architecture looks like:

```text
                         Route 53
                            |
                            v
                           ALB
                      /           \
                     /             \
                  AZ-A             AZ-B
                   |                 |
                  ASG               ASG
                   |                 |
                EC2/NGINX        EC2/NGINX
                   |                 |
                   +--------+--------+
                            |
                    Application Layer
                       /         \
                      /           \
                 PostgreSQL      Redis
                      |
                     S3
```

The exact architecture varies by workload, but the important principle is that EC2 should generally provide **replaceable compute capacity**, while durable state should be placed in services designed to preserve it.

## Interview Preparation Checklist

Before considering EC2 interview preparation complete, verify that you can explain:

- [ ] EC2 instance lifecycle
- [ ] Instance types and workload selection
- [ ] AMIs and Launch Templates
- [ ] Instance metadata and User Data
- [ ] EBS and snapshots
- [ ] Instance store
- [ ] EFS
- [ ] Security Groups
- [ ] NACLs
- [ ] Public and private subnets
- [ ] Internet Gateway
- [ ] NAT Gateway
- [ ] ALB and NLB
- [ ] Target groups and health checks
- [ ] Auto Scaling Groups
- [ ] Scaling policies
- [ ] Multi-AZ architecture
- [ ] EC2 status checks
- [ ] CloudWatch monitoring
- [ ] SSH troubleshooting
- [ ] Storage troubleshooting
- [ ] Network troubleshooting
- [ ] Application troubleshooting
- [ ] Database connection scaling
- [ ] Redis bottlenecks
- [ ] Deployment failures
- [ ] Instance replacement
- [ ] Capacity planning
- [ ] Backup and recovery
- [ ] Cost optimization
- [ ] Security hardening
- [ ] Production incident response

## Interview Answer Standard

For senior backend interviews, prefer answers that connect multiple layers.

Instead of:

> "I would check the Security Group."

Prefer:

> "I would first determine whether the failure is at the DNS, load-balancer, network, instance, or application layer. If the target is unhealthy, I would inspect the target health reason, verify the configured port and health-check path, test the application locally, and then validate the Security Group path between the load balancer and EC2. I would avoid changing rules until the failing layer is confirmed."

This demonstrates:

- Structured troubleshooting
- Evidence-based diagnosis
- Network understanding
- Application awareness
- Production safety
- Ability to reason across dependencies

## Key Takeaways

- **Master EC2 as a system, not an isolated AWS service:** connect compute, networking, storage, load balancing, Auto Scaling, and application behavior.
- **Use layered troubleshooting:** identify the failing boundary before changing configuration or restarting infrastructure.
- **Senior interviews emphasize trade-offs:** scaling, availability, security, performance, cost, deployment safety, and recovery all matter together.
- **Treat production EC2 instances as replaceable compute:** keep durable state outside instances and use automation for provisioning and recovery.
- **Scenario questions are the highest-value practice:** explain symptom, evidence, root cause, mitigation, validation, and prevention.