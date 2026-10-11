# 15- Lambda CLI Interview Guide

## Overview

AWS Lambda CLI interview questions evaluate whether an engineer can create, configure, deploy, inspect, secure, and troubleshoot Lambda functions using the AWS CLI. At senior level, the focus extends beyond command syntax to safe operational workflows, IAM permissions, deployment consistency, concurrency management, event source configuration, and production recovery.

The AWS CLI is particularly useful for:

- Automating repeatable operational procedures.
- Integrating Lambda deployment into CI/CD pipelines.
- Inspecting deployed configuration during incidents.
- Managing versions, aliases, and concurrency.
- Configuring event source mappings and invocation permissions.
- Retrieving logs and validating changes.
- Building scripts for controlled deployment and verification.

The examples use Bash-compatible syntax and AWS CLI v2. Commands should be executed only after verifying the AWS account, Region, resource identifiers, and intended change.

## AWS CLI Fundamentals

### How do you verify the AWS account and Region before operating on Lambda?

**Model answer**

Verify the active identity and explicitly specify the Region for resource operations.

```bash
aws sts get-caller-identity \
  --profile dev

aws configure get region \
  --profile dev
```

The first command identifies the account and principal associated with the credentials. The second checks the configured default Region, which may be absent or overridden by command-line options and environment variables.

For critical operations, specify the profile and Region explicitly:

```bash
aws lambda get-function-configuration \
  --function-name orders-api \
  --profile dev \
  --region ap-south-1
```

**Why this matters**

- Lambda functions are regional resources.
- A correct function name in the wrong Region may produce a misleading `ResourceNotFoundException`.
- A profile may point to a different AWS account than expected.
- CI/CD credentials may have different permissions from local credentials.

**Follow-up:** Does a successful `get-caller-identity` call prove that you can update a Lambda function?

No. It confirms the identity used by the request, not whether that principal has permission to perform a particular Lambda operation.

### How do you inspect a function's configuration?

```bash
aws lambda get-function-configuration \
  --function-name orders-api \
  --profile dev \
  --region ap-south-1 \
  --query '{
    Runtime:Runtime,
    Handler:Handler,
    Role:Role,
    Timeout:Timeout,
    MemorySize:MemorySize,
    Architectures:Architectures,
    State:State,
    LastUpdateStatus:LastUpdateStatus
  }'
```

This is a read-only operation. It provides the configuration fields most useful during deployment verification and incident diagnosis.

To inspect function metadata and its deployment package location:

```bash
aws lambda get-function \
  --function-name orders-api \
  --profile dev \
  --region ap-south-1
```

The returned deployment package URL is temporary. Treat it as sensitive and do not publish it in logs or tickets.

**Follow-up:** Why might the function be present but unavailable?

Inspect `State`, `LastUpdateStatus`, runtime errors, permissions, and the deployed integration. Resource existence alone does not prove that the function is ready to serve requests.

## Function Creation and Deployment

### How do you create a Lambda function using the CLI?

**Model answer**

Creating a ZIP-based Lambda function requires a deployment artifact and an execution role trusted by the Lambda service.

Example handler:

```python
# app.py

def lambda_handler(event, context):
    return {
        "message": "Hello from Lambda",
        "request_id": context.aws_request_id,
    }
```

Create the ZIP package:

```bash
zip function.zip app.py
```

The execution role must already exist and have a trust policy that allows `lambda.amazonaws.com` to assume it. The function's runtime permissions, such as access to DynamoDB, must be granted separately.

Create the function:

```bash
aws lambda create-function \
  --function-name orders-api \
  --runtime python3.12 \
  --handler app.lambda_handler \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-orders-execution-role \
  --zip-file fileb://function.zip \
  --timeout 15 \
  --memory-size 512 \
  --profile dev \
  --region ap-south-1
```

The runtime value is illustrative. Before using it, verify that the selected Python runtime is currently supported in the target Region.

**Important details**

- `ACCOUNT_ID` is a placeholder and must be replaced.
- `app.lambda_handler` refers to the `app.py` module and its `lambda_handler` callable.
- `fileb://` passes the local ZIP file as binary input.
- The execution role must exist before the function can be created.
- The basic example does not grant permissions to invoke the function or access application resources.
- The command creates a resource and may incur charges when the function is invoked or associated features are used.

Verify the result:

```bash
aws lambda get-function-configuration \
  --function-name orders-api \
  --profile dev \
  --region ap-south-1
```

### How do you update the code of an existing function?

**Model answer**

Use `update-function-code` to replace the deployed code artifact.

```bash
aws lambda update-function-code \
  --function-name orders-api \
  --zip-file fileb://function.zip \
  --profile dev \
  --region ap-south-1
```

Then verify the update:

```bash
aws lambda get-function-configuration \
  --function-name orders-api \
  --query '{
    State:State,
    LastUpdateStatus:LastUpdateStatus,
    LastUpdateStatusReason:LastUpdateStatusReason
  }' \
  --profile dev \
  --region ap-south-1
```

Wait for the update to finish before invoking or publishing a release:

```bash
aws lambda wait function-updated-v2 \
  --function-name orders-api \
  --profile dev \
  --region ap-south-1
```

**Senior-level considerations**

- This workflow updates the function's mutable code configuration.
- Production releases should generally publish a version and update an alias after verification.
- A direct code update does not automatically run tests or validate downstream compatibility.
- Concurrent deployment pipelines can overwrite one another unless release ownership is controlled.
- Infrastructure as Code should remain the source of truth for managed configuration.

### How do you update memory and timeout?

```bash
aws lambda update-function-configuration \
  --function-name orders-api \
  --memory-size 1024 \
  --timeout 30 \
  --profile dev \
  --region ap-south-1
```

This modifies the function's configuration. Verify the values afterward:

```bash
aws lambda get-function-configuration \
  --function-name orders-api \
  --query '{MemorySize:MemorySize,Timeout:Timeout}' \
  --profile dev \
  --region ap-south-1
```

Memory influences CPU allocation as well as memory capacity. Increasing memory can improve performance, but the result should be measured against actual duration and cost.

Do not increase timeouts to conceal stalled network connections or inefficient downstream calls.

## Function Invocation

### How do you invoke a Lambda function synchronously?

```bash
aws lambda invoke \
  --function-name orders-api \
  --invocation-type RequestResponse \
  --payload fileb://event.json \
  response.json \
  --profile dev \
  --region ap-south-1
```

Example `event.json`:

```json
{
  "order_id": "order-123"
}
```

The CLI writes the function's response payload to `response.json`. The command also returns invocation metadata, including a `StatusCode` for the invocation request.

Inspect the payload:

```bash
cat response.json
```

**Important distinction:** A successful Lambda invocation status does not necessarily mean the application succeeded. Inspect the response payload and the `FunctionError` field in the CLI output.

For synchronous invocation, Lambda can return a successful invocation status while the function itself reports an error in the invocation response.

### How do you invoke a Lambda function asynchronously?

```bash
aws lambda invoke \
  --function-name orders-worker \
  --invocation-type Event \
  --payload fileb://event.json \
  response.json \
  --profile dev \
  --region ap-south-1
```

With `InvocationType=Event`, Lambda accepts the event for asynchronous processing. The immediate response indicates acceptance, not successful completion of the handler.

The response file is not a reliable way to inspect the eventual handler result. Use CloudWatch logs, metrics, and configured failure destinations to observe processing outcomes.

**Follow-up:** When would you use asynchronous invocation instead of SQS?

Direct asynchronous invocation can suit a simple handoff when Lambda's asynchronous delivery and failure semantics meet the requirements. SQS is preferable when explicit backlog visibility, durable queue management, consumer-controlled throughput, and redrive behavior are important.

### How do you invoke a function using a published version or alias?

```bash
aws lambda invoke \
  --function-name orders-api:production \
  --invocation-type RequestResponse \
  --payload fileb://event.json \
  response.json \
  --profile dev \
  --region ap-south-1
```

The qualifier `production` identifies an alias.

Aliases provide a stable name for a published version and can support controlled traffic shifting. Invoking the unqualified function name targets the mutable `$LATEST` version, which is usually less appropriate as a production release target.

## Versions, Aliases, and Releases

### How do you publish a version?

After deploying and verifying the function configuration:

```bash
aws lambda publish-version \
  --function-name orders-api \
  --description "Release candidate" \
  --profile dev \
  --region ap-south-1
```

The command returns the published version number.

Inspect the versions:

```bash
aws lambda list-versions-by-function \
  --function-name orders-api \
  --query 'Versions[].{Version:Version,Modified:LastModified}' \
  --profile dev \
  --region ap-south-1
```

Published versions are immutable snapshots of the function's code and supported versioned configuration. Environment configuration, aliases, and external resources must still be managed carefully.

### How do you create or update an alias?

Create an alias:

```bash
aws lambda create-alias \
  --function-name orders-api \
  --name production \
  --function-version 5 \
  --description "Production release" \
  --profile dev \
  --region ap-south-1
```

Update an existing alias:

```bash
aws lambda update-alias \
  --function-name orders-api \
  --name production \
  --function-version 6 \
  --profile dev \
  --region ap-south-1
```

These commands modify production routing if the alias is used by callers.

Verify the target:

```bash
aws lambda get-alias \
  --function-name orders-api \
  --name production \
  --query '{Name:Name,Version:FunctionVersion,Routing:RoutingConfig}' \
  --profile dev \
  --region ap-south-1
```

**Follow-up:** Is moving the alias backward always a complete rollback?

No. It changes which function version the alias targets, but it does not reverse database migrations, external side effects, or incompatible data changes.

### How do you configure weighted alias routing?

A weighted alias can distribute a portion of traffic to a secondary published version.

```bash
aws lambda update-alias \
  --function-name orders-api \
  --name production \
  --function-version 6 \
  --routing-config '{"AdditionalVersionWeights":{"5":0.1}}' \
  --profile dev \
  --region ap-south-1
```

This example directs the configured primary version and an additional weighted version according to the alias routing configuration. Verify the actual alias after updating it.

Use weighted routing only when the application can tolerate mixed-version traffic. Both versions must be compatible with shared data and downstream contracts.

## Environment Variables and Configuration

### How do you configure environment variables?

```bash
aws lambda update-function-configuration \
  --function-name orders-api \
  --environment 'Variables={ORDERS_TABLE=Orders,LOG_LEVEL=INFO}' \
  --profile dev \
  --region ap-south-1
```

**Important:** The `Variables` map replaces the existing environment-variable map. It does not merge the supplied keys with the existing values.

Before modifying production configuration, inspect the current map:

```bash
aws lambda get-function-configuration \
  --function-name orders-api \
  --query 'Environment.Variables' \
  --profile dev \
  --region ap-south-1
```

If you need to preserve existing keys, construct the complete desired map and submit it as one update.

Avoid placing credentials directly in command-line arguments or shell history. Use Secrets Manager or Parameter Store for managed secrets and apply least-privilege access.

## IAM and Invocation Permissions

### How do you associate an execution role with a function?

The execution role is specified when creating the function. An existing function can be updated with:

```bash
aws lambda update-function-configuration \
  --function-name orders-api \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-orders-execution-role \
  --profile dev \
  --region ap-south-1
```

This changes the function's runtime identity. The replacement role must trust the Lambda service and grant all required runtime permissions.

Verify the configured role:

```bash
aws lambda get-function-configuration \
  --function-name orders-api \
  --query 'Role' \
  --profile dev \
  --region ap-south-1
```

### How do you allow API Gateway or another AWS service to invoke Lambda?

Lambda resource-based permissions can grant a service principal permission to invoke the function.

Example for an API Gateway integration:

```bash
aws lambda add-permission \
  --function-name orders-api \
  --statement-id allow-api-gateway \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn 'arn:aws:execute-api:ap-south-1:ACCOUNT_ID:API_ID/*/POST/orders' \
  --profile dev \
  --region ap-south-1
```

Replace the placeholders with the actual API identifiers and account information. The source ARN should be restricted to the required API, stage, method, and resource where practical.

Inspect the resource policy:

```bash
aws lambda get-policy \
  --function-name orders-api \
  --profile dev \
  --region ap-south-1
```

**Common interview trap:** An execution role controls what the function can do. It does not automatically grant API Gateway, S3, or EventBridge permission to invoke the function.

For cross-account invocation, evaluate both the relevant resource policy and the caller's authorization requirements.

## Concurrency Management

### How do you configure reserved concurrency?

```bash
aws lambda put-function-concurrency \
  --function-name orders-worker \
  --reserved-concurrent-executions 50 \
  --profile dev \
  --region ap-south-1
```

This reserves concurrency for the function and caps its simultaneous executions. It can protect downstream services but may also throttle requests if the workload exceeds the configured limit.

Inspect the setting:

```bash
aws lambda get-function-concurrency \
  --function-name orders-worker \
  --profile dev \
  --region ap-south-1
```

Remove the reserved concurrency configuration:

```bash
aws lambda delete-function-concurrency \
  --function-name orders-worker \
  --profile dev \
  --region ap-south-1
```

Removing reserved concurrency does not guarantee unlimited capacity. Account quotas and other function reservations still apply.

### How do you configure provisioned concurrency?

Provisioned concurrency is configured for a published version or alias, not directly for the mutable `$LATEST` version.

```bash
aws lambda put-provisioned-concurrency-config \
  --function-name orders-api \
  --qualifier production \
  --provisioned-concurrent-executions 10 \
  --profile dev \
  --region ap-south-1
```

Inspect its status:

```bash
aws lambda get-provisioned-concurrency-config \
  --function-name orders-api \
  --qualifier production \
  --profile dev \
  --region ap-south-1
```

Provisioned concurrency can improve latency predictability but incurs additional charges. Check its status before depending on it for latency-sensitive traffic, and size it using observed concurrency and load tests.

## Event Source Mappings

### How do you list event source mappings?

```bash
aws lambda list-event-source-mappings \
  --function-name orders-worker \
  --profile dev \
  --region ap-south-1
```

Inspect a particular mapping:

```bash
aws lambda get-event-source-mapping \
  --uuid EVENT_SOURCE_MAPPING_UUID \
  --profile dev \
  --region ap-south-1
```

Replace `EVENT_SOURCE_MAPPING_UUID` with the mapping's actual UUID.

The response includes its state, source ARN, batch configuration, and other applicable settings.

### How do you create an SQS event source mapping?

```bash
aws lambda create-event-source-mapping \
  --function-name orders-worker \
  --event-source-arn arn:aws:sqs:ap-south-1:ACCOUNT_ID:orders-queue \
  --batch-size 10 \
  --enabled \
  --function-response-types ReportBatchItemFailures \
  --profile dev \
  --region ap-south-1
```

The command creates a mapping between the SQS queue and Lambda. The function's execution role needs the permissions required to consume messages from the queue, and the queue must be in a supported configuration.

Verify the mapping:

```bash
aws lambda list-event-source-mappings \
  --function-name orders-worker \
  --profile dev \
  --region ap-south-1 \
  --query 'EventSourceMappings[].{
    UUID:UUID,
    State:State,
    BatchSize:BatchSize,
    ResponseTypes:FunctionResponseTypes
  }'
```

**Production considerations**

- Confirm that the batch size is valid for the source.
- Configure the SQS visibility timeout in relation to Lambda timeout and batch processing behavior.
- Enable partial batch responses only when the handler returns the expected response structure.
- Configure the queue's redrive policy and define a dead-letter replay process.
- Check source-specific scaling and concurrency settings before changing throughput.

### How do you disable an event source mapping temporarily?

```bash
aws lambda update-event-source-mapping \
  --uuid EVENT_SOURCE_MAPPING_UUID \
  --no-enabled \
  --profile dev \
  --region ap-south-1
```

Verify the resulting state:

```bash
aws lambda get-event-source-mapping \
  --uuid EVENT_SOURCE_MAPPING_UUID \
  --query '{State:State,StateTransitionReason:StateTransitionReason}' \
  --profile dev \
  --region ap-south-1
```

Disabling a mapping affects message consumption. It does not delete queued messages, and source retention policies still apply. Before disabling production processing, assess backlog growth, message retention, ordering requirements, and downstream impact.

## CloudWatch Logs and Monitoring

### How do you retrieve recent Lambda logs?

```bash
aws logs tail /aws/lambda/orders-api \
  --since 30m \
  --profile dev \
  --region ap-south-1
```

Follow new entries:

```bash
aws logs tail /aws/lambda/orders-api \
  --follow \
  --profile dev \
  --region ap-south-1
```

The caller needs the relevant CloudWatch Logs read permissions. The Lambda execution role also needs permissions to create the log group and write log streams and events when those resources are not managed through another deployment mechanism.

### How do you query recent errors using CloudWatch Logs Insights?

Start a query:

```bash
QUERY_ID=$(aws logs start-query \
  --log-group-name /aws/lambda/orders-api \
  --start-time "$(date -u -d '30 minutes ago' +%s)" \
  --end-time "$(date -u +%s)" \
  --query-string 'fields @timestamp, @message
    | filter @message like /ERROR/
    | sort @timestamp desc
    | limit 50' \
  --query queryId \
  --output text \
  --profile dev \
  --region ap-south-1)
```

Retrieve the results:

```bash
aws logs get-query-results \
  --query-id "$QUERY_ID" \
  --profile dev \
  --region ap-south-1
```

The timestamp expressions above use GNU `date`, as commonly available in Linux CI runners. On other operating systems, calculate the epoch values using an equivalent tool.

Logs Insights queries are asynchronous. If the query is still running, poll `get-query-results` until the query reaches a terminal status.

### How would you investigate throttling from the CLI?

Inspect function configuration first:

```bash
aws lambda get-function-concurrency \
  --function-name orders-worker \
  --profile dev \
  --region ap-south-1
```

Then retrieve the CloudWatch `Throttles` metric for the relevant time window:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Throttles \
  --dimensions Name=FunctionName,Value=orders-worker \
  --start-time 2026-10-11T18:00:00Z \
  --end-time 2026-10-11T19:00:00Z \
  --period 60 \
  --statistics Sum \
  --profile dev \
  --region ap-south-1
```

Replace the timestamps with the incident's actual UTC time range.

A nonzero throttle count should be interpreted alongside concurrency, invocation volume, account quotas, and downstream capacity. It does not by itself identify the root cause.

## Deployment and Operational Safety

### How do you delete a Lambda function?

```bash
aws lambda delete-function \
  --function-name orders-api \
  --profile dev \
  --region ap-south-1
```

This is destructive. Before deletion, verify the account, Region, function name, callers, event source mappings, aliases, and any infrastructure-as-code ownership.

Deleting a function does not delete every related resource, such as its CloudWatch log group, SQS queues, IAM role, or other dependencies. Clean up resources only when their ownership and dependencies are understood.

### How do you deploy Lambda from CI/CD safely?

A production deployment pipeline should:

1. Authenticate using short-lived credentials, preferably through GitHub Actions OIDC federation.
2. Build the artifact in a reproducible environment.
3. Run unit tests, static checks, and dependency scanning.
4. Deploy the artifact to the intended function.
5. Wait for the update to complete.
6. Run smoke tests.
7. Publish a version.
8. Shift the intended alias to the new version.
9. Monitor errors, duration, throttles, and business outcomes.
10. Roll back the alias when the release violates operational criteria.

Keep deployment permissions separate from the function's execution role. The deployment identity needs permission to release code and configuration; the execution role needs only the permissions required at runtime.

Avoid storing long-lived AWS access keys in repository secrets when OIDC federation is available and suitable for the deployment design.

## Senior-Level CLI Scenarios

### Scenario: `ResourceNotFoundException` occurs even though the function exists.

**Likely causes**

- Wrong AWS Region.
- Wrong AWS account or profile.
- Incorrect function name or qualifier.
- Function deleted or not yet created.
- Typographical error in the command.

**Diagnostic commands**

```bash
aws sts get-caller-identity \
  --profile dev

aws lambda list-functions \
  --profile dev \
  --region ap-south-1 \
  --query 'Functions[].FunctionName'
```

Verify the account and Region before attempting another modification.

### Scenario: `ResourceConflictException` occurs during deployment.

**Likely causes**

- Another update is still in progress.
- Multiple deployment jobs are modifying the same function.
- A previous deployment has not completed.

**Diagnostic command**

```bash
aws lambda get-function-configuration \
  --function-name orders-api \
  --query '{State:State,LastUpdateStatus:LastUpdateStatus,Reason:LastUpdateStatusReason}' \
  --profile dev \
  --region ap-south-1
```

Wait for the existing update to finish, inspect its status, and serialize deployments for the same function. Do not blindly retry configuration updates while another release is in progress.

### Scenario: An SQS event source mapping exists but messages are not being processed.

**Investigation**

- Inspect mapping state and state-transition reason.
- Verify the source queue ARN and Region.
- Check the Lambda execution role's SQS permissions.
- Confirm the queue has available messages.
- Inspect Lambda errors, throttles, and concurrency.
- Check visibility timeout, redrive policy, and message retention.
- Verify that the function and mapping configuration match the expected deployment.

A mapping's existence does not prove that it is enabled, healthy, or successfully processing messages.

### Scenario: The CLI deployment succeeds, but production still runs the old code.

**Likely causes**

- API Gateway or another caller invokes a published version or alias.
- The code update targeted `$LATEST`, but the production alias still points to an older version.
- The caller uses a different Region or account.
- The deployment updated the wrong function.

Inspect the alias:

```bash
aws lambda get-alias \
  --function-name orders-api \
  --name production \
  --profile dev \
  --region ap-south-1
```

Verify the deployed code, published version, alias target, and caller configuration before making another change.

## CLI Interview Quick Reference

| Task | Command |
|---|---|
| Verify identity | `aws sts get-caller-identity` |
| Inspect configuration | `aws lambda get-function-configuration` |
| Inspect function metadata | `aws lambda get-function` |
| Create function | `aws lambda create-function` |
| Update code | `aws lambda update-function-code` |
| Update configuration | `aws lambda update-function-configuration` |
| Invoke synchronously | `aws lambda invoke --invocation-type RequestResponse` |
| Invoke asynchronously | `aws lambda invoke --invocation-type Event` |
| Publish version | `aws lambda publish-version` |
| Create alias | `aws lambda create-alias` |
| Update alias | `aws lambda update-alias` |
| Configure reserved concurrency | `aws lambda put-function-concurrency` |
| Inspect concurrency | `aws lambda get-function-concurrency` |
| Configure provisioned concurrency | `aws lambda put-provisioned-concurrency-config` |
| List event source mappings | `aws lambda list-event-source-mappings` |
| Inspect event source mapping | `aws lambda get-event-source-mapping` |
| Retrieve logs | `aws logs tail` |
| Inspect function policy | `aws lambda get-policy` |
| Delete function | `aws lambda delete-function` |

## Key Takeaways

- Verify the AWS account, Region, and principal before executing commands that modify production resources.
- Understand the distinction between function code, mutable configuration, published versions, aliases, execution roles, and resource-based policies.
- Treat event source mappings, retries, concurrency settings, and failure handling as operational controls that directly affect reliability.
- Use CLI verification commands, CloudWatch logs, and metrics to confirm outcomes rather than assuming that a successful command proves application health.
- Automate deployments through reproducible CI/CD workflows, short-lived credentials, versioned releases, smoke tests, and a tested rollback strategy.
```