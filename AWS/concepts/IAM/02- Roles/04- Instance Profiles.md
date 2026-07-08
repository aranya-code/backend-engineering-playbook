# Instance Profiles

## The Missing Link Between EC2 and IAM Roles

IAM roles themselves cannot be attached directly to an EC2 instance — an **instance profile** is the actual container that makes this possible. In the console, creating a role "for EC2" automatically creates a matching instance profile behind the scenes, which is why this distinction is easy to miss entirely — but it matters for anyone working with the AWS CLI or infrastructure-as-code directly, where the instance profile is a separate resource you must create and reference explicitly.

## How It Actually Works

```text
EC2 Instance
     ↓ (has an attached Instance Profile)
Instance Profile
     ↓ (contains exactly one IAM Role)
IAM Role
     ↓ (has a trust policy allowing ec2.amazonaws.com, and a permission policy)
Permissions
```

## The Credential Delivery Mechanism

Once an instance profile (and its role) is attached to a running instance, the EC2 service automatically makes temporary credentials for that role available to the instance via the **Instance Metadata Service (IMDS)**, refreshed automatically before they expire — application code on the instance retrieves them from `http://169.254.169.254/...` rather than ever needing a hardcoded access key baked into an AMI or config file.

## Why This Matters for Security

Before instance roles existed as a pattern, applications on EC2 commonly had IAM access keys hardcoded into configuration files or environment variables on the instance — a standing, long-lived credential sitting on every instance, at risk if the instance were ever compromised. Instance profiles eliminate this entirely: no credential is ever stored on disk, and the credentials delivered via IMDS are short-lived and automatically rotated by AWS.

## Practical Notes

- An instance can have **only one** instance profile (and therefore effectively one role) attached at a time — if a workload needs a broader set of permissions, they need to live in that one role's permission policy, not spread across multiple roles
- Changing which role is attached to a running instance takes effect without needing to stop/restart the instance — new API calls will use the newly attached role's permissions going forward
- IMDSv2 (a hardened version of the metadata service requiring session-oriented requests) is the current best practice specifically because IMDSv1 was a real vector for SSRF-based credential theft — this is covered in depth in `EC2/EC2-Instance-Metadata.md`

## Senior-Level Considerations

- "Attach a role to an EC2 instance" is technically shorthand for "attach an instance profile containing that role" — precise enough to matter when working outside the console (CLI, Terraform, CloudFormation all require creating/referencing the instance profile as its own resource)
- This same instance-profile-and-credential-delivery pattern conceptually extends to how other AWS compute services (ECS task roles, Lambda execution roles) deliver credentials to running code — the specific delivery mechanism differs by service, but the underlying principle (temporary credentials delivered automatically, nothing hardcoded) is the same
