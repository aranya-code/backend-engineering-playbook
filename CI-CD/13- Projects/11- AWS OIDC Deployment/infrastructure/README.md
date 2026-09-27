# Infrastructure

This project intentionally keeps AWS resources abstract. Configure the GitHub
OIDC provider and IAM role in the AWS account, then reference the role ARN from
GitHub Actions.
