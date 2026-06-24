# AWS CloudFormation

## What is AWS CloudFormation?

AWS CloudFormation is an **Infrastructure as Code (IaC)** service that allows you to model, provision, and manage AWS resources using code.

Instead of manually creating AWS resources through the AWS Management Console, CloudFormation enables you to define your infrastructure in a template file (YAML or JSON) and deploy it automatically.

---

## Why CloudFormation?

Imagine you need to create:

* VPC
* Subnets
* Route Tables
* Internet Gateway
* Security Groups
* EC2 Instances
* Load Balancers
* RDS Databases

Creating these resources manually is:

* Time-consuming
* Error-prone
* Difficult to reproduce
* Hard to manage across environments

CloudFormation solves these problems through Infrastructure as Code.

---

# Infrastructure as Code (IaC)

Infrastructure as Code means managing infrastructure using code rather than manual configuration.

Instead of:

```text
AWS Console → Click → Configure → Save
```

You write:

```yaml
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
```

CloudFormation creates the resource automatically.

---

# How CloudFormation Works

```text
CloudFormation Template
           │
           ▼
     CloudFormation Stack
           │
           ▼
    AWS Resources Created
```

Example:

```text
Template
   │
   ▼
Stack
   │
   ├── VPC
   ├── EC2
   ├── RDS
   ├── S3
   └── IAM
```

---

# Core Concepts

## Template

A template is a YAML or JSON file that describes the infrastructure.

Example:

```yaml
Resources:
  DemoBucket:
    Type: AWS::S3::Bucket
```

---

## Stack

A Stack is a collection of AWS resources managed as a single unit.

Example:

```text
Production Stack

├── VPC
├── EC2
├── RDS
└── ALB
```

CloudFormation creates, updates, and deletes resources together through stacks.

---

## Resources

Resources are the AWS services that CloudFormation creates.

Examples:

| Resource | Type                 |
| -------- | -------------------- |
| EC2      | AWS::EC2::Instance   |
| S3       | AWS::S3::Bucket      |
| RDS      | AWS::RDS::DBInstance |
| IAM Role | AWS::IAM::Role       |
| VPC      | AWS::EC2::VPC        |

---

# Benefits of CloudFormation

## 1. Infrastructure as Code

Infrastructure becomes version-controlled code.

```text
Git Repository
      │
      ▼
CloudFormation Templates
```

Benefits:

* Track changes
* Review changes
* Rollback easily

---

## 2. Automation

CloudFormation automatically provisions resources.

Example:

```text
Create VPC
     ↓
Create Subnet
     ↓
Create Route Table
     ↓
Create EC2
```

No manual intervention required.

---

## 3. Consistency

Deploy the same infrastructure across multiple environments.

```text
Development
     │
QA
     │
Production
```

All environments remain identical.

---

## 4. Repeatability

Templates can be reused multiple times.

```text
Create Stack
Delete Stack
Create Again
```

The infrastructure remains the same every time.

---

## 5. Productivity

Engineers spend less time configuring infrastructure manually.

Benefits:

* Faster deployments
* Reduced errors
* Standardized environments

---

## 6. Separation of Concerns

Application developers focus on:

* Code
* APIs
* Business logic

Infrastructure teams focus on:

* Networking
* Security
* Deployment

CloudFormation acts as the bridge between both teams.

---

# Supported Template Formats

CloudFormation supports:

## YAML (Recommended)

```yaml
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
```

Advantages:

* Cleaner syntax
* Easier to read
* Supports comments

---

## JSON

```json
{
  "Resources": {
    "MyBucket": {
      "Type": "AWS::S3::Bucket"
    }
  }
}
```

Less readable compared to YAML.

---

# CloudFormation Lifecycle

## Create Stack

```text
Template
   ↓
Create Stack
   ↓
Resources Created
```

---

## Update Stack

```text
Modify Template
        ↓
Update Stack
        ↓
Resources Updated
```

---

## Delete Stack

```text
Delete Stack
       ↓
Resources Deleted
```

---

# Real-World Example

Suppose your application requires:

* 1 VPC
* 2 Public Subnets
* 2 Private Subnets
* Application Load Balancer
* 2 EC2 Instances
* RDS Database

Without CloudFormation:

```text
Console Clicks
Configuration
Manual Validation
Manual Dependency Handling
```

With CloudFormation:

```bash
aws cloudformation create-stack \
--stack-name production-stack \
--template-body file://template.yaml
```

Entire infrastructure is deployed automatically.

---

# CloudFormation vs Manual Deployment

| Feature         | Manual | CloudFormation |
| --------------- | ------ | -------------- |
| Repeatable      | ❌      | ✅              |
| Version Control | ❌      | ✅              |
| Automation      | ❌      | ✅              |
| Rollback        | ❌      | ✅              |
| Reusability     | ❌      | ✅              |
| Consistency     | ❌      | ✅              |

---

# Common Use Cases

## Environment Provisioning

Create:

* Development
* QA
* UAT
* Production

Environments quickly.

---

## Disaster Recovery

Recreate infrastructure from templates.

---

## Multi-Region Deployments

Deploy the same architecture across regions.

---

## CI/CD Integration

CloudFormation integrates with:

* AWS CodePipeline
* AWS CodeBuild
* GitHub Actions
* Jenkins
* GitLab CI/CD

---

# Key Takeaways

* AWS CloudFormation is AWS's Infrastructure as Code service.
* Infrastructure is defined using YAML or JSON templates.
* Templates create AWS resources automatically.
* Resources are managed through Stacks.
* Supports automation, consistency, repeatability, and version control.
* Eliminates manual infrastructure provisioning.
* Widely used in DevOps, Platform Engineering, and Cloud Architecture.

---

# Interview Questions

### What is AWS CloudFormation?

AWS CloudFormation is an Infrastructure as Code service that allows users to define and provision AWS infrastructure using YAML or JSON templates.

### What is a CloudFormation Stack?

A Stack is a collection of AWS resources managed as a single unit by CloudFormation.

### What are the major benefits of CloudFormation?

* Infrastructure as Code
* Automation
* Consistency
* Repeatability
* Version Control
* Rollback Support

### Which template formats are supported?

* YAML
* JSON

(YAML is generally preferred.)

### What is the difference between a Template and a Stack?

| Template       | Stack                  |
| -------------- | ---------------------- |
| Blueprint      | Running Infrastructure |
| YAML/JSON File | AWS Deployment         |
| Definition     | Actual Resources       |
