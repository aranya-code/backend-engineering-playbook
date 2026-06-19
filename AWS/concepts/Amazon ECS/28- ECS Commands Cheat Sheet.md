# ECS Commands Cheat Sheet

# AWS CLI Configuration

## Verify AWS CLI

```bash
aws --version
```

---

## Configure Credentials

```bash
aws configure
```

---

## Verify Identity

```bash
aws sts get-caller-identity
```

---

# ECS Cluster Commands

## List Clusters

```bash
aws ecs list-clusters
```

---

## Describe Cluster

```bash
aws ecs describe-clusters \
--clusters my-cluster
```

---

## Create Cluster

```bash
aws ecs create-cluster \
--cluster-name my-cluster
```

---

## Delete Cluster

```bash
aws ecs delete-cluster \
--cluster my-cluster
```

---

# Task Definition Commands

## List Task Definitions

```bash
aws ecs list-task-definitions
```

---

## Describe Task Definition

```bash
aws ecs describe-task-definition \
--task-definition my-app
```

---

## Register Task Definition

```bash
aws ecs register-task-definition \
--cli-input-json file://task-def.json
```

---

## Deregister Revision

```bash
aws ecs deregister-task-definition \
--task-definition my-app:5
```

---

# Task Commands

## List Tasks

```bash
aws ecs list-tasks \
--cluster my-cluster
```

---

## Describe Tasks

```bash
aws ecs describe-tasks \
--cluster my-cluster \
--tasks TASK_ID
```

---

## Run Task

```bash
aws ecs run-task \
--cluster my-cluster \
--task-definition my-app
```

---

## Stop Task

```bash
aws ecs stop-task \
--cluster my-cluster \
--task TASK_ID
```

---

# Service Commands

## List Services

```bash
aws ecs list-services \
--cluster my-cluster
```

---

## Describe Service

```bash
aws ecs describe-services \
--cluster my-cluster \
--services my-service
```

---

## Create Service

```bash
aws ecs create-service \
--cluster my-cluster \
--service-name my-service \
--task-definition my-app
```

---

## Update Service

```bash
aws ecs update-service \
--cluster my-cluster \
--service my-service
```

---

## Force New Deployment

```bash
aws ecs update-service \
--cluster my-cluster \
--service my-service \
--force-new-deployment
```

---

## Scale Service

```bash
aws ecs update-service \
--cluster my-cluster \
--service my-service \
--desired-count 5
```

---

# ECS Exec Commands

## Enable ECS Exec

Requires:

```text
ExecuteCommand Enabled
```

---

## Open Shell

```bash
aws ecs execute-command \
--cluster my-cluster \
--task TASK_ID \
--container app \
--interactive \
--command "/bin/sh"
```

---

## Run Bash

```bash
aws ecs execute-command \
--cluster my-cluster \
--task TASK_ID \
--container app \
--interactive \
--command "/bin/bash"
```

---

# ECR Commands

## Login To ECR

```bash
aws ecr get-login-password \
| docker login \
--username AWS \
--password-stdin ACCOUNT.dkr.ecr.REGION.amazonaws.com
```

---

## Create Repository

```bash
aws ecr create-repository \
--repository-name my-app
```

---

## List Repositories

```bash
aws ecr describe-repositories
```

---

## Push Image

```bash
docker tag app:latest REPO_URI:v1
docker push REPO_URI:v1
```

---

## Describe Images

```bash
aws ecr describe-images \
--repository-name my-app
```

---

# Docker Commands

## Build Image

```bash
docker build -t app:v1 .
```

---

## Run Locally

```bash
docker run -p 8000:8000 app:v1
```

---

## View Containers

```bash
docker ps
```

---

## View Logs

```bash
docker logs CONTAINER_ID
```

---

## Enter Container

```bash
docker exec -it CONTAINER_ID sh
```

---

# CloudWatch Logs

## List Log Groups

```bash
aws logs describe-log-groups
```

---

## List Log Streams

```bash
aws logs describe-log-streams \
--log-group-name /ecs/my-app
```

---

## Tail Logs

```bash
aws logs tail \
/ecs/my-app \
--follow
```

---

## Get Log Events

```bash
aws logs get-log-events
```

---

# CloudWatch Metrics

## View Metrics

```bash
aws cloudwatch list-metrics
```

---

## Get Metric Statistics

```bash
aws cloudwatch get-metric-statistics
```

---

# Auto Scaling Commands

## Describe Scalable Targets

```bash
aws application-autoscaling \
describe-scalable-targets
```

---

## Describe Policies

```bash
aws application-autoscaling \
describe-scaling-policies
```

---

# ALB Commands

## List Load Balancers

```bash
aws elbv2 describe-load-balancers
```

---

## Describe Target Groups

```bash
aws elbv2 describe-target-groups
```

---

## Check Target Health

```bash
aws elbv2 describe-target-health \
--target-group-arn ARN
```

---

# IAM Commands

## List Roles

```bash
aws iam list-roles
```

---

## Get Role

```bash
aws iam get-role \
--role-name ECSRole
```

---

## List Attached Policies

```bash
aws iam list-attached-role-policies \
--role-name ECSRole
```

---

# Secrets Manager Commands

## List Secrets

```bash
aws secretsmanager list-secrets
```

---

## Get Secret

```bash
aws secretsmanager get-secret-value \
--secret-id my-secret
```

---

# EventBridge Commands

## List Rules

```bash
aws events list-rules
```

---

## Describe Rule

```bash
aws events describe-rule \
--name rule-name
```

---

# Troubleshooting Commands

## Find Running Tasks

```bash
aws ecs list-tasks \
--desired-status RUNNING
```

---

## Find Stopped Tasks

```bash
aws ecs list-tasks \
--desired-status STOPPED
```

---

## Describe Service Events

```bash
aws ecs describe-services \
--cluster my-cluster \
--services my-service
```

Look at:

```text
events
```

section.

---

# Common Debug Workflow

Step 1

```bash
aws ecs describe-services
```

---

Step 2

```bash
aws ecs list-tasks
```

---

Step 3

```bash
aws ecs describe-tasks
```

---

Step 4

```bash
aws logs tail
```

---

Step 5

```bash
aws ecs execute-command
```

---

# ECS Deployment Commands

## Force Redeployment

```bash
aws ecs update-service \
--force-new-deployment
```

---

## Check Deployment Status

```bash
aws ecs describe-services
```

---

# Useful JMESPath Queries

## Running Count

```bash
aws ecs describe-services \
--cluster my-cluster \
--services my-service \
--query "services[0].runningCount"
```

---

## Desired Count

```bash
aws ecs describe-services \
--cluster my-cluster \
--services my-service \
--query "services[0].desiredCount"
```

---

## Latest Task Definition

```bash
aws ecs describe-services \
--cluster my-cluster \
--services my-service \
--query "services[0].taskDefinition"
```

---

# Production Troubleshooting Shortcuts

## Check ECS Health

```bash
aws ecs describe-services
```

---

## Check ALB Health

```bash
aws elbv2 describe-target-health
```

---

## Check Logs

```bash
aws logs tail
```

---

## Check Scaling

```bash
aws application-autoscaling \
describe-scaling-policies
```

---

## Check IAM

```bash
aws iam get-role
```

---

# Senior Engineer Daily Commands

Most frequently used:

```bash
aws ecs describe-services
aws ecs list-tasks
aws ecs describe-tasks
aws ecs execute-command
aws logs tail
aws elbv2 describe-target-health
aws sts get-caller-identity
```

---

# Key Takeaways

- Learn ECS CLI commands.
- Learn CloudWatch troubleshooting.
- Learn ECS Exec.
- Learn ECR workflows.
- Learn ALB diagnostics.
- Learn IAM verification commands.
- Most production debugging starts with service events, logs, and task status.
