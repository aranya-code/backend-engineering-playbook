# Production Container API

## Overview

Many enterprise applications cannot run entirely on serverless platforms.

Common reasons include:

- Long-running processes
- Large machine learning libraries
- Background workers
- Custom operating system dependencies
- Stateful connections
- High and predictable traffic

For these workloads, containers provide greater flexibility while maintaining scalability.

In this hands-on project, you'll build a **production-ready containerized API** using:

- Amazon API Gateway
- Amazon ECS Fargate
- Amazon ECR
- Application Load Balancer
- VPC Link
- Amazon RDS
- Amazon ElastiCache (Redis)
- CloudFront
- AWS WAF

This architecture closely resembles what many enterprise backend teams deploy in production.

---

# What You'll Build

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

     ECS Task      ECS Task      ECS Task

          │

          ▼

     PostgreSQL • Redis
```

---

# Technologies Used

- Docker
- FastAPI (or Django)
- Amazon ECS Fargate
- Amazon ECR
- Application Load Balancer
- API Gateway HTTP API
- VPC Link
- Amazon RDS PostgreSQL
- Amazon ElastiCache Redis
- CloudWatch
- AWS X-Ray

---

# Project Features

The application supports:

- CRUD REST API
- JWT Authentication
- Containerized Deployment
- Auto Scaling
- Health Checks
- Database Persistence
- Redis Caching
- HTTPS
- CloudWatch Monitoring
- CI/CD Deployment

---

# Step 1 — Containerize the Application

Create a Docker image.

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]
```

Build:

```bash
docker build -t backend-api .
```

---

# Step 2 — Push Image to Amazon ECR

Create repository:

```text
backend-api
```

Push:

```bash
docker push <ecr-repository>
```

ECS will pull the image from ECR.

---

# Step 3 — Create an ECS Cluster

Choose:

```text
Amazon ECS

↓

Fargate
```

Create:

```text
Production Cluster
```

---

# Step 4 — Create Task Definition

Example configuration:

| Setting | Value |
|----------|-------|
| CPU | 0.5 vCPU |
| Memory | 1 GB |
| Port | 8000 |

Container Image:

```text
Amazon ECR
```

---

# Step 5 — Create ECS Service

Deploy:

```text
Desired Count

↓

3 Tasks
```

Distribute tasks across multiple Availability Zones.

---

# Step 6 — Configure Application Load Balancer

Listener:

```text
HTTP

↓

Port 80
```

Target Group:

```text
ECS Tasks
```

Health Check:

```text
GET /health
```

---

# Step 7 — Deploy PostgreSQL

Create:

```text
Amazon RDS

↓

PostgreSQL
```

Enable:

- Multi-AZ
- Automated Backups
- Encryption

---

# Step 8 — Deploy Redis

Create:

```text
Amazon ElastiCache

↓

Redis
```

Use Redis for:

- API Cache
- Session Storage
- Frequently Accessed Data

---

# Step 9 — Configure Security Groups

Allow:

```text
API Gateway

↓

ALB

↓

ECS

↓

PostgreSQL

↓

Redis
```

Only required ports should be open.

---

# Step 10 — Configure VPC Link

Create:

```text
API Gateway

↓

VPC Link

↓

Application Load Balancer
```

API Gateway now communicates privately with ECS.

---

# Step 11 — Create HTTP API

Integration:

```text
VPC Link

↓

ALB
```

Routes:

```text
GET /products

POST /products

PUT /products/{id}

DELETE /products/{id}
```

---

# Step 12 — Enable Cognito Authentication

Protect every route.

Flow:

```text
User

↓

Cognito

↓

JWT

↓

API Gateway

↓

ECS
```

Unauthorized requests never reach the containers.

---

# Step 13 — Configure CloudFront

Place CloudFront before API Gateway.

Benefits:

- Global Edge Locations
- Lower Latency
- HTTPS
- Caching

---

# Step 14 — Configure AWS WAF

Attach a Web ACL.

Enable:

- SQL Injection Protection
- XSS Protection
- Rate Limiting
- IP Reputation Rules

---

# Step 15 — Configure Auto Scaling

Scale ECS tasks based on:

- CPU Utilization
- Memory Utilization
- Request Count

Example:

```text
3 Tasks

↓

6 Tasks

↓

12 Tasks
```

---

# Step 16 — Enable CloudWatch

Monitor:

- ECS CPU
- ECS Memory
- Request Count
- Latency
- ALB Errors
- API Gateway Errors

Create dashboards and alarms.

---

# Step 17 — Enable Distributed Tracing

Enable:

```text
AWS X-Ray

↓

API Gateway

↓

Application

↓

Database
```

This provides end-to-end visibility.

---

# Step 18 — Configure CI/CD

Pipeline:

```text
GitHub

↓

GitHub Actions

↓

Docker Build

↓

Push to ECR

↓

Deploy ECS

↓

Health Check

↓

Production
```

Infrastructure should be managed with:

- CloudFormation
- AWS CDK
- Terraform

---

# Request Flow

```text
Client

↓

CloudFront

↓

AWS WAF

↓

API Gateway

↓

JWT Validation

↓

VPC Link

↓

ALB

↓

ECS Task

↓

Redis

↓

PostgreSQL
```

---

# High Availability

```text
Availability Zone A

↓

ECS Task

---------------------

Availability Zone B

↓

ECS Task

---------------------

Availability Zone C

↓

ECS Task
```

Traffic is distributed automatically by the ALB.

---

# Scaling Strategy

```text
Traffic Spike

↓

API Gateway

↓

ALB

↓

Auto Scaling

↓

Additional ECS Tasks
```

Containers scale independently of API Gateway.

---

# Monitoring Dashboard

Monitor:

- Request Count
- ECS CPU
- ECS Memory
- ALB Target Health
- API Latency
- Database Connections
- Redis Hit Ratio
- 4XX Errors
- 5XX Errors

---

# Logging Strategy

Collect:

- API Gateway Access Logs
- ALB Access Logs
- ECS Container Logs
- Application Logs

Store all logs in:

```text
Amazon CloudWatch Logs
```

Use structured JSON logging for easier analysis.

---

# Production Folder Structure

```text
container-api/

├── app/
│   ├── main.py
│   ├── routes/
│   ├── services/
│   ├── models/
│   └── database.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
│
├── infrastructure/
│   ├── ecs.yaml
│   ├── alb.yaml
│   ├── api-gateway.yaml
│   ├── rds.yaml
│   └── redis.yaml
│
├── .github/
│   └── workflows/
│
└── README.md
```

---

# Production Architecture

```text
                     Users

                        │

                        ▼

                  Amazon Route 53

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

            ┌───────────┼───────────┐

            ▼           ▼           ▼

        ECS Task    ECS Task    ECS Task

            │

     ┌──────┴─────────────┐

     ▼                    ▼

Redis Cache      PostgreSQL (Multi-AZ)

            │

            ▼

 CloudWatch • X-Ray • SNS
```

This architecture is commonly used for enterprise containerized APIs.

---

# Common Issues

### Containers Keep Restarting

Check:

- Application logs
- Health check endpoint
- Container port
- Environment variables

---

### ALB Returns 503

Verify:

- Target Group
- ECS Task health
- Security Groups
- Listener configuration

---

### API Gateway Returns 502

Check:

- VPC Link status
- ALB listener
- Backend application
- Container logs

---

### Database Connection Failures

Verify:

- Security Groups
- Database endpoint
- Credentials
- Connection pool configuration

---

# What You Learned

In this project, you learned how to:

- Containerize a production API using Docker.
- Store images in Amazon ECR.
- Deploy containers on Amazon ECS Fargate.
- Expose services using an Application Load Balancer.
- Connect API Gateway using VPC Link.
- Integrate PostgreSQL and Redis.
- Protect APIs using Cognito, CloudFront, and AWS WAF.
- Automate deployments with CI/CD.

---

# Common Interview Questions

### Why choose ECS over Lambda?

ECS is well suited for applications that require long-running processes, custom runtimes, predictable performance, large dependencies, or persistent connections.

---

### Why use an Application Load Balancer with ECS?

The ALB distributes traffic across ECS tasks, performs health checks, and enables high availability and horizontal scaling.

---

### Why is VPC Link required?

VPC Link provides secure, private connectivity between API Gateway and resources inside a VPC, such as an ALB.

---

### Why include Redis in this architecture?

Redis caches frequently accessed data, reducing database load and improving API response times.

---

### Why combine API Gateway with ECS?

API Gateway provides authentication, throttling, request validation, monitoring, and a consistent public API endpoint, while ECS handles scalable container execution and application hosting.

---

# Key Takeaways

- Containerized APIs provide greater flexibility for workloads that are not ideal for serverless execution.
- API Gateway, VPC Link, ALB, and ECS form a secure and scalable architecture for enterprise applications.
- Redis, PostgreSQL, Auto Scaling, CloudWatch, and X-Ray enhance performance, reliability, and observability.
- CloudFront, AWS WAF, and Cognito add global performance and layered security to internet-facing APIs.
- This architecture closely reflects how many production backend systems are deployed in enterprise AWS environments.