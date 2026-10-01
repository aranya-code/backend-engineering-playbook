# 13- GITHUB_TOKEN and Permissions Questions

## Overview

`GITHUB_TOKEN` is the default GitHub-provided authentication token available to GitHub Actions workflows. Its security impact depends primarily on the permissions granted to it and the code that executes with those permissions.

For senior backend engineering, the important question is not simply:

> "What is `GITHUB_TOKEN`?"

It is:

> "What can this workflow execution do if its code, an action dependency, or a runner is compromised?"

A production security model therefore combines:

```text
GITHUB_TOKEN
    +
Explicit permissions
    +
Job isolation
    +
Secret isolation
    +
Environment protection
    +
Third-party action controls
    +
Untrusted-input handling
    +
Runner isolation
```

A typical secure deployment pipeline looks like:

```text
Pull Request
    ↓
Unprivileged CI
    ↓
Tests / Security Scan
    ↓
Trusted Build
    ↓
Immutable Artifact
    ↓
Protected Environment
    ↓
OIDC
    ↓
AWS STS
    ↓
Least-Privilege IAM Role
    ↓
Production
```

---

## GitHub Actions Execution Model

A useful model is:

```text
Workflow
   ↓
Job
   ↓
Runner
   ↓
Steps
   ↓
Actions / Scripts
   ↓
GITHUB_TOKEN + Secrets + External Credentials
```

Every step executed by a job potentially runs with the permissions and access available to that job.

For example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    permissions:
      contents: read

    steps:
      - uses: actions/checkout@v4

      - run: pytest
```

The important security property is:

```text
Test code
   ↓
contents: read
```

rather than:

```text
Test code
   ↓
Broad repository write permissions
   ↓
Cloud credentials
   ↓
Production
```

---

## What Is `GITHUB_TOKEN`?

`GITHUB_TOKEN` is an automatically created authentication token that allows a workflow to interact with GitHub APIs and resources according to its configured permissions.

It is exposed to workflow steps through the `github.token` context and commonly through the `GITHUB_TOKEN` environment variable.

For example:

```yaml
- name: Inspect repository
  env:
    GH_TOKEN: ${{ github.token }}
  run: |
    gh repo view
```

The token is intended to provide workflow-specific GitHub access without requiring a manually created personal access token for common automation tasks.

---

## Why Does `GITHUB_TOKEN` Exist?

Without a workflow token, every workflow that needed to interact with GitHub would require manually managed credentials.

`GITHUB_TOKEN` provides:

- Automatic provisioning.
- Workflow-scoped authentication.
- Permission controls.
- Reduced credential-management overhead.
- Integration with GitHub APIs and CLI.
- A token associated with the workflow execution.

The security benefit depends on correctly limiting its permissions.

---

## Authentication vs Authorization

These concepts should be separated.

### Authentication

Answers:

```text
Who is making the request?
```

### Authorization

Answers:

```text
What is that identity allowed to do?
```

For `GITHUB_TOKEN`:

```text
GITHUB_TOKEN
    ↓
Authentication
    ↓
GitHub identifies the workflow token
    ↓
Permissions
    ↓
Authorization
```

A valid token does not automatically imply unrestricted access.

---

## `GITHUB_TOKEN` Permission Model

Permissions determine what the token can do.

Example:

```yaml
permissions:
  contents: read
```

This grants read access to repository contents while avoiding unrelated write privileges.

A deployment job may require additional permissions:

```yaml
permissions:
  contents: read
  id-token: write
```

The second permission is relevant to OIDC authentication with AWS and does not mean the token itself becomes an AWS credential.

---

## Common Permissions

| Permission | Typical purpose |
|---|---|
| `contents` | Repository contents |
| `actions` | Actions and workflow operations |
| `packages` | Package registry operations |
| `pull-requests` | Pull request operations |
| `issues` | Issue operations |
| `checks` | Check runs |
| `deployments` | Deployment operations |
| `id-token` | OIDC identity token requests |

The exact permission required depends on the operation being performed.

---

## Read vs Write Permissions

Permissions commonly have states such as:

```text
read
write
none
```

For example:

```yaml
permissions:
  contents: read
```

is substantially narrower than granting write access.

Prefer the smallest permission that satisfies the job.

---

## Explicit Permissions

A secure workflow commonly establishes a restrictive baseline:

```yaml
permissions:
  contents: read
```

Then privileged jobs explicitly request additional permissions.

Example:

```yaml
jobs:
  test:
    permissions:
      contents: read

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - run: pytest

  deploy:
    permissions:
      contents: read
      id-token: write

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
```

This creates privilege separation.

---

## Workflow-Level vs Job-Level Permissions

Workflow-level:

```yaml
permissions:
  contents: read
```

establishes permissions for the workflow unless overridden at the job level.

Job-level:

```yaml
jobs:
  deploy:
    permissions:
      contents: read
      id-token: write
```

allows finer-grained control.

A production workflow should prefer job-level privilege where only one job needs elevated access.

---

## Why Job-Level Permissions Matter

Consider:

```text
Lint
Unit Tests
Integration Tests
Security Scan
Build
Deploy
```

Only `Deploy` may need:

```text
id-token: write
```

If all jobs receive it:

```text
Compromised test
    ↓
OIDC token capability
    ↓
Potential AWS role assumption
```

If only the deployment job receives it:

```text
Compromised test
    ↓
No OIDC permission

Deploy job
    ↓
OIDC permission
```

The second architecture reduces the blast radius.

---

## Least Privilege

Least privilege means:

> Give each workflow job only the permissions and credentials required to perform its responsibility.

A good decomposition is:

```text
Test job
    → contents: read

Build job
    → contents: read

Release job
    → contents: read
    → release-related permission if required

AWS deployment job
    → contents: read
    → id-token: write
```

Avoid granting broad privileges merely because they make workflow development easier.

---

## `write-all` and Broad Permissions

Broad permission configurations should be treated as security smells.

For example:

```yaml
permissions: write-all
```

makes it difficult to reason about the actual blast radius of a compromised action.

Prefer:

```yaml
permissions:
  contents: read
```

and add individual permissions only when required.

---

## Permission Inheritance and Overrides

A workflow can establish a baseline:

```yaml
permissions:
  contents: read
```

and individual jobs can define their own permission set.

When reviewing a workflow, inspect:

1. Workflow-level permissions.
2. Job-level permissions.
3. Reusable workflow permissions.
4. Action behavior.
5. Environment protection.
6. External credentials.

Do not assume the top-level block tells the entire security story.

---

## `GITHUB_TOKEN` vs Personal Access Token

| Property | `GITHUB_TOKEN` | Personal Access Token |
|---|---|---|
| Creation | Automatic | Manually created |
| Workflow integration | Native | Manual |
| Lifecycle | Workflow-oriented | User/token lifecycle |
| Permissions | Workflow-controlled | Token scopes |
| User dependency | No | Usually yes |
| Credential management | Lower overhead | Higher overhead |
| Common CI use | Preferred for supported operations | Use when specific capabilities require it |

Use `GITHUB_TOKEN` where it provides the required capability.

Do not introduce a long-lived personal token simply because it is familiar.

---

## `GITHUB_TOKEN` vs OIDC

These solve different problems.

### `GITHUB_TOKEN`

Used for GitHub resources:

```text
GitHub Actions
    ↓
GITHUB_TOKEN
    ↓
GitHub API / GitHub resources
```

### OIDC

Used to establish workload identity with an external provider such as AWS:

```text
GitHub Actions
    ↓
OIDC token
    ↓
AWS STS
    ↓
IAM role
    ↓
AWS resources
```

A secure AWS deployment may therefore use both:

```text
GITHUB_TOKEN
    → repository access

OIDC
    → AWS authentication
```

---

## `id-token: write`

AWS OIDC workflows commonly require:

```yaml
permissions:
  contents: read
  id-token: write
```

`id-token: write` allows the workflow to request an OIDC identity token.

It does **not** mean:

```text
The workflow receives unrestricted AWS access.
```

AWS authorization still depends on:

```text
OIDC trust policy
+
IAM role permissions
```

---

## AWS OIDC Flow

```mermaid
sequenceDiagram
    participant G as GitHub Actions
    participant O as GitHub OIDC
    participant S as AWS STS
    participant I as IAM
    participant A as AWS Resource

    G->>O: Request OIDC identity token
    O-->>G: OIDC token
    G->>S: AssumeRoleWithWebIdentity
    S->>I: Evaluate trust policy
    I-->>S: Allow / Deny
    S-->>G: Temporary credentials
    G->>A: API request
```

The security boundary consists of both:

```text
GitHub permissions
+
AWS trust policy
+
AWS IAM permissions
```

---

## IAM Trust Policy vs IAM Permissions

These are different.

### Trust Policy

Answers:

```text
Who can assume this role?
```

### Permissions Policy

Answers:

```text
What can the assumed role do?
```

Therefore:

```text
OIDC token
    ↓
Trust policy
    ↓
IAM role
    ↓
Permissions policy
    ↓
AWS resources
```

A secure deployment requires both sides to be restrictive.

---

## Repository-Scoped OIDC

Avoid broad trust relationships where possible.

Conceptually:

```text
Any GitHub repository
        ↓
Production IAM role
```

is much broader than:

```text
Specific repository
        ↓
Specific branch/environment
        ↓
Production IAM role
```

The exact conditions depend on the organization's repository and release model.

---

## GITHUB_TOKEN and Secrets

`GITHUB_TOKEN` and GitHub Secrets are separate concepts.

```text
GITHUB_TOKEN
    ↓
GitHub authentication

Secrets
    ↓
Application / external credentials
```

For example:

```yaml
env:
  API_TOKEN: ${{ secrets.API_TOKEN }}
```

The workflow may have both:

```text
GITHUB_TOKEN
+
API_TOKEN
```

Each should have an independent security boundary.

---

## Secrets Do Not Become Safe Because `GITHUB_TOKEN` Is Restricted

Consider:

```yaml
permissions:
  contents: read

env:
  PROD_PASSWORD: ${{ secrets.PROD_PASSWORD }}
```

The GitHub token may be tightly restricted while the production password is still available to the job.

Security must therefore consider:

```text
Token permissions
+
Secrets
+
Runner
+
Network
+
Code executed
```

---

## Environment Secrets

Production secrets should generally be associated with the appropriate environment.

Example:

```text
development
staging
production
```

A production deployment job can use:

```yaml
environment:
  name: production
```

and receive the credentials associated with that environment subject to the environment's protection rules.

---

## Required Reviewers

Production environments can require approval before deployment continues.

Conceptually:

```text
Build
 ↓
Staging
 ↓
Validation
 ↓
Production environment
 ↓
Required approval
 ↓
Deployment
```

This creates a human-controlled security boundary for high-impact operations.

---

## Branch Restrictions

Production deployment should not necessarily be available from every branch.

For example:

```text
main
release/*
```

may be allowed while:

```text
feature/*
experiment/*
```

are not.

The exact branch strategy depends on the repository's release process.

---

## `pull_request` and `GITHUB_TOKEN`

Pull request workflows should be designed with potentially untrusted code in mind.

A pull request can modify:

```text
Application code
Tests
Build scripts
Dependency files
Shell scripts
Dockerfiles
```

If CI executes that code, the workflow is effectively executing contributor-controlled code.

Therefore:

```text
PR code
    ≠
Trusted deployment code
```

---

## Fork Pull Requests

Forks are particularly important.

A contributor may create:

```text
Attacker-controlled repository
        ↓
Pull request
        ↓
Base repository workflow
```

The workflow should not automatically expose:

```text
Production secrets
+
Cloud credentials
+
Privileged self-hosted runners
```

to the untrusted code.

---

## `pull_request_target`

`pull_request_target` runs in the context of the base repository.

This can make repository resources and permissions available in situations where ordinary pull request workflows would not have them.

The dangerous pattern is:

```text
pull_request_target
       ↓
Checkout attacker-controlled PR
       ↓
Execute PR code
       ↓
Access privileged credentials
```

Avoid this architecture.

---

## Secure PR Architecture

Prefer:

```text
pull_request
    ↓
GitHub-hosted runner
    ↓
No production secrets
    ↓
Tests / lint / security checks
```

Then:

```text
Trusted branch
    ↓
Protected deployment workflow
    ↓
Environment approval
    ↓
OIDC
    ↓
Production
```

---

## Untrusted Input and Permissions

GitHub contexts contain values that may be influenced by users.

Examples:

```text
github.event.pull_request.title
github.event.pull_request.body
github.ref_name
github.event.head_commit.message
workflow_dispatch inputs
repository_dispatch payload
```

Do not treat these values as trusted simply because they are provided by GitHub.

---

## Shell Injection

Dangerous:

```yaml
- name: Process PR title
  run: |
    echo "${{ github.event.pull_request.title }}"
```

A malicious pull request title could contain shell syntax.

The expression is evaluated before the shell receives the command.

---

## Safer Input Handling

Prefer:

```yaml
- name: Process PR title
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: |
    printf '%s\n' "$PR_TITLE"
```

The value is passed as data through an environment variable.

This is a general pattern:

```text
Untrusted GitHub value
        ↓
Environment variable
        ↓
Quoted shell variable
```

---

## Python Subprocess Example

Avoid:

```python
import subprocess

subprocess.run(
    f"deploy {branch_name}",
    shell=True,
)
```

Prefer:

```python
import subprocess

subprocess.run(
    ["deploy", branch_name],
    check=True,
)
```

Use validation when the value is expected to belong to a constrained set.

---

## Permission Escalation Through Untrusted Inputs

An attacker may attempt to influence:

```text
Environment
AWS account
AWS role
Docker image
Deployment target
Matrix
Runner label
```

For security-sensitive values, use explicit allowlists.

Example:

```bash
case "$ENVIRONMENT" in
  staging|production)
    ;;
  *)
    echo "Invalid environment" >&2
    exit 1
    ;;
esac
```

---

## `GITHUB_OUTPUT` and Permission Boundaries

Outputs transfer data between workflow steps and jobs.

Example:

```bash
echo "image=$IMAGE" >> "$GITHUB_OUTPUT"
```

A privileged job should not blindly trust outputs produced by an untrusted job.

Consider:

```text
Untrusted job
    ↓
Output
    ↓
Privileged deployment job
```

The output becomes a trust boundary.

Validate security-sensitive values before consuming them.

---

## Dynamic Matrices

A planning job may generate:

```json
{
  "python": ["3.11", "3.12"],
  "database": ["postgres", "mysql"]
}
```

and expose it as an output.

A downstream job may use:

```yaml
strategy:
  matrix: ${{ fromJSON(needs.plan.outputs.matrix) }}
```

This is powerful but should be designed carefully if the matrix originates from untrusted input.

---

## Third-Party Actions and `GITHUB_TOKEN`

A third-party action executes within the workflow's security context.

If a job has:

```yaml
permissions:
  contents: write
```

then an action executed by that job may potentially use the available GitHub authorization to perform repository operations.

Therefore:

```text
Action trust
+
Token permissions
```

must be considered together.

---

## Least Privilege With Third-Party Actions

Prefer:

```yaml
permissions:
  contents: read
```

for jobs that only need repository access.

Avoid giving an entire job write access simply because one action requires a narrow capability.

Where possible, isolate privileged operations into a dedicated job.

---

## Action Pinning

Avoid:

```yaml
uses: third-party/action@main
```

for security-sensitive workflows.

A version reference is more controlled:

```yaml
uses: third-party/action@v4
```

SHA pinning provides stronger immutability:

```yaml
uses: third-party/action@<commit-sha>
```

Organizations should combine pinning with an update and review process.

---

## Compromised Action Scenario

Suppose:

```text
deploy job
    ↓
GITHUB_TOKEN
    ↓
id-token: write
    ↓
AWS production role
```

and a third-party action in that job becomes compromised.

The action may inherit the job's available capabilities.

This demonstrates why:

```text
Least-privilege job design
```

is more important than simply trusting the action's name or marketplace listing.

---

## Reusable Workflows and Permissions

Reusable workflows can centralize permission policies.

Example:

```yaml
on:
  workflow_call:

jobs:
  ci:
    permissions:
      contents: read
```

A deployment reusable workflow may deliberately request:

```yaml
permissions:
  contents: read
  id-token: write
```

The caller and reusable workflow should have a clear contract around privileges.

---

## `secrets: inherit`

A reusable workflow can receive inherited secrets:

```yaml
jobs:
  deploy:
    uses: org/platform/.github/workflows/deploy.yml@v1
    secrets: inherit
```

This is convenient but broad.

Use it only when the caller and reusable workflow have an appropriate trust relationship.

Explicit secret passing provides a clearer interface:

```yaml
jobs:
  deploy:
    uses: org/platform/.github/workflows/deploy.yml@v1
    secrets:
      DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```

---

## Reusable Workflow vs Composite Action

| Capability | Reusable Workflow | Composite Action |
|---|---|---|
| Multiple jobs | Yes | No |
| Job orchestration | Yes | No |
| Matrix at workflow/job level | Yes | Limited by caller |
| Environment/deployment orchestration | Yes | No |
| Package reusable steps | No | Yes |
| `workflow_call` | Yes | No |
| `action.yml` | No | Yes |

A reusable workflow is appropriate for pipeline orchestration.

A composite action is appropriate for packaging reusable steps within a job.

---

## Permission Design for Reusable Workflows

A reusable workflow should not expose more privileges than required.

For example:

```text
Reusable CI
    ↓
contents: read

Reusable deployment
    ↓
contents: read
id-token: write
```

This creates reusable security boundaries across repositories.

---

## Production Deployment Example

```yaml
name: Deploy

on:
  workflow_dispatch:
    inputs:
      image:
        description: Immutable container image
        required: true
        type: string

permissions:
  contents: read

concurrency:
  group: production
  cancel-in-progress: false

jobs:
  deploy:
    runs-on: ubuntu-latest

    environment:
      name: production

    permissions:
      contents: read
      id-token: write

    steps:
      - name: Validate image
        env:
          IMAGE: ${{ inputs.image }}
        run: |
          test -n "$IMAGE"
          printf 'Deploying %s\n' "$IMAGE"

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}

      - name: Deploy
        env:
          IMAGE: ${{ inputs.image }}
        run: |
          ./scripts/deploy.sh "$IMAGE"
```

The security model is:

```text
Minimal workflow permissions
        ↓
Protected production environment
        ↓
Job-specific OIDC permission
        ↓
AWS trust policy
        ↓
Least-privilege IAM role
        ↓
Immutable image
```

---

## Build Once, Promote Many

A secure production pipeline should prefer:

```text
Pull Request
 ↓
Tests
 ↓
Security Scan
 ↓
Build
 ↓
Immutable Artifact
 ↓
Staging
 ↓
Approval
 ↓
Production
```

rather than:

```text
Build staging image
 ↓
Staging

Rebuild source
 ↓
Production
```

Rebuilding creates a new artifact and therefore a new supply-chain event.

---

## Docker Image Identity

Prefer immutable identities such as:

```text
orders-api@sha256:...
```

or:

```text
orders-api:8f3a2c1
```

rather than relying solely on:

```text
orders-api:latest
```

Production deployment should know exactly which artifact is being deployed.

---

## GITHUB_TOKEN and Docker Registries

If using GitHub Container Registry, `GITHUB_TOKEN` may be used for authentication when the required package permissions are configured.

For example:

```yaml
permissions:
  contents: read
  packages: write
```

The exact permissions should be limited to the operation being performed.

For Amazon ECR, OIDC and AWS IAM are typically the more relevant authentication mechanism.

---

## Artifact Integrity

A secure artifact flow is:

```text
Build
 ↓
Scan
 ↓
SBOM
 ↓
Provenance
 ↓
Attestation / Signing
 ↓
Registry
 ↓
Promotion
```

The deployment system should verify or otherwise enforce the artifact controls appropriate to the organization's security requirements.

---

## Runner Security

`GITHUB_TOKEN` security cannot be separated from runner security.

A job may have:

```yaml
permissions:
  contents: read
```

but the runner may still have access to:

```text
Private network
Filesystem
Docker socket
Cloud metadata
Internal APIs
```

Therefore token permissions are only one layer of the security model.

---

## GitHub-Hosted Runners

GitHub-hosted runners are commonly suitable for untrusted CI because the execution environment is managed by GitHub and is separated from persistent organizational infrastructure.

They are particularly useful for:

```text
Pull request testing
Linting
Unit tests
Static analysis
Matrix testing
```

when private network access is unnecessary.

---

## Self-Hosted Runner Risks

A self-hosted runner may have:

```text
Persistent filesystem
Private VPC access
Custom credentials
Docker
Internal DNS
Internal APIs
Deployment tooling
```

If untrusted code runs there, compromising the runner can expose more than the `GITHUB_TOKEN`.

---

## Ephemeral Runners

For sensitive or untrusted workloads:

```text
Provision
 ↓
Register
 ↓
Run one job
 ↓
Destroy
```

reduces persistence.

This is particularly useful for workloads that need custom software or private network access.

---

## Runner Groups

Use runner groups to separate trust domains.

Example:

```text
General CI
    ↓
GitHub-hosted runners

Private integration tests
    ↓
Private runner group

Production deployment
    ↓
Restricted deployment runner group
```

Do not allow arbitrary pull-request workflows to select privileged deployment runners.

---

## Private Network Access

A runner with access to a private VPC can potentially reach:

```text
PostgreSQL
Redis
Kafka
Internal APIs
Kubernetes
Deployment systems
```

The workflow's GitHub permissions may be minimal while its network privileges remain broad.

Security architecture must consider both.

---

## GITHUB_TOKEN and Service Containers

Service containers are useful for integration tests:

```text
Python application
    ↓
PostgreSQL
    ↓
Redis
    ↓
pytest
```

These services should use isolated test credentials and networks.

A test job should not use production credentials simply because the application requires a database.

---

## Django Example

```yaml
jobs:
  integration:
    runs-on: ubuntu-latest

    permissions:
      contents: read

    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: app_test
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -r requirements.txt

      - name: Run migrations
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/app_test
        run: python manage.py migrate

      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/app_test
        run: pytest
```

This job needs repository read access but does not need production cloud permissions.

---

## Permission Isolation in a Complete Pipeline

A production pipeline can be structured as:

```text
Lint
  permissions:
    contents: read

Unit Tests
  permissions:
    contents: read

Integration Tests
  permissions:
    contents: read

Security Scan
  permissions:
    contents: read

Build
  permissions:
    contents: read

Publish
  permissions:
    contents: read
    packages: write

AWS Deployment
  permissions:
    contents: read
    id-token: write
```

This is much easier to audit than one workflow-wide broad permission set.

---

## Permission Troubleshooting

Use the following model:

```text
Symptom
 ↓
Identify operation
 ↓
Identify job
 ↓
Inspect permissions
 ↓
Identify required permission
 ↓
Grant minimum permission
 ↓
Retry
 ↓
Document requirement
```

Do not immediately grant:

```yaml
permissions: write-all
```

just to make a failing workflow pass.

---

## Symptom: API Request Returns 403

### Possible Causes

- Missing permission.
- Permission set to `none`.
- Job-level permissions overriding workflow permissions.
- Resource-specific authorization.
- Repository policy.
- Organization policy.

### Isolation

Identify:

```text
Which API?
Which job?
Which token?
Which permission?
```

Then inspect the workflow permission blocks.

### Corrective Action

Grant only the required permission.

---

## Symptom: AWS Deployment Returns `AccessDenied`

### Possible Causes

- Missing `id-token: write`.
- Incorrect IAM trust policy.
- Incorrect repository condition.
- Incorrect branch/environment condition.
- Incorrect IAM permission.
- Wrong AWS account.
- Incorrect role ARN.

### Checks

```bash
aws sts get-caller-identity
```

Then inspect the IAM trust and permissions policies.

---

## Symptom: Action Cannot Push Package

### Possible Causes

- Missing `packages: write`.
- Registry authentication failure.
- Repository/package policy.
- Incorrect registry configuration.

### Corrective Action

Add only the required package permission:

```yaml
permissions:
  contents: read
  packages: write
```

---

## Symptom: Pull Request Workflow Cannot Access Secret

This may be intentional.

Investigate:

```text
Is the PR from a fork?
Is the workflow using pull_request?
Is the secret repository/environment scoped?
Is the environment protected?
Is this an untrusted workflow?
```

Do not solve the problem by exposing production secrets to the PR.

---

## Symptom: `GITHUB_TOKEN` Can Modify Too Much

### Possible Causes

- Broad workflow permissions.
- Broad job permissions.
- Organization defaults.
- Privileged reusable workflow.
- Third-party action running in a privileged job.

### Corrective Action

Move to explicit permissions:

```yaml
permissions:
  contents: read
```

and isolate privileged operations.

---

## Symptom: Third-Party Action Requires Excessive Permission

First determine whether the action truly requires the requested capability.

Possible approaches:

- Replace the action.
- Isolate it in a dedicated job.
- Reduce job permissions.
- Use an internal action.
- Implement the operation directly.
- Pin and review the action.

Do not automatically grant repository-wide write permissions.

---

## Symptom: Production Deployment Can Be Triggered From Any Branch

### Possible Causes

- No environment restrictions.
- Workflow triggered by arbitrary branch.
- Manual dispatch accepts unrestricted input.
- IAM trust policy is too broad.
- Deployment workflow does not validate release source.

### Corrective Action

Combine:

```text
Branch restrictions
+
Environment protection
+
OIDC trust conditions
+
Deployment permissions
```

---

## Security Failure-Domain Matrix

| Failure | Primary Question | Control |
|---|---|---|
| 403 from GitHub API | Is token permission sufficient? | Explicit permissions |
| AWS `AccessDenied` | Is identity trusted and authorized? | OIDC + IAM |
| Secret unavailable | Should this workflow receive it? | Scope/environment |
| Secret exposed | Where did it escape? | Rotate + investigate |
| PR security issue | Is code trusted? | `pull_request` boundary |
| Action compromise | What can action access? | Pinning + least privilege |
| Runner compromise | What can runner reach? | Isolation |
| Artifact compromise | Can artifact be trusted? | Provenance + immutability |
| Deployment race | Can two releases overlap? | Concurrency |
| Unauthorized deployment | Who can promote? | Environment protection |

---

## GitHub CLI for Permission Operations

List workflows:

```bash
gh workflow list
```

Inspect workflow runs:

```bash
gh run list
```

Inspect a specific run:

```bash
gh run view RUN_ID
```

View logs:

```bash
gh run view RUN_ID --log
```

Inspect repository secrets metadata:

```bash
gh secret list
```

Inspect repository variables:

```bash
gh variable list
```

Repository information:

```bash
gh repo view
```

For deeper permission debugging, GitHub's API can be queried through `gh api`.

Example:

```bash
gh api repos/OWNER/REPO/actions/permissions
```

---

## Security Review Checklist

### Workflow Permissions

- [ ] Top-level permissions are explicit.
- [ ] Job-level permissions are used for privileged jobs.
- [ ] No unnecessary write permissions exist.
- [ ] `id-token: write` exists only where required.
- [ ] Third-party actions run with appropriate privileges.

### Pull Requests

- [ ] Fork PRs are treated as untrusted.
- [ ] Production secrets are not exposed to untrusted PR code.
- [ ] `pull_request_target` usage is reviewed.
- [ ] Untrusted GitHub values are not directly interpolated into shell commands.
- [ ] Self-hosted privileged runners are not exposed to arbitrary PR workflows.

### Secrets

- [ ] Production secrets are environment-scoped where appropriate.
- [ ] Secrets are not printed.
- [ ] Secrets are not passed unnecessarily between jobs.
- [ ] Secrets are not embedded in artifacts or Docker images.
- [ ] AWS long-lived credentials are avoided where OIDC is available.

### AWS

- [ ] OIDC is used where appropriate.
- [ ] IAM trust policies are narrow.
- [ ] IAM permissions are least privilege.
- [ ] Staging and production roles are separated where appropriate.
- [ ] CloudTrail can support incident investigation.

### Actions

- [ ] Third-party actions are reviewed.
- [ ] Actions use controlled references.
- [ ] SHA pinning is considered for high-trust workflows.
- [ ] Action dependencies are reviewed.
- [ ] Organization action policies are defined where appropriate.

### Runners

- [ ] Privileged runners are isolated.
- [ ] Runner groups restrict access.
- [ ] Ephemeral runners are considered for sensitive workloads.
- [ ] Private network access is minimized.
- [ ] Docker socket access is restricted.
- [ ] Runner images are maintained and replaceable.

---

## Interview Questions

### What is `GITHUB_TOKEN`?

It is a GitHub-provided authentication token for workflow execution. Its effective capabilities are controlled through GitHub Actions permissions.

---

### Why should permissions be explicitly configured?

Explicit permissions make the workflow's security boundary easier to reason about and reduce the blast radius of compromised workflow code or actions.

---

### What is the difference between workflow-level and job-level permissions?

Workflow-level permissions establish a default permission model. Job-level permissions allow individual jobs to receive a different, typically narrower or more privileged, permission set.

---

### Why is job-level permission isolation important?

Because jobs execute different types of code and often have different trust levels.

A test job should not automatically receive the same cloud or repository privileges as a deployment job.

---

### Why is `id-token: write` not equivalent to AWS administrator access?

`id-token: write` allows the workflow to request an OIDC identity token. AWS still evaluates the token through an IAM trust policy before issuing temporary credentials, and the resulting IAM role determines what AWS operations are authorized.

---

### How would you secure a production deployment using AWS?

Use:

```text
Protected environment
+
Restricted branch/source
+
Job-level id-token: write
+
OIDC
+
Narrow IAM trust policy
+
Least-privilege IAM permissions
+
Immutable artifact
+
Deployment concurrency
```

---

### Why should AWS access keys not normally be stored as GitHub secrets?

Long-lived credentials increase the persistence and management burden of a compromise. OIDC can provide short-lived AWS credentials through STS without storing permanent access keys in GitHub.

---

### Can `GITHUB_TOKEN` access repository secrets?

No. `GITHUB_TOKEN` and GitHub Secrets are separate mechanisms. A workflow may have access to both, but secret availability is controlled by secret scope, workflow context, environment, and other applicable rules.

---

### Why is `pull_request_target` risky?

It executes with the base repository context and can have access to privileges unavailable to ordinary pull request workflows. Checking out and executing attacker-controlled PR code in that context can expose secrets or privileged capabilities.

---

### How would you secure fork pull requests?

Use an unprivileged pull request workflow, minimize permissions, avoid production secrets, use appropriately isolated runners, and separate validation from privileged deployment.

---

### Why can this be dangerous?

```yaml
run: echo "${{ github.event.pull_request.title }}"
```

Because the pull request title can be attacker-controlled and is inserted into a shell command before execution.

Use an environment variable instead:

```yaml
env:
  PR_TITLE: ${{ github.event.pull_request.title }}
run: |
  printf '%s\n' "$PR_TITLE"
```

---

### Why does SHA pinning matter?

It prevents a mutable action reference from silently changing to a different commit. It improves reproducibility and reduces one class of supply-chain risk.

It does not replace action review or vulnerability management.

---

### What happens if a third-party action is compromised?

The action executes inside the workflow's security context. Its effective impact depends on:

```text
GITHUB_TOKEN permissions
+
Secrets
+
OIDC permissions
+
Runner access
+
Network access
```

Therefore least privilege limits the potential blast radius.

---

### Why should privileged actions be isolated into separate jobs?

A dedicated privileged job can have:

```text
Minimal required permissions
+
Restricted environment
+
Specific secrets
+
Specific runner
```

while the rest of the pipeline remains unprivileged.

---

### How do reusable workflows improve security?

They can centralize:

- Permission policies.
- Deployment logic.
- Security scanning.
- OIDC configuration.
- Environment controls.

This reduces duplicated security-sensitive configuration across repositories.

---

### What is the security concern with `secrets: inherit`?

It can expose more secrets than an explicit secret contract would.

Use inheritance only when the caller and reusable workflow have an appropriate trust relationship.

---

### How would you protect a self-hosted production runner?

Use:

```text
Restricted runner group
+
Dedicated repository/workflow access
+
Ephemeral lifecycle where appropriate
+
Minimal network access
+
Hardened runner image
+
Credential isolation
+
Monitoring
+
Fast replacement
```

Do not allow arbitrary PR workflows to execute on it.

---

### How would you investigate excessive `GITHUB_TOKEN` permissions?

Start with:

```text
Workflow-level permissions
 ↓
Job-level permissions
 ↓
Reusable workflow
 ↓
Third-party actions
 ↓
Repository/org policies
```

Then identify the exact GitHub operation that requires the permission and reduce the permission set to that requirement.

---

## Senior Scenario: Production Deployment Must Not Run Twice

Requirements:

```text
Production deployment
+
Only one active deployment
+
No overlapping releases
```

Use:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

Combine this with:

```text
Protected environment
+
Approval
+
Immutable artifact
+
Health checks
+
Rollback
```

The security concern is not only concurrency. It is preventing conflicting privileged state transitions.

---

## Senior Scenario: Multiple Python Versions

A test matrix can use:

```yaml
strategy:
  matrix:
    python-version:
      - "3.11"
      - "3.12"
      - "3.13"
```

The test jobs should normally use minimal permissions:

```yaml
permissions:
  contents: read
```

There is no reason for a compatibility matrix job to receive production AWS permissions.

---

## Senior Scenario: PostgreSQL and Redis

Use isolated service containers:

```text
Matrix Job
   ├── PostgreSQL
   ├── Redis
   └── pytest
```

Credentials should be test-only.

The integration-test job should not have:

```text
Production database credentials
Production Redis credentials
Production AWS role
```

---

## Senior Scenario: Reusable CI Across Repositories

Use a reusable workflow:

```text
Repository A
      ↓
Reusable CI
      ↑
Repository B
      ↓
Reusable CI
      ↑
Repository C
```

The reusable workflow can standardize:

```text
Permissions
Python setup
Linting
Testing
Security scanning
Artifact generation
```

Version the reusable workflow and establish ownership and change-management controls.

---

## Senior Scenario: Compromised Marketplace Action

Suppose a production workflow contains:

```yaml
- uses: third-party/action@v4
```

and the action is compromised.

The investigation should ask:

```text
Which repositories use it?
Which versions?
Which workflows?
What permissions?
What secrets?
What OIDC roles?
Which runners?
Which artifacts?
Which deployments?
```

Recovery:

```text
Stop affected workflows
 ↓
Pin/revert to trusted action
 ↓
Rotate exposed credentials
 ↓
Inspect artifacts
 ↓
Inspect AWS audit logs
 ↓
Rebuild trusted artifacts
 ↓
Redeploy verified artifacts
```

---

## Senior Scenario: Production Docker Image Must Not Be Rebuilt

Use:

```text
Build
 ↓
Image digest
 ↓
ECR
 ↓
Staging
 ↓
Approval
 ↓
Production
```

Pass the immutable digest between jobs.

Avoid:

```text
Staging build
+
Production rebuild
```

because the production image may no longer be identical to the tested image.

---

## Senior Scenario: Self-Hosted Runner Needs Private Network Access

Architecture:

```text
GitHub Actions
      ↓
Restricted runner group
      ↓
Ephemeral runner
      ↓
Private VPC
 ├── PostgreSQL
 ├── Redis
 ├── Internal APIs
 └── Deployment targets
```

Security controls should include:

```text
Network segmentation
+
Restricted runner access
+
Ephemeral lifecycle
+
Minimal IAM
+
Minimal security-group access
+
No arbitrary PR workloads
```

---

## Senior Architecture Questions

### Why Is `GITHUB_TOKEN` Security Not Enough to Secure GitHub Actions?

Because workflow security spans more than GitHub API permissions.

A compromised job may also access:

```text
Secrets
Filesystem
Network
Docker
Runner credentials
AWS OIDC
Artifacts
```

Therefore:

```text
Token security
≠
Complete CI/CD security
```

---

### What Is the Most Important Permission Design Principle?

Separate jobs by trust and privilege.

For example:

```text
CI
    → read-only

Build
    → read-only

Publish
    → package write

Deploy
    → OIDC + deployment permissions
```

---

### How Do You Minimize Blast Radius?

Use multiple independent controls:

```text
Least privilege
+
Job isolation
+
Environment protection
+
OIDC
+
Runner isolation
+
Action pinning
+
Immutable artifacts
+
Network segmentation
```

If one control fails, the remaining controls limit impact.

---

### Why Is a Privileged Runner More Dangerous Than a Broad Token Alone?

A runner can provide access outside the GitHub API permission model.

For example:

```text
Runner
 ├── Private VPC
 ├── Filesystem
 ├── Docker
 ├── Internal DNS
 └── Cloud tooling
```

Therefore runner compromise can bypass assumptions based solely on `GITHUB_TOKEN`.

---

## Production Security Reference Architecture

```mermaid
flowchart TD
    DEV[Developer] --> PR[Pull Request]

    PR --> CI[Unprivileged CI]
    CI --> LINT[Lint]
    CI --> TEST[Unit / Integration Tests]
    CI --> SCAN[Security Scan]

    LINT --> BUILD[Trusted Build]
    TEST --> BUILD
    SCAN --> BUILD

    BUILD --> ART[Immutable Artifact]
    ART --> PROV[SBOM / Provenance / Attestation]

    PROV --> ECR[ECR]
    ECR --> STAGE[Staging]

    STAGE --> HEALTH[Health Validation]
    HEALTH --> PRODENV[Protected Production Environment]

    PRODENV --> APPROVAL[Approval]
    APPROVAL --> DEPLOY[Privileged Deploy Job]

    DEPLOY --> OIDC[GitHub OIDC]
    OIDC --> STS[AWS STS]
    STS --> IAM[Least-Privilege IAM Role]
    IAM --> PROD[Production]

    PROD --> MONITOR[Monitoring]
    MONITOR --> ROLLBACK[Rollback]
    ROLLBACK --> ART
```

The core principle is:

```text
Untrusted code
    ↓
Low privilege

Trusted build
    ↓
Controlled artifact

Privileged deployment
    ↓
Protected environment

AWS
    ↓
Short-lived identity
+
Least-privilege IAM
```

---

## Security Review Questions for Senior Engineers

When reviewing a GitHub Actions workflow, ask:

### Identity

- Who is executing this workflow?
- Is the source trusted?
- Is the workflow triggered by a fork?

### Authorization

- What can `GITHUB_TOKEN` do?
- Which jobs have write permissions?
- Which job can request OIDC?

### Secrets

- Which secrets are available?
- Why does this job need them?
- Can the job execute untrusted code?

### Actions

- Which third-party actions execute?
- Are references controlled?
- What permissions do those actions inherit?

### Runners

- Where does the code execute?
- Is the runner persistent?
- Can it access private infrastructure?

### Artifacts

- What artifact is produced?
- Is it immutable?
- Can its provenance be established?

### Deployment

- Who can deploy?
- Which environment protects production?
- Can two deployments overlap?

### Recovery

- How are credentials rotated?
- How is a runner replaced?
- How is a known-good artifact restored?

---

## Production Checklist

### `GITHUB_TOKEN`

- [ ] Permissions are explicit.
- [ ] Default permissions are reviewed.
- [ ] Job-level permissions are used for privileged jobs.
- [ ] `write-all` is avoided.
- [ ] Only required permission categories are enabled.

### Pull Requests

- [ ] Fork PRs are treated as untrusted.
- [ ] Production secrets are unavailable to untrusted CI.
- [ ] `pull_request_target` usage is justified.
- [ ] Untrusted input is safely passed to shells.
- [ ] Privileged runners are inaccessible to arbitrary PR workflows.

### Secrets

- [ ] Production secrets are environment-scoped.
- [ ] Secrets are not printed.
- [ ] Secrets are not passed unnecessarily.
- [ ] Secrets are not embedded in Docker images.
- [ ] Long-lived AWS credentials are avoided where OIDC is appropriate.

### AWS

- [ ] `id-token: write` is granted only where required.
- [ ] OIDC trust policies are narrow.
- [ ] IAM permissions are least privilege.
- [ ] Production and non-production roles are appropriately separated.
- [ ] CloudTrail can support investigation.

### Actions

- [ ] Third-party actions are reviewed.
- [ ] Mutable references are avoided for high-trust workflows.
- [ ] SHA pinning is considered.
- [ ] Action dependencies are reviewed.
- [ ] Organization action policies are enforced where appropriate.

### Runners

- [ ] Production runners are restricted.
- [ ] Runner groups enforce access boundaries.
- [ ] Ephemeral runners are considered for sensitive workloads.
- [ ] Private network access is minimized.
- [ ] Docker socket access is controlled.

### Deployments

- [ ] Production environment protection is configured.
- [ ] Deployment concurrency is configured.
- [ ] Immutable artifacts are promoted.
- [ ] Health validation exists.
- [ ] Rollback is supported.

---

## Key Takeaways

- **`GITHUB_TOKEN` is an authentication mechanism, not a blanket authorization grant; explicit workflow- and job-level permissions determine what the token can do.**
- **Use least privilege and privilege isolation: unprivileged CI jobs should generally use `contents: read`, while only dedicated deployment jobs receive capabilities such as `id-token: write`.**
- **`GITHUB_TOKEN` security must be combined with pull-request trust boundaries, secret isolation, third-party action controls, runner isolation, and safe handling of untrusted GitHub input.**
- **For AWS deployments, prefer GitHub OIDC → STS → least-privilege IAM roles instead of long-lived AWS access keys, and restrict the IAM trust relationship to the intended repository and deployment context.**
- **The strongest production design separates untrusted CI from privileged deployment and combines minimal permissions, protected environments, immutable artifacts, concurrency controls, and auditable recovery procedures.**