# ECS Interview Questions

# ECS Fundamentals

### Q1. What is Amazon ECS?

A fully managed container orchestration service that runs Docker containers on AWS.

---

### Q2. What problems does ECS solve?

- Container scheduling
- Scaling
- Service management
- High availability
- Deployment automation

---

### Q3. ECS vs EKS?

ECS:

- AWS-native
- Simpler
- Lower operational overhead

EKS:

- Kubernetes-based
- More flexible
- More complex

---

### Q4. ECS vs Docker Swarm?

ECS is fully managed and tightly integrated with AWS services.

---

### Q5. Main ECS Components?

- Cluster
- Task Definition
- Task
- Service
- Capacity Provider

---

# ECS Architecture

### Q6. What is an ECS Cluster?

A logical grouping of compute resources where tasks run.

---

### Q7. What is a Task Definition?

A blueprint describing containers, CPU, memory, ports, and IAM roles.

---

### Q8. What is a Task?

A running instance of a Task Definition.

---

### Q9. What is an ECS Service?

Maintains desired task count and supports deployments.

---

### Q10. What is Desired Count?

Number of tasks ECS attempts to keep running.

---

# Launch Types

### Q11. EC2 Launch Type?

Tasks run on EC2 instances managed by you.

---

### Q12. Fargate Launch Type?

Serverless container execution managed by AWS.

---

### Q13. Advantages of Fargate?

- No server management
- Faster deployment
- Simpler operations

---

### Q14. Advantages of EC2?

- Lower cost at scale
- GPU support
- More control

---

### Q15. When would you choose Fargate?

Small teams, variable workloads, operational simplicity.

---

# Task Definitions

### Q16. Why version Task Definitions?

To support deployments and rollbacks.

---

### Q17. Difference between Task Role and Execution Role?

Task Role:

Application permissions.

Execution Role:

Container startup permissions.

---

### Q18. What happens after updating a Task Definition?

A new revision is created.

---

### Q19. Can multiple containers exist in a task?

Yes.

---

### Q20. What is an essential container?

If it fails, the task fails.

---

# Networking

### Q21. What network mode is commonly used with Fargate?

awsvpc

---

### Q22. What is awsvpc mode?

Each task receives its own ENI and IP address.

---

### Q23. Public vs Private Subnets?

Public:

Internet reachable.

Private:

No direct internet access.

---

### Q24. Why place ECS tasks in private subnets?

Reduce attack surface.

---

### Q25. What is a Security Group?

Stateful virtual firewall.

---

# Load Balancing

### Q26. Why use an ALB?

Traffic distribution and health checks.

---

### Q27. What is a Target Group?

Collection of backend targets.

---

### Q28. What happens if health checks fail?

Traffic stops flowing to the target.

---

### Q29. ALB vs NLB?

ALB = Layer 7

NLB = Layer 4

---

### Q30. What is path-based routing?

Route traffic based on URL path.

---

# IAM and Security

### Q31. What is least privilege?

Grant only required permissions.

---

### Q32. Why use Task Roles?

Avoid static AWS credentials.

---

### Q33. Where should secrets be stored?

AWS Secrets Manager.

---

### Q34. Why use KMS?

Encryption key management.

---

### Q35. What is Defense in Depth?

Multiple security layers protecting the system.

---

# Service Discovery

### Q36. What is Cloud Map?

AWS service discovery solution.

---

### Q37. Why not use hardcoded IPs?

IPs change frequently.

---

### Q38. What does Service Discovery solve?

Dynamic service location.

---

### Q39. Cloud Map vs ALB?

Cloud Map = discovery

ALB = traffic routing

---

### Q40. Why use DNS names?

Stable service access.

---

# Storage

### Q41. What is ephemeral storage?

Storage removed when the task stops.

---

### Q42. What is EFS?

Managed shared file storage.

---

### Q43. EFS vs EBS?

EFS = shared

EBS = block storage

---

### Q44. Can ECS mount S3 directly?

No.

---

### Q45. When would you use EFS?

Shared persistent files.

---

# Auto Scaling

### Q46. What is ECS Auto Scaling?

Automatic task count adjustment.

---

### Q47. Scale Out vs Scale In?

Add tasks vs remove tasks.

---

### Q48. What is Target Tracking?

Maintain a metric target value.

---

### Q49. What metrics are commonly used?

CPU and Memory.

---

### Q50. Why are cooldowns important?

Prevent scaling thrashing.

---

# Capacity Providers

### Q51. What is a Capacity Provider?

Determines where tasks run.

---

### Q52. What is Fargate Spot?

Discounted spare Fargate capacity.

---

### Q53. When should Spot be used?

Non-critical workloads.

---

### Q54. What are Base and Weight?

Task placement controls.

---

### Q55. Why use Capacity Provider Strategies?

Balance cost and reliability.

---

# Deployments

### Q56. What is a Rolling Deployment?

Gradually replace old tasks.

---

### Q57. What is Blue/Green Deployment?

Two environments with traffic switching.

---

### Q58. What is Canary Deployment?

Release to a small percentage of users first.

---

### Q59. What is a Deployment Circuit Breaker?

Automatic rollback protection.

---

### Q60. How do you perform ECS rollback?

Deploy a previous task definition revision.

---

# Monitoring

### Q61. Three pillars of observability?

Metrics, Logs, Traces.

---

### Q62. What is Container Insights?

Enhanced ECS monitoring.

---

### Q63. What should every ECS dashboard contain?

CPU, Memory, Errors, Latency.

---

### Q64. What are Golden Signals?

Latency, Traffic, Errors, Saturation.

---

### Q65. How do you investigate a slow service?

Metrics → Logs → Traces.

---

# EventBridge

### Q66. What events does ECS publish?

Task, Service, Deployment events.

---

### Q67. Why use EventBridge?

Event-driven automation.

---

### Q68. EventBridge vs SNS?

EventBridge offers richer routing and filtering.

---

### Q69. Common EventBridge targets?

Lambda, SNS, SQS.

---

### Q70. Example use case?

Task failure alerting.

---

# CI/CD

### Q71. Typical ECS deployment pipeline?

Code → Build → ECR → ECS.

---

### Q72. Why use image versioning?

Predictable deployments and rollbacks.

---

### Q73. Why avoid latest tags?

Poor traceability.

---

### Q74. Why use OIDC?

Avoid long-lived AWS credentials.

---

### Q75. What should run before deployment?

Tests and security scans.

---

# Cost Optimization

### Q76. Biggest ECS cost component?

Compute.

---

### Q77. How do you reduce ECS costs?

Rightsizing and Auto Scaling.

---

### Q78. Why use Fargate Spot?

Reduce compute costs.

---

### Q79. What is FinOps?

Cloud financial operations discipline.

---

### Q80. Common hidden AWS cost?

NAT Gateway.

---

# Troubleshooting

### Q81. Task stuck in PENDING. What do you check?

Capacity and service events.

---

### Q82. Container starts then exits. What do you check?

Logs and exit codes.

---

### Q83. Cannot pull image from ECR. What do you check?

Execution role and repository.

---

### Q84. ALB target unhealthy. What do you check?

Health check path and port.

---

### Q85. AccessDeniedException. What do you check?

IAM permissions.

---

# Senior-Level Scenario Questions

### Q86. Design ECS for a Django SaaS product.

Expected discussion:

- ALB
- ECS
- Redis
- PostgreSQL
- Auto Scaling
- Multi-AZ

---

### Q87. How would you handle 10x traffic growth?

- Caching
- Auto Scaling
- Read replicas
- Load testing

---

### Q88. Monolith or Microservices?

Depends on team size, scaling needs, and complexity.

---

### Q89. How would you secure ECS?

- Private subnets
- Task roles
- Secrets Manager
- KMS
- Monitoring

---

### Q90. What is your troubleshooting process?

Events → Metrics → Logs → Networking → IAM → Root Cause.

---

# Final Senior Engineer Questions

### Q91. Most common ECS production failures?

- IAM
- Networking
- Deployments
- Configuration

---

### Q92. Most important cloud engineering skill?

Systematic troubleshooting.

---

### Q93. What separates junior and senior cloud engineers?

Ability to make tradeoffs and operate systems in production.

---

### Q94. Most important architecture principle?

Simplicity.

---

### Q95. What is the goal of platform engineering?

Enable reliable software delivery at scale.

---

# Key Takeaways

- Learn concepts, not definitions.
- Understand tradeoffs.
- Know how systems fail.
- Know how to troubleshoot.
- Think in terms of reliability, security, scalability, and cost.
