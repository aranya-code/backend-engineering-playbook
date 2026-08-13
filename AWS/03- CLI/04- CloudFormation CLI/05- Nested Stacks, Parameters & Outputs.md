# Nested Stacks, Parameters & Outputs

> Learn how to build modular, reusable, and maintainable CloudFormation templates using Nested Stacks, Parameters, Outputs, Cross-Stack References, and Intrinsic Functions. These techniques are widely used in enterprise environments to organize large infrastructures and promote template reusability.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Nested Stacks
- Design reusable CloudFormation templates
- Work with Parameters
- Validate parameter input
- Export and import stack values
- Build cross-stack dependencies
- Use intrinsic functions effectively
- Design modular infrastructure

---

# Why Modular CloudFormation?

As infrastructure grows, a single CloudFormation template becomes difficult to maintain.

Instead of:

```text
One Template

↓

5000 Lines

↓

Everything Together
```

Split infrastructure into reusable components.

Example:

```text
Network Stack

↓

Security Stack

↓

Database Stack

↓

Application Stack
```

Each stack has a single responsibility.

---

# What is a Nested Stack?

A Nested Stack is a CloudFormation stack created from another CloudFormation stack.

Example:

```text
Root Stack

│

├── VPC Stack

├── IAM Stack

├── Database Stack

└── Application Stack
```

Nested Stacks improve:

- Maintainability
- Reusability
- Team collaboration
- Deployment speed

---

# Nested Stack Architecture

```text
Root Stack
      │
      ├────────────┐
      ▼            ▼
Network Stack   IAM Stack
      │            │
      ▼            ▼
Application Stack
      │
      ▼
EC2
Lambda
RDS
```

The Root Stack orchestrates child stacks.

---

# Creating a Nested Stack

Example:

```yaml
Resources:

  NetworkStack:

    Type: AWS::CloudFormation::Stack

    Properties:

      TemplateURL: https://bucket.s3.amazonaws.com/network.yaml
```

The child template must be stored in Amazon S3.

---

# Why Store Templates in S3?

CloudFormation downloads nested templates from Amazon S3.

Typical workflow:

```text
Local Template

↓

Upload to S3

↓

CloudFormation

↓

Nested Stack
```

---

# Deploy a Root Stack

```bash
aws cloudformation create-stack \
--stack-name production-stack \
--template-body file://root.yaml
```

CloudFormation automatically creates all nested stacks.

---

# Parameters

Parameters allow runtime configuration.

Example:

```yaml
Parameters:

  Environment:

    Type: String

    Default: Development
```

---

# Parameter Types

Common parameter types:

```text
String

Number

CommaDelimitedList

List<String>

AWS::EC2::KeyPair::KeyName

AWS::EC2::Subnet::Id

AWS::EC2::VPC::Id

AWS::SSM::Parameter::Value<String>
```

AWS-specific parameter types improve validation.

---

# Passing Parameters

```bash
aws cloudformation create-stack \
--stack-name backend-stack \
--template-body file://template.yaml \
--parameters \
ParameterKey=Environment,ParameterValue=Production
```

---

# Parameter Constraints

CloudFormation can validate parameter input.

Example:

```yaml
Parameters:

  Environment:

    Type: String

    AllowedValues:

      - Development

      - Testing

      - Production
```

Invalid values are rejected before deployment.

---

# Default Values

```yaml
Parameters:

  InstanceType:

    Type: String

    Default: t3.micro
```

Users may override defaults during deployment.

---

# NoEcho Parameters

Sensitive values should not appear in stack events.

Example:

```yaml
Parameters:

  DatabasePassword:

    Type: String

    NoEcho: true
```

Useful for:

- Passwords
- Tokens
- Secrets

---

# Outputs

Outputs expose values after deployment.

Example:

```yaml
Outputs:

  BucketName:

    Value: !Ref BackendBucket
```

Outputs are commonly consumed by:

- Engineers
- CI/CD pipelines
- Other CloudFormation stacks

---

# View Outputs

```bash
aws cloudformation describe-stacks \
--stack-name backend-stack
```

Outputs appear under:

```text
Outputs
```

---

# Exporting Values

Example:

```yaml
Outputs:

  VpcId:

    Value: !Ref ProductionVPC

    Export:

      Name: ProductionVpc
```

Exports can be shared across stacks.

---

# Listing Exports

```bash
aws cloudformation list-exports
```

---

# Importing Values

Example:

```yaml
SubnetId:

  Fn::ImportValue:

    ProductionSubnet
```

Or using YAML shorthand:

```yaml
SubnetId: !ImportValue ProductionSubnet
```

---

# List Imports

```bash
aws cloudformation list-imports \
--export-name ProductionVpc
```

Useful for understanding stack dependencies.

---

# Cross-Stack References

Example:

```text
Network Stack

↓

Exports VPC ID

↓

Application Stack

↓

Imports VPC ID

↓

Launch EC2
```

This enables independent stack management.

---

# Intrinsic Functions

CloudFormation includes built-in functions.

Common functions:

| Function | Purpose |
|----------|----------|
| `!Ref` | Reference a resource |
| `!Sub` | String substitution |
| `!Join` | Join strings |
| `!Split` | Split strings |
| `!Select` | Select list items |
| `!If` | Conditional logic |
| `!Equals` | Compare values |
| `!GetAtt` | Retrieve resource attributes |
| `!ImportValue` | Import exported values |
| `!FindInMap` | Lookup mapping values |

---

# Example: !Sub

```yaml
BucketArn:

  Value: !Sub arn:aws:s3:::${BackendBucket}
```

---

# Example: !Join

```yaml
!Join

- "-"

- [backend, production]
```

Produces:

```text
backend-production
```

---

# Example: !If

```yaml
!If

- IsProduction

- t3.large

- t3.micro
```

Allows environment-specific deployments.

---

# Modular Infrastructure

Recommended folder structure:

```text
CloudFormation

│

├── network.yaml

├── security.yaml

├── database.yaml

├── application.yaml

└── root.yaml
```

Each template manages one responsibility.

---

# Common Errors

## Export Name Already Exists

Example:

```text
Export with name already exists.
```

Export names must be unique within an AWS Region.

---

## ImportValue Not Found

Verify:

```bash
aws cloudformation list-exports
```

Ensure the export exists before importing it.

---

## ValidationError

Possible causes:

- Missing parameter
- Invalid parameter value
- Wrong parameter type

Run:

```bash
aws cloudformation validate-template \
--template-body file://template.yaml
```

---

# Production Best Practices

- Split large templates into Nested Stacks.
- Store nested templates in Amazon S3.
- Use Parameters instead of hardcoded values.
- Validate parameter input using constraints.
- Export only values intended for reuse.
- Use Cross-Stack References for shared infrastructure.
- Keep templates modular and version controlled.
- Use descriptive logical resource names.

---

# Real-World Workflow

Deploying a production application.

```text
Network Stack
      │
      ▼
Exports VPC
      │
      ▼
Database Stack
      │
      ▼
Exports Database Endpoint
      │
      ▼
Application Stack
      │
      ▼
Imports Both Values
      │
      ▼
Deployment Complete
```

---

# Architecture Note

```text
Root Stack
      │
      ├────────────┐
      ▼            ▼
Network       Security
      │            │
      ▼            ▼
Database    Application
      │            │
      └──────┬─────┘
             ▼
      Shared Outputs
```

Nested Stacks encourage modular architecture while Outputs and Imports enable communication between independent stacks.

---

# Interview Note

### Question

**Why would you use Nested Stacks instead of one large CloudFormation template?**

### Answer

Nested Stacks improve maintainability, reusability, and scalability by dividing infrastructure into smaller, focused templates. Teams can independently manage networking, security, databases, and applications while sharing common resources through Outputs and Imports. This modular approach reduces template complexity, simplifies updates, and enables infrastructure reuse across multiple projects and environments.

---

# Key Takeaways

- Nested Stacks enable modular Infrastructure as Code.
- Parameters make templates reusable across environments.
- Parameter constraints validate user input before deployment.
- Outputs expose deployment information for users and applications.
- Exports and Imports enable cross-stack communication.
- Intrinsic Functions make templates dynamic and reusable.
- Modular CloudFormation templates are easier to maintain, test, and scale.