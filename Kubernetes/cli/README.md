# ☸️ Kubernetes — CLI Reference

Quick-reference `kubectl` and Helm command sheets, organized by task. For the theory behind these commands, see [`../concepts`](../concepts).

---

## Setup & Context

- [Cluster and Context](Cluster%20and%20Context.md) — client/server version, cluster-info, node list and resource usage, API resources, events

## Workloads

- [Pods](Pods.md) — get, watch, describe, logs, exec, port-forward, delete, export as YAML
- [ReplicaSets](ReplicaSets.md) — get, describe, create, edit, scale, delete
- [Deployments](Deployments.md) — get, create, scale, restart, rollout status/history, rollback, delete

## Networking

- [Services](Services.md) — get, describe, create/edit, expose a Deployment as ClusterIP, NodePort, or LoadBalancer
- [Ingress](Ingress.md) — get, describe, create, update, edit, delete Ingress resources
- [Labels and Selectors](Labels%20and%20Selectors.md) — show-labels, and add/overwrite/remove labels on Pods, Deployments, Namespaces, Nodes

## Configuration & Storage

- [Namespaces](Namespaces.md) — get, describe, create, edit, export, delete, switch the active namespace
- [ConfigMaps and Secrets](ConfigMaps%20and%20Secrets.md) — get, describe, create from literals/files/env files/YAML, update
- [Persistent Volumes](Persistent%20Volumes.md) — get, describe, create, edit, delete, check status
- [StorageClass](StorageClass.md) — get, describe, create, edit, delete, sort by creation time

## Package Management

- [Helm](Helm.md) — version, repo add/update, search charts, inspect values/metadata/README, scaffold a new chart

## Local Development

- [Minikube](Minikube.md) — start/stop/delete a cluster, driver and resource flags, cluster IP and node info

## Utilities

- [Debugging](Debugging.md) — events, `describe`, logs (including previous-container and follow mode), `exec` into a Pod
- [YAML](YAML.md) — apply/delete from files or directories, dry-run YAML generation, export live objects as YAML
- [Useful Aliases](Useful%20Aliases.md) — shell aliases for `kubectl`, plus quick-list shortcuts for common resources

---

## 🔗 See Also

- [`../concepts`](../concepts) — the theory behind each of these commands
- [`../README.md`](../README.md) — full Kubernetes playbook overview

---

*Part of the [backend-engineering-playbook](../../) knowledge base — Aranya Majumdar*