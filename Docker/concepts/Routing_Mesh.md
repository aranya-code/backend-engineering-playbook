# Docker Swarm Routing Mesh

## Definition
Routing Mesh is Docker Swarm's built-in ingress load balancing system that routes incoming requests to the correct service task, regardless of which node receives the traffic.

## Key Points
- Works across all nodes in the Swarm cluster.
- Uses Linux IPVS (IP Virtual Server) for load balancing.
- Distributes requests across service replicas (tasks).
- Every node listens on published service ports.
- Users can connect to any node and still reach the service.

## How Routing Mesh Works

### 1. External Traffic
Client → Any Swarm Node → Routing Mesh → Available Service Task

- Traffic can enter through any node.
- Swarm forwards the request to a healthy task.
- The task may run on the same node or a different node.

### 2. Internal Service Communication
- Services communicate using an Overlay Network.
- Docker provides a Virtual IP (VIP).
- Requests are load-balanced across replicas.

## Example
```bash
docker service create   --name web   --replicas 3   -p 8080:80   nginx
```

Access:
```bash
http://<any-node-ip>:8080
```

## Interview Notes
Q: Do all replicas need to run on the node receiving traffic?
A: No. Routing Mesh forwards traffic to replicas running anywhere in the cluster.

Q: Which Linux technology powers Routing Mesh?
A: IPVS (IP Virtual Server).
