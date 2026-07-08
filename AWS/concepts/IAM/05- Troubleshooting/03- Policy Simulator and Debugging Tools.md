# Policy Simulator and Debugging Tools

Beyond reading error messages and manually tracing policy logic, AWS provides purpose-built tools for testing and debugging IAM permissions before (and after) something goes wrong.

## IAM Policy Simulator

Tests whether a specific action on a specific resource would be allowed or denied for a given user, group, or role — **without actually making the API call**. Reports the result along with which specific policy statement produced it (an Allow, an explicit Deny, or the implicit default deny).

**Best for:** confirming a policy change will have the intended effect *before* deploying it, and diagnosing exactly which statement is responsible for an unexpected Allow or Deny.

## IAM Access Analyzer's Policy Validation

Beyond finding unintended external access (see Security), Access Analyzer also validates policies as you write them — flagging syntax errors, overly permissive patterns, and warnings about constructs that technically work but are likely mistakes (e.g., an empty `Principal` block, or a condition that can never actually be true).

## CloudTrail — After-the-Fact Investigation

When Policy Simulator isn't enough (the issue only shows up under real conditions the simulator doesn't fully replicate — certain resource-based policy or SCP interactions in complex scenarios), CloudTrail's actual event history shows exactly what happened on a real request: the specific error, the exact principal, and enough detail to reconstruct the evaluation.

## `iam:SimulateCustomPolicy` and `iam:SimulatePrincipalPolicy` APIs

The programmatic equivalents of the console-based Policy Simulator — useful for building automated policy-testing into a CI/CD pipeline for infrastructure-as-code changes, catching an unintended permission regression before it's deployed rather than after.

## A Practical Debugging Toolkit, Top to Bottom

```text
1. Policy Simulator — test the hypothesis before touching real infrastructure
2. Access Analyzer policy validation — catch syntax/structural issues while writing the policy
3. Deploy the change
4. CloudTrail — confirm real-world behavior matches expectation, and investigate if it doesn't
```

## Senior-Level Considerations

- Policy Simulator has some real limitations — it doesn't fully evaluate every resource-based policy and SCP interaction in all cases, so a Simulator "Allow" isn't an absolute guarantee against every edge case, especially in complex multi-account setups; it's a strong first check, not a substitute for testing in a real (non-production) environment for high-stakes changes
- Building automated policy testing into CI/CD (via the Simulate APIs) catches a class of bug — "this infrastructure change quietly broke someone's access" — that's otherwise only discovered when the affected person tries to do their job and can't
