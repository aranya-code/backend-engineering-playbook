# CloudFormation Conditions

## What are Conditions?

Conditions allow CloudFormation to create resources or configure properties based on logical expressions.

They enable a single template to behave differently depending on:

* Environment
* Region
* Account
* User Input
* Deployment Type

Conditions are evaluated during stack creation and updates.

---

# Why Use Conditions?

Imagine you need:

```text
Development Environment
    │
    └── EC2 Only

Production Environment
    │
    ├── EC2
    ├── Load Balancer
    └── Auto Scaling Group
```

Instead of maintaining multiple templates:

```text
dev-template.yaml
qa-template.yaml
prod-template.yaml
```

you can use one template with Conditions.

---

# Conditions Section

Conditions are defined in the Conditions section.

```yaml
Conditions:

  ConditionName:
    ConditionExpression
```

Example:

```yaml
Conditions:

  IsProduction:
    !Equals [!Ref Environment, Production]
```

---

# How Conditions Work

```text
Parameter
    │
    ▼
Condition
    │
    ▼
True / False
    │
    ▼
Resource Created or Skipped
```

---

# Condition Functions

CloudFormation provides:

| Function   | Purpose           |
| ---------- | ----------------- |
| Fn::Equals | Compare values    |
| Fn::If     | Conditional logic |
| Fn::And    | Logical AND       |
| Fn::Or     | Logical OR        |
| Fn::Not    | Logical NOT       |

Short Form:

```yaml
!Equals
!If
!And
!Or
!Not
```

---

# Fn::Equals

Checks whether two values are equal.

Syntax:

```yaml
!Equals
  - Value1
  - Value2
```

Example:

```yaml
Conditions:

  IsProduction:

    !Equals
      - !Ref Environment
      - Production
```

Input:

```text
Environment = Production
```

Output:

```text
True
```

---

# Using Equals

Parameter:

```yaml
Parameters:

  Environment:

    Type: String

    AllowedValues:

      - Development
      - QA
      - Production
```

Condition:

```yaml
Conditions:

  IsProduction:

    !Equals
      - !Ref Environment
      - Production
```

---

# Applying Conditions to Resources

Use:

```yaml
Condition:
```

inside a resource.

Example:

```yaml
Resources:

  LoadBalancer:

    Type: AWS::ElasticLoadBalancingV2::LoadBalancer

    Condition: IsProduction
```

Behavior:

```text
Production
     ↓
Load Balancer Created

Development
     ↓
Load Balancer Not Created
```

---

# Fn::If

Returns one value if true and another if false.

Syntax:

```yaml
!If
  - ConditionName
  - ValueIfTrue
  - ValueIfFalse
```

---

# Example

```yaml
InstanceType:

  !If
    - IsProduction
    - t3.large
    - t2.micro
```

Result:

```text
Production  → t3.large
Development → t2.micro
```

---

# Fn::And

Returns true only if all conditions are true.

Syntax:

```yaml
!And
  - Condition1
  - Condition2
```

---

# Example

```yaml
Conditions:

  IsProd:

    !Equals
      - !Ref Environment
      - Production

  IsUSEast:

    !Equals
      - !Ref AWS::Region
      - us-east-1

  CreateSpecialResource:

    !And
      - !Condition IsProd
      - !Condition IsUSEast
```

Result:

```text
Production + us-east-1 = True
Anything Else = False
```

---

# Fn::Or

Returns true if any condition is true.

Syntax:

```yaml
!Or
  - Condition1
  - Condition2
```

---

# Example

```yaml
Conditions:

  IsDev:

    !Equals
      - !Ref Environment
      - Development

  IsQA:

    !Equals
      - !Ref Environment
      - QA

  IsNonProd:

    !Or
      - !Condition IsDev
      - !Condition IsQA
```

Result:

```text
Development = True
QA = True
Production = False
```

---

# Fn::Not

Negates a condition.

Syntax:

```yaml
!Not
  - Condition
```

---

# Example

```yaml
Conditions:

  IsDev:

    !Equals
      - !Ref Environment
      - Development

  IsNotDev:

    !Not
      - !Condition IsDev
```

Result:

```text
Development = False
Production = True
```

---

# Using Conditions with Resources

Example:

```yaml
Resources:

  AutoScalingGroup:

    Type: AWS::AutoScaling::AutoScalingGroup

    Condition: IsProduction
```

Only created when:

```text
Environment = Production
```

---

# Using Conditions with Outputs

Example:

```yaml
Outputs:

  LoadBalancerDNS:

    Condition: IsProduction

    Value: !GetAtt ALB.DNSName
```

Output appears only if condition evaluates to true.

---

# Using Conditions with Properties

Conditions can modify resource properties.

Example:

```yaml
Properties:

  InstanceType:

    !If
      - IsProduction
      - t3.large
      - t2.micro
```

---

# AWS::NoValue

Special pseudo parameter.

Used to remove properties.

---

## Example

```yaml
Properties:

  KeyName:

    !If
      - IsProduction
      - ProductionKey
      - !Ref AWS::NoValue
```

Result:

### Production

```yaml
KeyName: ProductionKey
```

### Non-Production

```yaml
KeyName removed completely
```

---

# Complete Example

```yaml
Parameters:

  Environment:

    Type: String

    AllowedValues:

      - Development
      - Production

Conditions:

  IsProduction:

    !Equals
      - !Ref Environment
      - Production

Resources:

  WebServer:

    Type: AWS::EC2::Instance

    Properties:

      ImageId: ami-12345678

      InstanceType:

        !If
          - IsProduction
          - t3.large
          - t2.micro

  ApplicationLoadBalancer:

    Type: AWS::ElasticLoadBalancingV2::LoadBalancer

    Condition: IsProduction
```

Behavior:

```text
Development
    └── EC2 Only

Production
    ├── EC2
    └── ALB
```

---

# Condition Evaluation Process

```text
Stack Creation
      │
      ▼
Read Parameters
      │
      ▼
Evaluate Conditions
      │
      ▼
Create Matching Resources
```

Conditions are evaluated before resources are created.

---

# Real-World Use Cases

## Environment-Based Deployments

```text
Dev
QA
Prod
```

Different resources per environment.

---

## Cost Optimization

Skip expensive resources:

```text
ALB
NAT Gateway
RDS Multi-AZ
```

in Development environments.

---

## Multi-Region Deployments

Create resources only in specific Regions.

Example:

```yaml
!Equals
  - !Ref AWS::Region
  - us-east-1
```

---

## Feature Toggles

Enable or disable:

```text
CloudFront
WAF
Auto Scaling
```

using Conditions.

---

# Best Practices

## Use Meaningful Names

Good:

```yaml
IsProduction
CreateALB
EnableWAF
```

Avoid:

```yaml
Cond1
TestCondition
Flag
```

---

## Keep Conditions Simple

Complex conditions are difficult to maintain.

Break them into smaller reusable conditions.

---

## Use AWS::NoValue

Cleaner than using empty strings or null values.

---

## Reuse Conditions

Define once.

Use across:

* Resources
* Properties
* Outputs

---

# Common Mistakes

## Using Fn::If Outside Supported Locations

`Fn::If` works only in:

* Metadata
* UpdatePolicy
* Resource Properties
* Outputs

---

## Deeply Nested Conditions

Bad:

```yaml
If
 └── If
      └── If
```

Difficult to troubleshoot.

---

## Hardcoding Environment Logic

Bad:

```yaml
InstanceType: t3.large
```

Use Conditions instead.

---

# Key Takeaways

* Conditions provide logical control in CloudFormation.
* Conditions evaluate to True or False.
* Main functions:

  * Fn::Equals
  * Fn::If
  * Fn::And
  * Fn::Or
  * Fn::Not
* Conditions can control:

  * Resources
  * Outputs
  * Properties
* AWS::NoValue removes properties conditionally.
* Conditions help create reusable enterprise templates.

---

# Interview Questions

### What are Conditions in CloudFormation?

Conditions allow resources and properties to be created or configured based on logical expressions.

---

### Which section defines Conditions?

```yaml
Conditions:
```

---

### What does Fn::Equals do?

Compares two values and returns:

```text
True
or
False
```

---

### What does Fn::If do?

Returns one value if the condition is true and another if false.

---

### What is AWS::NoValue?

A pseudo parameter used to remove a property from a resource definition.

---

### Can Conditions prevent a resource from being created?

Yes.

Using:

```yaml
Condition: ConditionName
```

on a resource.

---

### When are Conditions evaluated?

During stack creation and stack updates, before resources are created.
