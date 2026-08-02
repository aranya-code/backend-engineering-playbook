# Hands-on

The **Hands-on** section is the practical culmination of the Amazon API Gateway playbook. Instead of introducing new concepts, these labs bring together everything you've learned throughout the previous sections and demonstrate how to build real-world APIs using AWS services.

Starting with a simple HTTP API, you'll progressively build more sophisticated applications by adding authentication, persistent storage, private networking, containerization, production architecture, and deployment best practices.

By the end of this section, you'll have built complete API Gateway solutions that closely resemble architectures used by modern backend engineering teams.

---

# Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - Build Your First HTTP API](./01-%20Build%20Your%20First%20HTTP%20API.md) | Create your first serverless HTTP API using API Gateway and AWS Lambda. |
| [02 - Build a CRUD REST API](./02-%20Build%20a%20CRUD%20REST%20API.md) | Build a complete CRUD API using API Gateway, Lambda, and DynamoDB. |
| [03 - Secure API with Cognito](./03-%20Secure%20API%20with%20Cognito.md) | Protect API endpoints using Amazon Cognito and JWT authentication. |
| [04 - Deploy a Private API](./04-%20Deploy%20a%20Private%20API.md) | Deploy an internal API using Private REST APIs, AWS PrivateLink, and Interface VPC Endpoints. |
| [05 - Build a Containerized API](./05-%20Build%20a%20Containerized%20API.md) | Deploy a Dockerized API using Amazon ECS Fargate, ALB, and VPC Link. |
| [06 - Production Serverless API](./06-%20Production%20Serverless%20API.md) | Build a production-ready serverless architecture using API Gateway, Lambda, Cognito, CloudFront, WAF, and DynamoDB. |
| [07 - Production Container API](./07-%20Production%20Container%20API.md) | Build a production-grade container platform using ECS, API Gateway, ALB, Redis, PostgreSQL, CloudFront, and AWS WAF. |
| [08 - End-to-End API Gateway Project](./08-%20End-to-End%20API%20Gateway%20Project.md) | Combine all concepts into a complete enterprise-style API Gateway solution. |

---

# Learning Path

```text
HTTP API

      │

      ▼

CRUD REST API

      │

      ▼

Authentication

      │

      ▼

Private Networking

      │

      ▼

Containerized API

      │

      ▼

Production Serverless

      │

      ▼

Production Containers

      │

      ▼

Enterprise Project
```

Each project builds on the previous one, gradually introducing more advanced AWS services and production engineering practices.

---

# Skills You'll Build

By completing this section, you'll learn how to:

- Build HTTP APIs using Amazon API Gateway.
- Create CRUD APIs backed by DynamoDB.
- Secure APIs using Amazon Cognito and JWT authentication.
- Deploy private APIs inside a VPC using AWS PrivateLink.
- Containerize applications using Docker and Amazon ECS.
- Integrate API Gateway with Application Load Balancers through VPC Link.
- Design production-grade serverless architectures.
- Build highly available containerized backend services.
- Implement monitoring, logging, tracing, and operational best practices.
- Apply Infrastructure as Code and CI/CD principles to API deployments.

---

# Project Progression

## Project 1

```text
API Gateway

↓

Lambda
```

Learn the fundamentals of API Gateway.

---

## Project 2

```text
API Gateway

↓

Lambda

↓

DynamoDB
```

Introduce persistent storage.

---

## Project 3

```text
Client

↓

Cognito

↓

API Gateway

↓

Lambda
```

Add authentication and authorization.

---

## Project 4

```text
EC2

↓

Private Endpoint

↓

Private API Gateway
```

Build secure internal APIs.

---

## Project 5

```text
API Gateway

↓

VPC Link

↓

ALB

↓

ECS
```

Deploy containerized workloads.

---

## Project 6

```text
CloudFront

↓

AWS WAF

↓

API Gateway

↓

Lambda

↓

DynamoDB
```

Create a production-ready serverless platform.

---

## Project 7

```text
CloudFront

↓

AWS WAF

↓

API Gateway

↓

ALB

↓

ECS

↓

PostgreSQL
```

Deploy enterprise containerized applications.

---

## Project 8

```text
CloudFront

↓

AWS WAF

↓

API Gateway

↓

Authentication

↓

Backend Services

↓

Database

↓

Monitoring

↓

CI/CD
```

Build a complete production architecture.

---

# AWS Services You'll Use

Throughout these labs you'll work with:

- Amazon API Gateway
- AWS Lambda
- Amazon Cognito
- Amazon DynamoDB
- Amazon ECS Fargate
- Amazon ECR
- Application Load Balancer
- VPC Link
- AWS PrivateLink
- Amazon CloudFront
- AWS WAF
- Amazon RDS PostgreSQL
- Amazon ElastiCache (Redis)
- Amazon CloudWatch
- AWS X-Ray
- Amazon Route 53
- AWS Secrets Manager
- GitHub Actions
- AWS CloudFormation / CDK / Terraform

---

# End-to-End Architecture

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

            Authentication & Validation

                         │

          ┌──────────────┴──────────────┐

          ▼                             ▼

      AWS Lambda                 Amazon ECS

          │                             │

          ▼                             ▼

   DynamoDB / Redis          PostgreSQL / Redis

                         │

                         ▼

      CloudWatch • X-Ray • CloudTrail
```

This architecture demonstrates how API Gateway integrates with multiple AWS services to build secure, scalable, and production-ready backend systems.

---

# Recommended Workflow

Complete the projects in order.

```text
Project 1

↓

Project 2

↓

Project 3

↓

Project 4

↓

Project 5

↓

Project 6

↓

Project 7

↓

Project 8
```

Each project introduces concepts required for the next one.

---

# Best Practices

As you complete the labs:

- Build using Infrastructure as Code whenever possible.
- Follow the principle of least privilege for IAM.
- Enable CloudWatch Logs and Metrics.
- Secure every production API using authentication.
- Validate requests before reaching backend services.
- Keep backend services stateless.
- Monitor performance and costs continuously.
- Automate deployments using CI/CD pipelines.

---

# Final Outcome

After completing this section, you'll be able to design and implement production-ready APIs using Amazon API Gateway and a wide range of AWS services.

More importantly, you'll understand **how individual AWS services work together as a complete backend platform**, giving you the practical skills expected of a senior backend engineer working with cloud-native architectures.