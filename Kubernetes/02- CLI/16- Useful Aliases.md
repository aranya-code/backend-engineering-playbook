# Useful Aliases

## To create a short alias for kubectl (Linux/macOS)

```bash
alias k=kubectl
```

---

## To create a short alias for kubectl (Windows PowerShell)

```powershell
Set-Alias k kubectl
```

---

## To display Pods quickly

```bash
alias kgp="kubectl get pods"
```

---

## To display Pods in all namespaces

```bash
alias kgpa="kubectl get pods -A"
```

---

## To display Deployments

```bash
alias kgd="kubectl get deployments"
```

---

## To display ReplicaSets

```bash
alias kgrs="kubectl get rs"
```

---

## To display Services

```bash
alias kgs="kubectl get svc"
```

---

## To display Nodes

```bash
alias kgn="kubectl get nodes"
```

---

## To display Namespaces

```bash
alias kgns="kubectl get ns"
```

---

## To display ConfigMaps

```bash
alias kgcm="kubectl get configmaps"
```

---

## To display Secrets

```bash
alias kgsec="kubectl get secrets"
```

---

## To display Persistent Volumes

```bash
alias kgpv="kubectl get pv"
```

---

## To display Persistent Volume Claims

```bash
alias kgpvc="kubectl get pvc"
```

---

## To display StorageClasses

```bash
alias kgsc="kubectl get sc"
```

---

## To display Ingress resources

```bash
alias kging="kubectl get ingress"
```

---

## To display all Kubernetes resources

```bash
alias kga="kubectl get all"
```

---

## To describe a Pod

```bash
alias kdp="kubectl describe pod"
```

Usage

```bash
kdp <pod-name>
```

---

## To describe a Deployment

```bash
alias kdd="kubectl describe deployment"
```

Usage

```bash
kdd <deployment-name>
```

---

## To display Pod logs

```bash
alias kl="kubectl logs"
```

Usage

```bash
kl <pod-name>
```

---

## To follow Pod logs

```bash
alias klf="kubectl logs -f"
```

Usage

```bash
klf <pod-name>
```

---

## To execute a Bash shell inside a Pod

```bash
alias kexec="kubectl exec -it"
```

Usage

```bash
kexec <pod-name> -- bash
```

---

## To edit a resource

```bash
alias ke="kubectl edit"
```

Usage

```bash
ke deployment nginx
```

---

## To apply a manifest

```bash
alias kaf="kubectl apply -f"
```

Usage

```bash
kaf deployment.yaml
```

---

## To delete a manifest

```bash
alias kdf="kubectl delete -f"
```

Usage

```bash
kdf deployment.yaml
```

---

## To delete a resource

```bash
alias kd="kubectl delete"
```

Usage

```bash
kd pod nginx
```

---

## To restart a Deployment

```bash
alias krestart="kubectl rollout restart deployment"
```

Usage

```bash
krestart nginx
```

---

## To check Deployment rollout status

```bash
alias kstatus="kubectl rollout status deployment"
```

Usage

```bash
kstatus nginx
```

---

## To rollback a Deployment

```bash
alias kundo="kubectl rollout undo deployment"
```

Usage

```bash
kundo nginx
```

---

## To scale a Deployment

```bash
alias kscale="kubectl scale deployment"
```

Usage

```bash
kscale nginx --replicas=5
```

---

## To port-forward a Service

```bash
alias kpf="kubectl port-forward svc"
```

Usage

```bash
kpf nginx-service 8080:80
```

---

## To watch Pods continuously

```bash
alias kwatch="kubectl get pods -w"
```

---

## To display Pod resource usage

```bash
alias ktop="kubectl top pods"
```

---

## To display Node resource usage

```bash
alias ktopn="kubectl top nodes"
```

---

## To display cluster events

```bash
alias kevents="kubectl get events"
```

---

## To display the current context

```bash
alias kctx="kubectl config current-context"
```

---

## To display available contexts

```bash
alias kctxs="kubectl config get-contexts"
```

---

## To switch Kubernetes context

```bash
alias kuse="kubectl config use-context"
```

Usage

```bash
kuse production
```

---

## To display Helm releases

```bash
alias hls="helm list"
```

---

## To update Helm repositories

```bash
alias hru="helm repo update"
```

---

## To display Minikube status

```bash
alias mstatus="minikube status"
```

---

## To start Minikube

```bash
alias mstart="minikube start"
```

---

## To stop Minikube

```bash
alias mstop="minikube stop"
```

---

## To open the Minikube Dashboard

```bash
alias mdash="minikube dashboard"
```

---

## To permanently save aliases (Linux/macOS)

For **Bash**

```bash
nano ~/.bashrc
```

Add your aliases, then reload the shell:

```bash
source ~/.bashrc
```

---

For **Zsh**

```bash
nano ~/.zshrc
```

Reload the shell:

```bash
source ~/.zshrc
```

---

## To permanently save aliases (Windows PowerShell)

Open your PowerShell profile

```powershell
notepad $PROFILE
```

Add your aliases or functions, save the file, then reload:

```powershell
. $PROFILE
```

---

## To verify an alias

```bash
alias
```

To verify a specific alias

```bash
alias k
```

---

## To remove an alias

```bash
unalias k
```

---

## To display all configured aliases

```bash
alias
```