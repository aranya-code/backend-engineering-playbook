# 01- GitHub CLI Basics

## Overview

GitHub CLI (`gh`) is the command-line interface for GitHub. For CI/CD engineering, it provides an operational interface for GitHub Actions workflows, workflow runs, logs, artifacts, secrets, variables, environments, repositories, and releases.

The important distinction is:

```text
Git CLI
    ↓
Git repository operations

GitHub CLI
    ↓
GitHub platform operations
    ├── Actions
    ├── Pull Requests
    ├── Issues
    ├── Releases
    ├── Secrets
    └── Repository configuration
```

For backend engineers, `gh` becomes particularly useful when GitHub Actions must be operated repeatedly from terminals, scripts, incident runbooks, CI tooling, or deployment automation.

Typical production tasks include:

- Listing workflow runs.
- Inspecting failed jobs.
- Downloading workflow logs.
- Rerunning failed jobs.
- Manually triggering deployments.
- Inspecting artifacts.
- Managing repository secrets and variables.
- Inspecting environments.
- Managing releases.
- Automating operational workflows.

This document focuses on GitHub CLI capabilities that directly support GitHub Actions and CI/CD operations rather than attempting to cover GitHub CLI as a general-purpose GitHub course.

---

## GitHub CLI vs Git

Git and GitHub CLI solve different problems.

| Tool | Primary Responsibility |
|---|---|
| `git` | Local repository and version-control operations |
| `gh` | GitHub platform and API operations |
| `aws` | AWS infrastructure and cloud operations |
| `docker` | Container lifecycle and image operations |
| `kubectl` | Kubernetes operations |

For example:

```bash
git push origin main
```

pushes Git commits.

While:

```bash
gh run list
```

queries GitHub Actions workflow runs.

A production deployment investigation may use all of them:

```text
git
 ↓
GitHub
 ↓
gh
 ↓
GitHub Actions
 ↓
aws
 ↓
ECS / ECR / EC2
```

---

## Installing GitHub CLI

GitHub CLI is distributed for major operating systems.

After installation, verify it:

```bash
gh --version
```

Example output:

```text
gh version 2.x.x
```

The exact version depends on the installed release.

---

## Authentication

Authenticate the CLI with:

```bash
gh auth login
```

The interactive flow generally asks for:

- GitHub.com vs another GitHub host.
- Git protocol.
- Authentication method.

For GitHub.com, browser-based authentication is usually the simplest approach.

Verify authentication:

```bash
gh auth status
```

A successful status should identify the authenticated account and host.

---

## Authentication Model

GitHub CLI operates using GitHub authentication credentials and permissions.

The important architecture is:

```text
Developer / Automation
        ↓
GitHub CLI
        ↓
GitHub API
        ↓
Repository / Actions / Release / Environment
```

Authentication does not automatically imply authorization for every operation.

For example:

```text
Authenticated
     +
Insufficient Permission
     =
Operation Fails
```

This distinction is important when troubleshooting `403` or authorization failures.

---

## Authentication Security

Do not treat CLI authentication credentials like ordinary configuration.

Avoid:

```bash
echo "$GH_TOKEN"
```

or storing tokens in source code.

Prefer:

- Interactive authentication.
- Secure credential storage.
- Short-lived credentials where supported.
- Environment injection from a secure secret store for automation.
- Least privilege.

For CI/CD automation, avoid creating broad personal credentials merely to make a workflow succeed.

---

## `GH_TOKEN`

GitHub CLI can use the `GH_TOKEN` environment variable.

Example:

```bash
export GH_TOKEN="$CI_GITHUB_TOKEN"
gh run list
```

On PowerShell:

```powershell
$env:GH_TOKEN = $CI_GITHUB_TOKEN
gh run list
```

The token should come from a secure credential mechanism.

Never commit it into:

```text
.env
workflow files
shell scripts
Dockerfiles
source code
```

---

## GitHub CLI Command Structure

Most commands follow:

```text
gh <resource> <command> [flags]
```

Examples:

```bash
gh workflow list
gh run list
gh run view <run-id>
gh release list
```

The resource identifies what you are operating on.

---

## Discovering Commands

GitHub CLI includes built-in help:

```bash
gh help
```

For a resource:

```bash
gh run --help
```

For a specific operation:

```bash
gh run view --help
```

This is useful because CLI syntax and available flags can change between releases.

---

## Repository Context

Many `gh` commands automatically use the current Git repository.

Check the current repository:

```bash
gh repo view
```

For an explicit repository:

```bash
gh run list --repo OWNER/REPOSITORY
```

Example:

```bash
gh run list --repo acme/orders-api
```

This is particularly useful for platform engineers operating multiple repositories.

---

## Repository Operations

Inspect the current repository:

```bash
gh repo view
```

Open it in a browser:

```bash
gh repo view --web
```

List repositories for the authenticated account:

```bash
gh repo list
```

Clone a repository:

```bash
gh repo clone acme/orders-api
```

For CI/CD operations, repository commands are mainly useful for identifying the correct repository before operating workflows.

---

## GitHub Actions CLI Model

GitHub CLI exposes Actions primarily through:

```text
gh workflow
gh run
```

The distinction is important.

### Workflow

A workflow is the configured automation definition.

```text
.github/workflows/ci.yml
```

### Run

A run is one execution of that workflow.

```text
ci.yml
   ↓
Run #12345
```

Therefore:

```bash
gh workflow list
```

answers:

> What workflows exist?

while:

```bash
gh run list
```

answers:

> What executions have occurred?

---

## Listing Workflows

```bash
gh workflow list
```

Typical output contains information such as:

```text
ID       NAME       STATE    ID
CI       CI         active   ...
Deploy   Deploy     active   ...
```

For a specific repository:

```bash
gh workflow list --repo acme/orders-api
```

---

## Workflow Status

A workflow can be:

- Active.
- Disabled.
- Configured but not recently executed.

The workflow definition is not the same thing as its latest execution.

Always distinguish:

```text
Workflow Configuration
```

from:

```text
Workflow Run
```

when diagnosing problems.

---

## Running a Workflow Manually

For workflows supporting `workflow_dispatch`:

```bash
gh workflow run deploy.yml
```

Specify a branch:

```bash
gh workflow run deploy.yml --ref main
```

If the workflow defines inputs, provide them according to the CLI options supported by the installed GitHub CLI version.

Conceptually:

```text
Operator
   ↓
gh workflow run
   ↓
workflow_dispatch
   ↓
GitHub Actions
   ↓
Deployment
```

---

## Manual Deployment Example

A deployment workflow might contain:

```yaml
name: Deploy

on:
  workflow_dispatch:
    inputs:
      environment:
        description: Target environment
        required: true
        type: choice
        options:
          - staging
          - production
```

An operator can then trigger the workflow manually.

The important production consideration is that manual execution should still respect:

- Environment protection.
- Permissions.
- Deployment concurrency.
- Artifact selection.
- Approval requirements.

Manual triggering should not bypass security controls.

---

## Listing Workflow Runs

```bash
gh run list
```

For a specific repository:

```bash
gh run list --repo acme/orders-api
```

Limit results:

```bash
gh run list --limit 20
```

Filter by workflow:

```bash
gh run list --workflow ci.yml
```

Filter by branch:

```bash
gh run list --branch main
```

---

## Useful Run Filters

Common operational filters include:

```bash
gh run list --workflow ci.yml
gh run list --branch main
gh run list --status failure
gh run list --status success
```

This is useful during incident investigation.

For example:

```bash
gh run list \
  --workflow deploy.yml \
  --branch main \
  --status failure
```

can quickly identify recent production deployment failures.

---

## Inspecting a Workflow Run

```bash
gh run view <run-id>
```

Example:

```bash
gh run view 123456789
```

This is usually the first command after identifying a suspicious run.

It helps answer:

- What workflow executed?
- Which commit triggered it?
- What was the overall status?
- Which jobs ran?
- Which jobs failed?
- What event triggered the run?

---

## Inspecting Failed Jobs

Use:

```bash
gh run view <run-id>
```

Then identify the failed job.

The troubleshooting principle is:

```text
Run
 ↓
Failed Job
 ↓
Failed Step
 ↓
Actual Command
```

Do not stop at:

```text
Workflow failed
```

That is a status, not a root cause.

---

## Viewing Logs

View run logs:

```bash
gh run view <run-id> --log
```

For failed jobs only:

```bash
gh run view <run-id> --log-failed
```

This is especially useful during CI incidents because it avoids manually opening every job in the browser.

---

## Downloading Logs

For automation or deeper analysis, workflow logs can be downloaded using GitHub CLI capabilities available in the installed version.

When investigating a failure, preserve the relevant logs before rerunning if the original evidence may be lost or changed.

---

## Rerunning a Workflow

Rerun an entire workflow:

```bash
gh run rerun <run-id>
```

Rerun only failed jobs:

```bash
gh run rerun <run-id> --failed
```

This distinction matters.

### Full Rerun

Useful when:

- The failure may be transient.
- Multiple dependent jobs need to execute again.

### Failed-Only Rerun

Useful when:

- Earlier successful work is still valid.
- The failure is isolated.
- Re-running expensive jobs is unnecessary.

---

## Rerun Safety

A rerun is not automatically safe.

Before rerunning a production workflow, determine whether it performs:

- Database migrations.
- Infrastructure changes.
- Production deployment.
- Data modification.
- Release creation.
- External API calls.

For deployments, combine reruns with idempotency and deployment concurrency.

---

## Workflow Run Failure Investigation

A practical sequence is:

```text
1. List recent runs
2. Identify failed run
3. Inspect run
4. Identify failed job
5. Inspect logs
6. Classify failure
7. Determine transient vs deterministic
8. Decide whether rerun is safe
9. Rerun if appropriate
10. Validate result
```

Example:

```bash
gh run list --workflow deploy.yml --status failure --limit 10
gh run view <run-id>
gh run view <run-id> --log-failed
```

---

## Workflow Failure Classification

| Failure | Typical Response |
|---|---|
| Network timeout | Investigate and potentially retry |
| Test failure | Fix application/test issue |
| Missing secret | Correct configuration |
| `403` | Inspect permissions |
| OIDC failure | Inspect IAM trust and token permissions |
| Runner unavailable | Investigate runner infrastructure |
| Docker build failure | Inspect Docker/build context |
| ECR push failure | Inspect AWS/ECR permissions |
| Deployment health failure | Investigate runtime |
| Concurrency conflict | Inspect deployment controls |

---

## JSON Output

GitHub CLI supports structured output for many commands.

Example:

```bash
gh run list --json databaseId,status,conclusion
```

This is valuable for automation because scripts should avoid parsing human-readable output when structured data is available.

Example:

```bash
gh run list \
  --workflow deploy.yml \
  --json databaseId,status,conclusion,headSha
```

Conceptually:

```text
gh
 ↓
Structured JSON
 ↓
jq / Python / Automation
```

---

## Using `jq`

If JSON output is available:

```bash
gh run list \
  --workflow deploy.yml \
  --json databaseId,status,conclusion \
  --limit 20 | jq
```

Filter failures:

```bash
gh run list \
  --workflow deploy.yml \
  --json databaseId,conclusion \
  --limit 20 |
  jq '.[] | select(.conclusion == "failure")'
```

This is useful for operational scripts and CI dashboards.

---

## CI/CD Automation With JSON

A platform script might:

```text
Query workflow runs
      ↓
Filter failed production deployments
      ↓
Extract run IDs
      ↓
Inspect logs
      ↓
Generate incident information
```

Structured output makes this much more reliable than parsing terminal formatting.

---

## Workflow Run Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Queued
    Queued --> InProgress
    InProgress --> Success
    InProgress --> Failure
    InProgress --> Cancelled
    Failure --> Rerun
    Rerun --> Queued
    Success --> [*]
    Cancelled --> [*]
```

Understanding the run lifecycle helps distinguish:

- Queued.
- In progress.
- Completed successfully.
- Failed.
- Cancelled.

---

## Monitoring Queue Time

A workflow may appear healthy while jobs spend excessive time waiting for runners.

Operationally distinguish:

```text
Queue Time
+
Execution Time
=
Total Workflow Time
```

If execution time is stable but queue time increases, investigate:

- Runner capacity.
- Autoscaling.
- Matrix size.
- Concurrent workflows.
- Runner groups.
- Organization limits.

---

## Workflow Duration

Inspect recent runs:

```bash
gh run list --workflow ci.yml --limit 20
```

For deeper analysis, combine structured output with timestamps where available.

Track:

```text
Median Duration
P95 Duration
Queue Time
Failure Rate
```

Do not optimize workflow duration by removing necessary validation.

---

## Artifacts

Workflow artifacts are useful for:

- Test reports.
- Coverage reports.
- Build outputs.
- Debug files.
- Diagnostic logs.

Inspect a run:

```bash
gh run view <run-id>
```

The artifact information can then be used to identify what was produced by that execution.

---

## Artifact vs Cache

These are different concepts.

| Artifact | Cache |
|---|---|
| Deliberately produced output | Performance optimization |
| Often consumed by later jobs | Used to avoid repeated downloads/builds |
| Can represent release material | Can be safely regenerated |
| Important for debugging/recovery | Should not be a source of truth |
| Often retained intentionally | May expire or miss |

Never use a cache as the authoritative production artifact.

---

## Artifact Architecture

```text
Build
 ↓
Artifact
 ↓
Validation
 ↓
Promotion
 ↓
Deployment
```

For Docker:

```text
Build
 ↓
Image
 ↓
ECR
 ↓
Digest
 ↓
Staging
 ↓
Production
```

---

## Secrets Management

GitHub CLI can manage repository secrets.

List secrets:

```bash
gh secret list
```

Set a secret interactively:

```bash
gh secret set DATABASE_URL
```

Set from standard input:

```bash
printf '%s' "$DATABASE_URL" | gh secret set DATABASE_URL
```

The second pattern is useful in automation, provided the source itself is secure.

---

## Secret Scope

Secrets may exist at different scopes.

Conceptually:

```text
Organization
    ↓
Repository
    ↓
Environment
```

Environment secrets are particularly important for production deployments.

For example:

```text
staging
    └── STAGING_DATABASE_URL

production
    └── PRODUCTION_DATABASE_URL
```

Do not reuse production secrets merely to simplify CI.

---

## Secret Security

Never do:

```bash
gh secret set DATABASE_URL --body "postgres://user:password@..."
```

in a shell history-sensitive environment if the command exposes the secret to shell history or process inspection.

Prefer stdin or an interactive mechanism.

Also avoid:

```bash
echo "$SECRET"
```

during troubleshooting.

---

## Environment Management

GitHub environments provide deployment boundaries.

Typical environments:

```text
development
staging
production
```

They can contain:

- Environment secrets.
- Environment variables.
- Protection rules.
- Required reviewers.
- Deployment history.

The exact controls available depend on the repository and GitHub plan/configuration.

---

## Environment Operations

GitHub CLI provides environment-related commands through the appropriate repository management interfaces.

For production operations, use the CLI primarily to inspect and automate environment configuration while keeping sensitive values out of scripts and logs.

A useful operational model is:

```text
Repository
   ↓
Environment
   ↓
Protection
   ↓
Deployment
```

---

## Variables

Repository variables can be managed through GitHub CLI.

List variables:

```bash
gh variable list
```

Set a variable:

```bash
gh variable set APP_REGION --body "ap-south-1"
```

Variables are appropriate for non-sensitive configuration.

Do not store credentials or tokens in variables.

Use secrets for sensitive values.

---

## Secrets vs Variables

| Property | Secret | Variable |
|---|---|---|
| Sensitive value | Yes | No |
| Intended for credentials | Yes | No |
| Safe to display | No | Usually |
| Environment-specific | Yes | Yes |
| Typical examples | API token, password | Region, feature name |

A database hostname may be a variable.

A database password should be a secret.

---

## Releases

GitHub CLI can manage releases.

List releases:

```bash
gh release list
```

View a release:

```bash
gh release view v2.4.0
```

Create a release:

```bash
gh release create v2.4.0
```

A release can be associated with an immutable Git tag and release artifacts.

---

## Release Architecture

A production release flow can be:

```text
Commit
 ↓
CI
 ↓
Tests
 ↓
Build
 ↓
Artifact
 ↓
Git Tag
 ↓
GitHub Release
 ↓
Environment Promotion
```

GitHub CLI can automate operational parts of this process.

---

## Release Artifacts

A release can contain files such as:

```text
application.tar.gz
checksums.txt
SBOM.json
release-notes.md
```

For production systems, release artifacts should have traceable provenance.

---

## Semantic Versioning

Typical versions:

```text
2.3.0
2.3.1
3.0.0
```

A release command may therefore be:

```bash
gh release create v2.3.1
```

The release process should have a clearly defined version source of truth.

---

## Pull Request Operations Relevant to CI/CD

Although this document focuses on Actions, pull requests are often operational inputs to CI.

List pull requests:

```bash
gh pr list
```

View a pull request:

```bash
gh pr view <number>
```

This can help investigate:

- Which change triggered a workflow.
- Which PR contains a deployment change.
- Which checks are associated with a change.

---

## Repository Checks

A pull request's checks are part of the CI control plane.

The useful operational model is:

```text
Pull Request
    ↓
GitHub Actions
    ↓
Checks
    ↓
Merge Decision
```

When investigating a PR failure, inspect the associated workflow run rather than treating the check status as the complete diagnostic.

---

## CI/CD Operational Workflow

A typical operator workflow is:

```text
Identify Repository
        ↓
List Workflows
        ↓
List Recent Runs
        ↓
Inspect Failed Run
        ↓
Inspect Logs
        ↓
Identify Failure Domain
        ↓
Correct / Rerun
        ↓
Validate
```

Commands:

```bash
gh repo view
gh workflow list
gh run list --limit 20
gh run view <run-id>
gh run view <run-id> --log-failed
```

---

## Production Deployment Investigation

Suppose a production deployment failed.

Start with:

```bash
gh run list \
  --workflow deploy.yml \
  --branch main \
  --status failure \
  --limit 10
```

Inspect:

```bash
gh run view <run-id>
```

Then:

```bash
gh run view <run-id> --log-failed
```

If the workflow uses AWS:

```bash
aws sts get-caller-identity
```

If it uses Docker:

```bash
docker buildx inspect
```

The CLI tools complement one another:

```text
gh
 ↓
GitHub Actions State

aws
 ↓
AWS State

docker
 ↓
Container State
```

---

## Production Incident Workflow

During an incident:

### Identify

```bash
gh run list --workflow deploy.yml --limit 20
```

### Inspect

```bash
gh run view <run-id>
```

### Extract Failure Evidence

```bash
gh run view <run-id> --log-failed
```

### Determine Whether Rerun Is Safe

Check:

- Deployment state.
- Concurrency.
- Database migrations.
- Artifact identity.
- External side effects.

### Rerun if Appropriate

```bash
gh run rerun <run-id> --failed
```

### Validate

Confirm:

- Workflow result.
- Deployment state.
- Application health.
- Artifact identity.

---

## GitHub CLI in CI

GitHub CLI can also be installed inside a workflow when the workflow needs to perform GitHub operations.

Example:

```yaml
- name: Inspect workflow
  env:
    GH_TOKEN: ${{ github.token }}
  run: |
    gh run view "$GITHUB_RUN_ID"
```

The important security principle is to give the workflow only the permissions required for the operation.

---

## `GITHUB_TOKEN` and `gh`

GitHub CLI can use the workflow's `GITHUB_TOKEN` through `GH_TOKEN`.

Example:

```yaml
permissions:
  actions: read

steps:
  - name: Inspect workflow
    env:
      GH_TOKEN: ${{ github.token }}
    run: |
      gh run view "$GITHUB_RUN_ID"
```

The required permissions depend on the GitHub API operation.

Do not assume that authentication alone grants access.

---

## GitHub CLI and OIDC

GitHub CLI itself does not replace AWS OIDC.

The boundaries remain:

```text
GitHub Actions
    ↓
GitHub authentication
    ↓
AWS OIDC
    ↓
STS
    ↓
AWS IAM
```

Use the appropriate authentication mechanism for each platform.

---

## Repository Management

Repository-level operations can be useful during platform automation.

Examples:

```bash
gh repo view
gh repo list
```

For CI/CD engineering, repository management is relevant when building automation that:

- Inspects repositories.
- Applies standards.
- Audits workflow configuration.
- Identifies repositories using older workflows.

Avoid using repository-wide automation without appropriate permissions and change controls.

---

## Operational Scripting

A useful shell script can combine `gh` commands:

```bash
#!/usr/bin/env bash

set -euo pipefail

workflow="deploy.yml"

gh run list \
  --workflow "$workflow" \
  --branch main \
  --limit 10
```

For more complex automation, structured JSON is preferable:

```bash
gh run list \
  --workflow "$workflow" \
  --json databaseId,status,conclusion,headSha \
  --limit 10
```

This avoids brittle text parsing.

---

## Python Automation

GitHub CLI can also be used from Python when shelling out is appropriate.

```python
from __future__ import annotations

import json
import subprocess


result = subprocess.run(
    [
        "gh",
        "run",
        "list",
        "--workflow",
        "ci.yml",
        "--json",
        "databaseId,status,conclusion",
        "--limit",
        "20",
    ],
    check=True,
    capture_output=True,
    text=True,
)

runs = json.loads(result.stdout)

for run in runs:
    print(
        run["databaseId"],
        run["status"],
        run["conclusion"],
    )
```

For larger applications, prefer a proper API integration when that provides stronger control and error handling.

---

## Error Handling in Automation

Do not assume that a successful CLI process means the desired business operation completed.

For example:

```text
gh command succeeds
      ↓
Workflow request accepted
      ↓
Workflow executes asynchronously
      ↓
Deployment may still fail
```

Therefore distinguish:

```text
Command Success
```

from:

```text
Workflow Success
```

This distinction is critical for deployment automation.

---

## Asynchronous Workflow Execution

Consider:

```bash
gh workflow run deploy.yml --ref main
```

The command initiates the workflow.

It does not necessarily mean:

```text
Production deployment succeeded
```

The operational flow is:

```text
Trigger Accepted
      ↓
Run Created
      ↓
Run Queued
      ↓
Run Executing
      ↓
Run Completed
      ↓
Deployment Validated
```

Automation that requires a deployment result must inspect the resulting run.

---

## Polling Workflow Status

A deployment automation can:

```text
Trigger workflow
      ↓
Find run
      ↓
Poll status
      ↓
Wait for completion
      ↓
Inspect conclusion
      ↓
Return success/failure
```

Avoid uncontrolled polling loops.

Use:

- Timeouts.
- Backoff.
- Maximum attempts.
- Clear failure reporting.

---

## CI/CD Command Reference

| Task | Command |
|---|---|
| Authenticate | `gh auth login` |
| Check auth | `gh auth status` |
| List workflows | `gh workflow list` |
| Run workflow | `gh workflow run <workflow>` |
| List runs | `gh run list` |
| View run | `gh run view <run-id>` |
| View failed logs | `gh run view <run-id> --log-failed` |
| View all logs | `gh run view <run-id> --log` |
| Rerun run | `gh run rerun <run-id>` |
| Rerun failed jobs | `gh run rerun <run-id> --failed` |
| List secrets | `gh secret list` |
| Set secret | `gh secret set <name>` |
| List variables | `gh variable list` |
| Set variable | `gh variable set <name>` |
| List releases | `gh release list` |
| View release | `gh release view <tag>` |
| Repository view | `gh repo view` |
| Repository list | `gh repo list` |

---

## Common Mistakes

### Confusing `git` and `gh`

```bash
git log
```

operates on Git history.

```bash
gh run list
```

operates on GitHub Actions.

### Treating a Trigger as a Successful Deployment

```bash
gh workflow run deploy.yml
```

only initiates execution.

Inspect the resulting run.

### Rerunning Without Understanding Side Effects

A deployment rerun can repeat:

- Migrations.
- Infrastructure changes.
- External API operations.
- Release creation.

### Printing Secrets

Never use CLI commands that expose credentials unnecessarily.

### Parsing Human Output

Prefer:

```bash
gh ... --json ...
```

over brittle text parsing.

### Using Excessive Permissions

A GitHub token should have only the permissions required for the operation.

### Ignoring Repository Context

A command can operate against the wrong repository if automation relies on implicit context.

Use:

```bash
--repo OWNER/REPOSITORY
```

when operating across repositories.

---

## Security Considerations

GitHub CLI is an operational tool and therefore can become a privileged interface.

Protect:

- Authentication credentials.
- `GH_TOKEN`.
- Repository administration capabilities.
- Production workflow triggers.
- Environment configuration.
- Secrets.
- Release operations.

For production automation:

```text
Least Privilege
+
Explicit Repository
+
Structured Output
+
Auditing
+
Timeouts
+
Idempotency
```

should be preferred.

---

## Scalability Considerations

At small scale:

```text
Developer
 ↓
gh
 ↓
Repository
```

At organizational scale:

```text
Platform Automation
       ↓
GitHub CLI / API
       ↓
Many Repositories
       ↓
Many Workflows
```

Avoid writing scripts that assume:

- One repository.
- One workflow.
- One branch.
- One environment.
- One deployment.

Use explicit parameters and structured data.

---

## Reliability Considerations

Reliable CLI automation should:

- Use explicit repository identifiers.
- Use structured JSON output.
- Validate command results.
- Handle asynchronous execution.
- Implement timeouts.
- Implement bounded retries.
- Avoid secret exposure.
- Preserve workflow run IDs.
- Record artifact and commit identities.

Example:

```text
Repository
+
Workflow
+
Run ID
+
Commit SHA
+
Artifact Digest
```

provides strong operational traceability.

---

## Cost Considerations

GitHub CLI itself is generally not the main CI/CD cost driver.

The cost impact comes from what it triggers.

For example:

```bash
gh workflow run expensive-e2e.yml
```

may start:

- Multiple runners.
- Large matrix jobs.
- Integration environments.
- Docker builds.
- AWS infrastructure.

Therefore operational automation should avoid accidental repeated execution.

---

## Disaster Recovery Considerations

GitHub CLI can help operate recovery workflows, but recovery should not depend solely on interactive CLI access.

Maintain:

- Documented recovery workflows.
- Known-good artifacts.
- Deployment metadata.
- Rollback procedures.
- Appropriate credentials.
- Break-glass procedures.

A recovery process should remain understandable even when normal automation is degraded.

---

## Interview Scenarios

### What Is the Difference Between `git` and `gh`?

`git` operates on Git repositories and version history.

`gh` operates against GitHub's platform capabilities, including Actions, workflows, runs, releases, secrets, and repositories.

### How Would You Investigate a Failed GitHub Actions Deployment From the CLI?

Use:

```bash
gh run list
gh run view <run-id>
gh run view <run-id> --log-failed
```

Then classify the failure before deciding whether to rerun.

### Does `gh workflow run` Mean the Deployment Succeeded?

No.

It means the workflow was requested.

The workflow executes asynchronously and must be inspected until completion.

### How Would You Safely Rerun a Production Deployment?

First determine:

- Whether the deployment is idempotent.
- Whether another deployment is running.
- Whether migrations were executed.
- Which artifact is being deployed.
- Whether the workflow has appropriate concurrency controls.

Then rerun only when the operation is understood to be safe.

### Why Use `--json`?

Structured output is more reliable for automation than parsing human-readable terminal output.

### How Would You Use `gh` in a Python Automation Tool?

Invoke it with `subprocess` when appropriate, use structured JSON output, validate exit status, parse the response, and implement timeout/error handling.

### How Can `gh` Help During a CI Incident?

It can rapidly:

```text
List runs
 ↓
Identify failure
 ↓
Inspect logs
 ↓
Rerun safely
 ↓
Validate completion
```

This reduces dependence on manually navigating the GitHub web interface.

---

## Production CLI Workflow

A practical deployment operator workflow is:

```mermaid
sequenceDiagram
    participant O as Operator
    participant GH as GitHub CLI
    participant GA as GitHub Actions
    participant AWS as AWS

    O->>GH: gh workflow run deploy.yml
    GH->>GA: Trigger workflow
    GA-->>GH: Run created
    O->>GH: gh run view <run-id>
    GH->>GA: Query status
    GA-->>GH: Running
    O->>GH: Inspect logs
    GH->>GA: Query logs
    GA-->>GH: Logs
    GA->>AWS: Deploy
    AWS-->>GA: Deployment result
    O->>GH: Inspect final run
    GH->>GA: Query conclusion
    GA-->>GH: Success / Failure
```

This illustrates the critical distinction between **triggering** an operation and **observing its completion**.

---

## Practical Operational Checklist

### Authentication

- [ ] `gh auth status` succeeds.
- [ ] Correct GitHub host is selected.
- [ ] Automation credentials are protected.
- [ ] Token permissions are minimal.

### Workflow Operations

- [ ] Correct repository selected.
- [ ] Correct workflow selected.
- [ ] Correct branch/ref selected.
- [ ] Inputs validated.
- [ ] Workflow run ID captured.

### Failure Investigation

- [ ] Run status inspected.
- [ ] Failed job identified.
- [ ] Failed logs inspected.
- [ ] Failure domain classified.
- [ ] Rerun safety evaluated.

### Deployment Operations

- [ ] Artifact identity known.
- [ ] Deployment concurrency checked.
- [ ] Environment protection respected.
- [ ] Health validation performed.
- [ ] Rollback path understood.

### Automation

- [ ] Structured JSON used where practical.
- [ ] Timeouts configured.
- [ ] Retries bounded.
- [ ] Secrets never printed.
- [ ] Asynchronous execution handled explicitly.

## Key Takeaways

- **GitHub CLI (`gh`) is the operational command-line interface for GitHub capabilities such as Actions workflows, workflow runs, logs, artifacts, secrets, variables, environments, and releases.**
- **`gh workflow` operates on workflow definitions, while `gh run` operates on individual workflow executions; distinguishing the two is fundamental to CI/CD troubleshooting.**
- **Triggering a workflow is not the same as successful deployment—production automation must inspect the resulting run, logs, conclusion, and deployment health.**
- **Use structured JSON output, explicit repository context, least-privilege credentials, bounded retries, and careful secret handling when building reliable CLI automation.**
- **During incidents, a practical sequence is: list runs → inspect the run → inspect failed logs → classify the failure → determine whether rerun is safe → rerun if appropriate → validate the final state.**