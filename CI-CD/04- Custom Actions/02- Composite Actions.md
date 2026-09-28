# 02- Composite Actions

## Overview

Composite actions package multiple GitHub Actions steps into a reusable unit that can be invoked from a workflow job.

They are particularly useful for standardizing repeated CI behavior such as:

- Python environment setup.
- Dependency installation.
- Code-quality checks.
- Authentication setup.
- Repository initialization.
- Common build preparation.
- Repeated shell-based operational tasks.

A composite action executes **within the calling job**. It does not create jobs or orchestrate a workflow.

```text
Workflow
   │
   └── Job
        │
        ├── Step
        │
        ├── Composite Action
        │     ├── Step
        │     ├── Step
        │     └── Step
        │
        └── Step
```

This makes composite actions fundamentally different from reusable workflows.

| Capability | Composite Action | Reusable Workflow |
|---|---|---|
| Packages steps | Yes | Yes |
| Runs inside a job | Yes | No |
| Creates multiple jobs | No | Yes |
| Job dependency graph | No | Yes |
| Matrix orchestration | No | Yes |
| Environment promotion | No | Yes |
| Approval gates | No | Yes |
| Workflow-level concurrency | No | Yes |
| Can invoke other actions | Yes | Yes |
| Best for | Reusable step groups | Reusable pipelines |

Composite actions should therefore be treated as **reusable implementation units**, while reusable workflows should be treated as **pipeline orchestration units**.

## Why Composite Actions Exist

Without composite actions, the same workflow logic may be duplicated across repositories.

For example:

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Set up Python
    uses: actions/setup-python@v5
    with:
      python-version: "3.12"

  - name: Upgrade pip
    run: python -m pip install --upgrade pip

  - name: Install dependencies
    run: python -m pip install -r requirements.txt
```

If this pattern appears in twenty repositories, changes become difficult to manage.

A composite action can encapsulate the repeated steps:

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Set up backend environment
    uses: ./.github/actions/python-setup
```

The workflow becomes responsible for **what should happen**, while the action owns **how the repeated setup is implemented**.

## Composite Action Architecture

A repository-local composite action commonly looks like:

```text
.github/
└── actions/
    └── python-setup/
        ├── action.yml
        └── README.md
```

An organization-wide action may use a dedicated repository:

```text
company-python-setup/
├── action.yml
├── README.md
└── tests/
```

The `action.yml` file is the action's metadata and execution contract.

```yaml
name: "Python Backend Setup"
description: "Configure Python and install backend dependencies"

inputs:
  python-version:
    description: "Python version"
    required: false
    default: "3.12"

  dependency-file:
    description: "Dependency file"
    required: false
    default: "requirements.txt"

runs:
  using: "composite"

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
      run: python -m pip install -r "${{ inputs.dependency-file }}"
```

## `action.yml`

A composite action requires:

```yaml
runs:
  using: "composite"
```

A basic structure is:

```yaml
name: "Action Name"
description: "Action description"

inputs:
  input-name:
    description: "Input description"
    required: true

outputs:
  output-name:
    description: "Output description"
    value: ${{ steps.some-step.outputs.result }}

runs:
  using: "composite"

  steps:
    - name: Execute
      shell: bash
      run: echo "Running"
```

The main components are:

| Component | Purpose |
|---|---|
| `name` | Action name |
| `description` | Action purpose |
| `inputs` | Configuration supplied by callers |
| `outputs` | Values returned to callers |
| `runs` | Composite execution definition |
| `steps` | Individual operations executed by the action |

## Inputs

Inputs provide the public configuration interface of a composite action.

Example:

```yaml
inputs:
  python-version:
    description: "Python version to install"
    required: false
    default: "3.12"

  install-dev:
    description: "Install development dependencies"
    required: false
    default: "true"
```

The caller provides values through `with`:

```yaml
- name: Configure Python
  uses: ./.github/actions/python-setup
  with:
    python-version: "3.12"
    install-dev: "true"
```

Inside the action:

```yaml
run: |
  echo "Python version: ${{ inputs.python-version }}"
  echo "Install dev dependencies: ${{ inputs.install-dev }}"
```

## Input Design

Composite action inputs should represent meaningful configuration rather than implementation details.

Prefer:

```yaml
with:
  python-version: "3.12"
  dependency-file: "requirements.txt"
```

Avoid exposing internal commands:

```yaml
with:
  command-1: ...
  command-2: ...
  internal-path: ...
  temporary-file: ...
  implementation-mode: ...
```

A good action interface is:

- Small.
- Explicit.
- Stable.
- Predictable.
- Backward compatible.
- Easy to understand.

The action should own implementation decisions that consumers do not need to control.

## Required and Optional Inputs

Required input:

```yaml
inputs:
  environment:
    description: "Target environment"
    required: true
```

Optional input:

```yaml
inputs:
  python-version:
    description: "Python runtime"
    required: false
    default: "3.12"
```

Use required inputs when omitting the value would make the action ambiguous or unsafe.

Use defaults for common, safe behavior.

## Outputs

Composite actions can expose outputs to the calling step.

Example:

```yaml
outputs:
  python-version:
    description: "Resolved Python version"
    value: ${{ steps.version.outputs.python-version }}
```

The step can create the output using `GITHUB_OUTPUT`:

```yaml
- name: Determine Python version
  id: version
  shell: bash
  run: |
    VERSION="$(python --version 2>&1 | awk '{print $2}')"
    echo "python-version=${VERSION}" >> "$GITHUB_OUTPUT"
```

The caller can consume the result:

```yaml
- name: Configure Python
  id: setup
  uses: ./.github/actions/python-setup

- name: Display Python version
  run: echo "Python: ${{ steps.setup.outputs.python-version }}"
```

The output flow is:

```text
Composite Step
     │
     │ GITHUB_OUTPUT
     ▼
Step Output
     │
     ▼
Composite Action Output
     │
     ▼
Calling Workflow Step
```

## Passing Values Between Steps

Composite action steps can use environment variables:

```yaml
- name: Prepare
  shell: bash
  run: echo "BUILD_ENV=staging" >> "$GITHUB_ENV"

- name: Consume value
  shell: bash
  run: echo "Environment: $BUILD_ENV"
```

For explicit data flow, outputs are generally easier to reason about:

```yaml
- name: Generate metadata
  id: metadata
  shell: bash
  run: |
    echo "version=1.4.2" >> "$GITHUB_OUTPUT"

- name: Use metadata
  shell: bash
  run: |
    echo "Version: ${{ steps.metadata.outputs.version }}"
```

Use `GITHUB_ENV` for environment state and `GITHUB_OUTPUT` for explicit step/action data.

## Shell Requirements

Every `run` step in a composite action should specify its shell.

```yaml
- name: Run tests
  shell: bash
  run: pytest
```

This is especially important when the action may run on different runner operating systems.

For Windows:

```yaml
- name: Run PowerShell command
  shell: pwsh
  run: |
    Write-Host "Running on Windows"
```

The shell should be selected deliberately based on the action's supported platforms.

## Working Directory

Composite actions may need to operate against the caller's repository.

Use an explicit working directory when required:

```yaml
- name: Run tests
  shell: bash
  working-directory: backend
  run: pytest
```

Avoid assuming that the action repository's directory is the application's working directory.

This distinction becomes important for actions stored in separate repositories.

## Environment Variables

A composite action can define environment variables for individual steps:

```yaml
- name: Run migration check
  shell: bash
  env:
    DJANGO_SETTINGS_MODULE: config.settings.test
  run: python manage.py check
```

This is preferable to embedding configuration directly inside shell commands.

For secrets:

```yaml
- name: Authenticate
  shell: bash
  env:
    API_TOKEN: ${{ inputs.api-token }}
  run: ./scripts/authenticate.sh
```

Do not print sensitive values.

## Composite Actions and Secrets

Composite actions do not automatically provide unrestricted access to secrets.

The calling workflow should explicitly provide sensitive values where necessary.

Example:

```yaml
- name: Authenticate deployment
  uses: ./.github/actions/deploy
  with:
    api-token: ${{ secrets.DEPLOY_TOKEN }}
```

The action should document the requirement:

```yaml
inputs:
  api-token:
    description: "Deployment API token"
    required: true
```

However, passing secrets through action inputs requires careful handling because an action implementation may accidentally expose them.

Never do this:

```yaml
- name: Debug
  shell: bash
  run: echo "Token=${{ inputs.api-token }}"
```

Instead:

```yaml
- name: Authenticate
  shell: bash
  env:
    API_TOKEN: ${{ inputs.api-token }}
  run: ./scripts/authenticate.sh
```

## Security and Untrusted Input

Composite actions often execute shell commands, so untrusted input must be treated as data.

Dangerous pattern:

```yaml
- name: Execute branch command
  shell: bash
  run: |
    git checkout ${{ github.head_ref }}
```

A malicious branch name can potentially alter shell interpretation.

Prefer environment variables:

```yaml
- name: Checkout branch
  shell: bash
  env:
    BRANCH_NAME: ${{ github.head_ref }}
  run: |
    git checkout -- "$BRANCH_NAME"
```

Even better, use dedicated action inputs or Git commands that avoid unnecessary shell interpretation.

The same principle applies to:

- Pull request titles.
- Commit messages.
- Branch names.
- Issue content.
- Manual workflow inputs.
- Repository dispatch payloads.
- External API data.

## Composite Actions and `pull_request`

Composite actions can execute code from the repository in which they are defined.

For pull request workflows, distinguish between:

```text
Trusted workflow logic
        ↓
Untrusted pull request content/code
```

A workflow processing code from an untrusted fork must not automatically provide sensitive credentials or privileged permissions.

Composite actions should therefore be designed so that they do not require secrets unless the calling workflow has deliberately established a trusted security boundary.

## Calling Local Composite Actions

A repository-local action can be referenced with:

```yaml
- name: Backend setup
  uses: ./.github/actions/backend-setup
```

Example repository:

```text
repository/
├── .github/
│   └── actions/
│       └── backend-setup/
│           └── action.yml
├── app/
├── tests/
├── requirements.txt
└── .github/
    └── workflows/
        └── ci.yml
```

This is useful for repository-specific conventions.

## Calling Organization-Wide Composite Actions

A shared action can be maintained separately:

```yaml
- name: Backend setup
  uses: company/backend-actions/python-setup@v1
```

For a dedicated repository:

```yaml
- name: Python setup
  uses: company/python-setup@v1
```

This provides centralized implementation and version management.

The trade-off is that the action becomes an organizational dependency.

## Versioning Composite Actions

Treat shared composite actions as versioned APIs.

Common references include:

```yaml
uses: company/python-setup@v1
```

or:

```yaml
uses: company/python-setup@v1.3.0
```

For stronger supply-chain integrity:

```yaml
uses: company/python-setup@<commit-sha>
```

A practical organizational strategy is:

```text
v1
 ├── v1.0.0
 ├── v1.1.0
 └── v1.2.0
```

Consumers can remain on the `v1` compatibility line while the implementation evolves through backward-compatible releases.

Breaking behavior should generally require a new major version.

## Semantic Versioning

Use semantic versioning for organization-wide actions when the action has a stable public interface:

```text
MAJOR.MINOR.PATCH
```

Examples:

```text
1.0.0
1.1.0
1.1.1
2.0.0
```

Typical interpretation:

| Change | Version |
|---|---|
| Breaking input/output behavior | Major |
| Backward-compatible feature | Minor |
| Bug/security fix without interface break | Patch |

The action's versioning policy should be documented and consistently applied.

## Composite Actions and Reusable Workflows

A common architecture is:

```text
Reusable Workflow
       │
       ├── Lint Job
       │     └── Python Setup Action
       │
       ├── Test Job
       │     └── Python Setup Action
       │
       └── Build Job
             └── Docker Setup Action
```

The reusable workflow handles:

- Jobs.
- Dependencies.
- Matrix strategies.
- Environments.
- Approvals.
- Concurrency.
- Artifacts.
- Promotion.

The composite actions handle:

- Repeated steps.
- Setup.
- Commands.
- Authentication helpers.
- Standardized local behavior.

This separation prevents composite actions from becoming oversized workflow replacements.

## Composite Actions in Python CI

A production Python backend may use a composite action to standardize Python setup.

```yaml
name: "Python Backend Setup"
description: "Set up Python and install backend dependencies"

inputs:
  python-version:
    description: "Python version"
    required: false
    default: "3.12"

  dependency-file:
    description: "Dependency file"
    required: false
    default: "requirements.txt"

runs:
  using: "composite"

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
      run: python -m pip install -r "${{ inputs.dependency-file }}"
```

A Django workflow can then remain focused:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: ./.github/actions/python-setup
        with:
          python-version: "3.12"

      - name: Run Django checks
        run: python manage.py check

      - name: Run tests
        run: pytest
```

## Composite Actions with FastAPI

The same action can support a FastAPI application:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Configure Python
        uses: ./.github/actions/python-setup
        with:
          python-version: "3.12"

      - name: Run tests
        run: pytest
```

The action should remain application-framework agnostic when its responsibility is simply Python environment setup.

Do not create separate actions for Django and FastAPI unless their setup requirements materially differ.

## PostgreSQL and Redis Integration

A composite action should generally not own the complete service topology.

The workflow can define services:

```yaml
jobs:
  integration-test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: app_test
        ports:
          - 5432:5432

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Configure Python
        uses: ./.github/actions/python-setup

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/app_test
          REDIS_URL: redis://localhost:6379/0
        run: pytest tests/integration
```

This preserves a useful separation:

```text
Workflow
 ├── Infrastructure topology
 │    ├── PostgreSQL
 │    └── Redis
 │
 └── Composite Action
      └── Application setup
```

## Composite Actions for Standardized Quality Checks

An organization may standardize quality checks:

```yaml
name: "Python Quality"
description: "Run standard Python quality checks"

inputs:
  source-directory:
    description: "Source directory"
    required: false
    default: "."

runs:
  using: "composite"

  steps:
    - name: Ruff
      shell: bash
      run: ruff check "${{ inputs.source-directory }}"

    - name: Ruff format check
      shell: bash
      run: ruff format --check "${{ inputs.source-directory }}"

    - name: Type checking
      shell: bash
      run: mypy "${{ inputs.source-directory }}"
```

Caller:

```yaml
- name: Run quality checks
  uses: company/python-quality@v1
  with:
    source-directory: "src"
```

This can establish a consistent organization-wide baseline.

## Composite Actions and Caching

Composite actions can invoke caching actions:

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: ${{ inputs.python-version }}
    cache: pip
    cache-dependency-path: ${{ inputs.dependency-file }}
```

Caching should remain deterministic.

The cache should accelerate dependency installation, not become a required source of correctness.

A workflow must still succeed on a cache miss.

```text
Cache Hit
   ↓
Fast dependency installation

Cache Miss
   ↓
Normal dependency installation
```

Never design a composite action so that a cache miss causes functional failure.

## Composite Actions and Outputs

A useful composite action may return build metadata.

```yaml
outputs:
  version:
    description: "Application version"
    value: ${{ steps.version.outputs.version }}

runs:
  using: "composite"

  steps:
    - name: Generate version
      id: version
      shell: bash
      run: |
        VERSION="$(git describe --tags --always)"
        echo "version=${VERSION}" >> "$GITHUB_OUTPUT"
```

Caller:

```yaml
- name: Generate metadata
  id: metadata
  uses: ./.github/actions/build-metadata

- name: Build Docker image
  run: |
    docker build \
      --build-arg APP_VERSION="${{ steps.metadata.outputs.version }}" \
      -t "backend:${{ steps.metadata.outputs.version }}" .
```

Keep outputs small and deterministic.

Large files should be transferred using artifacts rather than outputs.

## Composite Action Error Handling

Shell steps should fail correctly.

Use:

```yaml
- name: Run checks
  shell: bash
  run: |
    set -euo pipefail
    ./scripts/check.sh
```

Avoid:

```yaml
- name: Run checks
  shell: bash
  run: |
    ./scripts/check.sh || true
```

unless ignoring failure is an intentional part of the action contract.

Suppressing errors makes downstream failures harder to diagnose.

## Exit Codes

The action should preserve meaningful exit status.

```text
Command succeeds
    → Step succeeds
    → Action succeeds

Command fails
    → Step fails
    → Action fails
    → Job normally fails
```

If failure is intentionally tolerated, make that behavior explicit in the action interface.

Do not silently convert operational failures into successful workflow execution.

## Composite Actions and `continue-on-error`

The caller may decide whether an action failure should be tolerated:

```yaml
- name: Optional security scan
  uses: company/security-check@v1
  continue-on-error: true
```

However, the action itself should normally report genuine failures accurately.

This separates:

```text
Action correctness
```

from:

```text
Workflow policy about failure tolerance
```

## Composite Actions and `GITHUB_ENV`

A composite action can expose environment state to subsequent steps:

```yaml
- name: Configure environment
  shell: bash
  run: |
    echo "APP_ENV=ci" >> "$GITHUB_ENV"
```

This modifies the job environment for subsequent steps.

However, outputs are often preferable for explicit data dependencies:

```yaml
echo "environment=ci" >> "$GITHUB_OUTPUT"
```

Use the mechanism that reflects the intended scope.

| Requirement | Mechanism |
|---|---|
| Environment for later steps | `GITHUB_ENV` |
| Explicit step result | `GITHUB_OUTPUT` |
| Add executable to PATH | `GITHUB_PATH` |
| Human-readable job information | Step summary |

## `GITHUB_PATH`

A composite action can add a directory to the runner's `PATH`:

```yaml
- name: Add tool directory
  shell: bash
  run: echo "$HOME/.local/bin" >> "$GITHUB_PATH"
```

Subsequent steps can then invoke tools from that directory.

Avoid modifying `PATH` unnecessarily because it can make execution behavior harder to understand.

## Step Summaries

Composite actions can contribute useful operational information to the job summary:

```yaml
- name: Publish result
  shell: bash
  run: |
    {
      echo "## Backend Checks"
      echo ""
      echo "- Ruff: passed"
      echo "- Tests: passed"
    } >> "$GITHUB_STEP_SUMMARY"
```

Use summaries for concise human-readable diagnostics rather than dumping large logs.

## Action Composition

Composite actions can use other actions:

```yaml
runs:
  using: "composite"

  steps:
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ inputs.python-version }}

    - name: Install dependencies
      shell: bash
      run: python -m pip install -r requirements.txt
```

This allows an action to compose existing trusted functionality.

However, every dependency becomes part of the action's supply-chain surface.

## Dependency Trust

A composite action may indirectly depend on multiple actions:

```text
Organization Composite Action
          │
          ├── setup-python
          ├── cache action
          └── shell scripts
```

Review:

- Action ownership.
- Version references.
- Required permissions.
- Security posture.
- Maintenance.
- Transitive dependencies.

For high-security environments, immutable SHA references can reduce the risk associated with mutable tags.

## Private and Internal Composite Actions

Organizations can maintain internal actions for common engineering standards.

Examples:

```text
company/python-quality
company/docker-build
company/security-scan
company/aws-auth
company/backend-setup
```

An internal action can standardize:

```text
Repository
    ↓
Company CI Standards
    ↓
Reusable Composite Actions
    ↓
Application Workflow
```

This is useful when teams need consistent behavior without copying implementation details between repositories.

## When Not to Use a Composite Action

Avoid a composite action when the logic requires:

- Multiple jobs.
- Job-level dependency graphs.
- Matrix orchestration.
- Deployment approvals.
- Environment promotion.
- Workflow-level concurrency.
- Cross-job artifact orchestration.
- Complex deployment state machines.

For example, this should remain workflow-level:

```text
Lint
 ↓
Tests
 ↓
Build
 ↓
Staging
 ↓
Approval
 ↓
Production
```

A composite action can assist individual jobs, but should not become the container for this entire pipeline.

## Composite Action vs Copy-Paste

| Approach | Reuse | Maintenance | Consistency | Flexibility |
|---|---:|---:|---:|---:|
| Copy-paste | Low | Low | Low | High |
| Composite action | High | High | High | High |
| Reusable workflow | Very high | High | Very high | Workflow-level |
| Organization platform | Very high | High | Very high | Depends on API |

Use the smallest abstraction that solves the duplication problem.

If only three steps are repeated, a composite action may be appropriate.

If complete CI architecture is repeated, use a reusable workflow.

## Production Architecture

A mature backend CI platform can use several layers:

```mermaid
flowchart TD
    A[Application Repository] --> B[Workflow]
    B --> C[Reusable Workflow]
    C --> D[Job]
    D --> E[Composite Action]

    E --> F[Setup]
    E --> G[Quality Checks]
    E --> H[Build Helper]

    C --> I[Environment]
    C --> J[Concurrency]
    C --> K[Artifacts]

    K --> L[Staging]
    L --> M[Approval]
    M --> N[Production]
```

This architecture separates responsibilities:

- **Workflow**: repository-specific orchestration.
- **Reusable workflow**: standardized pipeline orchestration.
- **Composite action**: reusable step implementation.
- **Environment**: deployment protection.
- **Artifacts**: build outputs.
- **Concurrency**: resource coordination.

## Reliability Considerations

A production composite action should be:

- Deterministic.
- Idempotent where possible.
- Explicit about failure.
- Safe to retry.
- Independent of unnecessary external state.
- Compatible with its documented runner platforms.

Avoid hidden dependencies such as:

```text
Assumes tool X is installed
Assumes directory Y exists
Assumes environment variable Z exists
Assumes previous workflow step ran
```

If a dependency is required, either establish it inside the action or document it clearly.

## Performance Considerations

Composite actions can reduce workflow duplication, but they do not eliminate execution cost.

Consider:

- Repeated package installation.
- External API calls.
- Tool initialization.
- Cache effectiveness.
- Network downloads.
- Repeated Docker operations.

For example, an action that installs a large toolchain every time may become expensive at organizational scale.

Prefer:

```text
Cache
  +
Deterministic setup
  +
Minimal initialization
```

rather than repeatedly performing expensive setup without reuse.

## Scalability Considerations

An organization-wide composite action may be consumed by hundreds of repositories.

Therefore, changes should be evaluated as platform changes.

Before releasing a breaking change:

```text
Change
  ↓
Compatibility analysis
  ↓
Tests
  ↓
Version
  ↓
Canary consumers
  ↓
Broader rollout
```

Avoid silently changing behavior behind a stable major version when the change can break consumers.

## High Availability and External Dependencies

Composite actions that call external services should consider:

- Timeouts.
- Retries.
- Rate limits.
- Temporary failures.
- Idempotency.
- API availability.

For example:

```bash
curl --fail-with-body \
  --retry 3 \
  --retry-delay 2 \
  --connect-timeout 10 \
  --max-time 60 \
  "$API_ENDPOINT"
```

Retries should be used carefully.

A deployment operation that is not idempotent should not be blindly retried.

## Cost Optimization

Composite actions can reduce maintenance cost, but poorly designed actions can increase CI execution cost.

Monitor:

- Average action duration.
- Cache hit rate.
- Network transfer.
- External API calls.
- Runner minutes.
- Docker or tool initialization time.

A centralized action should make CI more consistent without making every repository execute unnecessary work.

## Testing Composite Actions

Composite actions should be tested independently from consumer workflows where practical.

A useful test strategy is:

```text
Action Change
     ↓
Syntax Validation
     ↓
Unit / Script Tests
     ↓
Integration Workflow
     ↓
Representative Consumer
```

Test at least:

- Required inputs.
- Default inputs.
- Valid inputs.
- Invalid inputs.
- Output generation.
- Failure behavior.
- Platform-specific behavior.
- Secret handling.
- External dependency failures.

## Testing Repository-Local Actions

A repository-local action can be tested through a dedicated workflow:

```yaml
name: Test Composite Action

on:
  pull_request:
    paths:
      - ".github/actions/python-setup/**"
      - ".github/workflows/test-action.yml"

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Execute action
        id: action
        uses: ./.github/actions/python-setup
        with:
          python-version: "3.12"

      - name: Verify Python
        run: python --version
```

Path filters prevent unrelated repository changes from triggering action-specific tests unnecessarily.

## Testing Organization-Wide Actions

For shared actions, include representative consumer workflows.

For example:

```text
Action Repository
      ↓
Compatibility Tests
      ↓
Django Consumer
      ↓
FastAPI Consumer
      ↓
Service Consumer
```

This catches integration issues that unit tests cannot detect.

## Documentation

A production composite action should document:

- Purpose.
- Inputs.
- Outputs.
- Supported runners.
- Required permissions.
- Required secrets.
- Usage.
- Versioning.
- Failure behavior.
- Security considerations.
- Compatibility requirements.

Example:

```markdown
## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `python-version` | No | `3.12` | Python runtime |
| `dependency-file` | No | `requirements.txt` | Dependency file |

## Usage

```yaml
- name: Python setup
  uses: company/python-setup@v1
  with:
    python-version: "3.12"
```
```

The documentation is part of the action's public contract.

## Common Mistakes

### Treating a Composite Action as a Workflow

A composite action cannot replace workflow orchestration.

Do not put deployment pipelines, approvals, and multi-job coordination inside one action.

### Excessive Inputs

An action with dozens of switches becomes difficult to understand and maintain.

Keep the interface focused.

### Hidden Runner Dependencies

Do not assume software is installed without documenting or provisioning it.

### Unsafe Shell Interpolation

Avoid directly interpolating untrusted GitHub values into shell commands.

Prefer environment variables and safe argument handling.

### Printing Secrets

Never log:

```bash
echo "$TOKEN"
```

or:

```yaml
run: echo "${{ secrets.API_TOKEN }}"
```

Even when GitHub masks known secret values, secret exposure should be prevented rather than relying exclusively on masking.

### Ignoring Failure Codes

Avoid:

```bash
command || true
```

unless failure is intentionally part of the contract.

### Mutable Dependency References

Unreviewed floating dependencies can change behavior unexpectedly.

Use an intentional action versioning strategy.

### Over-Abstraction

Not every repeated two-line command requires an organization-wide action.

Abstraction should reduce complexity rather than hide it.

## Troubleshooting

Use the standard troubleshooting model:

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

### Action Cannot Be Found

Check:

```text
.github/actions/<action-name>/action.yml
```

For a local action:

```yaml
uses: ./.github/actions/<action-name>
```

Verify:

- Directory name.
- `action.yml` spelling.
- Repository checkout.
- Workflow path.
- Branch or commit containing the action.

### Input Is Not Available

Verify the caller:

```yaml
with:
  python-version: "3.12"
```

and the action:

```yaml
inputs:
  python-version:
    required: false
```

Then verify the expression:

```yaml
${{ inputs.python-version }}
```

### Output Is Empty

Trace:

```text
Step ID
  ↓
GITHUB_OUTPUT
  ↓
Action output mapping
  ↓
Calling step ID
  ↓
steps.<id>.outputs.<name>
```

For example:

```yaml
outputs:
  version:
    value: ${{ steps.version.outputs.value }}
```

and:

```yaml
- id: version
  shell: bash
  run: echo "value=1.0.0" >> "$GITHUB_OUTPUT"
```

### Works Locally but Fails in GitHub Actions

Check:

- Runner operating system.
- Installed tools.
- Working directory.
- Environment variables.
- File permissions.
- Shell.
- Network access.
- Authentication.
- Case-sensitive paths.

### Windows Failure

If the action was written around Bash assumptions:

```yaml
shell: bash
```

may be appropriate if Bash is available and supported.

Otherwise provide an explicit Windows-compatible implementation.

Do not assume Linux shell behavior on every runner.

### Permission Failure

Check workflow permissions:

```yaml
permissions:
  contents: read
```

and expand only when required.

For an action using GitHub APIs, identify the exact API operation and corresponding token permission rather than granting broad write access.

## Debugging Techniques

Inspect workflow logs:

```bash
gh run list
```

View a run:

```bash
gh run view <run-id>
```

View logs:

```bash
gh run view <run-id> --log
```

Rerun after fixing the action:

```bash
gh run rerun <run-id>
```

For local development, test shell scripts independently where possible:

```bash
bash -n scripts/setup.sh
```

Then execute them under the same assumptions used by the action.

## Interview Scenarios

### Standardize Python Setup Across Repositories

Design a composite action used by Django and FastAPI repositories.

Discuss:

- Inputs.
- Defaults.
- Dependency installation.
- Caching.
- Versioning.
- Testing.
- Security.
- Rollout strategy.

### Composite Action or Reusable Workflow?

A company wants every repository to run:

```text
Lint
→ Unit Tests
→ Integration Tests
→ Build
→ Security Scan
```

The correct architectural question is whether the requirement is reusable **steps** or reusable **pipeline orchestration**.

A composite action is appropriate for repeated step-level behavior.

A reusable workflow is appropriate for the multi-job pipeline.

### Secure Pull Request Processing

A composite action receives a pull request title and passes it to a shell command.

Identify the risk:

```yaml
run: ./process.sh "${{ github.event.pull_request.title }}"
```

Discuss:

- Shell injection.
- Untrusted input.
- Environment variables.
- Safe argument handling.
- `pull_request` security boundaries.
- Secrets availability.

### Organization-Wide Action Change

A shared action is used by 100 repositories.

A breaking change is required.

Discuss:

```text
New major version
      ↓
Compatibility testing
      ↓
Representative consumers
      ↓
Migration documentation
      ↓
Gradual rollout
```

Avoid silently breaking every consumer.

### Composite Action for AWS Deployment

A team wants a composite action that deploys a Docker image to ECS.

Discuss:

- Whether deployment orchestration belongs in a reusable workflow.
- OIDC authentication.
- `id-token: write`.
- IAM role trust policy.
- Image immutability.
- Deployment health checks.
- Rollback.
- Concurrency.

The composite action can encapsulate a deployment operation, while the workflow remains responsible for deployment orchestration and environment controls.

## Production Checklist

Before using a composite action in production:

- [ ] `action.yml` defines a clear public interface.
- [ ] Inputs are minimal and documented.
- [ ] Required inputs are explicit.
- [ ] Defaults are safe.
- [ ] Outputs are documented.
- [ ] `GITHUB_OUTPUT` is used for explicit output data.
- [ ] `GITHUB_ENV` is used only when environment propagation is intended.
- [ ] Shell is explicitly specified.
- [ ] Runner compatibility is documented.
- [ ] Untrusted values are not directly interpolated into shell commands.
- [ ] Secrets are not printed.
- [ ] Required permissions are documented.
- [ ] Third-party actions are reviewed.
- [ ] Dependencies are versioned appropriately.
- [ ] Failure codes are preserved.
- [ ] Action behavior is tested.
- [ ] Versioning follows a defined strategy.
- [ ] Documentation includes production usage.
- [ ] Breaking changes use an appropriate major version.
- [ ] The action is not being used to hide workflow-level orchestration.

## Key Takeaways

- Composite actions package reusable steps within a single GitHub Actions job; they are implementation abstractions, not workflow orchestrators.
- Design composite actions around a small, stable input/output interface and keep implementation details inside the action.
- Use `GITHUB_OUTPUT`, `GITHUB_ENV`, and `GITHUB_PATH` deliberately according to the required data or environment scope.
- Treat shell commands, secrets, third-party actions, and untrusted GitHub event data as security boundaries requiring explicit handling and least privilege.
- Use composite actions for reusable step-level behavior and reusable workflows for multi-job CI/CD orchestration, environments, approvals, concurrency, and promotion.