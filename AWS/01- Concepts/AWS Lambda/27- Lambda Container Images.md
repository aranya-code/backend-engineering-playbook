# 27- Lambda Container Images

# Introduction

AWS Lambda originally supported only ZIP package deployments. While ZIP packages are sufficient for most serverless workloads, they have limitations when applications require large dependencies, custom runtimes, native libraries, or containerized development workflows.

To address these limitations, AWS introduced **Lambda Container Images**, allowing developers to package Lambda functions as **OCI-compliant Docker images** up to **10 GB** in size.

Container images provide greater flexibility while retaining the serverless benefits of AWS Lambda.

---

# Why Container Images?

Traditional ZIP deployments work well for:

- Small applications
- Python
- Node.js
- Java
- Go

However, enterprise applications often require:

- Large machine learning libraries
- Custom operating system packages
- Native binaries
- FFmpeg
- ImageMagick
- TensorFlow
- OpenCV
- Headless Chrome

Container images solve these challenges.

---

# ZIP Deployment vs Container Images

| Feature | ZIP Package | Container Image |
|----------|-------------|-----------------|
| Maximum Size | 250 MB (unzipped) | 10 GB |
| Deployment Format | ZIP | Docker Image |
| Base Operating System | AWS Managed | Custom |
| Native Libraries | Limited | Full Support |
| Docker Workflow | No | Yes |
| Amazon ECR Required | No | Yes |

---

# High-Level Architecture

```
Developer

      │

      ▼

Docker Build

      │

      ▼

Amazon ECR

      │

      ▼

AWS Lambda

      │

      ▼

Execute Container
```

---

# Deployment Workflow

```
Write Code

↓

Dockerfile

↓

docker build

↓

docker tag

↓

Push to Amazon ECR

↓

Create Lambda Function

↓

Invoke Lambda
```

---

# Why Amazon ECR?

Lambda stores container images in **Amazon Elastic Container Registry (ECR)**.

```
Docker Image

↓

Amazon ECR

↓

Lambda Pulls Image

↓

Execution Environment
```

---

# Base Images

AWS provides official Lambda base images.

Examples:

```
Python

Node.js

Java

.NET

Go

Ruby
```

Each base image includes:

- Runtime
- Runtime Interface Client
- Lambda bootstrap process

---

# Example Architecture

```
GitHub

↓

GitHub Actions

↓

Docker Build

↓

Amazon ECR

↓

Lambda

↓

CloudWatch
```

---

# Container Lifecycle

```
Image Stored

↓

Lambda Pulls Image

↓

Initialize Runtime

↓

Execute Handler

↓

Reuse Environment
```

Warm execution environments continue to be reused just like ZIP deployments.

---

# Typical Dockerfile

Example:

```dockerfile
FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY app.py .

CMD ["app.handler"]
```

---

# Docker Build

```
docker build -t image-processor .
```

Produces a container image locally.

---

# Push to Amazon ECR

```
docker tag image-processor:latest \
123456789012.dkr.ecr.us-east-1.amazonaws.com/image-processor

docker push \
123456789012.dkr.ecr.us-east-1.amazonaws.com/image-processor
```

Lambda references the ECR image URI.

---

# Lambda Handler

The handler remains the same.

Python example:

```python
def handler(event, context):
    return {
        "statusCode": 200,
        "body": "Hello from Lambda Container!"
    }
```

Container images change the packaging method—not the Lambda programming model.

---

# Image Structure

```
Container Image

├── Runtime
├── Dependencies
├── Application Code
├── Native Libraries
├── Configuration
└── Bootstrap
```

---

# Image Size

Maximum supported image size:

```
10 GB
```

However:

Large images increase:

- Download time
- Initialization time
- Cold start latency

Smaller images are always preferred.

---

# Cold Starts

Cold starts still occur.

```
First Request

↓

Download Image

↓

Initialize Runtime

↓

Execute
```

Large container images generally produce longer cold starts than optimized ZIP deployments.

---

# Custom Runtimes

Container images allow custom runtimes.

Example:

```
Rust

Swift

PHP

Custom Linux Runtime
```

As long as the Lambda Runtime API is implemented.

---

# Native Libraries

Container images simplify using:

```
TensorFlow

OpenCV

FFmpeg

LibreOffice

Ghostscript
```

No complex Lambda Layer packaging is required.

---

# Machine Learning Example

```
API Gateway

↓

Lambda Container

↓

TensorFlow

↓

Inference

↓

Return Prediction
```

---

# Headless Browser Example

```
Lambda Container

↓

Chromium

↓

Generate PDF

↓

Upload to S3
```

Container images make packaging Chromium significantly easier.

---

# Security

Best practices:

- Use official AWS base images
- Scan images for vulnerabilities
- Keep images updated
- Remove unnecessary packages
- Avoid running as root when possible

---

# Amazon ECR Image Scanning

Amazon ECR supports automatic vulnerability scanning.

```
Image Push

↓

Security Scan

↓

Critical Vulnerability?

↓

Alert
```

---

# IAM Permissions

Lambda requires permission to pull images.

Typical permissions include:

- ecr:GetDownloadUrlForLayer
- ecr:BatchGetImage
- ecr:BatchCheckLayerAvailability

These are generally handled automatically when using Lambda with ECR in the same account.

---

# Logging

Logging works exactly the same.

```
Container

↓

stdout

↓

CloudWatch Logs
```

---

# Monitoring

Use CloudWatch metrics:

- Duration
- Errors
- Invocations
- Throttles
- Concurrent Executions

Use AWS X-Ray for tracing.

---

# Cost

Billing is unchanged.

You are charged for:

- Requests
- Execution duration
- Memory allocation

Container images do **not** incur additional Lambda execution charges.

Amazon ECR storage is billed separately.

---

# ZIP vs Container Images

Choose ZIP when:

- Small applications
- Fast deployments
- Standard runtimes
- Minimal dependencies

Choose Container Images when:

- Native binaries
- Large dependencies
- Machine learning
- Existing Docker workflows
- Custom runtimes

---

# Lambda vs ECS vs Fargate

| Feature | Lambda | Lambda Container | ECS/Fargate |
|----------|---------|------------------|-------------|
| Serverless | ✅ | ✅ | Fargate Only |
| Max Runtime | 15 Minutes | 15 Minutes | Long Running |
| Image Support | ❌ | ✅ | ✅ |
| Scaling | Automatic | Automatic | Configurable |
| Background Services | ❌ | ❌ | ✅ |

---

# Common Mistakes

## Building Large Images

Bad:

```
8 GB Image
```

Better:

```
Minimal Base Image

↓

Only Required Packages
```

---

## Installing Development Tools

Avoid shipping:

- Git
- Editors
- Build tools
- Test frameworks

Only runtime dependencies should be included.

---

## Ignoring Security Updates

Container images should be rebuilt regularly to receive updated base images and security patches.

---

## Treating Lambda Like a Traditional Container

Although packaged as Docker images, Lambda remains:

- Stateless
- Event-driven
- Ephemeral
- Limited to 15-minute execution

Container images do not change Lambda's execution model.

---

# Best Practices

✅ Use official AWS Lambda base images.

✅ Keep container images as small as possible.

✅ Use multi-stage Docker builds.

✅ Scan images for vulnerabilities.

✅ Store secrets in Secrets Manager.

✅ Push images to Amazon ECR.

✅ Rebuild images regularly for security updates.

✅ Monitor cold start performance.

---

# Real-World Architecture

```
Developers

      │

GitHub Repository

      │

GitHub Actions

      │

Docker Build

      │

Amazon ECR

      │

Lambda Container Image

      │

API Gateway

      │

CloudWatch

      │

Amazon S3 / Aurora / EventBridge
```

---

# Senior Backend Engineering Perspective

Lambda Container Images bridge the gap between traditional containerized development and serverless computing.

They are particularly valuable when applications require large dependency trees, native binaries, machine learning frameworks, or standardized Docker-based CI/CD pipelines.

However, container images should not be the default choice. For most Python, Node.js, or Go applications, ZIP deployments are simpler, smaller, and often result in lower cold start latency.

Senior engineers select the packaging format based on operational requirements rather than preference. If an application fits comfortably within ZIP deployment limits and does not require custom runtimes or native libraries, ZIP packages remain the recommended approach.

---

# Key Takeaways

- Lambda Container Images allow deployment of OCI-compliant Docker images up to **10 GB**.
- Images are stored in Amazon ECR and pulled by Lambda during initialization.
- Container images are ideal for machine learning, native binaries, custom runtimes, and Docker-based development workflows.
- Large images increase cold start latency, so minimizing image size is critical.
- Although packaged as containers, Lambda functions remain serverless, stateless, event-driven, and subject to the same execution limits as ZIP-based functions.