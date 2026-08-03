# Docker Networking

## Overview
Docker networking allows containers to communicate with each other, the host system, and the outside world. By default, containers are isolated, but Docker provides built-in network drivers to configure robust and secure communication channels.

## Common Commands

| Command | Description |
|---|---|
| `docker network ls` | List all Docker networks. |
| `docker network create <network>` | Create a new custom network. |
| `docker network inspect <network>` | View detailed information about a network. |
| `docker network connect <network> <container>` | Connect a running container to a network. |
| `docker network disconnect <network> <container>` | Disconnect a container from a network. |
| `docker network rm <network>` | Remove one or more networks. |
| `docker network prune` | Remove all unused networks. |

## Command Breakdown

### Network Drivers Comparison

Docker uses drivers to manage how networking operates. 

| Driver | Description | When to Use |
|---|---|---|
| **bridge** | The default driver. Creates an isolated network for containers on the same host. | Running standalone containers that need to communicate on a single host. |
| **host** | Removes network isolation between the container and the Docker host. | High-performance networking or when a container needs to bind to a large range of ports. |
| **overlay** | Connects multiple Docker daemons together (Swarm mode). | Multi-host networking, distributed services. |
| **macvlan** | Assigns a MAC address to a container, making it appear as a physical device on the network. | Legacy applications that expect to be directly connected to the physical network. |
| **none** | Completely disables networking for a container. | Maximum isolation, running a purely offline task. |

### Attaching a Container at Creation

You can specify a network when starting a container using the `--network` flag:

```bash
docker run -d --name web --network my_custom_network nginx
```

## Practical Examples

### Creating a Custom Bridge Network

```bash
# Create the network
docker network create my-app-network

# Run a database container on the network
docker run -d --name db --network my-app-network postgres

# Run an app container on the same network
docker run -d --name app --network my-app-network node-app
```

### DNS Resolution Between Containers

Containers on a **custom bridge network** can resolve each other by container name.

```bash
# From inside the 'app' container, ping the 'db' container
docker exec -it app ping db
```
```text
PING db (172.18.0.2): 56 data bytes
64 bytes from 172.18.0.2: icmp_seq=0 ttl=64 time=0.100 ms
```

### Expected Output for `docker network ls`

```bash
docker network ls
```
```text
NETWORK ID     NAME               DRIVER    SCOPE
1a2b3c4d5e6f   bridge             bridge    local
2b3c4d5e6f7a   host               host      local
3c4d5e6f7a8b   my-app-network     bridge    local
4d5e6f7a8b9c   none               null      local
```

### Expected Output for `docker network inspect`

```bash
docker network inspect my-app-network
```
```text
[
    {
        "Name": "my-app-network",
        "Id": "3c4d5e6f7a8b...",
        "Scope": "local",
        "Driver": "bridge",
        "IPAM": {
            "Config": [
                {
                    "Subnet": "172.18.0.0/16",
                    "Gateway": "172.18.0.1"
                }
            ]
        },
        "Containers": {
            "abc123def456...": {
                "Name": "db",
                "IPv4Address": "172.18.0.2/16"
            }
        }
    }
]
```

## Real-World Use Cases
- **Isolating Services:** Placing internal databases on a backend network that isn't exposed to the host or internet, while putting web servers on a frontend network.
- **Multi-Container Apps:** Ensuring that APIs, caches, and databases can communicate efficiently using internal DNS rather than hardcoded IP addresses.

## Common Mistakes
- **Using the Default Bridge for Production:** The default `bridge` network does not support automatic DNS resolution between containers by name. You must use legacy `--link` flags, which is deprecated.
- **Not Creating Custom Networks:** Throwing all containers onto the default bridge creates a massive attack surface if one container is compromised.
- **Hardcoding IP Addresses:** Container IPs change. Always rely on Docker's built-in DNS (container names) within custom networks.

## Best Practices
- **Always Use Custom Networks:** Create separate networks for separate environments or application tiers (e.g., `frontend-net`, `backend-net`).
- **Name Networks Descriptively:** Use clear, recognizable names (`ecommerce-db-net`) to easily identify their purpose.
- **Prune Regularly:** Run `docker network prune` periodically to clean up orphaned networks.

## Interview Tips
**Q: What is the default Docker network?**  
A: The default network is the `bridge` network. All containers attach to this by default unless specified otherwise. It provides basic isolation but lacks automatic DNS resolution between containers.

**Q: How do containers communicate with each other?**  
A: Containers on the same custom bridge network can communicate using the built-in DNS server, resolving each other's container names to internal IP addresses.

## Related Topics
- [Images and Containers](02-%20Images%20and%20Containers.md)
- [Docker Compose](06-%20Docker%20Compose.md)
- [Docker Swarm](09-%20Docker%20Swarm.md)

## Key Takeaways
- Use `docker network ls` and `docker network inspect` to explore existing networks.
- Always create custom bridge networks for applications to enable automatic DNS resolution.
- Understand the difference between `bridge`, `host`, and `overlay` drivers to select the right networking model.
- Avoid the default `bridge` network for production applications.
