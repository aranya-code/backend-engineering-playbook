# Stack Deployment

## Overview

Docker Stacks are deployed using a Compose file and the `docker stack deploy` command.

Unlike individual service creation, stack deployment allows an entire application to be deployed from a single YAML file.

---

# Why Stack Deployment?

Without stacks:

```bash
docker service create frontend
docker service create backend
docker service create database
```

With stacks:

```bash
docker stack deploy -c stack.yml myapp
```

Everything is deployed together.

---

# Deployment Workflow

```text
Compose File
      │
      ▼
docker stack deploy
      │
      ▼
Create Services
      │
      ▼
Create Tasks
      │
      ▼
Run Containers
```

---

# Stack File Example

```yaml
version: "3.9"

services:

  web:
    image: nginx

  api:
    image: httpd
```

---

# Deploy a Stack

```bash
docker stack deploy -c stack.yml myapp
```

Where:

```text
-c stack.yml = Compose File

myapp = Stack Name
```

---

# Verify Deployment

List stacks:

```bash
docker stack ls
```

Example:

```text
NAME
myapp
```

---

# View Stack Services

```bash
docker stack services myapp
```

Example:

```text
NAME          MODE        REPLICAS

myapp_web     replicated  1/1

myapp_api     replicated  1/1
```

---

# View Stack Tasks

```bash
docker stack ps myapp
```

Displays:

- Task IDs
- Node Placement
- Status
- Errors

---

# What Happens During Deployment?

```text
Stack File
      │
      ▼
Services Created
      │
      ▼
Scheduler Assigns Tasks
      │
      ▼
Containers Started
```

Docker Swarm handles scheduling automatically.

---

# Updating a Stack

Modify:

```yaml
image: nginx:latest
```

Redeploy:

```bash
docker stack deploy -c stack.yml myapp
```

Swarm performs rolling updates automatically.

---

# Removing a Stack

```bash
docker stack rm myapp
```

Removes:

```text
Services

Tasks

Containers

Networks
```

created by the stack.

---

# Stack Lifecycle

```text
Create File
      │
      ▼
Deploy Stack
      │
      ▼
Run Services
      │
      ▼
Update Stack
      │
      ▼
Remove Stack
```

---

# Troubleshooting

## Check Services

```bash
docker stack services myapp
```

---

## Check Tasks

```bash
docker stack ps myapp
```

---

## Check Service Logs

```bash
docker service logs <service-name>
```

---

## Verify Nodes

```bash
docker node ls
```

---

# Common Commands

## Deploy

```bash
docker stack deploy -c stack.yml myapp
```

---

## List Stacks

```bash
docker stack ls
```

---

## View Services

```bash
docker stack services myapp
```

---

## View Tasks

```bash
docker stack ps myapp
```

---

## Remove Stack

```bash
docker stack rm myapp
```

---

# Best Practices

## Store Stack Files in Git

Infrastructure as Code.

---

## Use Overlay Networks

For service communication.

---

## Use Secrets

Avoid hardcoding passwords.

---

## Deploy Using Versioned Images

Avoid:

```yaml
image: nginx:latest
```

Prefer:

```yaml
image: nginx:1.27
```

---

# Common Interview Questions

## Which Command Deploys a Stack?

```bash
docker stack deploy
```

---

## Which Command Lists Stacks?

```bash
docker stack ls
```

---

## Which Command Removes a Stack?

```bash
docker stack rm
```

---

## Does Stack Deployment Support Rolling Updates?

Yes. Docker Swarm performs rolling updates when the stack is redeployed.

---

# Interview One-Liner

Docker Stack deployment uses a Compose file and the `docker stack deploy` command to create, update, and manage multi-service applications in a Docker Swarm cluster as a single unit.
