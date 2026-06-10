# S3 Buckets

## Definition
A bucket is a logical container used to store objects in S3.

## Important Characteristics

### Region Specific
Buckets are created in a specific AWS Region.

### Globally Unique
Bucket names must be unique across all AWS accounts.

### Virtually Unlimited Objects
A bucket can store billions of objects.

## Naming Rules
- 3–63 characters
- Lowercase only
- Numbers allowed
- Hyphen allowed
- Must start and end with letter or number

## Good Naming Examples
prod-company-backups
dev-website-assets
logs-ap-south-1

## AWS CLI

Create Bucket

aws s3 mb s3://company-backups

List Buckets

aws s3 ls

Delete Bucket

aws s3 rb s3://company-backups

## Best Practices
- Include environment
- Include region
- Avoid generic names

## Exam Tip
Bucket Name = Global
Bucket Data = Regional
