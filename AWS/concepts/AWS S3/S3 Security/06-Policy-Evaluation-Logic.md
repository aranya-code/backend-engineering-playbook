# Policy Evaluation Logic

## How AWS Evaluates Permissions

Step 1:
Check Explicit Deny

Step 2:
Check Allow

Step 3:
Default Deny

## Rule

Explicit Deny always wins.

## Exam Trap
Even if IAM allows access, a Bucket Policy Explicit Deny blocks it.
