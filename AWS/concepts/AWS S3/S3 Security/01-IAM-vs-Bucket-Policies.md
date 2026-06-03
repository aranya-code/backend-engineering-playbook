# IAM vs Bucket Policies

## IAM Policies
Identity-based permissions attached to users, groups, or roles.

Example:
Allow DevOps engineers to upload files.

## Bucket Policies
Resource-based permissions attached directly to a bucket.

Example:
Allow CloudFront to read objects.

## Comparison

| Feature | IAM Policy | Bucket Policy |
|----------|-----------|--------------|
| Attached To | User/Role | Bucket |
| Cross Account Access | Limited | Excellent |
| Resource Based | No | Yes |

## Interview Question
When should Bucket Policies be preferred?
Answer: Cross-account access and public access configurations.
