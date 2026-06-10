# AWS CLI & SDK Examples

Generate Download URL

aws s3 presign s3://mybucket/report.pdf

Example SDK Flow

1. Backend generates URL
2. Returns URL to client
3. Client uploads/downloads directly
