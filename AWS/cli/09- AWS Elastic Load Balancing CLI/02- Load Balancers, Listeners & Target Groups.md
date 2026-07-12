# Load Balancers, Listeners & Target Groups

> Learn how to create, configure, and manage AWS Load Balancers, Listeners, Listener Rules, and Target Groups using the AWS CLI. This chapter covers Application Load Balancers (ALB), Network Load Balancers (NLB), Target Registration, Listener configuration, and production traffic routing.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Create Load Balancers
- Configure Listeners
- Create Target Groups
- Register Targets
- Configure Listener Rules
- Understand Request Routing
- Design highly available traffic distribution

---

# Load Balancer Workflow

A typical request follows this path:

```text
Internet

↓

Route 53

↓

Application Load Balancer

↓

Listener

↓

Listener Rule

↓

Target Group

↓

EC2 / ECS / Lambda
```

---

# Load Balancer Components

```text
Application Load Balancer

│

├── Listener

├── Listener Rules

├── Target Groups

├── Registered Targets

└── Health Checks
```

---

# Create an Application Load Balancer

Example:

```bash
aws elbv2 create-load-balancer \
--name production-alb \
--subnets subnet-11111111 subnet-22222222 \
--security-groups sg-0123456789abcdef0
```

Returns:

- Load Balancer ARN
- DNS Name
- Scheme
- State

---

# Internal Load Balancer

For private applications:

```bash
aws elbv2 create-load-balancer \
--name internal-alb \
--scheme internal \
--subnets subnet-private-a subnet-private-b \
--security-groups sg-private
```

Internal ALBs are accessible only within the VPC.

---

# Internet-Facing Load Balancer

Default configuration:

```text
Internet

↓

ALB

↓

Public Subnets
```

Typically used for:

- Public APIs
- Websites
- Mobile applications

---

# List Load Balancers

```bash
aws elbv2 describe-load-balancers
```

Displays:

- ARN
- DNS Name
- Type
- Scheme
- VPC
- Availability Zones

---

# Delete a Load Balancer

```bash
aws elbv2 delete-load-balancer \
--load-balancer-arn arn:aws:elasticloadbalancing:...
```

---

# What is a Listener?

A Listener waits for incoming requests on a specific protocol and port.

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

# Listener Workflow

```text
Client

↓

Listener

↓

Listener Rule

↓

Target Group
```

---

# Create a Target Group

```bash
aws elbv2 create-target-group \
--name web-targets \
--protocol HTTP \
--port 80 \
--vpc-id vpc-0123456789abcdef0
```

---

# Target Types

Target Groups support:

```text
Target Group

│

├── EC2 Instances

├── IP Addresses

└── Lambda Functions
```

---

# List Target Groups

```bash
aws elbv2 describe-target-groups
```

---

# Delete Target Group

```bash
aws elbv2 delete-target-group \
--target-group-arn arn:aws:elasticloadbalancing:...
```

---

# Register Targets

Example:

```bash
aws elbv2 register-targets \
--target-group-arn arn:aws:elasticloadbalancing:... \
--targets Id=i-0123456789abcdef0
```

---

# Deregister Targets

```bash
aws elbv2 deregister-targets \
--target-group-arn arn:aws:elasticloadbalancing:... \
--targets Id=i-0123456789abcdef0
```

---

# View Registered Targets

```bash
aws elbv2 describe-target-health \
--target-group-arn arn:aws:elasticloadbalancing:...
```

Shows:

- Target ID
- Health State
- Health Reason
- Availability Zone

---

# Create an HTTP Listener

```bash
aws elbv2 create-listener \
--load-balancer-arn arn:aws:elasticloadbalancing:... \
--protocol HTTP \
--port 80 \
--default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

---

# Create an HTTPS Listener

```bash
aws elbv2 create-listener \
--load-balancer-arn arn:aws:elasticloadbalancing:... \
--protocol HTTPS \
--port 443 \
--certificates CertificateArn=arn:aws:acm:... \
--default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

Requires an ACM certificate.

---

# List Listeners

```bash
aws elbv2 describe-listeners \
--load-balancer-arn arn:aws:elasticloadbalancing:...
```

---

# Delete Listener

```bash
aws elbv2 delete-listener \
--listener-arn arn:aws:elasticloadbalancing:...
```

---

# Listener Rules

A Listener can contain multiple rules.

Example:

```text
/api/*

↓

API Servers
```

```text
/images/*

↓

Image Service
```

```text
/admin/*

↓

Admin Service
```

---

# Rule Evaluation

```text
Incoming Request

↓

Priority 1

↓

Priority 2

↓

Priority 3

↓

Default Rule
```

Rules are evaluated in ascending priority order.

---

# Host-Based Routing

Example:

```text
api.example.com

↓

API Target Group
```

```text
admin.example.com

↓

Admin Target Group
```

Ideal for microservices.

---

# Path-Based Routing

Example:

```text
/api/*

↓

API Service
```

```text
/checkout/*

↓

Checkout Service
```

```text
/products/*

↓

Product Service
```

Multiple services can share one ALB.

---

# Redirect Rule

Example:

```text
HTTP

↓

HTTPS
```

Improves security by forcing encrypted connections.

---

# Fixed Response Rule

Useful for:

- Maintenance pages
- Error responses
- Temporary service shutdown

Example:

```text
503

↓

Maintenance
```

---

# Authentication Rule

ALB supports authentication with:

- Amazon Cognito
- OpenID Connect (OIDC)

Example:

```text
User

↓

Authenticate

↓

Application
```

---

# Listener Rule Architecture

```text
Internet

↓

ALB

↓

Listener

↓

Rule

↓

Target Group

↓

Application
```

---

# Multi-Service Architecture

```text
Users

↓

Application Load Balancer

│

├── /api/*

│      ↓

│   API Target Group

│

├── /admin/*

│      ↓

│   Admin Target Group

│

└── /static/*

       ↓

   Static Service
```

One ALB can serve multiple applications.

---

# Common Errors

## LoadBalancerNotFound

Verify:

- Load Balancer ARN
- Region
- AWS Account

---

## TargetGroupNotFound

Verify:

- Target Group ARN
- VPC
- Region

---

## ListenerNotFound

The Listener ARN is invalid or deleted.

---

## DuplicateListener

A Listener already exists on the specified port.

---

## CertificateNotFound

Verify:

- ACM Certificate
- Region
- Certificate status

---

# Production Best Practices

- Deploy Load Balancers across multiple Availability Zones.
- Use HTTPS for all production applications.
- Redirect HTTP traffic to HTTPS.
- Keep Target Groups small and focused.
- Use Host-Based Routing for microservices.
- Use Path-Based Routing for monolithic APIs.
- Register only healthy targets.
- Monitor Target Health continuously.

---

# Real-World Workflow

```text
Create Load Balancer

↓

Create Target Group

↓

Register Targets

↓

Create Listener

↓

Configure Rules

↓

Test Traffic

↓

Production
```

---

# Architecture Note

```text
Internet
      │
      ▼
Application Load Balancer
      │
      ▼
HTTPS Listener
      │
      ▼
Listener Rules
      │
      ▼
Target Groups
      │
      ▼
EC2 / ECS / Lambda
```

The Listener acts as the entry point for incoming requests, while Listener Rules determine how traffic is routed to backend Target Groups.

---

# Interview Note

### Question

**What is the difference between a Listener and a Target Group in an Application Load Balancer?**

### Answer

A **Listener** is the front-end component of a Load Balancer that listens for incoming client connections on a specific protocol and port, such as HTTP on port 80 or HTTPS on port 443. It evaluates Listener Rules and determines how requests should be handled. A **Target Group** is a collection of backend resources—such as EC2 instances, ECS tasks, Lambda functions, or IP addresses—that receive traffic forwarded by the Listener. The Listener decides *where* to send requests, while the Target Group defines *who* receives them.

---

# Key Takeaways

- Load Balancers distribute traffic across backend resources.
- Listeners receive client requests on specific ports and protocols.
- Target Groups contain the backend resources that process requests.
- Listener Rules enable host-based and path-based routing.
- HTTPS Listeners require ACM certificates.
- Register only healthy targets for reliable traffic distribution.
- Proper Listener and Target Group configuration is fundamental to building scalable and highly available AWS applications.