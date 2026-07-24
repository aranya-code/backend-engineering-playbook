# Common Interview Questions

This section covers frequently asked VPC interview questions at the senior DevOps / solutions architect level. Each question includes a detailed answer with the depth expected in technical interviews.

---

# Fundamentals

## Q1: What is a VPC and why is it important?

A VPC is a logically isolated virtual network within AWS where you deploy resources. It provides complete control over IP addressing, subnets, routing, gateways, and security controls.

It is important because without a VPC, resources would run on shared, flat networks with no isolation. VPCs provide network segmentation, security boundaries, and compliance-grade isolation.

---

## Q2: What is the difference between a public and private subnet?

The difference is determined by the **route table**, not a subnet property.

- A **public subnet** has a route table entry with `0.0.0.0/0 → Internet Gateway`. Instances can have public IPs and are reachable from the internet.
- A **private subnet** has no route to an Internet Gateway. Instances use a NAT Gateway for outbound internet (if needed) and are unreachable from the internet.

---

## Q3: How many IP addresses does AWS reserve per subnet, and what are they?

AWS reserves **5 IP addresses** in every subnet:

| Address | Purpose |
|---------|---------|
| x.x.x.0 | Network address |
| x.x.x.1 | VPC router |
| x.x.x.2 | DNS server |
| x.x.x.3 | Reserved for future use |
| x.x.x.255 | Broadcast address (not supported) |

A /24 subnet has 256 − 5 = **251 usable IPs**.

---

# Security

## Q4: What is the difference between Security Groups and NACLs?

| Feature | Security Groups | NACLs |
|---------|----------------|-------|
| Scope | Instance (ENI) level | Subnet level |
| Statefulness | Stateful (return traffic automatic) | Stateless (return traffic must be allowed) |
| Rule types | Allow only | Allow and Deny |
| Evaluation | All rules evaluated | In order (first match wins) |
| Default | Deny all inbound, allow all outbound | Allow all (default NACL) |

Security Groups are the primary control. NACLs are additional guardrails.

---

## Q5: Why do NACLs need ephemeral port rules?

Because NACLs are **stateless**. When an inbound request on port 443 is allowed, the response goes back on an ephemeral port (1024–65535). Since NACLs don't track state, you must explicitly allow outbound ephemeral ports for the response to reach the client.

---

## Q6: What is security group chaining and why is it recommended?

Security group chaining means referencing other security groups as sources/destinations instead of CIDR ranges.

Example: App SG allows port 8080 from `sg-alb` (the ALB's security group) instead of `10.0.1.0/24`.

Benefits:
- Rules automatically apply to new instances in the referenced SG
- No updates needed when IPs change
- Cleaner and more maintainable

---

# Gateways and Connectivity

## Q7: What is the difference between an Internet Gateway and a NAT Gateway?

| Feature | Internet Gateway | NAT Gateway |
|---------|-----------------|-------------|
| Direction | Bidirectional | Outbound only |
| Subnet type | Public | Private (deployed in public) |
| Cost | Free | ~$32/month + data processing |
| HA | Fully redundant across AZs | AZ-scoped (deploy per AZ) |

IGW enables full internet access. NAT Gateway enables private instances to initiate outbound connections only.

---

## Q8: How do you make a NAT Gateway highly available?

Deploy **one NAT Gateway per Availability Zone**. Each AZ's private subnet route table points to its own NAT Gateway. If an AZ fails, instances in other AZs are unaffected.

---

## Q9: What are VPC Endpoints and why should you use them?

VPC Endpoints provide private connectivity to AWS services without traversing the internet.

**Gateway Endpoints** (S3, DynamoDB) — free, route table-based.
**Interface Endpoints** (200+ services) — ENI-based, support security groups, ~$0.01/hr.

Benefits: improved security (no internet exposure), lower cost (less NAT Gateway traffic), better performance, compliance.

---

## Q10: What is the difference between VPC Peering and Transit Gateway?

| Feature | VPC Peering | Transit Gateway |
|---------|------------|----------------|
| Model | Point-to-point | Hub-and-spoke |
| Transitive | No | Yes |
| Scalability | Poor (N² connections) | Excellent (5,000 attachments) |
| VPN/DX support | No | Yes |
| Cost | Free (data charges) | ~$0.05/hr per attachment |

Use VPC Peering for 2-3 simple VPC connections. Use Transit Gateway for 4+ VPCs, hybrid connectivity, or centralized management.

---

## Q11: What is the difference between Site-to-Site VPN and Direct Connect?

| Feature | VPN | Direct Connect |
|---------|-----|---------------|
| Connection | Encrypted, over internet | Dedicated private fiber |
| Bandwidth | Up to 1.25 Gbps/tunnel | 1/10/100 Gbps |
| Latency | Variable | Consistent, low |
| Setup time | Minutes | Weeks to months |
| Cost | Low (~$0.05/hr) | Higher |
| Encryption | Built-in (IPsec) | Not by default |

Best practice: Direct Connect primary + VPN backup. Run VPN over DX for encryption.

---

# Architecture and Design

## Q12: How would you design a VPC for a production three-tier web application?

```text
VPC (10.0.0.0/16), 2+ AZs:

Public Subnets:  ALB, NAT Gateways
Private Subnets: EC2/ECS (app tier), route to NAT GW
Data Subnets:    RDS Multi-AZ, ElastiCache, no internet route

Security:
- SG chaining: ALB-SG → App-SG → DB-SG
- NACLs as subnet guardrails
- VPC Flow Logs enabled

Endpoints: S3 (gateway), DynamoDB (gateway), 
          Secrets Manager, ECR, SSM (interface)
```

---

## Q13: How do you reduce NAT Gateway costs?

1. Deploy **S3 and DynamoDB Gateway Endpoints** (free) — this removes S3/DynamoDB traffic from NAT.
2. Use **Interface Endpoints** for frequently accessed services (Secrets Manager, ECR, CloudWatch).
3. Review which private instances truly need internet access.
4. Consolidate outbound traffic patterns.
5. Consider a **private-only VPC** with all access via endpoints for maximum savings.

---

## Q14: What is a private-only VPC and when would you use it?

A VPC with **no Internet Gateway and no NAT Gateway**. All AWS service access is through VPC Endpoints.

Use when:
- Workloads don't need internet access
- Security/compliance requires no internet exposure
- You want to eliminate NAT Gateway costs
- Sensitive data processing environments

You must deploy Interface Endpoints for every AWS service the workload needs (ECR, SSM, Secrets Manager, CloudWatch, KMS, STS, etc.).

---

## Q15: How does VPC Flow Logs help with security?

Flow Logs capture network flow metadata (source, destination, ports, action) at VPC/subnet/ENI level.

Security uses:
- Detect rejected connection attempts (unauthorized access)
- Monitor for data exfiltration (unusual outbound volume)
- Identify port scanning patterns
- Audit compliance (prove only authorized traffic flows)
- Feed into GuardDuty for automated threat detection
- Analyze with Athena for forensic investigation

---

## Q16: Explain the traffic flow when a user accesses a web application in a VPC.

```text
1. User → DNS resolution (Route 53)
2. User → CloudFront edge (if CDN enabled)
3. CloudFront → ALB (in public subnet)
4. ALB → NACL (subnet-level check, stateless)
5. ALB → Security Group (instance-level check, stateful)
6. ALB → EC2/ECS (in private subnet, via SG chaining)
7. EC2 → Security Group check → RDS (in data subnet)
8. RDS response → back through same path
9. NACLs re-evaluated on return (stateless)
10. Security Groups NOT re-evaluated (stateful)
```

---

## Q17: What happens when you create a VPC?

AWS automatically creates:
- A **main route table** (with local route only)
- A **default security group** (allows all traffic within the group)
- A **default NACL** (allows all inbound and outbound)

You must manually create:
- Subnets
- Internet Gateway (and attach it)
- NAT Gateways
- Additional route tables
- Custom security groups

---
