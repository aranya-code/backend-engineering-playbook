# IAM Users, Groups & Roles

> Learn how to create and manage IAM Users, Groups, and Roles using the AWS CLI. This chapter covers identity management, trust relationships, Instance Profiles, AssumeRole, and production best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Create and manage IAM Users
- Create and manage IAM Groups
- Create and manage IAM Roles
- Understand Trust Policies
- Work with Instance Profiles
- Use AssumeRole
- Manage cross-account roles
- Apply production identity management practices

---

# Understanding IAM Identities

IAM provides three primary identity types.

```text
IAM
│
├── Users
├── Groups
└── Roles
```

Each serves a different purpose.

---

# IAM Users

An IAM User represents a person or application requiring long-term access.

Examples:

- Developer
- Administrator
- CI/CD User
- Automation Account

Each IAM User has:

- Username
- Credentials
- Permissions
- Optional Access Keys
- Optional MFA

---

# List IAM Users

```bash
aws iam list-users
```

---

# Create an IAM User

```bash
aws iam create-user \
--user-name backend-admin
```

Example output:

```json
{
    "User": {
        "UserName": "backend-admin"
    }
}
```

---

# View a User

```bash
aws iam get-user \
--user-name backend-admin
```

Returns:

- Username
- ARN
- Creation Date
- User ID

---

# Delete a User

```bash
aws iam delete-user \
--user-name backend-admin
```

Before deleting a user, remove:

- Access Keys
- Login Profile
- Attached Policies
- Group Membership
- MFA Devices

Otherwise AWS returns an error.

---

# IAM Groups

Groups simplify permission management.

Instead of attaching policies individually:

```text
Developer 1

Developer 2

Developer 3
```

Create:

```text
Developers Group
```

Then attach policies to the group.

---

# List Groups

```bash
aws iam list-groups
```

---

# Create a Group

```bash
aws iam create-group \
--group-name Developers
```

---

# Delete a Group

```bash
aws iam delete-group \
--group-name Developers
```

The group must be empty before deletion.

---

# Add User to Group

```bash
aws iam add-user-to-group \
--user-name backend-admin \
--group-name Developers
```

---

# Remove User from Group

```bash
aws iam remove-user-from-group \
--user-name backend-admin \
--group-name Developers
```

---

# View Group Members

```bash
aws iam get-group \
--group-name Developers
```

Returns:

- Group Details
- Member List

---

# Why Groups Matter

Instead of managing permissions individually:

```text
Developer

↓

Attach Policy
```

Use:

```text
Group

↓

Attach Policy

↓

All Members Receive Permissions
```

This greatly simplifies administration.

---

# IAM Roles

IAM Roles provide temporary credentials.

Unlike IAM Users:

- No password
- No Access Keys
- No permanent identity

Roles are assumed when needed.

---

# Common IAM Role Use Cases

- EC2
- Lambda
- ECS
- EKS
- CloudFormation
- Cross-account access
- GitHub Actions
- CI/CD pipelines

Production workloads should generally use Roles instead of IAM Users.

---

# List Roles

```bash
aws iam list-roles
```

---

# Understanding Trust Policies

Roles require a Trust Policy.

Example:

```json
{
    "Version":"2012-10-17",
    "Statement":[
        {
            "Effect":"Allow",
            "Principal":{
                "Service":"ec2.amazonaws.com"
            },
            "Action":"sts:AssumeRole"
        }
    ]
}
```

This allows Amazon EC2 to assume the role.

---

# Create a Role

```bash
aws iam create-role \
--role-name BackendEC2Role \
--assume-role-policy-document file://trust-policy.json
```

---

# View a Role

```bash
aws iam get-role \
--role-name BackendEC2Role
```

---

# Delete a Role

```bash
aws iam delete-role \
--role-name BackendEC2Role
```

Detach policies before deleting the role.

---

# Instance Profiles

EC2 instances cannot use IAM Roles directly.

Instead:

```text
IAM Role

↓

Instance Profile

↓

EC2 Instance
```

Instance Profiles bridge EC2 and IAM Roles.

---

# Create an Instance Profile

```bash
aws iam create-instance-profile \
--instance-profile-name BackendProfile
```

---

# Add Role to Instance Profile

```bash
aws iam add-role-to-instance-profile \
--instance-profile-name BackendProfile \
--role-name BackendEC2Role
```

---

# List Instance Profiles

```bash
aws iam list-instance-profiles
```

---

# AssumeRole

One IAM identity can temporarily assume another role.

Example:

```bash
aws sts assume-role \
--role-arn arn:aws:iam::123456789012:role/AdminRole \
--role-session-name AdminSession
```

AWS returns temporary credentials.

---

# Cross-Account Access

Example:

```text
Account A

↓

Assume Role

↓

Account B
```

No Access Keys need to be shared.

This is the preferred approach for multi-account environments.

---

# Identity Architecture

```text
IAM User
      │
      ▼
IAM Group
      │
      ▼
IAM Policy
      │
      ▼
AWS Resources
```

For services:

```text
EC2

↓

IAM Role

↓

Instance Profile

↓

Temporary Credentials
```

---

# Common Errors

## EntityAlreadyExists

Example:

```text
EntityAlreadyExists
```

The IAM User, Group, or Role already exists.

Choose another name or use the existing resource.

---

## DeleteConflict

Example:

```text
DeleteConflict
```

Cause:

The resource still has dependencies.

Examples:

- Attached Policies
- Group Membership
- Access Keys
- Instance Profiles

Remove dependencies before deleting.

---

## NoSuchEntity

Example:

```text
NoSuchEntity
```

Verify:

- User Name
- Group Name
- Role Name

IAM resource names are case-sensitive.

---

# Production Best Practices

- Prefer IAM Roles over IAM Users.
- Use Groups for permission management.
- Enable MFA for human users.
- Avoid long-lived Access Keys.
- Use Instance Profiles for EC2.
- Use AssumeRole for cross-account access.
- Follow the Principle of Least Privilege.
- Remove unused identities regularly.

---

# Real-World Workflow

Provisioning a new backend engineer.

```text
Create User
      │
      ▼
Enable MFA
      │
      ▼
Add User to Developers Group
      │
      ▼
Permissions Granted
```

Provisioning a new EC2 server.

```text
Create Role
      │
      ▼
Create Instance Profile
      │
      ▼
Attach Role
      │
      ▼
Launch EC2
      │
      ▼
Temporary Credentials
```

---

# Architecture Note

```text
IAM User
      │
      ▼
IAM Group
      │
      ▼
IAM Policies
      │
      ▼
AWS Services
```

Service authentication:

```text
EC2
      │
      ▼
Instance Profile
      │
      ▼
IAM Role
      │
      ▼
STS Temporary Credentials
      │
      ▼
AWS Resources
```

IAM Roles eliminate the need for permanent credentials in AWS workloads.

---

# Interview Note

### Question

**What is the difference between an IAM User and an IAM Role?**

### Answer

An **IAM User** represents a person or application requiring long-term credentials such as passwords or access keys. An **IAM Role** does not have permanent credentials and is assumed temporarily by trusted entities such as EC2 instances, Lambda functions, or users from another AWS account. AWS Security best practices recommend using IAM Roles for workloads and automation because they provide temporary credentials and reduce the risk associated with long-lived access keys.

---

# Key Takeaways

- IAM Users represent people or long-term identities.
- IAM Groups simplify permission management.
- IAM Roles provide temporary credentials.
- EC2 uses Instance Profiles to obtain Role credentials.
- AssumeRole enables secure cross-account access.
- Prefer Roles over Users for applications and AWS services.
- Follow the Principle of Least Privilege when assigning permissions.

---
