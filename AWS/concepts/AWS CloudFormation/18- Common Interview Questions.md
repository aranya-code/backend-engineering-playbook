# CloudFormation Interview Questions

# Beginner Level

## 1. What is AWS CloudFormation?

AWS CloudFormation is an Infrastructure as Code (IaC) service that allows users to define and provision AWS infrastructure using YAML or JSON templates.

---

## 2. What are the benefits of CloudFormation?

* Infrastructure as Code
* Automation
* Repeatability
* Consistency
* Version Control
* Automatic Rollbacks

---

## 3. What formats are supported by CloudFormation?

* YAML (Recommended)
* JSON

---

## 4. What is a CloudFormation Template?

A YAML or JSON file that defines AWS infrastructure and configuration.

---

## 5. What is a Stack?

A Stack is a collection of AWS resources managed as a single unit by CloudFormation.

---

## 6. Which section is mandatory in a CloudFormation template?

```yaml
Resources:
```

---

## 7. What are Resources?

AWS services or components that CloudFormation creates.

Examples:

* EC2
* S3
* RDS
* IAM
* Lambda

---

## 8. What is a Logical ID?

A unique identifier for a resource within a CloudFormation template.

Example:

```yaml
Resources:

  WebServer:
    Type: AWS::EC2::Instance
```

`WebServer` is the Logical ID.

---

## 9. What is a Physical ID?

The actual AWS resource identifier.

Example:

```text
i-0123456789abcdef
```

for an EC2 instance.

---

## 10. What is Infrastructure as Code?

Managing infrastructure using code rather than manual configuration.

---

# Parameters

## 11. What are Parameters?

Inputs provided during stack creation or update.

---

## 12. Why use Parameters?

To avoid hardcoded values and make templates reusable.

---

## 13. How do you reference a Parameter?

```yaml
!Ref ParameterName
```

---

## 14. What is NoEcho?

Hides sensitive parameter values.

Example:

```yaml
NoEcho: true
```

---

## 15. What are AWS-specific Parameter Types?

Examples:

```yaml
AWS::EC2::Subnet::Id
AWS::EC2::KeyPair::KeyName
AWS::EC2::VPC::Id
```

---

# Pseudo Parameters

## 16. What are Pseudo Parameters?

Predefined values automatically supplied by CloudFormation.

---

## 17. Name common Pseudo Parameters.

```text
AWS::Region
AWS::AccountId
AWS::StackName
AWS::StackId
AWS::Partition
AWS::NoValue
```

---

## 18. What does AWS::Region return?

Current AWS Region.

Example:

```text
ap-south-1
```

---

## 19. What does AWS::AccountId return?

Current AWS Account ID.

---

## 20. What is AWS::NoValue?

Removes a property conditionally.

---

# Mappings

## 21. What are Mappings?

Static lookup tables inside templates.

---

## 22. How do you retrieve Mapping values?

```yaml
!FindInMap
```

---

## 23. What is the most common use of Mappings?

Region-specific AMI lookups.

---

## 24. Can users modify Mappings during deployment?

No.

Mappings are fixed values.

---

# Conditions

## 25. What are Conditions?

Logical expressions used to control resource creation and configuration.

---

## 26. Which functions are used in Conditions?

```text
Fn::Equals
Fn::If
Fn::And
Fn::Or
Fn::Not
```

---

## 27. What does Fn::Equals do?

Compares two values.

Returns:

```text
True
False
```

---

## 28. What does Fn::If do?

Returns one value if true and another if false.

---

## 29. Can Conditions prevent resource creation?

Yes.

Using:

```yaml
Condition: MyCondition
```

---

## 30. When are Conditions evaluated?

During stack creation and updates.

---

# Intrinsic Functions

## 31. What are Intrinsic Functions?

Built-in CloudFormation functions used for dynamic values.

---

## 32. What does !Ref do?

Returns:

* Parameter Value
* Resource Identifier

---

## 33. What does !GetAtt do?

Returns resource attributes.

Example:

```yaml
!GetAtt MyBucket.Arn
```

---

## 34. What does !Sub do?

Performs string substitution.

---

## 35. What does !Join do?

Concatenates strings.

---

## 36. What does !Split do?

Splits a string into a list.

---

## 37. What does !Select do?

Returns a specific element from a list.

---

## 38. What does !Base64 do?

Encodes data.

Commonly used for EC2 UserData.

---

## 39. What does !ImportValue do?

Imports values exported from another stack.

---

## 40. Which intrinsic functions are used most often?

```text
!Ref
!Sub
!GetAtt
```

---

# Outputs

## 41. What are Outputs?

Values returned after stack creation.

---

## 42. Why use Outputs?

Expose useful information.

Example:

```text
VpcId
BucketName
LoadBalancerDNS
```

---

## 43. Can Outputs be exported?

Yes.

Using:

```yaml
Export:
```

---

## 44. What is a Cross Stack Reference?

Importing exported values from another stack.

---

## 45. Which function is used for Cross Stack References?

```yaml
!ImportValue
```

---

# Stack Lifecycle

## 46. What are the main stack operations?

```text
Create
Update
Delete
Rollback
```

---

## 47. What is CREATE_COMPLETE?

Stack creation succeeded.

---

## 48. What is UPDATE_COMPLETE?

Stack update succeeded.

---

## 49. What is DELETE_COMPLETE?

Stack deletion succeeded.

---

## 50. What is CREATE_FAILED?

Stack creation failed.

---

# Change Sets

## 51. What is a Change Set?

A preview of infrastructure changes before deployment.

---

## 52. Why use Change Sets?

To understand deployment impact before execution.

---

## 53. What actions can appear in a Change Set?

```text
Add
Modify
Remove
Import
```

---

## 54. What does Replacement: True mean?

CloudFormation will recreate the resource.

---

## 55. Are Change Sets mandatory?

No.

But highly recommended for production.

---

# Rollbacks

## 56. What is Rollback?

Automatic recovery when a stack operation fails.

---

## 57. What causes Rollbacks?

Examples:

```text
Invalid AMI
Permission Issues
Resource Conflicts
```

---

## 58. What is UPDATE_ROLLBACK_COMPLETE?

CloudFormation successfully restored the previous state.

---

## 59. What is UPDATE_ROLLBACK_FAILED?

CloudFormation failed during rollback.

---

## 60. How do you recover from UPDATE_ROLLBACK_FAILED?

```bash
aws cloudformation continue-update-rollback
```

---

# Deletion Policies

## 61. What is DeletionPolicy?

Controls what happens when resources are deleted.

---

## 62. What DeletionPolicy values exist?

```text
Delete
Retain
Snapshot
```

---

## 63. What does Retain do?

Keeps the resource after stack deletion.

---

## 64. What does Snapshot do?

Creates a snapshot before deletion.

---

## 65. Which resources commonly support Snapshot?

```text
RDS
EBS
Redshift
```

---

# Service Roles

## 66. What is a Service Role?

An IAM Role assumed by CloudFormation.

---

## 67. Why use Service Roles?

Provides consistent deployment permissions.

---

## 68. Who assumes the Service Role?

```text
CloudFormation
```

---

## 69. What must exist in the Trust Policy?

```json
"Service":
"cloudformation.amazonaws.com"
```

---

## 70. How do you specify a Service Role?

```bash
--role-arn
```

---

# Capabilities

## 71. What are Capabilities?

Security acknowledgments required for sensitive resources.

---

## 72. What is CAPABILITY_IAM?

Allows CloudFormation to create IAM resources.

---

## 73. What is CAPABILITY_NAMED_IAM?

Required for named IAM resources.

---

## 74. What is CAPABILITY_AUTO_EXPAND?

Required for:

```text
Macros
Transforms
AWS SAM
```

---

## 75. What happens if Capabilities are missing?

Stack creation fails.

---

# Custom Resources

## 76. What are Custom Resources?

CloudFormation extensions that execute custom logic.

---

## 77. What is a ServiceToken?

The Lambda ARN used by a Custom Resource.

---

## 78. What request types are supported?

```text
Create
Update
Delete
```

---

## 79. What happens if the Custom Resource returns FAILED?

CloudFormation fails the stack operation.

---

## 80. Where are Custom Resource logs stored?

```text
CloudWatch Logs
```

---

# Senior-Level Questions

## 81. What is Configuration Drift?

When actual AWS resources differ from the CloudFormation template.

---

## 82. What is Drift Detection?

A feature that identifies configuration drift.

---

## 83. Why avoid manual changes?

They create drift.

---

## 84. What is a Nested Stack?

A stack managed by another parent stack.

---

## 85. Benefits of Nested Stacks?

* Reusability
* Modularity
* Easier Maintenance

---

## 86. What are Stack Policies?

Policies that protect resources from updates.

---

## 87. What is a StackSet?

Deploys stacks across:

* Multiple Accounts
* Multiple Regions

---

## 88. Difference between Stack and StackSet?

| Stack             | StackSet                 |
| ----------------- | ------------------------ |
| Single Deployment | Multi-Account Deployment |

---

## 89. Difference between DeletionPolicy and UpdateReplacePolicy?

| DeletionPolicy | UpdateReplacePolicy  |
| -------------- | -------------------- |
| Stack Deletion | Resource Replacement |

---

## 90. Difference between Change Sets and Rollbacks?

| Change Set       | Rollback         |
| ---------------- | ---------------- |
| Prevent Problems | Recover Problems |

---

# Scenario-Based Questions

## 91. How would you deploy the same infrastructure to multiple environments?

Use:

* Parameters
* Conditions
* Mappings

---

## 92. How would you share a VPC between stacks?

Use:

```yaml
Export
ImportValue
```

---

## 93. How would you protect an RDS database from accidental deletion?

Use:

```yaml
DeletionPolicy: Snapshot
```

or

```yaml
DeletionPolicy: Retain
```

---

## 94. How would you troubleshoot CREATE_FAILED?

Check:

```text
CloudFormation Events
```

for the root cause.

---

## 95. How would you troubleshoot UPDATE_ROLLBACK_FAILED?

1. Check Events
2. Fix issue
3. Run:

```bash
aws cloudformation continue-update-rollback
```

---

## 96. How would you securely store database passwords?

Use:

```text
AWS Secrets Manager
SSM Parameter Store
```

---

## 97. How would you reduce production deployment risk?

Use:

```text
Change Sets
Service Roles
Rollback
Stack Policies
```

---

## 98. How would you organize a large CloudFormation environment?

Separate stacks:

```text
Network Stack
Application Stack
Database Stack
Monitoring Stack
```

---

## 99. How would you detect unauthorized infrastructure changes?

Use:

```text
Drift Detection
CloudTrail
```

---

## 100. What are the most important CloudFormation concepts for real-world projects?

```text
Templates
Stacks
Parameters
Mappings
Conditions
Intrinsic Functions
Outputs
Change Sets
Rollbacks
Deletion Policies
Service Roles
Custom Resources
StackSets
Drift Detection
```

---

# Senior Architect Quick Revision Sheet

### Core Components

```text
Resources
Parameters
Mappings
Conditions
Outputs
```

---

### Important Functions

```text
!Ref
!Sub
!GetAtt
!ImportValue
!FindInMap
!If
```

---

### Important Stack States

```text
CREATE_COMPLETE
CREATE_FAILED
UPDATE_COMPLETE
UPDATE_ROLLBACK_COMPLETE
DELETE_COMPLETE
```

---

### Critical Production Features

```text
Change Sets
Rollback
DeletionPolicy
Service Roles
Stack Policies
Drift Detection
```

---

### Security Features

```text
IAM Capabilities
NoEcho
Secrets Manager
Least Privilege
Service Roles
```

---

### Enterprise Features

```text
Nested Stacks
Cross Stack References
StackSets
Custom Resources
CI/CD Integration
```

---

# Final Interview Advice

For AWS interviews, focus heavily on:

1. Parameters
2. Intrinsic Functions
3. Change Sets
4. Rollbacks
5. Deletion Policies
6. Service Roles
7. StackSets
8. Drift Detection
9. Cross Stack References
10. Custom Resources

These topics appear frequently in:

* AWS Cloud Engineer Interviews
* DevOps Engineer Interviews
* Platform Engineer Interviews
* Solutions Architect Interviews
* Senior Backend Developer Interviews
