# ☁️ AWS Notes Repository

A structured and interview-focused AWS learning repository containing:
- Core AWS concepts
- Architecture notes
- Real-world explanations
- Interview preparation material
- Troubleshooting references
- Production insights

This repository is designed for:
- AWS certification preparation
- Backend/System Design interviews
- DevOps learning
- Cloud engineering practice
- Quick revision before interviews

---

# 📂 Repository Structure

```text
AWS/
│
├── cli/
│
├── concepts/
│   │
│   ├── EC2/
│   ├── Databases/
│   ├── IAM/
│   ├── S3/
│   ├── VPC/
│   ├── ECS/
│   ├── Lambda/
│   ├── CloudWatch/
│   └── ...
│
└── README.md
```

---

# 🖥️ EC2 Topics

## Compute Basics
- EC2 Basics
- Instance Types
- Purchasing Options
- Launch Templates
- User Data
- AMIs

---

## Load Balancing
- Elastic Load Balancer (ELB)
- Application Load Balancer (ALB)
- Network Load Balancer (NLB)
- Gateway Load Balancer (GWLB)
- Sticky Sessions
- SSL Certificates
- SNI
- Target Groups
- Health Checks
- Cross-Zone Load Balancing
- Connection Draining

---

## Auto Scaling
- Auto Scaling Groups (ASG)
- Scaling Policies
- Cooldown Periods
- Dynamic Scaling
- Target Tracking
- Step Scaling

---

# 🗄️ Database Topics

## Amazon RDS
- RDS Overview
- Read Replicas
- Multi-AZ
- RDS Proxy
- RDS Security
- Storage Auto Scaling
- Point-in-Time Recovery

---

## Aurora
- Aurora Overview
- Aurora Security
- Aurora vs RDS

---

## ElastiCache
- Redis
- Memcached
- Cache Aside
- Write Through
- TTL
- Cache Invalidation
- DB Cache Architecture

---

## MemoryDB
- MemoryDB for Redis
- MemoryDB vs ElastiCache

---

# 🎯 Interview Focus

These notes are written with:
- Interview explanations
- Real-world architecture thinking
- Practical AWS usage
- Common interview traps
- Frequently asked differences

Examples:
- Multi-AZ vs Read Replica
- ALB vs NLB
- Redis vs Memcached
- RDS vs DB on EC2

---

# 🧠 Learning Philosophy

The goal is not only to memorize AWS services, but to understand:

- Why a service exists
- What problem it solves
- When to use it
- Real-world tradeoffs
- How services work together

Example Architecture Thinking:

```text
Route53
   ↓
ALB
   ↓
Auto Scaling Group
   ↓
EC2 Instances
   ↓
RDS + ElastiCache
```

---

# 📝 Notes Style

The notes follow:
- Small definitions
- Interview-ready explanations
- Real-world examples
- Quick revision points
- Easy markdown readability

Each concept is intentionally separated into focused markdown files.

---

# 🚀 Future Topics

Planned additions:
- ECS
- EKS
- Docker on AWS
- CI/CD
- CloudFormation
- Terraform
- Route 53
- VPC Deep Dive
- Security Best Practices
- Monitoring & Logging
- Disaster Recovery
- High Availability Architectures

---

# 📌 Best Practices Used in This Repository

- One topic = one file
- One service = one folder
- Separate quick revision notes
- Interview concepts separated
- Architecture-first learning approach

---

# 💡 Personal Advice

When learning AWS:

❌ Don't memorize services blindly.

✅ Learn:
- Architecture patterns
- Service integration
- Scaling strategies
- Cost optimization
- Failure handling
- Security design

That is what real interviews and real jobs expect.

---

# 📚 Recommended Usage

## For Learning
Read topic-by-topic.

## For Interviews
Use:
- Quick Revision Notes
- Interview folders
- Architecture comparisons

## For Real Projects
Use these notes as:
- Deployment references
- Troubleshooting references
- Design guidance

---

# 🔥 Final Goal

This repository is being built as:
- Personal cloud engineering knowledge base
- Interview preparation system
- Real-world AWS reference
- Long-term backend/devops handbook

---