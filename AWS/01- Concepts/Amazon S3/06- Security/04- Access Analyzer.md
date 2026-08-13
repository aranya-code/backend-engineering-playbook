# IAM Access Analyzer

---

# Introduction

As AWS environments grow, permissions become increasingly difficult to manage. Bucket Policies, IAM Policies, Access Points, and cross-account roles can unintentionally expose Amazon S3 resources to users outside your organization.

**IAM Access Analyzer** is an AWS security service that continuously analyzes resource policies and identifies unintended public or cross-account access. Rather than waiting for a security incident, Access Analyzer helps engineers detect and fix overly permissive access before sensitive data is exposed.

For production environments, IAM Access Analyzer is an essential governance tool for Amazon S3.

---

# Learning Objectives

In this chapter you'll learn:

- What IAM Access Analyzer is
- How it works
- Public access findings
- Cross-account access findings
- External access analysis
- Unused access analysis
- Production workflows
- Best practices
- Common mistakes

---

# What is IAM Access Analyzer?

IAM Access Analyzer evaluates resource-based policies using automated reasoning.

It analyzes resources such as:

- Amazon S3 Buckets
- AWS KMS Keys
- IAM Roles
- Amazon SQS Queues
- AWS Secrets Manager Secrets

For Amazon S3, it determines whether a bucket can be accessed by:

- The public
- Another AWS account
- An AWS Organization outside your own

> 💡 **Engineering Insight**
>
> IAM Access Analyzer doesn't change permissions—it identifies risky permissions so you can review and remediate them.

---

# How Access Analyzer Works

```text
Bucket Policy
      │
      ▼
IAM Access Analyzer
      │
Analyze Resource Policy
      │
 ┌────┴────────────┐
 │                 │
No External     External Access
Access              Found
 │                 │
 ▼                 ▼
Healthy         Security Finding
```

Whenever a policy allows unintended external access, Access Analyzer generates a finding.

---

# Types of Findings

## Public Access

Detects resources that can be accessed by anyone.

Example:

```text
Principal: "*"
```

Public buckets are one of the most common causes of S3 data exposure.

---

## Cross-Account Access

Detects buckets shared with AWS accounts outside your organization.

Common legitimate examples include:

- Central logging
- Shared data lakes
- Backup accounts
- CI/CD pipelines

The analyzer helps distinguish expected sharing from accidental exposure.

---

## Unused Access

IAM Access Analyzer can also recommend least-privilege improvements by identifying permissions that haven't been used over a period of time.

This helps security teams reduce excessive IAM permissions.

> 🏗️ **Production Pattern**
>
> Run Access Analyzer continuously and review new findings as part of your deployment pipeline or security operations process.

---

# Integration with Amazon S3

Typical workflow:

```text
Developer
     │
Deploy Bucket Policy
     │
     ▼
IAM Access Analyzer
     │
Analyze Policy
     │
Finding Generated?
     │
 ┌───┴────┐
 │        │
No       Yes
 │        │
 ▼        ▼
Done   Investigate
```

Many organizations require that all high-severity findings be resolved before infrastructure changes are promoted to production.

---

# Best Practices

- Enable IAM Access Analyzer in every AWS account.
- Review findings regularly.
- Investigate all public bucket findings immediately.
- Validate intentional cross-account access.
- Combine with AWS Config and Security Hub.
- Integrate checks into CI/CD pipelines.

---

# Common Mistakes

- Ignoring informational findings.
- Assuming public access is always intentional.
- Granting broad permissions without review.
- Treating Access Analyzer as a replacement for IAM design.

> ⚠️ **Common Mistake**
>
> Access Analyzer identifies exposure—it does not automatically remove risky permissions. Security teams must review and remediate findings.

---

# Interview Questions

**Q:** Does IAM Access Analyzer modify IAM or Bucket Policies?

**A:** No. It analyzes policies and generates findings but never changes permissions automatically.

**Q:** What types of S3 exposure can it detect?

**A:** Public access, cross-account access, and other external access allowed through resource-based policies.

---

# Key Takeaways

IAM Access Analyzer provides continuous visibility into unintended public and cross-account access for Amazon S3. By integrating it with security reviews, CI/CD pipelines, and governance processes, organizations can proactively identify risky bucket configurations before they lead to data exposure.

In the next chapter, we'll explore **Amazon S3 Access Points** and learn how they simplify secure access management for shared datasets and large-scale applications.
