# Quick Revision

## Fundamentals
- EC2 = resizable virtual servers, full OS control, IaaS
- Nitro System = modern hypervisor, offloads networking/storage/monitoring to dedicated hardware
- Instance lifecycle: pending → running → (stopping → stopped) → shutting-down → terminated
- Stopped instances: no compute charge, EBS charges continue, RAM lost

## Instance Types
- Naming: `[family][generation][attributes].[size]` — e.g., `c6i.xlarge` = Compute, Gen 6, Intel, XL
- M = general purpose (fixed); T = general purpose (burstable, CPU credits)
- C = compute optimized; R/X/z = memory optimized; I/D/H = storage optimized; P/G/Inf/Trn = accelerated
- Graviton (ARM, suffix `g`) — ~20% cheaper, similar/better performance for most Linux workloads
- T-series: watch `CPUCreditBalance` — hits zero → throttled to baseline (Standard mode)

## Purchasing Options
- On-Demand: no commitment, most expensive per-hour
- Reserved Instances: 1/3-year commitment, up to 72% off, locked to instance config (unless Convertible)
- Savings Plans: commit to $/hour spend, more flexible than RIs, generally preferred today
- Spot: up to 90% off, 2-minute interruption warning, for interruption-tolerant workloads only
- Dedicated Host: per-socket/core license compliance; Dedicated Instance: hardware isolation only

## Access
- Key Pairs: asymmetric crypto, private key never touches AWS
- SSH default users vary by AMI (`ec2-user`, `ubuntu`, `admin`, etc.)
- User Data: bootstrap script, runs as root via cloud-init, pulled from IMDS, 16 KB limit — never put secrets here

## Instance Metadata (IMDS)
- `169.254.169.254` — instance ID, IAM credentials, user data, and more
- IMDSv1 = unauthenticated GET, vulnerable to SSRF (Capital One breach)
- IMDSv2 = PUT for token, then GET with token header — closes off most SSRF paths
- Enforce with `HttpTokens=required`

## Networking
- Security Groups: stateful, instance-level, allow-only
- NACL: stateless, subnet-level, allow AND deny — must configure both inbound and outbound
- Elastic IP: free only while attached to a running instance; unattached/stopped = billed
- Common ports: 22 SSH, 80 HTTP, 443 HTTPS, 3306 MySQL, 5432 PostgreSQL, 3389 RDP

## Storage
- EBS: persistent, network-attached, single-AZ, single-instance (unless Multi-Attach)
- gp3 = default choice, 3,000 baseline IOPS independent of size; io2 = guaranteed high IOPS; st1/sc1 = throughput, not IOPS, no boot volume
- EBS Multi-Attach: io1/io2 only, same AZ, up to 16 instances — attachment only, NOT write coordination
- EFS: real distributed filesystem, multi-AZ, multi-client, elastic — the right default for shared storage
- Instance Store: physically local, ephemeral (lost on stop/terminate, survives reboot), fastest, bundled into price
- Snapshots: incremental, region-scoped, use DLM to automate lifecycle

## Load Balancing
- ALB (L7, HTTP/HTTPS, path/host routing), NLB (L4, ultra-high performance, static IP support), CLB (legacy), GWLB (third-party appliances)
- SNI: multiple SSL certs on one IP/load balancer
- Sticky Sessions: binds client to a specific target instance

## Auto Scaling
- ASG maintains desired capacity, replaces unhealthy instances, scales on defined policies
- ELB health check (defers to target group) vs. EC2 health check (own status checks only) — different signals

## Troubleshooting
- Connection Refused → app not running, or bound to 127.0.0.1 instead of 0.0.0.0 (network layer is fine)
- Connection Timeout → check Security Group, then NACL (both directions — stateless!), then routing/NAT
- Failing health checks → check exact path/port, security group allows LB as source, grace period vs. genuinely broken app
- High CPU on T-series → check `CPUCreditBalance`; fix via Unlimited mode or move to M-series
