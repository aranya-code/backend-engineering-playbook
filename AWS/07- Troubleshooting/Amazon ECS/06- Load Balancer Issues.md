# Load Balancer Issues

Application Load Balancers (ALB) and Network Load Balancers (NLB) are responsible for routing traffic to healthy Amazon ECS tasks. Incorrect load balancer configuration can lead to application downtime, failed deployments, unhealthy targets, and HTTP 502/503/504 errors.

This guide focuses on diagnosing and resolving the most common load balancer issues encountered in Amazon ECS deployments.

---

# Typical Symptoms

You may observe one or more of the following:

- HTTP 502 Bad Gateway
- HTTP 503 Service Unavailable
- HTTP 504 Gateway Timeout
- Targets remain unhealthy
- Deployment never completes
- ECS repeatedly replaces tasks
- Users cannot access the application

Example

```
Internet

↓

Application Load Balancer

↓

No Healthy Targets

↓

503 Service Unavailable
```

---

# Troubleshooting Workflow

Always troubleshoot load balancer issues using a structured approach.

```
Application Error

        │

        ▼

ALB Listener

        │

        ▼

Target Group

        │

        ▼

Health Checks

        │

        ▼

ECS Service

        │

        ▼

Container

        │

        ▼

Application
```

---

# Step 1: Verify Listener Configuration

Check the ALB Listener.

Verify:

- Listener exists
- Correct protocol
- Correct port
- Correct forwarding rule

Example

```
HTTPS : 443

↓

Target Group
```

---

# Step 2: Verify Target Group

Open the Target Group.

Review:

- Registered targets
- Healthy targets
- Target type
- Port
- Health status

Example

```
Healthy

2

Unhealthy

1
```

---

# Step 3: Check Target Registration

Ensure ECS tasks are registered with the Target Group.

Expected flow

```
Task Started

↓

Target Registered

↓

Health Check Passed

↓

Traffic Begins
```

If registration never occurs, review the ECS Service configuration.

---

# Step 4: Verify Container Port

One of the most common problems is a port mismatch.

Example

Application

```
8000
```

Task Definition

```
8000
```

Target Group

```
5000
```

The Load Balancer cannot communicate with the application.

---

## Resolution

Ensure all ports match:

- Application
- Container
- Task Definition
- Target Group

---

# Step 5: Review Health Check Configuration

Verify:

- Path
- Port
- Protocol
- Timeout
- Interval
- Success codes

Example

```
GET

/health
```

Response

```
HTTP 200
```

---

# Step 6: Verify Security Groups

Traffic flow

```
Internet

↓

ALB

↓

Security Group

↓

ECS Tasks
```

Verify:

ALB Security Group

- Allows inbound traffic

Task Security Group

- Allows traffic from the ALB Security Group

---

# Step 7: Verify Network Configuration

Confirm:

- Correct VPC
- Correct subnets
- Internet Gateway
- NAT Gateway
- Route Tables

Example

```
ALB

Public Subnet

↓

ECS Tasks

Private Subnet
```

This is the recommended production architecture.

---

# Step 8: Review Application Logs

CloudWatch Logs often reveal why requests fail.

Look for:

- Startup failures
- Exceptions
- Port binding issues
- Database failures
- Dependency failures

---

# Step 9: Check ECS Service Events

Common events include:

```
Task failed ELB health checks.
```

```
Service unable to register targets.
```

```
Service reached steady state.
```

These events provide valuable deployment information.

---

# Step 10: Verify Load Balancer Type

Amazon ECS supports:

| Load Balancer | Typical Use Case |
|---------------|------------------|
| Application Load Balancer | HTTP/HTTPS applications |
| Network Load Balancer | TCP/UDP workloads |

For REST APIs and web applications, ALB is generally the preferred choice.

---

# Common HTTP Errors

## HTTP 502 Bad Gateway

### Possible Causes

- Application crashed
- Wrong container port
- Backend unavailable
- Health checks failing
- Target not responding

### Investigation

Review:

- CloudWatch Logs
- ECS Service Events
- Target Group health

---

## HTTP 503 Service Unavailable

### Possible Causes

- No healthy targets
- Tasks stopped
- Deployment in progress
- Service unavailable

### Investigation

Verify:

- Running tasks
- Target registration
- Health checks

---

## HTTP 504 Gateway Timeout

### Possible Causes

- Slow application
- Database latency
- External API delay
- Timeout configuration

### Investigation

Review:

- Response time
- Database performance
- CPU utilization
- Memory utilization

---

# Common Root Causes

| Problem | Solution |
|----------|----------|
| Wrong listener | Correct listener configuration |
| Wrong target group | Update ECS Service |
| Incorrect port mapping | Match container and target group ports |
| Failed health checks | Fix application or health endpoint |
| Security Group issue | Update inbound/outbound rules |
| Network routing | Verify VPC, subnets, and route tables |
| No registered targets | Verify ECS Service registration |
| Application startup failure | Review CloudWatch Logs |

---

# Diagnostic Checklist

Before modifying infrastructure, verify:

- ALB Listener configured.
- Target Group exists.
- Targets registered.
- Targets healthy.
- Health endpoint returns HTTP 200.
- Container port correct.
- Security Groups configured.
- Route Tables correct.
- ECS Service healthy.
- CloudWatch Logs reviewed.
- Application running correctly.

---

# Best Practices

- Use Application Load Balancer for HTTP and HTTPS applications.
- Configure health checks on lightweight endpoints.
- Deploy ECS tasks across multiple Availability Zones.
- Enable access logs for the Load Balancer.
- Configure CloudWatch alarms for unhealthy target counts.
- Use HTTPS for production traffic.
- Avoid hardcoding ports in application code.
- Regularly monitor Target Group health.

---

# Interview Questions

### Why would an ALB return HTTP 503?

Possible reasons include:

- No healthy targets
- ECS tasks stopped
- Failed health checks
- Incorrect Target Group configuration

---

### Why would an ALB return HTTP 502?

Common causes include:

- Backend application crashed
- Wrong container port
- Application not listening
- Health check failures

---

### Why would an ALB return HTTP 504?

Typically caused by:

- Slow application
- Long-running database queries
- External service latency
- Backend timeout

---

### How would you troubleshoot an unhealthy target?

Recommended investigation order:

1. Target Group health
2. ECS Service Events
3. Health check configuration
4. CloudWatch Logs
5. Container port
6. Security Groups
7. Application logs

---

### Why is an Application Load Balancer preferred over a Network Load Balancer for REST APIs?

Because ALBs provide Layer 7 features such as:

- HTTP/HTTPS support
- Path-based routing
- Host-based routing
- SSL termination
- Advanced health checks
- WebSocket support

These capabilities make ALBs better suited for most web applications and REST APIs.

---

# Key Takeaways

- Most ECS load balancer issues originate from incorrect listener configuration, unhealthy targets, port mismatches, networking problems, or failed health checks.
- Always troubleshoot from the Load Balancer inward: Listener → Target Group → Health Checks → ECS Service → Container → Application.
- Understanding the meaning of HTTP 502, 503, and 504 responses helps narrow down the root cause quickly.
- Proper health checks, security group configuration, and target registration are essential for reliable traffic routing.
- Continuous monitoring of Target Groups, CloudWatch metrics, and ECS Service Events helps detect load balancer issues before they impact users.