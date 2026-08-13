# Inline vs. Managed Policies

## Managed Policies

Standalone policy objects that exist independently of any identity, and can be attached to multiple users, groups, or roles.

- **AWS Managed** — created and maintained by AWS itself (e.g., `AmazonS3ReadOnlyAccess`). Convenient, but you can't customize them, and AWS occasionally updates their contents (usually to add coverage for new related actions), which is worth being aware of since the policy's effective permissions can shift without you changing anything
- **Customer Managed** — created and fully controlled by you, reusable across multiple identities, and versioned (IAM keeps up to 5 versions, letting you roll back if a change causes problems)

## Inline Policies

Embedded directly inside a single user, group, or role — not a standalone object, and not reusable elsewhere. Deleting the identity deletes the inline policy with it automatically.

## When to Use Which

| Use Case | Recommendation |
|---|---|
| Common permission set needed across many identities | Customer Managed |
| Standard AWS service access pattern | AWS Managed (with awareness that AWS controls its contents) |
| A truly one-off, identity-specific permission that should never be reused or accidentally attached elsewhere | Inline |
| Need policy versioning and rollback capability | Managed (inline policies have no version history) |

## Why Managed Policies Are Generally Preferred

Reusability, centralized management (update once, every attachment reflects the change), and version history make managed policies the default recommendation for most real-world cases. Inline policies exist for genuine one-offs, but overuse of inline policies across many identities makes an account's permission structure much harder to audit — there's no single place to review "every identity using this policy," since each inline policy only exists on one identity.

## Senior-Level Considerations

- A common audit question is "show me everywhere this permission is granted" — this is straightforward for a managed policy (check its attachment list) and much harder for inline policies scattered across many identities, which is a real operational argument in favor of managed policies at scale
- Customer managed policy versioning is genuinely useful during incident response — if a policy change is suspected of causing an access problem or an over-permission, rolling back to the previous version is immediate, without needing to reconstruct what the policy used to say
