# 13- Artifacts

## Overview

GitHub Actions artifacts provide persistent file storage for workflow outputs. They are designed to move files between jobs, preserve build and test results, and make important workflow outputs available after execution.

Artifacts are particularly useful when a workflow is split into multiple jobs:

```text
Build
  ↓
Generate files
  ↓
Upload Artifact
  ↓
Download Artifact
  ↓
Deploy / Inspect / Publish
```

Typical backend CI/CD artifacts include:

- Test reports
- Coverage reports
- Compiled packages
- Application bundles
- Docker metadata
- Generated documentation
- Debug logs
- Configuration snapshots
- Security scan reports
- Deployment manifests

Artifacts are different from caches. An artifact represents a workflow output that should be retained and consumed intentionally. A cache exists primarily to avoid repeating expensive dependency or build work.

The existing CI/CD notes use artifacts for test and build outputs while keeping container images versioned separately in Amazon ECR. :chatgpt-content-reference{index="0"}

---

## What Is a GitHub Actions Artifact?

An artifact is a collection of files uploaded from a workflow run and stored by GitHub Actions.

For example:

```yaml
- name: Upload test report
  uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: test-results.xml
```

The workflow produces:

```text
test-results.xml
```

and stores it as:

```text
Artifact
└── test-results
    └── test-results.xml
```

Another job can download it:

```yaml
- name: Download test report
  uses: actions/download-artifact@v5
  with:
    name: test-results
```

This allows the second job to access files produced by the first job even though the jobs may execute on different runners.

---

## Why Artifacts Exist

GitHub-hosted runners are ephemeral.

A simplified lifecycle is:

```text
Job starts
    ↓
Runner allocated
    ↓
Repository checked out
    ↓
Commands execute
    ↓
Files generated
    ↓
Job finishes
    ↓
Runner discarded
```

Files created directly on the runner should not be treated as durable workflow state.

Artifacts provide an explicit persistence boundary:

```text
Runner A
   │
   │ upload
   ▼
GitHub Actions Artifact Storage
   │
   │ download
   ▼
Runner B
```

This is why artifacts are useful for multi-job pipelines.

---

## Artifact Lifecycle

A typical artifact lifecycle is:

```mermaid
flowchart LR
    A[Workflow Step] --> B[Generate Files]
    B --> C[Upload Artifact]
    C --> D[Artifact Storage]
    D --> E[Download Artifact]
    E --> F[Consume Files]
    D --> G[Retain Until Expiration]
```

The workflow controls when an artifact is produced and consumed, while artifact retention determines how long it remains available.

---

## Artifact vs Working Directory

Files created within a job are normally available to later steps in that same job.

```yaml
steps:
  - name: Generate report
    run: |
      pytest --junitxml=test-results.xml

  - name: Inspect report
    run: |
      ls -lh test-results.xml
```

No artifact is required because both steps execute within the same job.

Artifacts become useful when the file must cross a job boundary:

```text
Job A
  ↓
test-results.xml
  ↓
Artifact
  ↓
Job B
  ↓
test-results.xml
```

---

## Artifact vs Cache

Artifacts and caches are frequently confused.

They have different purposes.

| Feature | Artifact | Cache |
|---|---|---|
| Primary purpose | Store workflow outputs | Reuse expensive-to-create data |
| Typical content | Reports, packages, binaries | Dependencies, build caches |
| Intended consumer | Humans or later jobs | Future workflow runs |
| Lifecycle | Explicit workflow output | Cache lifecycle |
| Correctness dependency | Often yes | Usually no |
| Example | `coverage.xml` | pip download cache |
| Deployment use | Common | Usually inappropriate |
| Debugging use | Common | Not intended |

A useful rule is:

```text
Artifact = output

Cache = acceleration
```

Do not use a cache as a substitute for an artifact.

---

## Uploading Artifacts

The standard mechanism is `actions/upload-artifact`.

Example:

```yaml
- name: Upload test results
  uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: test-results.xml
```

The `name` identifies the artifact.

The `path` identifies the files or directories to upload.

---

## Uploading Multiple Files

Multiple paths can be included.

```yaml
- name: Upload test outputs
  uses: actions/upload-artifact@v4
  with:
    name: test-output
    path: |
      test-results.xml
      coverage.xml
      htmlcov/
```

A more structured project may use:

```text
artifacts/
├── junit/
├── coverage/
├── security/
└── logs/
```

and upload a directory:

```yaml
- name: Upload CI artifacts
  uses: actions/upload-artifact@v4
  with:
    name: ci-results
    path: artifacts/
```

---

## Artifact Naming

Artifact names should communicate their purpose.

Good:

```text
unit-test-results
coverage-report
security-scan
python-package
deployment-manifest
```

Avoid vague names such as:

```text
files
output
data
artifact
```

For matrix jobs, artifact names should normally include the matrix dimension.

Example:

```yaml
- name: Upload test results
  uses: actions/upload-artifact@v4
  with:
    name: test-results-python-${{ matrix.python-version }}
    path: test-results.xml
```

This prevents ambiguity when several matrix jobs produce similarly named outputs.

---

## Artifact Paths

Paths are interpreted relative to the workspace unless an appropriate absolute path is provided.

Example:

```yaml
- name: Upload coverage
  uses: actions/upload-artifact@v4
  with:
    name: coverage
    path: coverage.xml
```

Directory:

```yaml
- name: Upload reports
  uses: actions/upload-artifact@v4
  with:
    name: reports
    path: reports/
```

Multiple paths:

```yaml
- name: Upload reports
  uses: actions/upload-artifact@v4
  with:
    name: reports
    path: |
      reports/
      logs/
```

Keep artifact paths deterministic.

A common production pattern is:

```text
workspace/
├── src/
├── tests/
├── reports/
│   ├── junit.xml
│   └── coverage.xml
└── artifacts/
```

Then the workflow can explicitly upload the generated output.

---

## Artifact Path Validation

An important operational practice is to fail clearly when an expected artifact does not exist.

For example:

```yaml
- name: Verify reports
  shell: bash
  run: |
    test -f reports/junit.xml
    test -f reports/coverage.xml

- name: Upload reports
  uses: actions/upload-artifact@v4
  with:
    name: test-reports
    path: |
      reports/junit.xml
      reports/coverage.xml
```

This prevents a workflow from appearing successful while silently producing incomplete outputs.

Whether missing paths should fail the upload should be an explicit pipeline decision rather than an accidental behavior.

---

## Uploading Test Reports

A Python backend commonly generates JUnit-compatible reports.

```yaml
- name: Run tests
  run: |
    mkdir -p reports
    pytest \
      --junitxml=reports/junit.xml \
      --cov=. \
      --cov-report=xml:reports/coverage.xml

- name: Upload test reports
  if: ${{ !cancelled() }}
  uses: actions/upload-artifact@v4
  with:
    name: python-test-reports
    path: reports/
```

This creates a durable record of the test execution.

Typical contents:

```text
python-test-reports/
├── junit.xml
└── coverage.xml
```

The artifact can then be downloaded for investigation or processed by another job.

---

## Django Testing Example

A Django CI job can generate test and coverage artifacts:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"
          cache: pip

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-django pytest-cov

      - name: Run tests
        run: |
          mkdir -p reports
          pytest \
            --junitxml=reports/junit.xml \
            --cov=. \
            --cov-report=xml:reports/coverage.xml

      - name: Upload test artifacts
        if: ${{ !cancelled() }}
        uses: actions/upload-artifact@v4
        with:
          name: django-test-results
          path: reports/
```

This keeps test execution and test-result persistence separate.

---

## FastAPI Testing Example

For FastAPI:

```yaml
- name: Run API tests
  run: |
    mkdir -p reports
    pytest \
      tests/ \
      --junitxml=reports/junit.xml \
      --cov=app \
      --cov-report=xml:reports/coverage.xml

- name: Upload API test reports
  if: ${{ !cancelled() }}
  uses: actions/upload-artifact@v4
  with:
    name: fastapi-test-results
    path: reports/
```

This is useful for both unit and integration test pipelines.

---

## Artifacts with PostgreSQL and Redis

A realistic backend integration pipeline may look like:

```text
Python Application
       ↓
PostgreSQL
       ↓
Redis
       ↓
pytest
       ↓
Coverage
       ↓
Test Reports
       ↓
Artifact
```

Example:

```yaml
jobs:
  integration-test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: app_test
        options: >-
          --health-cmd "pg_isready -U test -d app_test"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"
          cache: pip

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/app_test
          REDIS_URL: redis://localhost:6379/0
        run: |
          mkdir -p reports
          pytest \
            tests/integration \
            --junitxml=reports/integration.xml \
            --cov=app \
            --cov-report=xml:reports/coverage.xml

      - name: Upload integration reports
        if: ${{ !cancelled() }}
        uses: actions/upload-artifact@v4
        with:
          name: integration-test-results
          path: reports/
```

The artifact captures the result of the integration test job independently from the runner that executed it.

---

## Downloading Artifacts

Use `actions/download-artifact` to retrieve artifacts.

Example:

```yaml
- name: Download test reports
  uses: actions/download-artifact@v5
  with:
    name: test-results
    path: downloaded-reports/
```

The files become available in:

```text
downloaded-reports/
```

---

## Passing Artifacts Between Jobs

A common fan-out/fan-in pipeline is:

```mermaid
flowchart TD
    A[Build / Test] --> B[Upload Artifact]
    B --> C[Build Job]
    B --> D[Analysis Job]
    C --> E[Deployment]
    D --> E
```

More commonly:

```text
Test Job
   ↓
Upload Reports
   ↓
Artifact Storage
   ↓
Report Job
   ↓
Download Reports
```

Example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Generate report
        run: |
          mkdir -p reports
          pytest --junitxml=reports/junit.xml

      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: junit-report
          path: reports/junit.xml

  inspect:
    needs: test
    runs-on: ubuntu-latest

    steps:
      - name: Download report
        uses: actions/download-artifact@v5
        with:
          name: junit-report
          path: reports/

      - name: Inspect report
        run: |
          ls -lh reports/
```

The jobs do not need to run on the same physical runner.

---

## Artifact Promotion

Artifacts can be used to implement a build-once, promote-later model.

```text
Build
  ↓
Generate Artifact
  ↓
Staging
  ↓
Validation
  ↓
Approval
  ↓
Production
```

For example, a Python package can be built once:

```yaml
- name: Build package
  run: |
    python -m build --wheel --sdist

- name: Upload package
  uses: actions/upload-artifact@v4
  with:
    name: python-package
    path: dist/
```

A later deployment job downloads exactly that package.

```yaml
- name: Download package
  uses: actions/download-artifact@v5
  with:
    name: python-package
    path: dist/
```

This avoids rebuilding different binaries for different environments.

---

## Docker Artifacts vs Docker Images

A Docker image can technically be exported as a file and uploaded as an artifact, but this is usually not the preferred production distribution model.

For production container deployments:

```text
Docker Build
    ↓
Container Image
    ↓
Amazon ECR
    ↓
ECS
```

The existing ECS CI/CD notes use Amazon ECR as the image registry and recommend versioned images for reliable deployment and rollback. :chatgpt-content-reference{index="1"}

Artifacts are better suited for:

```text
Docker metadata
Build manifests
SBOM files
Scan reports
Debug bundles
Test results
```

The production container image itself should generally live in a container registry.

---

## Build Artifacts

Build artifacts can include:

- Python wheels
- Source distributions
- JavaScript bundles
- Compiled binaries
- Static assets
- Deployment manifests
- Helm packages
- Infrastructure plans
- Generated documentation

Example:

```yaml
- name: Build Python package
  run: |
    python -m pip install build
    python -m build

- name: Upload package
  uses: actions/upload-artifact@v4
  with:
    name: python-package
    path: dist/
```

---

## Artifact Immutability

For production pipelines, artifacts should be treated as immutable outputs.

The principle is:

```text
Build
  ↓
Artifact
  ↓
Validate
  ↓
Promote
```

not:

```text
Build
  ↓
Modify artifact
  ↓
Rebuild
  ↓
Deploy
```

Immutability improves:

- Reproducibility
- Auditability
- Rollback
- Incident investigation
- Release traceability

For container deployments, an immutable image reference such as a commit SHA is usually preferable to a mutable tag such as `latest`.

---

## Artifact Retention

Artifacts consume storage and should not be retained indefinitely without a reason.

Retention should reflect the artifact's purpose.

| Artifact | Typical retention strategy |
|---|---|
| PR test reports | Short |
| Debug logs | Short |
| Coverage reports | Short to medium |
| Release packages | Longer |
| Compliance evidence | Based on organizational policy |
| Production deployment metadata | Based on audit requirements |
| Temporary diagnostics | Very short |

Artifact retention should be configured deliberately.

Example:

```yaml
- name: Upload test reports
  uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: reports/
    retention-days: 7
```

Use repository or organization retention policies as the baseline, and override only where the artifact has a clear business or operational reason for different retention.

---

## Cost Considerations

Artifact storage can grow significantly in large organizations.

Common causes include:

- Large build outputs
- Browser test screenshots
- Video recordings
- Debug logs
- Large dependency bundles
- Repeated artifacts from matrix jobs
- Excessive retention periods

For example, a matrix with:

```yaml
matrix:
  python-version:
    - "3.10"
    - "3.11"
    - "3.12"
    - "3.13"
```

can produce four copies of the same report type.

If each job uploads a large artifact, storage usage scales with the matrix.

Prefer focused artifacts:

```text
test-results-python-3.10
test-results-python-3.11
test-results-python-3.12
test-results-python-3.13
```

and retain only the information necessary for diagnosis and audit.

---

## Matrix Artifacts

Matrix jobs require deliberate artifact naming.

Bad:

```yaml
- name: Upload report
  uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: reports/
```

Each matrix job attempts to produce the same artifact name.

Prefer:

```yaml
- name: Upload report
  uses: actions/upload-artifact@v4
  with:
    name: test-results-python-${{ matrix.python-version }}
    path: reports/
```

For a database matrix:

```yaml
- name: Upload integration report
  uses: actions/upload-artifact@v4
  with:
    name: integration-${{ matrix.database }}
    path: reports/
```

This makes the source of each artifact explicit.

---

## Combining Matrix Artifacts

A later aggregation job can download artifacts.

A useful pattern is:

```text
Python 3.11 ──┐
Python 3.12 ──┼──> Individual Artifacts
Python 3.13 ──┘
                     ↓
               Aggregation Job
                     ↓
              Combined Report
```

Example:

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version:
          - "3.11"
          - "3.12"
          - "3.13"

    runs-on: ubuntu-latest

    steps:
      - name: Run tests
        run: |
          mkdir -p reports
          pytest --junitxml=reports/junit.xml

      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: junit-${{ matrix.python-version }}
          path: reports/

  aggregate:
    needs: test
    runs-on: ubuntu-latest

    steps:
      - name: Download all reports
        uses: actions/download-artifact@v5
        with:
          path: reports/
```

The downloaded structure can then be inspected or processed.

---

## Artifact Overwrite Behavior

Artifact naming matters when multiple steps or jobs upload related data.

Do not design workflows around accidental artifact replacement.

If separate jobs produce independent outputs, give them distinct names:

```text
unit-tests
integration-tests
security-scan
build-package
```

If a single job intentionally needs to update an artifact, make the behavior explicit and understand the action's current artifact semantics before relying on it.

For production pipelines, immutable, uniquely named artifacts are easier to audit than mutable shared names.

---

## Artifact Compression

Artifacts are packaged and transferred by GitHub Actions.

For large files, compression and packaging can affect:

- Upload time
- Download time
- Runner CPU
- Storage consumption

Highly compressible text such as:

```text
JSON
XML
CSV
logs
source files
```

can benefit significantly from compression.

Already-compressed data such as:

```text
.zip
.gz
.jpeg
.mp4
```

may provide little additional benefit.

Do not repeatedly compress large artifacts unnecessarily.

---

## Artifact Integrity

Artifacts may be used as release or deployment inputs, so integrity matters.

For security-sensitive pipelines:

```text
Build
  ↓
Artifact
  ↓
Integrity / Security Verification
  ↓
Promotion
```

Consider recording:

- Commit SHA
- Build identifier
- Version
- Artifact name
- Artifact digest where applicable
- Dependency metadata
- SBOM
- Build provenance

For example:

```text
orders-api
version: 1.8.4
commit: 7a31c9f...
build: 4821
```

The objective is to establish a traceable relationship between:

```text
Source
  ↓
Build
  ↓
Artifact
  ↓
Deployment
```

---

## Security Considerations

Artifacts can contain sensitive information accidentally.

Potentially sensitive files include:

```text
.env
private keys
credentials
database dumps
production configuration
debug logs
request payloads
access tokens
```

Never upload an entire workspace without understanding its contents.

Avoid:

```yaml
- name: Upload everything
  uses: actions/upload-artifact@v4
  with:
    name: workspace
    path: .
```

Prefer explicit paths:

```yaml
- name: Upload test reports
  uses: actions/upload-artifact@v4
  with:
    name: test-reports
    path: reports/
```

---

## Secret Leakage Through Logs

Test reports and logs may contain secrets indirectly.

For example:

```text
HTTP request
    ↓
Authorization header
    ↓
Debug log
    ↓
Artifact
```

The artifact may now contain a credential even though the workflow did not explicitly upload a secret.

Before publishing logs, verify:

- Authentication headers are redacted.
- Tokens are not printed.
- Database connection strings are sanitized.
- Environment variables are not dumped.
- Exception messages do not expose credentials.
- Debug mode is appropriate for the environment.

---

## Artifacts from Pull Requests

Pull request workflows require additional security considerations.

Untrusted code can execute during CI.

For example:

```text
Fork Pull Request
      ↓
Workflow executes tests
      ↓
Tests generate files
      ↓
Files uploaded as artifact
```

Artifacts should therefore be treated as potentially untrusted data when produced by untrusted code.

Do not automatically execute downloaded artifacts from an untrusted workflow.

For example, avoid blindly doing:

```yaml
- name: Download artifact
  uses: actions/download-artifact@v5
  with:
    name: build-output

- name: Execute
  run: ./build-output/script.sh
```

unless the trust boundary is understood.

A safer architecture separates:

```text
Untrusted CI
    ↓
Validation
    ↓
Trusted build/promotion
```

rather than allowing arbitrary pull request output to become a production deployment input.

---

## Artifact Download Security

Downloaded artifacts should be treated according to their source and trust level.

Before consuming an artifact in a deployment workflow, consider:

- Which workflow produced it?
- Which commit produced it?
- Was the source trusted?
- Was the artifact generated from an approved branch?
- Was it validated?
- Does the deployment job have production credentials?
- Can an attacker influence its contents?

Artifact storage is not itself a substitute for supply-chain verification.

---

## Artifact Promotion Architecture

A production architecture can use artifacts as part of a controlled promotion process.

```mermaid
flowchart LR
    A[Pull Request] --> B[CI]
    B --> C[Build]
    C --> D[Immutable Artifact]
    D --> E[Staging]
    E --> F[Validation]
    F --> G[Approval]
    G --> H[Production]
    H --> I[Monitoring]
    I --> J[Rollback]
```

The important property is:

```text
Build once
    ↓
Promote the same output
```

rather than:

```text
Build staging
    ↓
Build production
```

The second model can produce different binaries from nominally identical source.

---

## Artifacts and AWS

Artifacts can support AWS deployment workflows without replacing AWS-native storage.

For example:

```text
GitHub Actions
      ↓
Build
      ↓
Artifact
      ↓
Validation
      ↓
ECR / S3
      ↓
AWS Deployment
```

Use the appropriate AWS service for long-lived production distribution:

| Requirement | Typical service |
|---|---|
| Container images | Amazon ECR |
| Large application objects | Amazon S3 |
| Python package distribution | Artifact/package registry |
| Temporary CI output | GitHub Actions artifact |
| Test reports | GitHub Actions artifact |
| Build metadata | GitHub Actions artifact/output |

The existing production project notes use:

```text
GitHub Actions
      ↓
ECR
      ↓
ECS
```

for container deployment. :chatgpt-content-reference{index="2"}

---

## Artifact vs Amazon S3

GitHub artifacts are convenient for CI/CD workflow outputs, but they are not a general-purpose application object store.

Use GitHub artifacts for:

```text
CI reports
Build outputs
Debug bundles
Workflow handoff
```

Use Amazon S3 when the application or deployment architecture requires:

```text
Long-lived object storage
Large datasets
Application assets
Backups
Data exchange
Durable production objects
```

Do not turn GitHub artifact storage into an accidental production data store.

---

## Artifact Naming Strategy

A production naming strategy should provide enough context to identify the artifact.

For example:

```text
orders-api-test-results-python-3.12
orders-api-security-scan-7a31c9f
orders-api-package-1.8.4
orders-api-build-metadata-7a31c9f
```

Useful dimensions include:

- Application
- Artifact type
- Version
- Commit
- Matrix dimension

Avoid putting unnecessary sensitive information into artifact names.

---

## Artifact Metadata

For build and release artifacts, include metadata that supports traceability.

Example:

```json
{
  "application": "orders-api",
  "version": "1.8.4",
  "commit": "7a31c9f",
  "workflow_run": "4821",
  "python": "3.12"
}
```

This metadata can itself be uploaded as an artifact:

```yaml
- name: Generate build metadata
  run: |
    cat > build-metadata.json <<'EOF'
    {
      "application": "orders-api",
      "commit": "${GITHUB_SHA}",
      "workflow_run": "${GITHUB_RUN_ID}"
    }
    EOF

- name: Upload metadata
  uses: actions/upload-artifact@v4
  with:
    name: build-metadata
    path: build-metadata.json
```

Avoid embedding secrets into metadata.

---

## Debugging Artifacts

Artifacts are valuable when a workflow fails after generating useful diagnostic data.

For example:

```yaml
- name: Run tests
  run: pytest

- name: Collect diagnostics
  if: ${{ failure() }}
  run: |
    mkdir -p diagnostics
    docker compose logs > diagnostics/docker-compose.log || true
    python --version > diagnostics/python-version.txt
    pip freeze > diagnostics/pip-freeze.txt

- name: Upload diagnostics
  if: ${{ failure() }}
  uses: actions/upload-artifact@v4
  with:
    name: diagnostics-${{ github.run_id }}
    path: diagnostics/
```

This can dramatically reduce incident investigation time.

However, diagnostic artifacts must be reviewed for secrets before upload.

---

## Failure Diagnostics

### Artifact Upload Fails

**Symptom**

The upload step fails.

**Possible causes**

- Incorrect path.
- File does not exist.
- Permissions or service issue.
- Invalid artifact configuration.
- Runner or network failure.

**Isolation**

```yaml
- name: Inspect output directory
  run: |
    pwd
    find reports -maxdepth 2 -type f -print
```

Verify that the path passed to `upload-artifact` matches the actual workspace.

---

### Artifact Is Empty or Incomplete

**Possible causes**

- Test command did not generate the expected file.
- The application wrote output to a different directory.
- The artifact path is incorrect.
- A matrix job generated different filenames.
- A cleanup step removed the output.

**Prevention**

Verify files before upload:

```yaml
- name: Verify artifact
  run: |
    test -f reports/junit.xml
    test -f reports/coverage.xml
```

---

### Downloaded Artifact Is Missing

**Possible causes**

- Producer job failed.
- Consumer job did not declare the correct dependency.
- Artifact name is incorrect.
- Artifact expired.
- The artifact was never uploaded.

Check the dependency graph:

```yaml
jobs:
  test:
    ...

  deploy:
    needs: test
    ...
```

A deployment job should not consume an artifact from a job whose successful completion is not explicitly represented in the workflow graph.

---

### Matrix Artifact Collision

**Symptom**

Multiple matrix jobs attempt to publish the same artifact.

**Cause**

Static artifact naming:

```yaml
name: test-results
```

**Fix**

Include matrix metadata:

```yaml
name: test-results-${{ matrix.python-version }}
```

---

### Artifact Contains Secrets

**Symptom**

Sensitive information appears in a downloaded artifact.

**Possible causes**

- Logs contain credentials.
- `.env` files were uploaded.
- Debug output contains authorization headers.
- Entire workspace was uploaded.

**Corrective action**

Restrict upload paths:

```yaml
path: reports/
```

instead of:

```yaml
path: .
```

Rotate any credentials that were exposed.

---

## Production Pitfalls

### Uploading the Entire Repository

Avoid:

```yaml
path: .
```

unless the entire workspace is intentionally part of the artifact.

It increases:

- Storage usage
- Upload time
- Security exposure
- Artifact size
- Investigation complexity

---

### Uploading Dependencies

Do not upload:

```text
.venv/
node_modules/
__pycache__/
```

unless they are explicitly required.

Dependencies should generally be restored through dependency installation and caching rather than treated as build artifacts.

---

### Using Artifacts as Caches

Do not use artifacts to accelerate every future workflow run.

Use dependency caches for that purpose.

---

### Rebuilding Instead of Promoting

If a package or binary has already been validated, rebuilding it for production undermines the build-once model.

Prefer:

```text
Build
 ↓
Artifact
 ↓
Test
 ↓
Promote
```

---

### Using Mutable Artifact Names as State

Avoid designing a pipeline where:

```text
latest-build
```

implicitly represents the current production version.

Production deployments should reference explicit build identity.

---

## Artifact Retention Strategy

A mature repository should define retention based on purpose.

Example policy:

```text
Pull request reports
    → short retention

Main branch CI reports
    → medium retention

Release artifacts
    → longer retention

Compliance evidence
    → organizational retention policy
```

Avoid retaining everything forever.

At scale:

```text
Number of runs
      ×
Artifact size
      ×
Retention period
      =
Storage growth
```

Matrix-heavy repositories can multiply storage quickly.

---

## Monitoring and Operations

Monitor artifact-related failures as part of CI/CD reliability.

Useful signals include:

- Artifact upload failures
- Artifact download failures
- Unexpected artifact size growth
- Missing test reports
- Missing deployment packages
- Excessive retention
- Repeated diagnostic artifact generation
- Matrix artifact duplication

For production pipelines, artifact failures should be visible in workflow logs and, where appropriate, operational alerting.

---

## Artifact Strategy for a Senior Backend Pipeline

A mature backend pipeline may use artifacts like this:

```text
Pull Request
    ↓
Lint
    ↓
Unit Tests
    ├── junit.xml
    └── coverage.xml
          ↓
       Artifacts
    ↓
Integration Tests
    ├── integration.xml
    └── logs/
          ↓
       Artifacts
    ↓
Security Scan
    ├── scan.json
    └── sbom.json
          ↓
       Artifacts
    ↓
Build
    └── immutable package/image metadata
          ↓
       Artifact / Registry
    ↓
Staging
    ↓
Approval
    ↓
Production
```

For containerized AWS deployments:

```text
GitHub
   ↓
GitHub Actions
   ↓
Test
   ↓
Build Docker Image
   ↓
Security Scan
   ↓
ECR
   ↓
ECS
```

The existing ECS documentation follows this general production model and emphasizes testing, security scanning, versioned images, monitoring, OIDC, and rollback. :chatgpt-content-reference{index="3"}

---

## Recommended Artifact Design

A production workflow should establish clear ownership for every artifact.

| Artifact | Producer | Consumer | Purpose |
|---|---|---|---|
| JUnit report | Test job | Developer/report job | Test diagnostics |
| Coverage report | Test job | Developer/quality tooling | Coverage analysis |
| Security report | Security job | Security/deployment job | Security validation |
| SBOM | Build job | Security/release process | Dependency inventory |
| Python wheel | Build job | Deployment/release job | Application package |
| Deployment manifest | Build job | Deployment job | Deployment input |
| Debug logs | Failure handler | Developer | Troubleshooting |
| Docker image | Build system | ECS/Kubernetes | Production deployment |

This creates explicit pipeline contracts.

---

## Interview Traps

### What Is the Difference Between an Artifact and a Cache?

An artifact is a workflow output intended to be retained or consumed. A cache is an optimization mechanism intended to avoid repeating expensive work.

```text
Artifact → correctness / output

Cache → performance / acceleration
```

---

### Why Do You Need Artifacts Between Jobs?

Jobs can execute on separate ephemeral runners. Files created by one job are not automatically available to another job.

Artifacts create an explicit persistence boundary.

---

### How Would You Pass a Test Report Between Jobs?

Generate the report, upload it as an artifact, then download it in the dependent job.

```text
Test Job
   ↓
JUnit XML
   ↓
Upload Artifact
   ↓
Report Job
   ↓
Download Artifact
```

---

### How Would You Handle Artifacts in a Matrix Build?

Give each matrix job a unique artifact name.

```yaml
name: test-results-${{ matrix.python-version }}
```

Then aggregate or inspect the outputs in a downstream job.

---

### Would You Store a Docker Image as a GitHub Artifact?

For production container deployment, normally no.

Use a container registry such as Amazon ECR:

```text
Docker Build
    ↓
ECR
    ↓
ECS
```

Use GitHub artifacts for supporting files such as reports, manifests, SBOMs, and debugging outputs.

---

### Why Should Production Be Built Once and Promoted?

Rebuilding separately for staging and production can produce different outputs.

A stronger model is:

```text
Source
  ↓
Build
  ↓
Immutable Artifact
  ↓
Staging
  ↓
Validation
  ↓
Production
```

This improves reproducibility and rollback confidence.

---

### How Would You Prevent Sensitive Data from Entering an Artifact?

Use explicit upload paths, sanitize logs, avoid uploading the entire workspace, and review generated reports before publishing them.

---

### How Would You Design Artifact Retention?

Retention should depend on the artifact's operational and compliance value.

Short-lived CI diagnostics should not consume storage for months, while release or compliance artifacts may require longer retention.

---

## Production Checklist

Before adopting artifacts in a production GitHub Actions pipeline:

- [ ] Artifact names clearly identify their purpose.
- [ ] Matrix jobs use unique artifact names.
- [ ] Artifact paths are explicit.
- [ ] Expected files are validated before upload.
- [ ] Test reports are preserved after failures where useful.
- [ ] Debug artifacts are uploaded only when needed.
- [ ] Artifacts are not used as dependency caches.
- [ ] Large or durable production objects use appropriate storage such as ECR or S3.
- [ ] Sensitive files are excluded from uploads.
- [ ] Logs are sanitized before becoming artifacts.
- [ ] Build artifacts are immutable where practical.
- [ ] Deployment jobs consume explicit artifact versions.
- [ ] Production deployment does not rebuild an already validated artifact unnecessarily.
- [ ] Artifact retention matches operational and compliance requirements.
- [ ] Artifact storage growth is monitored.
- [ ] Artifact integrity and provenance are considered for security-sensitive deployments.
- [ ] Pull request artifacts are treated as potentially untrusted when produced from untrusted code.
- [ ] Rollback can identify the exact artifact or image associated with a deployment.

## Key Takeaways

- GitHub Actions artifacts provide a persistence boundary for files generated by ephemeral workflow runners and are especially important for passing outputs between jobs.
- Artifacts represent workflow outputs; caches exist primarily to accelerate future executions and should not be treated as interchangeable mechanisms.
- Production pipelines should use explicit artifact paths, unique matrix-aware names, controlled retention, and immutable build outputs wherever practical.
- Never treat artifacts as inherently trusted or confidential; sanitize logs, exclude secrets, and consider the trust boundary of workflows that produced the artifact.
- A strong CI/CD design builds once, preserves the resulting artifact or image, validates it, and promotes the same immutable output through staging and production.