# Docker Swarm

## Overview
Docker Swarm is Docker's native clustering and orchestration tool. It allows you to manage a cluster of Docker nodes as a single virtual system, deploying services with high availability, scaling, and rolling updates. Swarm uses a decentralized architecture where nodes act as managers (handling orchestration and cluster state) or workers (executing tasks).

## Common Commands

| Command | Description |
|---|---|
| `docker swarm init` | Initialize a new swarm |
| `docker swarm join --token <token> <ip>:<port>` | Join a node to a swarm as a manager or worker |
| `docker swarm join-token worker` | Display the command to join a worker node |
| `docker swarm join-token manager` | Display the command to join a manager node |
| `docker swarm leave` | Leave a swarm (use `--force` on managers) |
| `docker node ls` | List all nodes in the swarm |
| `docker node promote <node>` | Promote a worker to a manager |
| `docker node demote <node>` | Demote a manager to a worker |
| `docker node inspect <node>` | Inspect a specific node |
| `docker node update --availability drain <node>` | Drain a node (stop tasks, prevent new tasks) |
| `docker network create --driver overlay <network>` | Create a multi-host overlay network |
| `docker service create <image>` | Create a new service |
| `docker service ls` | List running services |
| `docker service update <service> --<setting>` | Update a service's configuration |
| `docker service scale <service>=<replicas>` | Scale a service to a specific number of replicas |
| `docker service rollback <service>` | Roll back a service to its previous configuration |
| `docker service inspect <service>` | Inspect a specific service |
| `docker service ps <service>` | List tasks (containers) backing a service |
| `docker service logs myapp_web` | Fetch logs for a specific service |
| `docker stack deploy -c docker-compose.yml myapp` | Deploy or update a stack from a Compose file |
| `docker stack ls` | List deployed stacks |
| `docker stack ps myapp` | List the tasks in a stack |
| `docker stack services myapp` | List the services in a stack |
| `docker stack rm myapp` | Remove a stack |

## Command Breakdown

The `docker service create` command supports numerous flags to configure the service:

*   `--replicas`: Specify the number of container instances to run.
*   `--publish` / `-p`: Map a port on the host to a port inside the container (e.g., `-p 8080:80`). In Swarm, this uses the routing mesh by default.
*   `--network`: Attach the service to a specified overlay network.
*   `--env` / `-e`: Set environment variables.
*   `--mount`: Attach storage volumes or bind mounts (e.g., `--mount type=volume,source=my-vol,target=/app`).
*   `--constraint`: Restrict where tasks can be scheduled (e.g., `--constraint node.role==manager`).
*   `--update-delay`: Delay between updates of individual tasks during a rolling update (e.g., `10s`).
*   `--rollback-config`: Configuration for rolling back if an update fails.

## Practical Examples

### Initialize a Swarm and Join a Worker

Initialize the swarm on the manager node:
```bash
docker swarm init --advertise-addr 192.168.1.10
```

```text
Swarm initialized: current node (dxn1zl6l61619) is now a manager.

To add a worker to this swarm, run the following command:
    docker swarm join --token SWMTKN-1-49nj1cmql0jkz5s95... 192.168.1.10:2377
```

Join the worker node using the provided command:
```bash
docker swarm join --token SWMTKN-1-49nj1cmql0jkz5s95... 192.168.1.10:2377
```

### Deploy a Service with Replicas

```bash
docker service create --name web_app --replicas 3 --publish 8080:80 nginx
```

### Scale a Service

```bash
docker service scale web_app=5
```

```text
web_app scaled to 5
overall progress: 5 out of 5 tasks 
1/5: running   [==================================================>] 
2/5: running   [==================================================>] 
3/5: running   [==================================================>] 
4/5: running   [==================================================>] 
5/5: running   [==================================================>] 
verify: Service converged
```

### Rolling Update Workflow

Update the image of an existing service with a 10-second delay between task updates:
```bash
docker service update --image nginx:alpine --update-delay 10s web_app
```

## Real-World Use Cases
*   **High Availability:** Distributing replicas across multiple servers so an application remains available even if a node fails.
*   **Zero-Downtime Deployments:** Updating services incrementally across the cluster without interrupting user traffic.
*   **Microservices Architecture:** Using overlay networks and stacks to deploy complex applications comprising dozens of interdependent services.
*   **Load Balancing:** Leveraging the Swarm routing mesh to automatically route requests to any available node running a given service.

## Common Mistakes
*   **Running State on Workers:** Attempting to store persistent local data on worker nodes without using external volumes, leading to data loss when containers shift nodes.
*   **Even Number of Managers:** Running an even number of manager nodes (e.g., 2 or 4), which can lead to split-brain scenarios. A majority is required for consensus.
*   **Forgetting to Publish Ports:** Creating a service but not publishing ports, making it inaccessible from outside the swarm.

## Best Practices
*   **Odd Number of Managers:** Always run an odd number of manager nodes (3, 5, or 7) to maintain a healthy Raft consensus and fault tolerance.
*   **Drain Nodes for Maintenance:** Always run `docker node update --availability drain <node>` before taking a server down for OS updates or maintenance, ensuring tasks are gracefully rescheduled.
*   **Use Stacks for Declarative Configuration:** Prefer `docker stack deploy` with Compose files over imperative `docker service create` commands for reproducibility.

## Interview Tips
*   **What is the Swarm routing mesh?** It allows any node in the swarm to accept connections on published ports for any service in the swarm, transparently routing requests to an active task.
*   **How does Swarm maintain state?** Through an embedded distributed key-value store using the Raft consensus algorithm, managed entirely by the manager nodes.

## Related Topics
- [Docker Compose](06-%20Docker%20Compose.md)
- [Networking](05-%20Networking.md)
- [Docker Secrets](08-%20Docker%20Secrets.md)

## Key Takeaways
*   Swarm orchestrates containers across a cluster of nodes.
*   Managers handle state and scheduling; workers execute tasks.
*   Services provide high availability, scaling, and rolling updates.
*   Stacks allow deploying complex, multi-service applications declaratively.
*   Overlay networks enable cross-host container communication.
