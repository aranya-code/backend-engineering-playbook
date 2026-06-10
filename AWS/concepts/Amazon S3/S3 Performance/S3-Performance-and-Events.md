# S3 Performance, Metadata, Tags & Event Notifications

## S3 Multipart Upload
- Recommended for files >100 MB
- Required for files >5 GB
- Uploads parts in parallel
- Retries only failed parts

## S3 Transfer Acceleration
- Uses AWS Edge Locations
- Transfers data over AWS backbone network
- Faster uploads/downloads for global users
- Compatible with Multipart Upload

## S3 Byte-Range Fetches
- Retrieve specific byte ranges
- Parallel downloads
- Faster retrieval of large files
- Useful for video streaming and large logs

## S3 Metadata
- User-defined key-value pairs
- Prefix: x-amz-meta-
- Retrieved with object
- Not searchable

## S3 Object Tags
- Key-value pairs attached to objects
- Used for IAM conditions
- Used for Lifecycle rules
- Used for Analytics and Cost Allocation

## Metadata vs Tags
- Metadata: object information
- Tags: management, permissions, lifecycle

## S3 Event Notifications
Destinations:
- Lambda
- SNS
- SQS
- EventBridge

### S3 -> SNS
SNS Topic Policy must allow SNS:Publish from S3

### S3 -> SQS
Queue Policy must allow SQS:SendMessage from S3

### S3 -> Lambda
Lambda Permission must allow lambda:InvokeFunction from S3

## Important Limitations
- At-least-once delivery
- Duplicate events possible
- Avoid recursive Lambda loops
- SQS FIFO requires EventBridge
