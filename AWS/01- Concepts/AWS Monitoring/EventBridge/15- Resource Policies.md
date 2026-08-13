# Resource Policies

Amazon EventBridge Resource Policies are JSON-based policies that control who can access and interact with an Event Bus. They enable secure sharing of Event Buses across AWS accounts and organizations.

Unlike IAM policies, which grant permissions to users and roles, Resource Policies are attached directly to EventBridge resources.

------------------------------------------------------------------------

# What are Resource Policies?

A Resource Policy defines who can:

- Put events
- Create rules
- Read rules
- Access Event Buses

Policies are attached directly to an Event Bus.

------------------------------------------------------------------------

# Why Use Resource Policies?

Resource Policies allow you to:

- Share Event Buses across accounts
- Enable centralized event routing
- Improve security
- Control access using least privilege

------------------------------------------------------------------------

# How Resource Policies Work

```text
Account A

      |

Permission

      |

      v

Event Bus

      |

      v

Account B
```

Only authorized accounts can publish or receive events.

------------------------------------------------------------------------

# Policy Structure

A Resource Policy contains:

- Version
- Statement
- Effect
- Principal
- Action
- Resource

Example:

```json
{
  "Effect": "Allow",
  "Principal": {
    "AWS": "123456789012"
  },
  "Action": "events:PutEvents",
  "Resource": "arn:aws:events:ap-south-1:111111111111:event-bus/MyBus"
}
```

------------------------------------------------------------------------

# Common Actions

Common EventBridge actions include:

- events:PutEvents
- events:PutRule
- events:DeleteRule
- events:DescribeRule
- events:ListRules

------------------------------------------------------------------------

# Cross-Account Access

A common use case:

```text
Development Account

↓

Publishes Events

↓

Production Monitoring Account
```

The Production Event Bus allows the Development account to publish events using a Resource Policy.

------------------------------------------------------------------------

# Resource Policies vs IAM Policies

| IAM Policy | Resource Policy |
|------------|-----------------|
| Attached to users or roles | Attached to Event Bus |
| Controls user permissions | Controls resource access |
| Identity-based | Resource-based |

Both can work together to secure EventBridge.

------------------------------------------------------------------------

# Security Best Practices

- Grant only required permissions.
- Use specific AWS account IDs.
- Avoid wildcard principals (`*`) unless absolutely necessary.
- Audit policies regularly.
- Enable CloudTrail for auditing.

------------------------------------------------------------------------

# Real-World Example

A company has separate AWS accounts for:

- Development
- Testing
- Production

The Production account owns a centralized Event Bus.

Resource Policies allow Development and Testing accounts to publish events while preventing unauthorized access.

------------------------------------------------------------------------

# Key Takeaways

- Resource Policies control access to EventBridge resources.
- They enable secure cross-account event routing.
- Resource Policies complement IAM policies.
- Always follow the principle of least privilege.