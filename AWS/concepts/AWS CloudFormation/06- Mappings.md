# CloudFormation Mappings

## What are Mappings?

Mappings are fixed lookup tables within a CloudFormation template.

They allow you to store predefined values and retrieve them dynamically during stack deployment.

Mappings are commonly used for:

* Region-specific AMIs
* Environment-specific configurations
* Instance sizing
* Account-specific values
* Static configuration data

---

# Why Use Mappings?

Without Mappings:

```yaml
ImageId: ami-0abcdef1234567890
```

Hardcoded values make templates difficult to reuse across Regions.

With Mappings:

```yaml
ImageId:
  !FindInMap
    - RegionMap
    - !Ref AWS::Region
    - AMI
```

CloudFormation automatically selects the correct AMI.

---

# Mapping Structure

Mappings are defined in the Mappings section.

```yaml
Mappings:

  MappingName:

    TopLevelKey:

      SecondLevelKey: Value
```

---

# Anatomy of a Mapping

Example:

```yaml
Mappings:

  RegionMap:

    ap-south-1:
      AMI: ami-11111111

    us-east-1:
      AMI: ami-22222222
```

Components:

| Component    | Purpose          |
| ------------ | ---------------- |
| RegionMap    | Mapping Name     |
| ap-south-1   | Top-Level Key    |
| AMI          | Second-Level Key |
| ami-11111111 | Value            |

---

# Accessing Mapping Values

CloudFormation uses:

```yaml
Fn::FindInMap
```

or

```yaml
!FindInMap
```

to retrieve values.

Syntax:

```yaml
!FindInMap
  - MappingName
  - TopLevelKey
  - SecondLevelKey
```

---

# Example 1: Region-Based AMI Lookup

Mapping:

```yaml
Mappings:

  RegionMap:

    ap-south-1:
      AMI: ami-12345678

    us-east-1:
      AMI: ami-87654321
```

Usage:

```yaml
ImageId:

  !FindInMap
    - RegionMap
    - !Ref AWS::Region
    - AMI
```

Result:

If Region:

```text
ap-south-1
```

Output:

```text
ami-12345678
```

---

# Example 2: Environment Configuration

```yaml
Mappings:

  EnvironmentConfig:

    Development:
      InstanceType: t2.micro

    QA:
      InstanceType: t3.micro

    Production:
      InstanceType: t3.large
```

Lookup:

```yaml
InstanceType:

  !FindInMap
    - EnvironmentConfig
    - Production
    - InstanceType
```

Output:

```text
t3.large
```

---

# Example 3: Multi-Value Mapping

```yaml
Mappings:

  RegionMap:

    ap-south-1:

      AMI: ami-12345678

      AZ1: ap-south-1a

      AZ2: ap-south-1b

    us-east-1:

      AMI: ami-87654321

      AZ1: us-east-1a

      AZ2: us-east-1b
```

Retrieve AMI:

```yaml
!FindInMap
  - RegionMap
  - ap-south-1
  - AMI
```

Retrieve AZ:

```yaml
!FindInMap
  - RegionMap
  - ap-south-1
  - AZ1
```

---

# Using Parameters with Mappings

Mappings are frequently combined with Parameters.

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

Mapping:

```yaml
Mappings:

  EnvironmentMap:

    Development:
      InstanceType: t2.micro

    QA:
      InstanceType: t3.micro

    Production:
      InstanceType: t3.large
```

Usage:

```yaml
InstanceType:

  !FindInMap
    - EnvironmentMap
    - !Ref Environment
    - InstanceType
```

---

# Complete Example

```yaml
AWSTemplateFormatVersion: '2010-09-09'

Parameters:

  Environment:

    Type: String

    AllowedValues:

      - Development
      - Production

Mappings:

  EnvironmentMap:

    Development:
      InstanceType: t2.micro

    Production:
      InstanceType: t3.large

Resources:

  WebServer:

    Type: AWS::EC2::Instance

    Properties:

      ImageId: ami-12345678

      InstanceType:

        !FindInMap
          - EnvironmentMap
          - !Ref Environment
          - InstanceType
```

---

# Mapping Lookup Flow

```text
Parameter Value
      │
      ▼
 Mapping
      │
      ▼
 FindInMap
      │
      ▼
 Resource Property
```

---

# Real-World Use Case

## Multi-Region Deployment

Template deployed in:

```text
ap-south-1
```

should use:

```text
ami-11111111
```

Template deployed in:

```text
us-east-1
```

should use:

```text
ami-22222222
```

Mappings make this possible without modifying the template.

---

# Mappings vs Parameters

| Feature                | Parameters | Mappings |
| ---------------------- | ---------- | -------- |
| User Input             | Yes        | No       |
| Static Values          | No         | Yes      |
| Dynamic Selection      | Yes        | Yes      |
| Defined by User        | Yes        | No       |
| Good for Lookup Tables | No         | Yes      |

---

# Mappings vs Conditions

| Feature                    | Mappings | Conditions |
| -------------------------- | -------- | ---------- |
| Stores Values              | Yes      | No         |
| Controls Resource Creation | No       | Yes        |
| Lookup Function            | Yes      | No         |
| Conditional Logic          | No       | Yes        |

---

# Nested Mapping Example

```yaml
Mappings:

  Config:

    Production:

      Web:

        InstanceType: t3.large
```

Not Supported.

CloudFormation supports only:

```text
Two-Level Mapping Structure
```

Valid:

```yaml
Mapping
 ├── Key1
 │    └── Value
```

Invalid:

```yaml
Mapping
 ├── Key1
 │    ├── Key2
 │    │    └── Value
```

---

# Best Practices

## Use Mappings for Static Data

Good examples:

* AMI IDs
* Region Values
* Environment Settings

---

## Do Not Use Mappings for User Input

Use Parameters instead.

Bad:

```yaml
Mappings:
```

to store user choices.

Use:

```yaml
Parameters:
```

instead.

---

## Combine Mappings with Parameters

Most common enterprise pattern.

```text
Parameter
     ↓
Mapping
     ↓
Resource
```

---

## Name Mappings Clearly

Good:

```yaml
RegionMap
EnvironmentMap
InstanceTypeMap
```

Avoid:

```yaml
Map1
Config
Values
```

---

# Common Mistakes

## Hardcoding Region Values

Bad:

```yaml
ImageId: ami-12345678
```

Use:

```yaml
!FindInMap
```

instead.

---

## Using Mappings for Secrets

Never store:

* Passwords
* Tokens
* Secrets

inside Mappings.

Use:

* AWS Secrets Manager
* AWS Systems Manager Parameter Store

---

## Overusing Mappings

Large mappings become difficult to maintain.

Consider:

* Parameters
* SSM Parameter Store
* Nested Stacks

for large environments.

---

# Key Takeaways

* Mappings are static lookup tables.
* Used to store predefined values.
* Accessed using `Fn::FindInMap` or `!FindInMap`.
* Commonly used for:

  * AMIs
  * Regions
  * Environment Configurations
* Mappings are not user inputs.
* Often combined with Parameters and Pseudo Parameters.
* Support only a two-level hierarchy.

---

# Interview Questions

### What are Mappings in CloudFormation?

Mappings are static lookup tables used to store predefined values.

---

### How do you access a Mapping value?

Using:

```yaml
!FindInMap
```

or

```yaml
Fn::FindInMap
```

---

### What is the most common use case for Mappings?

Region-specific AMI selection.

---

### What is the difference between Parameters and Mappings?

| Parameters                | Mappings            |
| ------------------------- | ------------------- |
| User Input                | Static Values       |
| Dynamic                   | Predefined          |
| Entered During Deployment | Defined in Template |

---

### Can Mappings be modified during stack creation?

No.

Mappings are fixed values defined inside the template.

---

### How many levels does a Mapping support?

Two levels:

```yaml
MappingName
  TopLevelKey
    SecondLevelKey
```

---

### Can Mappings store passwords?

No.

Use AWS Secrets Manager or Parameter Store for sensitive information.
