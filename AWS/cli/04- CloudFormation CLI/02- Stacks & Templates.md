# Stacks & Templates

> Learn how CloudFormation templates define AWS infrastructure and how stacks are created, updated, and managed using the AWS CLI. This chapter covers template structure, YAML vs JSON, Parameters, Outputs, Conditions, Mappings, intrinsic functions, and deploying your first stack.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand CloudFormation templates
- Build YAML and JSON templates
- Understand template sections
- Validate templates
- Create CloudFormation stacks
- Deploy infrastructure using AWS CLI
- Manage stack parameters
- Read stack outputs

---

# What is a CloudFormation Template?

A CloudFormation Template is a blueprint for AWS infrastructure.

Instead of manually creating resources:

```text
Create VPC

↓

Create EC2

↓

Create Security Group

↓

Create S3 Bucket
```

You define everything once:

```text
CloudFormation Template

↓

CloudFormation Stack

↓

Infrastructure Created
```

Templates are reusable and version controlled.

---

# YAML vs JSON

CloudFormation supports:

- YAML (Recommended)
- JSON

AWS recommends YAML because it is:

- Easier to read
- Less verbose
- Simpler to maintain

Example YAML:

```yaml
AWSTemplateFormatVersion: '2010-09-09'

Resources:
  MyBucket:
    Type: AWS::S3::Bucket
```

Equivalent JSON:

```json
{
    "AWSTemplateFormatVersion":"2010-09-09",
    "Resources":{
        "MyBucket":{
            "Type":"AWS::S3::Bucket"
        }
    }
}
```

Most production templates use YAML.

---

# Template Structure

A CloudFormation template contains several sections.

```text
Template
│
├── AWSTemplateFormatVersion
├── Description
├── Metadata
├── Parameters
├── Mappings
├── Conditions
├── Resources
├── Outputs
└── Rules (Optional)
```

Only the **Resources** section is mandatory.

---

# Resources Section

Resources define the AWS infrastructure.

Example:

```yaml
Resources:
  BackendBucket:
    Type: AWS::S3::Bucket
```

Every AWS resource follows this pattern.

---

# Parameters

Parameters make templates reusable.

Example:

```yaml
Parameters:

  InstanceType:

    Type: String

    Default: t3.micro
```

Instead of hardcoding values, users provide them during deployment.

---

# Deploy with Parameters

```bash
aws cloudformation create-stack \
--stack-name backend-stack \
--template-body file://template.yaml \
--parameters ParameterKey=InstanceType,ParameterValue=t3.small
```

---

# Outputs

Outputs export useful information.

Example:

```yaml
Outputs:

  BucketName:

    Value: !Ref BackendBucket
```

Outputs are commonly used for:

- Bucket Names
- EC2 Public IPs
- VPC IDs
- Security Group IDs

---

# View Stack Outputs

```bash
aws cloudformation describe-stacks \
--stack-name backend-stack
```

Outputs appear under:

```text
Outputs
```

---

# Mappings

Mappings define lookup tables.

Example:

```yaml
Mappings:

  RegionMap:

    ap-south-1:

      AMI: ami-123456

    us-east-1:

      AMI: ami-987654
```

Useful for Region-specific configurations.

---

# Conditions

Conditions determine whether resources are created.

Example:

```yaml
Conditions:

  IsProduction: !Equals [!Ref Environment, production]
```

Then:

```yaml
Condition: IsProduction
```

Only production deployments create the resource.

---

# Metadata

Metadata stores additional template information.

Example:

```yaml
Metadata:

  Author: Backend Team

  Version: 1.0
```

Metadata is ignored during deployment.

---

# Intrinsic Functions

CloudFormation provides built-in functions.

Common examples:

| Function | Purpose |
|----------|----------|
| `!Ref` | Reference another resource |
| `!GetAtt` | Get resource attribute |
| `!Sub` | String substitution |
| `!Join` | Join strings |
| `!FindInMap` | Lookup mapping |
| `!ImportValue` | Import exported value |
| `!If` | Conditional evaluation |

---

# Example: !Ref

```yaml
BucketName:

  Value: !Ref BackendBucket
```

Returns the logical resource ID or value.

---

# Example: !GetAtt

```yaml
Outputs:

  BucketArn:

    Value: !GetAtt BackendBucket.Arn
```

Returns the bucket ARN.

---

# Example: !Sub

```yaml
!Sub arn:aws:s3:::${BucketName}
```

Useful for building ARNs dynamically.

---

# Validate a Template

Always validate before deployment.

```bash
aws cloudformation validate-template \
--template-body file://template.yaml
```

Validation checks:

- YAML syntax
- JSON syntax
- Template format
- Required sections

It does **not** create resources.

---

# Create a Stack

Deploy infrastructure.

```bash
aws cloudformation create-stack \
--stack-name backend-stack \
--template-body file://template.yaml
```

CloudFormation begins creating all defined resources.

---

# Wait for Stack Creation

```bash
aws cloudformation wait stack-create-complete \
--stack-name backend-stack
```

Useful in automation and CI/CD pipelines.

---

# List Stacks

```bash
aws cloudformation list-stacks
```

---

# Describe a Stack

```bash
aws cloudformation describe-stacks \
--stack-name backend-stack
```

Returns:

- Parameters
- Outputs
- Tags
- Status
- Description

---

# List Stack Resources

```bash
aws cloudformation list-stack-resources \
--stack-name backend-stack
```

Shows every AWS resource created by the stack.

---

# Stack Creation Workflow

```text
Template

↓

Validate

↓

Create Stack

↓

Provision Resources

↓

Outputs

↓

Ready
```

---

# Common Errors

## ValidationError

Example:

```text
Template validation error
```

Run:

```bash
aws cloudformation validate-template
```

---

## AlreadyExistsException

The stack name already exists.

Use another name or delete the existing stack.

---

## InsufficientCapabilitiesException

Occurs when creating IAM resources.

Deploy using:

```bash
--capabilities CAPABILITY_NAMED_IAM
```

---

# Production Best Practices

- Prefer YAML templates.
- Keep templates modular.
- Parameterize environment-specific values.
- Validate every template before deployment.
- Store templates in Git.
- Avoid hardcoded resource names.
- Export important Outputs.
- Use descriptive logical IDs.

---

# Real-World Workflow

Deploy a new backend application.

```text
Write Template
      │
      ▼
Validate Template
      │
      ▼
Commit to Git
      │
      ▼
CI/CD Pipeline
      │
      ▼
CloudFormation
      │
      ▼
Infrastructure Created
```

---

# Architecture Note

```text
Template
      │
      ▼
CloudFormation
      │
      ▼
Stack
      │
      ├── EC2
      ├── S3
      ├── IAM
      ├── VPC
      └── RDS
```

A single template can provision an entire application infrastructure.

---

# Interview Note

### Question

**Why are CloudFormation Parameters important?**

### Answer

Parameters make CloudFormation templates reusable by allowing values such as instance types, environment names, VPC IDs, or bucket names to be supplied during deployment instead of being hardcoded. This enables the same template to be used across development, testing, staging, and production environments with different configurations.

---

# Key Takeaways

- Templates define AWS infrastructure as code.
- YAML is preferred over JSON for readability.
- Resources are the only mandatory template section.
- Parameters increase template flexibility.
- Outputs expose useful deployment information.
- Validate templates before deployment.
- Use intrinsic functions to build dynamic templates.
- Store templates in version control.

---
