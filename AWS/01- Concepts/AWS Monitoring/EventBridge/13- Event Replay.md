# Event Replay

Event Replay allows Amazon EventBridge to resend previously archived events to an Event Bus. This enables applications to reprocess historical events without manually recreating them.

Replay is especially useful for testing, debugging, disaster recovery, and recovering from application failures.

------------------------------------------------------------------------

# What is Event Replay?

Replay takes events stored in an EventBridge Archive and publishes them back to an Event Bus.

Applications process replayed events just as they would live events.

------------------------------------------------------------------------

# Why Use Replay?

Replay helps you:

- Recover lost processing
- Test new applications
- Validate bug fixes
- Rebuild downstream systems
- Replay business events

------------------------------------------------------------------------

# Replay Workflow

```text
Archive

   |

   v

Replay

   |

   v

Event Bus

   |

   v

Rules

   |

   v

Targets
```

------------------------------------------------------------------------

# Replay Process

1. Select an Archive.
2. Specify the replay time range.
3. Choose the destination Event Bus.
4. Start Replay.
5. EventBridge republishes matching events.

------------------------------------------------------------------------

# Replay Filtering

Replay supports filtering by:

- Time Range
- Event Pattern

Example:

Replay only:

```text
Order Created
```

events from:

```text
January 2026
```

------------------------------------------------------------------------

# Replay Use Cases

- Testing new services
- Disaster recovery
- Analytics rebuilding
- Data migration
- Application debugging

------------------------------------------------------------------------

# Replay vs Live Events

| Live Events | Replay |
|-------------|---------|
| Generated now | Historical events |
| Real-time processing | Reprocessing archived events |
| Immediate delivery | Controlled replay |

------------------------------------------------------------------------

# Real-World Example

An inventory service experiences a bug and misses processing several thousand order events.

After fixing the application:

1. Engineers select the Event Archive.
2. Replay the affected time window.
3. EventBridge republishes the missed events.
4. Inventory is rebuilt automatically.

No manual intervention is required.

------------------------------------------------------------------------

# Best Practices

- Archive important business events.
- Replay only the required time range.
- Test replay in non-production environments first.
- Ensure applications are idempotent before replaying events.
- Monitor replay activity using CloudWatch.

------------------------------------------------------------------------

# Common Mistakes

- Replaying duplicate events without idempotency.
- Replaying unnecessary data.
- Forgetting to archive important events.
- Using replay as a replacement for backups.

------------------------------------------------------------------------

# Key Takeaways

- Event Replay republishes archived events.
- Replay enables recovery, testing, and debugging.
- Applications process replayed events like live events.
- Replay is most effective when combined with EventBridge Archives and idempotent application design.