# Troubleshooting AWS Route 53

## Issue 1: DNS Changes Not Reflecting

**Symptoms:** updated a record, but some users still see the old value.

**Possible causes:**
- TTL of the previous record hasn't expired yet on the user's resolver/browser
- A local `hosts` file override
- A stale OS-level DNS cache on the client machine

**Solution:** confirm the change is live at the authoritative source first (`dig` or `nslookup` directly against one of the hosted zone's nameservers, bypassing local caches), then treat propagation as bounded by the *old* TTL — there is no way to force remote caches to drop early.

## Issue 2: Private Hosted Zone Not Resolving from an Instance

**Symptoms:** the record resolves fine over VPN or from a laptop, but not from an EC2 instance in the "right" VPC.

**Possible causes:**
- The private hosted zone isn't associated with that specific VPC
- The instance's DHCP option set isn't using the default VPC resolver
- A custom DNS server configured in the VPC's DHCP options that doesn't forward to the VPC Resolver

**Solution:** verify the VPC association list on the hosted zone first — this is the most common root cause by a wide margin.

## Issue 3: Failover Not Triggering

**Symptoms:** the primary is down, but traffic isn't shifting to the secondary.

**Possible causes:**
- No health check attached to the primary record at all
- Health check is misconfigured (wrong port/path, or checking a shallow endpoint that returns 200 even when the app is actually broken)
- Health check hasn't yet reached quorum failure across the distributed checker fleet

**Solution:** check the health check's current status and recent status history directly in the console before assuming the routing policy itself is broken.

## Issue 4: "Volumes Must Be a Mapping"-Style Config Errors (Terraform/CloudFormation)

**Symptoms:** infrastructure-as-code fails to apply a Route 53 record.

**Possible causes:** most commonly a malformed alias block (missing `zone_id` for the alias target) or attempting to create a CNAME at the zone apex.

**Solution:** validate that alias configurations include both the target DNS name **and** the target's hosted zone ID — a frequently missed field that differs by resource type (ALB, CloudFront, and S3 website endpoints each have their own fixed alias zone ID).

## Issue 5: Unexpected NXDOMAIN After Adding a New Record

**Symptoms:** a brand-new record returns "does not exist" for longer than expected.

**Possible causes:** a resolver cached the *negative* (NXDOMAIN) response from before the record existed, governed by the zone's negative-caching TTL in its SOA record.

**Solution:** query directly against the authoritative nameservers to confirm the record is live, and treat the negative-caching TTL (not the record's own TTL) as the bound on when other resolvers will stop returning the stale NXDOMAIN.
