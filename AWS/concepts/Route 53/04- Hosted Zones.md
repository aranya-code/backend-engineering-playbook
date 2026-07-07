# Hosted Zones

A Hosted Zone is a container for DNS records belonging to a domain — Route 53's equivalent of a traditional DNS zone file.

```bash
example.com
```

might contain records for:

```bash
www.example.com
api.example.com
mail.example.com
```

## Public Hosted Zones

Resolvable from anywhere on the internet.

**Use cases:** public websites, public APIs, internet-facing applications.

Every public hosted zone automatically gets NS and SOA records at creation, and is billed per zone per month plus per DNS query.

## Private Hosted Zones

Resolvable only from within one or more associated VPCs — queries from the public internet get no answer at all.

**Use cases:** internal microservice discovery, internal databases, corporate/internal-only applications.

Key properties:

- Associated explicitly with one or more VPCs (in the same account or a different one)
- The same domain name can exist as both a public and a private hosted zone simultaneously — this is called **split-horizon DNS**, and it's how you serve different answers to internal vs. external clients for the same name
- DNS queries from an associated VPC use the VPC's Route 53 Resolver (the `.2` address in the VPC's CIDR) to reach the private zone

## Cross-Account Private Hosted Zones

A private hosted zone can be associated with a VPC in a *different* AWS account, which is common in multi-account organizations where a central "network" account owns DNS and application accounts just consume it. This requires an explicit association authorization step from the zone-owning account.

## Zone Delegation

A hosted zone can delegate a subdomain to a different hosted zone (potentially in a different account) by placing NS records for that subdomain pointing to the child zone's nameservers. This is how large organizations split DNS management across teams — e.g., `example.com` managed centrally, but `payments.example.com` delegated to the payments team's own hosted zone.

## Common Pitfalls

- Deleting a hosted zone does **not** release the domain registration — those are separate resources with separate lifecycles
- Forgetting to associate a private hosted zone with a VPC is the most common reason "it resolves from my laptop over VPN but not from the EC2 instance" — check the VPC association list first
- A private and public zone with the *same name* can create confusing debugging sessions if you don't realize split-horizon DNS is in play
