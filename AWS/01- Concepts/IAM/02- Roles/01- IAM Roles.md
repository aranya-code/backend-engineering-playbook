# IAM Roles

## Definition

IAM roles are secure AWS identities with specific permissions that can be assumed by trusted entities — users, applications, or AWS services — rather than being uniquely tied to a single person the way a user is.

## No Long-Term Credentials

Unlike IAM users, roles do not have passwords or long-term access keys. Instead, whoever assumes a role receives **temporary security credentials** (an access key, secret key, and session token) via AWS STS, valid for a bounded window — typically 1 hour by default, configurable up to 12 hours depending on the role's settings.

## The Two Policies Every Role Has

A role's security model has two distinct, independently-configured parts:

| Policy Type | Answers |
|---|---|
| **Trust Policy** | *Who* is allowed to assume this role? |
| **Permission Policy** | *What* can this role do once assumed? |

A trust policy that's too permissive is just as dangerous as an overly broad permission policy — a role with narrow permissions but a trust policy allowing "anyone" to assume it is still a serious exposure.

## Why Roles Are Preferred Over Long-Term Credentials

- **Automatic expiration** — a leaked temporary credential is only useful for its remaining validity window, often under an hour, versus a leaked access key that's valid indefinitely until manually revoked
- **No credential to manage or rotate** — nothing to store, no rotation schedule to maintain, no risk of it being committed to a repo by accident
- **Auditable assumption events** — CloudTrail logs every `AssumeRole` call, giving clear visibility into who assumed what, when

## Common Role Use Cases

- An EC2 instance needing to call S3 or DynamoDB (via an instance profile — see that file)
- A Lambda function needing to write to a database
- A user or CI/CD pipeline federating in from an external identity provider (see `Cross-Account Roles.md` and the Identity Federation content in AWS-Security)
- Cross-account access, where an identity in one account temporarily assumes a role in another

## Senior-Level Considerations

- The trust policy and permission policy are evaluated as two entirely separate questions — "am I allowed to assume this role" and "what can I do once I have" — and both need to be correct for a role to work as intended
- Session duration should be tuned per role's sensitivity — a highly privileged role is a reasonable candidate for a shorter maximum session duration than a low-risk, read-only one
