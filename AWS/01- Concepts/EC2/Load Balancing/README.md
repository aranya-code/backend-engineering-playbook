# Load Balancing

Distributing traffic across instances, and the SSL/session mechanics that come with it.

---

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Elastic Load Balancer](01-%20Elastic%20Load%20Balancer.md) | What ELB is, and what it improves |
| 02 | [Load Balancer Types](02-%20Load%20Balancer%20Types.md) | CLB, ALB, NLB, and GWLB compared |
| 03 | [SSL Certificates](03-%20SSL%20Certificates.md) | TLS termination at the load balancer |
| 04 | [SNI](04-%20SNI.md) | Hosting multiple SSL certificates on one IP |
| 05 | [Sticky Sessions](05-%20Sticky%20Sessions.md) | Binding a client to a specific target instance |

---

## 🔗 See Also

- [`../`](../) — EC2 overview
- [`../Networking/01- Security Groups.md`](../Networking/01-%20Security%20Groups.md) — securing traffic between the load balancer and targets
- [`../Troubleshooting/03- Instance Failing Health Checks.md`](../Troubleshooting/03-%20Instance%20Failing%20Health%20Checks.md) — debugging target health specifically

---

*Part of the [backend-engineering-playbook](../../../../) knowledge base — Aranya Majumdar*
