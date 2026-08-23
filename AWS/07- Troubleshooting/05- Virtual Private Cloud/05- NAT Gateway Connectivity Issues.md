# 05- NAT Gateway Connectivity Issues

## Overview

A NAT Gateway provides outbound internet connectivity for resources in private subnets without requiring those resources to have publicly routable IP addresses. It is a managed AWS networking service that performs network address translation for outbound traffic and relies on an Internet Gateway on the public side of the VPC.

NAT connectivity problems are usually caused by an incomplete routing path, incorrect subnet placement, missing public connectivity, restrictive security controls, DNS failures, or an incorrectly configured NAT Gateway.

The expected IPv4 path is:

```text
Private Workload
      |
      v
Private Subnet
      |
      v
Private Route Table
      |
      | 0.0.0.0/0
      v
NAT Gateway
      |
      v
Public Subnet Route Table
      |
      | 0.0.0.0/0
      v
Internet Gateway
      |
      v
Internet
```

The most important troubleshooting principle is:

> A NAT Gateway does not create internet connectivity by itself. The complete private-subnet → NAT Gateway → public-subnet → Internet Gateway path must be valid.

## NAT Gateway Connectivity Model

A NAT Gateway is normally deployed in a public subnet.

A private subnet routes internet-bound traffic to the NAT Gateway:

```text
Private Route Table
------------------------------
10.0.0.0/16     local
0.0.0.0/0       nat-xxxxxxxx
```

The NAT Gateway's public subnet must then route internet-bound traffic to an Internet Gateway:

```text
Public Route Table
------------------------------
10.0.0.0/16     local
0.0.0.0/0       igw-xxxxxxxx
```

The architecture therefore has two separate routing decisions:

```mermaid
flowchart LR
    App[Private EC2 / ECS / EKS] --> PrivateRT[Private Route Table]
    PrivateRT --> NAT[NAT Gateway]
    NAT --> PublicRT[Public Route Table]
    PublicRT --> IGW[Internet Gateway]
    IGW --> Internet[Internet]
```

If either route is missing, outbound connectivity fails.

## What the NAT Gateway Actually Does

The NAT Gateway translates private source addresses into a public source address for outbound IPv4 traffic.

For example:

```text
Private instance:
10.0.20.15:49152
        |
        v
NAT Gateway
        |
        v
Public source address
203.0.113.25:xxxxx
        |
        v
Internet
```

The destination server sees the NAT Gateway's public address rather than the private instance address.

The NAT Gateway maintains the state required to map return traffic back to the originating private workload.

This is why a private instance can initiate:

```text
Private instance -> Internet
```

while unsolicited internet traffic cannot normally initiate a connection directly to that private instance through the NAT Gateway.

## NAT Gateway Requirements

A working public NAT Gateway architecture requires all of the following:

| Requirement | Purpose |
|---|---|
| NAT Gateway exists | Provides address translation |
| NAT Gateway is in a public subnet | Gives it a route toward the Internet Gateway |
| NAT Gateway has a public connectivity configuration | Required for a public NAT Gateway |
| Public subnet route table has `0.0.0.0/0 -> IGW` | Provides internet path |
| Private subnet route table has `0.0.0.0/0 -> NAT Gateway` | Sends private outbound traffic to NAT |
| NAT Gateway is available | Required for forwarding |
| Security controls allow traffic | Prevents network-level rejection |
| DNS works when using hostnames | Required for hostname-based destinations |

A failure in any of these layers can appear as a generic application timeout.

## Identify the Affected Workload

Start by identifying exactly which resource cannot reach the destination.

Examples include:

- EC2.
- ECS task.
- EKS pod.
- Lambda function attached to a VPC.
- Application running on a private VM.
- Celery worker.
- Django/FastAPI backend.
- Build or deployment worker.

Determine:

```text
Resource
  |
  +--> VPC
  +--> Subnet
  +--> ENI
  +--> Private IP
  +--> Route Table
  +--> Security Group
  +--> Network ACL
```

For EC2:

```bash
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[].Instances[].{
    VpcId:VpcId,
    SubnetId:SubnetId,
    PrivateIp:PrivateIpAddress,
    SecurityGroups:SecurityGroups
  }'
```

The goal is to establish the exact network path before changing anything.

## Verify the NAT Gateway

List NAT Gateways:

```bash
aws ec2 describe-nat-gateways \
  --filter Name=vpc-id,Values=vpc-0123456789abcdef0
```

Check the NAT Gateway state.

A healthy NAT Gateway should report:

```text
State: available
```

Common states include:

| State | Meaning |
|---|---|
| `pending` | Creation is still in progress |
| `available` | NAT Gateway is operational |
| `deleting` | NAT Gateway is being removed |
| `deleted` | NAT Gateway no longer exists |
| `failed` | Creation failed |

If the route table points to a deleted or unavailable NAT Gateway, private-subnet connectivity will fail.

## Verify NAT Gateway Placement

A public NAT Gateway should be placed in a public subnet.

Inspect the NAT Gateway:

```bash
aws ec2 describe-nat-gateways \
  --nat-gateway-ids nat-0123456789abcdef0
```

Identify:

- Subnet ID.
- VPC ID.
- Connectivity type.
- State.
- Network interface.

Then inspect the subnet:

```bash
aws ec2 describe-subnets \
  --subnet-ids subnet-0123456789abcdef0
```

The critical question is not simply:

> Is the NAT Gateway in a subnet named `public`?

Instead ask:

> Does the NAT Gateway's subnet use a route table that provides a valid path to the Internet Gateway?

## Verify the Public Route Table

The NAT Gateway's subnet must have a route similar to:

```text
Destination     Target
------------------------------
10.0.0.0/16     local
0.0.0.0/0       igw-xxxxxxxx
```

Inspect route tables:

```bash
aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values=vpc-0123456789abcdef0
```

Then verify the actual route-table association for the NAT Gateway subnet.

A common failure is:

```text
NAT Gateway
    |
    v
Subnet
    |
    v
Private Route Table
    |
    v
0.0.0.0/0 -> NAT Gateway
```

This creates a routing loop or otherwise invalid architecture.

The NAT Gateway needs a path to the Internet Gateway, not another NAT Gateway.

## Verify the Private Route Table

The affected private subnet should normally contain:

```text
Destination     Target
------------------------------
10.0.0.0/16     local
0.0.0.0/0       nat-xxxxxxxx
```

Inspect the route table:

```bash
aws ec2 describe-route-tables \
  --filters Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

If the private subnet instead contains:

```text
0.0.0.0/0 -> igw-xxxxxxxx
```

the architecture is incorrect for a private IPv4 workload.

If it contains:

```text
0.0.0.0/0 -> nat-xxxxxxxx
```

but the NAT Gateway is unavailable, outbound internet traffic will fail.

## Route Table Association Is Critical

One of the most common NAT troubleshooting mistakes is verifying a correct route table without verifying that the affected subnet actually uses it.

Suppose:

```text
Private Route Table A
0.0.0.0/0 -> NAT Gateway
```

is correctly configured.

But the application subnet actually uses:

```text
Private Route Table B
0.0.0.0/0 -> NAT Gateway-old
```

The application will continue using the wrong route.

Always trace:

```text
Workload
  |
  v
ENI
  |
  v
Subnet
  |
  v
Route-table association
  |
  v
Effective routes
```

## Verify NAT Gateway Connectivity Type

NAT Gateways can be configured for different connectivity models.

For the conventional public NAT Gateway pattern, verify that the NAT Gateway has public connectivity through its subnet and Internet Gateway.

Inspect the NAT Gateway:

```bash
aws ec2 describe-nat-gateways \
  --nat-gateway-ids nat-0123456789abcdef0 \
  --query 'NatGateways[].{
    State:State,
    ConnectivityType:ConnectivityType,
    SubnetId:SubnetId,
    VpcId:VpcId
  }'
```

For normal private-subnet internet egress, the architecture is typically:

```text
Private Subnet
      |
      v
Public NAT Gateway
      |
      v
Internet Gateway
      |
      v
Internet
```

Do not assume that every NAT Gateway configuration provides direct internet access.

## Security Group Considerations

NAT Gateway behavior is different from an EC2-based NAT instance.

For a standard NAT Gateway, the primary routing and subnet controls are more important than attempting to configure a Security Group directly on the NAT Gateway.

The private workload's Security Group must permit the required outbound traffic.

For example:

```text
Outbound:
TCP 443 -> 0.0.0.0/0
```

If outbound access is restricted intentionally, ensure the destination port and protocol are permitted.

Inspect the Security Group:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0
```

For common backend workloads, outbound HTTPS is frequently required for:

- AWS APIs.
- Package repositories.
- External REST APIs.
- OAuth providers.
- Monitoring services.
- Webhooks.
- Container registries.

A Security Group denial can look identical to a NAT failure from the application perspective.

## Network ACL Considerations

Network ACLs are stateless.

Therefore, if a private subnet uses restrictive NACLs, both outbound requests and return traffic must be permitted.

Example:

```text
Private workload
      |
      | outbound ephemeral connection
      v
NACL
      |
      v
NAT Gateway
      |
      v
Internet

Internet response
      |
      v
NAT Gateway
      |
      v
NACL
      |
      v
Private workload
```

Inspect the subnet's NACL:

```bash
aws ec2 describe-network-acls \
  --filters Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

A restrictive NACL can break:

- HTTPS.
- DNS.
- Package downloads.
- API calls.
- Container image pulls.

Do not assume a default NACL is present in every environment; production infrastructure often uses custom NACLs.

## DNS Failures

NAT connectivity is often blamed when the actual problem is DNS.

Test DNS resolution from the workload:

```bash
getent hosts example.com
```

or:

```bash
nslookup example.com
```

Then test the actual connection:

```bash
curl -v --connect-timeout 5 https://example.com
```

Separate the failure types:

```text
DNS resolution
    |
    +--> failure

TCP connection
    |
    +--> failure

TLS handshake
    |
    +--> failure

HTTP request
    |
    +--> failure
```

For example:

```text
example.com cannot resolve
```

does not prove that the NAT Gateway is broken.

## DNS Traffic and NAT

DNS resolution for standard VPC workloads generally uses the VPC-provided DNS infrastructure rather than sending DNS queries through the NAT Gateway.

Therefore, a DNS failure should trigger checks around:

- VPC DNS support.
- VPC DNS hostnames.
- Resolver configuration.
- Custom DNS servers.
- DHCP option sets.
- Security controls.
- Application resolver behavior.

Do not automatically increase NAT capacity or replace the NAT Gateway when the actual problem is DNS configuration.

## Test Connectivity From the Workload

The strongest diagnostic test is from the affected environment itself.

For EC2:

```bash
curl -v --connect-timeout 5 https://example.com
```

Test TCP:

```bash
nc -vz example.com 443
```

Test DNS:

```bash
getent hosts example.com
```

Inspect local routing:

```bash
ip route
```

For a private application server, you should normally see a default route through the subnet's VPC router.

Do not expect the operating system's route table to explicitly show:

```text
default -> NAT Gateway
```

The NAT Gateway is an AWS-side routing target referenced by the VPC route table.

## Test AWS Service Connectivity

If an application cannot reach an AWS API, first determine whether it actually needs NAT.

For example:

```text
Private Application
       |
       +--> S3
       |
       +--> DynamoDB
       |
       +--> ECR
       |
       +--> Secrets Manager
```

Depending on the service and architecture, VPC endpoints may provide private connectivity.

This can reduce NAT traffic and improve architecture by avoiding unnecessary internet egress.

For example:

```mermaid
flowchart LR
    App[Private Application] --> RT[Private Route Table]
    RT --> VPCE[VPC Endpoint]
    VPCE --> AWS[AWS Service]
```

Instead of:

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

For supported services, endpoint-based connectivity can be preferable.

## NAT Gateway and AWS API Failures

Backend applications frequently depend on external services.

A Django application might perform:

```python
import requests

response = requests.get(
    "https://api.example.com/health",
    timeout=5,
)
response.raise_for_status()
```

If this request times out only from a private subnet, investigate:

```text
Django
  |
  v
EC2/Container ENI
  |
  v
Private subnet
  |
  v
Private route table
  |
  v
NAT Gateway
  |
  v
Public route table
  |
  v
Internet Gateway
  |
  v
External API
```

The application code may be correct while the network path is broken.

## NAT Gateway and Containerized Workloads

For ECS tasks running in private subnets, verify that:

- The task ENI belongs to the expected subnet.
- The subnet uses the expected private route table.
- The private route table points to the correct NAT Gateway.
- The NAT Gateway is available.
- The NAT Gateway subnet has an Internet Gateway route.
- The task Security Group allows required egress.
- NACLs permit the traffic.

For EKS, determine whether the affected pod's traffic is expected to leave through:

- Node networking.
- NAT Gateway.
- VPC CNI-managed networking.
- A VPC endpoint.
- Another egress architecture.

Do not troubleshoot the NAT path solely from the Kubernetes service or pod definition.

## NAT Gateway and Lambda

A Lambda function attached to a VPC does not automatically gain internet access.

If a VPC-attached Lambda function needs public internet access, its subnet routing must provide an appropriate egress path.

Typical architecture:

```text
Lambda ENI
    |
    v
Private Subnet
    |
    v
Private Route Table
    |
    v
NAT Gateway
    |
    v
Internet Gateway
    |
    v
Internet
```

Common failure:

```text
Lambda
   |
   v
Private Subnet
   |
   X
No NAT route
```

The function may execute successfully while outbound API calls time out.

## VPC Flow Logs

VPC Flow Logs can help determine whether traffic is being accepted or rejected at the network interface level.

A simplified record might look like:

```text
srcaddr=10.0.20.15
dstaddr=203.0.113.10
srcport=49152
dstport=443
protocol=6
action=ACCEPT
```

A `REJECT` record can indicate a security-control problem.

Flow Logs should be interpreted with:

- Route tables.
- Security Groups.
- NACLs.
- NAT Gateway state.
- Application logs.

An `ACCEPT` record does not guarantee that the destination application responded successfully.

## NAT Gateway Metrics

Amazon CloudWatch provides NAT Gateway metrics that can help identify operational issues and unusual traffic patterns.

Useful metrics include:

- `BytesInFromSource`
- `BytesOutToDestination`
- `BytesInFromDestination`
- `BytesOutToSource`
- `PacketsInFromSource`
- `PacketsOutToDestination`
- `PacketsInFromDestination`
- `PacketsOutToSource`

Use metrics to distinguish:

```text
No traffic
```

from:

```text
Traffic reaches NAT
```

and:

```text
Traffic reaches NAT but application still fails
```

A sudden increase in bytes can also indicate:

- Large downloads.
- Container image traffic.
- Package installation.
- Backup traffic.
- Unexpected data transfer.
- Misconfigured retry loops.

## NAT Gateway Availability and AZ Design

A NAT Gateway is associated with a subnet in a specific Availability Zone.

For production workloads, consider the failure domain.

A common resilient architecture is:

```text
                 Internet
                    |
                    v
             Internet Gateway
              /             \
             /               \
         NAT-A              NAT-B
           |                  |
       Private-A          Private-B
           |                  |
        App-A              App-B
```

Each private subnet can route through the NAT Gateway in the same Availability Zone.

This provides better AZ isolation than forcing all private subnets through one NAT Gateway.

However, this architecture has a cost tradeoff because each NAT Gateway incurs hourly and data-processing charges.

The right design depends on:

- Availability requirements.
- Cross-AZ data-transfer implications.
- Traffic volume.
- Number of Availability Zones.
- Recovery objectives.
- Cost constraints.

## Cross-AZ NAT Routing

Consider:

```text
Private Subnet AZ-A
        |
        v
NAT Gateway AZ-B
        |
        v
Internet Gateway
```

This can work, but it introduces cross-AZ traffic.

A more failure-isolated design is:

```text
Private AZ-A -> NAT AZ-A
Private AZ-B -> NAT AZ-B
```

For high-volume production systems, evaluate both availability and cost rather than blindly centralizing NAT.

## NAT Gateway Connectivity Diagnostic Flow

```mermaid
flowchart TD
    Start[Private workload cannot reach internet] --> Resource[Identify workload and subnet]
    Resource --> PrivateRT[Inspect private route table]
    PrivateRT --> NATRoute{0.0.0.0/0 -> NAT Gateway?}

    NATRoute -->|No| FixPrivateRoute[Fix private route]
    NATRoute -->|Yes| NATState[Check NAT Gateway state]

    NATState --> Available{NAT Gateway available?}
    Available -->|No| FixNAT[Investigate NAT Gateway]
    Available -->|Yes| PublicSubnet[Inspect NAT subnet]

    PublicSubnet --> PublicRT{Public route -> IGW?}
    PublicRT -->|No| FixPublicRoute[Fix public route]
    PublicRT -->|Yes| Security[Check SG and NACL]

    Security --> DNS{DNS works?}
    DNS -->|No| FixDNS[Investigate DNS]
    DNS -->|Yes| Test[TCP / HTTPS test]

    Test --> Logs[Inspect Flow Logs and application logs]
```

## Common Failure Patterns

| Symptom | Likely Cause | First Check |
|---|---|---|
| Private instance has no internet | Missing NAT route | Private route table |
| NAT route exists but traffic times out | NAT unavailable or public path broken | NAT state and public route |
| NAT is available but no outbound traffic | Incorrect private route association | Subnet association |
| NAT subnet has no internet | Missing IGW route | Public route table |
| HTTPS fails but DNS works | SG/NACL/NAT/path issue | TCP connectivity |
| Hostname fails but direct IP works | DNS problem | Resolver configuration |
| AWS API calls fail | Missing NAT or endpoint | Service path |
| One AZ works, another fails | AZ-specific NAT/routing issue | Per-AZ route tables |
| Large transfers are slow/expensive | NAT data processing | NAT metrics and traffic analysis |
| Container image pulls fail | Private egress or endpoint problem | ECS/EKS subnet route |
| Lambda external API calls timeout | Missing VPC egress path | Lambda subnet route |
| Some workloads work, others fail | Different subnet/route table | ENI and subnet mapping |

## Troubleshooting Commands

### Inspect NAT Gateways

```bash
aws ec2 describe-nat-gateways \
  --filter Name=vpc-id,Values=vpc-0123456789abcdef0 \
  --query 'NatGateways[].{
    NatGatewayId:NatGatewayId,
    State:State,
    SubnetId:SubnetId,
    VpcId:VpcId,
    ConnectivityType:ConnectivityType
  }'
```

### Inspect Private Routes

```bash
aws ec2 describe-route-tables \
  --filters Name=association.subnet-id,Values=subnet-0123456789abcdef0 \
  --query 'RouteTables[].Routes[]'
```

### Inspect Public Routes

```bash
aws ec2 describe-route-tables \
  --filters Name=association.subnet-id,Values=subnet-0123456789abcdef0 \
  --query 'RouteTables[].Routes[]'
```

Use the NAT Gateway subnet ID for this check.

### Test DNS

```bash
getent hosts example.com
```

### Test HTTPS

```bash
curl -v --connect-timeout 5 https://example.com
```

### Test TCP

```bash
nc -vz example.com 443
```

### Inspect Host Routing

```bash
ip route
```

### Inspect Listening Services

```bash
ss -lntp
```

## Practical Troubleshooting Procedure

Use the following order to avoid random configuration changes.

### Identify the Source

Record:

```text
Resource
VPC
Subnet
ENI
Private IP
Security Groups
```

### Identify the Destination

Determine:

```text
Hostname or IP
Protocol
Port
IPv4 or IPv6
AWS service or public internet
```

### Validate the Private Route

Confirm:

```text
0.0.0.0/0 -> expected NAT Gateway
```

and verify that the affected subnet actually uses this route table.

### Validate the NAT Gateway

Confirm:

```text
State = available
```

and verify its subnet and VPC.

### Validate the Public Route

Confirm:

```text
0.0.0.0/0 -> Internet Gateway
```

for the NAT Gateway's subnet.

### Validate Security Controls

Check:

- Security Group egress.
- Network ACL inbound rules.
- Network ACL outbound rules.

### Validate DNS

Test:

```bash
getent hosts example.com
```

### Validate TCP

Test:

```bash
nc -vz example.com 443
```

### Validate the Application Protocol

Test:

```bash
curl -v https://example.com
```

### Inspect Evidence

Use:

- VPC Flow Logs.
- CloudWatch NAT Gateway metrics.
- Application logs.
- System logs.
- Reachability Analyzer.

Avoid changing multiple networking components simultaneously because doing so makes root-cause analysis difficult.

## Security Considerations

NAT Gateway is primarily an outbound connectivity mechanism, not a security boundary by itself.

Private workloads can still initiate connections to arbitrary internet destinations if their routing and Security Group rules permit it.

For sensitive workloads, consider:

- Restricting outbound Security Group rules.
- Using VPC endpoints for AWS services.
- Using AWS Network Firewall or another controlled egress architecture where required.
- Monitoring outbound destinations.
- Logging important network flows.
- Avoiding unrestricted egress when policy requires tighter controls.

A private subnet does not automatically mean:

```text
No internet access
```

It often means:

```text
No direct inbound internet addressing
+
Controlled outbound access
```

## Cost Considerations

NAT Gateway usage can become a significant infrastructure cost when high-volume traffic traverses it.

Potential sources include:

- Container image downloads.
- OS package updates.
- Python package installation.
- Large external API payloads.
- Object storage transfers.
- Logging.
- Data synchronization.
- Backup operations.

For AWS services that support VPC endpoints, consider whether traffic can remain within AWS networking instead of passing through NAT.

For example:

```text
Private Application
       |
       v
VPC Endpoint
       |
       v
AWS Service
```

can avoid unnecessary NAT processing for supported services.

Do not optimize NAT cost by removing redundancy required by the application's availability requirements.

## Production Best Practices

### Use One NAT Gateway per AZ When Appropriate

For high-availability architectures, routing each private subnet through a NAT Gateway in the same AZ can reduce cross-AZ dependencies.

### Use VPC Endpoints for Supported AWS Services

Evaluate endpoints for frequently accessed services such as:

- Amazon S3.
- Amazon DynamoDB.
- Amazon ECR.
- AWS Secrets Manager.
- AWS Systems Manager.

The exact endpoint type and service support should be verified for the target AWS Region and service.

### Separate Public and Private Route Tables

Maintain clear routing intent:

```text
Public:
0.0.0.0/0 -> IGW

Private:
0.0.0.0/0 -> NAT
```

### Manage Networking With Infrastructure as Code

Use Terraform, CloudFormation, AWS CDK, or another controlled IaC workflow.

This makes:

- Route associations reproducible.
- NAT topology reviewable.
- Changes auditable.
- Environments consistent.

### Monitor NAT Traffic

Create CloudWatch dashboards and alerts for meaningful traffic anomalies.

Investigate unexpected increases rather than treating NAT traffic as an unavoidable baseline.

## Common Mistakes

### Putting the NAT Gateway in a Private Subnet

A NAT Gateway intended for public internet access needs a public subnet with a route toward the Internet Gateway.

### Pointing the Private Route Table Directly to the Internet Gateway

This does not provide NAT for private IPv4 addresses.

Use:

```text
Private -> NAT Gateway -> IGW
```

### Forgetting the Public Route

The NAT Gateway can be healthy while its subnet has no:

```text
0.0.0.0/0 -> IGW
```

route.

### Checking Only NAT Gateway State

`available` does not prove end-to-end connectivity.

You must verify the entire route.

### Ignoring Route Table Associations

A correct route in an unused route table does not help the workload.

### Using One NAT Gateway Without Considering Availability

A single NAT Gateway can become an architectural dependency for multiple Availability Zones.

### Assuming All AWS Traffic Should Use NAT

Supported VPC endpoints can provide a more direct and potentially more cost-efficient path for AWS services.

### Ignoring NACL Return Traffic

NACLs are stateless. Return traffic must be allowed explicitly when custom restrictive rules are used.

## Interview Traps

### "A NAT Gateway Makes a Subnet Public"

Incorrect.

A NAT Gateway provides outbound translation for private resources. The private subnet remains private.

### "A NAT Gateway Needs a Public IP on the Private Instance"

Incorrect.

The private workload keeps its private address. The NAT Gateway performs the translation.

### "A NAT Gateway Can Receive Internet-Initiated Connections"

Not as a mechanism for directly exposing private workloads to unsolicited inbound internet connections.

NAT Gateway is designed primarily for outbound connectivity.

### "The NAT Gateway Is Enough for Internet Access"

Incorrect.

The complete route is required:

```text
Private Route
    ->
NAT Gateway
    ->
Public Route
    ->
Internet Gateway
    ->
Internet
```

### "One NAT Gateway Is Always the Best Architecture"

Incorrect.

It may reduce fixed infrastructure cost but can introduce cross-AZ traffic and a larger failure dependency.

### "Private Subnets Never Need Internet Access"

Incorrect.

Private applications frequently require outbound access for:

- External APIs.
- Package repositories.
- AWS services.
- Container registries.
- Authentication providers.

The important architectural question is how that egress should be provided and controlled.

## Production Diagnostic Checklist

```text
[ ] Identify affected workload
[ ] Identify workload ENI
[ ] Identify subnet
[ ] Identify VPC
[ ] Identify destination hostname/IP
[ ] Identify destination port
[ ] Identify IPv4 vs IPv6
[ ] Verify private subnet route-table association
[ ] Verify 0.0.0.0/0 -> NAT Gateway
[ ] Verify NAT Gateway belongs to the expected VPC
[ ] Verify NAT Gateway state = available
[ ] Verify NAT Gateway subnet
[ ] Verify NAT subnet route-table association
[ ] Verify NAT subnet has 0.0.0.0/0 -> IGW
[ ] Verify Internet Gateway is attached
[ ] Check Security Group egress
[ ] Check Network ACL rules
[ ] Check DNS resolution
[ ] Test TCP connectivity
[ ] Test HTTPS/application protocol
[ ] Inspect VPC Flow Logs
[ ] Inspect NAT Gateway CloudWatch metrics
[ ] Use Reachability Analyzer where appropriate
[ ] Check application and system logs
[ ] Check for AZ-specific routing differences
[ ] Check whether a VPC endpoint is more appropriate
[ ] Document root cause and remediation
```

## Key Takeaways

- **NAT connectivity requires an end-to-end route**: private subnet → NAT Gateway → public subnet → Internet Gateway → internet.
- **Always verify both route-table associations and routes**; a correct route in the wrong table is operationally equivalent to no route.
- **A healthy NAT Gateway does not guarantee connectivity**; Security Groups, NACLs, DNS, the public route, and the Internet Gateway must also be valid.
- **For production systems, evaluate NAT placement per Availability Zone and use VPC endpoints where appropriate** to improve resilience and reduce unnecessary NAT traffic.
- **Troubleshoot from the affected workload outward**, validating addressing, routing, NAT state, security controls, DNS, transport, and application behavior in that order.