# Route 53 with CloudFront

The production-grade version of the S3 static-hosting pattern, and broadly the standard way to front any AWS origin with a CDN.

## Architecture

```text
User
 ↓
Route 53 (Alias Record)
 ↓
CloudFront Distribution
 ↓
Origin (S3 / ALB / EC2 / API Gateway / custom)
```

## Why Add CloudFront

- **HTTPS support** — CloudFront provides free TLS via AWS Certificate Manager, solving S3's HTTPS gap directly
- **Caching** — static and cacheable dynamic content served from edge locations near the user, reducing origin load and latency
- **DDoS protection** — CloudFront absorbs and mitigates much of the traffic before it ever reaches your origin, and integrates with AWS Shield
- **Custom domain support** — attach your own domain to the distribution alongside its default `*.cloudfront.net` name

## Setup Essentials

1. Create the CloudFront distribution, pointing at the origin (an S3 bucket, ideally kept **private** and accessed only via Origin Access Control, or an ALB, etc.)
2. Request/attach an ACM certificate for your custom domain (must be in `us-east-1` regardless of where your other resources live — a common gotcha)
3. Add the custom domain as an Alternate Domain Name (CNAME) on the distribution
4. Create an Alias record in Route 53 pointing to the CloudFront distribution's domain name

## Why Alias, Not CNAME, Again

Same reasoning as with S3 — CloudFront distribution domain names are themselves AWS-managed hostnames, and using an Alias record allows this to work at the zone apex, with no extra client-facing DNS lookup, and no charge for the query.

## Senior-Level Considerations

- The `us-east-1`-only requirement for CloudFront's ACM certificate is one of the most common points of confusion for anyone new to this pattern — the distribution itself is global, but the certificate must be requested from that specific region
- Origin Access Control (the modern replacement for the older Origin Access Identity) should be used to ensure the S3 bucket is **not** publicly readable directly — only reachable through CloudFront — closing the gap left by the plain S3-website-endpoint pattern
