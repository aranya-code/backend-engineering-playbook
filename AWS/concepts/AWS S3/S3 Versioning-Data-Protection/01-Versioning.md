# S3 Versioning

## Definition
Versioning is a bucket-level feature that stores multiple versions of the same object.

## Why Versioning Exists
- Protect against accidental deletion
- Protect against accidental overwrite
- Enable rollback

## How It Works
Each upload receives a unique Version ID.

report.pdf -> Version A
report.pdf -> Version B
report.pdf -> Version C

All versions remain available.

## Important Facts
- Enabled at bucket level
- Cannot be fully disabled after enabling
- Can only be suspended

## Benefits
- Data recovery
- Auditability
- Rollback support

## AWS CLI

Enable Versioning

aws s3api put-bucket-versioning --bucket my-bucket --versioning-configuration Status=Enabled

Check Status

aws s3api get-bucket-versioning --bucket my-bucket
