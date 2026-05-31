# Docker Swarm

---

### Initializes a Swarm cluster.

```bash
docker swarm init
```

### Lists Swarm nodes.

```bash
docker node ls
```

### Creates a Swarm service.

```bash
docker service create <image>
```

### Lists Swarm services.

```bash
docker service ls
```

### Updates a service configuration.

```bash
docker service update <service> --<setting>
```

### Creates an overlay network.

```bash
docker network create --driver overlay <network>
```

### Deploys a stack.

```bash
docker stack deploy -c docker-compose.yml myapp
```

### Lists deployed stacks.

```bash
docker stack ls
```

### Shows stack tasks.

```bash
docker stack ps myapp
```

### Shows stack services.

```bash
docker stack services myapp
```

### Removes a stack.

```bash
docker stack rm myapp
```

### Displays service logs.

```bash
docker service logs myapp_web
```
