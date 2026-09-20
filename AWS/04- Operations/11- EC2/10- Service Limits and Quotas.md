# 10- Service Limits and Quotas

## Overview

AWS service quotas define limits on how many resources, how much capacity, or how much API activity an AWS account can use within a Region or service scope.

For EC2 environments, quotas can become an operational constraint long before CPU or memory becomes a problem.

A production scaling failure can look like:

```text
Application Traffic
        |
        v
Auto Scaling
        |
        v
Launch More EC2
        |
        v
AWS Quota
        |
        X
Capacity Cannot Increase
```

This means capacity planning must consider both:

```text
Workload Capacity
+
AWS Service Capacity
```

Common EC2-related constraints include:

- Running On-Demand instance vCPU quotas
- Spot instance vCPU quotas
- EBS volume and storage limits
- EBS IOPS and throughput limits
- Elastic IP address quotas
- Network interface limits
- Security Group rule limits
- VPC and subnet limits
- Auto Scaling limits
- Load balancer limits
- API request throttling
- Regional capacity availability

A quota is not necessarily a technical failure. It is an explicit boundary designed to protect the service and account from uncontrolled resource consumption.

## Quota vs Resource Limit vs Throttling

These concepts are related but different.

| Concept | Meaning | Example |
|---|---|---|
| Service quota | AWS account/resource boundary | EC2 vCPU quota |
| Resource limit | Maximum property of a specific resource | Maximum EBS performance supported by a configuration |
| API throttling | Request-rate protection | Too many `DescribeInstances` requests |
| Capacity availability | Whether AWS currently has capacity | Requested instance type unavailable in an AZ |
| Application limit | Your application's own constraint | PostgreSQL connection limit |

The distinction matters during troubleshooting.

For example:

```text
Run 500 EC2 instances
        |
        v
EC2 vCPU quota
        |
        X
Quota exceeded
```

is different from:

```text
Run 500 EC2 instances
        |
        v
Quota available
        |
        v
AZ capacity unavailable
        |
        X
Launch fails
```

It is also different from:

```text
Automation
    |
    v
Thousands of API calls
    |
    v
API throttling
    |
    X
Requests delayed/rejected
```

## Why Quotas Exist

AWS quotas provide controlled boundaries around service usage.

They help:

- Prevent accidental runaway resource creation
- Protect service stability
- Isolate accounts and workloads
- Manage regional capacity
- Establish predictable operational boundaries
- Provide a mechanism for requesting additional capacity

From an engineering perspective, quotas should be treated as **capacity-planning inputs**, not administrative details.

## Regional Scope

Many AWS quotas are Region-specific.

For example:

```text
Region: ap-south-1
EC2 vCPU quota: X

Region: ap-southeast-1
EC2 vCPU quota: Y
```

The values do not necessarily match.

Therefore, a multi-Region architecture must evaluate quotas independently.

```text
Production Region
ap-south-1
    |
    +-- EC2 quotas
    +-- EBS quotas
    +-- IP quotas
    +-- Network quotas
    |
    v
DR Region
ap-southeast-1
    |
    +-- EC2 quotas
    +-- EBS quotas
    +-- IP quotas
    +-- Network quotas
```

A disaster recovery Region that has never been exercised may have insufficient quota for the required recovery capacity.

## Service Quotas

AWS Service Quotas provides a centralized way to view and manage many AWS service limits.

CLI:

```bash
aws service-quotas list-services \
    --profile production \
    --region ap-south-1
```

Find EC2 quotas:

```bash
aws service-quotas list-service-quotas \
    --profile production \
    --region ap-south-1 \
    --service-code ec2
```

Inspect a specific quota:

```bash
aws service-quotas get-service-quota \
    --profile production \
    --region ap-south-1 \
    --service-code ec2 \
    --quota-code "$QUOTA_CODE"
```

Not every AWS limit is necessarily exposed or adjustable through Service Quotas. Some limits are documented separately or are fixed service constraints.

## Finding Quotas by Name

The CLI can be filtered using `--query`.

For example:

```bash
aws service-quotas list-service-quotas \
    --profile production \
    --region ap-south-1 \
    --service-code ec2 \
    --query 'Quotas[?contains(QuotaName, `Running On-Demand`)].{
        Name:QuotaName,
        Code:QuotaCode,
        Value:Value
    }' \
    --output table
```

This is useful when building operational tooling that needs to inspect quota values.

## EC2 vCPU Quotas

EC2 vCPU-based quotas control how much instance compute capacity an account can consume for applicable instance categories.

The quota is generally expressed in vCPUs rather than number of instances.

For example:

```text
Quota:
100 vCPUs

Instance:
8 vCPUs

Potential capacity:
12 x 8 = 96 vCPUs
```

The number of instances alone therefore does not tell you whether you will hit the quota.

Capacity planning should calculate:

```text
Required Instances
        x
vCPUs per Instance
        =
Required vCPUs
```

Then compare the result against the relevant quota.

## Why Instance Count Is Not Enough

Consider:

```text
Architecture A:
20 instances x 2 vCPU
= 40 vCPU

Architecture B:
5 instances x 8 vCPU
= 40 vCPU
```

Both consume the same vCPU capacity even though the instance counts differ.

Therefore:

```text
Instance Count != Compute Quota Consumption
```

This becomes particularly important when migrating from smaller instances to larger instance families.

## Auto Scaling and Quotas

Auto Scaling can increase desired capacity without being able to launch the required instances.

Example:

```text
Traffic Spike
     |
     v
ASG desired capacity
     |
     v
Launch Instances
     |
     v
EC2 vCPU Quota
     |
     X
Quota exceeded
```

The ASG may therefore fail to reach desired capacity.

Operationally monitor:

- ASG scaling activities
- Instance launch failures
- EC2 API errors
- CloudWatch capacity metrics
- Service quota utilization

A scaling policy is only useful if the underlying AWS account can actually provide the requested capacity.

## Quota Headroom

Do not plan production capacity to exactly match the quota.

Example:

```text
Quota: 100 vCPU
Normal: 50 vCPU
Peak: 80 vCPU
```

This provides some operational headroom.

A more dangerous configuration is:

```text
Quota: 100 vCPU
Normal: 90 vCPU
Peak: 100 vCPU
```

A small scaling event or replacement operation could exhaust the available quota.

A useful capacity model is:

```text
Required Capacity
+
Failure Capacity
+
Scaling Headroom
<
Service Quota
```

## Failure Capacity

Capacity planning should account for failure scenarios.

Suppose:

```text
Normal:
10 x 4 vCPU
= 40 vCPU
```

A Multi-AZ architecture may need additional capacity when one AZ becomes unavailable.

If the system must temporarily launch replacement instances:

```text
Normal capacity
+
Replacement capacity
+
Traffic surge
```

may exceed the current quota.

Therefore, quotas should be evaluated against the **failure-mode capacity requirement**, not just normal utilization.

## EBS Quotas and Limits

EBS introduces several capacity dimensions.

Consider:

- Number of volumes
- Total storage
- Provisioned IOPS
- Provisioned throughput
- Snapshot usage
- EBS bandwidth supported by the EC2 instance

A storage architecture can therefore encounter a constraint even when the EC2 vCPU quota is healthy.

```text
EC2
 |
 +-- vCPU quota
 |
 +-- Network capacity
 |
 +-- EBS bandwidth
 |
 +-- ENI/IP capacity
 |
 v
Application
```

The smallest relevant capacity boundary can become the bottleneck.

## EBS Performance Limits

EBS performance is constrained by both the volume configuration and the EC2 instance's EBS capabilities.

For a workload requiring high IOPS:

```text
Application
    |
    v
EBS Volume
    |
    +-- Provisioned IOPS
    |
    v
EC2 EBS bandwidth / limits
```

Provisioning a high-performance EBS volume does not guarantee that the EC2 instance can consume all of that performance.

Capacity planning should therefore evaluate:

- Volume type
- Volume size
- IOPS
- Throughput
- EC2 EBS bandwidth
- Workload I/O pattern

## EBS Volume Count

Applications that attach many volumes can encounter attachment or instance-specific limits.

For example:

```text
EC2
 |
 +-- EBS 1
 +-- EBS 2
 +-- EBS 3
 +-- ...
```

Large storage architectures should verify the maximum supported attachments for the selected instance type.

This matters for:

- Databases
- Storage-heavy applications
- Distributed systems
- Large data-processing nodes

## Elastic IP Quotas

Elastic IP addresses have quotas.

List allocated addresses:

```bash
aws ec2 describe-addresses \
    --profile production \
    --region ap-south-1 \
    --query 'Addresses[].{
        PublicIP:PublicIp,
        AllocationId:AllocationId,
        InstanceId:InstanceId,
        AssociationId:AssociationId
    }' \
    --output table
```

A common operational mistake is treating Elastic IPs as unlimited infrastructure.

Review:

- Allocated addresses
- Associated addresses
- Unused addresses
- Legacy architectures
- Static-IP requirements

Do not release an Elastic IP until its dependencies have been verified.

## Network Interface Limits

EC2 instances have limits related to Elastic Network Interfaces (ENIs) and IP addresses.

These limits vary by instance type.

A service that creates many network interfaces or requires many private IP addresses should consider:

```text
Instance Type
    |
    +-- ENI limit
    +-- IPv4 addresses per ENI
    +-- IPv6 capabilities
    |
    v
Network Architecture
```

This is relevant to:

- Container networking
- High-density services
- Network appliances
- Multiple interfaces
- Specialized architectures

## Subnet IP Capacity

Subnet address exhaustion is not exactly an EC2 service quota, but it is a common scaling boundary.

Example:

```text
Subnet
CIDR: /24

Available IPs
    |
    v
EC2 + ENIs + Load Balancers + Other Resources
    |
    v
IP Exhaustion
    |
    X
New Resource Cannot Launch
```

A subnet can therefore become a capacity bottleneck even when the account has sufficient EC2 quota.

Monitor:

- Available IP addresses
- Instance growth
- ENI growth
- Load balancer requirements
- Kubernetes/container requirements where applicable

## Availability Zone Capacity

Service quotas and actual AWS capacity are different.

You can have:

```text
Quota available
```

but still fail to launch a specific instance type in a specific AZ because capacity is unavailable.

Therefore:

```text
Quota Capacity
      +
AWS Physical Capacity
      =
Actual Launch Capacity
```

For resilient production architectures:

- Use multiple AZs.
- Avoid dependence on one instance type when possible.
- Consider multiple instance types.
- Consider multiple capacity strategies.
- Maintain sufficient scaling headroom.

## Auto Scaling Group Limits

Auto Scaling introduces additional operational boundaries.

Consider:

- Desired capacity
- Minimum capacity
- Maximum capacity
- Number of ASGs
- Scaling policies
- Lifecycle hooks
- Instance refresh operations
- Launch template versions

An ASG can be configured for a maximum capacity that is theoretically larger than the EC2 quota.

For example:

```text
ASG Max:
500 instances

EC2 quota:
100 vCPU

Instance:
4 vCPU
```

The ASG configuration does not mean 500 instances can actually launch.

The effective capacity is bounded by the underlying EC2 quota and other infrastructure limits.

## Load Balancer Limits

Load balancers have service-specific limits involving resources such as:

- Load balancers
- Listeners
- Listener rules
- Target groups
- Targets
- Certificates
- Security Groups
- Routing configuration

For large microservice environments:

```text
ALB
 |
 +-- Listener
 |    |
 |    +-- Rule
 |    +-- Rule
 |    +-- Rule
 |
 +-- Target Groups
      |
      +-- Service A
      +-- Service B
      +-- Service C
```

A design with hundreds of services should account for load balancer resource limits and operational complexity.

## Security Group Limits

Security Groups have limits involving:

- Number of Security Groups
- Rules per Security Group
- Security Groups per network interface
- References between Security Groups

A large microservice architecture can unintentionally create excessive rule complexity.

For example:

```text
Service A SG
    |
    +-- Service B
    +-- Service C
    +-- Service D
    +-- ...
```

Prefer structured security-group relationships rather than creating large numbers of unnecessary individual rules.

## Security Group Rule Explosion

A common anti-pattern is generating one rule per IP address.

Example:

```text
SG
 |
 +-- 10.0.1.1
 +-- 10.0.1.2
 +-- 10.0.1.3
 +-- ...
```

This can create maintenance and quota problems.

Prefer architectural controls such as:

- Security Group references
- Prefix lists
- Load balancers
- Network segmentation
- Controlled ingress points

where appropriate.

## API Throttling

AWS APIs have request-rate protections.

A high-volume automation system can encounter throttling even when resource quotas are available.

Example:

```text
Automation
    |
    +-- describe-instances
    +-- describe-volumes
    +-- describe-tags
    +-- describe-security-groups
    +-- ...
    |
    v
AWS API
    |
    X
Throttling
```

This is particularly relevant to:

- Inventory systems
- Monitoring agents
- Large CI/CD pipelines
- Fleet-management scripts
- Custom controllers
- Polling-based automation

## Handling API Throttling

Use:

- Exponential backoff
- Jitter
- Retries
- Pagination
- Caching
- Event-driven mechanisms where possible
- Reduced polling frequency

A basic retry strategy:

```text
Request
   |
   v
Throttled?
  /   \
No     Yes
 |      |
 v      v
Done   Backoff
          |
          v
        Retry
```

Do not implement an immediate tight retry loop.

## AWS CLI and Pagination

Large EC2 environments can generate significant API traffic if scripts repeatedly request full inventories.

Prefer:

```bash
aws ec2 describe-instances \
    --profile production \
    --region ap-south-1 \
    --filters Name=tag:Environment,Values=production \
    --query 'Reservations[].Instances[].InstanceId'
```

instead of repeatedly querying all instances and filtering locally.

For automation, understand the difference between:

- API-side filtering
- CLI pagination
- `--page-size`
- `--max-items`
- `--starting-token`

Reducing unnecessary API calls helps avoid throttling.

## Boto3 and API Throttling

Python automation should also handle throttling.

Example:

```python
import time

import boto3
from botocore.exceptions import ClientError

ec2 = boto3.client("ec2", region_name="ap-south-1")

for attempt in range(5):
    try:
        response = ec2.describe_instances()
        break
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]

        if error_code not in {"RequestLimitExceeded", "Throttling"}:
            raise

        time.sleep(2**attempt)
else:
    raise RuntimeError("EC2 API remained throttled after retries")
```

Production systems should normally use the SDK's retry configuration and add jitter where appropriate rather than implementing simplistic fixed retry loops everywhere.

## Service Quota Monitoring

Quota monitoring should focus on utilization, not only configured values.

Example:

```text
Quota:
100 vCPU

Current:
75 vCPU

Utilization:
75%

Threshold:
80%
```

An alert can trigger before capacity becomes a production incident.

Useful monitoring dimensions include:

- Current usage
- Quota value
- Percentage utilization
- Growth rate
- Peak utilization
- Failure-mode requirement

## Quota Headroom Model

A practical model is:

```text
Quota Headroom
=
Quota
-
Current Usage
```

Percentage:

```text
Headroom %
=
(Quota - Usage) / Quota * 100
```

For example:

```text
Quota = 200 vCPU
Usage = 140 vCPU

Headroom = 60 vCPU
Headroom = 30%
```

This is more useful operationally than simply knowing that the quota is 200 vCPU.

## Capacity Planning

Capacity planning should combine:

```text
Current Usage
+
Growth Forecast
+
Peak Traffic
+
Failure Scenario
+
Deployment Capacity
+
Recovery Capacity
```

Example:

```text
Normal:
80 vCPU

Traffic peak:
120 vCPU

AZ failure recovery:
160 vCPU

Deployment overlap:
180 vCPU

Quota:
200 vCPU
```

This provides approximately 20 vCPU of remaining headroom.

A quota increase may be appropriate before the workload approaches the boundary.

## Deployment Capacity

Deployments can temporarily require additional capacity.

For example, an instance refresh configured to maintain healthy capacity may launch new instances before terminating old ones.

```text
Existing:
10 instances

Deployment:
Launch 10 new
Then terminate old

Temporary:
20 instances
```

The required vCPU capacity may therefore temporarily double.

Quota planning should account for this.

## Blue/Green Capacity

Blue/green deployment can also increase temporary resource requirements.

```text
Blue:
10 instances

Green:
10 instances

Deployment capacity:
20 instances
```

If the quota only supports the steady-state fleet, the deployment may fail.

This is an important reason to calculate **peak operational capacity**, not only steady-state capacity.

## Disaster Recovery Quotas

A DR Region should have sufficient quotas before an incident.

Consider:

```text
Primary Region
    |
    v
Production Capacity
    |
    v
DR Requirement
    |
    v
Secondary Region Quotas
```

For example, if the production Region requires:

```text
100 vCPU
```

and the DR plan requires rebuilding the full workload:

```text
DR quota should support >= 100 vCPU
```

plus appropriate operational headroom.

A DR runbook that says "launch the production fleet in another Region" is incomplete unless the destination Region has been prepared to support it.

## Quota Increase Requests

Some quotas can be increased through Service Quotas.

The general workflow is:

```text
Current Quota
     |
     v
Determine Required Capacity
     |
     v
Calculate Headroom
     |
     v
Request Increase
     |
     v
Validate Approved Quota
     |
     v
Update Capacity Plan
```

Request only what is justified by the workload.

A quota increase should be treated as part of capacity planning rather than a substitute for fixing uncontrolled resource consumption.

## Quota Increase CLI

For quotas that support programmatic increases, the AWS CLI provides quota-request operations.

Example:

```bash
aws service-quotas request-service-quota-increase \
    --profile production \
    --region ap-south-1 \
    --service-code ec2 \
    --quota-code "$QUOTA_CODE" \
    --desired-value 200
```

Check requests:

```bash
aws service-quotas list-requested-service-quota-change-history \
    --profile production \
    --region ap-south-1 \
    --service-code ec2
```

Availability and approval behavior depends on the specific quota.

Do not assume every limit is adjustable.

## Fixed Limits

Some service constraints cannot simply be increased.

For fixed limits, the solution is architectural.

Examples may include:

- Resource-specific constraints
- Instance-specific ENI capabilities
- Per-resource configuration boundaries
- Certain networking constraints

The engineering response becomes:

```text
Limit
  |
  v
Architectural Redesign
  |
  +-- Split resources
  +-- Use another instance type
  +-- Use multiple AZs
  +-- Use multiple load balancers
  +-- Change service architecture
```

## Quota-Aware Architecture

A scalable architecture should treat quotas as design constraints.

Example:

```text
                    Traffic
                       |
                       v
                      ALB
                       |
              +--------+--------+
              |        |        |
             EC2      EC2      EC2
              |        |        |
              +--------+--------+
                       |
             +---------+---------+
             |                   |
          PostgreSQL           Redis
```

Capacity planning should evaluate:

```text
EC2 vCPU quota
EBS capacity
ENI capacity
Subnet IP capacity
Load balancer limits
Security Group limits
Database capacity
Redis capacity
```

The architecture is bounded by the most restrictive relevant dependency.

## Quota-Aware Microservices

Microservice architectures can multiply resource consumption.

For example:

```text
20 Services
   |
   +-- 2 EC2 instances each
   |
   = 40 instances
```

If each service also creates:

- Target groups
- Listener rules
- Security Groups
- ENIs
- IAM resources
- CloudWatch resources

the overall quota footprint becomes much larger.

Before adopting a large microservice architecture, model the AWS resource footprint.

## Kubernetes and EC2 Quotas

When Kubernetes runs on EC2, cluster scaling can consume EC2 resources rapidly.

Example:

```text
Kubernetes
    |
    v
Cluster Autoscaler
    |
    v
More Nodes
    |
    v
EC2 vCPU Quota
```

A Kubernetes workload may therefore remain pending because the node group cannot scale due to:

- EC2 quota
- Subnet IP exhaustion
- Instance capacity
- Node group limits
- Availability Zone constraints

Quota awareness is therefore important even when EC2 is managed indirectly.

## Monitoring and Alerting

Useful operational alerts include:

- EC2 quota utilization above threshold
- Repeated launch failures
- ASG unable to reach desired capacity
- Subnet IP exhaustion
- EBS capacity exhaustion
- API throttling
- Unexpected resource growth

A useful incident signal is:

```text
ASG Desired Capacity
        >
Healthy Instances
```

combined with:

```text
Launch failures
+
Quota / capacity errors
```

This can indicate a scaling boundary.

## Operational Troubleshooting Workflow

When an EC2 launch fails:

```text
Launch Failure
      |
      v
Read Exact Error
      |
      +--> Quota?
      |
      +--> AZ Capacity?
      |
      +--> Subnet IP?
      |
      +--> IAM?
      |
      +--> Security Group?
      |
      +--> EBS?
      |
      +--> Launch Template?
      |
      v
Correct Root Cause
      |
      v
Retry
```

Do not immediately request a quota increase.

First identify the actual failure.

## Example: ASG Cannot Scale

Suppose:

```text
ASG:
Desired = 20

Healthy:
14

Launch:
Failing
```

Investigate:

```text
ASG Activity History
        |
        v
Launch Failure Message
        |
        v
EC2 API Error
        |
        +--> vCPU quota exceeded
        |
        +--> subnet IP exhausted
        |
        +--> insufficient AZ capacity
        |
        +--> invalid launch configuration
```

The remediation depends on the actual error.

## Example: Subnet IP Exhaustion

Suppose:

```text
ASG:
Desired = 30

Current:
28

New instance:
Launch failed
```

Quota inspection shows sufficient EC2 capacity.

Check subnet availability:

```bash
aws ec2 describe-subnets \
    --profile production \
    --region ap-south-1 \
    --subnet-ids subnet-0123456789abcdef0 \
    --query 'Subnets[0].{
        SubnetId:SubnetId,
        CIDR:CidrBlock,
        AvailableIPs:AvailableIpAddressCount,
        AZ:AvailabilityZone
    }' \
    --output table
```

If available IPs are exhausted, increasing EC2 quota will not solve the problem.

## Example: API Throttling

Suppose an inventory service repeatedly executes:

```text
describe-instances
describe-instances
describe-instances
...
```

across many accounts and Regions.

The service begins receiving throttling errors.

The correct response is to:

- Reduce polling frequency
- Use pagination
- Filter server-side
- Cache stable metadata
- Add exponential backoff
- Consider event-driven inventory updates

Increasing an EC2 resource quota would not solve API throttling.

## Quota Management in CI/CD

CI/CD pipelines can unintentionally consume quota.

Examples:

- Parallel test environments
- Temporary EC2 runners
- Load-testing fleets
- Blue/green environments
- Integration environments

A pipeline may need:

```text
Build
 |
 v
Environment
 |
 v
Load Test
 |
 v
Destroy
```

If cleanup fails, resources accumulate and future jobs may hit quotas.

Always include cleanup and failure recovery in temporary environment workflows.

## Security Considerations

Quota management has security implications.

An attacker or compromised automation identity could attempt to create large numbers of resources.

Controls include:

- Least-privilege IAM
- Resource tagging
- AWS Organizations guardrails
- CloudTrail
- Service Quotas monitoring
- Budgets and cost alerts
- SCPs where appropriate
- Automated resource inventory

Quotas can limit blast radius, but they are not a substitute for security controls.

## Cost Considerations

Quota increases themselves are generally not the primary cost concern.

The more important issue is what increased quota enables.

For example:

```text
Quota:
100 -> 500 vCPU
```

does not directly mean the account is using 500 vCPU.

But it removes a protective boundary.

If automation is broken:

```text
Runaway Automation
       |
       v
More EC2
       |
       v
Higher Cost
```

Quota increases should therefore be combined with:

- Cost alerts
- Resource controls
- Auto Scaling limits
- Budget monitoring
- Ownership tagging

## Production Best Practices

### Monitor Quota Utilization

Track high-value quotas before they become incidents.

### Maintain Headroom

Do not operate permanently at the quota boundary.

### Include Failure Scenarios

Calculate capacity for:

- Peak traffic
- Deployment
- Instance replacement
- AZ failure
- DR recovery

### Validate DR Regions

Ensure required quotas exist before a disaster.

### Automate Quota Discovery

For large environments, periodically inventory quotas and current usage.

### Separate Quota Problems From Capacity Problems

Distinguish:

```text
Quota exceeded
```

from:

```text
AWS capacity unavailable
```

from:

```text
Subnet exhausted
```

from:

```text
API throttled
```

### Avoid Hard-Coded Assumptions

Do not assume quota values are identical across:

- Regions
- Accounts
- Environments
- Instance families

### Keep IaC Within Operational Limits

Terraform or CloudFormation can describe infrastructure that exceeds the account's available quotas.

Validate quota requirements before large deployments.

### Design for Graceful Degradation

When capacity cannot scale immediately, application behavior should remain controlled where possible.

Examples:

- Queue work
- Apply rate limits
- Shed non-critical load
- Degrade optional features
- Preserve core API functionality

## Common Mistakes

### Treating Quotas as Fixed Globally

Quota values can differ by Region and account.

**Avoid it:** query the relevant Region and account.

### Planning Only for Normal Capacity

A fleet may fit within quota under normal traffic but fail during deployment or AZ failure.

**Avoid it:** include peak and failure capacity.

### Assuming ASG Max Equals Real Capacity

`MaxSize` is an ASG configuration boundary, not a guarantee that AWS can launch that many instances.

**Avoid it:** validate EC2 quotas, subnet capacity, AZ capacity, and other limits.

### Requesting a Quota Increase Without Investigating

A quota increase does not solve subnet exhaustion, API throttling, or invalid configuration.

**Avoid it:** identify the exact failure first.

### Ignoring API Throttling

A service can have unlimited resource capacity available while its automation is still throttled.

**Avoid it:** use pagination, caching, backoff, jitter, and reduced polling.

### Ignoring DR Quotas

A DR plan can fail because the secondary Region lacks enough capacity or quota.

**Avoid it:** preflight DR capacity and periodically test recovery.

### Hard-Coding Resource Limits

Automation that assumes a fixed quota can become incorrect after account growth or architecture changes.

**Avoid it:** query service quotas where practical.

### Creating Excessive Security Group Rules

Large rule sets can create quota and maintenance problems.

**Avoid it:** use Security Group references, prefix lists, and structured network boundaries.

### Ignoring Subnet IP Capacity

EC2 quota can be healthy while the subnet has no available addresses.

**Avoid it:** monitor `AvailableIpAddressCount`.

## Interview Traps

### What Is an AWS Service Quota?

A service quota is an AWS-defined limit on resource usage or service operations for an account, Region, or service context.

### Is an EC2 vCPU Quota the Same as an Instance Count Limit?

No.

A vCPU quota measures applicable compute capacity, while instance count is simply the number of instances.

### Can an ASG Launch Unlimited Instances if `MaxSize` Is High?

No.

Actual capacity is constrained by service quotas, subnet capacity, instance availability, networking limits, and other AWS constraints.

### What Is the Difference Between Quota and Throttling?

A quota limits resource or service capacity. Throttling limits request rate or API activity.

### Can Increasing an EC2 Quota Fix Every Launch Failure?

No.

Launch failures can also result from:

- AZ capacity
- Subnet IP exhaustion
- Invalid configuration
- IAM permissions
- EBS constraints
- Instance-type availability

### Why Does DR Require Quota Planning?

Because the recovery Region must be able to create the required infrastructure during an incident. A DR architecture that exceeds destination quotas cannot be activated as designed.

### Why Should Quota Headroom Be Maintained?

Because scaling, deployments, failures, and recovery operations can temporarily require more resources than steady-state workloads.

### Why Is API Throttling Important in EC2 Automation?

Large automation systems can make many API calls and exceed request-rate limits even when the underlying EC2 resource quotas are healthy.

### What Should You Check When an ASG Cannot Reach Desired Capacity?

Check:

```text
ASG Activity History
        |
        v
Launch Error
        |
        +--> EC2 quota
        +--> Subnet IP capacity
        +--> AZ capacity
        +--> Launch Template
        +--> IAM
        +--> EBS
```

### What Is the Difference Between Quota and Physical Capacity?

A quota is an account/service usage boundary. Physical capacity refers to whether AWS can currently provide the requested resource in the selected location and configuration.

## Production Checklist

### Quota Management

- [ ] Critical EC2 quotas identified
- [ ] Current quota values documented
- [ ] Quota utilization monitored
- [ ] Adequate headroom maintained
- [ ] Quotas reviewed per Region
- [ ] Quotas reviewed per account

### Compute

- [ ] EC2 vCPU requirements calculated
- [ ] ASG maximum capacity validated
- [ ] Deployment capacity considered
- [ ] Failure capacity considered
- [ ] DR capacity considered
- [ ] Instance-family constraints reviewed

### Networking

- [ ] Subnet IP capacity monitored
- [ ] ENI limits reviewed
- [ ] IP-per-ENI limits reviewed
- [ ] Elastic IP requirements reviewed
- [ ] Load balancer limits considered
- [ ] Security Group limits considered

### Storage

- [ ] EBS capacity reviewed
- [ ] EBS volume limits reviewed
- [ ] EBS IOPS and throughput requirements reviewed
- [ ] Snapshot growth monitored

### Automation

- [ ] API throttling handled
- [ ] Pagination used
- [ ] Server-side filtering used
- [ ] Exponential backoff implemented
- [ ] Jitter used for distributed retries
- [ ] Resource cleanup implemented

### Disaster Recovery

- [ ] DR Region quotas validated
- [ ] DR subnet capacity validated
- [ ] DR instance capacity validated
- [ ] DR EBS capacity validated
- [ ] Recovery process tested
- [ ] Quota assumptions documented

## Key Takeaways

- **Treat quotas as capacity-planning constraints:** production capacity must account for normal demand, traffic peaks, deployments, instance replacement, and disaster recovery.
- **Distinguish quota failures from other capacity failures:** EC2 quota exhaustion, subnet IP exhaustion, Availability Zone capacity shortages, and API throttling require different remediation strategies.
- **Maintain quota headroom:** operating near a quota boundary can cause scaling, deployment, or recovery failures even when normal workload capacity appears sufficient.
- **Make automation quota-aware:** use Service Quotas, pagination, server-side filtering, exponential backoff, jitter, and monitoring to prevent large-scale operational tooling from becoming a bottleneck.
- **Validate limits across the entire architecture:** EC2, EBS, ENIs, IP addresses, Security Groups, load balancers, Auto Scaling, API rates, and downstream services can all become independent scaling boundaries.