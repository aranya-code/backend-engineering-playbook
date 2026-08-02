# Image Pull Failures

Before an Amazon ECS task can start, it must download its container image from a container registry such as **Amazon Elastic Container Registry (Amazon ECR)** or another supported registry. If ECS cannot retrieve the image, the task fails before the application even starts.

Image pull failures are among the most common ECS deployment problems and are usually caused by incorrect image references, IAM permission issues, authentication failures, or networking problems.

---

# Typical Symptoms

You may observe one or more of the following:

- Task immediately stops.
- Deployment fails.
- Tasks remain in **PENDING** briefly before stopping.
- ECS Service continuously retries task creation.
- No application logs appear.

Example

```
Task Created

↓

Pull Docker Image

↓

Failed

↓

Task Stopped
```

---

# Common Error Messages

Examples include:

```
CannotPullContainerError
```

```
pull access denied
```

```
no basic auth credentials
```

```
manifest unknown
```

```
repository does not exist
```

```
failed to resolve image
```

---

# Troubleshooting Workflow

Always investigate image pull failures using the following process.

```
Image Pull Failed

        │

        ▼

Task Stop Reason

        │

        ▼

Image Name

        │

        ▼

Amazon ECR

        │

        ▼

IAM Permissions

        │

        ▼

Network Connectivity

        │

        ▼

Root Cause
```

---

# Step 1: Check the Task Stop Reason

Open the failed task and review the **Stopped Reason**.

Examples

```
CannotPullContainerError
```

```
Image not found
```

```
Repository does not exist
```

This often immediately identifies the issue.

---

# Step 2: Verify the Image Name

A very common mistake is using the wrong repository or image tag.

Example

Correct

```
backend-api:v2
```

Incorrect

```
backend-api:v20
```

Verify:

- Repository name
- Image tag
- AWS Region
- Registry URI

---

# Step 3: Verify the Image Exists

Open Amazon ECR and confirm:

- Repository exists
- Image exists
- Tag exists
- Image was successfully pushed

Example

```
Repository

backend-api

↓

Image

v2

✓
```

---

# Step 4: Verify the Task Execution Role

The **Task Execution Role** is responsible for downloading container images.

It should include permissions such as:

```
ecr:GetAuthorizationToken

ecr:BatchGetImage

ecr:GetDownloadUrlForLayer

ecr:BatchCheckLayerAvailability
```

---

### Interview Tip

Downloading container images uses the **Execution Role**, not the **Task Role**.

---

# Step 5: Verify Repository Permissions

Check the Amazon ECR repository policy.

Verify that the ECS task is allowed to pull images.

Example

```
Execution Role

↓

Amazon ECR

↓

Allow
```

---

# Step 6: Verify Network Connectivity

For private subnets, ECS must be able to communicate with Amazon ECR.

Possible solutions include:

- NAT Gateway
- Interface VPC Endpoint for ECR
- Internet Gateway (public subnet)

Without network access, image downloads fail.

---

# Step 7: Verify AWS Region

A common mistake is referencing an image from another region.

Example

Task Definition

```
us-east-1
```

Repository

```
eu-west-1
```

The image cannot be located.

---

# Step 8: Verify Image Tag

Avoid relying on

```
latest
```

Always use versioned tags.

Example

```
backend-api:v1.0.5
```

instead of

```
latest
```

Versioned tags make deployments reproducible and easier to troubleshoot.

---

# Step 9: Verify Docker Image

Sometimes the image itself is corrupted.

Test locally.

Example

```
docker pull image

↓

docker run image
```

Ensure the image starts correctly before deploying.

---

# Step 10: Verify Registry Authentication

For third-party registries:

- Docker Hub
- GitHub Container Registry
- Harbor
- Private registries

verify:

- Username
- Password
- Token
- Registry credentials

Authentication failures prevent image downloads.

---

# Common Root Causes

| Problem | Solution |
|----------|----------|
| Wrong image tag | Correct the tag |
| Repository missing | Create or restore repository |
| Image missing | Push image again |
| Execution Role missing permissions | Update IAM policy |
| Repository policy | Grant pull access |
| Wrong AWS Region | Use correct regional repository |
| No network access | Configure NAT Gateway or VPC Endpoint |
| Registry authentication failure | Update credentials |
| Corrupted image | Rebuild and push image |

---

# Diagnostic Checklist

Before redeploying, verify:

- Repository exists.
- Image exists.
- Image tag correct.
- Registry URI correct.
- Task Execution Role configured.
- ECR permissions granted.
- Repository policy correct.
- Network connectivity available.
- Correct AWS Region.
- Image starts successfully locally.

---

# Best Practices

- Never use the `latest` tag in production.
- Use immutable version tags.
- Enable image vulnerability scanning in Amazon ECR.
- Use least-privilege IAM policies.
- Keep container images small.
- Regularly remove unused images.
- Store images in the same AWS Region as the ECS cluster.
- Test images locally before deployment.

---

# Interview Questions

### Why would ECS fail to pull a Docker image?

Common reasons include:

- Wrong image tag
- Repository missing
- Image missing
- Missing IAM permissions
- Network connectivity issues
- Authentication failures
- Wrong AWS Region

---

### Which IAM role downloads the image?

The **Task Execution Role**.

---

### Why is using the `latest` tag discouraged?

Because:

- Deployments become unpredictable.
- Rollbacks become difficult.
- Different environments may pull different images.
- Version tracking becomes unreliable.

Immutable version tags provide consistent deployments.

---

### How would you troubleshoot a `CannotPullContainerError`?

Recommended investigation order:

1. Review Task Stop Reason.
2. Verify image exists.
3. Check image tag.
4. Verify Task Execution Role.
5. Check ECR repository policy.
6. Verify network connectivity.
7. Confirm AWS Region.
8. Test the image locally.

---

### What is the difference between the Task Role and the Task Execution Role?

| Task Role | Task Execution Role |
|------------|--------------------|
| Used by the application | Used by ECS |
| Accesses AWS services during runtime | Pulls images and sends logs |
| Example: Access S3 | Example: Pull image from Amazon ECR |

---

# Key Takeaways

- Image pull failures occur before the application starts and are most often caused by incorrect image references, IAM permissions, or networking issues.
- The Task Execution Role—not the Task Role—is responsible for pulling images from Amazon ECR.
- Always verify the repository, image tag, AWS Region, and network connectivity before investigating application-level issues.
- Use immutable image tags instead of `latest` to ensure predictable deployments and simpler rollbacks.
- A systematic troubleshooting approach significantly reduces deployment failures related to container image retrieval.