# CloudFormation Parameters

## What are Parameters?

Parameters allow users to provide input values during stack creation or stack updates.

Instead of hardcoding values inside a template, parameters make templates reusable and flexible.

Without Parameters:

```yaml
InstanceType: t2.micro
```

With Parameters:

```yaml
InstanceType: !Ref InstanceType
```

The user chooses the value when creating the stack.

---

# Why Use Parameters?

Parameters help create reusable templates for different environments.

Example:

```text
Development
    │
QA
    │
Production
```

Using the same template:

```yaml
InstanceType:
  Type: String
```

Users can select:

```text
Dev  → t2.micro
QA   → t3.small
Prod → t3.large
```

without modifying the template.

---

# Parameter Section

Parameters are defined in the Parameters section.

```yaml
Parameters:

  ParameterName:

    Type: String
```

---

# Basic Syntax

```yaml
Parameters:

  InstanceType:

    Type: String

Resources:

  DemoEC2:

    Type: AWS::EC2::Instance

    Properties:

      InstanceType: !Ref InstanceType
```

When creating the stack:

```text
InstanceType = t2.micro
```

CloudFormation substitutes the value automatically.

---

# How Parameters Work

```text
User Input
     │
     ▼
Parameter
     │
     ▼
!Ref
     │
     ▼
Resource Property
```

---

# Parameter Types

CloudFormation supports multiple parameter types.

---

## String

Accepts text values.

```yaml
Parameters:

  Environment:

    Type: String
```

Example:

```text
Development
Production
QA
```

---

## Number

Accepts numeric values.

```yaml
Parameters:

  DesiredCapacity:

    Type: Number
```

Example:

```text
1
2
5
10
```

---

## CommaDelimitedList

Accepts comma-separated values.

```yaml
Parameters:

  SubnetIds:

    Type: CommaDelimitedList
```

Input:

```text
subnet-123,subnet-456,subnet-789
```

---

## List<Number>

```yaml
Parameters:

  Ports:

    Type: List<Number>
```

Example:

```text
80,443,8080
```

---

## AWS-Specific Parameter Types

CloudFormation can validate AWS resources automatically.

Example:

```yaml
Parameters:

  KeyName:

    Type: AWS::EC2::KeyPair::KeyName
```

CloudFormation displays existing Key Pairs automatically.

---

# Common AWS Parameter Types

## EC2 Key Pair

```yaml
Type: AWS::EC2::KeyPair::KeyName
```

---

## Security Group

```yaml
Type: AWS::EC2::SecurityGroup::Id
```

---

## Subnet

```yaml
Type: AWS::EC2::Subnet::Id
```

---

## VPC

```yaml
Type: AWS::EC2::VPC::Id
```

---

## AMI

```yaml
Type: AWS::EC2::Image::Id
```

---

# Using Parameters with !Ref

Parameters are commonly referenced using:

```yaml
!Ref
```

Example:

```yaml
Parameters:

  Environment:
    Type: String

Resources:

  DemoBucket:

    Type: AWS::S3::Bucket

    Properties:

      BucketName: !Ref Environment
```

Input:

```text
Production
```

Output:

```text
BucketName = Production
```

---

# Default Values

Default values allow a parameter to be optional.

```yaml
Parameters:

  InstanceType:

    Type: String

    Default: t2.micro
```

If the user does not provide a value:

```text
t2.micro
```

is used automatically.

---

# Allowed Values

Restricts user input.

```yaml
Parameters:

  Environment:

    Type: String

    AllowedValues:

      - Development
      - QA
      - Production
```

Valid:

```text
Development
QA
Production
```

Invalid:

```text
Testing
```

---

# Allowed Pattern

Validates input using Regular Expressions.

Example:

```yaml
Parameters:

  BucketName:

    Type: String

    AllowedPattern: "^[a-z0-9-]+$"
```

Valid:

```text
my-bucket
demo-bucket
```

Invalid:

```text
MyBucket
Bucket_01
```

---

# Minimum and Maximum Length

```yaml
Parameters:

  Username:

    Type: String

    MinLength: 3

    MaxLength: 20
```

Valid:

```text
admin
developer
```

Invalid:

```text
ab
```

---

# Minimum and Maximum Value

For Number parameters.

```yaml
Parameters:

  DesiredCapacity:

    Type: Number

    MinValue: 1

    MaxValue: 10
```

Valid:

```text
3
5
10
```

Invalid:

```text
0
20
```

---

# Description

Descriptions appear in the CloudFormation Console.

```yaml
Parameters:

  Environment:

    Type: String

    Description: Environment Name
```

Good descriptions improve usability.

---

# NoEcho

Used for sensitive information.

Example:

```yaml
Parameters:

  DBPassword:

    Type: String

    NoEcho: true
```

Behavior:

```text
Input: MySecretPassword

Display: *************
```

Useful for:

* Database Passwords
* API Keys
* Tokens

---

# Parameter Example

```yaml
Parameters:

  InstanceType:

    Type: String

    Default: t2.micro

    AllowedValues:

      - t2.micro
      - t3.micro
      - t3.small

Resources:

  WebServer:

    Type: AWS::EC2::Instance

    Properties:

      InstanceType: !Ref InstanceType

      ImageId: ami-12345678
```

---

# Multiple Parameters Example

```yaml
Parameters:

  Environment:

    Type: String

    Default: Development

  InstanceType:

    Type: String

    Default: t2.micro

  KeyName:

    Type: AWS::EC2::KeyPair::KeyName
```

During deployment:

```text
Environment = Production
InstanceType = t3.small
KeyName = production-key
```

---

# Passing Parameters via AWS CLI

## Create Stack

```bash
aws cloudformation create-stack \
--stack-name demo-stack \
--template-body file://template.yaml \
--parameters \
ParameterKey=Environment,ParameterValue=Production
```

---

## Multiple Parameters

```bash
aws cloudformation create-stack \
--stack-name demo-stack \
--template-body file://template.yaml \
--parameters \
ParameterKey=Environment,ParameterValue=Production \
ParameterKey=InstanceType,ParameterValue=t3.small
```

---

# Parameter Constraints

CloudFormation validates:

* Data Type
* Length
* Value Range
* Allowed Values
* Patterns

before resource creation begins.

This prevents deployment failures.

---

# Best Practices

## Avoid Hardcoded Values

Bad:

```yaml
InstanceType: t2.micro
```

Good:

```yaml
InstanceType: !Ref InstanceType
```

---

## Use Defaults

Provide sensible defaults whenever possible.

---

## Add Descriptions

Every parameter should have a description.

---

## Use AWS-Specific Types

Instead of:

```yaml
Type: String
```

Use:

```yaml
Type: AWS::EC2::Subnet::Id
```

CloudFormation validates automatically.

---

## Protect Sensitive Data

Use:

```yaml
NoEcho: true
```

for passwords and secrets.

---

# Common Mistakes

## Too Many Parameters

Templates become difficult to use.

Only expose values that users should modify.

---

## Missing Validation

Bad:

```yaml
Type: String
```

Better:

```yaml
AllowedValues:
  - Production
  - Development
```

---

## Hardcoded Resource Names

Avoid:

```yaml
BucketName: my-bucket
```

Use parameters for flexibility.

---

# Key Takeaways

* Parameters make templates reusable.
* Parameters accept user input during deployment.
* Common types:

  * String
  * Number
  * List
  * AWS-Specific Types
* Parameters are referenced using `!Ref`.
* Constraints improve validation.
* NoEcho hides sensitive values.
* Parameters eliminate hardcoded configurations.

---

# Interview Questions

### What are CloudFormation Parameters?

Parameters allow users to provide input values during stack creation and updates.

---

### How do you reference a parameter?

Using:

```yaml
!Ref ParameterName
```

---

### What is NoEcho?

NoEcho hides sensitive parameter values in the CloudFormation console and logs.

---

### What is the advantage of AWS-specific parameter types?

CloudFormation validates AWS resources automatically and provides dropdown selections in the console.

---

### What is the difference between Default and AllowedValues?

| Property      | Purpose                  |
| ------------- | ------------------------ |
| Default       | Provides a default value |
| AllowedValues | Restricts valid inputs   |

---

### Why should parameters be used instead of hardcoded values?

Parameters improve:

* Reusability
* Flexibility
* Maintainability
* Environment-specific deployments
