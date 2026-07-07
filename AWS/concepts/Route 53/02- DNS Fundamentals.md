# DNS Fundamentals

Route 53 is fundamentally a DNS service, so understanding DNS itself is the prerequisite for understanding everything else in this folder.

## What is DNS?

DNS (Domain Name System) translates human-readable domain names into machine-readable IP addresses.

```bash
google.com → 142.250.183.14
```

Without DNS, every user would need to memorize IP addresses for every service they use.

## DNS Resolution Flow

```text
User
 ↓
Browser Cache
 ↓
OS Cache
 ↓
ISP DNS Resolver (Recursive Resolver)
 ↓
Root DNS Server
 ↓
TLD Server (.com, .org, etc.)
 ↓
Authoritative Nameserver (Route 53 Hosted Zone)
 ↓
Application Server
```

Each layer caches results according to TTL, so most lookups never travel the full chain — they're answered from a cache closer to the user.

## Recursive vs. Authoritative

- **Recursive resolver** — does the legwork of walking the DNS hierarchy on the client's behalf (e.g., your ISP's resolver, or `8.8.8.8`)
- **Authoritative nameserver** — holds the actual DNS records for a domain and gives the definitive answer. Route 53 hosted zones are authoritative nameservers.

## Key DNS Terms

| Term | Meaning |
|---|---|
| Domain | A registered name, e.g. `example.com` |
| Subdomain | A name under a domain, e.g. `api.example.com` |
| DNS Record | A single mapping entry (name → value) |
| Hosted Zone | A container of DNS records for a domain (Route 53's term for a zone file) |
| Nameserver | A server that answers DNS queries for a zone |
| TTL | How long a resolver may cache a record before re-querying |
| Zone Apex / Root Domain | The domain itself with no subdomain, e.g. `example.com` (not `www.example.com`) |
| SOA Record | Start of Authority — metadata about the zone (primary nameserver, refresh intervals, etc.) |

## Negative Caching

Resolvers also cache the *absence* of a record (an NXDOMAIN response), governed by the negative caching TTL defined in the zone's SOA record. This matters operationally: if you delete a record too early relative to your negative TTL, some resolvers may have already cached "this doesn't exist" and take longer to pick up a re-added record than you'd expect.

## Why This Matters for Route 53

Every Route 53 feature — Alias records, routing policies, health checks — is built on top of this basic resolution model. Weighted routing, for instance, doesn't change *how* DNS resolution works; it changes *what answer* the authoritative nameserver gives when queried.
