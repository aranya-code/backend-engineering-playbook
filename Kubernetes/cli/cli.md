# Kubectl Commands

### To get node details

```bash
kubectl get nodes
```

### To get pod details

```bash
kubectl get pod
```

### To get kubernetes service details

```bash
kubectl get services
```

### Creating a deployment

```bash
kubectl create deployment <Name> --image=<Image Name> [options]
```

### To get all the deployment details

```bash
kubectl get deployment
```

### To get replicaset details

```bash
kubectl get replicaset
```

### Editing the deployment

```bash
kubectl edit deployment <name>
```

### Get the logs of a Pod

```bash
kubectl logs <Name>
```

### To get details of Pod

```bash
kubectl describe pod <Name>
```

### Entering execution mode

```bash
kubectl exec -it <Name> --bin/bash
```

### To delete the deployment

```bash
kubectl delete deployment <Name>
```

### To apply the changes in deployment

```bash
kubectl apply -f <filename>
```