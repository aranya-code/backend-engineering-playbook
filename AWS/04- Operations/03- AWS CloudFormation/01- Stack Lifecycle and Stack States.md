# 01- Stack Lifecycle and Stack States

## Overview

AWS CloudFormation manages infrastructure through a declarative stack lifecycle. A stack represents a collection of AWS resources described by a CloudFormation template and managed as a single unit.

Understanding stack states is essential for production operations because the stack status determines:

- Whether another operation can be started.
- Whether an update can be performed.
- Whether rollback is in progress or has failed.
- Whether the stack can be deleted.
- Whether manual recovery is required.
- Whether the current infrastructure state can safely accept another deployment.

CloudFormation exposes stack-level states such as `CREATE_IN_PROGRESS`, `CREATE_COMPLETE`, `UPDATE_IN_PROGRESS`, `UPDATE_ROLLBACK_COMPLETE`, `DELETE_IN_PROGRESS`, and `DELETE_COMPLETE`. Resource-level events provide the detailed explanation behind these states. :contentReference[oaicite:0]{index=0}

A useful operational model is:

```text
Template
   |
   v
CloudFormation Stack
   |
   +-------------------+
   |                   |
   v                   v
Stack State       Stack Events
   |                   |
   |                   v
   |             Resource State
   |                   |
   |                   v
   |             Resource Error
   |
   v
Allowed Next Operation
```

## Stack Lifecycle

A typical CloudFormation lifecycle consists of:

```text
CREATE
  |
  v
CREATE_IN_PROGRESS
  |
  +---- success ----> CREATE_COMPLETE
  |
  +---- failure ----> ROLLBACK_IN_PROGRESS
                           |
                           +---- success ----> ROLLBACK_COMPLETE
                           |
                           +---- failure ----> ROLLBACK_FAILED

UPDATE
  |
  v
UPDATE_IN_PROGRESS
  |
  +---- success ----> UPDATE_COMPLETE
  |
  +---- failure ----> UPDATE_ROLLBACK_IN_PROGRESS
                           |
                           +---- success ----> UPDATE_ROLLBACK_COMPLETE
                           |
                           +---- failure ----> UPDATE_ROLLBACK_FAILED

DELETE
  |
  v
DELETE_IN_PROGRESS
  |
  +---- success ----> DELETE_COMPLETE
  |
  +---- failure ----> DELETE_FAILED
```

The exact path depends on the operation, failure mode, stack configuration, and whether the stack has a previous stable state.

## Stack States vs Resource States

Stack states describe the overall operation. Resource states describe individual resources.

For example:

```text
Stack
UPDATE_ROLLBACK_FAILED
       |
       +-- AWS::EC2::Instance
       |      UPDATE_COMPLETE
       |
       +-- AWS::RDS::DBInstance
       |      UPDATE_FAILED
       |
       +-- AWS::ElasticLoadBalancingV2::LoadBalancer
              UPDATE_COMPLETE
```

The stack status alone is therefore insufficient for diagnosis.

Use:

```bash
aws cloudformation describe-stack-events \
  --stack-name <stack-name> \
  --region <region>
```

CloudFormation events expose fields such as `LogicalResourceId`, `PhysicalResourceId`, `ResourceType`, `ResourceStatus`, timestamp, and `ResourceStatusReason`. The `ResourceStatusReason` is frequently the most useful field for identifying the underlying failure. :contentReference[oaicite:1]{index=1}

## Create Lifecycle

### `CREATE_IN_PROGRESS`

The stack is being created.

CloudFormation evaluates the template, resolves dependencies, and provisions resources according to the dependency graph.

For example:

```text
VPC
 |
 +--> Subnet
       |
       +--> Security Group
              |
              +--> Application Load Balancer
                     |
                     +--> ECS Service
```

CloudFormation can create independent resources concurrently when their dependencies allow it.

### `CREATE_COMPLETE`

The stack was successfully created.

At this point the stack has reached a stable successful state and can normally be updated or deleted.

```bash
aws cloudformation describe-stacks \
  --stack-name my-backend-stack \
  --query 'Stacks[0].StackStatus'
```

Expected result:

```text
CREATE_COMPLETE
```

### `CREATE_FAILED`

Stack creation failed.

Common causes include:

- Invalid resource configuration.
- Missing IAM permissions.
- Invalid parameter values.
- Resource quota exhaustion.
- Resource stabilization timeout.
- Existing resource name conflicts.
- Dependency failures.
- AWS service errors.

Always inspect events:

```bash
aws cloudformation describe-stack-events \
  --stack-name my-backend-stack \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].{Resource:LogicalResourceId,Type:ResourceType,Reason:ResourceStatusReason}'
```

A `CREATE_FAILED` state should be investigated at the resource level rather than treated as a generic CloudFormation failure. :contentReference[oaicite:2]{index=2}

## Create Rollback States

### `ROLLBACK_IN_PROGRESS`

CloudFormation is removing resources created during a failed stack creation or an explicitly canceled creation operation.

```text
CREATE_IN_PROGRESS
       |
       v
Resource creation fails
       |
       v
ROLLBACK_IN_PROGRESS
       |
       v
Delete successfully created resources
```

The purpose is to return the environment to a clean state after an unsuccessful creation.

### `ROLLBACK_COMPLETE`

CloudFormation successfully completed the rollback of a failed creation.

This state is operationally important because a stack in `ROLLBACK_COMPLETE` can only be deleted. It cannot be updated into a working stack. :contentReference[oaicite:3]{index=3}

Typical recovery:

```bash
aws cloudformation delete-stack \
  --stack-name my-backend-stack \
  --region ap-south-1
```

Then correct the template or configuration and create a new stack.

### `ROLLBACK_FAILED`

CloudFormation could not successfully clean up after a failed creation.

For example:

```text
CREATE_FAILED
     |
     v
ROLLBACK_IN_PROGRESS
     |
     +--> Resource deletion fails
              |
              v
       ROLLBACK_FAILED
```

The stack may contain resources that still exist and require investigation before deletion or recovery.

## Update Lifecycle

A normal update follows:

```text
Stable Stack
     |
     v
UPDATE_IN_PROGRESS
     |
     +---- success ----> UPDATE_COMPLETE
     |
     +---- failure ----> UPDATE_ROLLBACK_IN_PROGRESS
                               |
                               v
                     UPDATE_ROLLBACK_COMPLETE
```

CloudFormation normally attempts to restore resources modified during a failed update to their previous configuration. :contentReference[oaicite:4]{index=4}

### `UPDATE_IN_PROGRESS`

An update is currently being applied.

While the update is running:

- Resource changes are being executed.
- Some resources may temporarily be unavailable.
- Replacement resources may be created.
- Dependencies may cause other resources to change.
- The final state is not yet known.

You can monitor progress with:

```bash
aws cloudformation describe-stack-events \
  --stack-name my-backend-stack \
  --region ap-south-1
```

### Canceling an Update

An update can be canceled while the stack is in `UPDATE_IN_PROGRESS`.

```bash
aws cloudformation cancel-update-stack \
  --stack-name my-backend-stack \
  --region ap-south-1
```

CloudFormation then rolls the stack back toward the configuration that existed before the update. :contentReference[oaicite:5]{index=5}

Do not treat cancellation as an immediate stop of every underlying AWS operation. CloudFormation still has to reconcile the stack state.

### `UPDATE_COMPLETE_CLEANUP_IN_PROGRESS`

CloudFormation has completed the main update work but is still performing cleanup associated with the operation.

This can be particularly relevant when resources are replaced.

For example:

```text
Old EC2 Instance
      |
      | replacement required
      v
New EC2 Instance
      |
      v
New resource becomes ready
      |
      v
Old resource cleanup
      |
      v
UPDATE_COMPLETE
```

Resource replacement can temporarily increase resource consumption because CloudFormation may create the replacement before deleting the old resource. This can expose account quotas during an update. :contentReference[oaicite:6]{index=6}

### `UPDATE_COMPLETE`

The update completed successfully.

This is a stable state from which another update can normally be initiated.

```text
UPDATE_COMPLETE
      |
      +--> update-stack
      |
      +--> delete-stack
      |
      +--> drift detection
      |
      +--> change set
```

## Update Rollback States

### `UPDATE_ROLLBACK_IN_PROGRESS`

A stack update failed and CloudFormation is attempting to restore the previous configuration.

```text
UPDATE_IN_PROGRESS
       |
       v
Resource update fails
       |
       v
UPDATE_ROLLBACK_IN_PROGRESS
       |
       v
Restore previous configuration
```

The rollback itself can fail if the original state cannot be restored.

### `UPDATE_ROLLBACK_COMPLETE`

CloudFormation successfully restored the stack to its previous stable configuration.

The failed update has not been applied, but the stack remains usable.

Typical workflow:

```text
UPDATE_FAILED
      |
      v
UPDATE_ROLLBACK_IN_PROGRESS
      |
      v
UPDATE_ROLLBACK_COMPLETE
      |
      v
Fix template/configuration
      |
      v
Retry update
```

### `UPDATE_ROLLBACK_FAILED`

This is one of the most important production states.

CloudFormation attempted to roll back an update but could not restore one or more resources.

For example:

```text
Previous State
     |
     v
Update DB
     |
     v
Update fails
     |
     v
Rollback DB
     |
     +---- previous DB was manually deleted
                    |
                    v
          Rollback cannot complete
                    |
                    v
       UPDATE_ROLLBACK_FAILED
```

A stack in this state cannot simply receive another normal update. The underlying rollback problem must be resolved first. :contentReference[oaicite:7]{index=7}

After fixing the cause, continue the rollback:

```bash
aws cloudformation continue-update-rollback \
  --stack-name my-backend-stack \
  --region ap-south-1
```

The target recovery state is generally:

```text
UPDATE_ROLLBACK_COMPLETE
```

CloudFormation also supports `--resources-to-skip` when specific resources cannot be rolled back. This is an advanced recovery mechanism and should be used carefully because skipped resources can become inconsistent with the template. :contentReference[oaicite:8]{index=8}

Example:

```bash
aws cloudformation continue-update-rollback \
  --stack-name my-backend-stack \
  --resources-to-skip MyResource
```

Do not immediately perform another update after skipping a resource. First reconcile the actual infrastructure state with the CloudFormation template.

## Delete Lifecycle

A normal deletion follows:

```text
Stable Stack
     |
     v
DELETE_IN_PROGRESS
     |
     +---- success ----> DELETE_COMPLETE
     |
     +---- failure ----> DELETE_FAILED
```

### `DELETE_IN_PROGRESS`

CloudFormation is deleting stack resources according to their dependencies and deletion policies.

Some resources may be retained instead of deleted because of:

- `DeletionPolicy: Retain`
- `DeletionPolicy: Snapshot`
- Resource-specific behavior

### `DELETE_COMPLETE`

The stack deletion completed successfully.

CloudFormation retains deleted stack information for a limited period, but the actual provisioned resources are removed unless they were intentionally retained. :contentReference[oaicite:9]{index=9}

### `DELETE_FAILED`

One or more resources could not be deleted.

Common causes include:

- Resource dependencies.
- Resource deletion protection.
- Resource still referenced elsewhere.
- Resource modified outside CloudFormation.
- Missing IAM permissions.
- Service-specific deletion restrictions.
- Retained resources.
- Custom resource deletion failures.

Inspect events:

```bash
aws cloudformation describe-stack-events \
  --stack-name my-backend-stack \
  --query 'StackEvents[?ResourceStatus==`DELETE_FAILED`].{Resource:LogicalResourceId,Type:ResourceType,Reason:ResourceStatusReason}'
```

Do not repeatedly delete the stack without understanding the failed resource.

## Review and Import States

CloudFormation also has lifecycle states related to review and resource import.

### `REVIEW_IN_PROGRESS`

This state can occur during creation workflows where CloudFormation creates an expected stack identity before resources are actually provisioned.

It is not equivalent to a successfully deployed stack.

A `REVIEW_IN_PROGRESS` stack also counts against the account's stack limit. :contentReference[oaicite:10]{index=10}

### Import States

Resource import introduces additional states:

```text
IMPORT_IN_PROGRESS
       |
       +---- success ----> IMPORT_COMPLETE
       |
       +---- failure ----> IMPORT_ROLLBACK_IN_PROGRESS
                                  |
                                  +----> IMPORT_ROLLBACK_COMPLETE
                                  |
                                  +----> IMPORT_ROLLBACK_FAILED
```

These states are relevant when bringing existing AWS resources under CloudFormation management.

Do not assume that an imported resource was created by CloudFormation. Import establishes CloudFormation management over an existing resource.

## Stack State Reference

| State | Meaning | Typical Next Action |
|---|---|---|
| `CREATE_IN_PROGRESS` | Creation running | Monitor events |
| `CREATE_COMPLETE` | Creation succeeded | Update, inspect, or delete |
| `CREATE_FAILED` | Creation failed | Inspect failed resource |
| `ROLLBACK_IN_PROGRESS` | Failed creation is being cleaned up | Monitor rollback |
| `ROLLBACK_COMPLETE` | Failed creation was successfully rolled back | Delete and recreate |
| `ROLLBACK_FAILED` | Creation rollback failed | Investigate failed cleanup |
| `UPDATE_IN_PROGRESS` | Update running | Monitor events |
| `UPDATE_COMPLETE_CLEANUP_IN_PROGRESS` | Update succeeded, cleanup running | Monitor |
| `UPDATE_COMPLETE` | Update succeeded | Normal operations |
| `UPDATE_FAILED` | Update failed | Inspect failure / rollback behavior |
| `UPDATE_ROLLBACK_IN_PROGRESS` | Failed update is being reverted | Monitor rollback |
| `UPDATE_ROLLBACK_COMPLETE` | Update rollback succeeded | Fix cause and retry |
| `UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS` | Rollback completed, cleanup running | Monitor |
| `UPDATE_ROLLBACK_FAILED` | Rollback itself failed | Fix issue and continue rollback |
| `DELETE_IN_PROGRESS` | Deletion running | Monitor |
| `DELETE_COMPLETE` | Deletion succeeded | No stack remains |
| `DELETE_FAILED` | Deletion failed | Inspect failed resource |
| `REVIEW_IN_PROGRESS` | Stack is awaiting completion of creation workflow | Complete or clean up appropriately |
| `IMPORT_IN_PROGRESS` | Import running | Monitor |
| `IMPORT_COMPLETE` | Import succeeded | Manage imported resources |
| `IMPORT_ROLLBACK_IN_PROGRESS` | Import rollback running | Monitor |
| `IMPORT_ROLLBACK_FAILED` | Import rollback failed | Investigate and recover |
| `IMPORT_ROLLBACK_COMPLETE` | Import rollback succeeded | Correct import configuration |

CloudFormation's API defines the valid stack status values; resource events additionally expose `DELETE_SKIPPED` for resources retained by a deletion policy. :contentReference[oaicite:11]{index=11}

## Stack State and Operation Eligibility

A useful operational distinction is between **stable**, **transitional**, and **failed-but-recoverable** states.

| Category | Examples | Operational Meaning |
|---|---|---|
| Stable | `CREATE_COMPLETE`, `UPDATE_COMPLETE` | Normal operations possible |
| Transitional | `*_IN_PROGRESS`, `*_CLEANUP_IN_PROGRESS` | Wait for current operation |
| Recoverable failure | `CREATE_FAILED`, `UPDATE_FAILED` | Investigate and recover according to operation |
| Rollback | `ROLLBACK_IN_PROGRESS`, `UPDATE_ROLLBACK_IN_PROGRESS` | CloudFormation is restoring state |
| Rollback failure | `ROLLBACK_FAILED`, `UPDATE_ROLLBACK_FAILED` | Manual investigation may be required |
| Terminal deletion | `DELETE_COMPLETE` | Stack no longer exists |
| Deletion failure | `DELETE_FAILED` | Resources remain and need investigation |

The exact operations available depend on the current stack state, so always inspect the current state before issuing a recovery command.

## Stack Events as the Operational Source of Truth

When a stack is not behaving as expected, inspect events before making changes.

```bash
aws cloudformation describe-stack-events \
  --stack-name my-backend-stack \
  --region ap-south-1
```

A useful filtered query is:

```bash
aws cloudformation describe-stack-events \
  --stack-name my-backend-stack \
  --region ap-south-1 \
  --query 'StackEvents[?contains(ResourceStatus, `FAILED`)].{LogicalId:LogicalResourceId,PhysicalId:PhysicalResourceId,Type:ResourceType,Status:ResourceStatus,Reason:ResourceStatusReason}' \
  --output table
```

The diagnostic hierarchy should be:

```text
Stack Status
     |
     v
Stack Event
     |
     v
Logical Resource ID
     |
     v
Physical Resource ID
     |
     v
Resource Status Reason
     |
     v
Underlying AWS Service
     |
     v
Root Cause
```

This prevents a common mistake: treating `UPDATE_ROLLBACK_FAILED` or `CREATE_FAILED` as the root cause when it is actually the consequence of a resource-level failure.

## Backend Deployment Example

Consider a backend deployment containing:

```text
CloudFormation
 |
 +--> VPC
 |
 +--> ECS Cluster
 |
 +--> Application Load Balancer
 |
 +--> RDS PostgreSQL
 |
 +--> ElastiCache Redis
 |
 +--> IAM Roles
 |
 +--> CloudWatch Resources
```

A deployment might follow:

```text
CI/CD
  |
  v
CloudFormation Change Set
  |
  v
Execute Update
  |
  v
UPDATE_IN_PROGRESS
  |
  +--> IAM Role
  |
  +--> ECS Service
  |
  +--> ALB
  |
  +--> RDS
  |
  v
UPDATE_COMPLETE
```

If the ECS service fails to stabilize:

```text
ECS Service
     |
     v
UPDATE_FAILED
     |
     v
UPDATE_ROLLBACK_IN_PROGRESS
     |
     +--> ECS rollback succeeds
     |
     v
UPDATE_ROLLBACK_COMPLETE
```

The correct response is not simply to retry the CloudFormation update. First determine why ECS failed to stabilize:

- Container health check failure.
- Invalid task definition.
- Missing IAM permission.
- Invalid networking configuration.
- Security group issue.
- Image pull failure.
- Insufficient capacity.
- Application startup failure.

CloudFormation is the orchestration layer; the underlying service remains the source of the resource-specific failure.

## Monitoring Stack Operations

For interactive troubleshooting:

```bash
aws cloudformation describe-stack-events \
  --stack-name my-backend-stack \
  --region ap-south-1
```

For CI/CD, capture:

- Stack name.
- Stack ID.
- Operation type.
- Start time.
- Final status.
- Failed logical resource.
- Resource type.
- Resource status reason.
- Deployment role.
- AWS account.
- AWS Region.
- Commit or release identifier.

A deployment system should correlate:

```text
Git Commit
    |
    v
CI/CD Run
    |
    v
CloudFormation Operation
    |
    v
Stack Events
    |
    v
AWS Resource
```

This makes infrastructure failures traceable back to the application or infrastructure change that introduced them.

## Production Considerations

### Never Assume Rollback Means Zero Impact

Rollback attempts to restore the previous CloudFormation-managed state, but the rollback itself can fail.

For example:

```text
Update
  |
  v
Resource A changed
  |
  v
Resource B fails
  |
  v
Rollback Resource A
  |
  +--> Previous state no longer exists
              |
              v
      Rollback failure
```

Manual changes made outside CloudFormation are a common cause of rollback problems. :contentReference[oaicite:12]{index=12}

### Understand Replacement Semantics

Some property changes require resource replacement rather than in-place modification.

This can temporarily require both:

```text
Old Resource
     +
New Resource
```

Resource replacement can therefore affect:

- Service quotas.
- IP addresses.
- DNS behavior.
- Network dependencies.
- Availability.
- Cost.
- Stateful workloads.

CloudFormation may create the replacement before deleting the old resource, so production changes should be evaluated for temporary capacity requirements. :contentReference[oaicite:13]{index=13}

### Protect Stateful Resources

For databases and other stateful infrastructure, carefully evaluate:

- `DeletionPolicy`
- `UpdateReplacePolicy`
- Snapshot behavior
- Replacement requirements
- Backup strategy
- Recovery procedure

Never assume that CloudFormation rollback is a database disaster-recovery mechanism.

### Use Change Sets for High-Risk Changes

Before executing a significant update:

```bash
aws cloudformation create-change-set \
  --stack-name my-backend-stack \
  --change-set-name release-2026-08-13 \
  --template-body file://template.yaml \
  --change-set-type UPDATE \
  --region ap-south-1
```

Then inspect:

```bash
aws cloudformation describe-change-set \
  --stack-name my-backend-stack \
  --change-set-name release-2026-08-13 \
  --region ap-south-1
```

Pay particular attention to:

- `Add`
- `Modify`
- `Remove`
- `Replacement`

A change set makes potentially destructive infrastructure changes visible before execution.

## Recovery Principles

### `UPDATE_ROLLBACK_FAILED`

First inspect the failed rollback resources:

```bash
aws cloudformation describe-stack-events \
  --stack-name my-backend-stack \
  --region ap-south-1 \
  --query 'StackEvents[?ResourceStatus==`UPDATE_FAILED`].{LogicalId:LogicalResourceId,Reason:ResourceStatusReason}' \
  --output table
```

Then:

1. Identify the resource that prevented rollback.
2. Determine why the previous state cannot be restored.
3. Correct the underlying infrastructure problem.
4. Continue the rollback.
5. Verify `UPDATE_ROLLBACK_COMPLETE`.
6. Reconcile the template and actual infrastructure state.
7. Only then perform another update.

```bash
aws cloudformation continue-update-rollback \
  --stack-name my-backend-stack \
  --region ap-south-1
```

If resources must be skipped, use the minimum necessary set. AWS explicitly warns that skipped resources can become inconsistent with the template and cause subsequent updates to fail. :contentReference[oaicite:14]{index=14}

### `ROLLBACK_COMPLETE`

For a failed creation:

```text
ROLLBACK_COMPLETE
       |
       v
Delete Stack
       |
       v
Fix Template
       |
       v
Create Again
```

Do not attempt to update a `ROLLBACK_COMPLETE` stack as if it were a normal operational stack. The state exists after failed creation and permits deletion as the normal cleanup path. :contentReference[oaicite:15]{index=15}

### `DELETE_FAILED`

Identify the resource:

```bash
aws cloudformation describe-stack-events \
  --stack-name my-backend-stack \
  --query 'StackEvents[?ResourceStatus==`DELETE_FAILED`].{LogicalId:LogicalResourceId,Type:ResourceType,Reason:ResourceStatusReason}' \
  --output table
```

Then resolve the resource-specific constraint before retrying deletion.

## Common Mistakes

### Treating Stack Status as the Root Cause

Incorrect:

```text
UPDATE_ROLLBACK_FAILED
```

Therefore:

```text
CloudFormation is broken.
```

Correct:

```text
UPDATE_ROLLBACK_FAILED
        |
        v
Inspect events
        |
        v
Find failed resource
        |
        v
Inspect ResourceStatusReason
```

### Retrying Immediately

A retry without fixing the underlying problem usually produces another failure.

First determine whether the issue is:

- IAM.
- Quota.
- Dependency.
- Configuration.
- External mutation.
- Service availability.
- Resource replacement.
- Application health.

### Manually Modifying Resources Without Reconciliation

Manual fixes can restore service temporarily while making CloudFormation's model less accurate.

If manual intervention is unavoidable:

1. Record exactly what changed.
2. Determine whether the change should be represented in the template.
3. Reconcile infrastructure and template state.
4. Perform a controlled subsequent update.

### Skipping Rollback Resources Carelessly

`--resources-to-skip` is not a normal retry mechanism.

It can leave:

```text
CloudFormation Template
        !=
Actual Resource State
```

This increases the risk of later update failures. AWS recommends skipping only the minimum resources necessary. :contentReference[oaicite:16]{index=16}

### Ignoring Nested Stack States

A parent stack can be blocked because a child stack failed.

For nested stacks, inspect both:

```text
Parent Stack
     |
     +--> Child Stack A
     |
     +--> Child Stack B
              |
              +--> Failed Resource
```

AWS notes that nested stack failures can leave parent and child stacks in different transitional or rollback states. :contentReference[oaicite:17]{index=17}

## Interview Traps

### What is the difference between `CREATE_FAILED` and `ROLLBACK_COMPLETE`?

`CREATE_FAILED` means the creation operation failed. `ROLLBACK_COMPLETE` means CloudFormation subsequently completed the cleanup/rollback of a failed creation. A stack in `ROLLBACK_COMPLETE` is not a normally usable stack and should generally be deleted before recreating the infrastructure. :contentReference[oaicite:18]{index=18}

### What does `UPDATE_ROLLBACK_FAILED` mean?

It means the update failed and CloudFormation also failed while attempting to restore the previous state.

The recovery path is usually:

```text
Fix rollback blocker
       |
       v
continue-update-rollback
       |
       v
UPDATE_ROLLBACK_COMPLETE
```

:contentReference[oaicite:19]{index=19}

### Can an update be canceled?

Yes. An update can be canceled while the stack is in `UPDATE_IN_PROGRESS`. CloudFormation then attempts to roll back the update. :contentReference[oaicite:20]{index=20}

### Where do you find the actual resource failure?

In stack events, especially:

```text
LogicalResourceId
ResourceType
ResourceStatus
ResourceStatusReason
PhysicalResourceId
```

:contentReference[oaicite:21]{index=21}

### Why can a rollback fail even though the original resource existed?

The resource or its configuration may have changed outside CloudFormation, the required permissions may have changed, a quota may have been reached, or the underlying AWS service operation may no longer be able to restore the previous state. :contentReference[oaicite:22]{index=22}

## Operational Checklist

Before changing a production stack:

- [ ] Confirm AWS account.
- [ ] Confirm AWS Region.
- [ ] Confirm stack name and stack ID.
- [ ] Inspect current `StackStatus`.
- [ ] Inspect recent stack events.
- [ ] Identify failed logical resources.
- [ ] Read `ResourceStatusReason`.
- [ ] Identify physical resources involved.
- [ ] Check resource dependencies.
- [ ] Check IAM and execution roles.
- [ ] Check service quotas.
- [ ] Check for external/manual changes.
- [ ] Check whether replacement is required.
- [ ] Check database and stateful-resource protection.
- [ ] Check nested stack states.
- [ ] Check change set details for planned updates.
- [ ] Determine whether rollback is possible.
- [ ] Avoid destructive recovery until the failure is understood.
- [ ] Verify the final stack state after recovery.
- [ ] Reconcile template and actual infrastructure state.

## Key Takeaways

- CloudFormation stack states describe the lifecycle and operational condition of the entire stack.
- Resource events provide the detailed information needed to diagnose most failures.
- `CREATE_IN_PROGRESS` and `UPDATE_IN_PROGRESS` are transitional states; avoid starting conflicting operations while they are active.
- `CREATE_COMPLETE` and `UPDATE_COMPLETE` represent normal stable states.
- `ROLLBACK_COMPLETE` occurs after a failed creation has been successfully cleaned up and normally requires deletion before recreating the stack.
- `UPDATE_ROLLBACK_COMPLETE` means a failed update was successfully restored to its previous stable state.
- `UPDATE_ROLLBACK_FAILED` means the rollback itself failed and requires recovery before another normal update.
- `DELETE_FAILED` means the stack deletion did not fully remove its resources and requires resource-level investigation.
- Always investigate `ResourceStatusReason` rather than treating the stack status as the root cause.
- Resource replacement can temporarily increase infrastructure consumption and may expose account quotas.
- Manual changes outside CloudFormation can cause rollback and reconciliation failures.
- `continue-update-rollback` is a recovery mechanism, not a normal deployment command.
- `--resources-to-skip` can leave resources inconsistent with the template and should be used only when necessary.
- Nested stacks require investigation at both the parent and child levels.
- Change sets provide an important safety boundary for reviewing high-risk infrastructure changes before execution.
- Production CloudFormation operations should be treated as state transitions with explicit observability, recovery, and reconciliation procedures.