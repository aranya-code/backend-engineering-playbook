# Traffic Flow

Traffic Flow is Route 53's visual policy editor for building routing configurations that are too complex to express as a single flat routing policy.

## What It Solves

Real-world routing logic is often layered: "route by latency, but within each region, weight between two versions, and fail over to a backup region if the primary is unhealthy." Configuring this by hand with individual records is error-prone and hard to visualize. Traffic Flow lets you build this as a tree/graph of routing rules and endpoints in a visual editor.

## Key Concepts

- **Traffic policy** — the visual configuration itself (a reusable template)
- **Policy record** — an instantiation of a traffic policy applied to a specific hosted zone and DNS name
- **Versioning** — traffic policies are versioned; you can update the policy and roll a hosted zone's policy record to a new version, with the old version retained for rollback

## When You Actually Need It

- Geoproximity routing (requires Traffic Flow — there's no other way to configure a bias)
- Multi-layer routing logic combining more than one policy type in a single decision tree
- Organizations that want a visual, auditable representation of routing logic rather than a flat list of records

## Senior-Level Considerations

- Because traffic policies are versioned and reusable, they're a good fit for applying the *same* routing logic pattern across multiple domains/hosted zones consistently — build once, instantiate many times
- Traffic Flow adds a layer of abstraction on top of ordinary records; when troubleshooting, remember that the "real" records visible via a DNS query are generated *from* the policy, and the source of truth for changes is the policy record, not manual edits to the generated records
