# Cost Optimization

## What You're Billed For

- Hosted zones (a flat monthly fee per zone)
- DNS queries (per million queries, with lower rates for Alias queries to AWS resources — which are actually **free**)
- Health checks (per check, with a higher rate for checks against endpoints outside AWS, and for "fast" 10-second-interval checks)
- Domain registration (annual, varies by TLD)
- Traffic Flow policy records (billed per policy record, separate from ordinary records)

## Cost Levers

### Prefer Alias Records Over CNAME/A for AWS Targets
Queries to Alias records pointing at AWS resources (ALB, CloudFront, S3, API Gateway) are **not billed** — a direct, easy cost win with zero downside, since Alias records are also functionally superior to CNAME at the zone apex anyway.

### Consolidate Hosted Zones Where Sensible
Each hosted zone carries its own flat monthly charge — dozens of near-empty hosted zones for closely related subdomains can often be consolidated into fewer zones with more records, if organizational/delegation requirements don't require the separation.

### Right-Size Health Check Frequency
"Fast" (10-second) health checks cost more than standard (30-second) checks. Reserve fast checks for endpoints where failover speed genuinely matters; use standard checks elsewhere.

### Avoid Unnecessary Calculated Health Checks
Each health check in a calculated health check's tree is billed individually — a large calculated-check hierarchy can add up faster than it first appears.

### Clean Up Unused Hosted Zones and Health Checks
Decommissioned environments frequently leave orphaned hosted zones and health checks still accruing charges long after the infrastructure they pointed to is gone.

## Senior-Level Considerations

- At real production query volumes, the query cost is usually a rounding error compared to compute/data transfer costs elsewhere in the architecture — but it's still worth eliminating the "billed" cases (CNAME/A to AWS resources) that have a strictly better *and* free alternative
- Domain registration renewal costs vary significantly by TLD (`.com` vs `.io` vs newer gTLDs) — worth factoring into domain choice for cost-sensitive projects with many domains
