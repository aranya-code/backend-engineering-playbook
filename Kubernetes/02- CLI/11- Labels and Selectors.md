# Labels and Selectors

# Labels

## To display labels for all resources

```bash
kubectl get pods --show-labels
```

---

## To display labels for Deployments

```bash
kubectl get deployments --show-labels
```

---

## To display labels for ReplicaSets

```bash
kubectl get rs --show-labels
```

---

## To display labels for Services

```bash
kubectl get svc --show-labels
```

---

## To display labels for Namespaces

```bash
kubectl get namespaces --show-labels
```

---

## To add a label to a Pod

```bash
kubectl label pod <pod-name> app=frontend
```

---

## To add multiple labels to a Pod

```bash
kubectl label pod <pod-name> env=dev tier=backend
```

---

## To overwrite an existing label

```bash
kubectl label pod <pod-name> app=backend --overwrite
```

---

## To remove a label from a Pod

```bash
kubectl label pod <pod-name> app-
```

---

## To add a label to a Deployment

```bash
kubectl label deployment <deployment-name> environment=production
```

---

## To add a label to a Namespace

```bash
kubectl label namespace <namespace-name> team=backend
```

---

## To add a label to a Node

```bash
kubectl label node <node-name> disktype=ssd
```

---

## To remove a label from a Node

```bash
kubectl label node <node-name> disktype-
```

---

## To display a resource in YAML and view labels

```bash
kubectl get pod <pod-name> -o yaml
```

Look under

```yaml
metadata:
  labels:
```

---

# Label Selectors

## To list Pods matching a label

```bash
kubectl get pods -l app=nginx
```

---

## To list Deployments matching a label

```bash
kubectl get deployments -l app=nginx
```

---

## To list Services matching a label

```bash
kubectl get svc -l app=nginx
```

---

## To list ReplicaSets matching a label

```bash
kubectl get rs -l app=nginx
```

---

## To list Pods with multiple labels

```bash
kubectl get pods -l app=nginx,environment=production
```

---

## To list Pods using an equality selector

```bash
kubectl get pods -l app=frontend
```

---

## To list Pods using a not equal selector

```bash
kubectl get pods -l app!=frontend
```

---

## To list Pods where a label exists

```bash
kubectl get pods -l app
```

---

## To list Pods where a label does not exist

```bash
kubectl get pods -l '!app'
```

---

## To list Pods using an "in" selector

```bash
kubectl get pods -l 'environment in (dev,test)'
```

---

## To list Pods using a "notin" selector

```bash
kubectl get pods -l 'environment notin (production)'
```

---

## To list Pods matching multiple expressions

```bash
kubectl get pods -l 'app=nginx,environment=production'
```

---

## To delete Pods matching a label

```bash
kubectl delete pods -l app=nginx
```

---

## To delete Deployments matching a label

```bash
kubectl delete deployments -l app=nginx
```

---

## To delete Services matching a label

```bash
kubectl delete svc -l app=nginx
```

---

# Annotations

## To display annotations of a resource

```bash
kubectl get pod <pod-name> -o yaml
```

Look under

```yaml
metadata:
  annotations:
```

---

## To add an annotation to a Pod

```bash
kubectl annotate pod <pod-name> owner=backend-team
```

---

## To overwrite an annotation

```bash
kubectl annotate pod <pod-name> owner=devops-team --overwrite
```

---

## To remove an annotation

```bash
kubectl annotate pod <pod-name> owner-
```

---

## To add an annotation to a Deployment

```bash
kubectl annotate deployment <deployment-name> owner=backend-team
```

---

## To add an annotation to a Namespace

```bash
kubectl annotate namespace development owner=backend
```

---

# Node Labels

## To display Node labels

```bash
kubectl get nodes --show-labels
```

---

## To display detailed information about a Node

```bash
kubectl describe node <node-name>
```

Look under

```text
Labels
```

---

## To schedule a Pod using a Node Selector

Specify the label in the Pod manifest.

```yaml
spec:
  nodeSelector:
    disktype: ssd
```

Apply the manifest

```bash
kubectl apply -f pod.yaml
```

---

# Troubleshooting Labels

## To verify Pod labels

```bash
kubectl get pods --show-labels
```

---

## To verify Service selectors

```bash
kubectl describe svc <service-name>
```

Look under

```text
Selector
```

---

## To verify Deployment selectors

```bash
kubectl describe deployment <deployment-name>
```

Look under

```text
Selector
```

---

## To verify ReplicaSet selectors

```bash
kubectl describe rs <replicaset-name>
```

Look under

```text
Selector
```

---

## To verify why a Service is not routing traffic

1. Check the Service selector

```bash
kubectl describe svc <service-name>
```

2. Verify Pod labels

```bash
kubectl get pods --show-labels
```

3. Ensure the labels match the Service selector.

---

## To verify resources using a specific label

```bash
kubectl get all -l app=nginx
```

---

## To display all resources with labels

```bash
kubectl get all --show-labels
```

---

## To apply all manifests in the current directory

```bash
kubectl apply -f .
```

---

## To delete all manifests in the current directory

```bash
kubectl delete -f .
```