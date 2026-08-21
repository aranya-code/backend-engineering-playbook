# 07- VPC Endpoint Policies

## Overview

VPC endpoints provide private connectivity from resources inside a VPC to supported AWS services without requiring traffic to traverse the public internet. A **VPC endpoint policy** adds an authorization layer that controls which AWS resources and actions can be accessed through an endpoint.

This is different from the endpoint's routing behavior and different from IAM permissions.

A useful mental model is:

```text
Application
    |
    | IAM credentials
    v
IAM Policy
    |
    v
VPC Endpoint
    |
    | Endpoint Policy
    v
AWS Service
    |
    | Resource Policy, where applicable
    v
Target Resource
```

For example, a private application may need access to only one S3 bucket:

```text
Private EC2 / ECS / EKS
        |
        v
VPC Endpoint
        |
        | Endpoint Policy
        | Allow bucket-a only
        v
Amazon S3
```

The endpoint policy can prevent the workload from using that endpoint to access unrelated S3 resources even when the workload's IAM identity has broader permissions.

Endpoint policies are therefore useful for **defense in depth, workload isolation, and reducing the blast radius of compromised credentials**.

---

## What a VPC Endpoint Policy Is

A VPC endpoint policy is an IAM-style resource policy attached to a VPC endpoint.

It defines which requests are allowed through that endpoint.

Conceptually:

```text
Request
   |
   +-- Does routing reach the endpoint?
   |
   +-- Does IAM permit the action?
   |
   +-- Does the endpoint policy permit the request?
   |
   +-- Does the AWS service/resource policy permit it?
   |
   v
AWS service operation
```

The exact authorization behavior depends on the AWS service and endpoint type, but the important engineering principle is that **an endpoint policy does not replace IAM**.

A request generally needs to satisfy all relevant authorization layers.

---

## Why Endpoint Policies Exist

Without an endpoint policy, a private endpoint may provide connectivity to an AWS service without sufficiently constraining which resources can be accessed through that path.

Consider an application with:

```text
IAM permissions:

s3:GetObject
Resource:
arn:aws:s3:::*
```

The application can potentially access many S3 buckets permitted by its identity policy.

An endpoint policy can provide an additional boundary:

```text
VPC Endpoint
    |
    +-- Allow access only to:
        arn:aws:s3:::company-production-assets
```

This does not make the IAM policy safe by itself. Instead, it creates another authorization boundary.

The principle is:

> IAM answers what the identity is allowed to do; the endpoint policy can constrain what can be done through a particular VPC endpoint.

---

## Endpoint Policy vs IAM Policy

These policies operate at different points in the authorization model.

| Property | IAM Identity Policy | VPC Endpoint Policy |
|---|---|---|
| Attached to | User, role, group, workload identity | VPC endpoint |
| Primary scope | Identity | Network access path |
| Controls | What identity can request | What can be requested through endpoint |
| Useful for workload isolation | Yes | Yes |
| Can replace IAM | No | No |
| Network-path aware | No | Yes |
| Typical purpose | Least privilege for identity | Restrict endpoint usage |

A strong production architecture commonly uses both.

```text
Application Role
    |
    +-- IAM Policy
    |      |
    |      +-- Allowed actions
    |
    v
VPC Endpoint
    |
    +-- Endpoint Policy
           |
           +-- Allowed resources/actions through this path
```

---

## Endpoint Policy vs Security Group

Security Groups control network traffic.

Endpoint policies control authorization to the AWS service through the endpoint.

For example:

```text
Security Group
    |
    +-- Allows TCP connectivity to endpoint ENI
```

while:

```text
Endpoint Policy
    |
    +-- Allows s3:GetObject
    +-- Allows only approved bucket
```

These controls solve different problems.

| Control | Answers |
|---|---|
| Route table | Where does traffic go? |
| Security Group | Can network traffic reach the resource? |
| NACL | Is traffic allowed across the subnet boundary? |
| IAM | Is this identity authorized? |
| Endpoint Policy | Is this request allowed through this endpoint? |
| Resource Policy | Is this resource willing to authorize the request? |

This layered model is important when troubleshooting private AWS service access.

---

## Gateway Endpoints vs Interface Endpoints

Endpoint policies are associated with supported VPC endpoint types, but the operational model differs between gateway and interface endpoints.

| Endpoint type | Typical services | Network model | Common use |
|---|---|---|---|
| Gateway endpoint | S3, DynamoDB | Route-table based | Private access from VPC to supported services |
| Interface endpoint | Many AWS services | ENI with private IP addresses | Private connectivity to AWS APIs |

Gateway endpoints are especially common for:

```text
EC2 / ECS / EKS
    |
    v
S3
```

Interface endpoints are commonly used for services such as:

```text
EC2
    |
    v
Interface Endpoint ENI
    |
    v
AWS API
```

The exact services and endpoint-policy capabilities should be validated against the current AWS service documentation before deployment.

---

## How Endpoint Policies Work

A simplified request flow is:

```mermaid
sequenceDiagram
    participant App as Application
    participant IAM as IAM
    participant EP as VPC Endpoint
    participant AWS as AWS Service
    participant Resource as AWS Resource

    App->>IAM: Request using workload credentials
    IAM-->>App: Identity authorization context
    App->>EP: Private service request
    EP->>EP: Evaluate endpoint policy
    EP->>AWS: Authorized request
    AWS->>AWS: Evaluate service authorization
    AWS->>Resource: Access target resource
    Resource-->>AWS: Response
    AWS-->>App: Response
```

The endpoint is therefore both a **network path** and, when endpoint policies apply, an **authorization boundary**.

---

## Endpoint Policy Structure

Endpoint policies use IAM policy syntax.

A common structure is:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSpecificBucket",
      "Effect": "Allow",
      "Principal": "*",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::company-production-assets/*"
      ]
    }
  ]
}
```

The important elements are:

- `Effect`
- `Principal`
- `Action`
- `Resource`
- Optional `Condition`
- Optional `Sid`

The policy should be intentionally narrow.

---

## Restricting S3 Access

S3 is a common endpoint-policy use case.

Suppose a private application requires:

```text
s3:GetObject
```

from:

```text
company-production-assets
```

A restrictive endpoint policy can limit access to that bucket.

Conceptually:

```text
Application
    |
    v
S3 VPC Endpoint
    |
    +-- Allow:
        s3:GetObject
        company-production-assets/*
```

The application should not automatically gain access to:

```text
other-production-bucket
developer-bucket
third-party-bucket
```

through that endpoint.

---

## Bucket-Level vs Object-Level Resources

For S3, pay attention to the distinction between bucket and object ARNs.

Bucket:

```text
arn:aws:s3:::company-production-assets
```

Objects:

```text
arn:aws:s3:::company-production-assets/*
```

For example:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadApplicationObjects",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::company-production-assets/*"
    }
  ]
}
```

Using the wrong resource ARN is a common cause of confusing `AccessDenied` errors.

---

## Restricting Actions

Endpoint policies can also limit actions.

For example:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadOnlyS3Access",
      "Effect": "Allow",
      "Principal": "*",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::company-production-assets",
        "arn:aws:s3:::company-production-assets/*"
      ]
    }
  ]
}
```

This is preferable to allowing:

```text
s3:*
```

when the workload only requires read access.

---

## Principal in Endpoint Policies

Endpoint policies commonly use:

```json
"Principal": "*"
```

because the endpoint policy acts as an additional restriction on requests using the endpoint rather than being the sole identity authorization mechanism.

The identity's IAM policy still matters.

For example:

```text
IAM Role:
Allow s3:GetObject on bucket A

Endpoint:
Allow s3:GetObject on bucket A
```

The request can proceed if all other applicable controls also permit it.

If the endpoint policy excludes bucket A:

```text
IAM Role:
Allow bucket A

Endpoint:
Deny by omission
```

the request should not be authorized through that endpoint.

Do not interpret `Principal: "*"` in an endpoint policy as equivalent to granting every identity unrestricted access.

---

## Allow-List Design

The safest operational pattern is usually an explicit allow-list.

For example:

```text
Allowed service:
S3

Allowed actions:
s3:GetObject
s3:ListBucket

Allowed resources:
company-production-assets
```

Avoid broad policies such as:

```json
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "*"
}
```

unless there is a strong architectural reason and the resulting access is intentionally accepted.

---

## Conditions

IAM policy conditions can provide additional restrictions where supported by the service and authorization context.

For example, a policy may constrain access based on:

- Principal attributes
- Requested resource
- AWS account
- Source VPC endpoint
- Encryption requirements
- Request context

A common S3 architecture uses both endpoint policies and bucket policies to enforce organizational boundaries.

Conceptually:

```text
Endpoint Policy
       |
       v
Approved endpoint
       |
       v
S3 Bucket Policy
       |
       v
Approved bucket access
```

Conditions should be used carefully because an incorrect condition can produce authorization failures that are difficult to diagnose.

---

## Endpoint Policy and S3 Bucket Policy

For S3, access may involve multiple policy layers.

A production architecture can look like:

```text
Application Role
      |
      | IAM Policy
      v
VPC Endpoint
      |
      | Endpoint Policy
      v
S3 Bucket
      |
      | Bucket Policy
      v
Object
```

Each layer can constrain access.

For example:

```text
IAM:
Allow GetObject

Endpoint:
Allow only production bucket

Bucket:
Allow only approved VPC endpoint
```

This creates a strong defense-in-depth model.

---

## Restricting a Bucket to a Specific VPC Endpoint

An S3 bucket policy can restrict access to a specific VPC endpoint using the appropriate condition context.

Conceptually:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowOnlyApprovedEndpoint",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::company-production-assets/*",
      "Condition": {
        "StringEquals": {
          "aws:sourceVpce": "vpce-0123456789abcdef0"
        }
      }
    }
  ]
}
```

This pattern can prevent access through unintended network paths.

The exact policy should be tested carefully because applying a restrictive bucket policy can also affect legitimate access paths such as administrative workflows, CI/CD systems, replication, or other AWS services.

---

## Private Backend Architecture

A typical backend system can use VPC endpoints to avoid public internet paths for AWS API access.

```mermaid
flowchart TB
    subgraph VPC["Production VPC"]
        App["Django / FastAPI"]
        SG["Application Security Group"]
        Endpoint["VPC Endpoint"]
    end

    App --> SG
    SG --> Endpoint
    Endpoint --> S3["Amazon S3"]

    IAM["IAM Role"] --> App
    Policy["Endpoint Policy"] --> Endpoint
```

For example, a Django application processing uploaded documents may require:

```text
Django
  |
  +-- S3 GetObject
  +-- S3 PutObject
```

The application can use private connectivity while the endpoint policy restricts access to approved buckets and actions.

---

## Why This Matters for Backend Systems

Consider a production FastAPI service running on private ECS tasks:

```text
Internet
    |
    v
ALB
    |
    v
Private ECS Tasks
    |
    +---- PostgreSQL
    |
    +---- Redis
    |
    +---- S3
    |
    +---- Secrets Manager
```

Without appropriate endpoints, the application may need NAT Gateway connectivity to reach AWS APIs.

With interface or gateway endpoints where supported:

```text
Private ECS Tasks
    |
    +---- VPC Endpoint
              |
              +---- AWS Service
```

This can improve:

- Network isolation
- Security posture
- Availability of AWS API connectivity
- Cost characteristics in some architectures
- Control over service access

Endpoint policies provide another layer of authorization.

---

## VPC Endpoint Policy and NAT Gateway

A common architecture decision is:

```text
Private Subnet
    |
    +---- AWS service endpoint
```

versus:

```text
Private Subnet
    |
    v
NAT Gateway
    |
    v
Internet
    |
    v
AWS public service endpoint
```

For supported AWS services, VPC endpoints can provide a private path.

| Requirement | NAT Gateway | VPC Endpoint |
|---|---|---|
| General internet access | Yes | No |
| Private AWS service access | Not inherently | Yes |
| Endpoint-specific authorization | No | Yes |
| Public internet dependency | Yes | No for endpoint traffic |
| Service-specific scope | Broad | Specific |
| Typical use | External APIs, package repositories, general internet | AWS service APIs |

A production VPC often uses both:

```text
Private workloads
    |
    +---- VPC endpoints ----> AWS services
    |
    +---- NAT Gateway ------> Internet
```

The endpoint policy can ensure that AWS service access through the endpoint remains tightly scoped.

---

## Security Design

Endpoint policies should follow least privilege.

A useful policy hierarchy is:

```text
Identity
  |
  | What can this workload do?
  v
IAM Policy
  |
  | Which path can perform it?
  v
Endpoint Policy
  |
  | Which resource accepts it?
  v
Resource Policy
```

Not every AWS service uses all these layers in the same way, but this is a useful architectural model.

---

## Defense in Depth

A compromised application role is a significant production risk.

Suppose an attacker obtains temporary credentials for:

```text
application-role
```

The IAM policy may accidentally permit broad access.

A restrictive endpoint policy can provide another boundary:

```text
Compromised credentials
        |
        v
Private VPC
        |
        v
Endpoint Policy
        |
        X
Unapproved resources
```

This does not replace credential security, IAM least privilege, runtime isolation, or detection.

It reduces the blast radius.

---

## Endpoint Policy Limitations

Endpoint policies are not a universal security mechanism.

Important limitations include:

- Not every AWS service supports endpoint policies in the same way.
- Endpoint policies do not replace IAM policies.
- They do not replace Security Groups.
- They do not replace resource policies.
- They do not provide application-layer authorization.
- They do not inspect arbitrary application payloads.
- They do not automatically make an endpoint secure merely because it is private.
- Incorrect policies can cause production `AccessDenied` failures.

Always verify the supported policy model for the specific AWS service and endpoint type.

---

## Security Groups Around Interface Endpoints

Interface endpoints create network interfaces inside your VPC.

Therefore, Security Groups are relevant to interface endpoint connectivity.

Conceptually:

```text
Application SG
      |
      | TCP 443
      v
Endpoint ENI
      |
      v
AWS Service
```

A common design is:

```text
Interface Endpoint SG
Inbound:
TCP 443
Source:
Application SG
```

The application must be able to establish the required network connection to the endpoint ENI.

Endpoint policy then provides an authorization layer after connectivity is established.

---

## DNS Considerations

Interface endpoints commonly rely on private DNS so that normal AWS service hostnames resolve to private endpoint IP addresses.

Conceptually:

```text
api.example-aws-service.amazonaws.com
                 |
                 v
          Private DNS
                 |
                 v
          Endpoint ENI
```

This allows application code such as Python's AWS SDK to continue using the normal AWS service endpoint without requiring application-specific URL changes.

For example:

```python
import boto3

s3 = boto3.client("s3")

response = s3.get_object(
    Bucket="company-production-assets",
    Key="documents/report.pdf",
)
```

The application does not need to know whether the network path uses a VPC endpoint.

Network and DNS configuration remain infrastructure concerns.

---

## Endpoint Policy and Python Applications

Django and FastAPI applications typically use AWS SDKs such as `boto3`.

A production architecture might be:

```text
FastAPI
   |
   | boto3
   v
AWS SDK
   |
   v
Private DNS
   |
   v
VPC Endpoint
   |
   v
S3
```

The application should still use IAM roles rather than static AWS credentials.

For EC2, ECS, and EKS workloads, prefer the AWS-supported workload identity mechanisms appropriate to the platform.

Endpoint policies should be treated as infrastructure authorization controls, not something implemented inside Python.

---

## Example: Restrict S3 to Read-Only

A private workload that only reads application assets might use:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadProductionAssets",
      "Effect": "Allow",
      "Principal": "*",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::company-production-assets/*"
      ]
    }
  ]
}
```

The workload's IAM role should independently grant the same required operation.

Do not use the endpoint policy as an excuse to grant the IAM role excessive permissions.

---

## Example: Read and Write to a Specific Bucket

A document-processing service may require:

```text
GetObject
PutObject
```

but not:

```text
DeleteObject
ListAllMyBuckets
PutBucketPolicy
```

A narrower endpoint policy could therefore permit only the required object operations against the approved bucket.

The policy should be designed from the application's actual AWS API calls rather than from a broad service permission such as:

```text
s3:*
```

---

## Policy Design Workflow

For each endpoint, define:

### Workload

```text
Who uses this endpoint?
```

Examples:

- ECS API service
- EC2 worker
- EKS workload
- Lambda with VPC connectivity

### Service

```text
Which AWS service is accessed?
```

Examples:

- S3
- Secrets Manager
- ECR
- CloudWatch
- STS

### Actions

```text
Which API operations are required?
```

### Resources

```text
Which exact resources are required?
```

### Conditions

```text
Which contextual restrictions are useful?
```

### Network Boundary

```text
Which subnets and Security Groups can reach the endpoint?
```

This produces a layered design rather than treating endpoint policies as an isolated JSON document.

---

## Production Architecture Example

A production backend might use:

```mermaid
flowchart LR
    subgraph VPC["Production VPC"]
        ALB["Application Load Balancer"]
        API["Django / FastAPI"]
        DB["PostgreSQL"]
        Redis["Redis"]

        S3EP["S3 Gateway Endpoint"]
        SecretsEP["Secrets Manager Interface Endpoint"]
        ECREP["ECR Interface Endpoint"]
        SG["Endpoint Security Groups"]
    end

    Client["Client"] --> ALB
    ALB --> API
    API --> DB
    API --> Redis
    API --> S3EP
    API --> SecretsEP
    API --> ECREP

    SG --> SecretsEP
    SG --> ECREP

    S3EP --> S3["S3"]
    SecretsEP --> Secrets["Secrets Manager"]
    ECREP --> ECR["ECR"]

    S3Policy["S3 Endpoint Policy"] --> S3EP
    SecretPolicy["Endpoint Policy"] --> SecretsEP
```

The endpoint policies should reflect the minimum service access required by the workload.

---

## Endpoint Policies and Microservices

Different services may require different AWS capabilities.

For example:

```text
Image Service
    |
    +---- S3 image bucket

Document Service
    |
    +---- S3 document bucket
    +---- Secrets Manager

Worker Service
    |
    +---- SQS
    +---- S3
```

A single unrestricted endpoint policy can weaken isolation.

Where practical, separate endpoint configurations and policies according to meaningful security boundaries.

The goal is not to create an endpoint for every single application operation. The goal is to create network and authorization boundaries that remain understandable and maintainable.

---

## Multi-Account Considerations

In a multi-account architecture:

```text
Security Account
        |
        +---- Central networking controls

Production Account
        |
        +---- VPC
        +---- Endpoints

Development Account
        |
        +---- VPC
        +---- Endpoints
```

Endpoint policies should be designed with account boundaries in mind.

For example:

```text
Production endpoint
    |
    +-- Production S3 resources
```

rather than:

```text
Production endpoint
    |
    +-- All S3 resources in every environment
```

Account separation combined with IAM, endpoint policies, and resource policies can substantially reduce cross-environment blast radius.

---

## Monitoring and Auditing

Endpoint policies themselves do not provide complete visibility into application behavior.

Use multiple sources of operational evidence.

### CloudTrail

Use AWS CloudTrail to audit AWS API activity.

Useful questions include:

- Which principal made the request?
- Which AWS API was called?
- Which resource was accessed?
- From which context did the request originate?
- Was the request successful?

### VPC Flow Logs

For network-level troubleshooting, VPC Flow Logs can help determine whether traffic reaches and leaves relevant network interfaces.

They are especially useful when diagnosing interface endpoint connectivity.

### AWS Config

Where applicable, use AWS Config to detect configuration drift and enforce organizational requirements.

---

## Troubleshooting AccessDenied

When an endpoint request returns:

```text
AccessDenied
```

do not immediately modify the endpoint policy.

Inspect the complete authorization chain.

```text
1. IAM identity policy
2. Permission boundary, if present
3. Session policy, if applicable
4. SCP, if applicable
5. Endpoint policy
6. Resource policy
7. Service-specific authorization
```

The exact set of applicable controls depends on the AWS service and identity model.

Use CloudTrail and IAM policy analysis tools where appropriate.

---

## Troubleshooting Connectivity

If the error is a timeout rather than `AccessDenied`, investigate networking first.

```text
DNS
 |
 v
Route
 |
 v
Security Group
 |
 v
NACL
 |
 v
Endpoint ENI
 |
 v
AWS service
```

For an interface endpoint, verify:

- Endpoint exists
- Endpoint is available
- Private DNS configuration is correct
- Endpoint ENI exists in required Availability Zones
- Security Group allows required traffic
- Subnet routing is appropriate
- Network ACLs permit traffic

An endpoint policy normally produces an authorization failure rather than a basic TCP connectivity timeout.

---

## Common Mistakes

### Treating Endpoint Policies as IAM Replacement

An endpoint policy does not replace the workload's IAM policy.

### Allowing `*` Unnecessarily

Broad actions and resources increase blast radius.

Prefer:

```text
Specific action
+
Specific resource
```

where supported.

### Confusing Endpoint Policy with Security Group

A Security Group controls network connectivity.

An endpoint policy controls authorization through the endpoint.

### Forgetting Resource Policies

S3 bucket policies and other resource-based policies can affect the final authorization decision.

### Incorrect S3 ARN

Distinguish:

```text
arn:aws:s3:::bucket
```

from:

```text
arn:aws:s3:::bucket/*
```

### Blocking Administrative Access

A restrictive resource policy or endpoint policy can unintentionally prevent legitimate operational workflows.

### Creating Excessive Endpoints

Endpoints have operational and potentially financial implications. Design them around real network and security boundaries.

### Ignoring DNS

Interface endpoint connectivity can fail if private DNS behavior is not correctly configured.

### Assuming Every AWS Service Behaves Identically

Endpoint support, policy semantics, and authorization behavior vary by AWS service.

---

## Production Best Practices

### Start With IAM Least Privilege

Endpoint policies should provide additional protection rather than compensate for excessive IAM permissions.

### Restrict Resources

Prefer:

```text
Approved bucket
Approved secret
Approved repository
```

over:

```text
*
```

where practical.

### Restrict Actions

Grant only the API operations the workload actually requires.

### Use Endpoint Policies as Defense in Depth

Do not make the endpoint policy the only security boundary.

### Separate Environments

Production endpoints should not unnecessarily provide access to development resources.

### Use Infrastructure as Code

Store endpoint policies in version control and review changes through CI/CD.

### Keep Policies Understandable

A policy that nobody can reason about is an operational risk.

### Test Negative Cases

Do not only verify that the expected request succeeds.

Also verify that unauthorized requests fail.

For example:

```text
Expected:
GetObject production bucket -> ALLOW

Expected:
GetObject development bucket -> DENY

Expected:
DeleteObject production bucket -> DENY
```

---

## Example Validation Matrix

| Test | Expected Result |
|---|---|
| Get approved S3 object | Allow |
| Put approved S3 object | Depends on policy |
| Delete approved S3 object | Deny if not required |
| Read unrelated bucket | Deny |
| Access AWS service without IAM permission | Deny |
| Reach interface endpoint on blocked port | Network failure |
| Access endpoint with valid IAM but disallowed endpoint policy | Deny |
| Access endpoint with valid endpoint policy but blocked Security Group | Network failure |

This distinction between **network failure** and **authorization failure** is valuable during production debugging.

---

## Cost Considerations

Endpoint selection has cost implications.

Gateway endpoints for supported services do not have the same per-hour interface-endpoint charging model as interface endpoints.

Interface endpoints can introduce:

- Per-endpoint hourly charges
- Per-data-processing charges
- Additional ENIs
- Additional DNS and network configuration

NAT Gateways also have hourly and data-processing costs.

The architecture should therefore evaluate:

```text
Security
+
Availability
+
Latency
+
Operational complexity
+
Traffic volume
+
Cost
```

Do not choose endpoints solely because they are cheaper than NAT or solely because they are considered more secure.

---

## Reliability and High Availability

For interface endpoints, consider Availability Zone placement.

A production workload distributed across multiple Availability Zones should avoid creating a single-AZ dependency when the endpoint is critical to application operation.

For example:

```text
AZ-A
API
 |
Endpoint ENI A

AZ-B
API
 |
Endpoint ENI B
```

This reduces dependence on a single endpoint network interface path.

For gateway endpoints, route-table associations must be designed so that the required subnets have access to the endpoint.

---

## Disaster Recovery

Endpoint configuration is part of the infrastructure definition.

For disaster recovery, preserve:

- Endpoint definitions
- Endpoint policies
- Route-table associations
- Security Groups
- DNS configuration
- IAM policies
- Resource policies
- Environment-specific resource identifiers

Infrastructure as Code makes endpoint configuration reproducible.

A DR environment should not accidentally inherit production resource access simply because the same broad endpoint policy was copied.

---

## Interview Traps

### Does a VPC endpoint policy replace IAM?

No. It is an additional policy layer.

### Does a Security Group determine whether an S3 object can be read?

No. Security Groups provide network connectivity controls; IAM and service/resource authorization determine whether the AWS API operation is authorized.

### Can endpoint policies restrict which S3 buckets a workload accesses?

Yes, where supported by the endpoint/service policy model.

### Why use an endpoint policy if IAM already exists?

Defense in depth and restriction of what can be accessed through a particular network path.

### Is private connectivity the same as authorization?

No.

```text
Private network path != authorization
```

A private endpoint can provide network reachability while IAM and endpoint policies still determine whether the requested operation is permitted.

### What is the difference between a timeout and AccessDenied?

A timeout usually points toward networking, DNS, routing, Security Groups, NACLs, or endpoint availability.

`AccessDenied` generally indicates an authorization problem.

---

## Practical Mental Model

When designing or debugging VPC endpoint access, use this layered model:

```text
                 Application
                      |
                      v
              Workload Identity
                      |
                      v
                 IAM Policy
                      |
                      v
                 Network Path
                      |
             +--------+--------+
             |                 |
          Routing          Security Group
             |                 |
             +--------+--------+
                      |
                      v
                 VPC Endpoint
                      |
                      v
               Endpoint Policy
                      |
                      v
                 AWS Service
                      |
                      v
              Resource Policy
```

Not every request uses every layer identically, but this model prevents a common mistake: assuming that because a workload can reach an endpoint, it is automatically authorized to perform every operation exposed by the service.

---

## Key Takeaways

- **VPC endpoint policies add an authorization boundary to private AWS service access** and should complement, not replace, IAM least privilege.
- Use endpoint policies to restrict **actions, resources, and approved access paths** where supported, especially for sensitive services such as S3.
- **Security Groups control network connectivity**, while endpoint policies participate in AWS authorization; a private network path does not imply permission to access the target resource.
- Production designs should combine **IAM, endpoint policies, resource policies, Security Groups, routing, DNS, and monitoring** according to the specific AWS service.
- Treat endpoint policies as **Infrastructure as Code**, test both allowed and denied operations, and design interface endpoints for multi-AZ reliability where they are operationally critical.