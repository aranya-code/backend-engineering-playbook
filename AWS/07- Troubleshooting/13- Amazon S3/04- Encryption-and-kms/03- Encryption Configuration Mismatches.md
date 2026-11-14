# 03- Encryption Configuration Mismatches

## Overview

Amazon S3 encryption configuration mismatches occur when the encryption settings required by a bucket, the settings supplied by an application, the KMS key associated with an object, or the policies governing encryption do not agree.

These problems frequently appear after changing a bucket's default encryption, migrating objects between buckets, introducing a customer managed KMS key, enabling S3 Bucket Keys, or deploying a new application version with different upload parameters.

Common symptoms include:

- `AccessDenied` when uploading objects with SSE-KMS.
- `InvalidArgument` or `400 Bad Request` responses caused by incompatible encryption headers.
- Uploads failing because a bucket policy requires a specific KMS key.
- Objects using an unexpected KMS key despite the bucket having the desired default encryption.
- Downloads failing because the application sends inappropriate encryption request headers.
- Copy operations preserving or changing encryption settings unexpectedly.
- KMS authorization failures appearing after S3 Bucket Keys are enabled.
- Different encryption behavior between development, staging, and production.

The central troubleshooting objective is to compare the intended encryption configuration with the actual request, bucket configuration, object metadata, and applicable policies.

A bucket's default encryption setting, an individual object's encryption metadata, and the application's request headers are separate parts of the configuration. Changing one does not necessarily update the others.

## Understand the Encryption Configuration Layers

S3 encryption behavior depends on several configuration layers.

| Configuration layer | Controls | Typical mismatch |
|---|---|---|
| Bucket default encryption | Default encryption applied to new uploads that do not specify another accepted configuration | Application assumes the bucket's default is the intended KMS key |
| Request encryption headers | Encryption mode, optional KMS key identifier, and related settings supplied by the client | Client sends a different key or encryption mode from the one required by the bucket |
| Bucket policy | Allows or denies requests based on encryption headers and other conditions | Policy requires a specific key, but the request omits it or specifies another key |
| KMS key policy and IAM permissions | Authorization to use the selected KMS key | Request identifies the correct key but the caller cannot use it |
| Object encryption metadata | Encryption configuration actually associated with an existing object | Application expects an object to have been re-encrypted after a bucket configuration change |
| S3 Bucket Key configuration | Reduces KMS request traffic for supported SSE-KMS objects | Encryption-context policy expects an object ARN instead of a bucket ARN |
| Application and SDK configuration | Parameters passed to S3 operations | Different application environments send different encryption settings |

For troubleshooting, distinguish a request that is rejected because its encryption parameters violate a policy from a request that reaches an otherwise valid encryption configuration but fails because the caller lacks permission to use the key.

## Identify the Encryption Mode

Amazon S3 supports several server-side encryption options.

| Encryption mode | Configuration identifier | Main consideration |
|---|---|---|
| SSE-S3 | `AES256` | S3 manages the encryption keys; customer KMS permissions are not required for this encryption mode |
| SSE-KMS | `aws:kms` | Uses an AWS KMS key and requires appropriate key authorization |
| DSSE-KMS | `aws:kms:dsse` | Uses dual-layer server-side encryption with AWS KMS integration |
| SSE-C | Customer-provided key headers | The client must supply the correct customer-provided key material for applicable requests |

Amazon S3 applies SSE-S3 by default to new object uploads unless another supported encryption configuration is used. A bucket can also be configured with default SSE-KMS encryption.

SSE-KMS requires a supported symmetric KMS key in the same Region as the bucket. Do not substitute an asymmetric KMS key or a key from another Region.

DSSE-KMS does not support S3 Bucket Keys. Avoid assuming that all SSE-KMS configuration options can be applied unchanged to DSSE-KMS.

## Diagnostic Workflow

### Capture the failed operation

Record the following before changing the configuration:

- AWS error code and message.
- HTTP status code.
- S3 operation, bucket, and object key.
- Effective AWS account and principal.
- Bucket Region.
- Encryption headers supplied by the application, excluding sensitive material.
- Expected encryption mode and KMS key ARN.
- Actual object encryption metadata, if available.
- S3 request ID and extended request ID.
- Relevant S3 and KMS CloudTrail events.

Do not record AWS secret access keys, session tokens, authorization headers, or complete presigned URLs in general application logs.

### Verify the effective AWS identity

Run these commands in the environment where the failure occurs:

```bash
aws sts get-caller-identity
aws configure list
```

For a named profile:

```bash
aws sts get-caller-identity --profile s3-debug
```

Confirm that the account and principal match the intended workload.

If the AWS CLI succeeds but Boto3 fails, verify whether both clients use the same identity, Region, and endpoint. A configuration mismatch should not be diagnosed as a KMS policy issue until the actual caller is established.

### Inspect bucket default encryption

Run:

```bash
aws s3api get-bucket-encryption \
  --bucket example-private-bucket \
  --region ap-south-1
```

Inspect the returned `ServerSideEncryptionConfiguration`, including the configured encryption algorithm, KMS key identifier where applicable, and Bucket Key setting.

The default encryption configuration describes the behavior for new objects. It does not prove that every existing object uses the same encryption mode or key.

### Inspect the affected object's encryption

Use:

```bash
aws s3api head-object \
  --bucket example-private-bucket \
  --key "documents/report.pdf" \
  --region ap-south-1
```

Inspect fields such as:

- `ServerSideEncryption`
- `SSEKMSKeyId`
- `BucketKeyEnabled`, when returned

If the object uses a KMS key that differs from the current bucket default, the difference may be legitimate. The object may have been uploaded before the configuration changed, copied from another bucket, or uploaded using explicit encryption parameters.

A `HeadObject` request can itself fail due to S3 authorization. Investigate that denial rather than assuming that the object's encryption metadata is missing.

Do not send SSE-KMS encryption request headers with `GetObject` or `HeadObject`. S3 does not require those headers to read an SSE-KMS object, and sending them can result in `400 Bad Request`.

### Inspect the bucket policy

Retrieve the bucket policy:

```bash
aws s3api get-bucket-policy \
  --bucket example-private-bucket \
  --region ap-south-1
```

Inspect any conditions involving:

- `s3:x-amz-server-side-encryption`
- `s3:x-amz-server-side-encryption-aws-kms-key-id`
- Other encryption-related request condition keys.

Look for explicit denies that reject missing encryption headers, an unexpected algorithm, or a different KMS key ARN.

A policy that requires a specific encryption header can reject an upload even when the bucket's default encryption would otherwise apply the intended encryption to the new object.

## Troubleshoot Default Encryption and Request Header Mismatches

### Understand how default encryption interacts with requests

When an upload does not explicitly specify an encryption configuration, S3 uses the applicable bucket default encryption settings.

However, bucket default encryption and a policy requiring specific request headers are different controls.

For example, consider a bucket configured with default SSE-KMS using a customer managed key. An application sends `PutObject` without encryption headers, expecting S3 to use that default.

The upload can still be denied if the bucket policy requires the request to explicitly contain a particular KMS key identifier.

The correct response is to determine which behavior the security design intends:

- Rely on bucket default encryption and avoid unnecessarily requiring clients to send redundant encryption headers; or
- Require the application to specify the approved encryption mode and key, then configure the request and policy consistently.

Do not remove a security condition merely to make the request succeed. Confirm the intended enforcement model before modifying the policy.

### Example: require a specific KMS key

An upload client can explicitly select the intended key:

```bash
aws s3api put-object \
  --bucket example-private-bucket \
  --key "uploads/report.pdf" \
  --body "./report.pdf" \
  --server-side-encryption aws:kms \
  --ssekms-key-id arn:aws:kms:ap-south-1:123456789012:key/EXAMPLE-KEY-ID \
  --region ap-south-1
```

Replace the example key ARN and Region with the intended values.

This request explicitly specifies the SSE-KMS algorithm and customer managed key. The principal still needs the necessary S3 and KMS permissions, and the bucket policy must allow the request.

If the bucket is intentionally designed to use default SSE-S3, do not send SSE-KMS headers unless the application is expected to override the default.

### Example: bucket policy requires a specific KMS key

An illustrative policy statement can deny writes that do not use an approved key:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyWritesWithoutApprovedKMSKey",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::example-private-bucket/*",
      "Condition": {
        "ArnNotEqualsIfExists": {
          "s3:x-amz-server-side-encryption-aws-kms-key-id": "arn:aws:kms:ap-south-1:123456789012:key/EXAMPLE-KEY-ID"
        }
      }
    }
  ]
}
```

This is an illustrative deny statement, not a complete bucket policy. It rejects writes that do not satisfy the specified key condition, including requests with a missing key header under the condition shown.

Review the precise policy semantics and test the statement in a non-production environment before deployment. Be particularly careful when changing policies that affect multiple applications, replication, service integrations, or cross-account uploads.

## Troubleshoot Wrong KMS Key Selection

The key requested by the application, the key configured as the bucket default, and the key associated with an existing object can be different.

| Observation | Possible explanation | Investigation |
|---|---|---|
| Upload uses an unexpected key | Request explicitly selected a key that overrides the bucket default | Inspect SDK parameters and request headers |
| Upload is rejected despite a correct default | Bucket policy requires an explicit key header or another encryption condition | Compare request headers with policy conditions |
| Download fails after key rotation | Existing objects are encrypted under a different key than expected | Inspect `SSEKMSKeyId` and key state |
| Copy creates an object encrypted with a different key | Destination defaults or explicit copy parameters select another encryption configuration | Inspect source and destination settings |
| Encryption works in one environment but not another | Environment-specific settings point to different keys or accounts | Compare effective identity, KMS ARN, Region, and client configuration |

### Validate the intended key

Use the actual KMS key ARN:

```bash
aws kms describe-key \
  --key-id arn:aws:kms:ap-south-1:123456789012:key/EXAMPLE-KEY-ID \
  --region ap-south-1
```

Verify the owning account, Region, key state, and intended use.

If a customer managed key is required, prefer an explicit full key ARN when the application or policy needs a particular key. This reduces ambiguity between accounts and aliases.

For cross-account requests, the key-owning account and the caller's account must both establish the required authorization path.

### Check KMS permissions separately

For standard SSE-KMS operations:

| Operation | Typical KMS permission |
|---|---|
| Upload with SSE-KMS | `kms:GenerateDataKey` |
| Download with SSE-KMS | `kms:Decrypt` |
| Complete a standard multipart upload | `kms:GenerateDataKey` and `kms:Decrypt`, as required by the multipart workflow |
| Copy an SSE-KMS object | Appropriate decryption permission for the source key and data-key generation permission for the destination key |

These are typical permissions; the full set depends on the API operation and implementation.

If the request selects the correct key but still fails, inspect the identity policy, KMS key policy, grants, explicit denies, and any applicable organizational restrictions. Do not broaden KMS permissions unless the missing authorization has been established.

## Troubleshoot S3 Bucket Key Configuration

S3 Bucket Keys reduce request traffic from S3 to AWS KMS for supported SSE-KMS workloads and can reduce KMS request costs significantly.

They also affect the encryption context used for KMS authorization.

Without an S3 Bucket Key, S3 normally uses the object ARN as the encryption context. When a Bucket Key is enabled, S3 uses the bucket ARN as the encryption context.

For example:

```text
Without S3 Bucket Key:
arn:aws:s3:::example-private-bucket/documents/report.pdf

With S3 Bucket Key:
arn:aws:s3:::example-private-bucket
```

These examples represent the resource ARN values associated with the encryption context; they are not KMS key ARNs.

### Symptoms of a Bucket Key mismatch

- KMS authorization begins failing after Bucket Keys are enabled.
- Existing encryption-context conditions work for some objects but not others.
- KMS CloudTrail events show a bucket-level ARN where the policy expects an object-level ARN.
- S3 and KMS permissions appear correct, but an encryption-context condition prevents access.

### Corrective action

Inspect the `kms:EncryptionContext` conditions in the IAM and KMS key policies. Update them only if the intended security design permits the bucket-level context.

Do not assume that changing the bucket's default Bucket Key setting rewrites existing objects. Enabling or disabling Bucket Keys for new uploads does not automatically convert all existing objects. Existing objects require an appropriate copy operation or another supported re-encryption workflow.

Bucket Keys are not supported for DSSE-KMS. Do not attempt to configure a DSSE-KMS workload as though it supports the same Bucket Key behavior.

## Troubleshoot Object Copy and Re-Encryption

Changing a bucket's default encryption does not automatically re-encrypt existing objects.

For example, a bucket previously using SSE-S3 is changed to use SSE-KMS. New objects can use the new default, while existing objects remain encrypted according to their original configuration.

Likewise, changing the bucket's default KMS key does not automatically migrate all existing objects to the new key.

### Diagnose a copy operation

Before copying or re-encrypting an object, verify:

- Source object encryption mode and key ARN.
- Destination bucket default encryption.
- Any explicitly selected destination encryption settings.
- Source S3 read permissions.
- Destination S3 write permissions.
- Source KMS decryption permissions when required.
- Destination KMS permissions when required.
- Whether the operation should enable or disable an S3 Bucket Key.

For a targeted copy, specify destination encryption settings intentionally:

```bash
aws s3api copy-object \
  --bucket example-private-bucket \
  --key "archive/report.pdf" \
  --copy-source "example-private-bucket/documents/report.pdf" \
  --server-side-encryption aws:kms \
  --ssekms-key-id arn:aws:kms:ap-south-1:123456789012:key/EXAMPLE-KEY-ID \
  --region ap-south-1
```

This example copies an object within the same bucket and requests SSE-KMS with the specified destination key. The caller needs the appropriate source and destination permissions, including KMS permissions required by the operation.

For larger objects or batch migrations, use a supported transfer or batch operation appropriate to the object size and migration scope. Confirm the encryption settings and verify representative destination objects before migrating an entire dataset.

### Verify the result

Inspect the copied object:

```bash
aws s3api head-object \
  --bucket example-private-bucket \
  --key "archive/report.pdf" \
  --region ap-south-1
```

Verify the returned encryption algorithm and KMS key identifier when applicable. Also verify that the intended consumer identity can read the destination object.

Do not consider a migration complete merely because the copy request returned successfully. Validate the destination configuration and the access pattern expected in production.

## Troubleshoot Application and SDK Configuration

Backend services may configure encryption per request, globally through service-layer defaults, or implicitly through the bucket's default encryption.

A centralized service layer makes the selected behavior easier to review and test.

Example using Boto3:

```python
import boto3
from botocore.exceptions import BotoCoreError, ClientError


class S3StorageService:
    def __init__(
        self,
        bucket_name: str,
        region_name: str,
        kms_key_arn: str | None = None,
    ) -> None:
        self.bucket_name = bucket_name
        self.kms_key_arn = kms_key_arn
        self.client = boto3.client(
            "s3",
            region_name=region_name,
        )

    def upload_file(self, local_path: str, key: str) -> None:
        extra_args = {}

        if self.kms_key_arn:
            extra_args = {
                "ServerSideEncryption": "aws:kms",
                "SSEKMSKeyId": self.kms_key_arn,
            }

        try:
            self.client.upload_file(
                local_path,
                self.bucket_name,
                key,
                ExtraArgs=extra_args,
            )
        except (ClientError, BotoCoreError):
            raise
```

This service explicitly selects SSE-KMS only when a KMS key ARN is supplied. Otherwise, it relies on the bucket's applicable default encryption configuration.

The example is a minimal service-layer illustration. In production, validate configuration at startup, restrict which encryption modes can be selected, avoid logging sensitive request material, and map AWS exceptions to appropriate application-level errors.

For Django, Django REST Framework, FastAPI, Flask, and Celery, keep encryption configuration centralized rather than independently hardcoding different KMS keys in individual routes or tasks.

### Configuration checks

Compare the following between development, staging, and production:

- `AWS_REGION` and explicit client Region.
- S3 bucket name.
- KMS key ARN and owning account.
- Whether an SSE-KMS key is supplied explicitly.
- Expected bucket default encryption.
- Bucket-policy conditions.
- Whether S3 Bucket Keys are required or enabled.
- Credential provider and effective principal.

Do not store credentials in source code or use hardcoded key ARNs without an environment-specific configuration strategy.

## Root Cause and Corrective Action

| Confirmed cause | Corrective action | Prevention |
|---|---|---|
| Application sends an unapproved encryption mode | Align the request with the bucket's approved encryption configuration | Validate encryption parameters in the service layer |
| Bucket policy requires a different key header | Correct the request or revise the policy through change control | Test request headers against policy requirements |
| Wrong KMS key is configured | Correct the key ARN, account, or Region | Validate configuration during deployment |
| Missing KMS permissions | Grant the required actions on the correct key | Test uploads, reads, and copies using the production workload role |
| Bucket Key encryption context differs | Update valid policy conditions to match the intended context | Test authorization before enabling Bucket Keys |
| Existing objects use an older encryption configuration | Perform a controlled copy or re-encryption workflow where required | Track object encryption requirements separately from bucket defaults |
| DSSE-KMS configured with unsupported Bucket Key behavior | Remove the incompatible Bucket Key configuration and use supported DSSE-KMS settings | Validate feature compatibility before deployment |
| GET or HEAD sends unnecessary SSE-KMS request headers | Remove the encryption request headers from the read request | Separate upload encryption parameters from read-operation parameters |
| Source or destination KMS access fails during copy | Correct source decryption and destination encryption authorization | Test the complete copy workflow with the intended role |

After applying the correction, repeat the original operation with the same principal, bucket, Region, key, and request configuration. Verify the actual object metadata and intended consumer access.

## Production Best Practices

- Establish an explicit encryption policy for every bucket and workload.
- Distinguish bucket default encryption from request-level encryption headers and bucket-policy enforcement.
- Use customer managed KMS keys when explicit key-policy control or supported cross-account access is required.
- Use symmetric KMS keys supported by S3 and keep them in the bucket's Region.
- Avoid unnecessary encryption headers on `GetObject` and `HeadObject`.
- Centralize encryption configuration in reusable backend service layers.
- Treat changing default encryption as a change affecting new uploads, not an automatic migration of existing objects.
- Before enabling S3 Bucket Keys, validate encryption-context conditions and their effect on access policies.
- Do not assume that SSE-KMS and DSSE-KMS support identical features; DSSE-KMS does not support S3 Bucket Keys.
- Validate encryption behavior for upload, download, copy, multipart, and cross-account operations separately.
- Apply policy and encryption changes through infrastructure-as-code and controlled deployment reviews.
- Use CloudTrail and object metadata to confirm the encryption configuration instead of inferring it from the bucket's current settings.

## Related AWS Documentation

- [Configuring default encryption for an S3 bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-bucket-encryption.html)
- [Specifying SSE-KMS encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/specifying-kms-encryption.html)
- [Specifying DSSE-KMS encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/specifying-dsse-encryption.html)
- [Examples of Amazon S3 bucket policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/example-bucket-policies.html)
- [Configuring S3 Bucket Keys](https://docs.aws.amazon.com/AmazonS3/latest/userguide/configuring-bucket-key.html)
- [Reducing SSE-KMS costs with S3 Bucket Keys](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-key.html)
- [AWS KMS key policies](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html)

## Key Takeaways

- Bucket default encryption, request encryption headers, bucket policies, and existing object metadata are separate configuration layers that must be diagnosed independently.
- A bucket policy can reject a request that would otherwise have used the bucket's default encryption if the required request headers are missing or inconsistent.
- S3 Bucket Keys change the SSE-KMS encryption context from an object ARN to a bucket ARN and are not supported for DSSE-KMS.
- Changing a bucket's default encryption affects new uploads; existing objects require a controlled copy or re-encryption workflow when migration is necessary.
- Verify the resulting object encryption metadata and consumer access after correcting a mismatch rather than relying solely on the bucket configuration.