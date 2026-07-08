# IAM Access Advisor

## What It Shows

For a given IAM user, group, or role, Access Advisor lists every AWS service that identity's attached policies grant permission to, alongside the **last time that service was actually accessed** (where AWS can track it) — directly answering "what does this identity actually use, versus what it's merely allowed to use."

## Why This Is the Core Tool for Least Privilege in Practice

Knowing an identity's permissions on paper doesn't tell you whether those permissions are needed. An identity with `AdministratorAccess` that Access Advisor shows has only ever touched S3 and DynamoDB over the past 90 days is a clear, concrete signal that its actual permission set could be scoped down dramatically without breaking anything real.

## Working With Access Advisor Data

```text
1. Open Access Advisor for a role/user
2. Review the "Last Accessed" column per service
3. Services never accessed (or not accessed in a long window) are strong candidates for removal
4. Narrow the policy accordingly, then monitor for any resulting AccessDenied errors before considering it final
```

## Limitations Worth Knowing

- Tracks access at the **service level** (e.g., "S3 was accessed"), and in some cases action-level granularity for certain services — it's not a perfect record of every single specific API call made, though action-level tracking has expanded over time for many services
- "Never accessed" doesn't necessarily mean "safe to remove immediately" — a permission used only rarely (an annual process, a disaster-recovery-only action) could show as unused in a 90-day window while still being genuinely needed; context matters, not just the raw data

## Access Advisor vs. Access Analyzer

Easy to conflate given the similar names — Access Advisor looks *inward*, at what a specific identity has actually used from its own permissions. Access Analyzer (see Security) looks *outward*, at whether resource policies grant unintended access to external principals. Different questions, different tools.

## Senior-Level Considerations

- Access Advisor data is most useful as a *before-you-remove-permissions* sanity check — combined with actually testing after a policy narrowing, not as a substitute for verifying nothing broke
- For roles with genuinely infrequent-but-legitimate use cases (annual compliance exports, disaster recovery procedures), document that context explicitly rather than relying on institutional memory to prevent someone from "cleaning up" a permission that's rarely used but still needed
