# CloudFormation Resources

## What are Resources?

Resources are the most important component of a CloudFormation template.

A resource represents an AWS service or component that CloudFormation creates, configures, updates, and deletes.

Examples:

* EC2 Instances
* S3 Buckets
* VPCs
* Security Groups
* RDS Databases
* IAM Roles
* Load Balancers
* Lambda Functions

Without the **Resources** section, CloudFormation cannot create any infrastructure.

---

# Why Resources Matter

CloudFormation templates are primarily built to create resources.

```text
Template
    │
    ▼
Resources
    │
    ▼
AWS Infrastructure
```

Every AWS environment eventually translates into a collection of resources.

---

# Resources Section Syntax

Basic Structure:

```yaml
Resources:

  LogicalResourceName:

    Type: AWS::Service::Resource

    Properties:
      Property1: Value
      Property2: Value
```

---

# Resource Anatomy

Example:

```yaml
Resources:

  DemoBucket:

    Type: AWS::S3::Bucket
```

Components:

| Component       | Purpose                |
| --------------- | ---------------------- |
| DemoBucket      | Logical ID             |
| AWS::S3::Bucket | Resource Type          |
| Properties      | Resource Configuration |

---

# Logical ID

Every resource requires a unique Logical ID within the template.

Example:

```yaml
Resources:

  WebServer:
    Type: AWS::EC2::Instance
```

Here:

```text
WebServer
```

is the Logical ID.

---

## Rules

* Must be unique
* Case-sensitive
* Used internally by CloudFormation
* Cannot contain spaces

Valid:

```yaml
WebServer
ApplicationLoadBalancer
ProductionDB
```

Invalid:

```yaml
Web Server
Prod-DB
My Server
```

---

# Resource Type

The Type specifies which AWS resource should be created.

Format:

```text
AWS::Service::Resource
```

Examples:

| Service  | Resource Type         |
| -------- | --------------------- |
| EC2      | AWS::EC2::Instance    |
| S3       | AWS::S3::Bucket       |
| RDS      | AWS::RDS::DBInstance  |
| IAM Role | AWS::IAM::Role        |
| Lambda   | AWS::Lambda::Function |
| VPC      | AWS::EC2::VPC         |

---

# Properties

Properties define the configuration of a resource.

Example:

```yaml
Resources:

  WebServer:

    Type: AWS::EC2::Instance

    Properties:

      InstanceType: t2.micro
      ImageId: ami-12345678
```

CloudFormation creates the EC2 instance using these settings.

---

# Example 1: S3 Bucket

```yaml
Resources:

  DemoBucket:

    Type: AWS::S3::Bucket
```

Creates:

```text
Amazon S3 Bucket
```

with default settings.

---

# Example 2: EC2 Instance

```yaml
Resources:

  WebServer:

    Type: AWS::EC2::Instance

    Properties:

      InstanceType: t2.micro
      ImageId: ami-12345678
```

Creates:

```text
Amazon EC2 Instance
```

using the specified AMI.

---

# Example 3: Security Group

```yaml
Resources:

  WebSG:

    Type: AWS::EC2::SecurityGroup

    Properties:

      GroupDescription: Allow HTTP

      SecurityGroupIngress:

        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
```

Creates:

```text
Security Group
```

allowing HTTP traffic.

---

# Resource Dependencies

Resources can reference other resources.

Example:

```yaml
Resources:

  DemoBucket:
    Type: AWS::S3::Bucket

  LambdaRole:
    Type: AWS::IAM::Role
```

CloudFormation automatically determines creation order.

---

# Resource References

Resources can use:

```yaml
!Ref
```

to reference another resource.

Example:

```yaml
Resources:

  MyBucket:
    Type: AWS::S3::Bucket

Outputs:

  BucketName:
    Value: !Ref MyBucket
```

---

# Referencing Resource Attributes

Use:

```yaml
!GetAtt
```

to retrieve attributes.

Example:

```yaml
Outputs:

  BucketArn:
    Value: !GetAtt MyBucket.Arn
```

Returns:

```text
arn:aws:s3:::my-bucket
```

---

# Resource Creation Order

CloudFormation automatically determines dependencies.

Example:

```yaml
Resources:

  MyVPC:
    Type: AWS::EC2::VPC

  MySubnet:

    Type: AWS::EC2::Subnet

    Properties:
      VpcId: !Ref MyVPC
```

Creation Order:

```text
VPC
 ↓
Subnet
```

---

# Explicit Dependencies

Sometimes dependencies must be specified manually.

Use:

```yaml
DependsOn
```

Example:

```yaml
Resources:

  InternetGateway:
    Type: AWS::EC2::InternetGateway

  GatewayAttachment:

    Type: AWS::EC2::VPCGatewayAttachment

    DependsOn: InternetGateway
```

---

# Resource Lifecycle

CloudFormation manages resources throughout their lifecycle.

```text
Create
   ↓
Update
   ↓
Delete
```

---

# Resource Updates

CloudFormation compares:

```text
Current State
        vs
Template State
```

and applies required changes.

Example:

```yaml
InstanceType: t2.micro
```

changed to

```yaml
InstanceType: t3.micro
```

CloudFormation updates the resource.

---

# Resource Replacement

Some changes require replacement.

Example:

```yaml
BucketName
```

often triggers:

```text
Delete Old Resource
Create New Resource
```

instead of an update.

---

# Common Resource Types

## Networking

```yaml
AWS::EC2::VPC
AWS::EC2::Subnet
AWS::EC2::RouteTable
AWS::EC2::InternetGateway
```

---

## Compute

```yaml
AWS::EC2::Instance
AWS::Lambda::Function
AWS::AutoScaling::AutoScalingGroup
```

---

## Storage

```yaml
AWS::S3::Bucket
AWS::EFS::FileSystem
AWS::EC2::Volume
```

---

## Database

```yaml
AWS::RDS::DBInstance
AWS::DynamoDB::Table
AWS::Redshift::Cluster
```

---

## Security

```yaml
AWS::IAM::Role
AWS::IAM::Policy
AWS::EC2::SecurityGroup
```

---

# Resource Naming Best Practices

Good:

```yaml
ProductionVPC
WebServerSG
ApplicationLoadBalancer
DatabaseSubnetGroup
```

Avoid:

```yaml
Resource1
Test123
MyThing
```

Use descriptive names.

---

# Resource Best Practices

## Use Parameters

Avoid hardcoding values.

Bad:

```yaml
InstanceType: t2.micro
```

Good:

```yaml
InstanceType: !Ref InstanceType
```

---

## Use Tags

Tag resources consistently.

Example:

```yaml
Tags:

  - Key: Environment
    Value: Production
```

---

## Keep Resources Modular

Large templates become difficult to maintain.

Use:

* Nested Stacks
* Cross-Stack References

for enterprise environments.

---

# Common Mistakes

## Duplicate Logical IDs

Invalid:

```yaml
Resources:

  DemoBucket:
    Type: AWS::S3::Bucket

  DemoBucket:
    Type: AWS::S3::Bucket
```

Logical IDs must be unique.

---

## Wrong Resource Type

Invalid:

```yaml
Type: AWS::EC2::Buckets
```

Correct:

```yaml
Type: AWS::S3::Bucket
```

---

## Missing Required Properties

Example:

```yaml
AWS::EC2::Instance
```

requires:

```yaml
ImageId
```

Missing required properties causes stack failure.

---

# Key Takeaways

* Resources are the heart of CloudFormation.
* Every AWS service is represented as a resource.
* Resources require:

  * Logical ID
  * Type
  * Properties
* CloudFormation automatically manages dependencies.
* Resources can reference each other using:

  * !Ref
  * !GetAtt
* CloudFormation creates, updates, and deletes resources automatically.

---

# Interview Questions

### Which section is mandatory in CloudFormation?

The **Resources** section.

---

### What is a Logical ID?

A unique identifier for a resource within a CloudFormation template.

---

### What is the format of a Resource Type?

```text
AWS::Service::Resource
```

Example:

```text
AWS::EC2::Instance
```

---

### What does !Ref do?

Returns the value of another resource or parameter.

---

### What does !GetAtt do?

Returns a specific attribute of a resource.

Example:

```yaml
!GetAtt MyBucket.Arn
```

---

### What is DependsOn?

DependsOn explicitly defines the order in which resources should be created.

---

### Can CloudFormation automatically determine dependencies?

Yes. CloudFormation automatically determines most dependencies through references such as `!Ref` and `!GetAtt`.
