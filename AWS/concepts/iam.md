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