# 10- Logging and Platform Hook Failures

## Overview

Elastic Beanstalk deployments involve more than uploading application code. The Elastic Beanstalk platform prepares the EC2 instance, processes configuration, executes deployment hooks, starts the application, performs health checks, and exposes logs from multiple layers.

When a deployment fails, the application log alone is often insufficient. The failure may originate from:

- Elastic Beanstalk deployment orchestration
- Platform hooks
- `.ebextensions` configuration
- Dependency installation
- Environment variables
- File permissions
- Operating-system packages
- Application startup
- Reverse proxy configuration
- Health checks
- Network connectivity
- IAM permissions

A production troubleshooting workflow therefore needs to distinguish between **application logs**, **platform logs**, **deployment logs**, and **hook execution logs**.

A useful mental model is:

```text
Elastic Beanstalk Deployment
          │
          ├── Platform lifecycle
          │       ├── Build
          │       ├── Deploy
          │       └── Start application
          │
          ├── Configuration
          │       └── .ebextensions / environment configuration
          │
          ├── Platform hooks
          │       ├── prebuild
          │       ├── predeploy
          │       └── postdeploy
          │
          └── Application
                  ├── Gunicorn / Uvicorn
                  ├── Django / FastAPI
                  └── Application logs
```

The key production principle is:

> Diagnose the layer that failed instead of treating every deployment failure as an application-code problem.

## Elastic Beanstalk Logging Layers

Elastic Beanstalk exposes several categories of logs.

| Log category | What it helps diagnose |
|---|---|
| Application logs | Django, FastAPI, Gunicorn, Uvicorn, application exceptions |
| Web server logs | Nginx or Apache request and proxy failures |
| Elastic Beanstalk engine logs | Deployment and platform lifecycle failures |
| Hook-related output | Failures in platform hook execution |
| System logs | OS-level failures, processes, packages, permissions |
| Deployment events | High-level deployment state and failure messages |

The same failure can appear in multiple logs, but at different levels of detail.

For example:

```text
Deployment failed
       ↓
Elastic Beanstalk event
       ↓
Platform hook returned exit code 1
       ↓
eb-engine.log
       ↓
Hook command stderr
       ↓
Actual application/configuration error
```

The event tells you **what happened**. The platform logs often explain **why it happened**.

## Overview of Platform Hooks

Platform hooks provide a mechanism for executing custom commands during the Elastic Beanstalk environment lifecycle.

For modern Elastic Beanstalk Linux platforms, application source bundles can contain:

```text
.platform/
└── hooks/
    ├── prebuild/
    ├── predeploy/
    └── postdeploy/
```

A typical application might use:

```text
my-app/
├── .platform/
│   └── hooks/
│       ├── prebuild/
│       │   └── 01-install-system-dependency.sh
│       ├── predeploy/
│       │   └── 01-prepare-application.sh
│       └── postdeploy/
│           └── 01-restart-worker.sh
├── application/
├── requirements.txt
└── ...
```

Hooks are executed on the EC2 instance as part of the Elastic Beanstalk deployment lifecycle.

## Hook Lifecycle

The exact lifecycle depends on the platform and deployment operation, but conceptually:

```mermaid
flowchart TD
    A[Application Version Uploaded] --> B[Instance Receives Version]
    B --> C[Source Extracted]
    C --> D[prebuild Hooks]
    D --> E[Platform Build Steps]
    E --> F[predeploy Hooks]
    F --> G[Application Deployment]
    G --> H[Application Starts]
    H --> I[postdeploy Hooks]
    I --> J[Health Check]
    J --> K[Environment Healthy]
```

A failure at an earlier stage prevents later stages from completing.

For example:

```text
prebuild failure
      ↓
Build does not complete
      ↓
predeploy not reached
      ↓
Application not deployed
```

Understanding the lifecycle prevents incorrect troubleshooting.

## Hook Directories

### `.platform/hooks/prebuild`

Used for commands that should run before the platform performs its build/deployment work.

Typical use cases include:

- Preparing files
- Installing required system-level dependencies
- Generating build-time artifacts
- Preparing directories

Avoid putting application startup operations here.

### `.platform/hooks/predeploy`

Used after build-related processing but before the application is deployed.

Typical use cases include:

- Preparing deployment artifacts
- Performing controlled application preparation
- Creating required directories
- Applying deployment-time configuration

### `.platform/hooks/postdeploy`

Used after deployment.

Typical use cases include:

- Post-deployment initialization
- Starting auxiliary processes
- Running controlled post-deployment tasks
- Performing deployment verification

Be careful with database migrations or other destructive operations. A `postdeploy` hook can execute on every instance participating in the deployment.

## Platform Hooks Versus `.ebextensions`

These mechanisms solve related but different problems.

| Mechanism | Primary purpose |
|---|---|
| `.platform/hooks/` | Execute commands during platform lifecycle |
| `.platform/confighooks/` | Execute hooks during configuration deployments |
| `.ebextensions/` | Configure Elastic Beanstalk resources and instance settings |
| Environment properties | Runtime configuration |
| Application code | Business/application behavior |

A useful distinction is:

```text
Configuration
    ↓
.ebextensions

Lifecycle command execution
    ↓
.platform/hooks

Runtime environment values
    ↓
Elastic Beanstalk environment properties
```

Do not use platform hooks as a general replacement for every Elastic Beanstalk configuration mechanism.

## Configuration Hooks

Elastic Beanstalk also supports configuration hooks under:

```text
.platform/confighooks/
```

These are intended for configuration deployments rather than normal application-version deployments.

The structure follows the lifecycle-oriented pattern:

```text
.platform/
└── confighooks/
    ├── prebuild/
    ├── predeploy/
    └── postdeploy/
```

This distinction matters when troubleshooting because a hook that works during application deployment may not behave the same way during an environment configuration update.

## Hook Execution Environment

A hook executes on the EC2 instance, not inside an isolated generic shell environment.

The command therefore depends on:

- Operating-system packages
- File permissions
- Current working directory
- Available binaries
- Environment variables
- Platform version
- User permissions
- Application source layout

A script that works locally may fail in Elastic Beanstalk because the EC2 instance does not have the same environment.

For example:

```bash
#!/bin/bash

python manage.py migrate
```

may fail if:

- `python` is not the expected interpreter
- The current directory is incorrect
- Dependencies are not installed yet
- `manage.py` is not in the current directory
- Required environment variables are unavailable

## Make Hook Scripts Explicit

Production hook scripts should avoid relying on implicit shell behavior.

Prefer:

```bash
#!/bin/bash
set -euo pipefail

cd /var/app/staging

echo "Preparing application"
```

Important properties:

- `set -e` stops after a failed command.
- `set -u` detects undefined variables.
- `set -o pipefail` prevents failed pipeline commands from being hidden.
- Explicit `cd` avoids dependence on the current working directory.

Without these protections, a hook can continue after an important command fails and produce misleading deployment results.

## Hook File Permissions

A common cause of hook failure is incorrect executable permissions.

For example:

```bash
chmod +x .platform/hooks/postdeploy/01-verify.sh
```

The executable bit must be preserved in the deployment artifact.

A script may exist in the deployed source tree but still fail if the platform cannot execute it as expected.

A production CI pipeline should validate:

```text
Hook exists
    ↓
Correct path
    ↓
Executable permission
    ↓
Valid shell syntax
    ↓
Required commands available
```

## Shell Syntax Validation

Validate scripts before deployment.

```bash
bash -n .platform/hooks/postdeploy/01-verify.sh
```

This checks shell syntax without executing the script.

For multiple scripts:

```bash
find .platform/hooks -type f -print0 |
while IFS= read -r -d '' file; do
    bash -n "$file"
done
```

Static validation is particularly useful when deployments are automated through CI/CD.

## Common Hook Failure

A hook may contain:

```bash
#!/bin/bash

python manage.py collectstatic --noinput
python manage.py migrate
```

If `collectstatic` fails, the second command may never execute when `set -e` is enabled.

This is desirable because the deployment should fail rather than continue in a partially prepared state.

Without explicit failure handling, a script may produce confusing results.

## Capture Hook Output

Use explicit logging in production hooks.

```bash
#!/bin/bash
set -euo pipefail

LOG_FILE="/var/log/myapp-deploy.log"

echo "Starting deployment preparation" | tee -a "$LOG_FILE"

cd /var/app/staging

echo "Running application checks" | tee -a "$LOG_FILE"
python manage.py check 2>&1 | tee -a "$LOG_FILE"

echo "Deployment preparation completed" | tee -a "$LOG_FILE"
```

This provides a dedicated application-specific log while still allowing Elastic Beanstalk platform logs to capture command output.

Avoid logging:

- Passwords
- API keys
- Database credentials
- Session tokens
- Private certificates
- Authorization headers

## Platform Logs

When a deployment fails, inspect platform logs rather than relying exclusively on application output.

The Elastic Beanstalk platform engine maintains logs that can reveal:

- Deployment lifecycle failures
- Hook execution failures
- Configuration processing failures
- Application startup failures
- Platform command failures

A particularly important platform log on Linux environments is:

```text
/var/log/eb-engine.log
```

Depending on the platform version and operation, additional logs may be relevant.

The important diagnostic principle is:

> Start with the log that represents the layer where the failure occurred.

## Elastic Beanstalk CLI Log Retrieval

The Elastic Beanstalk CLI can retrieve environment logs.

```bash
eb logs
```

For all available instance logs:

```bash
eb logs --all
```

The exact log options available can vary with the installed Elastic Beanstalk CLI version, so use:

```bash
eb logs --help
```

when troubleshooting CLI behavior.

A production investigation should usually gather logs from all affected instances rather than inspecting only one instance.

## Streaming Logs

When supported by the installed Elastic Beanstalk CLI version, logs can be streamed:

```bash
eb logs --stream
```

This is useful during:

- Deployments
- Startup failures
- Reproduction attempts
- Health-check failures
- Runtime debugging

For automated systems, prefer centralized logging rather than relying on a developer terminal session.

## Deployment Events

Events provide the high-level timeline of what Elastic Beanstalk believes happened.

```bash
eb events
```

Typical information includes:

```text
Application version deployed
Instance deployment started
Hook execution failed
Instance became unhealthy
Deployment aborted
```

Events are useful for establishing the timeline.

They usually should not be treated as the complete root-cause log.

## Events Versus Logs

Use events and logs together.

| Source | Best for |
|---|---|
| `eb events` | Deployment timeline and high-level status |
| `eb logs` | Application and platform log inspection |
| `eb-engine.log` | Elastic Beanstalk engine/deployment details |
| Application logs | Runtime/application exceptions |
| Nginx logs | HTTP/proxy failures |
| System logs | OS and process failures |

A useful troubleshooting sequence is:

```text
Event
  ↓
Identify failed lifecycle stage
  ↓
Identify affected instance
  ↓
Inspect platform log
  ↓
Inspect hook output
  ↓
Inspect application log
  ↓
Determine root cause
```

## Hook Failure Due to Missing Environment Variables

A common problem is assuming a variable exists.

Example:

```bash
#!/bin/bash
set -euo pipefail

echo "Environment: $APP_ENV"
```

If `APP_ENV` is missing, `set -u` causes the script to fail.

For optional variables:

```bash
APP_ENV="${APP_ENV:-production}"
```

For required variables:

```bash
: "${DATABASE_URL:?DATABASE_URL must be configured}"

echo "Database configuration is present"
```

Never print the value of sensitive variables while troubleshooting.

## Environment Variable Expansion

Elastic Beanstalk environment variables are available to application processes and, depending on the lifecycle stage and platform behavior, can be used by deployment scripts.

However, deployment-time assumptions should be validated rather than assumed.

A safer pattern is:

```bash
#!/bin/bash
set -euo pipefail

: "${DJANGO_SETTINGS_MODULE:?DJANGO_SETTINGS_MODULE is required}"

cd /var/app/staging

python manage.py check
```

This produces an explicit failure instead of a confusing downstream exception.

## Secret Handling

Never do this:

```bash
echo "DATABASE_PASSWORD=$DATABASE_PASSWORD"
```

Do not log secrets simply because a deployment hook is failing.

Instead:

```bash
if [[ -n "${DATABASE_PASSWORD:-}" ]]; then
    echo "Database password is configured"
else
    echo "Database password is missing"
    exit 1
fi
```

The objective is to verify configuration without exposing the credential.

## Wrong Working Directory

A hook can fail because it assumes the application exists in a specific directory.

For example:

```bash
python manage.py check
```

may fail with:

```text
python: can't open file 'manage.py'
```

Use an explicit directory when the deployment stage requires it:

```bash
cd /var/app/staging
python manage.py check
```

The correct path depends on the lifecycle stage and Elastic Beanstalk platform behavior, so scripts should be tested against the actual target platform.

## Dependency Availability

A hook can execute before a dependency has been installed.

For example:

```bash
#!/bin/bash
set -euo pipefail

python manage.py check
```

may fail if the Python environment has not yet been prepared for that lifecycle stage.

The solution is not necessarily to install everything manually inside the hook.

Instead:

1. Determine when the command executes.
2. Determine when the required dependency becomes available.
3. Place the operation in the appropriate lifecycle stage.
4. Use the platform's supported dependency mechanism.

Avoid duplicating dependency installation logic across multiple hooks.

## Operating-System Package Failures

Hooks that install operating-system packages can fail because of:

- Incorrect package name
- Package repository failure
- Network connectivity
- Repository availability
- Unsupported package version
- Insufficient permissions
- Platform version differences

For example:

```bash
apt-get install some-package
```

may work on one Linux platform but fail on another.

Elastic Beanstalk platform upgrades can therefore break assumptions in custom hooks.

## Platform Version Dependency

A production hook is part of the infrastructure.

If it assumes:

```text
/usr/bin/some-tool
```

or a specific package manager, interpreter path, library version, or directory structure, the hook is coupled to the platform.

Document such assumptions.

When upgrading the Elastic Beanstalk platform:

```text
Current platform
      ↓
Test application version
      ↓
Execute all hooks
      ↓
Validate logs
      ↓
Validate health checks
      ↓
Promote platform version
```

Do not treat platform upgrades as purely cosmetic changes.

## Nginx and Platform Hook Failures

Elastic Beanstalk commonly uses a reverse proxy such as Nginx in front of the application process.

A hook that modifies Nginx configuration can cause:

```text
Hook modifies configuration
        ↓
Nginx configuration invalid
        ↓
Nginx fails to reload/start
        ↓
Application becomes unreachable
        ↓
Health check fails
```

Always validate generated Nginx configuration before reloading it when the platform workflow allows it.

A configuration change should be reversible.

## Application Startup and Hook Interaction

A successful hook does not guarantee a healthy application.

The deployment can progress through:

```text
Hook succeeds
    ↓
Application starts
    ↓
Application crashes
    ↓
Health check fails
```

Conversely:

```text
Application code is correct
    ↓
Hook fails
    ↓
Deployment fails
```

This is why platform logs and application logs must be analyzed independently.

## Database Migration Hooks

Database migrations deserve special attention.

A tempting pattern is:

```bash
python manage.py migrate
```

inside a `postdeploy` hook.

The problem is that multiple instances may execute the command independently.

For example:

```text
Deployment
   │
   ├── EC2-1 → migrate
   ├── EC2-2 → migrate
   ├── EC2-3 → migrate
   └── EC2-4 → migrate
```

Depending on the migration system and database state, this can cause:

- Lock contention
- Deployment delays
- Concurrent migration execution
- Partial deployment behavior
- Schema/application compatibility problems

Prefer a controlled migration strategy rather than assuming every instance should run migrations.

## Leader-Only Operations

Not every operation should execute on every instance.

Examples include:

- Database migrations
- One-time data initialization
- Global cache warming
- Certain scheduled setup tasks

If an operation must execute once per environment rather than once per instance, design the deployment process accordingly.

Do not assume a platform hook automatically provides leader-only semantics.

## Idempotent Hooks

Production hooks should ideally be idempotent.

An idempotent operation can safely run more than once without causing an incorrect final state.

For example:

```bash
mkdir -p /opt/myapp/cache
```

is naturally idempotent.

This is preferable to an operation that fails simply because the directory already exists.

For configuration:

```bash
if ! grep -q '^MY_SETTING=' /etc/myapp/app.conf; then
    echo 'MY_SETTING=value' >> /etc/myapp/app.conf
fi
```

The exact implementation should depend on the configuration system, but the principle remains:

> Assume deployment operations may be repeated.

## Hook Retry and Failure Semantics

A deployment system may retry, replace, or rerun operations depending on the failure and deployment strategy.

Therefore:

- Avoid destructive commands unless necessary.
- Avoid assuming a hook runs exactly once.
- Make operations idempotent where possible.
- Fail explicitly when correctness cannot be guaranteed.
- Log enough information to reconstruct what happened.

## Permission Failures

A hook can fail because it attempts to modify a protected location.

Example:

```bash
echo "config" > /etc/myapp/config
```

The command may fail due to permissions.

If elevated privileges are actually required, make the privilege boundary explicit and carefully controlled.

Avoid indiscriminate:

```bash
chmod 777 ...
```

or:

```bash
chown -R ...
```

These can create security and operational problems.

## Temporary File Failures

Hooks often create temporary files.

Use a controlled temporary directory and clean up appropriately.

For example:

```bash
#!/bin/bash
set -euo pipefail

tmp_dir="$(mktemp -d)"

cleanup() {
    rm -rf "$tmp_dir"
}

trap cleanup EXIT

echo "Preparing deployment in $tmp_dir"
```

This avoids leaving unpredictable temporary state behind.

## Network-Dependent Hooks

Hooks that download resources introduce external dependencies.

For example:

```text
Deployment
   ↓
Hook
   ↓
Download package
   ↓
Internet / repository
```

If the network is unavailable:

```text
Download fails
   ↓
Hook fails
   ↓
Deployment fails
```

Prefer:

- Version-pinned dependencies
- Existing package mechanisms
- Reliable artifact repositories
- Appropriate timeouts
- Minimal external calls during deployment

Avoid making deployment dependent on an unreliable third-party service whenever possible.

## Logging Failures

Logging itself can fail.

For example:

```bash
echo "Starting" >> /some/path/app.log
```

may fail if:

- Directory does not exist
- Permission is incorrect
- Disk is full
- Filesystem is unavailable

Do not make diagnostic logging so fragile that it hides the original error.

Use standard output/error alongside dedicated logs when appropriate.

## Disk Space Problems

Deployment failures can occur because the EC2 instance runs out of disk space.

Potential causes include:

- Large application artifacts
- Docker images
- Old logs
- Temporary files
- Package caches
- Large application uploads

Inspect disk usage during troubleshooting.

```bash
df -h
```

Inspect directory usage:

```bash
du -sh /var/log/*
```

Do not blindly delete files from system directories in production.

Determine which component is consuming disk space first.

## Process and Port Failures

A hook may start a process that conflicts with another process.

For example:

```text
Existing process → port 8000
Hook starts process → port 8000
                   ↓
                bind failure
```

Avoid manually managing processes that Elastic Beanstalk already manages unless there is a clear architectural reason.

For application servers, prefer the platform's supported process-management configuration.

## Deployment Logs as a Timeline

A good investigation reconstructs the deployment timeline.

Example:

```text
14:00:01 Version deployment begins
14:00:08 Source extracted
14:00:12 prebuild hook starts
14:00:13 Dependency installation succeeds
14:00:17 predeploy hook starts
14:00:18 manage.py check fails
14:00:18 Deployment marked failed
14:00:20 Instance remains unhealthy
```

This is much more useful than simply seeing:

```text
Deployment failed.
```

## Troubleshooting Methodology

Use the following sequence for platform-hook failures.

### Identify the Failed Operation

Determine whether the failure occurred during:

- Build
- Configuration
- Prebuild
- Predeploy
- Application startup
- Postdeploy
- Health check

### Identify the Affected Instance

A multi-instance environment may not have identical state at the moment of failure.

Determine:

- Which instance failed
- Whether all instances failed
- Whether only the newly deployed instance failed

### Inspect Elastic Beanstalk Events

```bash
eb events
```

Establish the timeline and identify the lifecycle stage.

### Retrieve Logs

```bash
eb logs
```

For all instances:

```bash
eb logs --all
```

Inspect the platform engine log when instance-level access is available:

```bash
sudo less /var/log/eb-engine.log
```

### Inspect Hook Output

Search platform logs for:

```text
hook
failed
exit code
stderr
command
```

For example:

```bash
sudo grep -iE 'hook|failed|exit code|stderr' /var/log/eb-engine.log
```

### Reproduce the Command

Once the failing command is identified, reproduce it manually on the affected instance when safe.

For example:

```bash
cd /var/app/staging
python manage.py check
```

This often converts an opaque deployment error into a direct application error.

### Verify the Environment

Check:

```bash
which python
python --version
pwd
env
df -h
```

Do not dump sensitive environment variables into logs.

Use targeted checks instead:

```bash
test -n "${DJANGO_SETTINGS_MODULE:-}" && echo "settings configured"
```

### Validate Permissions

```bash
ls -la .platform/hooks/
```

Confirm:

- File exists
- File is executable
- Ownership is appropriate
- Path is correct

### Validate Dependencies

Check whether required commands exist:

```bash
command -v python
command -v nginx
```

Use platform-appropriate commands for other dependencies.

### Validate Application State

For Django:

```bash
python manage.py check
```

For FastAPI, verify that the configured application server can import the application module.

Example:

```bash
python -c "import myapp"
```

### Verify Health

After correcting the issue:

```text
Deployment
   ↓
Hook succeeds
   ↓
Application starts
   ↓
Health check succeeds
   ↓
Traffic restored
```

Do not stop troubleshooting simply because the hook returned exit code `0`.

## Example: Failing Django Hook

Suppose:

```bash
#!/bin/bash
set -euo pipefail

cd /var/app/staging
python manage.py collectstatic --noinput
python manage.py check
```

Deployment reports a hook failure.

Investigate:

```bash
eb events
```

Then retrieve logs:

```bash
eb logs --all
```

Search platform logs:

```bash
sudo grep -iE 'hook|collectstatic|failed|error' /var/log/eb-engine.log
```

Possible result:

```text
python: can't open file 'manage.py'
```

The problem is not Django itself. The hook is executing from an incorrect location.

The fix is to verify the deployment directory and lifecycle stage rather than blindly reinstalling dependencies.

## Example: Missing Python Dependency

Suppose the hook executes:

```bash
python manage.py check
```

and fails with:

```text
ModuleNotFoundError: No module named 'django'
```

The likely issue is lifecycle ordering or incorrect Python environment selection.

Investigate:

```bash
which python
python --version
python -m pip --version
```

Then verify the platform's dependency installation stage and ensure the hook executes only after the required runtime is available.

Avoid installing application dependencies manually in multiple places.

## Example: Hook Works Locally but Fails in CI/CD

Local:

```text
Hook succeeds
```

Elastic Beanstalk:

```text
Hook fails
```

Compare:

| Area | Local | Elastic Beanstalk |
|---|---|---|
| OS | Developer machine | EC2 platform |
| Python | Local version | Platform version |
| Environment variables | Local `.env` | EB environment |
| Working directory | Repository root | Deployment lifecycle directory |
| Permissions | Developer user | Platform execution context |
| Dependencies | Already installed | Lifecycle-dependent |
| Network | Local network | AWS VPC/network path |

The environment is part of the deployment contract.

## CI/CD Validation

Platform hooks should be validated before deployment.

A CI pipeline can perform:

```bash
bash -n .platform/hooks/prebuild/*
bash -n .platform/hooks/predeploy/*
bash -n .platform/hooks/postdeploy/*
```

It can also verify that expected files exist:

```bash
test -f .platform/hooks/postdeploy/01-verify.sh
```

For Python applications:

```bash
python -m compileall .
```

The more deployment assumptions are validated before production, the fewer failures need to be diagnosed on live instances.

## Production Logging Architecture

For production systems, treat Elastic Beanstalk instance logs as operational sources rather than the permanent source of truth.

A common architecture is:

```text
Application
    │
    ├── stdout/stderr
    ├── Nginx logs
    └── Platform logs
             │
             ▼
      CloudWatch Logs
             │
             ├── Metrics
             ├── Alarms
             └── Investigation
```

Centralized logs are particularly important when Auto Scaling creates and terminates instances.

Otherwise, useful logs can disappear with the instance.

## Logging and Auto Scaling

Consider:

```text
EC2-1
  └── Deployment failure logs

EC2-2
  └── Healthy

EC2-1 terminated
```

If logs existed only on EC2-1, the most useful diagnostic evidence may disappear.

Production environments should therefore centralize important logs where appropriate.

## Logging Security

Logs can become a security vulnerability.

Never log:

- Database passwords
- AWS access keys
- Secret keys
- JWT tokens
- Session cookies
- Authorization headers
- Private credentials

Be especially careful with shell debugging:

```bash
set -x
```

Shell tracing can expose command arguments and secrets.

Do not enable it indiscriminately in production deployment hooks.

## Common Mistakes

### Debugging Only Application Logs

The application may never have started.

If the failure occurred in `prebuild`, Django or FastAPI logs may contain nothing useful.

Start with the deployment lifecycle and platform logs.

### Assuming Hook Failure Means Code Failure

A hook can fail because of:

- Permissions
- Missing executable
- Wrong directory
- Missing dependency
- Platform mismatch
- Network failure

Classify the failure first.

### Ignoring Exit Codes

A shell command returning non-zero indicates failure.

Use:

```bash
set -euo pipefail
```

when appropriate so failed commands do not silently pass.

### Hard-Coding Paths

Hard-coded assumptions about platform directories can break after platform changes.

Use documented platform behavior and validate paths against the target platform.

### Assuming Hooks Run Only Once

In a multi-instance environment, hooks can execute on multiple instances.

Design operations accordingly.

### Running Migrations on Every Instance

This can create concurrency and deployment problems.

Use a controlled migration strategy.

### Logging Secrets

Debugging should never require exposing credentials.

Log state, not secrets.

### Ignoring File Permissions

A hook can be present but not executable.

Validate permissions in CI/CD.

### Downloading Unpinned Dependencies

A deployment that depends on whatever version is available at deployment time is less reproducible.

Prefer version-pinned artifacts and deterministic dependency installation.

### Making Hooks Too Large

A giant shell script that performs:

```text
OS configuration
+
application deployment
+
database migration
+
cache warming
+
process management
+
external API calls
```

becomes difficult to reason about and troubleshoot.

Keep lifecycle responsibilities focused.

## Production Best Practices

### Keep Hooks Small

Each hook should perform a narrowly defined operation.

Prefer:

```text
01-prepare.sh
02-validate.sh
03-configure.sh
```

over one extremely large script.

### Fail Fast

Use:

```bash
set -euo pipefail
```

when appropriate.

### Make Operations Idempotent

Prefer:

```bash
mkdir -p /opt/myapp
```

over commands that fail if the desired state already exists.

### Validate Inputs

Check required variables and files explicitly.

```bash
: "${DJANGO_SETTINGS_MODULE:?DJANGO_SETTINGS_MODULE is required}"
```

### Avoid Secrets in Logs

Log:

```text
DATABASE_URL configured
```

not:

```text
DATABASE_URL=postgres://user:password@host/db
```

### Pin Dependencies

Use deterministic dependency versions where practical.

### Minimize Network Dependencies

Avoid unnecessary external downloads during deployment.

### Test Platform Upgrades

Treat Elastic Beanstalk platform upgrades as infrastructure changes.

### Centralize Logs

Use centralized logging for production diagnostics.

### Monitor Deployment Failures

Create operational visibility around:

- Deployment failures
- Instance health
- HTTP 5xx errors
- Application startup failures
- Auto Scaling activity

### Keep Rollback Possible

Deployment processes should make it possible to return to a known-good application version when a new version fails.

## Interview Traps

### "Where do you look when an Elastic Beanstalk deployment fails?"

A strong answer is not simply "application logs."

Start with:

```text
Elastic Beanstalk events
        ↓
Platform/deployment logs
        ↓
Hook output
        ↓
Application/web-server logs
```

The exact order depends on the reported failure stage.

### "Why can a hook work locally but fail in Elastic Beanstalk?"

Because the execution environment differs:

- OS
- permissions
- environment variables
- Python/runtime version
- working directory
- dependencies
- network
- filesystem layout

### "Why should migrations not blindly run on every instance?"

Because a multi-instance deployment can execute the migration concurrently from several instances, creating locking, ordering, and deployment consistency problems.

### "Why are centralized logs important with Auto Scaling?"

Because instances can be replaced or terminated. Instance-local logs can disappear with the instance.

### "What is the difference between a platform hook and application code?"

Application code implements business behavior. Platform hooks execute infrastructure/deployment lifecycle operations on the Elastic Beanstalk instance.

## Troubleshooting Checklist

### Deployment

- [ ] Check `eb events`
- [ ] Identify the failed deployment stage
- [ ] Identify affected instances
- [ ] Check application version
- [ ] Check platform version

### Platform Hooks

- [ ] Verify hook path
- [ ] Verify executable permissions
- [ ] Validate shell syntax
- [ ] Check lifecycle stage
- [ ] Check working directory
- [ ] Check required binaries
- [ ] Check required environment variables
- [ ] Check permissions
- [ ] Check exit codes
- [ ] Check platform compatibility

### Logs

- [ ] Retrieve `eb logs`
- [ ] Retrieve logs from all instances when appropriate
- [ ] Inspect `eb-engine.log`
- [ ] Inspect application logs
- [ ] Inspect Nginx logs
- [ ] Inspect system logs
- [ ] Search for hook and exit-code messages
- [ ] Preserve relevant logs centrally

### Application

- [ ] Validate Python/runtime version
- [ ] Validate dependencies
- [ ] Run Django `check` where applicable
- [ ] Verify application importability
- [ ] Verify startup command
- [ ] Verify environment variables
- [ ] Verify database connectivity
- [ ] Verify health endpoint

### Security

- [ ] Ensure secrets are not logged
- [ ] Avoid shell tracing with sensitive arguments
- [ ] Review hook permissions
- [ ] Review downloaded artifacts
- [ ] Avoid unnecessary privileged operations

## Key Takeaways

- Elastic Beanstalk troubleshooting requires visibility into both the application and the platform lifecycle.
- Platform hooks execute custom commands during Elastic Beanstalk deployment and configuration lifecycles.
- Modern Linux platform hooks are organized under `.platform/hooks/`, including `prebuild`, `predeploy`, and `postdeploy`.
- Configuration hooks are available under `.platform/confighooks/` for configuration-related operations.
- Platform hooks are different from `.ebextensions`; use each mechanism for the problem it is designed to solve.
- `eb events` is useful for understanding the deployment timeline and high-level failure state.
- `eb logs` provides access to environment logs and should be combined with platform and application log inspection.
- `/var/log/eb-engine.log` is an important source for Elastic Beanstalk deployment-engine diagnostics on Linux environments.
- A hook can fail before the application ever starts, so application logs may contain no useful information.
- Hook scripts should use explicit paths, validate required inputs, and fail clearly when critical commands fail.
- `set -euo pipefail` is useful for making shell-hook failures explicit.
- Hook scripts should be executable and syntactically validated before deployment.
- Lifecycle ordering matters; a command can fail simply because its required dependency is not available at that stage.
- Hooks can depend on the operating system, platform version, runtime, permissions, filesystem layout, and network environment.
- Platform upgrades can break custom hooks that depend on undocumented or platform-specific assumptions.
- Keep deployment hooks small, focused, deterministic, and preferably idempotent.
- Do not assume a platform hook runs only once; multi-instance environments can execute lifecycle operations across multiple instances.
- Database migrations should not blindly run independently on every application instance.
- Avoid exposing credentials, tokens, passwords, or other sensitive values in hook or application logs.
- Centralized logging is important because Auto Scaling can terminate the instance that contains the most useful diagnostic evidence.
- Logging should support diagnosis without becoming a source of sensitive-data leakage.
- A successful hook does not guarantee a healthy application, and a healthy application does not imply every deployment hook succeeded.
- Troubleshooting should reconstruct the deployment timeline and identify the exact lifecycle stage where behavior diverged from the expected state.
- The strongest production approach is to validate hooks in CI/CD, test them against the target platform version, centralize logs, and keep rollback to a known-good application version available.