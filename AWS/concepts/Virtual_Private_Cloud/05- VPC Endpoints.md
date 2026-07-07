# VPC Endpoints

VPC Endpoints enable private connectivity from your VPC to supported AWS services without requiring traffic to traverse the public internet, NAT Gateways, or VPN connections. This reduces data transfer costs, lowers latency, and improves security by keeping traffic within the AWS network.

VPC Endpoints are a critical component of secure VPC architectures and are essential for compliance requirements that mandate private connectivity.

---

# Why VPC Endpoints?

Without VPC Endpoints, a private subnet instance accessing S3 or DynamoDB must route through a NAT Gateway and the Internet Gateway — traversing the public internet.

```text
Without Endpoints:                  With Endpoints:

Private Instance                    Private Instance
     │                                   │
     ▼                                   ▼
  NAT Gateway ($$$)                VPC Endpoint
     │                                   │
     ▼                                   │
  Internet Gateway                       │
     │                                   │
     ▼                                   ▼
  Public Internet                  AWS Service
     │                             (Private Network)
     ▼
  AWS Service
```

Benefits:
- **Security** — traffic never leaves the AWS network
- **Cost** — avoids NAT Gateway data processing charges
- **Performance** — lower latency, no internet hops
- **Compliance** — meets private connectivity requirements

---

# Types of VPC Endpoints

## Gateway Endpoints

- Support **S3** and **DynamoDB** only
- **Free** — no hourly or data processing charges
- Implemented as a route table entry pointing to the service
- No ENI created in your subnet
- Specify in the route table: `pl-xxxxx → vpce-xxxxx`

```text
Route Table Entry:
┌──────────────────────┬────────────────────┐
│ Destination          │ Target             │
├──────────────────────┼────────────────────┤
│ pl-63a5400a (S3)     │ vpce-abc123        │
│ 10.0.0.0/16          │ local              │
│ 0.0.0.0/0            │ nat-xyz789         │
└──────────────────────┴────────────────────┘
```

## Interface Endpoints (AWS PrivateLink)

- Support **200+ AWS services** (and custom services)
- Creates an **ENI** (Elastic Network Interface) in your subnet with a private IP
- Supports **security groups** for access control
- **DNS resolution** — creates private DNS entries that override public endpoints
- **Charged** — ~$0.01/hour per endpoint per AZ + data processing

```text
Interface Endpoint Architecture:

Private Subnet
┌─────────────────────────────┐
│                             │
│  ┌────────────────────┐     │
│  │ ENI (10.0.3.50)    │     │
│  │ vpce-abc123        │ ◄── Security Group attached
│  │                    │     │
│  │ Private DNS:       │     │
│  │ secretsmanager.    │     │
│  │ ap-south-1.        │     │
│  │ amazonaws.com      │     │
│  └────────┬───────────┘     │
│           │                 │
│  EC2 ─────┘                 │
│  (Resolves to private IP)   │
└─────────────────────────────┘
```

---

# Gateway vs Interface Endpoint Comparison

| Feature | Gateway Endpoint | Interface Endpoint |
|---------|-----------------|-------------------|
| **Services** | S3, DynamoDB only | 200+ services |
| **Cost** | Free | ~$0.01/hr/AZ + data |
| **Implementation** | Route table entry | ENI in subnet |
| **Security groups** | No | Yes |
| **Private DNS** | No | Yes (optional) |
| **Cross-region** | No | No |
| **On-premises access** | No | Yes (via VPN/DX) |
| **AZ scoping** | Region-wide | Per AZ |

---

# Endpoint Policies

Both endpoint types support **endpoint policies** — resource-based policies that control which AWS resources can be accessed through the endpoint.

```json
{
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::my-approved-bucket/*"
    }
  ]
}
```

Use cases:
- Restrict S3 access to specific buckets only
- Prevent data exfiltration to unauthorized S3 buckets
- Limit DynamoDB access to specific tables

---

# AWS PrivateLink

AWS PrivateLink is the technology behind Interface Endpoints. It can also be used to expose your own services privately to other VPCs or AWS accounts.

```text
Service Provider VPC          Consumer VPC
┌──────────────────┐          ┌──────────────────┐
│                  │          │                  │
│  ┌────────────┐  │          │  ┌────────────┐  │
│  │ NLB        │◄─┼──────────┼──│ Interface  │  │
│  │ (Service)  │  │PrivateLink│  │ Endpoint   │  │
│  └────────────┘  │          │  └────────────┘  │
│                  │          │                  │
│  EC2 / ECS       │          │  Consumer App    │
│  (Backend)       │          │                  │
└──────────────────┘          └──────────────────┘
```

Use cases:
- SaaS providers exposing services to customer VPCs
- Internal service exposure across accounts
- Replacing VPC peering for service-to-service communication

---

# Common VPC Endpoints to Deploy

| Service | Endpoint Type | Why |
|---------|--------------|-----|
| **S3** | Gateway (free) | Most common — avoid NAT costs for S3 traffic |
| **DynamoDB** | Gateway (free) | Avoid NAT costs for DynamoDB traffic |
| **Secrets Manager** | Interface | Secure secret retrieval from private subnets |
| **SSM** | Interface | SSM Session Manager without internet |
| **ECR** | Interface | Pull container images privately |
| **CloudWatch Logs** | Interface | Send logs without internet |
| **STS** | Interface | Assume roles without internet |
| **KMS** | Interface | Encryption operations privately |

---

# Key Takeaways

- VPC Endpoints keep traffic private and reduce costs by avoiding NAT Gateway data charges.
- **Gateway Endpoints** (S3, DynamoDB) are free — always deploy them.
- **Interface Endpoints** use ENIs with private IPs and support security groups.
- Use **endpoint policies** to restrict which resources can be accessed through the endpoint.
- **PrivateLink** extends the concept to your own services across VPCs and accounts.
- Deploy Interface Endpoints for SSM, Secrets Manager, ECR, and CloudWatch in private-only architectures.

---
