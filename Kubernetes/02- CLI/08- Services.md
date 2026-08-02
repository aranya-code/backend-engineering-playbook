# Services

## To list all Services

```bash
kubectl get services
```

---

## To list Services using the short name

```bash
kubectl get svc
```

---

## To list Services in all namespaces

```bash
kubectl get svc -A
```

---

## To list Services in a specific namespace

```bash
kubectl get svc -n <namespace>
```

---

## To display detailed information about a Service

```bash
kubectl describe svc <service-name>
```

---

## To display a Service in YAML format

```bash
kubectl get svc <service-name> -o yaml
```

---

## To display a Service in JSON format

```bash
kubectl get svc <service-name> -o json
```

---

## To create a Service from a YAML file

```bash
kubectl apply -f service.yaml
```

---

## To update an existing Service

```bash
kubectl apply -f service.yaml
```

---

## To edit a Service

```bash
kubectl edit svc <service-name>
```

---

## To expose a Deployment as a ClusterIP Service

```bash
kubectl expose deployment <deployment-name> \
--type=ClusterIP \
--port=80
```

---

## To expose a Deployment as a NodePort Service

```bash
kubectl expose deployment <deployment-name> \
--type=NodePort \
--port=80
```

---

## To expose a Deployment as a LoadBalancer Service

```bash
kubectl expose deployment <deployment-name> \
--type=LoadBalancer \
--port=80
```

---

## To expose a Pod as a Service

```bash
kubectl expose pod <pod-name> \
--type=ClusterIP \
--port=80
```

---

## To expose a ReplicaSet as a Service

```bash
kubectl expose rs <replicaset-name> \
--type=ClusterIP \
--port=80
```

---

## To delete a Service

```bash
kubectl delete svc <service-name>
```

---

## To delete a Service using a YAML file

```bash
kubectl delete -f service.yaml
```

---

## To delete all Services

```bash
kubectl delete svc --all
```

---

## To delete all Services in a namespace

```bash
kubectl delete svc --all -n <namespace>
```

---

## To display Services with additional information

```bash
kubectl get svc -o wide
```

---

## To continuously watch Service changes

```bash
kubectl get svc -w
```

---

## To list Services sorted by creation time

```bash
kubectl get svc --sort-by=.metadata.creationTimestamp
```

---

## To display only Service names

```bash
kubectl get svc -o name
```

---

## To list Services matching a label

```bash
kubectl get svc -l app=nginx
```

---

## To delete Services matching a label

```bash
kubectl delete svc -l app=nginx
```

---

## To view the Endpoints of a Service

```bash
kubectl get endpoints
```

---

## To view the Endpoints of a specific Service

```bash
kubectl describe endpoints <service-name>
```

---

## To display EndpointSlices

```bash
kubectl get endpointslices
```

---

## To describe an EndpointSlice

```bash
kubectl describe endpointslice <endpointslice-name>
```

---

## To verify which Pods are selected by a Service

```bash
kubectl describe svc <service-name>
```

Look under the **Endpoints** section.

---

## To port-forward a Service

```bash
kubectl port-forward svc/<service-name> 8080:80
```

---

## To access a NodePort Service using Minikube

```bash
minikube service <service-name>
```

---

## To view the external IP of a LoadBalancer Service

```bash
kubectl get svc
```

Check the **EXTERNAL-IP** column.

---

## To verify the Service selector

```bash
kubectl get svc <service-name> -o yaml
```

Look under:

```yaml
spec:
  selector:
```

---

## To verify Service ports

```bash
kubectl describe svc <service-name>
```

---

## To list Services without selectors

```bash
kubectl get svc
```

Then inspect individual Services using:

```bash
kubectl describe svc <service-name>
```

---

## To display the DNS name of a Service

Internal DNS format

```text
<service-name>.<namespace>.svc.cluster.local
```

Example

```text
backend.default.svc.cluster.local
```

---

## To test Service DNS resolution from inside a Pod

```bash
kubectl exec -it <pod-name> -- nslookup <service-name>
```

---

## To test connectivity to a Service from inside a Pod

```bash
kubectl exec -it <pod-name> -- curl http://<service-name>
```

---

## To verify the Service type

```bash
kubectl get svc
```

Check the **TYPE** column.

Possible values

- ClusterIP
- NodePort
- LoadBalancer
- ExternalName

---

## To check whether a Service has available Endpoints

```bash
kubectl get endpoints <service-name>
```

If no endpoints are listed, verify that the Service selector matches the Pod labels.

---

## To apply all Service manifests in the current directory

```bash
kubectl apply -f .
```

---

## To delete all Service manifests in the current directory

```bash
kubectl delete -f .
```

---

## To troubleshoot a Service that is not routing traffic

1. Check the Service

```bash
kubectl get svc
```

2. Verify the selector

```bash
kubectl describe svc <service-name>
```

3. Verify the Pods

```bash
kubectl get pods --show-labels
```

4. Verify the Endpoints

```bash
kubectl get endpoints <service-name>
```

5. Verify the application inside the Pod

```bash
kubectl logs <pod-name>
```