# README

## Overview

The `scripts/` directory contains command-line utilities for interacting with the Document Ingestion and Metadata Pipeline.

These utilities support document submission, processing-status inspection, failed-message queue inspection, and controlled infrastructure cleanup.

The scripts are operational entry points, not replacements for the application's API, ingestion services, or Terraform infrastructure definitions.

## Scripts

| Script | Responsibility | AWS Interaction |
|---|---|---|
| `submit_document.py` | Submits a local document through the FastAPI application. | Indirect; the API performs the S3 upload. |
| `check_processing_status.py` | Retrieves processing status for a submitted document. | Uses the configured application/API workflow. |
| `replay_failed_message.py` | Inspects the configured failed-message queue. | Read-only SQS inspection. |
| `cleanup_resources.sh` | Coordinates infrastructure destruction through Terraform. | Destructive infrastructure operation after explicit authorization. |

## Prerequisites

- Python 3.10 or later.
- Dependencies installed from the project-root `requirements.txt`.
- A running FastAPI application for document submission and API-backed status operations.
- AWS CLI and valid AWS credentials for utilities that access AWS resources.
- Terraform installed for infrastructure cleanup.
- Appropriate IAM permissions for the operation being performed.

Install the project dependencies from the project root:

```bash
python -m pip install -r requirements.txt
```

Configure AWS credentials using an appropriate provider, such as an AWS CLI profile or an IAM role.

Verify the active AWS identity before running AWS-backed operations:

```bash
aws sts get-caller-identity
```

Do not place AWS access keys or other credentials directly in scripts or committed configuration files.

## Document Submission

### `submit_document.py`

Submits a local document through the FastAPI document-submission endpoint.

The utility uses the application API rather than uploading directly to S3. This preserves the API's validation and object-key generation behavior.

Run the API before submitting a document.

Inspect the supported arguments:

```bash
python scripts/submit_document.py --help
```

Example:

```bash
python scripts/submit_document.py ./sample-document.pdf
```

The API validates the document and uploads it to the configured S3 bucket. A successful response indicates that the document was accepted for asynchronous processing; it does not guarantee that metadata extraction or downstream processing has completed.

The utility supports the API base URL, content type, request timeout, and verbose logging options. The default API URL is `http://127.0.0.1:8000`, and `DOCUMENT_API_URL` can be used to configure the URL through the environment.

### Operational Considerations

- Ensure the API is running and reachable before submitting documents.
- Use supported file formats and respect the configured maximum document size.
- Avoid blindly retrying a submission after an ambiguous network failure; the server may already have accepted the request.
- Retain the returned document identifier for subsequent status checks.

## Processing Status Inspection

### `check_processing_status.py`

Checks the processing status of a previously submitted document.

Inspect the supported arguments:

```bash
python scripts/check_processing_status.py --help
```

Use the documented command-line arguments to identify the document whose status must be inspected.

Processing is asynchronous. A document may be successfully uploaded while its metadata extraction or downstream processing is still pending.

When investigating a processing failure, correlate the document identifier and S3 object key with the relevant application, Lambda, SQS, and CloudWatch logs.

## Failed-Message Queue Inspection

### `replay_failed_message.py`

Despite its filename, this utility performs read-only inspection of the configured SQS queue. It does not receive, replay, send, or delete messages.

Inspect its supported arguments:

```bash
python scripts/replay_failed_message.py --help
```

The inspection workflow retrieves queue attributes to report information such as:

- Queue identity.
- Approximate visible message count.
- Approximate messages not visible.
- Approximate delayed message count.
- Configured redrive policy, when available.

The utility is intended for operational diagnosis. It does not modify queue state or perform message remediation.

### Remediation Boundary

Message replay is a separate operational action and requires an explicitly authorized workflow.

Do not interpret successful queue inspection as evidence that a message has been replayed or that a failed processing operation has been recovered.

Before performing remediation, establish:

- The root cause of the processing failure.
- Whether the original message or document has already been processed.
- Whether the processing operation is idempotent.
- Whether replay could create duplicate metadata or downstream side effects.
- Whether the remediation identity has only the permissions required for the approved operation.

## Infrastructure Cleanup

### `cleanup_resources.sh`

Coordinates infrastructure destruction through Terraform. It does not independently delete AWS resources outside Terraform state management.

The script includes safeguards such as AWS account identity validation, Terraform initialization and validation, destruction-plan generation, and explicit confirmation before applying a destruction plan.

Inspect the supported options:

```bash
bash scripts/cleanup_resources.sh --help
```

Generate and review a destruction plan without applying it:

```bash
bash scripts/cleanup_resources.sh --plan-only
```

The script supports environment selection and explicit approval options. Review its help output before using those options.

### Destructive Operation Precautions

Before authorizing cleanup:

1. Confirm the AWS account and Region.
2. Confirm the target environment.
3. Review the complete Terraform destruction plan.
4. Identify resources containing data that must be retained.
5. Confirm backup and recovery requirements.
6. Verify resource-protection settings and deletion dependencies.

Some DynamoDB tables and CloudWatch log groups have Terraform `prevent_destroy` protection. DynamoDB deletion protection may also prevent deletion. Resolve these protections through an approved infrastructure change rather than bypassing them indiscriminately.

S3 objects and retained data require particular attention. Confirm the consequences of object deletion and bucket destruction before proceeding.

## Logging and Diagnostics

Use verbose options where supported to obtain additional diagnostic information:

```bash
python scripts/submit_document.py --help
python scripts/replay_failed_message.py --help
```

Operational diagnostics should be correlated using document identifiers, S3 object keys, timestamps, and relevant AWS request or invocation information.

Avoid logging:

- AWS credentials or authorization headers.
- Document contents.
- Sensitive document metadata.
- Presigned URLs or other temporary access credentials.

## Operational Best Practices

- Run scripts from the project root unless their implementation explicitly supports another working directory.
- Inspect `--help` before executing a utility with unfamiliar arguments.
- Verify AWS identity and environment before AWS-backed operations.
- Use least-privilege credentials.
- Treat document submission as a potentially non-idempotent operation.
- Keep failed-message inspection separate from message replay or deletion.
- Generate and review Terraform destruction plans before approving cleanup.
- Keep operational logs free of document contents and credentials.
- Use non-production resources for integration and operational testing.

## Key Takeaways

- `submit_document.py` submits documents through FastAPI, preserving the application's validation and upload workflow.
- Processing-status inspection is separate from document submission because ingestion and downstream processing are asynchronous.
- `replay_failed_message.py` is read-only; message replay and remediation require a separate authorized operation.
- `cleanup_resources.sh` delegates destruction to Terraform and must be used with explicit environment, account, and data-retention checks.
- Always verify the target environment and understand the side effects before executing operational scripts.