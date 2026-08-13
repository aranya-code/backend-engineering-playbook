# EventBridge Archives

Amazon EventBridge Archives allow you to store historical events from an Event Bus for auditing, debugging, testing, and recovery purposes.

Archived events can later be replayed to reproduce application behavior or recover from failures.

------------------------------------------------------------------------

# What is an Archive?

An Archive is a storage location where EventBridge keeps copies of events.

Instead of permanently losing processed events, they can be stored for future use.

------------------------------------------------------------------------

# Why Use Archives?

Archives help you:

- Recover from failures
- Debug production issues
- Test new applications
- Meet compliance requirements
- Audit historical events

------------------------------------------------------------------------

# How Archives Work

```text
Producer

    |

    v

Event Bus

    |

    +----------+

    |          |

    v          v

 Rule      Archive

    |

    v

 Target
```

Every matching event can be stored automatically.

------------------------------------------------------------------------

# Archive Creation

When creating an archive, you specify:

- Archive Name
- Event Bus
- Event Pattern (Optional)
- Retention Period

Only matching events are archived.

------------------------------------------------------------------------

# Archive Filtering

You can archive:

- Every event
- Only EC2 events
- Only S3 events
- Only custom application events

Example:

```json
{
  "source": ["aws.s3"]
}
```

Only S3 events are archived.

------------------------------------------------------------------------

# Retention

Archives support configurable retention periods.

Example:

- 30 Days
- 90 Days
- 1 Year
- Indefinitely

Longer retention may increase storage costs.

------------------------------------------------------------------------

# Archive Workflow

```text
Application

      |

      v

EventBridge

      |

      v

Archive

      |

Historical Storage
```

------------------------------------------------------------------------

# Benefits

- Event recovery
- Historical analysis
- Compliance
- Debugging
- Testing
- Auditing

------------------------------------------------------------------------

# Common Use Cases

- Financial auditing
- Healthcare compliance
- Event recovery
- Development testing
- Disaster recovery

------------------------------------------------------------------------

# Real-World Example

A retail company stores every **Order Created** event for one year.

Months later, developers discover a bug in the analytics application.

Instead of recreating millions of orders manually, they replay archived events to regenerate analytics data.

------------------------------------------------------------------------

# Best Practices

- Archive important business events.
- Avoid archiving unnecessary events.
- Configure appropriate retention periods.
- Monitor archive storage costs.
- Use Event Patterns to reduce archive size.

------------------------------------------------------------------------

# Key Takeaways

- Archives store historical EventBridge events.
- Archived events support debugging, auditing, testing, and recovery.
- Event Patterns determine which events are archived.
- Archives work together with Event Replay.