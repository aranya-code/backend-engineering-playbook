# Docker Networking

## Overview

Docker networking is one of the most frequently tested topics in backend and DevOps interviews because it determines how containers communicate with each other, the host machine, and external systems. Interviewers often ask about network drivers, DNS, port mapping, bridge networks, overlay networks, and common networking issues.

This section contains beginner to advanced Docker networking interview questions with concise, interview-ready answers.

---

# Basic Interview Questions

## 1. Why does Docker need networking?

**Answer**

Docker networking enables containers to:

- Communicate with each other
- Access external services
- Receive incoming traffic
- Isolate network traffic
- Connect to databases and APIs

---

## 2. What is the default Docker network?

**Answer**

The default Docker network is the **bridge** network.

Containers connected to the default bridge network can communicate using IP addresses, but automatic DNS-based name resolution is limited compared to user-defined bridge networks.

---

## 3. How do you list Docker networks?

**Answer**

```bash
docker network ls
```

---

## 4. How do you inspect a Docker network?

**Answer**

```bash
docker network inspect bridge
```

---

## 5. How do you create a custom network?

**Answer**

```bash
docker network create my-network
```

---

## 6. Why should you use a user-defined bridge network?

**Answer**

Benefits include:

- Automatic DNS resolution
- Better container isolation
- Easier service communication
- Improved organization
- Better security

---

## 7. What is port mapping?

**Answer**

Port mapping exposes a container port to the host machine.

Example:

```bash
docker run -p 8080:80 nginx
```

Here:

- Host Port → **8080**
- Container Port → **80**

---

## 8. What happens if you don't publish a port?

**Answer**

The application is accessible only from inside Docker networks.

External clients cannot connect.

---

## 9. How do you view published ports?

**Answer**

```bash
docker port container_name
```

---

## 10. How do two containers communicate?

**Answer**

Containers connected to the same user-defined network can communicate using:

- Container names
- Service names (Docker Compose)

---

# Intermediate Interview Questions

## 11. What network drivers does Docker support?

**Answer**

Docker provides several built-in network drivers:

- Bridge
- Host
- None
- Overlay
- Macvlan
- IPvlan

---

## 12. What is the bridge network?

**Answer**

The bridge network is Docker's default network for standalone containers.

It enables communication between containers on the same host.

---

## 13. What is the host network?

**Answer**

The host network removes network isolation.

The container shares the host's network stack.

Advantages:

- Better performance
- Lower latency

Disadvantages:

- Reduced isolation
- Port conflicts

---

## 14. What is the none network?

**Answer**

The **none** driver disables networking completely.

The container has:

- No external connectivity
- No network interface except loopback

---

## 15. What is an overlay network?

**Answer**

Overlay networks allow containers running on different Docker Swarm nodes to communicate securely.

They are primarily used in multi-host deployments.

---

## 16. What is Macvlan?

**Answer**

Macvlan assigns a unique MAC address to each container.

Containers appear as physical devices on the network.

Useful for legacy applications that require direct network presence.

---

## 17. How does Docker provide DNS?

**Answer**

Docker includes a built-in DNS server.

Containers on the same user-defined network can resolve each other using container or service names.

---

## 18. Why shouldn't containers communicate using IP addresses?

**Answer**

Container IP addresses may change.

Using container or service names provides stable and reliable communication.

---

## 19. How do you connect an existing container to a network?

**Answer**

```bash
docker network connect my-network container_name
```

---

## 20. How do you disconnect a container from a network?

**Answer**

```bash
docker network disconnect my-network container_name
```

---

# Advanced Interview Questions

## 21. What happens when Docker creates a bridge network?

**Answer**

Docker creates:

- Virtual bridge interface
- Virtual Ethernet (veth) pairs
- Network namespace
- IP address allocation
- Internal DNS support (for user-defined bridges)

---

## 22. What is NAT in Docker?

**Answer**

Docker uses Network Address Translation (NAT) to allow containers to communicate with external networks while keeping internal IP addresses private.

---

## 23. How does Docker isolate network traffic?

**Answer**

Docker uses:

- Linux namespaces
- Virtual Ethernet interfaces
- Bridge networks
- iptables rules

These provide network isolation between containers.

---

## 24. What is the difference between bridge and overlay networks?

**Answer**

| Bridge | Overlay |
|---------|----------|
| Single host | Multiple hosts |
| Standalone containers | Docker Swarm |
| Simple configuration | Distributed networking |
| Local communication | Cross-node communication |

---

## 25. Why should production applications avoid exposing unnecessary ports?

**Answer**

Exposing unnecessary ports:

- Increases the attack surface
- Creates security risks
- Complicates firewall management

Only publish ports that are required.

---

# Scenario-Based Interview Questions

## 26. Two containers cannot communicate. What would you investigate?

**Expected Answer**

- Network configuration
- Container status
- Service names
- DNS resolution
- Firewall rules
- Docker network membership

Useful commands:

```bash
docker network ls
```

```bash
docker network inspect my-network
```

---

## 27. Your application works inside the container but cannot be accessed from the browser. Why?

**Expected Answer**

Possible causes:

- Port not published
- Wrong port mapping
- Application listening on `127.0.0.1`
- Firewall blocking traffic

The application should listen on:

```text
0.0.0.0
```

---

## 28. Why can't your application connect to the database using `localhost`?

**Expected Answer**

Inside a container, `localhost` refers to the container itself.

Applications should use:

- Container name
- Docker Compose service name

instead of `localhost`.

---

## 29. How would you troubleshoot DNS failures between containers?

**Expected Answer**

- Verify both containers are on the same network.
- Inspect the Docker network.
- Test DNS resolution using tools such as `nslookup` or `ping`.
- Check container names and service names.
- Restart Docker networking if necessary.

---

## 30. Your production deployment requires communication between multiple Docker hosts. Which network driver would you use?

**Answer**

An **overlay network** because it allows containers running on different Swarm nodes to communicate securely.

---

# Production-Level Questions

## 31. Which Docker network is recommended for production?

**Answer**

For standalone applications:

- User-defined bridge network

For clustered deployments:

- Overlay network

---

## 32. What networking best practices do you follow in production?

**Answer**

- Use user-defined networks.
- Expose only required ports.
- Avoid hardcoded IP addresses.
- Use service discovery.
- Enable TLS where appropriate.
- Restrict network access.
- Monitor network traffic.

---

## 33. How does Docker Compose simplify networking?

**Answer**

Docker Compose automatically:

- Creates a dedicated network
- Connects all services
- Provides automatic DNS resolution using service names

This eliminates manual network configuration for most multi-container applications.

---

# Interview Tips

- Know all Docker network drivers and when to use each.
- Be prepared to explain bridge vs overlay networking.
- Understand Docker DNS and service discovery.
- Explain why applications should listen on `0.0.0.0` instead of `127.0.0.1`.
- Expect troubleshooting questions involving port mapping, DNS, and container communication.

---

## Key Takeaways

- Docker networking enables communication between containers, hosts, and external systems.
- User-defined bridge networks are preferred over the default bridge network because they provide automatic DNS resolution and better isolation.
- Docker supports multiple network drivers, including bridge, host, none, overlay, Macvlan, and IPvlan, each suited to different use cases.
- Containers should communicate using container or service names rather than IP addresses.
- Understanding Docker networking concepts, troubleshooting techniques, and production best practices is essential for backend engineering and DevOps interviews.