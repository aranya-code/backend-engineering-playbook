# 11- Action Version Pinning

## Overview

GitHub Actions workflows depend on executable components such as:

- Marketplace actions.
- Organization-owned actions.
- Internal actions.
- Reusable workflows.
- JavaScript dependencies.
- Docker base images.
- Composite actions.

When a workflow references an action, the reference determines which implementation is executed.

For example:

```yaml
- uses: actions/checkout@v4
```

The reference `v4` is convenient, but it is not an immutable identity. The referenced tag can move to a different commit over time.

For security-sensitive CI/CD pipelines, especially production deployment workflows, action version pinning establishes a more deterministic dependency boundary:

```text
Workflow
    ↓
Pinned Action Reference
    ↓
Specific Commit
    ↓
Known Action Code
    ↓
Runner
```

Action pinning is therefore part of supply-chain security, reproducibility, change control, and incident response.

The key principle is:

> A production workflow should execute an explicitly reviewed version of every security-sensitive action.

Pinning does not make an action inherently trustworthy. It ensures that the workflow continues executing the reviewed revision until the workflow reference is intentionally changed.

## Why Action Version Pinning Matters

Consider:

```yaml
- uses: third-party/deploy-action@v1
```

At one point:

```text
v1 → Commit A
```

Later, the maintainer moves the tag:

```text
v1 → Commit B
```

The workflow file has not changed, but the executable code has.

This creates a hidden dependency change:

```text
Same Workflow
     ↓
Different Action Code
```

With a commit SHA:

```yaml
- uses: third-party/deploy-action@abc123...
```

the workflow points to one specific Git commit.

The workflow changes only when the reference is explicitly updated.

## Version Reference Types

GitHub Actions can be referenced using different forms.

| Reference | Example | Mutability | Typical Use |
|---|---|---:|---|
| Branch | `@main` | High | Development/testing |
| Major tag | `@v4` | Medium | General CI |
| Exact version tag | `@v4.2.0` | Medium | Controlled dependency |
| Commit SHA | `@abc123...` | Low | Security-sensitive workflows |

The exact security posture depends on who controls the repository and reference.

A tag is a human-friendly version identifier. A commit SHA is an immutable Git object identifier for the referenced commit.

## Branch References

Avoid security-sensitive workflow dependencies such as:

```yaml
- uses: example/action@main
```

A branch can move frequently.

The workflow can therefore execute different code without an obvious change to the workflow file.

This makes:

```text
@main
```

a poor choice for a production deployment dependency.

## Major Version Tags

A common reference is:

```yaml
- uses: actions/checkout@v4
```

This is convenient because the action maintainer can publish compatible fixes under the major version.

Advantages:

- Easy maintenance.
- Receives upstream fixes.
- Human-readable.
- Common ecosystem convention.

Limitations:

- The tag is mutable.
- Executed code can change without a workflow change.
- The exact commit is not obvious from the YAML.

For lower-risk CI workflows, organizations may accept this trade-off.

## Exact Version Tags

Example:

```yaml
- uses: example/action@v4.2.1
```

This provides stronger version intent than:

```yaml
@v4
```

but the Git tag can still theoretically be moved.

Therefore:

```text
Exact Version Tag
≠
Immutable Commit Reference
```

For strict supply-chain controls, use a verified commit SHA.

## Commit SHA Pinning

Example:

```yaml
- uses: actions/checkout@<verified-commit-sha>
```

The SHA identifies a specific commit.

The resulting dependency relationship is:

```text
Workflow
   ↓
Commit SHA
   ↓
Specific Repository Revision
```

Advantages:

- Strong immutability.
- Better reproducibility.
- Reduced mutable-tag risk.
- Easier forensic analysis.
- Explicit dependency changes.

Limitations:

- Less readable.
- Requires update management.
- Security fixes do not automatically enter the workflow.
- Every update requires a deliberate reference change.

## SHA Pinning Is Not Trust

Pinning an action to a SHA does not prove that the commit is safe.

For example:

```text
Malicious Commit
       ↓
SHA Pinning
       ↓
Malicious Code Still Executes
```

The SHA only guarantees that the workflow continues to use that particular revision.

Therefore secure action management requires:

```text
Trusted Source
+
Code Review
+
Dependency Review
+
Version Verification
+
SHA Pinning
+
Least Privilege
```

## Verify the Commit Before Pinning

Do not blindly copy a SHA from an untrusted source.

Before pinning an action:

1. Identify the intended release.
2. Inspect the upstream repository.
3. Verify the release/tag relationship.
4. Identify the corresponding commit.
5. Review relevant changes.
6. Test the action.
7. Update the workflow.
8. Run CI.
9. Merge through normal review.

The goal is to establish:

```text
Expected Version
       ↓
Expected Commit
       ↓
Reviewed SHA
       ↓
Workflow
```

## Pinning Production Actions

A production deployment workflow is a strong candidate for SHA pinning.

Example:

```yaml
name: Deploy

on:
  push:
    branches:
      - main

permissions:
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest

    environment:
      name: production

    permissions:
      contents: read
      id-token: write

    steps:
      - name: Checkout
        uses: actions/checkout@<verified-sha>

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@<verified-sha>
        with:
          role-to-assume: ${{ vars.AWS_DEPLOYMENT_ROLE }}
          aws-region: ${{ vars.AWS_REGION }}
```

The important security properties are:

- Trusted branch.
- Protected environment.
- Minimal repository permissions.
- OIDC restricted to the deployment job.
- Explicitly reviewed action revisions.

## Pinning Pull Request Actions

Pull-request workflows also benefit from controlled action references.

Example:

```yaml
on:
  pull_request:

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@<verified-sha>

      - name: Set up Python
        uses: actions/setup-python@<verified-sha>
        with:
          python-version: "3.12"

      - name: Test
        run: pytest
```

The difference is that the PR workflow should additionally remain low privilege.

Pinning does not replace:

```yaml
permissions:
  contents: read
```

or runner isolation.

## Pinning and Pull Request Security

The following are separate controls:

```text
Action Pinning
     ↓
Controls which action revision executes

Least Privilege
     ↓
Controls what the action can access

Runner Isolation
     ↓
Controls execution environment

Secret Isolation
     ↓
Controls credential exposure
```

A secure workflow needs the appropriate combination.

## Third-Party Action Security

Before pinning a third-party action, review:

- Repository owner.
- Source code.
- Release history.
- Maintainer activity.
- Dependencies.
- Required permissions.
- Runtime.
- Network behavior.
- Secret requirements.
- Known vulnerabilities.
- Release process.

The process should not be:

```text
Find Action
 ↓
Copy YAML
 ↓
Pin SHA
```

It should be:

```text
Identify Requirement
 ↓
Evaluate Action
 ↓
Review Source
 ↓
Review Dependencies
 ↓
Verify Release
 ↓
Pin Commit
 ↓
Test
 ↓
Deploy
```

## Action Dependencies

A JavaScript action may depend on npm packages:

```text
Workflow
   ↓
JavaScript Action
   ↓
package.json
   ↓
package-lock.json
   ↓
Transitive Dependencies
```

A Docker action may depend on:

```text
Docker Action
   ↓
Dockerfile
   ↓
Base Image
   ↓
OS Packages
   ↓
Application Dependencies
```

Pinning the top-level action does not automatically eliminate risks in its dependency tree.

## Dependabot

Dependabot or equivalent dependency-management tooling can help identify action updates.

A controlled update flow is:

```text
New Action Release
       ↓
Dependency Update
       ↓
Pull Request
       ↓
CI
       ↓
Security Review
       ↓
Merge
       ↓
Updated SHA
```

The update should be reviewed like any other production dependency.

## Automated SHA Updates

Manual SHA management becomes difficult across many repositories.

For example:

```text
100 Repositories
×
10 Actions
=
1000 Action References
```

Centralized automation can reduce maintenance effort.

The important requirement is that automated updates still pass through:

- CI.
- Security controls.
- Repository review.
- Required status checks.
- Deployment protection.

Automation should update references, not bypass governance.

## Action Update Lifecycle

A production action update should follow:

```mermaid
flowchart LR
    Release[New Action Release]
    Review[Review Changes]
    Verify[Verify Commit]
    Update[Update SHA]
    CI[Run CI]
    Merge[Merge]
    Deploy[Production]
    Rollback[Rollback]

    Release --> Review
    Review --> Verify
    Verify --> Update
    Update --> CI
    CI --> Merge
    Merge --> Deploy
    Deploy --> Rollback
```

Rollback should be possible by restoring the previous known-good SHA.

## Rollback

Suppose:

```yaml
uses: example/deploy-action@SHA_A
```

is changed to:

```yaml
uses: example/deploy-action@SHA_B
```

and production deployments fail.

A rollback can restore:

```yaml
uses: example/deploy-action@SHA_A
```

The action dependency itself therefore becomes version-controlled deployment configuration.

## Known-Good References

Maintain the ability to identify:

```text
Current SHA
Previous SHA
Reviewed Version
Release Date
Change Reason
```

This is valuable during incident response.

## Action Pinning and GitHub Releases

A release may be represented as:

```text
v4.2.1
    ↓
Commit SHA
```

The workflow can consume the SHA while documentation and dependency management refer to the human-readable version.

For example:

```yaml
# example/action v4.2.1
- uses: example/action@<verified-sha>
```

This improves readability while retaining immutable execution.

## Action Pinning and Semantic Versioning

Semantic versioning typically follows:

```text
MAJOR.MINOR.PATCH
```

For example:

```text
4.2.1
```

Conceptually:

```text
Major
 ↓
Breaking API expectations

Minor
 ↓
Backward-compatible features

Patch
 ↓
Backward-compatible fixes
```

However, semantic versioning is a versioning convention, not an integrity mechanism.

A mutable Git tag can still point somewhere unexpected.

## Major Version Pinning

Using:

```yaml
uses: example/action@v4
```

provides automatic compatibility updates within the major version if the maintainer follows the expected release model.

This reduces maintenance but increases the set of code revisions that the workflow may execute.

## SHA Pinning and Maintenance

A fully pinned workflow requires intentional updates.

For example:

```text
SHA_A
 ↓
Security Fix Released
 ↓
SHA_B
 ↓
Review
 ↓
CI
 ↓
Merge
```

This creates a controlled change process.

Without update automation, however, repositories may remain pinned to vulnerable versions indefinitely.

## Security Fixes and Pinning

Pinning does not mean:

```text
Pin Once
+
Never Update
```

That creates a different security problem.

The correct model is:

```text
Pin
 ↓
Monitor
 ↓
Review Updates
 ↓
Update
 ↓
Test
 ↓
Pin New Version
```

## Action Allowlisting

Organizations can restrict which actions repositories may use.

For example:

```text
Allowed:
- actions/*
- aws-actions/*
- organization/platform-actions/*

Restricted:
- arbitrary Marketplace actions
```

The exact policy depends on organizational requirements.

Allowlisting reduces the number of unknown dependencies entering the CI/CD environment.

## Internal Action Registry

A platform team can provide approved internal actions:

```text
platform-actions/
├── python-ci/
├── docker-build/
├── security-scan/
├── aws-auth/
└── deploy-ecs/
```

Repositories then consume standardized building blocks.

For example:

```yaml
- uses: organization/platform-actions/python-ci@<verified-sha>
```

Advantages include:

- Centralized ownership.
- Consistent security controls.
- Standardized permissions.
- Reduced duplicated configuration.
- Easier auditing.

## Reusable Workflows and Pinning

Reusable workflows are also versioned dependencies.

Example:

```yaml
jobs:
  deploy:
    uses: organization/platform/.github/workflows/deploy.yml@v3
```

The same trust questions apply:

```text
Who controls the workflow?
Can the reference move?
Who reviews changes?
What permissions are inherited?
What secrets are passed?
```

Security-sensitive reusable workflows can also be referenced using immutable revisions where appropriate.

## Reusable Workflow vs Action

These are separate dependency types.

| Mechanism | Scope | Typical Security Concern |
|---|---|---|
| Composite action | Steps within one job | Shell execution |
| JavaScript action | Executable Node code | Runtime/dependencies |
| Docker action | Containerized executable code | Image/base image |
| Reusable workflow | Multiple jobs | Permissions/secrets/orchestration |

Pinning policy should consider all executable dependencies, not just Marketplace actions.

## Pull Request Security

Action pinning becomes especially important when workflows process untrusted PRs.

A secure PR model is:

```text
Fork PR
   ↓
pull_request
   ↓
Restricted Runner
   ↓
Pinned Actions
   ↓
Minimal Permissions
   ↓
Tests
```

Do not combine a pinned third-party action with unnecessary privileges and assume the workflow is secure.

## `pull_request_target`

Particular caution is required when using:

```yaml
on:
  pull_request_target:
```

A pinned action does not make the overall workflow safe if the workflow also:

```text
Checks out PR code
+
Executes PR code
+
Has Secrets
+
Has Write Permissions
```

The trust boundary must still be preserved.

## GITHUB_TOKEN

Pinning should be combined with explicit permissions:

```yaml
permissions:
  contents: read
```

Do not allow an action to inherit broad repository capabilities merely because it is pinned.

The correct relationship is:

```text
Pinned Action
+
Minimal Permissions
=
Reduced Supply-Chain Risk
```

not:

```text
Pinned Action
=
Trusted Action
```

## OIDC

Production cloud authentication should be isolated to the trusted deployment path.

Example:

```yaml
permissions:
  contents: read
  id-token: write
```

Only the job requiring AWS authentication should receive:

```yaml
id-token: write
```

A pinned action that receives OIDC access still has significant privilege.

## AWS IAM

The AWS trust boundary should include:

```text
GitHub Repository
+
Workflow Context
+
OIDC Claims
+
IAM Trust Policy
+
IAM Permissions
```

The IAM role should be limited to the required AWS resources.

For example:

```text
GitHub Actions
    ↓
OIDC
    ↓
AWS STS
    ↓
Restricted IAM Role
    ↓
ECR / ECS / S3 / Lambda
```

The action itself should not receive administrator-level access merely because it performs deployment operations.

## Docker Build Actions

A Docker build action may interact with:

- Docker daemon.
- Buildx.
- Registry credentials.
- Build cache.
- Build secrets.
- Source repository.

Therefore action pinning should be combined with Docker security controls.

Example:

```text
Trusted Main
   ↓
Pinned Build Action
   ↓
Buildx
   ↓
Multi-stage Docker Build
   ↓
Security Scan
   ↓
SBOM
   ↓
ECR
```

## Immutable Docker Images

Action pinning and artifact pinning address different layers.

```text
Action SHA
    ↓
Controls CI dependency

Docker Image Digest
    ↓
Controls deployment artifact
```

A production pipeline should ideally make both dependencies explicit.

For example:

```text
Workflow
 ↓
Pinned Build Action
 ↓
Image
 ↓
Immutable Digest
 ↓
Production
```

## Production Pipeline

A mature pipeline can look like:

```text
Pull Request
      ↓
Lint
      ↓
Unit Tests
      ↓
Integration Tests
      ↓
Security Scan
      ↓
Matrix Tests
      ↓
Protected Main
      ↓
Build
      ↓
Docker Image
      ↓
ECR
      ↓
Staging
      ↓
Approval
      ↓
Production
      ↓
Monitoring
      ↓
Rollback
```

Every executable action in the pipeline should have an appropriate trust and versioning policy.

## Build Once, Promote Later

Action pinning should support an immutable artifact strategy:

```text
Trusted Main
      ↓
Pinned Build Dependencies
      ↓
Build
      ↓
Immutable Image
      ↓
ECR
      ↓
Staging
      ↓
Production
```

Do not rebuild the application separately for production if the goal is to deploy exactly what was tested.

## Action Pinning and Concurrency

Pinned dependencies do not prevent deployment races.

Use concurrency independently:

```yaml
concurrency:
  group: production-deployment
  cancel-in-progress: false
```

The security model is:

```text
Pinned Action
    ↓
Known Executable Dependency

Concurrency
    ↓
Controlled Deployment Execution
```

Both controls address different failure modes.

## Monitoring

Organizations should maintain visibility into:

- Action references.
- Action versions.
- Action SHAs.
- Workflow usage.
- Permission levels.
- Secret exposure.
- OIDC usage.
- Runner types.
- Deployment workflows.

This makes it possible to answer:

```text
Which repositories use this action?
Which SHA are they using?
Which workflows invoke it?
Which permissions does it receive?
```

## Incident Response

If a pinned action is discovered to be compromised:

1. Identify the affected action and SHA.
2. Identify all repositories using the SHA.
3. Identify workflows that executed it.
4. Determine execution dates.
5. Determine workflow permissions.
6. Identify accessible secrets.
7. Determine whether OIDC was enabled.
8. Identify self-hosted runner usage.
9. Review cloud audit logs.
10. Review workflow logs.
11. Replace the action with a trusted revision.
12. Rotate potentially exposed credentials.
13. Rebuild affected artifacts.
14. Review deployments performed during the exposure window.
15. Restore from known-good artifacts where necessary.

Pinning makes this investigation easier because the exact action revision is known.

## Disaster Recovery

A robust CI/CD system should maintain known-good references.

For example:

```text
Current Action SHA
       ↓
Compromise Detected
       ↓
Known-Good Previous SHA
       ↓
Workflow Rollback
       ↓
Known-Good Artifact
       ↓
Production Recovery
```

Do not depend on the latest upstream release during an incident.

## Reliability

Action updates are external dependencies and can introduce:

- Runtime changes.
- Input changes.
- Output changes.
- Dependency changes.
- Performance regressions.
- New permission requirements.

Use CI to validate updates before production use.

For critical workflows, consider a staged rollout:

```text
Update SHA
   ↓
Test Repository
   ↓
Non-Production
   ↓
Selected Production Workflows
   ↓
Organization-Wide Rollout
```

## Cost and Performance

SHA pinning itself has minimal runtime overhead.

The operational cost comes from:

- Dependency review.
- Testing.
- Update automation.
- Security scanning.
- Release management.

Organizations should automate these processes rather than avoiding pinning because of maintenance cost.

For example:

```text
Automated Update
      ↓
CI
      ↓
Security Checks
      ↓
Review
      ↓
Merge
```

reduces manual maintenance.

## Common Mistakes

### Using `@main`

Avoid:

```yaml
uses: example/action@main
```

for production workflows.

The branch can change without a workflow modification.

### Assuming `@v4` Is Immutable

A major tag is convenient but can move.

Do not confuse version naming with immutability.

### Pinning Without Reviewing the Commit

A malicious or compromised commit can still be pinned.

Verify the intended release and commit before adopting it.

### Pinning Once and Never Updating

A pinned vulnerable version remains vulnerable.

Pinning requires a maintenance process.

### Giving Pinned Actions Excessive Permissions

This is still dangerous:

```yaml
permissions: write-all
```

even if every action is SHA-pinned.

### Giving OIDC to the Entire Workflow

Use:

```yaml
permissions:
  id-token: write
```

only where cloud authentication is actually required.

### Passing All Secrets to Reusable Workflows

Prefer explicit secret passing where practical.

### Ignoring Action Dependencies

A pinned action can contain vulnerable dependencies.

Review the dependency chain.

### Updating Action SHAs Without Testing

The new commit may change behavior.

Run the same CI and integration tests used for normal dependency updates.

### Treating SHA Pinning as a Complete Supply-Chain Strategy

Pinning addresses mutable references.

It does not replace:

- Trusted sources.
- Dependency review.
- SBOMs.
- Provenance.
- Attestations.
- Signing.
- Least privilege.
- Runner isolation.

## Troubleshooting

Use the general model:

```text
Symptom
→ Possible Causes
→ Isolation Strategy
→ Commands / Checks
→ Root Cause
→ Corrective Action
→ Prevention
```

### Workflow Fails After SHA Update

**Possible causes**

- New action behavior.
- Changed inputs.
- Changed outputs.
- Runtime change.
- Dependency change.
- Permission requirement.

**Isolation**

Compare:

```text
Previous SHA
vs
New SHA
```

Review the action release and run the workflow in a controlled environment.

### Action SHA Does Not Match Expected Release

**Possible causes**

- Incorrect commit selected.
- Tag was misinterpreted.
- Fork or mirror used.
- Release mapping changed.

**Corrective action**

Verify the upstream repository and intended release before updating the workflow.

### Security Fix Is Available but Workflow Still Uses Old SHA

**Possible causes**

- No dependency automation.
- Update PR not merged.
- Repository uses an outdated internal action.

**Prevention**

Track action dependencies and automate update proposals.

### Different Repositories Use Different SHAs

**Possible causes**

- Independent update schedules.
- Manual dependency management.
- Different compatibility requirements.

**Corrective action**

Use organization-level reusable workflows or centralized action governance where appropriate.

### Action Works in One Repository but Not Another

Compare:

```text
Action SHA
Permissions
Runner
Environment
Inputs
Secrets
Workflow Context
```

Do not immediately grant broader permissions.

### Production Deployment Fails After Action Update

Check:

```text
Action SHA
 ↓
Action Inputs
 ↓
AWS OIDC
 ↓
IAM Trust Policy
 ↓
IAM Permissions
 ↓
Deployment API
```

If the previous SHA worked, compare action behavior before modifying IAM policies.

## GitHub CLI Operations

List workflows:

```bash
gh workflow list
```

List recent workflow runs:

```bash
gh run list
```

Inspect a run:

```bash
gh run view RUN_ID
```

View workflow logs:

```bash
gh run view RUN_ID --log
```

List repository secrets:

```bash
gh secret list
```

Inspect Actions permissions:

```bash
gh api repos/{owner}/{repo}/actions/permissions
```

Inspect workflow permissions:

```bash
gh api repos/{owner}/{repo}/actions/permissions/workflow
```

List environments:

```bash
gh api repos/{owner}/{repo}/environments
```

List releases:

```bash
gh release list
```

These commands support CI/CD investigation without exposing secret values.

## Enterprise Governance

A mature organization should establish an action policy.

Example:

```text
Enterprise
   ↓
Action Policy
   ├── Approved Sources
   ├── Pinning Requirements
   ├── Permission Standards
   ├── Runner Standards
   └── Security Review
          ↓
Repositories
          ↓
Workflows
```

Governance can define:

- Which Marketplace actions are permitted.
- Whether SHA pinning is mandatory.
- Which actions require security review.
- Which actions may access production.
- Which runners may execute privileged workflows.
- How action updates are handled.
- How incidents are investigated.

## Action Inventory

Maintain an inventory containing:

| Field | Example |
|---|---|
| Action | `example/action` |
| Version | `v4.2.1` |
| SHA | `abc123...` |
| Repository | `service-api` |
| Workflow | `deploy.yml` |
| Permissions | `contents: read` |
| OIDC | Yes/No |
| Secrets | Deployment token |
| Runner | GitHub-hosted |
| Owner | Platform Team |
| Review Status | Approved |

This inventory makes organization-wide upgrades and incident response significantly easier.

## Production Checklist

### Pinning

- [ ] Production-sensitive actions use immutable references where appropriate.
- [ ] Action SHAs are verified before adoption.
- [ ] Action versions are documented.
- [ ] Previous known-good references are recoverable.
- [ ] Action updates follow a controlled process.

### Security

- [ ] Action sources are reviewed.
- [ ] Dependencies are reviewed.
- [ ] `GITHUB_TOKEN` permissions are minimized.
- [ ] Secrets are scoped to required jobs.
- [ ] OIDC is restricted to trusted deployment jobs.
- [ ] Self-hosted runner access is controlled.
- [ ] Private network access is restricted.

### Supply Chain

- [ ] Dependency review is enabled where appropriate.
- [ ] Dependabot or equivalent tooling is used.
- [ ] SBOM generation is considered.
- [ ] Artifact provenance is available.
- [ ] Attestations are considered.
- [ ] Production artifacts can be verified.
- [ ] Approved action sources are defined.

### Operations

- [ ] Action versions are inventoried.
- [ ] Update failures can be diagnosed.
- [ ] Rollback to a known-good SHA is possible.
- [ ] Workflow logs are retained appropriately.
- [ ] Cloud audit logs are available.
- [ ] Credential rotation procedures exist.
- [ ] Incident response procedures cover compromised actions.

## Senior-Level Design Principles

### Pin Dependencies, Not Trust

A SHA establishes deterministic code selection.

It does not establish that the selected code is trustworthy.

### Automate Updates

A secure pinning strategy must include:

```text
Pin
 ↓
Monitor
 ↓
Update
 ↓
Test
 ↓
Review
 ↓
Deploy
```

### Keep Privileges Narrow

The safest action is one that:

```text
Executes Known Code
+
Receives Minimal Permissions
+
Receives Minimal Secrets
+
Runs in the Correct Trust Zone
```

### Separate Build and Deployment Trust

Do not allow a generic PR action to inherit production deployment privileges.

Use:

```text
PR CI
 ↓
Restricted

Trusted Build
 ↓
Artifact

Deployment
 ↓
Protected Environment
 ↓
OIDC
 ↓
Restricted IAM
```

### Make Rollback Explicit

Maintain a known-good action SHA and known-good production artifact.

This allows both the CI dependency and the application artifact to be rolled back independently when required.

## Interview Scenarios

### Why Pin GitHub Actions to a SHA?

Explain:

- Mutable tags.
- Reproducibility.
- Supply-chain risk.
- Deterministic execution.
- Update maintenance.
- Incident response.

### Is SHA Pinning Enough for Security?

Explain why it is not.

Discuss:

```text
Trusted Source
+
Commit Verification
+
Dependency Security
+
Least Privilege
+
Runner Isolation
+
Secret Isolation
+
Artifact Integrity
```

### How Would You Manage 500 Repositories?

Discuss:

- Central action inventory.
- Approved action sources.
- Reusable workflows.
- Internal actions.
- SHA pinning.
- Automated update PRs.
- Organization policies.
- Security scanning.
- Governance.
- Rollback.

### A Critical Action Releases a Security Fix

Explain:

```text
Release
 ↓
Verify Commit
 ↓
Update SHA
 ↓
Run CI
 ↓
Security Review
 ↓
Deploy
 ↓
Monitor
```

Also explain how to roll back if the update causes production failures.

### A Pinned Action Is Compromised

Describe how you would:

1. Identify affected SHA.
2. Inventory consumers.
3. Determine workflow permissions.
4. Identify secrets and OIDC access.
5. Review logs.
6. Review cloud audit events.
7. Rotate credentials.
8. Replace the action.
9. Rebuild affected artifacts.
10. Assess production deployments.

### Why Use a Reusable Internal Workflow?

Discuss:

- Standardization.
- Centralized security controls.
- Permission consistency.
- Reduced duplication.
- Easier upgrades.
- Organization-wide governance.

### How Would You Secure a Docker Build Pipeline?

Design:

```text
Protected Main
      ↓
Pinned Build Actions
      ↓
Buildx
      ↓
Multi-stage Docker Build
      ↓
Security Scan
      ↓
SBOM
      ↓
Immutable Image
      ↓
ECR
      ↓
Staging
      ↓
Approval
      ↓
Production
```

Explain how action pinning and image immutability protect different parts of the supply chain.

## Key Takeaways

- Action version pinning makes workflow dependencies deterministic by ensuring security-sensitive workflows execute an explicitly selected revision rather than an uncontrolled mutable reference.
- SHA pinning is a supply-chain control, not a trust guarantee; source review, dependency security, least privilege, secret isolation, runner isolation, and artifact integrity remain necessary.
- Pinning must be paired with an update lifecycle: monitor releases, verify changes, update deliberately, run CI, review, deploy, and retain a known-good rollback reference.
- Production workflows should minimize the blast radius of third-party actions through restricted permissions, scoped secrets, controlled OIDC access, protected environments, and approved action sources.
- Enterprise-scale CI/CD should combine immutable action references with centralized governance, reusable workflows, dependency automation, action inventories, provenance, and incident-response procedures.