# 08- Actions

## Overview

GitHub Actions are reusable automation components that encapsulate CI/CD logic inside a workflow. An action can perform a focused operation such as checking out source code, installing a runtime, authenticating with a registry, uploading an artifact, building a Docker image, or interacting with an external API.

Actions are one layer of the GitHub Actions execution model:

```text
Workflow
   │
   ├── Job
   │    │
   │    ├── Step
   │    │    ├── run: shell command
   │    │    └── uses: action
   │    │
   │    └── Runner
   │
   └── Trigger
```

A useful distinction is:

- **Workflow** — defines the automation process.
- **Job** — defines an execution unit and its dependencies.
- **Step** — defines an individual operation inside a job.
- **Action** — reusable implementation that a step can invoke.
- **Runner** — machine that executes the job.

Actions become especially important as CI/CD systems grow. Instead of duplicating checkout, authentication, dependency setup, artifact handling, Docker builds, AWS authentication, or deployment logic across dozens of workflows, those operations can be packaged and reused.

A production GitHub Actions system commonly combines official actions, trusted third-party actions, organization-owned actions, composite actions, and reusable workflows. The existing CI/CD material already uses actions such as checkout, Python setup, artifact upload, and Docker build/push as building blocks for application pipelines. :chatgpt-content-reference{index="0"}

The engineering goal is not to maximize the number of actions used. It is to create automation that is **reusable, auditable, secure, versioned, testable, and predictable**.

---

## What Is a GitHub Action?

An action is a reusable unit of automation that can be executed from a workflow step using the `uses` keyword.

For example:

```yaml
steps:
  - name: Checkout source
    uses: actions/checkout@v4

  - name: Set up Python
    uses: actions/setup-python@v5
    with:
      python-version: "3.12"
```

The workflow does not need to implement Git checkout or Python runtime installation itself. Those operations are delegated to reusable actions.

Conceptually:

```text
Workflow Step
     │
     │ uses:
     ▼
GitHub Action
     │
     ├── Inputs
     ├── Implementation
     ├── Environment
     └── Outputs
```

An action normally defines:

- Metadata
- Inputs
- Outputs
- Implementation
- Runtime requirements
- Execution behavior

The metadata is commonly stored in:

```text
action.yml
```

or:

```text
action.yaml
```

---

## Why Actions Exist

Without actions, workflows quickly become repetitive.

Consider a repository with 20 workflows. If every workflow independently implements:

```text
Checkout
Install Python
Configure credentials
Build Docker image
Upload artifact
```

then each workflow becomes responsible for maintaining the same logic.

Actions provide reuse at the **step level**.

```text
Without Actions

Workflow A ── checkout implementation
Workflow B ── checkout implementation
Workflow C ── checkout implementation
Workflow D ── checkout implementation
```

With an action:

```text
                 ┌── Workflow A
                 │
actions/checkout ├── Workflow B
                 │
                 ├── Workflow C
                 │
                 └── Workflow D
```

This improves:

- Consistency
- Maintainability
- Reusability
- Version control
- Standardization
- Developer productivity

However, abstraction also introduces a trust boundary. An action executes code with the permissions available to its job. Therefore, action reuse must be treated as a software supply-chain decision.

---

## Action Types

GitHub Actions supports three primary implementation models:

| Type | Implementation | Execution model | Best suited for |
|---|---|---|---|
| Composite | `action.yml` + shell/other steps | Runs steps within the caller job | Reusable step sequences |
| JavaScript | `action.yml` + Node.js | Runs JavaScript action code | API integration and complex logic |
| Docker | `action.yml` + `Dockerfile` | Runs inside a Docker container | Linux-oriented isolated tooling |

The important architectural distinction is that **composite actions package steps**, while JavaScript and Docker actions package executable implementations.

---

## Action Invocation

An action is normally invoked with:

```yaml
steps:
  - name: Checkout
    uses: actions/checkout@v4
```

An action can also receive inputs:

```yaml
steps:
  - name: Set up Python
    uses: actions/setup-python@v5
    with:
      python-version: "3.12"
      cache: "pip"
```

The general structure is:

```yaml
- name: Action description
  uses: OWNER/REPOSITORY@VERSION
  with:
    input-name: value
```

For an action located inside the same repository:

```yaml
- name: Run internal action
  uses: ./.github/actions/setup-python
```

This is useful for organization-specific automation.

---

## Action References and Versioning

Actions are referenced using a repository and a ref:

```yaml
uses: actions/checkout@v4
```

The ref can represent:

- Major version
- Minor version
- Exact version
- Git tag
- Branch
- Commit SHA

Examples:

```yaml
uses: actions/checkout@v4
```

```yaml
uses: actions/checkout@v4.2.2
```

```yaml
uses: actions/checkout@<commit-sha>
```

### Versioning Trade-offs

| Reference | Convenience | Reproducibility | Supply-chain control |
|---|---:|---:|---:|
| Branch | High | Low | Low |
| Major tag | High | Medium | Medium |
| Exact release | Medium | High | High |
| Commit SHA | Low | Highest | Highest |

For production environments, security-sensitive organizations often prefer immutable SHA pinning, sometimes combined with tooling that maps the SHA to a known release.

A version reference such as:

```yaml
uses: actions/checkout@v4
```

is convenient because compatible releases can receive updates.

A SHA-pinned reference:

```yaml
uses: actions/checkout@<known-commit-sha>
```

provides stronger immutability.

The trade-off is maintenance. SHA pinning requires an intentional update process.

---

## Action Metadata

An action is described by `action.yml`.

A simplified composite action can look like:

```yaml
name: Setup Python Environment
description: Configure Python and install project dependencies

inputs:
  python-version:
    description: Python version to install
    required: false
    default: "3.12"

  requirements-file:
    description: Dependency file
    required: false
    default: "requirements.txt"

runs:
  using: composite
  steps:
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ inputs.python-version }}

    - name: Install dependencies
      shell: bash
      run: |
        python -m pip install --upgrade pip
        python -m pip install -r "${{ inputs.requirements-file }}"
```

The metadata describes:

```text
Inputs
   ↓
Action Implementation
   ↓
Outputs
```

---

## Inputs

Inputs make actions configurable without duplicating their implementation.

Example:

```yaml
inputs:
  environment:
    description: Deployment environment
    required: true

  python-version:
    description: Python version
    required: false
    default: "3.12"
```

The workflow supplies values:

```yaml
- name: Configure application
  uses: ./.github/actions/configure-app
  with:
    environment: staging
    python-version: "3.12"
```

Inside a composite action:

```yaml
run: echo "Deploying to ${{ inputs.environment }}"
```

### Input Design Principles

Good action inputs should:

- Have clear names.
- Have useful descriptions.
- Define whether they are required.
- Provide safe defaults where appropriate.
- Avoid unnecessary configuration.
- Validate assumptions where practical.
- Avoid accepting arbitrary shell fragments unless absolutely necessary.

An action with 25 inputs is often an abstraction problem rather than a flexible design.

---

## Outputs

Actions can expose values to subsequent workflow steps.

A composite action can write an output through `$GITHUB_OUTPUT`.

Example:

```yaml
name: Generate Image Tag
description: Generate an immutable image tag

outputs:
  image-tag:
    description: Generated image tag
    value: ${{ steps.generate.outputs.image-tag }}

runs:
  using: composite
  steps:
    - name: Generate tag
      id: generate
      shell: bash
      run: |
        echo "image-tag=${GITHUB_SHA}" >> "$GITHUB_OUTPUT"
```

The caller can consume the output:

```yaml
- name: Generate image tag
  id: image
  uses: ./.github/actions/generate-image-tag

- name: Display image tag
  run: echo "Tag: ${{ steps.image.outputs.image-tag }}"
```

The important data flow is:

```text
Action
  │
  ├── writes $GITHUB_OUTPUT
  │
  ▼
Step Output
  │
  ▼
steps.<id>.outputs.<name>
```

Outputs should contain useful machine-readable information rather than large logs or arbitrary state.

---

## `$GITHUB_OUTPUT`

`$GITHUB_OUTPUT` is the supported mechanism for setting step outputs.

Example:

```bash
echo "version=1.4.0" >> "$GITHUB_OUTPUT"
```

With an identified step:

```yaml
- name: Generate version
  id: version
  shell: bash
  run: |
    echo "version=1.4.0" >> "$GITHUB_OUTPUT"

- name: Use version
  shell: bash
  run: |
    echo "Building version ${{ steps.version.outputs.version }}"
```

For multiline or structured values, use the supported multiline syntax carefully.

For JSON:

```yaml
- name: Generate matrix
  id: matrix
  shell: bash
  run: |
    echo 'matrix={"python":["3.11","3.12","3.13"]}' >> "$GITHUB_OUTPUT"
```

Then:

```yaml
strategy:
  matrix: ${{ fromJSON(needs.prepare.outputs.matrix) }}
```

This enables actions to participate in dynamic pipeline configuration.

---

## Composite Actions

A composite action packages multiple workflow steps into one reusable action.

Typical structure:

```text
.github/
└── actions/
    └── setup-python/
        └── action.yml
```

Example:

```yaml
name: Setup Python Project
description: Set up Python and install project dependencies

inputs:
  python-version:
    description: Python version
    required: false
    default: "3.12"

runs:
  using: composite
  steps:
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ inputs.python-version }}

    - name: Upgrade pip
      shell: bash
      run: python -m pip install --upgrade pip

    - name: Install dependencies
      shell: bash
      run: python -m pip install -r requirements.txt
```

Caller:

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Configure Python
    uses: ./.github/actions/setup-python
    with:
      python-version: "3.12"
```

### Why Composite Actions Are Useful

Composite actions are appropriate when multiple workflows repeat the same **sequence of steps**.

For example:

```text
Checkout
   ↓
Setup Python
   ↓
Upgrade pip
   ↓
Install dependencies
   ↓
Configure test environment
```

Instead of duplicating this sequence in every workflow, it can be packaged once.

### Advantages

- Simple implementation.
- Easy to understand.
- Can call other actions.
- Good for organization-specific conventions.
- Keeps repeated workflow steps consistent.

### Limitations

Composite actions are still fundamentally step orchestration. They are not a replacement for reusable workflows when the abstraction needs multiple jobs, matrices, environments, approvals, or job-level orchestration.

---

## JavaScript Actions

JavaScript actions execute action logic using a Node.js runtime.

Typical structure:

```text
my-action/
├── action.yml
├── package.json
├── src/
│   └── index.js
└── dist/
    └── index.js
```

A simplified `action.yml`:

```yaml
name: Deployment Metadata
description: Generate deployment metadata

inputs:
  environment:
    description: Target environment
    required: true

outputs:
  deployment-id:
    description: Generated deployment identifier

runs:
  using: node24
  main: dist/index.js
```

The exact runtime supported by GitHub should be verified when maintaining an action because action runtimes evolve over time.

A JavaScript action can use GitHub's action libraries, such as:

```text
@actions/core
@actions/github
```

Typical responsibilities include:

- Reading inputs.
- Setting outputs.
- Writing annotations.
- Calling GitHub APIs.
- Handling API responses.
- Implementing non-trivial automation logic.

Conceptually:

```text
Workflow
   │
   ▼
JavaScript Action
   │
   ├── @actions/core
   │
   ├── @actions/github
   │
   └── GitHub REST/GraphQL APIs
```

### Example

```javascript
const core = require("@actions/core");

async function run() {
  try {
    const environment = core.getInput("environment", {
      required: true,
    });

    const deploymentId = `${environment}-${process.env.GITHUB_SHA}`;

    core.setOutput("deployment-id", deploymentId);
  } catch (error) {
    core.setFailed(error.message);
  }
}

run();
```

A production JavaScript action should also have:

- Automated tests.
- Dependency management.
- Dependency auditing.
- Deterministic builds.
- A controlled release process.
- A generated distribution directory where required.
- Documentation for inputs and outputs.

---

## `@actions/core`

`@actions/core` provides common functionality for JavaScript actions.

Typical operations include:

```javascript
const core = require("@actions/core");

const environment = core.getInput("environment", {
  required: true,
});

core.info(`Deploying to ${environment}`);

core.setOutput("status", "ready");
```

It can also support:

- Errors
- Warnings
- Debug logging
- Groups
- Secrets
- State
- Outputs

Avoid exposing sensitive values in logs.

---

## `@actions/github`

`@actions/github` provides a convenient interface for interacting with GitHub APIs.

Example:

```javascript
const core = require("@actions/core");
const github = require("@actions/github");

async function run() {
  const token = core.getInput("token", { required: true });
  const octokit = github.getOctokit(token);

  const context = github.context;

  const { data } = await octokit.rest.repos.get({
    owner: context.repo.owner,
    repo: context.repo.repo,
  });

  core.setOutput("repository", data.full_name);
}

run().catch((error) => {
  core.setFailed(error.message);
});
```

The action should request only the GitHub permissions it actually requires.

---

## Docker Actions

Docker actions package the action implementation inside a Docker image.

Typical structure:

```text
docker-action/
├── action.yml
├── Dockerfile
└── entrypoint.sh
```

Example metadata:

```yaml
name: Security Scanner
description: Run the organization security scanner

inputs:
  target:
    description: Directory to scan
    required: true

runs:
  using: docker
  image: Dockerfile
  args:
    - ${{ inputs.target }}
```

Example Dockerfile:

```dockerfile
FROM alpine:3.22

RUN apk add --no-cache bash

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

Entry point:

```bash
#!/usr/bin/env bash
set -euo pipefail

target="${1:?target is required}"

echo "Scanning ${target}"
```

### Docker Action Execution

Conceptually:

```text
GitHub Runner
     │
     ▼
Build/prepare action container
     │
     ▼
Run entrypoint
     │
     ▼
Action result
```

### Docker Action Limitations

Docker actions have additional operational considerations:

- Container startup overhead.
- Linux-oriented execution requirements.
- Filesystem boundaries.
- Workspace mounting behavior.
- Environment propagation.
- Tool availability inside the container.
- Networking behavior.
- Platform constraints.

For simple repeated workflow steps, a composite action is often easier to operate.

For a self-contained Linux toolchain with controlled dependencies, a Docker action can be appropriate.

---

## Composite vs JavaScript vs Docker Actions

| Characteristic | Composite | JavaScript | Docker |
|---|---|---|---|
| Primary abstraction | Steps | Program logic | Containerized program |
| Can call other actions | Yes | Through implementation/API patterns | No direct workflow-step semantics |
| Startup overhead | Low | Low | Higher |
| Best for | Reusable step sequences | API/business logic | Isolated Linux tooling |
| Runtime control | Runner | Node.js | Container |
| Cross-platform | Strong | Strong | More limited |
| Complexity | Low | Medium/High | Medium |
| Good for internal standards | Excellent | Good | Good |
| Good for API integration | Limited | Excellent | Good |
| Good for custom CLI stacks | Good | Good | Excellent |

The correct choice depends on the abstraction being created, not on which action type is technically more powerful.

---

## Action vs Reusable Workflow

Actions and reusable workflows solve different problems.

### Action

An action is primarily a **step-level abstraction**.

```text
Job
 ├── Step
 ├── Step
 │    └── Custom Action
 ├── Step
 └── Step
```

### Reusable Workflow

A reusable workflow is a **workflow/job-level abstraction**.

```text
Caller Workflow
      │
      ▼
Reusable Workflow
      │
      ├── Job: Lint
      ├── Job: Test
      ├── Job: Build
      └── Job: Security
```

Example reusable workflow:

```yaml
name: Reusable Python CI

on:
  workflow_call:
    inputs:
      python-version:
        required: false
        type: string
        default: "3.12"

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ inputs.python-version }}

      - run: python -m pip install -r requirements.txt
      - run: pytest
```

Caller:

```yaml
jobs:
  ci:
    uses: organization/platform-workflows/.github/workflows/python-ci.yml@v1
    with:
      python-version: "3.12"
```

### Decision Rule

Use a **composite action** when the reusable unit is:

```text
Several steps inside one job
```

Use a **reusable workflow** when the reusable unit is:

```text
One or more jobs with orchestration
```

This distinction is important in large organizations.

---

## Action Inputs and Workflow Contexts

Actions can consume values from workflow contexts.

For example:

```yaml
- name: Build image
  uses: docker/build-push-action@v6
  with:
    tags: |
      my-registry/app:${{ github.sha }}
```

Commonly useful contexts include:

| Context | Typical use |
|---|---|
| `github` | Repository, commit, branch, event metadata |
| `env` | Environment variables |
| `vars` | Configuration variables |
| `secrets` | Sensitive values |
| `steps` | Previous step outputs |
| `needs` | Outputs/results from dependent jobs |
| `job` | Current job information |
| `runner` | Runner information |
| `matrix` | Current matrix values |
| `strategy` | Matrix strategy configuration |
| `inputs` | Workflow/action inputs |

Actions should consume the narrowest data required.

---

## Passing Environment Variables to Actions

Workflow:

```yaml
env:
  APP_ENV: staging

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Run build action
        uses: ./.github/actions/build
        env:
          APP_ENV: ${{ env.APP_ENV }}
```

For action inputs:

```yaml
- name: Deploy
  uses: ./.github/actions/deploy
  with:
    environment: staging
```

Prefer explicit inputs for configuration that represents the action's contract.

Use environment variables for process-level configuration.

---

## Actions and Secrets

An action can receive a secret as an input:

```yaml
- name: Authenticate registry
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.REGISTRY_USERNAME }}
    password: ${{ secrets.REGISTRY_TOKEN }}
```

However, secret handling requires careful design.

Avoid:

```yaml
run: echo "${{ secrets.DEPLOYMENT_TOKEN }}"
```

Avoid embedding secrets in URLs or command arguments where they may become visible through process output or debugging.

Prefer dedicated authentication mechanisms and environment variables where appropriate.

For AWS deployments, OIDC is generally preferable to storing long-lived AWS access keys as GitHub secrets.

---

## Actions and `GITHUB_TOKEN`

GitHub automatically provides a `GITHUB_TOKEN` to workflows.

Actions can use it for GitHub API operations when the workflow grants the required permissions.

Example:

```yaml
permissions:
  contents: read
  pull-requests: read
```

Avoid broad permissions such as:

```yaml
permissions: write-all
```

unless the workflow genuinely requires them.

A production principle is:

```text
Required capability
       ↓
Minimum permission
       ↓
Specific job
       ↓
Specific action
```

For example:

```yaml
permissions:
  contents: read
  id-token: write
```

can support source checkout and AWS OIDC authentication without granting unrelated write access.

---

## Action Security Boundary

An action executes as part of the job.

Therefore, if a job has:

```yaml
permissions:
  contents: write
```

then code executed by an action in that job may potentially use the available GitHub token permissions.

This means:

```text
Workflow permissions
        ↓
Job permissions
        ↓
Action execution
        ↓
Potential repository/API access
```

Actions should therefore be treated as executable dependencies.

Installing an action is not equivalent to installing passive configuration.

---

## Third-Party Actions and Supply-Chain Security

A third-party action can contain:

- JavaScript dependencies
- Shell commands
- Docker images
- Network calls
- GitHub API operations
- Credential-handling logic

A compromised action can therefore affect the CI/CD environment.

Before adopting an action, evaluate:

- Repository ownership.
- Maintainer reputation.
- Release history.
- Source availability.
- Dependency health.
- Required permissions.
- Runtime behavior.
- Security history.
- Versioning strategy.
- Whether the action is actually necessary.

For production environments, prefer trusted actions and pin versions appropriately.

---

## SHA Pinning

A version tag can move.

For example:

```yaml
uses: vendor/action@v1
```

may point to a different commit after a tag update.

A commit SHA identifies a specific revision:

```yaml
uses: vendor/action@<commit-sha>
```

This improves reproducibility and protects against mutable-reference changes.

The trade-off is operational maintenance. Teams need a controlled process for updating pinned versions.

A mature organization can combine:

```text
SHA pinning
+
Automated update tooling
+
Code review
+
Action allowlists
+
Permission restrictions
```

---

## Untrusted Input and Actions

GitHub metadata can be user-controlled.

Examples include:

- Pull request titles
- Issue titles
- Branch names
- Commit messages
- User-provided workflow inputs

Never assume these values are trusted shell syntax.

Unsafe pattern:

```yaml
- name: Process PR title
  run: |
    echo "PR title: ${{ github.event.pull_request.title }}"
```

The problem is not the GitHub expression itself. The problem is that the resulting value is inserted into a shell script.

A safer pattern is to pass the value through an environment variable:

```yaml
- name: Process PR title
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: |
    printf 'PR title: %s\n' "$PR_TITLE"
```

The shell then treats the value as data rather than source code.

This principle applies to custom actions as well.

---

## `pull_request` and `pull_request_target`

Actions frequently run on pull requests, which creates an important security boundary.

With:

```yaml
on:
  pull_request:
```

the workflow generally operates in the pull request context and should not assume that secrets are available to untrusted fork code.

`pull_request_target` executes in the context of the base repository and therefore requires particular caution.

A dangerous pattern is:

```text
pull_request_target
       ↓
Checkout attacker-controlled code
       ↓
Execute code
       ↓
Repository permissions/secrets
```

This can turn repository credentials into an execution primitive.

Do not use `pull_request_target` merely because a workflow needs additional permissions. Design the trust boundary explicitly.

---

## Actions with Pull Requests

A safer model is:

```text
Untrusted PR
     │
     ▼
Read-only validation
     │
     ├── Lint
     ├── Unit tests
     └── Static analysis
```

Privileged operations should be separated:

```text
Trusted branch
     │
     ▼
Build
     │
     ▼
Authenticate
     │
     ▼
Deploy
```

This separation reduces the blast radius of malicious pull requests.

---

## Action Outputs and Job Outputs

An action output is available to later steps in the same job.

A job output makes information available to dependent jobs.

Example:

```yaml
jobs:
  prepare:
    runs-on: ubuntu-latest

    outputs:
      image-tag: ${{ steps.metadata.outputs.image-tag }}

    steps:
      - name: Generate image tag
        id: metadata
        shell: bash
        run: |
          echo "image-tag=${GITHUB_SHA}" >> "$GITHUB_OUTPUT"

  build:
    needs: prepare
    runs-on: ubuntu-latest

    steps:
      - name: Build
        run: |
          echo "Building ${{ needs.prepare.outputs.image-tag }}"
```

Data flow:

```text
Action
  ↓
Step Output
  ↓
Job Output
  ↓
needs.<job>.outputs
  ↓
Dependent Job
```

This is especially useful for:

- Image tags
- Artifact names
- Version numbers
- Dynamic matrices
- Deployment metadata
- Environment identifiers

---

## Dynamic Matrix Generation with Actions

Actions can generate structured configuration for later jobs.

Example:

```yaml
jobs:
  prepare:
    runs-on: ubuntu-latest

    outputs:
      matrix: ${{ steps.generate.outputs.matrix }}

    steps:
      - name: Generate matrix
        id: generate
        shell: bash
        run: |
          matrix='{"python":["3.11","3.12","3.13"],"database":["postgres","mysql"]}'
          echo "matrix=${matrix}" >> "$GITHUB_OUTPUT"

  test:
    needs: prepare
    runs-on: ubuntu-latest

    strategy:
      matrix: ${{ fromJSON(needs.prepare.outputs.matrix) }}

    steps:
      - name: Test
        run: |
          echo "Python ${{ matrix.python }}"
          echo "Database ${{ matrix.database }}"
```

This allows a preparation step or action to determine the test topology dynamically.

---

## Actions for Backend CI

A Python backend pipeline might use:

```text
Checkout Action
      ↓
Python Setup Action
      ↓
Dependency Cache
      ↓
Lint
      ↓
Unit Tests
      ↓
Integration Tests
      ↓
Coverage Artifact
      ↓
Docker Build Action
```

Example:

```yaml
steps:
  - name: Checkout
    uses: actions/checkout@v4

  - name: Set up Python
    uses: actions/setup-python@v5
    with:
      python-version: "3.12"
      cache: "pip"

  - name: Install dependencies
    run: |
      python -m pip install --upgrade pip
      pip install -r requirements.txt
      pip install pytest pytest-cov

  - name: Run tests
    run: |
      pytest --cov=. --cov-report=xml

  - name: Upload coverage
    uses: actions/upload-artifact@v4
    with:
      name: coverage-report
      path: coverage.xml
```

The action is responsible for a reusable operation; the workflow remains responsible for pipeline orchestration.

---

## Actions with Django and FastAPI

A reusable Python setup action can standardize the environment for multiple backend repositories:

```text
Django Service
     │
     ├── Setup Python Action
     ├── Install Dependencies
     ├── Django Checks
     └── pytest

FastAPI Service
     │
     ├── Setup Python Action
     ├── Install Dependencies
     ├── API Tests
     └── pytest
```

The action should not become tightly coupled to one framework unless the organization intentionally wants a Django-specific or FastAPI-specific action.

Prefer:

```text
setup-python-project
```

over an action whose behavior silently assumes:

```text
Django + PostgreSQL + Redis + Celery
```

unless that combination is an explicit organizational standard.

---

## Actions and Artifacts

Actions commonly handle artifact lifecycle operations.

Example:

```yaml
- name: Upload test report
  uses: actions/upload-artifact@v4
  with:
    name: pytest-report
    path: test-results/
    retention-days: 7
```

Another job can retrieve it:

```yaml
- name: Download test report
  uses: actions/download-artifact@v4
  with:
    name: pytest-report
    path: test-results/
```

Artifacts represent outputs produced by a workflow.

Examples:

- Coverage reports
- Test results
- Compiled packages
- Deployment manifests
- Build archives
- Debug logs

---

## Actions and Caches

Caching is different from artifact storage.

A cache is intended to accelerate future executions.

Examples:

```text
pip cache
npm cache
Docker build cache
```

An artifact is a workflow output.

```text
Artifact:
"Here is the result of this build."

Cache:
"Reuse these dependencies/build layers if they are still valid."
```

A typical Python setup action can enable dependency caching:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
    cache: "pip"
```

For custom caching:

```yaml
- name: Cache dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

A cache hit should improve performance, not be required for correctness.

---

## Actions for Docker Builds

Production pipelines commonly use Docker-specific actions.

Example:

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Log in to registry
  uses: docker/login-action@v3
  with:
    registry: ${{ vars.REGISTRY }}
    username: ${{ secrets.REGISTRY_USERNAME }}
    password: ${{ secrets.REGISTRY_PASSWORD }}

- name: Build and push image
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: |
      ${{ vars.REGISTRY }}/backend:${{ github.sha }}
```

The resulting architecture is:

```text
GitHub Actions
      │
      ├── Docker Buildx
      │
      ├── Registry Authentication
      │
      ▼
Docker Image
      │
      ▼
Container Registry
      │
      ▼
Deployment Platform
```

For AWS:

```text
GitHub Actions
      │
      ▼
OIDC
      │
      ▼
AWS STS
      │
      ▼
Temporary IAM Credentials
      │
      ▼
ECR
      │
      ▼
ECS / EKS / EC2
```

The existing CI/CD notes use the same fundamental build → ECR → ECS deployment model and emphasize immutable image versioning, rollback, security scanning, and OIDC rather than long-lived credentials. :chatgpt-content-reference{index="1"}

---

## Action Composition

Actions can be composed into a higher-level workflow:

```yaml
jobs:
  ci:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Python setup
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Internal project setup
        uses: ./.github/actions/setup-project

      - name: Run lint
        run: ruff check .

      - name: Run tests
        run: pytest
```

The workflow remains readable because each action has a focused responsibility.

Avoid creating a single action that performs the entire CI/CD system:

```text
setup
+
lint
+
test
+
build
+
scan
+
push
+
deploy
+
rollback
```

That destroys observability and makes failure isolation harder.

---

## Action Design Principles

A good action should generally have:

### One Clear Responsibility

Good:

```text
setup-python
docker-build
generate-version
publish-artifact
```

Less desirable:

```text
run-entire-production-pipeline
```

### Explicit Inputs

```yaml
inputs:
  environment:
    required: true
```

Avoid hidden dependencies on repository-specific files unless the action explicitly documents them.

### Predictable Outputs

Outputs should be:

- Stable.
- Documented.
- Machine-readable.
- Small.
- Useful to downstream steps.

### Minimal Permissions

An action should not require broad permissions merely because they are convenient.

### Deterministic Behavior

Given the same inputs and source state, the action should behave predictably.

### Clear Failure Behavior

An action should fail with actionable information:

```text
What failed
Why it failed
What input caused it
What should be checked
```

---

## Action Repository Structure

A reusable composite action:

```text
.github/
└── actions/
    └── setup-python-project/
        ├── action.yml
        └── README.md
```

A JavaScript action:

```text
setup-project/
├── action.yml
├── package.json
├── package-lock.json
├── src/
│   └── index.js
├── dist/
│   └── index.js
├── tests/
│   └── index.test.js
└── README.md
```

A Docker action:

```text
security-scanner/
├── action.yml
├── Dockerfile
├── entrypoint.sh
├── tests/
└── README.md
```

For organization-wide actions, versioning and documentation should be treated like any other production software component.

---

## Action Testing

Actions should be tested independently from the workflows that consume them.

Test categories can include:

| Test | Purpose |
|---|---|
| Unit test | Validate internal logic |
| Input validation | Verify invalid configuration fails correctly |
| Output test | Verify expected outputs |
| API test | Validate GitHub API interactions |
| Integration test | Execute the action in a realistic runner |
| Security test | Validate permission and input handling |
| Regression test | Prevent previously fixed failures |

For a composite action, test important combinations of:

```text
Inputs
   ↓
Step execution
   ↓
Outputs
   ↓
Failure behavior
```

For a JavaScript action, unit test the implementation and mock external API interactions where practical.

For Docker actions, test:

- Image build.
- Entrypoint behavior.
- Required files.
- Exit codes.
- Input handling.
- Network behavior where required.

---

## Action Documentation

Every reusable action should document:

- Purpose
- Supported platforms
- Inputs
- Required inputs
- Defaults
- Outputs
- Required permissions
- Environment variables
- Secrets
- Example usage
- Failure behavior
- Versioning policy
- Security considerations
- Compatibility requirements

Example:

```markdown
## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `environment` | Yes | - | Deployment environment |
| `timeout` | No | `300` | Deployment timeout |

## Outputs

| Output | Description |
|---|---|
| `deployment-id` | Deployment identifier |

## Required Permissions

```yaml
permissions:
  contents: read
```
```

Documentation is particularly important for internal actions because the implementation may be reused by many repositories.

---

## Versioning Custom Actions

Treat organization-owned actions as software dependencies.

A practical versioning model is:

```text
v1
v1.1
v1.1.1
```

Use semantic versioning when the action has a stable public contract.

A major version should represent a compatibility boundary.

For example:

```text
v1 → backward-compatible changes
v2 → breaking input/output or behavior changes
```

A production repository can consume:

```yaml
uses: organization/setup-python-project@v1
```

while the action repository manages releases internally.

For highly controlled environments, workflows may pin an exact release or SHA.

---

## Internal and Private Actions

Organizations can maintain internal automation components such as:

```text
organization/
├── platform-actions
│   ├── setup-python
│   ├── security-scan
│   ├── docker-build
│   └── deployment-metadata
└── platform-workflows
    ├── python-ci.yml
    ├── docker-build.yml
    └── aws-deploy.yml
```

This creates a useful separation:

```text
Actions
   ↓
Reusable implementation

Reusable Workflows
   ↓
Pipeline orchestration

Application Workflows
   ↓
Repository-specific configuration
```

This is often more maintainable than copying complete CI pipelines into every repository.

---

## Actions and AWS OIDC

Actions are frequently used as the integration layer between GitHub and AWS.

A secure architecture is:

```text
GitHub Actions Job
        │
        │ OIDC token
        ▼
AWS IAM OIDC Trust
        │
        ▼
AWS STS AssumeRole
        │
        ▼
Temporary Credentials
        │
        ▼
ECR / ECS / S3 / Lambda / CloudFormation
```

Workflow permissions:

```yaml
permissions:
  contents: read
  id-token: write
```

Then:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
    aws-region: ap-south-1
```

This avoids storing long-lived AWS access keys in GitHub secrets.

The IAM role should restrict:

- Repository identity.
- Branch/environment conditions where appropriate.
- AWS account.
- Allowed actions.
- Allowed resources.

---

## Actions in a Production Deployment Pipeline

A mature backend pipeline may look like:

```text
Pull Request
     │
     ▼
Checkout Action
     │
     ▼
Python Setup Action
     │
     ▼
Lint
     │
     ▼
Unit Tests
     │
     ▼
Integration Tests
     │
     ▼
Security Scan
     │
     ▼
Build Docker Image
     │
     ▼
Generate Immutable Tag
     │
     ▼
Authenticate with AWS using OIDC
     │
     ▼
Push Image to ECR
     │
     ▼
Deploy Staging
     │
     ▼
Health Validation
     │
     ▼
Production Approval
     │
     ▼
Deploy Production
     │
     ▼
Monitor
     │
     └──── failure ────► Rollback
```

Actions implement individual operations, while the workflow defines the dependency graph.

This distinction is fundamental to maintainable CI/CD design.

---

## Build Once, Promote the Same Artifact

A production pipeline should generally avoid:

```text
Build staging image
        ↓
Deploy staging

Build production image
        ↓
Deploy production
```

because the two images can differ.

Prefer:

```text
Source
  ↓
Build
  ↓
Immutable Image
  ↓
ECR
  │
  ├── Staging
  │
  └── Production
```

For example:

```yaml
tags: |
  ${{ vars.ECR_REPOSITORY }}:${{ github.sha }}
```

The same SHA-tagged image can then be promoted across environments.

This improves:

- Reproducibility.
- Rollback.
- Auditability.
- Deployment confidence.

The existing ECS CI/CD material explicitly emphasizes image versioning and rollback rather than relying on mutable `latest` tags. :chatgpt-content-reference{index="2"}

---

## Actions and Integration Testing

Actions are useful for standardizing integration test setup.

A backend test job might use:

```yaml
jobs:
  integration:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: app
          POSTGRES_PASSWORD: test-password
          POSTGRES_DB: app_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U app -d app_test"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 10

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Install dependencies
        run: |
          python -m pip install -r requirements.txt
          python -m pip install pytest pytest-cov

      - name: Run tests
        env:
          DATABASE_URL: postgresql://app:test-password@localhost:5432/app_test
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest --cov=. --cov-report=xml

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage.xml
```

The existing backend CI notes use PostgreSQL service containers, Python setup, pytest, coverage, and uploaded reports as part of realistic CI pipelines. :chatgpt-content-reference{index="3"}

---

## Action Failure Isolation

When an action fails, distinguish between:

```text
Action implementation failure
        │
        ├── Input problem
        ├── Permission problem
        ├── Runner problem
        ├── Network problem
        ├── Dependency problem
        └── External service problem
```

Do not immediately replace the action.

First determine whether:

1. The action was invoked correctly.
2. Inputs are correct.
3. Required permissions exist.
4. The runner supports the action.
5. External services are reachable.
6. The action version is compatible.
7. The failure is deterministic.

---

## Troubleshooting Actions

### Symptom: Action Not Found

Possible causes:

- Incorrect repository.
- Incorrect path.
- Invalid version.
- Private repository access issue.
- Typographical error.

Check:

```yaml
uses: organization/action-repository@v1
```

For local actions:

```yaml
uses: ./.github/actions/my-action
```

Verify the repository contains:

```text
action.yml
```

at the expected location.

---

### Symptom: Required Input Missing

Possible cause:

```yaml
inputs:
  environment:
    required: true
```

but the caller omitted:

```yaml
with:
  environment: production
```

Check the action documentation and workflow invocation.

---

### Symptom: Action Has Permission Errors

Possible causes:

- Missing `GITHUB_TOKEN` permission.
- Incorrect job-level permissions.
- Environment protection.
- AWS IAM trust failure.
- Insufficient AWS role permissions.

Check:

```yaml
permissions:
  contents: read
  id-token: write
```

Then inspect the action's actual API operation.

---

### Symptom: Action Works Locally but Fails in GitHub Actions

Remember that actions execute in the runner environment.

Check:

```bash
python --version
node --version
docker version
git --version
pwd
env
```

Do not assume local developer tooling exists on the runner.

---

### Symptom: Composite Action Cannot Execute a Command

Possible causes:

- Incorrect shell.
- Missing executable.
- Wrong working directory.
- OS mismatch.

Specify the shell explicitly:

```yaml
- name: Run script
  shell: bash
  run: ./scripts/build.sh
```

---

### Symptom: Docker Action Fails

Check:

```text
Dockerfile
ENTRYPOINT
Input arguments
Filesystem paths
Exit code
Network requirements
Runner operating system
```

The action container does not automatically behave like the host shell environment.

---

### Symptom: Output Is Empty

Verify that the action writes to:

```bash
$GITHUB_OUTPUT
```

Example:

```bash
echo "image-tag=${GITHUB_SHA}" >> "$GITHUB_OUTPUT"
```

Verify the step has an ID:

```yaml
- name: Generate tag
  id: metadata
```

Then consume:

```yaml
${{ steps.metadata.outputs.image-tag }}
```

---

## Common Action Mistakes

### Treating Actions as Trusted Code

An action executes code.

**Why it happens:** the `uses` syntax looks declarative.

**Problem:** a compromised action can access credentials and permissions available to the job.

**Prevention:**

- Use trusted sources.
- Review source.
- Pin versions appropriately.
- Minimize permissions.
- Restrict marketplace usage.
- Regularly update dependencies.

---

### Using Excessive Permissions

Bad:

```yaml
permissions: write-all
```

Prefer:

```yaml
permissions:
  contents: read
```

and add only required permissions.

---

### Passing Untrusted Values into Shell Commands

Bad:

```yaml
run: echo "${{ github.event.pull_request.title }}"
```

Safer:

```yaml
env:
  PR_TITLE: ${{ github.event.pull_request.title }}
run: printf '%s\n' "$PR_TITLE"
```

---

### Creating Huge Composite Actions

An action containing dozens of unrelated operations becomes difficult to test and debug.

Prefer focused actions:

```text
setup
build
scan
publish
deploy
```

and orchestrate them through the workflow.

---

### Hiding Pipeline Logic Inside Actions

Over-abstraction can make workflows difficult to understand.

A reviewer should be able to identify:

```text
What is being tested?
What is being built?
What is being deployed?
Where are credentials used?
Where can deployment fail?
```

Do not hide all of these behind a single opaque action.

---

### Using Mutable Action References Without Governance

For example:

```yaml
uses: vendor/action@main
```

creates a moving dependency.

Use controlled release references or immutable pinning according to organizational security requirements.

---

### Rebuilding in Every Environment

Do not create separate action invocations that rebuild the same application for staging and production unless there is an intentional reason.

Prefer:

```text
Build once
   ↓
Immutable artifact
   ↓
Promote
```

---

## Action Security Checklist

Before approving an action, verify:

| Area | Question |
|---|---|
| Source | Who maintains the action? |
| Version | Is the reference controlled? |
| Permissions | What does the action need? |
| Secrets | Does it receive sensitive values? |
| Network | Does it call external services? |
| Dependencies | Are dependencies maintained? |
| Runner | Does it require a specific OS/toolchain? |
| Inputs | Can untrusted data reach shell commands? |
| Outputs | Can outputs be trusted downstream? |
| Updates | How are security updates handled? |

---

## Organization-Level Action Governance

Large organizations should establish policies around:

- Approved action publishers.
- Approved versions.
- SHA pinning requirements.
- Marketplace allowlists.
- Permission standards.
- Secret handling.
- Internal action ownership.
- Action lifecycle.
- Security reviews.
- Dependency updates.
- Vulnerability response.

A useful model is:

```text
Developer
   │
   ▼
Approved Action
   │
   ├── Version policy
   ├── Permission policy
   ├── Security review
   └── Ownership
   │
   ▼
Production Workflow
```

This prevents every application team from independently making security-sensitive CI/CD decisions.

---

## Observability for Actions

Actions should produce useful logs without leaking secrets.

Useful output includes:

```text
Action version
Input configuration excluding secrets
Major operation being executed
External resource identifier
Duration
Result
Failure reason
```

Avoid:

```text
Access token
Password
Secret environment
Private key
```

Use GitHub logging facilities appropriately.

For example:

```yaml
- name: Build application
  run: |
    echo "::group::Build"
    python -m build
    echo "::endgroup::"
```

For action implementations, use the appropriate action logging APIs.

---

## Performance Considerations

Actions affect workflow execution time.

Potential sources of overhead include:

- Action download.
- Docker image startup.
- Dependency installation.
- Network calls.
- Repeated setup.
- Large artifacts.
- Cache misses.
- External API calls.

For example:

```text
Workflow
 ├── Setup Python        10s
 ├── Install dependencies 45s
 ├── Lint                 15s
 ├── Tests                90s
 └── Docker build        180s
```

The largest gains often come from:

- Dependency caching.
- Docker layer caching.
- Parallel jobs.
- Matrix optimization.
- Avoiding unnecessary setup.
- Reusing build artifacts.
- Reducing redundant API calls.

Do not optimize actions independently from the entire workflow.

---

## Reliability Considerations

Actions often interact with external systems:

```text
GitHub API
Docker Registry
AWS
Package Registry
Security Scanner
Deployment Platform
```

External dependencies introduce failure modes such as:

- Timeouts.
- Rate limits.
- Authentication failures.
- Service outages.
- Network failures.
- API changes.

Production actions should fail clearly and avoid leaving ambiguous state.

For deployment actions, idempotency is particularly important.

A retry should not accidentally create:

```text
Two deployments
Two resources
Two releases
Two production changes
```

when only one was intended.

---

## Concurrency and Actions

Actions execute within jobs controlled by workflow concurrency.

For production deployment:

```yaml
concurrency:
  group: production-deployment
  cancel-in-progress: false
```

This ensures deployments do not race with each other.

For pull requests:

```yaml
concurrency:
  group: pr-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

An action itself should not be responsible for solving workflow-level concurrency problems.

Concurrency belongs primarily to workflow/job orchestration.

---

## Actions and Rollback

A deployment action should ideally support deterministic deployment identifiers.

For Docker:

```text
backend:7f8a91c
```

rather than:

```text
backend:latest
```

A rollback can then point the deployment system back to a known artifact.

```text
Production
    │
    ▼
backend:7f8a91c
    │
    │ failure
    ▼
backend:6d21ab4
```

This makes rollback an artifact selection operation rather than a rebuild operation.

The existing ECS material similarly identifies reverting to a previous task definition revision as the rollback mechanism. :chatgpt-content-reference{index="4"}

---

## Action Architecture for a Backend Engineering Organization

A mature organization might structure automation as:

```text
                    GitHub Repository
                           │
                           ▼
                    Application Workflow
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
       Reusable        Composite       Official
       Workflow         Actions         Actions
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                        Runner
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
             AWS         Docker       GitHub API
```

Responsibilities should remain separated:

| Layer | Responsibility |
|---|---|
| Workflow | Repository-specific orchestration |
| Reusable workflow | Organization-wide job orchestration |
| Composite action | Reusable step sequence |
| JavaScript action | Reusable program/API logic |
| Docker action | Containerized tooling |
| Runner | Execution environment |
| AWS/API | External infrastructure |

---

## Production Example: Python + Docker + AWS

A simplified production workflow might use actions like:

```yaml
name: Backend CI/CD

on:
  pull_request:
    branches:
      - main

  push:
    branches:
      - main

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          pytest --cov=. --cov-report=xml

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage.xml

  build:
    if: github.event_name == 'push'
    needs: test
    runs-on: ubuntu-latest

    permissions:
      contents: read
      id-token: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ap-south-1

      - name: Login to ECR
        id: ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push image
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: |
            ${{ steps.ecr.outputs.registry }}/${{ vars.ECR_REPOSITORY }}:${{ github.sha }}
```

The important design is not the individual action syntax. It is the separation:

```text
Test
  ↓
Build
  ↓
Immutable Image
  ↓
ECR
  ↓
Promotion
  ↓
Deployment
```

---

## Troubleshooting Model

Use the following sequence when an action fails:

```text
Symptom
   ↓
Possible Causes
   ↓
Isolation Strategy
   ↓
Commands / Checks
   ↓
Root Cause
   ↓
Corrective Action
   ↓
Prevention
```

Example:

### Action Cannot Authenticate with AWS

**Symptom**

```text
AccessDenied
InvalidIdentityToken
Not authorized to perform sts:AssumeRoleWithWebIdentity
```

**Possible Causes**

- Missing `id-token: write`.
- Incorrect IAM trust policy.
- Wrong role ARN.
- Repository/branch condition mismatch.
- Incorrect AWS account.
- OIDC provider configuration problem.

**Isolation Strategy**

Check workflow permissions:

```yaml
permissions:
  contents: read
  id-token: write
```

Check the configured role:

```yaml
role-to-assume: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
```

Then inspect the IAM trust policy and CloudTrail events.

**Corrective Action**

Fix the trust relationship or workflow permissions.

**Prevention**

Treat the GitHub OIDC trust policy as production security infrastructure and review it alongside the workflow.

---

## GitHub CLI for Action Operations

The GitHub CLI can be used for operational management.

List workflows:

```bash
gh workflow list
```

View a workflow:

```bash
gh workflow view ci.yml
```

Run a workflow manually:

```bash
gh workflow run ci.yml
```

List recent runs:

```bash
gh run list
```

Inspect a run:

```bash
gh run view <run-id>
```

View logs:

```bash
gh run view <run-id> --log
```

Rerun a failed workflow:

```bash
gh run rerun <run-id>
```

Cancel a run:

```bash
gh run cancel <run-id>
```

List artifacts associated with runs:

```bash
gh run view <run-id>
```

The CLI is particularly useful for operational troubleshooting because it allows engineers to inspect workflow state without navigating the web interface manually.

---

## Senior-Level Action Design Questions

When designing an action, ask:

1. Is this behavior actually reusable?
2. Should this be an action or a reusable workflow?
3. What is the smallest useful interface?
4. What inputs are required?
5. What outputs are required?
6. What permissions does it need?
7. Does it process untrusted input?
8. Does it handle secrets?
9. Is its behavior deterministic?
10. How is it versioned?
11. How is it tested?
12. How will consumers receive security updates?
13. What happens if an external API fails?
14. Is retry behavior safe?
15. Can the action be rolled back?
16. Is the action tied unnecessarily to one repository?
17. Does it hide important deployment logic?
18. What happens when the runner operating system changes?

These questions are more important than knowing the syntax of `action.yml`.

---

## Interview Scenarios

### Scenario: Five repositories duplicate Python setup

Each repository contains:

```text
checkout
setup Python
pip upgrade
install requirements
```

A reasonable solution is a composite action if the required abstraction is a reusable sequence of steps.

Consider a reusable workflow instead if the standardization needs to include multiple jobs such as linting, testing, security scanning, and artifact publishing.

---

### Scenario: Production deployment requires three jobs

The pipeline is:

```text
Build
  ↓
Security Scan
  ↓
Deploy
```

A composite action is not the appropriate primary abstraction because the requirement crosses job boundaries.

A reusable workflow can encapsulate the job graph.

---

### Scenario: An action needs GitHub API access

Determine:

```text
Which API?
Which repository?
Read or write?
Which permission?
Which token?
```

Then grant only the required `GITHUB_TOKEN` permission.

---

### Scenario: A third-party action requests broad permissions

Do not blindly grant them.

Evaluate:

```text
What operation requires the permission?
Can the operation be implemented with lower privilege?
Can another trusted action perform the operation?
Can the action be internally maintained?
```

---

### Scenario: An action receives a pull request title

Treat the value as untrusted.

Avoid directly interpolating it into shell source.

Use environment variables and quote values appropriately.

---

### Scenario: Docker image must be promoted from staging to production

Do not rebuild.

Use:

```text
Build
  ↓
Image tagged with commit SHA
  ↓
ECR
  ↓
Staging
  ↓
Approval
  ↓
Same image
  ↓
Production
```

This provides artifact identity across environments.

---

### Scenario: AWS credentials must not be stored as secrets

Use:

```text
GitHub Actions
      ↓
OIDC
      ↓
IAM
      ↓
STS
      ↓
Temporary credentials
```

The workflow needs:

```yaml
permissions:
  id-token: write
```

and the AWS IAM role must trust the appropriate GitHub OIDC identity.

---

### Scenario: A custom action suddenly starts failing

Investigate:

```text
Action version
       ↓
Runner image
       ↓
Runtime version
       ↓
Dependencies
       ↓
Input changes
       ↓
External APIs
       ↓
Permissions
```

Do not assume the application code caused the failure.

---

## Common Action Anti-Patterns

| Anti-pattern | Problem | Better approach |
|---|---|---|
| `@main` for production | Mutable dependency | Controlled release/SHA |
| `write-all` permissions | Excessive blast radius | Least privilege |
| One giant action | Poor observability | Focused actions/workflows |
| Secrets in shell arguments | Exposure risk | Secure inputs/env/auth mechanisms |
| Rebuilding production | Artifact drift | Promote immutable artifact |
| Untrusted PR + privileged action | Credential compromise risk | Separate trust boundaries |
| No action tests | Regressions | Automated action testing |
| No ownership | Unmaintained automation | Explicit maintainers |
| Hidden repository assumptions | Poor reuse | Explicit inputs/contracts |
| No version policy | Uncontrolled updates | Semantic releases/pinning |

---

## Production Checklist

Before introducing an action into a production pipeline, verify:

### Design

- [ ] The action has one clear responsibility.
- [ ] Composite action vs reusable workflow has been considered.
- [ ] Inputs are explicit and documented.
- [ ] Outputs are stable and useful.
- [ ] Repository-specific assumptions are minimized.

### Security

- [ ] Required permissions are documented.
- [ ] `GITHUB_TOKEN` permissions are minimized.
- [ ] Secrets are not logged.
- [ ] Untrusted GitHub data is handled safely.
- [ ] Third-party actions have been reviewed.
- [ ] Action versions are controlled.
- [ ] Supply-chain risks are considered.

### Reliability

- [ ] Failures produce actionable logs.
- [ ] External API failures are handled.
- [ ] Retries are safe.
- [ ] Deployment operations are idempotent.
- [ ] Action behavior is deterministic.

### Operations

- [ ] The action is tested.
- [ ] Releases are versioned.
- [ ] Ownership is defined.
- [ ] Security updates have an update process.
- [ ] Runner compatibility is documented.
- [ ] Rollback is possible where applicable.

### CI/CD Architecture

- [ ] Actions are not hiding critical pipeline decisions.
- [ ] Artifacts are immutable.
- [ ] Build and deployment responsibilities are separated.
- [ ] Staging and production promotion use controlled artifacts.
- [ ] AWS authentication uses OIDC where appropriate.
- [ ] Deployment concurrency is explicitly designed.

## Key Takeaways

- GitHub Actions are reusable executable components; treat them as software dependencies with versioning, testing, security, and ownership rather than passive YAML configuration.
- Composite actions package reusable steps, JavaScript actions package programmatic logic, Docker actions package containerized tooling, while reusable workflows provide job-level pipeline orchestration.
- Action security depends on least-privilege permissions, controlled versions, safe handling of untrusted GitHub data, careful secret usage, and explicit trust boundaries.
- Production CI/CD should use actions as focused building blocks while the workflow remains responsible for orchestration, artifact promotion, concurrency, approvals, deployment, and rollback.
- Mature action design prioritizes deterministic behavior, clear contracts, observability, secure AWS integration through OIDC, and maintainable organization-wide reuse.