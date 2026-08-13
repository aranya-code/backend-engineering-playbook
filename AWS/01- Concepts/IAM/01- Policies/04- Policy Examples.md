# Policy Examples

## Example 1: Resource-Based Policy Granting Cross-Account S3 Access

```json
{
  "Version": "2012-10-17",
  "Id": "S3-Account-Permissions",
  "Statement": [
    {
      "Sid": "1",
      "Effect": "Allow",
      "Principal": {
        "AWS": ["arn:aws:iam::123456789012:root"]
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::mybucket/*"
      ]
    }
  ]
}
```

This is a **bucket policy** (resource-based), attached directly to the S3 bucket rather than to an identity — notice the `Principal` element, which only appears in resource-based policies. It grants the entire account `123456789012` (via its root, meaning any sufficiently-permissioned identity in that account) read/write access to objects in `mybucket`. For this to actually work, the accessing identity in account `123456789012` also needs its own identity-based policy allowing `s3:GetObject`/`s3:PutObject` — both sides must agree.

## Example 2: Identity-Based Policy With a Condition

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "ec2:*",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
    }
  ]
}
```

Grants full EC2 access, but only for requests targeting `us-east-1` — a common pattern for restricting an otherwise-broad permission to an approved region, preventing accidental (or malicious) resource creation elsewhere.

## Example 3: Explicit Deny Overriding a Broader Allow

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": "s3:DeleteObject",
      "Resource": "arn:aws:s3:::production-data/*"
    }
  ]
}
```

Even if another attached policy grants broad `s3:*` access, this explicit `Deny` on `s3:DeleteObject` for this specific bucket wins — explicit deny always overrides any allow, from any policy (see Policy Evaluation Logic). A common, deliberate safeguard against accidental deletion of a critical bucket.

## Example 4: Permission Boundary-Style Scoping

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:*", "dynamodb:*"],
      "Resource": "*"
    },
    {
      "Effect": "Deny",
      "NotAction": ["s3:*", "dynamodb:*"],
      "Resource": "*"
    }
  ]
}
```

Uses `NotAction` to deny everything **except** S3 and DynamoDB actions — a compact way to express "only these two services, nothing else," useful as a permission boundary attached to a role that should never be able to touch other services regardless of what its permission policy might later be changed to allow.

## Senior-Level Considerations

- Real production policies are almost always more specific than these examples — scoping `Resource` to exact ARNs rather than `*`, and using `Condition` blocks to further narrow when a statement applies, is what separates a "works but risky" policy from a well-scoped one
- `NotAction` and `NotResource` are less commonly used than `Action`/`Resource` but are genuinely powerful for expressing broad exclusions concisely — worth recognizing even if you don't reach for them often
