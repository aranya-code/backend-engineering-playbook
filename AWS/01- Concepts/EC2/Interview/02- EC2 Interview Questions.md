# EC2 Interview Questions

## Beginner

**Q1. What is Amazon EC2?**
AWS's core Infrastructure-as-a-Service offering — resizable virtual servers with full OS-level control, running on the Nitro System (modern instances) which offloads networking and storage to dedicated hardware.

**Q2. Difference between a Security Group and a NACL?**
Security Groups are stateful, operate at the instance (ENI) level, and support allow rules only. NACLs are stateless, operate at the subnet level, and support both allow and deny rules — meaning NACLs require explicit rules for both inbound and outbound directions, since a NACL doesn't automatically allow a response.

**Q3. Difference between EBS and Instance Store?**
EBS is persistent, network-attached block storage that survives stop/reboot. Instance Store is temporary, physically-local storage that's lost on stop or terminate (though it survives a simple reboot) — much lower latency, but ephemeral.

**Q4. What is an Elastic IP, and why use one?**
A static public IPv4 address that stays fixed and under your control even as the underlying instance stops/restarts — used where other systems need a stable, unchanging address to reach, like bastion hosts or legacy IP-based allow-lists.

**Q5. What is User Data?**
A bootstrap script that runs as root during an instance's first launch, retrieved from the Instance Metadata Service, enabling automated configuration without manual SSH setup.

## Intermediate

**Q6. Why is IMDSv2 preferred over IMDSv1?**
IMDSv1 allows a simple, unauthenticated GET request to retrieve instance metadata — including live IAM role credentials — making it vulnerable to SSRF attacks (as in the 2019 Capital One breach). IMDSv2 requires a session token obtained via a PUT request first, which most SSRF vulnerabilities can't replicate, since they typically can't issue arbitrary HTTP methods or set custom headers.

**Q7. What's the difference between gp3 and io2 EBS volumes?**
gp3 provides a solid 3,000 IOPS baseline independent of volume size, with additional IOPS/throughput provisionable at incremental cost — the default choice for most workloads. io2 (and io2 Block Express) is for workloads needing guaranteed, sustained high IOPS beyond gp3's range, at a higher cost, typically for mission-critical, latency-sensitive databases.

**Q8. Explain the T-series CPU credit model, and what happens when credits run out.**
T-series instances provide a fixed CPU baseline with the ability to burst above it using accumulated credits. Under sustained load, credits deplete faster than they replenish; once exhausted in Standard mode, the instance is throttled back to its baseline percentage, which can mean a dramatic, sudden-feeling performance drop that's actually gradual credit exhaustion.

**Q9. What's the difference between EBS Multi-Attach and EFS for shared storage?**
EBS Multi-Attach allows a single io1/io2 volume to attach to multiple instances in the same AZ, but provides no write-coordination — the application must already handle concurrent writes itself (e.g., clustered database software). EFS is a genuine distributed filesystem built for concurrent multi-client access across AZs from the ground up, and is the right default for "shared storage across instances" for the vast majority of use cases.

**Q10. What are Placement Groups, and when would you use each type?**
Cluster (same rack, lowest latency, for HPC/tightly-coupled workloads), Spread (different racks, max 7 instances per AZ, for high-availability critical applications), and Partition (grouped racks with isolation between partitions, for partition-aware distributed systems like Kafka or Cassandra).

## Senior / Advanced

**Q11. An application on a T3 instance suddenly became 4-5x slower under sustained load with no code changes. Walk through your investigation.**
Check the `CPUCreditBalance` CloudWatch metric first — if it's trending toward or has hit zero during the slow period, this is CPU credit exhaustion throttling the instance to its baseline percentage. Fix options in order of structural durability: switch to Unlimited mode (quick, but can incur surplus charges if sustained), or move to an M-series fixed-performance instance if the workload's actual profile has shifted to consistently high CPU rather than bursty.

**Q12. Design a cost-optimized EC2 strategy for a workload with a steady baseline and unpredictable traffic spikes.**
Use a Savings Plan (or Reserved Instances) sized to cover the steady-state baseline for the discount, let On-Demand or Spot instances absorb burst capacity above that baseline via Auto Scaling, and use Spot specifically for any portion of the burst capacity that's genuinely interruption-tolerant (stateless web tier behind a load balancer) for the deepest additional discount.

**Q13. Why does IMDSv2's design specifically prevent most SSRF-based credential theft?**
SSRF vulnerabilities typically let an attacker trick a server into making a GET request to an attacker-chosen URL, but usually can't control the HTTP method or set arbitrary custom headers. IMDSv2 requires a PUT request to obtain a session token, then requires that token to be passed via a specific custom header on the subsequent GET — both constraints that a typical SSRF exploit path can't satisfy, which is precisely why it closes off the attack vector that IMDSv1 left open.

**Q14. A Target Group reports an instance as unhealthy, but the instance's own EC2 status checks are passing. What does this tell you, and how would you debug it?**
This tells you the instance itself is fundamentally fine at the infrastructure level — the problem is specific to whatever the Target Group's health check is actually probing (a specific path/port). Debug by manually curling the exact configured health check path and port from within the VPC, confirming the app is actually listening on that port, and checking that the load balancer's security group is allowed as a source on the instance's security group for that specific port.

**Q15. Compare EBS Multi-Attach, EFS, and a Multi-AZ RDS deployment as approaches to shared or highly-available storage — when would you choose each?**
EBS Multi-Attach fits narrow, already-clustered software (e.g., Oracle RAC) that implements its own write coordination on shared block storage. EFS fits general shared-file needs across many instances/AZs (media uploads, container persistent volumes) where a real distributed filesystem is the right abstraction. Multi-AZ RDS isn't really a "shared storage" pattern at all — it's a managed database's own synchronous replication for availability, and remains the right choice whenever the actual need is a highly-available relational database rather than shared filesystem access.
