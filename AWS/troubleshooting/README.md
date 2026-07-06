# AWS Troubleshooting

A collection of real-world AWS issues encountered during hands-on practice, organized by service. Each guide documents the **error**, **root cause**, **step-by-step resolution**, **CLI verification commands**, and **exam-relevant notes**.

---

## 📚 Issues by Service

### Amazon S3 (3 Issues)

| # | Issue | Error | Root Cause |
|---|-------|-------|------------|
| 01 | [NoSuchBucket Error](./S3/01-%20NoSuchBucket%20Error.md) | `NoSuchBucket` | CLI profile name mistakenly passed as a bucket name instead of using `--profile` |
| 02 | [MFA Delete Enable Failure](./S3/02-%20MFA%20Delete%20Enable%20Failure.md) | `NotDeviceOwnerError` | Placeholder values used for MFA device ARN and token instead of actual credentials |
| 03 | [AccessDenied — MFA Delete After Key Deletion](./S3/03-%20AccessDenied%20Error.md) | `AccessDenied` | Root access key deleted after enabling MFA Delete, locking out CLI management |

📂 **Path:** [`S3/`](./S3)

---

### Amazon EBS (1 Issue)

| # | Issue | Error | Root Cause |
|---|-------|-------|------------|
| 01 | [Root Volume Detach Failure](./EBS/01-%20Root%20Volume%20Detach%20Failure.md) | `Unable to detach root volume` | AWS prevents detaching a root EBS volume from a running EC2 instance |

📂 **Path:** [`EBS/`](./EBS)

---

## Quick Reference

### S3 — NoSuchBucket Error

**Symptom:** `aws s3 ls root-mfa-delete-demo` returns `NoSuchBucket`.

**Fix:** The argument was treated as a bucket name. Use the `--profile` flag:
```diff
- aws s3 ls root-mfa-delete-demo
+ aws s3 ls --profile root-mfa-delete-demo
```

> **📝 Exam Note:** AWS CLI profile names and S3 bucket names are completely different concepts — profiles are for authentication, bucket names are resource identifiers.

---

### S3 — MFA Delete Enable Failure

**Symptom:** `NotDeviceOwnerError` when enabling MFA Delete on a bucket.

**Fix:** Replace placeholder values with the actual MFA device ARN and a current 6-digit token:
```diff
- --mfa "arn-of-mfa-device mfa-code"
+ --mfa "arn:aws:iam::508931100893:mfa/root-account-mfa-device 123456"
```

> **📝 Exam Note:** Only the **Root Account** can enable or disable MFA Delete — IAM users cannot.

---

### S3 — AccessDenied After Root Key Deletion

**Symptom:** Cannot disable MFA Delete after accidentally deleting the root access key.

**Fix:**
1. Create a **new root access key** via Console → Security Credentials → Access Keys
2. Reconfigure the CLI profile with `aws configure --profile root-mfa-delete-demo`
3. Retry the disable command with the new credentials
4. If key creation is restricted → open an **AWS Support case**

> **📝 Exam Note:** MFA Delete **cannot** be managed from the AWS Console — it requires CLI/API with root credentials.

---

### EBS — Root Volume Detach Failure

**Symptom:** `Unable to detach root volume vol-xxx from instance i-xxx`.

**Fix:**

| Instance State | Action |
|---------------|--------|
| **Running** | Stop the instance first, then detach |
| **Stuck in "Stopping"** | Force stop, wait, then detach |
| **Terminated** | Check volume attachment metadata with `describe-volumes` |

**Cost Optimization:**
- **Option A:** Terminate the instance (root volume auto-deletes if `DeleteOnTermination` is enabled)
- **Option B:** Stop → Snapshot → Delete Volume (preserves data)

> **📝 Exam Note:** Root EBS volumes **cannot** be detached from a running instance. Non-root (data) volumes **can**.

---

## Interview Quick-Fire

| Question | Answer |
|----------|--------|
| Can a root EBS volume be detached from a running instance? | **No** — stop the instance first |
| Can a non-root EBS volume be detached while running? | **Yes** |
| Can IAM users enable/disable MFA Delete? | **No** — root account only |
| Can MFA Delete be managed from the AWS Console? | **No** — CLI/API only |
| Is an AWS CLI profile name the same as an S3 bucket name? | **No** — profiles are for auth, buckets are resources |

---

## Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [AWS](../README.md) |

---

> **Part of the [Backend Engineering Playbook](../../) — a structured learning resource for backend engineers.**
