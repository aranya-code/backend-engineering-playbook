# 03- Principals, Resources and ARNs

## Overview

AWS IAM authorization becomes much easier to reason about once three concepts are clearly separated:

- **Principal** — who or what is making the request
- **Resource** — which AWS object the request targets
- **ARN** — the identifier used to name many AWS resources precisely

A typical authorization request can be modeled as:

```text
Principal
    +
Action
    +
Resource
    +
Request Context
    ↓
IAM Policy Evaluation
    ↓
Allow / Deny
```

For example, a backend service may attempt:

```text
Principal:
    arn:aws:iam::123456789012:role/OrderServiceRole

Action:
    s3:GetObject

Resource:
    arn:aws:s3:::company-orders/invoices/12345.pdf
```

IAM then evaluates the applicable policies and request context to determine whether the operation is authorized.

These concepts are closely related but are not interchangeable. A role is a principal when it is acting as an identity, an ARN identifies a resource or identity, and a resource is the target on which an operation is being performed.

---

## Principal

A **principal** is an entity that can make a request to AWS or be referenced by an authorization policy.

AWS documents several principal types, including IAM users, IAM roles, role sessions, AWS accounts, federated identities, and AWS services. IAM groups are not principals because groups are permission-management constructs rather than authenticated identities. :contentReference[oaicite:0]{index=0}

Common principal categories include:

| Principal type | Example | Typical use |
|---|---|---|
| IAM user | `arn:aws:iam::123456789012:user/alice` | Legacy or specialized human access |
| IAM role | `arn:aws:iam::123456789012:role/OrderServiceRole` | Workloads and delegated access |
| Role session | `arn:aws:sts::123456789012:assumed-role/OrderServiceRole/backend` | Temporary role session |
| AWS account | `arn:aws:iam::123456789012:root` | Delegating access to an account |
| AWS service | `ecs-tasks.amazonaws.com` | AWS service trust |
| Federated identity | SAML/OIDC-based principal | External identity federation |

The important engineering question is not simply:

> Which IAM object exists?

It is:

> Which principal is actually making this request?

---

## Principal vs Identity

A useful distinction is:

```text
Identity
    ↓
Can represent an actor
    ↓
User / Role

Principal
    ↓
Identity or other supported entity
    ↓
Actually participates in an authorization decision
```

For example, an IAM role is an identity. When an application assumes that role and uses the resulting temporary credentials, the resulting session is represented as a role session principal.

This distinction becomes important in resource-based policies and audit investigation.

---

## IAM User as a Principal

An IAM user can be specified as a principal in supported resource-based policies.

Example:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::123456789012:user/alice"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::company-reports/*"
        }
    ]
}
```

The policy directly identifies the user.

For modern production systems, directly granting resource access to individual IAM users is usually less desirable than using role-based or centralized workforce access, because permissions become coupled to individual identities.

---

## IAM Role as a Principal

An IAM role can also be referenced as a principal.

Example:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::123456789012:role/OrderServiceRole"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::company-orders/*"
        }
    ]
}
```

Roles are especially important because they provide a reusable identity boundary for workloads.

A common production flow is:

```text
ECS Task
    ↓
OrderServiceRole
    ↓
Temporary Credentials
    ↓
S3
```

---

## Role Sessions

When a principal assumes a role, AWS issues temporary credentials for a role session.

Conceptually:

```text
IAM Role
    ↓
AssumeRole
    ↓
Role Session
    ↓
Temporary Credentials
    ↓
AWS API Request
```

A role session can have an ARN similar to:

```text
arn:aws:sts::123456789012:assumed-role/OrderServiceRole/backend-worker
```

AWS recommends using IAM role principals rather than role session principals in policies where possible, with conditions used for additional restrictions when necessary. :contentReference[oaicite:1]{index=1}

This is particularly relevant when designing resource-based policies.

---

## AWS Account Principal

A resource-based policy can specify another AWS account as a principal.

For example:

```json
{
    "Principal": {
        "AWS": "arn:aws:iam::555555555555:root"
    }
}
```

This does **not** mean that only the root user of account `555555555555` receives access.

An AWS account principal delegates access to that account. The account's administrator must then configure an identity in that account that can use the delegated permission. AWS documents both the account ARN form and the shortened account-ID form. :contentReference[oaicite:2]{index=2}

Conceptually:

```text
Account A
    |
    | Resource Policy
    | trusts Account B
    v

Account B
    |
    | Identity permissions
    v
User / Role
```

This is a fundamental pattern for cross-account access.

---

## AWS Service Principals

AWS services can also appear as principals.

For example, an IAM role trusted by EC2 might use:

```json
{
    "Principal": {
        "Service": "ec2.amazonaws.com"
    }
}
```

A Lambda execution role has a corresponding service trust relationship allowing the Lambda service to assume the role.

The service principal answers:

> Which AWS service is trusted to assume or use this identity?

Service principals should be treated as explicit trust boundaries rather than generic access grants.

---

## Federated Principals

External identity systems can participate in AWS authorization through federation.

Common mechanisms include:

- SAML federation
- OIDC federation
- IAM Identity Center
- Web identity federation

For backend workloads, OIDC-based federation is particularly useful for environments such as CI/CD systems and Kubernetes workloads because it can avoid storing long-lived AWS access keys.

The general pattern is:

```text
External Identity
        ↓
Federation
        ↓
AWS STS
        ↓
Temporary Credentials
        ↓
AWS Resource
```

---

## Principal in Identity-Based vs Resource-Based Policies

A major IAM distinction is where the policy is attached.

### Identity-Based Policy

Identity-based policies are attached to users, groups, or roles.

The principal is implicit because the policy is already associated with the identity.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::company-reports/*"
        }
    ]
}
```

There is no `Principal` element.

### Resource-Based Policy

Resource-based policies are attached to supported resources and explicitly specify the principal.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::123456789012:role/ReportingRole"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::company-reports/*"
        }
    ]
}
```

The `Principal` element is required for resource-based policies and is not used in identity-based policies. :contentReference[oaicite:3]{index=3}

---

## Avoid Broad Principals

The following grants access to all principals:

```json
{
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::company-public-data/*"
}
```

This may be intentional for public resources, but using `Principal: "*"` unintentionally can expose data.

AWS explicitly recommends against wildcard principals in `Allow` statements unless public or anonymous access is intended. :contentReference[oaicite:4]{index=4}

Prefer:

```json
{
    "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/AnalyticsRole"
    }
}
```

when a specific principal is intended.

---

## Resource

A **resource** is the AWS object to which an IAM statement applies.

Examples include:

- S3 bucket
- S3 object
- DynamoDB table
- SQS queue
- SNS topic
- KMS key
- Secrets Manager secret
- IAM role
- Lambda function

The `Resource` policy element identifies the objects to which a statement applies. AWS policy statements generally use an ARN to identify those resources. :contentReference[oaicite:5]{index=5}

Example:

```json
{
    "Effect": "Allow",
    "Action": "sqs:SendMessage",
    "Resource": "arn:aws:sqs:ap-south-1:123456789012:order-events"
}
```

The action and resource must correspond to what the target AWS service supports.

---

## Resource vs Action

A policy statement normally combines at least:

```text
Effect
Action
Resource
```

For example:

```json
{
    "Effect": "Allow",
    "Action": "dynamodb:GetItem",
    "Resource": "arn:aws:dynamodb:ap-south-1:123456789012:table/Orders"
}
```

This can be read as:

> Allow the specified principal to perform `dynamodb:GetItem` on the `Orders` table.

The action describes **what operation** is requested.

The resource describes **where that operation applies**.

---

## Resource-Level vs Service-Level Permissions

Not every AWS API action supports resource-level scoping in the same way.

Some actions can target a specific resource:

```text
s3:GetObject
dynamodb:GetItem
sqs:SendMessage
```

Other actions may require `"Resource": "*"` because the API does not support a resource-specific ARN for that authorization decision.

For example, permissions for certain account-level discovery APIs may require:

```json
{
    "Effect": "Allow",
    "Action": "ec2:DescribeRegions",
    "Resource": "*"
}
```

Do not assume that `Resource: "*"` is always a security mistake. The correct scope is determined by the AWS service's authorization model.

The engineering objective is to use the narrowest resource scope supported by the specific action.

---

## Amazon Resource Names

An **Amazon Resource Name (ARN)** identifies an AWS resource.

The general ARN structure is:

```text
arn:partition:service:region:account-id:resource
```

AWS documents the structure as:

```text
arn:
    partition:
    service:
    region:
    account:
    resource
```

The exact resource component varies by AWS service. :contentReference[oaicite:6]{index=6}

Example:

```text
arn:aws:sqs:ap-south-1:123456789012:order-events
```

Breaking it apart:

| Segment | Value | Meaning |
|---|---|---|
| ARN prefix | `arn` | Identifies an ARN |
| Partition | `aws` | Standard AWS partition |
| Service | `sqs` | Amazon SQS |
| Region | `ap-south-1` | Resource region |
| Account | `123456789012` | Owning account |
| Resource | `order-events` | Queue name |

---

## ARN Components

### Partition

The partition identifies the AWS environment.

Examples include:

```text
aws
aws-cn
aws-us-gov
```

For standard commercial AWS resources:

```text
arn:aws:...
```

The partition is important when designing multi-partition systems or tooling that must support commercial, China, or GovCloud environments.

AWS accounts in different partitions cannot directly delegate access to one another. :contentReference[oaicite:7]{index=7}

---

## Service

The service segment identifies the AWS service.

Examples:

```text
s3
sqs
sns
ec2
iam
lambda
dynamodb
secretsmanager
```

For example:

```text
arn:aws:lambda:ap-south-1:123456789012:function:invoice-generator
```

The service segment is not an arbitrary application label. It corresponds to the AWS service namespace.

---

## Region

The region segment identifies the resource's region when the service uses regional resources.

Example:

```text
arn:aws:ec2:ap-south-1:123456789012:instance/i-0123456789abcdef0
```

For IAM resources, the region segment is blank because IAM resource ARNs are global within an AWS partition:

```text
arn:aws:iam::123456789012:role/BackendRole
```

AWS explicitly documents the blank region field for IAM ARNs. :contentReference[oaicite:8]{index=8}

This difference matters when constructing policies programmatically.

---

## Account ID

The account segment identifies the AWS account associated with the resource.

Example:

```text
arn:aws:sqs:ap-south-1:123456789012:order-events
```

Here:

```text
123456789012
```

is the AWS account ID.

The exact presence and semantics of the account segment depend on the service.

---

## Resource Identifier

The final ARN segment identifies the resource.

Examples:

```text
role/BackendRole
```

```text
table/Orders
```

```text
order-events
```

```text
function:invoice-generator
```

The syntax is service-specific.

Do not assume all AWS resources use the same separator or naming pattern.

---

## Common ARN Examples

| AWS service | Example ARN |
|---|---|
| IAM role | `arn:aws:iam::123456789012:role/BackendRole` |
| IAM user | `arn:aws:iam::123456789012:user/alice` |
| S3 bucket | `arn:aws:s3:::company-assets` |
| S3 object | `arn:aws:s3:::company-assets/reports/report.pdf` |
| SQS queue | `arn:aws:sqs:ap-south-1:123456789012:order-events` |
| SNS topic | `arn:aws:sns:ap-south-1:123456789012:order-events` |
| Lambda function | `arn:aws:lambda:ap-south-1:123456789012:function:invoice-generator` |
| DynamoDB table | `arn:aws:dynamodb:ap-south-1:123456789012:table/Orders` |
| Secrets Manager secret | `arn:aws:secretsmanager:ap-south-1:123456789012:secret:prod/db` |
| EC2 instance | `arn:aws:ec2:ap-south-1:123456789012:instance/i-0123456789abcdef0` |

The important lesson is:

> Learn the ARN structure, but always use the target service's documented ARN format rather than inventing one.

---

## S3 ARN Differences

S3 is particularly important because a bucket and an object have different ARN forms.

Bucket:

```text
arn:aws:s3:::company-assets
```

Objects:

```text
arn:aws:s3:::company-assets/*
```

Specific object:

```text
arn:aws:s3:::company-assets/reports/report.pdf
```

For example:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::company-assets"
        },
        {
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::company-assets/reports/*"
        }
    ]
}
```

This distinction is important because bucket-level and object-level operations use different resource representations.

---

## ARN Wildcards

IAM supports wildcards in resource ARNs where the service authorization model permits them.

Common wildcard characters include:

```text
*
?
```

Example:

```text
arn:aws:s3:::company-assets/reports/*
```

This can match objects beneath the specified path.

AWS notes that `*` can expand across characters including `/` within an ARN segment, so wildcard scope should be reviewed carefully. :contentReference[oaicite:9]{index=9}

Prefer a specific prefix when only a subset of resources should be accessible.

Avoid:

```text
arn:aws:s3:::company-assets/*
```

when the application only needs:

```text
arn:aws:s3:::company-assets/reports/*
```

---

## ARN Wildcards vs Principal Wildcards

Resource wildcards and principal wildcards behave differently.

A resource ARN can use wildcard matching:

```text
arn:aws:s3:::company-assets/reports/*
```

However, AWS does not allow a wildcard to match only part of a principal name or ARN.

For example, this is not a supported pattern for matching arbitrary role names:

```json
{
    "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/*ServiceRole"
    }
}
```

AWS documents that principal wildcards cannot be used to match part of a principal name or ARN. :contentReference[oaicite:10]{index=10}

Use explicit principals or appropriate condition keys instead.

---

## IAM Paths

IAM users, groups, roles, and policies can have paths.

Example role ARN:

```text
arn:aws:iam::123456789012:role/backend/production/OrderServiceRole
```

The path can help organize identities:

```text
backend/
    production/
        OrderServiceRole
```

Paths can improve naming and administrative organization, but they do not automatically create an authorization boundary.

AWS notes that IAM does not enforce permissions boundaries based on paths alone. :contentReference[oaicite:11]{index=11}

Do not assume:

```text
role/backend/production/*
```

automatically means those roles are restricted to production resources.

Authorization still depends on policies.

---

## Policy Variables in ARNs

IAM policy variables can be used in the resource portion of supported ARN expressions.

Example:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "dynamodb:*",
            "Resource": "arn:aws:dynamodb:ap-south-1:123456789012:table/${aws:username}"
        }
    ]
}
```

Policy variables can be used in the resource portion of an ARN rather than replacing the earlier ARN components such as service or account. :contentReference[oaicite:12]{index=12}

This can support attribute-based or identity-dependent access patterns, but it should be used deliberately because dynamic policy expressions can make authorization logic harder to reason about.

---

## Principal, Resource and ARN Together

A useful policy mental model is:

```text
Principal
    "Who?"

Action
    "What operation?"

Resource
    "On what object?"

Condition
    "Under what circumstances?"

Effect
    "Allow or Deny?"
```

Example:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::123456789012:role/ReportingRole"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::company-reports/exports/*"
        }
    ]
}
```

Read it as:

```text
Principal:
    ReportingRole

Action:
    s3:GetObject

Resource:
    company-reports/exports/*

Effect:
    Allow
```

This simple decomposition is extremely useful when diagnosing authorization failures.

---

## Resource-Based Policy Example

Suppose account `123456789012` owns an S3 bucket and wants to allow an application role from account `555555555555` to read reports.

```mermaid
flowchart LR
    A[Account B] --> B[ReportingRole]
    B --> C[Cross-Account Request]
    C --> D[Account A S3 Bucket Policy]
    D --> E[Company Reports Bucket]
```

The bucket policy might contain:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowReportingRole",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::555555555555:role/ReportingRole"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::company-reports/exports/*"
        }
    ]
}
```

In a cross-account design, authorization also depends on the source account's identity permissions and the other applicable IAM controls.

The important architectural separation is:

```text
Source account
    ↓
Who is allowed to make the request?

Target account
    ↓
Which resource accepts that principal?

Both sides
    ↓
Effective authorization
```

---

## Role Trust Policies and Principals

IAM role trust policies are a special form of resource-based policy.

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

Here:

```text
Resource:
    IAM Role

Principal:
    ECS Tasks service

Action:
    sts:AssumeRole
```

The role's trust policy therefore answers:

> Which principal is allowed to become this role?

It does not grant the role permission to access S3, SQS, DynamoDB, or other services.

Those permissions belong in the role's permission policies.

---

## ARN vs Human-Readable Name

An AWS resource can have a friendly name:

```text
OrderServiceRole
```

while its ARN uniquely identifies it:

```text
arn:aws:iam::123456789012:role/OrderServiceRole
```

Use names for human operations where appropriate.

Use ARNs when authorization or API configuration needs an unambiguous resource identity.

For example:

```text
Human:
    OrderServiceRole

IAM Policy:
    arn:aws:iam::123456789012:role/OrderServiceRole
```

This distinction is especially important in multi-account environments where the same resource name may exist in different accounts.

---

## Global vs Regional Resources

AWS services can be global or regional, and this affects ARN construction and operational reasoning.

For IAM:

```text
arn:aws:iam::123456789012:role/BackendRole
```

There is no region component.

For a regional service such as SQS:

```text
arn:aws:sqs:ap-south-1:123456789012:order-events
```

the region is explicit.

This creates an important architectural distinction:

```text
Global IAM Identity
        |
        +----> ap-south-1 workload
        |
        +----> us-east-1 workload
        |
        +----> eu-west-1 workload
```

IAM resources themselves are global within an AWS partition, while many target resources are regional. :contentReference[oaicite:13]{index=13}

When writing region-restricting policies or SCPs, global services need special consideration because their ARNs and API semantics may not map to a normal regional resource.

---

## Backend Engineering Example

Consider a FastAPI service running in ECS:

```text
FastAPI
    ↓
ECS Task
    ↓
Task Role
    ↓
sqs:SendMessage
    ↓
arn:aws:sqs:ap-south-1:123456789012:order-events
```

The authorization model can be represented as:

```text
Principal:
    OrderServiceRole

Action:
    sqs:SendMessage

Resource:
    order-events queue ARN
```

A policy can therefore be scoped specifically to the queue:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sqs:SendMessage",
            "Resource": "arn:aws:sqs:ap-south-1:123456789012:order-events"
        }
    ]
}
```

This is preferable to giving the service broad SQS permissions across every queue in the account.

---

## Resource Scoping for Microservices

A microservice architecture can use resource-specific ARNs to create clear authorization boundaries.

```text
Order Service
    |
    +--> arn:aws:sqs:ap-south-1:123456789012:order-events

Payment Service
    |
    +--> arn:aws:sqs:ap-south-1:123456789012:payment-events

Notification Service
    |
    +--> arn:aws:sns:ap-south-1:123456789012:notifications
```

Each service role can then reference only the resources it requires.

This provides:

- Smaller blast radius
- Easier auditing
- Easier incident investigation
- Clearer ownership
- Better least-privilege enforcement

Resource naming and IAM design should therefore be considered together.

---

## Using `aws:PrincipalArn`

Advanced IAM designs sometimes use the `aws:PrincipalArn` condition key to further constrain access.

For example:

```json
{
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::company-reports/*",
    "Condition": {
        "ArnEquals": {
            "aws:PrincipalArn": "arn:aws:iam::123456789012:role/ReportingRole"
        }
    }
}
```

`aws:PrincipalArn` can be useful when designing resource policies and avoiding some of the lifecycle problems associated with directly embedding certain role principals.

AWS documents important behavioral differences between role principals and the `aws:PrincipalArn` condition key, so this pattern should be used with an understanding of the relevant policy evaluation rules rather than copied mechanically. :contentReference[oaicite:14]{index=14}

---

## Security Considerations

### Minimize Wildcards

Avoid unnecessarily broad resources:

```json
{
    "Effect": "Allow",
    "Action": "s3:*",
    "Resource": "*"
}
```

Prefer scoped access:

```json
{
    "Effect": "Allow",
    "Action": [
        "s3:GetObject",
        "s3:PutObject"
    ],
    "Resource": "arn:aws:s3:::company-reports/generated/*"
}
```

### Be Precise With Principals

A broad principal can be as dangerous as a broad resource.

Review both sides:

```text
Who can access?
    +
What can they access?
```

### Treat ARN Construction as Security-Sensitive

Incorrect ARNs can result in:

- Access being denied unexpectedly
- Access being granted to a broader set of resources than intended
- Cross-account authorization failures
- Production deployment failures

Infrastructure code should therefore construct and validate ARNs carefully.

---

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Treating a group as a principal | Groups look like identity objects | Remember that groups organize users and do not authenticate |
| Using `Principal: "*"` unintentionally | Fast way to make a policy work | Explicitly identify principals or constrain access with conditions |
| Assuming every ARN contains a region | Using one generic ARN template | Check the target service's ARN format |
| Granting `Resource: "*"` unnecessarily | Service examples often start broad | Scope the resource where the action supports it |
| Confusing bucket and object ARNs | S3 has different ARN patterns | Use bucket ARN for bucket APIs and object ARN for object APIs |
| Assuming IAM paths are security boundaries | Paths look hierarchical | Enforce boundaries through policies |
| Confusing role ARN with role-session ARN | Both represent role-related access | Understand role identity vs assumed-role session |
| Debugging only the role permissions | Trust may be the real failure | Check principal, trust policy, action, resource, and other authorization controls |
| Reusing resource names across accounts without checking ARNs | Names look identical | Use full ARNs when account or region context matters |

---

## Troubleshooting Workflow

When an AWS operation fails, decompose the request before modifying permissions.

```text
1. Identify the principal
        ↓
2. Identify the AWS account
        ↓
3. Identify the action
        ↓
4. Identify the resource ARN
        ↓
5. Check the relevant policy
        ↓
6. Check trust relationships if roles are involved
        ↓
7. Check conditions and request context
        ↓
8. Check broader authorization controls
```

For CLI sessions, start by verifying the actual identity:

```bash
aws sts get-caller-identity
```

Then inspect the requested resource and compare it with the policy.

For example:

```text
Expected:
arn:aws:iam::123456789012:role/OrderServiceRole

Actual:
arn:aws:iam::123456789012:role/DeveloperRole
```

A correct policy attached to `OrderServiceRole` does not help if the application is actually using `DeveloperRole`.

---

## Production Design Guidelines

For production IAM design:

- Define workload roles around explicit application responsibilities.
- Scope policies to the narrowest practical resource ARN.
- Prefer role principals over individual human identities for workload access.
- Avoid broad wildcard principals unless public or intentionally broad access is required.
- Validate service-specific ARN formats instead of assuming a generic structure.
- Treat resource names, account IDs, regions, and partitions as distinct concepts.
- Keep trust policies narrow and explicit.
- Use conditions when they materially improve authorization boundaries.
- Treat global IAM resources differently from regional service resources.
- Use infrastructure-as-code to make principal and resource relationships reviewable.
- During incidents, identify the actual principal and exact resource ARN before changing policy scope.

---

## Interview Perspective

### What Is a Principal?

A principal is an identity or supported entity that can participate in AWS authorization, such as an IAM user, IAM role, role session, AWS account, federated identity, or AWS service. Groups are not principals. :contentReference[oaicite:15]{index=15}

### What Is an ARN?

An ARN is the standardized identifier used to identify many AWS resources and follows a service-specific form based on:

```text
partition
service
region
account
resource
```

The exact format varies by service. :contentReference[oaicite:16]{index=16}

### Why Does IAM Use ARNs?

Resource names alone are not always globally unambiguous. ARNs provide a structured identifier containing account, service, region, and resource information where those dimensions apply.

### Why Does an IAM ARN Have No Region?

IAM resources are global within an AWS partition, so IAM ARNs leave the region field empty. :contentReference[oaicite:17]{index=17}

### Why Can `Resource` Be `*`?

Some AWS actions do not support resource-level authorization and therefore require a wildcard resource. A wildcard is also used intentionally when a policy is meant to cover multiple resources. The correct scope depends on the service authorization model. :contentReference[oaicite:18]{index=18}

### Can a Group Be a Principal?

No. An IAM group is a permissions-management object for users, not an authenticated principal that can make AWS requests. :contentReference[oaicite:19]{index=19}

---

## Reference Sources

- AWS IAM policy element — `Principal`: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_principal.html
- AWS IAM policy element — `Resource`: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_resource.html
- AWS IAM identifiers and ARN reference: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html
- AWS IAM policy element reference: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html
- AWS IAM condition context keys: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_iam-condition-keys.html

## Key Takeaways

- A **principal** answers "who is making the request," while a **resource** answers "what AWS object is being accessed"; IAM policies connect these concepts through actions and conditions.
- **ARNs provide structured resource identifiers** and must be interpreted according to the target AWS service rather than through one universal resource-name pattern.
- **IAM roles, role sessions, users, AWS accounts, federated identities, and AWS services can act as principals; IAM groups cannot.**
- Resource scope should be as narrow as practical, but `Resource: "*"` is sometimes required because certain AWS actions do not support resource-level permissions.
- Production IAM debugging should start with the **actual principal, exact action, exact resource ARN, account, region, trust relationships, and request context** before changing permissions.