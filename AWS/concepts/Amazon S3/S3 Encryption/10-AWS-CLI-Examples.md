# AWS CLI Examples

Upload with SSE-S3

aws s3 cp file.txt s3://bucket --sse AES256

Upload with SSE-KMS

aws s3 cp file.txt s3://bucket --sse aws:kms

View Encryption Settings

aws s3api get-bucket-encryption --bucket my-bucket
