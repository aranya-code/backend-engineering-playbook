# Helm

## To check the installed Helm version

```bash
helm version
```

---

## To display Helm environment information

```bash
helm env
```

---

## To list all configured repositories

```bash
helm repo list
```

---

## To add a Helm repository

```bash
helm repo add <repo-name> <repository-url>
```

Example

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
```

---

## To update all Helm repositories

```bash
helm repo update
```

---

## To remove a Helm repository

```bash
helm repo remove <repo-name>
```

---

## To search repositories for a chart

```bash
helm search repo <chart-name>
```

Example

```bash
helm search repo nginx
```

---

## To search the Artifact Hub

```bash
helm search hub <chart-name>
```

---

## To display detailed information about a chart

```bash
helm show all <repo-name>/<chart-name>
```

Example

```bash
helm show all bitnami/nginx
```

---

## To display the chart values

```bash
helm show values <repo-name>/<chart-name>
```

---

## To display the chart metadata

```bash
helm show chart <repo-name>/<chart-name>
```

---

## To display the chart README

```bash
helm show readme <repo-name>/<chart-name>
```

---

## To create a new Helm chart

```bash
helm create <chart-name>
```

Example

```bash
helm create my-app
```

---

## To package a Helm chart

```bash
helm package <chart-directory>
```

---

## To validate a Helm chart

```bash
helm lint <chart-directory>
```

---

## To install a Helm chart

```bash
helm install <release-name> <repo-name>/<chart-name>
```

Example

```bash
helm install my-nginx bitnami/nginx
```

---

## To install a chart using a values file

```bash
helm install <release-name> <chart> -f values.yaml
```

---

## To install a chart into a specific namespace

```bash
helm install <release-name> <chart> -n <namespace> --create-namespace
```

---

## To perform a dry-run installation

```bash
helm install <release-name> <chart> --dry-run
```

---

## To install and generate manifests without deploying

```bash
helm template <release-name> <chart>
```

---

## To list all installed releases

```bash
helm list
```

---

## To list releases in all namespaces

```bash
helm list -A
```

---

## To list releases in a specific namespace

```bash
helm list -n <namespace>
```

---

## To display the status of a release

```bash
helm status <release-name>
```

---

## To display the values of a release

```bash
helm get values <release-name>
```

---

## To display all values including defaults

```bash
helm get values <release-name> --all
```

---

## To display the generated manifests

```bash
helm get manifest <release-name>
```

---

## To display release notes

```bash
helm get notes <release-name>
```

---

## To display release metadata

```bash
helm get metadata <release-name>
```

---

## To upgrade a release

```bash
helm upgrade <release-name> <chart>
```

---

## To upgrade using a values file

```bash
helm upgrade <release-name> <chart> -f values.yaml
```

---

## To upgrade and install if the release doesn't exist

```bash
helm upgrade --install <release-name> <chart>
```

---

## To rollback to the previous revision

```bash
helm rollback <release-name>
```

---

## To rollback to a specific revision

```bash
helm rollback <release-name> <revision>
```

Example

```bash
helm rollback my-nginx 2
```

---

## To display the release history

```bash
helm history <release-name>
```

---

## To uninstall a release

```bash
helm uninstall <release-name>
```

---

## To uninstall a release from a namespace

```bash
helm uninstall <release-name> -n <namespace>
```

---

## To verify installed releases

```bash
helm list
```

---

## To verify chart dependencies

```bash
helm dependency list <chart-directory>
```

---

## To download chart dependencies

```bash
helm dependency update <chart-directory>
```

---

## To build chart dependencies

```bash
helm dependency build <chart-directory>
```

---

## To verify chart templates

```bash
helm template <release-name> <chart>
```

---

## To verify rendered manifests with values

```bash
helm template <release-name> <chart> -f values.yaml
```

---

## To verify release revisions

```bash
helm history <release-name>
```

---

## To troubleshoot a failed installation

1. Check release status

```bash
helm status <release-name>
```

2. Check release history

```bash
helm history <release-name>
```

3. Render manifests locally

```bash
helm template <release-name> <chart>
```

4. Validate the chart

```bash
helm lint <chart-directory>
```

5. Check Kubernetes resources

```bash
kubectl get all
```

---

## To apply Helm-generated manifests manually

```bash
helm template <release-name> <chart> > manifests.yaml
```

Then

```bash
kubectl apply -f manifests.yaml
```

---

## To clean up all resources created by a release

```bash
helm uninstall <release-name>
```