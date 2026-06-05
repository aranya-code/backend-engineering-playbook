# EC2 Instance Metadata

## Definition
EC2 Instance Metadata allows an EC2 instance to retrieve information about itself without requiring AWS credentials.

Metadata endpoint:

```bash
http://169.254.169.254/latest/meta-data/
```

## Common Use Cases
- Retrieve Instance ID
- Retrieve Public/Private IP
- Retrieve Availability Zone
- Retrieve IAM Role Name
- Retrieve Temporary Security Credentials

## Important Points
- IAM Role name can be retrieved.
- IAM Policy names cannot be directly retrieved through metadata.
- Applications use metadata to dynamically discover instance information.

## IMDSv1 vs IMDSv2

### IMDSv1
- No token required
- Simpler but less secure

### IMDSv2
- Token-based authentication
- Protects against SSRF attacks
- AWS recommended
