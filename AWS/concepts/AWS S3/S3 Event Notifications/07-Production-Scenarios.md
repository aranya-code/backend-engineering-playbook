# Production Scenarios

## Scenario 1

User uploads profile image.

Process:
S3 -> Lambda -> Resize Image

## Scenario 2

Application logs uploaded.

Process:
S3 -> SQS -> Analytics Pipeline

## Scenario 3

Compliance file uploaded.

Process:
S3 -> SNS -> Security Team Alert
