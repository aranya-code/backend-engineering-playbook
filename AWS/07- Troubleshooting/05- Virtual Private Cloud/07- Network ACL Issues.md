# 07- Network ACL Issues

## Overview

Network Access Control Lists (NACLs) are subnet-level, stateless network filters used to control traffic entering and leaving an Amazon VPC subnet. They operate alongside Security Groups, route tables, gateways, and application-level controls.

NACL-related failures are particularly easy to misdiagnose because a Security Group can be completely correct while a subnet-level NACL silently blocks the traffic.

The critical distinction is:

```text
Security Group:
"Is this traffic allowed for this network interface?"

Network ACL:
"Is this traffic allowed across this subnet boundary?"

Route Table:
"Where should this traffic go?"

Application:
"Is there a service listening and accepting it?"
```

A useful troubleshooting model is:

```text
Source
  |
  v
Source Subnet NACL
  |
  v
Route Table
  |
  v
Destination Subnet NACL
  |
  v
Destination Security Group
  |
  v
Application
```

The actual packet path can involve additional AWS networking components, but this model is useful for isolating the major control points.

## What Is a Network ACL?

A Network ACL is a stateless set of rules associated with a VPC subnet.

Every subnet is associated with exactly one NACL at a time. A single NACL can be associated with multiple subnets.

The default NACL generally allows inbound and outbound IPv4 traffic, and it can be modified.

A custom NACL can be used to create an additional subnet-level security boundary.

Typical use cases include:

- Explicit subnet-level allow/deny controls.
- Defense-in-depth.
- Blocking known address ranges.
- Enforcing organizational network boundaries.
- Restricting traffic between subnet classes.
- Supporting compliance requirements.

NACLs should generally not be used as the primary mechanism for application-to-application authorization. Security Groups are usually better suited to workload-level relationships.

## Stateless Behavior

NACLs are **stateless**.

This is the most important operational property to understand.

If a client initiates:

```text
10.0.10.20:49152
        |
        | TCP SYN
        v
10.0.20.30:5432
```

and the server responds:

```text
10.0.20.30:5432
        |
        | TCP SYN-ACK
        v
10.0.10.20:49152
```

the return traffic is treated as a separate packet flow.

A NACL therefore needs rules that permit both directions.

Conceptually:

```text
Outbound:
10.0.10.20:49152
        |
        v
10.0.20.30:5432

Inbound:
10.0.20.30:5432
        |
        v
10.0.10.20:49152
```

This is fundamentally different from a Security Group.

| Property | NACL | Security Group |
|---|---|---|
| Scope | Subnet | Network interface |
| State | Stateless | Stateful |
| Rules | Allow and deny | Allow only |
| Rule ordering | Lowest rule number first | No first-match ordering |
| Return traffic | Must be explicitly permitted | Automatically tracked |
| Typical role | Subnet boundary | Workload boundary |

## NACL Rule Evaluation

NACL rules are evaluated in ascending rule-number order.

For example:

```text
100  ALLOW TCP 443 from 0.0.0.0/0
110  DENY  TCP 443 from 203.0.113.0/24
*
```

The traffic from `203.0.113.0/24` matches rule `100` first and is therefore allowed.

The later deny rule does not override it.

This means:

> NACL rule ordering matters.

A common mistake is writing a specific deny rule after a broad allow rule and assuming the deny takes precedence.

Instead, put the more specific rule first:

```text
90   DENY  TCP 443 from 203.0.113.0/24
100  ALLOW TCP 443 from 0.0.0.0/0
```

The lower-numbered rule is evaluated first.

## The Implicit Deny

If no rule matches the traffic, the traffic is denied.

Conceptually:

```text
Rule 100 -> no match
Rule 110 -> no match
Rule 120 -> no match
Rule *   -> DENY
```

This is why custom NACLs can unexpectedly break applications when they contain only a few explicit allow rules.

When troubleshooting a NACL, do not ask only:

> "Is there a deny rule?"

Also ask:

> "Is there an allow rule that actually matches this packet?"

## NACL Architecture

Consider:

```text
Public Subnet
    |
    v
NACL-Public
    |
    v
Internet Gateway

Private Subnet
    |
    v
NACL-Private
    |
    v
NAT Gateway
```

A packet crossing from one subnet to another can encounter NACL processing at the relevant subnet boundaries.

For example:

```mermaid
flowchart LR
    Client[Client] --> PublicNACL[Public Subnet NACL]
    PublicNACL --> ALB[Application Load Balancer]
    ALB --> PrivateNACL[Private Subnet NACL]
    PrivateNACL --> App[Application]
    App --> DBNACL[Database Subnet NACL]
    DBNACL --> DB[(PostgreSQL)]
```

Every subnet boundary should therefore be considered independently during troubleshooting.

## Inbound and Outbound Rules

A NACL has separate:

- Inbound rules.
- Outbound rules.

For a connection:

```text
Application Subnet
        |
        | TCP 5432
        v
Database Subnet
```

the application subnet's outbound NACL must permit the outbound traffic.

The database subnet's inbound NACL must permit the incoming traffic.

For the response:

```text
Database Subnet
        |
        | TCP ephemeral port
        v
Application Subnet
```

the database subnet's outbound NACL must permit the response.

The application subnet's inbound NACL must permit that response.

This creates a four-rule-direction problem that is frequently overlooked.

## Ephemeral Ports

Ephemeral ports are one of the most common sources of NACL connectivity failures.

Suppose:

```text
Client:
10.0.10.20:49152

Server:
10.0.20.30:5432
```

The initial connection is:

```text
10.0.10.20:49152
        ->
10.0.20.30:5432
```

The server response uses:

```text
10.0.20.30:5432
        ->
10.0.10.20:49152
```

The client-side ephemeral port therefore becomes the destination port of the return traffic.

If the NACL allows only:

```text
TCP 5432
```

it may allow the initial request but block the response.

This can manifest as:

```text
Connection timeout
```

even though the Security Groups appear correct.

## Typical Ephemeral Port Configuration

The exact ephemeral port range depends on the operating system and workload.

For modern Linux systems, a commonly used range is:

```text
32768-60999
```

but the actual range should be verified rather than assumed.

Check a Linux host with:

```bash
cat /proc/sys/net/ipv4/ip_local_port_range
```

Example:

```text
32768 60999
```

A NACL requiring explicit ephemeral-port rules should be designed around the actual source workloads and their port behavior.

Avoid blindly copying an assumed range into every environment.

## Example: Application to PostgreSQL

Architecture:

```text
Application
10.0.10.20
    |
    | TCP 5432
    v
PostgreSQL
10.0.20.30
```

Assume the application uses:

```text
Source port: 49152
Destination port: 5432
```

The NACL requirements may look conceptually like:

```text
Application subnet outbound:
TCP 5432 -> database subnet

Database subnet inbound:
TCP 5432 <- application subnet

Database subnet outbound:
TCP ephemeral ports -> application subnet

Application subnet inbound:
TCP ephemeral ports <- database subnet
```

The Security Groups must independently allow the connection.

This is why a NACL change can break a previously healthy database connection even though no Security Group changed.

## NACL Troubleshooting Flow

A reliable troubleshooting process should move from the network path toward the application.

```mermaid
flowchart TD
    Start[Connectivity Failure] --> Source[Identify Source ENI/Subnet]
    Source --> Destination[Identify Destination ENI/Subnet]
    Destination --> Protocol[Identify Protocol and Ports]
    Protocol --> Route[Verify Route Tables]
    Route --> SourceNACL[Check Source Subnet Outbound NACL]
    SourceNACL --> DestNACL[Check Destination Subnet Inbound NACL]
    DestNACL --> ReturnNACL[Check Return Traffic NACL Rules]
    ReturnNACL --> SG[Check Security Groups]
    SG --> FlowLogs[Inspect VPC Flow Logs]
    FlowLogs --> Reachability[Use Reachability Analyzer]
    Reachability --> App[Verify Application]
```

Do not immediately modify rules.

First determine exactly which packet is failing.

## Identify the Subnets

Start by identifying the source and destination resources.

For an EC2 instance:

```bash
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[].Instances[].{
    InstanceId:InstanceId,
    PrivateIp:PrivateIpAddress,
    SubnetId:SubnetId,
    VpcId:VpcId
  }'
```

Then determine the NACL associated with the subnet.

```bash
aws ec2 describe-network-acls \
  --filters Name=association.subnet-id,Values=subnet-0123456789abcdef0
```

This prevents a common mistake:

> Inspecting the wrong NACL because the engineer assumed the resource's Security Group represented the subnet's network policy.

## Inspect NACL Rules

Retrieve a specific NACL:

```bash
aws ec2 describe-network-acls \
  --network-acl-ids acl-0123456789abcdef0
```

A useful query:

```bash
aws ec2 describe-network-acls \
  --network-acl-ids acl-0123456789abcdef0 \
  --query 'NetworkAcls[].Entries[].{
    RuleNumber:RuleNumber,
    Protocol:Protocol,
    Action:RuleAction,
    Egress:Egress,
    Cidr:CidrBlock,
    Ipv6Cidr:Ipv6CidrBlock,
    PortRange:PortRange
  }'
```

Inspect:

- Rule number.
- Direction.
- Protocol.
- Port range.
- Source/destination CIDR.
- Action.
- IPv4 versus IPv6.

## Verify Rule Ordering

Suppose the NACL contains:

```text
100  ALLOW TCP 443 0.0.0.0/0
110  DENY  TCP 443 203.0.113.0/24
```

The deny rule is ineffective for matching traffic from `203.0.113.0/24`.

Correct ordering:

```text
90   DENY  TCP 443 203.0.113.0/24
100  ALLOW TCP 443 0.0.0.0/0
```

Always reason about the first matching rule.

## Check Both Directions

For every connection, build a packet matrix.

Example:

| Direction | Source | Destination | Protocol | Port |
|---|---|---|---|---:|
| Request | App subnet | DB subnet | TCP | 5432 |
| Response | DB subnet | App subnet | TCP | Ephemeral |
| Request | Client subnet | API subnet | TCP | 443 |
| Response | API subnet | Client subnet | TCP | Ephemeral |

Then map each row to:

- Route table.
- Source NACL.
- Destination NACL.
- Security Group.

This is much more reliable than simply searching for a rule containing the server port.

## Network ACL and Security Group Interaction

A successful connection generally requires both controls to permit the relevant traffic.

Conceptually:

```text
Packet
  |
  +--> Route valid?
  |
  +--> Source NACL allows?
  |
  +--> Destination NACL allows?
  |
  +--> Destination SG allows?
  |
  +--> Application listening?
```

A Security Group cannot override a NACL deny.

Likewise, allowing traffic in a NACL does not override a Security Group restriction.

The controls operate at different layers.

## Network ACL and Route Table Interaction

A NACL cannot create a route.

For example, if an application needs to reach the internet:

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
```

The route must exist before NACL rules become relevant to successful forwarding.

For example:

```text
0.0.0.0/0 -> NAT Gateway
```

If the route is missing:

```text
NACL ALLOW
```

does not make the destination reachable.

This is a common troubleshooting trap.

## VPC Flow Logs

VPC Flow Logs are valuable for diagnosing NACL-related failures.

A flow record may contain:

```text
srcaddr
dstaddr
srcport
dstport
protocol
action
```

Example:

```text
srcaddr=10.0.10.20
dstaddr=10.0.20.30
srcport=49152
dstport=5432
protocol=6
action=REJECT
```

This indicates that the traffic was rejected at the network layer.

However, flow logs should be interpreted carefully.

An `ACCEPT` record means the traffic was accepted by the relevant network controls captured by Flow Logs. It does not prove that:

- The application was listening.
- The application accepted the request.
- Authentication succeeded.
- The database query succeeded.

Use flow logs as network evidence, not application-level proof.

## Filter Flow Logs for a Connection

When flow logs are delivered to CloudWatch Logs or another destination, filter around the exact:

```text
Source IP
Destination IP
Source port
Destination port
Protocol
Time window
```

For example:

```text
10.0.10.20 -> 10.0.20.30:5432
```

A useful troubleshooting sequence is:

```text
Request flow:
10.0.10.20:49152 -> 10.0.20.30:5432

Response flow:
10.0.20.30:5432 -> 10.0.10.20:49152
```

If the request is accepted but the response is rejected, inspect the reverse-direction NACL rules.

## Reachability Analyzer

AWS Reachability Analyzer can help determine whether supported AWS resources have a valid network path.

It can identify problems involving:

- Route tables.
- Security Groups.
- Network ACLs.
- Network interfaces.
- Gateways.

This is particularly useful when a VPC contains many subnets and routing components.

Use it to validate the modeled path instead of manually reconstructing every component.

## Common NACL Failure Patterns

| Symptom | Likely NACL Cause |
|---|---|
| Connection timeout | Missing allow rule |
| Request reaches server but response fails | Missing ephemeral-port rule |
| Only one subnet cannot connect | Wrong subnet NACL |
| HTTPS works but database fails | Port-specific NACL issue |
| One direction works | Stateless return path missing |
| Newly created subnet cannot communicate | Custom NACL association |
| Specific IP range cannot connect | CIDR deny or missing allow |
| IPv4 works but IPv6 fails | Missing IPv6 NACL rule |
| Rule appears correct but traffic denied | Earlier rule matches |
| Security Groups look correct | NACL may still block traffic |

## Custom NACL Design

Custom NACLs should be introduced deliberately.

A common pattern is:

```text
Public NACL
    |
    +--> Internet-facing workloads

Private Application NACL
    |
    +--> Backend workloads

Database NACL
    |
    +--> Databases
```

The exact design depends on the organization's security model.

Do not create highly restrictive NACLs simply because "more restrictions are more secure."

A poorly designed NACL can create:

- Operational complexity.
- Difficult troubleshooting.
- Application outages.
- Ephemeral-port failures.
- Deployment failures.
- Unexpected connectivity differences between subnets.

Security controls should be proportionate to the threat model.

## When NACLs Are Appropriate

NACLs are useful when you need subnet-level controls.

Examples:

- Blocking a known malicious CIDR.
- Establishing a subnet-level deny boundary.
- Implementing defense in depth.
- Meeting organizational network-control requirements.
- Controlling traffic between broad subnet classes.

Security Groups are generally preferable for workload-specific relationships such as:

```text
ALB -> API
API -> PostgreSQL
API -> Redis
Worker -> Kafka
```

Use the right control for the right scope.

## Common Mistakes

### Treating NACLs as Stateful

Incorrect assumption:

```text
Inbound allowed
    +
Return traffic automatically allowed
```

NACLs are stateless.

The return path requires its own matching rule.

### Allowing Only the Destination Port

For:

```text
Client:49152 -> Server:5432
```

allowing TCP `5432` alone may not be sufficient for the reverse traffic.

The response is sent toward the client's ephemeral port.

### Putting a Deny After a Broad Allow

Incorrect:

```text
100 ALLOW TCP 443 0.0.0.0/0
110 DENY  TCP 443 203.0.113.0/24
```

The deny will not be reached for matching traffic.

Put the deny before the broad allow.

### Checking Only the Destination NACL

The source subnet's outbound NACL may block the request.

The destination subnet's inbound NACL may block it.

The reverse direction can also fail.

Inspect all relevant directions.

### Assuming Security Groups Override NACLs

They do not.

A NACL deny can block traffic even when Security Groups allow it.

### Using NACLs for Every Application Rule

This creates unnecessary subnet-level coupling.

Application-specific trust relationships are usually easier to express with Security Groups.

### Forgetting IPv6

IPv4:

```text
0.0.0.0/0
```

IPv6:

```text
::/0
```

IPv6 traffic requires appropriate IPv6 rules.

### Modifying Rules Without IaC

Manual changes can create configuration drift.

Production NACL configuration should preferably be managed using:

- Terraform.
- CloudFormation.
- AWS CDK.
- Another approved infrastructure-as-code system.

## Practical Example: API to PostgreSQL

Suppose:

```text
API subnet:
10.0.10.0/24

DB subnet:
10.0.20.0/24
```

The API connects to:

```text
10.0.20.30:5432
```

The client chooses:

```text
49152
```

The packet flow becomes:

```text
10.0.10.20:49152
       |
       | TCP 5432
       v
10.0.20.30:5432
       |
       | TCP 49152
       v
10.0.10.20:49152
```

NACL validation:

```text
API subnet outbound:
ALLOW TCP 5432 -> 10.0.20.0/24

DB subnet inbound:
ALLOW TCP 5432 <- 10.0.10.0/24

DB subnet outbound:
ALLOW TCP ephemeral -> 10.0.10.0/24

API subnet inbound:
ALLOW TCP ephemeral <- 10.0.20.0/24
```

Security Groups then independently need to permit the application-to-database connection.

## Practical Example: Public HTTPS

Architecture:

```text
Internet
   |
   v
Public Subnet
   |
   v
ALB
   |
   v
Private Application Subnet
```

For HTTPS:

```text
Client ephemeral port
        |
        | TCP 443
        v
ALB
        |
        | TCP ephemeral
        v
Client
```

The public subnet NACL must account for both directions if it is restrictive.

A simplistic rule such as:

```text
Inbound TCP 443 ALLOW
```

does not automatically solve all return-traffic requirements.

The exact rules should be derived from the source and destination port behavior.

## Practical Example: NAT Gateway

For a private application accessing the internet:

```text
Private Application
        |
        v
Private Subnet NACL
        |
        v
Route Table
        |
        v
NAT Gateway
        |
        v
Public Subnet NACL
        |
        v
Internet Gateway
        |
        v
Internet
```

A restrictive NACL can break this flow in either direction.

For example:

```text
Application -> external HTTPS
```

requires:

```text
Outbound TCP 443
```

while the response returns toward the NAT-translated connection and may use an ephemeral destination port.

NAT troubleshooting therefore requires inspecting both subnet NACLs, not just the NAT Gateway itself.

## Practical Example: Microservices

Consider:

```text
API subnet
Worker subnet
Database subnet
Redis subnet
```

with:

```text
API -> Database
Worker -> Database
API -> Redis
Worker -> Redis
```

If NACLs are used to enforce subnet boundaries, document the intended traffic matrix.

| Source | Destination | Protocol | Port |
|---|---|---|---:|
| API subnet | DB subnet | TCP | 5432 |
| Worker subnet | DB subnet | TCP | 5432 |
| API subnet | Redis subnet | TCP | 6379 |
| Worker subnet | Redis subnet | TCP | 6379 |

Then explicitly account for the return traffic.

Without a traffic matrix, NACL rules quickly become difficult to reason about.

## Security Considerations

NACLs provide a useful defense-in-depth layer but should not be treated as the only security mechanism.

Combine them appropriately with:

- Security Groups.
- IAM.
- Private subnets.
- VPC endpoints.
- Network Firewall where required.
- Encryption in transit.
- Application authentication and authorization.
- VPC Flow Logs.
- CloudTrail.
- AWS Config.
- Centralized security monitoring.

Avoid broad rules such as:

```text
ALLOW ALL
0.0.0.0/0
```

unless the network design explicitly requires them.

At the same time, overly restrictive NACLs can become an availability risk.

Security and reliability must be designed together.

## Scalability Considerations

Large environments can accumulate complex NACL configurations.

Problems include:

- Many subnet-specific rules.
- Large CIDR allowlists.
- Frequent manual exceptions.
- Difficult rule-number management.
- Different policies across similar environments.
- Configuration drift.

Prefer predictable subnet classes and reusable policies.

For example:

```text
Public
Private Application
Private Data
```

can be easier to manage than hundreds of independently customized subnet policies.

Use infrastructure-as-code and automated validation to ensure that NACL changes do not unintentionally break required traffic paths.

## High Availability Considerations

NACL configuration should be consistent across subnets that represent the same application tier.

For example:

```text
Application-AZ1
Application-AZ2
Application-AZ3
```

should generally have equivalent network policy when they serve the same workload role.

An inconsistent NACL can create an especially difficult failure:

```text
Request -> AZ1 -> works
Request -> AZ2 -> timeout
Request -> AZ3 -> works
```

The application may appear intermittently unhealthy even though the underlying service is correctly deployed.

When troubleshooting intermittent connectivity, compare the subnet and NACL associated with each Availability Zone.

## Monitoring and Auditing

Monitor both traffic and configuration changes.

Useful sources include:

- VPC Flow Logs.
- AWS CloudTrail.
- AWS Config.
- CloudWatch.
- Load balancer logs.
- Application logs.
- Network monitoring systems.

CloudTrail is particularly useful for answering:

```text
Who changed the NACL?
When?
Which rule changed?
What was the previous configuration?
```

For production environments, alerting on unexpected network-policy changes can reduce time to detection.

## Production Best Practices

### Prefer Security Groups for Workload Relationships

Use NACLs for subnet-level controls and Security Groups for workload-level controls.

### Keep Rules Minimal

Avoid unnecessary rules.

Every rule increases the cognitive and operational burden of the network configuration.

### Design From a Traffic Matrix

Document:

```text
Source
Destination
Protocol
Port
Direction
```

before implementing restrictive rules.

### Account for Return Traffic

For every allowed flow, explicitly reason about:

```text
Request
Response
```

### Use Rule Numbering Deliberately

Leave gaps where appropriate:

```text
100
110
120
```

This provides room for future rules without immediately renumbering the entire policy.

### Manage NACLs Through IaC

Version-control all production network policy.

### Validate Changes Before Production

Use:

- Staging environments.
- Reachability Analyzer.
- Automated infrastructure validation.
- Controlled deployment pipelines.

### Document Exceptions

If a broad rule is required, document why it exists and what would allow it to be removed.

## Troubleshooting Checklist

```text
[ ] Identify source resource
[ ] Identify source ENI
[ ] Identify source subnet
[ ] Identify destination resource
[ ] Identify destination ENI
[ ] Identify destination subnet
[ ] Identify protocol
[ ] Identify source port
[ ] Identify destination port
[ ] Identify return-traffic port
[ ] Identify NACL associated with each subnet
[ ] Check source subnet outbound rules
[ ] Check destination subnet inbound rules
[ ] Check destination subnet outbound rules
[ ] Check source subnet inbound rules
[ ] Check NACL rule ordering
[ ] Check implicit deny
[ ] Check IPv4 vs IPv6
[ ] Check route tables
[ ] Check Security Groups
[ ] Inspect VPC Flow Logs
[ ] Use Reachability Analyzer where appropriate
[ ] Verify the destination service is listening
[ ] Check recent CloudTrail changes
[ ] Compare equivalent subnets across Availability Zones
[ ] Record the root cause and remediation
```

## Interview Traps

### "NACLs Are Stateful"

Incorrect.

NACLs are stateless.

### "Security Groups and NACLs Work the Same Way"

Incorrect.

Security Groups are stateful ENI-level controls, while NACLs are stateless subnet-level controls.

### "The Last Matching NACL Rule Wins"

Incorrect.

NACL rules are evaluated from the lowest rule number upward. The first matching rule determines the result.

### "A NACL Deny Can Be Added After an Allow"

Not if the earlier allow matches the same traffic.

Rule ordering is critical.

### "Allowing TCP 5432 Is Enough for PostgreSQL"

Not necessarily.

The return path may use the client's ephemeral port and requires appropriate NACL rules.

### "A Security Group Allow Makes the Traffic Reachable"

Incorrect.

Routing and NACLs can still block the packet.

### "A NACL Can Fix a Missing Route"

Incorrect.

NACLs filter traffic; they do not create routing paths.

### "A Flow Log ACCEPT Means the Application Worked"

Incorrect.

It only provides network-layer evidence. Application-level success must be validated separately.

## Key Takeaways

- **NACLs are stateless subnet-level filters**, so both request and return traffic must be explicitly permitted.
- **Rule ordering matters**: NACLs evaluate rules from the lowest rule number upward and stop at the first match.
- **Ephemeral ports are critical** when designing restrictive NACLs because response traffic does not necessarily use the server's destination port.
- **Troubleshoot the complete path** across routing, both subnet NACL directions, Security Groups, flow logs, and the destination application.
- **Use NACLs for subnet-level defense in depth**, while preferring Security Groups for workload-to-workload access control.