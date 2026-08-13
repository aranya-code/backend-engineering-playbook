# Troubleshooting: Instance Failing Health Checks

Distinct from a raw Connection Timeout or Connection Refused investigated directly against an instance — this covers the specific, very common scenario where a Load Balancer or Auto Scaling Group reports an instance as unhealthy and cycles it out of rotation.

## Where the Health Check Actually Comes From

| Source | What It Checks |
|---|---|
| Target Group (behind an ALB/NLB) | Configured protocol/path/port, checked directly by the load balancer |
| Auto Scaling Group (EC2 health check) | Whether the instance's underlying EC2 status checks pass |
| Auto Scaling Group (ELB health check, if enabled) | Defers to the attached load balancer's target health, rather than just EC2-level status |

An instance can be perfectly healthy at the EC2 level (fully booted, passing system/instance status checks) while still being reported unhealthy by a Target Group — these are genuinely different checks, and confusing them is a common early misstep in debugging.

## Common Causes

**Health check path returns a non-2xx/3xx status**

The most common cause — the configured health check path (often `/health` or similar) is returning an error, either because the application itself is unhealthy, or because the health check path was never actually implemented and returns a 404.

**Health check hits the wrong port**

The target group is configured to check a different port than the application is actually listening on — a simple, common misconfiguration, especially after changing an application's listening port without updating the target group to match.

**Application takes longer to become healthy than the health check's grace period allows**

An application with a slow startup (loading a large dataset, warming a cache, running migrations) can get marked unhealthy and terminated by the ASG before it's finished starting — before it ever gets the chance to actually pass a check.

**Security Group between the load balancer and the instance blocks the health check**

The load balancer's own security group needs to be allowed as a source in the instance's (or target's) security group specifically for the health check port — a distinct rule from whatever allows normal end-user traffic.

## A Practical Debugging Sequence

```text
1. Check exactly which health check is failing — Target Group or ASG's own
   EC2 status check — they point to different root causes
2. Manually curl the configured health check path/port from within the VPC
   (e.g., from a bastion or another instance in the same security group)
3. Confirm the health check port matches what the application is actually
   listening on
4. Check the security group allows the load balancer as a source on the
   health check port specifically
5. If the app is slow to start, increase the health check grace period on
   the Auto Scaling Group, or the healthy threshold/interval on the Target Group
```

## Senior-Level Considerations

- "Increase the grace period" is a legitimate fix for a genuinely slow-starting application, but it's worth distinguishing from papering over an application that's actually crashing shortly after starting — a grace period only helps if the app *would* eventually become healthy on its own
- A target group's health check path is a genuinely good place to verify real downstream dependencies (a database connection, a critical cache), not just return a static 200 — a shallow health check that always returns success provides false confidence that the instance can actually serve real traffic correctly
