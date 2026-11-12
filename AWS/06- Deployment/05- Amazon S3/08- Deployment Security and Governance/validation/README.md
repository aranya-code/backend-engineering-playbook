# README

## Overview

This directory contains Python validation utilities for checking baseline security and governance controls on Amazon S3 buckets.

The scripts are designed for local execution, CI/CD validation, and periodic security assessments. They inspect bucket configuration through the AWS SDK for Python (Boto3) and report compliance findings without modifying AWS resources.

The validation utilities currently cover:

| Script | Responsibility |
|---|---|
| `check_public_access.py` | Checks bucket-level Block Public Access configuration and potential public bucket-policy exposure. |
| `check_encryption.py` | Validates default server-side encryption configuration and optional KMS requirements. |
| `check_versioning.py` | Checks bucket versioning status and optional MFA Delete requirements. |
| `check_required_tags.py` | Validates the presence of required bucket tag keys. |

These checks provide configuration-level validation. They are not a complete AWS security assessment or a replacement for AWS IAM Access Analyzer, AWS Config, or dedicated security posture management tools.

## Directory Structure

```text
validation/
├── README.md
├── check_public_access.py
├── check_encryption.py
├── check_versioning.py
└── check_required_tags.py
```

## Prerequisites

- Python 3.10 or later.
- An AWS account with S3 buckets to inspect.
- AWS CLI configured with an appropriate profile or execution role.
- Boto3 installed.
- IAM permissions for the checks being executed.

Install the dependency:

```bash
python -m pip install boto3
```

Use an isolated virtual environment for local development:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

## AWS Credentials and Permissions

The scripts use Boto3's standard credential provider chain. They do not require AWS access keys to be embedded in source code.

Supported credential sources include:

- IAM roles attached to EC2 instances.
- ECS task roles.
- Lambda execution roles.
- EKS workload identity configurations.
- AWS IAM Identity Center profiles.
- Environment-based credentials for controlled local development.
- Shared AWS CLI credential profiles.

For local execution with a named profile:

```powershell
$env:AWS_PROFILE = "development"
```

For Linux or macOS:

```bash
export AWS_PROFILE=development
```

### Required IAM Permissions

Grant only the permissions needed by the selected validation scripts.

| Operation | IAM permission |
|---|---|
| List buckets | `s3:ListAllMyBuckets` |
| Inspect bucket public-access block | `s3:GetBucketPublicAccessBlock` |
| Inspect bucket policy | `s3:GetBucketPolicy` |
| Inspect default encryption | `s3:GetEncryptionConfiguration` |
| Inspect versioning | `s3:GetBucketVersioning` |
| Inspect bucket tags | `s3:GetBucketTagging` |

When bucket names are explicitly supplied through `--bucket`, the scripts do not need `s3:ListAllMyBuckets`.

An example read-only IAM policy for running all four checks against a specific bucket is:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InspectS3BucketSecurityConfiguration",
      "Effect": "Allow",
      "Action": [
        "s3:GetBucketPublicAccessBlock",
        "s3:GetBucketPolicy",
        "s3:GetEncryptionConfiguration",
        "s3:GetBucketVersioning",
        "s3:GetBucketTagging"
      ],
      "Resource": "arn:aws:s3:::example-production-bucket"
    }
  ]
}
```

To inspect all buckets without supplying names, add:

```json
{
  "Sid": "ListS3Buckets",
  "Effect": "Allow",
  "Action": "s3:ListAllMyBuckets",
  "Resource": "*"
}
```

The policy is an example. Adapt its resource scope and permissions to the actual account and execution environment.

## Running the Validation Scripts

Run scripts from this directory.

### Public Access Validation

Check bucket-level public-access controls and potential public bucket-policy exposure:

```bash
python check_public_access.py --bucket example-production-bucket
```

Inspect multiple buckets:

```bash
python check_public_access.py \
  --bucket example-production-bucket \
  --bucket example-staging-bucket
```

Enable JSON output:

```bash
python check_public_access.py \
  --bucket example-production-bucket \
  --json
```

Enable verbose logging:

```bash
python check_public_access.py \
  --bucket example-production-bucket \
  --verbose
```

The script checks the four bucket-level Block Public Access settings and inspects the bucket policy for wildcard principals.

Its policy inspection is a conservative static check. A wildcard principal alone does not establish the effective accessibility of every object. Policy actions, resources, conditions, identity policies, access points, and other applicable controls must also be considered.

### Encryption Validation

Check whether default server-side encryption is configured:

```bash
python check_encryption.py --bucket example-production-bucket
```

Require SSE-S3:

```bash
python check_encryption.py \
  --bucket example-production-bucket \
  --algorithm AES256
```

Require SSE-KMS:

```bash
python check_encryption.py \
  --bucket example-production-bucket \
  --algorithm aws:kms
```

Require a specific KMS key:

```bash
python check_encryption.py \
  --bucket example-production-bucket \
  --algorithm aws:kms \
  --kms-key-id arn:aws:kms:ap-south-1:123456789012:key/example-key-id
```

Require S3 Bucket Key for KMS encryption rules:

```bash
python check_encryption.py \
  --bucket example-production-bucket \
  --algorithm aws:kms \
  --require-bucket-key
```

The check validates the bucket's default encryption configuration. It does not independently inspect every existing object or prove that all KMS permissions and key policies are correct.

### Versioning Validation

Require bucket versioning to be enabled:

```bash
python check_versioning.py --bucket example-production-bucket
```

Inspect the configuration without requiring versioning to be enabled:

```bash
python check_versioning.py \
  --bucket example-production-bucket \
  --allow-disabled
```

Require MFA Delete:

```bash
python check_versioning.py \
  --bucket example-production-bucket \
  --require-mfa-delete
```

MFA Delete is a separate control from versioning. The script inspects its configured status but does not enable or modify it.

### Required Tag Validation

Run the default required-tag check:

```bash
python check_required_tags.py \
  --bucket example-production-bucket
```

The default required keys are:

- `Environment`
- `Owner`
- `Project`
- `CostCenter`

Provide a custom set of required tag keys:

```bash
python check_required_tags.py \
  --bucket example-production-bucket \
  --required-tags Environment,Owner,Application
```

Repeat the option to provide additional required keys:

```bash
python check_required_tags.py \
  --bucket example-production-bucket \
  --required-tags Environment,Owner \
  --required-tags Project,CostCenter
```

The script validates tag-key presence. It does not validate allowed values, ownership correctness, cost allocation activation, or organizational tagging policies.

## Output and Exit Codes

The scripts provide human-readable findings by default. Use `--json` when integrating them with automated pipelines or other reporting systems.

The common exit-code convention is:

| Exit code | Meaning |
|---|---|
| `0` | All evaluated checks passed, or no buckets were found. |
| `1` | One or more compliance checks failed. |
| `2` | An inspection or configuration error prevented reliable validation. |

A failed inspection must not be interpreted as a passed security check.

Example JSON output:

```json
[
  {
    "bucket": "example-production-bucket",
    "check": "required_tags",
    "passed": true,
    "severity": "INFO",
    "message": "All required tag keys are present."
  }
]
```

Exact findings and messages depend on the script and the bucket configuration.

## CI/CD Integration

Run validation scripts as part of an infrastructure validation stage after the target bucket has been provisioned.

Example GitHub Actions job:

```yaml
name: S3 Security Validation

on:
  workflow_dispatch:
  push:
    branches:
      - main

permissions:
  contents: read
  id-token: write

jobs:
  validate-s3:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_VALIDATION_ROLE_ARN }}
          aws-region: ap-south-1

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install boto3

      - name: Validate public access
        working-directory: 06- Deployment/05- Amazon S3/08- Deployment Security and Governance/validation
        run: |
          python check_public_access.py \
            --bucket "${{ vars.S3_BUCKET_NAME }}"

      - name: Validate encryption
        working-directory: 06- Deployment/05- Amazon S3/08- Deployment Security and Governance/validation
        run: |
          python check_encryption.py \
            --bucket "${{ vars.S3_BUCKET_NAME }}"

      - name: Validate versioning
        working-directory: 06- Deployment/05- Amazon S3/08- Deployment Security and Governance/validation
        run: |
          python check_versioning.py \
            --bucket "${{ vars.S3_BUCKET_NAME }}"

      - name: Validate required tags
        working-directory: 06- Deployment/05- Amazon S3/08- Deployment Security and Governance/validation
        run: |
          python check_required_tags.py \
            --bucket "${{ vars.S3_BUCKET_NAME }}"
```

Configure the GitHub OIDC trust relationship and IAM role permissions separately. The workflow assumes that the role can access the target bucket's configuration.

For production pipelines:

- Use OIDC federation and short-lived credentials.
- Restrict role assumption to the intended repository, branch, or deployment environment.
- Keep the validation role read-only.
- Store non-secret environment configuration in GitHub variables.
- Avoid placing AWS access keys in workflow files.
- Run checks against the intended account and Region.
- Preserve validation output as CI artifacts when audit evidence is required.

## Operational Considerations

### Validation Scope

These scripts inspect selected bucket-level configuration. They do not provide a complete security posture assessment.

| Control area | Current validation scope | Additional controls to consider |
|---|---|---|
| Public access | Bucket Block Public Access and static bucket-policy inspection | Account-level settings, access points, IAM policies, Access Analyzer |
| Encryption | Default encryption rules and optional KMS key requirements | Object-level encryption state, KMS key policy, grants, key availability |
| Versioning | Bucket versioning and optional MFA Delete status | Replication, lifecycle rules, recovery testing, noncurrent-version retention |
| Tags | Required tag-key presence | Allowed values, organization-wide policies, cost allocation configuration |

### Error Handling

A validation result is useful only when the script can successfully inspect the target resource.

Common causes of inspection errors include:

- Missing IAM permissions.
- Incorrect bucket names.
- Invalid AWS credentials.
- Expired sessions.
- Network connectivity failures.
- AWS service errors.
- Incorrect Region or account assumptions.

Investigate errors before treating a bucket as compliant.

### Account and Region Scope

S3 buckets belong to an AWS account and are created in a specific Region. A validation run should record the account and execution context when used for organization-wide governance.

For multi-account environments, execute the checks through explicitly authorized roles in each target account. Do not assume that a successful check in one account covers other accounts.

### Non-Destructive Execution

The scripts in this directory are intended to inspect configuration only.

They do not:

- Modify bucket policies.
- Change Block Public Access settings.
- Enable or disable encryption.
- Enable versioning or MFA Delete.
- Add, update, or remove bucket tags.
- Delete objects or buckets.

Remediation should be performed through reviewed infrastructure-as-code changes or a separately authorized operational workflow.

## Testing and Verification

Use mocked Boto3 clients for unit tests. This allows validation logic to be tested without making AWS API calls.

Recommended test cases include:

| Script | Test cases |
|---|---|
| `check_public_access.py` | All public-access flags enabled, missing configuration, wildcard principals, missing bucket policy, access denied |
| `check_encryption.py` | SSE-S3, SSE-KMS, DSSE-KMS, missing encryption configuration, unexpected KMS key, Bucket Key disabled |
| `check_versioning.py` | Enabled, suspended, unconfigured, MFA Delete enabled, MFA Delete disabled |
| `check_required_tags.py` | All required keys present, missing keys, no tag set, custom required keys |

Use `botocore.stub.Stubber` or a mocking library to simulate AWS responses and service errors.

Example test execution when a test suite is available:

```bash
python -m pytest -v
```

For integration testing, use a dedicated non-production AWS account and disposable buckets. Verify both compliant and non-compliant configurations, then remove test resources safely.

Do not use production buckets to test destructive remediation workflows.

## Common Pitfalls

- **Treating missing permissions as compliance:** An inspection failure is an error, not a successful security check.
- **Assuming default encryption proves every object is encrypted as expected:** Default encryption governs new object uploads that do not specify another supported encryption configuration; inspect existing objects separately when required.
- **Treating versioning as a complete backup strategy:** Versioning helps recover from certain object-level changes but does not replace independent backup and recovery controls.
- **Assuming wildcard-principal detection is complete policy evaluation:** Effective access depends on the complete authorization context.
- **Checking tag keys but ignoring values:** A bucket tagged with `Environment=unknown` still passes a key-presence-only check.
- **Running with broad administrative credentials:** Use a dedicated read-only validation role with narrowly scoped permissions.
- **Ignoring account boundaries:** Validate every intended account and environment rather than assuming one successful execution covers the organization.
- **Automatically remediating findings without review:** Configuration changes can affect workloads, access paths, retention, and recovery behavior.

## Key Takeaways

- Keep S3 validation read-only and use least-privilege IAM permissions.
- Treat inspection errors separately from failed compliance checks and successful checks.
- Combine bucket-level scripts with organization-wide controls such as AWS Config and IAM Access Analyzer.
- Run validation during deployment and periodically across all relevant AWS accounts.
- Remediate findings through reviewed infrastructure-as-code changes rather than silently modifying production resources.