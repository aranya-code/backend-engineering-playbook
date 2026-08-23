# 01- VPC Troubleshooting Methodology

## Overview

VPC troubleshooting is primarily a **layered network diagnosis problem**. When an application cannot reach another service, the failure may originate from DNS, routing, Network ACLs, Security Groups, network interfaces, load balancers, application listeners, or the application itself.

The most effective approach is to avoid changing configuration until the failing layer has been identified. Start with the intended traffic path, verify each dependency in order, and use observable evidence to eliminate possible causes.

A useful mental model is:

```text
Application
    |
    v
DNS Resolution
    |
    v
Source Network Interface
    |
    v
Route Table
    |
    v
Network ACL
    |
    v
Security Group
    |
    v
Network Path
    |
    v
Destination Network Interface
    |
    v
Destination Security Group
    |
    v
Destination Application
```

The exact path varies by architecture, but the principle remains the same: **trace the packet from source to destination and validate every control point**.

## Why VPC Troubleshooting Matters

Network failures often appear as application failures.

For example, a Django application might report:

```text
connection timed out
```

when connecting to PostgreSQL.

That message does not prove PostgreSQL is unhealthy. The actual problem could be:

- Incorrect DNS resolution.
- Missing route.
- Incorrect subnet route table.
- Security Group blocking TCP traffic.
- Network ACL blocking the request.
- Network ACL blocking the response.
- Incorrect destination port.
- PostgreSQL not listening on the expected interface.
- Host-level firewall rules.
- Incorrect database configuration.
- Network connectivity between Availability Zones.
- An unavailable networking dependency.

The troubleshooting objective is therefore not:

> "What AWS setting should I change?"

It is:

> "At which layer does the expected traffic path diverge from reality?"

## Troubleshooting Mindset

A production troubleshooting process should follow four principles:

| Principle | Practice |
|---|---|
| Evidence first | Collect logs, flow records, routes, DNS results, and connection tests before changing configuration |
| Layered diagnosis | Test infrastructure from lower-level network dependencies toward the application |
| Minimize changes | Avoid modifying multiple networking resources during investigation |
| Reproduce safely | Use controlled connectivity tests and temporary diagnostic resources where appropriate |

A useful distinction is:

```text
Configuration
     |
     v
Expected Network Path
     |
     v
Actual Network Behavior
     |
     v
Observed Evidence
     |
     v
Root Cause
```

Do not confuse a configuration that *looks correct* with traffic that has actually been proven to work.

## Establish the Expected Traffic Flow

Before troubleshooting, document:

- Source workload.
- Source subnet.
- Source private IP.
- Destination workload.
- Destination subnet.
- Destination private or public IP.
- Destination port.
- Protocol.
- DNS name.
- Expected route.
- Security boundaries.
- Whether traffic crosses Availability Zones.
- Whether traffic passes through a NAT Gateway, Internet Gateway, Transit Gateway, load balancer, or VPC endpoint.

For example:

```text
FastAPI
10.0.10.25
    |
    | TCP/5432
    v
PostgreSQL
10.0.20.50
```

The expected path might be:

```text
FastAPI ENI
    |
    v
Application Subnet Route Table
    |
    v
VPC Local Route
    |
    v
Database Subnet
    |
    v
PostgreSQL ENI
```

If the database is in the same VPC, traffic normally uses the VPC's local route rather than a NAT Gateway or Internet Gateway.

## Troubleshooting Workflow

Use the following sequence for most VPC connectivity incidents.

```mermaid
flowchart TD
    A[Define Source and Destination] --> B[Confirm DNS]
    B --> C[Confirm IP and Port]
    C --> D[Inspect Route Tables]
    D --> E[Inspect Security Groups]
    E --> F[Inspect Network ACLs]
    F --> G[Inspect Network Interfaces]
    G --> H[Inspect AWS Networking Components]
    H --> I[Test Connectivity]
    I --> J[Inspect Flow Logs]
    J --> K[Inspect Destination Service]
    K --> L[Identify Root Cause]
```

The order is not absolute for every incident, but it provides a repeatable baseline.

## Define the Source and Destination

Start with concrete values.

Avoid troubleshooting statements such as:

```text
The API cannot reach the database.
```

Convert them into something measurable:

```text
Source:
  Workload: FastAPI service
  Private IP: 10.0.10.25
  Subnet: subnet-application-a

Destination:
  Service: PostgreSQL
  Private IP: 10.0.20.50
  Port: TCP/5432
  Subnet: subnet-database-a
```

This eliminates ambiguity.

For distributed systems, also identify whether the failing request is:

- Client → Load Balancer.
- Load Balancer → Application.
- Application → PostgreSQL.
- Application → Redis.
- Application → Kafka.
- Application → AWS API.
- Worker → Message Broker.
- Service → Service through gRPC.

## DNS Troubleshooting

DNS problems can look like network failures.

First verify that the hostname resolves to the expected address.

From a Linux-based workload:

```bash
getent hosts db.internal.example
```

or:

```bash
nslookup db.internal.example
```

or:

```bash
dig db.internal.example
```

Check:

- Does the hostname resolve?
- Does it resolve to a private address?
- Does it return multiple addresses?
- Are the returned addresses expected?
- Is the resolver reachable?
- Is the application using the hostname you expect?

For an AWS internal service, confirm that private DNS behavior is configured correctly.

### DNS Failure Patterns

| Symptom | Possible Cause |
|---|---|
| Hostname does not resolve | DNS configuration or resolver issue |
| Resolves to public IP | Incorrect DNS record or resolution path |
| Resolves intermittently | DNS health, caching, or multiple endpoint behavior |
| Resolves correctly but connection fails | Move to routing and security investigation |
| Application uses stale address | DNS caching or application-level resolution behavior |

Do not spend time modifying Security Groups when the hostname does not resolve.

## Validate the Destination Port

A successful DNS lookup does not prove that the service is reachable.

Test the actual TCP connection where appropriate:

```bash
nc -vz 10.0.20.50 5432
```

For HTTPS:

```bash
curl -v https://internal-api.example.com
```

For a TLS service:

```bash
openssl s_client -connect internal-api.example.com:443
```

For PostgreSQL:

```bash
pg_isready \
  --host=10.0.20.50 \
  --port=5432
```

These tests help distinguish:

```text
DNS failure
    vs
TCP connectivity failure
    vs
TLS failure
    vs
Application protocol failure
```

Do not use `ping` as the primary test for TCP application connectivity. ICMP availability does not prove that TCP/443, TCP/5432, or another application port is reachable.

## Route Table Analysis

Once the source and destination are known, inspect the route table associated with the source subnet.

The key question is:

> Does the source have a route that matches the destination IP?

AWS route selection uses the most specific matching route.

For example:

```text
Destination        Target
10.0.0.0/16        local
0.0.0.0/0          nat-xxxxxxxx
```

A destination such as:

```text
10.0.20.50
```

matches:

```text
10.0.0.0/16
```

and therefore uses the local VPC route.

For external traffic:

```text
0.0.0.0/0
```

may route traffic through:

- NAT Gateway.
- Internet Gateway.
- Transit Gateway.
- Virtual private gateway.
- Network Firewall.
- Other supported targets.

### Route Troubleshooting Checklist

- Confirm the subnet associated with the source ENI.
- Confirm the route table associated with that subnet.
- Identify the longest-prefix match.
- Confirm the target exists.
- Confirm the target is in the expected Availability Zone or network topology.
- Check whether a more-specific route overrides the default route.
- Check both directions for routed networks.

### Common Routing Mistake

A common mistake is checking the route table attached to the destination subnet while ignoring the source subnet.

The source route table determines how the initial packet leaves the source.

For return traffic, the destination side must have a valid route back to the source.

## Security Group Analysis

Security Groups are stateful virtual firewalls attached to network interfaces.

For a TCP connection from an application to PostgreSQL:

```text
Application SG
      |
      | TCP/5432
      v
Database SG
```

A typical database rule might allow:

```text
Protocol: TCP
Port: 5432
Source: Application Security Group
```

This is generally preferable to allowing the entire VPC CIDR.

Example:

```text
Database Security Group

Inbound:
  TCP 5432
  Source: sg-application
```

### Why Security Group References Are Valuable

Using a Security Group as the source expresses an architectural relationship:

```text
Application workload
        |
        v
Database workload
```

rather than relying on a broad network range:

```text
10.0.0.0/16
```

This reduces the blast radius when additional workloads are deployed inside the VPC.

### Security Group Troubleshooting

Verify:

- Source ENI's Security Group.
- Destination ENI's Security Group.
- Destination port.
- Protocol.
- Inbound rules on the destination.
- Outbound rules on the source.
- Whether another Security Group attached to the same ENI provides the required rule.
- Whether the expected Security Group is actually attached to the interface.

Remember that Security Groups are **allow-list based**. There is no explicit deny rule.

## Network ACL Analysis

Network ACLs operate at the subnet boundary and are stateless.

That distinction is critical.

If an application sends:

```text
Source: 10.0.10.25:45000
Destination: 10.0.20.50:5432
```

the destination subnet needs to allow the inbound traffic to TCP/5432.

The response travels back using the ephemeral source port:

```text
Source: 10.0.20.50:5432
Destination: 10.0.10.25:45000
```

Therefore, a restrictive Network ACL must account for both directions.

```mermaid
sequenceDiagram
    participant App as Application
    participant NACL1 as Source NACL
    participant NACL2 as Destination NACL
    participant DB as PostgreSQL

    App->>NACL1: TCP 45000 -> 5432
    NACL1->>NACL2: Forward packet
    NACL2->>DB: TCP 45000 -> 5432
    DB-->>NACL2: TCP 5432 -> 45000
    NACL2-->>NACL1: Return packet
    NACL1-->>App: TCP 5432 -> 45000
```

When troubleshooting Network ACLs, inspect both inbound and outbound rules for both subnets.

## Network Interface Inspection

Elastic Network Interfaces are the actual network attachment points for many AWS resources.

Inspect:

- Private IP addresses.
- Subnet.
- Availability Zone.
- Security Groups.
- Interface status.
- Attached resource.
- Secondary private IPs where applicable.

Useful CLI command:

```bash
aws ec2 describe-network-interfaces \
  --network-interface-ids eni-0123456789abcdef0
```

For filtering interfaces:

```bash
aws ec2 describe-network-interfaces \
  --filters Name=subnet-id,Values=subnet-0123456789abcdef0
```

This is particularly useful when troubleshooting:

- EC2.
- ECS tasks.
- Load balancers.
- VPC endpoints.
- Lambda functions attached to a VPC.
- Other ENI-backed services.

## Connectivity Testing

Use tests that correspond to the actual protocol.

### TCP

```bash
nc -vz 10.0.20.50 5432
```

### HTTP

```bash
curl -v http://10.0.20.50:8080/health
```

### HTTPS

```bash
curl -vk https://internal-api.example.com/health
```

### TLS

```bash
openssl s_client \
  -connect internal-api.example.com:443 \
  -servername internal-api.example.com
```

### PostgreSQL

```bash
pg_isready \
  --host=db.internal.example.com \
  --port=5432
```

The goal is to test the smallest possible unit of the connection.

For example:

```text
DNS
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

If TCP fails, debugging HTTP response handling is premature.

## VPC Reachability Analyzer

AWS VPC Reachability Analyzer can be used to analyze whether a network path exists between supported AWS resources.

It is useful when manually tracing a complex architecture becomes difficult.

A typical analysis asks:

```text
Source ENI
    |
    v
Expected network path
    |
    v
Destination ENI
```

The result can identify blocking or missing network components such as:

- Routes.
- Security Groups.
- Network ACLs.
- Network interfaces.
- Other supported network configuration.

Use it as an evidence-gathering tool rather than relying entirely on manual inspection.

## VPC Flow Logs

Flow Logs provide network traffic metadata that can help determine whether traffic was accepted or rejected.

A simplified record contains information such as:

```text
source address
destination address
source port
destination port
protocol
action
bytes
packets
```

A rejected record can provide strong evidence that traffic reached a network control point but was rejected.

For example:

```text
10.0.10.25 -> 10.0.20.50
TCP
45000 -> 5432
REJECT
```

This significantly narrows the investigation.

Flow Logs should be interpreted together with:

- Route tables.
- Security Groups.
- Network ACLs.
- Application logs.
- Load balancer logs.
- DNS logs where applicable.

## Interpreting ACCEPT and REJECT

Do not treat Flow Logs as a complete application-level packet capture.

They provide network flow metadata, not application payloads.

A useful diagnostic model is:

```text
No Flow Log Record
        |
        +-- Traffic may not have reached the observed interface
        |
        +-- Wrong interface/log scope
        |
        +-- Traffic may not have occurred
        |
        v
Flow Record
        |
        +-- REJECT -> Investigate network controls
        |
        +-- ACCEPT -> Continue toward routing/application diagnosis
```

An `ACCEPT` record does not prove that the application successfully processed the request.

## Application-Level Validation

Once the network path appears valid, inspect the destination service.

For PostgreSQL:

```bash
ss -lntp | grep 5432
```

Verify:

- PostgreSQL is running.
- The service is listening.
- The expected port is configured.
- The service is bound to the expected interface.
- Database authentication is working.
- Connection limits are not exhausted.

For a FastAPI application:

```bash
ss -lntp | grep 8000
```

Then test locally:

```bash
curl http://127.0.0.1:8000/health
```

If local connectivity works but remote connectivity fails, continue investigating the network path.

## Distinguishing Timeout from Connection Refusal

The error type can provide useful evidence.

| Error | Likely Area |
|---|---|
| DNS resolution failure | DNS/application configuration |
| Connection timeout | Routing, Security Group, NACL, firewall, unreachable endpoint |
| Connection refused | Host reachable, but no listener or service rejected connection |
| TLS handshake failure | TLS configuration or certificate problem |
| HTTP 4xx | Application authorization/request semantics |
| HTTP 5xx | Application or upstream dependency |
| PostgreSQL authentication failure | Database authentication/configuration |
| Intermittent connection failure | Capacity, load balancing, DNS, ephemeral ports, network dependency, or application instability |

These are clues, not definitive diagnoses.

## Backend Example: FastAPI to PostgreSQL

Consider:

```text
FastAPI
10.0.10.25:random_ephemeral_port
        |
        | TCP/5432
        v
PostgreSQL
10.0.20.50:5432
```

Troubleshooting should proceed approximately as follows:

```text
1. Resolve database hostname.
2. Confirm it resolves to 10.0.20.50.
3. Confirm source subnet and ENI.
4. Confirm source route table.
5. Confirm local VPC route.
6. Confirm application Security Group.
7. Confirm database Security Group allows TCP/5432 from application SG.
8. Confirm Network ACLs.
9. Confirm PostgreSQL is listening.
10. Test TCP connectivity.
11. Inspect VPC Flow Logs if required.
12. Test database authentication.
```

Avoid immediately changing:

```text
0.0.0.0/0
```

into a Security Group rule simply because the connection is failing.

That may hide the real problem while unnecessarily weakening the network boundary.

## Backend Example: Application to AWS Service

Suppose a private FastAPI service needs to access Amazon S3.

The expected path might be:

```text
FastAPI
   |
   v
Private Subnet
   |
   v
VPC Endpoint
   |
   v
Amazon S3
```

If the application cannot access S3, verify:

- DNS behavior.
- Endpoint configuration.
- Route configuration where applicable.
- Endpoint policy.
- Security Group configuration for interface endpoints.
- Network ACLs.
- IAM permissions.
- Application credentials.

This demonstrates an important troubleshooting principle:

> A successful network path does not imply successful authorization.

AWS access can fail because of either network configuration or IAM/resource policy configuration.

## Kubernetes Considerations

Kubernetes adds additional networking layers.

A simplified path might be:

```text
Pod
 |
 v
Node / ENI
 |
 v
Subnet
 |
 v
Route
 |
 v
Security Controls
 |
 v
Destination
```

For EKS environments, investigate:

- Pod IP allocation.
- Node subnet.
- Security Groups.
- Security Groups for Pods where configured.
- Network ACLs.
- Route tables.
- Cluster networking.
- Load balancer configuration.
- Kubernetes NetworkPolicy.
- DNS inside the cluster.

A common mistake is to stop at AWS Security Groups while ignoring Kubernetes-level networking controls.

## Common Troubleshooting Scenarios

| Symptom | Investigation Order |
|---|---|
| DNS name does not resolve | DNS → resolver → hosted zone → application configuration |
| TCP timeout | Route → SG → NACL → endpoint → Flow Logs |
| TCP connection refused | Listener → process → service configuration |
| HTTP 403 | Authentication/authorization → application → upstream |
| HTTP 502/503 | Load balancer → target health → application listener |
| Database timeout | DNS → route → SG → NACL → PostgreSQL listener |
| S3 access failure | Endpoint/network path → IAM → endpoint/resource policy |
| Intermittent connectivity | DNS → load balancing → capacity → ephemeral ports → network dependencies |
| Cross-VPC failure | Routing → peering/TGW → SG → NACL → return route |
| Private subnet cannot reach internet | Route → NAT Gateway → NAT subnet route → IGW → egress rules |

## Common Mistakes

### Opening Everything in the Security Group

A common response to a connectivity failure is:

```text
0.0.0.0/0
```

on the required port.

This can prove that the Security Group was involved, but it is poor production practice.

Prefer:

```text
Source Security Group
        |
        v
Destination Security Group
```

or the smallest appropriate CIDR.

### Ignoring Return Traffic

Engineers often verify only:

```text
Client -> Server
```

but TCP requires bidirectional communication.

Always reason about:

```text
Client -> Server
Server -> Client
```

This is especially important with stateless Network ACLs and asymmetric routing.

### Checking Only Security Groups

Security Groups are only one layer.

A valid Security Group configuration cannot compensate for:

- Missing routes.
- Incorrect DNS.
- Network ACL denial.
- Broken endpoint configuration.
- Application listeners not running.

### Assuming ACCEPT Means Success

A Flow Log `ACCEPT` record indicates that traffic was accepted at the relevant flow-log observation point.

It does not prove:

- The application accepted the request.
- The destination process was listening.
- TLS succeeded.
- Authentication succeeded.
- The application returned a successful response.

### Changing Multiple Resources at Once

Changing:

- route tables,
- Security Groups,
- Network ACLs,
- DNS,
- and application configuration

simultaneously destroys useful diagnostic information.

Make controlled changes and validate each one.

## Production Troubleshooting Runbook

Use this checklist during incidents.

### Identify

- [ ] Identify source workload.
- [ ] Identify source IP.
- [ ] Identify destination workload.
- [ ] Identify destination IP.
- [ ] Identify protocol.
- [ ] Identify destination port.
- [ ] Record exact timestamp.
- [ ] Capture the exact application error.

### Validate DNS

- [ ] Resolve the hostname.
- [ ] Verify the returned address.
- [ ] Confirm private/public expectations.
- [ ] Check DNS configuration.

### Validate Routing

- [ ] Identify source subnet.
- [ ] Identify source route table.
- [ ] Find the matching route.
- [ ] Verify route target.
- [ ] Verify return route where required.

### Validate Security

- [ ] Inspect source Security Group.
- [ ] Inspect destination Security Group.
- [ ] Inspect Network ACLs.
- [ ] Check endpoint policies where applicable.
- [ ] Check Kubernetes NetworkPolicy where applicable.

### Validate Connectivity

- [ ] Test TCP connectivity.
- [ ] Test TLS where applicable.
- [ ] Test application protocol.
- [ ] Inspect Flow Logs.
- [ ] Use Reachability Analyzer where useful.

### Validate the Service

- [ ] Confirm destination process is running.
- [ ] Confirm listener is bound.
- [ ] Confirm service port.
- [ ] Check application logs.
- [ ] Check service-level health.
- [ ] Check resource exhaustion.

### Document

- [ ] Record root cause.
- [ ] Record evidence.
- [ ] Record configuration change.
- [ ] Record remediation.
- [ ] Identify preventive monitoring or automation.

## Security Considerations

Troubleshooting should never become an excuse to permanently weaken security controls.

Prefer:

- Temporary diagnostic rules with explicit expiration.
- Narrow source ranges.
- Security Group references.
- Controlled test instances.
- VPC Reachability Analyzer.
- Flow Logs.
- AWS CloudTrail for configuration changes.
- Infrastructure as Code for repeatable remediation.

Avoid:

- Permanent `0.0.0.0/0` access.
- Disabling Network ACLs without understanding their purpose.
- Removing endpoint restrictions.
- Exposing private services publicly.
- Sharing production credentials during troubleshooting.
- Making undocumented console changes.

## Scalability Considerations

A troubleshooting methodology must work as systems become more complex.

In a small VPC:

```text
EC2 -> PostgreSQL
```

manual inspection may be sufficient.

In a larger environment:

```text
Users
 |
 v
CloudFront
 |
 v
ALB
 |
 v
EKS
 |
 +----> Redis
 |
 +----> PostgreSQL
 |
 +----> Kafka
 |
 +----> S3
 |
 +----> External APIs
```

manual reasoning becomes harder.

At scale, invest in:

- Centralized Flow Logs.
- Standardized resource tagging.
- Infrastructure as Code.
- Automated configuration validation.
- Reachability analysis.
- Centralized observability.
- Consistent Security Group naming.
- Documented network diagrams.
- Automated quota monitoring.
- Repeatable incident runbooks.

## Monitoring and Prevention

Good troubleshooting is reactive; good engineering reduces the frequency of incidents.

Monitor:

| Signal | Why It Matters |
|---|---|
| Rejected Flow Logs | Detect blocked traffic |
| NAT Gateway metrics | Detect abnormal egress patterns |
| Load balancer target health | Detect backend connectivity issues |
| DNS failures | Detect service discovery problems |
| Network interface capacity | Detect scaling constraints |
| Subnet IP utilization | Detect address exhaustion |
| AWS service quotas | Detect impending capacity limits |
| CloudTrail changes | Detect unexpected configuration changes |

The goal is to detect network degradation before application failures become widespread.

## Interview Traps

### "Security Groups Are Stateless"

Incorrect.

Security Groups are **stateful**.

Network ACLs are **stateless**.

### "If the Security Group Allows It, Traffic Works"

Incorrect.

Routing, Network ACLs, DNS, endpoint configuration, and the destination service can still prevent successful communication.

### "Network ACLs Are Only Inbound"

Incorrect.

Network ACLs apply to both inbound and outbound traffic.

Because they are stateless, return traffic must be explicitly permitted where required.

### "Ping Tests Database Connectivity"

Incorrect.

ICMP success does not prove TCP connectivity to PostgreSQL on port `5432`.

Test the actual protocol and port.

### "Flow Logs Capture Application Payloads"

Incorrect.

VPC Flow Logs provide network flow metadata rather than application payload inspection.

## Root Cause Classification

After resolving an incident, classify the root cause.

| Category | Example |
|---|---|
| DNS | Incorrect private DNS record |
| Routing | Missing route |
| Security Group | Missing inbound rule |
| Network ACL | Return traffic blocked |
| Endpoint | Incorrect endpoint configuration |
| IAM | Network path works but authorization fails |
| Application | Service not listening |
| Capacity | Subnet or quota exhaustion |
| Deployment | Infrastructure changed unexpectedly |
| Human error | Manual configuration mistake |

This classification helps identify recurring failure patterns and informs future automation.

## Key Takeaways

- **Trace traffic layer by layer**: DNS, routing, Security Groups, Network ACLs, interfaces, network components, and finally the destination application.
- **Troubleshoot from evidence, not assumptions**: use exact source/destination addresses, ports, Flow Logs, connectivity tests, and AWS networking diagnostics.
- **Always reason about both directions**: TCP is bidirectional, and stateless Network ACLs require explicit consideration of return traffic.
- **Do not weaken security to prove connectivity**: use narrow temporary changes, Reachability Analyzer, Flow Logs, and controlled tests instead of broad permanent access.
- **Turn incidents into operational improvements**: document root causes and automate monitoring, validation, quota tracking, and repeatable remediation.