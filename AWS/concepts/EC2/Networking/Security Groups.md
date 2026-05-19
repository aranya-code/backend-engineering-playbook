## Security Groups

### Definition
A virtual, stateful firewall controlling inbound and outbound traffic at the instance level.

### Characteristics
- Stateful (If you allow a request *in*, the response is automatically allowed *out*, regardless of outbound rules).
- Attached directly to the network interface (ENI) of the instance.
- Scoped to the Region and VPC.

---

## Inbound Rules

### Definition
Controls incoming traffic trying to reach your EC2 instance.

### Example

| Port | Purpose |
|---|---|
| 22 | SSH (Should be locked down to your specific IP, never `0.0.0.0/0`) |
| 80 | HTTP (Standard web traffic) |
| 443 | HTTPS (Secure web traffic, usually terminates at the Load Balancer, not the EC2) |

---

## Outbound Rules

### Definition
Controls outgoing traffic leaving your EC2 instance.

### Default Behavior
- By default, all outbound traffic is allowed. In highly secure enterprise environments, we lock this down to prevent instances from dialing out to malicious servers if compromised.

---

## Important Security Group Concepts

- All inbound traffic is explicitly denied by default. You have to open ports.
- Multiple EC2 instances can (and should) share the same Security Group if they serve the same function (e.g., a "Web-Tier-SG").
- Best practice: Create a dedicated SG for SSH access (e.g., "Bastion-SG") and only attach it when debugging.
- SGs operate outside the EC2 OS, meaning a denied request never even reaches your server's kernel.

---
