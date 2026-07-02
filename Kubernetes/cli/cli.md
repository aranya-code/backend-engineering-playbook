# Cli

Created by: aranya majumdar

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

### To get service details

```bash
kubectl describe service <name>
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

### To get detailed information of pod

```bash
kubectl get pod -o wide
```

### To get deployment configuration

```bash
kubectl get deployment nginx-depl -o yaml
```

### To get deployment configuration into a file

```bash
kubectl get deployment nginx-depl -o yaml > <filename.yaml>
```

### To delete the deployment

```bash
kubectl delete deployment -f <filename>
```

### To delete the service

```bash
kubectl delete service -f <filename>
```

### To get all the clusters

```bash
kubectl get all
```

### To create a namespace

```bash
kubectl create namespace <name of namespace>
```

### To add ingress controller to cluster

```bash
minikube addons enable ingress
```

### To get all the pods of Kube System

```bash
 kubectl get pod -n kube-system
```

### To list all the namespaces

```bash
kubectl get ns
```

### To get all the details of kubernetes resources

```bash
kubectl get all -n kubernetes-dashboard
```

### To install a Helm package

```bash
helm install <chartname>
```

### To provide values to Helm packages

```bash
helm install --values=<my-values.yaml> <chartname>
```

### To provide values to Helm packages using set

```bash
helm install --set <values>
```

### To upgrade Helm packages

```bash
helm upgrade <chartname>
```

### To rollback Helm packages

```bash
helm rollback <chartname>
```