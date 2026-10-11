# 15- Diagnostic Commands

## Overview

Diagnosing AWS Lambda incidents requires correlating function configuration, CloudWatch metrics, logs, invocation permissions, event-source mappings, networking, and downstream dependencies. Individual commands provide only partial evidence; a reliable diagnosis combines several signals over the same incident window.

This reference organizes AWS CLI commands by operational purpose, emphasizing read-only inspection first, controlled remediation second, and verification afterward.

The examples use:

- Function: `order-processor`
- Alias: `production`
- AWS Region: `ap-south-1`
- Log group: `/aws/lambda/order-processor`

Replace these values with your actual resources. Commands that modify resources are explicitly identified. Run production changes only with appropriate authorization and change controls.

## Prepare the Diagnostic Environment

### Verify the AWS identity

**Read-only**

```bash
aws sts get-caller-identity
```

Confirm the account ID and principal before inspecting or changing production resources.

### Configure a named profile and Region

```bash
export AWS_PROFILE=production
export AWS_REGION=ap-south-1
```

These commands change the current shell environment, not AWS resources.

Verify the selected Region and identity:

```bash
aws sts get-caller-identity
aws configure list
```

Use an approved AWS CLI profile, IAM Identity Center session, or assumed role. Avoid storing long-lived production access keys in scripts or repository files.

### Define reusable variables

```bash
FUNCTION_NAME=order-processor
ALIAS_NAME=production
LOG_GROUP="/aws/lambda/${FUNCTION_NAME}"
REGION=ap-south-1
```

Use quoted variables when passing values to commands. Verify them before running any command that modifies resources.

## Inspect Function Configuration and State

### Retrieve the current configuration

**Read-only**

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION" \
  --query '{
    FunctionName:FunctionName,
    State:State,
    LastUpdateStatus:LastUpdateStatus,
    Runtime:Runtime,
    Handler:Handler,
    MemorySize:MemorySize,
    Timeout:Timeout,
    Role:Role,
    Version:Version,
    LastModified:LastModified
  }'
```

Inspect:

- `State`: whether the function is active or in another lifecycle state.
- `LastUpdateStatus`: whether the latest update succeeded.
- `Runtime` and `Handler`: whether the runtime and entry point match the deployment.
- `MemorySize` and `Timeout`: whether resource settings match workload requirements.
- `Role`: the execution role associated with the function.
- `Version`: the version represented by the response.

### Inspect the deployed package location

**Read-only**

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION" \
  --query '{
    Configuration:Configuration.{
      FunctionName:FunctionName,
      PackageType:PackageType,
      CodeSha256:CodeSha256,
      Version:Version
    },
    Code:Code.{
      RepositoryType:RepositoryType,
      ImageUri:ImageUri
    }
  }'
```

The returned response may contain a temporary download URL for ZIP-based deployment packages. Avoid logging or sharing the complete response unnecessarily.

For container-image functions, inspect the image URI and associated deployment configuration.

### List functions

**Read-only**

```bash
aws lambda list-functions \
  --region "$REGION" \
  --query 'Functions[].{
    Name:FunctionName,
    Runtime:Runtime,
    PackageType:PackageType,
    Memory:MemorySize,
    Timeout:Timeout,
    LastModified:LastModified
  }' \
  --output table
```

Use this to discover functions in the selected Region. The result is subject to AWS CLI pagination and the permissions of the current principal.

## Inspect Versions and Aliases

### List published versions

**Read-only**

```bash
aws lambda list-versions-by-function \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION" \
  --query 'Versions[].{
    Version:Version,
    Runtime:Runtime,
    CodeSha256:CodeSha256,
    LastModified:LastModified
  }' \
  --output table
```

Compare the version used during the incident with a previously healthy version.

### Inspect a production alias

**Read-only**

```bash
aws lambda get-alias \
  --function-name "$FUNCTION_NAME" \
  --name "$ALIAS_NAME" \
  --region "$REGION"
```

Check the alias's primary version and any additional version weights used for traffic shifting.

An alias can route traffic to a published version, but it does not automatically roll back external database changes, queue contents, or side effects.

## Inspect Lambda Metrics

CloudWatch metrics help determine whether an incident is caused by invocation failures, latency, concurrency pressure, or unexpected traffic.

Common Lambda metrics include:

| Metric | Diagnostic purpose |
|---|---|
| `Invocations` | Measures function invocation attempts counted by Lambda |
| `Errors` | Identifies invocations that resulted in function errors |
| `Throttles` | Identifies invocations rejected because of throttling |
| `Duration` | Measures execution duration |
| `ConcurrentExecutions` | Shows concurrent execution demand |
| `UnreservedConcurrentExecutions` | Shows account-level unreserved concurrency usage |
| `IteratorAge` | Indicates event-processing delay for supported stream-based integrations |
| `AsyncEventAge` | Helps identify delayed asynchronous invocation processing |
| `AsyncEventsDropped` | Indicates asynchronous events discarded under applicable conditions |

Metric availability and dimensions vary by integration. Some metrics, such as `IteratorAge`, apply only to particular event sources.

### Query errors over an incident window

**Read-only**

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
  --start-time 2026-10-11T12:00:00Z \
  --end-time 2026-10-11T13:00:00Z \
  --period 60 \
  --statistics Sum \
  --region "$REGION"
```

Replace the example UTC timestamps with the incident window.

### Inspect invocations and throttles

**Read-only**

```bash
for METRIC in Invocations Errors Throttles; do
  echo "=== ${METRIC} ==="

  aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name "$METRIC" \
    --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
    --start-time 2026-10-11T12:00:00Z \
    --end-time 2026-10-11T13:00:00Z \
    --period 60 \
    --statistics Sum \
    --region "$REGION"
done
```

This shell loop issues three read-only metric queries.

### Inspect duration percentiles

**Read-only**

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
  --start-time 2026-10-11T12:00:00Z \
  --end-time 2026-10-11T13:00:00Z \
  --period 60 \
  --extended-statistics p50 p90 p99 \
  --region "$REGION"
```

Use percentiles to identify tail-latency regressions that an average can hide.

`get-metric-statistics` supports a limited number of extended statistics per request. For more flexible multi-metric analysis, use CloudWatch metric math or `get-metric-data`.

### Interpret correlated metrics

| Observation | Likely investigation |
|---|---|
| Errors increase while invocations remain stable | Runtime, application, permission, or dependency failures |
| Throttles increase while concurrency approaches a limit | Concurrency configuration or account capacity |
| Duration rises before errors increase | Slow dependencies, resource pressure, or retry loops |
| Invocations spike unexpectedly | Traffic changes, recursive invocation, or event replay |
| Lambda metrics look healthy but work is delayed | Event-source backlog, routing, or downstream processing |
| Invocation count is unexpectedly low | Trigger configuration, upstream availability, or permissions |

Metrics narrow the search space; logs and dependency telemetry establish the root cause.

## Retrieve and Filter CloudWatch Logs

### Tail recent logs

**Read-only**

```bash
aws logs tail "$LOG_GROUP" \
  --since 30m \
  --region "$REGION"
```

This command displays recent log events. It requires appropriate CloudWatch Logs read permissions.

### Filter runtime exceptions

**Read-only**

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --start-time 1791720000000 \
  --end-time 1791723600000 \
  --filter-pattern '"Traceback" || "Runtime.ImportModuleError" || "Task timed out"' \
  --region "$REGION"
```

The timestamps are Unix epoch milliseconds. Replace them with the actual incident window.

CloudWatch Logs filter patterns are not full regular expressions. Confirm that the pattern syntax matches the intended search.

### Use Logs Insights for grouped error analysis

**Read-only query execution**

```bash
aws logs start-query \
  --log-group-name "$LOG_GROUP" \
  --start-time 1791720000 \
  --end-time 1791723600 \
  --query-string 'fields @timestamp, @requestId, @message
    | filter @message like /ERROR|Exception|Task timed out/
    | sort @timestamp desc
    | limit 100' \
  --region "$REGION"
```

The query returns a query ID. Retrieve its results:

```bash
aws logs get-query-results \
  --query-id "$QUERY_ID" \
  --region "$REGION"
```

Replace `QUERY_ID` with the returned identifier. The start and end values for Logs Insights are Unix epoch seconds, unlike the millisecond timestamps used by `filter-log-events`.

### Find slow invocations

A common Lambda platform log format includes `REPORT` records containing duration and memory information.

```text
REPORT RequestId: ... Duration: 4800.00 ms
Billed Duration: 4900 ms Memory Size: 512 MB
Max Memory Used: 490 MB
```

Query relevant records:

```sql
fields @timestamp, @requestId, @message
| filter @message like /REPORT/
| parse @message "Duration: * ms" as duration_ms
| parse @message "Max Memory Used: * MB" as max_memory_mb
| filter duration_ms > 3000
| sort duration_ms desc
| limit 100
```

Use the query in CloudWatch Logs Insights. Adjust the duration threshold to match the workload's expected latency.

Log formats can vary. Verify parsed fields before using them for incident decisions.

## Inspect Concurrency and Throttling

### Inspect reserved concurrency

**Read-only**

```bash
aws lambda get-function-concurrency \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION"
```

If reserved concurrency has not been configured, the command may return a resource-not-found response for that configuration.

### Inspect account concurrency limits

**Read-only**

```bash
aws lambda get-account-settings \
  --region "$REGION" \
  --query 'AccountLimit.{
    ConcurrentExecutions:ConcurrentExecutions,
    UnreservedConcurrentExecutions:UnreservedConcurrentExecutions,
    AccountLimit:ConcurrentExecutions
  }'
```

Use the response to understand account-level capacity. Function-level reservations, provisioned concurrency, and service quotas must be considered together when diagnosing capacity pressure.

### Inspect provisioned concurrency

**Read-only**

```bash
aws lambda get-provisioned-concurrency-config \
  --function-name "$FUNCTION_NAME" \
  --qualifier "$ALIAS_NAME" \
  --region "$REGION"
```

This command applies when provisioned concurrency is configured for the specified version or alias qualifier.

Inspect the returned status and allocated capacity before concluding that the intended capacity is ready.

## Inspect Event Source Mappings

Event source mappings poll or consume supported event sources and invoke Lambda with batches of records. Their state, batching configuration, and failure behavior can be independent of the function's basic configuration.

### List mappings

**Read-only**

```bash
aws lambda list-event-source-mappings \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION" \
  --query 'EventSourceMappings[].{
    UUID:UUID,
    State:State,
    StateTransitionReason:StateTransitionReason,
    EventSourceArn:EventSourceArn,
    BatchSize:BatchSize,
    LastProcessingResult:LastProcessingResult,
    FunctionArn:FunctionArn
  }' \
  --output table
```

### Inspect one mapping

**Read-only**

```bash
aws lambda get-event-source-mapping \
  --uuid "$MAPPING_UUID" \
  --region "$REGION"
```

Inspect:

- `State` and `StateTransitionReason`.
- `LastProcessingResult`.
- `BatchSize` and batching window.
- Event-source ARN.
- Function association.
- Failure destination and retry-related settings where applicable.

### Diagnose an inactive mapping

Use this sequence:

1. Confirm that the event source exists and is accessible.
2. Check the mapping state and transition reason.
3. Inspect permissions and event-source configuration.
4. Review Lambda errors and source-specific metrics.
5. Correct the underlying issue.
6. Re-enable processing only when it is safe to resume.

**State-changing command — use only after validating the cause and recovery plan:**

```bash
aws lambda update-event-source-mapping \
  --uuid "$MAPPING_UUID" \
  --enabled \
  --region "$REGION"
```

Verify the mapping state afterward:

```bash
aws lambda get-event-source-mapping \
  --uuid "$MAPPING_UUID" \
  --region "$REGION" \
  --query '{UUID:UUID,State:State,LastProcessingResult:LastProcessingResult}'
```

Re-enabling a mapping can cause accumulated work to resume immediately. Confirm downstream capacity and replay safety before doing so.

## Diagnose SQS Backlogs and Failed Batches

SQS-based Lambda consumers may experience growing queue depth because of throttling, handler errors, downstream overload, visibility-timeout problems, or poison messages.

### Inspect queue attributes

**Read-only**

```bash
aws sqs get-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attribute-names \
    ApproximateNumberOfMessages \
    ApproximateNumberOfMessagesNotVisible \
    ApproximateNumberOfMessagesDelayed \
    VisibilityTimeout \
    RedrivePolicy \
  --region "$REGION"
```

Interpret the attributes:

- `ApproximateNumberOfMessages`: messages visible for processing.
- `ApproximateNumberOfMessagesNotVisible`: messages currently being processed or hidden by the visibility timeout.
- `ApproximateNumberOfMessagesDelayed`: messages not yet available for delivery.
- `VisibilityTimeout`: how long a received message remains hidden.
- `RedrivePolicy`: configured dead-letter queue behavior.

Queue counts are approximate and can lag. Correlate them with queue-age metrics and Lambda processing telemetry.

### Inspect SQS metrics

Useful CloudWatch metrics include:

- `ApproximateNumberOfMessagesVisible`
- `ApproximateNumberOfMessagesNotVisible`
- `ApproximateAgeOfOldestMessage`
- `NumberOfMessagesReceived`
- `NumberOfMessagesDeleted`

The namespace is `AWS/SQS`. Confirm the queue name and metric dimensions when querying them.

### Recovery guidance

- Fix the handler or downstream failure before increasing consumer capacity.
- Verify that the visibility timeout is appropriate for the maximum processing duration and batching behavior.
- Use partial batch responses when supported and configured to avoid retrying successful records unnecessarily.
- Isolate poison messages using a suitable redrive policy and dead-letter queue.
- Inspect the dead-letter queue before redriving messages.
- Reconcile business state before replaying messages that may have been processed previously.

Do not purge a production queue as a routine troubleshooting step. Purging removes messages and can permanently destroy pending business work.

## Inspect IAM and Invocation Permissions

Lambda permissions involve multiple independent policy layers.

### Inspect the execution role

**Read-only**

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION" \
  --query 'Role'
```

The result is the execution role ARN. Inspect its trust policy and attached permissions using the relevant IAM commands and approved access.

### Inspect the function resource policy

**Read-only**

```bash
aws lambda get-policy \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION"
```

This policy controls which principals or AWS services can invoke the function under the applicable conditions.

If the function has no resource-based policy, the command can return a resource-not-found error.

### Inspect attached role policies

**Read-only**

```bash
aws iam list-attached-role-policies \
  --role-name "$ROLE_NAME"
```

For inline policies:

```bash
aws iam list-role-policies \
  --role-name "$ROLE_NAME"
```

Replace `ROLE_NAME` with the role name extracted from the execution role ARN.

These commands inspect policy attachments and names, not the complete effective authorization decision. Also examine inline policy documents, resource policies, permissions boundaries, service control policies, and applicable resource policies.

### Troubleshooting sequence

1. Capture the exact denied action and resource.
2. Identify the principal making the request.
3. Determine whether the failure concerns invocation or execution-role access.
4. Inspect relevant identity and resource policies.
5. Verify the resource ARN, account, Region, and conditions.
6. Apply the smallest authorized policy correction.
7. Retest using the intended principal.

Avoid broad permission grants as a default incident workaround.

## Inspect VPC Configuration

### Retrieve VPC settings

**Read-only**

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION" \
  --query 'VpcConfig'
```

Inspect the configured subnet IDs, security-group IDs, and VPC identifier.

### Investigate connectivity

Use the relevant EC2 commands to inspect network resources:

```bash
aws ec2 describe-subnets \
  --subnet-ids subnet-0123456789abcdef0 \
  --region "$REGION"
```

```bash
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0 \
  --region "$REGION"
```

```bash
aws ec2 describe-route-tables \
  --filters Name=association.subnet-id,Values=subnet-0123456789abcdef0 \
  --region "$REGION"
```

These commands are read-only. Replace the example subnet and security-group IDs.

A route-table query filtered by subnet association may not return a result when the subnet uses the VPC's main route table without an explicit association. If necessary, inspect the VPC's main route table separately.

### Check connectivity systematically

- Verify that the database or service endpoint resolves correctly.
- Confirm inbound rules permit traffic from the Lambda security group.
- Check outbound rules and subnet routing.
- Verify network ACLs and return traffic paths.
- Confirm NAT or VPC endpoint configuration where required.
- Inspect VPC Flow Logs when available.
- Check database connection limits and application timeouts.

Lambda VPC attachment does not automatically provide internet access. Private subnet routing, NAT, and endpoint configuration must match the workload's connectivity requirements.

## Inspect API Gateway Integration Failures

When a Lambda-backed API fails, determine whether the request reaches Lambda.

### Inspect API Gateway metrics and logs

For the relevant API and stage, inspect:

- Request count.
- 4xx and 5xx errors.
- Integration latency.
- Request latency.
- Access logs and execution logs, where enabled.

API Gateway logging and metric dimensions depend on the API type and stage configuration.

### Isolate the failure

1. Reproduce the request with a known test payload.
2. Check the API response status and body.
3. Determine whether Lambda was invoked.
4. Compare API Gateway and Lambda error timestamps.
5. Inspect the integration URI and invocation permissions.
6. Test the function independently where safe.
7. Verify the external API after remediation.

A successful direct Lambda invocation does not prove that API Gateway routing, authentication, request transformation, or response mapping is correct.

Function URLs use a different integration and authorization model. Diagnose them using their own configuration and resource policy rather than assuming API Gateway semantics.

## Inspect Asynchronous Invocation Failures

Lambda asynchronous invocation queues accepted events for later processing. Retries and failure handling differ from synchronous invocation and event-source mappings.

### Inspect asynchronous invocation configuration

**Read-only**

```bash
aws lambda get-function-event-invoke-config \
  --function-name "$FUNCTION_NAME" \
  --qualifier "$ALIAS_NAME" \
  --region "$REGION"
```

Inspect maximum event age, retry attempts, and configured destinations.

The qualifier must identify the appropriate function version or alias when inspecting qualified configuration.

### Diagnose delayed or discarded events

Inspect applicable metrics such as:

- `AsyncEventAge`
- `AsyncEventsDropped`
- `Errors`
- `Throttles`

Check configured destinations or dead-letter queues and their delivery permissions.

### Recovery considerations

- Correct the underlying handler or dependency failure.
- Verify the configured retry and event-age policy.
- Inspect destination-delivery failures.
- Confirm whether failed events can be safely replayed.
- Ensure idempotency before redriving work.

Do not assume all asynchronous events are retried indefinitely. Retry limits, event age, destination configuration, and invocation failures affect the final outcome.

## Inspect Function Logs, Tracing, and Telemetry

### Check whether a log group exists

**Read-only**

```bash
aws logs describe-log-groups \
  --log-group-name-prefix "$LOG_GROUP" \
  --region "$REGION"
```

If the log group is missing, investigate whether the function has been invoked, whether the execution role can create log streams and write events, and whether logging is configured as expected.

### Inspect log streams

**Read-only**

```bash
aws logs describe-log-streams \
  --log-group-name "$LOG_GROUP" \
  --order-by LastEventTime \
  --descending \
  --limit 10 \
  --region "$REGION"
```

Recent activity can help establish whether the function has emitted logs, but log-stream timestamps are not a substitute for invocation metrics.

### Inspect tracing configuration

**Read-only**

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION" \
  --query 'TracingConfig'
```

For tracing investigations, correlate the function's tracing configuration with the tracing service, sampling configuration, upstream request, and downstream integrations.

Missing traces do not necessarily indicate that no invocation occurred. Sampling, instrumentation, propagation, or export failures may explain the gap.

## Inspect Deployment and Update Failures

### Check update status

**Read-only**

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION" \
  --query '{
    State:State,
    LastUpdateStatus:LastUpdateStatus,
    LastUpdateStatusReason:LastUpdateStatusReason,
    LastUpdateStatusReasonCode:LastUpdateStatusReasonCode,
    LastModified:LastModified
  }'
```

Use the returned status and reason fields to investigate failed updates.

### Compare code versions

**Read-only**

```bash
aws lambda list-versions-by-function \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION" \
  --query 'Versions[].{
    Version:Version,
    CodeSha256:CodeSha256,
    LastModified:LastModified
  }'
```

Compare known-good and affected versions, then review deployment artifacts, dependencies, environment configuration, and infrastructure changes.

### Roll back an alias

**State-changing — production impact possible**

If a previous version is known to be healthy and rollback is approved:

```bash
aws lambda update-alias \
  --function-name "$FUNCTION_NAME" \
  --name "$ALIAS_NAME" \
  --function-version "$KNOWN_GOOD_VERSION" \
  --region "$REGION"
```

This updates the alias's primary version. It does not automatically reverse all additional routing configuration, infrastructure changes, database migrations, or external side effects. Review the alias's current routing configuration before executing a rollback.

Verify afterward:

```bash
aws lambda get-alias \
  --function-name "$FUNCTION_NAME" \
  --name "$ALIAS_NAME" \
  --region "$REGION"
```

Follow the rollback with smoke tests, metric checks, and business-state validation.

## Inspect Service Quotas and Capacity

Lambda incidents can be caused by service quotas or capacity constraints that are independent of the function's own timeout and memory configuration.

Investigate:

- Account concurrency quotas.
- Function reserved concurrency.
- Provisioned concurrency allocation and readiness.
- Event-source-specific throughput and scaling constraints.
- Downstream connection and request limits.
- Deployment package and payload constraints relevant to the integration.

For quota investigations, use the Service Quotas console or CLI commands appropriate to the quota being checked. Do not assume every Lambda quota is adjustable or has the same scope.

Increasing a quota or concurrency allocation is not a substitute for identifying downstream bottlenecks.

## Safe Operational Command Reference

| Operation | Command | Effect |
|---|---|---|
| Verify identity | `aws sts get-caller-identity` | Read-only |
| Inspect configuration | `aws lambda get-function-configuration` | Read-only |
| Inspect alias | `aws lambda get-alias` | Read-only |
| Query metrics | `aws cloudwatch get-metric-statistics` | Read-only |
| Tail logs | `aws logs tail` | Read-only |
| Inspect event-source mapping | `aws lambda get-event-source-mapping` | Read-only |
| Enable an event-source mapping | `aws lambda update-event-source-mapping --enabled` | Changes processing behavior |
| Update alias version | `aws lambda update-alias` | Changes traffic routing |
| Update function configuration | `aws lambda update-function-configuration` | Changes runtime configuration |
| Change reserved concurrency | `aws lambda put-function-concurrency` | Changes capacity allocation |
| Delete a function | `aws lambda delete-function` | Destructive |

Before running any state-changing command:

1. Confirm account, Region, and resource identity.
2. Capture the current configuration.
3. Assess the impact on traffic, retries, queues, and downstream dependencies.
4. Obtain required incident or change authorization.
5. Apply the smallest viable change.
6. Verify the new state and monitor the workload.

## Common Diagnostic Errors

| Mistake | Why it causes problems | Better approach |
|---|---|---|
| Using the wrong AWS profile or Region | Produces misleading evidence or targets the wrong resource | Verify identity and Region before investigation |
| Mixing epoch seconds and milliseconds | Queries the wrong time window or returns no data | Use seconds for Logs Insights queries and milliseconds for `filter-log-events` |
| Inspecting only `Errors` | Hides throttling, latency, trigger, and dependency failures | Correlate multiple metrics and logs |
| Assuming a missing log group proves no invocation occurred | Logging permissions or configuration may be broken | Check metrics, configuration, and upstream behavior |
| Re-enabling a mapping without checking the backlog | Can overwhelm dependencies or replay unsafe work | Verify capacity and idempotency first |
| Increasing concurrency without assessing dependencies | Can worsen database or API overload | Establish downstream capacity before scaling |
| Rolling back code without reviewing data changes | The previous version may be incompatible with the current schema | Assess migration and side-effect compatibility |
| Sharing full command output indiscriminately | Can expose sensitive configuration or temporary URLs | Filter output and redact sensitive fields |
| Treating approximate queue metrics as exact counts | Can lead to incorrect conclusions about backlog behavior | Correlate queue metrics, age, and processing logs |
| Making several changes before verification | Makes the root cause and effective mitigation unclear | Change one relevant variable at a time where practical |

## Key Takeaways

- Establish the AWS identity, Region, affected function, and incident time window before running diagnostics.
- Correlate Lambda metrics, CloudWatch logs, event-source state, deployment history, and downstream telemetry to isolate the failure domain.
- Distinguish read-only diagnostic commands from state-changing commands, especially when modifying aliases, concurrency, or event-source mappings.
- Verify recovery through both technical signals and business outcomes; successful invocations alone do not prove that events were processed correctly.
- Preserve data, use targeted reversible mitigations, and validate the final configuration after every production change.