# Elastic IP

## Definition

A static public IPv4 address allocated to your AWS account, which you control and can attach to (or move between) EC2 instances independently of any single instance's own lifecycle.

## Why It Exists

A regular EC2 instance's public IP changes every time the instance stops and starts (it may even launch on entirely different underlying hardware). For anything that other systems need to reliably reach at a fixed address — DNS records pointing at it, hardcoded firewall allow-lists, external partner integrations — a changing IP is a real operational problem. An Elastic IP solves this by decoupling the public address from any specific instance's lifecycle.

## Key Behaviors

- Remains fixed and under your control even if the attached instance is stopped and restarted
- Can be **remapped** to a different instance almost instantly — the basis for simple, fast manual failover (attach the EIP to a healthy standby instance if the primary fails)
- Only free while **attached to a running instance** — an allocated-but-unattached Elastic IP, or one attached to a *stopped* instance, incurs an hourly charge specifically to discourage hoarding unused addresses (IPv4 address space is a genuinely scarce, AWS-metered resource)

## Real-World Usage

- Bastion hosts, where external users/scripts need a stable, known IP to connect through
- NAT instances (the self-managed alternative to a NAT Gateway) needing a consistent outbound public IP
- Legacy integrations with partners who whitelist by static IP rather than DNS name

## Senior-Level Considerations

- An unattached or stopped-instance Elastic IP quietly accruing hourly charges is a genuinely common, easy-to-miss cost leak in real AWS accounts — a periodic audit for allocated-but-unused EIPs is worth building into routine cost review
- Modern architectures increasingly prefer an Application Load Balancer (with a stable DNS name, via Route 53 Alias records) over a bare Elastic IP on an individual instance — the load balancer's DNS name doesn't change even as the instances behind it scale, are replaced, or fail over, which is generally more robust than manually remapping an EIP
- AWS accounts have a default (soft) limit on the number of Elastic IPs that can be allocated, specifically to prevent IPv4 address hoarding at scale — a limit increase can be requested if genuinely needed, but hitting it unexpectedly is often itself a sign of unused EIPs that were never cleaned up
