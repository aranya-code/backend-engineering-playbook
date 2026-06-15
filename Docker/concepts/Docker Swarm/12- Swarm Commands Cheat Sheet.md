# Docker Swarm Commands Cheat Sheet

## Overview

This cheat sheet contains the most commonly used Docker Swarm commands for:

- Swarm Initialization
- Node Management
- Service Management
- Scaling
- Updates
- Rollbacks
- Networking
- Secrets
- Cluster Administration

Use this file for quick revision before interviews, certifications, or production work.

---

# Swarm Initialization

## Initialize Swarm

```bash
docker swarm init
```

Initialize current node as manager.

---

## Initialize with Advertise Address

```bash
docker swarm init \
--advertise-addr <manager-ip>
```

Example:

```bash
docker swarm init \
--advertise-addr 192.168.1.10
```

---

## View Swarm Information

```bash
docker info
```

Check:

```text
Swarm: active
```

---

## Inspect Swarm

```bash
docker swarm inspect
```

Pretty format:

```bash
docker swarm inspect --pretty
```

---

# Join and Leave Cluster

## Get Worker Join Token

```bash
docker swarm join-token worker
```

---

## Get Manager Join Token

```bash
docker swarm join-token manager
```

---

## Join as Worker

```bash
docker swarm join \
--token <worker-token> \
<manager-ip>:2377
```

---

## Join as Manager

```bash
docker swarm join \
--token <manager-token> \
<manager-ip>:2377
```

---

## Leave Swarm

```bash
docker swarm leave
```

---

## Force Manager Leave

```bash
docker swarm leave --force
```

---

# Node Management

## List Nodes

```bash
docker node ls
```

---

## Inspect Node

```bash
docker node inspect <node-name>
```

Pretty format:

```bash
docker node inspect <node-name> --pretty
```

---

## Promote Worker to Manager

```bash
docker node promote <node-name>
```

---

## Demote Manager to Worker

```bash
docker node demote <node-name>
```

---

## Remove Node

```bash
docker node rm <node-name>
```

---

# Node Availability

## Active

```bash
docker node update \
--availability active \
<node-name>
```

---

## Pause

```bash
docker node update \
--availability pause \
<node-name>
```

---

## Drain

```bash
docker node update \
--availability drain \
<node-name>
```

---

# Service Management

## Create Service

```bash
docker service create nginx
```

---

## Create Named Service

```bash
docker service create \
--name web \
nginx
```

---

## Create Service with Replicas

```bash
docker service create \
--name web \
--replicas 3 \
nginx
```

---

## Create Global Service

```bash
docker service create \
--mode global \
nginx
```

---

## List Services

```bash
docker service ls
```

---

## Inspect Service

```bash
docker service inspect web
```

Pretty format:

```bash
docker service inspect web --pretty
```

---

## Remove Service

```bash
docker service rm web
```

---

# Service Tasks

## View Service Tasks

```bash
docker service ps web
```

---

## View Running Containers

```bash
docker ps
```

---

# Scaling Services

## Scale Service

```bash
docker service scale web=5
```

---

## Scale Multiple Services

```bash
docker service scale \
web=5 \
api=3
```

---

## Alternative Scaling Method

```bash
docker service update \
--replicas 5 \
web
```

---

# Service Updates

## Update Service Image

```bash
docker service update \
--image nginx:latest \
web
```

---

## Update Parallelism

```bash
docker service update \
--update-parallelism 1 \
web
```

---

## Update Delay

```bash
docker service update \
--update-delay 30s \
web
```

---

## Automatic Rollback on Failure

```bash
docker service update \
--update-failure-action rollback \
web
```

---

# Rollbacks

## Rollback Service

```bash
docker service rollback web
```

---

## Rollback Delay

```bash
docker service update \
--rollback-delay 10s \
web
```

---

## Rollback Parallelism

```bash
docker service update \
--rollback-parallelism 1 \
web
```

---

# Networking

## List Networks

```bash
docker network ls
```

---

## Create Overlay Network

```bash
docker network create \
--driver overlay \
app-network
```

---

## Create Encrypted Overlay Network

```bash
docker network create \
--driver overlay \
--opt encrypted \
secure-network
```

---

## Inspect Network

```bash
docker network inspect app-network
```

---

## Remove Network

```bash
docker network rm app-network
```

---

# Port Publishing

## Publish Port

```bash
docker service create \
--name web \
--publish 80:80 \
nginx
```

---

## Multiple Ports

```bash
docker service create \
--publish 80:80 \
--publish 443:443 \
nginx
```

---

## Host Mode Publishing

```bash
docker service create \
--publish mode=host,target=80,published=80 \
nginx
```

---

# Secrets

## Create Secret

```bash
docker secret create \
db_password \
password.txt
```

---

## Create Secret from Echo

```bash
echo "mypassword" | \
docker secret create db_password -
```

---

## List Secrets

```bash
docker secret ls
```

---

## Inspect Secret

```bash
docker secret inspect db_password
```

---

## Remove Secret

```bash
docker secret rm db_password
```

---

## Create Service with Secret

```bash
docker service create \
--secret db_password \
mysql
```

---

## Add Secret to Existing Service

```bash
docker service update \
--secret-add db_password \
mysql
```

---

## Remove Secret from Service

```bash
docker service update \
--secret-rm db_password \
mysql
```

---

# Configs

## Create Config

```bash
docker config create \
nginx-config \
nginx.conf
```

---

## List Configs

```bash
docker config ls
```

---

## Inspect Config

```bash
docker config inspect nginx-config
```

---

## Remove Config

```bash
docker config rm nginx-config
```

---

# Placement Constraints

## Run Only on Managers

```bash
docker service create \
--constraint node.role==manager \
nginx
```

---

## Run Only on Workers

```bash
docker service create \
--constraint node.role==worker \
nginx
```

---

# Logs and Troubleshooting

## View Service Logs

```bash
docker service logs web
```

---

## Follow Logs

```bash
docker service logs -f web
```

---

## View Node Information

```bash
docker node ls
```

---

## View Service Status

```bash
docker service ps web
```

---

## View Container Logs

```bash
docker logs <container-id>
```

---

# Token Rotation

## Rotate Worker Token

```bash
docker swarm join-token \
--rotate worker
```

---

## Rotate Manager Token

```bash
docker swarm join-token \
--rotate manager
```

---

# High Availability

## Promote Worker

```bash
docker node promote worker1
```

---

## Demote Manager

```bash
docker node demote manager2
```

---

## Check Leader

```bash
docker node ls
```

Look for:

```text
Leader
```

---

# Cleanup Commands

## Remove Service

```bash
docker service rm web
```

---

## Remove Network

```bash
docker network rm app-network
```

---

## Remove Secret

```bash
docker secret rm db_password
```

---

## Leave Swarm

```bash
docker swarm leave
```

---

## Force Leave

```bash
docker swarm leave --force
```

---

# Interview Essentials

## Initialize Cluster

```bash
docker swarm init
```

---

## Join Worker

```bash
docker swarm join
```

---

## Create Service

```bash
docker service create
```

---

## Scale Service

```bash
docker service scale
```

---

## View Tasks

```bash
docker service ps
```

---

## Rolling Update

```bash
docker service update
```

---

## Rollback

```bash
docker service rollback
```

---

## Overlay Network

```bash
docker network create \
--driver overlay
```

---

## Create Secret

```bash
docker secret create
```

---

## View Nodes

```bash
docker node ls
```

---

# One-Page Revision Commands

```bash
docker swarm init

docker swarm join

docker node ls

docker node promote

docker node demote

docker service create

docker service ls

docker service ps

docker service scale

docker service update

docker service rollback

docker network create --driver overlay

docker secret create

docker secret ls

docker node update --availability drain

docker swarm leave
```

---

# Interview One-Liner

Mastering these Docker Swarm commands allows you to initialize clusters, manage nodes, deploy services, scale applications, perform rolling updates, manage secrets, configure networking, and troubleshoot production swarm environments efficiently.
