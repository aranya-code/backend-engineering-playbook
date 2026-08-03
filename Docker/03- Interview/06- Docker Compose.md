# Docker Compose

## Overview

Docker Compose is a tool for defining and managing multi-container Docker applications using a single YAML configuration file. Instead of running multiple `docker run` commands, Docker Compose allows developers to configure services, networks, volumes, environment variables, and dependencies in one place.

Docker Compose is widely used in backend development for local development, testing, CI/CD pipelines, and small-scale production deployments.

This section contains beginner to advanced Docker Compose interview questions with concise, interview-ready answers.

---

# Basic Interview Questions

## 1. What is Docker Compose?

**Answer**

Docker Compose is a tool used to define and manage multi-container Docker applications using a single `compose.yaml` (or `docker-compose.yml`) file.

---

## 2. Why is Docker Compose used?

**Answer**

Docker Compose simplifies:

- Multi-container applications
- Local development
- Service networking
- Volume management
- Environment configuration
- One-command application startup

---

## 3. What file does Docker Compose use?

**Answer**

Modern Docker Compose uses:

```text
compose.yaml
```

Older projects may still use:

```text
docker-compose.yml
```

---

## 4. How do you start a Compose application?

**Answer**

```bash
docker compose up
```

Run in detached mode:

```bash
docker compose up -d
```

---

## 5. How do you stop a Compose application?

**Answer**

```bash
docker compose down
```

---

## 6. How do you view running services?

**Answer**

```bash
docker compose ps
```

---

## 7. How do you view logs?

**Answer**

```bash
docker compose logs
```

Follow logs:

```bash
docker compose logs -f
```

---

## 8. How do you rebuild services?

**Answer**

```bash
docker compose up --build
```

---

## 9. How do you restart services?

**Answer**

```bash
docker compose restart
```

---

## 10. Can Docker Compose automatically create networks?

**Answer**

Yes.

Docker Compose automatically creates a dedicated network for the project unless configured otherwise.

---

# Intermediate Interview Questions

## 11. What are services in Docker Compose?

**Answer**

Each service represents one containerized application.

Example:

```yaml
services:
  web:
  db:
  redis:
```

Each service has:

- Image
- Ports
- Volumes
- Environment variables
- Networks

---

## 12. How do services communicate?

**Answer**

Services communicate using service names.

Example:

```text
DATABASE_HOST=db
```

instead of

```text
DATABASE_HOST=localhost
```

---

## 13. What is `depends_on`?

**Answer**

`depends_on` specifies startup order.

Example:

```yaml
depends_on:
  - db
```

However, it **does not guarantee** that the dependent service is ready to accept connections.

---

## 14. How do you pass environment variables?

**Answer**

Using:

```yaml
environment:
  DEBUG: "True"
```

or

```yaml
env_file:
  - .env
```

---

## 15. How do you define volumes?

**Answer**

Example:

```yaml
volumes:
  postgres-data:
```

Mount:

```yaml
services:
  db:
    volumes:
      - postgres-data:/var/lib/postgresql/data
```

---

## 16. How do you expose ports?

**Answer**

Example:

```yaml
ports:
  - "8000:8000"
```

---

## 17. Can Docker Compose build images?

**Answer**

Yes.

Example:

```yaml
build:
  context: .
```

---

## 18. How do you execute commands inside a Compose service?

**Answer**

```bash
docker compose exec web bash
```

or

```bash
docker compose exec web sh
```

---

## 19. How do you validate a Compose file?

**Answer**

```bash
docker compose config
```

---

## 20. What happens when you run `docker compose down`?

**Answer**

Docker removes:

- Containers
- Networks

Volumes remain unless:

```bash
docker compose down -v
```

is used.

---

# Advanced Interview Questions

## 21. What is the difference between `docker compose up` and `docker compose start`?

**Answer**

| `docker compose up` | `docker compose start` |
|---------------------|-------------------------|
| Creates missing containers | Starts existing containers |
| Creates networks | Uses existing resources |
| Builds images if required | Does not build images |

---

## 22. What is the difference between `docker compose stop` and `docker compose down`?

**Answer**

| `stop` | `down` |
|---------|---------|
| Stops containers | Removes containers |
| Preserves networks | Removes project network |
| Faster restart | Fresh deployment |

---

## 23. Can multiple Compose projects run simultaneously?

**Answer**

Yes.

Each project has:

- Separate network
- Separate containers
- Separate volumes (unless shared)

---

## 24. Why shouldn't applications use `localhost` to connect to databases?

**Answer**

Inside a container:

```text
localhost
```

refers to the container itself.

Applications should instead use the Compose service name.

Example:

```text
db
```

---

## 25. How does Docker Compose simplify development?

**Answer**

Compose enables:

- One-command startup
- Automatic networking
- Persistent volumes
- Shared configuration
- Reproducible environments

---

# Scenario-Based Interview Questions

## 26. Your web service cannot connect to PostgreSQL. What would you investigate?

**Expected Answer**

- Service names
- Network configuration
- Database container status
- Environment variables
- Health checks
- Database logs

---

## 27. Developers must start five containers manually every day. How would you improve this?

**Expected Answer**

Create a Compose file so the entire application starts using:

```bash
docker compose up
```

---

## 28. Why is your application unable to connect to Redis using `localhost`?

**Expected Answer**

`localhost` refers to the current container.

Use:

```text
redis
```

(the Compose service name).

---

## 29. Your database starts after your application, causing connection failures. How would you solve this?

**Expected Answer**

- Add health checks.
- Implement retry logic.
- Use `depends_on` for startup ordering (while recognizing it does not wait for readiness).

---

## 30. Your CI/CD pipeline rebuilds every service even when only one changes. How would you optimize it?

**Expected Answer**

- Build only the modified service.
- Leverage Docker layer caching.
- Optimize Dockerfiles.
- Cache dependencies.

---

# Production-Level Questions

## 31. Is Docker Compose suitable for production?

**Answer**

It depends.

Docker Compose is suitable for:

- Small deployments
- Internal applications
- Development
- Testing

For larger, highly available production environments, orchestration platforms such as Docker Swarm or Kubernetes are generally preferred.

---

## 32. What are the advantages of Docker Compose?

**Answer**

- Easy setup
- Simple YAML configuration
- Automatic networking
- Volume management
- Easy scaling for development
- Reproducible environments

---

## 33. What best practices do you follow?

**Answer**

- Use `.env` files for configuration.
- Avoid hardcoding secrets.
- Use health checks.
- Use named volumes.
- Pin image versions.
- Keep Compose files modular.
- Validate configuration using:

```bash
docker compose config
```

---

# Interview Tips

- Understand the complete lifecycle of a Compose application.
- Know the difference between `up`, `start`, `stop`, and `down`.
- Explain why Compose services communicate using service names.
- Be prepared for troubleshooting questions involving networking and dependencies.
- Know the limitations of `depends_on`.

---

## Key Takeaways

- Docker Compose simplifies multi-container application management through a declarative YAML configuration.
- Services communicate using service names over automatically created networks.
- `docker compose up` creates and starts services, while `docker compose down` removes project resources.
- Compose is ideal for development, testing, and small-scale deployments, but larger production environments typically require orchestration platforms.
- Understanding Compose configuration, networking, volumes, and troubleshooting is essential for backend engineering and DevOps interviews.