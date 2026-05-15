# IAM

Created by: aranya majumdar

# Background

**Identity and access management**

# Analysis

Its a global service. 

Root account is created by default and it should not be used as shared. 

Groups only contain users but not other groups. 

An user can belong to more than one group or individually without any group.

# Policies

Users or groups can be assigned to JSON documents which are named policies. 

These policies define the permission of the users. 

User without any group can be assigned to **Inline policies**. 

# IAM Policies Structure

### Consists of

- **Version:** policy language version, always include `"2012-10-17"`
- **Id:** an identifier for the policy (optional)
- **Statement:** one or more individual statements (required)

### Statements consist of

- **Sid:** an identifier for the statement (optional)
- **Effect:** whether the statement allows or denies access (`Allow`, `Deny`)
- **Principal:** account/user/role to which this policy applies
- **Action:** list of actions this policy allows or denies
- **Resource:** list of resources to which the actions apply
- **Condition:** conditions for when this policy is in effect (optional)

```json
{
  "Version": "2012-10-17",
  "Id": "S3-Account-Permissions",
  "Statement": [
    {
      "Sid": "1",
      "Effect": "Allow",
      "Principal": {
        "AWS": ["arn:aws:iam::123456789012:root"]
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::mybucket/*"
      ]
    }
  ]
}
```

# IAM Roles

**IAM roles** are secure AWS identities with specific permissions that can be assumed by trusted entities, such as users, applications, or AWS services, rather than being uniquely associated with a single person. 

 Unlike IAM users, roles **do not have long-term credentials** like passwords or access keys; instead, they provide **temporary security credentials** when assumed, which significantly reduces security risks associated with key exposure. 

## Common IAM Roles

- EC2 Instance Roles
- Lambda Function Roles
- Roles for Cloud Formation

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sts:AssumeRole"
            ],
            "Principal": {
                "Service": [
                    "ec2.amazonaws.com"
                ]
            }
        }
    ]
}
```

# **IAM Security Tools**

### IAM Credentials Report (account-level)

A report that lists all your account's users and the status of their various credentials

### IAM Access Advisor (user-level)

Access advisor shows the service permissions granted to a user and when those services were last accessed.

You can use this information to revise your policies.