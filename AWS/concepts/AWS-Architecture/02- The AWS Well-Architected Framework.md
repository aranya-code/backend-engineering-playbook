# The AWS Well-Architected Framework

AWS's own framework for evaluating architecture quality, organized into six pillars. It's less a checklist and more a shared vocabulary for architecture trade-off discussions — genuinely useful in design reviews and interviews alike.

## The Six Pillars

| Pillar | Core Question |
|---|---|
| Operational Excellence | Can you run and monitor this system, and improve it over time, without heroics? |
| Security | Is data and infrastructure protected, with least-privilege access throughout? |
| Reliability | Does the system recover from failure and meet its availability target? |
| Performance Efficiency | Are you using the right resources efficiently as demand changes? |
| Cost Optimization | Are you spending in proportion to the value delivered, avoiding waste? |
| Sustainability | Are you minimizing the environmental impact of the workload? |

## Why This Matters Beyond Being a Checklist

Every real architecture decision trades pillars against each other. Multi-region active-active improves Reliability and Performance Efficiency, but directly costs more (Cost Optimization) and adds operational complexity (Operational Excellence). A senior engineer's job isn't to maximize every pillar — it's to make the trade-off explicit and defensible for the actual business requirement.

## Design Principles That Cut Across Pillars

- **Stop guessing capacity** — use auto scaling and on-demand resources instead of provisioning for a peak that may never arrive
- **Test recovery procedures** — a DR plan that's never been executed is a hypothesis, not a capability (this recurs in the Disaster Recovery file)
- **Automate where possible** — manual processes don't scale and are a common root cause of incidents
- **Allow for evolutionary architecture** — design for the ability to change, not just for today's known requirements

## Using This in Practice

AWS provides a formal Well-Architected Review process (and a free tool in the console) that walks through pillar-specific questions against a real workload. Even informally, structuring an architecture discussion around these six pillars is a fast way to surface the trade-off that's actually being made — and to notice when a decision silently sacrifices a pillar nobody explicitly agreed to sacrifice.
