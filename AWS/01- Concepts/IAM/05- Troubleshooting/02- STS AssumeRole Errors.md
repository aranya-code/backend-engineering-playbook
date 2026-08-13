# Troubleshooting: STS AssumeRole Errors

## Common Causes

**Missing trust relationship** — the target role's trust policy doesn't list the calling principal at all. This is the most common root cause and the first thing worth checking.

**Incorrect Principal in the trust policy** — a typo in the account ID, an ARN pointing to the wrong role, or specifying a service principal when the actual caller is a different type of identity entirely.

**Missing `sts:AssumeRole` permission on the caller's side** — the trust policy might correctly allow the caller, but the caller's own identity-based policy also needs explicit `sts:AssumeRole` permission on that specific role ARN; both sides of this relationship need to independently agree.

**Cross-account trust misconfiguration** — for cross-account AssumeRole, common specific mistakes include: the target role's trust policy references the wrong account ID, or an `ExternalId` condition is present but the caller isn't passing a matching value.

**Session duration exceeding the role's maximum** — requesting a session duration longer than the role's configured maximum session duration (default 1 hour, configurable up to 12) results in a validation error, distinct from a permissions issue entirely.

**MFA condition not satisfied** — if the trust policy requires `aws:MultiFactorAuthPresent`, and the calling session wasn't authenticated with MFA, the assume-role call is denied even though every other condition is correctly configured.

## A Practical Debugging Sequence

```text
1. Confirm the exact role ARN being assumed is correct (a common, simple mistake)
2. Check the target role's trust policy — does its Principal include this caller?
3. Check any Condition blocks on the trust policy (ExternalId, MFA) — are they satisfied?
4. Check the caller's own identity-based policy — does it grant sts:AssumeRole on this role ARN?
5. Check the requested session duration against the role's configured maximum
```

## Reading the Specific Error

- `"is not authorized to perform: sts:AssumeRole"` — almost always a trust policy or caller-permission mismatch (steps 2–4 above)
- A validation error mentioning duration — a session duration request exceeding the role's maximum (step 5)
- An error referencing an external ID — a missing or mismatched `ExternalId` on a cross-account assume (step 3)

## Senior-Level Considerations

- Because both the trust policy (on the target role) and the caller's own policy need to independently allow the assume-role call, a debugging session should explicitly check both sides rather than assuming the problem is wherever you happen to have easier access to look first
- This class of error is a common practical test of whether someone actually understands the two-policy structure of roles (trust policy vs. permission policy) rather than just having memorized that "roles use policies" abstractly
