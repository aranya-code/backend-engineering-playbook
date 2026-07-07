# Route 53 Resolver (Hybrid DNS)

Route 53 Resolver provides DNS resolution *within* a VPC by default (every VPC gets one, reachable at the base of its CIDR range plus two, e.g. `10.0.0.2`), and extends to hybrid on-premises/AWS DNS resolution via Inbound and Outbound endpoints.

## The Default In-VPC Resolver

Every VPC automatically has a Resolver answering queries for:
- Public DNS names (recursively, out to the internet)
- Private hosted zones associated with that VPC
- Internal VPC DNS (e.g., `.internal` hostnames for EC2 instances, if enabled)

This is what's answering DNS queries inside your VPC even if you've never explicitly configured anything.

## Outbound Endpoints

Let resources inside a VPC resolve DNS names hosted **on-premises** (or in another network reachable via VPN/Direct Connect), by forwarding specific domain queries to on-prem DNS servers via conditional forwarding rules.

**Use case:** an EC2 instance needs to resolve `internal-app.corp.local`, which only your on-premises DNS server knows about.

## Inbound Endpoints

The reverse — let on-premises systems resolve Route 53 private hosted zone records, by giving on-prem DNS servers an entry point into the VPC's Resolver.

**Use case:** an on-premises server needs to resolve `db.internal.example.com`, a name that only exists in a Route 53 private hosted zone.

## Architecture

```text
On-Premises DNS Server
     ↕ (conditional forwarding both directions)
Route 53 Resolver Inbound/Outbound Endpoints (in a VPC)
     ↕
VPC Private Hosted Zones / Internet
```

## Resolver Rules

Forwarding behavior is controlled by **Resolver Rules**, which can be shared across accounts via AWS Resource Access Manager (RAM) — a common pattern in multi-account organizations where a central network account owns the Resolver endpoints and rules, shared out to application accounts.

## Senior-Level Considerations

- This is the piece that makes "hybrid cloud" DNS actually work day-to-day, rather than requiring every team to hardcode IPs or maintain separate DNS infrastructure
- Query Logging (a separate Resolver feature) can log all DNS queries made within a VPC to CloudWatch Logs, S3, or Kinesis Data Firehose — valuable both for security investigation and for understanding what a legacy application is actually trying to resolve
