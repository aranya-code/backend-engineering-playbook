# Block Public Access

---

# Introduction

One of the most common causes of cloud security incidents is the accidental exposure of sensitive data through publicly accessible Amazon S3 buckets. To help prevent these mistakes, AWS introduced **S3 Block Public Access**, a security feature that overrides bucket policies and Access Control Lists (ACLs) that would otherwise make objects publicly accessible.

For most production workloads, **Block Public Access should remain enabled**.

---

# Why Block Public Access Exists

Before this feature was introduced, many organizations unintentionally exposed confidential information by configuring permissive bucket policies or object ACLs.

Common examples include:

- Customer data
- Financial reports
- Database backups
- Application source code
- Internal documents
- Log archives

A single misconfigured policy could expose millions of objects to the internet.

> 💡 **Engineering Insight**
>
> Security incidents involving publicly accessible S3 buckets are almost always configuration mistakes rather than AWS platform failures.

---

# How Block Public Access Works

Block Public Access acts as an additional security layer.

Even if a bucket policy or ACL attempts to grant public access, Block Public Access can prevent the request from succeeding.

```text
Request
   │
   ▼
Block Public Access
   │
   ├── Public Access Allowed?
   │
   ├── No → Continue Policy Evaluation
   │
   └── Yes → Access Blocked
```

This protection applies before public access can be granted.

---

# Block Public Access Settings

Amazon S3 provides four independent settings.

## Block Public ACLs

Prevents new public ACLs from being created.

---

## Ignore Public ACLs

Ignores existing public ACLs when evaluating requests.

---

## Block Public Bucket Policies

Prevents bucket policies that allow public access.

---

## Restrict Public Buckets

Restricts access to buckets that have public policies, allowing only authorized AWS principals and services.

---

# Account-Level vs Bucket-Level

Block Public Access can be configured at two levels:

### Account Level

Applies to all buckets within an AWS account.

Recommended for most organizations.

### Bucket Level

Applies only to an individual bucket.

Useful when a small number of buckets legitimately require different behavior.

---

# When Should Public Access Be Allowed?

Most buckets should **never** be publicly accessible.

Legitimate exceptions include:

- Static website hosting
- Public software downloads
- Public documentation
- Open datasets

Even in these cases, review permissions carefully and expose only the required objects.

> 🏗️ **Production Pattern**
>
> Rather than making an S3 bucket public, many organizations place Amazon CloudFront in front of S3 and keep the bucket private using Origin Access Control (OAC).

---

# Best Practices

- Enable Block Public Access at the account level.
- Leave all four settings enabled unless there is a documented business requirement.
- Use IAM roles and bucket policies instead of public access.
- Review bucket permissions regularly.
- Monitor configuration changes with AWS Config and CloudTrail.

---

# Common Mistakes

- Disabling Block Public Access to solve an application access issue.
- Using public buckets for internal applications.
- Assuming object ACLs override Block Public Access.
- Forgetting to re-enable Block Public Access after testing.

> ⚠️ **Common Mistake**
>
> If an application receives **Access Denied**, do not immediately disable Block Public Access. Verify IAM permissions, bucket policies, and application configuration first.

---

# Key Takeaways

Block Public Access is one of the most important security features in Amazon S3. It helps prevent accidental exposure of sensitive data by blocking public bucket policies and ACLs before they can grant internet access.

For nearly every production environment, enabling Block Public Access at the account level should be considered a security baseline.

In the next chapter, we'll explore **Object Ownership** and learn how modern Amazon S3 deployments eliminate ACLs in favor of simplified ownership and policy-based access control.
