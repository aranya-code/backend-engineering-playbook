# 10 - Docker ECR Deployment

Publishes a Docker image to Amazon ECR using GitHub OIDC.

## Required GitHub configuration

Repository/environment variables:
- `AWS_REGION`
- `ECR_REPOSITORY`

Secret:
- `AWS_ROLE_ARN`

The AWS role trust policy must allow the repository to assume the role through GitHub's OIDC provider.

## Workflow concepts

- OIDC authentication
- ECR login
- Immutable SHA image tags
- Build and push
