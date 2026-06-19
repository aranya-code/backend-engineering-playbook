# ECS Architecture

# What is ECS Architecture?

ECS architecture defines how AWS manages, schedules, deploys, and scales containerized workloads.

At a high level:

Internet
    ↓
Load Balancer
    ↓
ECS Service
    ↓
Tasks
    ↓
Database

---

# ECS Architectural Components

An ECS environment consists of:

- Cluster
- Capacity Provider
- Task Definition
- Task
- Service
- Load Balancer
- Networking
- IAM Roles
- Storage

---

# ECS Control Plane

AWS manages the control plane.

Responsibilities:

- Task scheduling
- Service reconciliation
- Health monitoring
- Scaling decisions
- Deployment orchestration

Benefits:

- No master nodes to manage
- No etcd management
- No cluster upgrades

---

# ECS Data Plane

The data plane is where containers run.

Examples:

## EC2 Launch Type

ECS Cluster
    ↓
EC2 Instances
    ↓
Containers

## Fargate Launch Type

ECS Cluster
    ↓
Fargate Infrastructure
    ↓
Containers

---

# Request Flow in ECS

Example:

User
 ↓
Route53
 ↓
ALB
 ↓
ECS Service
 ↓
Task
 ↓
RDS

Detailed Flow:

1. User sends request.
2. Route53 resolves DNS.
3. ALB receives traffic.
4. ALB selects healthy task.
5. ECS task processes request.
6. Database returns data.
7. Response returned to client.

---

# ECS Cluster Architecture

A cluster is a logical boundary.

Example:

Production Cluster

- User Service
- Payment Service
- Order Service

Development Cluster

- Test APIs
- Internal Tools

Benefits:

- Resource organization
- Security boundaries
- Operational management

---

# ECS Service Architecture

Service ensures desired state.

Desired Count = 3

Running Tasks = 3

If one task crashes:

Running Tasks = 2

ECS automatically launches:

Replacement Task = 1

Final State = 3

This behavior is called self-healing.

---

# Task Lifecycle

Task Definition
      ↓
Task Created
      ↓
Pending
      ↓
Running
      ↓
Stopped

Pending State:

- Image pulling
- Resource allocation
- Network attachment

Running State:

- Application serving traffic

Stopped State:

- Failure
- Deployment
- Manual stop

---

# ECS Deployment Architecture

Version 1

Task A
Task B
Task C

Deployment Trigger

Version 2

Task A2
Task B2
Task C2

ECS gradually replaces old tasks.

Benefits:

- Zero downtime
- Automated rollback support
- Controlled deployments

---

# ECS Networking Architecture

Recommended Mode:

awsvpc

Each task receives:

- Private IP
- Elastic Network Interface
- Security Group

Example:

Task A → 10.0.1.10

Task B → 10.0.1.11

Benefits:

- Better isolation
- Simplified networking
- Security group per task

---

# ECS with Load Balancers

Application Load Balancer

Internet
   ↓
ALB
   ↓
Task A
Task B
Task C

Benefits:

- Health checks
- SSL termination
- Path-based routing
- Host-based routing

---

# ECS Scaling Architecture

Traffic Increase
       ↓
CPU > 70%
       ↓
CloudWatch Alarm
       ↓
Auto Scaling Policy
       ↓
Additional Tasks

Example:

3 Tasks
 ↓
6 Tasks

---

# ECS Security Architecture

IAM Roles

Task Role
   ↓
Application Access

Execution Role
   ↓
ECR Pull
CloudWatch Logs

Security Groups

ALB SG
 ↓
ECS SG
 ↓
Database SG

Principle:

Least Privilege Access

---

# ECS Logging Architecture

Container
    ↓
STDOUT
    ↓
CloudWatch Logs

Benefits:

- Centralized logs
- Searchable logs
- Retention policies
- Monitoring integration

---

# ECS Monitoring Architecture

Metrics:

- CPU Utilization
- Memory Utilization
- Network Usage
- Task Count

Integrated Services:

- CloudWatch Metrics
- Container Insights
- EventBridge

---

# Production Architecture Example

Internet
    ↓
CloudFront
    ↓
ALB
    ↓
ECS Fargate
    ↓
Redis
    ↓
PostgreSQL

Supporting Services:

- CloudWatch
- EventBridge
- Secrets Manager
- Auto Scaling

---

# Common Architecture Mistakes

## Single AZ Deployment

Risk:

AZ Failure = Application Outage

Solution:

Deploy across multiple AZs.

---

## Public Tasks

Risk:

Direct internet exposure.

Solution:

Use private subnets.

---

## No Health Checks

Risk:

Traffic routed to failed containers.

Solution:

Configure ALB health checks.

---

# Senior Engineer Perspective

When designing ECS architectures, focus on:

- Availability
- Scalability
- Security
- Cost Optimization
- Operational Simplicity
- Failure Recovery

Architecture decisions should always be driven by business requirements rather than service popularity.

---

# Key Takeaways

- ECS architecture consists of control plane and data plane.
- ECS services maintain desired task counts.
- ECS supports self-healing and automatic scaling.
- Load balancers distribute traffic to healthy tasks.
- CloudWatch provides monitoring and observability.
- Production deployments should be multi-AZ and highly available.
