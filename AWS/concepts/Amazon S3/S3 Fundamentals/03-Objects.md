# S3 Objects

## Definition
Objects are the files stored inside a bucket.

Examples:
- image.jpg
- backup.zip
- report.pdf
- video.mp4

## Object Components

### Key
Unique identifier.

### Data
Actual file content.

### Metadata
Information about object.

Examples:
- Content-Type
- Creation Date

### Tags
Key-value pairs used for management.

Example:
Environment=Production

### Version ID
Used when versioning is enabled.

## Maximum Object Size

5 TB

## Multipart Upload

Recommended when object size exceeds 5 GB.

Benefits:
- Faster uploads
- Retry failed parts only
- Parallel uploads

## Interview Question
Q: What is stored inside an S3 object?
A: Data, Metadata, Tags and Key.
