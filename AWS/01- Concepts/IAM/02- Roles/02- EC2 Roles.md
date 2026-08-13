# Common IAM Roles by Use Case

Different AWS services assume roles for different reasons — recognizing the common patterns helps in both real design work and interviews.

## EC2 Instance Roles

Attached to an EC2 instance via an **instance profile** (see `Instance Profiles.md` for the exact mechanism), letting applications running on the instance call AWS APIs without ever storing an access key on the instance itself.

**Example:** a web application on EC2 needing to read/write objects in S3, or read a secret from Secrets Manager.

## Lambda Function Roles (Execution Roles)

Every Lambda function has an associated **execution role**, defining what AWS resources the function's code is permitted to interact with during execution — plus baseline permissions to write logs to CloudWatch, which every function needs regardless of its specific business logic.

## Roles for CloudFormation

CloudFormation can assume a specified **service role** to create/update/delete resources on your behalf, using that role's permissions rather than the permissions of whoever triggered the stack operation.

**Why this matters:** it lets you grant a team permission to *run* a CloudFormation stack without granting them the (potentially much broader) permissions that stack's resources actually require directly — the team can trigger deployments through CloudFormation without personally holding, say, IAM-modifying permissions that the stack itself needs to create a role.

## The Common Thread

In every case, the *service* (EC2, Lambda, CloudFormation) is the one assuming the role and using its temporary credentials — not a human directly. This is the dominant real-world pattern for how AWS services are granted permissions, and it's why understanding roles well is foundational to almost everything else in a serverless or service-oriented AWS architecture.

## Senior-Level Considerations

- Each of these role types has a different trust policy principal (e.g., `ec2.amazonaws.com`, `lambda.amazonaws.com`, `cloudformation.amazonaws.com`) — the trust policy is what makes a role usable by that specific service in the first place, and a mismatched principal is a common setup error
- Following least privilege here specifically means each Lambda function or EC2 instance role should be scoped to only what that specific workload needs — a shared, overly broad "Lambda role" reused across many unrelated functions is a common anti-pattern that quietly widens blast radius
