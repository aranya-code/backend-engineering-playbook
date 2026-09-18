# 07- Identity-Based Policies

## Overview

Identity-based policies are JSON permissions policies attached to AWS identities such as IAM users, groups of users, and IAM roles. They define **what an identity can do, which resources it can access, and under what conditions**. AWS evaluates these policies when the identity makes an AWS API request. :contentReference[oaicite:0]{index=0}

They are one of the two primary permission models in IAM:

```text
Identity-Based Policy
    ↓
Attached to User / Group / Role
    ↓
Defines permissions

Resource-Based Policy
    ↓
Attached to supported AWS Resource
    ↓
Defines which principals can access it
```

An identity-based policy answers:

> **What is this identity allowed to do?**

A resource-based policy answers:

> **Who can access this resource?**

This distinction is essential when designing backend workloads, debugging `AccessDenied`, and reasoning about cross-account authorization.

---

## What Is an Identity-Based Policy?

An identity-based policy is a JSON policy attached to an IAM identity.

Supported IAM identities include:

- IAM users
- IAM groups
- IAM roles

AWS classifies identity-based policies into:

```text
Identity-Based Policies
    ├── AWS Managed Policies
    ├── Customer Managed Policies
    └── Inline Policies
```

AWS documents all three as identity-based policy types. :contentReference[oaicite:1]{index=1}

A simple example:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ReadReports",
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::company-reports/reports/*"
        }
    ]
}
```

If this policy is attached to `ReportingRole`, it means that the role's identity-based permissions include the ability to perform `s3:GetObject` against the matching resources, subject to the rest of IAM evaluation.

---

## Why Identity-Based Policies Exist

IAM needs a mechanism to express permissions around an identity.

A workload identity should be able to express:

```text
This service can:
    Read these S3 objects
    Send messages to this SQS queue
    Read this secret
```

without embedding those permissions into application code.

That produces a clean separation:

```text
Application
    ↓
AWS SDK
    ↓
Workload Identity
    ↓
Identity-Based Policy
    ↓
AWS Authorization
    ↓
AWS Resource
```

The application requests an AWS operation. IAM determines whether the runtime identity is authorized to perform it.

---

## Where Identity-Based Policies Are Attached

### IAM Users

A user can have identity-based policies attached directly.

```text
IAM User
    ↓
Policy
```

Users can also receive permissions through group membership.

```text
IAM User
    ↓
IAM Group
    ↓
Group Policy
```

For modern workforce environments, centralized identity and IAM Identity Center are commonly preferred over maintaining large collections of IAM users.

### IAM Groups

Policies can be attached to groups.

```text
Backend Developers
    ↓
DeveloperPermissions
    ├── User A
    ├── User B
    └── User C
```

A group policy therefore contributes to the permissions of users belonging to that group.

### IAM Roles

Roles are the most important identity-based policy target for backend workloads.

```text
ECS Task
    ↓
IAM Role
    ↓
Identity-Based Policy
    ↓
Temporary Credentials
    ↓
AWS API
```

This is the normal pattern for many AWS applications.

---

## Identity-Based Policies Do Not Contain `Principal`

A major structural distinction is that an identity-based policy does not specify a `Principal`.

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

There is no:

```json
"Principal": "..."
```

because the policy is already attached to the identity receiving the permissions.

Compare the two models:

```text
Identity-Based Policy

Role
  ↓
Policy
  ↓
Action + Resource


Resource-Based Policy

Resource
  ↓
Policy
  ↓
Principal + Action + Resource
```

AWS explicitly documents that identity-based policies do not specify a principal because the policy is attached to the identity to which the permissions apply. :contentReference[oaicite:2]{index=2}

---

## Basic Structure

A typical identity-based policy contains:

```text
Version
Statement
    ├── Sid
    ├── Effect
    ├── Action
    ├── Resource
    └── Condition
```

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

Conceptually:

```text
Effect
    What happens?

Action
    What API operation?

Resource
    Which AWS resource?

Condition
    Under what request context?
```

The `Principal` is implicit from the identity to which the policy is attached.

---

## Managed and Inline Identity-Based Policies

Identity-based policies have three operational forms.

| Type | Managed by | Reusable | Relationship |
|---|---|---:|---|
| AWS managed | AWS | Yes | Standalone |
| Customer managed | Your organization | Yes | Standalone |
| Inline | Your organization | No | One-to-one with identity |

AWS documents these as the three identity-based policy categories. :contentReference[oaicite:3]{index=3}

---

## AWS Managed Policies

AWS managed policies are created and maintained by AWS.

Example:

```text
arn:aws:iam::aws:policy/ReadOnlyAccess
```

They are convenient when a standard AWS-defined permission set is suitable.

Advantages:

- Fast to attach
- Maintained by AWS
- Reusable across identities
- Useful for common AWS use cases

Limitations:

- You cannot edit the policy.
- The policy may contain permissions broader than a specific application requires.
- The policy can change as AWS updates it.

AWS explicitly notes that AWS managed policies do not necessarily implement least privilege for a particular workload. :contentReference[oaicite:4]{index=4}

For production application roles, review the actual permissions rather than assuming an AWS managed policy is the correct scope.

---

## Customer Managed Policies

Customer managed policies are standalone policies created and controlled by your organization.

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

They can be attached to multiple identities.

```text
Customer Managed Policy
        |
        +----> OrderServiceRole
        |
        +----> OrderWorkerRole
```

Use customer managed policies when the permission set represents a reusable responsibility that your organization wants to control.

Examples:

```text
OrderEventPublisher
ReportingReader
ApplicationSecretReader
DeploymentOperator
```

AWS documents customer managed policies as standalone policies that you create, modify, and attach to multiple identities. :contentReference[oaicite:5]{index=5}

---

## Inline Policies

An inline policy is embedded directly into a specific IAM identity.

```text
OrderServiceRole
    ↓
Inline Policy
```

The policy maintains a strict one-to-one relationship with that identity and is deleted with the identity. :contentReference[oaicite:6]{index=6}

Inline policies are useful when:

- The permission is intentionally unique to one identity.
- Reuse is not desirable.
- The policy lifecycle should be tied directly to the identity.

Example:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "SpecificApplicationPermission",
            "Effect": "Allow",
            "Action": "sqs:SendMessage",
            "Resource": "arn:aws:sqs:ap-south-1:123456789012:legacy-special-queue"
        }
    ]
}
```

For reusable permission sets, a customer managed policy is usually easier to manage.

---

## Groups and Policy Inheritance

IAM users can receive permissions from policies attached to groups.

Example:

```text
DeveloperGroup
    |
    ├── Policy A
    └── Policy B
          |
          +---- User A
          +---- User B
          +---- User C
```

The user effectively receives permissions from applicable policies attached directly to the user and through group membership.

For example:

```text
User
    +
Group A
    +
Group B
    ↓
Applicable Identity-Based Permissions
```

This makes groups useful for common human access patterns.

For application workloads, roles are generally a better identity boundary than trying to model applications through IAM users and groups.

---

## Role Policies

Roles commonly use identity-based policies to define the permissions available to workloads.

Example:

```text
OrderServiceRole
    |
    +── Allow sqs:SendMessage
    |
    +── Allow secretsmanager:GetSecretValue
    |
    +── Allow s3:PutObject
```

A role policy does not determine who can assume the role.

That is controlled by the role's trust policy.

```text
Trust Policy
    "Who can assume this role?"

Identity-Based Permission Policy
    "What can this role do?"
```

Both concerns must be correct.

---

## Identity-Based Permission Policy vs Trust Policy

These are frequently confused.

### Permission Policy

Example:

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

This controls what the role can do.

### Trust Policy

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

This controls who can assume the role.

The separation is:

```text
Assume Role
    ↓
Trust Policy

Use Role Permissions
    ↓
Identity-Based Policy
```

---

## Identity-Based Policies in Backend Applications

A backend service should normally use a role whose identity-based policy expresses the service's AWS capabilities.

Example:

```text
FastAPI
    ↓
ECS Task
    ↓
OrderServiceRole
    ↓
Identity-Based Policies
    ├── SQS SendMessage
    ├── Secrets Manager GetSecretValue
    └── S3 PutObject
```

The Python application itself remains independent of the policy document.

```python
import boto3

sqs = boto3.client("sqs")

sqs.send_message(
    QueueUrl="https://sqs.ap-south-1.amazonaws.com/123456789012/order-events",
    MessageBody='{"order_id": "ORD-10001"}',
)
```

The AWS SDK obtains credentials from the runtime environment and AWS evaluates the request using the workload's identity.

---

## Least-Privilege Identity-Based Policies

The policy should reflect the actual application capability.

Suppose a worker needs:

```text
Receive messages
Delete messages
Read one secret
Write reports
```

A focused policy could be:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ConsumeOrderQueue",
            "Effect": "Allow",
            "Action": [
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes"
            ],
            "Resource": "arn:aws:sqs:ap-south-1:123456789012:order-events"
        },
        {
            "Sid": "ReadDatabaseSecret",
            "Effect": "Allow",
            "Action": "secretsmanager:GetSecretValue",
            "Resource": "arn:aws:secretsmanager:ap-south-1:123456789012:secret:prod/order-worker/db-*"
        },
        {
            "Sid": "WriteGeneratedReports",
            "Effect": "Allow",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::company-reports/generated/*"
        }
    ]
}
```

This is preferable to:

```json
{
    "Effect": "Allow",
    "Action": "*",
    "Resource": "*"
}
```

because each permission maps to an identifiable workload responsibility.

---

## Multiple Identity-Based Policies

An identity can have multiple identity-based policies.

For example:

```text
OrderServiceRole
    |
    +── OrderQueuePolicy
    |
    +── ApplicationSecretPolicy
    |
    +── ReportingBucketPolicy
```

The resulting permission set is determined by the applicable policies together.

A role could therefore receive:

```text
Policy A
    sqs:SendMessage

Policy B
    secretsmanager:GetSecretValue

Policy C
    s3:PutObject
```

This is useful when permission sets have clear ownership or reuse boundaries.

However, excessive fragmentation can make the role difficult to audit.

---

## Policy Attachment Strategy

A practical design is:

```text
Reusable permission set
    ↓
Customer managed policy

Identity-specific exception
    ↓
Inline policy
```

For example:

```text
ReportingReader
    ↓
Customer Managed Policy
    ↓
ReportingRole
```

while:

```text
LegacyServiceRole
    ↓
Inline Policy
    ↓
Unique legacy permission
```

Avoid creating dozens of tiny policies with no reuse or ownership boundary merely to make each statement a separate object.

Policy organization should optimize for reviewability and operational clarity.

---

## Identity-Based Policies and Resource-Based Policies

Identity-based and resource-based policies can work together.

Example:

```text
Application Role
    ↓
Identity-Based Policy
    ↓
s3:GetObject
    ↓
S3 Bucket
    ↑
Resource-Based Policy
    ↑
Application Role
```

The exact evaluation rules depend on the principal, account relationship, and other applicable policy types. AWS documents that same-account identity-based and resource-based policies can contribute to authorization, with explicit denies overriding allows. :contentReference[oaicite:7]{index=7}

Do not reduce the model to:

```text
Both policies must contain Allow
```

That is not universally correct.

Cross-account access has additional requirements, and resource-based policies have principal-specific evaluation behavior.

---

## Permissions Boundaries

Identity-based policies can be constrained by a permissions boundary.

Conceptually:

```text
Identity-Based Policy
        ∩
Permissions Boundary
        ↓
Effective Identity Permissions
```

Example:

```text
Role Policy
    s3:GetObject
    s3:PutObject
    s3:DeleteObject

Boundary
    s3:GetObject
    s3:PutObject

Effective
    s3:GetObject
    s3:PutObject
```

A permissions boundary does not grant permissions by itself.

AWS documents the effective permissions as the intersection of permissions granted by identity-based policies and permissions allowed by the boundary. :contentReference[oaicite:8]{index=8}

---

## Identity-Based Policies and SCPs

An identity-based allow can also be constrained by an AWS Organizations service control policy.

Conceptually:

```text
Role Identity Policy
        ∩
Permissions Boundary
        ∩
Organization SCP
        ↓
Effective Permissions
```

Suppose a role allows:

```text
ec2:RunInstances
```

but an organization policy prevents the requested operation.

The role policy alone does not override the organizational restriction.

AWS documents SCPs as maximum-permission guardrails for IAM users and roles in affected accounts. :contentReference[oaicite:9]{index=9}

---

## Session Policies

A temporary role session can also have a session policy that narrows the available permissions.

Conceptually:

```text
Role Identity Policy
        ∩
Permissions Boundary
        ∩
Session Policy
        ↓
Session Effective Permissions
```

This is useful for delegated or temporary access where the caller should receive only a subset of the role's normal permissions.

AWS documents session policies as an additional restriction applied to temporary role or federated-user sessions. :contentReference[oaicite:10]{index=10}

---

## Identity-Based Policies and Request Context

An identity-based policy can use conditions to make a permission context-dependent.

Example:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ReadReportsFromApprovedRegion",
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::company-reports/*",
            "Condition": {
                "StringEquals": {
                    "aws:RequestedRegion": "ap-south-1"
                }
            }
        }
    ]
}
```

The policy does not simply say:

```text
Role can read reports
```

It says:

```text
Role can read reports
when the relevant request context matches
```

AWS evaluates conditions against request context for all applicable policies. :contentReference[oaicite:11]{index=11}

---

## Identity-Based Policies and ABAC

Identity-based policies can participate in attribute-based access control patterns using policy variables and condition keys.

For example, access can be based on tags or principal attributes rather than maintaining a separate policy for every resource.

Conceptually:

```text
Principal Attributes
        +
Resource Attributes
        ↓
Policy Conditions
        ↓
Authorization
```

A tag-based design might use:

```text
Environment = production
Team = payments
```

to constrain access.

ABAC can reduce policy proliferation in large environments, but it introduces an additional dependency: **authorization now depends on the correctness and lifecycle of metadata**.

If tags are wrong, missing, or inconsistently maintained, authorization behavior can also become inconsistent.

---

## Identity-Based Policies in Multi-Account Architecture

A common AWS organization structure is:

```text
AWS Organization
    |
    +── Development
    |
    +── Staging
    |
    +── Production
```

Each account may contain workload roles with identity-based policies.

For example:

```text
Production Account
    |
    +── OrderServiceRole
    |      └── Production resources
    |
    +── ReportingRole
           └── Reporting resources
```

Cross-account access is then established separately through trusted roles and resource policies where required.

This keeps workload permissions local to the account while allowing controlled delegation across account boundaries.

---

## Identity-Based Policies and CI/CD

CI/CD systems commonly receive AWS access through roles.

Example:

```text
GitHub Actions
    ↓
OIDC Federation
    ↓
Deployment Role
    ↓
Identity-Based Policy
    ├── ECR
    ├── ECS
    └── CloudFormation
```

The deployment role might have:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DeployApplication",
            "Effect": "Allow",
            "Action": [
                "ecs:RegisterTaskDefinition",
                "ecs:UpdateService",
                "ecr:GetAuthorizationToken"
            ],
            "Resource": "*"
        }
    ]
}
```

The resource scope for each action should be determined from the AWS service authorization model. Some actions require `Resource: "*"` because they do not support resource-level permissions.

Avoid using a developer's personal IAM user access keys for CI/CD.

---

## Identity-Based Policies and Kubernetes

In EKS environments, a Kubernetes workload can use an AWS IAM role through an AWS-supported workload identity mechanism.

Conceptually:

```text
Kubernetes Pod
    ↓
Workload Identity
    ↓
IAM Role
    ↓
Identity-Based Policy
    ↓
AWS API
```

This lets the application use AWS services without embedding a static AWS access key in the container.

The authorization boundary becomes:

```text
Kubernetes Workload
    ↓
Dedicated IAM Role
    ↓
Required AWS Actions
    ↓
Required AWS Resources
```

This pattern is particularly useful for microservices running on Kubernetes because different workloads can receive different AWS permissions.

---

## Policy Lifecycle

A production identity-based policy should have a controlled lifecycle.

```mermaid
flowchart LR
    A[Requirement] --> B[Permission Design]
    B --> C[Policy as Code]
    C --> D[Code Review]
    D --> E[Validation / Simulation]
    E --> F[Deployment]
    F --> G[Monitoring]
    G --> H[Access Review]
    H --> B
```

A permission should have:

- A clear owner
- A documented purpose
- A controlled change process
- A review mechanism
- A removal path when no longer required

This is especially important for customer managed policies reused across multiple workloads.

---

## Policy as Code

IAM policies are strong candidates for infrastructure-as-code workflows.

Example repository structure:

```text
infrastructure/
    iam/
        policies/
            order-service.json
            reporting-reader.json
        roles/
            order-service-role.tf
            reporting-role.tf
```

A typical workflow:

```text
Policy Change
    ↓
Git Commit
    ↓
Pull Request
    ↓
Review
    ↓
Validation
    ↓
Deployment
```

This provides:

- Version history
- Peer review
- Repeatability
- Auditable changes
- Easier rollback
- Better environment consistency

For production IAM, policy changes should not depend exclusively on manual console operations.

---

## Testing Identity-Based Policies

IAM policy behavior should be tested before granting production access.

The IAM Policy Simulator can test identity-based policies and several other policy types without sending a real request to the target AWS service. :contentReference[oaicite:12]{index=12}

Conceptually:

```text
Policy
    +
Principal
    +
Action
    +
Resource
    +
Optional Context
    ↓
Policy Simulation
    ↓
Allow / Deny
```

For production workflows, combine simulation with:

- Infrastructure-as-code validation
- Code review
- Integration testing
- Access monitoring
- Runtime troubleshooting

Simulation is not a replacement for validating the full production authorization context.

---

## Troubleshooting Identity-Based Policies

When a role unexpectedly receives `AccessDenied`, inspect the identity-based policy first, but do not stop there.

Start with:

```bash
aws sts get-caller-identity
```

Then verify:

```text
1. Actual principal
2. Requested action
3. Requested resource
4. Attached managed policies
5. Inline policies
6. Permissions boundary
7. Session policy
8. SCP / RCP where applicable
9. Resource-based policy
10. Conditions
11. Cross-account configuration
```

Useful inspection commands include:

```bash
aws iam get-role \
    --role-name OrderServiceRole
```

```bash
aws iam list-attached-role-policies \
    --role-name OrderServiceRole
```

```bash
aws iam list-role-policies \
    --role-name OrderServiceRole
```

The objective is to determine whether the policy actually matches the request rather than simply adding more permissions.

---

## Example: Diagnosing an `AccessDenied`

Suppose a Django application running in ECS attempts:

```text
s3:GetObject
```

and receives:

```text
AccessDenied
```

Start with the runtime identity:

```bash
aws sts get-caller-identity
```

Expected:

```text
arn:aws:sts::123456789012:assumed-role/ReportingRole/django-task
```

Then compare the actual request with the identity-based policy:

```text
Requested action:
    s3:GetObject

Requested resource:
    arn:aws:s3:::company-reports/generated/report.pdf

Policy:
    s3:GetObject
    arn:aws:s3:::company-reports/generated/*
```

If these match, inspect additional controls:

```text
Permissions boundary
SCP / RCP
Resource policy
Condition keys
Cross-account relationship
```

Do not immediately broaden the policy to:

```text
s3:*
```

---

## Security Considerations

Identity-based policies are part of the workload's security boundary.

A broad role policy increases the blast radius of a compromised application.

### Broad Access

```text
OrderServiceRole
    ↓
s3:*
    ↓
Every accessible S3 resource
```

### Scoped Access

```text
OrderServiceRole
    ↓
s3:PutObject
    ↓
company-orders/generated/*
```

The second model makes the intended capability much clearer.

### Protect High-Impact Permissions

Certain permissions deserve additional scrutiny because they can affect identities or infrastructure.

Examples include:

```text
iam:PassRole
iam:CreateRole
iam:AttachRolePolicy
iam:PutRolePolicy
iam:CreatePolicyVersion
cloudformation:CreateStack
```

These permissions can become part of privilege-escalation paths if combined carelessly.

---

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Adding `Principal` to an identity policy | Confusing identity and resource policies | Let attachment define the principal |
| Giving every workload `AdministratorAccess` | Fastest way to remove permission errors | Create workload-specific permissions |
| Using the same broad role for many services | Reduces initial setup effort | Give services separate roles |
| Assuming role policy is the entire authorization model | Policy is visible directly on the role | Check boundaries, SCPs, resource policies, and sessions |
| Forgetting group-derived permissions | Only user-attached policies are inspected | Inspect group membership |
| Reusing an unrelated customer managed policy | Reuse is mistaken for good abstraction | Reuse only coherent permission sets |
| Using inline policies everywhere | Easy during initial setup | Use managed policies for reusable permissions |
| Ignoring `iam:PassRole` | Deployment failures appear unrelated | Check role-passing permissions |
| Using static credentials in applications | Familiar authentication model | Use workload roles and temporary credentials |
| Never removing unused permissions | Permissions accumulate over time | Perform regular access reviews |

---

## Production Design Guidance

For backend systems:

- Prefer IAM roles over IAM users for workloads.
- Keep identity-based policies narrowly aligned with application responsibilities.
- Use customer managed policies when a permission set is reusable and organization-controlled.
- Use inline policies selectively for identity-specific exceptions.
- Avoid large policies containing unrelated AWS services.
- Scope `Action` and `Resource` independently.
- Use conditions where they materially improve authorization boundaries.
- Treat permissions such as `iam:PassRole` as security-sensitive.
- Use policy-as-code and peer review for production IAM changes.
- Test policy behavior before deployment.
- Regularly review permissions for unused or unnecessary access.
- Investigate `AccessDenied` across the complete evaluation path rather than repeatedly broadening role policies.

---

## Comparison: Identity-Based vs Resource-Based

| Characteristic | Identity-Based Policy | Resource-Based Policy |
|---|---|---|
| Attached to | User, group, role | Supported AWS resource |
| Specifies `Principal` | No | Yes |
| Primary question | What can this identity do? | Who can access this resource? |
| Common example | ECS task role policy | S3 bucket policy |
| Managed policies | Yes | No, resource policies are embedded in the resource configuration |
| Inline form | Yes | Resource policy itself is attached to resource |
| Common workload use | Very common | Common for resource sharing and cross-account access |

AWS explicitly distinguishes these policy types by where they are attached and how they define permissions. :contentReference[oaicite:13]{index=13}

---

## Interview Perspective

### What Is an Identity-Based Policy?

A JSON policy attached to an IAM user, group, or role that defines what the identity can do on specified resources, optionally subject to conditions. :contentReference[oaicite:14]{index=14}

### Does an Identity-Based Policy Contain `Principal`?

No. The policy is attached to the identity receiving the permission, so the principal is implicit. :contentReference[oaicite:15]{index=15}

### What Are the Three Types of Identity-Based Policies?

```text
AWS Managed
Customer Managed
Inline
```

AWS and customer managed policies are standalone policies; inline policies have a strict one-to-one relationship with an IAM identity. :contentReference[oaicite:16]{index=16}

### Why Prefer Customer Managed Policies for Reusable Permissions?

Because the organization controls their content and lifecycle and can attach the same coherent permission set to multiple identities. :contentReference[oaicite:17]{index=17}

### Does an Identity-Based Policy Guarantee Access?

No.

The final result can be constrained by:

```text
Resource policies
Permissions boundaries
Session policies
SCPs
RCPs
Explicit denies
Conditions
Cross-account requirements
```

AWS evaluates all applicable policy types in the context of the request. :contentReference[oaicite:18]{index=18}

### Does a Permissions Boundary Grant Permissions?

No.

It limits the maximum permissions an identity-based policy can grant. The identity still needs applicable permission to perform the action. :contentReference[oaicite:19]{index=19}

---

## Senior-Level Mental Model

A useful senior-level model is:

```text
Workload
    ↓
IAM Principal
    ↓
Identity-Based Permissions
    ↓
        +----------------------+
        |                      |
Permissions Boundary      Session Policy
        |                      |
        +----------+-----------+
                   ↓
             Organization
             SCP / RCP
                   ↓
          Resource Policy
                   ↓
          Request Context
                   ↓
        Final Authorization
```

The important engineering lesson is that identity-based policies are **one layer in the authorization model**.

For simple applications:

```text
Role
    ↓
Identity Policy
    ↓
AWS Resource
```

For production organizations:

```text
Role
    ↓
Identity Policy
    ↓
Permissions Boundary
    ↓
Session Constraints
    ↓
Organization Controls
    ↓
Resource Policy
    ↓
Request Context
```

The more layers a system introduces, the more important systematic policy analysis becomes.

## Key Takeaways

- **Identity-based policies are attached to IAM users, groups, and roles and define what those identities can do on AWS resources.**
- Identity-based policies do **not** specify `Principal`; the identity receiving the policy establishes the principal context.
- AWS provides **AWS managed, customer managed, and inline** identity-based policies, with customer managed policies offering controlled, reusable permission sets.
- An identity-based policy is only one part of authorization; **permissions boundaries, session policies, SCPs, RCPs, resource policies, conditions, and explicit denies** can affect the final decision.
- For production backends, use **role-based identities, narrowly scoped permissions, policy-as-code, and systematic troubleshooting** instead of broad policies or long-lived credentials.