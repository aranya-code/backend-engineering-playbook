# 06- Load Balancer Operations

## Overview

Elastic Load Balancing provides the traffic distribution layer between clients and EC2-backed applications. In a production EC2 architecture, the load balancer typically receives client traffic, evaluates listener rules, selects healthy targets, performs health checks, and removes unhealthy or draining targets from service.

A common backend architecture is:

```text
                    Internet
                       |
                       v
                 +-----------+
                 |    ALB    |
                 +-----------+
                       |
                Listener :443
                       |
                Routing Rules
                       |
                       v
                 Target Group
                  /    |    \
                 /     |     \
                v      v      v
             EC2-1   EC2-2   EC2-3
               |       |       |
            Django   Django   Django
            /FastAPI /FastAPI /FastAPI
               \       |       /
                \      |      /
                     ASG
```

Operational load balancer management involves more than checking whether the load balancer itself is available. The important signals are:

- Listener state
- Listener rules
- Target registration
- Target health
- Health-check configuration
- Security Group connectivity
- Deregistration behavior
- Availability Zone coverage
- Connection behavior
- Application latency and errors
- Auto Scaling integration

For production EC2 environments, the load balancer should be treated as part of the application's traffic-management and availability architecture.

## Load Balancer Types

The two most common Elastic Load Balancing options for EC2 workloads are Application Load Balancer (ALB) and Network Load Balancer (NLB).

| Capability | ALB | NLB |
|---|---|---|
| Layer | Application-oriented | Network-oriented |
| Typical protocols | HTTP, HTTPS | TCP, TLS, UDP, QUIC |
| Host-based routing | Yes | Limited/architecture-dependent |
| Path-based routing | Yes | No |
| HTTP-aware routing | Yes | No |
| Static IP support | Not the primary model | Yes |
| Typical backend | Web/API applications | TCP, TLS, high-performance network services |
| Health checks | HTTP/HTTPS/TCP depending on target group | TCP/HTTP/HTTPS |
| Common use | Django, FastAPI, REST APIs | gRPC/TCP services, network workloads |

Choose the load balancer based on traffic semantics rather than simply choosing the newest or most familiar option.

## Core Components

A production load balancer architecture normally contains:

```text
Load Balancer
    |
    +-- Listener
    |     |
    |     +-- Default Action
    |     +-- Listener Rules
    |
    +-- Target Group
          |
          +-- Target 1
          +-- Target 2
          +-- Target 3
```

### Load Balancer

The load balancer provides the client-facing entry point.

Important attributes include:

- Name
- ARN
- Type
- Scheme
- State
- Availability Zones
- IP address type
- Security Groups
- DNS name

### Listener

A listener accepts connections on a protocol and port.

Typical listeners:

```text
HTTP  :80
HTTPS :443
TCP   :5432
TLS   :443
```

For an HTTPS ALB:

```text
Client
  |
  | HTTPS :443
  v
ALB Listener
  |
  | HTTP or HTTPS
  v
Target Group
  |
  v
EC2
```

### Target Group

A target group defines:

- Targets
- Target type
- Protocol
- Port
- Health checks
- Deregistration behavior
- Load-balancing attributes

Targets can be EC2 instances, IP addresses, or other supported target types depending on the load balancer and target group configuration.

For EC2 instance targets, an Auto Scaling Group can automatically register newly launched instances with the target group. :contentReference[oaicite:0]{index=0}

## Inspecting Load Balancers

List load balancers:

```bash
aws elbv2 describe-load-balancers \
    --profile production \
    --region ap-south-1
```

Get a compact inventory:

```bash
aws elbv2 describe-load-balancers \
    --profile production \
    --region ap-south-1 \
    --query 'LoadBalancers[].{
        Name:LoadBalancerName,
        Type:Type,
        Scheme:Scheme,
        State:State.Code,
        DNS:DNSName,
        VPC:VpcId,
        AZs:AvailabilityZones[].ZoneName
    }' \
    --output table
```

Inspect one load balancer:

```bash
aws elbv2 describe-load-balancers \
    --profile production \
    --region ap-south-1 \
    --names production-api-alb
```

Important operational fields:

| Field | Why it matters |
|---|---|
| `Type` | Determines load-balancing behavior |
| `Scheme` | Determines internet-facing vs internal placement |
| `State.Code` | Indicates operational state |
| `DNSName` | Client-facing endpoint |
| `VpcId` | Identifies network boundary |
| `AvailabilityZones` | Indicates enabled AZ coverage |
| `SecurityGroups` | Controls load balancer traffic |

## Load Balancer Scheme

The two common schemes are:

### Internet-Facing

```text
Internet
   |
   v
Internet-facing ALB
   |
   v
Private EC2 subnets
```

The ALB is publicly reachable while application instances can remain in private subnets.

### Internal

```text
VPC Service A
     |
     v
Internal ALB
     |
     v
EC2 Service B
```

Internal load balancers are useful for:

- Internal APIs
- Microservices
- Private administrative applications
- Service-to-service traffic

## Listener Operations

List listeners:

```bash
aws elbv2 describe-listeners \
    --profile production \
    --region ap-south-1 \
    --load-balancer-arn "$LOAD_BALANCER_ARN"
```

Compact view:

```bash
aws elbv2 describe-listeners \
    --profile production \
    --region ap-south-1 \
    --load-balancer-arn "$LOAD_BALANCER_ARN" \
    --query 'Listeners[].{
        ListenerArn:ListenerArn,
        Protocol:Protocol,
        Port:Port,
        DefaultActions:DefaultActions[].Type
    }' \
    --output table
```

Important operational checks:

- Is the expected listener present?
- Is it listening on the expected port?
- Is the protocol correct?
- Does the default action point to the expected target group?
- Are HTTPS certificates configured correctly?
- Are listener rules routing traffic as expected?

## Listener Rules

ALB listeners can route traffic based on conditions such as:

- Host header
- URL path
- HTTP headers
- Query strings
- Source IP

Example:

```text
https://api.example.com/users
             |
             v
        HTTPS :443
             |
             v
       Host = api.example.com
             |
             v
       Path = /users/*
             |
             v
     API Target Group
```

List listener rules:

```bash
aws elbv2 describe-rules \
    --profile production \
    --region ap-south-1 \
    --listener-arn "$LISTENER_ARN"
```

A production troubleshooting process should verify rule priority as well as the rule conditions.

## Target Groups

List target groups:

```bash
aws elbv2 describe-target-groups \
    --profile production \
    --region ap-south-1
```

Inspect a target group:

```bash
aws elbv2 describe-target-groups \
    --profile production \
    --region ap-south-1 \
    --target-group-arns "$TARGET_GROUP_ARN"
```

Useful fields:

- Protocol
- Port
- Target type
- VPC
- Health-check protocol
- Health-check path
- Health-check port
- Health-check interval
- Healthy threshold
- Unhealthy threshold

## Target Registration

Registering a target makes it eligible to receive traffic after the target passes the required health checks.

For an EC2 instance target:

```bash
aws elbv2 register-targets \
    --profile production \
    --region ap-south-1 \
    --target-group-arn "$TARGET_GROUP_ARN" \
    --targets Id=i-0123456789abcdef0
```

With a specific port:

```bash
aws elbv2 register-targets \
    --profile production \
    --region ap-south-1 \
    --target-group-arn "$TARGET_GROUP_ARN" \
    --targets Id=i-0123456789abcdef0,Port=8000
```

A target should not be registered before the application is ready to serve the configured health check.

For Auto Scaling Groups, prefer letting the ASG manage target registration instead of manually maintaining individual instances. AWS automatically registers instances launched by an attached ASG with the associated target group. :contentReference[oaicite:1]{index=1}

## Target Health

Target health is one of the most important operational signals.

```bash
aws elbv2 describe-target-health \
    --profile production \
    --region ap-south-1 \
    --target-group-arn "$TARGET_GROUP_ARN"
```

Compact output:

```bash
aws elbv2 describe-target-health \
    --profile production \
    --region ap-south-1 \
    --target-group-arn "$TARGET_GROUP_ARN" \
    --query 'TargetHealthDescriptions[].{
        Target:Target.Id,
        Port:Target.Port,
        State:TargetHealth.State,
        Reason:TargetHealth.Reason,
        Description:TargetHealth.Description
    }' \
    --output table
```

Common target states include:

| State | Meaning |
|---|---|
| `initial` | Registration or initial health checks are in progress |
| `healthy` | Target passed health checks |
| `unhealthy` | Target failed health checks |
| `draining` | Target is being deregistered |
| `unused` | Target is not currently eligible for traffic |
| `unavailable` | Health information is unavailable |

AWS exposes reason codes that provide additional diagnostic information, such as `Target.ResponseCodeMismatch`, `Target.Timeout`, and `Target.FailedHealthChecks`. :contentReference[oaicite:2]{index=2}

## Target Health Troubleshooting

A target marked `unhealthy` does not automatically mean the EC2 instance is unhealthy.

Investigate in layers:

```text
Load Balancer
      |
      v
Target Group
      |
      v
Health Check
      |
      v
Security Group
      |
      v
EC2 Network Interface
      |
      v
Listening Port
      |
      v
Nginx / Gunicorn / Uvicorn
      |
      v
Django / FastAPI
```

For example:

```text
ALB health check
GET /health
      |
      v
EC2:8000
      |
      X
Connection refused
```

Possible causes:

- Application is not running
- Wrong port
- Security Group blocks traffic
- Nginx is not listening
- Application binds only to `127.0.0.1`
- Health-check path is incorrect
- Application returns an unexpected status code
- Network ACL blocks traffic
- Application is overloaded

## Health Check Configuration

For an HTTP API, a typical health check might be:

```text
Protocol: HTTP
Port: traffic-port
Path: /health
Healthy threshold: 2
Unhealthy threshold: 3
Timeout: application-dependent
Interval: application-dependent
```

ALB periodically sends health-check requests to registered targets using the configured protocol, port, and path. Targets that fail the configured consecutive checks are removed from service. :contentReference[oaicite:3]{index=3}

The health endpoint should normally be:

```http
GET /health
```

with a lightweight response:

```json
{
  "status": "ok"
}
```

Avoid implementing expensive business logic in the health endpoint.

## Liveness vs Readiness

For production applications, distinguish between basic process health and ability to serve traffic.

### Liveness

Answers:

> Is the application process functioning?

Example:

```text
GET /health
```

### Readiness

Answers:

> Can this instance safely receive production traffic?

Example:

```text
GET /ready
```

A readiness check may verify critical dependencies, while a liveness check should generally avoid failing merely because a downstream dependency is temporarily unavailable.

This distinction helps avoid unnecessary instance replacement during transient dependency failures.

## Security Group Configuration

A common architecture is:

```text
Internet
   |
   v
ALB Security Group
   |
   | TCP 443
   v
ALB
   |
   | TCP 8000
   v
EC2 Security Group
```

The EC2 Security Group should allow the application port from the load balancer's Security Group rather than from the entire internet.

Example:

```text
EC2 SG inbound:

Source:
sg-alb

Port:
8000
```

AWS recommends ensuring that the load balancer can communicate with targets on both the listener and health-check ports. :contentReference[oaicite:4]{index=4}

## Nginx and Application Servers

A common EC2 backend deployment is:

```text
ALB
 |
 | HTTP :80
 v
Nginx
 |
 | localhost / private interface
 v
Gunicorn / Uvicorn
 |
 v
Django / FastAPI
```

For example:

```text
ALB
 |
 | :80
 v
Nginx :80
 |
 | :8000
 v
Gunicorn :8000
 |
 v
Django
```

The ALB health check should normally target a port that represents the actual traffic path.

If Nginx is the application entry point, checking Nginx directly may be appropriate:

```text
ALB -> Nginx -> Application
```

rather than bypassing Nginx:

```text
ALB -> Application
```

unless that is deliberately designed.

## HTTPS Termination

A common production design is:

```text
Client
  |
  | HTTPS :443
  v
ALB
  |
  | HTTP :8000
  v
EC2
```

The ALB terminates TLS and forwards traffic to the target group.

Advantages:

- Centralized certificate management
- Reduced TLS configuration on every instance
- Easier certificate rotation
- Consistent HTTPS enforcement
- Simplified application servers

For internal or end-to-end encrypted architectures:

```text
Client
  |
 HTTPS
  v
ALB
  |
 HTTPS
  v
EC2
```

The appropriate design depends on security requirements and trust boundaries.

## SNI and Multiple Certificates

An HTTPS listener can support multiple certificates for different hostnames.

Example:

```text
api.example.com
    |
    +----> Certificate A
    |
    v
ALB :443

admin.example.com
    |
    +----> Certificate B
    |
    v
ALB :443
```

Operationally verify:

- Correct certificate is attached
- Correct domain is covered
- Certificate is not expired
- Listener is using HTTPS
- Hostname routing matches certificate expectations

## Deregistration and Connection Draining

When a target is deregistered, the load balancer stops sending new traffic to the target and allows existing traffic to drain.

The target enters:

```text
draining
```

before becoming:

```text
unused
```

For ALB target groups, the default deregistration delay is 300 seconds and can be changed. :contentReference[oaicite:5]{index=5}

The operational flow is:

```text
Target InService
      |
      v
Deregister
      |
      v
Draining
      |
      +--> Existing requests finish
      |
      v
Unused
```

This is essential during:

- Instance termination
- Deployments
- Maintenance
- ASG scale-in
- Manual target replacement

## Inspecting Target Group Attributes

```bash
aws elbv2 describe-target-group-attributes \
    --profile production \
    --region ap-south-1 \
    --target-group-arn "$TARGET_GROUP_ARN"
```

Modify deregistration delay:

```bash
aws elbv2 modify-target-group-attributes \
    --profile production \
    --region ap-south-1 \
    --target-group-arn "$TARGET_GROUP_ARN" \
    --attributes \
        Key=deregistration_delay.timeout_seconds,Value=120
```

Choose the value based on actual request duration.

Do not simply configure a very large value. Long-lived connections may cause scale-in and deployment operations to take significantly longer.

## Safe Instance Maintenance

Before manually stopping or terminating an EC2 instance serving production traffic:

```text
Identify target
      |
      v
Deregister target
      |
      v
Wait for draining
      |
      v
Verify target is unused
      |
      v
Stop / terminate instance
```

Check target state:

```bash
aws elbv2 describe-target-health \
    --profile production \
    --region ap-south-1 \
    --target-group-arn "$TARGET_GROUP_ARN" \
    --targets Id=i-0123456789abcdef0
```

AWS recommends deregistering an application target and allowing connections to drain before stopping or terminating the application. :contentReference[oaicite:6]{index=6}

## Auto Scaling Integration

When a target group is attached to an ASG:

```text
ASG
 |
 +-- Launch EC2
 |      |
 |      v
 |  Register Target
 |      |
 |      v
 |  Health Check
 |      |
 |      v
 |  Receive Traffic
 |
 +-- Terminate EC2
        |
        v
    Deregister Target
        |
        v
      Drain
```

This allows the fleet and load balancer to operate as one scaling system.

Do not manually register every instance in an ASG unless there is a specific operational reason.

## Availability Zones

Production load balancers should generally span multiple Availability Zones.

Example:

```text
Region
 |
 +-- AZ-A
 |    |
 |    +-- ALB Node
 |    +-- EC2
 |    +-- EC2
 |
 +-- AZ-B
      |
      +-- ALB Node
      +-- EC2
      +-- EC2
```

The load balancer should have healthy targets available across the enabled Availability Zones.

An operational issue in one AZ should not unnecessarily remove the application's entire capacity.

## Cross-Zone Traffic Considerations

Cross-zone load balancing can affect:

- Traffic distribution
- Network traffic patterns
- AZ failure behavior
- Cost
- Target utilization

Do not treat cross-zone behavior as purely a configuration detail. It affects the architecture's traffic path and capacity distribution.

## Target Registration by Instance vs IP

Target groups can use different target types.

| Target type | Typical use |
|---|---|
| `instance` | EC2 instances managed as a fleet |
| `ip` | Direct IP targets, containers, or specialized networking |
| `lambda` | Lambda-based applications |
| `alb` | Chaining an ALB behind another load balancer where supported |

For a conventional EC2 Auto Scaling architecture:

```text
ASG -> instance target group -> EC2
```

is straightforward and integrates naturally with ASG lifecycle management.

## Operational Target Registration

Registering a target manually:

```bash
aws elbv2 register-targets \
    --profile production \
    --region ap-south-1 \
    --target-group-arn "$TARGET_GROUP_ARN" \
    --targets Id=i-0123456789abcdef0
```

Deregistering:

```bash
aws elbv2 deregister-targets \
    --profile production \
    --region ap-south-1 \
    --target-group-arn "$TARGET_GROUP_ARN" \
    --targets Id=i-0123456789abcdef0
```

Deregistering does not terminate or stop the EC2 instance. It only removes the target from receiving load balancer traffic. :contentReference[oaicite:7]{index=7}

## Monitoring Load Balancers

Monitor at multiple layers.

### Load Balancer Metrics

Useful signals include:

- Request count
- HTTP 4xx
- HTTP 5xx
- Target 4xx/5xx
- Target response time
- Healthy host count
- Unhealthy host count
- Rejected connections where applicable

### EC2 Metrics

Correlate with:

- CPU
- Network
- EBS
- Status checks
- Memory when collected through CloudWatch Agent

### Application Metrics

Monitor:

- Request latency
- Error rate
- Application exceptions
- Database latency
- Redis latency
- Queue depth
- Worker utilization

A useful incident view is:

```text
Traffic
  |
  v
ALB Request Count
  |
  v
Target Health
  |
  v
EC2 CPU / Network
  |
  v
Application Latency
  |
  v
Database / Redis / External APIs
```

## Observability During Incidents

If users report elevated latency:

1. Check ALB request count.
2. Check target response time.
3. Check healthy and unhealthy target counts.
4. Check EC2 resource utilization.
5. Check application logs.
6. Check database and cache latency.
7. Check scaling activities.
8. Check whether the issue is isolated to one AZ or target group.

Do not immediately restart instances.

The load balancer often provides the first useful signal showing whether the problem is:

```text
Client -> ALB
ALB -> Target
Target -> Application
Application -> Dependency
```

## Common Target Health Failures

### `Target.ResponseCodeMismatch`

The application responded, but the HTTP status did not match the configured success codes.

Example:

```text
Health check:
GET /health

Expected:
200

Actual:
503
```

Investigate application readiness and dependency behavior.

### `Target.Timeout`

The target did not respond within the configured timeout.

Possible causes:

- Application overload
- Network connectivity
- Slow database query
- Incorrect port
- Thread/process exhaustion
- Security Group/NACL issues

### `Target.FailedHealthChecks`

The load balancer could not successfully complete the health check.

Investigate:

```text
ALB
 |
 v
Security Group
 |
 v
Network
 |
 v
Port
 |
 v
Nginx
 |
 v
Application
```

AWS exposes reason codes and descriptions to help distinguish load-balancer-side and target-side failures. :contentReference[oaicite:8]{index=8}

## Common Port Misconfiguration

Example:

```text
ALB Listener
443

Target Group
8000

Application
8000

EC2 Security Group
Only allows 22
```

Result:

```text
ALB -> EC2:8000
       X
Security Group
```

The target remains unhealthy.

Correct the EC2 Security Group to allow traffic from the ALB Security Group on the target and health-check ports. :contentReference[oaicite:9]{index=9}

## Common Bind Address Problem

An application configured as:

```text
127.0.0.1:8000
```

is reachable only from the local machine.

For an EC2 target receiving traffic through Nginx or directly from the ALB, the service must listen on an address reachable through the intended network path.

For example, Uvicorn:

```bash
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000
```

The exact binding should follow the application's network architecture.

## Health Check Through Nginx

Example:

```text
ALB
 |
 | :80
 v
Nginx
 |
 | :8000
 v
FastAPI
```

If the ALB checks:

```text
GET /health
```

verify:

```bash
curl -i http://127.0.0.1/health
```

on the instance.

Then verify the application directly when appropriate:

```bash
curl -i http://127.0.0.1:8000/health
```

This isolates:

```text
ALB -> Nginx
```

from:

```text
Nginx -> Application
```

## Load Balancer and gRPC

ALB and NLB have different characteristics for gRPC workloads.

For HTTP/2 and gRPC-based services, validate:

- Listener protocol
- Target group protocol
- Health-check behavior
- TLS termination
- HTTP/2 configuration
- Connection lifetime
- Streaming behavior

For long-lived gRPC connections, deregistration and connection-draining behavior becomes especially important.

Do not assume an HTTP/1.1 REST configuration can simply be reused without validating gRPC-specific behavior.

## Long-Lived Connections

Long-lived connections change operational assumptions.

Examples:

- WebSockets
- gRPC streams
- Server-sent events
- Long polling

A target can be removed from receiving new traffic while existing connections remain active during draining.

Therefore:

```text
Deregister
   !=
Immediate process termination
```

The application shutdown sequence must account for connection lifetime.

## Deployment Strategy

A safe deployment pattern for EC2-backed services is:

```text
New Application Version
        |
        v
New AMI / Launch Template
        |
        v
Controlled Instance Refresh
        |
        v
New Instance
        |
        v
Health Check
        |
        v
ALB Healthy
        |
        v
Receive Traffic
        |
        v
Old Instance Draining
        |
        v
Old Instance Terminated
```

This integrates load balancer health with ASG replacement.

## Blue/Green Deployment

For higher isolation:

```text
                 ALB
                  |
          +-------+-------+
          |               |
       Blue TG         Green TG
          |               |
       Old EC2         New EC2
```

Traffic can be shifted between environments after validating the new fleet.

This can reduce deployment blast radius but requires additional infrastructure and operational coordination.

## Security Best Practices

- Expose only required listener ports.
- Prefer HTTPS for public APIs.
- Keep EC2 targets private when public access is not required.
- Restrict EC2 Security Groups to the load balancer Security Group where appropriate.
- Avoid allowing `0.0.0.0/0` directly to backend application ports.
- Use managed TLS certificates where appropriate.
- Rotate certificates before expiration.
- Review listener rules for unintended routing.
- Use least-privilege IAM permissions for operational tooling.
- Keep load balancer access logs and application logs available for incident analysis.
- Treat health-check endpoints as part of the security boundary.
- Avoid exposing sensitive diagnostic information through health endpoints.

## Scalability Considerations

Load balancer capacity should be considered together with the rest of the architecture.

```text
                    Traffic
                       |
                       v
                      ALB
                       |
             +---------+---------+
             |         |         |
            EC2       EC2       EC2
             |         |         |
             +---------+---------+
                       |
                 Connection Pool
                       |
                       v
                  PostgreSQL
```

Scaling EC2 does not automatically scale:

- PostgreSQL
- Redis
- Kafka
- External APIs
- Network throughput
- Connection pools

For a Django or FastAPI API, database connection management is particularly important because every new application instance can create additional database connections.

## Cost Considerations

Load balancer cost is influenced by usage and configuration.

Monitor:

- Number of load balancers
- Traffic volume
- Number of listeners and target groups
- Processed traffic
- Idle environments
- Duplicate environments
- Non-production infrastructure

Do not remove a load balancer solely because it appears lightly used if it provides an important availability boundary.

Instead, identify whether it is:

- Required
- Idle
- Duplicated
- Temporary
- Part of an environment that should be decommissioned

## Infrastructure as Code

Production load balancers should normally be managed through Infrastructure as Code.

Typical resources include:

```text
VPC
 |
 +-- Subnets
 |
 +-- Security Groups
 |
 +-- Load Balancer
 |
 +-- Listener
 |
 +-- Listener Rules
 |
 +-- Target Group
 |
 +-- Auto Scaling Group
```

Common tools:

- Terraform
- AWS CloudFormation
- AWS CDK

CLI changes are useful for operational investigation and controlled incident response, but permanent configuration should be represented in the infrastructure source of truth.

## Safe Operational Workflow

Before modifying a production load balancer:

```text
Verify AWS Identity
        |
        v
Verify Region
        |
        v
Inspect Load Balancer
        |
        v
Inspect Listener
        |
        v
Inspect Rules
        |
        v
Inspect Target Group
        |
        v
Inspect Target Health
        |
        v
Inspect Security Groups
        |
        v
Make Small Change
        |
        v
Monitor
        |
        v
Verify Traffic
```

Verify the active account:

```bash
aws sts get-caller-identity \
    --profile production
```

Then explicitly use the expected Region:

```bash
aws configure get region \
    --profile production
```

## Production Incident Workflow

When an application is returning errors:

### Check Load Balancer State

```bash
aws elbv2 describe-load-balancers \
    --profile production \
    --region ap-south-1 \
    --names production-api-alb \
    --query 'LoadBalancers[0].{
        Name:LoadBalancerName,
        State:State.Code,
        DNS:DNSName
    }' \
    --output table
```

### Check Listeners

```bash
aws elbv2 describe-listeners \
    --profile production \
    --region ap-south-1 \
    --load-balancer-arn "$LOAD_BALANCER_ARN" \
    --query 'Listeners[].{Protocol:Protocol,Port:Port,Arn:ListenerArn}' \
    --output table
```

### Check Target Health

```bash
aws elbv2 describe-target-health \
    --profile production \
    --region ap-south-1 \
    --target-group-arn "$TARGET_GROUP_ARN" \
    --query 'TargetHealthDescriptions[].{
        Target:Target.Id,
        State:TargetHealth.State,
        Reason:TargetHealth.Reason
    }' \
    --output table
```

### Check EC2 Status

```bash
aws ec2 describe-instance-status \
    --profile production \
    --region ap-south-1 \
    --include-all-instances
```

### Check ASG State

```bash
aws autoscaling describe-auto-scaling-groups \
    --profile production \
    --region ap-south-1 \
    --auto-scaling-group-names production-api-asg \
    --query 'AutoScalingGroups[0].{
        Min:MinSize,
        Desired:DesiredCapacity,
        Max:MaxSize,
        Instances:Instances[].{Id:InstanceId,State:LifecycleState,Health:HealthStatus}
    }' \
    --output json
```

This creates a useful operational chain:

```text
ALB
 |
 v
Target Health
 |
 v
EC2 Health
 |
 v
ASG State
 |
 v
Application
```

## Common Mistakes

### Opening Backend Ports to the Internet

Bad:

```text
EC2 :8000
Source: 0.0.0.0/0
```

Prefer:

```text
EC2 :8000
Source: ALB Security Group
```

### Checking Only EC2 State

An instance can be:

```text
running
```

while its application is completely unavailable.

Always correlate:

```text
EC2 status
+
Target health
+
Application health
```

### Wrong Health Check Path

If the application exposes:

```text
/api/health
```

but the target group checks:

```text
/health
```

the target can remain unhealthy even though the application is working.

### Wrong Health Check Port

The application may listen on:

```text
8000
```

while the target group checks:

```text
80
```

Verify the complete network path.

### Forgetting Security Groups

The ALB Security Group and EC2 Security Group must allow the intended traffic path.

### Terminating Before Draining

Immediately terminating a serving instance can cause:

- 5xx responses
- Broken connections
- Interrupted long-running requests

Deregister and allow appropriate draining first. :contentReference[oaicite:10]{index=10}

### Manually Managing ASG Targets

Manually registering and deregistering instances in an ASG can conflict with the ASG's lifecycle management.

Prefer the ASG integration.

### Setting Excessive Deregistration Delays

An unnecessarily long delay can make deployments and scale-in operations slow.

Set the delay according to real request and connection behavior.

### Ignoring Long-Lived Connections

A 30-second request and a 30-minute gRPC stream require very different draining strategies.

### Debugging Only From the Application

A 503 can originate from:

```text
ALB
Target Group
EC2
Nginx
Application
Database
```

Start at the traffic path and narrow the failure domain.

## Interview Traps

### What Is the Difference Between a Load Balancer and a Target Group?

A load balancer provides the traffic entry point and listener behavior.

A target group defines the backend targets, health checks, and target-level routing configuration.

### What Happens When a Target Fails a Health Check?

The load balancer stops routing new traffic to the unhealthy target. The target health API provides state, reason, and description information to help diagnose the failure. :contentReference[oaicite:11]{index=11}

### Does Deregistering a Target Terminate the EC2 Instance?

No.

Deregistering removes the target from the target group. The EC2 instance continues running unless another operation stops or terminates it. :contentReference[oaicite:12]{index=12}

### What Is Connection Draining?

Connection draining allows existing traffic to finish after a target is deregistered while preventing new traffic from being routed to that target. :contentReference[oaicite:13]{index=13}

### Why Can an EC2 Instance Be Healthy but the Target Be Unhealthy?

Because EC2 health and load balancer target health measure different things.

For example:

```text
EC2:
running + status checks passed

ALB:
GET /health -> timeout

Result:
EC2 healthy
ALB target unhealthy
```

### Why Should the EC2 Security Group Reference the ALB Security Group?

It limits backend access to traffic originating from the intended load balancer rather than exposing the application port to arbitrary network sources.

### Why Is a Load Balancer Useful With Auto Scaling?

The ASG changes fleet capacity while the load balancer routes traffic only to eligible healthy targets.

Together:

```text
Demand
  |
  v
Auto Scaling
  |
  v
EC2 Capacity
  |
  v
Target Group
  |
  v
Load Balancer
  |
  v
Clients
```

### Why Is a Health Endpoint Important?

It provides an explicit signal that the load balancer can use to determine whether an instance is capable of serving traffic.

### Why Can a Target Remain in `draining`?

Because deregistration is still in progress and the configured connection-draining period has not completed. :contentReference[oaicite:14]{index=14}

## Production Checklist

### Load Balancer

- [ ] Correct load balancer type
- [ ] Correct scheme
- [ ] Multiple Availability Zones
- [ ] Correct Security Groups
- [ ] Expected DNS name
- [ ] Required listeners configured

### Listener

- [ ] Correct protocol
- [ ] Correct port
- [ ] Correct default action
- [ ] Correct listener rules
- [ ] Correct certificate for HTTPS
- [ ] Correct rule priorities

### Target Group

- [ ] Correct target type
- [ ] Correct protocol
- [ ] Correct target port
- [ ] Correct health-check protocol
- [ ] Correct health-check path
- [ ] Correct success codes
- [ ] Appropriate health-check timing
- [ ] Appropriate deregistration delay

### EC2 Targets

- [ ] Instances are running
- [ ] EC2 status checks pass
- [ ] Application is listening
- [ ] Security Group permits load balancer traffic
- [ ] Network ACLs permit traffic
- [ ] Nginx/application server is healthy
- [ ] Application health endpoint responds correctly

### Auto Scaling

- [ ] Target group attached to the correct ASG
- [ ] Instances register automatically
- [ ] Unhealthy targets are replaced as intended
- [ ] Scale-in allows connection draining
- [ ] Instance warmup matches application startup

### Monitoring

- [ ] Healthy target count monitored
- [ ] Unhealthy target count monitored
- [ ] Request count monitored
- [ ] 4xx/5xx monitored
- [ ] Target response time monitored
- [ ] EC2 resource metrics correlated
- [ ] Application logs available

## Key Takeaways

- **Treat the load balancer as a traffic-management system:** operational correctness depends on the load balancer, listeners, rules, target groups, health checks, security groups, and backend instances working together.
- **Target health is different from EC2 health:** an EC2 instance can be `running` while its application is unreachable or failing the load balancer health check. :contentReference[oaicite:15]{index=15}
- **Use health checks and connection draining deliberately:** health checks determine traffic eligibility, while deregistration draining protects in-flight requests during maintenance, deployments, and scale-in. :contentReference[oaicite:16]{index=16}
- **Keep backend access restricted to the intended traffic path:** the EC2 Security Group should generally permit application traffic from the load balancer Security Group rather than exposing backend ports directly to the internet. :contentReference[oaicite:17]{index=17}
- **Debug from the traffic path outward:** correlate ALB state, listener configuration, target health, EC2 status, application servers, and downstream dependencies instead of assuming every load-balancer failure is an EC2 problem.