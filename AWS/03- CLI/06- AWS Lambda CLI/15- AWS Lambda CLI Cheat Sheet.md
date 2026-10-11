# 15- AWS Lambda CLI Cheat Sheet

## Overview

This cheat sheet provides frequently used AWS CLI commands for developing, deploying, inspecting, troubleshooting, and operating AWS Lambda functions. It is designed for day-to-day backend engineering work and production incident response.

Commands are grouped by operational responsibility, with an emphasis on safe execution order, verification, filtering, and repeatable workflows.

### Command conventions

The examples use Bash syntax and AWS CLI v2.

```bash
PROFILE=dev
REGION=ap-south-1
FUNCTION_NAME=orders-processor
LOG_GROUP="/aws/lambda/$FUNCTION_NAME"
```

Replace example names, ARNs, IDs, and file paths with values from your environment.

| Label | Meaning |
|---|---|
| Read-only | Inspects configuration, state, or telemetry |
| Mutating | Creates, updates, or deletes AWS resources |
| Potentially disruptive | Can interrupt processing, change traffic, or affect production behavior |

Always specify the intended profile and Region for operational commands. For production automation, use explicit account checks and fail-fast shell behavior.

## AWS CLI Setup and Account Verification

### Verify CLI installation

**Operation:** Read-only.

```bash
aws --version
```

Use AWS CLI v2 for current operational workflows.

### Inspect configured profiles

**Operation:** Read-only.

```bash
aws configure list-profiles
```

```bash
aws configure list --profile "$PROFILE"
```

The second command displays credential source and configuration metadata. Avoid sharing its output without reviewing it for sensitive information.

### Verify the active identity

**Operation:** Read-only.

```bash
aws sts get-caller-identity \
  --profile "$PROFILE" \
  --region "$REGION" \
  --output json
```

### Verify the target Region

**Operation:** Read-only.

```bash
aws configure get region --profile "$PROFILE"
```

An explicitly supplied `--region` overrides the configured Region for that command.

### Recommended safety check

```bash
EXPECTED_ACCOUNT_ID=123456789012

ACTUAL_ACCOUNT_ID=$(
  aws sts get-caller-identity \
    --profile "$PROFILE" \
    --query Account \
    --output text
)

if [ "$ACTUAL_ACCOUNT_ID" != "$EXPECTED_ACCOUNT_ID" ]; then
  echo "Unexpected AWS account: $ACTUAL_ACCOUNT_ID" >&2
  exit 1
fi

echo "AWS account verified: $ACTUAL_ACCOUNT_ID"
```

Use an account ID appropriate for the intended environment. For production automation, also verify the assumed role or principal where necessary.

## Function Inspection and Configuration

### List functions

**Operation:** Read-only.

```bash
aws lambda list-functions \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query 'Functions[].{
    Name:FunctionName,
    Runtime:Runtime,
    Memory:MemorySize,
    Timeout:Timeout,
    LastModified:LastModified
  }' \
  --output table
```

The result is limited to the selected account and Region. For large environments, use pagination or targeted filters.

### Inspect a function

**Operation:** Read-only.

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --output json
```

Useful fields include:

- `State` and `StateReason`
- `LastUpdateStatus` and `LastUpdateStatusReason`
- `Runtime`, `Handler`, and `Architectures`
- `MemorySize`, `Timeout`, and `EphemeralStorage`
- `Role`, `VpcConfig`, and `Environment`
- `CodeSha256` and `LastModified`

### Inspect function code metadata

**Operation:** Read-only.

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query '{
    Configuration:Configuration,
    Code:Code
  }' \
  --output json
```

The response can include a temporary code download URL. Treat the output as sensitive operational data.

### Inspect function versions

**Operation:** Read-only.

```bash
aws lambda list-versions-by-function \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query 'Versions[].{
    Version:Version,
    Modified:LastModified,
    Runtime:Runtime,
    Memory:MemorySize,
    Timeout:Timeout
  }' \
  --output table
```

### Inspect aliases

**Operation:** Read-only.

```bash
aws lambda list-aliases \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --output table
```

```bash
aws lambda get-alias \
  --function-name "$FUNCTION_NAME" \
  --name prod \
  --profile "$PROFILE" \
  --region "$REGION" \
  --output json
```

Aliases provide stable names for published versions and can support weighted traffic shifting.

## Create, Update, and Delete Functions

### Create a function

**Operation:** Mutating.

Prerequisites:

- A deployment ZIP containing the handler and dependencies.
- An existing execution role with the appropriate trust policy and permissions.
- A runtime supported in the target Region.

```bash
aws lambda create-function \
  --function-name orders-processor \
  --runtime python3.12 \
  --handler app.handler \
  --role arn:aws:iam::123456789012:role/lambda-orders-execution-role \
  --zip-file fileb://function.zip \
  --memory-size 512 \
  --timeout 30 \
  --profile "$PROFILE" \
  --region "$REGION"
```

The runtime is illustrative; verify currently supported runtimes before deployment. The role ARN must refer to an existing role trusted by Lambda.

### Update function code

**Operation:** Mutating.

```bash
aws lambda update-function-code \
  --function-name "$FUNCTION_NAME" \
  --zip-file fileb://function.zip \
  --profile "$PROFILE" \
  --region "$REGION"
```

### Update function configuration

**Operation:** Mutating.

```bash
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --memory-size 1024 \
  --timeout 45 \
  --profile "$PROFILE" \
  --region "$REGION"
```

This changes the memory allocation and timeout. Choose values based on measured workload behavior, not guesswork.

### Wait for an update to finish

**Operation:** Read-only polling.

```bash
aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION"
```

Verify the result:

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query '{
    State:State,
    LastUpdateStatus:LastUpdateStatus,
    Memory:MemorySize,
    Timeout:Timeout
  }' \
  --output json
```

### Delete a function

**Operation:** Mutating and potentially disruptive.

```bash
aws lambda delete-function \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION"
```

Deleting a function does not automatically remove every related resource, such as log groups, event source resources, queues, or infrastructure managed separately. Review dependencies and retention requirements before deletion.

## Invoke a Function

### Synchronous invocation

**Operation:** Executes application code.

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --payload '{"order_id":"ORD-1001"}' \
  --cli-binary-format raw-in-base64-out \
  response.json \
  --profile "$PROFILE" \
  --region "$REGION"
```

Inspect the payload response:

```bash
cat response.json
```

For synchronous invocation, inspect the CLI response for `StatusCode` and `FunctionError`. A successful invocation API response does not guarantee that application-level processing succeeded.

### Inspect a function error

**Operation:** Executes application code.

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --payload '{"order_id":"ORD-1001"}' \
  --cli-binary-format raw-in-base64-out \
  --log-type Tail \
  response.json \
  --profile "$PROFILE" \
  --region "$REGION"
```

When requested, the response can include a base64-encoded `LogResult` containing a short section of execution logs. Decode it when needed:

```bash
printf '%s' 'BASE64_LOG_RESULT' | base64 --decode
```

Replace `BASE64_LOG_RESULT` with the actual value returned by the command.

### Invoke asynchronously

**Operation:** Submits an asynchronous invocation.

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type Event \
  --payload '{"order_id":"ORD-1001"}' \
  --cli-binary-format raw-in-base64-out \
  async-response.json \
  --profile "$PROFILE" \
  --region "$REGION"
```

A successful submission does not prove that the function completed successfully. Configure and monitor retries and failure destinations according to the workload requirements.

## Environment Variables

### Inspect environment variable names

**Operation:** Read-only.

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query 'Environment.Variables' \
  --output json
```

Environment values may contain sensitive information. Do not print them in shared terminal sessions, CI logs, or incident reports.

### Update environment variables

**Operation:** Mutating.

Create a local JSON file containing the complete desired environment variable map:

```json
{
  "Variables": {
    "APP_ENV": "production",
    "LOG_LEVEL": "INFO",
    "TABLE_NAME": "orders"
  }
}
```

Save it as `environment.json`, then run:

```bash
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --environment file://environment.json \
  --profile "$PROFILE" \
  --region "$REGION"
```

**Important:** This replaces the function's environment variable map; it does not merge the supplied keys with the existing map. Preserve required existing variables when constructing the replacement.

Use Secrets Manager or Systems Manager Parameter Store for secrets where appropriate. Environment variable encryption does not eliminate the need to protect values from authorized principals and logs.

## Versions, Aliases, and Rollbacks

### Publish a version

**Operation:** Mutating.

```bash
aws lambda publish-version \
  --function-name "$FUNCTION_NAME" \
  --description "Release after deployment verification" \
  --profile "$PROFILE" \
  --region "$REGION"
```

A published version is immutable. Verify the returned version number before updating production aliases.

### Create an alias

**Operation:** Mutating.

```bash
aws lambda create-alias \
  --function-name "$FUNCTION_NAME" \
  --name prod \
  --function-version 12 \
  --description "Production alias" \
  --profile "$PROFILE" \
  --region "$REGION"
```

Replace `12` with the actual published version.

### Update an alias

**Operation:** Mutating.

```bash
aws lambda update-alias \
  --function-name "$FUNCTION_NAME" \
  --name prod \
  --function-version 13 \
  --profile "$PROFILE" \
  --region "$REGION"
```

### Roll back an alias

**Operation:** Mutating and potentially disruptive.

```bash
aws lambda update-alias \
  --function-name "$FUNCTION_NAME" \
  --name prod \
  --function-version 12 \
  --profile "$PROFILE" \
  --region "$REGION"
```

Rollback changes the alias target, not the state of external systems. Database migrations, queue messages, and other side effects may not be reversible.

## Concurrency and Scaling

### Inspect reserved concurrency

**Operation:** Read-only.

```bash
aws lambda get-function-concurrency \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION"
```

### Set reserved concurrency

**Operation:** Mutating.

```bash
aws lambda put-function-concurrency \
  --function-name "$FUNCTION_NAME" \
  --reserved-concurrent-executions 50 \
  --profile "$PROFILE" \
  --region "$REGION"
```

Choose the value according to expected load and downstream capacity.

### Remove reserved concurrency

**Operation:** Mutating.

```bash
aws lambda delete-function-concurrency \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION"
```

This removes the function-level reserved concurrency setting. It does not mean that concurrency is unlimited; account and service quotas still apply.

### Inspect account concurrency

**Operation:** Read-only.

```bash
aws lambda get-account-settings \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query '{
    ConcurrentExecutions:AccountUsage.ConcurrentExecutions,
    ConcurrentExecutionLimit:AccountLimit.ConcurrentExecutions,
    UnreservedConcurrentExecutions:AccountLimit.UnreservedConcurrentExecutions
  }' \
  --output json
```

### Inspect provisioned concurrency

**Operation:** Read-only.

```bash
aws lambda list-provisioned-concurrency-configs \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --output table
```

Provisioned concurrency requires a published version or alias qualifier. It incurs additional charges and should be configured based on latency requirements and traffic patterns.

## Event Source Mappings

### List mappings

**Operation:** Read-only.

```bash
aws lambda list-event-source-mappings \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query 'EventSourceMappings[].{
    UUID:UUID,
    State:State,
    Source:EventSourceArn,
    BatchSize:BatchSize,
    LastResult:LastProcessingResult
  }' \
  --output table
```

### Inspect a mapping

**Operation:** Read-only.

```bash
MAPPING_UUID='replace-with-mapping-uuid'

aws lambda get-event-source-mapping \
  --uuid "$MAPPING_UUID" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --output json
```

### Enable a mapping

**Operation:** Mutating and potentially disruptive.

```bash
aws lambda update-event-source-mapping \
  --uuid "$MAPPING_UUID" \
  --enabled \
  --profile "$PROFILE" \
  --region "$REGION"
```

### Disable a mapping

**Operation:** Mutating and potentially disruptive.

```bash
aws lambda update-event-source-mapping \
  --uuid "$MAPPING_UUID" \
  --no-enabled \
  --profile "$PROFILE" \
  --region "$REGION"
```

Disabling a mapping stops Lambda from polling the source through that mapping. Source data may continue accumulating, and behavior depends on the source's retention and delivery semantics.

## Resource-Based Invocation Permissions

### Inspect a function policy

**Operation:** Read-only.

```bash
aws lambda get-policy \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --output json
```

### Allow an AWS service to invoke a function

**Operation:** Mutating.

Example for an S3 bucket in the same account:

```bash
BUCKET_NAME=company-order-events
ACCOUNT_ID=123456789012

aws lambda add-permission \
  --function-name "$FUNCTION_NAME" \
  --statement-id allow-orders-bucket \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn "arn:aws:s3:::$BUCKET_NAME" \
  --source-account "$ACCOUNT_ID" \
  --profile "$PROFILE" \
  --region "$REGION"
```

This grants invocation permission to the specified S3 source. Configure the S3 notification separately and ensure that the bucket and Lambda function are in a supported Region relationship.

### Remove a permission statement

**Operation:** Mutating.

```bash
aws lambda remove-permission \
  --function-name "$FUNCTION_NAME" \
  --statement-id allow-orders-bucket \
  --profile "$PROFILE" \
  --region "$REGION"
```

Use the correct statement ID and verify that removing the permission will not break other integrations.

## Lambda Layers

### List layers

**Operation:** Read-only.

```bash
aws lambda list-layers \
  --profile "$PROFILE" \
  --region "$REGION" \
  --output table
```

### Publish a layer version

**Operation:** Mutating.

```bash
aws lambda publish-layer-version \
  --layer-name backend-shared-dependencies \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.12 \
  --profile "$PROFILE" \
  --region "$REGION"
```

Verify the runtime and architecture compatibility of dependencies before publishing.

### List versions of a layer

**Operation:** Read-only.

```bash
aws lambda list-layer-versions \
  --layer-name backend-shared-dependencies \
  --profile "$PROFILE" \
  --region "$REGION" \
  --output table
```

Layer versions are immutable. Updating a layer does not automatically update functions that reference an older layer version.

## CloudWatch Logs and Troubleshooting

### Tail recent logs

**Operation:** Read-only.

```bash
aws logs tail "$LOG_GROUP" \
  --since 30m \
  --format short \
  --profile "$PROFILE" \
  --region "$REGION"
```

### List log groups

**Operation:** Read-only.

```bash
aws logs describe-log-groups \
  --log-group-name-prefix "$LOG_GROUP" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --output table
```

### Query error events

**Operation:** Read-only.

```bash
START_TIME=$(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%SZ)
END_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)

aws logs start-query \
  --log-group-name "$LOG_GROUP" \
  --start-time "$(date -u -d '30 minutes ago' +%s)" \
  --end-time "$(date -u +%s)" \
  --query-string 'fields @timestamp, @message
    | filter @message like /ERROR|Exception|Task timed out/
    | sort @timestamp desc
    | limit 100' \
  --profile "$PROFILE" \
  --region "$REGION"
```

The command returns a query ID. Retrieve results with `aws logs get-query-results` after the query has progressed to a completed state.

### Inspect invocation metrics

**Operation:** Read-only.

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 60 \
  --statistics Sum \
  --profile "$PROFILE" \
  --region "$REGION" \
  --output table
```

Change the metric name to inspect `Errors`, `Throttles`, or `Duration`. Use the correct statistic for the metric, and verify the dimensions used by the CloudWatch metric.

## JMESPath Filtering and Output Formatting

AWS CLI supports JMESPath expressions through `--query`. Use these to reduce output, extract identifiers, and make scripts more reliable.

### Select specific function fields

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query '{
    Name:FunctionName,
    Runtime:Runtime,
    Memory:MemorySize,
    Timeout:Timeout,
    State:State
  }' \
  --output json
```

### List only Python functions

```bash
aws lambda list-functions \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query "Functions[?starts_with(Runtime, 'python')].{
    Name:FunctionName,
    Runtime:Runtime
  }" \
  --output table
```

### Filter functions by name

```bash
aws lambda list-functions \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query "Functions[?contains(FunctionName, 'orders')].FunctionName" \
  --output text
```

### Extract an ARN for scripting

```bash
FUNCTION_ARN=$(
  aws lambda get-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --profile "$PROFILE" \
    --region "$REGION" \
    --query FunctionArn \
    --output text
)

printf '%s\n' "$FUNCTION_ARN"
```

### Choose an output format

| Format | Best use |
|---|---|
| `json` | Automation, structured inspection, and piping into JSON tools |
| `table` | Human-readable terminal output |
| `text` | Simple extraction of values for shell scripts |
| `yaml` | Human-readable configuration inspection where supported |

Prefer JSON for scripts that need nested fields. Do not parse human-oriented table output in automation.

## Container Image Functions

### Inspect package type

**Operation:** Read-only.

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query '{
    PackageType:PackageType,
    Architectures:Architectures
  }' \
  --output json
```

### Update code from ECR

**Operation:** Mutating.

```bash
aws lambda update-function-code \
  --function-name "$FUNCTION_NAME" \
  --image-uri 123456789012.dkr.ecr.ap-south-1.amazonaws.com/orders-processor:release-2026-10 \
  --profile "$PROFILE" \
  --region "$REGION"
```

Use an image URI from the correct account and Region, and ensure Lambda has the permissions needed to retrieve the image. For reproducible releases, prefer immutable image digests or controlled tags over mutable tags.

## Repeatable Operational Workflow

The following workflow combines account verification, configuration inspection, and log retrieval before making a change.

```bash
#!/usr/bin/env bash
set -euo pipefail

PROFILE="${PROFILE:-dev}"
REGION="${REGION:-ap-south-1}"
FUNCTION_NAME="${FUNCTION_NAME:-orders-processor}"
EXPECTED_ACCOUNT_ID="${EXPECTED_ACCOUNT_ID:?Set EXPECTED_ACCOUNT_ID}"

ACTUAL_ACCOUNT_ID=$(
  aws sts get-caller-identity \
    --profile "$PROFILE" \
    --query Account \
    --output text
)

if [[ "$ACTUAL_ACCOUNT_ID" != "$EXPECTED_ACCOUNT_ID" ]]; then
  echo "Account mismatch: expected $EXPECTED_ACCOUNT_ID, got $ACTUAL_ACCOUNT_ID" >&2
  exit 1
fi

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
    Memory:MemorySize,
    Timeout:Timeout
  }' \
  --output json

echo "=== Recent logs ==="
aws logs tail "/aws/lambda/$FUNCTION_NAME" \
  --since 30m \
  --format short \
  --profile "$PROFILE" \
  --region "$REGION"
```

This workflow is read-only apart from the application execution that may already be occurring independently. Keep scripts focused, fail on identity mismatches, and avoid automatically changing production settings based on incomplete diagnostics.

## Common CLI Mistakes

| Mistake | Why it matters | Better practice |
|---|---|---|
| Omitting `--region` | Commands can target the wrong Region | Specify the Region explicitly |
| Using the wrong profile | Can inspect or modify the wrong account | Verify the caller identity first |
| Treating `StatusCode: 200` as application success | The invocation API can succeed while the function reports an error | Check `FunctionError` and the response payload |
| Replacing environment variables with a partial map | Existing variables can be removed | Build and review the complete desired map |
| Updating an alias before validating a release | Production traffic may reach an unverified version | Test the published version and then move the alias |
| Increasing concurrency without checking dependencies | Can overload databases and external services | Calculate capacity and apply backpressure |
| Removing a permission without checking integrations | Existing event sources may stop invoking the function | Inspect policy statements and source dependencies |
| Assuming a successful asynchronous submission means completion | Processing happens after the initial response | Monitor errors, retries, and failure destinations |
| Printing all environment variables or API responses | Can expose sensitive operational data | Query only required fields and redact output |
| Deleting resources without checking dependencies | Can disrupt processing or leave related resources behind | Inspect integrations and plan cleanup |

## Key Takeaways

- Verify the AWS account, profile, and Region before running operational commands.
- Use `get-function-configuration`, CloudWatch Logs, metrics, and event source mapping inspection to establish the failure domain before changing resources.
- Treat deployment, concurrency, permissions, environment variables, and event source configuration updates as controlled changes requiring verification.
- Use JMESPath and JSON output for reliable automation, and protect sensitive command output from logs and shared terminals.
- Build repeatable workflows with account guards, explicit parameters, least privilege, post-change verification, and a defined rollback procedure.