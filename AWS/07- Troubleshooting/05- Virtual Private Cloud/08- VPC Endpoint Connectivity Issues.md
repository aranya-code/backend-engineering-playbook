# 08- VPC Endpoint Connectivity Issues

## Overview

VPC endpoints provide private connectivity from resources inside a VPC to supported AWS services without requiring traffic to traverse the public internet. They are commonly used by private application subnets for services such as Amazon S3, DynamoDB, ECR, CloudWatch, Secrets Manager, and many other AWS APIs.

Endpoint connectivity failures are often misdiagnosed because several independent networking and authorization layers participate in the request:

```text
Application
    |
    v
DNS
    |
    v
Route / Endpoint Selection
    |
    v
VPC Endpoint
    |
    +--> Endpoint Policy
    |
    +--> Security Group / NACL
    |
    v
AWS Service
    |
    v
IAM Authorization
```

A working VPC endpoint therefore does not automatically imply that an application can successfully call the target AWS service.

A useful troubleshooting sequence is:

```text
DNS
  -> Endpoint type
  -> Route table
  -> Security Group
  -> Network ACL
  -> Endpoint policy
  -> IAM policy
  -> AWS service policy
  -> Application configuration
```

The exact path depends on whether the endpoint is a **Gateway Endpoint**, **Interface Endpoint**, or another endpoint-supported architecture.

## What Is a VPC Endpoint?

A VPC endpoint provides private connectivity between a VPC and supported AWS services.

The primary purpose is to avoid unnecessary internet-based paths for AWS service traffic.

Without an endpoint, a private application might use:

```text
Private Subnet
    |
    v
NAT Gateway
    |
    v
Internet Gateway
    |
    v
AWS Public Service Endpoint
```

With an endpoint, the architecture can instead be:

```text
Private Subnet
    |
    v
VPC Endpoint
    |
    v
AWS Service
```

This can improve:

- Network isolation.
- Security posture.
- Reliability of AWS-service access.
- Cost efficiency for supported traffic patterns.
- Control over service access.

## Endpoint Types

The most important troubleshooting distinction is between gateway and interface endpoints.

| Characteristic | Gateway Endpoint | Interface Endpoint |
|---|---|---|
| Implementation | Route-table target | ENIs in subnets |
| Uses PrivateLink | No | Yes |
| Typical services | S3, DynamoDB | Many AWS APIs |
| Security Group | Not attached to endpoint | Endpoint ENI uses Security Group |
| Route table | Required | Usually not the primary selection mechanism |
| DNS | Service-specific behavior | Private DNS commonly used |
| AZ placement | Route-table based | Endpoint ENI is placed in selected subnets |
| Cost model | No endpoint hourly charge | Endpoint hourly/data-processing charges apply |

The troubleshooting methodology differs significantly between the two.

## Gateway Endpoint Connectivity

Gateway endpoints are most commonly used for:

- Amazon S3.
- Amazon DynamoDB.

The endpoint is associated with route tables.

Conceptually:

```text
Private Subnet
    |
    v
Route Table
    |
    | Destination: S3 prefix list
    | Target: vpce-xxxx
    v
Gateway Endpoint
    |
    v
S3
```

The endpoint does not appear as an ENI inside the subnet in the same way as an interface endpoint.

## Interface Endpoint Connectivity

An interface endpoint creates one or more elastic network interfaces in selected subnets.

For example:

```text
Private Application Subnet
        |
        v
DNS
        |
        v
vpce ENI
10.0.10.50
        |
        v
AWS PrivateLink
        |
        v
AWS Service
```

The endpoint ENI has:

- A private IP address.
- A Security Group association.
- A subnet placement.
- DNS names associated with the endpoint.

Interface endpoints therefore require troubleshooting at the network-interface level.

## Endpoint Connectivity Architecture

A typical private backend architecture might look like:

```mermaid
flowchart LR
    App[Private Django / FastAPI Application]
    DNS[Route 53 / VPC DNS]
    S3[S3]
    Secrets[Secrets Manager]
    ECR[ECR API]
    VPCE1[Gateway Endpoint]
    VPCE2[Interface Endpoint]
    SG[Endpoint Security Group]
    IAM[IAM Policies]

    App --> DNS
    DNS --> VPCE2
    App --> VPCE1
    VPCE1 --> S3
    VPCE2 --> Secrets
    VPCE2 --> ECR
    SG --> VPCE2
    IAM --> App
```

The application can be completely private while still accessing required AWS APIs.

## Troubleshooting Methodology

When an endpoint request fails, do not immediately recreate the endpoint.

Determine exactly where the request fails.

Use this model:

```text
Application
    |
    v
Can DNS resolve the expected endpoint?
    |
    v
Is the endpoint type correct?
    |
    v
Does the network path exist?
    |
    v
Do SG/NACL rules permit traffic?
    |
    v
Does the endpoint policy permit the action?
    |
    v
Does IAM permit the action?
    |
    v
Does the AWS service resource policy permit it?
    |
    v
Does the application use the expected AWS region/service?
```

This avoids making unrelated changes that obscure the actual root cause.

## Verify the Endpoint Exists

Start by inspecting the endpoint:

```bash
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids vpce-0123456789abcdef0
```

Useful fields include:

```text
VpcEndpointId
VpcId
ServiceName
VpcEndpointType
State
SubnetIds
RouteTableIds
SecurityGroupIds
PrivateDnsEnabled
PolicyDocument
```

A healthy endpoint should normally have:

```text
State = available
```

A state such as:

```text
pending
failed
deleting
```

requires investigation before debugging application behavior.

## Verify the Endpoint Type

Do not apply gateway-endpoint troubleshooting to an interface endpoint.

Check:

```bash
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids vpce-0123456789abcdef0 \
  --query 'VpcEndpoints[].{
    Id:VpcEndpointId,
    Type:VpcEndpointType,
    Service:ServiceName,
    State:State
  }'
```

Example:

```text
Gateway
```

or:

```text
Interface
```

The type determines which networking components must be inspected.

## Gateway Endpoint Troubleshooting

For a gateway endpoint, inspect the route tables associated with the endpoint.

```bash
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids vpce-0123456789abcdef0 \
  --query 'VpcEndpoints[].RouteTableIds'
```

Then inspect those route tables:

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0
```

Look for the AWS service prefix-list route targeting the endpoint.

Conceptually:

```text
Destination:
pl-xxxxxxxx

Target:
vpce-xxxxxxxx
```

For S3 or DynamoDB, the endpoint route should be present in the route table used by the application subnet.

## Common Gateway Endpoint Failure

A private application is expected to access S3:

```text
Application subnet
      |
      v
Route Table
      |
      v
S3 Gateway Endpoint
```

But the subnet is associated with a different route table.

Result:

```text
Application
    |
    v
Wrong Route Table
    |
    X
No S3 Endpoint Route
```

The endpoint itself can be healthy while the application still cannot use it.

Always verify the actual route table associated with the application's subnet.

## Verify Subnet-to-Route-Table Association

Identify the subnet:

```bash
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[].Instances[].SubnetId'
```

Then inspect the route table:

```bash
aws ec2 describe-route-tables \
  --filters \
    Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

This is important because a route table can exist and contain the correct endpoint route while the workload is actually using another route table.

## Interface Endpoint Troubleshooting

Interface endpoints are fundamentally different.

The endpoint creates ENIs in selected subnets.

Inspect:

```bash
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids vpce-0123456789abcdef0 \
  --query 'VpcEndpoints[].{
    Id:VpcEndpointId,
    Type:VpcEndpointType,
    Subnets:SubnetIds,
    ENIs:NetworkInterfaceIds,
    SGs:Groups,
    PrivateDNS:PrivateDnsEnabled
  }'
```

Then inspect the endpoint ENIs:

```bash
aws ec2 describe-network-interfaces \
  --network-interface-ids eni-0123456789abcdef0
```

Verify:

- ENI state.
- Subnet.
- Private IP.
- Security Groups.
- VPC.
- Availability Zone.

## Endpoint Security Groups

Interface endpoints have network interfaces and therefore Security Groups.

A common architecture is:

```text
Application SG
      |
      | TCP 443
      v
Endpoint SG
      |
      v
Interface Endpoint ENI
```

The endpoint Security Group must allow the application traffic.

For HTTPS-based AWS APIs, the common port is:

```text
TCP 443
```

A typical endpoint SG rule is:

```text
Inbound
TCP 443
Source: Application Security Group
```

This is preferable to:

```text
TCP 443
0.0.0.0/0
```

when the endpoint is intended for private application access.

## Application Security Group

The application-side Security Group must also permit outbound traffic.

For example:

```text
Application SG
Outbound:
TCP 443
Destination: Endpoint SG
```

Security Groups are stateful, so the response traffic does not generally require a separate inbound return rule.

This differs from the stateless NACL behavior.

## Network ACLs and Interface Endpoints

NACLs can still block interface endpoint traffic.

The path can be:

```text
Application ENI
    |
    v
Application Subnet NACL
    |
    v
Endpoint ENI
    |
    v
Endpoint Subnet NACL
```

If the NACLs are restrictive, validate:

- Application subnet outbound.
- Endpoint subnet inbound.
- Endpoint subnet outbound.
- Application subnet inbound.
- Ephemeral return ports where applicable.

A healthy endpoint Security Group does not override a NACL deny.

## DNS Is a Common Failure Point

Interface endpoints often depend on private DNS.

A common failure looks like:

```text
Application
    |
    | Resolve service.amazonaws.com
    v
DNS
    |
    X
Public address returned
```

when the application expected:

```text
Application
    |
    v
Private DNS
    |
    v
Endpoint ENI private IP
```

Verify endpoint configuration:

```bash
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids vpce-0123456789abcdef0 \
  --query 'VpcEndpoints[].PrivateDnsEnabled'
```

For supported interface endpoints, private DNS can allow applications to continue using normal AWS service hostnames while resolving them to private endpoint addresses.

## Test DNS Resolution

From a workload inside the VPC:

```bash
dig secretsmanager.us-east-1.amazonaws.com
```

or:

```bash
nslookup secretsmanager.us-east-1.amazonaws.com
```

Inspect whether the response resolves to private addresses when private DNS is expected.

For Linux:

```bash
getent hosts secretsmanager.us-east-1.amazonaws.com
```

If the result is unexpectedly public, investigate:

- VPC DNS support.
- VPC DNS hostnames.
- DHCP options.
- Route 53 Resolver behavior.
- Endpoint private DNS configuration.
- Custom DNS servers.
- Conditional forwarding.

## VPC DNS Attributes

Check the VPC DNS configuration:

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --attribute enableDnsSupport

aws ec2 describe-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --attribute enableDnsHostnames
```

Private DNS-based endpoint architectures depend on correct VPC DNS behavior.

A custom DNS configuration can unintentionally bypass the expected AWS resolver path.

## Endpoint Policy

An endpoint can be reachable at the network layer but still reject an API request because of its endpoint policy.

This is a critical distinction:

```text
Network connectivity
        |
        v
SUCCESS
        |
        v
Endpoint policy
        |
        X
Access denied
```

Inspect the policy:

```bash
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids vpce-0123456789abcdef0 \
  --query 'VpcEndpoints[].PolicyDocument'
```

Endpoint policies can restrict:

- Principals.
- Actions.
- Resources.

The exact policy model depends on the AWS service.

## Endpoint Policy vs IAM Policy

Both can participate in authorization.

For example:

```text
Application
    |
    v
IAM Policy
    |
    v
VPC Endpoint Policy
    |
    v
AWS Service Resource Policy
    |
    v
AWS Service
```

A request can fail even if IAM appears correct because another authorization layer denies it.

When you see:

```text
AccessDenied
```

do not automatically conclude that the network is broken.

Network failures and authorization failures require different troubleshooting paths.

## S3 Gateway Endpoint Example

Suppose a Django application in a private subnet uploads files to S3.

Application:

```text
Django
   |
   | boto3
   v
S3
```

Desired network path:

```text
Django
   |
   v
Private Subnet
   |
   v
Route Table
   |
   v
S3 Gateway Endpoint
   |
   v
S3
```

Check:

```bash
aws ec2 describe-vpc-endpoints \
  --filters \
    Name=vpc-id,Values=vpc-0123456789abcdef0 \
    Name=service-name,Values=com.amazonaws.us-east-1.s3
```

Then verify that the application's subnet route table is associated with the endpoint.

## S3 Endpoint Policy Failure

Suppose the endpoint policy allows access only to:

```text
arn:aws:s3:::company-production-assets/*
```

but the application attempts:

```text
arn:aws:s3:::company-user-uploads/*
```

The network path can be completely healthy.

The request may still fail authorization.

Therefore distinguish:

```text
Timeout
```

from:

```text
AccessDenied
```

A timeout suggests a networking problem more strongly than an explicit authorization error.

## ECR Connectivity

Private container workloads frequently need ECR access.

A typical ECS or Kubernetes architecture may require access to:

```text
ECR API
ECR DKR
S3
```

depending on the image-pull workflow and platform.

A simplified architecture:

```mermaid
flowchart LR
    Workload[Private Container Workload]
    ECRAPI[ECR API Endpoint]
    ECRDKR[ECR DKR Endpoint]
    S3[S3 Gateway Endpoint]

    Workload --> ECRAPI
    Workload --> ECRDKR
    Workload --> S3
```

If one required endpoint is missing, image pulls can fail even though other AWS APIs remain reachable.

Do not diagnose this as a generic "ECR problem."

Identify the exact service endpoint and network path involved.

## Secrets Manager Connectivity

A private Django, FastAPI, ECS, or Kubernetes workload may retrieve credentials from Secrets Manager:

```text
Application
    |
    v
Secrets Manager Interface Endpoint
    |
    v
Secrets Manager
```

If the endpoint is unavailable or DNS resolves incorrectly, the application may fail during:

- Startup.
- Configuration loading.
- Secret rotation.
- Request processing.

For production workloads, avoid making application startup depend on an unvalidated network path to a private endpoint.

Validate endpoint connectivity as part of infrastructure deployment.

## Endpoint Placement Across Availability Zones

Interface endpoints are deployed into selected subnets.

For highly available architectures:

```text
AZ-A
  |
  +--> Application
  |
  +--> Endpoint ENI

AZ-B
  |
  +--> Application
  |
  +--> Endpoint ENI
```

This reduces dependency on a single Availability Zone.

If an interface endpoint exists only in one AZ while workloads operate across several AZs, connectivity may still work through AWS networking, but the architecture can introduce unnecessary cross-AZ dependencies and costs.

For critical production services, consider placing interface endpoint ENIs in the required Availability Zones.

## Endpoint Availability and Application Resilience

An endpoint is part of the application's dependency graph.

For example:

```text
FastAPI
   |
   +--> PostgreSQL
   |
   +--> Redis
   |
   +--> Secrets Manager Endpoint
   |
   +--> S3 Endpoint
```

If an endpoint becomes unreachable, application behavior depends on the SDK and application timeout/retry configuration.

Production systems should avoid:

- Excessively long SDK timeouts.
- Unbounded retries.
- Synchronous dependency chains where unnecessary.
- Treating endpoint availability as guaranteed application availability.

Use appropriate:

- Connect timeouts.
- Read timeouts.
- Retry policies.
- Circuit-breaking strategies where appropriate.
- Health checks.

## Troubleshooting With Connectivity Tests

From an EC2 instance or other diagnostic environment inside the relevant subnet:

```bash
curl -v https://secretsmanager.us-east-1.amazonaws.com/
```

For TCP connectivity:

```bash
nc -vz secretsmanager.us-east-1.amazonaws.com 443
```

For DNS:

```bash
dig secretsmanager.us-east-1.amazonaws.com
```

These tests answer different questions.

| Test | What it tells you |
|---|---|
| `dig` / `nslookup` | DNS resolution |
| `nc` | TCP connectivity |
| `curl -v` | DNS + TCP + TLS + HTTP behavior |
| AWS CLI | Network + TLS + authentication + service authorization |

Do not treat a successful `ping` as proof of HTTPS service availability. ICMP behavior is not equivalent to TCP/443 connectivity.

## VPC Flow Logs

Flow Logs can help determine whether traffic reaches the endpoint ENI.

For interface endpoints, investigate flows involving:

```text
Application private IP
Endpoint ENI private IP
TCP 443
```

Conceptually:

```text
Application
10.0.10.20:49152
       |
       | TCP 443
       v
Endpoint ENI
10.0.20.50:443
```

If the flow is rejected, inspect:

- Security Groups.
- NACLs.
- Subnet configuration.

If the flow is accepted but the API call returns `AccessDenied`, investigate authorization instead.

## Reachability Analyzer

Reachability Analyzer is useful for validating network paths involving:

- ENIs.
- Subnets.
- Security Groups.
- Network ACLs.
- Route tables.
- VPC endpoints and related networking components where supported.

A useful workflow is:

```text
Application ENI
       |
       v
Endpoint ENI
```

If reachability fails, inspect the reported blocking component before changing configuration.

## Common Failure Patterns

| Symptom | Likely Cause |
|---|---|
| DNS returns public IP | Private DNS issue |
| DNS resolution fails | VPC/custom DNS issue |
| TCP 443 timeout | SG/NACL/routing/network path |
| Endpoint state not `available` | Endpoint provisioning/configuration issue |
| S3 access fails from one subnet | Missing gateway endpoint route |
| `AccessDenied` | IAM, endpoint policy, or service policy |
| Works in AZ-A but not AZ-B | Endpoint placement or subnet configuration |
| ECR image pull fails | Missing required endpoint/service path |
| Secrets Manager unavailable | Interface endpoint/DNS/SG issue |
| AWS CLI works publicly but not privately | Endpoint path or DNS configuration |
| Application uses NAT unexpectedly | Endpoint route/DNS configuration |
| Intermittent failures | AZ-specific or subnet-specific endpoint configuration |

## Troubleshooting Checklist

```text
[ ] Identify the AWS service being accessed
[ ] Identify the AWS region
[ ] Identify the VPC
[ ] Identify the source workload
[ ] Identify the source subnet
[ ] Identify the source Availability Zone
[ ] Identify endpoint type
[ ] Verify endpoint exists
[ ] Verify endpoint state is available
[ ] Verify service name is correct
[ ] Verify endpoint is in the expected VPC
[ ] For gateway endpoints, verify route-table association
[ ] For gateway endpoints, verify prefix-list route
[ ] For interface endpoints, verify subnet placement
[ ] For interface endpoints, inspect endpoint ENIs
[ ] Verify endpoint Security Groups
[ ] Verify application Security Groups
[ ] Verify NACLs
[ ] Verify VPC DNS support
[ ] Verify VPC DNS hostnames
[ ] Verify private DNS configuration
[ ] Test DNS from the workload subnet
[ ] Test TCP/443 connectivity
[ ] Inspect VPC Flow Logs
[ ] Inspect endpoint policy
[ ] Inspect IAM policies
[ ] Inspect service resource policies
[ ] Check AWS region configuration
[ ] Use Reachability Analyzer where appropriate
[ ] Compare endpoint configuration across Availability Zones
[ ] Check whether traffic unexpectedly uses NAT Gateway
[ ] Check recent CloudTrail configuration changes
[ ] Verify application timeout and retry behavior
```

## Common Mistakes

### Assuming an Endpoint Automatically Enables Connectivity

Creating:

```text
VPC Endpoint
```

does not guarantee:

```text
Application -> AWS Service
```

Routing, DNS, Security Groups, NACLs, endpoint policies, IAM, and service policies may still prevent access.

### Using the Wrong Endpoint Type

Gateway and interface endpoints have different networking behavior.

Do not look for an interface ENI when troubleshooting a gateway endpoint.

### Forgetting Gateway Endpoint Route Tables

A gateway endpoint is useful only to workloads whose route tables are configured to use it.

### Forgetting Private DNS

An interface endpoint can exist and be healthy while applications continue resolving the public service endpoint because private DNS is disabled or DNS is misconfigured.

### Allowing the Wrong Security Group

For interface endpoints, the endpoint ENI's Security Group must permit the application traffic.

A Security Group attached to the application alone is insufficient.

### Ignoring NACLs

A restrictive NACL can block traffic even when endpoint and Security Group configuration is correct.

### Treating AccessDenied as a Network Failure

An explicit authorization error usually requires policy analysis rather than route or Security Group changes.

### Testing From the Wrong Network

Testing an endpoint from a laptop or another VPC does not prove that the production workload subnet can reach it.

Run network tests from the same network context whenever possible.

### Deploying Interface Endpoints in Only One AZ

This can create unnecessary cross-AZ dependencies and make the architecture less resilient to subnet or AZ-specific failures.

### Assuming NAT and Endpoints Are Interchangeable

An endpoint and a NAT Gateway provide different network paths.

If endpoint configuration is broken, traffic may fail even though the NAT path would otherwise work. Conversely, allowing unrestricted NAT access may defeat the intended private-access architecture.

## Production Best Practices

### Use Endpoints for Appropriate AWS Traffic

For private workloads, evaluate whether supported AWS service traffic should use:

- Gateway endpoints.
- Interface endpoints.
- NAT Gateway.
- Other AWS networking mechanisms.

Do not automatically send all AWS API traffic through NAT.

### Centralize Endpoint Design Carefully

Large organizations may centralize endpoints, but cross-VPC and cross-account architectures introduce additional routing, DNS, security, and cost considerations.

Keep endpoint ownership and traffic paths explicit.

### Deploy Critical Interface Endpoints Across Required AZs

For highly available workloads, place endpoint ENIs in appropriate Availability Zones.

### Restrict Endpoint Security Groups

Prefer workload-specific sources:

```text
TCP 443
Source: Application SG
```

over broad CIDRs when practical.

### Restrict Endpoint Policies

Where supported and appropriate, limit endpoint policies to required:

- Services.
- Actions.
- Resources.
- Principals.

### Manage Endpoints With Infrastructure as Code

Use:

- Terraform.
- CloudFormation.
- AWS CDK.

Avoid production-only manual endpoint changes.

### Monitor Endpoint Dependencies

Include endpoint connectivity in operational monitoring for workloads that depend on private AWS APIs.

### Validate During CI/CD

Infrastructure pipelines should validate:

- Endpoint existence.
- Endpoint type.
- Subnet placement.
- Route-table associations.
- Private DNS.
- Security Groups.
- Endpoint policies.

## Security Considerations

VPC endpoints can improve isolation because private workloads can access supported AWS services without requiring a public internet path.

However, private connectivity does not replace authorization.

A secure architecture should combine:

```text
Private subnet
    +
VPC endpoint
    +
Restrictive endpoint policy
    +
Security Group
    +
IAM least privilege
    +
Service resource policy
```

Avoid assuming:

```text
Private = trusted
```

An attacker who compromises a workload inside the VPC may still attempt to use available AWS endpoints.

Apply least privilege at every relevant layer.

## Cost Considerations

Gateway endpoints for supported services can reduce the need to route that traffic through NAT Gateway infrastructure.

Interface endpoints have their own pricing considerations, including endpoint-related hourly and data-processing charges.

Therefore endpoint architecture should be evaluated using actual traffic patterns.

For example:

```text
Many private workloads
        |
        v
Large S3 traffic volume
        |
        v
Gateway Endpoint
```

may be preferable to:

```text
Private workloads
        |
        v
NAT Gateway
        |
        v
S3
```

when the service and architecture support the gateway endpoint.

For interface endpoints, deploying an endpoint in every subnet may not always be necessary. Balance:

- Availability.
- Latency.
- Cross-AZ traffic.
- Endpoint hourly charges.
- Operational simplicity.

## Performance Considerations

Private endpoints can improve network architecture by keeping service traffic on AWS private connectivity paths.

However, endpoint architecture does not automatically guarantee lower latency.

Measure:

- DNS resolution latency.
- TCP connection establishment.
- TLS handshake.
- API latency.
- Cross-AZ traffic.
- NAT path versus endpoint path where applicable.

For high-throughput applications, connection reuse is important.

For Python applications using AWS SDKs such as `boto3`, avoid creating a new client for every request when the application's architecture allows safe client reuse.

For example:

```python
import boto3

s3_client = boto3.client("s3")


def upload_object(bucket: str, key: str, body: bytes) -> None:
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
    )
```

Connection pooling and SDK configuration can materially affect endpoint traffic efficiency.

## Backend Engineering Example

Consider a FastAPI service running on ECS in private subnets.

The service needs:

- Secrets Manager for configuration.
- S3 for document storage.
- ECR for container image retrieval.

A private architecture could be:

```mermaid
flowchart TB
    Internet[Internet] --> ALB[Public ALB]

    ALB --> API[FastAPI ECS Tasks]

    API --> Secrets[Secrets Manager Interface Endpoint]
    API --> S3[S3 Gateway Endpoint]

    ECRService[ECR] --> ECRAPI[ECR API Endpoint]
    ECRService --> ECRDKR[ECR DKR Endpoint]

    API --> Redis[(Redis)]
    API --> PostgreSQL[(PostgreSQL)]

    API --> ECRAPI
    API --> ECRDKR
```

A failure in Secrets Manager connectivity can prevent the application from starting.

A failure in S3 endpoint routing can prevent document uploads.

A failure in ECR endpoint configuration can prevent new tasks from starting.

These are operationally different failures even though all involve "AWS service connectivity."

## Interview Traps

### "VPC Endpoints Always Use Private IP Addresses"

Not all endpoint types behave identically.

Interface endpoints use ENIs with private IP addresses. Gateway endpoints integrate with VPC routing for supported services.

### "A VPC Endpoint Removes the Need for IAM"

Incorrect.

IAM remains an authorization layer.

### "An Endpoint Being Available Means the Application Can Use It"

Incorrect.

DNS, routing, Security Groups, NACLs, endpoint policies, IAM, and service policies can still block requests.

### "Gateway Endpoints Use Security Groups"

Gateway endpoints do not use endpoint ENIs and Security Groups in the same way interface endpoints do.

### "Interface Endpoints Require a Route Table Entry Like Gateway Endpoints"

The primary mechanism for interface endpoint connectivity is the endpoint ENI and DNS/private connectivity rather than a gateway-style prefix-list route.

### "Private DNS Is Just a Convenience"

For many interface endpoint architectures, private DNS is operationally critical because applications continue using normal AWS service hostnames.

### "AccessDenied Means the Endpoint Is Broken"

Not necessarily.

`AccessDenied` strongly suggests an authorization-layer problem that should be investigated across IAM, endpoint policies, and service resource policies.

### "NAT Gateway and VPC Endpoints Are the Same"

They provide different connectivity models.

NAT provides outbound internet connectivity for private resources. VPC endpoints provide private connectivity to supported AWS services.

## Key Takeaways

- **Identify the endpoint type first**: gateway endpoints and interface endpoints use fundamentally different networking mechanisms and require different troubleshooting approaches.
- **Interface endpoint failures commonly involve DNS, endpoint ENI Security Groups, NACLs, and private DNS configuration**, while gateway endpoint failures commonly involve route-table associations and endpoint routes.
- **Separate network connectivity from authorization**: endpoint policies, IAM policies, and AWS service resource policies can reject requests even when the network path is healthy.
- **For production workloads, treat VPC endpoints as infrastructure dependencies** and design their DNS, subnet/AZ placement, security, monitoring, and failure behavior deliberately.
- **Use the complete troubleshooting path—DNS, routing, SG/NACL, endpoint policy, IAM, service policy, and application behavior—rather than assuming the endpoint itself is the failure.**