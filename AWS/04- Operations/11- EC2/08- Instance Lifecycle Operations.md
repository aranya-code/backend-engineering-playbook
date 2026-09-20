# 08- Instance Lifecycle Operations

## Overview

EC2 instance lifecycle operations control how instances are launched, started, stopped, rebooted, replaced, maintained, and terminated throughout their operational lifetime.

The lifecycle is not simply:

```text
Launch -> Run -> Terminate
```

A production environment usually involves:

```text
                         +----------------+
                         | Launch Request |
                         +-------+--------+
                                 |
                                 v
                           +-----------+
                           | Pending   |
                           +-----+-----+
                                 |
                                 v
                           +-----------+
                           | Running   |
                           +--+-----+--+
                              |     |
                   +----------+     +----------+
                   |                           |
                   v                           v
              +---------+                +----------+
              | Stopping|                | Rebooting|
              +----+----+                +----+-----+
                   |                          |
                   v                          |
              +---------+                     |
              | Stopped |<--------------------+
              +----+----+
                   |
                   v
              +---------+
              | Starting|
              +----+----+
                   |
                   v
              +---------+
              | Running |
              +---------+

                   Running
                      |
                      v
                Terminating
                      |
                      v
                Terminated
```

For production systems, lifecycle management must account for:

- Application availability
- Load balancer draining
- Auto Scaling
- Persistent storage
- Instance metadata
- IAM roles
- Security Groups
- User Data
- AMIs and Launch Templates
- Scheduled maintenance
- Instance health
- Backups
- Cost
- Recovery procedures

The most important operational principle is:

> **Treat application instances as replaceable infrastructure whenever the architecture permits it.**

This is particularly important for Django, FastAPI, Celery, Nginx, and other backend workloads deployed behind an Auto Scaling Group and load balancer.

## EC2 Instance States

An EC2 instance progresses through defined states.

| State | Meaning | Typical operation |
|---|---|---|
| `pending` | Instance is being prepared | Launch |
| `running` | Instance is executing | Normal operation |
| `stopping` | Stop operation is in progress | Stop |
| `stopped` | Instance is not running | Restart later |
| `shutting-down` | Termination is in progress | Terminate |
| `terminated` | Instance has been permanently terminated | Recovery requires replacement |

The lifecycle state is different from the instance's health.

For example:

```text
Instance state:
running

System status:
passed

Application:
unhealthy
```

An instance can therefore be operationally unusable even though EC2 reports it as `running`.

## Inspecting Instance State

List instances:

```bash
aws ec2 describe-instances \
    --profile production \
    --region ap-south-1 \
    --query 'Reservations[].Instances[].{
        Id:InstanceId,
        State:State.Name,
        Type:InstanceType,
        AZ:Placement.AvailabilityZone,
        PrivateIP:PrivateIpAddress,
        PublicIP:PublicIpAddress
    }' \
    --output table
```

Inspect a specific instance:

```bash
aws ec2 describe-instances \
    --profile production \
    --region ap-south-1 \
    --instance-ids i-0123456789abcdef0
```

Check status checks:

```bash
aws ec2 describe-instance-status \
    --profile production \
    --region ap-south-1 \
    --instance-ids i-0123456789abcdef0
```

Use both lifecycle state and health information when making operational decisions.

## Launching Instances

Production instances should normally be launched through:

- Auto Scaling Groups
- Launch Templates
- Infrastructure as Code
- CI/CD pipelines
- Approved AMIs

Manual instance launches are useful for:

- Incident recovery
- Troubleshooting
- Development
- Controlled administrative operations

A typical production launch flow is:

```text
Golden AMI
    |
    v
Launch Template
    |
    v
Auto Scaling Group
    |
    v
EC2 Instance
    |
    v
Bootstrap / User Data
    |
    v
Application Startup
    |
    v
Health Checks
    |
    v
Load Balancer
```

## Launch Templates

Launch Templates provide a versioned definition for EC2 instance launches.

A template can define:

- AMI
- Instance type
- IAM instance profile
- Security Groups
- EBS mappings
- User Data
- Metadata options
- Network configuration
- Purchasing options

Inspect templates:

```bash
aws ec2 describe-launch-templates \
    --profile production \
    --region ap-south-1
```

Inspect versions:

```bash
aws ec2 describe-launch-template-versions \
    --profile production \
    --region ap-south-1 \
    --launch-template-name production-api
```

Launch Templates are preferable to maintaining undocumented launch parameters across individual instances.

## User Data During Lifecycle

User Data is commonly executed during initial instance boot.

A typical bootstrap flow:

```text
EC2 Launch
    |
    v
Operating System
    |
    v
Cloud-init / User Data
    |
    +-- Install dependencies
    +-- Fetch configuration
    +-- Start services
    +-- Register application
    |
    v
Health Check
```

For a production application, User Data should be:

- Idempotent where practical
- Observable
- Fast enough for instance startup expectations
- Free of hard-coded secrets
- Compatible with the AMI
- Safe to rerun when appropriate

Avoid turning User Data into a large deployment script containing the entire application's operational logic.

## Starting an Instance

Start a stopped instance:

```bash
aws ec2 start-instances \
    --profile production \
    --region ap-south-1 \
    --instance-ids i-0123456789abcdef0
```

Wait for the state transition:

```bash
aws ec2 wait instance-running \
    --profile production \
    --region ap-south-1 \
    --instance-ids i-0123456789abcdef0
```

Then verify:

```bash
aws ec2 describe-instances \
    --profile production \
    --region ap-south-1 \
    --instance-ids i-0123456789abcdef0 \
    --query 'Reservations[0].Instances[0].{
        State:State.Name,
        PrivateIP:PrivateIpAddress,
        PublicIP:PublicIpAddress
    }' \
    --output table
```

Starting an instance does not guarantee that the application is ready.

Continue with:

```text
EC2 running
    |
    v
Status checks
    |
    v
Application startup
    |
    v
Target health
    |
    v
Production traffic
```

## Stopping an Instance

Stop:

```bash
aws ec2 stop-instances \
    --profile production \
    --region ap-south-1 \
    --instance-ids i-0123456789abcdef0
```

Wait:

```bash
aws ec2 wait instance-stopped \
    --profile production \
    --region ap-south-1 \
    --instance-ids i-0123456789abcdef0
```

Stopping an instance is different from terminating it.

A stopped EBS-backed instance can generally be started again, while its EBS volumes remain available according to their lifecycle configuration.

Important considerations include:

- Application shutdown
- In-flight requests
- Background jobs
- Database connections
- Temporary state
- Public IPv4 changes
- EBS costs
- Instance-store data

## Stop vs Terminate

| Operation | Can restart? | EBS data | Instance-store data | Typical use |
|---|---|---|---|---|
| Stop | Yes | Usually retained | Lost | Temporary shutdown |
| Reboot | Yes | Retained | Retained | OS/application restart |
| Terminate | No | Depends on `DeleteOnTermination` | Lost | Permanent removal |

Termination should be treated as a destructive operation.

## Rebooting an Instance

Reboot:

```bash
aws ec2 reboot-instances \
    --profile production \
    --region ap-south-1 \
    --instance-ids i-0123456789abcdef0
```

Rebooting is appropriate when:

- The OS requires a reboot
- A controlled kernel update requires it
- A temporary OS-level issue exists
- A service restart is insufficient

Do not use reboot as the default response to application problems.

For example:

```text
High API latency
    |
    +--> Check ALB
    +--> Check CPU
    +--> Check memory
    +--> Check DB
    +--> Check Redis
    +--> Check application logs
    |
    v
Determine root cause
```

A reboot can temporarily hide symptoms without resolving the underlying problem.

## Application Restart vs Instance Reboot

For a Django application:

```text
Code/config issue
      |
      v
Restart Gunicorn
```

For an operating-system problem:

```text
Kernel/system issue
      |
      v
Reboot EC2
```

Use the least disruptive operation that addresses the actual failure.

For example:

```bash
sudo systemctl restart gunicorn
```

is operationally different from:

```bash
sudo reboot
```

The first affects the application service; the second affects the entire instance.

## Terminating an Instance

Terminate:

```bash
aws ec2 terminate-instances \
    --profile production \
    --region ap-south-1 \
    --instance-ids i-0123456789abcdef0
```

Wait:

```bash
aws ec2 wait instance-terminated \
    --profile production \
    --region ap-south-1 \
    --instance-ids i-0123456789abcdef0
```

Before terminating a production instance, verify:

- It is not uniquely hosting persistent state
- It is not required for a critical workload
- Traffic has been drained
- Backups exist
- Replacement capacity is available
- The instance is not part of an active investigation
- The termination is consistent with the ASG/IaC source of truth

## Termination Protection

Termination protection can help prevent accidental termination through the EC2 API or console.

Inspect:

```bash
aws ec2 describe-instance-attribute \
    --profile production \
    --region ap-south-1 \
    --instance-id i-0123456789abcdef0 \
    --attribute disableApiTermination
```

Enable:

```bash
aws ec2 modify-instance-attribute \
    --profile production \
    --region ap-south-1 \
    --instance-id i-0123456789abcdef0 \
    --disable-api-termination
```

Disable:

```bash
aws ec2 modify-instance-attribute \
    --profile production \
    --region ap-south-1 \
    --instance-id i-0123456789abcdef0 \
    --no-disable-api-termination
```

Termination protection is a safety mechanism, not a replacement for backups.

It should also be used carefully with Auto Scaling because automated replacement mechanisms have their own lifecycle behavior.

## Stop Protection

Stop protection prevents accidental stopping of an instance through supported EC2 operations.

Inspect:

```bash
aws ec2 describe-instance-attribute \
    --profile production \
    --region ap-south-1 \
    --instance-id i-0123456789abcdef0 \
    --attribute disableApiStop
```

Enable:

```bash
aws ec2 modify-instance-attribute \
    --profile production \
    --region ap-south-1 \
    --instance-id i-0123456789abcdef0 \
    --disable-api-stop
```

Use protection mechanisms selectively. Excessive protection can make automation and incident response harder.

## EBS Lifecycle During Instance Operations

EBS volumes have their own lifecycle.

For an EBS-backed instance:

```text
EC2
 |
 +-- Root EBS
 |
 +-- Data EBS
```

When the instance is stopped:

```text
EC2 -> stopped
EBS -> retained
```

When the instance is terminated:

```text
EC2 -> terminated

Root EBS:
    DeleteOnTermination -> determines behavior

Data EBS:
    DeleteOnTermination -> determines behavior
```

Inspect block device mappings:

```bash
aws ec2 describe-instances \
    --profile production \
    --region ap-south-1 \
    --instance-ids i-0123456789abcdef0 \
    --query 'Reservations[0].Instances[0].BlockDeviceMappings[].{
        Device:DeviceName,
        Volume: Ebs.VolumeId,
        DeleteOnTermination:Ebs.DeleteOnTermination
    }' \
    --output table
```

Never assume all attached EBS volumes survive termination.

## Instance Store During Lifecycle Operations

Instance store is ephemeral.

Data stored on instance-store volumes is lost when the instance is stopped, hibernated, or terminated according to the instance lifecycle semantics.

Do not use instance store as the only location for important persistent application data.

Appropriate uses include:

- Temporary files
- Caches
- Scratch processing
- Rebuildable intermediate data

For persistent state, use appropriate durable storage.

## Public IPv4 Address Changes

A dynamically assigned public IPv4 address is not guaranteed to remain the same across stop/start operations.

If stable public addressing is required, an Elastic IP can provide a persistent public IPv4 address.

However, production APIs should generally prefer stable DNS and load balancers rather than binding application architecture directly to an individual EC2 public IP.

Recommended:

```text
Client
  |
  v
DNS
  |
  v
ALB
  |
  v
EC2
```

rather than:

```text
Client
  |
  v
EC2 Public IP
```

## Private IP Addresses

For many EC2 networking architectures, the private IP address is more operationally important than the public address.

Private IPs are used for:

- ALB-to-EC2 traffic
- EC2-to-database traffic
- Service-to-service communication
- Internal APIs
- Monitoring
- Management

Do not hard-code instance private IP addresses in application configuration when the instances are expected to be replaced.

Use:

- DNS
- Load balancers
- Service discovery
- Auto Scaling
- Configuration management

## Instance Replacement

For stateless workloads, replacement is usually preferable to manual repair.

Example:

```text
Unhealthy Instance
       |
       v
Remove From Traffic
       |
       v
Launch Replacement
       |
       v
Health Checks
       |
       v
Receive Traffic
       |
       v
Terminate Old Instance
```

This is the foundation of immutable infrastructure.

For an ASG, replacement can be automatic when the instance is detected as unhealthy.

## Auto Scaling Lifecycle

An Auto Scaling Group changes instance lifecycle state independently of the raw EC2 state.

Example:

```text
Pending
   |
   v
Pending:Wait
   |
   v
InService
   |
   v
Terminating:Wait
   |
   v
Terminating
   |
   v
Terminated
```

Lifecycle hooks can pause transitions so that custom actions can complete.

Use lifecycle hooks for operations such as:

- Configuration registration
- Log collection
- Application initialization
- Connection draining
- External service deregistration
- Cleanup

Do not use lifecycle hooks as a substitute for normal application orchestration.

## Auto Scaling and Unhealthy Instances

An ASG can replace an unhealthy instance.

Typical flow:

```text
EC2
 |
 v
Health Check Fails
 |
 v
ASG Marks Instance Unhealthy
 |
 v
Instance Replacement
 |
 +--> New Instance
 |
 +--> Old Instance Terminated
```

Depending on configuration, health information can come from EC2 status checks, load balancer health, and other supported health sources.

Repeated replacement indicates a problem that should be investigated rather than ignored.

Common causes:

- Broken AMI
- Incorrect User Data
- Wrong application port
- Failed health endpoint
- Security Group misconfiguration
- Startup dependency failure
- Insufficient capacity
- Bad application deployment

## Instance Refresh

Instance Refresh is useful when a fleet needs to move to a new launch configuration.

Example:

```text
Launch Template v1
        |
        v
Existing Fleet
        |
        v
Launch Template v2
        |
        v
Instance Refresh
        |
        +----> Replace Instance 1
        |
        +----> Health Check
        |
        +----> Replace Instance 2
        |
        +----> Health Check
        |
        v
Fleet on v2
```

Use it for:

- AMI updates
- OS patching
- Application image updates
- Launch Template changes
- Security configuration changes

Validate the new launch configuration before starting a fleet-wide refresh.

## Scheduled Events

AWS can schedule infrastructure maintenance affecting EC2 instances.

Possible actions include:

- Reboot
- Stop
- Retirement
- Maintenance-related events

Inspect scheduled events:

```bash
aws ec2 describe-instance-status \
    --profile production \
    --region ap-south-1 \
    --instance-ids i-0123456789abcdef0 \
    --include-all-instances
```

When an instance has a scheduled event:

1. Identify the event.
2. Determine the expected impact.
3. Check whether the workload is redundant.
4. Confirm backup status.
5. Replace or migrate the instance when appropriate.
6. Verify application health afterward.

## Maintenance Strategy

For a standalone production instance:

```text
Scheduled Maintenance
       |
       v
Backup
       |
       v
Drain Traffic
       |
       v
Maintenance
       |
       v
Health Validation
       |
       v
Restore Traffic
```

For an ASG-backed application:

```text
Scheduled Maintenance
       |
       v
ASG Capacity
       |
       +--> Healthy Instance A
       +--> Healthy Instance B
       +--> Replacement Instance
```

The second model is generally more resilient because maintenance does not have to depend on repairing one specific instance.

## Application Drain Before Maintenance

When an instance is behind an ALB:

```text
ALB
 |
 +-- EC2-A
 |
 +-- EC2-B
 |
 +-- EC2-C
```

Before maintaining EC2-B:

```text
ALB
 |
 +-- EC2-A
 |
 +-- EC2-C

EC2-B
 |
 +-- Draining
```

Existing requests should be allowed to complete according to the target group's deregistration behavior.

This is particularly important for:

- Long API requests
- WebSockets
- gRPC streams
- Server-sent events
- Long-running jobs

## Lifecycle Operations for Celery Workers

A Celery worker should not simply be terminated while actively processing important tasks.

A safer sequence is:

```text
Remove Worker From Scheduling
          |
          v
Stop New Work
          |
          v
Allow Current Tasks to Finish
          |
          v
Shutdown Worker
          |
          v
Terminate EC2
```

The exact mechanism depends on the Celery deployment and task acknowledgment configuration.

For critical workloads, design tasks to be retryable and idempotent so that instance termination does not create unrecoverable work.

## Graceful Shutdown

A production application should handle termination signals correctly.

For example:

```text
SIGTERM
   |
   v
Application Shutdown
   |
   +-- Stop accepting new work
   +-- Finish safe in-flight work
   +-- Close DB connections
   +-- Close Redis connections
   +-- Flush logs
   |
   v
Process Exit
```

This becomes important when instances are:

- Terminated by ASG
- Replaced during deployment
- Removed during scaling
- Rebooted
- Manually stopped

## Instance Metadata and Lifecycle

Instance metadata can provide runtime information such as:

- Instance ID
- Instance type
- Availability Zone
- Region
- Local IP
- IAM role credentials through the metadata service

Applications should use IMDSv2 where possible and avoid exposing instance metadata endpoints unnecessarily.

For production systems, configure metadata options deliberately in the Launch Template.

## Safe Lifecycle Automation

A lifecycle automation script should verify its target before executing a destructive operation.

Example:

```bash
INSTANCE_ID="i-0123456789abcdef0"
REGION="ap-south-1"
PROFILE="production"

aws ec2 describe-instances \
    --profile "$PROFILE" \
    --region "$REGION" \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].{
        Id:InstanceId,
        State:State.Name,
        Name:Tags[?Key==`Name`]|[0].Value
    }' \
    --output table
```

Then explicitly confirm the intended operation before termination.

For automation, prefer tag-based discovery combined with strong filters rather than hard-coded instance IDs.

## Tag-Based Lifecycle Operations

Example:

```bash
aws ec2 describe-instances \
    --profile production \
    --region ap-south-1 \
    --filters \
        "Name=tag:Environment,Values=staging" \
        "Name=tag:Application,Values=api" \
        "Name=instance-state-name,Values=running" \
    --query 'Reservations[].Instances[].InstanceId' \
    --output text
```

This can be useful for controlled operational workflows.

Be careful with broad filters:

```text
Environment=production
```

may match many resources.

Use multiple identifying dimensions where possible:

```text
Environment
+
Application
+
Role
+
Owner
```

## Waiting for Lifecycle Transitions

AWS CLI waiters reduce the risk of assuming an operation has completed.

Start:

```bash
aws ec2 start-instances \
    --profile production \
    --region ap-south-1 \
    --instance-ids "$INSTANCE_ID"

aws ec2 wait instance-running \
    --profile production \
    --region ap-south-1 \
    --instance-ids "$INSTANCE_ID"
```

Stop:

```bash
aws ec2 stop-instances \
    --profile production \
    --region ap-south-1 \
    --instance-ids "$INSTANCE_ID"

aws ec2 wait instance-stopped \
    --profile production \
    --region ap-south-1 \
    --instance-ids "$INSTANCE_ID"
```

Terminate:

```bash
aws ec2 terminate-instances \
    --profile production \
    --region ap-south-1 \
    --instance-ids "$INSTANCE_ID"

aws ec2 wait instance-terminated \
    --profile production \
    --region ap-south-1 \
    --instance-ids "$INSTANCE_ID"
```

A lifecycle state transition is not equivalent to application readiness.

## Production Lifecycle Workflow

For a controlled maintenance operation:

```text
Identify Instance
       |
       v
Verify Environment
       |
       v
Check Health
       |
       v
Check Traffic
       |
       v
Check Backup
       |
       v
Drain / Remove From Service
       |
       v
Perform Lifecycle Operation
       |
       v
Wait for State Transition
       |
       v
Verify EC2 Health
       |
       v
Verify Application Health
       |
       v
Verify Load Balancer Health
       |
       v
Restore Traffic
```

This workflow prevents the common mistake of considering an AWS API response as the end of the operation.

## Production Lifecycle Architecture

For a modern backend:

```text
                    Git
                     |
                     v
                  CI/CD
                     |
                     v
                Golden AMI
                     |
                     v
              Launch Template
                     |
                     v
               Auto Scaling
                Group
              /    |    \
             /     |     \
           EC2    EC2    EC2
             \     |     /
              \    |    /
               Target Group
                     |
                     v
                    ALB
                     |
                     v
                   Users
```

The operational model becomes:

```text
Do not preserve:
"this exact EC2 instance"

Preserve:
"the ability to recreate a healthy EC2 instance"
```

This distinction is fundamental to scalable infrastructure.

## High Availability Considerations

Avoid architectures where one EC2 instance represents the entire service.

Prefer:

- Multiple Availability Zones
- Auto Scaling Groups
- Load balancers
- Stateless application instances
- Externalized persistent state
- Automated health checks
- Tested recovery procedures

Example:

```text
                  ALB
                   |
          +--------+--------+
          |                 |
         AZ-A              AZ-B
          |                 |
       EC2-A1            EC2-B1
       EC2-A2            EC2-B2
```

The lifecycle of one instance should not determine the availability of the entire application.

## Security Considerations

Lifecycle operations can be destructive and should therefore be controlled.

Use:

- Least-privilege IAM
- Separate production profiles
- Strong resource tagging
- CloudTrail auditing
- MFA where appropriate
- Change approval for destructive operations
- Termination protection where justified
- Restricted `ec2:TerminateInstances`
- Restricted modification of Launch Templates
- Systems Manager Session Manager instead of unnecessary SSH exposure

A production operator should always verify:

```bash
aws sts get-caller-identity \
    --profile production
```

before executing destructive operations.

## Cost Considerations

Lifecycle management directly affects EC2 cost.

Stopping development instances can reduce compute charges while preserving EBS storage costs.

Terminating unused instances removes compute and attached storage costs where applicable, but can also destroy recoverability if backups are missing.

Review:

- Long-running idle instances
- Stopped instances
- Unused EBS volumes
- Old AMIs
- Old snapshots
- Elastic IPs
- Oversized instances

Do not terminate resources solely based on low CPU utilization. Verify ownership and workload purpose first.

## Monitoring Lifecycle Operations

Monitor:

- Instance state transitions
- Status checks
- ASG scaling activities
- Instance refresh progress
- Target health
- Application startup time
- User Data execution
- CloudWatch alarms
- Scheduled events
- Termination events

A useful operational metric is startup time:

```text
Instance Launch
      |
      v
OS Ready
      |
      v
Application Ready
      |
      v
ALB Healthy
```

If this takes too long, Auto Scaling may struggle to respond quickly to traffic changes.

## Troubleshooting

### Instance Stuck in `pending`

Investigate:

- Capacity availability
- AMI validity
- Launch configuration
- Network configuration
- EBS configuration
- IAM instance profile
- Service events

### Instance Running but Application Unavailable

Check:

```text
EC2 state
   |
   v
Status checks
   |
   v
Security Group
   |
   v
Listening port
   |
   v
Nginx
   |
   v
Gunicorn/Uvicorn
   |
   v
Application
```

### Instance Starts but Never Becomes Healthy

Common causes:

- User Data failure
- Incorrect application configuration
- Health-check path mismatch
- Security Group issue
- Application startup failure
- Missing environment variables
- Database connectivity failure
- Incorrect target group port

### ASG Repeatedly Replaces Instances

This usually indicates a systematic fleet problem.

Investigate:

```text
Launch Template
      |
      v
AMI
      |
      v
User Data
      |
      v
Application Startup
      |
      v
Health Check
      |
      v
Target Group
```

Do not keep increasing the ASG desired capacity without understanding why instances are becoming unhealthy.

### Instance Terminated Unexpectedly

Investigate:

- CloudTrail
- ASG activity history
- Scheduled events
- Instance status
- Auto Scaling policies
- Instance refresh
- Manual operators
- Infrastructure-as-Code changes

Determine whether termination was:

```text
Intentional
    |
    +-- Deployment
    +-- Scale-in
    +-- Maintenance

or

Unexpected
    |
    +-- Failure
    +-- Misconfiguration
    +-- Operator action
    +-- Automation
```

## Common Mistakes

### Treating `running` as Healthy

`running` only represents the EC2 lifecycle state.

**Avoid it:** check status checks, target health, and application health.

### Rebooting Instead of Diagnosing

A reboot can hide symptoms without solving the underlying problem.

**Avoid it:** establish whether the problem is application, OS, network, dependency, or infrastructure related.

### Terminating Before Draining

Terminating a serving instance can interrupt active requests.

**Avoid it:** deregister the target and allow appropriate connection draining.

### Storing Persistent Data on Disposable Instances

A replacement instance can destroy unique local state.

**Avoid it:** externalize persistent state and maintain appropriate backups.

### Hard-Coding Instance IPs

Auto Scaling and replacement make instance IPs unstable.

**Avoid it:** use DNS, load balancers, or service discovery.

### Running Manual Changes Against ASG Instances

A manual change to one instance can disappear when the ASG replaces it.

**Avoid it:** modify the Launch Template, AMI, configuration, or deployment pipeline.

### Using User Data as a Monolithic Deployment System

Large bootstrap scripts become difficult to test and debug.

**Avoid it:** bake stable dependencies into images and use focused initialization logic.

### Ignoring Instance Store Ephemeral Behavior

Data stored there can disappear during lifecycle operations.

**Avoid it:** use durable storage for important data.

### Forgetting `DeleteOnTermination`

An engineer may accidentally delete or retain EBS volumes contrary to the intended lifecycle.

**Avoid it:** inspect block-device mappings before destructive operations.

### Disabling Lifecycle Protection Indiscriminately

Protection mechanisms can prevent accidental operations, but excessive use can interfere with automation.

**Avoid it:** apply protection based on workload requirements.

## Interview Traps

### What Is the Difference Between Stop and Terminate?

Stopping shuts down an EBS-backed instance while preserving the instance resource for later restart. Termination permanently removes the instance resource.

### What Is the Difference Between Reboot and Stop/Start?

A reboot restarts the operating system while keeping the instance allocation. Stop/start involves stopping the instance and subsequently starting it again, which can involve different underlying infrastructure behavior and may change a dynamically assigned public IPv4 address.

### Does Stopping an Instance Delete Its EBS Volume?

Not normally. EBS volumes associated with the instance are generally retained during a stop operation.

### Does Terminating an Instance Always Delete Its EBS Volumes?

No. The `DeleteOnTermination` setting determines whether an attached EBS volume is deleted when the instance is terminated.

### Why Prefer Replacement Over Repair?

Replacement provides a known, reproducible state and aligns with immutable infrastructure.

```text
Known-good image
      |
      v
New instance
      |
      v
Health check
      |
      v
Traffic
```

### What Happens to Instance Store During Lifecycle Operations?

Instance-store data is ephemeral and should not be treated as durable storage.

### Why Can an ASG Keep Replacing Instances?

Because a systematic problem may cause new instances to fail health checks, startup, or other lifecycle requirements.

Typical causes include:

- Bad AMI
- Broken User Data
- Incorrect Security Group
- Failed application startup
- Wrong health-check configuration

### Why Should Production EC2 Instances Be Behind a Load Balancer?

It separates client traffic from individual instance lifecycle and allows healthy instances to continue serving traffic while another instance is replaced or maintained.

### Why Is Infrastructure as Code Important for Lifecycle Management?

Manual instance changes are difficult to reproduce. IaC and Launch Templates provide a consistent source of truth for rebuilding infrastructure.

## Production Checklist

### Before Lifecycle Changes

- [ ] Verify AWS account
- [ ] Verify Region
- [ ] Identify the exact instance
- [ ] Verify environment and application tags
- [ ] Check instance health
- [ ] Check target health
- [ ] Check backup status
- [ ] Check attached EBS volumes
- [ ] Check `DeleteOnTermination`
- [ ] Verify replacement capacity
- [ ] Verify maintenance impact

### During Maintenance

- [ ] Drain application traffic
- [ ] Stop new work where required
- [ ] Preserve critical in-flight operations
- [ ] Perform the minimum necessary lifecycle operation
- [ ] Monitor state transitions
- [ ] Monitor application health

### After Lifecycle Changes

- [ ] Verify EC2 state
- [ ] Verify EC2 status checks
- [ ] Verify application startup
- [ ] Verify target health
- [ ] Verify logs
- [ ] Verify downstream connectivity
- [ ] Restore traffic
- [ ] Confirm monitoring is healthy
- [ ] Document the change

## Key Takeaways

- **Distinguish lifecycle state from health:** an EC2 instance being `running` does not mean the operating system or application is healthy.
- **Prefer replacement over manual repair for stateless workloads:** AMIs, Launch Templates, Auto Scaling, and load balancers make instances reproducible and disposable.
- **Perform lifecycle operations safely:** drain traffic, preserve required work, verify storage and backups, execute the operation, then validate EC2, application, and load-balancer health.
- **Treat termination as destructive:** understand `DeleteOnTermination`, instance-store behavior, persistent data, backups, and recovery before terminating an instance.
- **Keep the source of truth outside individual instances:** changes required for future instances should be implemented through AMIs, Launch Templates, configuration management, CI/CD, and Infrastructure as Code.