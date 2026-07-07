# Route 53 with S3

A common pattern for hosting static websites entirely on serverless infrastructure — no EC2, no servers to manage.

## Architecture

```text
User
 ↓
Route 53 (Alias Record)
 ↓
S3 Static Website Endpoint
```

## Setup Steps

1. Create an S3 bucket named **exactly** matching the domain (e.g., a bucket literally named `www.example.com` for that hostname — S3 website endpoints match bucket name to hostname)
2. Enable static website hosting on the bucket, specifying an index document (and optionally an error document)
3. Set bucket policy/public access settings to allow public reads (or front it with CloudFront and keep the bucket private — see the next file)
4. Create an **Alias** record in Route 53 pointing to the S3 website endpoint

## Why It Must Be an Alias, Not a CNAME

The S3 website endpoint is itself a domain name (e.g., `example-com.s3-website-us-east-1.amazonaws.com`), and if you want this working at the zone apex (`example.com`, not just `www.example.com`), a CNAME won't work there at all — this is the exact zone-apex limitation Alias records exist to solve.

## Limitations of This Pattern (Uncached)

- No HTTPS support directly on an S3 website endpoint — S3 website endpoints are HTTP-only
- No custom error pages beyond the single configured error document
- No caching/CDN benefit — every request hits S3 directly

Because of the HTTPS gap alone, production setups almost always add CloudFront in front of S3 rather than pointing Route 53 straight at the S3 website endpoint — see the next file.

## Senior-Level Considerations

- This pattern is genuinely serverless and can be extremely cheap for low-to-moderate traffic static sites, but the lack of native HTTPS makes bare S3-website-endpoint hosting unsuitable for anything production-facing today
- Bucket naming must match the hostname exactly for the S3 website endpoint approach — a very common first-time setup mistake
