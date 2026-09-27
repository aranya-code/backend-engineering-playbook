# 11 - AWS OIDC Deployment

Focused OIDC lab for AWS authentication without storing long-lived AWS access keys.

## Concepts

1. GitHub issues an OIDC token.
2. AWS STS validates the token through the IAM trust policy.
3. STS returns temporary credentials.
4. The workflow calls AWS APIs.

## Required

Create GitHub environments named `staging` and `production`, then configure:
- `AWS_REGION` as an environment variable
- `AWS_ROLE_ARN` as an environment secret

Add appropriate environment protection rules for production.
