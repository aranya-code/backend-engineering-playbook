# Common Interview Questions

## Beginner

**Q1. What is Amazon Route 53?**
A highly available, scalable DNS web service used for domain registration, DNS management, health checking, and intelligent traffic routing, backed by a 100% availability SLA.

**Q2. What is a Hosted Zone?**
A container for DNS records belonging to a domain — Route 53's version of a DNS zone file. Can be public (internet-resolvable) or private (VPC-only).

**Q3. What's the difference between a CNAME and an Alias record?**

| CNAME | Alias |
|---|---|
| Standard DNS record type | AWS-specific, resolved server-side |
| Cannot be used at the zone apex | Works at the zone apex |
| Extra DNS lookup | No extra client-facing lookup |
| Billed per query | Free for AWS resource targets |

**Q4. What's the difference between a public and private hosted zone?**
Public zones are resolvable from the internet; private zones are resolvable only within associated VPC(s), and never answer queries from outside.

**Q5. Why use health checks?**
To enable automatic, health-aware routing decisions — failover, exclusion from Multivalue Answer responses, etc. — without manual DNS intervention.

## Intermediate

**Q6. Explain the seven Route 53 routing policies.**
Simple, Weighted, Latency-based, Failover, Geolocation, Geoproximity, and Multivalue Answer — covering everything from single-resource routing to health-aware global traffic distribution. (See the dedicated routing policy files for depth on each.)

**Q7. Why must Alias records be used instead of A records for ALB/CloudFront targets?**
Because those resources' underlying IP addresses can change at any time; an Alias record resolves dynamically at query time and always reflects the current target, while a hardcoded A record would eventually go stale and break.

**Q8. What happens if a geolocation routing policy has no default record?**
Users from any country not explicitly mapped get no DNS answer at all — always configure a Default record for geolocation routing.

**Q9. How does TTL affect failover time?**
Failover routing changes what a *new* DNS query returns, but clients/resolvers that already cached the old answer won't see the change until their cached TTL expires — actual failover time is bounded by TTL, not instantaneous.

**Q10. What is DNSSEC and what does it protect against?**
Cryptographic signing of DNS responses so resolvers can verify authenticity, protecting against cache poisoning and DNS spoofing. Requires both signing on the hosted zone and a Delegation Signer record at the registrar.

## Senior / Advanced

**Q11. Explain shuffle sharding and why Route 53 uses it.**
A technique that assigns each hosted zone a different combination of nameservers drawn from a larger pool, rather than every zone sharing the same fixed set — isolating the blast radius of any partial infrastructure degradation to a smaller, semi-random subset of zones rather than everyone at once.

**Q12. Why is DNS-based failover not sufficient as a complete DR strategy on its own?**
It only controls where new DNS lookups point; it does nothing for in-flight connections, data replication, or application state consistency between regions. It's a necessary component of DR, not a complete one.

**Q13. What is subdomain takeover, and how do you prevent it?**
When a DNS record (CNAME/Alias) points at a resource that's since been deleted or released (an S3 bucket, an old CloudFront distribution), an attacker can claim that same resource name and effectively hijack the subdomain. Prevented by promptly cleaning up DNS records whenever the underlying resource is decommissioned, and by regular audits of records pointing at cloud resources.

**Q14. How would you design DNS for a multi-account AWS Organization?**
Typically a centralized "network" account owns the public hosted zone(s) and Route 53 Resolver endpoints/rules, sharing resolver rules via AWS RAM to application accounts, with subdomains delegated (via NS records) to individual application-account-owned hosted zones where teams need autonomy.

**Q15. Latency-based routing sent a user to a region that felt slower than expected — why might that happen?**
Latency routing decisions are based on the *resolver's* inferred location, not necessarily the end user's actual location — if the user's resolver (e.g., a public DNS provider or corporate VPN exit point) is geographically distant from the user themselves, the routing decision will reflect the resolver's position, not the user's.
