# Cheat Sheet & Interview Guide

> A practical reference for the most commonly used AWS Elastic Load Balancing (ELB) CLI commands, deployment workflows, troubleshooting techniques, and interview preparation. This chapter serves as a day-to-day operational guide for Backend Engineers, DevOps Engineers, Cloud Engineers, Platform Engineers, and AWS Solutions Architects.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Quickly recall frequently used ELB CLI commands
- Create and manage Load Balancers
- Configure Target Groups and Listeners
- Troubleshoot unhealthy targets
- Integrate ELB with Auto Scaling
- Secure applications using HTTPS and AWS WAF
- Prepare for AWS certification and backend engineering interviews

---

# Why a Cheat Sheet?

Elastic Load Balancing is used in almost every production AWS architecture.

Instead of memorizing every CLI command, experienced engineers remember:

- Deployment workflow
- Listener configuration
- Target Group management
- Health Check troubleshooting
- Scaling integration
- Security best practices

This chapter provides a quick operational reference.

---

# Command Syntax

General syntax:

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

# Load Balancer Commands

## List Load Balancers

```bash
aws elbv2 describe-load-balancers
```

---

## Create Load Balancer

```bash
aws elbv2 create-load-balancer
```

---

## Delete Load Balancer

```bash
aws elbv2 delete-load-balancer
```

---

## Modify Load Balancer Attributes

```bash
aws elbv2 modify-load-balancer-attributes
```

---

# Listener Commands

## List Listeners

```bash
aws elbv2 describe-listeners
```

---

## Create Listener

```bash
aws elbv2 create-listener
```

---

## Modify Listener

```bash
aws elbv2 modify-listener
```

---

## Delete Listener

```bash
aws elbv2 delete-listener
```

---

# Listener Rule Commands

## List Rules

```bash
aws elbv2 describe-rules
```

---

## Create Rule

```bash
aws elbv2 create-rule
```

---

## Modify Rule

```bash
aws elbv2 modify-rule
```

---

## Delete Rule

```bash
aws elbv2 delete-rule
```

---

# Target Group Commands

## List Target Groups

```bash
aws elbv2 describe-target-groups
```

---

## Create Target Group

```bash
aws elbv2 create-target-group
```

---

## Modify Target Group

```bash
aws elbv2 modify-target-group
```

---

## Delete Target Group

```bash
aws elbv2 delete-target-group
```

---

# Target Registration Commands

## Register Target

```bash
aws elbv2 register-targets
```

---

## Deregister Target

```bash
aws elbv2 deregister-targets
```

---

## View Target Health

```bash
aws elbv2 describe-target-health
```

---

# Health Check Commands

## Modify Health Check

```bash
aws elbv2 modify-target-group
```

---

## View Health Status

```bash
aws elbv2 describe-target-health
```

---

# AWS Certificate Manager Commands

## List Certificates

```bash
aws acm list-certificates
```

---

## Describe Certificate

```bash
aws acm describe-certificate
```

---

# AWS WAF Commands

## Associate WAF

```bash
aws wafv2 associate-web-acl
```

---

## Get WAF Association

```bash
aws wafv2 get-web-acl-for-resource
```

---

## Disassociate WAF

```bash
aws wafv2 disassociate-web-acl
```

---

# Auto Scaling Commands

## Attach Target Group

```bash
aws autoscaling attach-load-balancer-target-groups
```

---

## Detach Target Group

```bash
aws autoscaling detach-load-balancer-target-groups
```

---

## Describe Auto Scaling Groups

```bash
aws autoscaling describe-auto-scaling-groups
```

---

# Useful Global Options

| Option | Purpose |
|----------|----------|
| `--profile` | Use named AWS profile |
| `--region` | Override Region |
| `--output json` | JSON output |
| `--output table` | Table output |
| `--query` | Filter CLI output |
| `--debug` | Enable debug logging |
| `--no-cli-pager` | Disable pager |

---

# Load Balancer Comparison

| Load Balancer | OSI Layer | Best For |
|--------------|-----------|----------|
| Application Load Balancer | Layer 7 | HTTP, HTTPS, REST APIs, Microservices |
| Network Load Balancer | Layer 4 | TCP, UDP, TLS, Low latency |
| Gateway Load Balancer | Layer 3/4 | Firewalls and Network Appliances |
| Classic Load Balancer | Legacy | Existing legacy workloads |

---

# Listener Quick Reference

| Protocol | Common Port |
|-----------|------------:|
| HTTP | 80 |
| HTTPS | 443 |
| TCP | Custom |
| TLS | Custom |
| UDP | Custom |

---

# Target Types

| Target Type | Supported |
|--------------|-----------|
| EC2 Instance | ✅ |
| IP Address | ✅ |
| Lambda Function | ✅ |

---

# Common Health Check Settings

| Setting | Typical Value |
|----------|--------------|
| Protocol | HTTP |
| Path | `/health` |
| Interval | 30 Seconds |
| Timeout | 5 Seconds |
| Healthy Threshold | 5 |
| Unhealthy Threshold | 2 |

---

# Common Errors

| Error | Cause | Resolution |
|--------|-------|------------|
| LoadBalancerNotFound | Invalid ARN | Verify ARN and Region |
| TargetGroupNotFound | Target Group missing | Verify Target Group |
| ListenerNotFound | Listener missing | Verify Listener ARN |
| Target.NotRegistered | Instance not registered | Register Target |
| SSLHandshakeError | Certificate issue | Verify ACM certificate |
| HTTP 502 | Backend application issue | Verify application and target port |
| HTTP 503 | No healthy targets | Verify Target Health |
| HTTP 504 | Backend timeout | Check application latency |

---

# Deployment Checklist

Before exposing a production application:

- □ Load Balancer created
- □ Target Group created
- □ Targets registered
- □ Health Checks passing
- □ HTTPS Listener configured
- □ ACM Certificate attached
- □ HTTP redirected to HTTPS
- □ Security Groups verified
- □ Route 53 Alias Record configured
- □ Auto Scaling attached

---

# Security Checklist

Production ELBs should have:

- HTTPS only
- AWS WAF enabled
- ACM-managed certificates
- Access Logs enabled
- Deletion Protection enabled
- Least-privilege Security Groups
- Regular certificate rotation

---

# Monitoring Checklist

Monitor:

- HealthyHostCount
- UnHealthyHostCount
- RequestCount
- HTTPCode_ELB_5XX_Count
- HTTPCode_Target_5XX_Count
- TargetResponseTime
- ActiveConnectionCount

---

# High Availability Checklist

Every production deployment should include:

```text
Route 53

↓

Application Load Balancer

↓

Multiple Availability Zones

↓

Auto Scaling Group

↓

Healthy Targets
```

---

# Troubleshooting Workflow

```text
Client

↓

Route 53

↓

Load Balancer

↓

Listener

↓

Target Group

↓

Health Check

↓

Application
```

---

# Production Architecture

```text
Users
      │
      ▼
Route 53
      │
      ▼
Application Load Balancer
      │
      ▼
HTTPS Listener
      │
      ▼
Target Group
      │
      ▼
Auto Scaling Group
      │
      ├── EC2 (AZ-A)
      ├── EC2 (AZ-B)
      └── EC2 (AZ-C)
```

---

# Interview Questions

## 1. What is Elastic Load Balancing?

**Answer**

Elastic Load Balancing (ELB) is a managed AWS service that automatically distributes incoming traffic across multiple healthy backend targets to improve scalability, fault tolerance, and application availability.

---

## 2. What is the difference between ALB and NLB?

**Answer**

An Application Load Balancer (ALB) operates at Layer 7 and supports HTTP/HTTPS, advanced routing, WebSockets, and gRPC. A Network Load Balancer (NLB) operates at Layer 4 and supports TCP, UDP, and TLS, making it suitable for ultra-low latency and high-performance applications.

---

## 3. What is a Target Group?

**Answer**

A Target Group is a collection of backend resources such as EC2 instances, ECS tasks, Lambda functions, or IP addresses. The Load Balancer forwards requests only to healthy targets within the Target Group.

---

## 4. What is a Listener?

**Answer**

A Listener monitors a protocol and port on the Load Balancer, evaluates Listener Rules, and forwards requests to the appropriate Target Group.

---

## 5. How do Health Checks work?

**Answer**

The Load Balancer periodically checks backend targets using a configured protocol, port, and path. Unhealthy targets are automatically removed from request routing until they recover.

---

## 6. What is SSL Termination?

**Answer**

SSL Termination occurs when the Load Balancer decrypts HTTPS traffic before forwarding requests to backend targets, centralizing certificate management and reducing encryption overhead on application servers.

---

## 7. What is Connection Draining?

**Answer**

Connection Draining (Deregistration Delay) allows existing client requests to complete before a target is removed from a Target Group during deployments or scaling events.

---

## 8. How does ELB integrate with Auto Scaling?

**Answer**

Auto Scaling automatically registers newly launched instances with the Target Group and deregisters terminating instances. Traffic is only routed to instances that pass the configured Health Checks.

---

## 9. When should you use Sticky Sessions?

**Answer**

Sticky Sessions are appropriate for stateful applications that store user session data on individual application servers. Stateless applications generally should not require them.

---

## 10. How would you troubleshoot HTTP 503 errors from an ALB?

**Answer**

I would verify that the Target Group contains healthy registered targets, review Health Check configuration and results, ensure the application is running on the correct port, check Security Groups and Network ACLs, inspect CloudWatch metrics and ALB Access Logs, and confirm the Listener forwards traffic to the intended Target Group.

---

# Senior Engineer Tips

Experienced cloud engineers typically:

- Prefer Application Load Balancers for HTTP workloads.
- Deploy Load Balancers across multiple Availability Zones.
- Use HTTPS exclusively.
- Store certificates in ACM.
- Keep backend services stateless.
- Enable AWS WAF for internet-facing applications.
- Enable Access Logs for auditing.
- Use Route 53 Alias Records instead of static IP addresses.
- Integrate ALB with Auto Scaling Groups.
- Continuously monitor CloudWatch metrics.

---

# Quick Reference

| Task | Command |
|------|---------|
| List Load Balancers | `aws elbv2 describe-load-balancers` |
| Create Load Balancer | `aws elbv2 create-load-balancer` |
| Create Target Group | `aws elbv2 create-target-group` |
| Register Target | `aws elbv2 register-targets` |
| View Target Health | `aws elbv2 describe-target-health` |
| Create Listener | `aws elbv2 create-listener` |
| List Listeners | `aws elbv2 describe-listeners` |
| List ACM Certificates | `aws acm list-certificates` |
| Associate WAF | `aws wafv2 associate-web-acl` |
| Attach Target Group to ASG | `aws autoscaling attach-load-balancer-target-groups` |

---

# Final Thoughts

Elastic Load Balancing is a core building block of modern AWS architectures. Combined with Route 53, Auto Scaling, ACM, CloudWatch, AWS WAF, and EC2 or ECS, ELB enables highly available, scalable, secure, and fault-tolerant applications capable of serving millions of requests reliably.

---

# Congratulations 🎉

You have completed the **AWS Elastic Load Balancing (ELB) CLI** guide.

You now understand:

- Load Balancer types
- Listeners and Listener Rules
- Target Groups
- Health Checks
- SSL/TLS and ACM
- Auto Scaling integration
- High Availability architectures
- AWS WAF integration
- Access Logging
- Production best practices
- Troubleshooting strategies
- Interview-focused ELB concepts