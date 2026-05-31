# Docker Stacks

## Definition
Docker Stack is a production-grade deployment method for Docker Swarm that uses Compose files to deploy and manage multi-service applications.

## Why Stacks?
Before stacks:
```bash
docker service create
```

With stacks:
```bash
docker stack deploy
```

A stack manages:
- Services
- Networks
- Volumes
- Secrets
- Configurations

## Deployment

```bash
docker stack deploy -c docker-compose.yml myapp
```

## Important Concepts

### Uses Compose Files
Stacks use docker-compose.yml as the application definition.

### Stack Name Prefix
Docker automatically prefixes resources.

Example:
```text
myapp_web
myapp_backend
myapp_db
```

### Deploy Section
The deploy: section is used only by Swarm.

Example:
```yaml
services:
  web:
    image: nginx
    deploy:
      replicas: 3
```

### Build Limitation
Swarm ignores:
```yaml
build:
```

Therefore images must already exist in a registry.

## Lifecycle

Development:
```bash
docker compose up
```

CI/CD:
```bash
docker compose up
```

Production:
```bash
docker stack deploy -c docker-compose.yml myapp
```

## Interview Notes
Q: Difference between Compose and Stack?
A:
- Compose = Local container orchestration.
- Stack = Production deployment on Swarm.

Q: Does Swarm use build:?
A: No. Swarm ignores build: and uses prebuilt images.
