# Docker Secrets

## Definition
Docker Secrets provide a secure mechanism for storing and distributing sensitive information to services running in Docker Swarm.

## What Can Be Stored?
- Database passwords
- API keys
- TLS certificates
- SSH keys
- Tokens
- Any confidential application data

## Why Use Secrets?
Without secrets:
- Passwords may be stored in environment variables.
- Passwords may appear in logs.
- Passwords may exist in Compose files.

With secrets:
- Encrypted at rest.
- Encrypted in transit.
- Available only to authorized services.

## Architecture

### Storage
- Stored in Swarm's Raft database.
- Raft database is encrypted.
- Stored only on Manager nodes.

### Distribution
- Secret created in Swarm.
- Secret attached to services.
- Only assigned containers can access it.

### Mount Location

```text
/run/secrets/<secret_name>
```

Secrets appear as files.

Example:
```text
/run/secrets/db_password
```

## Create a Secret

```bash
echo "MyStrongPassword" | docker secret create db_password -
```

List secrets:

```bash
docker secret ls
```

Inspect:

```bash
docker secret inspect db_password
```

## Use Secret in a Service

```bash
docker service create   --name mysql   --secret db_password   mysql
```

## Compose Example

```yaml
version: "3.8"

services:
  app:
    image: nginx
    secrets:
      - db_password

secrets:
  db_password:
    external: true
```

## Best Practices
- Never hardcode credentials.
- Rotate secrets regularly.
- Use least privilege.
- Separate secrets from application code.
- Store certificates as secrets.

## Interview Notes
Q: Where are Docker Secrets stored?
A: In the encrypted Swarm Raft database.

Q: Can every container read a secret?
A: No. Only services explicitly granted access.

Q: Are secrets environment variables?
A: No. They are mounted as files.
