# Namespaces

## To list all Namespaces

```bash
kubectl get namespaces
```

---

## To list Namespaces using the short name

```bash
kubectl get ns
```

---

## To display detailed information about a Namespace

```bash
kubectl describe namespace <namespace-name>
```

---

## To create a Namespace

```bash
kubectl create namespace <namespace-name>
```

Example

```bash
kubectl create namespace development
```

---

## To create a Namespace from a YAML file

```bash
kubectl apply -f namespace.yaml
```

---

## To update a Namespace

```bash
kubectl apply -f namespace.yaml
```

---

## To edit a Namespace

```bash
kubectl edit namespace <namespace-name>
```

---

## To export Namespace YAML

```bash
kubectl get namespace <namespace-name> -o yaml
```

---

## To export Namespace JSON

```bash
kubectl get namespace <namespace-name> -o json
```

---

## To delete a Namespace

```bash
kubectl delete namespace <namespace-name>
```

---

## To delete a Namespace using a YAML file

```bash
kubectl delete -f namespace.yaml
```

---

## To display the current Namespace

```bash
kubectl config view --minify --output 'jsonpath={..namespace}'
```

---

## To switch the default Namespace for the current context

```bash
kubectl config set-context --current --namespace=<namespace-name>
```

Example

```bash
kubectl config set-context --current --namespace=development
```

---

## To switch back to the default Namespace

```bash
kubectl config set-context --current --namespace=default
```

---

## To list Pods in a specific Namespace

```bash
kubectl get pods -n <namespace-name>
```

---

## To list Deployments in a specific Namespace

```bash
kubectl get deployments -n <namespace-name>
```

---

## To list Services in a specific Namespace

```bash
kubectl get svc -n <namespace-name>
```

---

## To list ReplicaSets in a specific Namespace

```bash
kubectl get rs -n <namespace-name>
```

---

## To list ConfigMaps in a specific Namespace

```bash
kubectl get cm -n <namespace-name>
```

---

## To list Secrets in a specific Namespace

```bash
kubectl get secrets -n <namespace-name>
```

---

## To create a Pod in a specific Namespace

```bash
kubectl apply -f pod.yaml -n <namespace-name>
```

---

## To create a Deployment in a specific Namespace

```bash
kubectl apply -f deployment.yaml -n <namespace-name>
```

---

## To delete all Pods in a Namespace

```bash
kubectl delete pods --all -n <namespace-name>
```

---

## To delete all Deployments in a Namespace

```bash
kubectl delete deployments --all -n <namespace-name>
```

---

## To delete all Services in a Namespace

```bash
kubectl delete svc --all -n <namespace-name>
```

---

## To display all resources in a Namespace

```bash
kubectl get all -n <namespace-name>
```

---

## To display all resources in all Namespaces

```bash
kubectl get all -A
```

---

## To display events in a Namespace

```bash
kubectl get events -n <namespace-name>
```

---

## To display resource usage in a Namespace (Metrics Server required)

```bash
kubectl top pods -n <namespace-name>
```

---

## To port-forward a Pod in a Namespace

```bash
kubectl port-forward pod/<pod-name> 8080:80 -n <namespace-name>
```

---

## To execute a command inside a Pod in a Namespace

```bash
kubectl exec -it <pod-name> -n <namespace-name> -- bash
```

---

## To view logs from a Pod in a Namespace

```bash
kubectl logs <pod-name> -n <namespace-name>
```

---

## To follow logs from a Pod in a Namespace

```bash
kubectl logs -f <pod-name> -n <namespace-name>
```

---

## To describe a Pod in a Namespace

```bash
kubectl describe pod <pod-name> -n <namespace-name>
```

---

## To describe a Deployment in a Namespace

```bash
kubectl describe deployment <deployment-name> -n <namespace-name>
```

---

## To describe a Service in a Namespace

```bash
kubectl describe svc <service-name> -n <namespace-name>
```

---

## To display labels on Namespaces

```bash
kubectl get namespaces --show-labels
```

---

## To add a label to a Namespace

```bash
kubectl label namespace <namespace-name> environment=development
```

---

## To remove a label from a Namespace

```bash
kubectl label namespace <namespace-name> environment-
```

---

## To annotate a Namespace

```bash
kubectl annotate namespace <namespace-name> owner=backend-team
```

---

## To remove an annotation from a Namespace

```bash
kubectl annotate namespace <namespace-name> owner-
```

---

## To verify the Namespace of a Pod

```bash
kubectl get pods -A
```

Check the **NAMESPACE** column.

---

## To display only Namespace names

```bash
kubectl get namespaces -o name
```

---

## To list Namespaces sorted by creation time

```bash
kubectl get namespaces --sort-by=.metadata.creationTimestamp
```

---

## To apply all manifests to a specific Namespace

```bash
kubectl apply -f . -n <namespace-name>
```

---

## To delete all manifests from a specific Namespace

```bash
kubectl delete -f . -n <namespace-name>
```

---

## To troubleshoot Namespace issues

1. Verify the Namespace exists

```bash
kubectl get namespaces
```

2. Verify the current context

```bash
kubectl config current-context
```

3. Verify the current Namespace

```bash
kubectl config view --minify --output 'jsonpath={..namespace}'
```

4. Verify resources inside the Namespace

```bash
kubectl get all -n <namespace-name>
```