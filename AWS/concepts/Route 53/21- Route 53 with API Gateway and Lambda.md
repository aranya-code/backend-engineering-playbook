# Route 53 with API Gateway and Lambda

The standard pattern for exposing serverless APIs under a custom domain.

## Architecture

```text
User
 ↓
Route 53 (Alias Record)
 ↓
API Gateway Custom Domain
 ↓
API Gateway (REST or HTTP API)
 ↓
Lambda Function(s)
```

## Setup Essentials

1. Request an ACM certificate for the custom domain (region depends on endpoint type — `us-east-1` for edge-optimized, same region as the API for regional)
2. Create a Custom Domain Name resource in API Gateway, attaching the certificate
3. Map the custom domain to a specific API and stage (base path mapping)
4. Create an Alias record in Route 53 pointing to the API Gateway custom domain's target domain name

## Edge-Optimized vs. Regional Endpoints

- **Edge-optimized** — requests are routed through CloudFront's edge network first, reducing latency for geographically distributed clients; certificate must be in `us-east-1`
- **Regional** — requests go directly to the API Gateway in its region, with no CloudFront layer in front — lower latency for clients already close to that region, and it's the endpoint type to use if you want to put your *own* CloudFront distribution in front for more control over caching/WAF rules

## Why This Matters for Serverless Architectures

This pattern lets a fully serverless API (API Gateway + Lambda, no servers, no load balancer) still present a clean custom domain rather than the default `execute-api` AWS-generated hostname — essential for any production-facing API.

## Senior-Level Considerations

- Base path mapping lets multiple API versions or services share one custom domain under different paths (e.g., `api.example.com/v1`, `api.example.com/v2`, potentially backed by entirely different API Gateway APIs)
- As with ALB and CloudFront, always use an Alias record here — API Gateway's underlying infrastructure addresses are not something you should ever hardcode
