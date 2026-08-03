# Docker Secrets

## Overview
Docker Secrets provides a secure mechanism to manage sensitive data, such as passwords, API keys, and TLS certificates, in a Docker Swarm cluster. Instead of hardcoding secrets in images or passing them as environment variables (which can be exposed in logs or inspection commands), Docker Secrets encrypts the data at rest and securely delivers it only to the services that are explicitly granted access.

## Common Commands

| Command | Description |
|---|---|
| `docker secret create <name> <file|->` | Create a new secret from a file or standard input |
| `echo "mypassword" \| docker secret create db_password -` | Create a secret using standard input |
| `docker secret ls` | List all secrets in the swarm |
| `docker secret inspect db_password` | View metadata about a secret (does not reveal the value) |
| `docker secret rm db_password` | Remove a secret |
| `docker service create --name mysql --secret db_password mysql` | Create a service with access to a secret |
| `ls /run/secrets` | List available secrets inside a container |
| `cat /run/secrets/db_password` | Read the contents of a secret inside a container |

## Command Breakdown

*   `docker secret create`: Accepts a name for the secret and the path to a file containing the sensitive data. You can also pass `-` to read from standard input.
*   `--secret` flag in `docker service create/update`: Grants the service access to the named secret. By default, the secret is mounted at `/run/secrets/<secret_name>` inside the container.

## Practical Examples

### Create a Secret from a File

```bash
docker secret create db_password ./password.txt
```

### Attach Multiple Secrets to a Service

```bash
docker service create \
  --name api_server \
  --secret api_key \
  --secret tls_cert \
  --secret tls_key \
  my_api_image
```

### Expected Output for List and Inspect

```bash
docker secret ls
```
```text
ID                          NAME          DRIVER    CREATED          UPDATED
j8y8b9v1x2q3w4e5r6t7y8u9i   db_password             10 minutes ago   10 minutes ago
```

```bash
docker secret inspect db_password
```
```text
[
    {
        "ID": "j8y8b9v1x2q3w4e5r6t7y8u9i",
        "Version": {
            "Index": 12
        },
        "CreatedAt": "2023-10-27T10:00:00Z",
        "UpdatedAt": "2023-10-27T10:00:00Z",
        "Spec": {
            "Name": "db_password",
            "Labels": {}
        }
    }
]
```

### Compose File Secrets Example

In a `docker-compose.yml` file designed for Swarm deployment:

```yaml
version: '3.8'
services:
  db:
    image: postgres
    secrets:
      - db_password
      - api_key
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password

secrets:
  db_password:
    external: true
  api_key:
    file: ./api_key.txt
```

### Rotate a Secret

To rotate a secret without downtime:
1. Create the new secret: `docker secret create db_password_v2 ./new_password.txt`
2. Update the service to add the new secret and remove the old one:
   ```bash
   docker service update \
     --secret-add db_password_v2 \
     --secret-rm db_password \
     db_service
   ```
3. Remove the old secret: `docker secret rm db_password`

## Real-World Use Cases
*   **Database Passwords:** Passing credentials securely to database containers and application servers.
*   **API Keys:** Supplying third-party API keys to microservices without exposing them in version control.
*   **TLS Certificates:** Managing private keys and certificates for web servers acting as reverse proxies.

## Common Mistakes
*   **Using `echo` for Creation:** Creating secrets via `echo "mypassword" | docker secret create db_password -` leaves the password visible in your shell history.
*   **Expecting Secrets in Local Containers:** Trying to use Docker Secrets with standalone containers (`docker run`). Secrets are only fully supported in a Swarm context (though Docker Compose can emulate them locally).
*   **Modifying Existing Secrets:** You cannot change the value of an existing secret. You must create a new one, update the services, and remove the old one.

## Best Practices
*   **Use File-Based or Secure Creation:** Prefer creating secrets from files (`docker secret create name ./file.txt`) or using `printf` instead of `echo` to avoid polluting shell history.
*   **Leverage `_FILE` Environment Variables:** Many official images support configuring passwords via files by appending `_FILE` to the environment variable (e.g., `MYSQL_ROOT_PASSWORD_FILE=/run/secrets/mysql_root_password`).

## Interview Tips
*   **Where are secrets stored?** In the encrypted Raft logs on the manager nodes. They are decrypted in memory when delivered to a worker node running a task that requires them.
*   **Can you read a secret after creation?** No, the Docker API only allows you to inspect metadata, not the secret's value. The value is only accessible from within the container filesystem.

## Related Topics
- [Docker Swarm](09-%20Docker%20Swarm.md)
- [Docker Compose](06-%20Docker%20Compose.md)
- [Docker Health Checks](07-%20Docker%20Health%20Checks.md)

## Key Takeaways
*   Secrets are first-class objects in Docker Swarm for secure data management.
*   They are stored encrypted at rest and delivered only to authorized services.
*   Inside the container, secrets appear as files in an in-memory filesystem (usually `/run/secrets/`).
*   Secrets are immutable; updating requires creating a new secret and rotating it.
