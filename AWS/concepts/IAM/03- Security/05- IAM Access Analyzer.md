# IAM Access Analyzer

## What Problem It Solves

Access Advisor (see Monitoring) tells you what a specific identity *has used*. Access Analyzer answers a different, equally important question: **does anything in this account grant access to an external entity that shouldn't have it?**

## How It Works

Access Analyzer uses automated reasoning (a formal, mathematical analysis of policy logic — not simple pattern matching) to examine resource-based policies (S3 bucket policies, IAM role trust policies, KMS key policies, and others) and identify any that grant access to a principal **outside** a defined "zone of trust" (typically your account or your AWS Organization).

## Example Findings

- An S3 bucket policy that unintentionally grants public read access
- An IAM role whose trust policy allows an external AWS account to assume it, where that external access wasn't actually intended
- A KMS key policy granting decrypt permissions to a principal outside the organization

## Access Analyzer vs. Manually Reviewing Policies

Manually reading every resource-based policy across a large account for unintended external access doesn't scale, and subtle policy logic (nested conditions, wildcard principals) is genuinely easy to misjudge by eye. Access Analyzer's automated reasoning approach can definitively determine what a policy *actually* allows, not just what it appears to allow on a quick read.

## Access Analyzer Also Generates Least-Privilege Policies

A second major capability: Access Analyzer can review a role's actual CloudTrail activity over a period of time and generate a policy scoped to exactly the actions and resources it actually used — a concrete, automated way to implement Least Privilege (see that file) rather than manually guessing at a minimal permission set.

## Senior-Level Considerations

- Access Analyzer findings need the same thing every detection tool needs (see Security Monitoring in AWS-Security): an actual review and remediation process, not just a dashboard nobody checks — an unintended-access finding that sits unreviewed provides no real protection
- Setting up Access Analyzer at the AWS Organization level (rather than per-account) gives a single, comprehensive view across every account's external-access posture, which is the practical way most real organizations actually run it
- The distinction from Access Advisor is worth being precise about in an interview: Access Advisor is about *unused* permissions for identities *within* your account; Access Analyzer is about *unintended external* access via resource-based policies — related but answering genuinely different questions
