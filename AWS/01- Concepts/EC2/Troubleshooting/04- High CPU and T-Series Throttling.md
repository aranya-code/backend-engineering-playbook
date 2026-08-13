# Troubleshooting: High CPU and T-Series Throttling

## The Specific Failure Mode

A T-series instance (see `Instance Types.md` for the full CPU credit model) appears to slow down dramatically under sustained load, even though nothing else about the application or infrastructure has changed. This is one of the most common "why did performance suddenly degrade" investigations on EC2, and it has a very specific, checkable root cause.

## Why This Happens

T-series instances provide a CPU baseline (e.g., 20% for a `t3.medium`) with the ability to burst above it using accumulated CPU credits. Under genuinely sustained load — not a brief spike, but continuous demand — credits deplete faster than they accumulate, and once exhausted, the instance is throttled back down to its baseline percentage in **Standard** credit mode. An application that needs 80% CPU to perform well, throttled down to a 20% baseline, becomes roughly four to five times slower — a dramatic, sudden-feeling change that's actually a gradual credit depletion reaching zero.

## Diagnosing It

```text
1. Check the CloudWatch metric CPUCreditBalance for the instance
2. If it's trending toward zero (or already at zero) during the period
   of degraded performance, this is very likely the cause
3. Also check CPUSurplusCreditBalance if in Unlimited mode, and
   CPUSurplusCreditsCharged for any associated overage cost
```

## Fixes, in Order of How Structural They Are

**Switch to Unlimited credit mode** — allows the instance to burst past its credit balance, billed per vCPU-hour for the overage, rather than being hard-throttled to baseline. A quick mitigation, but can result in unexpected charges if the sustained-high-load pattern continues indefinitely rather than being a temporary spike.

**Move to an M-series (fixed-performance) instance** — if the workload is now genuinely, consistently CPU-heavy rather than occasionally bursty, a T-series instance was likely the wrong choice for its actual usage pattern in the first place, and a non-burstable family removes the credit mechanic entirely.

**Right-size based on actual utilization data** — AWS Compute Optimizer and CloudWatch metrics over a real observation window will show whether the workload's actual CPU profile matches a burstable or steady-state instance family better.

## Senior-Level Considerations

- A T-series instance quietly running in Unlimited mode with sustained high CPU can accumulate meaningful surplus charges without an obvious, single alarming event — regularly reviewing `CPUSurplusCreditsCharged` is worth building into routine cost monitoring, not just performance monitoring
- This failure mode is a good illustration of why "it was fine yesterday, nothing changed, but it's slow today" doesn't always mean nothing changed — gradual credit depletion under a slowly growing, sustained load can cross the throttling threshold without any discrete deploy or configuration change to point to
- Setting a CloudWatch alarm on `CPUCreditBalance` approaching zero (rather than waiting to notice degraded performance after the fact) turns this from a reactive investigation into a proactive one
