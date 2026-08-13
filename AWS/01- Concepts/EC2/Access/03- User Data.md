# EC2 User Data

# What is User Data?

User Data is a bootstrap script that runs automatically as `root` during the first launch of an EC2 instance. It enables automated instance configuration without manual SSH intervention.

---

# How User Data Works

```text
Instance Launch
      │
      ▼
Nitro/Hypervisor boots the OS
      │
      ▼
cloud-init starts (built into most AMIs)
      │
      ▼
cloud-init retrieves User Data from IMDS
(http://169.254.169.254/latest/user-data)
      │
      ▼
Executes User Data as root
      │
      ▼
Instance becomes available
```

---

# User Data Formats

## Shell Script (Most Common)

```bash
#!/bin/bash
yum update -y
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -aG docker ec2-user
docker pull myrepo/myapp:latest
docker run -d -p 80:8000 myrepo/myapp:latest
```

## cloud-init Directive

```yaml
#cloud-config
packages:
  - nginx
  - python3-pip
write_files:
  - path: /etc/nginx/conf.d/app.conf
    content: |
      server {
          listen 80;
          location / {
              proxy_pass http://localhost:8000;
          }
      }
runcmd:
  - systemctl start nginx
  - pip3 install gunicorn django
```

---

# Production User Data Example

A real-world User Data script for a Django application server:

```bash
#!/bin/bash
set -euo pipefail

# Log all output for debugging
exec > /var/log/user-data.log 2>&1

echo "=== Starting User Data Execution ==="

# Install dependencies
yum update -y
yum install -y python3 python3-pip git

# Retrieve secrets from Parameter Store (not hardcoded!)
DB_HOST=$(aws ssm get-parameter --name /myapp/db-host --query 'Parameter.Value' --output text --region us-east-1)
DB_PASSWORD=$(aws ssm get-parameter --name /myapp/db-password --with-decryption --query 'Parameter.Value' --output text --region us-east-1)

# Clone application code
git clone https://github.com/myorg/myapp.git /opt/myapp

# Install Python dependencies
cd /opt/myapp
pip3 install -r requirements.txt

# Configure environment
cat > /opt/myapp/.env <<EOF
DB_HOST=${DB_HOST}
DB_PASSWORD=${DB_PASSWORD}
DJANGO_SETTINGS_MODULE=config.settings.production
EOF

# Start application
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --daemon

echo "=== User Data Execution Complete ==="
```

---

# User Data Limitations

| Limitation | Detail |
|-----------|--------|
| Max size | 16 KB (before base64 encoding) |
| Execution | Runs only on **first launch** (not after stop/start) |
| Runs as | `root` user |
| Error handling | Failures do not prevent instance from reaching `running` state |
| Visibility | Readable via IMDS and EC2 console (do NOT put secrets here) |
| Timeout | No built-in timeout — a hung script keeps the instance in a degraded state |

---

# Debugging User Data

User Data logs are stored at:

```text
/var/log/cloud-init-output.log    ← Full stdout/stderr of User Data
/var/log/cloud-init.log           ← cloud-init internal processing log
```

**Common Failure Causes:**
1. Missing shebang (`#!/bin/bash`) — script is not executed
2. Missing `set -e` — script continues after errors
3. Network dependency fails — trying to `yum install` before network is ready
4. Wrong IAM permissions — instance role can't access SSM Parameter Store or S3
5. Exceeding 16 KB limit — script is silently truncated

---

# User Data vs AMI Baking

```text
AMI Baking Approach:
  Bake everything into AMI ──► Launch ──► Ready in seconds
  (OS + packages + app code)
  Pros: Fast boot, consistent, no external dependencies at launch
  Cons: AMI rebuild needed for every code change

User Data Approach:
  Launch base AMI ──► User Data installs/configures ──► Ready in minutes
  Pros: Flexible, easy to change configuration
  Cons: Slow boot, depends on external services (yum, git, S3)

Production Pattern (Hybrid):
  Bake OS + packages into AMI ──► User Data for instance-specific config
  (e.g., retrieve secrets, set environment variables, register with LB)
```

---

# Security Considerations

- **Never put secrets in User Data** — it is visible via IMDS (`/latest/user-data`) and the EC2 console. Use AWS Secrets Manager or SSM Parameter Store.
- User Data runs as root — a malicious script has full system access.
- Base64-encoded User Data is NOT encrypted — it is simply encoded for transport.

---

# Key Takeaways

- User Data runs once on first launch as root. It does not re-run on stop/start.
- Always start with `#!/bin/bash` and `set -euo pipefail` for reliable error handling.
- Never hardcode secrets in User Data — use SSM Parameter Store or Secrets Manager.
- Debug failures using `/var/log/cloud-init-output.log`.
- In production, use a hybrid approach: bake packages into the AMI, use User Data only for instance-specific configuration.
- User Data failures do not prevent the instance from reaching `running` state — you must monitor for configuration success separately.

---
