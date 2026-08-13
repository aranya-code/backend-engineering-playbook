# Event Patterns

Event Patterns are JSON-based filters that determine whether an incoming event matches a rule.

Instead of processing every event, EventBridge evaluates each event against its configured Event Patterns and forwards only matching events to the target.

------------------------------------------------------------------------

# What is an Event Pattern?

An Event Pattern defines the conditions that an event must satisfy.

Example:

```json
{
  "source": ["aws.ec2"]
}
```

Only EC2 events match this pattern.

------------------------------------------------------------------------

# Why Use Event Patterns?

Event Patterns help you:

- Filter unwanted events
- Reduce unnecessary processing
- Route events accurately
- Improve application performance

------------------------------------------------------------------------

# Basic Event Pattern

```json
{
  "source": ["aws.s3"]
}
```

This matches every Amazon S3 event.

------------------------------------------------------------------------

# Matching Multiple Sources

```json
{
  "source": [
    "aws.ec2",
    "aws.s3"
  ]
}
```

This matches events from EC2 and S3.

------------------------------------------------------------------------

# Matching Detail Types

```json
{
  "detail-type": [
    "Object Created"
  ]
}
```

Only object creation events are matched.

------------------------------------------------------------------------

# Matching Event Details

```json
{
  "detail": {
    "state": ["running"]
  }
}
```

Matches EC2 instances entering the running state.

------------------------------------------------------------------------

# Prefix Matching

```json
{
  "detail": {
    "bucket": [{
      "prefix": "prod-"
    }]
  }
}
```

Matches bucket names beginning with **prod-**.

------------------------------------------------------------------------

# Anything-But Matching

```json
{
  "detail": {
    "state": [{
      "anything-but": "terminated"
    }]
  }
}
```

Matches every state except terminated.

------------------------------------------------------------------------

# Exists Matching

```json
{
  "detail": {
    "instance-id": [{
      "exists": true
    }]
  }
}
```

Checks whether the field exists.

------------------------------------------------------------------------

# Numeric Matching

```json
{
  "detail": {
    "size": [{
      "numeric": [">", 100]
    }]
  }
}
```

Matches values greater than 100.

------------------------------------------------------------------------

# Event Pattern Flow

```text
Incoming Event

      |

      v

Event Pattern

      |

Match?

      |

+-----+------+

|            |

Yes          No

|            |

v            X

Target
```

------------------------------------------------------------------------

# Best Practices

- Keep patterns simple.
- Filter early.
- Avoid unnecessary conditions.
- Test patterns before deployment.
- Use Custom Event Buses for better organization.

------------------------------------------------------------------------

# Key Takeaways

- Event Patterns filter incoming events.
- They are written in JSON.
- Multiple matching operators are supported.
- Proper Event Patterns improve scalability and reduce unnecessary processing.