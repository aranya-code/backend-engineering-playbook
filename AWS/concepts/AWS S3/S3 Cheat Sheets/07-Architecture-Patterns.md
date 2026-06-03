# Architecture Patterns

Static Website

Route53
-> CloudFront
-> S3

Image Processing

S3
-> Lambda

Global Uploads

Presigned URL
-> Transfer Acceleration
-> S3

Disaster Recovery

S3
-> CRR
-> Backup Region
