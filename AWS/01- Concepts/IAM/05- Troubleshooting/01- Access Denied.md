# Troubleshooting: Access Denied

## Step 1 — Read the Actual Error Message Carefully

AWS `AccessDenied` errors usually name the specific action and resource that were denied — this is the single most useful piece of information and is easy to skim past under frustration. Confirm exactly which action, on which resource, by which principal, before investigating further.

## Common Causes, Roughly in Order of Likelihood

**Missing permission entirely** — the identity-based policy simply doesn't grant the action. Check every attached policy (direct, group-attached, and any inline policies) for the specific action and resource.

**An explicit Deny somewhere in the chain** — remember that explicit deny always wins (see Policy Evaluation Logic), regardless of any Allow elsewhere. Check for deny statements in identity-based policies, resource-based policies, permission boundaries, and (if applicable) SCPs.

**Wrong resource ARN** — the policy allows the action, but on a different resource than the one being accessed (a typo in the ARN, a wildcard that doesn't actually match the specific resource path, or an account ID mismatch).

**SCP restrictions** — even a permission that's clearly allowed by the identity-based policy can be blocked by an Organization-level SCP, which applies regardless of anything the account's own IAM policies say.

**Missing resource-based policy grant** — for cross-account access, or for services like S3/SQS/KMS that support resource-based policies, both the identity-based policy *and* the resource-based policy need to allow the action.

**Missing `sts:AssumeRole` permission** — if the failure happens while trying to assume a role, the calling identity needs its own `sts:AssumeRole` permission on the target role's ARN, separate from whatever permissions the target role itself would grant once assumed.

## A Practical Debugging Sequence

```text
1. Identify exactly which action + resource + principal was denied (from the error)
2. Check the identity-based policies attached to that principal
3. Check for permission boundaries on that principal
4. Check applicable SCPs, if in an Organization
5. If the resource supports resource-based policies, check those too
6. Use the IAM Policy Simulator to test the request against the actual policy chain
```

## Using the IAM Policy Simulator

AWS provides a Policy Simulator specifically for this: it evaluates a hypothetical request against an identity's actual attached policies (and can factor in resource-based policies and SCPs in some cases) and reports Allow/Deny with an explanation of which statement produced that result — genuinely useful for confirming a fix *before* deploying a policy change.

## Senior-Level Considerations

- Resist the instinct to "just add `*:*` to unblock this" — it resolves the symptom immediately but reintroduces exactly the least-privilege problem this troubleshooting process exists to avoid; find the specific missing permission instead
- Cross-account access denials should always prompt checking *both* accounts' policies, not just the one you have direct control over — a very common mistake is repeatedly tweaking the calling side's policy when the actual gap is in the target account's resource-based or trust policy
