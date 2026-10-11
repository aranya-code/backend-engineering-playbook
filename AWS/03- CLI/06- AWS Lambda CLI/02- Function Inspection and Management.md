# 02- Function Inspection and Management

## Overview

AWS Lambda function inspection and management through the AWS CLI provides direct control over deployed functions, their configuration, execution state, deployment packages, and operational metadata.

For backend engineers, these commands are essential for diagnosing deployment failures, verifying runtime configuration, investigating unexpected behavior, automating maintenance tasks, and validating production changes without relying exclusively on the AWS Management Console.

This document covers function discovery, configuration inspection, code and configuration updates, function lifecycle management, safe deletion, and post-operation verification. Invocation, concurrency, versions, aliases, event source mappings, and deployment packaging are covered in their respective CLI documents.

## Prerequisites

Before executing the commands, ensure that:

- AWS CLI v2 is installed.
- Credentials are configured through an appropriate profile, IAM role, or federated identity.
- The active identity has the necessary Lambda permissions.
- The correct AWS account and Region have been selected.
- The target function name or ARN is known.

Verify the active identity and Region:

```bash
aws sts get-caller-identity --profile dev
aws configure get region --profile dev
```

For the examples below, assume:

```bash
PROFILE=dev
REGION=ap-south-1
FUNCTION_NAME=orders-api
```

These assignments use Bash syntax. In PowerShell, use `$PROFILE`, `$REGION`, and `$FUNCTION_NAME` instead.

For commands that modify resources, explicitly provide the profile and Region. This reduces the risk of accidentally changing a function in another environment.

## Understand Function Identifiers

Lambda functions can be addressed by name, ARN, or qualified identifier.

| Identifier | Example | Purpose |
|---|---|---|
| Function name | `orders-api` | Identifies the function in the current account and Region |
| Function ARN | `arn:aws:lambda:ap-south-1:123456789012:function:orders-api` | Fully identifies the function resource |
| Version-qualified ARN | `arn:aws:lambda:ap-south-1:123456789012:function:orders-api:12` | Identifies a published version |
| Alias-qualified ARN | `arn:aws:lambda:ap-south-1:123456789012:function:orders-api:production` | Identifies an alias and its routing configuration |

A function name alone is not globally unique. The account and Region are part of the effective resource context.

Use an alias when investigating production traffic routed through a stable deployment identifier. Inspecting the unqualified function configuration does not necessarily tell you which published version an alias invokes.

## List Lambda Functions

### List functions in a Region

The `list-functions` command retrieves functions visible to the current identity.

```bash
aws lambda list-functions \
  --profile "$PROFILE" \
  --region "$REGION"
```

The response contains function metadata, including function names, ARNs, runtimes, handlers, memory settings, timeouts, and modification timestamps.

### Return a concise inventory

Use JMESPath to display only the fields needed for an inventory.

```bash
aws lambda list-functions \
  --query 'Functions[].{Name:FunctionName,Runtime:Runtime,MemoryMB:MemorySize,TimeoutSeconds:Timeout,LastModified:LastModified}' \
  --output table \
  --profile "$PROFILE" \
  --region "$REGION"
```

This is useful for identifying configuration inconsistencies across functions.

### Filter functions by runtime

```bash
aws lambda list-functions \
  --query 'Functions[?Runtime==`python3.12`].{Name:FunctionName,Runtime:Runtime}' \
  --output table \
  --profile "$PROFILE" \
  --region "$REGION"
```

Runtime support and deprecation status change over time. Use this query as an inventory mechanism, not as proof that a runtime is currently supported for new deployments.

### Filter functions by naming convention

```bash
aws lambda list-functions \
  --query 'Functions[?starts_with(FunctionName, `orders-`)].FunctionName' \
  --output text \
  --profile "$PROFILE" \
  --region "$REGION"
```

Naming conventions can help organize serverless systems, but they should not replace resource tags, account boundaries, or infrastructure-as-code ownership.

### Pagination considerations

AWS CLI automatically handles pagination for normal command output unless pagination is disabled or a command-specific option changes that behavior.

For a large account, avoid assuming that one API response contains every function. Use the standard CLI paginator for complete inventories. When scripting with `--max-items`, account for the returned pagination token and retrieve subsequent pages as necessary.

## Inspect Function Configuration

The `get-function-configuration` command retrieves the configuration of a function or a qualified version.

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION"
```

### Inspect important fields

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Name:FunctionName,Arn:FunctionArn,Runtime:Runtime,Handler:Handler,Role:Role,MemoryMB:MemorySize,TimeoutSeconds:Timeout,EphemeralStorageMB:EphemeralStorage.Size,Architectures:Architectures,State:State,LastUpdateStatus:LastUpdateStatus,LastModified:LastModified}' \
  --output json \
  --profile "$PROFILE" \
  --region "$REGION"
```

Important fields include:

| Field | Engineering significance |
|---|---|
| `Runtime` | Identifies the managed runtime, when applicable |
| `Handler` | Identifies the entry point for supported handler-based runtimes |
| `Role` | ARN of the execution role assumed by Lambda |
| `MemorySize` | Configured memory allocation, which also influences available CPU |
| `Timeout` | Maximum execution duration for a single invocation |
| `EphemeralStorage.Size` | Configured `/tmp` storage capacity |
| `Architectures` | Configured instruction-set architecture |
| `State` | Current function lifecycle state |
| `LastUpdateStatus` | Status of the most recent configuration or code update |
| `LastModified` | Timestamp of the most recent function modification |
| `Environment.Variables` | Configured environment variables, which require careful handling |
| `VpcConfig` | VPC-related configuration, when applicable |

Do not assume every field is present for every function. Container-image functions, custom runtimes, published versions, and other configurations can expose different combinations of fields.

### Inspect a published version

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --qualifier 12 \
  --query '{Arn:FunctionArn,Version:Version,Runtime:Runtime,MemoryMB:MemorySize,TimeoutSeconds:Timeout}' \
  --output json \
  --profile "$PROFILE" \
  --region "$REGION"
```

Replace `12` with an existing published version.

A published version represents a snapshot of function code and configuration. Inspecting a version-qualified resource is useful when debugging a production alias that points to a specific version.

### Inspect the execution role

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query 'Role' \
  --output text \
  --profile "$PROFILE" \
  --region "$REGION"
```

The returned role ARN identifies the function's execution role. It does not show every effective permission: managed policies, inline policies, resource policies, permission boundaries, service control policies, and other authorization controls can affect the final result.

## Inspect Function Code and Deployment Metadata

Use `get-function` to retrieve function metadata and a download URL for the deployed package when applicable.

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION"
```

The response includes configuration and a `Code` section. For ZIP-based functions, `Code.Location` is a temporary, presigned download URL.

Avoid printing or storing the entire response in shared CI logs because the URL grants temporary access to the deployment artifact.

To inspect only selected metadata:

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --query '{FunctionArn:Configuration.FunctionArn,Version:Configuration.Version,PackageType:Configuration.PackageType,CodeSha256:Configuration.CodeSha256,LastModified:Configuration.LastModified}' \
  --output json \
  --profile "$PROFILE" \
  --region "$REGION"
```

`CodeSha256` can help compare deployed ZIP code with a known artifact. Ensure that the hash comparison uses the expected encoding and artifact representation. For container-image functions, inspect the image-related metadata and ECR artifact digest rather than assuming the ZIP-oriented workflow applies.

For more detailed deployment procedures, use the dedicated deployment-package and container-image CLI documentation.

## Inspect Environment Variables Safely

Environment variables commonly hold non-secret configuration such as log levels, feature flags, table names, and downstream service endpoints.

Inspect selected configuration without displaying all variable values:

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Name:FunctionName,VariableNames:keys(Environment.Variables || `{}`)}' \
  --output json \
  --profile "$PROFILE" \
  --region "$REGION"
```

The query lists variable names rather than their values. If your CLI version or query environment does not accept this expression, retrieve the configuration and filter it locally using a controlled script.

Do not dump all environment variables into terminal recordings, CI logs, issue trackers, or support messages. Lambda encrypts environment variables at rest, but authorized principals may still be able to retrieve their values.

For credentials and other sensitive values, prefer AWS Secrets Manager or Systems Manager Parameter Store with narrowly scoped IAM permissions. Environment-variable encryption is not a substitute for access control or secret rotation.

## Inspect VPC Configuration

For functions configured to access private resources, inspect the VPC-related settings.

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{VpcConfig:VpcConfig,State:State,LastUpdateStatus:LastUpdateStatus}' \
  --output json \
  --profile "$PROFILE" \
  --region "$REGION"
```

Review:

- VPC ID.
- Subnet IDs.
- Security group IDs.
- VPC configuration status and related networking details returned by the API.

A successful VPC configuration update does not prove that a database, cache, or external endpoint is reachable. Connectivity also depends on routing, security groups, network ACLs, DNS, endpoint policies, and the availability of the destination service.

Lambda does not receive public internet access merely because it is configured with a public subnet. For outbound internet access from a VPC-connected function, the architecture must provide an appropriate egress path, such as NAT, or use suitable private service endpoints.

## Inspect Tags

Tags support ownership, cost allocation, environment classification, and automation.

Retrieve a function's ARN:

```bash
FUNCTION_ARN=$(aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query 'FunctionArn' \
  --output text \
  --profile "$PROFILE" \
  --region "$REGION")
```

List its tags:

```bash
aws lambda list-tags \
  --resource "$FUNCTION_ARN" \
  --profile "$PROFILE" \
  --region "$REGION"
```

Example tags might include:

| Tag | Example value |
|---|---|
| `Environment` | `production` |
| `Service` | `orders` |
| `Owner` | `backend-platform` |
| `CostCenter` | `engineering` |
| `ManagedBy` | `cloudformation` |

Tag values should follow an organizational convention. Never store secrets or personal data in tags.

## Update Function Configuration

The `update-function-configuration` command changes settings such as timeout, memory, environment variables, runtime, architecture, and VPC configuration.

Configuration changes can affect running workloads. Validate the proposed values, use the correct function qualifier when applicable, and verify the final state.

### Update timeout and memory

```bash
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --timeout 20 \
  --memory-size 1024 \
  --profile "$PROFILE" \
  --region "$REGION"
```

The command requests a timeout of 20 seconds and a memory allocation of 1024 MB.

Wait for the update:

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
  --query '{MemoryMB:MemorySize,TimeoutSeconds:Timeout,State:State,LastUpdateStatus:LastUpdateStatus}' \
  --output table \
  --profile "$PROFILE" \
  --region "$REGION"
```

Memory and timeout should be selected from observed workload behavior rather than copied from another function. More memory can provide more CPU and improve execution time, but it can also increase the configured compute price per unit of execution time.

### Update environment variables

The `--environment` option replaces the environment-variable map supplied to the API; it should not be treated as a patch operation that automatically preserves omitted keys.

For example, create a local JSON file named `environment.json`:

```json
{
  "Variables": {
    "APP_ENV": "staging",
    "LOG_LEVEL": "INFO",
    "ORDERS_TABLE": "orders-staging"
  }
}
```

Apply the complete intended variable set:

```bash
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --environment file://environment.json \
  --profile "$PROFILE" \
  --region "$REGION"
```

Wait for completion and verify the variable names and expected non-sensitive values.

Before updating an existing function, retrieve its current environment configuration through an approved, secure workflow and merge the intended changes. Otherwise, existing variables may be unintentionally removed.

Keep environment-specific values in deployment configuration rather than hardcoding production resource names into application code.

## Update Function Code

For ZIP-based functions, `update-function-code` deploys a new package.

```bash
aws lambda update-function-code \
  --function-name "$FUNCTION_NAME" \
  --zip-file fileb://function.zip \
  --profile "$PROFILE" \
  --region "$REGION"
```

This command modifies the function's deployed code. It does not automatically create a new published version.

Wait for the code update:

```bash
aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION"
```

Verify the deployment metadata:

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --query '{Arn:Configuration.FunctionArn,Version:Configuration.Version,CodeSha256:Configuration.CodeSha256,LastModified:Configuration.LastModified,LastUpdateStatus:Configuration.LastUpdateStatus}' \
  --output json \
  --profile "$PROFILE" \
  --region "$REGION"
```

For production, deploy an artifact produced by a controlled build pipeline, verify its provenance, and use versions and aliases for release management. Avoid manually packaging source code from an unreviewed working directory.

Container-image functions use a different deployment workflow involving an image in Amazon ECR. Do not use `--zip-file` for a function configured for container-image deployment.

## Wait for Updates and Inspect State

Lambda updates may be asynchronous. A successful API response can indicate that an update was accepted rather than that the function is already ready for the next operation.

Use the appropriate waiter:

```bash
aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION"
```

Then inspect the state:

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{State:State,StateReason:StateReason,StateReasonCode:StateReasonCode,LastUpdateStatus:LastUpdateStatus,LastUpdateStatusReason:LastUpdateStatusReason}' \
  --output json \
  --profile "$PROFILE" \
  --region "$REGION"
```

Investigate a failed update before retrying. Repeatedly issuing updates can obscure the original failure and introduce additional configuration changes.

## Delete a Lambda Function Safely

Deleting a function is destructive. It removes the function resource and can disrupt API integrations, event processing, scheduled jobs, or downstream workflows.

Before deletion:

- Verify the AWS account and Region.
- Identify aliases, published versions, event source mappings, and integrations that depend on the function.
- Confirm whether infrastructure as code owns the resource.
- Preserve required logs, deployment artifacts, and operational evidence.
- Confirm that the function is not receiving production traffic.

Inspect the target first:

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Arn:FunctionArn,State:State,Role:Role,LastModified:LastModified}' \
  --output json \
  --profile "$PROFILE" \
  --region "$REGION"
```

Delete only after the required approval and dependency checks:

```bash
aws lambda delete-function \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION"
```

Verify that the function no longer exists:

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --profile "$PROFILE" \
  --region "$REGION"
```

The final command should return a resource-not-found error when the function has been successfully removed. Do not interpret every error as proof of deletion; authentication, authorization, and endpoint failures can produce different errors.

If the function is managed by CloudFormation or AWS SAM, prefer deleting or updating the owning stack. Direct deletion can cause infrastructure drift and complicate subsequent deployments.

## Common Management Errors

| Symptom | Likely cause | Corrective action |
|---|---|---|
| Function not found | Wrong account, Region, name, or qualifier | Verify the active identity and function ARN |
| Access denied | Missing IAM permission or organizational restriction | Inspect the active identity and applicable policies |
| Update still in progress | Lambda has not completed a previous update | Wait for completion and inspect update status |
| Environment variables disappear | The update supplied an incomplete variable map | Restore the complete intended map and validate configuration |
| Function deploys but behaves unexpectedly | Wrong artifact, handler, alias, or environment configuration | Compare deployed metadata with the intended release |
| VPC function cannot reach a database | Network path, security group, DNS, or database configuration is incorrect | Test each network boundary and inspect VPC settings |
| Deletion disrupts an integration | Dependencies were not identified before removal | Inspect triggers, mappings, resource policies, and infrastructure ownership |

## Production Management Checklist

Use this checklist before changing a production function.

- [ ] Verify the AWS account, Region, profile, and function ARN.
- [ ] Confirm whether the target is an unqualified function, published version, or alias.
- [ ] Record the current runtime, handler, memory, timeout, architecture, role, and relevant configuration.
- [ ] Confirm the artifact or configuration change is reviewed and reproducible.
- [ ] Check execution-role permissions and invocation permissions separately.
- [ ] Assess downstream dependencies, concurrency requirements, and potential side effects.
- [ ] Wait for updates to complete and verify the resulting state.
- [ ] Run an appropriate smoke test and inspect logs and metrics.
- [ ] Ensure infrastructure-as-code definitions remain consistent with deployed resources.
- [ ] Document rollback steps before making a high-impact change.

## Key Takeaways

- Use `list-functions`, `get-function-configuration`, and `get-function` to inspect resources before modifying them.
- Verify the account, Region, function qualifier, and update status to avoid operating on the wrong deployment.
- Treat environment-variable updates as complete-map replacements and protect sensitive configuration.
- Use waiters and post-operation verification because accepted updates are not necessarily completed updates.
- Prefer infrastructure as code, controlled deployment artifacts, and explicit dependency checks for production function management.