# 02- VPC Security Questions

## Overview

VPC security questions are common in backend, cloud, DevOps, and system design interviews because they test whether an engineer understands the difference between **network reachability, traffic authorization, exposure, and isolation**.

A strong answer should not stop at definitions such as "Security Groups are firewalls." Interviewers typically want to know:

- Where the control is applied.
- Whether it is stateful or stateless.
- How traffic flows through it.
- How it interacts with routing.
- How to implement least privilege.
- How to troubleshoot failures.
- How the design changes at production scale.

The core security model is layered:

```text
                    Internet
                       |
                       v
                Internet Gateway
                       |
                       v
                Public Subnet
                       |
                 Load Balancer
                       |
                       v
              Private Application
                       |
              +--------+--------+
              |                 |
              v                 v
          PostgreSQL          Redis
```

Each layer should expose only what is required.

## Security Architecture Fundamentals

### Question: What are the main security controls in an AWS VPC?

**Answer:**

The primary networking security mechanisms include:

- Security Groups.
- Network ACLs.
- Route tables.
- VPC endpoints and endpoint policies.
- IAM policies for AWS API access.
- AWS Network Firewall where required.
- VPC Flow Logs for visibility.
- Private subnets and network segmentation.
- Encryption mechanisms such as TLS and IPsec.

These controls solve different problems.

| Control | Primary Responsibility |
|---|---|
| Route table | Determines network path |
| Security Group | Controls traffic at the network-interface/workload level |
| Network ACL | Controls traffic at subnet level |
| VPC Endpoint | Provides private access to supported AWS services |
| Endpoint policy | Controls allowed access through an endpoint |
| IAM | Controls AWS API/resource authorization |
| VPC Flow Logs | Provides network traffic visibility |
| Network Firewall | Centralized network inspection/filtering |

A secure architecture combines these controls rather than depending on one mechanism.

---

### Question: What is the difference between network security and IAM security?

**Answer:**

Network security controls whether a connection can reach a resource.

IAM controls whether an authenticated AWS principal is authorized to perform an AWS API action.

For example:

```text
Application
    |
    | TCP 5432
    v
PostgreSQL
```

A Security Group may allow the TCP connection.

But PostgreSQL authentication still determines whether the application can log in.

Similarly:

```text
Application
    |
    | AWS API request
    v
S3
```

Network connectivity does not imply IAM authorization.

A production design should treat these as separate security layers.

---

## Security Groups

### Question: What is a Security Group?

**Answer:**

A Security Group is a stateful virtual firewall associated with supported network interfaces.

It controls inbound and outbound traffic using allow rules.

For example:

```text
ALB Security Group
        |
        | TCP 8000
        v
API Security Group
        |
        | TCP 5432
        v
Database Security Group
```

This allows security relationships to follow application architecture.

---

### Question: Why are Security Groups stateful?

**Answer:**

Security Groups track connection state.

If an inbound connection is permitted, the corresponding response traffic is automatically permitted without requiring a separate reverse-direction rule.

For example:

```text
Client
  |
  | TCP request
  v
Server
  |
  | TCP response
  v
Client
```

If the inbound flow is permitted by the Security Group, the response traffic is allowed as part of the established connection.

This is one of the major differences from Network ACLs.

---

### Question: Do Security Groups have deny rules?

**Answer:**

No.

Security Groups support allow rules.

If traffic does not match an applicable allow rule, it is implicitly denied.

For example:

```text
Inbound:
TCP 443 from 0.0.0.0/0
```

allows HTTPS from the Internet.

There is no Security Group rule equivalent to:

```text
DENY TCP 22 from 1.2.3.4
```

If selective explicit denies are required at the subnet/network layer, a Network ACL or another network security control may be appropriate.

---

### Question: What is the best practice for Security Group rules?

**Answer:**

Use **least privilege**.

Instead of:

```text
TCP 5432
Source: 0.0.0.0/0
```

use:

```text
TCP 5432
Source: application-security-group
```

For example:

```text
Internet
   |
   | TCP 443
   v
ALB-SG
   |
   | TCP 8000
   v
API-SG
   |
   | TCP 5432
   v
DB-SG
```

This creates an explicit trust chain.

---

### Question: Can a Security Group reference another Security Group?

**Answer:**

Yes.

A Security Group can be used as the source or destination in appropriate Security Group rules.

For example:

```text
Database SG

Inbound:
TCP 5432
Source: api-sg
```

This is preferable to using an individual application server IP because application instances may be dynamically created or replaced.

This pattern is particularly useful with:

- EC2 Auto Scaling.
- ECS.
- EKS.
- Microservices.
- Load balancers.

---

### Question: What happens if an EC2 instance belongs to multiple Security Groups?

**Answer:**

The effective inbound permissions are generally the union of the applicable allow rules.

For example:

```text
SG-A:
TCP 443 from Internet

SG-B:
TCP 22 from Corporate CIDR
```

The instance can receive:

```text
TCP 443
TCP 22
```

assuming the rest of the network path permits the traffic.

This means attaching an additional permissive Security Group can unintentionally expand access.

---

### Question: Can Security Groups reference Security Groups across VPCs?

**Answer:**

Security Group references have specific scope and connectivity requirements and should not be treated as a generic replacement for CIDR-based rules across arbitrary networks.

When dealing with:

- VPC peering.
- Transit Gateway.
- Shared VPCs.
- Cross-account networking.

verify the supported Security Group referencing model for the specific architecture and AWS service.

The important interview principle is that **network connectivity and Security Group authorization are separate concerns**.

---

## Network ACLs

### Question: What is a Network ACL?

**Answer:**

A Network ACL, or NACL, is a subnet-level network traffic filter.

NACLs support:

- Allow rules.
- Deny rules.

They are **stateless**, meaning inbound and outbound traffic must be permitted independently.

---

### Question: Why are NACLs stateless?

**Answer:**

A NACL does not track connection state in the same way a Security Group does.

If a client initiates a connection:

```text
Client
  |
  | Request
  v
Server
  |
  | Response
  v
Client
```

the NACL must permit the relevant traffic in both directions.

This becomes particularly important for ephemeral client ports.

For example:

```text
Client:
TCP source port 49152

Server:
TCP destination port 443
```

The return traffic may use:

```text
Server:
TCP source port 443

Client:
TCP destination port 49152
```

A restrictive NACL must account for the return path.

---

### Question: What is the difference between Security Groups and NACLs?

**Answer:**

| Feature | Security Group | Network ACL |
|---|---|---|
| Scope | Network interface | Subnet |
| Stateful | Yes | No |
| Rules | Allow | Allow and deny |
| Evaluation | Applicable rules | Rule number order |
| Return traffic | Automatically tracked | Must be explicitly permitted |
| Typical use | Workload-level access control | Subnet-level filtering |

A common production model is:

```text
NACL
  ↓
Subnet-level guardrail

Security Group
  ↓
Workload-level least privilege
```

---

### Question: When should you use NACLs?

**Answer:**

NACLs are useful when subnet-level filtering or explicit deny rules are required.

They can provide an additional defense layer for:

- Sensitive network segments.
- Known malicious address ranges.
- Compliance requirements.
- Broad subnet-level restrictions.

However, overly complex NACLs can make troubleshooting significantly harder.

Security Groups should normally remain the primary workload-level access control mechanism.

---

## Routing and Security

### Question: Does a route table provide security?

**Answer:**

A route table determines where traffic is sent, but it is not an authorization mechanism.

For example:

```text
10.20.0.0/16 → Transit Gateway
```

means AWS has a route toward that destination.

It does not mean the destination is authorized to accept the traffic.

The complete path may still be blocked by:

- Security Groups.
- NACLs.
- Network Firewall.
- Endpoint policies.
- Destination-side firewall rules.

A useful mental model is:

```text
Routing:
"Where should the packet go?"

Security:
"Is the packet allowed?"

Application:
"Will the service accept the request?"
```

---

### Question: Can a route bypass a Security Group?

**Answer:**

No.

Routing determines the path, but Security Groups still apply to supported network interfaces.

For example:

```text
Source
  |
  v
Route Table
  |
  v
Destination ENI
  |
  v
Security Group
```

A valid route does not override a Security Group restriction.

---

## Public and Private Network Security

### Question: Why should databases normally be placed in private subnets?

**Answer:**

Databases generally do not need direct Internet reachability.

A secure architecture separates public entry points from internal data services:

```text
Internet
   |
   v
Application Load Balancer
   |
   v
Private API
   |
   v
Private Database
```

The database Security Group can then allow traffic only from the application layer.

For PostgreSQL:

```text
DB-SG inbound:

Protocol: TCP
Port: 5432
Source: API-SG
```

This reduces the attack surface.

---

### Question: Does a private subnet guarantee that a resource is secure?

**Answer:**

No.

Private networking reduces exposure but does not automatically provide application security.

A private workload can still be vulnerable through:

- Excessively permissive Security Groups.
- Compromised internal workloads.
- Vulnerable applications.
- Excessive IAM permissions.
- Stolen credentials.
- Misconfigured endpoints.
- Lateral movement.
- Insecure service-to-service communication.

Private networking is one layer of defense, not a complete security model.

---

### Question: Should an application server have a public IP if an ALB is already public?

**Answer:**

Usually not.

A common architecture is:

```text
Internet
   |
   v
Public ALB
   |
   v
Private Application
```

The application receives traffic from the ALB rather than directly from the Internet.

This provides a cleaner trust boundary and reduces the number of publicly reachable resources.

---

## Internet Gateway and NAT Security

### Question: What is the security difference between an Internet Gateway and a NAT Gateway?

**Answer:**

An Internet Gateway supports Internet connectivity for appropriately addressed resources in a VPC.

A NAT Gateway enables private resources to initiate outbound Internet connections without requiring public IP addresses on those resources.

Typical architecture:

```text
Public Subnet
     |
     +---- Internet-facing ALB
     |
     +---- NAT Gateway
              |
              v
        Internet Gateway
              |
              v
           Internet

Private Subnet
     |
     +---- Application
              |
              v
          NAT Gateway
```

The NAT Gateway is not a replacement for a Security Group.

---

### Question: Does a NAT Gateway make private resources Internet-accessible from inbound connections?

**Answer:**

No.

NAT Gateway is primarily used for connections initiated from private resources toward external destinations.

For example:

```text
Private API
    |
    | outbound HTTPS
    v
NAT Gateway
    |
    v
External API
```

It does not provide a general inbound path from the Internet to the private API.

---

## VPC Endpoints and Security

### Question: Why are VPC endpoints useful from a security perspective?

**Answer:**

VPC endpoints can provide private connectivity between workloads and supported AWS services.

Instead of:

```text
Private Application
      |
      v
NAT Gateway
      |
      v
Internet
      |
      v
AWS Service
```

a supported service may be accessed through:

```text
Private Application
      |
      v
VPC Endpoint
      |
      v
AWS Service
```

This can reduce dependency on public Internet paths and NAT infrastructure.

---

### Question: What is an endpoint policy?

**Answer:**

An endpoint policy can control which AWS resources or actions are permitted through a VPC endpoint, depending on the endpoint/service.

For example, a workload might need access to only a specific S3 bucket.

A layered model can look like:

```text
Network Path
     ↓
VPC Endpoint
     ↓
Endpoint Policy
     ↓
IAM Policy
     ↓
S3 Bucket Policy
```

Each layer can contribute to the final authorization decision.

---

## Encryption and Secure Communication

### Question: Does a VPC automatically encrypt all traffic?

**Answer:**

No.

Private networking does not automatically mean application-layer encryption.

For example:

```text
Private API
    |
    | HTTP
    v
Internal Service
```

is still unencrypted at the application protocol layer.

For sensitive communication, use TLS:

```text
Private API
    |
    | HTTPS / TLS
    v
Internal Service
```

This is particularly important for:

- Authentication credentials.
- Personal or financial data.
- Internal APIs.
- Database connections.
- Service-to-service communication.

---

### Question: Should internal microservices use TLS?

**Answer:**

For production systems with meaningful security requirements, yes.

Internal network location should not automatically be treated as a trusted identity boundary.

A stronger architecture is:

```text
Service A
   |
   | mTLS / TLS
   v
Service B
```

Combined with:

- Authentication.
- Authorization.
- Network segmentation.
- Least-privilege Security Groups.
- Secrets management.

---

## Security Group Design

### Question: How would you design Security Groups for a Django or FastAPI application?

**Answer:**

Separate responsibilities.

For example:

```text
Internet
   |
   v
ALB-SG
   |
   | 443
   v
API-SG
   |
   +---- 5432 ----> DB-SG
   |
   +---- 6379 ----> Redis-SG
```

Example rules:

| Security Group | Port | Source |
|---|---:|---|
| ALB-SG | 443 | Internet |
| API-SG | Application port | ALB-SG |
| DB-SG | 5432 | API-SG |
| Redis-SG | 6379 | API-SG |

This is more maintainable than allowing broad CIDR ranges everywhere.

---

### Question: Why should you avoid `0.0.0.0/0` for database access?

**Answer:**

`0.0.0.0/0` represents all IPv4 addresses.

Allowing:

```text
TCP 5432 from 0.0.0.0/0
```

makes the database network-accessible from arbitrary IPv4 sources if the rest of the path permits it.

For PostgreSQL, the preferred pattern is:

```text
DB-SG
TCP 5432
Source: API-SG
```

The database should also enforce authentication and authorization independently of the network layer.

---

### Question: What is a good Security Group naming strategy?

**Answer:**

Names should describe the workload or trust boundary.

Examples:

```text
alb-public
api-private
worker-private
postgres-private
redis-private
```

Avoid names such as:

```text
sg-1
new-sg
test-security
allow-all
```

Clear naming makes production troubleshooting significantly easier.

---

## Security Group Troubleshooting

### Question: An API cannot connect to PostgreSQL. How do you troubleshoot the Security Group configuration?

**Answer:**

Start with the source and destination.

```text
API
 |
 | TCP 5432
 v
PostgreSQL
```

Then verify:

1. Identify the API ENI and its Security Groups.
2. Identify the database ENI and its Security Groups.
3. Verify the database Security Group allows TCP `5432`.
4. Verify the source is the intended API Security Group or CIDR.
5. Verify the route exists.
6. Verify NACLs.
7. Verify DNS resolution.
8. Verify PostgreSQL is listening.
9. Verify database authentication.

Do not assume:

```text
"Both resources are in the same VPC, therefore they can communicate."
```

Network connectivity depends on routing and security controls.

---

### Question: Why might a Security Group rule look correct but connectivity still fail?

**Answer:**

Because the Security Group is only one part of the network path.

For example:

```text
Application
   |
   v
Route Table
   |
   v
NACL
   |
   v
Security Group
   |
   v
Database
```

Other possible causes include:

- Incorrect route.
- NACL deny.
- Wrong destination IP.
- DNS resolution failure.
- Wrong port.
- Application not listening.
- OS firewall.
- Database configuration.
- TLS configuration.
- Network Firewall policy.

Always troubleshoot the entire path.

---

## Network Segmentation

### Question: Why segment a VPC into multiple subnets?

**Answer:**

Segmentation creates separate network boundaries for different workload classes.

A typical backend architecture may use:

```text
VPC
|
+-- Public Subnets
|      |
|      +-- ALB
|      +-- NAT Gateway
|
+-- Private Application Subnets
|      |
|      +-- Django
|      +-- FastAPI
|      +-- Celery
|
+-- Private Database Subnets
       |
       +-- PostgreSQL
       +-- Redis
```

Benefits include:

- Reduced exposure.
- Easier traffic control.
- Better fault isolation.
- Clearer architecture.
- Easier compliance boundaries.
- More predictable routing.

---

### Question: Should application and database workloads share the same Security Group?

**Answer:**

Usually no.

Separating Security Groups makes trust relationships explicit.

For example:

```text
API-SG
   |
   | TCP 5432
   v
DB-SG
```

If both workloads share one broad Security Group, it becomes easier to accidentally allow unnecessary lateral communication.

Separate Security Groups make the architecture easier to reason about.

---

## VPC Peering and Security

### Question: How do Security Groups work with VPC peering?

**Answer:**

VPC peering provides the network path, but Security Groups still determine whether the workload permits the connection.

For example:

```text
VPC A
10.0.0.0/16
   |
   | Peering
   |
VPC B
10.1.0.0/16
```

Both sides need appropriate routing and security configuration.

The effective path is:

```text
VPC A
  ↓
Route Table
  ↓
Peering Connection
  ↓
Route Table
  ↓
Destination ENI
  ↓
Security Group
```

VPC peering is not itself an authorization mechanism.

---

### Question: Why is overlapping CIDR a security and connectivity concern?

**Answer:**

Overlapping CIDRs make network destinations ambiguous.

For example:

```text
VPC A:
10.0.0.0/16

VPC B:
10.0.0.0/16
```

Trying to establish routed connectivity between them becomes problematic because the same destination address range exists in both networks.

For organizations expecting:

- VPC peering.
- Transit Gateway.
- VPN.
- Direct Connect.
- Multi-account networking.

CIDR planning should happen before production deployment.

---

## Transit Gateway Security

### Question: How does Transit Gateway affect VPC security?

**Answer:**

Transit Gateway centralizes connectivity between multiple networks.

For example:

```text
                 Transit Gateway
                /       |       \
               /        |        \
            VPC-A     VPC-B     VPC-C
```

The security model must consider:

- Transit Gateway route tables.
- VPC route tables.
- Security Groups.
- NACLs.
- Network Firewall where applicable.
- Destination-side controls.

A Transit Gateway route does not automatically authorize application traffic.

---

### Question: How would you isolate production and development VPCs?

**Answer:**

Use explicit routing and security boundaries.

For example:

```text
                  Transit Gateway
                 /               \
                /                 \
        Production VPC        Development VPC
              |                     |
           DB-SG                  DB-SG
```

Do not automatically allow:

```text
Development → Production
```

unless there is a specific requirement.

If limited connectivity is required, expose only the necessary destination and port.

For example:

```text
Development
    |
    | TCP 443
    v
Production Internal API
```

rather than broad network access to the entire production CIDR.

---

## VPC Flow Logs

### Question: What are VPC Flow Logs?

**Answer:**

VPC Flow Logs provide visibility into network traffic metadata.

They can help determine whether traffic was:

- Accepted.
- Rejected.

They are useful for troubleshooting:

```text
Application
   |
   | connection attempt
   v
Network Path
   |
   v
Flow Logs
```

Flow Logs do not replace application logs or packet capture.

---

### Question: Can VPC Flow Logs tell you why an application request failed?

**Answer:**

They can provide evidence about the network flow, but they do not provide the complete application-level explanation.

For example, Flow Logs may show:

```text
ACCEPT
```

but the application may still fail because:

- PostgreSQL rejected authentication.
- TLS negotiation failed.
- The application sent an invalid request.
- The destination process was unavailable.
- The application timed out elsewhere.

Flow Logs should therefore be correlated with:

- Application logs.
- Load balancer logs.
- DNS diagnostics.
- CloudWatch metrics.
- Service-specific logs.

---

## Network Firewall and Centralized Security

### Question: When would you use AWS Network Firewall?

**Answer:**

AWS Network Firewall is appropriate when centralized, managed network traffic inspection and filtering are required beyond basic Security Groups and NACLs.

Possible use cases include:

- Centralized egress filtering.
- Domain-based controls.
- Stateful inspection.
- Intrusion prevention patterns.
- Central security boundaries.

A simplified architecture is:

```text
Application VPC
      |
      v
Inspection Path
      |
      v
Network Firewall
      |
      v
External Network
```

The routing design must ensure traffic actually traverses the inspection path.

---

## Least Privilege

### Question: What does least privilege mean in VPC security?

**Answer:**

Least privilege means allowing only the network communication required by a workload.

For example, if an API needs:

```text
API → PostgreSQL: 5432
API → Redis: 6379
API → External API: 443
```

do not automatically permit:

```text
API → Any Internal Host: Any Port
```

A practical security matrix might look like:

| Source | Destination | Port | Reason |
|---|---|---:|---|
| Internet | ALB | 443 | Public API |
| ALB | API | 8000 | Application traffic |
| API | PostgreSQL | 5432 | Database |
| API | Redis | 6379 | Cache |
| Worker | Kafka | 9092/secure listener | Messaging |

Every rule should have a business or technical reason.

---

## Production Security Architecture

### Question: How would you secure a production Django or FastAPI VPC?

**Answer:**

A practical architecture is:

```text
                         Internet
                            |
                            v
                    Internet Gateway
                            |
                     Public Subnets
                            |
                      Public ALB
                            |
                     Private Subnets
                            |
             +--------------+--------------+
             |                             |
        API / Django                  Celery Worker
             |                             |
             +---------------+-------------+
                             |
                  +----------+----------+
                  |                     |
                  v                     v
             PostgreSQL               Redis
             Private DB             Private DB
```

Security principles:

- Keep application servers private.
- Keep databases private.
- Expose only the load balancer publicly.
- Terminate TLS appropriately.
- Use least-privilege Security Groups.
- Restrict database access to application workloads.
- Use private connectivity to AWS services where appropriate.
- Use IAM roles instead of long-lived AWS credentials.
- Store secrets in an appropriate secrets-management system.
- Enable network visibility through Flow Logs where required.
- Monitor changes to security-sensitive resources.
- Avoid broad CIDR-based access when Security Group references can express the trust relationship more precisely.

---

## IAM and VPC Security

### Question: Why is IAM still important if Security Groups protect the network?

**Answer:**

Security Groups control network connectivity, not AWS API authorization.

Consider an EC2 application:

```text
EC2
 |
 +---- Network access ----> PostgreSQL
 |
 +---- AWS API access ----> S3
```

The Security Group controls the first relationship.

IAM controls what the EC2 workload can do through AWS APIs.

A secure design therefore needs both:

```text
Network Security
+
Identity Security
```

---

### Question: Why should applications use IAM roles instead of hard-coded AWS credentials?

**Answer:**

Hard-coded credentials create significant security risk.

Avoid:

```python
AWS_ACCESS_KEY = "..."
AWS_SECRET_KEY = "..."
```

Instead, use workload identities such as IAM roles supported by the deployment platform.

This provides:

- Temporary credentials.
- Credential rotation handled by AWS mechanisms.
- Reduced secret-management burden.
- Better auditability.
- Least-privilege permissions.

---

## Common Security Mistakes

### Mistake: Allowing SSH from the Internet

Bad:

```text
TCP 22
0.0.0.0/0
```

This exposes SSH to arbitrary Internet sources.

Prefer:

```text
TCP 22
Source: trusted administrative network
```

or use managed access mechanisms such as AWS Systems Manager where appropriate.

---

### Mistake: Opening PostgreSQL to the Internet

Bad:

```text
TCP 5432
0.0.0.0/0
```

Better:

```text
TCP 5432
Source: API-SG
```

The database should also require strong authentication and encrypted connections where appropriate.

---

### Mistake: Treating a private subnet as a security boundary by itself

A private subnet does not stop an already-compromised internal workload from attacking another internal workload.

Use:

- Security Groups.
- Segmentation.
- Authentication.
- Authorization.
- Encryption.
- Monitoring.
- Least privilege.

---

### Mistake: Making every Security Group permissive

A rule such as:

```text
All traffic
Source: VPC CIDR
```

may appear convenient but can create excessive lateral connectivity.

Prefer explicit workload-to-workload relationships.

---

### Mistake: Using NACLs as the primary application firewall

NACLs are useful as subnet-level controls but are often unnecessarily complex for application-specific authorization.

Use Security Groups for workload-level access control and NACLs for broader subnet-level requirements.

---

### Mistake: Forgetting IPv6

A Security Group configuration that is restrictive for IPv4 may still be too permissive for IPv6 if IPv6 connectivity is enabled and rules are not reviewed accordingly.

Review both:

```text
0.0.0.0/0
```

and:

```text
::/0
```

when IPv6 is part of the architecture.

---

## Interview Scenarios

### Scenario: An API is publicly accessible even though the EC2 instance is in a private subnet. What would you investigate?

**Answer:**

Do not assume the subnet classification is correct.

Investigate:

1. Subnet route table.
2. ENI and IP addressing.
3. Load balancer configuration.
4. Security Groups.
5. Public IP or Elastic IP associations.
6. IPv6 addressing and routing.
7. Any proxy or reverse-proxy architecture.
8. Whether the traffic is actually reaching the instance directly or through an intended public entry point.

The key principle is to identify the actual network path rather than relying on the label "private subnet."

---

### Scenario: PostgreSQL is unreachable from the application, but both resources are in the same VPC. What do you check?

**Answer:**

Check in this order:

```text
DNS
 ↓
Destination IP
 ↓
Route
 ↓
Security Group
 ↓
NACL
 ↓
PostgreSQL listener
 ↓
Authentication
```

Same-VPC placement does not eliminate the need for correct security and service configuration.

---

### Scenario: An application can access the Internet but cannot access S3 privately. What do you investigate?

**Answer:**

Check:

- VPC endpoint configuration.
- Endpoint type.
- Route table association for gateway endpoints.
- Endpoint network interfaces for interface endpoints.
- Private DNS behavior where applicable.
- Endpoint policy.
- Security Groups for interface endpoints.
- IAM permissions.
- S3 bucket policy.
- DNS resolution.

The application may have working Internet access through NAT while the intended private S3 path is incorrectly configured.

---

### Scenario: A developer says, "The Security Group allows port 443, so the request must work." How do you respond?

**Answer:**

Port authorization is only one part of connectivity.

The complete path may still fail because of:

```text
DNS
Route
NACL
Security Group
Gateway
TLS
Application Listener
Application Logic
```

A Security Group rule means the Security Group is not blocking that specific traffic. It does not guarantee end-to-end application success.

---

## Interview Traps

### Trap: "Security Groups are stateless."

**Correct answer:**

Security Groups are stateful.

NACLs are stateless.

---

### Trap: "NACLs only support allow rules."

**Correct answer:**

NACLs support both allow and deny rules.

---

### Trap: "Security Groups are attached to subnets."

**Correct answer:**

Security Groups are associated with network interfaces/resources, while NACLs are associated with subnets.

---

### Trap: "A private subnet cannot access the Internet."

**Correct answer:**

A private subnet can have outbound Internet access through a NAT Gateway or another appropriate egress architecture without assigning public IP addresses to the private workloads.

---

### Trap: "If the route exists, the connection is secure."

**Correct answer:**

A route establishes a possible network path. Security controls still determine whether the traffic is allowed.

---

### Trap: "A VPC is secure because it is isolated."

**Correct answer:**

VPC isolation is only one security layer. Workloads can still be compromised through application vulnerabilities, excessive IAM permissions, exposed services, weak credentials, or overly permissive internal networking.

---

## Diagnostic CLI Commands

### Inspect Security Groups

```bash
aws ec2 describe-security-groups \
  --query 'SecurityGroups[*].[GroupId,GroupName,VpcId,IpPermissions]' \
  --output json
```

### Inspect Network ACLs

```bash
aws ec2 describe-network-acls \
  --query 'NetworkAcls[*].[NetworkAclId,VpcId,Associations,Entries]' \
  --output json
```

### Inspect ENIs

```bash
aws ec2 describe-network-interfaces \
  --query 'NetworkInterfaces[*].[NetworkInterfaceId,SubnetId,PrivateIpAddress,Groups[*].GroupId]' \
  --output table
```

### Inspect Route Tables

```bash
aws ec2 describe-route-tables \
  --query 'RouteTables[*].[RouteTableId,VpcId,Routes]' \
  --output json
```

### Inspect VPC Attributes

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id vpc-xxxxxxxx \
  --attribute enableDnsSupport
```

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id vpc-xxxxxxxx \
  --attribute enableDnsHostnames
```

---

## Security Design Checklist

Use this checklist when reviewing a production VPC:

| Area | Security Check |
|---|---|
| Public exposure | Only required resources are Internet-facing |
| Load balancer | Public entry point is intentional |
| Applications | Application workloads are private where possible |
| Databases | No direct Internet exposure |
| Security Groups | Least-privilege rules |
| Security Group references | Prefer workload relationships over broad CIDRs |
| NACLs | Rules are intentional and documented |
| Routing | No unintended network paths |
| NAT | Egress is intentionally controlled |
| VPC endpoints | Private AWS service access used where appropriate |
| IAM | Workloads use least-privilege roles |
| Secrets | Credentials are not hard-coded |
| Encryption | Sensitive communication uses TLS/encryption |
| IPv6 | IPv6 rules are reviewed when enabled |
| Logging | Network and application visibility is available |
| Monitoring | Security-sensitive changes and failures are monitored |
| Multi-account | Production and non-production access is separated |
| Connectivity | Cross-VPC access is explicitly controlled |

## Key Takeaways

- **Security Groups are stateful workload-level firewalls**, while **Network ACLs are stateless subnet-level controls** that support explicit allow and deny rules.
- **Routing and authorization are different concerns**: a route creates a possible network path, while Security Groups, NACLs, and other controls determine whether traffic is permitted.
- **Least privilege should be expressed through explicit workload relationships**, such as `API-SG → DB-SG:5432`, instead of broad rules such as `0.0.0.0/0`.
- **Private subnets reduce Internet exposure but do not make workloads inherently secure**; production security requires layered network, identity, encryption, application, and monitoring controls.
- **Strong VPC security troubleshooting follows the complete path**: DNS → destination IP → route → NACL → Security Group → gateway/endpoint → service listener → authentication/application behavior.