# README

## Overview

Amazon S3 integrations cover the implementation patterns, SDK usage, framework-specific workflows, and event-driven architectures required to connect S3 to web applications, Python backends, and asynchronous processing systems. It addresses web and content delivery configuration, Boto3 SDK usage, event-driven processing with Lambda, SQS, SNS, and EventBridge, and framework-specific integrations for Django, FastAPI, Flask, and Celery.

This section of the Backend Engineering Playbook provides a structured reference for Python backend engineers who build production applications that use S3 as a storage layer: integrating S3 correctly into each framework and service boundary, enforcing application-level authorization, and designing reliable asynchronous processing pipelines.

The focus is on practical integration engineering: selecting the right SDK method for each transfer type, enforcing authorization at the application boundary rather than relying on S3 access controls alone, designing idempotent event processing, and avoiding the memory, performance, and security issues that arise from common integration mistakes.

## Navigation

| # | Folder | Description |
|---|---|---|
| 01 | [01- web-and-content-delivery](./01-%20web-and-content-delivery/) | CORS configuration, static website hosting, and CloudFront integration for browser-based and content delivery workloads |
| 02 | [02- boto3](./02-%20boto3/) | Boto3 client setup, object uploads and downloads, multipart upload, and presigned URL generation for Python applications |
| 03 | [03- event-driven](./03-%20event-driven/) | S3 event notifications, Lambda, SNS, SQS, and EventBridge integrations for asynchronous object processing pipelines |
| 04 | [04- backend-frameworks](./04-%20backend-frameworks/) | Django, DRF, FastAPI, Flask, and Celery integration patterns for file upload, download, and background processing workflows |

## Why S3 Integration Matters

S3 is a storage service, not an application platform. Integrating it correctly requires application-level logic to handle authorization, key construction, transfer coordination, and processing sequencing that S3 itself does not provide. Poor integration decisions — buffering large files in memory, skipping application authorization before presigned URL generation, or coupling upload handlers to synchronous processing — produce applications that are slow, memory-inefficient, or insecure.

Common integration risks include:

- Returning S3 object URLs directly in API responses, exposing bucket structure and bypassing application-level access control.
- Generating presigned URLs without verifying that the requesting user is authorized to access the referenced object at the application level.
- Using synchronous S3 operations in HTTP request handlers for large file transfers, causing request timeouts and degraded concurrency.
- Processing S3 events without idempotency guards, causing duplicate side effects when S3 delivers the same notification more than once.
- Constructing S3 object keys from raw user-provided filenames, introducing namespace collisions and path traversal risks.
- Missing dead-letter queue configuration on event-driven processing pipelines, silently discarding failed events in production.

Effective S3 integration combines the correct SDK method for each transfer type, application-level authorization before every S3 operation, idempotent event processing, and streaming transfers that do not buffer entire files in application memory.

## Documentation Structure

| Area | Primary focus |
|---|---|
| Web and content delivery | CORS, static website hosting, and CloudFront origin configuration for browser and CDN workloads |
| Boto3 | Python SDK configuration, transfer methods, multipart upload, and presigned URL generation |
| Event-driven | S3 notification configuration, Lambda, SNS, SQS, EventBridge, and reliable processing workflow design |
| Backend frameworks | Django, DRF, FastAPI, Flask, and Celery integration patterns and file workflow design |

## Core Integration Principles

### Enforce Application Authorization Before Every S3 Operation

S3 IAM and bucket policies control which AWS principals can access a bucket. They do not enforce application-level ownership — which user created which object, which tenant can access which file, or which API caller is authorized for the requested operation. Enforce application-level authorization in the application layer before every upload, download, presigned URL generation, or delete operation.

### Stream Transfers, Never Buffer Entire Files

Loading an entire uploaded file into memory before writing it to S3 exhausts memory under concurrent load. Use `upload_fileobj` and streaming request body access in upload handlers. Use `get_object` with response body streaming or `download_fileobj` in download handlers. Never accumulate file bytes in a Python variable before passing them to S3.

### Construct Object Keys from Application Identifiers

Never use raw client-provided filenames as S3 object keys. Construct keys from application-controlled identifiers — UUID, user ID, tenant ID, content hash — combined with a structured prefix. This prevents namespace collisions, path traversal, and key enumeration by API clients.

### Design Event Processing for Idempotency

S3 event notifications can be delivered more than once. Design processing logic so that receiving the same event twice produces the same result. Use a database record or external state check to detect and skip duplicate processing.

### Always Configure a Dead-Letter Queue

Configure a dead-letter queue for every Lambda function and SQS consumer that processes S3 events. Without a DLQ, failed processing events are silently discarded after the retry limit. A DLQ preserves failed events for investigation, alerting, and replay.

## Key Takeaways

- Application-level authorization must be enforced before generating presigned URLs or returning download paths; S3 access controls cannot enforce application ownership boundaries.
- Streaming transfers are essential for production file handling; buffering files in application memory is a reliability risk under concurrent load.
- S3 object keys must be constructed from application-controlled identifiers, not raw client input, to prevent namespace and security issues.
- S3 event notifications may be delivered more than once; idempotent processing and dead-letter queues are both required for reliable production event pipelines.
- CORS configuration, presigned URL generation, and CloudFront OAC must all be set up correctly for browser-based S3 access to work securely; each layer addresses a different part of the access model.
