# Cross-Account Roles

## The Problem They Solve

An organization with multiple AWS accounts (common practice — see the multi-account patterns in AWS-Architecture and AWS-Security) needs a way for identities in one account to access resources in another, without creating duplicate IAM users in every account or sharing long-term credentials between them.

## The Pattern

```text
Account A (e.g., a central Security/Audit account)
      ↓ sts:AssumeRole
Account B: IAM Role with a trust policy naming Account A as an allowed principal
      ↓
Temporary credentials, scoped to that role's permissions, for the session duration
```

## Setting This Up

**In Account B (the account being accessed):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111111111111:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "a-shared-secret-value"
        }
      }
    }
  ]
}
```

This trust policy allows account `111111111111` (Account A) to assume this role, provided the `ExternalId` condition matches — a safeguard particularly important when the party assuming the role is a third party rather than another account you fully control.

**In Account A (the account initiating access):** the calling identity needs its own identity-based policy granting `sts:AssumeRole` on the specific role ARN in Account B.

## Common Real-World Use Cases

- A central security/audit account with read-only roles it can assume across every application account in an Organization, for centralized monitoring and compliance checks
- A CI/CD pipeline in a shared tooling account assuming a deployment role in each environment account (dev, staging, production) it deploys to
- A third-party SaaS vendor (monitoring tools, cost management platforms) accessing your account via a role you define and control, rather than you handing them a static access key

## Why This Is Safer Than Alternatives

Compared to sharing an IAM user's access keys across accounts (a long-lived, hard-to-audit credential that has to be manually rotated and distributed), cross-account roles provide temporary, automatically-expiring access, with every assumption event independently logged in CloudTrail — both accounts get an audit trail of exactly when access happened and by which identity.

## Senior-Level Considerations

- The External ID condition specifically defends against the "confused deputy" problem — without it, if a third-party vendor reuses the same role ARN pattern for multiple customers, there's a theoretical risk of one customer's setup being used to access a different customer's account; a unique External ID per customer closes this gap
- Cross-account role trust policies should be scoped as narrowly as possible on the `Principal` — trusting an entire account's root (as in the example above) is common and often acceptable when Account A is fully within your own organizational control, but trusting a *specific role* rather than an entire account is a tighter, more auditable practice when feasible
