# 08- Environment Configuration and Secrets

## Overview

AWS Lambda functions require configuration to connect application code with the resources and services they depend on. This configuration includes environment-specific values, database connection details, feature flags, API endpoints, and credentials used to access external systems.

A production application must distinguish between **configuration**, **secrets**, and **permissions**:

- **Configuration** controls application behavior, such as log levels, table names, and feature flags.
- **Secrets** contain sensitive values, such as database passwords, API tokens, and third-party credentials.
- **IAM permissions** determine which AWS resources the function can access.

These concerns should be managed separately. Environment variables are convenient for non-sensitive configuration, Secrets Manager and Systems Manager Parameter Store provide managed storage for sensitive or operational configuration, and IAM policies control access.

For a Python backend, a good configuration strategy should support multiple environments without requiring source-code changes, avoid exposing credentials, handle secret rotation, and remain compatible with Lambda's execution-environment reuse model.

## Configuration Sources

Lambda applications can obtain configuration from several sources. Each has different security, operational, and performance characteristics.

| Source | Appropriate use | Advantages | Limitations |
|---|---|---|---|
| Lambda environment variables | Non-sensitive runtime settings | Simple, available to the handler | Configuration changes require function updates; values have a size limit |
| AWS Secrets Manager | Database credentials, API tokens, secrets requiring managed rotation | Secret lifecycle and rotation capabilities | Additional service cost and retrieval latency |
| AWS Systems Manager Parameter Store | Application settings and parameters, including encrypted `SecureString` values | Hierarchical naming and convenient configuration management | Standard and advanced parameter capabilities differ; secure retrieval requires IAM permissions |
| AWS AppConfig | Managed application configuration and feature flags requiring controlled rollout | Supports configuration validation and gradual deployment workflows | Requires an additional configuration-management integration |
| IAM execution role | AWS service access permissions | Avoids distributing long-lived AWS credentials | Applies to AWS authorization, not arbitrary external credentials |
| Deployment-time configuration | Environment-specific resource identifiers and settings | Integrates configuration with CI/CD and IaC | Incorrect deployment configuration can affect production behavior |

Choose a source according to how sensitive the value is, how frequently it changes, whether rotation is required, and whether runtime updates must become effective without redeploying the function.

## Lambda Environment Variables

Environment variables provide a straightforward way to inject configuration into a Lambda execution environment.

Common examples include:

- `LOG_LEVEL`
- `ORDERS_TABLE_NAME`
- `REDIS_ENDPOINT`
- `EXTERNAL_API_BASE_URL`
- `FEATURE_ENABLE_NEW_CHECKOUT`

Environment variables are configured on the Lambda function and are available to the runtime when the function executes.

### Configure environment variables

Using AWS CLI, update the function configuration:

```bash
aws lambda update-function-configuration \
  --function-name order-processor \
  --environment 'Variables={LOG_LEVEL=INFO,ORDERS_TABLE_NAME=orders-prod}' \
  --region ap-south-1
```

**Important:** The `--environment` option replaces the function's existing environment-variable map; it does not merge the supplied keys with the existing map. Include all required variables when updating the configuration.

This is a state-changing operation. Inspect the existing configuration first and verify the result afterward.

Read the current environment-variable configuration:

```bash
aws lambda get-function-configuration \
  --function-name order-processor \
  --region ap-south-1 \
  --query 'Environment.Variables' \
  --output json
```

Avoid printing environment variables indiscriminately in production logs or CI/CD output because they may contain sensitive values.

### Read configuration in Python

Python's `os.environ` provides access to environment variables.

```python
import os


def get_required_setting(name: str) -> str:
    value = os.environ.get(name)

    if not value:
        raise RuntimeError(
            f"Required environment variable {name} is missing or empty"
        )

    return value


ORDERS_TABLE_NAME = get_required_setting("ORDERS_TABLE_NAME")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
```

This pattern validates required configuration during module initialization, making configuration errors visible before the function starts processing requests.

Module-level configuration is generally appropriate for values that remain stable during the execution environment's lifetime. A configuration change that updates the Lambda function does not guarantee that every existing execution environment immediately observes the new value. Lambda manages environment replacement and reuse as part of its execution model.

For secrets that must rotate without waiting for function configuration changes, use an appropriate managed secret retrieval strategy.

### Configuration validation

Fail fast when required configuration is missing or invalid.

For example, validate URLs, integer timeouts, and enumerated settings rather than assuming environment-variable values are correct.

```python
import os
from urllib.parse import urlparse


def load_config() -> dict[str, str]:
    api_url = os.environ.get("EXTERNAL_API_BASE_URL", "").strip()
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    parsed_url = urlparse(api_url)

    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise RuntimeError("EXTERNAL_API_BASE_URL must be a valid HTTP(S) URL")

    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise RuntimeError("LOG_LEVEL is invalid")

    return {
        "external_api_base_url": api_url.rstrip("/"),
        "log_level": log_level,
    }
```

This example demonstrates basic validation. Production applications should define configuration types explicitly and avoid embedding secrets in validation errors.

## Environment-Specific Configuration

Development, staging, and production should use separate configuration values and appropriate resource boundaries.

For example:

| Setting | Development | Staging | Production |
|---|---|---|---|
| `LOG_LEVEL` | `DEBUG` | `INFO` | `INFO` or `WARNING` |
| DynamoDB table | `orders-dev` | `orders-staging` | `orders-prod` |
| Secret identifier | Development secret | Staging secret | Production secret |
| API endpoint | Test endpoint | Staging endpoint | Production endpoint |
| IAM permissions | Development resources | Staging resources | Production resources only |

The exact values should be supplied through IaC, deployment configuration, or an approved configuration-management system.

Avoid selecting production resources through hardcoded conditional logic in application code. Keep environment differences explicit and reviewable.

### Infrastructure as Code example

A SAM template can inject non-sensitive configuration:

```yaml
Parameters:
  EnvironmentName:
    Type: String
    AllowedValues:
      - dev
      - staging
      - prod

Resources:
  OrderFunction:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: python3.12
      Handler: app.lambda_handler
      CodeUri: src/
      Environment:
        Variables:
          ENVIRONMENT: !Ref EnvironmentName
          LOG_LEVEL: INFO
          ORDERS_TABLE_NAME: !Sub "orders-${EnvironmentName}"
```

This is a function-configuration fragment intended to illustrate environment-specific settings. A deployable application must also define or reference its execution role and required resources, and the table name must match an existing or separately managed table.

Do not use a single production-capable role across all environments merely because the function code is identical.

## Secrets Management

Secrets differ from ordinary configuration because their disclosure can allow unauthorized access to databases, APIs, or other systems.

Typical secrets include:

- Database usernames and passwords.
- Third-party API keys.
- Private service credentials.
- Credentials for systems that do not support IAM-based authentication.

Whenever possible, avoid static credentials altogether. For example, use IAM authorization for AWS services and supported database authentication mechanisms instead of storing long-lived access keys.

When a secret is necessary, use a managed secret store and grant access through the Lambda execution role.

### AWS Secrets Manager

Secrets Manager is appropriate when a workload needs centralized secret storage, access control, auditability, and managed rotation capabilities.

A secret can contain a JSON document:

```json
{
  "username": "app_user",
  "password": "managed-secret-value"
}
```

The JSON structure is an application-defined convention, not a requirement imposed on all Secrets Manager secrets.

Store only the secret identifier in Lambda configuration, for example:

```text
DATABASE_SECRET_ARN=arn:aws:secretsmanager:ap-south-1:123456789012:secret:orders/database-AbCdEf
```

The execution role should have permission to retrieve only the required secret. If the secret uses a customer-managed KMS key, the role may also need appropriate KMS permissions.

### Retrieve a secret in Python

Install and package `boto3` explicitly if the application relies on a particular SDK version. Do not assume that the SDK version available in the managed runtime will always match the version tested locally.

```python
import json
import os
from functools import lru_cache

import boto3


secrets_client = boto3.client("secretsmanager")


@lru_cache(maxsize=32)
def get_secret(secret_id: str) -> dict[str, str]:
    response = secrets_client.get_secret_value(
        SecretId=secret_id
    )

    secret_string = response.get("SecretString")

    if not secret_string:
        raise RuntimeError("Expected a text-based secret")

    secret = json.loads(secret_string)

    if not isinstance(secret, dict):
        raise RuntimeError("Secret must contain a JSON object")

    return secret


def lambda_handler(event, context):
    secret_id = os.environ["DATABASE_SECRET_ARN"]
    database_secret = get_secret(secret_id)

    username = database_secret["username"]
    password = database_secret["password"]

    # Use these values to initialize or refresh a database connection.
    # Never log the credentials.

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Configuration loaded"}),
    }
```

This example demonstrates retrieval and caching, not a complete database connection implementation.

The cache reduces repeated Secrets Manager calls, but it also means the execution environment may continue using a previously retrieved secret after rotation. A production application must implement a refresh strategy appropriate to its rotation requirements.

Avoid placing secret values in global application configuration that gets serialized, logged, or included in diagnostic output.

### Secret caching trade-offs

Lambda may reuse an execution environment across multiple invocations. Caching secrets can reduce latency and service cost, but cached values are not automatically refreshed simply because the underlying secret changes.

| Strategy | Advantages | Limitations |
|---|---|---|
| Retrieve on every invocation | Fresh retrieval on each request | Adds latency and service calls; can increase cost |
| Cache for the execution environment's lifetime | Low retrieval overhead | May retain stale credentials |
| Cache with a defined TTL | Balances performance and freshness | Requires refresh and concurrency handling |
| Use a managed caching integration | Can simplify retrieval and caching behavior | Adds a component to configure, secure, and operate |

Select the strategy according to secret rotation frequency, request volume, latency requirements, and the impact of stale credentials.

If a database password rotates while a Lambda environment retains an old connection pool, the application may continue to fail even after retrieving the new secret. Refreshing the secret and recreating affected connections may both be necessary.

## AWS Systems Manager Parameter Store

Parameter Store provides centralized storage for configuration values. It supports ordinary `String` and `StringList` parameters, along with encrypted `SecureString` parameters.

A common naming convention separates parameters by application and environment:

```text
/order-service/dev/log-level
/order-service/staging/orders-table
/order-service/prod/orders-table
/order-service/prod/database-secret-arn
```

The hierarchy is an organizational convention. Access control still depends on IAM permissions and, for encrypted parameters, the relevant KMS configuration.

### Create a parameter

The following command creates or updates a parameter and therefore changes AWS state:

```bash
aws ssm put-parameter \
  --name "/order-service/prod/log-level" \
  --type String \
  --value "INFO" \
  --overwrite \
  --region ap-south-1
```

Use `--overwrite` only when replacing an existing parameter is intended.

For sensitive values, use `SecureString`:

```bash
aws ssm put-parameter \
  --name "/order-service/prod/external-api-token" \
  --type SecureString \
  --value "REPLACE_WITH_SECRET_VALUE" \
  --region ap-south-1
```

Avoid placing real secrets directly in shell commands, scripts, terminal history, or CI logs. Prefer controlled provisioning mechanisms that do not expose the secret value.

### Retrieve a parameter

For an ordinary string parameter:

```bash
aws ssm get-parameter \
  --name "/order-service/prod/log-level" \
  --region ap-south-1 \
  --query 'Parameter.Value' \
  --output text
```

For an encrypted parameter:

```bash
aws ssm get-parameter \
  --name "/order-service/prod/external-api-token" \
  --with-decryption \
  --region ap-south-1 \
  --query 'Parameter.Value' \
  --output text
```

These retrieval commands are read-only but may expose sensitive values in terminal output. Do not use them casually in shared terminals or automated logs.

### Choosing Parameter Store or Secrets Manager

| Requirement | Typical choice |
|---|---|
| Ordinary application configuration | Parameter Store `String` |
| Encrypted configuration value | Parameter Store `SecureString` |
| Database credentials requiring managed rotation | Secrets Manager |
| Third-party API credentials with a defined secret lifecycle | Secrets Manager |
| Hierarchical operational parameters | Parameter Store |
| Secret lifecycle features and rotation workflows | Secrets Manager |

The services overlap in some capabilities. Choose based on the required lifecycle, rotation model, security controls, retrieval patterns, and cost rather than treating one service as universally superior.

## IAM Permissions for Configuration and Secrets

A Lambda function accesses AWS resources using its execution role. The role should grant only the required actions against the intended resource ARNs.

For a function retrieving one Secrets Manager secret, a policy statement can follow this pattern:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:ap-south-1:123456789012:secret:orders/database-AbCdEf"
    }
  ]
}
```

Replace the example ARN with the actual secret ARN. Secret ARNs can include generated suffixes, so verify the exact identifier.

Avoid policies such as:

```json
{
  "Effect": "Allow",
  "Action": "secretsmanager:*",
  "Resource": "*"
}
```

This grants unnecessarily broad access and increases the impact of a compromised function.

For Parameter Store, the function generally needs `ssm:GetParameter` or another narrowly selected read action for the required parameters. `SecureString` decryption also requires the appropriate KMS authorization when the encryption configuration requires it.

Use separate policies for execution access and deployment access. The CI/CD role provisions or updates resources; the Lambda execution role reads the configuration required while the application runs.

## Environment Variable Encryption

Lambda encrypts environment variables at rest using AWS KMS. The Lambda service handles encryption and decryption for the configured function.

You can use a customer-managed KMS key when additional control over key policy, auditing, or organizational key-management requirements is necessary.

However, encryption at rest does not make environment variables an ideal secret-management system. Authorized principals and application code may still access their plaintext values at runtime, and configuration can accidentally be exposed through logs or diagnostic output.

For sensitive credentials:

- Prefer a managed secret store.
- Restrict access to configuration-management APIs.
- Use customer-managed KMS keys when required by the security model.
- Avoid logging environment variables.
- Audit changes to function configuration and secret policies.
- Keep secrets out of source control and deployment artifacts.

## Configuration Changes and Execution Environments

Lambda separates function configuration from the handler's application logic, but configuration updates can affect execution environments and deployment behavior.

When an environment variable or other function setting changes, Lambda applies the new configuration through its managed update process. The service may replace execution environments as necessary; applications should not rely on a specific reuse or replacement schedule.

This matters when configuration includes:

- Database endpoints and credentials.
- Connection pool sizes.
- Feature flags.
- External API URLs.
- Timeout or retry behavior.
- Runtime initialization settings.

For example, changing a database endpoint does not guarantee that an application with module-level connection objects will immediately stop using existing connections. Design initialization and connection management so stale resources can be detected and recreated safely.

For feature flags requiring controlled rollout, validation, or runtime refresh, consider a dedicated configuration service such as AWS AppConfig instead of treating Lambda environment variables as a dynamic configuration database.

## Secure Configuration in GitHub Actions

CI/CD pipelines should not store production secrets in source files or embed them into deployment packages.

Prefer OIDC-based AWS authentication for deployment operations. This removes the need to maintain long-lived AWS access keys in GitHub secrets.

When a workflow needs a secret for an external system, use an approved GitHub secret or retrieve the value from an authorized secret store. Limit which workflows and environments can access it.

A workflow should pass secret references or non-sensitive identifiers into deployment configuration whenever possible, rather than copying plaintext secret values into templates.

For example, a workflow may deploy a Lambda function with a secret ARN as a configuration value:

```yaml
- name: Deploy Lambda configuration
  run: |
    aws lambda update-function-configuration \
      --function-name order-processor \
      --environment "Variables={DATABASE_SECRET_ARN=${{ vars.DATABASE_SECRET_ARN }},LOG_LEVEL=INFO}" \
      --region ap-south-1
```

This example is illustrative and requires the existing environment-variable map to be preserved in full. It also assumes `DATABASE_SECRET_ARN` is a non-sensitive GitHub environment variable.

Do not interpolate untrusted input directly into shell commands. Prefer carefully quoted environment variables, validate inputs, and use reviewed deployment scripts for complex configuration changes. Where possible, manage the full environment-variable map through IaC rather than ad hoc CLI updates.

## Networking Considerations for Secret Retrieval

A Lambda function in a VPC may need network access to retrieve secrets or parameters.

For a VPC-connected function, verify:

- Subnet routing and DNS configuration.
- NAT or other appropriate outbound connectivity when using public service endpoints.
- VPC endpoints where supported and appropriate.
- Endpoint policies and IAM permissions.
- Security group and network ACL behavior.
- KMS access requirements for encrypted values.

A Lambda function's execution role may authorize a Secrets Manager request while network connectivity still prevents the request from succeeding. IAM authorization and network reachability are separate concerns.

Use VPC endpoints where they fit the architecture and security requirements, but account for endpoint configuration, policy restrictions, availability, and cost.

## Failure Handling and Troubleshooting

Configuration and secret failures should be diagnosed separately from business-logic errors.

| Symptom | Possible cause | Verification | Corrective action |
|---|---|---|---|
| Missing environment variable | Incorrect deployment configuration | Inspect the specific variable name in function configuration | Update the environment map through the approved deployment process |
| `AccessDeniedException` retrieving a secret | Execution role lacks permission or a resource policy denies access | Inspect the role policy, secret resource policy, and KMS policy where relevant | Grant only the required access |
| `ResourceNotFoundException` | Incorrect secret or parameter identifier, account, or Region | Verify the exact identifier and target Region | Correct the configuration reference |
| Secret retrieval timeout | VPC connectivity, DNS, endpoint, or outbound routing problem | Inspect networking and endpoint configuration | Restore the required network path |
| `DecryptionFailure` | KMS policy, key state, or ciphertext configuration issue | Inspect KMS permissions and key configuration | Correct the relevant authorization or encryption setup |
| Authentication failures after rotation | Cached credentials or existing connections are stale | Compare secret version, connection state, and rotation timeline | Refresh the secret and recreate affected connections |
| Configuration update unexpectedly removes variables | CLI update replaced the environment-variable map | Inspect the current environment map | Restore the complete intended configuration |
| Sensitive values appear in logs | Debugging or exception handling exposes credentials | Review logging statements and log access | Remove secret output and restrict log access |

Use a consistent diagnostic process:

1. Identify the exact setting or secret the function needs.
2. Confirm that the configured identifier is correct.
3. Verify the target account and Region.
4. Check execution-role and resource-policy permissions.
5. Validate KMS authorization where applicable.
6. Check network connectivity and service endpoints.
7. Confirm cache freshness and connection state.
8. Verify the corrective change through a controlled test.

Do not include plaintext secret values in diagnostic reports or support tickets.

## Operational Best Practices

- Keep non-sensitive configuration separate from credentials.
- Validate required settings during initialization or controlled application startup.
- Use separate resources and secret identifiers for development, staging, and production.
- Prefer IAM-based access over static AWS credentials.
- Store secrets in a managed service with appropriate access controls and lifecycle management.
- Grant access to specific secrets and parameters instead of using wildcard resource permissions.
- Cache configuration and secrets deliberately, with an explicit refresh strategy.
- Design connection pools to recover from stale credentials and endpoint changes.
- Manage configuration through IaC or an approved deployment mechanism.
- Monitor access failures, secret retrieval latency, and configuration-related errors.
- Avoid logging secret values, full environment maps, or sensitive exception details.
- Document secret ownership, rotation requirements, recovery procedures, and expected application behavior during rotation.

## Production Readiness Checklist

Before deploying a Lambda function that uses environment configuration or secrets, verify the following:

- [ ] Required environment variables are documented and validated.
- [ ] Non-sensitive configuration is separated from secret values.
- [ ] Development, staging, and production use appropriate configuration boundaries.
- [ ] Secrets are stored in Secrets Manager or Parameter Store where appropriate.
- [ ] The execution role has only the permissions required for the intended configuration resources.
- [ ] KMS authorization is correct for encrypted values.
- [ ] VPC networking permits access to required AWS services.
- [ ] Secret caching and rotation behavior have been tested.
- [ ] Database connections can recover from stale credentials.
- [ ] Configuration updates preserve all required environment variables.
- [ ] CI/CD workflows avoid exposing secrets in logs and deployment artifacts.
- [ ] Monitoring and recovery procedures cover configuration and secret retrieval failures.

## Key Takeaways

- Use Lambda environment variables for non-sensitive runtime configuration, and use managed secret stores for credentials requiring stronger lifecycle and access controls.
- Prefer IAM-based AWS service access over static credentials, and grant the execution role narrowly scoped permissions.
- Treat secret caching and rotation as an explicit design problem because reused execution environments may retain stale values.
- Manage environment-specific configuration through reviewed IaC or deployment workflows, preserving the complete intended configuration during updates.
- Diagnose configuration failures across identifiers, IAM, KMS, networking, caching, and connection state without exposing plaintext secrets.