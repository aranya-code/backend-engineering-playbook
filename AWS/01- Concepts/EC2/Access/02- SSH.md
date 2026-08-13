# SSH Access to EC2

# SSH Fundamentals

SSH (Secure Shell) provides encrypted remote access to EC2 instances. Authentication uses public-key cryptography: the client proves it holds the private key matching the public key stored on the server, without ever transmitting the private key.

---

# Connecting to EC2

```text
ssh -i /path/to/key.pem <username>@<public-ip-or-dns>
```

## Default Usernames by AMI

| AMI | Default User |
|-----|-------------|
| Amazon Linux 2 / 2023 | `ec2-user` |
| Ubuntu | `ubuntu` |
| Debian | `admin` |
| CentOS | `centos` |
| RHEL | `ec2-user` |
| SUSE | `ec2-user` |
| Fedora | `fedora` |

## Common Connection Failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Permission denied (publickey)` | Wrong key, wrong username, or wrong permissions on `.pem` | Verify key, username, `chmod 400 key.pem` |
| `Connection timed out` | Security Group not allowing port 22 | Add inbound rule: TCP 22 from your IP |
| `Connection refused` | SSH service not running or wrong port | Check instance state, verify sshd is running |
| `Host key verification failed` | Instance relaunched with same IP, different host key | Remove old entry from `~/.ssh/known_hosts` |

---

# Bastion Host (Jump Box) Pattern

A bastion host is a hardened instance in a public subnet that serves as the single entry point for SSH access to private instances.

```text
Internet
    │
    ▼
┌──────────────────────────────────────────┐
│ VPC                                       │
│                                           │
│ Public Subnet                             │
│ ┌───────────────────┐                    │
│ │ Bastion Host      │ ◄── SSH from your IP only  │
│ │ (Port 22 open to  │     (SG: 22 from x.x.x.x) │
│ │  admin IPs only)  │                    │
│ └────────┬──────────┘                    │
│          │ SSH (port 22)                 │
│          ▼                               │
│ Private Subnet                           │
│ ┌───────────────────┐                    │
│ │ App Server        │ ◄── SG: 22 from Bastion-SG only  │
│ │ (No public IP)    │                    │
│ └───────────────────┘                    │
└──────────────────────────────────────────┘
```

## SSH Config for ProxyJump

```text
# ~/.ssh/config
Host bastion
    HostName 54.123.45.67
    User ec2-user
    IdentityFile ~/.ssh/bastion-key.pem

Host private-app
    HostName 10.0.1.42
    User ec2-user
    IdentityFile ~/.ssh/app-key.pem
    ProxyJump bastion

# Usage: ssh private-app
# (automatically tunnels through bastion)
```

---

# SSH Tunneling (Port Forwarding)

## Local Port Forwarding

Access a private database through an SSH tunnel:

```text
ssh -i key.pem -L 5432:my-rds-endpoint:5432 ec2-user@bastion-ip

Your Machine            Bastion (SSH tunnel)         Private RDS
localhost:5432  ──────► bastion:22 ──────────────────► rds:5432

# Now connect your database client to localhost:5432
psql -h localhost -p 5432 -U myuser mydb
```

---

# AWS Systems Manager Session Manager (SSM)

SSM Session Manager is the recommended replacement for SSH in production environments.

## SSH vs SSM Comparison

| Feature | SSH | SSM Session Manager |
|---------|-----|---------------------|
| Port 22 Required | Yes | No (uses HTTPS 443 outbound) |
| Key Management | Manual key pairs | No keys — uses IAM authentication |
| Public IP Required | Yes (or bastion) | No (works in private subnets via VPC endpoint) |
| Audit Logging | Manual (sshd logs) | Automatic via CloudTrail |
| Session Recording | No | Optional (log to S3 or CloudWatch) |
| Firewall Traversal | Requires inbound rule | Outbound HTTPS only |
| Access Control | Key-based | IAM policies (fine-grained per-user) |

## How SSM Works

```text
Admin's Browser / CLI
        │
        │  (HTTPS via AWS APIs / IAM authenticated)
        ▼
AWS Systems Manager Service
        │
        │  (SSM Agent polls for sessions via HTTPS outbound)
        ▼
EC2 Instance (SSM Agent running)
  - No inbound ports needed
  - No public IP needed
  - No key pairs needed
```

## Requirements for SSM
1. SSM Agent installed (pre-installed on Amazon Linux 2/2023 and recent Ubuntu AMIs)
2. IAM Instance Profile with `AmazonSSMManagedInstanceCore` policy
3. Outbound HTTPS access to SSM endpoints (or VPC endpoint for private subnets)

---

# EC2 Instance Connect

Browser-based SSH access through the AWS Console. AWS generates a temporary SSH key pair, pushes the public key to the instance's metadata for 60 seconds, and connects.

**Limitations**: Only works for Amazon Linux 2 and Ubuntu. Requires a public IP or VPC endpoint. Keys are ephemeral (60 seconds).

---

# Common Mistakes

- Opening port 22 to `0.0.0.0/0` — always restrict to specific admin IPs or use SSM instead.
- Using SSH with key pairs in production when SSM Session Manager would provide better security, audit logging, and no key management.
- Wrong file permissions on the `.pem` file — SSH requires `chmod 400` (owner read-only).
- Using the wrong default username for the AMI (e.g., `root` instead of `ec2-user`).
- SSH Agent Forwarding in untrusted environments — a compromised bastion can use your forwarded agent to access other servers.

---

# Key Takeaways

- Use SSM Session Manager instead of SSH for production. It eliminates port 22, key management, and public IP requirements.
- If SSH is required, use the bastion host pattern with ProxyJump for private instances.
- SSH tunneling (local port forwarding) enables secure access to private databases.
- Always restrict port 22 to specific admin IPs — never `0.0.0.0/0`.
- Each AMI has a specific default username. Using the wrong one is the most common SSH failure.

---
