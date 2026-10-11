# 02- Common Lambda Errors and Timeouts

## Overview

AWS Lambda failures can originate from application code, runtime initialization, deployment artifacts, execution limits, invocation integrations, or downstream dependencies. Correct diagnosis requires distinguishing between a function execution error, an invocation rejection, a timeout, and a business operation that completed incorrectly.

This document covers common Lambda errors and timeout scenarios, with diagnostic commands, root-cause verification, corrective actions, and production prevention strategies.

The standard diagnostic sequence is:

**Symptom → Possible causes → Isolation strategy → Diagnostic commands → Root cause verification → Corrective action → Prevention**

## Establish a Diagnostic Baseline

Before changing configuration, establish which function version is failing and identify the affected time window.

### Set diagnostic variables

```bash
export AWS_PROFILE=dev
export AWS_REGION=ap-south-1
export FUNCTION_NAME=orders-processor
export LOG_GROUP="/aws/lambda/$FUNCTION_NAME"
```

Replace the example values with the actual environment.

### Verify the account and function state

**Operation: Read-only.**

```bash
aws sts get-caller-identity \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION"
```

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION" \
  --query '{
    Name:FunctionName,
    Version:Version,
    State:State,
    LastUpdateStatus:LastUpdateStatus,
    Runtime:Runtime,
    Handler:Handler,
    Memory:MemorySize,
    Timeout:Timeout,
    LastModified:LastModified
  }' \
  --output json
```

For production functions invoked through an alias, inspect the alias separately:

```bash
aws lambda get-alias \
  --function-name "$FUNCTION_NAME" \
  --name prod \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION"
```

An alias may point to a published version different from the function's current `$LATEST` version. Diagnose the version actually receiving traffic.

### Retrieve recent logs

**Operation: Read-only.**

```bash
aws logs tail "$LOG_GROUP" \
  --since 30m \
  --format short \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION"
```

Look for Python tracebacks, `INIT_REPORT`, `START`, `END`, and `REPORT` records, timeout messages, and downstream error responses.

Not every failure produces an application traceback. Invocation rejection, initialization failures, and integration errors may require CloudWatch metrics, service logs, or configuration inspection.

## Handler and Runtime Errors

### `Runtime.ImportModuleError`

**Typical symptom**

```text
Runtime.ImportModuleError: Unable to import module 'app'
```

**Possible causes**

- The configured handler references a module that does not exist in the deployment package.
- The Python file is nested in an unexpected directory.
- A required dependency was not packaged.
- A native dependency was built for an incompatible operating system, architecture, or Python version.
- The deployed artifact differs from the locally tested artifact.

**Isolation strategy**

Inspect the handler configuration:

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION" \
  --query '{Handler:Handler,Runtime:Runtime,Architectures:Architectures}' \
  --output json
```

Inspect the ZIP structure locally:

```bash
unzip -l function.zip
```

For a handler configured as `app.handler`, the deployment package should contain an importable `app.py` module at the expected package root, with a callable named `handler`.

**Root cause verification**

- Confirm that the expected module exists in the ZIP.
- Verify that dependencies are installed into the deployment package or supplied through an attached layer.
- Test the same artifact and runtime assumptions used by the deployment pipeline.

**Corrective action**

Build the package with the correct directory layout and runtime-compatible dependencies.

For example:

```text
function.zip
    app.py
    orders/
        __init__.py
        service.py
    dependencies...
```

For ZIP-based Python deployments, dependencies can be installed into a staging directory:

```bash
python -m pip install \
  --requirement requirements.txt \
  --target package/
```

Copy the handler and application modules into `package/`, then create the ZIP from inside that directory.

**Prevention**

- Build deployment artifacts in a compatible environment.
- Pin dependencies and validate the handler configuration in CI.
- Test the packaged artifact rather than only the source tree.
- Include architecture and native dependency compatibility checks.

### `Runtime.HandlerNotFound`

**Typical symptom**

Lambda cannot locate the configured handler function.

**Possible causes**

- The handler name is incorrect.
- The module imports successfully, but the expected callable is missing.
- The handler configuration does not match the deployed code.

**Corrective action**

If the file is `app.py` and the callable is `lambda_handler`, configure:

```text
app.lambda_handler
```

Example:

```python
def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": "processed",
    }
```

Verify the deployed handler configuration after updating it. A successful deployment does not guarantee that the configured handler matches the artifact.

### `Runtime.ExitError` or initialization failure

**Possible causes**

- Application code fails during module import.
- A required environment variable is missing.
- Initialization performs an unavailable network call.
- A native library fails to load.
- An extension or runtime component fails during startup.

**Diagnostic approach**

1. Find the first initialization error, not merely the final runtime error.
2. Inspect `INIT_REPORT` or other initialization-related log records when available.
3. Check environment variable names, dependency versions, and package compatibility.
4. Identify network calls or resource creation performed during module import.

Move nonessential initialization out of the import path when it unnecessarily increases startup time. Required configuration should fail clearly rather than allowing the handler to continue in an invalid state.

## Python Exceptions and Unhandled Errors

### Common application exceptions

| Error | Typical cause | Recommended action |
|---|---|---|
| `KeyError` | Required event field is missing | Validate the event schema before accessing fields |
| `TypeError` | Unexpected input type or invalid function arguments | Validate types and enforce clear contracts |
| `ValueError` | Invalid input or conversion | Reject invalid data explicitly |
| `ConnectionError` | Network or downstream connectivity issue | Inspect DNS, routing, TLS, and dependency availability |
| `TimeoutError` | A client operation exceeded its configured timeout | Review the dependency timeout and overall Lambda deadline |
| Database exceptions | Authentication, SQL errors, exhausted connections, or transaction failures | Inspect database health, credentials, pool usage, and transaction handling |

### Example: validate an event before processing

```python
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    if not isinstance(event, dict):
        raise ValueError("Expected an object event")

    order_id = event.get("order_id")

    if not isinstance(order_id, str) or not order_id.strip():
        logger.warning(
            "Invalid order event",
            extra={"request_id": context.aws_request_id},
        )
        raise ValueError("order_id must be a non-empty string")

    logger.info(
        "Processing order",
        extra={
            "request_id": context.aws_request_id,
            "order_id": order_id,
        },
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"order_id": order_id, "status": "accepted"}),
    }
```

The example deliberately raises an exception for invalid input. Whether that is appropriate depends on the invocation model:

- For a synchronous API, translate invalid input into the correct client response.
- For an asynchronous invocation, an exception can trigger retries.
- For SQS or stream processing, a failed invocation can cause message retry or checkpoint consequences.

Do not assume that every invalid event should be retried. Permanent validation failures should be handled according to the source's failure semantics, often by routing them to a controlled failure path.

## Lambda Timeouts

### What a timeout means

A Lambda timeout occurs when an invocation exceeds the configured maximum execution duration. Lambda terminates the execution when the limit is reached.

Common causes include:

- Slow or unbounded HTTP requests.
- Database connection establishment delays.
- Lock contention or slow SQL queries.
- Large payload processing.
- Inefficient algorithms or repeated serialization.
- Waiting on an external service that never responds.
- Excessive initialization work.
- Insufficient memory for CPU-intensive work.

Increasing the Lambda timeout can help a legitimate workload finish, but it does not fix a dependency that hangs indefinitely or an algorithm whose cost grows uncontrollably.

### Recognize timeout evidence

A common log message is:

```text
Task timed out after 30.00 seconds
```

The `REPORT` record may include duration and memory information, but application logs can be incomplete because the runtime is terminated before cleanup or final logging occurs.

### Inspect the configured timeout

**Operation: Read-only.**

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION" \
  --query '{Timeout:Timeout,Memory:MemorySize}' \
  --output json
```

### Change the timeout

**Operation: Mutating.**

```bash
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --timeout 60 \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION"
```

This example changes the timeout to 60 seconds. Choose a value based on measured execution requirements and the invocation source's own time constraints.

Verify the update:

```bash
aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME" \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION"

aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION" \
  --query '{Timeout:Timeout,LastUpdateStatus:LastUpdateStatus}' \
  --output json
```

### Set downstream timeouts explicitly

A downstream operation should usually have a shorter timeout than the remaining Lambda execution budget.

For example, using Python's `requests` library:

```python
import requests


def fetch_order_service(order_id: str) -> dict:
    response = requests.get(
        f"https://orders.internal.example/orders/{order_id}",
        timeout=(2.0, 5.0),
    )
    response.raise_for_status()
    return response.json()
```

The tuple sets connection and read timeouts. The read timeout is generally the maximum wait between received data, not necessarily a strict wall-clock deadline for the complete request.

A production implementation should also account for the Lambda's remaining time, retry budgets, and downstream operation semantics. Do not begin a new operation when insufficient time remains to complete it safely.

### Use the remaining execution time

The Lambda context exposes the remaining execution time in milliseconds.

```python
import json


def handler(event, context):
    remaining_seconds = context.get_remaining_time_in_millis() / 1000

    if remaining_seconds < 3:
        raise TimeoutError("Insufficient time remaining to start processing")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "remaining_seconds": remaining_seconds,
        }),
    }
```

This example demonstrates deadline awareness. In real applications, use the remaining budget to configure downstream deadlines and decide whether to continue, defer, or fail safely.

### When to increase the timeout

Increase the timeout when measurements show that the workload legitimately requires more time and the integration permits it.

Examples include:

- Processing a bounded batch of records.
- Calling a slow but necessary external service with a documented latency profile.
- Generating a report with a known upper execution bound.

Do not use a longer timeout as a substitute for:

- Fixing an unbounded loop.
- Adding a missing database index.
- Configuring HTTP client timeouts.
- Eliminating retry amplification.
- Moving long-running work to an asynchronous workflow.

For long-running or multi-step jobs, consider SQS-backed workers, Step Functions, AWS Batch, or ECS/Fargate according to the workload and execution requirements.

## Memory Exhaustion and High Memory Utilization

### Typical symptoms

- `Runtime.OutOfMemory` or runtime termination associated with memory exhaustion.
- Unexpected process exits while handling large payloads.
- High memory usage in `REPORT` records.
- Duration increases as payload sizes grow.

Lambda's memory setting also influences CPU allocation. Increasing memory can improve CPU-bound workloads and reduce execution duration, but it increases the configured resource allocation cost.

### Inspect memory and duration

Review `REPORT` log records for fields such as:

```text
REPORT RequestId: ... Duration: ... ms
Max Memory Used: ... MB
```

The precise fields depend on runtime and reporting format.

### Increase memory

**Operation: Mutating.**

```bash
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --memory-size 1024 \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION"
```

Benchmark representative workloads before and after the change.

### Common memory-related mistakes

- Loading an entire S3 object into memory when streaming is possible.
- Creating large intermediate lists or data frames.
- Decoding and re-encoding large payloads repeatedly.
- Keeping unbounded caches in reusable execution environments.
- Processing oversized batches without considering per-record memory consumption.

For file processing, stream data where practical and bound batch sizes. If the workload requires memory or runtime beyond Lambda's supported limits, select a compute service designed for those requirements.

## Cold Starts and Initialization Latency

### Symptoms

- High latency on the first request after an idle period or deployment.
- Elevated initialization duration in logs or telemetry.
- Significant differences between initialization-heavy and warm invocations.

Cold starts can include environment preparation, runtime startup, dependency loading, and application initialization. The exact behavior depends on runtime, package size, configuration, and features such as provisioned concurrency or SnapStart where supported.

### Diagnostic approach

1. Compare initialization duration with normal execution duration.
2. Check package size and dependency count.
3. Inspect expensive work performed during module import.
4. Review VPC and downstream connection setup.
5. Determine whether latency requirements justify a specialized cold-start mitigation.

### Practical improvements

- Reduce unnecessary dependencies.
- Keep initialization deterministic and lightweight.
- Reuse safe clients and connection pools across invocations.
- Avoid retrieving secrets or making remote calls during import unless required.
- Benchmark provisioned concurrency or other supported startup features when latency objectives justify their cost.

Do not treat every slow invocation as a cold start. A warm invocation can also be slow because of a database, network, CPU, or application bottleneck.

## Throttling and Concurrency Errors

### Common symptom

```text
TooManyRequestsException
```

This can occur when function-level concurrency settings or account-level capacity prevent additional invocations from being accepted.

For queue-based event source mappings, throttling can also affect how quickly messages are processed and may lead to repeated delivery attempts.

### Inspect reserved concurrency

**Operation: Read-only.**

```bash
aws lambda get-function-concurrency \
  --function-name "$FUNCTION_NAME" \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION"
```

### Inspect account concurrency

**Operation: Read-only.**

```bash
aws lambda get-account-settings \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION" \
  --output json
```

### Corrective action

- Determine whether the function has reserved concurrency configured.
- Check account concurrency and applicable service quotas.
- Estimate demand using request rate and average execution duration.
- Verify that databases and downstream services can support increased parallelism.
- Apply backpressure or reduce intake if dependencies are already overloaded.

A rough concurrency estimate is:

\[
\text{Concurrency} \approx \text{Request rate} \times \text{Average duration in seconds}
\]

For example, 100 requests per second with an average duration of 0.4 seconds requires approximately 40 concurrent executions under steady-state assumptions. Bursts, retries, variance in execution time, and downstream bottlenecks can change the actual requirement.

Increasing concurrency without validating downstream capacity can turn a Lambda throttling problem into a database outage.

## IAM Authorization Errors

### Typical symptoms

```text
AccessDeniedException
```

```text
not authorized to perform: dynamodb:PutItem
```

### Diagnostic process

Identify which principal is performing the rejected action.

- Lambda execution role: authorizes application code to call AWS services.
- Function resource policy: authorizes principals or services to invoke the function.
- Deployment role: authorizes deployment and configuration changes.
- Caller identity: authorizes direct invocation when applicable.

Inspect the execution role:

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION" \
  --query Role \
  --output text
```

Inspect the function resource policy:

```bash
aws lambda get-policy \
  --function-name "$FUNCTION_NAME" \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION"
```

### Corrective action

Grant only the missing permissions to the correct principal. Verify resource ARNs, Region, account, and relevant conditions.

Do not resolve authorization errors by attaching broad administrator permissions. Also inspect resource policies, permission boundaries, session policies, and organizational service control policies when identity-based permissions appear correct.

## API Gateway and Function URL Errors

### Common symptoms

| Symptom | Possible cause |
|---|---|
| HTTP 502 | Function exception, malformed proxy response, or integration failure |
| HTTP 403 | Authentication, authorization, resource policy, or API configuration |
| HTTP 504 or gateway timeout | Integration timeout or slow function/dependency |
| Function URL returns 403 | Authentication mode or resource policy does not authorize the request |
| API returns an incorrect status code | Application response format or error mapping is incorrect |

### Verify the handler response

For a Lambda proxy integration, ensure that the response follows the integration's expected schema.

```python
import json


def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {
            "content-type": "application/json",
        },
        "body": json.dumps({"status": "ok"}),
        "isBase64Encoded": False,
    }
```

Integration formats differ by service and configuration. Verify the contract used by API Gateway, an Application Load Balancer, or a function URL instead of assuming that all integrations behave identically.

### Diagnostic sequence

1. Inspect the API or function URL configuration.
2. Check the caller-visible status code and response body.
3. Inspect API Gateway execution or access logs when enabled.
4. Correlate the request with Lambda logs.
5. Verify invocation permissions and authentication settings.
6. Compare integration timeout limits with Lambda and downstream deadlines.

A gateway timeout does not necessarily prove that Lambda stopped processing. The caller may time out while downstream work continues, creating uncertainty about whether the operation completed. Design retries around idempotency.

## VPC Connectivity and Database Failures

### Common symptoms

- Connection timeouts.
- DNS resolution failures.
- TLS handshake errors.
- Database authentication failures.
- Exhausted database connection limits.
- Lambda duration increases after VPC configuration changes.

### Isolation strategy

Check:

- VPC, subnet, and security group configuration.
- Database security group ingress rules.
- Route tables, NAT gateways, and VPC endpoints.
- DNS settings and hostname resolution.
- Database availability and connection limits.
- Connection pooling and reuse behavior.

Inspect VPC configuration:

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION" \
  --query 'VpcConfig' \
  --output json
```

### Corrective action

Correct the specific networking or database configuration issue rather than opening broad network access.

For relational databases, consider connection reuse, bounded connection pools, RDS Proxy where appropriate, and concurrency limits aligned with database capacity.

Lambda can scale faster than a traditional database can accept new connections. A function that creates a new database connection for every request may exhaust the connection limit during a traffic spike.

## Event Source and Retry Failures

### Amazon SQS

**Symptoms**

- Messages repeatedly appear in the queue.
- Queue age increases.
- The same business operation is processed multiple times.
- Messages move to a dead-letter queue.

**Check**

- Queue depth and age of oldest message.
- Visibility timeout relative to processing duration.
- Event source mapping state and batch size.
- Redrive policy and receive count.
- Whether partial batch responses are configured and implemented correctly.

An SQS-triggered Lambda normally receives messages through an event source mapping. A failed batch can cause retry behavior, and without partial batch response support, successfully processed records may be delivered again with the failed records.

### DynamoDB Streams and other stream sources

**Symptoms**

- Records are processed repeatedly.
- Iterator age increases.
- Shard processing stops progressing.
- Downstream throttling affects stream processing.

**Check**

- Event source mapping state.
- Batch configuration and retry limits.
- Partial batch response behavior, where supported.
- Stream retention and record age.
- Downstream dependency health.

Stream checkpointing and retry semantics differ from SQS acknowledgment. Inspect the specific source's event source mapping configuration and delivery guarantees before changing retries.

### Direct asynchronous invocation

Asynchronous Lambda invocation uses a Lambda-managed queue and has its own retry and failure handling behavior.

Inspect asynchronous invocation configuration:

```bash
aws lambda get-function-event-invoke-config \
  --function-name "$FUNCTION_NAME" \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION"
```

This command does not inspect event source mappings.

### Corrective action

- Classify errors as transient or permanent.
- Use bounded retries and failure destinations appropriate to the invocation mechanism.
- Implement idempotent processing.
- Configure partial batch responses for supported event sources when appropriate.
- Monitor queue age, retries, and failed-event volume.

Exactly-once business outcomes generally require application-level idempotency and durable state transitions. They cannot be assumed merely because an invocation returned successfully.

## Deployment and Configuration Errors

### Common symptoms

- `LastUpdateStatus` reports `Failed`.
- New code behaves differently from the tested release.
- A function cannot start after deployment.
- The production alias points to an unexpected version.
- Environment variables disappear after a configuration update.

### Diagnostic commands

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION" \
  --query '{
    State:State,
    StateReason:StateReason,
    UpdateStatus:LastUpdateStatus,
    UpdateReason:LastUpdateStatusReason,
    CodeSha256:CodeSha256,
    LastModified:LastModified
  }' \
  --output json
```

### Corrective action

- Wait for code and configuration updates to finish.
- Confirm the deployed artifact and code hash.
- Verify runtime, handler, architecture, and dependencies.
- Inspect published versions and alias targets.
- Compare environment configuration with the intended complete map.
- Roll back to a known-good version when appropriate.

Rolling back code does not reverse external side effects or incompatible database migrations. Use backward-compatible deployment and migration strategies.

## Missing Logs and Misleading Metrics

### Symptom

The function appears to run, but no expected logs or metrics are visible.

**Possible causes**

- The wrong account, Region, function, or log group is being inspected.
- The function's execution role lacks CloudWatch Logs permissions.
- The function was never invoked.
- The invocation failed before application logging.
- The time window or metric dimensions are incorrect.
- Logs or metrics have not yet appeared.

**Corrective action**

1. Verify the function and Region.
2. Confirm that the function was invoked.
3. Inspect the execution role's logging permissions.
4. Check CloudWatch Logs and Lambda metrics independently.
5. Validate timestamps, dimensions, and log retention configuration.

Do not conclude that a function is healthy merely because its error metric is zero. A function that is not receiving traffic may also report zero errors.

## Unexpected Costs and Invocation Spikes

### Symptoms

- Invocation count increases unexpectedly.
- Duration or billed compute usage increases.
- CloudWatch Logs ingestion grows sharply.
- Retry activity amplifies traffic.
- Concurrency increases after an event source begins producing more records.

### Diagnostic approach

- Inspect invocation, duration, error, and throttling metrics.
- Review queue depth and age, stream iterator age, and event source configuration.
- Check recent deployments and changes to triggers.
- Investigate recursive invocation paths.
- Inspect log volume and retention settings.
- Compare the workload with expected request rates and batch sizes.

### Corrective action

- Stop unintended invocation loops.
- Correct trigger filters or event routing.
- Apply safe concurrency controls.
- Reduce excessive logging while preserving actionable diagnostics.
- Review retry behavior and dead-letter handling.
- Use AWS cost tools and billing data to confirm the actual cost source.

Do not disable production triggers blindly. Assess the backlog, event retention, data-loss risk, and recovery plan before pausing processing.

## A Repeatable Diagnostic Script

The following script captures basic function configuration and recent logs. It is intended for first-pass investigation, not automated remediation.

```bash
#!/usr/bin/env bash
set -euo pipefail

PROFILE="${AWS_PROFILE:-dev}"
REGION="${AWS_REGION:-ap-south-1}"
FUNCTION_NAME="${FUNCTION_NAME:-orders-processor}"

echo "=== AWS identity ==="
aws sts get-caller-identity \
  --profile "$PROFILE" \
  --region "$REGION"

echo "=== Function configuration ==="
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query '{
    Name:FunctionName,
    State:State,
    UpdateStatus:LastUpdateStatus,
    Runtime:Runtime,
    Handler:Handler,
    Memory:MemorySize,
    Timeout:Timeout,
    LastModified:LastModified
  }' \
  --output json

echo "=== Recent logs ==="
aws logs tail "/aws/lambda/$FUNCTION_NAME" \
  --since 30m \
  --format short \
  --profile "$PROFILE" \
  --region "$REGION"
```

For production use, add an expected account ID check and ensure diagnostic output does not expose sensitive data.

## Prevention and Production Readiness

Use the following controls to reduce recurring failures:

- **Timeouts:** Set explicit function and downstream timeouts based on measured latency and the end-to-end deadline.
- **Memory:** Benchmark representative payloads and monitor memory utilization.
- **Dependencies:** Pin versions and build native dependencies for the target runtime and architecture.
- **IAM:** Apply least privilege to execution roles and invocation policies.
- **Concurrency:** Protect downstream dependencies with capacity planning and backpressure.
- **Retries:** Configure source-specific retry behavior and failure destinations.
- **Idempotency:** Make repeated delivery safe for business operations.
- **Observability:** Use structured logs, correlation IDs, actionable alarms, and appropriate traces.
- **Deployment:** Test the packaged artifact, publish immutable versions, and use controlled alias updates.
- **Recovery:** Maintain rollback procedures and account for external side effects and data migrations.
- **Cost:** Monitor invocation volume, duration, logs, retries, and unused resources.

## Key Takeaways

- Diagnose the exact failure domain before changing timeouts, memory, permissions, networking, or event source configuration.
- Lambda timeouts and memory failures often expose deeper problems in dependency latency, payload handling, or resource usage.
- Distinguish invocation errors from handler exceptions and business failures, especially for asynchronous and event-driven workloads.
- Use configuration, logs, metrics, and source-specific diagnostics together to verify the root cause and recovery.
- Prevent recurrence through bounded timeouts, least privilege, idempotency, controlled concurrency, deployment verification, and actionable monitoring.