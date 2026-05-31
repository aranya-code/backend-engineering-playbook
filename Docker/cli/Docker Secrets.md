# Docker Secrets

---

### Creates a new Docker Secret.

```bash
echo "mypassword" | docker secret create db_password -
```

### Lists all Docker Secrets.

```bash
docker secret ls
```

### Displays details of a specific Secret.

```bash
docker secret inspect db_password
```

### Creates a service with an attached Secret.

```bash
docker service create --name mysql --secret db_password mysql
```

### Removes a Secret.

```bash
docker secret rm db_password
```

### Lists mounted Secrets inside a container.

```bash
ls /run/secrets
```

### Displays the value of a mounted Secret.

```bash
cat /run/secrets/db_password
```
