# Auto Scaling Integration & High Availability

> Learn how AWS Elastic Load Balancing integrates with Amazon EC2 Auto Scaling to build highly available, fault-tolerant, and automatically scalable applications. This chapter covers Auto Scaling Groups, dynamic scaling, target registration, cross-zone load balancing, multi-AZ architectures, and production deployment strategies.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand ELB and Auto Scaling integration
- Configure Load Balancers with Auto Scaling Groups
- Understand Cross-Zone Load Balancing
- Build Multi-AZ architectures
- Understand Scaling Policies
- Design highly available applications
- Apply production deployment strategies

---

# Why Integrate ELB with Auto Scaling?

A Load Balancer distributes traffic.

Auto Scaling adjusts capacity.

Together they provide:

- High Availability
- Fault Tolerance
- Automatic Scaling
- Zero Downtime Deployments

---

# High-Level Architecture

```text
Users

↓

Route 53

↓

Application Load Balancer

↓

Auto Scaling Group

↓

EC2 Instances
```

---

# Without Auto Scaling

```text
Users

↓

ALB

↓

EC2

↓

Traffic Spike

↓

Application Slow
```

Resources cannot grow automatically.

---

# With Auto Scaling

```text
Users

↓

ALB

↓

Auto Scaling Group

↓

2 EC2

↓

Traffic Spike

↓

6 EC2
```

Capacity grows automatically.

---

# ELB + ASG Workflow

```text
Traffic

↓

ALB

↓

Auto Scaling Group

↓

Healthy Instances

↓

Serve Requests
```

---

# Target Registration

When Auto Scaling launches a new EC2 instance:

```text
Launch Instance

↓

Register

↓

Target Group

↓

Health Check

↓

Healthy

↓

Receive Traffic
```

Registration is automatic.

---

# Instance Termination

When Auto Scaling removes an instance:

```text
Instance

↓

Connection Draining

↓

Deregister

↓

Terminate
```

Existing requests complete before removal.

---

# Auto Scaling Lifecycle

```text
Launch

↓

Pending

↓

Health Check

↓

In Service

↓

Terminate
```

Only healthy instances receive requests.

---

# Attach Target Group

Associate an Auto Scaling Group with a Target Group.

```bash
aws autoscaling attach-load-balancer-target-groups \
--auto-scaling-group-name production-asg \
--target-group-arns arn:aws:elasticloadbalancing:...
```

---

# Describe Auto Scaling Group

```bash
aws autoscaling describe-auto-scaling-groups
```

Displays:

- Desired Capacity
- Minimum Size
- Maximum Size
- Target Groups
- Instance Count

---

# Detach Target Group

```bash
aws autoscaling detach-load-balancer-target-groups \
--auto-scaling-group-name production-asg \
--target-group-arns arn:aws:elasticloadbalancing:...
```

---

# Scaling Policies

Common scaling policies:

```text
Scaling Policies

│

├── Target Tracking

├── Step Scaling

└── Scheduled Scaling
```

---

# Target Tracking

Automatically adjusts capacity.

Example:

```text
CPU > 60%

↓

Launch EC2
```

When CPU decreases:

```text
CPU < 30%

↓

Terminate EC2
```

---

# Step Scaling

Example:

```text
CPU > 70%

↓

Add 2 Instances
```

```text
CPU > 90%

↓

Add 5 Instances
```

Scaling occurs in predefined steps.

---

# Scheduled Scaling

Useful for predictable workloads.

Example:

```text
09:00

↓

Add Capacity
```

```text
20:00

↓

Reduce Capacity
```

---

# Cross-Zone Load Balancing

Without Cross-Zone:

```text
AZ-A

↓

4 Instances

────────────

AZ-B

↓

1 Instance
```

Traffic may become uneven.

---

# With Cross-Zone Load Balancing

```text
Users

↓

ALB

↓

AZ-A

↓

2 Requests

────────────

AZ-B

↓

2 Requests
```

Traffic is evenly distributed.

---

# Availability Zones

Deploy resources across multiple Availability Zones.

```text
Application Load Balancer

↓

AZ-A

↓

EC2

────────────

AZ-B

↓

EC2
```

Failure of one AZ does not interrupt service.

---

# Multi-AZ Architecture

```text
Users

↓

Route 53

↓

Application Load Balancer

↓

AZ-A

↓

Application

────────────

AZ-B

↓

Application
```

---

# Rolling Deployment

```text
Version 1

↓

Launch Version 2

↓

Health Check

↓

Switch Traffic

↓

Terminate Version 1
```

Downtime is minimized.

---

# Blue-Green Deployment

```text
Blue Environment

↓

Production

────────────

Green Environment

↓

Testing
```

After validation:

```text
Users

↓

Green Environment
```

Rollback is simple if issues occur.

---

# Canary Deployment

```text
Users

↓

ALB

↓

95%

↓

Version 1

────────────

5%

↓

Version 2
```

Traffic gradually shifts.

---

# Instance Refresh

Auto Scaling can gradually replace instances.

```text
Old Instances

↓

Launch New

↓

Health Check

↓

Terminate Old
```

Useful after AMI updates.

---

# Load Balancer States

Typical states:

```text
Provisioning

↓

Active

↓

Failed
```

Monitor state before directing production traffic.

---

# Common Errors

## Target Registration Failed

Verify:

- Correct Target Group
- VPC
- Security Group
- Instance State

---

## Instance Never Becomes Healthy

Verify:

- Health Check path
- Application running
- Correct port
- Firewall rules

---

## Scaling Does Not Occur

Check:

- CloudWatch metrics
- Scaling policy
- Desired capacity
- Maximum capacity

---

## Uneven Traffic Distribution

Verify:

- Cross-Zone Load Balancing
- Healthy targets
- Target registration
- Availability Zone configuration

---

# Production Best Practices

- Always integrate ALB with Auto Scaling Groups.
- Deploy across at least two Availability Zones.
- Use Target Tracking for most workloads.
- Enable Cross-Zone Load Balancing.
- Configure realistic Health Checks.
- Enable Connection Draining during deployments.
- Test scaling policies under load.
- Monitor scaling events with CloudWatch.

---

# Real-World Workflow

```text
Deploy Auto Scaling Group

↓

Create Target Group

↓

Attach Target Group

↓

Deploy ALB

↓

Configure Listener

↓

Health Checks

↓

Production
```

---

# Architecture Note

```text
Users
      │
      ▼
Amazon Route 53
      │
      ▼
Application Load Balancer
      │
      ▼
Auto Scaling Group
      │
      ├── EC2 (AZ-A)
      ├── EC2 (AZ-B)
      └── EC2 (AZ-C)
```

Elastic Load Balancing and Auto Scaling together provide the foundation for highly available, fault-tolerant, and automatically scalable AWS applications.

---

# Interview Note

### Question

**How does an Application Load Balancer integrate with an Auto Scaling Group?**

### Answer

An Application Load Balancer distributes incoming requests to a Target Group, while the Auto Scaling Group automatically launches or terminates EC2 instances based on scaling policies. Newly launched instances are automatically registered with the Target Group and begin receiving traffic only after passing health checks. When instances are terminated, the Load Balancer first drains existing connections before deregistering them, ensuring zero or minimal disruption to client requests.

---

# Key Takeaways

- ELB and Auto Scaling are complementary services that enable scalable architectures.
- Auto Scaling automatically registers and deregisters instances with Target Groups.
- Cross-Zone Load Balancing distributes traffic evenly across Availability Zones.
- Multi-AZ deployments improve fault tolerance and availability.
- Target Tracking is the recommended scaling policy for most production workloads.
- Rolling, Blue-Green, and Canary deployments reduce deployment risk.
- Combining ELB, Auto Scaling, and Health Checks enables resilient, production-ready AWS applications.