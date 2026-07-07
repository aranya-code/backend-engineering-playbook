# Alias Records

An Alias record is Route 53's AWS-specific extension that behaves like a CNAME but without CNAME's limitations.

## How It's Different From a CNAME

A CNAME is a *real* DNS record type recognized by every DNS server on earth. An Alias record is **not** a standard DNS record type at all — it's a Route 53-specific construct. When a query hits an Alias record, Route 53 resolves the target **internally**, server-side, and returns the appropriate A/AAAA answer directly. The client never sees a CNAME-style redirect; from the outside it looks like a normal A record response.

This internal resolution is exactly what allows Alias records to bypass CNAME's biggest restriction.

## Why Alias Records Exist

| CNAME | Alias |
|---|---|
| Standard DNS record | AWS-specific |
| Cannot be used at the zone apex | Works at the zone apex |
| Extra DNS lookup for the client | Resolved server-side by Route 53 — no extra client-facing lookup |
| No AWS-awareness | Automatically tracks target IP changes (e.g., when an ALB's IPs rotate) |
| Billed per query | No charge for queries to AWS resource Alias targets |

## Supported Targets

- Elastic Load Balancers (ALB, NLB, CLB)
- CloudFront distributions
- S3 static website endpoints
- API Gateway custom domain endpoints
- VPC endpoints (interface endpoints)
- Global Accelerator
- Another record in the *same* hosted zone

## Zone Apex Support — Why It Matters

Most companies want their root domain (`example.com`, not just `www.example.com`) to point at a load balancer or CloudFront distribution. A CNAME can't do this at all. Before Alias records existed, the common workaround was to A-record the apex to a static IP and accept that it wouldn't track load balancer IP changes — a real operational hazard, since ALB/CloudFront IPs are not guaranteed stable. Alias records solve this cleanly by resolving dynamically at query time.

## Practical Notes

- Alias records still show as type A or AAAA in the console/API; "Alias" is a checkbox/flag on the record, not a distinct record type in the data model
- Because resolution happens inside Route 53, Alias records have no visible TTL to configure for AWS target types — Route 53 manages the effective caching behavior
- If you ever see "special AWS DNS name behaves differently than a plain CNAME would," Alias records are almost always the explanation
