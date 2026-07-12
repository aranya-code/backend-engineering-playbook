# Introduction to ELB CLI

> Learn how to deploy, manage, and troubleshoot AWS Elastic Load Balancers (ELB) using the AWS Command Line Interface (AWS CLI). This chapter introduces Elastic Load Balancing, load balancing concepts, Application Load Balancers (ALB), Network Load Balancers (NLB), Gateway Load Balancers (GWLB), and the core CLI commands used to manage them.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Elastic Load Balancing
- Understand different Load Balancer types
- Learn request distribution
- Understand high availability
- Understand Target Groups
- Navigate ELB CLI commands
- Build a strong foundation for production traffic management

---

# Why Learn Elastic Load Balancing?

Modern applications rarely run on a single server.

Instead, applications run across multiple instances.

Example:

```text
EC2

EC2

EC2

EC2
```

A Load Balancer distributes incoming requests among these servers.

Benefits include:

- High Availability
- Scalability
- Fault Tolerance
- Zero Downtime Deployments
- Health Monitoring

Elastic Load Balancing is one of the most important AWS networking services.

---

# What is Elastic Load Balancing?

Elastic Load Balancing (ELB) automatically distributes incoming traffic across multiple targets.

Targets can include:

- EC2
- ECS Tasks
- Lambda
- IP Addresses

This improves application availability and scalability.

---

# Traditional Architecture

Without a Load Balancer:

```text
Users

↓

Single EC2

↓

Application
```

Problems:

- Single point of failure
- No scaling
- Downtime during maintenance

---

# Architecture with ELB

```text
Users

↓

Load Balancer

↓

EC2 A

EC2 B

EC2 C
```

Traffic is automatically distributed across healthy targets.

---

# Types of AWS Load Balancers

AWS provides four types.

```text
Elastic Load Balancing

│

├── Application Load Balancer (ALB)

├── Network Load Balancer (NLB)

├── Gateway Load Balancer (GWLB)

└── Classic Load Balancer (Legacy)
```

---

# Application Load Balancer (ALB)

Works at:

```text
OSI Layer 7

(Application Layer)
```

Supports:

- HTTP
- HTTPS
- WebSockets
- gRPC

Ideal for:

- REST APIs
- Web Applications
- Microservices

---

# Network Load Balancer (NLB)

Works at:

```text
OSI Layer 4

(Transport Layer)
```

Supports:

- TCP
- UDP
- TLS

Ideal for:

- Gaming
- Financial systems
- High-performance networking
- Low latency applications

---

# Gateway Load Balancer (GWLB)

Designed for:

- Firewalls
- Security Appliances
- Network inspection
- Third-party virtual appliances

---

# Classic Load Balancer

Legacy service.

AWS recommends:

- ALB
- NLB

for new deployments.

---

# High-Level Architecture

```text
Internet
      │
      ▼
Route 53
      │
      ▼
Application Load Balancer
      │
      ▼
Target Group
      │
      ▼
EC2 Instances
```

---

# Load Balancer Components

A Load Balancer consists of:

```text
Load Balancer

│

├── Listeners

├── Listener Rules

├── Target Groups

├── Targets

└── Health Checks
```

---

# What is a Listener?

A Listener waits for incoming connections.

Example:

```text
Port 80

↓

HTTP
```

or

```text
Port 443

↓

HTTPS
```

---

# What is a Target Group?

A Target Group contains backend resources.

Example:

```text
Target Group

↓

EC2

↓

EC2

↓

Lambda
```

The Load Balancer forwards traffic to healthy targets.

---

# Health Checks

The Load Balancer continuously verifies target health.

```text
ALB

↓

Health Check

↓

Healthy?

↓

Forward Traffic
```

Unhealthy targets stop receiving requests.

---

# ELB CLI Namespace

Elastic Load Balancing Version 2 uses:

```bash
aws elbv2 <operation>
```

Examples:

```bash
aws elbv2 describe-load-balancers
```

```bash
aws elbv2 create-load-balancer
```

```bash
aws elbv2 describe-target-groups
```

---

# List Load Balancers

```bash
aws elbv2 describe-load-balancers
```

Displays:

- ARN
- DNS Name
- Scheme
- VPC
- Type
- State

---

# Describe Target Groups

```bash
aws elbv2 describe-target-groups
```

---

# Describe Listeners

```bash
aws elbv2 describe-listeners
```

---

# Verify Current Identity

Before modifying production infrastructure:

```bash
aws sts get-caller-identity
```

---

# Global CLI Options

Examples:

```bash
aws elbv2 describe-load-balancers \
--profile production
```

```bash
aws elbv2 describe-load-balancers \
--region ap-south-1
```

---

# Production Tip

Always deploy Load Balancers across **multiple Availability Zones**.

```text
Internet

↓

ALB

↓

AZ-A

↓

EC2

────────────

AZ-B

↓

EC2
```

This provides fault tolerance and high availability.

---

# Architecture Note

```text
Users
      │
      ▼
Route 53
      │
      ▼
Elastic Load Balancer
      │
      ▼
Target Group
      │
      ▼
Application Servers
```

Elastic Load Balancing acts as the intelligent traffic distribution layer between users and backend applications.

---

# Interview Note

### Question

**What is Elastic Load Balancing?**

### Answer

Elastic Load Balancing (ELB) is a fully managed AWS service that automatically distributes incoming traffic across multiple healthy targets such as EC2 instances, ECS tasks, Lambda functions, or IP addresses. It improves scalability, fault tolerance, and application availability while integrating with Auto Scaling, Route 53, CloudWatch, AWS Certificate Manager (ACM), and AWS WAF.

---

# Key Takeaways

- Elastic Load Balancing distributes incoming traffic across multiple targets.
- AWS provides Application, Network, Gateway, and Classic Load Balancers.
- ALB operates at Layer 7, while NLB operates at Layer 4.
- Target Groups organize backend resources.
- Health Checks ensure traffic is routed only to healthy targets.
- The AWS CLI uses the `aws elbv2` namespace for managing modern Load Balancers.
- ELB is a core building block of highly available AWS architectures.# Introduction to ELB CLI

> Learn how to deploy, manage, and troubleshoot AWS Elastic Load Balancers (ELB) using the AWS Command Line Interface (AWS CLI). This chapter introduces Elastic Load Balancing, load balancing concepts, Application Load Balancers (ALB), Network Load Balancers (NLB), Gateway Load Balancers (GWLB), and the core CLI commands used to manage them.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Elastic Load Balancing
- Understand different Load Balancer types
- Learn request distribution
- Understand high availability
- Understand Target Groups
- Navigate ELB CLI commands
- Build a strong foundation for production traffic management

---

# Why Learn Elastic Load Balancing?

Modern applications rarely run on a single server.

Instead, applications run across multiple instances.

Example:

```text
EC2

EC2

EC2

EC2
```

A Load Balancer distributes incoming requests among these servers.

Benefits include:

- High Availability
- Scalability
- Fault Tolerance
- Zero Downtime Deployments
- Health Monitoring

Elastic Load Balancing is one of the most important AWS networking services.

---

# What is Elastic Load Balancing?

Elastic Load Balancing (ELB) automatically distributes incoming traffic across multiple targets.

Targets can include:

- EC2
- ECS Tasks
- Lambda
- IP Addresses

This improves application availability and scalability.

---

# Traditional Architecture

Without a Load Balancer:

```text
Users

↓

Single EC2

↓

Application
```

Problems:

- Single point of failure
- No scaling
- Downtime during maintenance

---

# Architecture with ELB

```text
Users

↓

Load Balancer

↓

EC2 A

EC2 B

EC2 C
```

Traffic is automatically distributed across healthy targets.

---

# Types of AWS Load Balancers

AWS provides four types.

```text
Elastic Load Balancing

│

├── Application Load Balancer (ALB)

├── Network Load Balancer (NLB)

├── Gateway Load Balancer (GWLB)

└── Classic Load Balancer (Legacy)
```

---

# Application Load Balancer (ALB)

Works at:

```text
OSI Layer 7

(Application Layer)
```

Supports:

- HTTP
- HTTPS
- WebSockets
- gRPC

Ideal for:

- REST APIs
- Web Applications
- Microservices

---

# Network Load Balancer (NLB)

Works at:

```text
OSI Layer 4

(Transport Layer)
```

Supports:

- TCP
- UDP
- TLS

Ideal for:

- Gaming
- Financial systems
- High-performance networking
- Low latency applications

---

# Gateway Load Balancer (GWLB)

Designed for:

- Firewalls
- Security Appliances
- Network inspection
- Third-party virtual appliances

---

# Classic Load Balancer

Legacy service.

AWS recommends:

- ALB
- NLB

for new deployments.

---

# High-Level Architecture

```text
Internet
      │
      ▼
Route 53
      │
      ▼
Application Load Balancer
      │
      ▼
Target Group
      │
      ▼
EC2 Instances
```

---

# Load Balancer Components

A Load Balancer consists of:

```text
Load Balancer

│

├── Listeners

├── Listener Rules

├── Target Groups

├── Targets

└── Health Checks
```

---

# What is a Listener?

A Listener waits for incoming connections.

Example:

```text
Port 80

↓

HTTP
```

or

```text
Port 443

↓

HTTPS
```

---

# What is a Target Group?

A Target Group contains backend resources.

Example:

```text
Target Group

↓

EC2

↓

EC2

↓

Lambda
```

The Load Balancer forwards traffic to healthy targets.

---

# Health Checks

The Load Balancer continuously verifies target health.

```text
ALB

↓

Health Check

↓

Healthy?

↓

Forward Traffic
```

Unhealthy targets stop receiving requests.

---

# ELB CLI Namespace

Elastic Load Balancing Version 2 uses:

```bash
aws elbv2 <operation>
```

Examples:

```bash
aws elbv2 describe-load-balancers
```

```bash
aws elbv2 create-load-balancer
```

```bash
aws elbv2 describe-target-groups
```

---

# List Load Balancers

```bash
aws elbv2 describe-load-balancers
```

Displays:

- ARN
- DNS Name
- Scheme
- VPC
- Type
- State

---

# Describe Target Groups

```bash
aws elbv2 describe-target-groups
```

---

# Describe Listeners

```bash
aws elbv2 describe-listeners
```

---

# Verify Current Identity

Before modifying production infrastructure:

```bash
aws sts get-caller-identity
```

---

# Global CLI Options

Examples:

```bash
aws elbv2 describe-load-balancers \
--profile production
```

```bash
aws elbv2 describe-load-balancers \
--region ap-south-1
```

---

# Production Tip

Always deploy Load Balancers across **multiple Availability Zones**.

```text
Internet

↓

ALB

↓

AZ-A

↓

EC2

────────────

AZ-B

↓

EC2
```

This provides fault tolerance and high availability.

---

# Architecture Note

```text
Users
      │
      ▼
Route 53
      │
      ▼
Elastic Load Balancer
      │
      ▼
Target Group
      │
      ▼
Application Servers
```

Elastic Load Balancing acts as the intelligent traffic distribution layer between users and backend applications.

---

# Interview Note

### Question

**What is Elastic Load Balancing?**

### Answer

Elastic Load Balancing (ELB) is a fully managed AWS service that automatically distributes incoming traffic across multiple healthy targets such as EC2 instances, ECS tasks, Lambda functions, or IP addresses. It improves scalability, fault tolerance, and application availability while integrating with Auto Scaling, Route 53, CloudWatch, AWS Certificate Manager (ACM), and AWS WAF.

---

# Key Takeaways

- Elastic Load Balancing distributes incoming traffic across multiple targets.
- AWS provides Application, Network, Gateway, and Classic Load Balancers.
- ALB operates at Layer 7, while NLB operates at Layer 4.
- Target Groups organize backend resources.
- Health Checks ensure traffic is routed only to healthy targets.
- The AWS CLI uses the `aws elbv2` namespace for managing modern Load Balancers.
- ELB is a core building block of highly available AWS architectures.