# ReplicaSets

## To list all ReplicaSets

```bash
kubectl get replicasets
```

---

## To list ReplicaSets using the short name

```bash
kubectl get rs
```

---

## To list ReplicaSets in all namespaces

```bash
kubectl get rs -A
```

---

## To list ReplicaSets in a specific namespace

```bash
kubectl get rs -n <namespace>
```

---

## To display detailed information about a ReplicaSet

```bash
kubectl describe rs <replicaset-name>
```

---

## To display a ReplicaSet in YAML format

```bash
kubectl get rs <replicaset-name> -o yaml
```

---

## To display a ReplicaSet in JSON format

```bash
kubectl get rs <replicaset-name> -o json
```

---

## To create a ReplicaSet from a YAML file

```bash
kubectl apply -f replicaset.yaml
```

---

## To update an existing ReplicaSet

```bash
kubectl apply -f replicaset.yaml
```

---

## To edit a ReplicaSet

```bash
kubectl edit rs <replicaset-name>
```

---

## To scale a ReplicaSet

```bash
kubectl scale rs <replicaset-name> --replicas=5
```

---

## To delete a ReplicaSet

```bash
kubectl delete rs <replicaset-name>
```

---

## To delete a ReplicaSet using a YAML file

```bash
kubectl delete -f replicaset.yaml
```

---

## To delete all ReplicaSets

```bash
kubectl delete rs --all
```

---

## To delete all ReplicaSets in a namespace

```bash
kubectl delete rs --all -n <namespace>
```

---

## To display ReplicaSets with additional information

```bash
kubectl get rs -o wide
```

---

## To display ReplicaSet labels

```bash
kubectl get rs --show-labels
```

---

## To continuously watch ReplicaSet changes

```bash
kubectl get rs -w
```

---

## To list ReplicaSets sorted by creation time

```bash
kubectl get rs --sort-by=.metadata.creationTimestamp
```

---

## To display only ReplicaSet names

```bash
kubectl get rs -o name
```

---

## To list ReplicaSets matching a label

```bash
kubectl get rs -l app=nginx
```

---

## To delete ReplicaSets matching a label

```bash
kubectl delete rs -l app=nginx
```

---

## To display the Pods managed by a ReplicaSet

```bash
kubectl get pods -l app=nginx
```

> Replace `app=nginx` with the label selector used by your ReplicaSet.

---

## To verify the desired and current replica count

```bash
kubectl get rs
```

---

## To display events related to a ReplicaSet

```bash
kubectl describe rs <replicaset-name>
```

Scroll to the **Events** section at the bottom.

---

## To check the owner of a ReplicaSet

```bash
kubectl describe rs <replicaset-name>
```

Look for the **Controlled By** field.

---

## To check which image a ReplicaSet is using

```bash
kubectl describe rs <replicaset-name>
```

or

```bash
kubectl get rs <replicaset-name> -o yaml
```

---

## To apply all ReplicaSet manifests in the current directory

```bash
kubectl apply -f .
```

---

## To delete all ReplicaSet manifests in the current directory

```bash
kubectl delete -f .
```

---

## To verify that a ReplicaSet recreated a deleted Pod (Self-Healing)

```bash
kubectl get pods -w
```

Delete one Pod in another terminal:

```bash
kubectl delete pod <pod-name>
```

The ReplicaSet automatically creates a new Pod to maintain the desired replica count.

---

## To see which Deployment owns a ReplicaSet

```bash
kubectl describe rs <replicaset-name>
```

Look for:

```text
Controlled By: Deployment/<deployment-name>
```

---

## To list old ReplicaSets created during Deployment updates

```bash
kubectl get rs
```

Old ReplicaSets are retained to support Deployment rollbacks.

---

## To compare desired, current and ready replicas

```bash
kubectl get rs
```

The output includes:

- DESIRED
- CURRENT
- READY

These values help determine whether the ReplicaSet has successfully created and maintained the required number of Pods.