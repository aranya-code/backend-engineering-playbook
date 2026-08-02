# Debugging

## To display all cluster events

```bash
kubectl get events
```

---

## To display events sorted by creation time

```bash
kubectl get events --sort-by=.metadata.creationTimestamp
```

---

## To display events in a specific namespace

```bash
kubectl get events -n <namespace-name>
```

---

## To display detailed information about a Pod

```bash
kubectl describe pod <pod-name>
```

---

## To display detailed information about a Deployment

```bash
kubectl describe deployment <deployment-name>
```

---

## To display detailed information about a Service

```bash
kubectl describe svc <service-name>
```

---

## To display detailed information about a Node

```bash
kubectl describe node <node-name>
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

## To display logs from the previous crashed container

```bash
kubectl logs --previous <pod-name>
```

---

## To display logs from a specific container

```bash
kubectl logs <pod-name> -c <container-name>
```

---

## To execute a command inside a Pod

```bash
kubectl exec -it <pod-name> -- bash
```

---

## To execute a shell inside a Pod

```bash
kubectl exec -it <pod-name> -- sh
```

---

## To run a single command inside a Pod

```bash
kubectl exec <pod-name> -- ls
```

---

## To debug a running Pod with an Ephemeral Container

```bash
kubectl debug <pod-name> -it --image=busybox
```

---

## To port-forward a Pod

```bash
kubectl port-forward pod/<pod-name> 8080:80
```

---

## To port-forward a Service

```bash
kubectl port-forward svc/<service-name> 8080:80
```

---

## To display resource usage of Nodes (Metrics Server required)

```bash
kubectl top nodes
```

---

## To display resource usage of Pods (Metrics Server required)

```bash
kubectl top pods
```

---

## To display resource usage of Pods in a namespace

```bash
kubectl top pods -n <namespace-name>
```

---

## To verify the rollout status of a Deployment

```bash
kubectl rollout status deployment <deployment-name>
```

---

## To view Deployment rollout history

```bash
kubectl rollout history deployment <deployment-name>
```

---

## To rollback a Deployment

```bash
kubectl rollout undo deployment <deployment-name>
```

---

## To restart a Deployment

```bash
kubectl rollout restart deployment <deployment-name>
```

---

## To display all Pods

```bash
kubectl get pods
```

---

## To continuously watch Pod status

```bash
kubectl get pods -w
```

---

## To display Pods with additional information

```bash
kubectl get pods -o wide
```

---

## To display all resources

```bash
kubectl get all
```

---

## To display all resources in all namespaces

```bash
kubectl get all -A
```

---

## To verify Node status

```bash
kubectl get nodes
```

---

## To display Persistent Volume Claims

```bash
kubectl get pvc
```

---

## To display Persistent Volumes

```bash
kubectl get pv
```

---

## To display StorageClasses

```bash
kubectl get sc
```

---

## To verify Service Endpoints

```bash
kubectl get endpoints
```

---

## To display EndpointSlices

```bash
kubectl get endpointslices
```

---

## To verify Pod labels

```bash
kubectl get pods --show-labels
```

---

## To verify Service selectors

```bash
kubectl describe svc <service-name>
```

---

## To verify Namespace resources

```bash
kubectl get all -n <namespace-name>
```

---

## To display all Namespaces

```bash
kubectl get ns
```

---

## To display the current Kubernetes context

```bash
kubectl config current-context
```

---

## To display all Kubernetes contexts

```bash
kubectl config get-contexts
```

---

## To test DNS resolution inside a Pod

```bash
kubectl exec -it <pod-name> -- nslookup <service-name>
```

---

## To test connectivity to a Service

```bash
kubectl exec -it <pod-name> -- curl http://<service-name>
```

---

## To verify Ingress resources

```bash
kubectl get ingress
```

---

## To display Ingress details

```bash
kubectl describe ingress <ingress-name>
```

---

## To verify the Ingress Controller

```bash
kubectl get pods -n ingress-nginx
```

---

## To display Ingress Controller logs

```bash
kubectl logs -n ingress-nginx <controller-pod>
```

---

## To verify ConfigMaps

```bash
kubectl get configmaps
```

---

## To verify Secrets

```bash
kubectl get secrets
```

---

## To verify ReplicaSets

```bash
kubectl get rs
```

---

## To verify Deployments

```bash
kubectl get deployments
```

---

## To verify Services

```bash
kubectl get svc
```

---

## To troubleshoot a Pod stuck in Pending

1. Check Pod status

```bash
kubectl get pods
```

2. Describe the Pod

```bash
kubectl describe pod <pod-name>
```

3. Check cluster events

```bash
kubectl get events
```

4. Verify available Nodes

```bash
kubectl get nodes
```

---

## To troubleshoot CrashLoopBackOff

1. Check Pod status

```bash
kubectl get pods
```

2. View Pod logs

```bash
kubectl logs <pod-name>
```

3. View previous logs

```bash
kubectl logs --previous <pod-name>
```

4. Describe the Pod

```bash
kubectl describe pod <pod-name>
```

---

## To troubleshoot ImagePullBackOff

1. Describe the Pod

```bash
kubectl describe pod <pod-name>
```

2. Verify the image name

```bash
kubectl get pod <pod-name> -o yaml
```

3. Verify image pull secrets

```bash
kubectl get secrets
```

---

## To troubleshoot a Service with no Endpoints

1. Verify the Service

```bash
kubectl describe svc <service-name>
```

2. Verify Pod labels

```bash
kubectl get pods --show-labels
```

3. Verify Endpoints

```bash
kubectl get endpoints <service-name>
```

---

## To troubleshoot PVC issues

1. Verify the PVC

```bash
kubectl get pvc
```

2. Describe the PVC

```bash
kubectl describe pvc <pvc-name>
```

3. Verify Persistent Volumes

```bash
kubectl get pv
```

4. Verify StorageClasses

```bash
kubectl get sc
```

---

## To collect all cluster information

```bash
kubectl cluster-info dump
```