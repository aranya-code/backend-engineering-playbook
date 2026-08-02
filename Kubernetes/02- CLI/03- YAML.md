# YAML

## To create a resource from a YAML file

```bash
kubectl apply -f <filename>.yaml
```

---

## To create all resources from a directory

```bash
kubectl apply -f .
```

---

## To delete a resource using a YAML file

```bash
kubectl delete -f <filename>.yaml
```

---

## To delete all resources from a directory

```bash
kubectl delete -f .
```

---

## To replace an existing resource

```bash
kubectl replace -f <filename>.yaml
```

---

## To force replace a resource

```bash
kubectl replace --force -f <filename>.yaml
```

---

## To validate a YAML file before applying

```bash
kubectl apply --dry-run=client -f <filename>.yaml
```

---

## To validate multiple YAML files

```bash
kubectl apply --dry-run=client -f .
```

---

## To create a Pod YAML without creating the Pod

```bash
kubectl run nginx \
--image=nginx \
--dry-run=client \
-o yaml
```

---

## To create a Deployment YAML without creating the Deployment

```bash
kubectl create deployment nginx \
--image=nginx \
--dry-run=client \
-o yaml
```

---

## To create a Service YAML without creating the Service

```bash
kubectl create service clusterip nginx \
--tcp=80:80 \
--dry-run=client \
-o yaml
```

---

## To export a Pod as YAML

```bash
kubectl get pod <pod-name> -o yaml
```

---

## To export a Deployment as YAML

```bash
kubectl get deployment <deployment-name> -o yaml
```

---

## To export a Service as YAML

```bash
kubectl get svc <service-name> -o yaml
```

---

## To export a ReplicaSet as YAML

```bash
kubectl get rs <replicaset-name> -o yaml
```

---

## To export a ConfigMap as YAML

```bash
kubectl get configmap <configmap-name> -o yaml
```

---

## To export a Secret as YAML

```bash
kubectl get secret <secret-name> -o yaml
```

---

## To export a Namespace as YAML

```bash
kubectl get namespace <namespace-name> -o yaml
```

---

## To export a Persistent Volume as YAML

```bash
kubectl get pv <pv-name> -o yaml
```

---

## To export a Persistent Volume Claim as YAML

```bash
kubectl get pvc <pvc-name> -o yaml
```

---

## To export a StorageClass as YAML

```bash
kubectl get sc <storageclass-name> -o yaml
```

---

## To export an Ingress as YAML

```bash
kubectl get ingress <ingress-name> -o yaml
```

---

## To export all Pods as YAML

```bash
kubectl get pods -o yaml
```

---

## To export all Deployments as YAML

```bash
kubectl get deployments -o yaml
```

---

## To export all Services as YAML

```bash
kubectl get svc -o yaml
```

---

## To export all ConfigMaps as YAML

```bash
kubectl get configmaps -o yaml
```

---

## To export all Secrets as YAML

```bash
kubectl get secrets -o yaml
```

---

## To edit a resource directly

```bash
kubectl edit <resource-type> <resource-name>
```

Example

```bash
kubectl edit deployment nginx
```

---

## To compare a YAML file with the running resource

```bash
kubectl diff -f <filename>.yaml
```

---

## To display only the generated YAML

```bash
kubectl create deployment nginx \
--image=nginx \
--dry-run=client \
-o yaml
```

---

## To save generated YAML to a file

```bash
kubectl create deployment nginx \
--image=nginx \
--dry-run=client \
-o yaml > deployment.yaml
```

---

## To generate a Pod YAML file

```bash
kubectl run nginx \
--image=nginx \
--dry-run=client \
-o yaml > pod.yaml
```

---

## To generate a Service YAML file

```bash
kubectl create service clusterip nginx \
--tcp=80:80 \
--dry-run=client \
-o yaml > service.yaml
```

---

## To apply changes recursively

```bash
kubectl apply -R -f manifests/
```

---

## To delete resources recursively

```bash
kubectl delete -R -f manifests/
```

---

## To apply resources in a specific namespace

```bash
kubectl apply -f deployment.yaml -n <namespace-name>
```

---

## To delete resources in a specific namespace

```bash
kubectl delete -f deployment.yaml -n <namespace-name>
```

---

## To display the last applied configuration

```bash
kubectl apply view-last-applied deployment/<deployment-name>
```

---

## To annotate a resource with the last applied configuration

```bash
kubectl apply set-last-applied -f deployment.yaml
```

---

## To update the last applied configuration

```bash
kubectl apply set-last-applied -f deployment.yaml --create-annotation=true
```

---

## To prune resources that are no longer defined

```bash
kubectl apply -f manifests/ --prune
```

> **Note:** Use `--prune` carefully, as it deletes resources that are no longer present in the manifest set.

---

## To view YAML with managed fields removed

```bash
kubectl get deployment <deployment-name> -o yaml --show-managed-fields=false
```

---

## To convert YAML output to JSON

```bash
kubectl get deployment <deployment-name> -o json
```

---

## To troubleshoot YAML validation errors

1. Validate the manifest

```bash
kubectl apply --dry-run=client -f deployment.yaml
```

2. Compare with the cluster

```bash
kubectl diff -f deployment.yaml
```

3. Verify API compatibility

```bash
kubectl api-resources
```

4. Check cluster events

```bash
kubectl get events
```

5. Apply the manifest

```bash
kubectl apply -f deployment.yaml
```