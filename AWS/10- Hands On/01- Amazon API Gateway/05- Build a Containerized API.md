# Build a Containerized API

## Overview

While AWS Lambda is an excellent choice for many workloads, not every application is well suited for serverless execution.

Applications that require:

- Long-running processes
- Large dependencies
- Full operating system access
- Background workers
- Custom networking
- Predictable performance

are often deployed as containers.

In this hands-on project, you'll build a containerized REST API using:

- Docker
- Amazon ECS (Fargate)
- Application Load Balancer (ALB)
- Amazon API Gateway
- VPC Link

This architecture is widely used by enterprise backend teams for deploying scalable microservices.

---

# What You'll Build

```text
               Client

                  │

                  ▼

          Amazon API Gateway

                  │

              VPC Link

                  │

                  ▼

     Application Load Balancer

                  │

                  ▼

          Amazon ECS Service

                  │

                  ▼

          Python REST API
```

The API remains accessible through API Gateway while the backend runs as Docker containers.

---

# Prerequisites

Before starting, ensure you have:

- AWS Account
- Docker installed
- Basic understanding of containers
- Amazon VPC with public and private subnets

---

# Architecture

```text
                 Internet

                     │

                     ▼

             Amazon API Gateway

                     │

                 VPC Link

                     │

                     ▼

          Application Load Balancer

                     │

                     ▼

             Amazon ECS Service

                     │

                     ▼

            Docker Containers
```

API Gateway remains the public entry point.

---

# Step 1 — Create a Simple API

Example using FastAPI:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
def hello():
    return {
        "message": "Hello from ECS!"
    }
```

---

# Step 2 — Create a Dockerfile

Example:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

# Step 3 — Build the Docker Image

```bash
docker build -t api-demo .
```

---

# Step 4 — Run Locally

```bash
docker run -p 8000:8000 api-demo
```

Test:

```text
http://localhost:8000/hello
```

Expected response:

```json
{
    "message":"Hello from ECS!"
}
```

---

# Step 5 — Push Image to Amazon ECR

Create an ECR repository.

Example:

```text
backend-api
```

Push the image.

```bash
docker push <repository-url>
```

---

# Step 6 — Create an ECS Cluster

Navigate:

```text
Amazon ECS

↓

Create Cluster
```

Launch type:

```text
AWS Fargate
```

---

# Step 7 — Create Task Definition

Configure:

| Setting | Value |
|----------|-------|
| Launch Type | Fargate |
| CPU | 0.25 vCPU |
| Memory | 512 MB |
| Container Port | 8000 |

Specify the ECR image.

---

# Step 8 — Create ECS Service

Deploy:

```text
Desired Tasks

↓

2
```

Using multiple tasks improves availability.

---

# Step 9 — Create an Application Load Balancer

Configure:

```text
Listener

↓

HTTP :80
```

Target Group:

```text
ECS Tasks
```

The ALB distributes requests across containers.

---

# Step 10 — Verify ECS Service

Open:

```text
ALB DNS

↓

/hello
```

Expected:

```json
{
    "message":"Hello from ECS!"
}
```

The containerized API is now running.

---

# Step 11 — Create a VPC Link

Navigate:

```text
API Gateway

↓

VPC Link

↓

Create
```

Choose:

```text
Application Load Balancer
```

API Gateway now has private connectivity into the VPC.

---

# Step 12 — Create an HTTP API

Create:

```text
HTTP API
```

Integration:

```text
VPC Link

↓

Application Load Balancer
```

---

# Step 13 — Create Route

Route:

```text
GET /hello
```

Deploy:

```text
prod
```

---

# Step 14 — Test API Gateway

Call:

```text
GET /hello
```

Flow:

```text
API Gateway

↓

VPC Link

↓

ALB

↓

ECS

↓

FastAPI
```

---

# Request Flow

```text
Client

↓

API Gateway

↓

VPC Link

↓

ALB

↓

ECS Task

↓

Container

↓

Response
```

---

# Auto Scaling

Instead of:

```text
One Container
```

Use:

```text
Two Tasks

↓

Five Tasks

↓

Ten Tasks
```

ECS Service Auto Scaling adjusts capacity automatically.

---

# Health Checks

ALB periodically checks:

```text
GET /health
```

Healthy containers receive traffic.

Failed containers are replaced automatically.

---

# Logging

Enable:

```text
Amazon CloudWatch Logs
```

Log:

- Requests
- Errors
- Startup events
- Container crashes

---

# Monitoring

Monitor:

- ECS CPU
- ECS Memory
- Request Count
- ALB Latency
- API Gateway Latency
- 4XX Errors
- 5XX Errors

CloudWatch dashboards provide operational visibility.

---

# Production Improvements

A production deployment should also include:

- HTTPS
- AWS WAF
- CloudFront
- Cognito Authentication
- Auto Scaling Policies
- Multiple Availability Zones
- Blue-Green Deployments
- CI/CD Pipeline
- Infrastructure as Code

---

# Production Architecture

```text
                   Users

                      │

                      ▼

                CloudFront

                      │

                      ▼

                  AWS WAF

                      │

                      ▼

             Amazon API Gateway

                      │

                  VPC Link

                      │

                      ▼

         Application Load Balancer

                      │

        ┌─────────────┼─────────────┐

        ▼             ▼             ▼

     ECS Task     ECS Task     ECS Task

        │

        ▼

 PostgreSQL • Redis • S3
```

This is a common enterprise architecture for containerized backend services.

---

# Cleanup

Delete:

- ECS Service
- ECS Cluster
- Task Definition
- ALB
- VPC Link
- API Gateway
- ECR Repository

to avoid unnecessary AWS charges.

---

# What You Learned

In this hands-on project, you learned how to:

- Containerize a Python API using Docker.
- Store container images in Amazon ECR.
- Deploy containers using Amazon ECS Fargate.
- Expose services through an Application Load Balancer.
- Connect API Gateway to private resources using VPC Link.
- Monitor containerized applications with CloudWatch.

---

# Common Interview Questions

### Why use ECS instead of Lambda?

ECS is better suited for long-running applications, large dependencies, custom runtimes, and workloads requiring predictable performance or full operating system control.

---

### Why is a VPC Link required?

VPC Link enables API Gateway to privately access resources such as Application Load Balancers that reside inside a VPC.

---

### Why place an ALB in front of ECS?

The Application Load Balancer distributes traffic across ECS tasks, performs health checks, and enables high availability and scaling.

---

### Why use Fargate?

AWS Fargate eliminates server management by allowing you to run containers without provisioning or maintaining EC2 instances.

---

### What are the advantages of combining API Gateway with ECS?

API Gateway provides authentication, authorization, throttling, request validation, monitoring, and a unified API endpoint, while ECS handles scalable container execution.

---

# Key Takeaways

- Amazon ECS Fargate provides a managed platform for running containerized APIs without managing servers.
- API Gateway integrates with ECS through VPC Link and an Application Load Balancer, enabling secure private connectivity.
- Docker, ECR, ECS, and ALB together form a scalable and highly available container platform.
- Auto Scaling, health checks, CloudWatch monitoring, and load balancing are essential for production deployments.
- This architecture is commonly used for enterprise microservices that require greater flexibility than serverless functions.