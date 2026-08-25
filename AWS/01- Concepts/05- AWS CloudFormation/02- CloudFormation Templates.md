# CloudFormation Templates

## What is a CloudFormation Template?

A CloudFormation Template is a blueprint that defines AWS infrastructure and configuration.

Templates are written in:

* YAML (Recommended)
* JSON

CloudFormation reads the template and provisions the specified AWS resources automatically.

---

# Why Templates?

Templates provide a repeatable and automated way to create infrastructure.

Benefits:

* Infrastructure as Code (IaC)
* Version Control
* Repeatable Deployments
* Consistent Environments
* Reduced Human Errors

---

# Template Formats

## YAML (Recommended)

```yaml
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
```

### Advantages

* Easier to read
* Supports comments
* Less verbose
* Industry standard

---

## JSON

```json
{
  "Resources": {
    "MyBucket": {
      "Type": "AWS::S3::Bucket"
    }
  }
}
```

### Disadvantages

* Verbose
* Difficult to maintain
* Less readable

---

# Template Structure

A CloudFormation template contains multiple sections.

```yaml
AWSTemplateFormatVersion: '2010-09-09'

Description: Demo Template

Metadata:

Parameters:

Mappings:

Conditions:

Resources:

Outputs:
```

---

# Template Sections

## 1. AWSTemplateFormatVersion

Specifies the CloudFormation template version.

```yaml
AWSTemplateFormatVersion: '2010-09-09'
```

### Notes

* Current version is 2010-09-09
* Optional
* Rarely changes

---

## 2. Description

Provides information about the template.

```yaml
Description: Creates an EC2 instance and S3 bucket
```

### Best Practices

Keep descriptions meaningful.

Example:

```yaml
Description: Production VPC with Public and Private Subnets
```

---

## 3. Metadata

Stores additional information about the template.

```yaml
Metadata:
  Author: Aranya
  Version: 1.0
```

### Use Cases

* Documentation
* Tool Integration
* Template Information

---

## 4. Parameters

Used to accept user input.

Example:

```yaml
Parameters:

  InstanceType:
    Type: String

  KeyName:
    Type: AWS::EC2::KeyPair::KeyName
```

### Benefits

Avoid hardcoding values.

Users can choose:

* Instance Types
* AMIs
* Environment Names
* Database Sizes

during deployment.

---

## 5. Mappings

Stores fixed lookup values.

```yaml
Mappings:

  RegionMap:

    us-east-1:
      AMI: ami-123456

    us-west-2:
      AMI: ami-987654
```

### Use Cases

* Region-specific AMIs
* Environment-specific values
* Account-specific values

---

## 6. Conditions

Controls whether resources are created.

```yaml
Conditions:

  CreateProdResources: !Equals
    - !Ref Environment
    - Production
```

### Use Cases

* Production-only resources
* Feature toggles
* Conditional deployments

---

## 7. Resources

The most important section.

This section defines the AWS resources to create.

```yaml
Resources:

  DemoBucket:
    Type: AWS::S3::Bucket
```

### Mandatory Section

Only the Resources section is mandatory.

Without Resources, CloudFormation cannot provision infrastructure.

---

## 8. Outputs

Returns values after deployment.

```yaml
Outputs:

  BucketName:
    Value: !Ref DemoBucket
```

### Use Cases

* Export resource IDs
* Export ARNs
* Cross-stack references

---

# Minimal Template Example

The smallest valid CloudFormation template:

```yaml
Resources:

  DemoBucket:
    Type: AWS::S3::Bucket
```

---

# Complete Template Example

```yaml
AWSTemplateFormatVersion: '2010-09-09'

Description: EC2 Example

Parameters:

  InstanceType:
    Type: String
    Default: t2.micro

Resources:

  DemoEC2:
    Type: AWS::EC2::Instance

    Properties:
      InstanceType: !Ref InstanceType
      ImageId: ami-12345678

Outputs:

  InstanceId:
    Value: !Ref DemoEC2
```

---

# Template Validation

Always validate templates before deployment.

## AWS CLI

```bash
aws cloudformation validate-template \
--template-body file://template.yaml
```

---

## Validation Checks

CloudFormation validates:

* YAML Syntax
* JSON Syntax
* Resource Types
* Property Names
* Template Structure

---

# Template Limits

| Item          | Limit        |
| ------------- | ------------ |
| Template Body | 51,200 Bytes |
| S3 Template   | 1 MB         |
| Parameters    | 200          |
| Outputs       | 200          |
| Mappings      | 200          |
| Resources     | 500          |

---

# Template Best Practices

## Use YAML

Preferred over JSON.

---

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

## Add Descriptions

Document templates properly.

```yaml
Description: Production Web Server Stack
```

---

## Use Outputs

Expose useful values.

Example:

```yaml
Outputs:
  VpcId:
    Value: !Ref DemoVPC
```

---

## Keep Templates Modular

Large templates become difficult to maintain.

Use:

* Nested Stacks
* Cross-Stack References

for large environments.

---

# Common Template Deployment Methods

## AWS Console

```text
CloudFormation
    ↓
Create Stack
    ↓
Upload Template
```

---

## AWS CLI

```bash
aws cloudformation create-stack \
--stack-name my-stack \
--template-body file://template.yaml
```

---

## CI/CD Pipelines

CloudFormation integrates with:

* GitHub Actions
* Jenkins
* GitLab CI/CD
* AWS CodePipeline

---

# Common Mistakes

## Missing Resources Section

Invalid:

```yaml
Parameters:
  Environment:
    Type: String
```

Resources section missing.

---

## Hardcoded Values

Bad practice.

```yaml
InstanceType: t2.micro
```

Use Parameters instead.

---

## No Outputs

Makes troubleshooting difficult.

Always expose important values.

---

# Key Takeaways

* Templates are blueprints for AWS infrastructure.
* YAML is preferred over JSON.
* Resources section is mandatory.
* Parameters provide user inputs.
* Mappings provide lookup values.
* Conditions enable conditional deployment.
* Outputs expose deployed resource information.
* Templates should be validated before deployment.

---

# Interview Questions

### What is a CloudFormation Template?

A CloudFormation Template is a YAML or JSON file that defines AWS infrastructure and configuration.

---

### Which section is mandatory in a CloudFormation template?

The **Resources** section.

---

### What is the purpose of Parameters?

Parameters allow users to provide input values during stack creation.

---

### What is the purpose of Outputs?

Outputs expose useful information from deployed resources.

---

### Why is YAML preferred over JSON?

* Easier to read
* Less verbose
* Supports comments
* Easier maintenance

---

### How do you validate a template?

```bash
aws cloudformation validate-template \
--template-body file://template.yaml
```
