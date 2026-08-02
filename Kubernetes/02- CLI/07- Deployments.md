# Deployments

## To list Deployments

```bash
kubectl get deployments
```

---

## To create a Deployment

```bash
kubectl create deployment nginx --image=nginx
```

---

## To describe a Deployment

```bash
kubectl describe deployment <deployment-name>
```

---

## To scale a Deployment

```bash
kubectl scale deployment <deployment-name> --replicas=5
```

---

## To restart a Deployment

```bash
kubectl rollout restart deployment <deployment-name>
```

---

## To check rollout status

```bash
kubectl rollout status deployment <deployment-name>
```

---

## To view rollout history

```bash
kubectl rollout history deployment <deployment-name>
```

---

## To rollback a Deployment

```bash
kubectl rollout undo deployment <deployment-name>
```

---

## To delete a Deployment

```bash
kubectl delete deployment <deployment-name>
```