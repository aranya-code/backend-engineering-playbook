# 14- Reachability Analyzer and Diagnostic Tools

## Overview

AWS VPC troubleshooting becomes significantly more reliable when network configuration is evaluated systematically rather than by changing Security Groups, route tables, or NACLs until connectivity starts working.

VPC Reachability Analyzer provides a configuration-based path analysis capability that evaluates whether network connectivity is possible between supported AWS resources. It is particularly useful for answering questions such as:

- Can an EC2 instance reach another EC2 instance?
- Can an ENI reach a load balancer?
- Is a route missing?
- Is a Security Group blocking traffic?
- Is a Network ACL preventing connectivity?
- Is a Transit Gateway path correctly configured?
- Is a VPC peering route missing?
- Is a network path being blocked by a configuration rule?

Reachability Analyzer complements, rather than replaces, other diagnostic tools.

A production troubleshooting workflow typically combines:

```text
Reachability Analyzer
        +
VPC Flow Logs
        +
Route Table Inspection
        +
Security Group Inspection
        +
Network ACL Inspection
        +
DNS Diagnostics
        +
Application-Level Tests
```

The distinction is important:

- **Reachability Analyzer** evaluates the configured network path.
- **VPC Flow Logs** provide observed flow-level network telemetry.
- **Application tests** establish whether the real workload can communicate.
- **Packet capture** provides packet-level evidence when deeper analysis is required.

## Why Reachability Analysis Matters

Traditional VPC troubleshooting often involves manually following a network path:

```text
Source
  |
  v
Route Table
  |
  v
NACL
  |
  v
Transit Gateway / Peering / NAT
  |
  v
Destination Subnet
  |
  v
Destination Security Group
  |
  v
Destination
```

As architectures become larger, this becomes difficult to reason about.

A production environment may contain:

```text
Multiple VPCs
Multiple route tables
Transit Gateway
VPC Peering
NAT Gateways
Load Balancers
PrivateLink
VPN
Direct Connect
Multiple Security Groups
Multiple NACLs
Kubernetes workloads
```

Reachability Analyzer can reduce this complexity by evaluating the network configuration and identifying the path or the blocking component.

## Reachability Analyzer Mental Model

Think of Reachability Analyzer as a **configuration-aware network path validator**.

Instead of asking:

> "Is this server responding right now?"

ask:

> "Given the current AWS network configuration, is there a valid path between these two supported endpoints?"

This distinction matters.

A successful analysis does not guarantee that:

- The application process is running.
- The destination application is healthy.
- DNS is correct.
- TLS negotiation succeeds.
- Authentication succeeds.
- The remote service is operational.
- Network conditions have not changed since the analysis.

It primarily validates the configured network path.

## Network Path Model

A typical path can be represented as:

```mermaid
flowchart LR
    Source[Source ENI]
    Route[Route Table]
    NACL1[Source NACL]
    Intermediate[Transit Gateway / Peering / NAT]
    NACL2[Destination NACL]
    SG[Destination Security Group]
    Destination[Destination ENI]

    Source --> Route
    Route --> NACL1
    NACL1 --> Intermediate
    Intermediate --> NACL2
    NACL2 --> SG
    SG --> Destination
```

The exact path depends on the architecture.

For example:

```text
EC2 -> NAT Gateway -> Internet Gateway -> Internet
```

is fundamentally different from:

```text
EC2 -> Transit Gateway -> Destination VPC -> EC2
```

and:

```text
EC2 -> VPC Peering -> Destination VPC -> EC2
```

The troubleshooting process must therefore start with the intended architecture.

## What Reachability Analyzer Evaluates

Reachability Analyzer can reason about relevant network configuration, including components such as:

- Network interfaces.
- Route tables.
- Security Groups.
- Network ACLs.
- Transit Gateway paths.
- VPC peering.
- Internet Gateway paths.
- NAT Gateway paths.
- Other supported AWS networking components.

The exact resource types and analysis capabilities depend on the AWS networking feature and current service support.

Do not assume every AWS networking component can be analyzed in every source/destination combination.

## What Reachability Analyzer Does Not Prove

A successful path analysis does not mean:

```text
curl succeeded
```

It does not mean:

```text
HTTP 200
```

It does not mean:

```text
PostgreSQL authentication succeeded
```

It does not mean:

```text
Redis responded
```

It does not mean:

```text
Kafka metadata retrieval succeeded
```

It does not mean:

```text
TLS negotiation succeeded
```

A useful model is:

```text
Reachability Analyzer
        |
        v
Network configuration is reachable
        |
        v
Actual network traffic
        |
        v
Protocol
        |
        v
Application
```

Each layer requires separate validation.

## Reachability Analysis Versus Flow Logs

These tools answer different questions.

| Capability | Reachability Analyzer | VPC Flow Logs |
|---|---|---|
| Configuration path analysis | Yes | No |
| Observed network traffic | No | Yes |
| Identifies path blockers | Yes, when supported | Provides evidence |
| Source/destination metadata | Analysis inputs | Observed records |
| Historical traffic analysis | No | Yes |
| Application payload | No | No |
| Packet capture | No | No |
| Useful for pre-deployment validation | Yes | Limited |
| Useful for active incidents | Yes | Yes |
| Shows actual traffic occurred | No | Yes |

The strongest troubleshooting workflow combines both.

For example:

```text
Reachability Analyzer:
Path blocked by NACL

Flow Logs:
REJECT records observed

Conclusion:
Configuration and runtime telemetry agree
```

That is much stronger evidence than either source alone.

## When to Use Reachability Analyzer

Use Reachability Analyzer when:

- A known source cannot reach a known destination.
- A route appears correct but connectivity still fails.
- Multiple routing components are involved.
- Transit Gateway routing is complex.
- VPC peering is involved.
- Security Groups and NACLs are difficult to reason about.
- You want to validate connectivity before deployment.
- You need to identify the configuration component preventing a path.

It is particularly useful when the network path contains multiple hops.

## When Not to Rely on It Alone

Reachability Analyzer should not be the only diagnostic tool when investigating:

- DNS failures.
- Application failures.
- TLS errors.
- Authentication errors.
- Protocol-specific behavior.
- Packet retransmissions.
- MTU problems.
- Remote firewall behavior outside AWS.
- Intermittent runtime behavior.
- Application-level timeouts.

In those cases, combine it with:

```text
dig
curl
nc
ss
VPC Flow Logs
CloudWatch
Application logs
VPN logs
Packet capture
```

## Basic Reachability Workflow

A disciplined workflow looks like:

```mermaid
flowchart TD
    Problem[Connectivity Problem]
    Identify[Identify Source and Destination]
    Analysis[Run Reachability Analysis]
    Result{Reachable?}
    Config[Inspect Blocking Configuration]
    Flow[Check VPC Flow Logs]
    DNS[Check DNS]
    App[Check Application]
    Remote[Check Remote Network]

    Problem --> Identify
    Identify --> Analysis
    Analysis --> Result
    Result -->|No| Config
    Result -->|Yes| Flow
    Flow --> DNS
    DNS --> App
    App --> Remote
```

This prevents unnecessary infrastructure changes.

## Identifying Source and Destination

Before starting an analysis, identify:

```text
Source resource
Destination resource
Protocol
Destination port
```

For example:

```text
Source:
EC2 instance i-0123456789abcdef0

Destination:
EC2 instance i-0987654321abcdef0

Protocol:
TCP

Destination port:
5432
```

This corresponds to a realistic backend dependency:

```text
FastAPI
   |
   | TCP 5432
   v
PostgreSQL
```

## Example: EC2 to EC2

Suppose:

```text
Application VPC:
10.10.0.0/16

Database VPC:
10.20.0.0/16
```

The application runs at:

```text
10.10.10.20
```

The PostgreSQL server runs at:

```text
10.20.10.30:5432
```

The intended architecture is:

```text
Application EC2
10.10.10.20
      |
      v
Transit Gateway
      |
      v
Database VPC
      |
      v
PostgreSQL
10.20.10.30:5432
```

Reachability analysis can help determine whether the configured AWS network path exists.

## AWS CLI Workflow

AWS CLI commands can be used to inspect the resources involved in troubleshooting.

Find an instance's network interface:

```bash
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[].Instances[].NetworkInterfaces[].{
    NetworkInterfaceId:NetworkInterfaceId,
    PrivateIp:PrivateIpAddress,
    SubnetId:SubnetId,
    VpcId:VpcId
  }'
```

Inspect the destination:

```bash
aws ec2 describe-instances \
  --instance-ids i-0987654321abcdef0 \
  --query 'Reservations[].Instances[].NetworkInterfaces[].{
    NetworkInterfaceId:NetworkInterfaceId,
    PrivateIp:PrivateIpAddress,
    SubnetId:SubnetId,
    VpcId:VpcId
  }'
```

The resulting ENIs and subnet information can then be correlated with the network architecture.

## Creating a Reachability Analysis

Reachability Analyzer analyses can be created through the AWS console or AWS CLI.

The exact CLI parameters depend on the selected source, destination, protocol, and AWS resource types.

A representative command is:

```bash
aws ec2 create-network-insights-path \
  --source eni-0123456789abcdef0 \
  --destination eni-0987654321abcdef0 \
  --protocol tcp \
  --destination-port 5432
```

The returned path identifier can then be used to run the analysis.

```bash
aws ec2 start-network-insights-analysis \
  --network-insights-path-id nip-0123456789abcdef0
```

Retrieve the result:

```bash
aws ec2 describe-network-insights-analyses \
  --network-insights-analysis-ids nia-0123456789abcdef0
```

Resource identifiers are examples and must be replaced with real infrastructure identifiers.

## Analysis States

An analysis has a lifecycle.

Conceptually:

```text
Path Created
     |
     v
Analysis Started
     |
     v
Running
     |
     +------> Succeeded
     |
     +------> Failed
```

The exact status values returned by the API should be treated according to the current AWS API documentation.

The important operational distinction is:

```text
Analysis execution state
```

versus:

```text
Network reachability result
```

Do not confuse an API operation succeeding with the network path being reachable.

## Interpreting a Failed Analysis

A failed analysis should be treated as a diagnostic result, not merely:

```text
"Network is broken."
```

The useful question is:

> Which component prevented the expected path?

Potential causes include:

- No route.
- Security Group restriction.
- Network ACL restriction.
- Incorrect Transit Gateway routing.
- Invalid peering route.
- Missing return path.
- Unsupported or incorrect path configuration.

Use the reported explanation to locate the relevant configuration object, then inspect the infrastructure directly.

## Route Table Failures

A common failure is:

```text
No route to destination
```

Suppose:

```text
Source subnet:
10.10.10.0/24

Destination:
10.20.10.30
```

The source route table must contain a route covering:

```text
10.20.0.0/16
```

with the correct next hop.

Inspect the route table:

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0 \
  --query 'RouteTables[].Routes[]'
```

Validate:

```text
Destination CIDR
Target
State
Route-table association
```

A correct route in the wrong route table is still effectively a broken configuration.

## Transit Gateway Diagnostics

Transit Gateway adds another routing decision.

The path may be:

```text
Source ENI
   |
   v
Source Route Table
   |
   v
Transit Gateway
   |
   v
TGW Route Table
   |
   v
Destination Attachment
   |
   v
Destination VPC
```

A source VPC route can be correct while the Transit Gateway route table is wrong.

This is a common production failure mode.

Inspect Transit Gateway routes:

```bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0 \
  --filters Name=type,Values=static,propagated
```

Check:

- Destination prefix.
- Attachment.
- Route state.
- Blackhole routes.
- Association.
- Propagation.

## VPC Peering Diagnostics

For VPC peering:

```text
VPC A
10.10.0.0/16
    |
    v
Peering Connection
    |
    v
VPC B
10.20.0.0/16
```

Both sides need appropriate routes.

VPC A:

```text
10.20.0.0/16 -> pcx-xxxxxxxx
```

VPC B:

```text
10.10.0.0/16 -> pcx-xxxxxxxx
```

Inspect:

```bash
aws ec2 describe-route-tables \
  --filters Name=route.destination-cidr-block,Values=10.20.0.0/16
```

Also verify that the peering connection itself is active.

## Security Group Diagnostics

Security Groups are stateful.

For:

```text
Application -> PostgreSQL
```

the destination Security Group should allow the expected inbound connection.

Inspect the Security Group:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0
```

Verify:

```text
Protocol
Destination port
Source
```

Prefer:

```text
Source = application Security Group
```

over:

```text
Source = 0.0.0.0/0
```

when both resources are within AWS and a Security Group reference is appropriate.

## Network ACL Diagnostics

Network ACLs are stateless.

Therefore, a valid TCP path requires both directions to be permitted.

Example:

```text
Application:
10.10.10.20:49152

Database:
10.20.10.30:5432
```

Outbound:

```text
49152 -> 5432
```

Return:

```text
5432 -> 49152
```

A restrictive NACL can block the response even when the destination Security Group is correct.

Inspect:

```bash
aws ec2 describe-network-acls \
  --filters \
    Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

Evaluate rule order carefully.

## Return Path Analysis

A senior-level network diagnosis must consider both directions.

A common incorrect model is:

```text
Source
  |
  v
Destination
```

For TCP, think:

```text
Source
  |
  | SYN
  v
Destination
  |
  | SYN-ACK
  v
Source
```

The forward route can be correct while the return route is broken.

This is particularly important with:

- Transit Gateway.
- VPN.
- Direct Connect.
- VPC peering.
- Hybrid networks.
- Multiple route domains.

## Asymmetric Routing

Asymmetric routing occurs when traffic travels through different paths in each direction.

Example:

```text
Forward:
VPC A -> TGW -> VPC B

Return:
VPC B -> VPN -> On-Premises -> VPC A
```

This may cause problems depending on the network architecture and stateful devices involved.

When troubleshooting hybrid networks, explicitly map:

```text
Forward path
Return path
```

Do not assume the reverse route mirrors the forward route.

## NAT Gateway Diagnostics

For private workloads accessing the Internet:

```text
Private EC2
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

Check:

```text
Private route table
NAT Gateway
Public subnet route table
Internet Gateway
NAT Gateway state
Security Groups
NACLs
```

Reachability analysis can help validate supported portions of the AWS-side path, but it does not prove that the external service is healthy.

## Internet Gateway Diagnostics

For public connectivity, inspect:

```text
Route:
0.0.0.0/0 -> Internet Gateway
```

Then verify:

- Correct subnet association.
- Public addressing.
- Security Group.
- NACL.
- Destination service.
- Application listener.

Do not treat an Internet Gateway route as sufficient proof of Internet connectivity.

## Load Balancer Diagnostics

A load balancer introduces multiple network paths.

```text
Client
  |
  v
Load Balancer
  |
  v
Target
```

The client-to-load-balancer path can work while the load-balancer-to-target path fails.

For example:

```text
Client -> ALB       SUCCESS
ALB -> Target       FAILURE
```

Investigate the target path independently.

Check:

- Target Security Group.
- Load Balancer Security Group.
- Target subnet NACL.
- Target route.
- Target port.
- Health checks.
- Application listener.

## EKS and Kubernetes Diagnostics

Kubernetes introduces additional networking layers.

```text
Pod
 |
 v
Kubernetes CNI
 |
 v
ENI / Node Network
 |
 v
VPC
 |
 v
AWS Network Path
```

When troubleshooting EKS, identify:

```text
Pod IP
Node
ENI
Subnet
Security Groups
NetworkPolicy
Route table
```

A successful VPC-level reachability result does not prove that a Kubernetes NetworkPolicy permits the connection.

Conversely, a Kubernetes policy failure does not necessarily mean the VPC path is broken.

## DNS Diagnostics

Reachability Analyzer is not a replacement for DNS diagnostics.

Separate:

```text
Name resolution
```

from:

```text
IP connectivity
```

For example:

```bash
dig api.internal.example.com
```

Then:

```bash
nc -vz 10.20.10.30 443
```

And:

```bash
curl -v https://api.internal.example.com
```

These tests progressively validate:

```text
DNS
 |
 v
TCP
 |
 v
TLS / HTTP
```

If DNS fails, there may be no meaningful IP-level connectivity test to perform until the name-resolution issue is resolved.

## VPC Flow Logs Correlation

Reachability Analyzer evaluates configuration.

Flow Logs show observed traffic.

Use both:

```text
Reachability Analyzer:
Expected path blocked by NACL

Flow Logs:
REJECT observed

Conclusion:
Strong evidence of NACL-related connectivity failure
```

Another example:

```text
Reachability Analyzer:
Path reachable

Flow Logs:
ACCEPT observed

Application:
Timeout
```

Now investigate:

```text
Return traffic
Remote firewall
Application
TLS
Protocol
Destination health
```

Do not stop at the first successful network diagnostic.

## Application-Level Diagnostics

Once AWS network configuration appears correct, test from the workload itself.

For TCP:

```bash
nc -vz 10.20.10.30 5432
```

For HTTPS:

```bash
curl -v https://api.example.com
```

For DNS:

```bash
dig api.example.com
```

For a listening socket:

```bash
ss -lntp
```

For PostgreSQL:

```bash
pg_isready -h 10.20.10.30 -p 5432
```

These tests answer different questions.

| Tool | Primary Question |
|---|---|
| `dig` | Does DNS resolve? |
| `nc` | Can TCP connect? |
| `curl` | Can the HTTP/TLS stack communicate? |
| `ss` | Is a local service listening? |
| `pg_isready` | Is PostgreSQL accepting readiness checks? |
| Reachability Analyzer | Is the configured AWS network path reachable? |
| Flow Logs | Was network traffic observed and accepted/rejected? |

## Diagnostic Tool Selection

A practical tool-selection model is:

| Symptom | First Tools |
|---|---|
| DNS failure | `dig`, Route 53 diagnostics |
| Missing AWS route | Reachability Analyzer, route inspection |
| Security Group suspicion | Reachability Analyzer, SG inspection |
| NACL suspicion | Reachability Analyzer, Flow Logs, NACL inspection |
| VPC peering failure | Reachability Analyzer, route tables |
| TGW failure | Reachability Analyzer, TGW route tables |
| VPN failure | Reachability Analyzer, VPN telemetry, Flow Logs |
| NAT failure | Reachability Analyzer, NAT metrics, route inspection |
| Application timeout | Reachability Analyzer, Flow Logs, `nc`, application logs |
| TLS failure | `curl -v`, `openssl`, application logs |
| TCP retransmission | Packet capture |
| Kafka broker connectivity | Reachability analysis, Flow Logs, Kafka client logs |
| PostgreSQL connectivity | Reachability analysis, Flow Logs, `pg_isready`, PostgreSQL logs |

## Diagnostic Tool Layering

A mature troubleshooting process moves through layers.

```text
Layer 1: Name Resolution
    |
    v
Layer 2: Network Configuration
    |
    v
Layer 3: Observed Network Traffic
    |
    v
Layer 4: TCP Connectivity
    |
    v
Layer 5: TLS / Protocol
    |
    v
Layer 6: Application
```

Typical tools:

```text
DNS:
dig

Network configuration:
Reachability Analyzer
AWS CLI

Observed traffic:
VPC Flow Logs

TCP:
nc
telnet where appropriate

TLS:
curl
openssl

Application:
service-specific clients
application logs
```

This layered approach avoids mixing unrelated failure domains.

## Pre-Deployment Validation

Reachability Analyzer is particularly useful before production deployment.

Suppose a new application subnet will communicate with PostgreSQL:

```text
Application subnet
        |
        v
Transit Gateway
        |
        v
Database VPC
        |
        v
PostgreSQL
```

Before deployment, validate:

```text
Application -> PostgreSQL:5432
Application -> Redis:6379
Application -> Kafka:9092/appropriate listener
Application -> Internal API:443
```

This can catch configuration errors before they become production incidents.

## CI/CD and Infrastructure Validation

Reachability checks can complement infrastructure-as-code validation.

A production pipeline might conceptually use:

```text
Terraform / CloudFormation
        |
        v
Infrastructure Deployment
        |
        v
Network Validation
        |
        v
Reachability Analysis
        |
        v
Application Smoke Tests
```

Static infrastructure validation can detect configuration problems, while reachability analysis can validate the resulting AWS network path.

Do not rely solely on unit tests for infrastructure networking.

## Troubleshooting a FastAPI Service

Consider:

```text
FastAPI
   |
   v
PostgreSQL
```

The application reports:

```text
connection timeout
```

A senior troubleshooting process is:

```text
1. Resolve database hostname.
2. Identify database IP.
3. Identify FastAPI source ENI.
4. Run Reachability Analyzer.
5. Check route path.
6. Check Security Groups.
7. Check NACLs.
8. Check Flow Logs.
9. Run nc from the application host/container.
10. Check PostgreSQL listener.
11. Check PostgreSQL logs.
```

Do not immediately modify the database Security Group.

## Troubleshooting Django

For Django:

```text
Django
  |
  v
Redis
  |
  v
Celery
```

If Celery workers cannot connect to Redis:

```text
Django / Celery Worker
        |
        v
Redis:6379
```

validate:

```text
DNS
Source ENI
Route
Security Group
NACL
Reachability
Flow Logs
Redis listener
```

If Reachability Analyzer says the path is reachable but Celery still fails, move upward:

```text
TCP
 |
 v
Redis TLS / protocol
 |
 v
Authentication
 |
 v
Celery configuration
```

## Troubleshooting gRPC

For:

```text
Service A
   |
   | gRPC / HTTP2
   v
Service B
```

validate the network path first:

```text
Service A -> Service B:443
```

Then validate:

```text
TCP
TLS
HTTP/2
gRPC
Application
```

Reachability Analyzer only addresses the network configuration layer.

It cannot establish that the gRPC service method itself is functioning.

## Common Mistakes

### Treating Reachability Analyzer as a Live Connectivity Test

Incorrect:

```text
Reachability = reachable
therefore
application connection = successful
```

Correct:

```text
Reachability = configured AWS path appears reachable
```

Then perform an actual application-level test.

### Ignoring DNS

A valid IP path does not fix a hostname-resolution problem.

Always separate:

```text
DNS
```

from:

```text
IP connectivity
```

### Ignoring Return Routes

A forward path can succeed while the response path fails.

Always inspect:

```text
Source -> Destination
Destination -> Source
```

### Checking Only the Source Route Table

The destination side can have:

- Incorrect route.
- Wrong route-table association.
- NACL restriction.
- Security Group restriction.

### Assuming Transit Gateway Has One Global Route Table

Transit Gateway can use multiple route tables and attachment associations.

Always identify:

```text
TGW attachment
TGW route table
association
propagation
destination route
```

### Changing Infrastructure Before Running Diagnostics

Unstructured changes make incidents harder to reason about.

Prefer:

```text
Observe
  |
Analyze
  |
Change
  |
Validate
```

rather than:

```text
Change
  |
Change again
  |
Change again
```

### Ignoring Kubernetes NetworkPolicy

A VPC-level reachable path does not necessarily mean a pod-level network policy allows traffic.

### Ignoring External Firewalls

AWS can have a valid route while an on-premises firewall or external service blocks traffic.

## Production Pitfalls

### Over-Reliance on Console Inspection

Large environments are difficult to reason about manually.

Prefer reproducible commands and documented diagnostics.

### Lack of Network Path Documentation

For critical dependencies, document:

```text
Source
Destination
Protocol
Port
VPC
Subnet
Route
Intermediate network
Security boundary
```

### No Standardized Diagnostic Procedure

Different engineers should not troubleshoot the same connectivity problem using unrelated processes.

Create runbooks containing:

```text
Identification
Reachability Analysis
Flow Log Query
Route Inspection
Security Inspection
Application Test
Escalation
```

### No Pre-Deployment Network Validation

Network configuration errors are cheaper to fix before deployment.

Integrate connectivity validation into infrastructure deployment workflows where practical.

## Security Considerations

Reachability diagnostics expose infrastructure topology and network configuration.

Protect access to:

- EC2 metadata.
- Network configuration.
- Flow Logs.
- Route tables.
- Security Groups.
- Transit Gateway configuration.
- VPC topology.

Use least-privilege IAM.

A troubleshooting role should not automatically have permission to modify production networking.

Separate:

```text
Read / Diagnose
```

from:

```text
Modify / Remediate
```

where operationally practical.

This reduces the risk of accidental network changes during incidents.

## Reliability Considerations

For production systems, validate critical communication paths before incidents occur.

Examples:

```text
API -> Database
API -> Redis
API -> Kafka
Worker -> Database
Worker -> Redis
Worker -> External API
VPC A -> VPC B
AWS -> On-Premises
```

For each critical path, document:

```text
Expected source
Expected destination
Protocol
Port
Network path
Security boundary
Diagnostic command
```

This creates a repeatable troubleshooting model.

## Monitoring Considerations

Reachability Analyzer is primarily a diagnostic and validation mechanism.

It should complement continuous monitoring.

Use:

```text
CloudWatch
VPC Flow Logs
Application metrics
Synthetic tests
Load balancer metrics
VPN metrics
Transit Gateway metrics
DNS telemetry
```

For critical services, synthetic connectivity tests can detect real runtime failures that static path analysis cannot.

A useful distinction is:

```text
Reachability Analyzer:
Can the configured path exist?

Synthetic test:
Does the real service work?

Flow Logs:
What traffic was observed?
```

## Cost Considerations

Diagnostic tools should be used intentionally.

Consider:

- Flow Log ingestion.
- CloudWatch Logs storage.
- S3 storage.
- Query costs.
- Long-term retention.
- Repeated diagnostic analyses.

Do not disable observability solely to reduce cost.

Instead define:

```text
Required telemetry
+
Retention policy
+
Diagnostic workflow
+
Cost budget
```

## Disaster Recovery and Multi-Region Considerations

Network paths should also be validated across disaster-recovery architectures.

For example:

```text
Primary Region
    |
    v
Primary VPC
    |
    v
Primary Database

        X

Secondary Region
    |
    v
Secondary VPC
    |
    v
Secondary Database
```

Do not assume that a DR environment has identical network configuration.

Validate:

- Route tables.
- Transit Gateway attachments.
- Inter-region connectivity.
- Security Groups.
- NACLs.
- DNS.
- Service endpoints.
- Application dependencies.

A DR environment that cannot reach its dependencies is not operationally equivalent to production.

## Production Troubleshooting Checklist

```text
[ ] Identify source workload
[ ] Identify destination workload
[ ] Identify source ENI
[ ] Identify destination ENI
[ ] Identify protocol
[ ] Identify destination port
[ ] Identify source and destination VPCs
[ ] Identify source and destination subnets
[ ] Identify intended network path
[ ] Check DNS separately
[ ] Create or identify Reachability Analyzer path
[ ] Run network analysis
[ ] Check analysis state
[ ] Check reachability result
[ ] Identify any reported blocking component
[ ] Inspect source route table
[ ] Inspect destination route table
[ ] Inspect Transit Gateway routes if applicable
[ ] Inspect VPC peering routes if applicable
[ ] Inspect VPN routing if applicable
[ ] Inspect NAT configuration if applicable
[ ] Inspect Internet Gateway configuration if applicable
[ ] Inspect Security Groups
[ ] Inspect Network ACLs
[ ] Check return path
[ ] Check VPC Flow Logs
[ ] Run TCP connectivity test
[ ] Run protocol-specific test
[ ] Check application logs
[ ] Check external firewalls if applicable
[ ] Check Kubernetes NetworkPolicies if applicable
[ ] Check recent infrastructure changes
[ ] Validate remediation
[ ] Document the confirmed failure layer
```

## Diagnostic Decision Matrix

| Observation | Next Investigation |
|---|---|
| Reachability analysis fails with route issue | Inspect route table and route association |
| Reachability analysis identifies SG restriction | Inspect Security Group rules |
| Reachability analysis identifies NACL restriction | Inspect NACL rules and ephemeral ports |
| TGW path fails | Inspect TGW association, propagation, and routes |
| Peering path fails | Inspect routes on both VPCs |
| Analysis succeeds but application fails | Test TCP, protocol, TLS, and application |
| Flow Logs show `REJECT` | Correlate with network controls |
| Flow Logs show `ACCEPT` but timeout occurs | Investigate return path and remote/application layers |
| DNS fails | Investigate Route 53/VPC DNS configuration |
| AWS path works but on-premises fails | Investigate VPN, BGP, and remote firewall |
| EKS path works but pod cannot connect | Investigate CNI and NetworkPolicy |
| ALB reachable but target unhealthy | Investigate ALB-to-target path |

## Interview Traps

### "Reachability Analyzer Proves the Application Is Healthy"

Incorrect.

It validates network reachability based on supported configuration.

### "Reachability Analyzer Replaces Flow Logs"

Incorrect.

Reachability Analyzer evaluates configuration; Flow Logs provide observed traffic telemetry.

### "A Reachable Path Means TCP Works"

Not necessarily.

The actual workload still needs to establish the connection successfully.

### "Reachability Analyzer Can Diagnose DNS"

Not directly.

DNS should be tested independently.

### "A Successful AWS Path Proves On-Premises Connectivity"

Incorrect.

Remote firewalls, routers, VPN tunnels, and BGP can still prevent traffic.

### "One TGW Route Table Is Enough to Troubleshoot Transit Gateway"

Incorrect.

You must account for:

```text
Attachment
Association
Propagation
Route table
Route
```

### "A Network Path Is the Same as an Application Dependency"

Incorrect.

An application dependency includes layers above networking:

```text
DNS
TCP
TLS
Protocol
Authentication
Application
```

## Recommended Production Workflow

Use the following sequence for serious VPC connectivity incidents:

```text
1. Identify the source and destination.
2. Establish protocol and destination port.
3. Identify source and destination ENIs.
4. Identify the intended network architecture.
5. Validate DNS separately.
6. Run Reachability Analyzer.
7. Inspect any reported blocking component.
8. Validate both forward and return routes.
9. Check Security Groups and NACLs.
10. Check Transit Gateway, peering, VPN, NAT, or Internet Gateway where applicable.
11. Correlate with VPC Flow Logs.
12. Perform an actual TCP connectivity test.
13. Perform a protocol-specific test.
14. Validate the destination service.
15. Check remote infrastructure when the path leaves AWS.
16. Apply the smallest justified configuration change.
17. Re-run diagnostics.
18. Validate from the actual workload.
19. Record the root cause and remediation.
```

The important operational principle is:

> **Use Reachability Analyzer to understand the configured path, Flow Logs to understand observed traffic, and application-level tests to prove real connectivity.**

## Key Takeaways

- **Reachability Analyzer validates the configured AWS network path**, making it especially useful for diagnosing route, Security Group, NACL, Transit Gateway, and VPC peering problems.
- **Reachability Analyzer and VPC Flow Logs answer different questions**: one evaluates configuration, while the other provides evidence about observed network traffic.
- **A reachable analysis result does not prove application success**; DNS, TCP, TLS, protocol, authentication, and application behavior must still be validated separately.
- **Always analyze the complete bidirectional path**, including route associations, Transit Gateway routing, NACLs, hybrid connectivity, and return routes.
- **Use reproducible diagnostics before changing production networking** and combine AWS path analysis, Flow Logs, CLI inspection, and workload-level tests to establish the actual failure layer.