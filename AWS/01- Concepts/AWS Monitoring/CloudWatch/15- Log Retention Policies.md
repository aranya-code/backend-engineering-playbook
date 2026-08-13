# Log Retention Policies

A **Log Retention Policy** determines how long CloudWatch Logs keeps log events before they are automatically deleted. Proper retention settings help control storage costs while meeting operational and compliance requirements.

---

# What is Log Retention?

By default, a new CloudWatch Log Group keeps log events indefinitely (**Never Expire**).

A retention policy allows you to automatically remove older log events after a specified period.

---

# Why are Retention Policies Important?

Retention policies help you:

- Control CloudWatch storage costs
- Meet compliance requirements
- Remove outdated log data automatically
- Reduce operational overhead
- Manage the log lifecycle efficiently

---

# Available Retention Periods

CloudWatch supports several predefined retention periods, including:

- 1 Day
- 3 Days
- 5 Days
- 7 Days
- 14 Days
- 30 Days
- 60 Days
- 90 Days
- 120 Days
- 150 Days
- 180 Days
- 1 Year
- 13 Months
- 18 Months
- 2 Years
- 3 Years
- 5 Years
- 10 Years
- Never Expire

Choose the retention period based on business, operational, and regulatory requirements.

---

# How Retention Works

```text
Application
      |
      v
CloudWatch Log Group
      |
      v
Retention Policy
      |
      v
Old Log Events Automatically Deleted
```

CloudWatch continuously checks log age and removes events that exceed the configured retention period.

---

# Configuring Retention

Retention is configured **per Log Group**.

Different applications can have different retention periods.

Example:

| Log Group | Retention |
|-----------|-----------|
| /aws/lambda/payment-service | 30 Days |
| /aws/ec2/web-server | 90 Days |
| /application/security | 5 Years |

---

# Cost Considerations

Longer retention means:

- Higher storage costs
- More historical data available
- Better support for audits and investigations

Shorter retention means:

- Lower storage costs
- Less historical information
- Faster cleanup of old logs

Balance cost with operational and compliance needs.

---

# Compliance Considerations

Some industries require logs to be retained for extended periods.

Examples:

- Financial services
- Healthcare
- Government
- Insurance

Always verify retention requirements before deleting log data.

---

# Real-World Example

An e-commerce company configures:

- Application logs: 30 days
- Infrastructure logs: 90 days
- Security audit logs: 5 years

This approach keeps recent operational logs readily available while retaining security logs for compliance.

---

# Best Practices

- Configure a retention policy for every Log Group.
- Avoid using **Never Expire** unless required.
- Use shorter retention for development environments.
- Use longer retention for audit and security logs.
- Review retention policies periodically to optimize storage costs.

---

# Key Takeaways

- Log Retention Policies define how long CloudWatch stores log events.
- Retention is configured per Log Group.
- Automatic deletion helps control storage costs.
- Choose retention periods based on operational, business, and compliance requirements.
