# ☸️ Kubernetes — Concepts

Conceptual notes covering Kubernetes from fundamentals through workloads, networking, storage, and package management — building up to interview prep. For command syntax, see [`../cli`](../cli); for example manifests, see [`../sample files`](../sample%20files).

---

## 📚 Concept Notes (16-part series)

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Introduction](01%20-%20Introduction.md) | What Kubernetes is, why container orchestration matters at scale, and the problems it solves |
| 02 | [Core Components](02%20-%20Core%20Components.md) | The Deployment → ReplicaSet → Pod → Container hierarchy and how the pieces relate |
| 03 | [Labels, Selectors & YAML Basics](03%20-%20Labels,%20Selectors%20&%20YAML%20Basics.md) | Key-value tagging for organizing resources, selectors, and core YAML structure |
| 04 | [Namespaces](04-%20Namespaces.md) | Logical partitioning of a cluster for multi-team and multi-environment isolation |
| 05 | [Ingress](05-%20Ingress.md) | Single entry point for routing external HTTP/HTTPS traffic to the right Service |
| 06 | [Helm](06-%20Helm.md) | Kubernetes' package manager — templating, installing, and upgrading applications |
| 07 | [Persistent Storage](07-%20Persistent%20Storage.md) | Why containers are ephemeral, and how PV, PVC, and StorageClass solve data persistence |
| 08 | [StatefulSets](08-%20StatefulSets.md) | Managing stateful workloads — stable identity, storage, and ordered scaling vs. stateless apps |
| 09 | [Kubernetes Services](09-%20Kubernetes%20Services.md) | Stable networking endpoints for Pods that are inherently ephemeral |
| 10 | [Pods](10%20-%20Pods.md) | The smallest deployable unit — one or more containers sharing network, storage, and lifecycle |
| 11 | [ReplicaSets](11%20-%20ReplicaSets.md) | The self-healing controller that maintains a desired Pod replica count |
| 12 | [Deployments](12%20-%20Deployments.md) | Managing ReplicaSets and Pods with rolling updates and rollback support |
| 13 | [ConfigMaps & Secrets](13%20-%20ConfigMaps%20&%20Secrets.md) | Externalizing non-sensitive and sensitive configuration from application code |
| 14 | [kubectl Commands](14%20-%20kubectl%20Commands.md) | The primary CLI for talking to the Kubernetes API server |
| 15 | [Minikube](15%20-%20Minikube.md) | Running a single-node cluster locally for learning and testing |
| 16 | [Kubernetes Interview Questions](16%20-%20Kubernetes%20Interview%20Questions.md) | Interview Q&A grouped by topic, beginner through senior level |

---

## 🔗 See Also

- [`../cli`](../cli) — kubectl and Helm command references for everything above
- [`../sample files`](../sample%20files) — example Deployment and Service manifests
- [`../README.md`](../README.md) — full Kubernetes playbook overview

---

*Part of the [backend-engineering-playbook](../../) knowledge base — Aranya Majumdar*