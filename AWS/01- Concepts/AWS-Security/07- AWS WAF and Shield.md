# AWS WAF and Shield

AWS WAF (Web Application Firewall) and AWS Shield are security services that protect web applications from common exploits, bots, and DDoS attacks. WAF operates at the application layer (Layer 7) to filter malicious requests, while Shield provides infrastructure-level DDoS protection at Layers 3, 4, and 7.

Together, they form the first line of defense for internet-facing applications, sitting at the edge of your architecture in front of CloudFront, ALB, and API Gateway.

---

# AWS WAF

## What is AWS WAF?

AWS WAF is a web application firewall that lets you monitor and control HTTP/HTTPS requests forwarded to your protected resources based on customizable rules.

```text
Internet Traffic
       │
       ▼
┌──────────────┐
│   AWS WAF    │
│              │
│  Rule Group  │
│  ├── Allow   │
│  ├── Block   │
│  └── Count   │
└──────┬───────┘
       │
       ▼
  Protected Resource
  (CloudFront / ALB / API Gateway)
```

## WAF Components

### Web ACL (Access Control List)

A Web ACL is the core WAF resource. It contains rules that define which requests to allow, block, or count.

### Rules

Rules define inspection criteria and actions.

| Rule Type | Description |
|-----------|-------------|
| **Regular Rule** | Matches request properties (IP, headers, body, URI) |
| **Rate-Based Rule** | Triggers when request rate exceeds a threshold |
| **Rule Group** | Reusable collection of rules |

### Actions

| Action | Behavior |
|--------|----------|
| **Allow** | Forward request to the protected resource |
| **Block** | Return 403 Forbidden |
| **Count** | Count the match but take no action (for testing) |
| **CAPTCHA** | Challenge the client with a CAPTCHA |

---

## WAF Rule Capabilities

| Capability | Description |
|-----------|-------------|
| **IP Sets** | Allow/block by IP address or CIDR range |
| **Geo Match** | Allow/block by country |
| **Size Constraints** | Block oversized requests |
| **Regex Patterns** | Match URI, headers, body with regex |
| **String Match** | Match specific strings in request components |
| **SQL Injection** | Detect SQL injection in query strings, body, headers |
| **XSS** | Detect cross-site scripting attacks |
| **Rate Limiting** | Throttle requests exceeding a rate per 5-minute window |
| **Label Match** | Match labels added by other rules |

---

## Managed Rule Groups

AWS and AWS Marketplace vendors provide pre-configured rule groups.

### AWS Managed Rules (Free with WAF)

| Rule Group | Protection |
|-----------|------------|
| **Core Rule Set (CRS)** | OWASP Top 10 protections |
| **Known Bad Inputs** | Common exploit patterns |
| **SQL Injection** | SQL injection detection |
| **Linux/POSIX OS** | LFI, command injection |
| **Admin Protection** | Admin page access control |
| **Bot Control** | Bot detection and management |
| **Account Takeover Prevention** | Credential stuffing protection |
| **IP Reputation** | Known malicious IP blocking |

---

## WAF Integration Points

```text
Internet
    │
    ├──► CloudFront ──► WAF Web ACL
    │
    ├──► ALB ──► WAF Web ACL
    │
    ├──► API Gateway ──► WAF Web ACL
    │
    └──► AWS AppSync ──► WAF Web ACL
```

| Resource | WAF Region | Notes |
|----------|-----------|-------|
| CloudFront | Global (us-east-1) | Best for global protection |
| ALB | Regional | Protects specific region |
| API Gateway | Regional | REST and HTTP APIs |
| AppSync | Regional | GraphQL APIs |

---

# AWS Shield

## AWS Shield Standard

- **Free** — automatically enabled for all AWS accounts
- Protects against most common **Layer 3/4 DDoS attacks**
- SYN floods, UDP floods, reflection attacks
- Always-on detection and automatic inline mitigation
- No configuration required

## AWS Shield Advanced

- **Paid** — $3,000/month per organization + data transfer fees
- Enhanced protection for **Layer 3, 4, and 7 DDoS attacks**
- Available for: CloudFront, ALB, NLB, Elastic IP, Global Accelerator, Route 53
- Features:

| Feature | Description |
|---------|-------------|
| **DDoS Response Team (DRT)** | 24/7 access to AWS DDoS experts |
| **Cost Protection** | AWS credits for scaling costs during attacks |
| **Advanced Metrics** | Real-time attack visibility in CloudWatch |
| **Health-Based Detection** | Uses Route 53 health checks for faster detection |
| **Automatic WAF Rules** | DRT can create WAF rules during attacks |
| **Proactive Engagement** | DRT contacts you during detected events |

---

## Shield Standard vs Shield Advanced

| Feature | Standard | Advanced |
|---------|----------|---------|
| Cost | Free | $3,000/month |
| Layer 3/4 protection | ✅ | ✅ Enhanced |
| Layer 7 protection | ❌ | ✅ (with WAF) |
| DDoS Response Team | ❌ | ✅ 24/7 |
| Cost protection | ❌ | ✅ |
| Attack visibility | Basic | Advanced metrics |
| Proactive engagement | ❌ | ✅ |

---

# DDoS Protection Architecture

```text
Internet
    │
    ▼
┌──────────────┐
│  Route 53    │  ◄── Shield Advanced (DNS-level)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  CloudFront  │  ◄── Shield Standard/Advanced
│  + WAF       │      + WAF Web ACL (Layer 7)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  ALB         │  ◄── Shield Standard/Advanced
│  + WAF       │      + Security Groups
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  EC2 / ECS   │  ◄── Security Groups
│  Application │      + NACLs
└──────────────┘
```

---

# AWS Firewall Manager

AWS Firewall Manager centrally manages WAF rules, Shield Advanced protections, and security groups across multiple accounts in an AWS Organization.

- Apply WAF rules across all accounts from a central administrator
- Ensure Shield Advanced is enabled on all required resources
- Enforce security group policies
- Automatic remediation of non-compliant resources

---

# Key Takeaways

- **WAF** protects against application-layer attacks (SQL injection, XSS, bots, rate limiting).
- **Shield Standard** is free and protects against common Layer 3/4 DDoS attacks automatically.
- **Shield Advanced** adds DDoS Response Team, cost protection, and Layer 7 DDoS protection ($3,000/month).
- Deploy WAF on **CloudFront** for global protection or on **ALB** for regional protection.
- Use **AWS Managed Rules** for baseline protection against OWASP Top 10.
- Use **rate-based rules** for brute force and credential stuffing protection.
- **Firewall Manager** centralizes WAF/Shield management across AWS Organizations.

---

# Interview Questions

### Q: What is the difference between WAF and Shield?

WAF filters application-layer (Layer 7) HTTP requests. Shield protects against volumetric and protocol-level DDoS attacks (Layers 3/4 and 7 with Advanced).

### Q: Is Shield Standard free?

Yes, Shield Standard is automatically enabled for all AWS accounts at no cost.

### Q: Where can WAF be deployed?

CloudFront (global), ALB (regional), API Gateway (regional), and AppSync (regional).

### Q: What does Shield Advanced cost protection mean?

If a DDoS attack causes your infrastructure to scale (more EC2, higher data transfer), AWS credits the scaling costs incurred during the attack.

---
