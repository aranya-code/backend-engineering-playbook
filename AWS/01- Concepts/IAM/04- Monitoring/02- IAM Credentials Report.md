# IAM Credentials Report

## What It Is

An account-wide, downloadable report (CSV format) listing every IAM user in the account and the status of all their credentials — password, access keys, and MFA — in one place, rather than needing to check each user individually.

## What the Report Includes Per User

| Field | Purpose |
|---|---|
| Password enabled / last used | Whether console access exists, and staleness |
| Password last changed | Age of the current password, relevant to rotation policy |
| MFA active | Whether MFA is enabled for this user |
| Access key 1/2 active, last used, last rotated | Existence, staleness, and rotation history of up to two access keys per user |

## Why an Account-Wide Report Matters

Access Advisor (the other Monitoring tool) answers "what has *this one identity* used." The Credentials Report answers a different, account-wide question: "across every user in this account, who has stale passwords, unused access keys, or missing MFA?" — the report you'd actually run for a periodic security review or compliance audit, rather than investigating one identity at a time.

## Typical Review Workflow

```text
1. Generate the credentials report (available via console, CLI, or API)
2. Filter for: users without MFA enabled
3. Filter for: access keys not rotated within policy (e.g., 90 days)
4. Filter for: access keys or passwords unused for a long window — candidates for removal entirely
5. Take action: enforce MFA, force rotation, deactivate/remove stale credentials
```

## Automating This

Manually reviewing this report periodically is a reasonable starting point, but the report can also be consumed programmatically (via the `GetCredentialReport` API) and fed into automated compliance checks — e.g., an AWS Config rule or a scheduled Lambda that flags any user without MFA or with an access key older than a defined threshold, rather than depending on someone remembering to run the report manually.

## Senior-Level Considerations

- This report is specifically about IAM **users'** credentials — it has nothing to say about roles, since roles don't have long-term passwords or access keys to report on in the first place, which is itself a useful reminder of why roles are the preferred pattern
- Combining this report's findings with an account-wide push toward federation and role-based access (reducing the number of IAM users with standing credentials at all) addresses the root cause rather than just repeatedly cleaning up the same category of finding every review cycle
