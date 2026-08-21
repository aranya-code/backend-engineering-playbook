# 10- Gateway Endpoints

## Overview

Gateway endpoints provide private connectivity from resources in a VPC to supported AWS services through VPC route tables.

They are one of the simplest mechanisms for reducing unnecessary internet egress from private workloads. Unlike interface endpoints, gateway endpoints do not create endpoint network interfaces in your subnets. Instead, they integrate with route tables.

Gateway endpoints currently support:

- Amazon S3
- Amazon DynamoDB

A typical private-subnet architecture is:

```text
Private Application
       |
       v
Private Route Table
       |
       v
Gateway Endpoint
       |
       v
S3 / DynamoDB
```

Without a gateway endpoint, a private IPv4 workload may instead use:

```text
Private Application
       |
       v
NAT Gateway
       |
       v
Internet Gateway
       |
       v
AWS Service
```

For backend systems that frequently access S3 or DynamoDB, gateway endpoints can simplify networking, reduce NAT dependency, and keep service traffic on a private AWS connectivity path.

---

## What Is a Gateway Endpoint?

A gateway endpoint is a VPC endpoint that provides private access to supported AWS services by adding service-specific routes to selected VPC route tables.

The endpoint itself is not an Elastic Network Interface.

Instead, AWS integrates the endpoint with the VPC routing layer.

Conceptually:

```text
Application
    |
    v
Subnet
    |
    v
Route Table
    |
    +----> Local VPC traffic
    |
    +----> Gateway Endpoint
                  |
                  v
             AWS Service
```

The two supported services are:

| AWS Service | Gateway Endpoint |
|---|---|
| Amazon S3 | Yes |
| Amazon DynamoDB | Yes |

For other AWS services, an interface endpoint is typically the relevant endpoint type when the service supports AWS PrivateLink.

---

## Why Gateway Endpoints Exist

Private applications frequently need AWS-managed storage and database services.

For example, a Django application may store uploaded files in S3:

```text
Django
   |
   v
S3
```

If the Django application runs in a private subnet, it still needs a network path to S3.

One option is:

```text
Django
   |
   v
NAT Gateway
   |
   v
Internet Gateway
   |
   v
S3
```

A gateway endpoint provides:

```text
Django
   |
   v
Private Route Table
   |
   v
S3 Gateway Endpoint
   |
   v
S3
```

The second architecture removes NAT Gateway from that traffic path.

---

## Gateway Endpoint vs Interface Endpoint

The distinction is fundamental to VPC endpoint design.

| Characteristic | Gateway Endpoint | Interface Endpoint |
|---|---|---|
| Primary mechanism | Route table | Network interfaces |
| AWS technology | VPC endpoint routing | AWS PrivateLink |
| ENI created | No | Yes |
| Security Group attached to endpoint | No | Yes |
| Subnet selection | No endpoint ENI placement | Required |
| Route table association | Required | Not the primary mechanism |
| Supported services | S3, DynamoDB | Many AWS services |
| Private DNS | Not the core mechanism | Commonly used |
| Typical cost model | No hourly endpoint charge | Hourly and data-processing charges |
| Operational complexity | Low | Higher |

A useful rule is:

```text
S3 / DynamoDB
    |
    v
Gateway Endpoint

Most other supported AWS services
    |
    v
Interface Endpoint
```

Always verify current AWS service support for the target Region and service.

---

## How Gateway Endpoints Work

A gateway endpoint changes the routing behavior of the selected route tables.

For example, a private subnet may have a route table containing:

```text
Destination                  Target
10.0.0.0/16                  local
S3 prefix list               vpce-xxxxxxxx
0.0.0.0/0                    nat-xxxxxxxx
```

The important point is that the S3-specific route is more specific than the default route.

Therefore:

```text
S3 traffic
    |
    v
Gateway Endpoint
```

while general internet traffic continues to use:

```text
0.0.0.0/0
    |
    v
NAT Gateway
```

This allows the same private subnet to use both mechanisms.

---

## Route Selection

AWS route tables use longest-prefix matching.

Conceptually:

```text
S3 destination
      |
      +----> S3-specific route
      |
      +----> 0.0.0.0/0
```

The S3-specific route wins because it is more specific than the default route.

Therefore, creating a gateway endpoint does not necessarily mean that all outbound traffic stops using NAT.

Instead:

```text
S3
  -> Gateway Endpoint

DynamoDB
  -> Gateway Endpoint

Third-party API
  -> NAT Gateway
```

This is an important production networking pattern.

---

## Gateway Endpoint Architecture

```mermaid
flowchart TB
    subgraph VPC["VPC"]
        APP["Private Application"]
        RT["Private Route Table"]
        EP["Gateway Endpoint"]
        NAT["NAT Gateway"]
    end

    S3["Amazon S3"]
    INTERNET["External Internet"]

    APP --> RT

    RT -->|S3 route| EP
    EP --> S3

    RT -->|0.0.0.0/0| NAT
    NAT --> INTERNET
```

The gateway endpoint handles supported AWS service traffic while the NAT Gateway remains available for destinations that genuinely require public internet egress.

---

## Gateway Endpoint and S3

S3 is one of the most common gateway endpoint use cases.

A private application might perform:

```text
PUT object
GET object
DELETE object
LIST objects
```

through the S3 API.

With a gateway endpoint:

```text
Application
    |
    v
Route Table
    |
    v
S3 Gateway Endpoint
    |
    v
Amazon S3
```

No public IPv4 address is required on the application.

No NAT Gateway is required for that S3 traffic.

---

## Gateway Endpoint and DynamoDB

DynamoDB is the other AWS service supported by gateway endpoints.

A private backend service might perform:

```text
Application
    |
    v
DynamoDB API
```

through:

```text
Application
    |
    v
Private Route Table
    |
    v
DynamoDB Gateway Endpoint
    |
    v
DynamoDB
```

This is useful for private microservices, workers, batch systems, and server-side applications that access DynamoDB heavily.

---

## Gateway Endpoint Is Not a Network Interface

One of the easiest ways to distinguish endpoint types is:

```text
Gateway Endpoint
    -> Route table integration

Interface Endpoint
    -> ENI in subnet
```

A gateway endpoint does not consume a private IP address from your subnet for an endpoint ENI.

This makes gateway endpoints operationally simpler than interface endpoints.

---

## Gateway Endpoint and Private Subnets

A gateway endpoint is particularly useful in private subnets.

For example:

```text
Private Subnet A
    |
    +----> Django
    |
    +----> Celery Worker
    |
    +----> S3 Gateway Endpoint
```

The workload can remain private while still interacting with S3.

This is a common architecture for:

- File storage
- Backups
- Data processing
- Static asset storage
- Application exports
- Log archives
- Data pipelines

---

## Gateway Endpoint and Public Subnets

Gateway endpoints are not inherently restricted to private subnets.

The endpoint is associated with route tables, and any subnet using those route tables can use the endpoint.

However, the strongest architectural use case is often private workloads that should avoid unnecessary internet egress.

For example:

```text
Public Web Tier
    |
    v
S3

Private Application Tier
    |
    v
S3 Gateway Endpoint
```

The endpoint is a routing mechanism rather than a "private subnet feature."

---

## Route Table Association

When creating a gateway endpoint, route tables must be associated with it.

For example:

```text
Gateway Endpoint
    |
    +---- Private Route Table A
    |
    +---- Private Route Table B
    |
    +---- Private Route Table C
```

This means workloads in those route-table-associated subnets can use the endpoint.

If a subnet uses a route table that is not associated with the gateway endpoint, the endpoint route will not be available there.

---

## One Endpoint for Multiple Subnets

A single gateway endpoint can be associated with multiple route tables.

For example:

```text
                 S3 Gateway Endpoint
                    /      |      \
                   /       |       \
                  v        v        v
              Route A   Route B   Route C
                 |         |         |
                 v         v         v
              Subnet A  Subnet B  Subnet C
```

This differs from interface endpoints, where endpoint network interfaces are placed into selected subnets.

---

## Availability Zone Considerations

Gateway endpoints are not deployed into individual Availability Zones.

They are associated with route tables.

Therefore, a single gateway endpoint can be used by workloads across multiple Availability Zones through the appropriate route tables.

For example:

```text
AZ A                     AZ B
-----                    -----
App A                    App B
  |                        |
  v                        v
Route A                  Route B
  |                        |
  +-----------+------------+
              |
              v
       Gateway Endpoint
              |
              v
         Amazon S3
```

This is one of the operational differences between gateway and interface endpoints.

---

## Gateway Endpoint and NAT Gateway

A common production architecture uses both.

```text
                         Private Application
                                |
                                v
                           Route Table
                           /        \
                          /          \
                    S3/DynamoDB    Other traffic
                       |               |
                       v               v
                Gateway Endpoint   NAT Gateway
                       |               |
                       v               v
                 AWS Service       Internet
```

The decision is based on destination.

| Destination | Typical Path |
|---|---|
| S3 | Gateway endpoint |
| DynamoDB | Gateway endpoint |
| Secrets Manager | Interface endpoint |
| SQS | Interface endpoint |
| ECR | Interface endpoints + required AWS service paths |
| Third-party REST API | NAT Gateway |
| Public SaaS | NAT Gateway |

---

## S3 Gateway Endpoint and NAT Cost

Suppose an application uploads large files to S3.

Without a gateway endpoint:

```text
Application
    |
    v
NAT Gateway
    |
    v
S3
```

Large amounts of data may therefore pass through NAT infrastructure.

With a gateway endpoint:

```text
Application
    |
    v
Gateway Endpoint
    |
    v
S3
```

This removes the NAT Gateway from that traffic path.

For high-volume S3 workloads, this can be an important architectural and cost consideration.

---

## Gateway Endpoint and AWS Service Traffic

A useful private-subnet architecture is:

```text
                         Private Workload
                               |
                     +---------+---------+
                     |                   |
                     v                   v
              AWS Service Traffic   Public Egress
                     |                   |
                     v                   v
              VPC Endpoints         NAT Gateway
                     |                   |
                     v                   v
              AWS Services            Internet
```

This creates a deliberate separation between:

- AWS-private traffic
- Public internet traffic

That separation is useful for security and operational reasoning.

---

## Gateway Endpoint Policy

Gateway endpoints can have endpoint policies.

An endpoint policy can control what can be accessed through the endpoint.

For example:

```text
Application
    |
    v
S3 Gateway Endpoint
    |
    | Endpoint Policy
    v
Approved S3 Bucket
```

This provides an additional authorization layer alongside IAM and resource policies.

---

## Endpoint Policy vs IAM

These controls should not be confused.

### IAM

IAM answers:

> Is this identity allowed to perform this API operation?

### Endpoint Policy

The endpoint policy can restrict:

> Which AWS resources and actions are allowed through this VPC endpoint?

### Resource Policy

For S3, the bucket policy can additionally determine:

> Does this bucket allow this principal and request?

A mature architecture may therefore use:

```text
Identity Policy
      +
Endpoint Policy
      +
Bucket Policy
```

to implement defense in depth.

---

## S3 Endpoint Policy Example

A restrictive endpoint policy might look like:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowProductionReportsBucket",
      "Effect": "Allow",
      "Principal": "*",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::production-reports/*"
      ]
    }
  ]
}
```

The exact policy should match the application's actual requirements.

Avoid broad endpoint policies when the workload only needs access to a small number of resources.

---

## S3 Bucket Policy and Gateway Endpoints

A bucket policy can further restrict access.

For example, organizations may restrict access to requests originating from a specific VPC endpoint.

Conceptually:

```text
Private Application
      |
      v
S3 Gateway Endpoint
      |
      v
S3 Bucket
      |
      +----> Bucket Policy
                 |
                 v
          Allow approved endpoint
```

This can be useful for highly controlled data environments.

However, bucket policies should be designed carefully because an incorrect policy can block legitimate workloads.

---

## Gateway Endpoint and Django

Consider a Django application storing user-uploaded files in S3.

Application code might use:

```python
import boto3

s3 = boto3.client("s3")

s3.upload_file(
    "/tmp/report.pdf",
    "production-reports",
    "reports/report.pdf",
)
```

The application does not need endpoint-specific code.

The networking path can be:

```text
Django
   |
   v
Private Route Table
   |
   v
S3 Gateway Endpoint
   |
   v
S3
```

This is a desirable separation of concerns:

```text
Application
    -> AWS SDK

Infrastructure
    -> Routing through VPC endpoint
```

---

## Gateway Endpoint and FastAPI

FastAPI applications can use the same architecture.

For example:

```python
import boto3

s3 = boto3.client("s3")

def upload_report(path: str) -> None:
    s3.upload_file(
        path,
        "production-reports",
        "reports/report.json",
    )
```

The application does not need to know whether S3 connectivity uses:

```text
NAT Gateway
```

or:

```text
Gateway Endpoint
```

That decision belongs to the infrastructure layer.

---

## Gateway Endpoint and Celery

Celery workers commonly perform asynchronous file-processing operations.

For example:

```text
Celery Worker
     |
     v
Process file
     |
     v
Upload result to S3
```

The production network path can be:

```text
Celery Worker
     |
     v
Private Route Table
     |
     v
S3 Gateway Endpoint
     |
     v
S3
```

This allows workers to remain private while accessing object storage.

---

## Gateway Endpoint and Data Processing

Large data-processing workloads are particularly relevant.

For example:

```text
Private Processing Cluster
          |
          v
      S3 Dataset
```

The workload may:

- Read large input files
- Write transformed datasets
- Store intermediate objects
- Upload reports
- Archive results

Routing all of that traffic through NAT can create unnecessary dependency and cost.

A gateway endpoint provides a more direct architecture:

```text
Processing Cluster
        |
        v
Gateway Endpoint
        |
        v
S3
```

---

## Gateway Endpoint and Kubernetes

An EKS workload can access S3 through a gateway endpoint if the underlying node or pod networking uses route tables associated with the endpoint.

Conceptually:

```text
Pod
 |
 v
Node / Pod Network
 |
 v
VPC Route Table
 |
 v
S3 Gateway Endpoint
 |
 v
S3
```

This is particularly useful for:

- Model artifacts
- Configuration files
- Application assets
- Data pipelines
- Backups
- Batch processing

Endpoint behavior should be validated against the specific EKS networking model in use.

---

## Gateway Endpoint and Docker

Docker itself does not change VPC routing.

A container running on an EC2 host or container platform ultimately uses the networking path provided by its underlying network architecture.

For a private workload:

```text
Container
    |
    v
VPC Networking
    |
    v
Route Table
    |
    v
Gateway Endpoint
    |
    v
S3
```

The important architectural layer is the VPC networking path rather than Docker itself.

---

## Gateway Endpoint and PostgreSQL

Gateway endpoints do not replace normal private VPC connectivity to databases.

For example:

```text
Django
   |
   | PostgreSQL
   v
Private PostgreSQL
```

This uses VPC local routing.

S3 access may use:

```text
Django
   |
   v
S3 Gateway Endpoint
   |
   v
S3
```

These are two independent network paths.

---

## Gateway Endpoint and Redis

Redis should similarly remain on private VPC networking:

```text
Application
    |
    v
Private Redis
```

S3 access can use:

```text
Application
    |
    v
S3 Gateway Endpoint
```

Do not route internal service communication through a gateway endpoint.

Gateway endpoints are specifically for supported AWS services.

---

## Gateway Endpoint and Kafka

Kafka communication is normally separate from gateway endpoint routing.

For example:

```text
Application
    |
    v
Private Kafka
```

S3 access:

```text
Application
    |
    v
S3 Gateway Endpoint
```

External Kafka services may require a different connectivity model, such as NAT Gateway, PrivateLink, VPC peering, Transit Gateway, or dedicated connectivity depending on the provider.

---

## AWS CLI: List Gateway Endpoints

List all VPC endpoints:

```bash
aws ec2 describe-vpc-endpoints
```

Filter gateway endpoints:

```bash
aws ec2 describe-vpc-endpoints \
    --filters Name=vpc-endpoint-type,Values=Gateway
```

Filter by VPC:

```bash
aws ec2 describe-vpc-endpoints \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx \
              Name=vpc-endpoint-type,Values=Gateway
```

Inspect an endpoint:

```bash
aws ec2 describe-vpc-endpoints \
    --vpc-endpoint-ids vpce-xxxxxxxx
```

---

## Creating an S3 Gateway Endpoint

Example:

```bash
aws ec2 create-vpc-endpoint \
    --vpc-id vpc-xxxxxxxx \
    --service-name com.amazonaws.us-east-1.s3 \
    --vpc-endpoint-type Gateway \
    --route-table-ids rtb-private-a rtb-private-b
```

The service name is Region-specific.

For another Region, use the appropriate service name for that Region.

---

## Creating a DynamoDB Gateway Endpoint

Example:

```bash
aws ec2 create-vpc-endpoint \
    --vpc-id vpc-xxxxxxxx \
    --service-name com.amazonaws.us-east-1.dynamodb \
    --vpc-endpoint-type Gateway \
    --route-table-ids rtb-private-a rtb-private-b
```

---

## Terraform: S3 Gateway Endpoint

A typical Terraform configuration is:

```hcl
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.us-east-1.s3"
  vpc_endpoint_type = "Gateway"

  route_table_ids = [
    aws_route_table.private_a.id,
    aws_route_table.private_b.id,
  ]

  tags = {
    Name = "s3-gateway-endpoint"
  }
}
```

For production infrastructure, avoid hard-coding the Region when the Terraform configuration already has a Region provider or variable.

For example:

```hcl
data "aws_region" "current" {}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"

  route_table_ids = [
    aws_route_table.private_a.id,
    aws_route_table.private_b.id,
  ]

  tags = {
    Name = "s3-gateway-endpoint"
  }
}
```

---

## Terraform: DynamoDB Gateway Endpoint

```hcl
data "aws_region" "current" {}

resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.dynamodb"
  vpc_endpoint_type = "Gateway"

  route_table_ids = [
    aws_route_table.private_a.id,
    aws_route_table.private_b.id,
  ]

  tags = {
    Name = "dynamodb-gateway-endpoint"
  }
}
```

---

## Route Table Verification

After creating a gateway endpoint, verify that the route tables contain the expected endpoint route.

For example:

```bash
aws ec2 describe-route-tables \
    --route-table-ids rtb-private-a
```

Look for a route associated with the relevant AWS service prefix list and gateway endpoint.

The exact route representation may vary in CLI output, so inspect the complete route table rather than relying on a single field.

---

## Prefix Lists

Gateway endpoints use AWS-managed prefix lists to represent service destinations.

Conceptually:

```text
Private Application
       |
       v
Route Table
       |
       | Destination = S3 prefix list
       v
Gateway Endpoint
       |
       v
S3
```

This is different from simply adding:

```text
0.0.0.0/0
```

to the endpoint.

The service-specific route is more precise.

---

## Prefix List vs CIDR

A common mistake is expecting the gateway endpoint route to look like:

```text
S3 -> 52.x.x.x/...
```

AWS service IP ranges can be dynamic and are not something application teams should manually maintain for this purpose.

The AWS-managed prefix list abstracts the service destination.

This is one reason gateway endpoints are operationally simpler than manually maintaining routes to changing AWS service IP ranges.

---

## Gateway Endpoint Routing Behavior

Consider:

```text
Route Table

Destination                  Target
10.0.0.0/16                  local
S3 prefix list               vpce-xxxxxxxx
0.0.0.0/0                    nat-xxxxxxxx
```

Traffic behaves approximately as:

```text
Destination = S3
    |
    v
S3 prefix-list route
    |
    v
Gateway Endpoint
```

while:

```text
Destination = api.example.com
    |
    v
Default route
    |
    v
NAT Gateway
```

This is a powerful pattern because endpoint traffic and internet traffic can coexist in the same private subnet.

---

## Security Considerations

Gateway endpoints improve network isolation but do not automatically provide least-privilege access.

Use multiple controls:

```text
Application
    |
    v
IAM
    |
    v
Gateway Endpoint
    |
    v
Endpoint Policy
    |
    v
S3 Bucket Policy
    |
    v
S3
```

Important considerations include:

- Restrict IAM permissions.
- Use endpoint policies where appropriate.
- Restrict S3 bucket policies.
- Restrict access to sensitive buckets.
- Use encryption for sensitive data.
- Use KMS where required.
- Monitor access through CloudTrail and service-specific logging.
- Avoid assuming network-private means authorization-safe.

---

## S3 Security Example

Suppose a production application should only access:

```text
s3://production-reports/
```

A robust authorization model can combine:

```text
IAM
  -> Allow required S3 actions

Endpoint Policy
  -> Restrict endpoint access

Bucket Policy
  -> Restrict approved principals/endpoints

S3 Block Public Access
  -> Prevent public exposure
```

Each control protects against different classes of mistakes.

---

## Gateway Endpoint and S3 Encryption

A gateway endpoint does not encrypt S3 objects by itself.

S3 encryption should be designed independently.

Common options include:

- S3-managed encryption
- AWS KMS-based encryption
- Customer-managed KMS keys

The network path:

```text
Application
    |
    v
Gateway Endpoint
    |
    v
S3
```

does not replace:

```text
S3 encryption
+
IAM
+
KMS authorization
```

Security must be considered at both network and data layers.

---

## Monitoring

Gateway endpoints themselves do not provide the same ENI-level monitoring model as interface endpoints.

Monitor the surrounding system:

- VPC Flow Logs
- CloudTrail
- S3 access logs where appropriate
- CloudWatch service metrics
- Application errors
- Application latency
- Route table configuration
- Endpoint configuration

For S3, application-level errors can help distinguish:

```text
Application authorization failure
```

from:

```text
Network routing failure
```

from:

```text
S3 service failure
```

---

## Troubleshooting Gateway Endpoints

When a private workload cannot access S3 or DynamoDB, verify the path systematically.

```text
Application
    |
    v
Subnet
    |
    v
Associated Route Table
    |
    v
Gateway Endpoint Route
    |
    v
AWS Service
```

Check each layer.

---

## Troubleshooting Checklist

```text
[ ] Is the destination S3 or DynamoDB?
[ ] Does the AWS Region support the required endpoint?
[ ] Does the gateway endpoint exist?
[ ] Is the endpoint in the correct VPC?
[ ] Is the workload subnet using the expected route table?
[ ] Is that route table associated with the endpoint?
[ ] Does the route table contain the expected service route?
[ ] Is the endpoint policy allowing the operation?
[ ] Does IAM allow the API operation?
[ ] Does the S3 bucket/DynamoDB resource policy allow it?
[ ] Are Security Groups relevant to the actual path?
[ ] Are NACLs blocking traffic?
[ ] Is DNS functioning correctly?
[ ] Is the AWS service itself healthy?
```

---

## Common Troubleshooting Scenario

Suppose a private EC2 instance can reach the internet through NAT but cannot access S3 as expected.

First check:

```text
Route Table
```

You may find:

```text
0.0.0.0/0 -> NAT Gateway
```

but no gateway endpoint route.

In that case, the traffic can still potentially reach S3 through NAT, but the intended endpoint architecture is not being used.

Verify that:

```text
S3 prefix list -> Gateway Endpoint
```

exists in the route table used by the subnet.

---

## Gateway Endpoint vs NAT Gateway

| Requirement | Gateway Endpoint | NAT Gateway |
|---|---|---|
| S3 access | Yes | Yes |
| DynamoDB access | Yes | Yes |
| Third-party API | No | Yes |
| Arbitrary internet destination | No | Yes |
| Private AWS service path | Yes | No |
| Requires public subnet | No | NAT itself requires public connectivity |
| Uses route table | Yes | Private route uses NAT target |
| Typical S3 design | Preferred | Alternative |
| Internet egress | No | Yes |

The key difference is scope.

Gateway endpoints provide private access to specific supported AWS services.

NAT Gateway provides outbound IPv4 internet access.

---

## Gateway Endpoint vs Interface Endpoint

For an AWS service requirement:

```text
S3
 |
 v
Gateway Endpoint

DynamoDB
 |
 v
Gateway Endpoint

Secrets Manager
 |
 v
Interface Endpoint

SQS
 |
 v
Interface Endpoint
```

Do not create an interface endpoint simply because the term "VPC endpoint" sounds more general.

Choose the endpoint type based on the AWS service and required architecture.

---

## Cost Considerations

Gateway endpoints are particularly attractive from a cost perspective because they do not have the same per-hour endpoint pricing model associated with interface endpoints.

They can also reduce NAT Gateway data-processing costs when they replace NAT-based S3 or DynamoDB traffic.

Consider:

```text
Without Gateway Endpoint

Application
    |
    v
NAT Gateway
    |
    v
S3
```

versus:

```text
With Gateway Endpoint

Application
    |
    v
Gateway Endpoint
    |
    v
S3
```

For high-volume workloads, the reduction in NAT processing can be significant.

Always evaluate the complete architecture and current AWS pricing rather than assuming one network design is universally cheaper.

---

## Performance Considerations

Gateway endpoints can remove an unnecessary NAT hop for S3 and DynamoDB traffic.

Compare:

```text
Application
    |
    v
NAT Gateway
    |
    v
AWS Service
```

with:

```text
Application
    |
    v
Gateway Endpoint
    |
    v
AWS Service
```

The endpoint architecture provides a more direct service-specific network path.

However, application performance is still affected by:

- AWS service latency
- Application connection management
- SDK behavior
- Request size
- Concurrency
- Retry policies
- Service throttling

Do not attribute every AWS API latency problem to VPC routing.

---

## Reliability Considerations

Gateway endpoints are naturally well suited to multi-AZ private architectures because route tables in multiple AZs can reference the same endpoint.

For example:

```text
AZ A
App A
 |
 v
Route A
 |
 +------+
        |
        v
 Gateway Endpoint
        ^
        |
 +------+
 |
 v
Route B
 |
 v
App B
AZ B
```

There is no need to deploy one gateway endpoint per AZ simply because the applications span multiple AZs.

However, every relevant route table must be correctly associated.

---

## Disaster Recovery

Gateway endpoints should be part of the VPC's Infrastructure as Code.

A disaster recovery environment should recreate:

- VPC
- Subnets
- Route tables
- Gateway endpoints
- Endpoint policies
- IAM policies
- S3 bucket policies
- Required service configuration

For example:

```text
Primary VPC
    |
    +---- S3 Gateway Endpoint

DR VPC
    |
    +---- S3 Gateway Endpoint
```

Do not assume that recreating only application instances is sufficient.

Networking dependencies are part of the application platform.

---

## Infrastructure as Code

For production environments, manage gateway endpoints through:

- Terraform
- AWS CloudFormation
- AWS CDK
- Other approved Infrastructure-as-Code systems

Avoid manually creating production endpoints through the console when the environment is expected to be reproducible.

A gateway endpoint is not merely a configuration convenience.

It is part of the application's network architecture.

---

## Production Architecture

A typical multi-AZ backend architecture can look like:

```mermaid
flowchart TB
    subgraph VPC["Production VPC"]
        subgraph AZ_A["Availability Zone A"]
            APP_A["Private Application A"]
            RT_A["Private Route Table A"]
        end

        subgraph AZ_B["Availability Zone B"]
            APP_B["Private Application B"]
            RT_B["Private Route Table B"]
        end

        S3EP["S3 Gateway Endpoint"]
        DDBEP["DynamoDB Gateway Endpoint"]
        NAT["NAT Gateway"]
    end

    S3["Amazon S3"]
    DDB["Amazon DynamoDB"]
    INTERNET["External Internet"]

    APP_A --> RT_A
    APP_B --> RT_B

    RT_A --> S3EP
    RT_B --> S3EP

    RT_A --> DDBEP
    RT_B --> DDBEP

    RT_A --> NAT
    RT_B --> NAT

    S3EP --> S3
    DDBEP --> DDB
    NAT --> INTERNET
```

The architecture intentionally separates:

```text
AWS storage/database traffic
        ->
Gateway endpoints

Public internet traffic
        ->
NAT Gateway
```

---

## Production Best Practices

### Associate All Required Route Tables

Make sure every subnet that needs the endpoint uses a route table associated with it.

### Use Endpoint Policies

Restrict endpoint access where the security model requires it.

### Use IAM Least Privilege

Endpoint policies do not replace IAM.

### Keep Internal Traffic Private

Do not route VPC-internal services through NAT.

### Use Gateway Endpoints for Supported Services

Prefer the appropriate endpoint type rather than unnecessarily routing supported service traffic through internet egress.

### Manage Endpoints Through IaC

Make endpoint configuration reproducible.

### Monitor Access

Use VPC Flow Logs, CloudTrail, service metrics, and application telemetry as appropriate.

### Validate Multi-AZ Routing

Ensure every relevant route table is configured consistently.

---

## Common Mistakes

### Assuming Gateway Endpoints Create ENIs

They do not.

Gateway endpoints integrate with route tables.

### Forgetting Route Table Association

Creating the endpoint alone does not make it available to every subnet.

### Assuming All AWS Services Support Gateway Endpoints

Gateway endpoints primarily support S3 and DynamoDB.

### Assuming Gateway Endpoints Replace NAT

They do not provide arbitrary internet access.

### Using NAT for Everything

This can introduce unnecessary NAT dependency and cost.

### Ignoring Endpoint Policies

IAM may allow an operation while the endpoint policy prevents it.

### Confusing Route Tables With Security Groups

Gateway endpoints are routing constructs. Security Groups are stateful network controls attached to network interfaces.

### Assuming the Endpoint Handles IAM

The endpoint provides connectivity. AWS authorization still applies.

### Forgetting the DR Environment

The endpoint should be part of the reproducible network architecture.

---

## Interview Traps

### What is a gateway endpoint?

A VPC endpoint that provides private connectivity to supported AWS services through VPC route tables.

### Which AWS services support gateway endpoints?

Amazon S3 and DynamoDB.

### Does a gateway endpoint create an ENI?

No.

### Does a gateway endpoint require a subnet?

It is associated with route tables rather than placing endpoint network interfaces into subnets.

### How does traffic reach an S3 gateway endpoint?

The route table contains a route for the S3 service prefix list targeting the gateway endpoint.

### Can one gateway endpoint serve multiple subnets?

Yes, by associating it with the route tables used by those subnets.

### Does a gateway endpoint require a NAT Gateway?

No.

### Does a gateway endpoint provide general internet access?

No.

### Can a private subnet use both a gateway endpoint and NAT Gateway?

Yes.

For example:

```text
S3 -> Gateway Endpoint
Internet -> NAT Gateway
```

### Does a gateway endpoint replace IAM?

No.

IAM remains responsible for identity authorization.

### What is the main difference between gateway and interface endpoints?

Gateway endpoints use route-table integration for S3 and DynamoDB, while interface endpoints use private network interfaces and AWS PrivateLink for many supported services.

### Why are gateway endpoints useful for S3-heavy workloads?

They provide private service connectivity and can remove S3 traffic from the NAT Gateway path, reducing unnecessary dependency and potentially lowering networking costs.

## Key Takeaways

- Gateway endpoints provide private, route-table-based connectivity from VPC resources to Amazon S3 and DynamoDB without requiring NAT Gateway or public internet access for that service traffic.
- Gateway endpoints do not create ENIs; instead, they add service-specific routes to the route tables associated with the endpoint.
- A private subnet can use both gateway endpoints and NAT Gateway, allowing AWS service traffic to use private routing while third-party and public internet traffic uses NAT.
- Gateway endpoint security should combine endpoint policies, IAM, resource policies, encryption, and appropriate monitoring rather than relying on network isolation alone.
- For production systems, manage gateway endpoints through Infrastructure as Code and ensure all required route tables, endpoint policies, and disaster recovery environments are consistently configured.