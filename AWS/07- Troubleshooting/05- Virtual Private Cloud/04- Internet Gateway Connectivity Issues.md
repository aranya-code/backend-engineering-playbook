# 04- Internet Gateway Connectivity Issues

## Overview

An Internet Gateway (IGW) provides the VPC-side connectivity required for IPv4 and IPv6 communication between resources in a VPC and the public internet. It is a highly available, horizontally scaled VPC component managed by AWS; it is not a server, proxy, or NAT device that you operate.

Internet connectivity failures are frequently caused by an incomplete path rather than a single broken component. A working Internet Gateway requires the correct combination of:

- Internet Gateway attachment.
- Subnet route table.
- Appropriate public addressing.
- Security Group rules.
- Network ACL rules.
- Correct return routing.
- Correct DNS configuration when hostnames are involved.
- Correct IPv4 or IPv6 configuration.

A useful troubleshooting model is:

```text
Workload
   |
   v
Network Interface
   |
   v
Subnet
   |
   v
Route Table
   |
   v
0.0.0.0/0 or ::/0
   |
   v
Internet Gateway
   |
   v
Internet
```

If any required layer is missing or incorrectly configured, internet connectivity can fail.

## Internet Gateway Fundamentals

An Internet Gateway is a VPC component that provides a logical path between a VPC and the internet.

It is attached to the VPC:

```text
VPC
 |
 +--> Internet Gateway
```

A subnet becomes internet-facing only when its route table sends appropriate traffic toward the Internet Gateway and the resources have the required addressing and security configuration.

The IGW itself does not provide:

- Private-to-public address translation for private instances.
- Security Group rules.
- Network ACL rules.
- DNS resolution.
- Application-layer proxying.
- Automatic route-table configuration.

These responsibilities belong to other networking components.

## Public Subnet Internet Path

A typical public subnet contains a route such as:

```text
Destination     Target
------------------------------
10.0.0.0/16     local
0.0.0.0/0       igw-xxxxxxxx
```

The resulting path for an IPv4 workload is:

```mermaid
flowchart LR
    Client[Internet Client] --> IGW[Internet Gateway]
    IGW --> RT[Public Subnet Route Table]
    RT --> ENI[Instance ENI]
    ENI --> App[Application]
```

For outbound traffic, the logical flow is reversed:

```mermaid
flowchart LR
    App[EC2 / Application] --> ENI[Network Interface]
    ENI --> RT[Route Table]
    RT --> IGW[Internet Gateway]
    IGW --> Internet[Internet]
```

The workload still requires an appropriate public IPv4 address or IPv6 address.

## Internet Gateway vs NAT Gateway

These components solve different problems.

| Component | Primary Purpose | Typical Workload |
|---|---|---|
| Internet Gateway | Internet connectivity for VPC resources with appropriate public addressing | Public-facing resources |
| NAT Gateway | Outbound internet access for private resources | Private application servers |
| VPC Endpoint | Private access to supported AWS services | Private workloads |
| Transit Gateway | Connectivity between VPCs and networks | Multi-VPC/hybrid architectures |

A common architecture is:

```text
                 Internet
                    |
                    v
             Internet Gateway
                /         \
               /           \
       Public Subnet     Public Subnet
            |                 |
          ALB/Nginx        NAT Gateway
                              |
                              v
                       Private Subnet
                              |
                         Django/FastAPI
```

A private application should generally not receive a public IP simply because it needs outbound internet access.

## Verify Internet Gateway Attachment

The first check is whether an Internet Gateway is attached to the VPC.

```bash
aws ec2 describe-internet-gateways \
  --filters Name=attachment.vpc-id,Values=vpc-0123456789abcdef0
```

A healthy attachment should show the expected VPC:

```json
{
  "Attachments": [
    {
      "State": "available",
      "VpcId": "vpc-0123456789abcdef0"
    }
  ]
}
```

If no attachment exists, routes targeting an Internet Gateway cannot provide the intended connectivity.

## Verify the Route Table

Inspect route tables:

```bash
aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values=vpc-0123456789abcdef0
```

For a public IPv4 subnet, verify a route similar to:

```text
Destination: 0.0.0.0/0
Target:      igw-0123456789abcdef0
State:       active
```

For IPv6:

```text
Destination: ::/0
Target:      igw-0123456789abcdef0
State:       active
```

A route to an IGW is necessary but not sufficient.

## Verify the Subnet Association

One of the most common mistakes is inspecting the wrong route table.

Find the subnet:

```bash
aws ec2 describe-subnets \
  --subnet-ids subnet-0123456789abcdef0
```

Then inspect route table associations:

```bash
aws ec2 describe-route-tables \
  --filters Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

If there is no explicit association, the subnet uses the VPC's main route table.

Therefore, during troubleshooting verify:

```text
Instance
   |
   v
ENI
   |
   v
Subnet
   |
   v
Actual Route Table
```

Do not assume the route table name implies which subnets use it.

## Verify Public Addressing

An Internet Gateway does not automatically give an instance a public IP.

For an IPv4 instance, verify the network interface:

```bash
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[].Instances[].{
    PrivateIp:PrivateIpAddress,
    PublicIp:PublicIpAddress,
    Subnet:SubnetId,
    Vpc:VpcId
  }'
```

A public subnet can contain resources that do not have public addresses.

For example:

```text
Public Subnet
    |
    +--> Instance A: Public IP
    |
    +--> Instance B: Private IP only
```

Instance A can potentially communicate directly with the internet, subject to routing and security controls.

Instance B cannot simply use the IGW as a NAT service.

## Public IPv4 vs Elastic IP

For workloads requiring a stable public IPv4 address, an Elastic IP can be associated with an appropriate resource.

Do not assume that a dynamically assigned public IPv4 address is permanent.

For production systems, consider whether the workload actually needs a directly addressable public IP.

Common patterns include:

```text
Internet
   |
   v
Application Load Balancer
   |
   v
Private Application Instances
```

rather than:

```text
Internet
   |
   v
Public EC2 Instance
```

The load-balancer pattern reduces direct exposure of application instances.

## Security Group Checks

Security Groups control traffic at the resource's network interface.

For an internet-facing web server, inbound rules commonly allow:

```text
TCP 443 from approved internet sources
```

and potentially:

```text
TCP 80 from 0.0.0.0/0
```

when HTTP is intentionally supported.

Inspect Security Groups:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0
```

For a Django or FastAPI service, verify that:

- The application is listening on the expected port.
- The Security Group allows the expected destination port.
- The service binds to the expected interface.
- The operating system firewall allows the traffic.

A route cannot override a Security Group denial.

## Network ACL Checks

Network ACLs operate at the subnet boundary.

Because Network ACLs are stateless, both inbound and outbound traffic must be explicitly permitted.

For example, a web request can involve:

```text
Internet
   |
   v
Inbound NACL rule
   |
   v
Instance
   |
   v
Outbound NACL rule
   |
   v
Internet
```

Inspect NACLs:

```bash
aws ec2 describe-network-acls \
  --filters Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

A restrictive NACL can produce connectivity failures even when:

- The IGW is attached.
- The route is correct.
- The Security Group is correct.

## DNS vs Internet Connectivity

DNS failures can look like internet connectivity failures.

For example:

```bash
curl https://api.example.com
```

may fail because:

```text
DNS resolution
```

is broken rather than because:

```text
Internet Gateway routing
```

is broken.

Separate the investigation:

```bash
getent hosts api.example.com
```

Then test the resolved address:

```bash
curl -v https://api.example.com
```

For direct connectivity testing:

```bash
curl -v https://1.1.1.1
```

Be careful when interpreting HTTPS tests against an IP because TLS certificate validation may fail even when network connectivity is working.

The important diagnostic distinction is:

```text
DNS failure
!=
TCP failure
!=
TLS failure
!=
HTTP failure
```

## Application Binding Problems

A correctly routed public instance can still be unreachable if the application is not listening correctly.

For example, a FastAPI service bound only to loopback:

```python
uvicorn.run(app, host="127.0.0.1", port=8000)
```

is reachable only from the local host.

For a service intended to receive traffic through the instance network interface:

```python
uvicorn.run(app, host="0.0.0.0", port=8000)
```

The same principle applies to Django deployments behind Gunicorn, Nginx, or another reverse proxy.

Verify listeners:

```bash
ss -lntp
```

A typical production path might be:

```text
Internet
   |
   v
Internet Gateway
   |
   v
Load Balancer
   |
   v
Nginx
   |
   v
Gunicorn/Uvicorn
   |
   v
Django/FastAPI
```

## Route Table Connectivity Issues

A public subnet usually needs:

```text
0.0.0.0/0 -> Internet Gateway
```

If the route is instead:

```text
0.0.0.0/0 -> NAT Gateway
```

the subnet is not using the normal public-subnet pattern.

If the route is:

```text
0.0.0.0/0 -> Transit Gateway
```

traffic is intentionally being sent through another network path.

During incidents, do not only ask:

> Is there a default route?

Ask:

> Which route matches the destination, and where does it send the traffic?

## Longest-Prefix Matching

Suppose the route table contains:

```text
10.0.0.0/16  -> local
10.0.20.0/24 -> tgw-xxxxxxxx
0.0.0.0/0    -> igw-xxxxxxxx
```

Traffic to:

```text
10.0.20.50
```

uses:

```text
10.0.20.0/24
```

rather than the default route.

This can produce surprising behavior when a specific route was introduced for testing, migration, inspection, or hybrid connectivity.

Always inspect more-specific routes before blaming the default route.

## IPv6 Internet Connectivity

IPv6 requires explicit IPv6 routing.

A typical IPv6 public subnet needs:

```text
::/0 -> Internet Gateway
```

An IPv4 default route:

```text
0.0.0.0/0 -> Internet Gateway
```

does not provide IPv6 routing.

When debugging dual-stack applications, determine:

```text
Does DNS return A records?
Does DNS return AAAA records?
Which address family does the client select?
Does the subnet have IPv6 addressing?
Does the route table contain ::/0?
Do Security Groups permit IPv6?
Do NACLs permit IPv6?
```

A common production failure occurs when IPv6 is introduced but only IPv4 security and routing assumptions are reviewed.

## Internet Gateway Connectivity Test

From an EC2 instance, inspect routing:

```bash
ip route
```

Typical IPv4 output might contain:

```text
default via 10.0.1.1 dev eth0
10.0.0.0/16 dev eth0 proto kernel scope link
```

Test DNS:

```bash
getent hosts example.com
```

Test TCP/HTTPS:

```bash
curl -v --connect-timeout 5 https://example.com
```

Test a specific port:

```bash
nc -vz example.com 443
```

Use `ping` carefully.

Many internet destinations intentionally block ICMP, so:

```bash
ping example.com
```

failing does not prove that HTTPS connectivity is broken.

## Reachability Analyzer

VPC Reachability Analyzer is useful for diagnosing AWS-side connectivity.

Use it when the path contains multiple components such as:

```text
EC2
 |
 v
Subnet
 |
 v
Route Table
 |
 v
Internet Gateway
```

or:

```text
Load Balancer
 |
 v
Route Table
 |
 v
Network Firewall
 |
 v
Transit Gateway
```

It can help identify where the expected network path is blocked.

For complex production environments, it is preferable to manually reasoning through every route and security rule when the service supports the required source and destination analysis.

## VPC Flow Logs

Flow Logs can provide evidence about traffic observed at the relevant network interface.

For example:

```text
Source        Destination     Port   Action
10.0.1.25     203.0.113.10    443    ACCEPT
```

A `REJECT` record can point toward security controls such as:

- Security Groups.
- Network ACLs.

Flow Logs should be interpreted alongside routing information.

A missing or unexpected record does not automatically prove that the Internet Gateway is broken.

## Common Internet Gateway Failure Patterns

| Symptom | Likely Cause | First Check |
|---|---|---|
| Instance has no internet access | Missing default route | Route table |
| Public subnet cannot reach internet | Wrong route-table association | Subnet association |
| Instance has no public IPv4 | No public address | ENI/instance |
| HTTPS inbound fails | Security Group/NACL/application | Security controls and listener |
| IPv4 works, IPv6 fails | Missing IPv6 route/security | `::/0` and IPv6 rules |
| DNS name fails but IP works | DNS issue | Resolver configuration |
| Route exists but traffic fails | SG/NACL/application | Security and listener |
| Instance cannot receive inbound traffic | No public address or incorrect path | Addressing and routing |
| Outbound private workload fails | NAT or endpoint path missing | Private subnet route |
| Some destinations work, others fail | More-specific route | Route matching |
| Ping fails but HTTPS works | ICMP filtering | Test actual application port |

## NAT Gateway vs Internet Gateway Troubleshooting

For private applications, troubleshoot the NAT path instead of expecting the IGW to provide translation.

Expected private-subnet architecture:

```mermaid
flowchart LR
    App[Private Django/FastAPI] --> RT[Private Route Table]
    RT --> NAT[NAT Gateway]
    NAT --> PublicRT[Public Route Table]
    PublicRT --> IGW[Internet Gateway]
    IGW --> Internet[Internet]
```

Expected public-resource architecture:

```mermaid
flowchart LR
    App[Publicly Addressed Resource] --> RT[Public Route Table]
    RT --> IGW[Internet Gateway]
    IGW --> Internet[Internet]
```

If a private instance has:

```text
0.0.0.0/0 -> Internet Gateway
```

that does not turn the private IP into a publicly routable address.

Use a NAT Gateway or an appropriate VPC endpoint when private resources require outbound access.

## High Availability Considerations

The Internet Gateway itself is managed by AWS and is not deployed as a single EC2-style instance.

However, your surrounding architecture can still create single points of failure.

For example:

```text
Internet
   |
   v
IGW
   |
   v
Single EC2
```

has a very different availability profile from:

```text
Internet
   |
   v
IGW
   |
   v
ALB
 / \
AZ-A AZ-B
 |     |
App   App
```

For production workloads:

- Use multiple Availability Zones.
- Prefer load balancers for internet-facing application tiers.
- Keep application instances private when direct public exposure is unnecessary.
- Design NAT Gateway placement according to availability and cost requirements.
- Avoid routing critical traffic through a single self-managed appliance.

## Security Considerations

An Internet Gateway creates a path to and from the public internet, but it does not make every VPC resource publicly accessible.

Public exposure should be intentional.

A preferred architecture for a typical backend service is:

```text
Internet
   |
   v
Internet Gateway
   |
   v
Application Load Balancer
   |
   v
Private Subnets
   |
   +--> Django/FastAPI
   |
   +--> Redis
   |
   +--> PostgreSQL
```

Avoid placing databases or internal Redis instances directly on public internet-facing paths.

Review every public route for:

- Intended source networks.
- Intended destination networks.
- Public IP requirements.
- Security Group exposure.
- NACL behavior.
- Application authentication.
- TLS termination.
- Logging and monitoring.

## Operational Best Practices

### Separate Public and Private Subnets

Use explicit subnet roles.

```text
Public:
  ALB
  NAT Gateway

Private:
  Django
  FastAPI
  Celery
  Redis
  PostgreSQL
```

Do not use a single route table for every subnet merely because it is convenient.

### Make Route Associations Explicit

Manage route tables and associations through Infrastructure as Code.

This prevents accidental dependence on the VPC main route table.

### Test Both Directions

For internet-facing services, validate:

```text
Internet -> Application
Application -> Internet
```

These are separate connectivity paths from an operational perspective.

### Test the Actual Protocol

For an HTTPS service:

```bash
curl -v https://service.example.com
```

For PostgreSQL:

```bash
nc -vz database.example.internal 5432
```

Do not rely solely on ICMP tests.

### Keep Public Exposure Minimal

Prefer:

```text
Internet -> ALB -> Private Application
```

over exposing every application instance directly.

## Common Mistakes

### Assuming an IGW Automatically Provides Internet Access

It does not.

The route table, addressing, and security configuration must also be correct.

### Giving Private Instances Public IPs to Fix Outbound Connectivity

This can bypass the intended private-subnet architecture.

Use NAT Gateway or appropriate VPC endpoints for private workloads.

### Checking the Wrong Route Table

A correctly configured route table is irrelevant if the affected subnet uses another route table.

### Forgetting IPv6

IPv6 has separate addressing, routes, and security rules.

### Treating Ping as the Primary Connectivity Test

ICMP can be blocked while TCP/HTTPS works normally.

### Ignoring Application-Level Failures

A network path can be completely healthy while:

- Nginx is not listening.
- Gunicorn is down.
- Uvicorn is bound incorrectly.
- The application process crashed.
- TLS configuration is invalid.

### Opening Security Groups to `0.0.0.0/0` Without Understanding the Path

Broad inbound access can hide the actual design problem and create unnecessary exposure.

## Interview Traps

### "An Internet Gateway Performs NAT"

Incorrect.

NAT is provided by NAT Gateway or another NAT-capable component.

### "A Public Subnet Is Public Because It Has an Internet Gateway"

Incomplete.

A subnet is commonly considered public when its route table has a route to an Internet Gateway. Resources still need appropriate addressing and security configuration to communicate directly with the internet.

### "Every Instance in a Public Subnet Is Reachable From the Internet"

Incorrect.

Public reachability also depends on public addressing and security controls.

### "A NAT Gateway Is Required for Public EC2 Instances"

Incorrect.

Publicly addressed resources can use the Internet Gateway directly.

### "An Internet Gateway Is a Single Server"

Incorrect.

It is an AWS-managed VPC networking component rather than a server that you provision and scale.

## Practical Diagnostic Checklist

```text
[ ] Identify source resource
[ ] Identify source ENI
[ ] Identify source subnet
[ ] Identify destination
[ ] Identify IPv4 vs IPv6
[ ] Verify Internet Gateway exists
[ ] Verify IGW is attached to the correct VPC
[ ] Verify actual subnet route-table association
[ ] Check 0.0.0.0/0 for IPv4
[ ] Check ::/0 for IPv6
[ ] Check more-specific routes
[ ] Verify route target and route state
[ ] Verify public IPv4 or IPv6 addressing
[ ] Check Security Group rules
[ ] Check Network ACL rules
[ ] Check host firewall
[ ] Verify application listener
[ ] Verify DNS resolution
[ ] Test TCP connectivity
[ ] Test the actual application protocol
[ ] Inspect VPC Flow Logs
[ ] Use Reachability Analyzer where appropriate
[ ] Check return traffic
[ ] Check application logs
[ ] Record root cause and remediation
```

## Key Takeaways

- **An Internet Gateway is only one part of the internet connectivity path**; routing, addressing, Security Groups, NACLs, and application configuration must also be correct.
- **Always verify the actual subnet-to-route-table association** and the matching `0.0.0.0/0` or `::/0` route.
- **NAT Gateway and Internet Gateway solve different problems**: NAT provides outbound connectivity for private resources, while an IGW provides VPC internet connectivity for appropriately addressed resources.
- **Troubleshoot by network layer**: addressing → routing → security controls → transport → TLS/DNS → application listener.
- **Prefer controlled public exposure through load balancers and keep backend data services private** unless direct internet exposure is explicitly required.