# 11- Interface Endpoints and AWS PrivateLink

## Overview

Interface endpoints provide private connectivity from resources in a VPC to supported AWS services, AWS Marketplace services, and other services exposed through AWS PrivateLink.

Unlike gateway endpoints, interface endpoints are implemented using elastic network interfaces (ENIs) placed into selected subnets. Applications connect to private IP addresses associated with those ENIs, allowing service traffic to remain within the AWS networking environment without requiring public internet access or a NAT Gateway.

The fundamental architecture is:

```text
Private Application
       |
       v
Interface Endpoint ENI
       |
       v
AWS PrivateLink
       |
       v
Supported AWS Service
```

This mechanism is particularly important for production private subnets because many AWS services do not support gateway endpoints.

For example, a private FastAPI service may need:

- AWS Secrets Manager
- Amazon SQS
- Amazon ECR
- AWS Systems Manager
- Amazon CloudWatch APIs

Instead of routing all of this traffic through a NAT Gateway, interface endpoints can provide private connectivity where supported.

---

## Gateway Endpoint vs Interface Endpoint

The two endpoint models solve related but different networking problems.

| Characteristic | Gateway Endpoint | Interface Endpoint |
|---|---|---|
| Implementation | Route-table integration | ENI |
| Technology | VPC endpoint | AWS PrivateLink |
| ENI created | No | Yes |
| Security Group | No | Yes |
| Subnet selection | Route tables | Subnets |
| Private IP addresses | No endpoint ENI IP | Yes |
| Supported services | S3, DynamoDB | Many AWS services |
| DNS integration | Different model | Central to normal usage |
| Typical use | S3, DynamoDB | Secrets Manager, SQS, ECR, etc. |
| Hourly endpoint cost | No | Yes |
| Data processing charges | Service-dependent | Applies according to endpoint pricing |
| Multi-AZ design | Route-table based | Usually deploy endpoint ENIs across AZs |

A practical decision rule is:

```text
S3 / DynamoDB
    |
    v
Gateway Endpoint

Other supported AWS services
    |
    v
Interface Endpoint / PrivateLink
```

---

## What Is AWS PrivateLink?

AWS PrivateLink is the underlying AWS networking technology that enables private access to services through endpoint network interfaces.

It allows a service consumer to connect to a service without exposing the service through a public internet path.

Conceptually:

```text
Consumer VPC
     |
     v
Interface Endpoint
     |
     v
PrivateLink
     |
     v
Service Provider
```

The service provider may be:

- An AWS service
- An AWS Marketplace service
- A third-party SaaS provider
- Another AWS account exposing a service through a VPC endpoint service

This makes PrivateLink useful beyond AWS-managed services.

---

## Why PrivateLink Exists

Traditional private connectivity between VPCs often involves mechanisms such as:

- VPC peering
- Transit Gateway
- VPN
- AWS Direct Connect

Those mechanisms establish broader network connectivity.

PrivateLink provides a narrower service-oriented model.

Instead of exposing an entire network:

```text
VPC A
   |
   | broad network connectivity
   v
VPC B
```

PrivateLink can expose a specific service:

```text
VPC A
   |
   v
Specific Service
```

This creates a smaller trust boundary.

For organizations operating multiple microservices or multi-account AWS environments, this distinction is significant.

---

## Interface Endpoint Architecture

An interface endpoint creates one or more ENIs inside selected subnets.

For example:

```text
VPC
 |
 +-- Private Subnet A
 |      |
 |      +-- Application
 |      |
 |      +-- Interface Endpoint ENI
 |
 +-- Private Subnet B
        |
        +-- Application
        |
        +-- Interface Endpoint ENI
```

The endpoint ENIs receive private IP addresses from their respective subnets.

Applications can therefore communicate with the endpoint using private network addresses.

---

## How Interface Endpoints Work

A typical request flow is:

```text
Application
    |
    v
DNS Resolution
    |
    v
Private IP of Endpoint ENI
    |
    v
Interface Endpoint
    |
    v
AWS PrivateLink
    |
    v
AWS Service
```

For example:

```text
FastAPI
   |
   v
secretsmanager.<region>.amazonaws.com
   |
   v
Private DNS
   |
   v
10.x.x.x
   |
   v
Interface Endpoint
   |
   v
Secrets Manager
```

The application normally continues using the standard AWS SDK endpoint hostname.

The networking infrastructure determines how that hostname resolves.

---

## Endpoint ENIs

The ENI is the most important implementation detail of an interface endpoint.

For example:

```text
Private Subnet A
    |
    +-- Endpoint ENI
          |
          +-- 10.0.1.50

Private Subnet B
    |
    +-- Endpoint ENI
          |
          +-- 10.0.2.50
```

Each ENI is a normal VPC network interface from the networking perspective.

This means interface endpoints interact with:

- Subnet IP capacity
- Security Groups
- Network ACLs
- Availability Zones
- Route tables
- DNS

---

## Why Deploy Interface Endpoints Across Multiple AZs?

For a highly available production architecture, create endpoint ENIs in multiple Availability Zones.

For example:

```text
                    Interface Endpoint
                    /                \
                   /                  \
              AZ A                    AZ B
               |                       |
          Endpoint ENI            Endpoint ENI
               |                       |
          Application A            Application B
```

This avoids unnecessarily forcing all workload traffic through a single Availability Zone.

It also reduces the impact of an AZ-level failure.

A common production design is:

```text
AZ A -> Endpoint ENI A
AZ B -> Endpoint ENI B
AZ C -> Endpoint ENI C
```

when the workload itself is distributed across those AZs and the service architecture justifies the additional endpoint cost.

---

## Subnet Selection

When creating an interface endpoint, you select subnets.

For example:

```text
Interface Endpoint
    |
    +-- subnet-private-a
    +-- subnet-private-b
```

The endpoint service creates ENIs in those subnets.

Unlike gateway endpoints, you do not associate an interface endpoint directly with route tables as the primary placement mechanism.

The endpoint ENIs exist inside specific subnets.

---

## Security Groups

Interface endpoint ENIs can have Security Groups.

This is an important difference from gateway endpoints.

For example:

```text
Application Security Group
          |
          | HTTPS / TCP 443
          v
Endpoint Security Group
          |
          v
AWS Service
```

A common endpoint Security Group rule is:

```text
Inbound:
TCP 443
Source:
Application Security Group
```

This allows only workloads belonging to the approved application Security Group to communicate with the endpoint.

---

## Endpoint Security Group Design

A dedicated endpoint Security Group is generally easier to reason about than broadly allowing access.

For example:

```text
sg-application
    |
    | TCP 443
    v
sg-vpce
```

Endpoint Security Group:

```text
Inbound
-------
TCP 443
Source: sg-application
```

Application Security Group:

```text
Outbound
--------
TCP 443
Destination: sg-vpce
```

This creates an explicit relationship between the workload and the endpoint.

---

## Security Groups vs Endpoint Policies

These controls operate at different layers.

| Control | Primary Responsibility |
|---|---|
| Security Group | Network connectivity to endpoint ENI |
| IAM | Identity authorization |
| Endpoint Policy | What can be accessed through endpoint |
| Resource Policy | Whether target resource permits request |
| KMS Policy | Encryption-key authorization |

A production request may therefore pass through multiple controls:

```text
Application
    |
    v
Security Group
    |
    v
Interface Endpoint
    |
    v
Endpoint Policy
    |
    v
IAM
    |
    v
Resource Policy
    |
    v
AWS Service
```

A successful network connection does not imply that the AWS API operation will be authorized.

---

## Private DNS

Private DNS is one of the most important features of interface endpoints.

When enabled for supported AWS services, applications can continue using normal AWS service DNS names.

For example:

```text
secretsmanager.us-east-1.amazonaws.com
```

can resolve to private endpoint IP addresses inside the VPC.

Conceptually:

```text
Application
    |
    | DNS query
    v
Route 53 Resolver
    |
    v
Private DNS
    |
    v
Endpoint ENI private IP
```

This means application code usually does not need to be changed to explicitly reference the endpoint's IP address.

---

## Why Private DNS Matters

Without private DNS, an application may resolve an AWS service hostname to public service addresses.

With private DNS enabled:

```text
AWS SDK
   |
   v
Standard AWS hostname
   |
   v
Private DNS resolution
   |
   v
Interface Endpoint ENI
```

This allows the same application configuration to work while infrastructure controls the actual network path.

That separation is highly desirable.

---

## DNS and AWS SDKs

A Python application might simply execute:

```python
import boto3

client = boto3.client("secretsmanager")

response = client.get_secret_value(
    SecretId="production/database",
)
```

The application does not need to know whether the request reaches Secrets Manager through:

```text
NAT Gateway
```

or:

```text
Interface Endpoint
```

The VPC DNS and endpoint configuration determine the network path.

---

## Private DNS Is Not the Same as Private Connectivity

Private DNS is a mechanism for resolving names.

Private connectivity is the actual network path.

You need both to achieve the typical seamless interface endpoint architecture:

```text
Application
    |
    v
Private DNS
    |
    v
Endpoint ENI
    |
    v
PrivateLink
    |
    v
AWS Service
```

Changing DNS alone does not create PrivateLink connectivity.

---

## AWS Services Commonly Accessed Through Interface Endpoints

Many AWS services can be accessed through interface endpoints.

Examples include:

| Service | Common Private Endpoint Use Case |
|---|---|
| AWS Secrets Manager | Retrieve application secrets |
| AWS Systems Manager | Instance management |
| Amazon SQS | Queue operations |
| Amazon SNS | Messaging APIs |
| Amazon ECR API | Container image operations |
| Amazon ECR DKR | Container registry image pulls |
| CloudWatch Logs | Log ingestion |
| AWS STS | Credential operations |
| AWS KMS | Key-management API calls |

Exact endpoint availability varies by Region and service.

Always verify the current AWS service documentation before designing the endpoint architecture.

---

## Interface Endpoint for Secrets Manager

A common private backend architecture is:

```text
Django / FastAPI
       |
       v
Secrets Manager
       |
       v
Database credentials
```

Without an interface endpoint:

```text
Private Application
       |
       v
NAT Gateway
       |
       v
Secrets Manager
```

With an interface endpoint:

```text
Private Application
       |
       v
Private DNS
       |
       v
Secrets Manager Interface Endpoint
       |
       v
Secrets Manager
```

This removes the NAT dependency for Secrets Manager API traffic.

---

## Interface Endpoint for SQS

A Celery or worker-based architecture might use SQS:

```text
Application
    |
    v
SQS
    |
    v
Worker
```

Both applications and workers may need access to SQS.

Using an interface endpoint:

```text
Application
      |
      v
SQS Interface Endpoint
      |
      v
SQS

Worker
      |
      v
SQS Interface Endpoint
      |
      v
SQS
```

This is useful when the workloads are intentionally isolated from public internet egress.

---

## Interface Endpoint for ECR

Private container workloads may need access to Amazon ECR.

The architecture can involve separate endpoint connectivity for the required ECR APIs.

Conceptually:

```text
Private Container Host
       |
       +----> ECR API Endpoint
       |
       +----> ECR DKR Endpoint
       |
       +----> S3 Gateway Endpoint
```

ECR image pulls can involve multiple AWS services, so simply creating one endpoint and assuming all image-pull traffic is covered is a common mistake.

The exact endpoint requirements depend on the workload and current AWS ECR architecture.

---

## Interface Endpoint for KMS

Applications may call KMS directly:

```text
Application
    |
    v
KMS API
```

For private workloads:

```text
Application
    |
    v
KMS Interface Endpoint
    |
    v
AWS KMS
```

This can be useful when an application performs operations such as:

- Encrypt
- Decrypt
- GenerateDataKey
- DescribeKey

through the KMS API.

The application's IAM permissions and KMS key policy still control authorization.

---

## Interface Endpoint for STS

AWS SDKs and workloads may call AWS Security Token Service.

For example:

```text
Application
    |
    v
STS
    |
    v
Temporary credentials
```

In private environments, an STS interface endpoint can avoid sending STS API traffic through NAT where supported and appropriately configured.

This can matter for:

- IAM roles
- Temporary credentials
- Cross-account access
- EKS workloads
- AWS SDK operations

---

## Interface Endpoint and Microservices

PrivateLink is particularly useful in service-oriented architectures.

Consider:

```text
Consumer VPC
     |
     v
PrivateLink
     |
     v
Payment Service
```

The consumer does not need broad access to the provider VPC.

Instead, it receives access to a specific service.

This supports a strong principle:

> Expose services, not entire networks, when broad network connectivity is unnecessary.

---

## AWS PrivateLink Service Provider Model

PrivateLink can involve two parties.

### Service Consumer

The consumer creates an interface endpoint:

```text
Consumer VPC
    |
    v
Interface Endpoint
```

### Service Provider

The provider exposes a service through a VPC endpoint service.

Conceptually:

```text
Consumer VPC
     |
     v
Interface Endpoint
     |
     v
AWS PrivateLink
     |
     v
Endpoint Service
     |
     v
Network Load Balancer
     |
     v
Provider Service
```

This allows private service consumption across VPC and AWS account boundaries.

---

## Endpoint Service Architecture

A service provider can expose an application through a Network Load Balancer.

```mermaid
flowchart LR
    CONSUMER["Consumer VPC"]
    ENI["Interface Endpoint ENI"]
    PL["AWS PrivateLink"]
    SERVICE["VPC Endpoint Service"]
    NLB["Network Load Balancer"]
    APP["Provider Application"]

    CONSUMER --> ENI
    ENI --> PL
    PL --> SERVICE
    SERVICE --> NLB
    NLB --> APP
```

The consumer sees a private endpoint.

The provider controls the underlying service.

---

## Why PrivateLink Is Useful for Microservices

Suppose an organization has:

```text
Application Account
Payment Account
Analytics Account
```

The payment service could be exposed through PrivateLink.

Instead of:

```text
Application VPC
    <---- broad connectivity ---->
Payment VPC
```

the architecture can be:

```text
Application VPC
       |
       v
Payment PrivateLink Endpoint
       |
       v
Payment Service
```

This reduces the network exposure surface.

---

## PrivateLink vs VPC Peering

| Characteristic | PrivateLink | VPC Peering |
|---|---|---|
| Scope | Specific service | Network connectivity |
| Consumer access | Service-oriented | VPC CIDRs |
| Provider exposure | Specific endpoint service | VPC networking |
| Routing model | Endpoint | VPC routes |
| Transitive routing | Not general-purpose network routing | Not transitive |
| Security boundary | Narrow | Broader |
| Common use | SaaS/service exposure | VPC-to-VPC communication |

Use PrivateLink when the requirement is:

> "Allow access to this service."

Use VPC peering when the requirement is closer to:

> "Allow these VPC networks to communicate."

---

## PrivateLink vs Transit Gateway

Transit Gateway is designed for centralized network connectivity.

PrivateLink is designed for service exposure.

Conceptually:

```text
Transit Gateway
    |
    +---- VPC A
    +---- VPC B
    +---- VPC C
    +---- VPC D
```

versus:

```text
PrivateLink
    |
    +---- Specific Service
```

Transit Gateway is appropriate for broader network architecture.

PrivateLink is appropriate when consumers should access selected services without receiving broad network reachability.

---

## Route Tables and Interface Endpoints

Interface endpoints still exist within the VPC routing model.

However, unlike gateway endpoints, they are reached through ENI IP addresses.

For example:

```text
Application
    |
    v
Route Table
    |
    v
Endpoint ENI
```

The endpoint ENI has an IP address inside the subnet.

Traffic destined for that private IP is handled through normal VPC routing.

The endpoint's Security Group then controls network access to the ENI.

---

## Network ACL Considerations

Network ACLs apply at the subnet level.

If an interface endpoint ENI exists in a subnet, subnet-level NACL rules can affect connectivity.

A troubleshooting path can therefore be:

```text
Application
    |
    v
Application Subnet NACL
    |
    v
Route Table
    |
    v
Endpoint ENI
    |
    v
Endpoint Subnet NACL
    |
    v
PrivateLink
```

Avoid overly restrictive NACL configurations unless the organization has a strong reason to maintain them.

Security Groups are generally easier to reason about for stateful workload-level controls.

---

## Interface Endpoint and NAT Gateway

Interface endpoints do not make NAT obsolete.

A production private subnet may use both:

```text
Private Application
       |
       +---- AWS service
       |       |
       |       v
       |   Interface Endpoint
       |
       +---- S3
       |       |
       |       v
       |   Gateway Endpoint
       |
       +---- Public API
               |
               v
           NAT Gateway
```

This creates destination-specific egress architecture.

---

## Cost Considerations

Interface endpoints generally have costs associated with:

- Endpoint hourly usage
- Data processing

The exact pricing depends on the endpoint and AWS pricing model.

This creates a trade-off.

Suppose a workload needs access to many AWS services.

You might have:

```text
10 AWS Services
    |
    v
10 Interface Endpoints
```

The NAT architecture might be operationally simpler:

```text
Private Application
       |
       v
NAT Gateway
       |
       v
AWS Services
```

But the NAT architecture may have higher data-processing and egress-related costs and creates an additional network dependency.

The correct architecture depends on:

- Traffic volume
- Number of AZs
- Number of services
- Security requirements
- Availability requirements
- NAT costs
- Endpoint costs
- Operational complexity

---

## Endpoint Per AZ and Cost

If you deploy interface endpoints in three AZs:

```text
AZ A -> Endpoint ENI
AZ B -> Endpoint ENI
AZ C -> Endpoint ENI
```

you gain better locality and availability but increase endpoint resource usage.

This is an engineering trade-off:

```text
More AZ coverage
      +
Higher endpoint cost
```

versus:

```text
Fewer endpoint ENIs
      +
Potential cross-AZ dependency
```

For production workloads, optimize for the required availability architecture rather than simply minimizing endpoint count.

---

## Availability and Failure Domains

Interface endpoints should be considered part of the application's dependency graph.

For a multi-AZ backend:

```text
                AWS Service
                     ^
                     |
               PrivateLink
              /            \
             /              \
         AZ A                AZ B
          |                    |
     Endpoint ENI         Endpoint ENI
          |                    |
      App A                  App B
```

This prevents a single endpoint ENI in one AZ from becoming an avoidable architectural dependency.

---

## DNS Failure Modes

DNS is a critical part of interface endpoint connectivity.

A common request path is:

```text
Application
    |
    v
DNS Resolver
    |
    v
Private DNS
    |
    v
Endpoint ENI IP
```

If DNS is incorrectly configured, the application may resolve the public AWS service address instead.

Potential symptoms include:

- Requests unexpectedly traversing NAT
- Connectivity failures in isolated networks
- Unexpected latency
- Unexpected NAT charges
- Different behavior between environments

Always validate DNS as part of endpoint troubleshooting.

---

## DNS Configuration Considerations

For typical VPC configurations, verify:

- VPC DNS support is enabled.
- VPC DNS hostnames are enabled where required.
- Private DNS is enabled on the interface endpoint when appropriate.
- Route 53 Resolver behavior is understood.
- Custom DNS infrastructure does not bypass the expected AWS DNS resolution path.

A custom corporate DNS architecture can change the behavior significantly.

---

## Split-Horizon DNS

Organizations with centralized DNS may use split-horizon DNS.

For example:

```text
Application
    |
    v
Corporate DNS
    |
    +---- Internal AWS hostname
    |
    +---- External hostname
```

If private endpoint DNS is involved, make sure the organization's DNS architecture does not accidentally override or bypass the intended endpoint resolution.

DNS architecture becomes especially important in multi-account environments.

---

## Interface Endpoint Policies

Many AWS interface endpoints can use endpoint policies to restrict service access.

For example:

```text
Application
    |
    v
Interface Endpoint
    |
    v
Endpoint Policy
    |
    v
AWS Service
```

The policy can limit actions and resources depending on the supported service and policy capabilities.

Use endpoint policies as an additional defense-in-depth mechanism.

Do not treat them as a replacement for IAM.

---

## IAM Still Applies

An interface endpoint does not bypass AWS authorization.

For example:

```text
Application
    |
    v
Secrets Manager Endpoint
    |
    v
IAM Authorization
```

If the application's IAM role does not allow:

```text
secretsmanager:GetSecretValue
```

the request should fail even though the network connection is successful.

This separation is fundamental:

```text
Network connectivity != authorization
```

---

## Security Architecture

A mature private AWS architecture can look like:

```mermaid
flowchart TB
    APP["Private Application"]

    SG["Endpoint Security Group"]
    DNS["Private DNS"]
    ENI["Interface Endpoint ENI"]
    POLICY["Endpoint Policy"]
    IAM["IAM Policy"]
    SERVICE["AWS Service"]
    RESOURCE["Resource Policy"]

    APP --> DNS
    DNS --> ENI
    APP --> SG
    SG --> ENI
    ENI --> POLICY
    POLICY --> IAM
    IAM --> SERVICE
    SERVICE --> RESOURCE
```

The actual evaluation and request path varies by service, but the architectural principle remains:

> Network reachability and authorization are separate controls.

---

## AWS CLI: List Interface Endpoints

List interface endpoints:

```bash
aws ec2 describe-vpc-endpoints \
    --filters Name=vpc-endpoint-type,Values=Interface
```

Filter by VPC:

```bash
aws ec2 describe-vpc-endpoints \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx \
              Name=vpc-endpoint-type,Values=Interface
```

Inspect a specific endpoint:

```bash
aws ec2 describe-vpc-endpoints \
    --vpc-endpoint-ids vpce-xxxxxxxx
```

---

## Creating an Interface Endpoint

Example:

```bash
aws ec2 create-vpc-endpoint \
    --vpc-id vpc-xxxxxxxx \
    --service-name com.amazonaws.us-east-1.secretsmanager \
    --vpc-endpoint-type Interface \
    --subnet-ids subnet-private-a subnet-private-b \
    --security-group-ids sg-vpce \
    --private-dns-enabled
```

The exact service name depends on the AWS Region and service.

---

## Terraform Interface Endpoint

A production Terraform example:

```hcl
data "aws_region" "current" {}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [
    aws_subnet.private_a.id,
    aws_subnet.private_b.id,
  ]
  security_group_ids  = [aws_security_group.vpce.id]
  private_dns_enabled = true

  tags = {
    Name = "secretsmanager-interface-endpoint"
  }
}
```

For production, endpoint resources should be parameterized and managed consistently across environments.

---

## Terraform Endpoint Security Group

```hcl
resource "aws_security_group" "vpce" {
  name        = "vpce-endpoints"
  description = "Allow private application access to VPC interface endpoints"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "HTTPS from application workloads"
    protocol        = "tcp"
    from_port       = 443
    to_port         = 443
    security_groups = [aws_security_group.application.id]
  }

  egress {
    description = "Allow endpoint response traffic"
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "vpce-endpoints"
  }
}
```

The exact egress policy should follow the organization's security model.

---

## Application Security Group

A corresponding application Security Group might allow outbound HTTPS:

```hcl
resource "aws_security_group_rule" "application_to_vpce" {
  type                     = "egress"
  security_group_id        = aws_security_group.application.id
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.vpce.id
}
```

Avoid creating redundant rules if an existing application egress policy already permits the required traffic.

---

## Troubleshooting Interface Endpoints

Troubleshooting should follow the complete request path.

```text
Application
    |
    v
DNS
    |
    v
Endpoint ENI
    |
    v
Security Group
    |
    v
Route Table
    |
    v
NACL
    |
    v
PrivateLink
    |
    v
AWS Service
```

Check each layer rather than immediately changing application code.

---

## Troubleshooting Checklist

```text
[ ] Does the endpoint exist?
[ ] Is it in the correct VPC?
[ ] Is the required service supported?
[ ] Is the endpoint deployed in the required AZs?
[ ] Does the application subnet have network reachability to the endpoint ENI?
[ ] Does the endpoint Security Group allow TCP 443 from the application?
[ ] Do NACLs allow the traffic?
[ ] Is private DNS enabled where appropriate?
[ ] Is VPC DNS support enabled?
[ ] Does the service hostname resolve to private endpoint IPs?
[ ] Is the endpoint policy allowing the operation?
[ ] Does IAM allow the operation?
[ ] Does the target resource policy allow the request?
[ ] Are KMS permissions correct if encryption is involved?
[ ] Is the AWS service available?
```

---

## Useful DNS Verification

From an EC2 instance or appropriate private workload:

```bash
dig secretsmanager.us-east-1.amazonaws.com
```

or:

```bash
nslookup secretsmanager.us-east-1.amazonaws.com
```

If private DNS is configured correctly, the result should resolve according to the interface endpoint's private DNS behavior rather than unexpectedly sending the workload toward public service addresses.

Exact DNS results depend on the VPC, Region, endpoint configuration, and resolver architecture.

---

## Testing Connectivity

Test TCP connectivity to the endpoint's private IP when appropriate:

```bash
nc -vz 10.0.1.50 443
```

Testing the AWS hostname is usually more representative of actual application behavior:

```bash
curl -I https://secretsmanager.us-east-1.amazonaws.com
```

The AWS API may reject an unauthenticated request, but DNS and TCP/TLS behavior can still provide useful troubleshooting information.

Do not interpret an HTTP authorization failure as proof of a network failure.

---

## Common Mistakes

### Creating an Interface Endpoint Without Private DNS

Applications may continue resolving AWS service hostnames publicly.

Validate the DNS behavior explicitly.

### Deploying the Endpoint in Only One AZ

This can create an unnecessary cross-AZ dependency or availability concern.

Deploy endpoint ENIs in the AZs required by the workload.

### Using the Wrong Security Group

The application must be able to establish TCP 443 connectivity to the endpoint ENI.

### Forgetting Endpoint Security Groups

Interface endpoint ENIs are protected by Security Groups.

A restrictive endpoint Security Group can block otherwise correctly configured workloads.

### Assuming PrivateLink Replaces IAM

It does not.

Private connectivity and authorization are independent.

### Assuming One Endpoint Supports Every AWS Service

Interface endpoints are service-specific.

You generally need endpoint resources for the services that your private workloads actually consume.

### Ignoring DNS

An endpoint can exist and still not be used as expected if DNS is incorrectly configured.

### Creating Too Many Endpoints

Every interface endpoint has operational and cost implications.

Create endpoints based on actual requirements.

### Routing Everything Through NAT

NAT may be appropriate for public internet traffic, but it is not necessarily the best path for supported private AWS service access.

### Ignoring ECR's Multiple Dependencies

Private container image pulls can require multiple AWS service endpoints and S3 connectivity.

Do not assume one ECR endpoint is sufficient for every image-pull scenario.

---

## Performance Considerations

Interface endpoints can reduce unnecessary NAT traversal for supported AWS service traffic.

For example:

```text
Without Interface Endpoint

Application
    |
    v
NAT Gateway
    |
    v
AWS Service
```

versus:

```text
With Interface Endpoint

Application
    |
    v
Private DNS
    |
    v
Endpoint ENI
    |
    v
PrivateLink
    |
    v
AWS Service
```

The actual performance difference depends on workload, AWS service behavior, AZ placement, DNS, connection reuse, and traffic volume.

Do not assume that an endpoint automatically makes every request faster.

---

## Connection Reuse

Backend applications should still use efficient SDK/client configuration.

For example, creating a new AWS client for every request can be less efficient than reusing a client where the SDK and application architecture support it.

The network architecture does not compensate for poor application connection management.

For high-throughput systems, evaluate:

- Connection pooling
- Keep-alive behavior
- Request concurrency
- SDK retries
- Timeout configuration
- Service throttling
- Endpoint placement

---

## Reliability Considerations

Interface endpoints become infrastructure dependencies.

If an application requires Secrets Manager during startup:

```text
Application startup
       |
       v
Secrets Manager
       |
       v
Interface Endpoint
```

endpoint availability becomes part of the application's startup dependency chain.

Therefore:

- Deploy endpoints across required AZs.
- Avoid unnecessary single-AZ dependencies.
- Monitor endpoint health and application failures.
- Include endpoint configuration in disaster recovery infrastructure.

---

## Monitoring

Monitor both endpoint infrastructure and application behavior.

Useful sources include:

- VPC Flow Logs
- CloudTrail
- Route 53 Resolver logs where configured
- CloudWatch service metrics
- Application metrics
- AWS SDK errors
- DNS resolution failures
- Connection timeout metrics

For example, track:

```text
DNS resolution failures
        +
TCP connection failures
        +
TLS failures
        +
AWS authorization failures
        +
AWS throttling
```

These failures indicate different layers of the system and should not be treated as one generic "endpoint problem."

---

## Operational Considerations

Maintain an inventory of interface endpoints.

For example:

| Endpoint | Purpose | AZs | Owner |
|---|---|---|---|
| Secrets Manager | Application secrets | A, B | Platform |
| SQS | Async messaging | A, B | Platform |
| ECR API | Container image access | A, B | Platform |
| ECR DKR | Container registry | A, B | Platform |
| KMS | Encryption APIs | A, B | Platform |

This helps prevent:

- Duplicate endpoints
- Forgotten endpoints
- Unused endpoints
- Inconsistent security groups
- Inconsistent endpoint policies
- Unexpected infrastructure costs

---

## Production Design Pattern

A mature private backend environment may use:

```mermaid
flowchart TB
    subgraph VPC["Production VPC"]
        subgraph AZ1["AZ A"]
            APP1["Application"]
            VPCE1["Interface Endpoint ENI"]
        end

        subgraph AZ2["AZ B"]
            APP2["Application"]
            VPCE2["Interface Endpoint ENI"]
        end

        S3EP["S3 Gateway Endpoint"]
        NAT["NAT Gateway"]
    end

    SM["Secrets Manager"]
    SQS["SQS"]
    KMS["KMS"]
    S3["S3"]
    INTERNET["Public APIs"]

    APP1 --> VPCE1
    APP2 --> VPCE2

    VPCE1 --> SM
    VPCE2 --> SM

    VPCE1 --> SQS
    VPCE2 --> SQS

    VPCE1 --> KMS
    VPCE2 --> KMS

    APP1 --> S3EP
    APP2 --> S3EP
    S3EP --> S3

    APP1 --> NAT
    APP2 --> NAT
    NAT --> INTERNET
```

The resulting traffic model is:

```text
S3
    -> Gateway Endpoint

Secrets Manager
    -> Interface Endpoint

SQS
    -> Interface Endpoint

KMS
    -> Interface Endpoint

Public third-party APIs
    -> NAT Gateway
```

This is a common production pattern for highly private backend environments.

---

## When to Use Interface Endpoints

Use interface endpoints when:

- The required service supports interface endpoints.
- Private workloads need AWS service access.
- You want to reduce NAT dependency.
- Security requirements discourage public internet paths.
- You need service-level connectivity across VPC or account boundaries.
- You operate private microservices or SaaS integrations.
- You need PrivateLink-based service exposure.

Avoid automatically creating endpoints for every service.

Evaluate:

```text
Security
+
Availability
+
Traffic volume
+
Cost
+
Operational complexity
```

before introducing each endpoint.

---

## When PrivateLink Is the Better Architecture

PrivateLink is particularly valuable when a consumer needs:

```text
Access to one service
```

rather than:

```text
Access to an entire network.
```

For example:

```text
Consumer VPC
     |
     v
Payment API
```

is a strong PrivateLink use case when the payment provider wants to expose only its service rather than its whole VPC.

This supports a least-connectivity architecture.

---

## PrivateLink and Service Ownership

PrivateLink also creates a useful organizational boundary.

A provider team can own:

```text
Payment Service
```

while consumer teams only receive:

```text
Private Endpoint
```

The consumer does not need to understand the provider's internal VPC topology.

This reduces coupling between infrastructure teams.

---

## PrivateLink Security Model

A provider should carefully control which consumers can connect.

Controls can include:

- Allowed AWS principals
- Endpoint acceptance policies
- Security Groups
- IAM authorization
- Application-level authentication
- TLS
- Network Load Balancer configuration
- Service-level authorization

PrivateLink should not be interpreted as authentication.

It provides private connectivity; the application still needs appropriate authentication and authorization.

---

## Interview Traps

### What is an interface endpoint?

An interface endpoint provides private connectivity to supported services through ENIs inside the consumer VPC.

### What technology powers interface endpoints?

AWS PrivateLink.

### Does an interface endpoint create an ENI?

Yes.

### Where are the ENIs created?

In subnets selected when creating the interface endpoint.

### Can Security Groups be attached to interface endpoints?

Yes.

### Why is private DNS important?

It allows standard AWS service hostnames to resolve to private endpoint addresses, allowing applications to use normal AWS SDK configuration.

### Does PrivateLink provide broad VPC-to-VPC connectivity?

No.

It exposes specific services rather than providing general-purpose network connectivity.

### PrivateLink vs VPC Peering?

PrivateLink provides service-level connectivity; VPC peering provides network-level connectivity between VPCs.

### PrivateLink vs Transit Gateway?

PrivateLink is service-oriented; Transit Gateway is designed for broader centralized network connectivity.

### Does an interface endpoint replace NAT?

Not universally.

It can replace NAT for supported AWS service traffic, while NAT may still be required for public internet destinations.

### Does an interface endpoint bypass IAM?

No.

IAM and other authorization controls still apply.

### Why deploy interface endpoints in multiple AZs?

To improve availability and avoid making a single-AZ endpoint a dependency for multi-AZ workloads.

### What is the biggest operational difference from gateway endpoints?

Gateway endpoints use route-table integration and support S3/DynamoDB, while interface endpoints use ENIs and PrivateLink for many supported services.

## Key Takeaways

- Interface endpoints provide private connectivity through ENIs and AWS PrivateLink, making them the standard VPC endpoint model for many AWS services beyond S3 and DynamoDB.
- Private DNS is a critical part of the normal interface-endpoint architecture because standard AWS service hostnames can resolve to private endpoint IP addresses without application-specific networking changes.
- Interface endpoints should be deployed across the Availability Zones required by the workload, with dedicated Security Groups and appropriately restrictive endpoint policies.
- PrivateLink provides service-level connectivity rather than broad network connectivity, making it useful for private AWS services, cross-account services, SaaS integrations, and microservice architectures.
- Interface endpoints complement rather than universally replace NAT Gateway; production architectures should deliberately route AWS service traffic through endpoints, S3/DynamoDB through gateway endpoints, and genuine public internet traffic through NAT where required.