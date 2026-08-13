# CloudFormation Pseudo Parameters

## What are Pseudo Parameters?

Pseudo Parameters are predefined parameters provided automatically by AWS CloudFormation.

Unlike normal parameters, you do not define them in the Parameters section.

CloudFormation automatically supplies their values during stack creation and updates.

Example:

```yaml
!Ref AWS::Region
```

returns the AWS Region where the stack is being deployed.

---

# Why Use Pseudo Parameters?

Pseudo Parameters make templates:

* Portable
* Reusable
* Environment Independent
* Multi-Region Ready
* Multi-Account Ready

Without Pseudo Parameters:

```yaml
BucketName: my-app-us-east-1
```

Hardcoded.

With Pseudo Parameters:

```yaml
BucketName: !Sub my-app-${AWS::Region}
```

Dynamic and reusable.

---

# How Pseudo Parameters Work

```text
CloudFormation Stack
         │
         ▼
Pseudo Parameter
         │
         ▼
AWS Provides Value
```

Example:

```yaml
!Ref AWS::AccountId
```

CloudFormation automatically returns:

```text
123456789012
```

---

# Available Pseudo Parameters

| Pseudo Parameter      | Description        |
| --------------------- | ------------------ |
| AWS::AccountId        | AWS Account ID     |
| AWS::NotificationARNs | Notification ARNs  |
| AWS::NoValue          | Removes a property |
| AWS::Partition        | AWS Partition      |
| AWS::Region           | Current AWS Region |
| AWS::StackId          | Unique Stack ID    |
| AWS::StackName        | Stack Name         |
| AWS::URLSuffix        | AWS URL Suffix     |

---

# AWS::AccountId

Returns the AWS Account ID.

Example:

```yaml
!Ref AWS::AccountId
```

Output:

```text
123456789012
```

---

## Example

```yaml
Outputs:

  AccountId:

    Value: !Ref AWS::AccountId
```

Output:

```text
123456789012
```

---

# AWS::Region

Returns the Region where the stack is deployed.

Example:

```yaml
!Ref AWS::Region
```

Output:

```text
us-east-1
```

or

```text
ap-south-1
```

---

## Example

```yaml
Outputs:

  CurrentRegion:

    Value: !Ref AWS::Region
```

Output:

```text
ap-south-1
```

---

# AWS::StackName

Returns the stack name.

Example:

```yaml
!Ref AWS::StackName
```

Output:

```text
production-stack
```

---

## Example

```yaml
Outputs:

  StackName:

    Value: !Ref AWS::StackName
```

---

# AWS::StackId

Returns the unique Stack ARN.

Example:

```yaml
!Ref AWS::StackId
```

Output:

```text
arn:aws:cloudformation:ap-south-1:
123456789012:stack/demo-stack/abc123
```

---

## Example

```yaml
Outputs:

  StackId:

    Value: !Ref AWS::StackId
```

---

# AWS::Partition

Returns the AWS partition.

Example:

```yaml
!Ref AWS::Partition
```

Output:

```text
aws
```

Other examples:

```text
aws-cn
aws-us-gov
```

---

## Common Usage

Building ARNs dynamically.

```yaml
!Sub arn:${AWS::Partition}:s3:::mybucket
```

Result:

```text
arn:aws:s3:::mybucket
```

---

# AWS::URLSuffix

Returns AWS domain suffix.

Example:

```yaml
!Ref AWS::URLSuffix
```

Output:

```text
amazonaws.com
```

China Region:

```text
amazonaws.com.cn
```

---

## Example

```yaml
!Sub s3.${AWS::Region}.${AWS::URLSuffix}
```

Result:

```text
s3.ap-south-1.amazonaws.com
```

---

# AWS::NotificationARNs

Returns a list of SNS topic ARNs associated with the stack.

Example:

```yaml
!Ref AWS::NotificationARNs
```

Output:

```text
arn:aws:sns:ap-south-1:
123456789012:alerts
```

Used primarily for stack notifications.

---

# AWS::NoValue

Special pseudo parameter.

Used to remove a property conditionally.

---

## Example

```yaml
Conditions:

  CreateProdResource:
    !Equals [!Ref Environment, Production]
```

```yaml
Resources:

  DemoEC2:

    Type: AWS::EC2::Instance

    Properties:

      SecurityGroupIds:

        - !If
          - CreateProdResource
          - sg-123456
          - !Ref AWS::NoValue
```

---

## Behavior

If condition is false:

```text
SecurityGroupIds property removed entirely
```

rather than receiving a null value.

---

# Practical Example 1

Create Dynamic Bucket Names

```yaml
Resources:

  DemoBucket:

    Type: AWS::S3::Bucket

    Properties:

      BucketName:

        !Sub myapp-${AWS::AccountId}-${AWS::Region}
```

Result:

```text
myapp-123456789012-ap-south-1
```

---

# Practical Example 2

Create Dynamic Resource Tags

```yaml
Tags:

  - Key: Region
    Value: !Ref AWS::Region

  - Key: Account
    Value: !Ref AWS::AccountId
```

---

# Practical Example 3

Dynamic IAM ARN

```yaml
!Sub arn:${AWS::Partition}:iam::${AWS::AccountId}:role/AdminRole
```

Output:

```text
arn:aws:iam::123456789012:role/AdminRole
```

---

# Combining with !Sub

Pseudo Parameters are commonly used with:

```yaml
!Sub
```

Example:

```yaml
BucketName:
  !Sub ${AWS::StackName}-${AWS::Region}
```

Result:

```text
production-stack-ap-south-1
```

---

# Pseudo Parameters vs Parameters

| Feature                 | Parameters | Pseudo Parameters |
| ----------------------- | ---------- | ----------------- |
| User Input Required     | Yes        | No                |
| Defined in Template     | Yes        | No                |
| Provided by AWS         | No         | Yes               |
| Can Be Modified         | Yes        | No                |
| Automatically Available | No         | Yes               |

---

# Best Practices

## Use AWS::Region

Avoid hardcoding Regions.

Bad:

```yaml
Region: ap-south-1
```

Good:

```yaml
Region: !Ref AWS::Region
```

---

## Use AWS::AccountId

Avoid hardcoding account numbers.

Bad:

```yaml
arn:aws:iam::123456789012:role/Admin
```

Good:

```yaml
!Sub arn:aws:iam::${AWS::AccountId}:role/Admin
```

---

## Use AWS::StackName

Useful for naming resources.

Example:

```yaml
BucketName:
  !Sub ${AWS::StackName}-bucket
```

---

## Use AWS::NoValue

Cleaner than returning empty values.

---

# Common Mistakes

## Hardcoding Account IDs

Bad:

```yaml
123456789012
```

Use:

```yaml
!Ref AWS::AccountId
```

---

## Hardcoding Regions

Bad:

```yaml
ap-south-1
```

Use:

```yaml
!Ref AWS::Region
```

---

## Ignoring AWS::Partition

Templates may fail in:

* GovCloud
* China Regions

Use:

```yaml
AWS::Partition
```

for portability.

---

# Key Takeaways

* Pseudo Parameters are predefined by AWS.
* No declaration is required.
* Commonly used values:

  * AWS::Region
  * AWS::AccountId
  * AWS::StackName
  * AWS::StackId
* AWS::NoValue removes properties conditionally.
* Pseudo Parameters improve template portability and reusability.
* Frequently used with `!Sub` and Conditions.

---

# Interview Questions

### What are Pseudo Parameters?

Pseudo Parameters are predefined values automatically provided by CloudFormation.

---

### Do Pseudo Parameters need to be declared?

No.

They are automatically available in every template.

---

### What does AWS::Region return?

The AWS Region where the stack is deployed.

Example:

```text
ap-south-1
```

---

### What does AWS::AccountId return?

The AWS Account ID.

Example:

```text
123456789012
```

---

### What is AWS::NoValue used for?

To remove a property conditionally from a resource definition.

---

### Why is AWS::Partition important?

It allows templates to work across:

* Commercial AWS
* AWS GovCloud
* AWS China

without modification.

---

### Which pseudo parameters are most commonly used?

* AWS::Region
* AWS::AccountId
* AWS::StackName
* AWS::NoValue
