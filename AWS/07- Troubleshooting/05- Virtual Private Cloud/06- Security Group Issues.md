# 06- Security Group Issues

## Overview

Security Groups (SGs) are stateful virtual firewalls attached to AWS network interfaces. They control inbound and outbound traffic for resources such as EC2 instances, ECS tasks, load balancers, and other ENI-backed workloads.

Security Group failures are among the most common causes of application connectivity problems inside a VPC. A backend service may be healthy, the route table may be correct, and the destination may be reachable, yet the connection can still fail because the relevant Security Group does not allow the required traffic.

The important troubleshooting distinction is:

```text
Routing determines:
"Can traffic find a path?"

Security Groups determine:
"Is this traffic allowed?"

Application configuration determines:
"Will the service actually accept and process it?"
```

A useful mental model is:

```text
Application
    |
    v
Network Interface
    |
    +--> Route Table
    |       |
    |       v
    |    Network Path
    |
    +--> Security Group
            |
            v
        Allowed / Denied
```

Security Groups should therefore be investigated as one layer of a larger network path rather than as an isolated configuration.

## Security Group Architecture

Security Groups are attached to network interfaces rather than directly to individual applications.

For an EC2 instance:

```text
EC2 Instance
     |
     v
Elastic Network Interface
     |
     +--> Security Group A
     |
     +--> Security Group B
```

Multiple Security Groups can be associated with the same network interface.

The effective policy is the union of the rules from all associated Security Groups.

For example:

```text
SG-A:
TCP 443 from 10.0.10.0/24

SG-B:
TCP 5432 from sg-xxxxxxxx
```

The network interface can receive traffic permitted by either rule set.

A common troubleshooting mistake is inspecting only one Security Group while the workload has several attached.

## Stateful Behavior

Security Groups are stateful.

If an inbound connection is permitted, the return traffic for that connection is automatically allowed without requiring a separate outbound rule specifically for the response.

Conceptually:

```text
Client
  |
  | TCP SYN
  v
Server
  |
  | TCP SYN-ACK
  v
Client
```

If the inbound connection is permitted by the destination Security Group, the return traffic is tracked as part of the established connection.

This differs from Network ACLs, which are stateless.

| Property | Security Group | Network ACL |
|---|---|---|
| State | Stateful | Stateless |
| Attached to | ENI | Subnet |
| Rules | Allow only | Allow and deny |
| Rule evaluation | Union of applicable allows | Ordered rules |
| Return traffic | Automatically tracked | Must be explicitly permitted |
| Typical use | Workload-level access control | Subnet-level boundary control |

## Inbound Rules

Inbound rules define which traffic can reach a resource.

Example:

```text
Protocol    Port    Source
TCP         443     0.0.0.0/0
TCP         8000    sg-frontend
TCP         5432    sg-app
```

For a production API:

```text
Internet
   |
   v
Application Load Balancer
   |
   v
EC2 / ECS
```

The application workload should generally not expose its application port directly to the entire internet.

Instead:

```text
Internet
   |
   | TCP 443
   v
ALB Security Group
   |
   | TCP 8000
   v
Application Security Group
```

The application Security Group can allow traffic specifically from the load balancer Security Group.

## Outbound Rules

Outbound rules control traffic initiated from the resource.

A default Security Group commonly allows all outbound traffic:

```text
0.0.0.0/0
```

This is convenient but may be broader than required for security-sensitive systems.

For example, an application might need outbound:

```text
TCP 443 -> Internet
TCP 5432 -> PostgreSQL
TCP 6379 -> Redis
```

A restrictive egress policy should be designed around actual dependencies rather than blindly allowing or denying everything.

## Security Group References

One of the most useful production patterns is referencing another Security Group instead of using IP addresses.

Example:

```text
sg-alb
    |
    | TCP 8000
    v
sg-app
```

The application Security Group can allow:

```text
Source: sg-alb
Port: 8000
Protocol: TCP
```

This is preferable to:

```text
Source: 10.0.10.0/24
```

when the real trust relationship is:

```text
Load Balancer -> Application
```

The relationship remains valid even when workload private IP addresses change.

## Security Group References for Databases

A typical backend architecture is:

```text
Internet
    |
    v
ALB
    |
    v
Application
    |
    v
PostgreSQL
```

Security Groups can represent the trust boundaries:

```text
sg-alb
  |
  | TCP 8000
  v
sg-app
  |
  | TCP 5432
  v
sg-db
```

The database should not generally use:

```text
0.0.0.0/0 -> TCP 5432
```

Instead:

```text
Source: sg-app
Port: 5432
```

This expresses the architecture directly:

> Only workloads belonging to the application Security Group may connect to PostgreSQL.

## Common Connectivity Symptoms

Security Group problems can produce several symptoms:

| Symptom | Possible SG Cause |
|---|---|
| Connection timeout | Traffic blocked by SG/NACL/path |
| Connection refused | Service reachable but application is not listening |
| HTTPS works but HTTP fails | Port-specific rule |
| One service can connect but another cannot | Different SG |
| Application cannot reach PostgreSQL | DB SG missing application source |
| Application cannot reach Redis | Redis SG missing application source |
| Load balancer returns 502 | ALB-to-target SG or application issue |
| SSH unavailable | Port 22 not allowed |
| Health checks fail | Health-check port not allowed |

Do not assume every timeout is a Security Group problem. First establish whether the packet can reach the destination and whether the destination service is listening.

## Identify the Security Groups

Start with the affected resource.

For EC2:

```bash
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[].Instances[].{
    InstanceId:InstanceId,
    PrivateIp:PrivateIpAddress,
    SubnetId:SubnetId,
    SecurityGroups:SecurityGroups
  }'
```

For a specific network interface:

```bash
aws ec2 describe-network-interfaces \
  --network-interface-ids eni-0123456789abcdef0 \
  --query 'NetworkInterfaces[].{
    ENI:NetworkInterfaceId,
    PrivateIp:PrivateIpAddress,
    SubnetId:SubnetId,
    Groups:Groups
  }'
```

The ENI is often the best starting point because it identifies the actual network interface involved in the connection.

## Inspect Security Group Rules

Retrieve a Security Group:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0
```

A more focused query:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0 \
  --query 'SecurityGroups[].{
    GroupId:GroupId,
    GroupName:GroupName,
    Ingress:IpPermissions,
    Egress:IpPermissionsEgress
  }'
```

Verify:

- Protocol.
- Destination port.
- Source.
- IPv4 versus IPv6.
- Referenced Security Group.
- Description and intended purpose.

## Verify the Destination Port

A frequent mistake is validating the wrong port.

Suppose FastAPI runs on:

```text
8000
```

but the Security Group allows:

```text
443
```

The Security Group is behaving correctly; the configuration is simply inconsistent with the application architecture.

Determine the actual listening port:

```bash
ss -lntp
```

For example:

```text
LISTEN 0 128 0.0.0.0:8000
```

Then compare it with:

```text
Load Balancer target port
Security Group destination port
Container port
Application port
```

All layers must agree.

## Test TCP Connectivity

From the source workload:

```bash
nc -vz 10.0.30.15 5432
```

For HTTPS:

```bash
nc -vz api.internal.example 443
```

Or:

```bash
curl -v --connect-timeout 5 https://api.internal.example
```

Interpret the result carefully.

### Timeout

```text
Connection timed out
```

Potential causes:

- Security Group.
- Network ACL.
- Route.
- Missing NAT.
- Incorrect destination.
- Network path failure.

### Connection Refused

```text
Connection refused
```

Usually indicates that the network path succeeded but the destination rejected the connection because the service is not listening or actively refused it.

This is an important distinction:

```text
Timeout
    -> investigate network path

Refused
    -> investigate destination service
```

## Security Group Rule Direction

For a connection:

```text
Application -> PostgreSQL
```

the relevant rules are:

```text
Application SG:
Outbound TCP 5432 -> PostgreSQL

PostgreSQL SG:
Inbound TCP 5432 <- Application SG
```

Both sides should be considered.

A common mistake is checking only:

```text
DB inbound
```

while forgetting that the application's outbound policy may also be restricted.

For a restrictive architecture, validate both directions.

## Application Load Balancer Troubleshooting

A common architecture is:

```mermaid
flowchart LR
    Client[Client] --> ALB[Application Load Balancer]
    ALB --> App[Application]
    App --> DB[(PostgreSQL)]
```

Use separate Security Groups:

```text
sg-alb
sg-app
sg-db
```

Recommended relationship:

```text
Internet
   |
   | 443
   v
sg-alb
   |
   | 8000
   v
sg-app
   |
   | 5432
   v
sg-db
```

The application Security Group should not need to trust the entire internet merely because the ALB is public.

## ALB 502 and Security Groups

An ALB returning `502 Bad Gateway` does not automatically mean the ALB Security Group is wrong.

Possible causes include:

- ALB cannot connect to target.
- Target Security Group blocks ALB traffic.
- Application is not listening.
- Target port is incorrect.
- Application process is unhealthy.
- Health check configuration is incorrect.

Troubleshoot:

```text
Client
  |
  v
ALB listener
  |
  v
Target group
  |
  v
Target ENI
  |
  v
Target Security Group
  |
  v
Application port
```

The Security Group must permit the ALB-to-target connection on the target port.

## ECS Security Group Issues

ECS tasks using `awsvpc` networking have their own ENIs and Security Groups.

Therefore, inspect the task network interface rather than assuming the EC2 host's Security Group controls the entire connection.

The path may be:

```text
ALB
 |
 v
Task ENI
 |
 v
Task Security Group
 |
 v
Container
```

A common mistake is configuring the ECS container port correctly but forgetting that the task Security Group must allow traffic from the ALB Security Group.

## EKS Security Group Issues

For EKS, networking can involve:

- Pod ENIs.
- Node ENIs.
- Security Groups for Pods.
- Cluster Security Groups.
- Node Security Groups.

The exact path depends on the networking model.

When troubleshooting, identify the actual source and destination ENIs and determine which Security Groups apply.

Do not assume:

```text
Pod -> Node Security Group
```

is always the complete security boundary.

## PostgreSQL Connectivity

For PostgreSQL:

```text
Application
    |
    | TCP 5432
    v
PostgreSQL
```

A common production configuration is:

```text
sg-app
   |
   | TCP 5432
   v
sg-db
```

Database Security Group:

```text
Inbound:
TCP 5432
Source: sg-app
```

Application Security Group:

```text
Outbound:
TCP 5432
Destination: database
```

Then test:

```bash
nc -vz postgres.internal.example 5432
```

If TCP connectivity works but the application still fails, investigate:

- PostgreSQL authentication.
- Database name.
- Credentials.
- SSL requirements.
- Connection limits.
- Application connection pool.
- DNS.

Do not continue changing Security Groups after the TCP layer has been proven healthy.

## Redis Connectivity

For Redis:

```text
Application
    |
    | TCP 6379
    v
Redis
```

Use a dedicated Redis Security Group:

```text
sg-app
   |
   | 6379
   v
sg-redis
```

Avoid:

```text
6379 from 0.0.0.0/0
```

A publicly reachable Redis service is a serious security risk.

## SSH Connectivity

SSH failures are commonly caused by:

```text
TCP 22 not allowed
```

A safer pattern is to avoid exposing SSH directly to the public internet when possible.

Instead consider:

- AWS Systems Manager Session Manager.
- Bastion hosts with restricted source addresses.
- VPN or private connectivity.

If SSH is required:

```text
TCP 22
Source: trusted administrative network
```

is preferable to:

```text
TCP 22
Source: 0.0.0.0/0
```

## Security Group and NACL Interaction

Security Groups and Network ACLs operate at different layers.

For inbound traffic:

```text
Client
  |
  v
Network ACL
  |
  v
Security Group
  |
  v
ENI
  |
  v
Application
```

A permissive Security Group cannot override a restrictive NACL.

Similarly, changing a Security Group will not fix a route-table failure.

When debugging, evaluate the complete path:

```text
DNS
  |
Route
  |
NACL
  |
Security Group
  |
Application
```

## VPC Flow Logs

VPC Flow Logs can provide evidence about accepted or rejected traffic.

A simplified record:

```text
srcaddr=10.0.10.15
dstaddr=10.0.20.25
srcport=49152
dstport=5432
protocol=6
action=REJECT
```

A `REJECT` is strong evidence that the traffic was rejected at the network interface or subnet boundary.

However, an `ACCEPT` record does not mean the application successfully processed the request.

You may still have:

```text
ACCEPT
    |
    v
Application not listening
```

or:

```text
ACCEPT
    |
    v
Application error
```

Use Flow Logs together with application and infrastructure telemetry.

## Reachability Analyzer

AWS Reachability Analyzer can help analyze whether a network path is reachable between supported AWS resources.

It can identify problems involving:

- Route tables.
- Security Groups.
- Network ACLs.
- Network interfaces.
- Gateways.

Use it when manual inspection becomes difficult, especially in larger VPCs.

The key benefit is that it evaluates the modeled network path rather than requiring you to infer the entire route manually.

## IPv4 and IPv6 Considerations

A common Security Group mistake is validating only IPv4 rules.

For IPv4:

```text
0.0.0.0/0
```

For IPv6:

```text
::/0
```

An application may behave differently depending on whether DNS returns:

```text
A
```

or:

```text
AAAA
```

If IPv6 connectivity is enabled, inspect IPv6 Security Group rules separately.

Do not assume an IPv4 rule automatically authorizes IPv6 traffic.

## Ephemeral Ports

Clients typically use ephemeral source ports.

For example:

```text
10.0.10.15:49152
    |
    v
10.0.20.25:5432
```

The destination port is:

```text
5432
```

while the source port is dynamically selected.

Security Groups are stateful, so return traffic for an allowed connection is tracked automatically.

Network ACLs are stateless, so custom restrictive NACLs may need to permit the return traffic's ephemeral port range.

This distinction is a common interview and production troubleshooting point.

## Security Group Rule Evaluation

Security Groups do not use traditional first-match rule processing.

If multiple rules allow traffic, the connection is permitted.

For example:

```text
SG-A:
TCP 443 from 10.0.0.0/16

SG-B:
TCP 443 from 0.0.0.0/0
```

The broader rule still permits the connection.

There is no explicit deny rule that can override the allow.

Therefore, when auditing a Security Group configuration, inspect all attached Security Groups.

## Security Group Rule Limits

Security Groups have service quotas for:

- Number of Security Groups per network interface.
- Number of inbound rules.
- Number of outbound rules.
- Other related resources.

Large microservice environments can accumulate excessive rules.

A common design problem is:

```text
Service A
 -> Service B
 -> Service C
 -> Service D
 -> Service E
 ...
```

with hundreds of tightly coupled Security Group rules.

Prefer meaningful trust boundaries and reusable Security Groups rather than generating a unique rule for every individual workload when unnecessary.

## Common Security Group Failure Patterns

| Symptom | Likely Cause | First Check |
|---|---|---|
| EC2 cannot receive SSH | Missing TCP 22 rule | Inbound SG |
| API unavailable | Missing listener port | Inbound SG |
| ALB health checks fail | Target SG blocks ALB | Target SG |
| App cannot reach DB | DB SG missing app source | DB inbound |
| App cannot reach Redis | Redis SG missing app source | Redis inbound |
| Outbound API fails | Egress restriction | Source SG |
| IPv6 works differently | Missing IPv6 rule | SG IPv6 rules |
| One instance works | Different SG association | ENI SGs |
| Connection times out | SG/NACL/routing | Full network path |
| Connection refused | Service not listening | Application |
| Security change has no effect | Wrong SG inspected | ENI association |
| Unexpected access remains | Another SG allows it | All attached SGs |

## Troubleshooting Methodology

Use an evidence-driven sequence.

### Identify the Source

Determine:

```text
Source resource
Source ENI
Source subnet
Source private IP
Source Security Groups
```

### Identify the Destination

Determine:

```text
Destination resource
Destination ENI
Destination IP
Destination port
Destination Security Groups
```

### Identify the Protocol

For example:

```text
TCP 443
TCP 5432
TCP 6379
TCP 8000
UDP 53
```

Do not troubleshoot only by hostname.

### Verify Routing

Confirm that the source can actually route to the destination.

```text
Source
  |
  v
Route Table
  |
  v
Destination
```

### Inspect All Source Security Groups

Do not stop after finding one Security Group.

List every Security Group associated with the source ENI.

### Inspect Destination Inbound Rules

Verify that the destination allows:

```text
Protocol
Port
Source
```

### Inspect Source Outbound Rules

If egress is restricted, verify that the source allows the destination traffic.

### Inspect NACLs

Check both directions because NACLs are stateless.

### Test TCP Connectivity

```bash
nc -vz <destination> <port>
```

### Inspect Flow Logs

Look for:

```text
ACCEPT
REJECT
```

and verify the source, destination, port, and protocol.

### Validate the Application

If TCP connectivity succeeds, investigate the application layer.

For example:

```bash
curl -v http://10.0.20.25:8000/health
```

For PostgreSQL:

```bash
pg_isready -h postgres.internal.example -p 5432
```

## Practical Example: Django to PostgreSQL

Consider:

```text
Django
  |
  | TCP 5432
  v
PostgreSQL
```

Security Groups:

```text
sg-django
sg-postgres
```

Required relationship:

```text
sg-postgres:
Inbound TCP 5432
Source sg-django
```

If the application cannot connect:

```bash
nc -vz postgres.internal.example 5432
```

If the result is:

```text
timed out
```

investigate:

- Django subnet route.
- NACL.
- Django egress.
- PostgreSQL inbound rule.
- PostgreSQL subnet.
- PostgreSQL ENI.

If the result is:

```text
connection refused
```

investigate:

- PostgreSQL process.
- Listening address.
- PostgreSQL port.
- Target IP.
- Database configuration.

The Security Group may already be correct.

## Practical Example: FastAPI Behind an ALB

Architecture:

```text
Internet
   |
   | HTTPS 443
   v
ALB
   |
   | HTTP 8000
   v
FastAPI
```

Security Groups:

```text
sg-alb:
Inbound TCP 443 from approved clients
Outbound TCP 8000 -> sg-app

sg-app:
Inbound TCP 8000 from sg-alb
Outbound as required
```

A common mistake is:

```text
sg-app:
Inbound TCP 8000 from 0.0.0.0/0
```

This bypasses the intended ALB trust boundary.

Prefer:

```text
Source: sg-alb
Port: 8000
```

## Practical Example: Microservices

Suppose:

```text
API
 |
 +--> User Service
 |
 +--> Payment Service
 |
 +--> Inventory Service
```

Avoid designing security rules around every possible IP address.

Prefer explicit trust relationships:

```text
sg-api
  |
  +--> sg-user
  |
  +--> sg-payment
  |
  +--> sg-inventory
```

Each destination Security Group defines which upstream workloads are trusted.

This approach remains stable as instances, containers, and private IPs change.

## Production Best Practices

### Use Security Groups as Trust Boundaries

Model relationships such as:

```text
ALB -> API
API -> Database
API -> Redis
Worker -> Kafka
```

rather than broad CIDR-based access wherever possible.

### Minimize Public Exposure

Avoid:

```text
Database 5432 -> 0.0.0.0/0
Redis 6379 -> 0.0.0.0/0
Internal API 8000 -> 0.0.0.0/0
SSH 22 -> 0.0.0.0/0
```

Use the smallest appropriate source.

### Separate Security Groups by Responsibility

Common groups include:

```text
sg-alb
sg-api
sg-worker
sg-db
sg-redis
sg-bastion
```

This makes architecture and troubleshooting easier.

### Prefer Security Group References

When the relationship is workload-to-workload, prefer:

```text
Source: sg-api
```

over a hardcoded private CIDR where appropriate.

### Manage Rules Through Infrastructure as Code

Use Terraform, CloudFormation, AWS CDK, or equivalent tooling.

Security Group changes should be:

- Reviewable.
- Auditable.
- Reproducible.
- Version-controlled.

### Keep Rule Descriptions Meaningful

For example:

```text
Allow API to PostgreSQL
Allow ALB to application
Allow worker to Redis
```

Avoid descriptions such as:

```text
test
temp
new
fix
```

Meaningful descriptions make future troubleshooting significantly easier.

## Common Mistakes

### Opening Every Port to the Internet

Example:

```text
0.0.0.0/0 -> all TCP
```

This eliminates most of the security value of the Security Group.

Use explicit ports and trusted sources.

### Assuming Security Groups Have Deny Rules

They do not support explicit deny rules.

If access remains possible, another attached Security Group may be allowing it.

### Inspecting Only One Security Group

Multiple Security Groups can be attached to an ENI.

The effective policy includes allowed traffic from all applicable groups.

### Confusing Security Groups With NACLs

Security Groups:

```text
Stateful
ENI-level
Allow rules
```

NACLs:

```text
Stateless
Subnet-level
Allow and deny rules
```

### Allowing Database Access From a CIDR When a SG Reference Is Better

This can create overly broad trust.

Prefer:

```text
Source: sg-app
```

when the intended relationship is application-to-database.

### Forgetting Egress

Restrictive outbound rules can prevent:

- API calls.
- Database connections.
- Redis access.
- Package downloads.
- AWS API calls.

### Testing the Wrong Port

The application might listen on:

```text
8000
```

while the Security Group allows:

```text
8080
```

Always verify the actual listening port.

### Changing Rules Without Recording the Root Cause

Uncontrolled rule changes can create configuration drift and make future troubleshooting harder.

Use IaC and document the intended trust relationship.

## Security Considerations

Security Groups should implement least-privilege network access.

Prefer:

```text
ALB -> API -> Database
```

over:

```text
Internet -> API
Internet -> Database
```

and prefer:

```text
API -> Database
```

over:

```text
Entire VPC -> Database
```

For highly sensitive environments, combine Security Groups with:

- Network ACLs.
- AWS Network Firewall.
- VPC endpoints.
- Private subnets.
- IAM authorization.
- Application-level authentication.
- Encryption in transit.
- VPC Flow Logs.
- Centralized security monitoring.

Network-level authorization should not replace application-level authorization.

## Monitoring and Auditing

Monitor changes to Security Groups as well as traffic behavior.

Useful operational sources include:

- AWS CloudTrail.
- VPC Flow Logs.
- AWS Config.
- Security Hub where applicable.
- Application logs.
- Load balancer access logs.

CloudTrail can help answer:

```text
Who changed the Security Group?
When?
Which rule changed?
What was the previous configuration?
```

This is particularly important when connectivity changes unexpectedly after deployment.

## Production Diagnostic Checklist

```text
[ ] Identify source workload
[ ] Identify source ENI
[ ] Identify source private IP
[ ] Identify all source Security Groups
[ ] Identify destination workload
[ ] Identify destination ENI
[ ] Identify destination port
[ ] Identify protocol
[ ] Verify source route
[ ] Verify source SG egress
[ ] Verify destination SG ingress
[ ] Verify all attached SGs
[ ] Check IPv4 vs IPv6
[ ] Check Network ACLs
[ ] Check VPC Flow Logs
[ ] Test TCP connectivity
[ ] Verify destination service is listening
[ ] Verify application-level behavior
[ ] Check CloudTrail for recent SG changes
[ ] Check infrastructure-as-code state
[ ] Record root cause and remediation
```

## Interview Traps

### "Security Groups Are Attached to Subnets"

Incorrect.

Security Groups are associated with network interfaces.

Network ACLs are associated with subnets.

### "Security Groups Are Stateless"

Incorrect.

Security Groups are stateful.

### "A Security Group Rule Can Explicitly Deny Traffic"

Incorrect.

Security Groups support allow rules. There is no explicit deny rule that overrides an allow.

### "If One Security Group Blocks Traffic, Another Cannot Allow It"

Incorrect.

The effective Security Group policy is the union of applicable allow rules.

### "Security Group Rules Use First Match"

Incorrect.

They are not processed as an ordered first-match ACL.

### "A Database Should Allow the Entire VPC CIDR"

Not necessarily.

If the intended trust boundary is a specific application tier, a Security Group reference is generally more precise.

### "A Timeout Always Means the Security Group Is Wrong"

Incorrect.

Timeouts can result from:

- Routing.
- NACLs.
- NAT.
- DNS.
- Security Groups.
- Application availability.

Always troubleshoot the entire network path.

## Key Takeaways

- **Security Groups are stateful, ENI-level allow controls; their effective policy is the union of rules from all attached Security Groups.**
- **Model workload relationships explicitly with Security Group references**, such as `ALB → API → PostgreSQL`, instead of broad CIDR-based access where possible.
- **Troubleshoot both directions of a connection**: source egress, destination ingress, routing, NACLs, and the destination service itself.
- **A timeout does not prove a Security Group problem**; distinguish routing, security, transport, and application-layer failures using targeted tests and telemetry.
- **Treat Security Group configuration as production infrastructure**: enforce least privilege, manage changes through IaC, audit modifications, and avoid unnecessary public exposure.