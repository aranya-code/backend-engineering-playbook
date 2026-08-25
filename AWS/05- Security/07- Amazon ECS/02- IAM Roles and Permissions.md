# 02- IAM Roles and Permissions

## Overview

IAM is the primary authorization mechanism for ECS workloads that interact with AWS services.

An ECS application should not use long-lived AWS access keys embedded in source code, environment variables, or container images. Instead, ECS integrates with IAM roles to provide temporary credentials to workloads.

The most important distinction is between the **task execution role** and the **task role**:

```text
                         ECS Task
                            |
              +-------------+-------------+
              |                           |
              v                           v
      Task Execution Role             Task Role
              |                           |
              v                           v
        ECS Runtime                Application Code
              |                           |
       +------+------+              +-----+------+
       |      |      |              |     |      |
      ECR   Logs   Secrets          S3   SQS   DynamoDB
```

These roles have different purposes and should not be treated as interchangeable.

IAM design directly affects the security blast radius of an ECS workload. If an application container is compromised, the permissions attached to its task role determine which AWS resources the attacker may potentially access.

A production ECS IAM design should therefore emphasize:

- Least privilege
- Separation of responsibilities
- Short-lived credentials
- Resource-level permissions
- Explicit trust relationships
- Environment isolation
- Continuous review and auditing

## IAM Roles in ECS

Several identities can participate in an ECS deployment.

| Identity | Used By | Primary Purpose |
|---|---|---|
| Task execution role | ECS/Fargate runtime | Pull images, send logs, retrieve supported startup secrets |
| Task role | Application container | Access AWS services from application code |
| ECS infrastructure role | ECS infrastructure features | Allows ECS to manage supported infrastructure integrations |
| CI/CD role | Deployment system | Build/deploy application infrastructure and services |
| Human IAM identity | Engineers/operators | Administrative and operational access |

The most important distinction for application developers is:

```text
Execution Role
    |
    +-- Used by ECS

Task Role
    |
    +-- Used by application code
```

Giving application code permissions intended only for ECS runtime operations is poor separation of responsibility.

## Task Execution Role

The task execution role grants permissions that the ECS/Fargate runtime needs to start and operate the task.

Typical responsibilities include:

- Pulling private images from Amazon ECR
- Sending container logs to CloudWatch Logs
- Retrieving certain secrets or configuration values when configured through ECS integrations

The application itself does not normally use the execution role to call AWS APIs.

Conceptually:

```text
ECS
 |
 +-- Execution Role
        |
        +-- ECR image pull
        +-- CloudWatch logging
        +-- Startup integrations
```

### When to Use It

Use the task execution role whenever ECS requires AWS permissions to perform runtime operations on behalf of the task.

### Production Considerations

The execution role should contain only the permissions required by the ECS runtime configuration.

Do not add application-specific permissions such as:

```text
s3:PutObject
dynamodb:PutItem
sqs:SendMessage
```

to the execution role simply because the application needs them.

Those permissions belong on the task role when the application itself performs those operations.

## Task Role

The task role is the AWS identity available to the application containers running inside the ECS task.

For example:

```text
FastAPI Application
        |
        v
   AWS SDK / boto3
        |
        v
     Task Role
        |
        +---- S3
        +---- SQS
        +---- Secrets Manager
        +---- DynamoDB
```

A Python application can use the AWS SDK without explicitly supplying access keys:

```python
import boto3

s3 = boto3.client("s3")

response = s3.get_object(
    Bucket="production-assets",
    Key="reports/report.json",
)

data = response["Body"].read()
```

The AWS SDK obtains credentials from the ECS-provided credential mechanism associated with the task role.

### Why It Exists

The task role provides workload identity.

Instead of:

```text
Application
   |
   +-- Hard-coded AWS Access Key
```

the architecture becomes:

```text
Application
   |
   v
ECS Task Role
   |
   v
Temporary AWS Credentials
   |
   v
AWS Service
```

This avoids distributing long-lived credentials with the application.

## Task Role vs Execution Role

This is one of the most important ECS concepts.

| Capability | Task Execution Role | Task Role |
|---|---:|---:|
| Pull private ECR image | Yes | No |
| Send logs through ECS logging integration | Yes | No |
| Application calls S3 | No | Yes |
| Application sends SQS message | No | Yes |
| Application reads DynamoDB | No | Yes |
| Application accesses AWS APIs | Not normally | Yes |
| Used by ECS runtime | Yes | No |
| Used by application code | No | Yes |

The practical rule is:

> **Execution role = ECS runtime permissions. Task role = application permissions.**

## IAM Trust Policy

An IAM role has two important policy dimensions:

```text
IAM Role
   |
   +-- Trust Policy
   |       |
   |       v
   |   Who can assume/use the role?
   |
   +-- Permissions Policy
           |
           v
       What can it do?
```

The trust policy defines which principal is allowed to assume the role.

For ECS task roles, the trust relationship typically allows the ECS tasks service principal to assume the role.

Example:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

The trust policy answers:

> Who is allowed to become this identity?

The permissions policy answers:

> What can this identity do after it is assumed?

These are separate controls.

## Permissions Policies

A permissions policy defines allowed or denied AWS API operations.

For example:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::production-assets/reports/*"
    }
  ]
}
```

This policy allows the identity to retrieve objects under the specified S3 path.

It does not automatically grant:

```text
s3:PutObject
s3:DeleteObject
s3:ListBucket
```

Least privilege requires explicitly granting the operations the application needs.

## Least Privilege

Least privilege means granting only the permissions required for a workload to perform its intended responsibilities.

Consider an order-processing service:

```text
Order Service
    |
    +-- Read product data
    +-- Write order data
    +-- Publish order event
```

Its task role might need access to:

```text
DynamoDB
    dynamodb:GetItem
    dynamodb:PutItem

SQS
    sqs:SendMessage
```

It should not automatically receive:

```text
s3:*
ec2:*
iam:*
kms:*
```

unless those permissions are genuinely required.

### Why Least Privilege Matters

Suppose the application has a remote-code-execution vulnerability.

Without least privilege:

```text
Compromised ECS Task
        |
        v
Broad IAM Role
        |
        +---- S3
        +---- DynamoDB
        +---- SQS
        +---- Secrets
        +---- Other AWS Resources
```

With least privilege:

```text
Compromised ECS Task
        |
        v
Restricted IAM Role
        |
        +---- Only Required Resources
```

The IAM policy therefore becomes a blast-radius control.

## Resource-Level Permissions

Whenever an AWS service supports resource-level permissions for the required operation, scope the resource explicitly.

Avoid:

```json
{
  "Effect": "Allow",
  "Action": "s3:GetObject",
  "Resource": "*"
}
```

Prefer:

```json
{
  "Effect": "Allow",
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::production-assets/uploads/*"
}
```

This limits the potential impact if the application is compromised.

Resource scoping should be combined with action scoping:

```text
Principal
   |
   v
Specific Actions
   |
   v
Specific Resources
   |
   v
Optional Conditions
```

## Action-Level Least Privilege

Avoid granting an entire service when only a few API operations are required.

For example, if a worker only sends messages:

```json
{
  "Effect": "Allow",
  "Action": "sqs:SendMessage",
  "Resource": "arn:aws:sqs:ap-south-1:123456789012:order-events"
}
```

Do not automatically grant:

```text
sqs:*
```

unless the workload actually requires administrative access to the queue.

## Policy Evaluation

AWS evaluates multiple policy types when determining whether an API request is authorized.

At a simplified level:

```text
Request
   |
   v
Identity-Based Policies
   |
   +---- Resource-Based Policies
   |
   +---- Permissions Boundaries
   |
   +---- Session Policies
   |
   +---- SCPs
   |
   v
Authorization Decision
```

An explicit deny takes precedence over an allow.

A useful mental model is:

```text
Explicit Deny
     |
     v
   DENY

No Allow
     |
     v
   DENY

Allow + No Applicable Deny
     |
     v
   ALLOW
```

Actual IAM evaluation includes additional policy types and conditions, so production troubleshooting should use AWS IAM policy analysis tools rather than relying solely on simplified reasoning.

## Identity-Based vs Resource-Based Policies

IAM permissions can be expressed through identity-based policies and, for supported services, resource-based policies.

### Identity-Based Policy

Attached to an IAM identity:

```text
Task Role
   |
   v
IAM Policy
   |
   v
Allow S3 Access
```

### Resource-Based Policy

Attached to a resource:

```text
S3 Bucket
   |
   v
Bucket Policy
   |
   v
Allow Specific Principal
```

For ECS workloads, understanding both models becomes important when accessing resources such as S3 buckets, SQS queues, KMS keys, and other AWS services that support resource policies.

## ECS Task Definition IAM Configuration

A task definition can specify both the execution role and task role.

Example:

```json
{
  "family": "orders-api",
  "executionRoleArn": "arn:aws:iam::123456789012:role/orders-api-execution",
  "taskRoleArn": "arn:aws:iam::123456789012:role/orders-api-task",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "123456789012.dkr.ecr.ap-south-1.amazonaws.com/orders-api:8f31c2a",
      "essential": true
    }
  ]
}
```

The separation should be deliberate:

```text
orders-api-execution
    |
    +-- ECR
    +-- CloudWatch Logs
    +-- ECS startup integrations

orders-api-task
    |
    +-- S3
    +-- SQS
    +-- DynamoDB
```

## Secrets Manager and IAM

If an ECS application needs secrets from AWS Secrets Manager, IAM permissions must be designed according to how the secret is retrieved.

For example, an application using the AWS SDK directly requires its task role to have the required Secrets Manager permission:

```json
{
  "Effect": "Allow",
  "Action": "secretsmanager:GetSecretValue",
  "Resource": "arn:aws:secretsmanager:ap-south-1:123456789012:secret:production/orders-api-*"
}
```

If ECS injects the secret into a container through the task definition, the relevant ECS runtime permission belongs to the execution role.

This distinction is important:

```text
ECS injects secret
    |
    v
Execution Role

Application calls Secrets Manager
    |
    v
Task Role
```

The IAM design should match the actual access mechanism.

## KMS Permissions

Encrypted resources may introduce additional IAM requirements.

For example:

```text
ECS Task
   |
   v
Secrets Manager
   |
   v
KMS
```

If a customer-managed KMS key is involved, the effective authorization may depend on both IAM policies and the KMS key policy.

This can create confusing errors where:

```text
secretsmanager:GetSecretValue
```

appears to be allowed but access still fails because the required KMS permissions are not available.

When using customer-managed keys, evaluate:

- IAM permissions
- KMS key policy
- Resource policy where applicable
- Encryption context conditions where used

## Separate Roles by Workload

Different ECS services should normally have different task roles when their AWS responsibilities differ.

For example:

```text
User Service
    |
    +-- user-service-task-role

Order Service
    |
    +-- order-service-task-role

Notification Service
    |
    +-- notification-service-task-role
```

Avoid using one broad role:

```text
All ECS Services
       |
       v
shared-admin-task-role
```

A shared role makes permission management easier initially but greatly increases blast radius and makes authorization auditing more difficult.

## Separate Roles by Environment

Production and non-production workloads should not normally share the same IAM role.

Prefer:

```text
Development
    |
    +-- orders-api-dev-role

Staging
    |
    +-- orders-api-staging-role

Production
    |
    +-- orders-api-prod-role
```

This reduces the possibility of an application in development accessing production resources.

Environment separation should also exist at the resource level.

```text
Dev Task Role
    |
    +-- Dev S3 Bucket

Prod Task Role
    |
    +-- Prod S3 Bucket
```

Do not rely exclusively on naming conventions to enforce environment isolation.

## Cross-Account Access

Organizations often separate environments or workloads across AWS accounts.

For example:

```text
Development Account
        |
        v
Development ECS

Production Account
        |
        v
Production ECS
```

If a workload must access resources in another account, IAM role assumption can be used.

```text
ECS Task Role
      |
      | sts:AssumeRole
      v
Target Account Role
      |
      v
Target Resource
```

The target role must trust the source principal, while the source identity must have permission to assume the role.

Both sides therefore participate in authorization.

## IAM Conditions

IAM conditions can further restrict permissions.

For example, policies can sometimes restrict access based on:

- AWS account context
- Source VPC or endpoint
- Resource tags
- Encryption requirements
- Requested regions
- Principal attributes
- Specific API request conditions

Conditions should be used carefully because overly complicated policies can become difficult to reason about and troubleshoot.

The goal is stronger authorization without creating an unmaintainable policy system.

## Permissions Boundaries

Permissions boundaries provide a maximum permissions boundary for an IAM role.

Conceptually:

```text
Role Policy
     |
     v
Requested Permissions
     |
     +----------+
                |
                v
       Permissions Boundary
                |
                v
        Maximum Allowed
```

They can be useful in organizations where teams or automation are allowed to create IAM roles but must not exceed an organizational permission ceiling.

For a straightforward ECS deployment, permissions boundaries may not be necessary. They become more valuable in larger AWS organizations with delegated administration.

## Service Control Policies

AWS Organizations service control policies (SCPs) can establish account-level guardrails.

Conceptually:

```text
AWS Organization
       |
       v
      SCP
       |
       v
AWS Account
       |
       v
IAM Role
       |
       v
ECS Task
```

An SCP does not grant permissions. It can restrict the maximum permissions available within an account.

For example, an organization might prevent workloads from using certain services or regions regardless of what an IAM role allows.

This provides a defense layer above individual ECS task roles.

## CI/CD IAM Roles

CI/CD systems should have their own IAM identities.

A typical deployment architecture is:

```text
GitHub Actions
      |
      v
OIDC
      |
      v
AWS IAM Role
      |
      +---- ECR Push
      +---- ECS Task Definition
      +---- ECS Service Deployment
```

Avoid using the ECS task role for deployment operations.

The application runtime and deployment system have different responsibilities and should have different identities.

## GitHub Actions and OIDC

For GitHub Actions, OpenID Connect can provide short-lived AWS credentials without storing long-lived AWS access keys.

Conceptually:

```text
GitHub Actions
      |
      | OIDC Token
      v
AWS STS
      |
      v
Deployment IAM Role
      |
      v
AWS Resources
```

The trust policy should restrict which GitHub repository, branch, environment, or other supported claims can assume the role.

The deployment role should then receive only the permissions required by the pipeline.

## IAM Role Naming

Consistent naming improves operational visibility.

A useful convention is:

```text
<environment>-<service>-<purpose>-role
```

Examples:

```text
prod-orders-api-task-role
prod-orders-api-execution-role
prod-orders-api-deployment-role
```

The exact convention is organization-specific, but names should make the workload and purpose obvious.

## IAM Policy Design Example

Consider a Django order service that:

- Reads product images from S3.
- Uploads generated invoices.
- Publishes events to SQS.
- Does not access DynamoDB.

Its task role should reflect those responsibilities.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadProductImages",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::prod-product-assets/images/*"
    },
    {
      "Sid": "WriteInvoices",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::prod-invoices/orders/*"
    },
    {
      "Sid": "PublishOrderEvents",
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage"
      ],
      "Resource": "arn:aws:sqs:ap-south-1:123456789012:order-events"
    }
  ]
}
```

This policy is easier to review because each permission maps to an explicit application responsibility.

## Permission Boundaries Between Services

Consider three services:

```text
                 ECS
                  |
       +----------+----------+
       |          |          |
       v          v          v
     Users      Orders     Reports
       |          |          |
      IAM        IAM        IAM
       |          |          |
       v          v          v
    Users DB   Orders DB   S3 Reports
```

A compromise of the Reports service should not automatically provide access to the Orders database or Users resources.

Separate roles make this isolation possible.

## IAM and Microservices

Microservice architectures often increase the number of IAM identities.

This is intentional.

```text
Service
   |
   +-- Identity
   +-- Permissions
   +-- Resources
```

Each service should own its permissions based on its responsibility.

This aligns IAM with service boundaries.

However, excessive role fragmentation can also create operational overhead. The objective is meaningful isolation, not creating hundreds of nearly identical roles without a clear security benefit.

## Monitoring IAM Usage

IAM permissions should be reviewed against actual usage.

Useful questions include:

- Which permissions does the task actually use?
- Which permissions have never been used?
- Which roles have excessive access?
- Which services share roles unnecessarily?
- Which roles have production access?
- Which IAM policies contain wildcard actions or resources?

AWS IAM tooling can help identify unused permissions and support least-privilege refinement.

A practical workflow is:

```text
Grant Required Permissions
        |
        v
Observe Actual Usage
        |
        v
Identify Unused Permissions
        |
        v
Reduce Policy
        |
        v
Validate Application
```

Least privilege should be treated as an ongoing process rather than a one-time configuration.

## Troubleshooting IAM Errors

A typical application error may look like:

```text
AccessDeniedException:
User is not authorized to perform:
s3:GetObject
```

A systematic troubleshooting flow is:

```text
Application Error
      |
      v
Identify AWS API
      |
      v
Identify Calling Identity
      |
      v
Check Task Role
      |
      v
Check Identity Policy
      |
      v
Check Resource Policy
      |
      v
Check Explicit Deny
      |
      v
Check Conditions
      |
      v
Check KMS / Dependent Permissions
```

Do not immediately solve an IAM error by adding `AdministratorAccess`.

That hides the actual authorization problem and creates a larger security risk.

## Common IAM Mistakes

### Using the Execution Role for Application Permissions

The application needs S3 access, so the developer adds S3 permissions to the execution role.

This confuses ECS runtime permissions with application permissions.

**Better:** put application AWS API permissions on the task role.

### Using One Role for Every ECS Service

This creates unnecessary permission sharing.

If one service is compromised, its credentials may provide access to resources belonging to other services.

**Better:** separate task roles according to workload boundaries.

### Using Wildcard Permissions

Examples:

```text
Action: "*"
Resource: "*"
```

These policies dramatically increase blast radius.

**Better:** scope actions and resources to actual application requirements.

### Embedding AWS Access Keys

Long-lived credentials stored in:

```text
.env
Dockerfile
GitHub Secrets
Source Code
```

can leak and require manual rotation.

**Better:** use IAM roles and short-lived credentials.

### Giving Production Roles to Development

A development ECS task should not normally have permissions against production databases or buckets.

**Better:** isolate accounts, roles, and resources by environment.

### Ignoring Resource Policies

A task role can contain the expected permission while an S3 bucket, KMS key, or other resource policy still prevents access.

**Better:** evaluate the complete authorization chain.

### Ignoring Explicit Denies

An explicit deny can override an allow.

**Better:** inspect SCPs, permissions boundaries, resource policies, and other applicable controls.

### Overusing Conditions

Highly complex policies can become difficult to understand and maintain.

**Better:** use conditions when they provide meaningful security value and keep the policy understandable.

## Production IAM Checklist

| Area | Recommended Practice |
|---|---|
| Task role | Application-specific permissions |
| Execution role | ECS runtime permissions |
| Least privilege | Scope actions and resources |
| Credentials | Avoid long-lived access keys |
| Environment | Separate dev/staging/prod access |
| Services | Separate roles when responsibilities differ |
| Resources | Prefer resource-level permissions |
| CI/CD | Separate deployment role |
| GitHub Actions | Prefer OIDC and short-lived credentials |
| Secrets | Restrict access to required secrets |
| KMS | Review both IAM and key policies |
| Cross-account | Use explicit role assumption |
| SCPs | Use organizational guardrails where appropriate |
| Monitoring | Review IAM activity and unused permissions |
| Auditing | Track role and policy changes |
| Troubleshooting | Investigate the full IAM evaluation chain |

## Interview Traps

### What Is the Difference Between a Task Role and an Execution Role?

The execution role is used by the ECS runtime for operations such as pulling images and sending logs.

The task role is the identity available to application code for calling AWS APIs.

### Where Should S3 Permissions for a Python Application Go?

Normally on the ECS task role because the application itself is calling S3.

### Why Should Every ECS Service Not Share One IAM Role?

Shared roles increase permission coupling and blast radius. A compromised service may gain access to resources belonging to unrelated services.

### Does an IAM Policy Automatically Grant Access?

No.

Authorization depends on the complete applicable policy evaluation, including identity policies, resource policies, explicit denies, permissions boundaries, SCPs, and conditions where applicable.

### Why Are IAM Roles Better Than AWS Access Keys Inside Containers?

Roles provide temporary credentials and avoid distributing long-lived secrets with the application.

### Can a Task Role Access Another AWS Account?

Yes, when cross-account role assumption is configured correctly. The source identity needs permission to assume the target role, and the target role must trust the source principal.

### What Happens if a Task Role Is Too Powerful?

A compromised application can potentially use the task's AWS credentials to access or modify many unrelated resources.

This is why IAM permissions are an important part of ECS blast-radius control.

## Key Takeaways

- **Task execution roles and task roles have different responsibilities**: execution roles serve the ECS runtime, while task roles authorize application code.
- ECS applications should use **least-privilege task roles with narrowly scoped actions and resources**, rather than broad service or administrator permissions.
- Separate IAM roles by **service, environment, and responsibility** when meaningful isolation is required to reduce blast radius.
- Avoid long-lived AWS access keys inside containers; use **ECS task roles and short-lived credentials**, and use OIDC-based roles for CI/CD where supported.
- IAM troubleshooting requires evaluating the **complete authorization chain**, including identity policies, resource policies, explicit denies, permissions boundaries, SCPs, conditions, and dependent services such as KMS.