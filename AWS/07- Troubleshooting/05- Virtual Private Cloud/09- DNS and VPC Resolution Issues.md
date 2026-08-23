# 09- DNS and VPC Resolution Issues

## Overview

DNS is a foundational dependency of VPC networking. Applications rarely connect to AWS services, databases, caches, load balancers, or microservices using raw IP addresses. They resolve hostnames and then establish connections to the resulting addresses.

A DNS failure can therefore look like a networking failure:

```text
Application
    |
    v
DNS Resolution
    |
    X
No IP address
```

But DNS can also succeed while returning the wrong address:

```text
Application
    |
    v
DNS
    |
    v
Public IP
    |
    X
Expected private endpoint
```

This distinction is especially important with:

- VPC interface endpoints.
- Internal Application Load Balancers.
- Amazon RDS.
- ElastiCache.
- Private hosted zones.
- Route 53 Resolver.
- Kubernetes workloads.
- Private microservices.
- Hybrid networks using VPN or Direct Connect.
- Custom DNS infrastructure.

A production troubleshooting process should treat DNS as a separate layer from routing, Security Groups, NACLs, and IAM.

## VPC DNS Architecture

A VPC provides AWS-managed DNS resolution through the Route 53 Resolver service.

A simplified request path is:

```mermaid
sequenceDiagram
    participant App as Application
    participant OS as OS Resolver
    participant VPC as VPC Resolver
    participant DNS as DNS Authority
    participant Target as Target Service

    App->>OS: Resolve hostname
    OS->>VPC: DNS query
    VPC->>DNS: Resolve if required
    DNS-->>VPC: DNS response
    VPC-->>OS: IP address
    OS-->>App: IP address
    App->>Target: TCP/TLS connection
```

The actual path can vary depending on:

- Private hosted zones.
- Resolver rules.
- Forwarding rules.
- Custom DNS servers.
- DNS caching.
- Public DNS.
- Hybrid connectivity.

The key engineering question is not simply:

> "Does DNS work?"

It is:

> "Does the hostname resolve to the address that this workload is supposed to use?"

## VPC DNS Attributes

Two VPC attributes are particularly important:

- `enableDnsSupport`
- `enableDnsHostnames`

Inspect them with:

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --attribute enableDnsSupport

aws ec2 describe-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --attribute enableDnsHostnames
```

### DNS Support

`enableDnsSupport` controls whether DNS resolution is supported through the VPC-provided DNS resolver.

If DNS support is disabled, workloads may be unable to resolve names through the expected VPC DNS path.

### DNS Hostnames

`enableDnsHostnames` controls DNS hostnames for instances in the VPC.

It is especially relevant when using AWS features that depend on DNS hostnames and private DNS behavior.

For production VPCs, these settings should be deliberately configured and validated rather than treated as incidental defaults.

## AmazonProvidedDNS

The VPC resolver is commonly reachable through the VPC's reserved DNS address.

For a VPC CIDR such as:

```text
10.0.0.0/16
```

the resolver is available at:

```text
10.0.0.2
```

The exact resolver address is derived from the VPC network range.

On Linux, inspect resolver configuration:

```bash
cat /etc/resolv.conf
```

You may see an AWS-provided resolver address or a local resolver such as:

```text
127.0.0.53
```

A local resolver does not necessarily mean DNS is being resolved locally. Systems such as `systemd-resolved` can forward requests to the configured upstream resolver.

## First Troubleshooting Principle

Always distinguish these states:

| Result | Interpretation |
|---|---|
| DNS query fails | Resolution problem |
| DNS resolves to unexpected public IP | DNS configuration/private DNS problem |
| DNS resolves to expected private IP | Continue to networking |
| TCP connection times out | Routing/SG/NACL/network issue |
| TCP connection succeeds but TLS fails | TLS/certificate/name issue |
| HTTP returns `403`/`AccessDenied` | Application or authorization layer |
| Application uses stale IP | DNS caching/application behavior |

This layered interpretation prevents DNS problems from being incorrectly diagnosed as routing problems.

## Basic DNS Troubleshooting

Run DNS tests from the same network context as the failing workload.

For Linux:

```bash
getent hosts example.internal
```

For detailed DNS behavior:

```bash
dig example.internal
```

For a simpler lookup:

```bash
nslookup example.internal
```

For an AWS service:

```bash
dig secretsmanager.us-east-1.amazonaws.com
```

Do not perform the test only from a developer laptop and assume it represents the production subnet.

## `dig` Output

A useful `dig` command is:

```bash
dig +short example.internal
```

This removes most diagnostic metadata and shows the returned addresses.

For detailed analysis:

```bash
dig example.internal
```

Inspect:

- `status`.
- Answer records.
- Authority section.
- Additional records.
- TTL.
- Query type.
- Server used.

Example:

```text
;; ->>HEADER<<- opcode: QUERY, status: NOERROR
```

indicates that the DNS server successfully processed the query.

It does not necessarily mean the returned address is the correct address for the application.

## NXDOMAIN vs NOERROR

These responses are operationally different.

### NXDOMAIN

```text
status: NXDOMAIN
```

The DNS system indicates that the requested name does not exist.

Typical causes include:

- Incorrect hostname.
- Missing Route 53 record.
- Incorrect private hosted zone.
- Wrong domain suffix.
- Resolver forwarding problem.
- Split-horizon DNS configuration.

### NOERROR With No Answer

A query can return `NOERROR` while containing no useful answer for the requested record type.

This can happen with:

- Incorrect record type.
- DNS configuration issues.
- Delegation behavior.
- Empty or unexpected authoritative responses.

Do not treat all non-answer cases as equivalent.

## DNS Record Types

The record type matters during troubleshooting.

| Record | Purpose |
|---|---|
| `A` | IPv4 address |
| `AAAA` | IPv6 address |
| `CNAME` | Alias to another hostname |
| `Alias` | AWS-specific routing target behavior |
| `TXT` | Text metadata |
| `NS` | Name server delegation |
| `SOA` | Zone authority information |
| `PTR` | Reverse DNS |

For application connectivity, `A`, `AAAA`, and `CNAME` are especially important.

## Private Hosted Zones

A Route 53 private hosted zone provides DNS records that are intended to resolve within associated VPCs.

Example:

```text
api.internal.example.com
        |
        v
10.0.20.50
```

The private hosted zone must be associated with the VPC where the workload performs the lookup.

Conceptually:

```text
VPC A
  |
  +--> Private Hosted Zone
         |
         +--> api.internal.example.com
                 |
                 v
              10.0.20.50

VPC B
  |
  X
No association
```

If the VPC is not associated with the private hosted zone, workloads in that VPC may not receive the expected private answer.

## Verify Private Hosted Zone Associations

List hosted zones:

```bash
aws route53 list-hosted-zones
```

Inspect a specific zone:

```bash
aws route53 get-hosted-zone \
  --id /hostedzone/Z0123456789ABCDEFGHIJ
```

Look for the VPC associations.

For larger environments, explicitly track:

- Hosted zone.
- VPC.
- AWS account.
- Region.
- Record.
- Resolver rules.

DNS configuration should be treated as infrastructure, not tribal knowledge.

## Split-Horizon DNS

Split-horizon DNS means the same hostname can resolve differently depending on where the query originates.

Example:

```text
api.example.com

Internet:
203.0.113.10

Inside VPC:
10.0.20.10
```

This is useful for private service architectures.

```mermaid
flowchart LR
    InternetClient[Internet Client]
    VPCClient[VPC Workload]
    PublicDNS[Public DNS]
    PrivateDNS[Private Hosted Zone]
    PublicALB[Public ALB]
    InternalALB[Internal ALB]

    InternetClient --> PublicDNS
    PublicDNS --> PublicALB

    VPCClient --> PrivateDNS
    PrivateDNS --> InternalALB
```

A common production failure is creating a private record with the same name but associating it with the wrong VPC.

## Route 53 Resolver

Route 53 Resolver provides DNS resolution inside VPCs and supports DNS forwarding architectures.

Resolver components can include:

- Inbound endpoints.
- Outbound endpoints.
- Resolver rules.
- Forwarding destinations.

A common hybrid architecture is:

```text
AWS VPC
   |
   v
Route 53 Resolver
   |
   v
Outbound Resolver Endpoint
   |
   v
Corporate DNS
```

The reverse direction can be:

```text
Corporate Network
   |
   v
Corporate DNS
   |
   v
Inbound Resolver Endpoint
   |
   v
AWS Private DNS
```

This allows hybrid environments to resolve names across AWS and on-premises networks.

## Resolver Rules

Resolver rules determine where matching DNS queries should be forwarded.

For example:

```text
*.corp.example.com
        |
        v
Corporate DNS
```

while:

```text
*.internal.example.com
        |
        v
AWS Route 53
```

A misconfigured rule can cause queries to be sent to the wrong DNS infrastructure.

Symptoms include:

- NXDOMAIN.
- Timeouts.
- Wrong IP addresses.
- Inconsistent results between VPCs.
- Resolution working from one subnet but not another.

## Inspect Resolver Rules

List rules:

```bash
aws route53resolver list-resolver-rules
```

Inspect rule associations:

```bash
aws route53resolver list-resolver-rule-associations
```

Verify:

- Rule state.
- Domain name.
- Rule type.
- Target IP addresses.
- VPC associations.

## Custom DNS Servers

Some organizations configure workloads to use corporate DNS servers instead of the default VPC resolver.

This can be necessary for:

- Hybrid environments.
- Legacy applications.
- Centralized enterprise DNS.
- Active Directory integration.

However, it introduces another dependency:

```text
Application
    |
    v
Custom DNS
    |
    v
Forwarder
    |
    v
AWS Resolver
```

If the custom DNS infrastructure is unavailable, AWS private names may stop resolving.

This is one reason to avoid replacing the VPC resolver without a clear operational requirement.

## DHCP Options

VPC DHCP option sets can influence which DNS servers instances use.

Inspect the VPC's DHCP options:

```bash
aws ec2 describe-dhcp-options
```

Then inspect the VPC:

```bash
aws ec2 describe-vpcs \
  --vpc-ids vpc-0123456789abcdef0 \
  --query 'Vpcs[].DhcpOptionsId'
```

When debugging DNS, verify that the workload is actually using the intended resolver.

Changing DHCP options may not immediately alter already-running hosts until their network configuration is refreshed or renewed.

## Interface Endpoint DNS Issues

Interface VPC endpoints are a frequent source of DNS confusion.

Suppose an application calls:

```text
secretsmanager.us-east-1.amazonaws.com
```

With appropriate private DNS configuration, the application can resolve the service hostname to private endpoint addresses.

Conceptually:

```text
secretsmanager.us-east-1.amazonaws.com
              |
              v
       Route 53 Resolver
              |
              v
      Interface Endpoint
              |
              v
         10.0.20.50
```

If private DNS is disabled, the same hostname may resolve to public AWS addresses instead.

## Verify Private DNS on an Endpoint

```bash
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids vpce-0123456789abcdef0 \
  --query 'VpcEndpoints[].{
    Service:ServiceName,
    Type:VpcEndpointType,
    State:State,
    PrivateDNS:PrivateDnsEnabled
  }'
```

For interface endpoints, verify that the endpoint configuration matches the application's intended DNS architecture.

## Endpoint-Specific DNS Names

Interface endpoints provide DNS names associated with the endpoint.

Inspect:

```bash
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids vpce-0123456789abcdef0 \
  --query 'VpcEndpoints[].DnsEntries'
```

These names can be useful for diagnostics.

However, production applications should generally use the intended AWS service hostname or explicitly designed private service hostname rather than hard-coding endpoint-specific implementation details unless the architecture requires it.

## IPv4 vs IPv6 DNS Problems

Modern environments may support both:

```text
A     -> IPv4
AAAA  -> IPv6
```

An application may prefer IPv6 if an `AAAA` record exists.

This can create confusing behavior:

```text
DNS
 |
 +--> A     -> 10.0.20.10
 |
 +--> AAAA  -> IPv6 address
```

If IPv6 routing or Security Groups are incorrectly configured, the application may attempt IPv6 first and fail even though IPv4 connectivity works.

When debugging, test both:

```bash
dig A example.internal
dig AAAA example.internal
```

And test explicitly when supported:

```bash
curl -4 https://example.internal
curl -6 https://example.internal
```

Do not disable IPv6 globally merely to hide an underlying configuration problem.

## DNS TTL and Caching

DNS responses include a TTL.

For example:

```text
TTL = 60
```

means a resolver can generally cache the response for the specified period.

Caching can cause a configuration change to appear ineffective.

The request path may be:

```text
Application
    |
    v
OS Cache
    |
    v
Local Resolver Cache
    |
    v
VPC Resolver Cache
    |
    v
Authoritative DNS
```

Changing a Route 53 record does not guarantee that every application immediately sees the new address.

This is particularly important during:

- Failovers.
- Service migrations.
- Blue/green deployments.
- DNS-based traffic shifting.
- Private service migrations.

## Application-Level DNS Caching

Some runtimes and libraries may cache DNS results independently.

This matters for long-running:

- Python processes.
- JVM applications.
- Go services.
- Node.js services.
- Sidecars.
- Service meshes.

For Python applications, the exact behavior depends on the resolver stack and libraries involved.

Do not assume that changing a DNS record immediately changes the destination of an already-running process.

## Kubernetes DNS

Kubernetes adds another DNS layer.

A typical request may look like:

```text
Pod
 |
 v
CoreDNS
 |
 v
VPC Resolver
 |
 v
Route 53 / AWS DNS
 |
 v
AWS Service
```

For example:

```text
Pod
  |
  v
kube-dns / CoreDNS
  |
  v
VPC DNS
```

This means an application running in EKS can experience DNS problems even when the VPC resolver itself is healthy.

Troubleshoot:

- Pod `/etc/resolv.conf`.
- CoreDNS health.
- CoreDNS configuration.
- Kubernetes DNS policies.
- Network Policies.
- VPC DNS.
- Route 53 private hosted zones.
- Resolver rules.

From a pod:

```bash
cat /etc/resolv.conf
```

Then:

```bash
nslookup example.internal
```

or:

```bash
dig example.internal
```

## Docker DNS

Docker also introduces DNS behavior.

Inside a container:

```bash
cat /etc/resolv.conf
```

may show a Docker-provided resolver rather than the VPC resolver directly.

The effective path can be:

```text
Application
    |
    v
Container DNS
    |
    v
Docker Resolver
    |
    v
Host/VPC DNS
```

When debugging a containerized Django or FastAPI service, test DNS from inside the container.

A successful DNS lookup from the EC2 host does not necessarily prove that the application container has equivalent DNS configuration.

## ECS DNS Troubleshooting

For ECS tasks, inspect DNS from the actual task environment where possible.

Common causes include:

- Incorrect VPC DNS configuration.
- Custom DNS configuration.
- Service discovery configuration.
- Security Groups.
- Network ACLs.
- Endpoint private DNS.
- Incorrect AWS region.
- Task networking configuration.

A task in `awsvpc` mode receives its own ENI, making subnet-level DNS and networking behavior particularly important.

## DNS and TLS

DNS problems can also manifest as TLS failures.

Consider:

```text
api.internal.example.com
        |
        v
10.0.20.10
        |
        v
TLS certificate
```

If DNS resolves to the wrong service, TLS may fail because the certificate does not match the requested hostname.

For example:

```text
Requested:
api.internal.example.com

Certificate:
database.internal.example.com
```

The underlying TCP connection may succeed while TLS verification fails.

Use:

```bash
curl -v https://api.internal.example.com
```

to distinguish:

- DNS resolution.
- TCP connection.
- TLS handshake.
- Certificate validation.
- HTTP response.

## DNS and Load Balancers

Internal Application Load Balancers commonly depend on private DNS records.

Example:

```text
api.internal.example.com
        |
        v
Internal ALB
        |
        v
Private ECS services
```

If DNS returns the ALB's private addresses correctly but the request times out, stop troubleshooting DNS and inspect:

- Security Groups.
- Listener configuration.
- Target health.
- NACLs.
- Routing.

This is a common boundary in incident debugging.

## DNS and Security Groups

Security Groups do not directly control DNS record creation, but they can prevent DNS traffic from reaching a custom resolver.

If a workload uses a custom DNS server:

```text
Application
    |
    | UDP/TCP 53
    v
Custom DNS
```

the Security Group and NACL path must permit the relevant DNS traffic.

DNS can use:

- UDP 53.
- TCP 53.

TCP can be required for larger responses and certain DNS operations.

Do not assume that allowing only UDP/53 is universally sufficient.

## DNS and Network ACLs

A restrictive NACL can break DNS.

For a custom resolver:

```text
Workload Subnet
      |
      | UDP/TCP 53
      v
DNS Resolver Subnet
```

The NACL must allow both the request and response paths.

Because NACLs are stateless, ephemeral return ports can be relevant.

Security Groups are stateful, while NACLs are stateless.

This distinction is important during incident response.

## DNS Failure Decision Tree

```mermaid
flowchart TD
    Start[Application cannot reach hostname] --> Resolve{Does hostname resolve?}

    Resolve -->|No| DNSConfig[Check resolver, VPC DNS, hosted zones, rules]
    Resolve -->|Yes| Expected{Is returned address expected?}

    Expected -->|No| PrivateDNS[Check private DNS / split horizon / resolver rules]
    Expected -->|Yes| TCP{Can TCP connection be established?}

    TCP -->|No| Network[Check routes, SGs, NACLs, endpoint/network path]
    TCP -->|Yes| TLS{Does TLS succeed?}

    TLS -->|No| Certificate[Check hostname, certificate, TLS configuration]
    TLS -->|Yes| HTTP[Check HTTP/application/authentication]
```

This decision tree keeps troubleshooting layered.

## Practical Troubleshooting Workflow

### Verify the Application Hostname

Determine exactly what hostname the application is using.

For example:

```text
DATABASE_URL
AWS_REGION
REDIS_URL
API_BASE_URL
```

Inspect configuration without exposing secrets.

A common production problem is simply using:

```text
service.us-west-2.amazonaws.com
```

from a workload intended to use:

```text
service.us-east-1.amazonaws.com
```

AWS service endpoints are region-sensitive.

### Test DNS From the Workload

```bash
getent hosts example.internal
```

Then:

```bash
dig example.internal
```

Record:

- Returned IP.
- TTL.
- Resolver address.
- Response status.

### Test TCP

```bash
nc -vz example.internal 443
```

If DNS succeeds but TCP fails, investigate networking.

### Test TLS

```bash
curl -v https://example.internal
```

This provides significantly more information than:

```bash
ping example.internal
```

### Test the AWS API

For example:

```bash
aws sts get-caller-identity
```

or a service-specific operation appropriate to the workload.

A successful API request confirms substantially more than DNS alone, including authentication and service-level access.

## Common DNS Failure Patterns

| Symptom | Likely Cause |
|---|---|
| `NXDOMAIN` | Missing/wrong DNS record or zone |
| DNS timeout | Resolver/network path problem |
| Public IP returned unexpectedly | Private DNS/split-horizon issue |
| Private IP returned but connection times out | Routing/SG/NACL issue |
| Works from one VPC but not another | Hosted zone or resolver rule association |
| Works on host but not in container | Container DNS configuration |
| Works on EC2 but not EKS pod | CoreDNS/Kubernetes DNS issue |
| IPv4 works, IPv6 fails | AAAA/routing/SG configuration |
| DNS changed but old IP remains | TTL/cache |
| TLS hostname mismatch | DNS points to wrong service |
| AWS endpoint resolves publicly | Interface endpoint private DNS issue |
| Internal hostname resolves externally but not internally | Private hosted zone/resolver issue |

## AWS CLI Diagnostic Commands

### Inspect VPC DNS Configuration

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --attribute enableDnsSupport

aws ec2 describe-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --attribute enableDnsHostnames
```

### Inspect VPC

```bash
aws ec2 describe-vpcs \
  --vpc-ids vpc-0123456789abcdef0
```

### Inspect DHCP Options

```bash
aws ec2 describe-dhcp-options
```

### Inspect Hosted Zones

```bash
aws route53 list-hosted-zones
```

### Inspect a Private Hosted Zone

```bash
aws route53 get-hosted-zone \
  --id /hostedzone/Z0123456789ABCDEFGHIJ
```

### Inspect Resolver Rules

```bash
aws route53resolver list-resolver-rules
```

### Inspect Resolver Rule Associations

```bash
aws route53resolver list-resolver-rule-associations
```

### Inspect Interface Endpoint DNS

```bash
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids vpce-0123456789abcdef0 \
  --query 'VpcEndpoints[].DnsEntries'
```

### Inspect Endpoint Private DNS

```bash
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids vpce-0123456789abcdef0 \
  --query 'VpcEndpoints[].PrivateDnsEnabled'
```

## Production Monitoring

DNS should be observable as part of the application's dependency health.

Monitor where appropriate:

- DNS resolution latency.
- DNS failure rate.
- Resolver endpoint health.
- CoreDNS health in Kubernetes.
- Private hosted zone configuration.
- Route 53 health checks where applicable.
- Application connection failures.
- Endpoint connectivity.
- Service discovery failures.

For critical services, application metrics should distinguish:

```text
dns_resolution_failure
tcp_connection_failure
tls_handshake_failure
http_error
```

instead of recording every failure as:

```text
request_failed
```

This dramatically improves incident diagnosis.

## Security Considerations

DNS is part of the security boundary.

A compromised workload may attempt to:

- Resolve internal service names.
- Enumerate internal records.
- Reach unauthorized services.
- Bypass intended network boundaries.
- Exfiltrate data through DNS-based mechanisms.

Use appropriate controls such as:

- Least-privilege Resolver rules.
- Restricted inbound/outbound Resolver endpoints.
- Controlled private hosted zones.
- Network segmentation.
- Security monitoring.
- DNS query logging where required.

Avoid exposing internal DNS infrastructure unnecessarily.

## Scalability Considerations

DNS infrastructure must scale with the number of:

- Workloads.
- Queries.
- Services.
- VPCs.
- Accounts.
- Resolver rules.
- Hybrid connections.

Large organizations should establish a deliberate DNS architecture rather than allowing each team to create independent naming systems.

A typical multi-account architecture may include:

```text
AWS Organizations
        |
        +----------------+
        |                |
     VPC A            VPC B
        |                |
        +-------+--------+
                |
        Central DNS Architecture
                |
        Route 53 / Resolver
                |
        Corporate DNS
```

Centralization can improve consistency but can also introduce blast-radius concerns.

Design for:

- Redundancy.
- Clear ownership.
- Failure isolation.
- Controlled delegation.
- Operational visibility.

## Reliability and High Availability

Avoid making a single custom DNS server a critical dependency.

For hybrid DNS:

```text
VPC
 |
 +--> Resolver Endpoint AZ-A
 |
 +--> Resolver Endpoint AZ-B
 |
 +--> Corporate DNS
```

For production workloads, consider failure behavior when:

- A Resolver endpoint becomes unavailable.
- A DNS forwarding target fails.
- A private hosted zone is modified incorrectly.
- A Kubernetes CoreDNS instance becomes unavailable.
- A network path to corporate DNS is interrupted.

DNS failures can become application-wide outages because almost every request may depend on name resolution.

## Disaster Recovery Considerations

DNS configuration should be included in disaster recovery planning.

Document:

- Private hosted zones.
- Record ownership.
- VPC associations.
- Resolver rules.
- Resolver endpoints.
- DNS forwarding targets.
- Hybrid DNS dependencies.
- Kubernetes CoreDNS configuration.
- Service discovery configuration.

Manage DNS infrastructure with IaC where practical so that it can be recreated consistently.

## Infrastructure as Code

Terraform example:

```hcl
resource "aws_route53_zone" "internal" {
  name = "internal.example.com"

  vpc {
    vpc_id = aws_vpc.main.id
  }
}

resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.internal.zone_id
  name    = "api.internal.example.com"
  type    = "A"
  ttl     = 30

  records = [
    "10.0.20.50"
  ]
}
```

In production, avoid hard-coding infrastructure addresses when the target is dynamically managed.

Prefer AWS-native targets, service discovery, or load balancer aliases where appropriate.

## Common Mistakes

### Testing DNS From the Wrong Environment

A developer laptop may resolve:

```text
api.internal.example.com
```

while a production VPC does not.

Always reproduce DNS behavior from the failing network.

### Assuming DNS Success Means Network Success

DNS only answers:

> "What address does this name resolve to?"

It does not prove:

> "Can the application reach that address?"

### Ignoring Private Hosted Zone Associations

A correct Route 53 record is useless to a VPC that cannot see the private hosted zone.

### Forgetting Split-Horizon DNS

Public and private zones may return different answers for the same hostname.

Always determine which view the workload should receive.

### Disabling DNS to Fix a Networking Problem

Disabling VPC DNS attributes is rarely an appropriate troubleshooting fix.

It can create additional failures rather than solving the underlying problem.

### Ignoring DNS Caching

After changing records, stale responses may remain until TTLs expire or caches are refreshed.

### Testing Only `ping`

ICMP is not a reliable test for HTTPS, database, Redis, or AWS API connectivity.

Use protocol-specific tests.

### Ignoring IPv6

A valid `AAAA` record can cause applications to prefer IPv6 even when IPv6 routing is incomplete.

Test both address families.

### Using Custom DNS Without a Clear Architecture

Replacing the AWS resolver with custom DNS creates an additional dependency and operational failure mode.

### Hard-Coding IP Addresses

Hard-coded AWS service or load-balancer IP addresses are fragile.

AWS-managed services frequently change their underlying addresses.

Use DNS-based service discovery unless there is a specific architectural reason not to.

## Interview Traps

### "Route 53 Is Only a Public DNS Service"

Incorrect.

Route 53 also supports private hosted zones and integrates with VPC Resolver functionality.

### "Private Hosted Zones Automatically Apply to Every VPC"

Incorrect.

Private hosted zones must be associated with the relevant VPCs, directly or through supported association mechanisms.

### "DNS Resolution and DNS Hostnames Are the Same Setting"

Incorrect.

`enableDnsSupport` and `enableDnsHostnames` control related but distinct VPC DNS behavior.

### "If DNS Returns an IP, Networking Is Working"

Incorrect.

DNS resolution occurs before the application establishes the network connection.

### "Private DNS Means the Service Is Automatically Reachable"

Incorrect.

Private DNS can return the correct private address while Security Groups, NACLs, routes, or endpoint policies still prevent access.

### "DNS Uses Only UDP"

Incorrect.

DNS commonly uses UDP, but TCP is also used for larger responses and other DNS operations.

### "Changing a Route 53 Record Immediately Changes Every Application"

Incorrect.

Resolvers, operating systems, runtimes, and libraries can cache DNS results according to TTL and implementation behavior.

## Production Troubleshooting Checklist

```text
[ ] Identify the exact hostname being resolved
[ ] Identify the expected IP/address family
[ ] Identify the source workload
[ ] Identify the source VPC
[ ] Identify the source subnet
[ ] Identify the source Availability Zone
[ ] Check enableDnsSupport
[ ] Check enableDnsHostnames
[ ] Inspect /etc/resolv.conf
[ ] Identify the resolver actually being queried
[ ] Test with getent
[ ] Test with dig
[ ] Check A records
[ ] Check AAAA records
[ ] Check CNAME chains
[ ] Check DNS response status
[ ] Check TTL
[ ] Verify private hosted zone associations
[ ] Verify split-horizon configuration
[ ] Verify Route 53 records
[ ] Verify Resolver rules
[ ] Verify Resolver rule associations
[ ] Verify DHCP options if custom DNS is used
[ ] Verify interface endpoint private DNS
[ ] Test from the actual workload environment
[ ] Test TCP connectivity after DNS succeeds
[ ] Test TLS after TCP succeeds
[ ] Inspect Security Groups
[ ] Inspect NACLs
[ ] Inspect routing
[ ] Inspect Kubernetes CoreDNS if applicable
[ ] Inspect Docker/container DNS if applicable
[ ] Check application-level DNS caching
[ ] Check IPv4 and IPv6 behavior
[ ] Check recent DNS/IaC changes
[ ] Verify monitoring and DNS query visibility
```

## Key Takeaways

- **DNS is a distinct networking layer**: successful name resolution does not prove that the resulting address is reachable or that the application request will succeed.
- **Always validate the resolver path and returned address**: VPC Resolver, private hosted zones, Resolver rules, custom DNS, interface endpoint private DNS, and Kubernetes/CoreDNS can all change resolution behavior.
- **Troubleshoot from the failing workload's network context**, then progress from DNS to TCP, TLS, and finally application or authorization behavior.
- **Treat private DNS as production infrastructure** with explicit ownership, high availability, monitoring, Infrastructure as Code, and disaster recovery considerations.
- **Avoid hard-coded IPs and ad-hoc DNS fixes**; use AWS-native DNS, controlled private hosted zones, and deliberate Resolver architecture for scalable backend systems.