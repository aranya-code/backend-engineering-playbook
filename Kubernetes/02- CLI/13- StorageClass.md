# StorageClass

## To list all StorageClasses

```bash
kubectl get storageclass
```

---

## To list StorageClasses using the short name

```bash
kubectl get sc
```

---

## To display detailed information about a StorageClass

```bash
kubectl describe storageclass <storageclass-name>
```

---

## To display a StorageClass in YAML format

```bash
kubectl get storageclass <storageclass-name> -o yaml
```

---

## To display a StorageClass in JSON format

```bash
kubectl get storageclass <storageclass-name> -o json
```

---

## To create a StorageClass

```bash
kubectl apply -f storageclass.yaml
```

---

## To update a StorageClass

```bash
kubectl apply -f storageclass.yaml
```

---

## To edit a StorageClass

```bash
kubectl edit storageclass <storageclass-name>
```

---

## To delete a StorageClass

```bash
kubectl delete storageclass <storageclass-name>
```

---

## To delete a StorageClass using the short name

```bash
kubectl delete sc <storageclass-name>
```

---

## To display StorageClasses with additional information

```bash
kubectl get sc -o wide
```

---

## To display only StorageClass names

```bash
kubectl get sc -o name
```

---

## To list StorageClasses sorted by creation time

```bash
kubectl get sc --sort-by=.metadata.creationTimestamp
```

---

## To identify the default StorageClass

```bash
kubectl get storageclass
```

Check the **(default)** annotation in the output.

---

## To display the provisioner used by a StorageClass

```bash
kubectl get storageclass
```

Check the **PROVISIONER** column.

---

## To display the reclaim policy of a StorageClass

```bash
kubectl describe storageclass <storageclass-name>
```

Look for

```text
ReclaimPolicy
```

---

## To display the volume binding mode

```bash
kubectl describe storageclass <storageclass-name>
```

Look for

```text
VolumeBindingMode
```

---

## To display the allowVolumeExpansion setting

```bash
kubectl describe storageclass <storageclass-name>
```

Look for

```text
AllowVolumeExpansion
```

---

## To verify which StorageClass a PVC is using

```bash
kubectl get pvc
```

Check the **STORAGECLASS** column.

---

## To describe a PVC and verify its StorageClass

```bash
kubectl describe pvc <pvc-name>
```

Look for

```text
StorageClass
```

---

## To list all Persistent Volume Claims with their StorageClass

```bash
kubectl get pvc
```

---

## To list all Persistent Volumes

```bash
kubectl get pv
```

---

## To verify dynamically provisioned Persistent Volumes

```bash
kubectl get pv
```

Check whether a new PV has been created automatically after creating a PVC.

---

## To create a PVC that uses a specific StorageClass

Specify the StorageClass in the PVC manifest.

```yaml
spec:
  storageClassName: standard
```

Apply the manifest

```bash
kubectl apply -f pvc.yaml
```

---

## To create a StorageClass from a YAML file

```bash
kubectl apply -f storageclass.yaml
```

---

## To export all StorageClasses

```bash
kubectl get storageclass -o yaml
```

---

## To display events related to a PVC waiting for a StorageClass

```bash
kubectl describe pvc <pvc-name>
```

Scroll to the **Events** section.

---

## To verify available provisioners in the cluster

```bash
kubectl get storageclass
```

Examples

- ebs.csi.aws.com
- disk.csi.azure.com
- pd.csi.storage.gke.io
- rancher.io/local-path

---

## To verify whether dynamic provisioning is working

1. Create a PVC

```bash
kubectl apply -f pvc.yaml
```

2. Check the PVC

```bash
kubectl get pvc
```

3. Check the PV

```bash
kubectl get pv
```

A new Persistent Volume should be created automatically.

---

## To troubleshoot a PVC stuck in Pending

Check the available StorageClasses

```bash
kubectl get storageclass
```

---

Describe the PVC

```bash
kubectl describe pvc <pvc-name>
```

---

Verify that the requested StorageClass exists

```bash
kubectl get storageclass <storageclass-name>
```

---

Verify the default StorageClass

```bash
kubectl get storageclass
```

---

Check cluster events

```bash
kubectl get events
```

---

## To apply all StorageClass manifests in the current directory

```bash
kubectl apply -f .
```

---

## To delete all StorageClass manifests in the current directory

```bash
kubectl delete -f .
```