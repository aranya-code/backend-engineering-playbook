# AWS X-Ray with ECS & Fargate

Amazon ECS and AWS Fargate support AWS X-Ray, enabling distributed tracing for containerized applications.

Tracing helps monitor communication between containers, databases, APIs, and other AWS services without changing the overall application architecture.

------------------------------------------------------------------------

# Why Use X-Ray with Containers?

Containerized applications often consist of multiple microservices.

X-Ray helps:

- Trace requests across containers
- Measure service latency
- Detect failures
- Build Service Maps
- Analyze dependencies

------------------------------------------------------------------------

# Architecture

```text
Client

↓

Application Load Balancer

↓

Amazon ECS Service

↓

Container

↓

X-Ray Daemon

↓

AWS X-Ray
```

------------------------------------------------------------------------

# ECS Deployment Models

There are two common deployment approaches.

## Sidecar Container

The X-Ray Daemon runs as a separate container alongside the application container.

```text
Task

├── Application Container

└── X-Ray Daemon Container
```

This is the recommended approach.

------------------------------------------------------------------------

## Daemon Service (EC2 Launch Type)

For ECS using EC2 launch type, the X-Ray Daemon can run once per EC2 instance.

All containers send trace data to the daemon.

------------------------------------------------------------------------

# AWS Fargate

For Fargate tasks, the daemon typically runs as a sidecar container because there is no underlying host to manage.

------------------------------------------------------------------------

# Trace Flow

```text
Client

↓

ALB

↓

Application Container

↓

X-Ray SDK

↓

Daemon Container

↓

AWS X-Ray
```

------------------------------------------------------------------------

# Required Components

- X-Ray SDK
- X-Ray Daemon
- IAM Task Role
- Active instrumentation

------------------------------------------------------------------------

# IAM Permissions

Attach the managed policy:

```text
AWSXRayDaemonWriteAccess
```

to the ECS Task Role.

------------------------------------------------------------------------

# Service Map

Example:

```text
Client

↓

ALB

↓

Orders Container

↓

Payments Container

↓

Amazon DynamoDB
```

Each container appears as a separate service in the Service Map.

------------------------------------------------------------------------

# Real-World Example

An online streaming platform uses Amazon ECS.

```text
User

↓

Application Load Balancer

↓

Authentication Service

↓

Recommendation Service

↓

Content Service

↓

Amazon ElastiCache
```

X-Ray shows that the Recommendation Service experiences high latency during peak hours, helping engineers optimize the recommendation algorithm.

------------------------------------------------------------------------

# Best Practices

- Use the sidecar container pattern.
- Instrument all microservices.
- Enable tracing for inter-service communication.
- Monitor daemon container health.
- Use CloudWatch alongside X-Ray.
- Configure appropriate sampling rules.

------------------------------------------------------------------------

# Key Takeaways

- AWS X-Ray supports Amazon ECS and AWS Fargate.
- The sidecar daemon pattern is recommended for most deployments.
- Each container contributes segments to distributed traces.
- X-Ray provides end-to-end visibility across containerized microservices.