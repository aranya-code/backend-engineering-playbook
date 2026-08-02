# Cluster and Context

## To check the Kubernetes client and server version

```bash
kubectl version
```

---

## To display cluster information

```bash
kubectl cluster-info
```

---

## To list all nodes in the cluster

```bash
kubectl get nodes
```

---

## To list nodes using the short name

```bash
kubectl get no
```

---

## To display detailed information about a node

```bash
kubectl describe node <node-name>
```

---

## To display resource usage of all nodes (Metrics Server required)

```bash
kubectl top nodes
```

---

## To display resource usage of all Pods (Metrics Server required)

```bash
kubectl top pods
```

---

## To display all API resources available in the cluster

```bash
kubectl api-resources
```

---

## To display all API versions supported by the cluster

```bash
kubectl api-versions
```

---

## To display cluster events

```bash
kubectl get events
```

---

## To display events sorted by creation time

```bash
kubectl get events --sort-by=.metadata.creationTimestamp
```

---

## To list all namespaces

```bash
kubectl get namespaces
```

---

## To list namespaces using the short name

```bash
kubectl get ns
```

---

## To display all resources in the current namespace

```bash
kubectl get all
```

---

## To display all resources in a specific namespace

```bash
kubectl get all -n <namespace>
```

Example

```bash
kubectl get all -n kubernetes-dashboard
```

---

## To display all resources in all namespaces

```bash
kubectl get all -A
```

---

## To display the current Kubernetes context

```bash
kubectl config current-context
```

---

## To list all available contexts

```bash
kubectl config get-contexts
```

---

## To switch to another Kubernetes context

```bash
kubectl config use-context <context-name>
```

---

## To rename a Kubernetes context

```bash
kubectl config rename-context <old-context> <new-context>
```

---

## To delete a Kubernetes context

```bash
kubectl config delete-context <context-name>
```

---

## To display the current kubeconfig file

```bash
kubectl config view
```

---

## To display the flattened kubeconfig

```bash
kubectl config view --flatten
```

---

## To display the raw kubeconfig

```bash
kubectl config view --raw
```

---

## To set the default namespace for the current context

```bash
kubectl config set-context --current --namespace=<namespace>
```

Example

```bash
kubectl config set-context --current --namespace=development
```

---

## To remove the default namespace from the current context

```bash
kubectl config set-context --current --namespace=default
```

---

## To view the current user

```bash
kubectl config view --minify
```

---

## To display detailed cluster information

```bash
kubectl cluster-info dump
```

---

## To check if the API Server is reachable

```bash
kubectl get componentstatuses
```

> **Note:** `componentstatuses` is deprecated in newer Kubernetes versions but may still appear in older clusters.

---

## To display the current Kubernetes configuration file path

### Linux / macOS

```bash
echo $KUBECONFIG
```

### Windows PowerShell

```powershell
echo $env:KUBECONFIG
```

---

## To verify that kubectl is configured correctly

```bash
kubectl get nodes
```

If the nodes are listed successfully, your `kubectl` configuration is working correctly.