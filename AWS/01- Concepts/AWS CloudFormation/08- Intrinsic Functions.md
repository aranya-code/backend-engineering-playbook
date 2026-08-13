# CloudFormation Intrinsic Functions

## What are Intrinsic Functions?

Intrinsic Functions are built-in CloudFormation functions that help dynamically generate values, reference resources, perform lookups, manipulate strings, and build complex configurations.

Without Intrinsic Functions, templates would contain hardcoded values and would be difficult to reuse.

---

# Why Intrinsic Functions?

Example:

Without Function:

```yaml
BucketName: my-production-bucket
```

Hardcoded.

With Function:

```yaml
BucketName: !Sub ${AWS::StackName}-bucket
```

Dynamic.

Result:

```text
production-stack-bucket
```

---

# Common Intrinsic Functions

| Function        | Short Form   | Purpose                        |
| --------------- | ------------ | ------------------------------ |
| Ref             | !Ref         | Reference Parameters/Resources |
| Fn::GetAtt      | !GetAtt      | Get Resource Attributes        |
| Fn::Sub         | !Sub         | String Substitution            |
| Fn::Join        | !Join        | Join Strings                   |
| Fn::Split       | !Split       | Split Strings                  |
| Fn::Select      | !Select      | Select List Values             |
| Fn::Base64      | !Base64      | Encode Data                    |
| Fn::FindInMap   | !FindInMap   | Mapping Lookup                 |
| Fn::ImportValue | !ImportValue | Cross-Stack References         |
| Fn::If          | !If          | Conditional Values             |

---

# Ref

## What is Ref?

Returns:

* Parameter Value
* Resource Identifier

Most frequently used intrinsic function.

---

## Syntax

```yaml
!Ref LogicalName
```

---

## Parameter Example

```yaml
Parameters:

  Environment:
    Type: String
```

Usage:

```yaml
BucketName:
  !Ref Environment
```

Input:

```text
Production
```

Output:

```text
Production
```

---

## Resource Example

```yaml
Resources:

  MyBucket:
    Type: AWS::S3::Bucket
```

Usage:

```yaml
Outputs:

  BucketName:
    Value: !Ref MyBucket
```

Output:

```text
bucket-name
```

---

# Fn::GetAtt

## What is GetAtt?

Retrieves resource attributes.

Examples:

* ARN
* DNS Name
* Endpoint
* Availability Zone

---

## Syntax

```yaml
!GetAtt Resource.Attribute
```

or

```yaml
Fn::GetAtt:
  - Resource
  - Attribute
```

---

## Example

```yaml
Outputs:

  BucketArn:
    Value: !GetAtt MyBucket.Arn
```

Output:

```text
arn:aws:s3:::my-bucket
```

---

## EC2 Example

```yaml
Outputs:

  PublicIP:
    Value: !GetAtt WebServer.PublicIp
```

Output:

```text
52.66.10.25
```

---

# Fn::Sub

## What is Sub?

Performs string substitution.

Most commonly used function in production templates.

---

## Syntax

```yaml
!Sub String
```

---

## Example

```yaml
!Sub ${AWS::StackName}-bucket
```

Output:

```text
production-stack-bucket
```

---

## Multiple Variables

```yaml
!Sub arn:aws:s3:::${BucketName}
```

---

## IAM ARN Example

```yaml
!Sub arn:aws:iam::${AWS::AccountId}:role/AdminRole
```

Output:

```text
arn:aws:iam::123456789012:role/AdminRole
```

---

# Fn::Join

## What is Join?

Combines multiple strings.

---

## Syntax

```yaml
!Join
  - Delimiter
  - ListOfValues
```

---

## Example

```yaml
!Join
  - "-"
  - - app
    - production
    - bucket
```

Output:

```text
app-production-bucket
```

---

## ARN Example

```yaml
!Join
  - ""
  - - arn:aws:s3:::
    - !Ref BucketName
```

---

# Fn::Split

## What is Split?

Splits a string into a list.

---

## Syntax

```yaml
!Split
  - Delimiter
  - String
```

---

## Example

```yaml
!Split
  - ","
  - subnet-1,subnet-2,subnet-3
```

Output:

```yaml
- subnet-1
- subnet-2
- subnet-3
```

---

# Fn::Select

## What is Select?

Returns a specific item from a list.

---

## Syntax

```yaml
!Select
  - Index
  - List
```

---

## Example

```yaml
!Select
  - 0
  - !Ref SubnetIds
```

Input:

```yaml
subnet-1
subnet-2
subnet-3
```

Output:

```text
subnet-1
```

---

## Common Pattern

```yaml
!Select
  - 0
  - !GetAZs ''
```

Returns:

```text
ap-south-1a
```

---

# Fn::Base64

## What is Base64?

Encodes data into Base64 format.

Frequently used for EC2 User Data.

---

## Syntax

```yaml
!Base64 String
```

---

## Example

```yaml
UserData:

  !Base64 |
    #!/bin/bash
    yum update -y
```

CloudFormation automatically encodes the script.

---

# Fn::FindInMap

## What is FindInMap?

Retrieves values from Mappings.

---

## Syntax

```yaml
!FindInMap
  - MappingName
  - TopLevelKey
  - SecondLevelKey
```

---

## Example

```yaml
Mappings:

  RegionMap:

    ap-south-1:
      AMI: ami-12345
```

Usage:

```yaml
ImageId:

  !FindInMap
    - RegionMap
    - !Ref AWS::Region
    - AMI
```

---

# Fn::ImportValue

## What is ImportValue?

Imports Outputs from another CloudFormation Stack.

Used for Cross-Stack References.

---

## Export Stack

```yaml
Outputs:

  VpcId:

    Value: !Ref MyVPC

    Export:

      Name: ProductionVPC
```

---

## Import Stack

```yaml
VpcId:

  !ImportValue ProductionVPC
```

---

## Architecture

```text
Network Stack
     │
     ▼
Export VPC ID
     │
     ▼
Application Stack
     │
     ▼
Import VPC ID
```

---

# Fn::If

## What is If?

Returns values conditionally.

---

## Syntax

```yaml
!If
  - ConditionName
  - ValueIfTrue
  - ValueIfFalse
```

---

## Example

```yaml
InstanceType:

  !If
    - IsProduction
    - t3.large
    - t2.micro
```

Output:

```text
Production → t3.large
Development → t2.micro
```

---

# Combining Functions

CloudFormation functions can be nested.

Example:

```yaml
!Sub arn:aws:s3:::${BucketName}
```

where:

```yaml
BucketName:
  !Ref MyBucket
```

---

## Advanced Example

```yaml
!Join
  - ""
  - - arn:aws:s3:::
    - !Ref MyBucket
```

Result:

```text
arn:aws:s3:::bucket-name
```

---

# Real-World Example

EC2 Deployment:

```yaml
Resources:

  WebServer:

    Type: AWS::EC2::Instance

    Properties:

      ImageId:

        !FindInMap
          - RegionMap
          - !Ref AWS::Region
          - AMI

      InstanceType:

        !If
          - IsProduction
          - t3.large
          - t2.micro

      UserData:

        !Base64 |
          #!/bin/bash
          yum update -y
```

Multiple intrinsic functions working together.

---

# Most Common Functions in Production

Frequency of usage:

```text
1. !Ref
2. !Sub
3. !GetAtt
4. !ImportValue
5. !If
6. !FindInMap
7. !Join
8. !Select
9. !Split
10. !Base64
```

---

# Best Practices

## Prefer !Sub over !Join

Bad:

```yaml
!Join
  - "-"
  - - app
    - prod
```

Better:

```yaml
!Sub app-prod
```

---

## Use !Ref for Parameters

Avoid hardcoding values.

---

## Use !GetAtt for Resource Attributes

Never hardcode ARNs.

---

## Use !ImportValue for Cross-Stack References

Keeps templates modular.

---

## Keep Nested Functions Readable

Avoid excessive nesting.

---

# Common Mistakes

## Using GetAtt for Resource Names

Wrong:

```yaml
!GetAtt MyBucket.Name
```

Correct:

```yaml
!Ref MyBucket
```

---

## Hardcoded ARNs

Bad:

```yaml
arn:aws:iam::123456789012:role/Admin
```

Use:

```yaml
!Sub arn:aws:iam::${AWS::AccountId}:role/Admin
```

---

## Excessive Join Usage

Prefer `!Sub` whenever possible.

---

# Key Takeaways

* Intrinsic Functions add dynamic behavior to templates.
* `!Ref` and `!Sub` are the most commonly used functions.
* `!GetAtt` retrieves resource attributes.
* `!FindInMap` accesses mapping values.
* `!ImportValue` enables cross-stack references.
* `!Base64` is commonly used with EC2 User Data.
* Functions can be nested for complex logic.
* Nearly every production CloudFormation template uses intrinsic functions.

---

# Interview Questions

### What are Intrinsic Functions?

Built-in CloudFormation functions used for dynamic values and resource references.

---

### What does !Ref return?

* Parameter Value
* Resource Identifier

depending on what is referenced.

---

### What does !GetAtt do?

Returns a resource attribute such as:

* ARN
* DNS Name
* Endpoint
* Public IP

---

### What is the difference between !Sub and !Join?

| !Sub                 | !Join                |
| -------------------- | -------------------- |
| String Interpolation | String Concatenation |
| Easier to Read       | More Verbose         |

---

### What is !ImportValue used for?

To import exported outputs from another CloudFormation stack.

---

### Why is !Base64 commonly used?

To encode EC2 User Data scripts.

---

### Which intrinsic functions are used most frequently?

* !Ref
* !Sub
* !GetAtt
* !ImportValue
* !If
