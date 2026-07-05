# Composite Alarms

A **Composite Alarm** is a CloudWatch Alarm that monitors the state of multiple CloudWatch Alarms instead of monitoring a single metric directly. It evaluates logical conditions (such as **AND**, **OR**, and **NOT**) across multiple alarms to determine its own state.

Composite Alarms help reduce alert fatigue by combining multiple alarms into a single, meaningful notification.

---

# What is a Composite Alarm?

Unlike a standard CloudWatch Alarm, which evaluates a metric, a Composite Alarm evaluates the state of one or more existing CloudWatch Alarms.

For example:

```text
CPU Alarm = ALARM

Memory Alarm = ALARM

Composite Alarm = ALARM
```

The Composite Alarm does not monitor metrics directly. Instead, it monitors the state of other alarms.

---

# Why Use Composite Alarms?

Composite Alarms help you:

- Reduce duplicate notifications
- Eliminate alert fatigue
- Combine multiple monitoring conditions
- Simplify operational dashboards
- Improve incident management
- Create more meaningful alerts

---

# How Composite Alarms Work

```text
CloudWatch Metrics
        |
        v
Standard Alarms
        |
        +----------------------+
        |                      |
        v                      v
 CPU Alarm             Memory Alarm
        |                      |
        +----------+-----------+
                   |
                   v
          Composite Alarm
                   |
                   v
          Amazon SNS / Lambda
```

Instead of receiving multiple notifications, engineers receive one notification from the Composite Alarm.

---

# Alarm Rules

Composite Alarms use **Alarm Rules** to evaluate the state of other alarms.

Common logical operators include:

- AND
- OR
- NOT

---

# AND Condition

The Composite Alarm enters the **ALARM** state only if **all monitored alarms** are in the **ALARM** state.

Example:

```text
CPU Alarm = ALARM

AND

Memory Alarm = ALARM
```

Result:

```text
Composite Alarm = ALARM
```

This is useful when multiple failures indicate a genuine production issue.

---

# OR Condition

The Composite Alarm enters the **ALARM** state if **any monitored alarm** enters the **ALARM** state.

Example:

```text
CPU Alarm = ALARM

OR

Disk Alarm = ALARM
```

Result:

```text
Composite Alarm = ALARM
```

Useful when any single condition requires immediate attention.

---

# NOT Condition

The **NOT** operator reverses the alarm state.

Example:

```text
CPU Alarm

AND

NOT Maintenance Alarm
```

This prevents alerts during scheduled maintenance windows.

---

# Example Alarm Rule

```text
(ALARM(CPUAlarm))
AND
(ALARM(MemoryAlarm))
```

The Composite Alarm enters the **ALARM** state only when both alarms are triggered.

---

# Composite Alarm States

Like standard CloudWatch Alarms, Composite Alarms have three possible states:

- **OK**
- **ALARM**
- **INSUFFICIENT_DATA**

The state depends on the evaluation of the underlying alarms.

---

# Alarm Actions

Composite Alarms support the same notification actions as standard alarms.

Common actions include:

- Amazon SNS notifications
- AWS Lambda invocation
- Incident management integration
- Third-party monitoring tools

**Note:** Composite Alarms cannot directly perform EC2 recovery or Auto Scaling actions because they do not monitor metrics directly. Those actions should remain on the underlying metric alarms.

---

# Standard Alarm vs Composite Alarm

| Standard Alarm | Composite Alarm |
|----------------|-----------------|
| Monitors a metric | Monitors other alarms |
| Evaluates metric values | Evaluates alarm states |
| Simple configuration | Supports logical conditions |
| Best for individual resources | Best for application-level monitoring |

---

# Common Use Cases

Composite Alarms are commonly used for:

- Production monitoring
- Multi-tier applications
- Auto Scaling environments
- High availability systems
- Microservices
- Reducing duplicate alerts

---

# Real-World Example

A production e-commerce application consists of:

- Web Server
- Application Server
- Database Server

Individual alarms monitor:

- CPU Utilization
- Memory Utilization
- Database Connections

Instead of sending three separate alerts, a Composite Alarm is configured:

```text
CPU Alarm

AND

Memory Alarm

AND

Database Alarm
```

Only when all critical alarms indicate a problem does the Composite Alarm send a notification to the operations team.

This significantly reduces unnecessary alerts and focuses attention on genuine production incidents.

---

# Best Practices

- Use Composite Alarms to reduce alert fatigue.
- Keep alarm rules simple and easy to understand.
- Combine only related alarms.
- Use meaningful alarm names.
- Test alarm rules before deploying to production.
- Continue using standard alarms for Auto Scaling and EC2 recovery actions.

---

# Common Mistakes

- Creating overly complex alarm rules.
- Combining unrelated alarms.
- Using Composite Alarms for every workload.
- Forgetting to test alarm logic.
- Replacing all standard alarms with Composite Alarms.

---

# Key Takeaways

- Composite Alarms monitor the state of other CloudWatch Alarms instead of monitoring metrics directly.
- They support logical operators such as **AND**, **OR**, and **NOT**.
- Composite Alarms reduce alert fatigue by combining multiple alarms into a single notification.
- They improve operational efficiency by highlighting only meaningful incidents.
- Composite Alarms are ideal for production environments with multiple related monitoring conditions.