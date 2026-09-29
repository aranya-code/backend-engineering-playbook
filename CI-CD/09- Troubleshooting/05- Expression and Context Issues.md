# 05- Expression and Context Issues

## Overview

GitHub Actions expressions and contexts control much of the dynamic behavior inside workflows. They determine which jobs and steps execute, which values are passed between jobs, how matrices are generated, which environment or deployment target is selected, and how workflow decisions are made.

Expression-related failures are often difficult because the YAML can be syntactically valid while the workflow behaves incorrectly.

Typical problems include:

- A value evaluates to an unexpected result.
- A context is unavailable in a particular location.
- An expression is evaluated at a different stage than expected.
- Shell syntax is confused with GitHub expression syntax.
- A string is compared with a boolean or number incorrectly.
- `needs` values are unavailable because the dependency is missing.
- Matrix data is generated as malformed JSON.
- Secrets are referenced in an inappropriate context.
- `if` conditions cause jobs or steps to be skipped.
- `success()`, `failure()`, `always()`, or `cancelled()` produce unexpected behavior.
- Dynamic values are injected into shell commands unsafely.

A reliable troubleshooting model is:

```text
Symptom
  ↓
Identify Evaluation Boundary
  ↓
Identify Event / Job / Step Context
  ↓
Inspect Expression
  ↓
Inspect Available Context
  ↓
Validate Type / Value
  ↓
Reproduce With Safe Diagnostics
  ↓
Root Cause
  ↓
Corrective Action
  ↓
Prevention
```

The most important distinction is:

```text
GitHub expression evaluation
        ≠
Shell execution
```

---

## GitHub Actions Expression Model

Expressions use:

```yaml
${{ expression }}
```

Example:

```yaml
if: ${{ github.ref == 'refs/heads/main' }}
```

Expressions can read workflow state and perform operations using contexts and functions.

Conceptually:

```text
Workflow YAML
    ↓
GitHub expression evaluation
    ↓
Resolved values
    ↓
Runner execution
    ↓
Shell / Action
```

Not every expression is evaluated at the same time or in the same context.

---

## Why Expressions Exist

Expressions allow workflows to make decisions dynamically.

Examples:

```text
Run deployment only on main
Select environment based on input
Pass a job output to another job
Generate a matrix dynamically
Run diagnostics after failure
Select configuration from workflow inputs
```

Without expressions, workflows would require large amounts of duplicated YAML.

---

## Expression Syntax

Basic expression:

```yaml
${{ github.ref }}
```

Comparison:

```yaml
${{ github.ref == 'refs/heads/main' }}
```

Logical operators:

```yaml
${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
```

Negation:

```yaml
${{ !cancelled() }}
```

Multiple conditions:

```yaml
${{
  github.event_name == 'push' &&
  github.ref == 'refs/heads/main'
}}
```

Keep complex conditions readable. If an expression becomes difficult to reason about, move part of the decision into a planning step and expose a simple output.

---

## Expressions vs Shell Commands

This distinction is fundamental.

GitHub expression:

```yaml
if: ${{ github.ref == 'refs/heads/main' }}
```

Shell command:

```yaml
run: |
  if [[ "$BRANCH" == "main" ]]; then
    echo "deploy"
  fi
```

They are evaluated by different systems.

```text
GitHub expression
        ↓
Workflow processing
        ↓
Resolved environment / command
        ↓
Shell
        ↓
Command execution
```

Do not assume shell syntax can be used directly inside an expression.

---

## Expression Evaluation vs Runtime Execution

Consider:

```yaml
- name: Test
  env:
    BRANCH: ${{ github.ref_name }}
  run: |
    echo "$BRANCH"
```

The GitHub expression resolves the value before the shell executes.

The shell receives:

```text
BRANCH=<resolved value>
```

This separation is useful for both debugging and security.

---

## Safe Data Flow

Prefer:

```yaml
- name: Print branch
  env:
    BRANCH_NAME: ${{ github.ref_name }}
  run: |
    printf 'Branch: %s\n' "$BRANCH_NAME"
```

rather than embedding potentially untrusted data directly into shell syntax.

This pattern separates:

```text
Expression Data
    ↓
Environment Variable
    ↓
Quoted Shell Expansion
```

---

## Expression Operators

Common operators include:

| Operator | Purpose |
|---|---|
| `==` | Equality |
| `!=` | Inequality |
| `&&` | Logical AND |
| `||` | Logical OR |
| `!` | Logical NOT |
| `>` | Greater than |
| `<` | Less than |
| `>=` | Greater than or equal |
| `<=` | Less than or equal |

Use parentheses when they improve readability:

```yaml
if: ${{ (github.ref == 'refs/heads/main') && github.event_name == 'push' }}
```

Avoid unnecessarily complex boolean expressions.

---

## Equality and Type Awareness

Expressions can involve strings, booleans, numbers, null-like values, and structured data.

For example:

```yaml
with:
  enabled: ${{ inputs.enabled }}
```

Do not assume that every value behaves like a shell string.

For reusable workflows and manual inputs, define input types explicitly:

```yaml
on:
  workflow_call:
    inputs:
      deploy:
        required: true
        type: boolean
```

This makes workflow contracts more predictable.

---

## Common Type Mistake

Suppose a workflow expects:

```yaml
type: boolean
```

but the implementation treats the value as a string:

```bash
if [[ "$DEPLOY" == "true" ]]; then
  ...
fi
```

This can be valid in the shell, but it obscures the original workflow-level type.

Prefer a clear boundary:

```yaml
env:
  DEPLOY: ${{ inputs.deploy }}
```

Then deliberately convert or test the value in the execution environment.

---

## `github` Context

The `github` context contains information about the workflow execution.

Common values include:

```yaml
github.repository
github.repository_owner
github.ref
github.ref_name
github.sha
github.actor
github.event_name
github.workflow
github.run_id
github.run_number
github.job
```

Example:

```yaml
- name: Show execution metadata
  env:
    REPOSITORY: ${{ github.repository }}
    REF: ${{ github.ref }}
    SHA: ${{ github.sha }}
    EVENT: ${{ github.event_name }}
  run: |
    printf 'repository=%s\n' "$REPOSITORY"
    printf 'ref=%s\n' "$REF"
    printf 'sha=%s\n' "$SHA"
    printf 'event=%s\n' "$EVENT"
```

---

## Event-Specific `github` Data

The `github.event` object depends on the triggering event.

For example:

```yaml
github.event.pull_request
```

is meaningful for pull-request events.

It should not be assumed to exist for:

```text
push
workflow_dispatch
schedule
```

A common expression failure is referencing event-specific data without checking the event type.

---

## Event-Aware Conditions

Instead of assuming PR data exists:

```yaml
if: ${{ github.event.pull_request.base.ref == 'main' }}
```

prefer an event-aware condition:

```yaml
if: >-
  ${{
    github.event_name == 'pull_request' &&
    github.event.pull_request.base.ref == 'main'
  }}
```

This makes the expected context explicit.

---

## `env` Context

The `env` context exposes environment variables configured through workflow configuration.

Example:

```yaml
env:
  APP_ENV: staging

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Show environment
        run: echo "${{ env.APP_ENV }}"
```

Environment variables can exist at:

- Workflow level
- Job level
- Step level

The most specific scope takes precedence when the same variable is defined at multiple levels.

---

## Environment Variable Precedence

Conceptually:

```text
Workflow env
    ↓
Job env
    ↓
Step env
```

A step-level value can override the broader value.

Example:

```yaml
env:
  APP_ENV: development

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      APP_ENV: staging

    steps:
      - name: Check
        env:
          APP_ENV: test
        run: echo "$APP_ENV"
```

The step receives:

```text
test
```

---

## `vars` Context

The `vars` context provides configuration variables.

Examples:

```yaml
vars.APP_ENV
vars.AWS_REGION
vars.ECR_REPOSITORY
```

Example:

```yaml
env:
  AWS_REGION: ${{ vars.AWS_REGION }}
```

Variables are appropriate for non-sensitive configuration.

Do not store credentials in variables.

Use secrets or short-lived identity mechanisms where appropriate.

---

## `secrets` Context

Secrets are referenced through:

```yaml
secrets.API_TOKEN
```

Example:

```yaml
env:
  API_TOKEN: ${{ secrets.API_TOKEN }}
```

Secrets can exist at:

- Repository scope
- Organization scope
- Environment scope

Their availability depends on the workflow context and security boundary.

---

## Secrets Are Not General Configuration

Use:

```text
vars → non-sensitive configuration
secrets → sensitive credentials
OIDC → short-lived AWS identity
```

For AWS deployments, prefer:

```text
GitHub OIDC
    ↓
AWS STS
    ↓
Temporary Credentials
```

over storing long-lived AWS access keys as GitHub secrets.

---

## Secret Availability Problems

### Symptom

A secret appears empty.

### Possible Causes

- Wrong secret name.
- Secret exists at a different scope.
- Environment secret is not associated with the job.
- Event does not provide the secret.
- Fork pull request security restrictions.
- Reusable workflow did not receive the secret.

### Safe Check

```yaml
- name: Validate token configuration
  env:
    API_TOKEN: ${{ secrets.API_TOKEN }}
  run: |
    if [[ -z "$API_TOKEN" ]]; then
      echo "API_TOKEN is unavailable"
      exit 1
    fi
```

Never print the actual secret.

---

## `steps` Context

The `steps` context exposes outputs from previous steps.

Example:

```yaml
steps:
  - id: version
    run: |
      VERSION="1.4.0"
      echo "version=$VERSION" >> "$GITHUB_OUTPUT"

  - name: Use version
    env:
      VERSION: ${{ steps.version.outputs.version }}
    run: |
      echo "$VERSION"
```

The important requirements are:

```text
Step has an id
        ↓
Step writes to GITHUB_OUTPUT
        ↓
Later step references steps.<id>.outputs.<name>
```

---

## Common Step Output Failure

Incorrect:

```yaml
- run: echo "version=1.4.0" >> "$GITHUB_OUTPUT"

- run: echo "${{ steps.version.outputs.version }}"
```

The first step has no:

```yaml
id: version
```

Correct:

```yaml
- id: version
  run: echo "version=1.4.0" >> "$GITHUB_OUTPUT"
```

---

## `$GITHUB_OUTPUT`

Modern step output communication uses:

```bash
echo "name=value" >> "$GITHUB_OUTPUT"
```

Example:

```yaml
- id: build
  name: Calculate image tag
  run: |
    IMAGE_TAG="${GITHUB_SHA}"
    echo "image_tag=$IMAGE_TAG" >> "$GITHUB_OUTPUT"
```

Then:

```yaml
- name: Show tag
  env:
    IMAGE_TAG: ${{ steps.build.outputs.image_tag }}
  run: |
    echo "$IMAGE_TAG"
```

---

## Multiline Outputs

For structured or multiline values, use the supported multiline output syntax.

Example:

```bash
{
  echo 'metadata<<EOF'
  echo '{"environment":"staging","region":"ap-south-1"}'
  echo 'EOF'
} >> "$GITHUB_OUTPUT"
```

When possible, keep outputs compact and structured rather than passing large documents through workflow expressions.

For large data, artifacts are generally a better mechanism.

---

## `needs` Context

The `needs` context exposes outputs and results from dependent jobs.

Example:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image: ${{ steps.image.outputs.image }}
    steps:
      - id: image
        run: |
          echo "image=backend:${GITHUB_SHA}" >> "$GITHUB_OUTPUT"

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - env:
          IMAGE: ${{ needs.build.outputs.image }}
        run: |
          echo "Deploying $IMAGE"
```

The data flow is:

```text
Step Output
    ↓
Job Output
    ↓
needs
    ↓
Downstream Job
```

---

## Common `needs` Failure

If a job does not declare:

```yaml
needs: build
```

then:

```yaml
needs.build.outputs.image
```

is not available as expected.

The dependency graph must match the data flow.

---

## `needs.<job>.result`

A downstream job can inspect the result of a dependency:

```yaml
if: ${{ always() }}
```

Then:

```yaml
env:
  TEST_RESULT: ${{ needs.test.result }}
```

Possible values include states such as:

```text
success
failure
cancelled
skipped
```

This is useful for reporting and conditional orchestration.

---

## `job` Context

The `job` context contains information about the current job execution.

It should not be confused with:

```yaml
needs.<job>
```

which describes upstream jobs.

A useful mental model is:

```text
job
 ↓
Current job

needs
 ↓
Dependency jobs
```

---

## `runner` Context

The `runner` context contains information about the runner.

Useful values include:

```yaml
runner.os
runner.arch
runner.name
runner.temp
runner.tool_cache
```

Example:

```yaml
- name: Runner diagnostics
  env:
    OS: ${{ runner.os }}
    ARCH: ${{ runner.arch }}
  run: |
    printf 'OS=%s\n' "$OS"
    printf 'ARCH=%s\n' "$ARCH"
```

This is useful when debugging matrix and self-hosted runner differences.

---

## `matrix` Context

The `matrix` context exposes the current matrix combination.

Example:

```yaml
strategy:
  matrix:
    python-version:
      - "3.11"
      - "3.12"

steps:
  - uses: actions/setup-python@v5
    with:
      python-version: ${{ matrix.python-version }}
```

For debugging:

```yaml
- name: Matrix diagnostics
  env:
    PYTHON_VERSION: ${{ matrix.python-version }}
  run: |
    printf 'Python=%s\n' "$PYTHON_VERSION"
```

---

## `strategy` Context

The `strategy` context provides information associated with the matrix strategy.

It becomes particularly useful when workflows need to reason about matrix execution behavior.

For most application logic, prefer exposing the specific matrix values you actually need rather than creating highly coupled conditions around strategy internals.

---

## `inputs` Context

The `inputs` context is useful for:

- `workflow_dispatch`
- `workflow_call`

Example:

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        required: true
        type: choice
        options:
          - staging
          - production
```

Use:

```yaml
${{ inputs.environment }}
```

to access the input.

---

## Manual Input Validation

Do not assume a manually supplied value is safe simply because it came from the GitHub UI.

For deployment:

```yaml
if: ${{ inputs.environment == 'staging' || inputs.environment == 'production' }}
```

For shell commands, pass it through an environment variable:

```yaml
env:
  TARGET_ENV: ${{ inputs.environment }}
run: |
  printf 'Deploying %s\n' "$TARGET_ENV"
```

Validate again before performing privileged operations.

---

## Context Availability

Not every context is available everywhere.

The correct troubleshooting question is:

```text
Is this context available in this workflow key and execution phase?
```

Do not assume that because a context works in:

```yaml
run:
```

it will work identically in:

```yaml
jobs.<job_id>.if
```

or another workflow key.

When a value behaves unexpectedly, check the supported context availability for that location.

---

## Context Availability as a Failure Domain

A useful model is:

```text
Expression
    ↓
Workflow Key
    ↓
Evaluation Phase
    ↓
Available Contexts
    ↓
Resolved Value
```

If an expression evaluates incorrectly, first identify where the expression is being evaluated.

---

## `if` Conditions

Example:

```yaml
if: ${{ github.ref == 'refs/heads/main' }}
```

Job-level:

```yaml
jobs:
  deploy:
    if: ${{ github.ref == 'refs/heads/main' }}
```

Step-level:

```yaml
steps:
  - name: Deploy
    if: ${{ github.ref == 'refs/heads/main' }}
    run: ./deploy.sh
```

The workflow can exist and start while individual jobs or steps are skipped.

---

## `if` Without Explicit Expression Syntax

GitHub Actions allows conditions in certain locations without explicitly writing `${{ }}`:

```yaml
if: github.ref == 'refs/heads/main'
```

This is valid in supported `if` contexts.

For consistency and readability, many teams still use:

```yaml
if: ${{ github.ref == 'refs/heads/main' }}
```

Do not mix styles arbitrarily within a large workflow.

---

## `success()`

`success()` is true when preceding relevant execution has succeeded.

Example:

```yaml
- name: Deploy
  if: ${{ success() && github.ref == 'refs/heads/main' }}
  run: ./deploy.sh
```

It is useful when a step should only execute after successful previous execution.

---

## `failure()`

Use `failure()` for failure-specific diagnostics or recovery behavior.

```yaml
- name: Collect diagnostics
  if: ${{ failure() }}
  run: ./scripts/collect-diagnostics.sh
```

This is appropriate for:

- Logs
- Debug artifacts
- Test reports
- Diagnostic dumps

Be careful when using it in jobs with `needs`, because upstream job state also influences execution.

---

## `cancelled()`

`cancelled()` is useful for distinguishing cancellation from failure.

Example:

```yaml
- name: Cancellation diagnostics
  if: ${{ cancelled() }}
  run: ./scripts/record-cancellation.sh
```

Cancellation often occurs because of:

- Concurrency
- Manual cancellation
- Matrix fail-fast
- Workflow replacement

Do not treat cancellation as equivalent to application failure.

---

## `always()`

`always()` is useful for cleanup or reporting:

```yaml
- name: Publish test report
  if: ${{ always() }}
  uses: actions/upload-artifact@v4
  with:
    name: test-report
    path: reports/
```

Use it deliberately because it can cause steps to execute in situations where the main pipeline has already failed or been cancelled.

---

## Status Functions and Job Dependencies

Suppose:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest

  report:
    needs: test
    if: ${{ always() }}
    runs-on: ubuntu-latest
    steps:
      - run: ./generate-report.sh
```

`report` can execute even when `test` fails because its condition overrides the normal dependency success behavior.

This is useful for reporting, not for bypassing safety boundaries.

---

## `continue-on-error` vs `failure()`

These mechanisms have different purposes.

| Mechanism | Purpose |
|---|---|
| `continue-on-error` | Change failure propagation |
| `failure()` | Detect a failure condition |
| `always()` | Run regardless of normal success/failure gating |
| `cancelled()` | Detect cancellation |
| `success()` | Require successful execution |

Do not use them interchangeably.

---

## Expression Functions

Important functions include:

```text
success()
failure()
always()
cancelled()
contains()
startsWith()
endsWith()
format()
fromJSON()
toJSON()
hashFiles()
```

Each solves a different problem.

---

## `contains()`

Example:

```yaml
if: ${{ contains(github.ref, 'release/') }}
```

For lists or structured data, use it carefully and understand what type is being tested.

A broad substring check can produce unexpected matches.

Prefer explicit comparisons where possible.

---

## `startsWith()`

Example:

```yaml
if: ${{ startsWith(github.ref, 'refs/tags/v') }}
```

Useful for release tags.

For stronger release workflows, combine the condition with an explicit event:

```yaml
if: >-
  ${{
    github.event_name == 'push' &&
    startsWith(github.ref, 'refs/tags/v')
  }}
```

---

## `endsWith()`

Example:

```yaml
if: ${{ endsWith(github.ref_name, '-staging') }}
```

Useful for naming conventions, but avoid relying on naming conventions alone for security-sensitive deployment decisions.

---

## `format()`

`format()` can construct strings.

Example:

```yaml
env:
  IMAGE: ${{ format('{0}:{1}', vars.ECR_REPOSITORY, github.sha) }}
```

For complex values, avoid deeply nested formatting expressions.

If a value is becoming difficult to read, calculate it in a step and expose it as an output.

---

## `toJSON()`

`toJSON()` can serialize structured context data.

Example:

```yaml
- name: Inspect safe metadata
  env:
    MATRIX: ${{ toJSON(matrix) }}
  run: |
    printf '%s\n' "$MATRIX"
```

Use it carefully.

Do not serialize sensitive contexts such as secrets into logs.

---

## `fromJSON()`

`fromJSON()` converts JSON text into structured workflow data.

A common use is dynamic matrices.

Planning job:

```yaml
jobs:
  plan:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.plan.outputs.matrix }}
    steps:
      - id: plan
        run: |
          echo 'matrix={"python":["3.11","3.12"]}' >> "$GITHUB_OUTPUT"

  test:
    needs: plan
    strategy:
      matrix: ${{ fromJSON(needs.plan.outputs.matrix) }}
    runs-on: ubuntu-latest
    steps:
      - run: echo "${{ matrix.python }}"
```

---

## Dynamic Matrix Failure

The following value must be valid JSON:

```text
{"python":["3.11","3.12"]}
```

Malformed JSON can prevent matrix expansion.

Debug the producer:

```yaml
- name: Show generated matrix
  env:
    MATRIX: ${{ steps.plan.outputs.matrix }}
  run: |
    printf '%s\n' "$MATRIX"
```

Then validate the JSON independently where appropriate:

```bash
python -m json.tool
```

---

## `hashFiles()`

`hashFiles()` is useful for dependency cache keys.

Example:

```yaml
key: ${{ runner.os }}-python-${{ hashFiles('**/requirements.lock') }}
```

It makes cache invalidation dependent on relevant file content.

---

## Cache Expression Failures

If a cache never invalidates when dependencies change, check:

```text
Lock file path
Glob pattern
Working repository
Hash expression
Cache key structure
```

A common mistake is hashing the wrong file.

For example:

```yaml
hashFiles('requirements.txt')
```

does not detect changes to:

```text
pyproject.toml
uv.lock
poetry.lock
```

unless those files are included in the hash.

---

## Expressions in Environment Variables

Example:

```yaml
env:
  IMAGE_TAG: ${{ github.sha }}
```

Then:

```yaml
run: docker build -t "$IMAGE_TAG" .
```

This is generally easier to reason about than embedding expressions throughout shell commands.

---

## Expressions in `run`

Avoid directly interpolating untrusted values:

```yaml
run: echo "${{ github.event.pull_request.title }}"
```

A pull request title can contain shell-sensitive characters.

Safer:

```yaml
env:
  PR_TITLE: ${{ github.event.pull_request.title }}

run: |
  printf '%s\n' "$PR_TITLE"
```

This is both clearer and safer.

---

## Shell Injection

A dangerous pattern is:

```yaml
run: |
  ./deploy.sh "${{ inputs.environment }}"
```

If an input is controlled externally, expression substitution can change the shell command itself.

Prefer:

```yaml
env:
  TARGET_ENV: ${{ inputs.environment }}
run: |
  ./deploy.sh "$TARGET_ENV"
```

Then validate:

```bash
case "$TARGET_ENV" in
  staging|production)
    ;;
  *)
    echo "Invalid environment"
    exit 1
    ;;
esac
```

---

## Expression and Secret Safety

Never use expressions to expose secrets in logs.

Avoid:

```yaml
run: echo "${{ secrets.API_TOKEN }}"
```

Even though GitHub attempts to mask secrets, masking is not a complete security boundary.

Prefer passing secrets directly to the process that needs them:

```yaml
env:
  API_TOKEN: ${{ secrets.API_TOKEN }}
run: ./deploy.sh
```

---

## Context Debugging

When debugging expressions, inspect only safe values.

Example:

```yaml
- name: Debug execution context
  env:
    EVENT: ${{ github.event_name }}
    REF: ${{ github.ref }}
    SHA: ${{ github.sha }}
    JOB: ${{ github.job }}
    RUNNER_OS: ${{ runner.os }}
    RUNNER_ARCH: ${{ runner.arch }}
  run: |
    printf 'event=%s\n' "$EVENT"
    printf 'ref=%s\n' "$REF"
    printf 'sha=%s\n' "$SHA"
    printf 'job=%s\n' "$JOB"
    printf 'runner_os=%s\n' "$RUNNER_OS"
    printf 'runner_arch=%s\n' "$RUNNER_ARCH"
```

Avoid dumping:

```yaml
toJSON(github)
```

in production workflows because the context can contain sensitive or untrusted information.

---

## Expression Debugging Workflow

### Symptom

A deployment job is unexpectedly skipped.

### Possible Causes

```text
Wrong branch
Wrong event
Wrong input
Wrong environment
Wrong needs result
Wrong boolean comparison
Unavailable context
```

### Isolation Strategy

Expose the decision inputs:

```yaml
- name: Debug deployment decision
  env:
    EVENT: ${{ github.event_name }}
    REF: ${{ github.ref }}
    ENVIRONMENT: ${{ inputs.environment }}
  run: |
    printf 'event=%s\n' "$EVENT"
    printf 'ref=%s\n' "$REF"
    printf 'environment=%s\n' "$ENVIRONMENT"
```

Then compare the actual values against the expression.

### Root Cause

Determine which operand differs from the expected value.

### Corrective Action

Simplify or correct the expression.

### Prevention

Use clear inputs, outputs, and explicit conditions instead of deeply nested expressions.

---

## Job Decision Example

Consider:

```yaml
jobs:
  deploy:
    if: >-
      ${{
        github.event_name == 'push' &&
        github.ref == 'refs/heads/main' &&
        needs.test.result == 'success'
      }}
```

Potential problem:

```text
needs.test
```

requires the job to declare:

```yaml
needs: test
```

Correct:

```yaml
deploy:
  needs: test
  if: >-
    ${{
      github.event_name == 'push' &&
      github.ref == 'refs/heads/main' &&
      needs.test.result == 'success'
    }}
```

---

## Matrix + `needs`

A common architecture is:

```text
Plan
 ↓
Dynamic Matrix
 ↓
Parallel Tests
 ↓
Build
```

Example:

```yaml
jobs:
  plan:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.matrix.outputs.value }}
    steps:
      - id: matrix
        run: |
          echo 'value={"python":["3.11","3.12"]}' >> "$GITHUB_OUTPUT"

  test:
    needs: plan
    strategy:
      matrix: ${{ fromJSON(needs.plan.outputs.matrix) }}
    runs-on: ubuntu-latest
    steps:
      - run: python --version

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: echo "build"
```

The data and dependency flow must align:

```text
plan output
    ↓
needs.plan.outputs.matrix
    ↓
fromJSON()
    ↓
matrix
```

---

## Matrix Output Problems

Matrix jobs require careful output design.

If multiple matrix executions produce the same logical output name, the final value may not represent all combinations in the way you expect.

For aggregation, prefer:

```text
Matrix jobs
    ↓
Artifacts / uniquely named outputs
    ↓
Aggregation job
```

rather than assuming a single matrix output can represent all results.

---

## Structured Data Between Jobs

Use JSON when passing structured configuration:

```json
{
  "environment": "staging",
  "region": "ap-south-1",
  "services": [
    "users",
    "orders"
  ]
}
```

Workflow pattern:

```text
Planning Job
    ↓
JSON Output
    ↓
fromJSON()
    ↓
Matrix / Conditional Jobs
```

This is powerful but increases complexity.

Validate generated JSON before consuming it.

---

## Expression Complexity

Avoid:

```yaml
if: >-
  ${{
    github.event_name == 'push' &&
    github.ref == 'refs/heads/main' &&
    (vars.DEPLOY_ENABLED == 'true') &&
    needs.security.result == 'success' &&
    needs.integration.result == 'success' &&
    contains(fromJSON(needs.plan.outputs.services), 'backend')
  }}
```

This is difficult to troubleshoot.

Prefer a planning job:

```text
Inputs
 ↓
Deployment Decision
 ↓
Simple Output
 ↓
Deployment Job
```

For example:

```yaml
outputs:
  deploy: ${{ steps.decision.outputs.deploy }}
```

Then:

```yaml
if: ${{ needs.plan.outputs.deploy == 'true' }}
```

---

## Planning Jobs

A planning job centralizes decision logic.

```mermaid
flowchart TD
    A[Event] --> B[Planning Job]
    B --> C[Change Detection]
    B --> D[Environment Decision]
    B --> E[Matrix Generation]
    B --> F[Deployment Decision]

    C --> G[Tests]
    E --> G
    F --> H[Deployment]

    G --> H
```

Advantages:

- Easier debugging
- Smaller job conditions
- Structured outputs
- Better observability
- Clear dependency graph

Trade-off:

- Additional workflow complexity
- More output contracts
- Planning logic becomes important infrastructure

---

## Contexts and Reusable Workflows

Reusable workflows define explicit contracts.

Example:

```yaml
on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
    secrets:
      AWS_ROLE_ARN:
        required: true
```

Caller:

```yaml
jobs:
  deploy:
    uses: org/platform/.github/workflows/deploy.yml@v1
    with:
      environment: staging
    secrets:
      AWS_ROLE_ARN: ${{ secrets.AWS_ROLE_ARN }}
```

Do not assume every caller context is automatically available inside the reusable workflow.

Pass required information explicitly through:

- Inputs
- Secrets
- Workflow/job outputs
- Repository/environment configuration

---

## `secrets: inherit`

For trusted reusable workflows, secrets can be inherited:

```yaml
jobs:
  deploy:
    uses: org/platform/.github/workflows/deploy.yml@v1
    secrets: inherit
```

This simplifies configuration but broadens the secret interface.

Use explicit secrets where practical, especially for security-sensitive reusable workflows.

---

## Contexts in Composite Actions

Composite actions execute steps inside the calling job.

Inputs should be declared explicitly:

```yaml
inputs:
  environment:
    required: true
    description: Deployment environment
```

Then:

```yaml
steps:
  - shell: bash
    env:
      TARGET_ENV: ${{ inputs.environment }}
    run: |
      echo "$TARGET_ENV"
```

Do not design composite actions around hidden assumptions about repository-specific context.

---

## Expression Problems in Custom Actions

When an action receives an unexpected value, determine whether the problem occurred in:

```text
Caller Expression
    ↓
Action Input
    ↓
Action Runtime
    ↓
Shell / Node / Docker
```

For JavaScript actions, log safe normalized inputs.

For composite actions, use explicit environment variables.

For Docker actions, verify how inputs are mapped into the container.

---

## Environment Selection

A production deployment often has:

```text
development
staging
production
```

Avoid deriving privileged deployment decisions solely from user-controlled strings.

A safer model is:

```text
Input
 ↓
Allowlist Validation
 ↓
Environment Selection
 ↓
Environment Protection
 ↓
Deployment
```

Example:

```yaml
if: ${{ inputs.environment == 'staging' }}
```

and a separate protected production path.

---

## Expression-Driven AWS Deployment

Example:

```yaml
env:
  AWS_REGION: ${{ vars.AWS_REGION }}
  ECR_REPOSITORY: ${{ vars.ECR_REPOSITORY }}
  IMAGE_TAG: ${{ github.sha }}
```

Then:

```bash
aws ecr get-login-password --region "$AWS_REGION" |
  docker login \
    --username AWS \
    --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
```

Keep configuration resolution separate from command execution.

---

## Expression-Driven Docker Image Identity

Prefer immutable identity:

```yaml
env:
  IMAGE_TAG: ${{ github.sha }}
```

Then:

```bash
docker build \
  -t "$REGISTRY/$IMAGE_REPOSITORY:$IMAGE_TAG" \
  .
```

This makes artifact identity traceable to:

```text
Git commit
    ↓
CI run
    ↓
Docker image
    ↓
Deployment
```

---

## Expression and Artifact Promotion

A production workflow can pass an image digest through job outputs:

```text
Build
 ↓
Image Digest
 ↓
Job Output
 ↓
Staging
 ↓
Approval
 ↓
Production
```

Example:

```yaml
outputs:
  image_digest: ${{ steps.push.outputs.digest }}
```

Downstream:

```yaml
env:
  IMAGE_DIGEST: ${{ needs.build.outputs.image_digest }}
```

This is safer than reconstructing artifact identity from mutable tags.

---

## Expression and Deployment Concurrency

Expressions can be used to construct concurrency groups:

```yaml
concurrency:
  group: deploy-${{ inputs.environment }}
  cancel-in-progress: false
```

This can serialize:

```text
staging deployments
```

separately from:

```text
production deployments
```

Be deliberate about the group key.

An overly broad group can block unrelated deployments.

An overly narrow group may allow races.

---

## Common Context Mistakes

### Using PR Context on Push

```yaml
github.event.pull_request.number
```

may not exist on a normal push event.

### Forgetting `needs`

Referencing:

```yaml
needs.build.outputs.image
```

without:

```yaml
needs: build
```

is a dependency-design error.

### Missing Step ID

```yaml
steps.build.outputs.image
```

requires the producing step to have:

```yaml
id: build
```

### Printing Secrets

Never use context debugging as an excuse to expose credentials.

### Treating `vars` as Secrets

Variables are not a replacement for secrets.

### Treating Expressions as Shell

GitHub expressions and shell syntax are different languages.

### Embedding Untrusted Values in Shell

Use environment variables and quoted expansion.

### Overly Complex Conditions

Move decision logic into a planning job when conditions become difficult to reason about.

---

## Troubleshooting by Failure Domain

### Expression Syntax Error

**Symptom**

Workflow validation fails.

**Possible Causes**

- Invalid operator
- Missing delimiter
- Malformed expression
- Unsupported expression location

**Isolation**

Validate the expression and simplify it.

**Corrective Action**

Break the expression into smaller conditions.

**Prevention**

Keep expressions readable and use planning outputs for complex decisions.

---

### Unexpected Empty Value

**Symptom**

A variable appears empty.

**Possible Causes**

- Wrong context
- Missing secret
- Missing output
- Incorrect scope
- Event-specific field unavailable

**Checks**

```yaml
env:
  VALUE: ${{ ... }}
run: |
  if [[ -z "$VALUE" ]]; then
    echo "Value is empty"
    exit 1
  fi
```

---

### Job Unexpectedly Skipped

**Symptom**

Job shows `skipped`.

**Possible Causes**

- `if` condition false
- `needs` failure
- `needs` skipped
- Matrix exclusion
- Event mismatch

**Isolation**

Inspect:

```text
if
needs
event
matrix
```

---

### Step Unexpectedly Skipped

**Symptom**

Previous step succeeds but a later step does not run.

**Possible Causes**

- Step-level `if`
- Previous failure
- `continue-on-error` behavior
- Cancellation
- Status function

**Isolation**

Inspect the exact step condition and preceding step state.

---

### Dynamic Matrix Failure

**Symptom**

Matrix job fails to expand.

**Possible Causes**

- Invalid JSON
- Wrong output name
- Missing `needs`
- Incorrect `fromJSON()`
- Empty matrix

**Checks**

```bash
python -m json.tool
```

Validate the exact generated JSON.

---

### Output Missing

**Symptom**

Downstream job receives an empty output.

**Checks**

```text
Producer step has id?
 ↓
Writes to GITHUB_OUTPUT?
 ↓
Job declares output?
 ↓
Downstream declares needs?
 ↓
Output reference correct?
```

---

### Incorrect Boolean Behavior

**Symptom**

A condition behaves unexpectedly.

**Possible Causes**

- String vs boolean
- Manual input type
- Environment variable conversion
- Incorrect comparison

**Isolation**

Expose the value safely and verify the input contract.

---

## Practical Diagnostic Template

Use this pattern for difficult expression failures:

```yaml
- name: Expression diagnostics
  env:
    EVENT: ${{ github.event_name }}
    REF: ${{ github.ref }}
    REF_NAME: ${{ github.ref_name }}
    SHA: ${{ github.sha }}
    ENVIRONMENT: ${{ inputs.environment }}
    APP_ENV: ${{ vars.APP_ENV }}
  run: |
    set -euo pipefail

    printf 'event=%s\n' "$EVENT"
    printf 'ref=%s\n' "$REF"
    printf 'ref_name=%s\n' "$REF_NAME"
    printf 'sha=%s\n' "$SHA"
    printf 'environment=%s\n' "$ENVIRONMENT"
    printf 'app_env=%s\n' "$APP_ENV"
```

This turns an opaque expression problem into observable input data.

---

## Expression Debugging With Python

For generated JSON:

```yaml
- name: Validate matrix JSON
  env:
    MATRIX_JSON: ${{ steps.plan.outputs.matrix }}
  run: |
    python - <<'PY'
    import json
    import os

    value = os.environ["MATRIX_JSON"]
    parsed = json.loads(value)
    print(json.dumps(parsed, indent=2))
    PY
```

This is useful when dynamic matrices are generated by Python scripts.

---

## Expression Debugging With `toJSON`

For safe, non-sensitive structures:

```yaml
- name: Debug matrix
  env:
    MATRIX: ${{ toJSON(matrix) }}
  run: |
    printf '%s\n' "$MATRIX"
```

Do not apply this blindly to:

```text
secrets
authentication tokens
sensitive event payloads
```

---

## Production Example: Python Matrix

```yaml
jobs:
  test:
    strategy:
      fail-fast: false
      matrix:
        python-version:
          - "3.11"
          - "3.12"

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: python -m pytest
```

The expression:

```yaml
${{ matrix.python-version }}
```

is resolved by GitHub before the setup action executes.

---

## Production Example: Django + PostgreSQL + Redis

```yaml
jobs:
  integration:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_USER: app
          POSTGRES_PASSWORD: test-password
          POSTGRES_DB: app_test
        options: >-
          --health-cmd="pg_isready -U app -d app_test"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5

      redis:
        image: redis:7
        options: >-
          --health-cmd="redis-cli ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Django checks
        env:
          DATABASE_URL: postgresql://app:test-password@localhost:5432/app_test
          REDIS_URL: redis://localhost:6379/0
        run: |
          python manage.py check
          python manage.py migrate --noinput
          python manage.py test
```

Expressions configure runtime values; the shell and application consume them.

---

## Production Example: Build Output to Deployment

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image: ${{ steps.meta.outputs.image }}

    steps:
      - id: meta
        env:
          REGISTRY: ${{ vars.ECR_REGISTRY }}
          REPOSITORY: ${{ vars.ECR_REPOSITORY }}
          SHA: ${{ github.sha }}
        run: |
          echo "image=${REGISTRY}/${REPOSITORY}:${SHA}" >> "$GITHUB_OUTPUT"

  deploy:
    needs: build
    runs-on: ubuntu-latest

    steps:
      - name: Deploy image
        env:
          IMAGE: ${{ needs.build.outputs.image }}
        run: |
          echo "Deploying $IMAGE"
```

The important data flow is:

```text
github.sha
    ↓
Step Environment
    ↓
GITHUB_OUTPUT
    ↓
Job Output
    ↓
needs.build.outputs.image
    ↓
Deployment
```

---

## Production Example: Conditional Deployment

```yaml
deploy:
  needs:
    - test
    - security

  if: >-
    ${{
      github.event_name == 'push' &&
      github.ref == 'refs/heads/main' &&
      needs.test.result == 'success' &&
      needs.security.result == 'success'
    }}

  runs-on: ubuntu-latest
```

This is appropriate when the deployment must only follow successful validation.

If the expression becomes significantly more complex, introduce a planning job.

---

## Expression Design Guidelines

Prefer:

```text
Simple expression
    ↓
Explicit inputs
    ↓
Explicit outputs
    ↓
Clear dependency graph
```

Avoid:

```text
Large nested expression
    ↓
Multiple contexts
    ↓
Multiple event assumptions
    ↓
Hidden type conversions
    ↓
Difficult debugging
```

The goal is not to minimize the number of lines of YAML. The goal is to minimize ambiguity.

---

## Security Considerations

Expressions are part of the workflow's security boundary.

Potentially untrusted values include:

- Pull request titles
- Branch names
- Commit messages
- Issue content
- Manual inputs
- Repository dispatch payloads
- External API responses

Unsafe:

```yaml
run: |
  echo "${{ github.event.pull_request.title }}"
```

Safer:

```yaml
env:
  TITLE: ${{ github.event.pull_request.title }}
run: |
  printf '%s\n' "$TITLE"
```

For privileged workflows, validate values before using them to select:

- AWS accounts
- Environments
- Docker images
- Deployment targets
- Shell commands
- Kubernetes resources

---

## `pull_request_target` and Expressions

`pull_request_target` deserves particular caution because the workflow executes with the base repository's trust context.

Never combine:

```text
Privileged workflow
+
Secrets
+
Untrusted PR-controlled values
+
Unsafe shell interpolation
```

without deliberate isolation.

The expression layer can become an attack path if untrusted data is transformed into executable shell syntax.

---

## AWS OIDC and Context Restrictions

OIDC trust policies can restrict identity using claims associated with the workflow context.

The overall model is:

```text
GitHub Event
    ↓
Workflow Identity
    ↓
OIDC Token
    ↓
AWS STS
    ↓
IAM Trust Policy
    ↓
Temporary Credentials
```

The workflow should not rely on a generic AWS role if the role can be restricted to:

```text
Repository
Branch
Environment
Workflow identity
```

Use least privilege at both the GitHub and AWS layers.

---

## Performance Considerations

Complex expression logic can make workflows harder to maintain and increase planning complexity.

For large repositories:

```text
Event
 ↓
Planning
 ↓
Change Detection
 ↓
Dynamic Matrix
 ↓
Parallel Jobs
```

This can reduce unnecessary execution.

However, excessive dynamic logic can itself become a reliability problem.

Use planning jobs when the complexity provides measurable operational value.

---

## Scalability Considerations

At enterprise scale, expression-driven decisions may determine:

```text
Which repositories run
Which services test
Which matrix combinations execute
Which environments deploy
Which artifacts promote
```

A centralized reusable workflow can standardize these decisions:

```text
Repository
    ↓
Reusable Workflow
    ↓
Standard Planning
    ↓
Standard Security
    ↓
Standard Testing
    ↓
Standard Deployment
```

Keep repository-specific decisions exposed through explicit inputs and outputs.

---

## Reliability Considerations

Reliable expressions should be:

- Deterministic
- Explicit
- Type-aware
- Event-aware
- Easy to inspect
- Small enough to understand

Avoid relying on accidental behavior such as:

```text
Missing value → implicit fallback → deployment
```

For production deployments, fail closed:

```text
Unknown environment
    ↓
Reject deployment
```

rather than:

```text
Unknown environment
    ↓
Guess default
    ↓
Deploy
```

---

## Common Production Pitfalls

### Context Exists in One Event but Not Another

A push workflow and pull-request workflow do not have identical event payloads.

### Complex Expressions Hide Failure Causes

A single expression containing ten conditions is difficult to diagnose.

### Outputs Are Not Automatically Available Everywhere

Data must move through supported output and dependency mechanisms.

### `toJSON()` Can Leak Sensitive Data

Do not serialize entire contexts indiscriminately.

### Manual Inputs Are Still User Input

Validate them before privileged operations.

### Cache Keys Use the Wrong Files

A correct `hashFiles()` call must represent the dependencies that actually affect the cache.

### Matrix Data Is Treated as Static

Dynamic matrices require valid JSON and correct output wiring.

### Environment Variables Hide Type Semantics

Everything arriving through a shell environment is handled as shell data, even when the source was a typed workflow input.

---

## Architecture Pattern: Planning and Execution

A scalable workflow can separate decision-making from execution:

```mermaid
flowchart TD
    A[Event] --> B[Planning Job]

    B --> C[Event Validation]
    B --> D[Change Detection]
    B --> E[Environment Selection]
    B --> F[Dynamic Matrix]
    B --> G[Deployment Decision]

    C --> H[Test Matrix]
    D --> H
    F --> H

    H --> I[Build]
    I --> J[Immutable Artifact]
    G --> K[Deployment]
    J --> K

    K --> L[Health Validation]
    L --> M[Monitoring]
```

This architecture makes the decision boundary observable.

---

## Architecture Pattern: Artifact Promotion

```mermaid
flowchart LR
    A[Git Commit] --> B[Build]
    B --> C[Image Digest]
    C --> D[ECR]
    D --> E[Staging]
    E --> F[Approval]
    F --> G[Production]

    B -. metadata .-> H[Job Output]
    H -. immutable identity .-> E
    H -. immutable identity .-> G
```

Expressions and contexts should transport artifact identity without reconstructing it inconsistently.

---

## GitHub CLI for Expression Troubleshooting

List workflows:

```bash
gh workflow list
```

Inspect workflow:

```bash
gh workflow view <workflow>
```

List runs:

```bash
gh run list
```

Inspect run:

```bash
gh run view <run-id>
```

Inspect failed logs:

```bash
gh run view <run-id> --log-failed
```

Rerun failed jobs:

```bash
gh run rerun <run-id> --failed
```

For expression problems, the CLI is most useful for establishing:

```text
Did the workflow run?
Which event triggered it?
Which job was skipped?
Which step failed?
```

---

## Diagnostic Decision Tree

```text
Expression Problem
       ↓
Did workflow start?
   ├── No → Trigger/configuration
   └── Yes
        ↓
Did job start?
   ├── No → if / needs / matrix
   └── Yes
        ↓
Did step start?
   ├── No → step if / previous failure
   └── Yes
        ↓
Was value correct?
   ├── No → context / scope / type
   └── Yes
        ↓
Did shell/action fail?
   ├── Yes → runtime diagnosis
   └── No → inspect downstream data flow
```

---

## Interview Scenarios

### A Job Is Unexpectedly Skipped

Explain how you would inspect:

```text
if
needs
event
matrix
status functions
```

Do not immediately change the condition.

---

### A Step Output Is Empty

Trace:

```text
Step ID
 ↓
GITHUB_OUTPUT
 ↓
Step Output
 ↓
Job Output
 ↓
needs
```

Identify the exact boundary where the value disappears.

---

### A Dynamic Matrix Fails

Trace:

```text
Planning Script
 ↓
JSON
 ↓
GITHUB_OUTPUT
 ↓
Job Output
 ↓
needs
 ↓
fromJSON()
 ↓
matrix
```

Validate JSON independently.

---

### A Deployment Condition Uses PR Data

Ask:

```text
Which event triggers the workflow?
```

If the workflow can also run on `push`, PR-specific fields may not exist.

Make the condition event-aware.

---

### A Shell Command Uses a PR Title

Explain why:

```yaml
run: echo "${{ github.event.pull_request.title }}"
```

is unsafe.

Use:

```yaml
env:
  PR_TITLE: ${{ github.event.pull_request.title }}
run: |
  printf '%s\n' "$PR_TITLE"
```

Then explain validation and shell quoting.

---

### A Production Workflow Receives an Environment Input

Design:

```text
Manual Input
 ↓
Allowlist
 ↓
Environment Selection
 ↓
Environment Protection
 ↓
OIDC
 ↓
Deployment
```

Do not allow arbitrary strings to select privileged infrastructure.

---

### A Workflow Works on Push but Fails on Pull Request

Investigate:

```text
Event payload
Secrets availability
Permissions
Ref semantics
Changed checkout behavior
Context availability
Fork security model
```

The workflow is running under a different event context.

---

### Multiple Repositories Need the Same Expression Logic

Move shared orchestration into a reusable workflow.

Expose:

```text
Inputs
Secrets
Outputs
```

rather than copying complex expressions into every repository.

---

### A Matrix Job Produces Different Results

Explain why aggregation should usually use:

```text
Unique artifact names
+
Aggregation job
```

rather than assuming a single output automatically represents every matrix execution.

---

## Production Review Checklist

### Expressions

```text
[ ] Expressions are readable
[ ] Conditions are explicit
[ ] Event-specific contexts are guarded
[ ] Types are understood
[ ] Complex logic is centralized
```

### Contexts

```text
[ ] github context used correctly
[ ] env scope understood
[ ] vars used only for non-sensitive configuration
[ ] secrets protected
[ ] steps outputs have IDs
[ ] needs dependencies are explicit
[ ] matrix values are correct
[ ] inputs are validated
```

### Data Flow

```text
[ ] GITHUB_OUTPUT used correctly
[ ] Job outputs declared
[ ] needs used correctly
[ ] JSON validated
[ ] Artifacts used for large data
```

### Security

```text
[ ] Untrusted values do not become shell syntax
[ ] Secrets are never printed
[ ] Manual inputs are validated
[ ] OIDC trust is restricted
[ ] Privileged workflows isolate untrusted code
```

### Reliability

```text
[ ] Conditions fail closed
[ ] Matrix failures are observable
[ ] Planning decisions are debuggable
[ ] Deployment decisions are deterministic
[ ] Immutable artifact identity is preserved
```

---

## Key Takeaways

- GitHub Actions expressions and shell commands are **different evaluation systems**; understanding where and when each value is resolved is the foundation of reliable troubleshooting.
- Treat contexts as explicit data sources: `github`, `env`, `vars`, `secrets`, `steps`, `needs`, `matrix`, `runner`, `strategy`, and `inputs` have different scopes and availability.
- Trace workflow data through **step output → job output → `needs` → downstream job**, and validate dynamic JSON before using `fromJSON()` for matrices or structured configuration.
- Keep conditions simple, event-aware, type-conscious, and security-conscious; move complex decisions into planning jobs and never allow untrusted context data to become executable shell syntax.
- For production CI/CD, use expressions to make **artifact identity, environment selection, concurrency, approvals, AWS OIDC, and deployment decisions explicit and deterministic**.