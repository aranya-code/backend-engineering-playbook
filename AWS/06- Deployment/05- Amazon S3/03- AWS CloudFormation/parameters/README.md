# README

## Overview

This directory contains environment-specific CloudFormation parameter files for deploying the Amazon S3 static website infrastructure defined in `../templates/static-website-bucket.yaml`.

Each JSON file supplies deployment values for a specific environment while keeping the CloudFormation template reusable. This separates infrastructure logic from environment configuration and reduces the risk of maintaining multiple nearly identical templates.

| File | Environment | Purpose |
|---|---|---|
| `dev.json` | Development | Development deployment configuration |
| `staging.json` | Staging | Pre-production validation configuration |
| `production.json` | Production | Production deployment configuration |

The parameter files use the JSON array format accepted by AWS CloudFormation CLI operations such as `create-stack` and `update-stack` through `--parameters file://...`.

## Directory Structure

```text
parameters/
├── README.md
├── dev.json
├── staging.json
└── production.json
```

## Parameter Reference

The parameter keys must match the parameters declared in `static-website-bucket.yaml`.

| Parameter | Description | Example |
|---|---|---|
| `BucketName` | Globally unique S3 bucket name | `your-unique-production-static-website-bucket` |
| `Environment` | Deployment environment identifier | `production` |
| `DefaultRootObject` | Default object served by CloudFront | `index.html` |
| `PriceClass` | CloudFront edge-location price class | `PriceClass_100` |
| `EnableBucketVersioning` | Enables S3 bucket versioning | `true` |
| `EnableCloudFrontAccessLogging` | Enables CloudFront access logging | `false` |
| `LoggingBucketName` | S3 bucket receiving CloudFront access logs | Empty when logging is disabled |

### BucketName

S3 bucket names must be globally unique within the applicable AWS partition and comply with S3 naming requirements.

Replace the example value with an actual bucket name before deployment.

Use environment-specific names to avoid accidental resource sharing between development, staging, and production.

### Environment

Identifies the deployment environment and is commonly used for resource tags, naming, and operational identification.

Keep the values consistent across parameter files:

- `dev`
- `staging`
- `production`

### DefaultRootObject

Defines the default object CloudFront returns when a viewer requests the distribution root.

For a static website, this is normally:

```text
index.html
```

This setting does not automatically configure SPA routing or custom error responses.

### PriceClass

Controls which CloudFront edge locations are used to serve content.

| Value | Description |
|---|---|
| `PriceClass_100` | Lowest-cost supported edge-location set |
| `PriceClass_200` | Expanded edge-location coverage |
| `PriceClass_All` | All CloudFront edge locations |

Select a price class based on audience geography, latency requirements, and cost constraints.

### EnableBucketVersioning

Enables S3 object versioning.

Versioning provides recovery options for overwritten or deleted objects, but it can increase storage costs because previous object versions remain stored.

Production deployments should normally keep versioning enabled unless a documented requirement justifies otherwise.

### EnableCloudFrontAccessLogging

Controls whether CloudFront access logging is enabled.

When enabled, configure `LoggingBucketName` with a suitable logging bucket name and ensure the destination bucket has the required configuration and permissions.

When disabled, the logging bucket parameter can remain empty.

## Environment Configuration

### Development

`dev.json` provides development-specific values.

Typical characteristics:

- Isolated development bucket.
- Versioning enabled.
- Lower CloudFront price class.
- Access logging disabled unless required for testing.

### Staging

`staging.json` provides pre-production values.

Use staging to validate:

- CloudFormation changes.
- CloudFront behavior.
- Static website deployment.
- Cache configuration.
- Access-control and origin configuration.
- Release and rollback procedures.

Keep staging configuration as close to production as practical while preserving resource isolation.

### Production

`production.json` provides production-specific values.

Before deployment:

- Replace the example bucket name with a globally unique production bucket name.
- Confirm the target AWS account and Region.
- Review CloudFront price-class requirements.
- Confirm whether access logging is required.
- If logging is enabled, configure a valid logging destination and its required permissions.
- Review the proposed CloudFormation change set before execution.

Do not reuse development or staging bucket names in production.

## Parameter File Format

CloudFormation parameter files used with `--parameters file://...` must be JSON arrays.

Example:

```json
[
  {
    "ParameterKey": "BucketName",
    "ParameterValue": "your-unique-production-static-website-bucket"
  },
  {
    "ParameterKey": "Environment",
    "ParameterValue": "production"
  },
  {
    "ParameterKey": "DefaultRootObject",
    "ParameterValue": "index.html"
  },
  {
    "ParameterKey": "PriceClass",
    "ParameterValue": "PriceClass_100"
  },
  {
    "ParameterKey": "EnableBucketVersioning",
    "ParameterValue": "true"
  },
  {
    "ParameterKey": "EnableCloudFrontAccessLogging",
    "ParameterValue": "false"
  },
  {
    "ParameterKey": "LoggingBucketName",
    "ParameterValue": ""
  }
]
```

Important requirements:

- `ParameterKey` must exactly match a template parameter name.
- `ParameterValue` must be represented as a string.
- Boolean values must use `"true"` or `"false"`.
- Do not add comments; JSON does not support comments.
- Do not include credentials, access keys, or other secrets.
- Keep all required template parameters represented in the environment configuration.

## Deployment Workflow

Run deployment commands from the CloudFormation directory:

```bash
cd "06- Deployment/05- Amazon S3/03- AWS CloudFormation"
```

### Validate JSON

Validate the selected parameter file before deployment:

```bash
python3 -m json.tool parameters/production.json
```

Validate the CloudFormation template:

```bash
aws cloudformation validate-template \
  --template-body file://templates/static-website-bucket.yaml \
  --region ap-south-1
```

### Create a Stack

```bash
aws cloudformation create-stack \
  --stack-name s3-static-website-production \
  --template-body file://templates/static-website-bucket.yaml \
  --parameters file://parameters/production.json \
  --region ap-south-1
```

### Update a Stack

```bash
aws cloudformation update-stack \
  --stack-name s3-static-website-production \
  --template-body file://templates/static-website-bucket.yaml \
  --parameters file://parameters/production.json \
  --region ap-south-1
```

For production changes, prefer the change-set workflow implemented by `scripts/deploy-stack.sh`. Review the proposed resource changes before executing them.

### Monitor Deployment

```bash
aws cloudformation describe-stacks \
  --stack-name s3-static-website-production \
  --region ap-south-1
```

Inspect recent stack events:

```bash
aws cloudformation describe-stack-events \
  --stack-name s3-static-website-production \
  --region ap-south-1 \
  --max-items 20
```

### Inspect Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name s3-static-website-production \
  --region ap-south-1 \
  --query "Stacks[0].Outputs" \
  --output table
```

## Validation and Configuration Management

Treat parameter files as version-controlled deployment configuration.

Recommended practices:

- Keep one parameter file per environment.
- Review production parameter changes through pull requests.
- Validate JSON syntax in CI.
- Validate parameter names and values against the CloudFormation template.
- Use separate AWS accounts for production and non-production environments where practical.
- Keep bucket names explicit and environment-specific.
- Use CloudFormation change sets for production updates.
- Avoid manual console changes that create infrastructure drift.
- Store secrets in AWS Secrets Manager or Systems Manager Parameter Store rather than parameter files.
- Restrict production deployment permissions to approved CI/CD roles or authorized operators.

A valid JSON file does not guarantee that CloudFormation will accept its values. Template constraints, AWS resource requirements, account permissions, and resource-name availability are evaluated separately.

## Common Mistakes

| Mistake | Impact | Prevention |
|---|---|---|
| Reusing an S3 bucket name | Deployment failure or resource collision | Use globally unique environment-specific names |
| Incorrect `ParameterKey` | CloudFormation parameter validation failure | Match template parameter names exactly |
| Using JSON comments | JSON parsing failure | Keep parameter files valid JSON |
| Supplying booleans without string values | Parameter parsing or type mismatch | Use `"true"` and `"false"` |
| Enabling logging without a valid destination | Deployment failure or missing logs | Configure and validate the logging bucket |
| Deploying production values to a non-production account | Incorrect resource placement | Verify account identity and deployment role |
| Updating production without a change set | Unexpected infrastructure changes | Review and approve changes before execution |
| Storing credentials in parameter files | Secret exposure through Git | Use IAM roles and managed secret stores |
| Assuming JSON validation verifies CloudFormation compatibility | Deployment-time failures | Validate the template and inspect change sets |

## Operational Considerations

### Production Change Management

For production deployments:

1. Review the parameter-file diff.
2. Validate JSON syntax and the CloudFormation template.
3. Verify the AWS account, Region, and deployment role.
4. Create a CloudFormation change set.
5. Review resource additions, modifications, replacements, and deletions.
6. Obtain the required approval.
7. Execute the change set.
8. Monitor stack events until the deployment reaches a stable state.
9. Verify stack outputs and the deployed S3 and CloudFront configuration.

### Configuration Drift

CloudFormation parameter files describe the desired configuration used during deployment. They do not automatically detect manual changes made directly to AWS resources.

Use the drift-detection workflow in:

```text
scripts/detect-drift.sh
```

Investigate drift before applying further production changes. Reconcile the template and actual resource configuration deliberately rather than overwriting changes without review.

### Cost and Security

- CloudFront price-class selection affects delivery cost and geographic coverage.
- S3 versioning increases storage consumption when previous versions accumulate.
- CloudFront access logging creates additional S3 storage and request costs.
- Keep the S3 origin private and use CloudFront Origin Access Control where configured by the template.
- Apply least-privilege deployment permissions.
- Do not commit credentials or sensitive production configuration to the repository.

## Key Takeaways

- Environment-specific JSON parameter files keep CloudFormation templates reusable and deployment configuration isolated.
- Parameter keys and values must remain compatible with `static-website-bucket.yaml`.
- Production deployments should use unique resource names, verified account and Region settings, and reviewed change sets.
- JSON validation is necessary but does not replace CloudFormation validation or deployment-time verification.
- Protect parameter files from secrets and manage infrastructure drift through controlled change management.