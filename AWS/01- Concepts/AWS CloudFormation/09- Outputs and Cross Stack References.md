# Outputs and Cross Stack References

## What are Outputs?

Outputs allow CloudFormation to expose useful information after a stack is created or updated.

Outputs provide values that can be:

* Viewed in the CloudFormation Console
* Retrieved using AWS CLI
* Consumed by other CloudFormation stacks
* Used in CI/CD Pipelines
* Shared across teams

---

# Why Use Outputs?

Imagine you create:

```text
VPC
Subnet
EC2
RDS
```

CloudFormation generates IDs automatically:

```text
vpc-123456
subnet-789012
i-abcdef
database.xyz.ap-south-1.rds.amazonaws.com
```

Outputs expose these values for future use.

---

# Outputs Section

Outputs are defined in:

```yaml
Outputs:
```

section of a template.

Basic Structure:

```yaml
Outputs:

  OutputName:

    Value: ValueToExport
```

---

# Basic Example

```yaml
Outputs:

  BucketName:

    Value: !Ref MyBucket
```

Output:

```text
my-demo-bucket
```

---

# Output Anatomy

Example:

```yaml
Outputs:

  VpcId:

    Description: Created VPC ID

    Value: !Ref DemoVPC
```

Components:

| Component   | Purpose                    |
| ----------- | -------------------------- |
| VpcId       | Output Logical Name        |
| Description | Human Readable Description |
| Value       | Returned Value             |

---

# Viewing Outputs

## AWS Console

```text
CloudFormation
      ↓
Stack
      ↓
Outputs Tab
```

Displays all output values.

---

## AWS CLI

```bash
aws cloudformation describe-stacks \
--stack-name demo-stack
```

Output:

```json
{
  "OutputKey": "VpcId",
  "OutputValue": "vpc-123456"
}
```

---

# Output Example: EC2 Instance

```yaml
Resources:

  WebServer:

    Type: AWS::EC2::Instance

Outputs:

  InstanceId:

    Value: !Ref WebServer
```

Result:

```text
i-0ab123456789
```

---

# Output Example: Public IP

```yaml
Outputs:

  PublicIP:

    Value: !GetAtt WebServer.PublicIp
```

Result:

```text
52.66.10.25
```

---

# Output Example: ARN

```yaml
Outputs:

  BucketArn:

    Value: !GetAtt MyBucket.Arn
```

Result:

```text
arn:aws:s3:::my-bucket
```

---

# Description Field

Descriptions improve readability.

Example:

```yaml
Outputs:

  VpcId:

    Description: Production VPC Identifier

    Value: !Ref ProductionVPC
```

---

# Exporting Outputs

Outputs can be exported and shared with other stacks.

Syntax:

```yaml
Outputs:

  OutputName:

    Value: Value

    Export:

      Name: ExportName
```

---

# Export Example

```yaml
Outputs:

  ProductionVpcId:

    Value: !Ref MyVPC

    Export:

      Name: ProductionVpcId
```

CloudFormation stores:

```text
ProductionVpcId
     ↓
vpc-123456
```

for other stacks to consume.

---

# What are Cross Stack References?

Cross Stack References allow one stack to use values exported by another stack.

This enables:

* Modular Architecture
* Reusable Infrastructure
* Team Separation
* Independent Deployments

---

# Why Cross Stack References?

Without Cross Stack References:

```text
Network Stack
Application Stack

Duplicate VPC IDs
Duplicate Configurations
```

Hard to maintain.

With Cross Stack References:

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

Single source of truth.

---

# ImportValue

CloudFormation imports exported values using:

```yaml
!ImportValue
```

---

# Syntax

```yaml
!ImportValue ExportName
```

---

# Example

Exporting Stack:

```yaml
Outputs:

  SharedVpc:

    Value: !Ref MyVPC

    Export:

      Name: SharedVpc
```

---

Importing Stack:

```yaml
Resources:

  WebServerSG:

    Type: AWS::EC2::SecurityGroup

    Properties:

      VpcId:

        !ImportValue SharedVpc
```

Result:

```text
VpcId = vpc-123456
```

---

# Complete Example

## Network Stack

```yaml
Resources:

  ProductionVPC:

    Type: AWS::EC2::VPC

Outputs:

  ProductionVpcId:

    Value: !Ref ProductionVPC

    Export:

      Name: ProductionVpcId
```

---

## Application Stack

```yaml
Resources:

  ApplicationSG:

    Type: AWS::EC2::SecurityGroup

    Properties:

      VpcId:

        !ImportValue ProductionVpcId
```

---

# Architecture Diagram

```text
Network Stack
│
├── VPC
├── Subnets
└── Route Tables
      │
      ▼
 Export Values
      │
      ▼
Application Stack
│
├── EC2
├── ALB
└── Security Groups
```

---

# Export Name Rules

Export names must be:

* Unique within a Region
* Unique within an Account

Invalid:

```text
Two stacks exporting:

SharedVpc
```

CloudFormation error occurs.

---

# Dynamic Export Names

Use:

```yaml
!Sub
```

Example:

```yaml
Outputs:

  VpcId:

    Value: !Ref MyVPC

    Export:

      Name:

        !Sub ${AWS::StackName}-VpcId
```

Output:

```text
network-stack-VpcId
```

---

# Conditional Outputs

Outputs can use Conditions.

Example:

```yaml
Outputs:

  ALBDNS:

    Condition: IsProduction

    Value: !GetAtt ALB.DNSName
```

Result:

```text
Production → Output Created

Development → Output Skipped
```

---

# Common Output Values

## VPC ID

```yaml
Value: !Ref MyVPC
```

---

## Subnet ID
