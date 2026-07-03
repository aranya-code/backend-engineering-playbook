# Minikube

## To check the installed Minikube version

```bash
minikube version
```

---

## To start a Minikube cluster

```bash
minikube start
```

---

## To start Minikube using the Docker driver

```bash
minikube start --driver=docker
```

---

## To start Minikube with a specific Kubernetes version

```bash
minikube start --kubernetes-version=v1.30.0
```

---

## To start Minikube with a specific amount of memory

```bash
minikube start --memory=4096
```

---

## To start Minikube with a specific number of CPUs

```bash
minikube start --cpus=4
```

---

## To stop the Minikube cluster

```bash
minikube stop
```

---

## To restart the Minikube cluster

```bash
minikube stop

minikube start
```

---

## To delete the Minikube cluster

```bash
minikube delete
```

---

## To check the Minikube cluster status

```bash
minikube status
```

---

## To display the Minikube IP address

```bash
minikube ip
```

---

## To display cluster information

```bash
kubectl cluster-info
```

---

## To list cluster nodes

```bash
kubectl get nodes
```

---

## To SSH into the Minikube node

```bash
minikube ssh
```

---

## To open the Kubernetes Dashboard

```bash
minikube dashboard
```

---

## To list available Minikube addons

```bash
minikube addons list
```

---

## To enable the Ingress addon

```bash
minikube addons enable ingress
```

---

## To disable the Ingress addon

```bash
minikube addons disable ingress
```

---

## To enable the Metrics Server addon

```bash
minikube addons enable metrics-server
```

---

## To disable the Metrics Server addon

```bash
minikube addons disable metrics-server
```

---

## To enable the Dashboard addon

```bash
minikube addons enable dashboard
```

---

## To disable the Dashboard addon

```bash
minikube addons disable dashboard
```

---

## To list Docker images inside Minikube

```bash
minikube image ls
```

---

## To load a local Docker image into Minikube

```bash
minikube image load <image-name>:<tag>
```

Example

```bash
minikube image load backend-api:latest
```

---

## To remove an image from Minikube

```bash
minikube image rm <image-name>:<tag>
```

---

## To open a Service in the browser

```bash
minikube service <service-name>
```

Example

```bash
minikube service nginx-service
```

---

## To display the URL of a Service

```bash
minikube service <service-name> --url
```

---

## To expose a LoadBalancer Service locally

```bash
minikube tunnel
```

---

## To stop the Minikube tunnel

Press

```text
Ctrl + C
```

---

## To display Minikube logs

```bash
minikube logs
```

---

## To display only the last few log entries

```bash
minikube logs --problems
```

---

## To update Minikube

### Windows (Chocolatey)

```powershell
choco upgrade minikube
```

### macOS (Homebrew)

```bash
brew upgrade minikube
```

---

## To update the Kubernetes configuration

```bash
kubectl config view
```

---

## To display the active profile

```bash
minikube profile
```

---

## To list all Minikube profiles

```bash
minikube profile list
```

---

## To start a specific Minikube profile

```bash
minikube start -p <profile-name>
```

---

## To switch to another Minikube profile

```bash
minikube profile <profile-name>
```

---

## To delete a specific profile

```bash
minikube delete -p <profile-name>
```

---

## To mount a local directory inside Minikube

```bash
minikube mount <local-path>:<minikube-path>
```

Example

```bash
minikube mount C:\Projects:/mnt/projects
```

---

## To display the Docker environment variables

```bash
minikube docker-env
```

---

## To configure Docker to use Minikube's Docker daemon

### Linux / macOS

```bash
eval $(minikube docker-env)
```

---

### Windows PowerShell

```powershell
minikube -p minikube docker-env | Invoke-Expression
```

---

## To return Docker to the local Docker daemon

### Linux / macOS

```bash
eval $(minikube docker-env --unset)
```

---

### Windows PowerShell

```powershell
minikube -p minikube docker-env --unset | Invoke-Expression
```

---

## To verify that the Ingress Controller is running

```bash
kubectl get pods -n ingress-nginx
```

---

## To verify the Metrics Server is running

```bash
kubectl get pods -n kube-system
```

Look for

```text
metrics-server
```

---

## To display all running Pods

```bash
kubectl get pods -A
```

---

## To verify cluster resource usage

```bash
kubectl top nodes
```

---

## To verify Pod resource usage

```bash
kubectl top pods
```

---

## To troubleshoot Minikube startup issues

1. Check cluster status

```bash
minikube status
```

2. View Minikube logs

```bash
minikube logs
```

3. Verify Docker is running

```bash
docker ps
```

4. Verify cluster nodes

```bash
kubectl get nodes
```

---

## To completely reset the Minikube environment

```bash
minikube stop

minikube delete

minikube start
```

---

## To apply all Kubernetes manifests

```bash
kubectl apply -f .
```

---

## To delete all Kubernetes manifests

```bash
kubectl delete -f .
```