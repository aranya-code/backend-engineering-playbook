# IAM Policy Structure

## Top-Level Elements

| Element | Purpose |
|---|---|
| Version | Policy language version — almost always `"2012-10-17"` (the current version; an older `"2008-10-17"` exists but is legacy) |
| Id | An optional identifier for the policy as a whole |
| Statement | One or more individual permission statements (required) — an array, even if there's only one |

## Statement-Level Elements

| Element | Purpose |
|---|---|
| Sid | Optional statement identifier, useful for readability in policies with many statements |
| Effect | `Allow` or `Deny` — every statement must specify one |
| Principal | Who the policy applies to — only used in resource-based policies (identity-based policies don't need this, since the policy is already attached to a specific identity) |
| Action | The specific API actions this statement covers, e.g. `s3:GetObject`, or a wildcard like `s3:*` |
| Resource | The specific resource(s) this statement applies to, typically an ARN, or `*` for all resources |
| Condition | Optional — narrows when the statement applies (e.g., only from a specific IP range, only with MFA present) |

## A Fully Annotated Example

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowReadOnlyS3Access",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ],
      "Condition": {
        "Bool": {
          "aws:MultiFactorAuthPresent": "true"
        }
      }
    }
  ]
}
```

This statement allows reading objects and listing contents of `my-bucket`, but only if the requester authenticated with MFA — a common senior-level pattern for gating sensitive read access.

## Why Both Bucket and Bucket/* Appear Above

`s3:ListBucket` operates on the *bucket itself* (`arn:aws:s3:::my-bucket`), while `s3:GetObject` operates on *objects inside it* (`arn:aws:s3:::my-bucket/*`). Forgetting the bucket-level ARN for list operations is one of the most common IAM policy mistakes — it results in being able to fetch a specific known object but not list what's in the bucket.

## Wildcards — Powerful and Risky

`Action: "s3:*"` or `Resource: "*"` are valid but broad — they should be a deliberate, justified choice, not a default reached for to "make it work" under time pressure (see `Least Privilege.md`).

## Senior-Level Considerations

- `Condition` blocks are where a lot of real production sophistication lives — enforcing MFA, restricting by source IP or VPC endpoint, restricting by time of day, or requiring a specific tag on the resource are all expressed here
- Statements within the same policy are combined — if any statement's `Deny` matches, the whole request is denied regardless of other `Allow` statements (see Policy Evaluation Logic for the full resolution order across multiple policies)
