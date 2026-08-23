# 08- VPC Flow Logs and Troubleshooting Questions

## Overview

VPC Flow Logs and network troubleshooting questions evaluate whether you can diagnose connectivity failures systematically rather than changing Security Groups or route tables at random.

A strong troubleshooting approach separates the network path into distinct layers:

```text
Application
    |
    v
DNS
    |
    v
Network Interface
    |
    v
Security Group
    |
    v
Network ACL
    |
    v
Route Table
    |
    v
Gateway / Endpoint / Transit Gateway
    |
    v
Destination
```

VPC Flow Logs provide network-level evidence about traffic observed by supported network interfaces and other supported resources. They are particularly useful when an application reports symptoms such as:

- Connection timeout.
- Connection refused.
- Intermittent connectivity.
- Unexpected source or destination.
- Rejected traffic.
- Missing response traffic.
- Cross-VPC connectivity failure.
- Unexpected outbound traffic.

Flow Logs should not be treated as a complete packet capture. They provide metadata about network traffic and its disposition, not application payloads.

## What Are VPC Flow Logs?

VPC Flow Logs capture information about network traffic to and from network interfaces and supported AWS resources.

A simplified record contains information such as:

```text
Source address
Destination address
Source port
Destination port
Protocol
Packets
Bytes
Start time
End time
Action
Log status
```

The exact available fields depend on the configured flow-log format and AWS capabilities.

A typical flow-log record can help answer:

> Did traffic from source A reach the network interface, and was it accepted or rejected?

It generally cannot answer:

> What HTTP response did the application return?

That distinction is important.

## Why Flow Logs Exist

Traditional application logs may show:

```text
Database connection timeout
```

but they do not necessarily tell you whether the failure originated from:

- Incorrect routing.
- Security Group rules.
- NACL rules.
- Incorrect destination IP.
- Wrong destination port.
- Transit Gateway routing.
- VPN connectivity.
- Return-path problems.

Flow Logs provide another layer of evidence.

```mermaid
flowchart LR
    App[Application]
    OS[Host / Network Stack]
    VPC[VPC Networking]
    Flow[VPC Flow Logs]
    Dest[Destination]

    App --> OS
    OS --> VPC
    VPC --> Dest
    VPC --> Flow
```

The application tells you what it experienced.

Flow Logs help establish what happened at the VPC networking layer.

## When to Use VPC Flow Logs

Use Flow Logs when investigating:

- Unexpected `REJECT` traffic.
- Unexpected `ACCEPT` traffic.
- Connection timeouts.
- Network paths between subnets.
- Cross-VPC communication.
- Hybrid connectivity.
- Security incidents.
- Unexpected outbound connections.
- Network policy changes.
- Kubernetes networking problems.
- Intermittent connectivity.

Flow Logs are especially useful when application-level evidence does not identify the network failure.

## Flow Logs vs Packet Capture

Flow Logs are metadata-oriented.

Packet capture is payload-oriented.

| Capability | VPC Flow Logs | Packet Capture |
|---|---|---|
| Source/destination metadata | Yes | Yes |
| Ports | Yes | Yes |
| Protocol | Yes | Yes |
| Accept/reject information | Yes | Not directly equivalent |
| Application payload | No | Potentially |
| HTTP request inspection | No | Potentially |
| TLS payload inspection | No | Encrypted |
| Operational overhead | Relatively low | Higher |
| Long-term centralized logging | Well suited | Less suited |

Do not attempt to use Flow Logs as a replacement for packet-level diagnostics.

## Flow Log Architecture

Flow Logs can deliver records to supported destinations such as:

- Amazon CloudWatch Logs.
- Amazon S3.
- Amazon Data Firehose.

A simplified architecture is:

```mermaid
flowchart TB
    ENI[Network Interface]
    FL[VPC Flow Log]
    CW[CloudWatch Logs]
    S3[S3]
    FH[Firehose]

    ENI --> FL
    FL --> CW
    FL --> S3
    FL --> FH
```

The appropriate destination depends on operational requirements.

### CloudWatch Logs

Useful for:

- Operational troubleshooting.
- Log queries.
- Shorter-term investigations.
- Integration with CloudWatch tooling.

### Amazon S3

Useful for:

- Long-term retention.
- Centralized security analysis.
- Large-volume archival.
- Athena-based querying.

### Firehose

Useful when flow records need to be delivered into supported downstream analytics or observability systems.

## Flow Log Scope

When enabling Flow Logs, carefully select the scope.

Depending on the supported configuration, Flow Logs can be associated with resources such as:

- VPCs.
- Subnets.
- Network interfaces.

A broad VPC-level configuration provides broad visibility, while narrower scopes can be useful when investigating a specific workload or reducing unnecessary logging volume.

The architectural question is not simply:

> Should Flow Logs be enabled?

It is:

> What traffic needs to be observable, for how long, and at what operational cost?

## ACCEPT vs REJECT

One of the most important fields in troubleshooting is the traffic action.

Conceptually:

```text
ACCEPT
    |
    +--> Traffic was permitted

REJECT
    |
    +--> Traffic was rejected
```

A `REJECT` record is strong evidence that a network-level policy rejected the traffic.

However, the absence of a `REJECT` record does not automatically prove that the application connection succeeded.

For example:

```text
Client
  |
  | SYN
  v
Server
  |
  X Application unavailable
```

The network path may permit the packet even though the application is not listening.

## Interview Question: What Does ACCEPT Mean?

`ACCEPT` indicates that the traffic was permitted at the relevant network layer represented by the flow record.

It does not necessarily mean:

- The application accepted the connection.
- The destination process was listening.
- The application returned HTTP 200.
- The database authentication succeeded.
- The request completed successfully.

This is a common interview trap.

## Interview Question: What Does REJECT Mean?

`REJECT` indicates that traffic was rejected at the network layer represented by the flow record.

Possible causes include:

- Security Group policy.
- Network ACL policy.
- Other supported network-level filtering behavior.

The next troubleshooting step is to inspect the network path and policies rather than immediately changing every rule.

## Connection Timeout vs Connection Refused

These symptoms provide useful diagnostic information.

### Connection Timeout

A timeout often indicates that packets or responses are not successfully completing the expected path.

Potential causes include:

- Security Group.
- NACL.
- Route table.
- Missing return route.
- Transit Gateway routing.
- VPN failure.
- Network appliance.
- Destination unavailable.

### Connection Refused

A refusal generally indicates that the destination was reachable enough for the connection attempt to receive an explicit refusal.

Potential causes include:

- No process listening on the target port.
- Service stopped.
- Host firewall.
- Incorrect application configuration.

The distinction is useful:

```text
Timeout
    |
    +--> Investigate network path first

Refused
    |
    +--> Investigate destination service/listener
```

It is not absolute, but it is a useful first diagnostic branch.

## A Systematic Troubleshooting Workflow

When an application cannot reach another service, avoid changing infrastructure immediately.

Use a structured process.

### Identify Source and Destination

Determine:

```text
Source:
10.0.11.25

Destination:
10.0.21.50

Protocol:
TCP

Destination Port:
5432
```

For example:

```text
FastAPI
10.0.11.25
    |
    | TCP 5432
    v
PostgreSQL
10.0.21.50
```

### Validate DNS

If the application uses:

```text
postgres.internal.example.com
```

verify that the hostname resolves to the expected address.

From a Linux host:

```bash
getent hosts postgres.internal.example.com
```

or:

```bash
dig postgres.internal.example.com
```

If DNS resolves to the wrong address, investigating Security Groups first may waste time.

### Validate Routing

Inspect the route table associated with the source subnet.

For example:

```text
Destination       Target
10.0.0.0/16       local
```

For cross-VPC connectivity, verify that an appropriate route exists toward:

- VPC peering.
- Transit Gateway.
- VPN.
- Network appliance.

Then verify the destination side has a return route.

### Validate Security Groups

For PostgreSQL:

```text
Destination:
TCP 5432

Source:
Application Security Group
```

Do not assume that because both resources are in the same VPC, the traffic is allowed.

### Validate NACLs

Check both directions.

Because NACLs are stateless, return traffic must be permitted independently.

A common mistake is:

```text
Inbound:
5432 allowed

Outbound:
Ephemeral ports blocked
```

The connection may still fail because response traffic cannot return.

### Inspect Flow Logs

Search for:

```text
Source IP
Destination IP
Destination Port
Protocol
Action
```

Example:

```text
10.0.11.25
10.0.21.50
5432
TCP
REJECT
```

This provides strong evidence that the traffic was rejected at the network layer.

### Validate the Destination

If networking appears correct, check:

```bash
nc -vz 10.0.21.50 5432
```

For HTTP services:

```bash
curl -v https://service.internal.example.com
```

For TLS:

```bash
openssl s_client -connect service.internal.example.com:443
```

The objective is to determine whether the failure is:

```text
DNS
  |
  v
Network
  |
  v
TCP
  |
  v
TLS
  |
  v
HTTP
  |
  v
Application
```

## End-to-End Troubleshooting Flow

```mermaid
flowchart TD
    Start[Application Cannot Connect]
    DNS[Validate DNS]
    Route[Validate Route]
    SG[Validate Security Groups]
    NACL[Validate NACLs]
    Flow[Inspect Flow Logs]
    Reach[Use Reachability Analyzer]
    TCP[Test TCP Connectivity]
    App[Inspect Destination Application]

    Start --> DNS
    DNS --> Route
    Route --> SG
    SG --> NACL
    NACL --> Flow
    Flow --> Reach
    Reach --> TCP
    TCP --> App
```

The exact order can vary, but the principle is to move from addressing and routing toward policy and then application behavior.

## Interview Question: How Would You Troubleshoot a Timeout?

A strong answer could be:

1. Identify source and destination IPs.
2. Verify DNS resolution if a hostname is involved.
3. Confirm the source subnet route table.
4. Confirm the destination subnet route table and return path.
5. Check Security Groups.
6. Check NACLs.
7. Inspect VPC Flow Logs for `ACCEPT` or `REJECT`.
8. Use Reachability Analyzer for supported network-path analysis.
9. Test the destination port from the source environment.
10. Inspect the destination service if network connectivity is valid.

The important part is demonstrating a hypothesis-driven process.

## Reachability Analyzer

Reachability Analyzer is a network diagnostic capability that analyzes whether a path between specified network resources is reachable based on the configured network topology and routing/security configuration.

Conceptually:

```text
Source
  |
  v
Route Table
  |
  v
Security Group
  |
  v
NACL
  |
  v
Gateway / Network Path
  |
  v
Destination
```

It can help identify the component preventing reachability.

This is particularly valuable when manually tracing large routing configurations becomes difficult.

## Flow Logs vs Reachability Analyzer

| Tool | Best Use |
|---|---|
| VPC Flow Logs | Observe actual traffic metadata |
| Reachability Analyzer | Analyze expected network reachability |
| Application logs | Understand application behavior |
| CloudTrail | Investigate configuration/API changes |
| DNS tools | Validate name resolution |
| `curl` / `nc` | Test actual connectivity |
| Packet capture | Inspect packet-level behavior |

These tools complement one another.

A strong production workflow does not rely on one tool.

## Interview Question: Why Use Reachability Analyzer If Flow Logs Exist?

Because they answer different questions.

Flow Logs help answer:

> What traffic was observed?

Reachability Analyzer helps answer:

> Based on the current network configuration, is a path expected to be reachable, and where is the blocking component?

For example:

```text
Flow Logs:
REJECT

Reachability Analyzer:
Blocked by network ACL
```

Together they provide stronger evidence than either tool alone.

## Troubleshooting Security Group Problems

Consider:

```text
ALB
 |
 | TCP 443
 v
API
 |
 | TCP 5432
 v
PostgreSQL
```

A good Security Group relationship is:

```text
API-SG
    |
    | TCP 5432
    v
DB-SG
```

The database should not need:

```text
0.0.0.0/0 -> TCP 5432
```

A production diagnostic process should identify exactly which source and destination are expected.

## Troubleshooting NACL Problems

NACLs are stateless.

Suppose:

```text
Client: 10.0.11.20
Server: 10.0.21.30
Server Port: 443
```

The client may use an ephemeral source port:

```text
Client
10.0.11.20:49152
      |
      | TCP 443
      v
Server
10.0.21.30:443
```

The return traffic is:

```text
Server
10.0.21.30:443
      |
      | TCP 49152
      v
Client
10.0.11.20:49152
```

NACL rules must account for both directions.

This is a frequent production troubleshooting issue.

## Troubleshooting Cross-VPC Connectivity

Consider:

```text
VPC A
10.10.0.0/16
     |
     | Transit Gateway
     |
VPC B
10.20.0.0/16
```

Verify:

```text
VPC A route table
10.20.0.0/16 -> TGW

TGW route table
10.20.0.0/16 -> VPC B

VPC B route table
10.10.0.0/16 -> TGW
```

Then verify:

- Security Groups.
- NACLs.
- TGW attachment state.
- TGW route-table association.
- TGW route propagation/static routes.
- Return path.

A common mistake is checking only the source-side route.

## Troubleshooting VPC Peering

For:

```text
VPC A <----> VPC B
```

verify:

- Peering connection state.
- Source route table.
- Destination route table.
- Security Groups.
- NACLs.
- Non-overlapping CIDRs.

Remember that VPC peering is not transitive.

If:

```text
A <--> B
B <--> C
```

traffic from A to C does not automatically traverse B.

## Troubleshooting Transit Gateway

For Transit Gateway connectivity, check:

```text
VPC
 |
 v
TGW Attachment
 |
 v
TGW Route Table
 |
 v
Destination Attachment
```

Common failures include:

- Attachment not available.
- Incorrect TGW route-table association.
- Missing route.
- Incorrect route propagation.
- Incorrect VPC route.
- Missing return route.
- Security Group restrictions.
- NACL restrictions.

For complex TGW environments, route-table segmentation should be reviewed explicitly.

## Troubleshooting NAT Gateway Connectivity

Suppose a private application cannot reach an external API.

Expected path:

```text
Private Subnet
      |
      v
Route Table
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

Verify:

- Private subnet has a default route to NAT.
- NAT Gateway is available.
- NAT Gateway is in a subnet with appropriate Internet routing.
- Internet Gateway is attached.
- Security controls permit the traffic.
- DNS resolves the external hostname.
- External service is reachable.

A common mistake is placing a NAT Gateway in a private subnet.

A NAT Gateway used for Internet egress needs the appropriate public-subnet architecture.

## Troubleshooting VPC Endpoints

For an interface endpoint:

```text
Application
    |
    v
Private DNS
    |
    v
Interface Endpoint ENI
    |
    v
AWS Service
```

Check:

- Endpoint exists.
- Endpoint is available.
- Correct subnets are associated.
- Security Group permits traffic to the endpoint.
- DNS resolution is configured correctly.
- Endpoint policy permits the required operation.
- Application resolves the AWS service hostname to the expected endpoint path.

For gateway endpoints, verify route-table association and endpoint policy.

## Troubleshooting Hybrid Connectivity

Consider:

```text
AWS VPC
   |
   v
Transit Gateway
   |
   v
VPN / Direct Connect
   |
   v
Corporate Network
```

Troubleshoot both directions.

Verify:

- AWS route tables.
- TGW routes.
- VPN tunnel state.
- Direct Connect state where applicable.
- On-premises routes.
- Firewall rules.
- Security Groups.
- NACLs.
- DNS.
- Return path.

A frequent mistake is assuming:

```text
AWS -> On-Premises
```

working means:

```text
On-Premises -> AWS
```

must also work.

Routing is bidirectional for most request/response flows.

## Flow Logs and Application Debugging

Suppose a Django application reports:

```text
psycopg connection timeout
```

Do not immediately change PostgreSQL configuration.

Investigate:

```text
Django
  |
  | TCP 5432
  v
PostgreSQL
```

Then:

```text
1. Resolve PostgreSQL hostname.
2. Verify target IP.
3. Verify route.
4. Verify Security Group.
5. Verify NACL.
6. Inspect Flow Logs.
7. Test TCP 5432.
8. Check PostgreSQL listener.
```

The same methodology applies to FastAPI, gRPC services, Celery workers, Redis, and other network-dependent backend components.

## Flow Logs for Security Investigation

Flow Logs can also support security investigations.

For example, unexpected outbound traffic may reveal:

```text
Application ENI
    |
    | TCP 443
    v
Unexpected external IP
```

Potential investigation areas include:

- Compromised workload.
- Unexpected dependency.
- Misconfigured application.
- Malware.
- Unauthorized administrative activity.

Flow Logs should be combined with:

- CloudTrail.
- GuardDuty.
- Application logs.
- Host telemetry.
- Security findings.

Flow Logs alone do not explain why the traffic occurred.

## Querying Flow Logs

When using CloudWatch Logs Insights, a conceptual query can filter records by action:

```text
fields @timestamp, srcAddr, dstAddr, srcPort, dstPort, protocol, action
| filter action = "REJECT"
| sort @timestamp desc
| limit 100
```

For a specific destination port:

```text
fields @timestamp, srcAddr, dstAddr, srcPort, dstPort, protocol, action
| filter dstPort = 5432
| sort @timestamp desc
| limit 100
```

For a specific source:

```text
fields @timestamp, srcAddr, dstAddr, srcPort, dstPort, protocol, action
| filter srcAddr = "10.0.11.25"
| sort @timestamp desc
| limit 100
```

The exact field names depend on the configured flow-log format.

## AWS CLI Diagnostic Commands

List VPCs:

```bash
aws ec2 describe-vpcs
```

List subnets:

```bash
aws ec2 describe-subnets
```

Inspect route tables:

```bash
aws ec2 describe-route-tables
```

Inspect Security Groups:

```bash
aws ec2 describe-security-groups
```

Inspect network interfaces:

```bash
aws ec2 describe-network-interfaces
```

Inspect VPC Flow Logs:

```bash
aws ec2 describe-flow-logs
```

Inspect Transit Gateway:

```bash
aws ec2 describe-transit-gateways
```

Inspect Transit Gateway attachments:

```bash
aws ec2 describe-transit-gateway-attachments
```

Inspect VPC peering:

```bash
aws ec2 describe-vpc-peering-connections
```

Inspect NAT Gateways:

```bash
aws ec2 describe-nat-gateways
```

Inspect VPC endpoints:

```bash
aws ec2 describe-vpc-endpoints
```

Inspect network ACLs:

```bash
aws ec2 describe-network-acls
```

These commands are most useful when combined with filtering and resource identifiers rather than dumping an entire account's configuration.

## Useful Host-Level Commands

When you have access to the source host, combine AWS-side analysis with OS-level testing.

DNS:

```bash
getent hosts service.internal.example.com
```

TCP connectivity:

```bash
nc -vz service.internal.example.com 443
```

HTTP:

```bash
curl -v https://service.internal.example.com
```

Route inspection:

```bash
ip route
```

Listening sockets:

```bash
ss -lntp
```

Traceroute where supported:

```bash
traceroute service.internal.example.com
```

These commands help separate:

```text
DNS failure
```

from:

```text
TCP connectivity failure
```

from:

```text
Application failure
```

## Common Interview Traps

### "Flow Logs Show ACCEPT, So the Application Works"

Incorrect.

`ACCEPT` indicates network-level acceptance, not successful application processing.

### "No REJECT Means There Is No Network Problem"

Incorrect.

Traffic can be accepted but still fail because of:

- Application listener.
- Host firewall.
- TLS.
- Protocol mismatch.
- Incorrect application configuration.
- Destination failure.

### "Security Group Rules Are Enough to Diagnose Everything"

Incorrect.

You must also consider:

- Route tables.
- NACLs.
- Gateways.
- Endpoints.
- TGW.
- Peering.
- Hybrid routes.
- DNS.

### "NACLs Are Stateful"

Incorrect.

Security Groups are stateful.

NACLs are stateless.

### "A VPC Flow Log Is a Packet Capture"

Incorrect.

Flow Logs provide network-flow metadata, not application payload inspection.

### "The Source Has a Route, So Connectivity Works"

Incorrect.

The destination must also have a valid return path.

### "The Database Is in the Same VPC, So It Is Reachable"

Incorrect.

Same-VPC routing does not bypass Security Groups, NACLs, or service-level availability problems.

## Production Pitfalls

### Enabling Excessive Logging Without Cost Planning

Large VPCs can generate substantial flow-log volume.

Consider:

- Scope.
- Retention.
- Destination.
- Query frequency.
- Storage lifecycle.
- Centralized analysis.

### Insufficient Retention

Short retention may make incident investigation difficult.

Security and compliance requirements should determine retention rather than convenience.

### No Centralized Network Observability

If every team independently stores logs with inconsistent retention and naming, cross-service incidents become harder to investigate.

Centralized observability can improve incident response.

### Logging Without Resource Context

A flow record containing only IP addresses may be difficult to interpret later.

Maintain reliable mappings between:

```text
ENI
IP
Instance
Pod
Service
Environment
Application
```

where practical.

### Treating Flow Logs as Real-Time Application Monitoring

Flow Logs are not a replacement for:

- Application metrics.
- Distributed tracing.
- Access logs.
- Error logs.
- Database monitoring.

They are one layer of observability.

## Production Troubleshooting Checklist

When investigating a VPC connectivity problem, check:

| Layer | Questions |
|---|---|
| DNS | Does the hostname resolve correctly? |
| Source | Is the workload using the expected IP/interface? |
| Routing | Is there a route toward the destination? |
| Return Path | Can the destination return traffic? |
| Security Group | Is the required protocol/port allowed? |
| NACL | Are both directions allowed? |
| Gateway | Is IGW/NAT/TGW/endpoint available? |
| Peering | Is the peering relationship active and routed? |
| TGW | Are attachments and route tables correct? |
| Hybrid | Are VPN/DX routes and tunnels healthy? |
| Flow Logs | Is traffic accepted or rejected? |
| Reachability | Does Reachability Analyzer identify a blocked path? |
| TCP | Can the destination port be reached? |
| Application | Is the destination service listening and healthy? |

## Senior-Level Troubleshooting Approach

A senior engineer should avoid making several infrastructure changes simultaneously.

Instead:

1. Define the exact source and destination.
2. Identify the protocol and destination port.
3. Establish the expected network path.
4. Form a hypothesis.
5. Check the relevant AWS configuration.
6. Check Flow Logs and diagnostic tools.
7. Perform a targeted connectivity test.
8. Change one control at a time.
9. Validate the result.
10. Document the root cause and preventive control.

For example:

```text
Symptom:
FastAPI cannot connect to PostgreSQL.

Hypothesis:
DB Security Group blocks TCP 5432.

Evidence:
Flow Logs show REJECT.

Action:
Allow TCP 5432 from API-SG to DB-SG.

Validation:
Connection succeeds.

Root Cause:
Incorrect Security Group relationship.

Preventive Action:
Manage SG rules through IaC and automated validation.
```

This approach is significantly more reliable than repeatedly modifying route tables and Security Groups until the connection happens to work.

## Key Takeaways

- **VPC Flow Logs provide network-flow evidence, not application payloads; use them to correlate source, destination, ports, protocol, and traffic disposition.**
- **`ACCEPT` or `REJECT` describes network-level behavior and does not by itself prove application-level success or failure.**
- **Effective troubleshooting requires tracing the complete path: DNS, routing, Security Groups, NACLs, gateways/endpoints, return routing, TCP connectivity, and finally the application.**
- **Reachability Analyzer, Flow Logs, AWS CLI commands, host-level tools, and application logs answer different diagnostic questions and are most effective when used together.**
- **Production troubleshooting should be hypothesis-driven, evidence-based, minimally invasive, and followed by a preventive control such as Infrastructure as Code, monitoring, or automated network validation.**