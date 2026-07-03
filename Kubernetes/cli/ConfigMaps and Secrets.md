# ConfigMaps and Secrets

# ConfigMaps

## To list all ConfigMaps

```bash
kubectl get configmaps
```

---

## To list ConfigMaps using the short name

```bash
kubectl get cm
```

---

## To list ConfigMaps in all namespaces

```bash
kubectl get cm -A
```

---

## To list ConfigMaps in a specific namespace

```bash
kubectl get cm -n <namespace-name>
```

---

## To display detailed information about a ConfigMap

```bash
kubectl describe configmap <configmap-name>
```

---

## To display a ConfigMap in YAML format

```bash
kubectl get configmap <configmap-name> -o yaml
```

---

## To display a ConfigMap in JSON format

```bash
kubectl get configmap <configmap-name> -o json
```

---

## To create a ConfigMap from literals

```bash
kubectl create configmap <configmap-name> \
--from-literal=APP_ENV=production
```

---

## To create a ConfigMap from a file

```bash
kubectl create configmap <configmap-name> \
--from-file=config.properties
```

---

## To create a ConfigMap from an environment file

```bash
kubectl create configmap <configmap-name> \
--from-env-file=.env
```

---

## To create a ConfigMap from a YAML file

```bash
kubectl apply -f configmap.yaml
```

---

## To update a ConfigMap

```bash
kubectl apply -f configmap.yaml
```

---

## To edit a ConfigMap

```bash
kubectl edit configmap <configmap-name>
```

---

## To delete a ConfigMap

```bash
kubectl delete configmap <configmap-name>
```

---

## To delete all ConfigMaps

```bash
kubectl delete configmaps --all
```

---

## To delete all ConfigMaps in a namespace

```bash
kubectl delete configmaps --all -n <namespace-name>
```

---

## To display ConfigMaps with labels

```bash
kubectl get cm --show-labels
```

---

## To list ConfigMaps sorted by creation time

```bash
kubectl get cm --sort-by=.metadata.creationTimestamp
```

---

## To display only ConfigMap names

```bash
kubectl get cm -o name
```

---

# Secrets

## To list all Secrets

```bash
kubectl get secrets
```

---

## To list Secrets in all namespaces

```bash
kubectl get secrets -A
```

---

## To list Secrets in a specific namespace

```bash
kubectl get secrets -n <namespace-name>
```

---

## To display detailed information about a Secret

```bash
kubectl describe secret <secret-name>
```

---

## To display a Secret in YAML format

```bash
kubectl get secret <secret-name> -o yaml
```

---

## To display a Secret in JSON format

```bash
kubectl get secret <secret-name> -o json
```

---

## To create a generic Secret from literals

```bash
kubectl create secret generic <secret-name> \
--from-literal=username=admin \
--from-literal=password=admin123
```

---

## To create a Secret from a file

```bash
kubectl create secret generic <secret-name> \
--from-file=credentials.txt
```

---

## To create a Docker Registry Secret

```bash
kubectl create secret docker-registry <secret-name> \
--docker-server=<registry-url> \
--docker-username=<username> \
--docker-password=<password> \
--docker-email=<email>
```

---

## To create a TLS Secret

```bash
kubectl create secret tls <secret-name> \
--cert=tls.crt \
--key=tls.key
```

---

## To create a Secret from a YAML file

```bash
kubectl apply -f secret.yaml
```

---

## To update a Secret

```bash
kubectl apply -f secret.yaml
```

---

## To edit a Secret

```bash
kubectl edit secret <secret-name>
```

---

## To delete a Secret

```bash
kubectl delete secret <secret-name>
```

---

## To delete all Secrets

```bash
kubectl delete secrets --all
```

---

## To delete all Secrets in a namespace

```bash
kubectl delete secrets --all -n <namespace-name>
```

---

## To display only Secret names

```bash
kubectl get secrets -o name
```

---

## To list Secrets sorted by creation time

```bash
kubectl get secrets --sort-by=.metadata.creationTimestamp
```

---

## To decode a Secret value (Linux/macOS)

```bash
kubectl get secret <secret-name> \
-o jsonpath="{.data.password}" | base64 --decode
```

---

## To decode a Secret value (Windows PowerShell)

```powershell
[System.Text.Encoding]::UTF8.GetString(
[System.Convert]::FromBase64String(
(kubectl get secret <secret-name> -o jsonpath="{.data.password}")
))
```

---

## To view all keys stored inside a Secret

```bash
kubectl get secret <secret-name> -o yaml
```

---

## To list Secret types

```bash
kubectl get secrets
```

Check the **TYPE** column.

Common types include:

- Opaque
- kubernetes.io/tls
- kubernetes.io/dockerconfigjson
- kubernetes.io/service-account-token

---

# Common Commands

## To list both ConfigMaps and Secrets

```bash
kubectl get cm,secrets
```

---

## To apply all ConfigMap and Secret manifests

```bash
kubectl apply -f .
```

---

## To delete all ConfigMap and Secret manifests

```bash
kubectl delete -f .
```

---

## To verify ConfigMaps used by a Pod

```bash
kubectl describe pod <pod-name>
```

Look under:

- Environment
- Volumes
- Mounts

---

## To verify Secrets used by a Pod

```bash
kubectl describe pod <pod-name>
```

Look under:

- Environment Variables
- Secret Volumes

---

## To troubleshoot missing ConfigMaps

```bash
kubectl get cm
```

---

## To troubleshoot missing Secrets

```bash
kubectl get secrets
```

---

## To check events if a Pod cannot load a ConfigMap or Secret

```bash
kubectl describe pod <pod-name>
```

Scroll to the **Events** section.

---

## To verify that a ConfigMap or Secret exists before deployment

```bash
kubectl get cm
kubectl get secrets
```