# CloudFormation Capabilities

## What are Capabilities?

Capabilities are special acknowledgments that allow CloudFormation to create or modify certain AWS resources that may have security implications.

When a template contains sensitive resources such as IAM entities, CloudFormation requires explicit permission from the user before deployment.

This prevents accidental creation or modification of privileged resources.

---

# Why Capabilities Exist

Imagine a CloudFormation template contains:

```text
IAM Role
IAM Policy
IAM User
IAM Group
```

These resources can:

* Grant permissions
* Access AWS services
* Modify security settings
* Assume privileged roles

CloudFormation requires explicit approval before deploying them.

---

# How Capabilities Work

```text
Template
    │
    ▼
Contains IAM Resources?
    │
    ├── No
    │      ▼
    │   Deploy
    │
    └── Yes
           ▼
Capability Required
           ▼
Deploy
```

---

# Common Error

If IAM resources exist but capabilities are not specified:

```text
Requires capabilities:
[CAPABILITY_IAM]
```

Deployment fails.

---

# Available Capabilities

CloudFormation supports:

| Capability             | Purpose                    |
| ---------------------- | -------------------------- |
| CAPABILITY_IAM         | IAM resources              |
| CAPABILITY_NAMED_IAM   | Named IAM resources        |
| CAPABILITY_AUTO_EXPAND | Macros and Transformations |

---

# CAPABILITY_IAM

## What is CAPABILITY_IAM?

Allows CloudFormation to create or modify IAM resources.

Examples:

```text
IAM Role
IAM Policy
IAM Group
IAM User
```

---

## Example

```yaml
Resources:

  AppRole:

    Type: AWS::IAM::Role

    Properties:

      AssumeRolePolicyDocument:
        Version: '2012-10-17'
```

Deployment requires:

```text
CAPABILITY_IAM
```

---

# AWS CLI Example

```bash
aws cloudformation create-stack \
--stack-name demo-stack \
--template-body file://template.yaml \
--capabilities CAPABILITY_IAM
```

---

# CAPABILITY_NAMED_IAM

## What is CAPABILITY_NAMED_IAM?

Required when IAM resources contain custom names.

Example:

```yaml
Resources:

  AdminRole:

    Type: AWS::IAM::Role

    Properties:

      RoleName: ProductionAdminRole
```

Because:

```yaml
RoleName: ProductionAdminRole
```

is explicitly specified, CloudFormation requires:

```text
CAPABILITY_NAMED_IAM
```

---

# Example Error

Without capability:

```text
Requires capabilities:
[CAPABILITY_NAMED_IAM]
```

Deployment fails.

---

# CLI Example

```bash
aws cloudformation create-stack \
--stack-name prod-stack \
--template-body file://template.yaml \
--capabilities CAPABILITY_NAMED_IAM
```

---

# IAM vs Named IAM

## CAPABILITY_IAM

CloudFormation generates names automatically.

Example:

```yaml
Resources:

  DemoRole:

    Type: AWS::IAM::Role
```

Generated Name:

```text
stackname-demo-role-abc123
```

---

## CAPABILITY_NAMED_IAM

User specifies names.

Example:

```yaml
RoleName: ProductionAdminRole
```

---

# Comparison

| Feature              | CAPABILITY_IAM | CAPABILITY_NAMED_IAM |
| -------------------- | -------------- | -------------------- |
| IAM Resources        | Yes            | Yes                  |
| Custom Names         | No             | Yes                  |
| Auto Generated Names | Yes            | Yes                  |
| Explicit Role Names  | No             | Yes                  |

---

# CAPABILITY_AUTO_EXPAND

## What is CAPABILITY_AUTO_EXPAND?

Required when templates use:

```text
Macros
Transforms
AWS SAM
Custom Template Processing
```

CloudFormation expands templates before deployment.

---

# Example

```yaml
Transform: AWS::Serverless-2016-10-31
```

Requires:

```text
CAPABILITY_AUTO_EXPAND
```

---

# AWS SAM Example

```yaml
Transform: AWS::Serverless-2016-10-31

Resources:

  MyFunction:

    Type: AWS::Serverless::Function
```

Deployment:

```bash
aws cloudformation create-stack \
--stack-name sam-stack \
--template-body file://template.yaml \
--capabilities CAPABILITY_AUTO_EXPAND
```

---

# Multiple Capabilities

Templates may require multiple capabilities.

Example:

```yaml
Transform: AWS::Serverless-2016-10-31

Resources:

  AdminRole:

    Type: AWS::IAM::Role

    Properties:

      RoleName: ProductionAdminRole
```

Required:

```bash
--capabilities \
CAPABILITY_NAMED_IAM \
CAPABILITY_AUTO_EXPAND
```

---

# Console Deployment

AWS Console automatically detects capabilities.

During deployment:

```text
Create Stack
      ↓
Review
      ↓
I acknowledge that AWS CloudFormation
might create IAM resources
```

Checkbox appears.

---

# Update Stack Example

```bash
aws cloudformation update-stack \
--stack-name prod-stack \
--template-body file://template.yaml \
--capabilities CAPABILITY_NAMED_IAM
```

Capabilities must be supplied during updates as well.

---

# Change Sets and Capabilities

Creating Change Sets with IAM resources:

```bash
aws cloudformation create-change-set \
--stack-name prod-stack \
--change-set-name update-v1 \
--template-body file://template.yaml \
--capabilities CAPABILITY_NAMED_IAM
```

Capabilities are still required.

---

# Real-World Example

Template:

```yaml
Resources:

  AppRole:

    Type: AWS::IAM::Role

    Properties:

      RoleName: ProductionAppRole

  EC2Policy:

    Type: AWS::IAM::Policy
```

Deployment:

```bash
aws cloudformation create-stack \
--stack-name app-stack \
--template-body file://template.yaml \
--capabilities CAPABILITY_NAMED_IAM
```

Without the capability:

```text
Stack Creation Failed
```

---

# Security Considerations

IAM resources can:

```text
Grant Access
Modify Permissions
Access AWS Services
Assume Roles
```

Capabilities force administrators to explicitly approve such changes.

---

# Common Deployment Commands

## Create Stack

```bash
aws cloudformation create-stack \
--stack-name demo-stack \
--template-body file://template.yaml \
--capabilities CAPABILITY_IAM
```

---

## Update Stack

```bash
aws cloudformation update-stack \
--stack-name demo-stack \
--template-body file://template.yaml \
--capabilities CAPABILITY_IAM
```

---

## Create Change Set

```bash
aws cloudformation create-change-set \
--stack-name demo-stack \
--change-set-name update-v1 \
--template-body file://template.yaml \
--capabilities CAPABILITY_IAM
```

---

# Best Practices

## Use CAPABILITY_IAM When Possible

Avoid hardcoded names unless required.

---

## Use CAPABILITY_NAMED_IAM Carefully

Named IAM resources:

```text
Must Be Unique
Can Cause Naming Conflicts
```

---

## Review IAM Changes

Always inspect:

```text
Roles
Policies
Trust Relationships
```

before deployment.

---

## Combine with Change Sets

Review security changes before execution.

---

## Follow Least Privilege

CloudFormation should create only required permissions.

---

# Common Mistakes

## Forgetting Capabilities

Most common error:

```text
Requires capabilities:
[CAPABILITY_IAM]
```

---

## Using Named IAM Unnecessarily

Avoid:

```yaml
RoleName: MyRole
```

unless required.

Let CloudFormation generate names.

---

## Over-Permissioned IAM Roles

CloudFormation will create exactly what is defined.

Review policies carefully.

---

## Ignoring Macro Capabilities

SAM and Macros require:

```text
CAPABILITY_AUTO_EXPAND
```

---

# Troubleshooting

## Error

```text
Requires capabilities:
[CAPABILITY_IAM]
```

Solution:

```bash
--capabilities CAPABILITY_IAM
```

---

## Error

```text
Requires capabilities:
[CAPABILITY_NAMED_IAM]
```

Solution:

```bash
--capabilities CAPABILITY_NAMED_IAM
```

---

## Error

```text
Requires capabilities:
[CAPABILITY_AUTO_EXPAND]
```

Solution:

```bash
--capabilities CAPABILITY_AUTO_EXPAND
```

---

# Key Takeaways

* Capabilities are security acknowledgments required by CloudFormation.
* They prevent accidental creation of privileged resources.
* Main capabilities:

  * CAPABILITY_IAM
  * CAPABILITY_NAMED_IAM
  * CAPABILITY_AUTO_EXPAND
* IAM resources require explicit approval.
* Named IAM resources require CAPABILITY_NAMED_IAM.
* Macros and AWS SAM require CAPABILITY_AUTO_EXPAND.
* Capabilities must be supplied during:

  * Stack Creation
  * Stack Updates
  * Change Set Creation

---

# Interview Questions

### What are CloudFormation Capabilities?

Capabilities are explicit acknowledgments allowing CloudFormation to create or modify sensitive resources such as IAM entities.

---

### When is CAPABILITY_IAM required?

When templates contain IAM resources.

---

### When is CAPABILITY_NAMED_IAM required?

When IAM resources have explicitly defined names such as:

```yaml
RoleName: ProductionRole
```

---

### What is CAPABILITY_AUTO_EXPAND?

A capability required for Macros, Transforms, and AWS SAM templates.

---

### Can multiple capabilities be specified together?

Yes.

Example:

```bash
--capabilities \
CAPABILITY_NAMED_IAM \
CAPABILITY_AUTO_EXPAND
```

---

### Why did AWS introduce Capabilities?

To prevent accidental deployment of security-sensitive resources.

---

### Which capability is commonly required for AWS SAM?

```text
CAPABILITY_AUTO_EXPAND
```
