# ECS Intermediate Interview Questions

This section covers intermediate-level Amazon ECS interview questions commonly asked for backend, cloud, and DevOps roles. These questions focus on networking, deployment, load balancing, scaling, storage, service discovery, monitoring, and day-to-day ECS operations.

---

# Table of Contents

1. Explain the ECS Deployment Process.
2. What is Desired Count?
3. What is Minimum Healthy Percent?
4. What is Maximum Percent?
5. Explain Rolling Deployments.
6. What is Blue/Green Deployment?
7. ECS Deployment Controller Types
8. What happens during an ECS Service Update?
9. How does ECS work with an Application Load Balancer?
10. Difference between ALB and NLB
11. Explain ECS Health Checks.
12. How does Service Discovery work?
13. What is Amazon Cloud Map?
14. How does ECS Auto Scaling work?
15. Service Auto Scaling vs Cluster Auto Scaling
16. What metrics are commonly used for scaling?
17. Explain Capacity Providers in detail.
18. What storage options are available?
19. How are Secrets managed in ECS?
20. Common Intermediate Interview Questions

---

# 1. Explain the ECS Deployment Process.

### Answer

A typical ECS deployment follows these steps:

```
Developer
      │
      ▼
Build Docker Image
      │
      ▼
Push Image to Amazon ECR
      │
      ▼
Create New Task Definition Revision
      │
      ▼
Update ECS Service
      │
      ▼
Rolling Deployment Starts
      │
      ▼
Old Tasks Terminated
```

ECS gradually replaces old tasks with new ones while maintaining service availability.

---

### Interview Tip

Always mention that **Task Definitions are immutable**. Updating an application creates a **new revision**, not a modification of the existing one.

---

# 2. What is Desired Count?

### Answer

Desired Count specifies how many task instances ECS should keep running.

Example:

```
Desired Count = 4

Running Tasks

✓ Task 1
✓ Task 2
✓ Task 3
✓ Task 4
```

If one task fails:

```
Task 3 Crashes

↓

Running = 3

↓

ECS Starts New Task

↓

Running = 4
```

---

# 3. What is Minimum Healthy Percent?

### Answer

Minimum Healthy Percent determines how many existing tasks must remain running during a deployment.

Example

Desired Tasks = 10

Minimum Healthy = 50%

At least:

```
5 Tasks
```

must remain healthy while ECS deploys new versions.

---

### Interview Question

Why not set it to 0%?

Because all tasks could stop simultaneously, causing downtime.

---

# 4. What is Maximum Percent?

### Answer

Maximum Percent controls how many tasks ECS can temporarily run during deployment.

Example

Desired Count = 10

Maximum Percent = 200%

Maximum running tasks during deployment:

```
20 Tasks
```

After deployment completes, ECS returns to the desired count.

---

# 5. Explain Rolling Deployments.

### Answer

Rolling deployment replaces old tasks gradually.

```
Old Old Old Old

↓

New Old Old Old

↓

New New Old Old

↓

New New New Old

↓

New New New New
```

Advantages

- Minimal downtime
- Easy rollback
- Lower deployment risk

---

# 6. What is Blue/Green Deployment?

### Answer

Blue/Green deployments maintain two separate environments.

```
Blue Environment

(Current Production)

↓

Deploy

↓

Green Environment

↓

Traffic Switch

↓

Blue Removed
```

Benefits

- Zero downtime
- Easy rollback
- Safer deployments

---

### Interview Follow-up

Which AWS service enables Blue/Green deployments?

**AWS CodeDeploy** integrates with ECS to perform Blue/Green deployments.

---

# 7. ECS Deployment Controller Types

ECS supports three deployment controllers.

| Controller | Use Case |
|------------|----------|
| ECS | Standard rolling deployment |
| CodeDeploy | Blue/Green deployments |
| External | Third-party deployment tools |

---

# 8. What happens during an ECS Service Update?

When a service is updated:

1. ECS creates new tasks.
2. Registers them with the load balancer.
3. Waits for health checks.
4. Drains old tasks.
5. Stops old containers.

The process is automatic.

---

# 9. How does ECS work with an Application Load Balancer?

Application Load Balancer distributes traffic across ECS tasks.

```
Internet
      │
      ▼
Application Load Balancer
      │
      ▼
Task A

Task B

Task C
```

Benefits

- High availability
- Health checks
- Path-based routing
- SSL termination

---

# 10. Difference between ALB and NLB

| ALB | NLB |
|------|------|
| Layer 7 | Layer 4 |
| HTTP/HTTPS | TCP/UDP |
| Path Routing | No |
| Host Routing | No |
| SSL Termination | Limited |
| Web Applications | High-performance TCP services |

---

### Interview Question

Which one is most common with ECS?

Application Load Balancer.

---

# 11. Explain ECS Health Checks.

Two types of health checks exist.

### Container Health Check

Executed inside the container.

Example

```
curl localhost:8000/health
```

---

### Load Balancer Health Check

Executed by ALB or NLB.

Example

```
GET /health
```

Only healthy tasks receive traffic.

---

# 12. How does Service Discovery work?

Instead of using IP addresses:

```
10.1.2.55
```

applications communicate using DNS.

Example

```
orders.internal

payments.internal

users.internal
```

This makes service-to-service communication simpler.

---

# 13. What is Amazon Cloud Map?

Cloud Map automatically registers ECS services into DNS.

Example

```
payments.internal

↓

10.0.3.12

10.0.5.14

10.0.7.18
```

Applications only need to know the service name.

---

# 14. How does ECS Auto Scaling work?

Auto Scaling adjusts the number of running tasks based on demand.

Example

```
CPU > 70%

↓

Scale Out

↓

More Tasks
```

```
CPU < 20%

↓

Scale In

↓

Remove Tasks
```

---

# 15. Service Auto Scaling vs Cluster Auto Scaling

| Service Auto Scaling | Cluster Auto Scaling |
|----------------------|----------------------|
| Adds tasks | Adds EC2 instances |
| Uses CloudWatch metrics | Uses Capacity Providers |
| Scales applications | Scales infrastructure |

---

# 16. What metrics are commonly used for scaling?

Common CloudWatch metrics include:

- CPU Utilization
- Memory Utilization
- Request Count
- Target Response Time
- Queue Length
- Custom Metrics

---

### Interview Tip

CPU alone is not always a good scaling metric.

For APIs, request count or response time often provides a better indication of load.

---

# 17. Explain Capacity Providers in detail.

Capacity Providers determine where ECS launches tasks.

Supported providers:

- EC2
- Fargate
- Fargate Spot

Example

```
70%

↓

EC2

30%

↓

Fargate Spot
```

This allows balancing cost and availability.

---

# 18. What storage options are available?

ECS supports multiple storage options.

- Ephemeral storage
- Docker volumes
- Bind mounts
- Amazon EFS
- Amazon EBS (EC2 launch type)

---

### Interview Question

Which storage survives container restarts?

Amazon EFS.

---

# 19. How are Secrets managed in ECS?

Sensitive information should never be stored directly inside Docker images.

Recommended services:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store

ECS injects secrets into containers securely at runtime.

---

### Example

Instead of

```
DATABASE_PASSWORD=mysecret
```

Use

```
Secrets Manager

↓

Inject into Container
```

---

# 20. Common Intermediate Interview Questions

- Explain rolling deployments.
- Explain Blue/Green deployments.
- Difference between Service Auto Scaling and Cluster Auto Scaling.
- How does ECS integrate with ALB?
- What is Amazon Cloud Map?
- Explain Capacity Providers.
- How does ECS update services?
- How are secrets managed?
- What storage options are available?
- How does ECS monitor application health?

---

# Key Takeaways

- ECS deployments are driven by immutable Task Definition revisions.
- Rolling deployments provide gradual updates with minimal downtime, while Blue/Green deployments enable near-zero-downtime releases.
- Desired Count, Minimum Healthy Percent, and Maximum Percent control deployment behavior and service availability.
- Application Load Balancers distribute traffic only to healthy ECS tasks.
- Service Discovery with Amazon Cloud Map simplifies service-to-service communication.
- Service Auto Scaling scales application tasks, whereas Cluster Auto Scaling adjusts the underlying compute capacity.
- ECS supports secure secret management through AWS Secrets Manager and Systems Manager Parameter Store.
- Persistent storage is typically provided through Amazon EFS for shared container data.