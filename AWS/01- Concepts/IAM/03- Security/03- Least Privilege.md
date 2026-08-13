# Least Privilege

## The Principle

Grant only the minimum permissions required for a user, role, or service to perform its actual task — nothing more "just in case," and nothing broad "to save time" during initial setup.

## Why It's Harder Than It Sounds

Determining the *exact* minimum permission set an application genuinely needs requires either deep upfront knowledge of every API call it will make, or an iterative process of starting narrow and adding permissions as legitimate `AccessDenied` errors surface — both take real, deliberate effort compared to just attaching `AdministratorAccess` and moving on, which is exactly why least privilege is so often skipped under time pressure despite being well understood.

## Practical Techniques

- **Start narrow, expand deliberately** — begin with minimal permissions and add specific actions as genuine needs are identified, rather than starting broad and hoping to narrow later (which rarely actually happens once something "works")
- **Use IAM Access Advisor** (see Monitoring) to review what permissions an existing identity has *actually used* over the past 90+ days, and remove what's unused
- **Use AWS Access Analyzer** (see that file) to generate a least-privilege policy automatically based on a role's actual CloudTrail activity
- **Scope `Resource` to specific ARNs** rather than `*` wherever the use case allows it
- **Use `Condition` blocks** to further restrict even a necessarily-broad action (e.g., limit to a specific VPC endpoint, IP range, or time window)

## The Cost of Getting This Wrong

An overly broad policy doesn't cause a problem *until* the identity holding it is compromised — at which point the blast radius is exactly as large as the unused permissions that were never trimmed. Least privilege isn't about preventing normal operation; it's about minimizing the damage ceiling if something goes wrong.

## Least Privilege Is Not a One-Time Task

Permission needs change as an application evolves, and unused permissions tend to accumulate rather than disappear on their own — a policy that was appropriately scoped a year ago may now be far broader than the identity's current actual usage, simply because nobody removed anything as requirements shifted. Regular reviews (via Access Advisor or Access Analyzer) are what keep this from silently drifting.

## Senior-Level Considerations

- "Explicit deny wins" (see Policy Evaluation Logic) makes explicit deny statements a useful tool for enforcing least privilege guardrails even on top of an otherwise broad policy — e.g., explicitly denying a small number of especially dangerous actions regardless of what else is granted
- Least privilege and developer velocity are a real, ongoing tension — the senior-level skill isn't picking one over the other permanently, but building processes (fast, low-friction permission requests; automated tooling like Access Analyzer) that keep velocity high without reflexively defaulting to overly broad access
