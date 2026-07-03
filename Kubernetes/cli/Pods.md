# Pods

## To list all Pods

```bash
kubectl get pods
```

---

## To list Pods in all namespaces

```bash
kubectl get pods -A
```

---

## To continuously watch Pods

```bash
kubectl get pods -w
```

---

## To show detailed Pod information

```bash
kubectl describe pod <pod-name>
```

---

## To delete a Pod

```bash
kubectl delete pod <pod-name>
```

---

## To view Pod logs

```bash
kubectl logs <pod-name>
```

---

## To follow Pod logs in real time

```bash
kubectl logs -f <pod-name>
```

---

## To view logs from a previous crashed container

```bash
kubectl logs --previous <pod-name>
```

---

## To execute a command inside a Pod

```bash
kubectl exec -it <pod-name> -- bash
```

---

## To port-forward a Pod

```bash
kubectl port-forward pod/<pod-name> 8080:80
```

---

## To export Pod YAML

```bash
kubectl get pod <pod-name> -o yaml
```