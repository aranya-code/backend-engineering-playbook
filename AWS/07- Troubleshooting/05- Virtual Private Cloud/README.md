# README.md

## Overview

This directory contains production-oriented troubleshooting guidance for **Amazon VPC** networking failures.

The material is organized around progressively deeper diagnostic scenarios, from foundational VPC troubleshooting through routing, DNS, connectivity, observability, and production incident diagnosis.

The recommended approach is to troubleshoot network failures from the infrastructure boundary inward:

```text
Workload
   ↓
ENI
   ↓
Subnet
   ↓
Route Table
   ↓
Security Group / NACL
   ↓
AWS Network Path
   ↓
Destination
   ↓
Application
```

Use the documents as operational references during development, incident response, architecture reviews, and technical interviews.

## Quick Navigation

| # | Topic | Coverage |
|---|---|---|
| 01 | [VPC Troubleshooting Methodology](01-%20VPC%20Troubleshooting%20Methodology.md) | Foundational VPC troubleshooting methodology and common diagnostic patterns. |
| 02 | [Subnet Connectivity Issues](02-%20Subnet%20Connectivity%20Issues.md) | Route selection, route-table associations, missing routes, and blackhole routes. |
| 03 | [Route Table and Routing Issues](03-%20Route%20Table%20and%20Routing%20Issues.md) | Security Group connectivity failures, inbound/outbound rules, and SG references. |
| 04 | [Internet Gateway Connectivity Issues](04-%20Internet%20Gateway%20Connectivity%20Issues.md) | Stateless NACL behavior, rule evaluation, ephemeral ports, and subnet-level filtering. |
| 05 | [NAT Gateway Connectivity Issues](05-%20NAT%20Gateway%20Connectivity%20Issues.md) | Public and private subnet Internet connectivity and NAT troubleshooting. |
| 06 | [Security Group Issues](06-%20Security%20Group%20Issues.md) | Gateway and interface endpoint connectivity, routing, policies, DNS, and endpoint Security Groups. |
| 07 | [Network ACL Issues](07-%20Network%20ACL%20Issues.md) | Detailed NACL troubleshooting and production connectivity failures. |
| 08 | [VPC Endpoint Connectivity Issues](08-%20VPC%20Endpoint%20Connectivity%20Issues.md) | Systematic diagnosis of VPC endpoint connectivity failures. |
| 09 | [DNS and VPC Resolution Issues](09-%20DNS%20and%20VPC%20Resolution%20Issues.md) | VPC DNS, Route 53, private hosted zones, Resolver, and name-resolution failures. |
| 10 | [VPC Peering Connectivity Issues](10-%20VPC%20Peering%20Connectivity%20Issues.md) | VPC peering routes, CIDR overlap, security controls, and cross-VPC connectivity. |
| 11 | [Transit Gateway Connectivity Issues](11-%20Transit%20Gateway%20Connectivity%20Issues.md) | Transit Gateway attachments, route tables, propagation, and multi-VPC connectivity. |
| 12 | [VPN Connectivity Issues](12-%20VPN%20Connectivity%20Issues.md) | Site-to-Site VPN tunnels, routing, BGP, hybrid connectivity, and tunnel failures. |
| 13 | [Flow Log Based Troubleshooting](13-%20Flow%20Log%20Based%20Troubleshooting.md) | VPC Flow Logs, ACCEPT/REJECT analysis, traffic patterns, and incident investigation. |
| 14 | [Reachability Analyzer and Diagnostic Tools](14-%20Reachability%20Analyzer%20and%20Diagnostic%20Tools.md) | Reachability Analyzer and AWS networking diagnostic capabilities. |
| 15 | [Common Production VPC Failures](15-%20Common%20Production%20VPC%20Failures.md) | Recurring production failure patterns, root causes, and remediation strategies. |
| 16 | [Diagnostic CLI Commands](16-%20Diagnostic%20CLI%20Commands.md) | AWS CLI and host-level commands for systematic VPC diagnosis. |

## Recommended Reading Order

The troubleshooting material is best consumed in layers.

### Foundation

Start with:

- [01- VPC Troubleshooting Basics.md](./01-%20VPC%20Troubleshooting%20Basics.md)
- [02- Route Table Issues.md](./02-%20Route%20Table%20Issues.md)
- [03- Security Group Issues.md](./03-%20Security%20Group%20Issues.md)
- [04- Network ACL Issues.md](./04-%20Network%20ACL%20Issues.md)

These establish the core diagnostic model:

```text
Source
  ↓
ENI
  ↓
Subnet
  ↓
Route Table
  ↓
Security Controls
  ↓
Destination
```

### Connectivity

Then move into service-to-service and cross-network connectivity:

- [05- Internet Gateway and NAT Gateway Issues.md](./05-%20Internet%20Gateway%20and%20NAT%20Gateway%20Issues.md)
- [06- VPC Endpoint Issues.md](./06-%20VPC%20Endpoint%20Issues.md)
- [07- Network ACL Issues.md](./07-%20Network%20ACL%20Issues.md)
- [08- VPC Endpoint Connectivity Issues.md](./08-%20VPC%20Endpoint%20Connectivity%20Issues.md)
- [09- DNS and VPC Resolution Issues.md](./09-%20DNS%20and%20VPC%20Resolution%20Issues.md)

These scenarios are particularly relevant to backend workloads running Django, FastAPI, ECS, EKS, Lambda, PostgreSQL, Redis, and other AWS-managed services.

### Multi-Network Connectivity

For larger production environments:

- [10- VPC Peering Connectivity Issues.md](./10-%20VPC%20Peering%20Connectivity%20Issues.md)
- [11- Transit Gateway Connectivity Issues.md](./11-%20Transit%20Gateway%20Connectivity%20Issues.md)
- [12- VPN Connectivity Issues.md](./12-%20VPN%20Connectivity%20Issues.md)

These cover connectivity beyond a single VPC, including:

```text
VPC
 ├── VPC Peering
 ├── Transit Gateway
 └── Site-to-Site VPN
        ↓
    On-Premises
```

### Observability and Diagnostics

Finally, use:

- [13- Flow Log Based Troubleshooting.md](./13-%20Flow%20Log%20Based%20Troubleshooting.md)
- [14- Reachability Analyzer and Diagnostic Tools.md](./14-%20Reachability%20Analyzer%20and%20Diagnostic%20Tools.md)
- [15- Common Production VPC Failures.md](./15-%20Common%20Production%20VPC%20Failures.md)
- [16- Diagnostic CLI Commands.md](./16-%20Diagnostic%20CLI%20Commands.md)

These are intended as operational references during real incidents.

## Core Diagnostic Model

Most VPC connectivity failures can be reduced to a small number of questions:

| Layer | Diagnostic Question |
|---|---|
| Identity | Am I investigating the correct AWS account and region? |
| Workload | What resource is initiating the connection? |
| ENI | Which network interface and private IP are actually involved? |
| Subnet | Which subnet contains the workload? |
| Routing | Which route table is associated with that subnet? |
| Destination | Is the destination address correct and reachable? |
| Security Group | Does the traffic satisfy stateful SG rules? |
| NACL | Do stateless subnet-level rules permit both directions? |
| AWS Path | Is NAT, IGW, endpoint, peering, TGW, or VPN configured correctly? |
| DNS | Does the hostname resolve to the expected address? |
| Observability | Do Flow Logs show ACCEPT or REJECT traffic? |
| Reachability | Can AWS identify a valid network path? |
| Runtime | Can the workload establish TCP/TLS connectivity? |
| Application | Is the application actually listening and accepting requests? |

## Standard Troubleshooting Flow

```mermaid
flowchart TD
    A[Connectivity Failure] --> B[Verify AWS Account and Region]
    B --> C[Identify Source ENI]
    C --> D[Identify Source Subnet]
    D --> E[Identify Route Table]
    E --> F{Expected Route Exists?}

    F -->|No| G[Fix Routing]
    F -->|Yes| H[Inspect Security Group]

    H --> I[Inspect NACL]
    I --> J[Inspect AWS Network Path]

    J --> K{DNS Required?}
    K -->|Yes| L[Test DNS Resolution]
    K -->|No| M[Test TCP]

    L --> M
    M --> N{TCP Reachable?}

    N -->|No| O[Inspect Flow Logs / Reachability Analyzer]
    N -->|Yes| P[Test TLS / Protocol]

    P --> Q{Application Responds?}
    Q -->|No| R[Inspect Application]
    Q -->|Yes| S[Connectivity Confirmed]
```

## Diagnostic Principle

Do not start with:

> "The Security Group must be blocking it."

Instead, establish evidence layer by layer.

A reliable investigation looks like:

```text
Account / Region
      ↓
Source Resource
      ↓
Source ENI
      ↓
Subnet
      ↓
Route Table
      ↓
Destination
      ↓
Security Group
      ↓
NACL
      ↓
AWS Network Service
      ↓
DNS
      ↓
TCP
      ↓
TLS / Protocol
      ↓
Application
```

This prevents a common production failure mode where engineers repeatedly modify Security Groups without proving that the Security Group is actually responsible.

## Backend Engineering Context

VPC troubleshooting is directly relevant to common backend architectures.

### Django / FastAPI → PostgreSQL

```text
Django / FastAPI
      |
      | TCP 5432
      v
PostgreSQL
```

Typical diagnostic layers:

```text
DNS
→ Route
→ SG
→ NACL
→ TCP
→ PostgreSQL
```

### Application → Redis

```text
API
 |
 | TCP 6379
 v
Redis
```

Validate:

```text
DNS
→ Route
→ SG
→ NACL
→ TCP
→ Redis
```

### Microservice → Microservice

```text
Service A
   |
   | REST / gRPC
   v
Service B
```

Investigate:

```text
Service discovery
→ DNS
→ Route
→ Security Group
→ NACL
→ TCP
→ TLS
→ HTTP/gRPC
```

### Private Application → AWS Service

```text
Private Workload
      |
      v
VPC Endpoint
      |
      v
AWS Service
```

The diagnostic path becomes:

```text
DNS
→ Endpoint
→ Route / ENI
→ Endpoint SG
→ Endpoint Policy
→ AWS Service
```

## Production Troubleshooting Checklist

When responding to a VPC connectivity incident, capture:

- AWS account ID.
- AWS region.
- Source resource.
- Source ENI.
- Source private IP.
- Source subnet.
- Source Security Groups.
- Source route table.
- Destination hostname.
- Destination IP.
- Destination resource.
- Destination Security Groups.
- Relevant NACLs.
- Relevant AWS network service.
- DNS resolution result.
- TCP connectivity result.
- Flow Log evidence.
- Reachability Analyzer result where applicable.
- Recent CloudTrail configuration changes.

Avoid making infrastructure changes until the relevant evidence has been collected.

## Operational Best Practices

- Use read-only diagnostic permissions whenever possible.
- Verify the AWS account and region before investigation.
- Prefer targeted AWS CLI filters over unrestricted resource dumps.
- Use `--query` to extract only relevant fields.
- Keep VPC resources consistently tagged.
- Maintain VPC Flow Logs for environments where network visibility is operationally important.
- Use Reachability Analyzer for supported AWS paths.
- Keep CloudTrail enabled for infrastructure change auditing.
- Maintain standardized incident runbooks.
- Test connectivity from the workload itself, not only from an engineer's workstation.
- Treat DNS, routing, security controls, and application behavior as separate diagnostic layers.
- Make one controlled change at a time and verify the result.

## Interview Perspective

A strong VPC troubleshooting answer should demonstrate a systematic methodology rather than immediately naming a specific AWS service.

For example:

> "I would first identify the source ENI, subnet, destination, and associated route table. Then I would verify the route to the destination, inspect Security Groups and NACLs, validate any NAT, endpoint, peering, Transit Gateway, or VPN path, check DNS resolution, inspect Flow Logs or Reachability Analyzer, and finally test TCP and the application protocol from the workload."

This demonstrates understanding of the complete network path rather than memorization of individual AWS services.

## Key Takeaways

- **Troubleshoot VPC connectivity layer by layer**: resource, ENI, subnet, route table, security controls, network path, DNS, transport, and application.
- **Use evidence instead of assumptions**: verify actual subnet associations, routes, ENIs, Security Groups, NACLs, and AWS network services involved in the path.
- **Combine infrastructure and runtime diagnostics**: AWS CLI, Flow Logs, Reachability Analyzer, DNS tools, TCP tools, TLS tools, and application health checks provide complementary evidence.
- **Production troubleshooting should be repeatable**: standardized commands, tagging, read-only access, observability, CloudTrail, and incident runbooks reduce diagnosis time and operator error.
- **Understand the complete network path** rather than focusing on a single component such as a Security Group or route table.