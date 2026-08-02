# Ingress

## To list all Ingress resources

```bash
kubectl get ingress
```

---

## To list Ingress resources using the short name

```bash
kubectl get ing
```

---

## To list Ingress resources in all namespaces

```bash
kubectl get ingress -A
```

---

## To list Ingress resources in a specific namespace

```bash
kubectl get ingress -n <namespace-name>
```

---

## To display detailed information about an Ingress

```bash
kubectl describe ingress <ingress-name>
```

---

## To display an Ingress in YAML format

```bash
kubectl get ingress <ingress-name> -o yaml
```

---

## To display an Ingress in JSON format

```bash
kubectl get ingress <ingress-name> -o json
```

---

## To create an Ingress from a YAML file

```bash
kubectl apply -f ingress.yaml
```

---

## To update an existing Ingress

```bash
kubectl apply -f ingress.yaml
```

---

## To edit an Ingress

```bash
kubectl edit ingress <ingress-name>
```

---

## To delete an Ingress

```bash
kubectl delete ingress <ingress-name>
```

---

## To delete an Ingress using the short name

```bash
kubectl delete ing <ingress-name>
```

---

## To delete an Ingress using a YAML file

```bash
kubectl delete -f ingress.yaml
```

---

## To display Ingress resources with additional information

```bash
kubectl get ingress -o wide
```

---

## To continuously watch Ingress resources

```bash
kubectl get ingress -w
```

---

## To display only Ingress names

```bash
kubectl get ingress -o name
```

---

## To list Ingress resources sorted by creation time

```bash
kubectl get ingress --sort-by=.metadata.creationTimestamp
```

---

## To list Ingress resources matching a label

```bash
kubectl get ingress -l app=frontend
```

---

## To delete Ingress resources matching a label

```bash
kubectl delete ingress -l app=frontend
```

---

## To verify the host rules configured in an Ingress

```bash
kubectl describe ingress <ingress-name>
```

Look under

```text
Rules
```

---

## To verify the backend Services used by an Ingress

```bash
kubectl describe ingress <ingress-name>
```

Look under

```text
Backend
```

---

## To verify the TLS configuration

```bash
kubectl describe ingress <ingress-name>
```

Look under

```text
TLS
```

---

## To display the Ingress address

```bash
kubectl get ingress
```

Check the **ADDRESS** column.

---

## To verify the Ingress class

```bash
kubectl get ingress
```

Check the **CLASS** column.

---

## To describe the IngressClass

```bash
kubectl describe ingressclass <ingressclass-name>
```

---

## To list all IngressClasses

```bash
kubectl get ingressclass
```

---

## To display an IngressClass in YAML format

```bash
kubectl get ingressclass <ingressclass-name> -o yaml
```

---

## To verify the NGINX Ingress Controller Pods

```bash
kubectl get pods -n ingress-nginx
```

---

## To verify the NGINX Ingress Controller Service

```bash
kubectl get svc -n ingress-nginx
```

---

## To view logs of the NGINX Ingress Controller

```bash
kubectl logs -n ingress-nginx <ingress-controller-pod>
```

---

## To follow the Ingress Controller logs

```bash
kubectl logs -f -n ingress-nginx <ingress-controller-pod>
```

---

## To install the NGINX Ingress Controller on Minikube

```bash
minikube addons enable ingress
```

---

## To verify that the Ingress addon is enabled

```bash
minikube addons list
```

---

## To test an Ingress locally

```bash
minikube tunnel
```

---

## To verify Services used by an Ingress

```bash
kubectl get svc
```

---

## To verify Endpoints used by an Ingress

```bash
kubectl get endpoints
```

---

## To verify Pods behind an Ingress

```bash
kubectl get pods
```

---

## To verify DNS resolution from inside a Pod

```bash
kubectl exec -it <pod-name> -- nslookup <service-name>
```

---

## To verify connectivity to a backend Service

```bash
kubectl exec -it <pod-name> -- curl http://<service-name>
```

---

## To check events related to an Ingress

```bash
kubectl describe ingress <ingress-name>
```

Scroll to the **Events** section.

---

## To troubleshoot an Ingress that is not routing traffic

1. Verify the Ingress

```bash
kubectl get ingress
```

2. Describe the Ingress

```bash
kubectl describe ingress <ingress-name>
```

3. Verify the backend Service

```bash
kubectl get svc
```

4. Verify the Endpoints

```bash
kubectl get endpoints
```

5. Verify the Pods

```bash
kubectl get pods
```

6. Verify the Ingress Controller

```bash
kubectl get pods -n ingress-nginx
```

7. Check the Ingress Controller logs

```bash
kubectl logs -n ingress-nginx <ingress-controller-pod>
```

---

## To apply all Ingress manifests in the current directory

```bash
kubectl apply -f .
```

---

## To delete all Ingress manifests in the current directory

```bash
kubectl delete -f .
```