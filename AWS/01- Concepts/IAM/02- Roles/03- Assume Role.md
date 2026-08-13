# Assume Role

## What "Assuming a Role" Actually Means

Calling the `sts:AssumeRole` API (or a related STS action) to exchange proof of an existing identity for a new set of **temporary credentials** matching the target role's permissions. The caller doesn't "become" the role permanently — they receive a time-limited credential set that expires and must be re-requested.

## The Trust Policy — Who's Allowed to Assume

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sts:AssumeRole"
            ],
            "Principal": {
                "Service": [
                    "ec2.amazonaws.com"
                ]
            }
        }
    ]
}
```

This is a **trust policy** — attached to the role itself, defining who may assume it. This specific example allows the EC2 service to assume the role, which is exactly what makes an instance profile (see that file) work — EC2 assumes the role on behalf of the instance.

A trust policy's `Principal` could instead be an AWS account, a specific IAM role/user ARN, or a federated identity provider — the mechanism is identical regardless of who's on the other side.

## The Assume-Role Flow

```text
1. Caller has some existing identity (IAM user, another role, or a federated identity)
2. Caller calls sts:AssumeRole, specifying the target role's ARN
3. STS checks the target role's trust policy — does it allow this specific caller?
4. If allowed, STS issues temporary credentials (access key, secret key, session token)
5. Caller uses these temporary credentials for subsequent API calls, until they expire
```

## Cross-Account AssumeRole

The same mechanism extends naturally across accounts: a role in Account B can have a trust policy naming Account A (or a specific role within it) as an allowed principal, letting an identity in Account A assume a role in Account B temporarily — the foundation of cross-account access (see `Cross-Account Roles.md`).

## External ID — A Detail Worth Knowing

For third-party cross-account access (e.g., a SaaS vendor assuming a role in your account), AWS recommends including an `ExternalId` condition in the trust policy — a shared secret value that must be passed during the assume-role call. This protects against the "confused deputy" problem, where a third party might otherwise be tricked into assuming a role on behalf of an unintended customer.

## Senior-Level Considerations

- `sts:AssumeRole` itself is just an API call — the actual security boundary is entirely defined by the trust policy's `Principal` and any `Condition` block on it, not by anything inherent to the assume-role mechanism itself
- Debugging "AccessDenied" on an AssumeRole call almost always comes down to one of: the trust policy doesn't list this principal, the caller lacks `sts:AssumeRole` permission on their own side, or (for cross-account) an `ExternalId` mismatch — see `STS AssumeRole Errors.md` for the full troubleshooting rundown
