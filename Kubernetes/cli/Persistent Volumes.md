# Persistent Volumes

# Persistent Volumes (PV)

## To list all Persistent Volumes

```bash
kubectl get pv
```

---

## To display detailed information about a Persistent Volume

```bash
kubectl describe pv <pv-name>
```

---

## To display a Persistent Volume in YAML format

```bash
kubectl get pv <pv-name> -o yaml
```

---

## To display a Persistent Volume in JSON format

```bash
kubectl get pv <pv-name> -o json
```

---

## To create a Persistent Volume

```bash
kubectl apply -f persistent-volume.yaml
```

---

## To update a Persistent Volume

```bash
kubectl apply -f persistent-volume.yaml
```

---

## To edit a Persistent Volume

```bash
kubectl edit pv <pv-name>
```

---

## To delete a Persistent Volume

```bash
kubectl delete pv <pv-name>
```

---

## To display Persistent Volumes with additional information

```bash
kubectl get pv -o wide
```

---

## To display only Persistent Volume names

```bash
kubectl get pv -o name
```

---

## To list Persistent Volumes sorted by creation time

```bash
kubectl get pv --sort-by=.metadata.creationTimestamp
```

---

## To display the status of Persistent Volumes

```bash
kubectl get pv
```

Common statuses

- Available
- Bound
- Released
- Failed

---

## To display the reclaim policy of a Persistent Volume

```bash
kubectl describe pv <pv-name>
```

Look for

```text
Reclaim Policy
```

---

## To display the storage capacity of a Persistent Volume

```bash
kubectl get pv
```

Check the **CAPACITY** column.

---

## To display the access mode of a Persistent Volume

```bash
kubectl get pv
```

Check the **ACCESS MODES** column.

---

# Persistent Volume Claims (PVC)

## To list all Persistent Volume Claims

```bash
kubectl get pvc
```

---

## To list Persistent Volume Claims in all namespaces

```bash
kubectl get pvc -A
```

---

## To list Persistent Volume Claims in a specific namespace

```bash
kubectl get pvc -n <namespace-name>
```

---

## To display detailed information about a Persistent Volume Claim

```bash
kubectl describe pvc <pvc-name>
```

---

## To display a Persistent Volume Claim in YAML format

```bash
kubectl get pvc <pvc-name> -o yaml
```

---

## To display a Persistent Volume Claim in JSON format

```bash
kubectl get pvc <pvc-name> -o json
```

---

## To create a Persistent Volume Claim

```bash
kubectl apply -f persistent-volume-claim.yaml
```

---

## To update a Persistent Volume Claim

```bash
kubectl apply -f persistent-volume-claim.yaml
```

---

## To edit a Persistent Volume Claim

```bash
kubectl edit pvc <pvc-name>
```

---

## To delete a Persistent Volume Claim

```bash
kubectl delete pvc <pvc-name>
```

---

## To delete all Persistent Volume Claims in a namespace

```bash
kubectl delete pvc --all -n <namespace-name>
```

---

## To display Persistent Volume Claims with additional information

```bash
kubectl get pvc -o wide
```

---

## To display only Persistent Volume Claim names

```bash
kubectl get pvc -o name
```

---

## To list Persistent Volume Claims sorted by creation time

```bash
kubectl get pvc --sort-by=.metadata.creationTimestamp
```

---

## To display the status of Persistent Volume Claims

```bash
kubectl get pvc
```

Common statuses

- Pending
- Bound
- Lost

---

## To verify which Persistent Volume is bound to a Persistent Volume Claim

```bash
kubectl get pvc
```

Check the **VOLUME** column.

---

## To verify which Pod is using a Persistent Volume Claim

```bash
kubectl describe pod <pod-name>
```

Look under the **Volumes** section.

---

## To verify the StorageClass used by a Persistent Volume Claim

```bash
kubectl get pvc
```

Check the **STORAGECLASS** column.

---

## To verify the requested storage size

```bash
kubectl describe pvc <pvc-name>
```

---

## To check whether a PVC is waiting for a PV

```bash
kubectl get pvc
```

If the status is

```text
Pending
```

the claim has not yet been bound.

---

## To check events related to a Persistent Volume Claim

```bash
kubectl describe pvc <pvc-name>
```

Scroll to the **Events** section.

---

## To verify the Persistent Volume bound to a claim

```bash
kubectl describe pvc <pvc-name>
```

Look for

```text
Volume:
```

---

## To display all Persistent Volumes and Persistent Volume Claims

```bash
kubectl get pv,pvc
```

---

## To apply all Persistent Volume manifests

```bash
kubectl apply -f .
```

---

## To delete all Persistent Volume manifests

```bash
kubectl delete -f .
```

---

## To troubleshoot a PVC stuck in Pending

1. Check the PVC

```bash
kubectl get pvc
```

2. Describe the PVC

```bash
kubectl describe pvc <pvc-name>
```

3. Check available PVs

```bash
kubectl get pv
```

4. Verify the StorageClass

```bash
kubectl get storageclass
```

---

## To verify the Pod has successfully mounted the volume

```bash
kubectl describe pod <pod-name>
```

Look under

- Volumes
- Mounts

---

## To verify available storage classes

```bash
kubectl get storageclass
```

or

```bash
kubectl get sc
```