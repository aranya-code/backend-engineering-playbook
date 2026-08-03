# Rapid Fire Questions

## Overview

Rapid-fire questions are commonly asked during the final rounds of technical interviews to quickly evaluate the depth and breadth of a candidate's Docker knowledge. These questions usually require concise, accurate answers in one or two sentences rather than lengthy explanations.

This section is designed as a quick revision guide covering the most frequently asked Docker interview questions. Reviewing these questions before an interview can help reinforce core concepts and improve confidence.

---

# Docker Fundamentals

## 1. What is Docker?

A containerization platform used to package, distribute, and run applications consistently across different environments.

---

## 2. What is containerization?

Packaging an application together with its runtime, libraries, dependencies, and configuration into an isolated container.

---

## 3. What is the difference between a container and a virtual machine?

Containers share the host operating system's kernel, while virtual machines run their own guest operating system.

---

## 4. What is Docker Engine?

The core Docker runtime consisting of the Docker Daemon, Docker CLI, and Docker API.

---

## 5. What is Docker Desktop?

A desktop application that bundles Docker Engine, Docker Compose, Kubernetes (optional), and management tools for Windows and macOS.

---

# Docker Images

## 6. What is a Docker image?

A read-only template used to create Docker containers.

---

## 7. What command lists Docker images?

```bash
docker images
```

---

## 8. What command downloads an image?

```bash
docker pull image_name
```

---

## 9. What command removes an image?

```bash
docker rmi image_name
```

---

## 10. What creates an image layer?

Most Dockerfile instructions such as `RUN`, `COPY`, and `ADD`.

---

# Docker Containers

## 11. What command starts a new container?

```bash
docker run image_name
```

---

## 12. What command lists running containers?

```bash
docker ps
```

---

## 13. What command lists all containers?

```bash
docker ps -a
```

---

## 14. How do you stop a container?

```bash
docker stop container_name
```

---

## 15. How do you remove a container?

```bash
docker rm container_name
```

---

# Dockerfile

## 16. What instruction specifies the base image?

```dockerfile
FROM
```

---

## 17. Which instruction copies files?

```dockerfile
COPY
```

---

## 18. Which instruction executes commands during image build?

```dockerfile
RUN
```

---

## 19. Which instruction specifies the startup command?

```dockerfile
CMD
```

---

## 20. Which instruction specifies the executable?

```dockerfile
ENTRYPOINT
```

---

# Docker Networking

## 21. What is Docker's default network?

Bridge network.

---

## 22. How do you list Docker networks?

```bash
docker network ls
```

---

## 23. Which network driver is used in Docker Swarm?

Overlay network.

---

## 24. Should containers communicate using IP addresses?

No.

Use container names or service names instead.

---

## 25. Why should applications listen on `0.0.0.0`?

To allow connections from outside the container.

---

# Docker Volumes

## 26. Why are Docker volumes used?

To persist data independently of the container lifecycle.

---

## 27. How do you create a volume?

```bash
docker volume create my-volume
```

---

## 28. How do you list volumes?

```bash
docker volume ls
```

---

## 29. Which storage option is recommended for production?

Named volumes.

---

## 30. What happens if data is stored only inside a container?

It is lost when the container is removed.

---

# Docker Compose

## 31. What command starts Compose services?

```bash
docker compose up
```

---

## 32. What command stops Compose services?

```bash
docker compose down
```

---

## 33. What command validates a Compose file?

```bash
docker compose config
```

---

## 34. How do Compose services communicate?

Using service names.

---

## 35. Does `depends_on` wait until a service is ready?

No.

It controls startup order but does not guarantee readiness.

---

# Docker Swarm

## 36. What command initializes a Swarm?

```bash
docker swarm init
```

---

## 37. What command lists Swarm nodes?

```bash
docker node ls
```

---

## 38. What command lists services?

```bash
docker service ls
```

---

## 39. What is a replica?

A running instance of a service.

---

## 40. Which consensus algorithm does Swarm use?

Raft.

---

# Docker Security

## 41. Should containers run as root?

No.

Use a non-root user whenever possible.

---

## 42. Where should secrets be stored?

In a secure secret management solution such as Docker Secrets or a cloud secret manager.

---

## 43. Should secrets be hardcoded into Dockerfiles?

No.

---

## 44. Why should official images be preferred?

They are maintained, regularly updated, and generally more secure.

---

## 45. What is Docker Scout?

Docker's image vulnerability scanning tool.

---

# Production

## 46. Why shouldn't production use the `latest` tag?

Because it changes over time and makes deployments unpredictable.

---

## 47. Why should applications be stateless?

To simplify scaling, replacement, and recovery.

---

## 48. Why are health checks important?

They allow unhealthy containers to be detected and replaced automatically.

---

## 49. What should be monitored in production?

CPU, memory, disk usage, logs, health checks, response times, and error rates.

---

## 50. What is immutable infrastructure?

Replacing containers with new versions instead of modifying running containers.

---

# Common Commands

## 51. View logs

```bash
docker logs container_name
```

---

## 52. Execute a shell inside a container

```bash
docker exec -it container_name sh
```

---

## 53. Inspect a container

```bash
docker inspect container_name
```

---

## 54. Monitor resource usage

```bash
docker stats
```

---

## 55. View Docker information

```bash
docker info
```

---

## 56. View image history

```bash
docker history image_name
```

---

## 57. Remove unused resources

```bash
docker system prune
```

---

## 58. List Docker volumes

```bash
docker volume ls
```

---

## 59. List Docker networks

```bash
docker network ls
```

---

## 60. List running services in Compose

```bash
docker compose ps
```

---

# Senior-Level Rapid Fire

## 61. Blue-Green or Rolling Deployment?

Rolling Deployment for most updates; Blue-Green when instant rollback and minimal downtime are priorities.

---

## 62. Docker Compose or Kubernetes?

Compose for development and small deployments; Kubernetes for large-scale production orchestration.

---

## 63. Volume or Bind Mount?

Volumes for production, bind mounts for local development.

---

## 64. Bridge or Overlay Network?

Bridge for single-host deployments, Overlay for multi-host clusters.

---

## 65. `CMD` or `ENTRYPOINT`?

`ENTRYPOINT` defines the executable; `CMD` provides default arguments or the default command.

---

## 66. `COPY` or `ADD`?

Prefer `COPY`; use `ADD` only when its additional functionality is required.

---

## 67. `docker stop` or `docker kill`?

`docker stop` performs a graceful shutdown; `docker kill` immediately terminates the container.

---

## 68. Named Volume or Anonymous Volume?

Named volumes are preferred because they are easier to identify, manage, and reuse.

---

## 69. Docker Hub or Private Registry?

Docker Hub for public images; private registries for enterprise and production workloads.

---

## 70. Biggest Docker production mistake?

Running containers without proper security, monitoring, backups, health checks, or versioned images.

---

# Interview Tips

- Answer confidently and concisely.
- Explain concepts before mentioning commands when appropriate.
- Use production-oriented terminology such as scalability, reliability, observability, and security.
- If unsure, explain your reasoning rather than guessing.
- Practice these questions aloud to improve fluency during interviews.

---

## Key Takeaways

- Rapid-fire questions test your understanding of Docker fundamentals, commands, architecture, security, networking, storage, and production practices.
- Strong candidates answer clearly, accurately, and without unnecessary detail.
- Understanding the reasoning behind Docker best practices is more valuable than memorizing commands.
- Consistent practice with these questions improves confidence and interview performance.
- This section serves as a comprehensive last-minute revision guide before Docker technical interviews.