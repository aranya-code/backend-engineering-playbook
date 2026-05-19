## EC2 User Data

### Definition
A bootstrap shell script that executes with root privileges during the instance's very first startup cycle.

### Purpose
Automate initial server configuration so you don't have to SSH in and configure things manually.

### Common Tasks
- Update OS packages
- Install dependencies (Docker, Python, Git)
- Pull latest application code from a repository
- Start services automatically

### Important Note
It only runs during the *first* boot. If you stop and start the instance later, it won't run again (unless you specifically wipe the state).

### Example

```bash
#!/bin/bash

yum update -y
amazon-linux-extras install docker -y
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

docker run -d -p 80:8000 my-backend-api:latest
```

---
