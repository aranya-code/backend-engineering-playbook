# IAM Interview Questions

## Beginner

**Q1. What's the difference between an IAM user and an IAM role?**
A user has long-term credentials (password/access keys) and represents a persistent identity. A role has no long-term credentials — it's assumed temporarily, issuing short-lived credentials via STS, and is the preferred pattern for applications and services.

**Q2. What's the difference between inline and managed policies?**
Inline policies are embedded directly in a single identity and aren't reusable. Managed policies are standalone objects (AWS-managed or customer-managed) that can be attached to multiple identities and support versioning.

**Q3. What is AssumeRole?**
The STS action that exchanges an existing identity's credentials for temporary credentials matching a target role, provided the role's trust policy allows the caller.

**Q4. Why are IAM roles considered safer than long-term access keys?**
Role credentials are temporary and auto-expire (often within an hour), drastically limiting the usefulness of a leaked credential compared to a long-term access key that remains valid until manually revoked.

**Q5. What's the difference between authentication and authorization?**
Authentication confirms who you are (a password, an access key, a federated token). Authorization determines what you're allowed to do once authenticated, based entirely on attached policies — these are separate, sequential checks.

## Intermediate

**Q6. Explain the structure of an IAM policy document.**
A `Version`, an optional `Id`, and one or more `Statement` entries — each with an `Effect` (Allow/Deny), `Action`, `Resource`, and optionally `Principal` (for resource-based policies) and `Condition`.

**Q7. What's the difference between identity-based and resource-based policies?**
Identity-based policies attach to a user, group, or role. Resource-based policies (e.g., an S3 bucket policy) attach directly to a resource and specify a `Principal`. For cross-account access, both sides typically need to independently grant the access.

**Q8. What is a permission boundary, and how does it differ from a regular policy?**
A permission boundary sets the maximum permissions an identity-based policy is allowed to grant to a specific user or role — it doesn't grant anything itself; the effective permission is the intersection of the identity-based policy and the boundary, never the union.

**Q9. What's the difference between a permission boundary and an SCP?**
A permission boundary applies to one specific user or role. An SCP applies at the AWS Organizations level to entire accounts or OUs, restricting every identity in the account — including its root user — and requires an Organization to use at all.

**Q10. What is an instance profile, and why does it matter for EC2?**
The container object that actually attaches an IAM role to an EC2 instance — roles can't be attached directly. It's what makes the instance metadata service able to deliver automatically-rotating temporary credentials to code running on the instance, with no hardcoded access key needed.

## Senior / Advanced

**Q11. Walk through exactly how AWS resolves multiple applicable policies into a single Allow/Deny decision.**
Default is implicit deny. SCPs are evaluated first — any SCP deny ends evaluation immediately. Then resource-based, identity-based, permission boundary, and session policies are all evaluated; if any explicit Deny appears anywhere in this chain, the request is denied regardless of any Allow elsewhere. If at least one explicit Allow exists and no Deny was found, the request is allowed.

**Q12. Why does cross-account S3 access require configuration on both accounts?**
The accessing account's identity-based policy must allow the S3 action, and the bucket-owning account's bucket policy (a resource-based policy) must separately allow that external principal. Either side alone is insufficient — this is intentional, requiring both parties to agree before cross-account access is granted.

**Q13. What is the "confused deputy" problem, and how does ExternalId address it?**
A scenario where a trusted intermediary (e.g., a SaaS vendor with a role in your account) could potentially be manipulated into acting on behalf of the wrong customer, if the same role-assumption pattern is reused across customers. Requiring a unique `ExternalId` per customer, checked via a trust policy condition, ensures a request is only honored if it includes the value specific to the intended relationship.

**Q14. How would you audit an AWS account for IAM identities with excessive, unused permissions?**
Use the IAM Credentials Report for account-wide credential hygiene (stale keys, missing MFA), Access Advisor per-identity to see actually-used services versus granted permissions, and IAM Access Analyzer both for unintended external access findings and for generating least-privilege policies based on real CloudTrail activity.

**Q15. Design an IAM strategy for a multi-account AWS Organization with a central security team and multiple product teams.**
Use SCPs at the Organization level for non-negotiable guardrails (region restrictions, preventing CloudTrail from being disabled). Give the security team cross-account roles with read-only access into every account for auditing. Let product teams create their own application roles within a permission boundary that caps what they can ever grant themselves, enabling self-service without unbounded risk. Federate all human access through IAM Identity Center rather than per-account IAM users, and require roles (not long-term keys) for every service-to-service integration.
