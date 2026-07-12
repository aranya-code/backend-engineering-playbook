# Introduction to Lambda CLI

> Learn how to build, deploy, manage, and automate serverless applications using AWS Lambda and the AWS Command Line Interface (AWS CLI). This chapter introduces Lambda architecture, execution model, event-driven computing, and the most commonly used Lambda CLI commands.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand AWS Lambda
- Understand serverless computing
- Navigate Lambda CLI commands
- Understand Lambda execution lifecycle
- Deploy and invoke Lambda functions
- Build a foundation for serverless applications

---

# Why Learn Lambda CLI?

AWS Lambda is AWS's serverless compute service.

Instead of managing EC2 servers:

```text
Provision EC2

↓

Configure OS

↓

Install Runtime

↓

Deploy Application

↓

Maintain Servers
```

With Lambda:

```text
Upload Code

↓

Invoke Function

↓

AWS Manages Infrastructure
```

AWS automatically handles:

- Server provisioning
- Scaling
- High availability
- Runtime management
- Operating system updates

Backend Engineers, DevOps Engineers, Platform Engineers, and Cloud Engineers use Lambda extensively for modern cloud-native applications.

---

# What is Serverless Computing?

Serverless does **not** mean there are no servers.

Instead:

- AWS manages the servers.
- Developers focus only on application code.

Benefits include:

- No infrastructure management
- Automatic scaling
- Pay only for execution time
- Faster deployments
- Reduced operational overhead

---

# Common Lambda Use Cases

Lambda powers many production workloads.

Examples include:

- REST APIs
- Background jobs
- File processing
- Image resizing
- Data transformation
- Scheduled jobs
- Event processing
- ETL pipelines
- Automation scripts
- Chatbots

---

# Event-Driven Computing

Lambda is primarily event-driven.

```text
Event

↓

Lambda Function

↓

Business Logic

↓

Response
```

A function runs only when an event occurs.

---

# Common Event Sources

Lambda integrates with many AWS services.

Examples:

- API Gateway
- S3
- EventBridge
- SNS
- SQS
- DynamoDB Streams
- Kinesis
- CloudWatch Events
- CloudFormation Custom Resources

---

# Lambda Architecture

```text
Event Source
      │
      ▼
AWS Lambda
      │
      ▼
Runtime
      │
      ▼
Handler
      │
      ▼
Response
```

---

# Lambda Execution Lifecycle

Every Lambda invocation follows this lifecycle.

```text
Invoke Function

↓

Initialize Runtime

↓

Execute Handler

↓

Return Response

↓

Freeze Environment
```

If AWS reuses the execution environment, initialization is skipped.

---

# Cold Starts

The first invocation of a Lambda function requires AWS to initialize the execution environment.

```text
First Request

↓

Initialize Runtime

↓

Load Function

↓

Execute
```

This is called a **Cold Start**.

Subsequent requests may reuse the same environment.

---

# Warm Starts

```text
Request

↓

Existing Runtime

↓

Execute Immediately
```

Warm starts are significantly faster than cold starts.

---

# Lambda Components

Every Lambda function consists of:

```text
Function

│

├── Runtime

├── Handler

├── Execution Role

├── Environment Variables

├── Layers

└── Triggers
```

---

# How AWS CLI Communicates with Lambda

Lambda commands follow this pattern.

```bash
aws lambda <operation>
```

Examples:

```bash
aws lambda list-functions
```

```bash
aws lambda create-function
```

```bash
aws lambda invoke
```

```bash
aws lambda update-function-code
```

---

# List Lambda Functions

```bash
aws lambda list-functions
```

Displays all Lambda functions in the selected Region.

---

# Get Function Details

```bash
aws lambda get-function \
--function-name payment-api
```

Returns:

- Runtime
- Handler
- Role
- Timeout
- Memory
- Code location
- Last modified

---

# List Supported Runtimes

Common runtimes include:

- Python
- Node.js
- Java
- .NET
- Go
- Ruby
- Custom Runtime

Choose the runtime that best fits your application.

---

# Verify AWS Identity

Before deploying functions:

```bash
aws sts get-caller-identity
```

Always confirm the active AWS account.

---

# Global CLI Options

Examples:

```bash
aws lambda list-functions \
--profile production
```

```bash
aws lambda list-functions \
--region ap-south-1
```

```bash
aws lambda list-functions \
--output table
```

---

# Production Tip

Keep Lambda functions focused on a single responsibility.

Instead of one large function:

```text
Order Service

↓

5000 Lines
```

Prefer:

```text
Create Order

Update Inventory

Send Email

Generate Invoice
```

Small functions are easier to test, deploy, monitor, and scale.

---

# Architecture Note

```text
Client
      │
      ▼
API Gateway
      │
      ▼
Lambda
      │
      ▼
Database / S3 / SQS
```

Lambda is commonly used as the compute layer in serverless architectures.

---

# Interview Note

### Question

**What is AWS Lambda?**

### Answer

AWS Lambda is a serverless compute service that executes code in response to events without requiring developers to provision or manage servers. AWS automatically handles infrastructure management, scaling, availability, and runtime maintenance. Lambda is widely used for APIs, automation, event processing, and microservices.

---

# Key Takeaways

- Lambda is AWS's serverless compute service.
- Functions execute only when triggered by events.
- AWS manages infrastructure and scaling.
- Lambda integrates with many AWS services.
- Cold starts occur during runtime initialization.
- Small, single-purpose functions are easier to maintain and scale.