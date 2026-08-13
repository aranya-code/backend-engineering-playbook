# CloudFormation Service Role

## What is a CloudFormation Service Role?

A CloudFormation Service Role is an IAM Role that CloudFormation assumes when creating, updating, or deleting resources on your behalf.

Instead of using the permissions of the user who launches the stack, CloudFormation uses the permissions attached to the Service Role.

---

# Why Do We Need a Service Role?

By default:

```text
User
  │
  ▼
CloudFormation
  │
  ▼
AWS Resources
```

CloudFormation uses the permissions of the user.

Problems:

* Different users have different permissions
* Deployment inconsistency
* Security risks
* Difficult auditing

---

# With a Service Role

```text
User
  │
  ▼
CloudFormation
  │
Assume Role
  │
  ▼
Service Role
  │
  ▼
AWS Resources
```

Now deployments use a consistent permission set.

---

# How Service Roles Work

During stack creation:

```text
Create Stack
      │
      ▼
CloudFormation
      │
      ▼
Assume Service Role
      │
      ▼
Execute AWS API Calls
```

Example:

```text
Create EC2
Create RDS
Create S3
Create IAM Roles
```

using the Service Role permissions.

---

# Benefits of Service Roles

## Consistent Permissions

Every deployment uses the same IAM Role.

---

## Improved Security

Users do not need elevated permissions.

---

## Least Privilege

CloudFormation receives only required permissions.

---

## Better Auditing

CloudTrail records:

```text
CloudFormation
    ↓
Service Role
    ↓
AWS API Calls
```

---

## Delegated Administration

Developers can deploy infrastructure without full AWS access.

---

# Architecture

```text
Developer
     │
     ▼
CloudFormation Stack
     │
AssumeRole
     │
     ▼
CloudFormation Service Role
     │
     ▼
AWS Resources
```

---

# Creating a Service Role

## Trust Policy

CloudFormation must be allowed to assume the role.

Example:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudformation.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

---

# Permissions Policy

Grant required permissions.

Example:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "s3:*",
        "rds:*"
      ],
      "Resource": "*"
    }
  ]
}
```

---

# Example Service Role

```text
CloudFormationServiceRole

Permissions:

✓ EC2
✓ S3
✓ RDS
✓ ELB
✓ CloudWatch
```

CloudFormation can create these resources.

---

# Using Service Role in AWS Console

During stack creation:

```text
Create Stack
      ↓
Advanced Options
      ↓
IAM Role
      ↓
Select Service Role
```

CloudFormation uses the selected role.

---

# Using Service Role via AWS CLI

Create Stack:

```bash
aws cloudformation create-stack \
--stack-name production-stack \
--template-body file://template.yaml \
--role-arn arn:aws:iam::123456789012:role/CloudFormationServiceRole
```

---

# Update Stack

```bash
aws cloudformation update-stack \
--stack-name production-stack \
--template-body file://template.yaml \
--role-arn arn:aws:iam::123456789012:role/CloudFormationServiceRole
```

---

# Service Role vs User Permissions

## Without Service Role

```text
Developer Permissions
        │
        ▼
CloudFormation Permissions
```

If developer lacks permission:

```text
Deployment Fails
```

---

## With Service Role

```text
Developer
      │
Create Stack
      │
      ▼
CloudFormation
      │
      ▼
Service Role Permissions
```

Deployment succeeds.

---

# Example Scenario

Developer Permissions:

```text
Read Only
```

Service Role Permissions:

```text
EC2 Full Access
S3 Full Access
RDS Full Access
```

Developer can deploy stacks because CloudFormation assumes the Service Role.

---

# Service Role Lifecycle

```text
Create Stack
      │
      ▼
Assume Service Role
      │
      ▼
Create Resources
      │
      ▼
Release Role
```

Role is used only during stack operations.

---

# Common Permissions

## EC2

```json
"ec2:*"
```

---

## S3

```json
"s3:*"
```

---

## RDS

```json
"rds:*"
```

---

## IAM

```json
"iam:*"
```

Required if CloudFormation creates IAM resources.

---

## Lambda

```json
"lambda:*"
```

---

## CloudWatch

```json
"cloudwatch:*"
```

---

# Service Role and IAM Capabilities

Example:

Template creates:

```text
IAM Role
IAM Policy
```

Requirements:

```text
CAPABILITY_IAM
```

and

```text
iam:* permissions
```

inside the Service Role.

Both are required.

---

# CloudTrail Example

Without Service Role:

```text
Developer
   ↓
Create EC2
```

CloudTrail shows:

```text
Developer User
```

---

With Service Role:

```text
Developer
    ↓
CloudFormation
    ↓
Service Role
```

CloudTrail shows:

```text
Assumed Role
CloudFormationServiceRole
```

Better auditing.

---

# Service Role vs Execution Role

Many engineers confuse these.

---

## CloudFormation Service Role

Used by:

```text
CloudFormation
```

Purpose:

```text
Create Infrastructure
```

---

## Lambda Execution Role

Used by:

```text
Lambda Function
```

Purpose:

```text
Run Application Code
```

---

# Comparison

| Feature    | Service Role           | Execution Role |
| ---------- | ---------------------- | -------------- |
| Used By    | CloudFormation         | Lambda         |
| Purpose    | Deploy Resources       | Run Code       |
| Assumed By | CloudFormation Service | Lambda Service |

---

# Real-World Enterprise Pattern

```text
Developers
      │
      ▼
CloudFormation
      │
      ▼
Deployment Role
      │
      ▼
AWS Infrastructure
```

Benefits:

* Security
* Standardization
* Governance
* Compliance

---

# Best Practices

## Use Service Roles for Production

Avoid direct user permissions.

---

## Follow Least Privilege

Grant only required permissions.

Bad:

```json
"*"
```

Good:

```json
"ec2:*"
"s3:*"
```

only if needed.

---

## Separate Roles by Environment

Example:

```text
DevCloudFormationRole
QACloudFormationRole
ProdCloudFormationRole
```

---

## Monitor with CloudTrail

Track infrastructure changes.

---

## Avoid AdministratorAccess

Use granular permissions.

---

# Common Mistakes

## No Trust Policy

CloudFormation cannot assume the role.

Error:

```text
Access Denied
```

---

## Missing Permissions

Role exists but lacks permissions.

Example:

```text
ec2:RunInstances denied
```

---

## Using User Permissions Instead

Creates inconsistent deployments.

---

## Excessive Permissions

Security risk.

---

# Troubleshooting

## Error

```text
AccessDenied
```

Check:

```text
Trust Policy
IAM Permissions
Role ARN
```

---

## Error

```text
CloudFormation cannot assume role
```

Verify:

```json
"Service":
"cloudformation.amazonaws.com"
```

exists in Trust Policy.

---

## Error

```text
UnauthorizedOperation
```

Role lacks required permissions.

---

# Key Takeaways

* A Service Role is an IAM Role assumed by CloudFormation.
* Provides consistent deployment permissions.
* Improves security and auditing.
* Uses:

  * Trust Policy
  * Permissions Policy
* Specified using:

  * AWS Console
  * `--role-arn`
* Recommended for production environments.
* Supports least privilege and governance models.

---

# Interview Questions

### What is a CloudFormation Service Role?

An IAM Role that CloudFormation assumes to create, update, and delete AWS resources.

---

### Why use a Service Role?

To provide consistent permissions and improve security.

---

### Who assumes the Service Role?

```text
CloudFormation Service
```

---

### What must exist in the Trust Policy?

```json
"Service":
"cloudformation.amazonaws.com"
```

---

### How do you specify a Service Role?

```bash
--role-arn
```

during stack creation or update.

---

### What happens if the Service Role lacks permissions?

CloudFormation operations fail with authorization errors.

---

### Should production stacks use Service Roles?

Yes.

It is considered a CloudFormation and AWS security best practice.
