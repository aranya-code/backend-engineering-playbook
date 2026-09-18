# 04- IAM Policy Basics

## Overview

An AWS IAM policy is a JSON document that defines permissions. Policies are the primary mechanism AWS uses to describe whether a principal can perform an action against a resource, optionally under specific conditions.

A useful mental model is:

```text
Principal
    ↓
Policy
    ├── Effect
    ├── Action
    ├── Resource
    └── Condition
            ↓
      Authorization Decision
```

For example:

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

This policy expresses a simple rule:

> Allow the identity to perform `s3:GetObject` against objects in the `company-reports` bucket.

Policies become more important as systems grow because production authorization usually involves multiple dimensions:

- Identity
- Action
- Resource
- Request context
- Conditions
- Multiple policy sources
- Account boundaries
- Organizational controls

The policy document is therefore not just configuration. It is part of the application's security model.

---

## What an IAM Policy Does

An IAM policy describes permissions using JSON.

The policy language supports several elements:

| Element | Purpose |
|---|---|
| `Version` | Specifies the policy language version |
| `Statement` | Contains one or more permission statements |
| `Sid` | Optional statement identifier |
| `Effect` | `Allow` or `Deny` |
| `Action` | AWS API actions to allow or deny |
| `Resource` | Resources to which the statement applies |
| `Principal` | Principal affected by a resource-based policy |
| `Condition` | Conditions under which the statement applies |

The exact elements allowed depend on the policy type. For example, `Principal` is used in resource-based policies and trust policies, while identity-based permission policies do not include an explicit `Principal` because the identity to which the policy is attached is already known. :contentReference[oaicite:0]{index=0}

A policy can contain multiple statements because different actions, resources, or conditions often require different authorization rules.

---

## Basic Policy Structure

A standard IAM policy commonly looks like this:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ReadReports",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::company-reports/reports/*"
            ]
        }
    ]
}
```

Conceptually:

```text
Policy
 ├── Version
 └── Statement[]
       ├── Sid
       ├── Effect
       ├── Action
       ├── Resource
       └── Condition
```

The JSON property ordering is not semantically significant. What matters is the policy structure and the values supplied to each element. :contentReference[oaicite:1]{index=1}

---

## Version

The `Version` element defines the version of the IAM policy language.

For new policies, use:

```json
"Version": "2012-10-17"
```

This should not be confused with **managed policy versioning**.

There are two different concepts:

```text
Policy language Version
    "2012-10-17"

Managed policy version
    v1
    v2
    v3
    ...
```

The former controls the policy language syntax and features. The latter represents revisions of a customer managed policy stored in IAM.

AWS currently identifies `2012-10-17` as the current policy language version and recommends using it for new policies. :contentReference[oaicite:2]{index=2}

---

## Statement

`Statement` contains one or more individual authorization rules.

A policy can contain a single statement:

```json
{
    "Version": "2012-10-17",
    "Statement": {
        "Effect": "Allow",
        "Action": "s3:GetObject",
        "Resource": "arn:aws:s3:::company-reports/*"
    }
}
```

or multiple statements:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::company-reports/*"
        },
        {
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::company-reports"
        }
    ]
}
```

Using separate statements is generally clearer when different permissions apply to different resources or have different conditions.

---

## Sid

`Sid` means **Statement ID**.

It is optional and can be used to make statements easier to identify.

Example:

```json
{
    "Sid": "AllowInvoiceRead",
    "Effect": "Allow",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::company-invoices/*"
}
```

Useful `Sid` values can improve:

- Code review
- Policy maintenance
- Troubleshooting
- Infrastructure-as-code diffs
- Human readability

Avoid meaningless identifiers such as:

```json
"Sid": "Statement1"
```

Prefer a purpose-oriented name:

```json
"Sid": "AllowInvoiceRead"
```

---

## Effect

`Effect` determines whether a statement allows or explicitly denies the specified operation.

Valid values are:

```text
Allow
Deny
```

Example:

```json
{
    "Effect": "Allow",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::company-reports/*"
}
```

Explicit deny:

```json
{
    "Effect": "Deny",
    "Action": "s3:DeleteObject",
    "Resource": "arn:aws:s3:::company-reports/*"
}
```

AWS authorization starts from an implicit deny, and an explicit `Deny` can override an applicable `Allow`. :contentReference[oaicite:3]{index=3}

The detailed interaction between multiple policy sources belongs to IAM policy evaluation, but the basic principle is essential:

```text
No applicable Allow
    → Denied

Applicable Allow
    → Potentially allowed

Applicable Explicit Deny
    → Denied
```

The word **potentially** matters because additional controls can still affect the final decision.

---

## Action

`Action` identifies the AWS API operation or operations covered by the statement.

Examples:

```text
s3:GetObject
s3:PutObject
sqs:SendMessage
dynamodb:GetItem
secretsmanager:GetSecretValue
ec2:DescribeInstances
```

A single statement can contain multiple actions:

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

This is useful when several operations have the same effect and apply to the same resource scope.

---

## Action Wildcards

Wildcards can reduce policy size, but they also increase permission scope.

For example:

```json
{
    "Effect": "Allow",
    "Action": "s3:Get*",
    "Resource": "arn:aws:s3:::company-reports/*"
}
```

This can be appropriate when all matching read operations are genuinely required.

However, avoid broad permissions such as:

```json
{
    "Effect": "Allow",
    "Action": "s3:*",
    "Resource": "*"
}
```

unless that broad access is explicitly required and governed by an appropriate administrative design.

For application roles, prefer the smallest action set that satisfies the workload.

---

## Resource

`Resource` identifies which AWS resources the statement applies to.

AWS generally identifies resources in policies using ARNs, although the exact ARN structure differs by service. :contentReference[oaicite:4]{index=4}

Example:

```json
{
    "Effect": "Allow",
    "Action": "sqs:SendMessage",
    "Resource": "arn:aws:sqs:ap-south-1:123456789012:order-events"
}
```

The meaning is:

```text
Action:
    sqs:SendMessage

Resource:
    order-events queue

Effect:
    Allow
```

A policy can specify multiple resources:

```json
{
    "Effect": "Allow",
    "Action": "sqs:SendMessage",
    "Resource": [
        "arn:aws:sqs:ap-south-1:123456789012:order-events",
        "arn:aws:sqs:ap-south-1:123456789012:retry-events"
    ]
}
```

---

## Resource Wildcards

Wildcards are useful when a policy should apply to multiple resources.

Example:

```json
{
    "Effect": "Allow",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::company-reports/reports/*"
}
```

This scopes access to objects below the `reports/` prefix.

Avoid unnecessarily broad resource scopes.

Prefer:

```text
arn:aws:s3:::company-reports/reports/*
```

over:

```text
arn:aws:s3:::company-reports/*
```

when the application only requires access to the `reports/` area.

AWS documents that resource ARN wildcards can be used to match multiple resources, but the exact behavior depends on the resource ARN structure. :contentReference[oaicite:5]{index=5}

---

## `Resource: "*"`

Some AWS actions do not support resource-level permissions and therefore require:

```json
"Resource": "*"
```

For example, certain account-level or service-wide discovery operations cannot be restricted to one resource ARN.

Therefore:

```text
Resource: "*"
```

does not automatically mean the policy is incorrectly designed.

The correct question is:

> Does this specific AWS action support resource-level authorization?

Always check the service authorization documentation when designing least-privilege policies.

---

## Principal

`Principal` identifies who receives permissions in a **resource-based policy**.

Example:

```json
{
    "Effect": "Allow",
    "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/ReportingRole"
    },
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::company-reports/*"
}
```

For an identity-based policy attached to a role, you do not specify:

```json
"Principal": ...
```

because the role receiving the policy is already the intended identity.

This distinction is fundamental:

```text
Identity-based policy
    Attached to identity
    Principal is implicit

Resource-based policy
    Attached to resource
    Principal is explicit
```

:contentReference[oaicite:6]{index=6}

---

## Condition

`Condition` adds contextual restrictions to a statement.

Example:

```json
{
    "Effect": "Allow",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::company-reports/*",
    "Condition": {
        "Bool": {
            "aws:MultiFactorAuthPresent": "true"
        }
    }
}
```

The statement is applicable only when the specified condition evaluates to true.

Conditions can evaluate context such as:

- Principal attributes
- Resource attributes
- Request source
- MFA state
- IP address
- Region
- Tags
- Time
- Organization information

AWS describes `Condition` as an optional element used to evaluate policy context keys with condition operators. :contentReference[oaicite:7]{index=7}

Conditions are particularly valuable when static `Action` and `Resource` matching is not sufficient.

---

## Condition Structure

A condition has three conceptual parts:

```text
Condition
    ↓
Operator
    ↓
Context Key
    ↓
Expected Value
```

Example:

```json
{
    "Condition": {
        "StringEquals": {
            "aws:RequestedRegion": "ap-south-1"
        }
    }
}
```

This means the statement applies only when the request context contains the requested region specified by the condition.

The exact semantics depend on the condition key and operator being used.

---

## Identity-Based Policy Example

Suppose an ECS task role needs to read application configuration from Secrets Manager.

A narrowly scoped policy could be:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ReadApplicationDatabaseSecret",
            "Effect": "Allow",
            "Action": "secretsmanager:GetSecretValue",
            "Resource": "arn:aws:secretsmanager:ap-south-1:123456789012:secret:prod/order-service/db-*"
        }
    ]
}
```

The application's request path is conceptually:

```text
ECS Task
    ↓
Task Role
    ↓
GetSecretValue
    ↓
Specific Secret ARN
    ↓
IAM Authorization
    ↓
Secret
```

The policy gives the workload permission without embedding an AWS access key in the application.

---

## Resource-Based Policy Example

S3 can use a bucket policy to specify access directly on the bucket.

Example:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowReportingRoleRead",
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

This policy differs from an identity-based policy because the policy is attached to the S3 resource and explicitly identifies the principal.

Resource-based policies are supported only by certain AWS services. :contentReference[oaicite:8]{index=8}

---

## Identity-Based vs Resource-Based Policies

| Property | Identity-based | Resource-based |
|---|---|---|
| Attached to | User, group, role | Supported AWS resource |
| `Principal` | Not used | Used |
| Primary question | What can this identity do? | Who can access this resource? |
| Common examples | Role permission policy | S3 bucket policy, SQS queue policy |
| Managed form | Managed or inline | Resource policies are inline |
| Cross-account use | Possible with additional configuration | Common pattern |

These two policy types are not interchangeable.

A strong AWS design often uses both.

For example:

```text
Application Role
    ↓
Identity Policy
    ↓
s3:GetObject

S3 Bucket
    ↓
Bucket Policy
    ↓
Allows trusted principal
```

The effective authorization still depends on the complete IAM evaluation model.

---

## Managed Policies

Managed policies are standalone policies that can be attached to multiple IAM identities.

There are two main categories:

```text
Managed Policies
    ├── AWS managed policies
    └── Customer managed policies
```

AWS also supports inline policies, which maintain a one-to-one relationship with the identity to which they are attached. :contentReference[oaicite:9]{index=9}

---

## AWS Managed Policies

AWS managed policies are created and maintained by AWS.

Example:

```text
arn:aws:iam::aws:policy/ReadOnlyAccess
```

Advantages:

- Quick to apply
- Maintained by AWS
- Useful for common AWS-wide permission sets
- Convenient for experimentation and certain operational roles

Limitations:

- You cannot customize their statements.
- They may grant more permissions than a specific application needs.
- Their contents can change as AWS updates them.

AWS explicitly notes that AWS managed policies are not designed to guarantee least privilege for a particular workload. :contentReference[oaicite:10]{index=10}

For production application roles, customer managed policies with workload-specific scope are often more appropriate.

---

## Customer Managed Policies

Customer managed policies are created and controlled by your organization.

Example:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublishOrderEvents",
            "Effect": "Allow",
            "Action": "sqs:SendMessage",
            "Resource": "arn:aws:sqs:ap-south-1:123456789012:order-events"
        }
    ]
}
```

Advantages:

- Precise permissions
- Reusable across multiple identities
- Organization-owned lifecycle
- Easier to align with application responsibilities

Typical production usage:

```text
Customer Managed Policy
        |
        +--> Order Service Role
        |
        +--> Worker Role
```

Use a shared managed policy only when the permission set genuinely represents a reusable responsibility.

Do not create a single giant policy containing unrelated permissions merely because it can be reused.

---

## Inline Policies

An inline policy is embedded directly into a specific IAM identity.

Example:

```text
OrderServiceRole
    └── Inline Policy
```

The policy has a strict one-to-one relationship with that identity.

Inline policies can be appropriate when:

- The permission is intentionally unique to one identity.
- You want the policy lifecycle coupled to the identity.
- Reuse is not desired.

AWS generally recommends managed policies instead of inline policies in most cases, while recognizing scenarios where inline policies are appropriate. :contentReference[oaicite:11]{index=11}

For infrastructure-as-code, the decision should be based on whether the permission set represents a reusable capability or an identity-specific exception.

---

## Managed vs Inline Policies

| Characteristic | AWS managed | Customer managed | Inline |
|---|---|---|---|
| Managed by | AWS | Your organization | Your organization |
| Reusable | Yes | Yes | No |
| Customizable | No | Yes | Yes |
| One-to-one with identity | No | No | Yes |
| Typical production use | Common baseline access | Preferred for custom reusable permissions | Specific identity-only exceptions |
| Least-privilege control | Limited | High | High |
| Lifecycle | AWS-controlled | Organization-controlled | Coupled to identity |

---

## Policy Versions

A customer managed policy can have multiple versions.

This is different from:

```json
"Version": "2012-10-17"
```

which refers to the IAM policy language.

For example:

```text
Policy
    ├── v1
    ├── v2
    └── v3
```

A change to a customer managed policy creates a new policy version rather than replacing the historical version representation in place. IAM allows a default policy version to be selected.

This is useful operationally because policy changes can be reviewed and managed as explicit revisions.

---

## Session Policies

A session policy is an additional policy that can be passed when creating a temporary role session.

Conceptually:

```text
Role Permissions
        +
Session Policy
        ↓
Effective Role Session Permissions
```

Session policies can restrict the permissions available to a session beyond those provided by the role's identity-based policies.

They are useful in delegated-access scenarios where the caller should receive a narrower set of permissions for a particular session.

A session policy does not turn a role into a broader permission source. It acts as an additional restriction on the session.

---

## Policy Variables

IAM policy variables allow supported runtime values to be substituted into policy elements.

Example:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::company-home/${aws:username}/*"
        }
    ]
}
```

Variables are useful when the same policy structure needs to operate against identity-specific or context-specific resources.

AWS notes that policy variables require the `2012-10-17` policy language version. :contentReference[oaicite:12]{index=12}

Use policy variables deliberately because dynamic authorization rules can become harder to understand and test than explicit resource mappings.

---

## Wildcards

Wildcards can be used in supported `Action` and `Resource` expressions.

Examples:

```text
s3:Get*
```

```text
arn:aws:s3:::company-reports/* 
```

They reduce policy size but increase matching scope.

A useful design progression is:

```text
Exact action
    ↓
Exact resource
    ↓
Small justified wildcard
    ↓
Broad wildcard only when necessary
```

Prefer explicit permissions for sensitive production workloads.

---

## Policy Composition

Production IAM rarely depends on one isolated policy.

A role may have:

```text
Role
 ├── Customer Managed Policy
 ├── Another Managed Policy
 ├── Inline Policy
 ├── Permissions Boundary
 └── Session Policy
```

And the AWS account may also be governed by broader controls such as:

```text
AWS Organizations
    ↓
Service Control Policy
```

The effective permissions are therefore the result of multiple authorization layers.

This is why adding an `Allow` statement does not always resolve an `AccessDenied` error.

Detailed policy evaluation rules should be treated separately from the basic policy syntax documented here.

---

## Policy Design for Backend Services

Consider a FastAPI service that publishes order events to SQS.

A focused customer managed policy could be:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublishOrderEvents",
            "Effect": "Allow",
            "Action": "sqs:SendMessage",
            "Resource": "arn:aws:sqs:ap-south-1:123456789012:order-events"
        }
    ]
}
```

The application then simply calls the AWS SDK:

```python
import boto3

sqs = boto3.client("sqs")

sqs.send_message(
    QueueUrl="https://sqs.ap-south-1.amazonaws.com/123456789012/order-events",
    MessageBody='{"order_id": "ORD-12345"}',
)
```

The service does not need to know the policy contents. Its runtime identity provides the authorization context.

This separation is desirable:

```text
Application code
    ↓
AWS SDK
    ↓
Runtime identity
    ↓
IAM policy
    ↓
AWS service
```

---

## Policy Design for Microservices

For a backend platform with multiple services:

```text
Order Service
    └── sqs:SendMessage → order-events

Worker Service
    ├── sqs:ReceiveMessage → order-events
    └── s3:PutObject → generated-reports/*

Reporting Service
    └── s3:GetObject → generated-reports/*
```

Do not create one shared policy such as:

```text
All Services
    └── s3:*
    └── sqs:*
    └── dynamodb:*
    └── secretsmanager:*
```

Instead, align policies with workload responsibilities.

This improves:

- Security isolation
- Auditing
- Incident response
- Permission review
- Change management
- Service ownership

---

## Policy Design Principles

### Start With the Required API Operations

Before writing a policy, identify:

```text
What does the application actually call?
```

For an S3 upload workflow:

```text
s3:PutObject
```

may be enough.

Do not start with:

```text
s3:*
```

and remove permissions later unless there is a specific reason to do so.

### Scope the Resource

Identify the exact resource or resource prefix required.

```text
Required:
    company-reports/generated/*

Avoid when unnecessary:
    company-reports/*
```

### Separate Responsibilities

A role that publishes SQS messages should not automatically receive permissions to:

- Delete SQS queues
- Modify IAM
- Read unrelated secrets
- Alter VPC infrastructure

### Keep Permissions Reviewable

A good policy should communicate its intent.

This is easier to review:

```json
{
    "Sid": "PublishOrderEvents",
    "Effect": "Allow",
    "Action": "sqs:SendMessage",
    "Resource": "arn:aws:sqs:ap-south-1:123456789012:order-events"
}
```

than a large wildcard policy with many unrelated actions.

---

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Using `Action: "*"` | Fast way to unblock development | List required actions |
| Using `Resource: "*"` everywhere | Easier than finding exact ARNs | Scope supported resources |
| Adding `Principal` to a role permission policy | Confusing policy types | Use `Principal` in resource-based policies and trust policies |
| Treating `Version` as policy revision | Confusing language version with managed-policy versions | Keep the two concepts separate |
| Using AWS managed policies blindly | Convenient defaults | Review actual permissions and use customer policies where appropriate |
| Creating huge reusable policies | Reuse is mistaken for good design | Reuse only coherent permission sets |
| Using inline policies for everything | Easy to attach during development | Prefer managed policies for reusable permissions |
| Forgetting conditions | Static permissions are easier to write | Add contextual restrictions when they materially improve security |
| Overusing wildcards | Shorter policies | Prefer precise actions and resources |
| Granting permissions to solve every failure | AccessDenied is treated as a simple missing Allow | Investigate the entire authorization path |

---

## Production Pitfalls

### Broad Application Policies

A role such as:

```text
AdministratorAccess
```

may solve immediate permission problems but creates a very large blast radius.

Application identities should normally have application-specific permissions.

### Shared Policies With Unrelated Responsibilities

Suppose a customer managed policy contains:

```text
S3
SQS
Secrets Manager
IAM
EC2
CloudFormation
```

and is attached to several unrelated roles.

A change intended for one application can unexpectedly affect others.

Use policy reuse around a coherent responsibility, not arbitrary aggregation.

### Permissions Hidden Inside Multiple Layers

When a role gets permissions from several managed and inline policies, the effective authorization model becomes harder to reason about.

Keep the permission structure understandable and document intentional exceptions.

### Ignoring Resource-Based Policies

A role may appear correctly configured while the destination resource has its own policy restricting access.

For services supporting resource-based policies, inspect both sides during authorization troubleshooting.

---

## Security Considerations

IAM policy design directly affects the blast radius of compromised workloads.

Consider these two designs:

```text
Application A
    ↓
One broad role
    ↓
All S3 buckets
All SQS queues
All Secrets
```

versus:

```text
Application A
    ↓
ApplicationARole
    ├── GetSecretValue → application secret
    ├── SendMessage → order queue
    └── PutObject → application bucket
```

The second model creates a narrower authorization boundary.

Security improvements should focus on:

- Least privilege
- Resource scoping
- Explicit trust relationships
- Minimal use of wildcard actions
- Minimal use of wildcard resources
- Temporary credentials for workloads
- Regular permission review
- Auditable policy changes

---

## Policy Review Checklist

Before deploying a policy to production, review:

```text
Identity
    ↓
What workload or team receives this policy?

Actions
    ↓
Are every action necessary?

Resources
    ↓
Can resources be narrowed?

Conditions
    ↓
Would request-context restrictions materially improve security?

Wildcards
    ↓
Are * patterns intentional?

Trust
    ↓
If a role is involved, who can assume it?

Reusability
    ↓
Should this be a customer managed policy or identity-specific inline policy?

Operations
    ↓
Can the policy be understood and audited six months from now?
```

---

## IAM Policy Tooling

AWS provides tooling that can help with policy authoring and analysis.

Useful operational tools include:

- IAM Policy Simulator
- IAM Access Analyzer
- AWS CLI
- CloudTrail
- Infrastructure-as-code validation and review pipelines

For local CLI validation, basic identity inspection is useful:

```bash
aws sts get-caller-identity
```

When a policy is managed through infrastructure-as-code, policy JSON should be reviewed alongside the resource and role definitions that consume it.

---

## Policy as Code

A production backend team should treat IAM policies as code when possible.

For example:

```text
Infrastructure Repository
    |
    ├── IAM roles
    ├── Customer managed policies
    ├── Trust policies
    └── Service resources
         |
         v
     Code Review
         |
         v
       CI/CD
         |
         v
      AWS Account
```

Advantages include:

- Version control
- Peer review
- Repeatability
- Auditability
- Change history
- Automated validation

Avoid making critical production IAM changes directly in the console without recording the intended configuration in the organization's infrastructure source of truth.

---

## Interview Perspective

### What Are the Core IAM Policy Elements?

The most important elements are:

```text
Version
Statement
Effect
Action
Resource
Principal
Condition
```

Not every element applies to every policy type. `Principal`, for example, is used in resource-based policies and trust policies rather than ordinary identity-based permission policies. :contentReference[oaicite:13]{index=13}

### Difference Between `Action` and `Resource`

```text
Action
    What operation is being requested?

Resource
    Which AWS object is targeted?
```

Example:

```text
s3:GetObject
+
arn:aws:s3:::company-reports/reports/*
```

### Difference Between `Effect: Allow` and `Effect: Deny`

```text
Allow
    Grants the specified permission when applicable.

Deny
    Explicitly blocks the specified permission.
```

An explicit deny has special significance during authorization evaluation. :contentReference[oaicite:14]{index=14}

### Why Use Customer Managed Policies?

They provide reusable, organization-controlled permission definitions that can be customized to the application's actual requirements. :contentReference[oaicite:15]{index=15}

### When Is an Inline Policy Useful?

When a permission set is intentionally unique to one identity and should maintain a strict one-to-one relationship with that identity. AWS generally recommends managed policies for most reusable permission scenarios. :contentReference[oaicite:16]{index=16}

### Why Is Least Privilege More Than Removing `*`?

Least privilege requires looking at the complete authorization model:

```text
Actions
    +
Resources
    +
Conditions
    +
Trust relationships
    +
Additional policy controls
```

A policy containing no wildcard can still grant excessive permissions if the resource or action set is broader than the workload requires.

---

## Practical Policy Template

A useful baseline for an application-specific permission policy is:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DescribePurposeClearly",
            "Effect": "Allow",
            "Action": [
                "service:RequiredAction"
            ],
            "Resource": [
                "arn:aws:service:region:account-id:resource"
            ],
            "Condition": {
                "StringEquals": {
                    "aws:RequestedRegion": "ap-south-1"
                }
            }
        }
    ]
}
```

Treat this as a structural template rather than a policy to copy unchanged.

The correct `Action`, `Resource`, and `Condition` values must come from the target service's authorization model and the actual workload requirements.

---

## Reference Sources

- AWS IAM policies and permissions: :contentReference[oaicite:17]{index=17}
- IAM JSON policy elements: :contentReference[oaicite:18]{index=18}
- IAM policy grammar: :contentReference[oaicite:19]{index=19}
- Identity-based and resource-based policies: :contentReference[oaicite:20]{index=20}
- Managed and inline policies: :contentReference[oaicite:21]{index=21}
- IAM `Effect` element: :contentReference[oaicite:22]{index=22}
- IAM `Resource` element: :contentReference[oaicite:23]{index=23}
- IAM `Condition` element: :contentReference[oaicite:24]{index=24}
- IAM policy variables: :contentReference[oaicite:25]{index=25}

## Key Takeaways

- An IAM policy is a JSON authorization document built around **Effect, Action, Resource, and optional Condition**, with `Principal` used where the policy type requires an explicit principal. 
- `Action` defines **what AWS operation** is permitted or denied, while `Resource` defines **which AWS object** the statement applies to.
- Prefer **least-privilege customer managed policies** for reusable application permissions; use AWS managed policies deliberately and reserve inline policies for identity-specific cases.
- Treat wildcards, resource scope, conditions, and policy composition as security-sensitive design decisions rather than syntax details.
- Manage production IAM policies as **reviewable infrastructure code** so permission changes are versioned, auditable, and tested alongside the systems they protect.