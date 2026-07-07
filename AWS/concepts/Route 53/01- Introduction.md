# What is Amazon Route 53?

Amazon Route 53 is AWS's highly available, scalable DNS (Domain Name System) web service. It handles domain registration, DNS record management, health checking, and intelligent traffic routing — all backed by a 100% availability SLA, one of the few AWS services with that guarantee.

## Why the Name "Route 53"?

- **Route** → routes internet traffic to the correct destination
- **53** → the standard port number DNS uses (both TCP and UDP)

## Simple Mental Model

Think of Route 53 as the internet's phonebook. A user types `www.example.com`; Route 53 resolves it to an IP address like `3.110.24.5` so the browser knows where to connect.

## What Problems Does Route 53 Solve?

- **Human-readable addressing** — nobody memorizes IP addresses
- **Global traffic distribution** — routing users to the closest or healthiest endpoint
- **Automatic failover** — removing unhealthy endpoints from rotation without manual intervention
- **Hybrid connectivity** — resolving DNS consistently across AWS and on-premises networks

## Core Features

| Feature | Purpose |
|---|---|
| Domain Registration | Buy and manage domain names directly through AWS |
| DNS Management | Host and serve DNS records for a domain |
| Health Checks | Monitor endpoint health and availability |
| Traffic Routing | Route requests using policies (latency, geo, weighted, failover, etc.) |
| Route 53 Resolver | Hybrid DNS resolution between AWS and on-premises |
| DNSSEC | Cryptographically sign DNS responses against spoofing |

## Why It Matters at a Senior Level

DNS is often the first hop in every request path, and it's invisible until it breaks. A misconfigured TTL, a missed health check, or an unplanned failover routing policy can take down an otherwise healthy application. Route 53 sits at the intersection of networking, availability architecture, and cost — understanding it well is foundational to designing multi-region, highly available systems.

## Common Use Cases

- Hosting DNS for production domains
- Multi-region active-active or active-passive architectures
- Blue-green and canary deployments via weighted routing
- Disaster recovery via health-check-driven failover
- Hybrid cloud DNS resolution
