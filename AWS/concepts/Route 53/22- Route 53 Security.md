# Route 53 Security

## IAM Integration

All Route 53 management actions (creating records, hosted zones, health checks) are controlled through IAM policies. Common production practice: grant a CI/CD pipeline or automation role narrow permissions scoped to specific hosted zone IDs, rather than blanket `route53:*` access — a compromised or buggy pipeline shouldn't be able to modify DNS for zones it has no business touching.

## DNSSEC (Domain Name System Security Extensions)

DNSSEC adds cryptographic signing to DNS responses, allowing resolvers to verify that a response genuinely came from the authoritative source and wasn't tampered with or spoofed in transit (protecting against cache poisoning and man-in-the-middle DNS attacks).

Enabling DNSSEC in Route 53 requires two separate steps:
1. **Signing** — enabled on the hosted zone itself, which starts cryptographically signing records
2. **Chain of trust** — a Delegation Signer (DS) record must be submitted to the parent zone/registrar so validating resolvers can verify the signature chain all the way up

Both the hosted zone (signing) and the domain registration (DS record submission) need to be configured — enabling one without the other leaves DNSSEC incomplete.

## Query Logging

Route 53 can log all public DNS queries against a hosted zone to CloudWatch Logs, giving visibility into query volume, query types, and source — useful both for security monitoring (detecting unusual query patterns) and for capacity/cost analysis.

## Protecting Against DNS-Based Attacks

- **DDoS** — Route 53's anycast architecture inherently absorbs and distributes volumetric attacks across its global network; AWS Shield Standard is automatically included, with Shield Advanced available for additional protection and cost protection guarantees
- **Domain hijacking prevention** — enable a registrar transfer lock, keep WHOIS/contact information current (so ownership verification during a dispute goes smoothly), and use MFA on the AWS account managing the domain
- **Subdomain takeover** — a genuinely common real-world vulnerability: if a CNAME or Alias record points to a resource (e.g., an S3 bucket, an old CloudFront distribution) that's since been deleted, an attacker who claims that same resource name can effectively take over the subdomain. Regularly audit DNS records for ones pointing at decommissioned resources

## Senior-Level Considerations

- Subdomain takeover is worth calling out specifically in any security review — it's a classic "looks fine, isn't" issue that automated scanners increasingly check for, and it's entirely preventable by keeping DNS hygiene tight when resources are decommissioned
- CAA records (see DNS Record Types) are a low-effort, high-value hardening step frequently skipped simply because teams don't know they exist
