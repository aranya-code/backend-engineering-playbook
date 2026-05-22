# Elastic Load Balancer (ELB)

## What is ELB?

Elastic Load Balancer (ELB) is an AWS managed service that automatically distributes incoming traffic across multiple backend resources such as EC2 instances, ECS tasks, containers, and Lambda functions.

It improves:
- Availability
- Scalability
- Fault tolerance
- Performance

AWS fully manages the infrastructure, scaling, upgrades, and high availability of ELB.

---

# Why Use a Load Balancer?

## Main Benefits

- Distributes traffic across multiple servers
- Provides a single DNS endpoint for clients
- Improves application availability
- Performs health checks on targets
- Supports SSL/TLS termination
- Handles traffic spikes efficiently
- Supports high availability across Availability Zones
- Separates public traffic from private backend servers

---

# Cross-Zone Load Balancing

## Definition

Cross-zone load balancing distributes traffic evenly across all healthy instances in all enabled Availability Zones.

## Example

If:
- AZ-1 has 2 instances
- AZ-2 has 4 instances

Without cross-zone balancing:
- Each load balancer node sends traffic only to its own AZ

With cross-zone balancing:
- Traffic is evenly distributed across all 6 instances

## Important Note

Cross-zone load balancing helps prevent uneven traffic distribution and improves resource utilization.

---

# Connection Draining / Deregistration Delay

## Definition

When an instance is being removed from a load balancer, ELB waits before stopping traffic completely.

This allows:
- Existing requests to complete
- Active user sessions to finish gracefully

## Default Value

- Default deregistration delay: 300 seconds

## Use Case

Useful during:
- Deployments
- Scaling activities
- Maintenance windows

---

# ELB Integrations

ELB integrates well with:

- EC2 Auto Scaling
- Amazon ECS
- Route 53
- CloudWatch
- AWS WAF
- AWS Global Accelerator

---

# Interview Notes

## Important Points

- ELB is a fully managed AWS service.
- ELB itself scales automatically.
- Health checks determine whether a target receives traffic.
- ELB improves fault tolerance and high availability.
- ELB works closely with Auto Scaling Groups.

