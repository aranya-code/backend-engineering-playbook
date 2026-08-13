# Users vs Groups vs Roles

## IAM User

A persistent identity representing a person or an application, with long-term credentials (a password for console access, and/or access keys for programmatic access).

**Best fit:** individual human access when federation isn't set up, or in rare cases a genuinely long-lived application identity — though roles are strongly preferred for applications today (see Roles).

## IAM Group

A named collection of users, used purely to attach policies to many users at once rather than repeating the same policy attachment per user.

**Key limitation:** a group can only contain users — **groups cannot be nested inside other groups**, and a group cannot be assumed like a role. It exists solely as a policy-attachment convenience.

## IAM Role

A temporary, assumable identity with **no long-term credentials at all** — instead, whoever assumes it (a user, an application, an AWS service) receives short-lived, automatically-expiring credentials via STS.

**Best fit:** AWS services acting on your behalf (EC2 instances, Lambda functions), cross-account access, and federated human access — the default choice for nearly every scenario today, over long-lived user credentials.

## Quick Comparison

| | User | Group | Role |
|---|---|---|---|
| Has credentials? | Yes (long-term) | No (not an identity itself) | Yes (temporary, via STS) |
| Can be assumed? | No | No | Yes |
| Can contain other entities? | No | Users only | No |
| Typical use | Human console access (legacy pattern) | Bulk policy attachment for users | Services, cross-account access, federation |

## Why This Distinction Is a Common Interview Question

It tests whether you understand the shift AWS security best practice has made over time: away from long-lived user credentials (a standing liability if leaked) and toward roles with temporary, automatically-rotating credentials wherever possible. A candidate who says "just create a user with access keys for that" for a service-to-service integration is signaling outdated practice.

## Senior-Level Considerations

- A user can belong to multiple groups simultaneously, and its effective permissions are the union of all attached policies — direct user policies, group policies, and (if applicable) permission boundaries all apply together
- "Can a role be a member of a group?" — no. Groups exist only for users. This is a genuinely common point of confusion worth being precise about
- The industry-wide trend (and AWS's own guidance) is to minimize IAM users with long-term credentials entirely — using IAM Identity Center or federation for humans, and roles for everything programmatic
