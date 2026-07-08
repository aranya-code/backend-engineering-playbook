# IAM Privilege Escalation Paths

## Why This Deserves Its Own File

Least Privilege (see that file) is about minimizing what a single permission grants. Privilege escalation is a related but distinct concern: certain **combinations** of individually-reasonable-looking permissions let an identity grant itself far more access than was ever intended — a risk that reviewing permissions one at a time can completely miss.

## Common Escalation Paths

**Editing a policy you're already allowed to modify**
```text
iam:CreatePolicyVersion → set a new default version of a policy attached to yourself,
                           granting broader permissions than the current version
```
If a user can create new versions of a customer-managed policy already attached to them, they can effectively rewrite their own permissions.

**Reverting to an old, more permissive policy version**
```text
iam:SetDefaultPolicyVersion → roll back to an earlier version of a policy
                               that was more permissive before it was tightened
```

**PassRole combined with a resource-creation permission**
```text
iam:PassRole + lambda:CreateFunction (or ec2:RunInstances, etc.)
   → create a Lambda function (or EC2 instance) and "pass" it a highly-privileged
     execution role, then invoke that function to act with that role's permissions
```
This is the single most well-known IAM escalation pattern. `iam:PassRole` alone looks harmless — it just lets you *assign* a role to a resource — but combined with permission to create that resource and control what it runs, it becomes a path to effectively gain that role's full permission set.

**Attaching a more permissive policy to yourself**
```text
iam:AttachUserPolicy / iam:AttachRolePolicy → attach AdministratorAccess
                                               (or any broader managed policy) to your own identity
```

**Modifying a role's trust policy to add yourself**
```text
iam:UpdateAssumeRolePolicy → add yourself as an allowed principal on a
                              highly-privileged role's trust policy, then assume it
```

**Creating access keys for another, more privileged user**
```text
iam:CreateAccessKey → generate long-term credentials for a different,
                       higher-privileged IAM user, if permitted to do so
```

## The Underlying Lesson

None of `iam:CreatePolicyVersion`, `iam:PassRole`, or `iam:AttachUserPolicy` look dangerous in isolation — they're exactly the kind of administrative-adjacent permissions that get granted without much scrutiny. The risk only becomes visible when considering what an identity can do by **chaining** permissions together, which is precisely why a permission-by-permission review is insufficient for catching this class of risk.

## Detection and Mitigation

- **IAM Access Analyzer's** policy generation and unintended-access findings help here, but the specific escalation-path pattern is also directly checkable with dedicated open-source tooling (e.g., PMapper, IAM Vulnerable-style scanners) designed to graph exactly these permission combinations across an account
- **Permission boundaries** (see Policies) are a direct, practical mitigation — a boundary that excludes `iam:*` entirely prevents a role from modifying its own or others' policies, closing off several of the paths above regardless of what its identity-based policy grants
- **Avoid granting `iam:PassRole` broadly** — scope it to the specific role ARN(s) that actually need to be passed, with a `Condition` restricting which service can receive it, rather than `Resource: "*"`
- **Restrict IAM-modifying permissions to a small, deliberately trusted set of administrative roles**, never bundled casually into a broader "developer" policy for convenience

## Senior-Level Considerations

- This is one of the highest-value things to explicitly check for in a security review, precisely because it's invisible to anyone reviewing permissions individually rather than thinking about achievable permission *combinations*
- A genuinely useful mental exercise: for any identity with `iam:PassRole`, ask "what's the most privileged role this identity could pass to a resource it can create or control?" — if the answer is "anything," that's a real, fixable gap
- This topic connects directly back to Policy Evaluation Logic and Least Privilege — privilege escalation paths are really just least-privilege violations that are one indirect step removed from being obvious
