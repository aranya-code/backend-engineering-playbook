# 01- Elastic Beanstalk CLI Fundamentals

## Overview

The Elastic Beanstalk Command Line Interface (EB CLI) is a developer-oriented command-line tool for creating, configuring, deploying, inspecting, and operating Elastic Beanstalk applications.

It provides commands that map closely to the Elastic Beanstalk application and environment model, allowing backend engineers to manage deployments without manually constructing every Elastic Beanstalk API request.

For production engineering, the EB CLI is most useful for:

- Initial application and environment setup
- Local-to-environment deployment workflows
- Environment inspection
- Application configuration
- Log retrieval
- Health and event inspection
- Environment scaling
- Operational troubleshooting
- Deployment automation

The EB CLI should not be confused with the AWS CLI. The AWS CLI is the general-purpose interface for AWS services, while the EB CLI provides a workflow-oriented interface specifically designed around Elastic Beanstalk.

## EB CLI vs AWS CLI

| Tool | Primary purpose | Typical use |
|---|---|---|
| EB CLI | Elastic Beanstalk workflows | `eb deploy`, `eb health`, `eb logs` |
| AWS CLI | General AWS resource management | `aws ec2`, `aws iam`, `aws s3`, `aws elasticbeanstalk` |
| AWS Console | Interactive management | Configuration, inspection, troubleshooting |
| CI/CD pipeline | Automated delivery | Build, test, deploy, verify |

A backend engineer may use all three.

For example:

```text
Developer
   │
   ├── EB CLI ───────────────► Elastic Beanstalk deployment
   │
   ├── AWS CLI ──────────────► Supporting AWS resources
   │
   └── Git / CI/CD ──────────► Automated source delivery
```

The EB CLI should generally be treated as a deployment and operational convenience layer rather than the only interface to AWS.

## Installation and Verification

After installing the EB CLI, verify that it is available:

```bash
eb --version
```

Display the available commands:

```bash
eb --help
```

Get help for a specific command:

```bash
eb deploy --help
```

This is useful because command options can vary with EB CLI versions.

## Authentication

The EB CLI ultimately operates against AWS resources and therefore requires AWS credentials with appropriate permissions.

A common local-development setup uses the AWS CLI credential configuration:

```bash
aws configure
```

Verify the active identity:

```bash
aws sts get-caller-identity
```

The response identifies the AWS account and principal being used.

For example:

```json
{
  "UserId": "AIDAXXXXXXXXXXXXXXXX",
  "Account": "123456789012",
  "Arn": "arn:aws:iam::123456789012:user/developer"
}
```

Do not use highly privileged credentials simply because they make initial setup easier.

For production workflows, prefer short-lived credentials and IAM roles through the CI/CD platform or AWS identity mechanisms rather than storing long-lived access keys.

## EB CLI Project Structure

The EB CLI associates a local project with an Elastic Beanstalk application and environment through the `.elasticbeanstalk` directory.

A typical project may look like:

```text
backend-service/
├── .elasticbeanstalk/
│   └── config.yml
├── application/
├── manage.py
├── requirements.txt
├── Procfile
└── .gitignore
```

The `.elasticbeanstalk/config.yml` file contains EB CLI configuration for the local project.

It should not be confused with application configuration.

For example:

- `.elasticbeanstalk/config.yml` → EB CLI project configuration
- `.ebextensions/` → Elastic Beanstalk environment configuration
- `.platform/` → platform hooks and platform-specific configuration
- application settings → Django/FastAPI application configuration

## Initialize a Project

The first major EB CLI command is:

```bash
eb init
```

This associates the current directory with an Elastic Beanstalk application.

The interactive process typically asks for information such as:

- AWS region
- Application name
- Platform
- Platform version
- SSH configuration

After initialization, the project contains the Elastic Beanstalk configuration required by the EB CLI.

A typical workflow is:

```bash
cd backend-service

eb init
```

Then verify the configuration:

```bash
eb status
```

## Creating an Environment

An Elastic Beanstalk application can contain multiple environments.

For example:

```text
Application: orders-api

├── development
├── staging
└── production
```

Create an environment with:

```bash
eb create staging
```

The environment name becomes the logical identifier used by subsequent EB CLI commands.

For example:

```bash
eb create production
```

Creating an environment can provision or configure several underlying AWS resources depending on the selected platform and configuration.

The important distinction is:

```text
Elastic Beanstalk Application
        │
        ├── Environment A
        ├── Environment B
        └── Environment C
```

An application is the logical container for environments. The environment is the deployable runtime.

## Selecting an Environment

A local project can work with multiple environments.

List environments:

```bash
eb list
```

Switch the current environment:

```bash
eb use staging
```

Then verify:

```bash
eb status
```

This is important when operating multiple environments because commands such as `eb deploy` act on the currently selected environment unless another environment is explicitly specified.

A useful production habit is to verify the target before deploying:

```bash
eb status
```

Do not assume the current environment is correct.

## Checking Environment Status

Use:

```bash
eb status
```

This provides a high-level view of the current environment.

Typical information includes:

- Environment name
- Application name
- Platform
- Health
- CNAME
- Current version

For a more operationally useful view:

```bash
eb health
```

The health command can provide information about environment health and individual instances.

This is useful when determining whether a deployment problem is:

- Application-wide
- Instance-specific
- Load-balancer-related
- Capacity-related
- Platform-related

## Deployment

The primary deployment command is:

```bash
eb deploy
```

A typical backend deployment flow is:

```text
Local source
     │
     ▼
EB CLI
     │
     ▼
Application version
     │
     ▼
Elastic Beanstalk environment
     │
     ▼
EC2 instances
     │
     ▼
Application process
```

Deploy the current source:

```bash
eb deploy
```

Deploy to a specific environment:

```bash
eb deploy staging
```

For production, explicitly specifying the environment can reduce accidental deployments:

```bash
eb deploy production
```

The deployment process packages the application source and uploads it for Elastic Beanstalk to deploy according to the environment configuration.

## Deployment Versioning

Elastic Beanstalk creates application versions as part of its deployment model.

This makes the distinction between:

```text
Source code
    │
    ▼
Application Version
    │
    ▼
Environment
```

important.

An environment is not simply a directory containing the latest source code. It points to an application version that Elastic Beanstalk deploys.

This model supports controlled deployments and environment updates.

## Application Versions and Deployment Safety

Production deployments should be associated with identifiable versions.

Avoid relying on ambiguous deployment labels such as:

```text
latest
test
new
final
```

Prefer identifiers that can be traced to source control:

```text
orders-api-8f31c2a
orders-api-v2026.08.13.1
```

A useful deployment relationship is:

```text
Git commit
    │
    ▼
CI build
    │
    ▼
Application version
    │
    ▼
Elastic Beanstalk environment
```

This makes rollback and incident investigation significantly easier.

## Viewing Events

Elastic Beanstalk events are useful for understanding environment activity.

Run:

```bash
eb events
```

Events can reveal issues such as:

- Deployment failures
- Instance launches
- Instance termination
- Configuration changes
- Health transitions
- Platform operations
- Load balancer events

For troubleshooting, events should usually be inspected before assuming the application code is responsible.

## Retrieving Logs

Application and environment logs are one of the most important operational features of the EB CLI.

Retrieve logs:

```bash
eb logs
```

Retrieve recent logs:

```bash
eb logs --all
```

The exact available options depend on the EB CLI version, so use:

```bash
eb logs --help
```

Logs should be correlated with:

```text
Deployment
   │
   ├── EB events
   ├── Environment health
   ├── Application logs
   ├── Load balancer logs
   └── CloudWatch metrics
```

Do not rely exclusively on application logs. Infrastructure-level failures can occur before the request reaches Django, FastAPI, or another application process.

## SSH Access

For environments where SSH access is configured and permitted:

```bash
eb ssh
```

This can be useful for diagnosing:

- Running processes
- Local filesystem state
- Application startup
- Environment variables
- Installed packages
- Runtime configuration
- Instance-level problems

Example:

```bash
eb ssh production
```

SSH should be treated as a troubleshooting mechanism rather than the normal production deployment mechanism.

Avoid making undocumented manual changes directly on an instance because those changes may disappear when Elastic Beanstalk replaces the instance.

## Environment Variables

Inspect environment variables:

```bash
eb printenv
```

Set an environment variable:

```bash
eb setenv DJANGO_SETTINGS_MODULE=config.settings.production
```

Multiple variables can be configured together:

```bash
eb setenv \
  DJANGO_SETTINGS_MODULE=config.settings.production \
  LOG_LEVEL=INFO
```

Remove an environment variable:

```bash
eb unsetenv LOG_LEVEL
```

Environment variables are useful for non-secret configuration.

Sensitive values should generally be managed through AWS Secrets Manager or AWS Systems Manager Parameter Store with appropriate IAM controls rather than being casually exposed through command history, logs, source control, or scripts.

## Configuration Management

Elastic Beanstalk configuration can exist at multiple layers.

| Mechanism | Purpose |
|---|---|
| `eb init` | Initialize local EB CLI configuration |
| `eb setenv` | Configure environment variables |
| `.elasticbeanstalk/` | EB CLI project configuration |
| `.ebextensions/` | Environment configuration |
| `.platform/` | Platform hooks and runtime customization |
| Elastic Beanstalk configuration | Environment-level AWS settings |
| Infrastructure as Code | Repeatable infrastructure management |

A production system should avoid depending on undocumented console changes.

Configuration should be reproducible.

## Common Configuration Files

A Python backend might use:

```text
backend-service/
├── .elasticbeanstalk/
│   └── config.yml
├── .ebextensions/
│   ├── 01-packages.config
│   └── 02-environment.config
├── .platform/
│   └── hooks/
├── application/
├── requirements.txt
└── Procfile
```

The exact structure depends on the Elastic Beanstalk platform and application architecture.

## Application Commands

The EB CLI exposes several commands commonly used during development and operations.

| Command | Purpose |
|---|---|
| `eb init` | Initialize an Elastic Beanstalk application |
| `eb create` | Create an environment |
| `eb list` | List environments |
| `eb use` | Select an environment |
| `eb status` | Show environment status |
| `eb health` | Inspect environment health |
| `eb deploy` | Deploy application source |
| `eb events` | View environment events |
| `eb logs` | Retrieve logs |
| `eb printenv` | Display environment variables |
| `eb setenv` | Set environment variables |
| `eb unsetenv` | Remove environment variables |
| `eb ssh` | Connect to an instance |
| `eb open` | Open the application URL |
| `eb config` | Display environment configuration |
| `eb scale` | Configure environment capacity |
| `eb swap` | Swap environment CNAMEs |
| `eb terminate` | Terminate an environment |

Use command-specific help when uncertain:

```bash
eb <command> --help
```

## Opening the Application

Open the environment URL:

```bash
eb open
```

This is primarily a convenience command.

For production systems, traffic normally enters through controlled DNS and load-balancing architecture rather than developers manually opening an Elastic Beanstalk endpoint.

## Scaling

Elastic Beanstalk environments can be configured with multiple instances.

The EB CLI provides:

```bash
eb scale
```

For example:

```bash
eb scale 3
```

Scaling should not be treated as a substitute for capacity planning.

Production capacity depends on:

- Request rate
- CPU utilization
- Memory consumption
- Database capacity
- Network throughput
- Background jobs
- External API latency
- Instance type
- Auto Scaling configuration

For production environments, automatic scaling is generally more appropriate than repeatedly changing instance counts manually.

## Environment Configuration

Inspect environment configuration:

```bash
eb config
```

Configuration should be treated as infrastructure state.

For production environments, changes should ideally follow a controlled workflow:

```text
Configuration change
        │
        ▼
Version control
        │
        ▼
Review
        │
        ▼
CI/CD
        │
        ▼
Elastic Beanstalk
        │
        ▼
Validation
```

This reduces configuration drift between environments.

## Environment Swapping

Elastic Beanstalk supports environment swapping:

```bash
eb swap production --destination staging
```

The exact command syntax should be confirmed using:

```bash
eb swap --help
```

Environment swapping can be useful for deployment strategies where two environments represent different application versions.

The important architectural idea is:

```text
Environment A ── Version A
Environment B ── Version B

        │
        ▼
Traffic mapping can be switched
```

However, environment swapping should not be treated as a universal replacement for blue/green deployment design. Database migrations, external dependencies, sessions, caches, and backward compatibility must also be considered.

## Terminating an Environment

Terminate an environment with:

```bash
eb terminate staging
```

For production environments, termination is a destructive operation and should be treated carefully.

Before terminating:

```bash
eb status
eb events
```

Confirm:

- Correct environment
- Correct AWS account
- Current deployment state
- Required backups
- Dependent resources
- DNS configuration
- Database lifecycle
- Data-retention requirements

Avoid using destructive commands in automation without explicit safeguards.

## Deployment Workflow for a Python Backend

A Django or FastAPI deployment might follow:

```text
Developer
   │
   ▼
Git commit
   │
   ▼
Tests / Build
   │
   ▼
EB CLI
   │
   ▼
eb deploy
   │
   ▼
Application Version
   │
   ▼
Elastic Beanstalk
   │
   ├── EC2
   ├── Load Balancer
   └── Auto Scaling
   │
   ▼
Health Checks
   │
   ▼
Application Ready
```

A typical local workflow:

```bash
git status
git add .
git commit -m "deploy orders API"

eb status
eb health
eb deploy staging

eb events
eb health
eb logs
```

The deployment should be followed by verification rather than assuming that a successful upload means the application is healthy.

## Production CI/CD

The EB CLI can be used in CI/CD, but production pipelines should not simply execute:

```bash
eb deploy production
```

without validation.

A more robust pipeline is:

```text
Commit
  │
  ▼
Unit Tests
  │
  ▼
Integration Tests
  │
  ▼
Security / Dependency Checks
  │
  ▼
Build
  │
  ▼
Deploy Staging
  │
  ▼
Smoke Tests
  │
  ▼
Approval / Promotion
  │
  ▼
Deploy Production
  │
  ▼
Health Verification
  │
  ├── Healthy ──► Complete
  │
  └── Unhealthy ─► Rollback / Incident Response
```

The deployment identity should have only the permissions required for the deployment workflow.

## Operational Troubleshooting Workflow

When a deployment fails, avoid immediately changing application code.

Use a structured process:

### Check the environment

```bash
eb status
```

### Check health

```bash
eb health
```

### Check events

```bash
eb events
```

### Retrieve logs

```bash
eb logs
```

### Inspect configuration

```bash
eb config
```

### Inspect environment variables

```bash
eb printenv
```

### Access an instance when necessary

```bash
eb ssh
```

This creates a troubleshooting chain:

```text
Status
  │
  ▼
Health
  │
  ▼
Events
  │
  ▼
Logs
  │
  ▼
Configuration
  │
  ▼
Instance inspection
```

This approach prevents random configuration changes and helps isolate the failure domain.

## Common Failure Patterns

| Symptom | First investigation |
|---|---|
| Deployment failed | `eb events` |
| Environment unhealthy | `eb health` |
| Application returns 5xx | Application logs |
| Application does not start | Startup command and logs |
| Instances fail health checks | Health endpoint, process, port, security groups |
| Configuration appears wrong | `eb config` |
| Missing runtime setting | `eb printenv` |
| One instance behaves differently | Instance health and `eb ssh` |
| Deployment succeeded but API fails | Application logs and health checks |
| Environment cannot reach dependency | VPC, security groups, routes, DNS |
| Slow requests | Application metrics, database, load balancer, CloudWatch |

## Security Considerations

The EB CLI is an operational interface and therefore should be treated as a privileged tool.

### Use least privilege

The IAM principal used by the EB CLI should have only the permissions required for the intended operation.

Avoid:

```text
Developer CLI
     │
     ▼
AdministratorAccess
```

Prefer:

```text
Developer CLI
     │
     ▼
Scoped IAM permissions
     │
     ├── Elastic Beanstalk
     ├── Required supporting services
     └── Read-only diagnostics where appropriate
```

### Protect credentials

Do not place AWS credentials directly in:

- Git repositories
- `.env` files committed to source control
- Dockerfiles
- shell scripts
- CI logs
- application configuration
- documentation

Use appropriate AWS identity mechanisms and secret-management services.

### Protect production operations

Separate development and production permissions.

For example:

```text
Developer
   │
   └── Development / Staging

CI/CD Role
   │
   └── Controlled Production Deployment

Platform Administrator
   │
   └── Infrastructure Operations
```

This reduces the blast radius of compromised credentials.

## Performance Considerations

The EB CLI itself is not normally part of the application's request path, so its performance has little direct effect on API latency.

Its operational impact is indirect.

Poor deployment practices can cause:

- Longer deployment windows
- Excessive instance replacement
- Unnecessary application restarts
- Configuration churn
- Increased deployment risk

For backend systems, deployment performance should therefore be evaluated together with:

- Application startup time
- Dependency installation time
- Health-check duration
- Database migration duration
- Instance provisioning time
- Load balancer registration
- Deployment strategy

## Cost Considerations

Most EB CLI commands do not introduce a meaningful standalone application cost. The underlying AWS resources do.

For example:

```text
eb create
   │
   └── May provision resources such as:
       ├── EC2 instances
       ├── Load Balancer
       ├── Auto Scaling
       └── Other configured resources
```

Therefore, `eb create` is not simply a local CLI operation.

Review the resulting infrastructure and its associated costs.

Similarly, retaining many application versions, logs, snapshots, or additional environments can contribute to operational cost.

## Common Mistakes

### Deploying to the wrong environment

A developer runs:

```bash
eb deploy
```

without checking the active environment.

Prevent this with:

```bash
eb status
```

before production deployments.

### Treating EB CLI configuration as application configuration

The `.elasticbeanstalk` directory controls EB CLI behavior. It does not replace proper application configuration management.

### Using administrator credentials

Giving the EB CLI unrestricted AWS access makes a compromised developer workstation or CI runner much more dangerous.

Use least privilege.

### Storing secrets with source configuration

Commands such as:

```bash
eb setenv DATABASE_PASSWORD=...
```

can expose sensitive information through shell history, process handling, terminal output, or operational workflows.

Use managed secret storage for sensitive credentials.

### Using SSH as a deployment mechanism

Manual changes through:

```bash
eb ssh
```

are difficult to reproduce and can disappear when instances are replaced.

Use version-controlled configuration and automated deployments instead.

### Assuming successful deployment means healthy application

A deployment can complete while the application remains unhealthy.

Always verify:

```bash
eb health
```

and inspect events and logs when necessary.

### Ignoring environment drift

Manual console changes combined with CLI deployments can produce environments that are difficult to reproduce.

Use controlled configuration and infrastructure automation.

### Treating rollback as an afterthought

A production deployment should have a defined recovery strategy before deployment begins.

## Interview Traps

### Is EB CLI the same as AWS CLI?

No.

The AWS CLI is a general AWS management interface. The EB CLI is specialized around Elastic Beanstalk application and environment workflows.

### Does `eb deploy` deploy directly to EC2?

Conceptually, the command deploys an application version to the Elastic Beanstalk environment. Elastic Beanstalk then orchestrates deployment to the underlying resources.

### Does Elastic Beanstalk eliminate the need for IAM?

No.

Elastic Beanstalk relies heavily on IAM for service operations, instance permissions, deployment access, and access to supporting AWS services.

### Does the EB CLI replace CI/CD?

No.

The EB CLI can be used by CI/CD, but production delivery still requires testing, approvals where appropriate, deployment controls, health verification, and rollback strategies.

### Does SSH configuration make an application production-ready?

No.

SSH is an operational troubleshooting capability. Production readiness depends on repeatable configuration, security controls, observability, deployment automation, and reliable recovery procedures.

### Is an Elastic Beanstalk environment the same thing as an application?

No.

An Elastic Beanstalk application is a logical container for versions and environments. An environment represents a running deployment of the application.

## Practical Command Reference

| Task | Command |
|---|---|
| Show EB CLI version | `eb --version` |
| Show help | `eb --help` |
| Initialize project | `eb init` |
| Create environment | `eb create <environment>` |
| List environments | `eb list` |
| Select environment | `eb use <environment>` |
| Check status | `eb status` |
| Check health | `eb health` |
| Deploy | `eb deploy` |
| Deploy to environment | `eb deploy <environment>` |
| View events | `eb events` |
| Retrieve logs | `eb logs` |
| Show environment variables | `eb printenv` |
| Set environment variables | `eb setenv KEY=value` |
| Remove environment variable | `eb unsetenv KEY` |
| Open application | `eb open` |
| SSH into instance | `eb ssh` |
| View configuration | `eb config` |
| Scale environment | `eb scale <count>` |
| Swap environments | `eb swap` |
| Terminate environment | `eb terminate <environment>` |

Always verify command syntax for the installed EB CLI version:

```bash
eb <command> --help
```

## Recommended Production Workflow

A disciplined production workflow can be reduced to:

```bash
# Confirm repository state
git status

# Confirm the target environment
eb status

# Inspect current health
eb health

# Deploy
eb deploy production

# Verify environment activity
eb events

# Verify application health
eb health
```

If the deployment is unhealthy:

```bash
eb events
eb logs
eb health
```

Then determine whether the failure originates in:

- Application code
- Startup configuration
- Dependency installation
- Environment variables
- Infrastructure
- Networking
- Database connectivity
- Health checks
- Load balancing
- IAM permissions

## Key Takeaways

- The EB CLI provides a workflow-oriented interface for Elastic Beanstalk applications and environments.
- `eb init`, `eb create`, `eb use`, and `eb deploy` form the core application deployment workflow.
- Always understand which environment is currently selected before performing operational actions.
- `eb status`, `eb health`, `eb events`, and `eb logs` form the core troubleshooting workflow.
- `eb printenv` and `eb setenv` are useful for environment configuration, but sensitive secrets should be managed through appropriate AWS secret-management services.
- Treat `.elasticbeanstalk`, `.ebextensions`, `.platform`, and application configuration as different configuration layers.
- Use IAM least privilege for local and CI/CD access.
- Do not use SSH or manual console changes as a substitute for reproducible deployments.
- Production deployments should include testing, controlled promotion, health verification, and a rollback strategy.
- The EB CLI does not replace the AWS CLI, IAM, infrastructure automation, observability, or CI/CD.
- Successful deployment does not necessarily mean a healthy application; always verify the environment after deployment.
- The most important production skill is not memorizing EB CLI commands but understanding how each command affects the Elastic Beanstalk environment and its underlying AWS infrastructure.