# Credential Rotation

## Why Rotation Matters

A credential's risk isn't just "could it leak" — it's "if it leaks, how long is it useful to an attacker before it stops working." Regular rotation bounds that window, turning "we don't know how long this has been exposed" into "this credential has been invalid for at most N days" during an incident.

## What Gets Rotated

| Credential | Rotation Approach |
|---|---|
| IAM user passwords | Enforce a password policy with a maximum age (e.g., 90 days) |
| IAM access keys | Rotate periodically — create a new key, update wherever it's used, then deactivate and delete the old one |
| Database credentials | Automatic rotation via Secrets Manager (see AWS-Security) for supported databases |
| Role session credentials | Automatic — STS-issued temporary credentials expire on their own, no manual rotation needed at all |

## The Manual Access Key Rotation Process

```text
1. Create a new access key (a user can have up to 2 active at once, specifically to support this overlap)
2. Update the application/config to use the new key
3. Verify the new key is working correctly
4. Deactivate the old key (don't delete yet — deactivating is reversible if something was missed)
5. After confirming nothing broke, delete the old key
```

The two-key limit exists precisely to support this safe overlap — attempting to rotate a key that's the *only* one active risks an outage if something depends on it that wasn't accounted for.

## Removing Unused Credentials

Stale, unused access keys and passwords are a pure liability with no offsetting benefit — an unused credential that still works is exactly as dangerous as an actively-used one if it leaks, but provides no value in exchange. IAM Credentials Report (see Monitoring) directly surfaces exactly this: which credentials exist and how recently they were used.

## Why This Category of Manual Rotation Is Shrinking

The broader industry (and AWS's own guidance) trend is toward eliminating long-term credentials that need manual rotation at all — replacing IAM user access keys with role-based temporary credentials (for services) and federation (for humans), each of which rotate automatically via STS with no manual process required. Manual credential rotation is increasingly a sign that a long-term credential exists somewhere it arguably shouldn't.

## Senior-Level Considerations

- A rotation *policy* that exists on paper but isn't automated or enforced tends not to actually happen consistently — automating rotation (Secrets Manager's built-in rotation, or a scheduled Lambda for less-standard credentials) is far more reliable than a documented process depending on someone remembering
- The real long-term fix for "credential rotation is a burden" is usually reducing the number of long-term credentials that need rotating in the first place, not just getting better at rotating the ones you have
