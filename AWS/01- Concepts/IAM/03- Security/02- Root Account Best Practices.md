# Root Account Best Practices

## Why the Root Account Is Different

The root user is created automatically with every AWS account and holds **unrestrictable** permissions — no IAM policy, permission boundary, or SCP can limit what the root user can do, including closing the account entirely and changing the linked payment method. Every other identity in the account (however senior) operates under IAM's normal permission-checking rules; the root user does not.

## Core Best Practices

- **Enable MFA on the root account immediately** — ideally a hardware key or FIDO security key given the account's unrestrictable nature
- **Never use the root account for daily work** — create an IAM administrator (or use IAM Identity Center) for actual day-to-day administrative tasks
- **Never create long-term access keys for the root user** — if they already exist, delete them; the root user should have no programmatic access keys at all in a well-run account
- **Set up account recovery contacts and alternate contacts** — so account recovery doesn't hinge entirely on one person's access to a single email inbox
- **Lock away root credentials** — treat the root password and MFA device as a "break glass" emergency-only asset, not something used in a regular workflow

## What the Root Account Should Actually Be Used For

A short, specific list of tasks that genuinely require it: changing the account's support plan, closing the account, changing the root user's own email/password, and a small number of other account-level settings that IAM policies structurally cannot delegate to any other identity. Nearly everything else — including "administrator" work — should be done via an IAM role or user with appropriately scoped (even if broad) permissions instead.

## In a Multi-Account Organization

Each member account still has its own root user. AWS Organizations offers **root credential management** features to centrally view and manage (and in supported cases, remove long-term credentials from) root users across all member accounts from the management account — a meaningful operational improvement over manually auditing root account hygiene account-by-account.

## Senior-Level Considerations

- A genuinely common real-world security gap: root MFA enabled on the management account, but not consistently enforced across every member account in a large Organization — root account hygiene needs to be checked account-by-account, not assumed from the management account's own good practices
- Because SCPs (see Policy Evaluation Logic) do apply even to an account's root user, an Organization can use SCPs to restrict what root can do within member accounts — one of the only mechanisms that can meaningfully constrain root's otherwise-unrestrictable nature
