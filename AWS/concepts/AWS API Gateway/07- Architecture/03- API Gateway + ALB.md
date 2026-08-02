# API Gateway + Application Load Balancer (ALB)

## Overview

Amazon API Gateway and **Application Load Balancer (ALB)** are frequently used together to expose web applications and microservices securely.

In this architecture:

- API Gateway acts as the public API endpoint.
- API Gateway handles API management.
- ALB distributes traffic across backend services.
- Backend applications process business logic.

This pattern is commonly used when applications run on:

- Amazon ECS
- Amazon EKS
- Amazon EC2
- Kubernetes
- On-premises applications connected through hybrid networking

Unlike Lambda integrations, ALB is designed to distribute traffic across multiple long-running application instances.

---

# Why API Gateway + ALB?

Without API Gateway:

```text
Client

↓

Application Load Balancer

↓

Backend Services
```

Problems:

- Authentication implemented by application
- No API Keys
- No Usage Plans
- No request validation
- No API management
- Public ALB exposure

With API Gateway:

```text
Client

↓

API Gateway

↓

VPC Link

↓

Application Load Balancer

↓

Backend Services
```

Benefits:

- Authentication
- Authorization
- Request validation
- Rate limiting
- Monitoring
- Custom domains
- API versioning

---

# High-Level Architecture

```text
                 Client

                    │

                    ▼

           Amazon API Gateway

                    │

                VPC Link

                    │

                    ▼

      Internal Application Load Balancer

                    │

         ┌──────────┼──────────┐

         ▼          ▼          ▼

     Service A  Service B  Service C
```

API Gateway exposes the API while ALB distributes requests across backend services.

---

# Request Flow

```text
Client

↓

HTTPS Request

↓

API Gateway

↓

Authentication

↓

Request Validation

↓

VPC Link

↓

Application Load Balancer

↓

Target Group

↓

Backend

↓

Response

↓

API Gateway

↓

Client
```

---

# Why Use an ALB?

Application Load Balancer provides:

- Layer 7 load balancing
- HTTP/HTTPS routing
- Host-based routing
- Path-based routing
- Health checks
- SSL termination
- Sticky sessions (if required)

It efficiently distributes requests among backend targets.

---

# Target Groups

ALB forwards requests to Target Groups.

Example:

```text
ALB

│

├── Users Target Group

├── Orders Target Group

└── Payments Target Group
```

Each Target Group can contain multiple backend instances.

---

# Health Checks

ALB continuously monitors backend health.

```text
ALB

↓

Health Check

↓

Healthy

↓

Receive Traffic
```

If an instance becomes unhealthy:

```text
Health Check Failed

↓

Removed from Rotation
```

Traffic is automatically redirected to healthy instances.

---

# Path-Based Routing

ALB can route requests using URL paths.

Example:

```text
/users/*

↓

User Service

-------------------

/orders/*

↓

Order Service

-------------------

/payments/*

↓

Payment Service
```

Useful for microservice architectures.

---

# Host-Based Routing

ALB can also route using hostnames.

Example:

```text
users.company.com

↓

Users Service

---------------------

payments.company.com

↓

Payment Service
```

---

# API Gateway vs ALB Responsibilities

| API Gateway | Application Load Balancer |
|-------------|--------------------------|
| Authentication | Load Balancing |
| Authorization | Health Checks |
| API Keys | SSL Termination |
| Usage Plans | Target Routing |
| Request Validation | Backend Distribution |
| Throttling | Session Affinity |
| Monitoring | Target Health |

Each service has a distinct role.

---

# Authentication Flow

```text
Client

↓

JWT Token

↓

API Gateway

↓

Validation

↓

ALB

↓

Backend
```

Backend services receive only authenticated requests.

---

# Request Validation

API Gateway validates requests before forwarding them.

Example:

```json
{
    "email":"john@example.com"
}
```

Invalid request:

```http
400 Bad Request
```

The ALB and backend are never reached.

---

# Scaling

```text
Traffic

↓

API Gateway

↓

ALB

↓

Auto Scaling Group

↓

EC2 Instances
```

or

```text
Traffic

↓

API Gateway

↓

ALB

↓

Amazon ECS
```

ALB automatically distributes requests across healthy targets.

---

# High Availability

```text
API Gateway

↓

Internal ALB

↓

AZ-1

↓

Backend

--------------------

AZ-2

↓

Backend
```

ALB distributes traffic across Availability Zones.

---

# Security

Production architecture:

```text
Internet

↓

API Gateway

↓

VPC Link

↓

Private ALB

↓

Private Backend
```

The ALB remains private inside the VPC.

---

# Monitoring

Monitor:

API Gateway:

- Request Count
- Latency
- 4XX Errors
- 5XX Errors

ALB:

- Healthy Hosts
- Unhealthy Hosts
- Request Count
- Target Response Time
- HTTP Error Codes

Backend:

- CPU
- Memory
- Application Metrics

---

# Logging

Logs are available from:

```text
API Gateway

↓

CloudWatch Logs

------------------

ALB Access Logs

↓

Amazon S3

------------------

Application Logs

↓

CloudWatch Logs
```

Together they provide complete request tracing.

---

# Common Use Cases

API Gateway + ALB is commonly used for:

- Django applications
- Spring Boot APIs
- ASP.NET applications
- Java microservices
- Kubernetes services
- Legacy enterprise applications
- Multi-service architectures

---

# Advantages

- Mature Layer 7 load balancing
- Advanced routing capabilities
- Automatic health checks
- Independent backend scaling
- Supports any programming language
- Integrates with ECS, EC2, and EKS
- Simplifies backend traffic distribution

---

# Limitations

- Additional networking complexity
- Requires VPC Link
- Higher operational cost than direct Lambda integration
- ALB management required
- Does not replace API Gateway's API management capabilities

---

# Production Architecture

```text
                     Client

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

        Internal Application Load Balancer

                        │

          ┌─────────────┼─────────────┐

          ▼             ▼             ▼

      EC2 App      ECS Service      EKS Pods

                        │

                        ▼

             PostgreSQL • Redis
```

This architecture is widely used for enterprise applications.

---

# API Gateway vs ALB

| Feature | API Gateway | ALB |
|----------|-------------|-----|
| API Management | ✅ | ❌ |
| Authentication | ✅ | Limited |
| API Keys | ✅ | ❌ |
| Usage Plans | ✅ | ❌ |
| Request Validation | ✅ | ❌ |
| Throttling | ✅ | ❌ |
| Load Balancing | ❌ | ✅ |
| Health Checks | ❌ | ✅ |
| Path Routing | Basic | Advanced |
| Host Routing | Limited | Advanced |

API Gateway manages APIs, while ALB manages traffic distribution.

---

# Best Practices

- Keep the ALB private and expose only API Gateway publicly.
- Use VPC Link for secure communication between API Gateway and ALB.
- Configure health checks for all target groups.
- Separate services into dedicated target groups.
- Enable CloudWatch monitoring and ALB access logs.
- Scale backend services independently of API Gateway.
- Use Auto Scaling Groups or ECS Service Auto Scaling.
- Implement authentication and request validation in API Gateway rather than in backend applications whenever possible.

---

# Common Interview Questions

### Why use API Gateway with an ALB?

API Gateway provides API management capabilities such as authentication, authorization, request validation, throttling, and monitoring, while ALB focuses on Layer 7 load balancing and traffic distribution.

---

### Why should the ALB be private?

A private ALB prevents direct internet access to backend services. API Gateway becomes the single public entry point, improving security and simplifying API management.

---

### What is the difference between API Gateway routing and ALB routing?

API Gateway routes requests to backend integrations, while ALB distributes requests among healthy backend targets using host-based and path-based routing.

---

### Can API Gateway replace an ALB?

No.

API Gateway is an API management service, whereas ALB is a Layer 7 load balancer. They solve different problems and are often used together.

---

### When is API Gateway + ALB a better choice than API Gateway + Lambda?

When applications require long-running processes, containerized workloads, traditional web servers, or multiple backend instances running on ECS, EC2, or Kubernetes.

---

# Key Takeaways

- API Gateway and Application Load Balancer complement each other in production architectures.
- API Gateway provides authentication, authorization, request validation, throttling, monitoring, and API management.
- ALB distributes traffic across healthy backend services using advanced Layer 7 routing capabilities.
- Keeping the ALB private behind a VPC Link improves security while allowing API Gateway to remain the single public entry point.
- This architecture is widely adopted for enterprise applications running on Amazon ECS, EC2, EKS, and other containerized platforms.