# 🐳 Docker Swarm

Docker's native orchestration and clustering solution — architecture, node roles, networking, scaling, and high availability, plus a head-to-head with Kubernetes.

---

## 📚 Notes

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Introduction](01-%20Introduction.md) | What Docker Swarm is and the orchestration problems it solves — HA, scaling, load balancing, service discovery |
| 02 | [Swarm Architecture](02-%20Swarm%20Architecture.md) | Control plane vs. data plane, and the layers that make up a Swarm cluster |
| 03 | [Manager and Worker Nodes](03-%20Manager%20and%20Worker%20Nodes.md) | Node types and the responsibilities of manager nodes |
| 04 | [Swarm Initialization and Cluster Management](04-%20Swarm%20Initialization%20and%20Cluster%20Management.md) | Initializing a swarm, the advertise address, and cluster state before/after |
| 05 | [Services and Tasks](05-%20Services%20and%20Tasks.md) | Traditional Docker vs. Swarm services, desired state, and service architecture |
| 06 | [Service Scaling and Replication](06-%20Service%20Scaling%20and%20Replication.md) | Vertical vs. horizontal scaling, and why replication matters |
| 07 | [Routing Mesh and Load Balancing](07-%20Routing%20Mesh%20and%20Load%20Balancing.md) | How the routing mesh publishes ports and load-balances traffic across nodes |
| 08 | [Overlay Networks](08-%20Overlay%20Networks.md) | Multi-host networking and service discovery across the Swarm |
| 09 | [Rolling Updates and Rollbacks](09-%20Rolling%20Updates%20and%20Rollbacks.md) | Zero-downtime service updates and the rolling update process |
| 10 | [Docker Swarm Secrets](10-%20Docker%20Swarm%20Secrets.md) | Secure secret distribution to services, and how secrets work under the hood |
| 11 | [High Availability and Raft](11-%20High%20Availability%20and%20Raft.md) | Manager node HA and the Raft consensus algorithm behind it |
| 12 | [Swarm Commands Cheat Sheet](12-%20Swarm%20Commands%20Cheat%20Sheet.md) | Core CLI commands — init, join tokens, inspect, and cluster management |
| 13 | [Docker Swarm vs Kubernetes](13-%20Docker%20Swarm%20vs%20Kubernetes.md) | Architecture and cluster setup compared side-by-side |

---

## 🔗 See Also

- [`../Docker Stacks`](../Docker%20Stacks) — deploying multi-service apps on top of a Swarm cluster
- [`../`](../) — Docker concepts overview
- [`../../README.md`](../../README.md) — full Docker knowledge base

---

*Part of the [backend-engineering-playbook](../../../) knowledge base — Aranya Majumdar*