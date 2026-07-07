# Production Best Practices

## Design for Failure at the DNS Layer, Not Just the App Layer

Assume any single region, AZ, or resource can fail, and make sure routing policy + health checks reflect a real failover path — not just a load balancer's internal target health.

## Keep TTLs Deliberately Low on Anything That Might Need to Change Fast

Records tied to failover, active migrations, or blue-green cutovers should run low TTLs (60s or less) as a standing practice, not just something you remember to lower right before a migration.

## Treat DNS Changes Like Code

Manage hosted zone records through infrastructure-as-code (Terraform, CloudFormation, CDK) rather than manual console edits — DNS misconfigurations are exactly the kind of change that benefits from review, version history, and the ability to revert cleanly.

## Test Failover For Real, Regularly

A health check and failover routing policy that have never actually been exercised are a hypothesis, not a verified capability. Run scheduled failover drills (deliberately failing a health check target) to confirm the whole chain — detection, routing shift, secondary readiness — actually works end to end.

## Use Split-Horizon DNS Deliberately, Not Accidentally

If you have both public and private hosted zones for the same domain, document that clearly for the team — it's a common source of "works on my machine (VPN) but not in prod" confusion if engineers don't realize which zone is answering which query.

## Guard the Zone Apex Carefully

Zone apex misconfigurations (accidentally deleting the NS/SOA records, or trying to add a CNAME there) can take an entire domain offline. Apply extra review/approval requirements to apex record changes specifically.

## Audit for Subdomain Takeover Risk Continuously

Any time a resource that a DNS record points to (an S3 bucket, an old ALB, a CloudFront distribution) is decommissioned, remove or repoint the corresponding DNS record in the same change — don't leave dangling records as "cleanup for later."

## Document Ownership of Hosted Zones

In multi-account or multi-team organizations, make it unambiguous which team owns which hosted zone or delegated subdomain — DNS changes made by the wrong team, or duplicated across teams, are a recurring source of production incidents.
